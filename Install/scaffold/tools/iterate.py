#!/usr/bin/env python3
"""
Iterate orchestrator — manages adversarial review sessions for scaffold documents.

Coordinates between Claude (via sub-skills) and adversarial-review.py (external LLM reviewer)
using file-based message passing:
  - action.json: iterate.py writes the next instruction for Claude
  - result.json: Claude's sub-skill writes its response

Commands:
    preflight    Check if a layer/target is ready for review.
    next-action  Write action.json with the next instruction. Starts or resumes a session.
    resolve      Read result.json, process it, write next action.json.

Session state persists in .reviews/iterate/session-<id>.json.
Temp files (action.json, result.json) are overwritten each exchange.
No pip dependencies — uses Python standard library only.

Convergence rules:
  - "Stable" = a verification pass of changed sections produces zero new
    issues that aren't already in resolved_root_causes.
  - "New issue" = different root cause than any previously resolved issue.
    Reworded issues with the same root cause are deduped by _extract_root_cause().
  - Verification pass only re-reviews sections that had changes applied (not all sections).
  - Max iterations cap prevents infinite loops (default 10).
  - Escalation: issues with severity CRITICAL that are rejected twice → stop iteration, report as blocking.

Issue categorization:
  - Mechanical (LOW severity + concrete suggestion, or category:"mechanical"):
    auto-accepted, skip adjudication, go straight to apply batch.
  - Quality (MEDIUM/HIGH with suggestion): full adjudicate → scope-check → apply.
  - Architecture-affecting (changes ownership, authority, contracts): adjudicate → scope-check required.
  - Ambiguous (no suggestion, unclear fix): escalate to user.
"""

import json
import os
import sys
import argparse
import hashlib
import re
import subprocess
import time
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TOOLS_DIR = Path(__file__).parent
CONFIGS_DIR = TOOLS_DIR / "configs" / "iterate"
SCAFFOLD_DIR = TOOLS_DIR.parent
REVIEWS_DIR = SCAFFOLD_DIR / ".reviews" / "iterate"
DOC_REVIEW_SCRIPT = TOOLS_DIR / "adversarial-review.py"
CODE_REVIEW_SCRIPT = TOOLS_DIR / "code-review.py"
ACTION_FILE = REVIEWS_DIR / "action.json"
RESULT_FILE = REVIEWS_DIR / "result.json"


# ---------------------------------------------------------------------------
# YAML Parser (minimal, no dependencies)
# ---------------------------------------------------------------------------

def _parse_yaml_value(val):
    """Parse a YAML scalar value into a Python type."""
    val = val.strip()
    if val == "" or val == "~" or val == "null":
        return None
    if val == "true" or val == "True":
        return True
    if val == "false" or val == "False":
        return False
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    if (val.startswith('"') and val.endswith('"')) or \
       (val.startswith("'") and val.endswith("'")):
        return val[1:-1]
    return val


def _count_indent(line):
    return len(line) - len(line.lstrip())


def load_yaml(path):
    """Minimal YAML loader for iterate configs."""
    path = Path(path)
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    return _parse_yaml_block(lines, 0, 0)[0]


def _parse_yaml_block(lines, start, base_indent):
    result = {}
    i = start
    is_list = False
    result_list = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = _count_indent(line)

        if indent < base_indent:
            break

        if indent == base_indent:
            if stripped.startswith("- "):
                is_list = True
                item_text = stripped[2:].strip()

                if ":" in item_text and not item_text.startswith('"'):
                    colon_pos = item_text.index(":")
                    key = item_text[:colon_pos].strip()
                    val_text = item_text[colon_pos + 1:].strip()

                    if val_text:
                        item_dict = {key: _parse_yaml_value(val_text)}
                    else:
                        item_dict = {key: None}

                    next_i = i + 1
                    if next_i < len(lines):
                        next_stripped = lines[next_i].strip()
                        next_indent = _count_indent(lines[next_i]) if next_stripped else 0
                        if next_stripped and next_indent > indent:
                            child, next_i = _parse_yaml_block(lines, next_i, next_indent)
                            if not val_text:
                                item_dict[key] = child
                            i = next_i
                            result_list.append(item_dict)
                            continue

                    i += 1
                    result_list.append(item_dict)
                    continue
                else:
                    result_list.append(_parse_yaml_value(item_text))
                    i += 1
                    continue

            if ":" in stripped:
                colon_pos = stripped.index(":")
                key = stripped[:colon_pos].strip()
                val_text = stripped[colon_pos + 1:].strip()

                if val_text.startswith("[") and val_text.endswith("]"):
                    inner = val_text[1:-1]
                    if inner.strip():
                        items = [_parse_yaml_value(x.strip()) for x in inner.split(",")]
                    else:
                        items = []
                    result[key] = items
                    i += 1
                    continue

                if val_text:
                    result[key] = _parse_yaml_value(val_text)
                    i += 1
                    continue

                next_i = i + 1
                while next_i < len(lines) and not lines[next_i].strip():
                    next_i += 1

                if next_i < len(lines):
                    next_indent = _count_indent(lines[next_i])
                    if next_indent > base_indent:
                        child, next_i = _parse_yaml_block(lines, next_i, next_indent)
                        result[key] = child
                        i = next_i
                        continue

                result[key] = None
                i += 1
                continue

        i += 1

    if is_list:
        return result_list, i
    return result, i


# ---------------------------------------------------------------------------
# Config & Session
# ---------------------------------------------------------------------------

def load_layer_config(layer):
    config_path = CONFIGS_DIR / f"{layer}.yaml"
    if not config_path.exists():
        return None
    return load_yaml(config_path)


def _session_id(layer, target):
    key = f"{layer}:{target}"
    h = hashlib.md5(key.encode()).hexdigest()[:8]
    name = Path(target).stem if target else layer
    return f"iter-{name}-{h}"


def _session_path(session_id):
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    return REVIEWS_DIR / f"session-{session_id}.json"


def _load_session(session_id):
    path = _session_path(session_id)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_session(session_id, data):
    path = _session_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _write_action(data):
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ACTION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _read_result():
    if not RESULT_FILE.exists():
        return None
    with open(RESULT_FILE, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Context File Resolution
# ---------------------------------------------------------------------------

def resolve_context_files(config, target_path, section_heading=None):
    """Resolve context using the hierarchical context system.
    Falls back to legacy context_files format if no 'context' key in config."""
    # New format: use context.py resolver
    if "context" in config:
        try:
            from context import resolve as ctx_resolve, resolve_as_text
            ctx_text = resolve_as_text(config, target_path, section_heading)
            if ctx_text:
                # Write extracted context to a single temp file
                # (adversarial-review.py reads --context-files as whole files)
                ctx_file = REVIEWS_DIR / f"ctx-{hashlib.md5((target_path + str(section_heading)).encode()).hexdigest()[:8]}.md"
                ctx_file.write_text(ctx_text, encoding="utf-8")
                return [str(ctx_file)]
            return []
        except ImportError:
            pass  # Fall through to legacy

    # Legacy format: flat context_files
    files = []
    static = config.get("context_files", {})
    if isinstance(static, dict):
        static_list = static.get("static", [])
    elif isinstance(static, list):
        static_list = static
    else:
        static_list = []

    for rel_path in static_list:
        abs_path = SCAFFOLD_DIR / rel_path
        if abs_path.exists():
            files.append(str(abs_path))

    dynamic = config.get("context_files", {})
    if isinstance(dynamic, dict):
        dynamic_list = dynamic.get("dynamic", [])
    else:
        dynamic_list = []

    for entry in dynamic_list:
        if isinstance(entry, dict):
            pattern = entry.get("pattern", "")
            if pattern:
                for match in sorted(SCAFFOLD_DIR.glob(pattern)):
                    filter_str = entry.get("filter", "")
                    if filter_str and match.exists():
                        content = match.read_text(encoding="utf-8")
                        if filter_str not in content:
                            continue
                    files.append(str(match))

    target_abs = SCAFFOLD_DIR / target_path if not Path(target_path).is_absolute() else Path(target_path)
    if target_abs.exists() and str(target_abs) not in files:
        files.insert(0, str(target_abs))

    return files


# ---------------------------------------------------------------------------
# Section Extraction
# ---------------------------------------------------------------------------

def _extract_section(doc_content, heading):
    """Extract content under a specific heading from a markdown document."""
    level = len(heading) - len(heading.lstrip("#"))
    heading_text = heading.lstrip("# ").strip()
    pattern = rf"^{'#' * level}\s+{re.escape(heading_text)}\s*$"

    lines = doc_content.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(pattern, line.strip()):
            start = i
            break

    if start is None:
        return None

    # Find the end — next heading at same or higher level
    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i].strip()
        if line.startswith("#"):
            match = re.match(r"^(#+)", line)
            if match and len(match.group(1)) <= level:
                end = i
                break

    return "\n".join(lines[start:end]).strip()


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

def cmd_preflight(args):
    config = load_layer_config(args.layer)
    if not config:
        _output({"status": "error", "message": f"No config found for layer '{args.layer}'"})
        return

    preflight = config.get("preflight", {})
    required = preflight.get("required_files", [])
    issues = []

    for rel_path in required:
        abs_path = SCAFFOLD_DIR / rel_path
        if not abs_path.exists():
            issues.append(f"Required file missing: {rel_path}")

    # Check target exists
    if args.target:
        target_abs = SCAFFOLD_DIR / args.target
        if not target_abs.exists():
            # Try glob
            pattern = preflight.get("glob_pattern", "")
            if pattern:
                matches = list(SCAFFOLD_DIR.glob(pattern))
                if not matches:
                    issues.append(f"Target not found: {args.target}")

    if issues:
        msg = preflight.get("blocked_message", "Preflight failed.")
        _output({"status": "blocked", "message": msg, "issues": issues})
        return

    # Check critical sections if target provided
    if args.target:
        target_abs = SCAFFOLD_DIR / args.target
        if target_abs.exists():
            content = target_abs.read_text(encoding="utf-8")
            critical = preflight.get("critical_sections", [])
            for section_name in critical:
                # Search for heading at any level
                pattern = rf"^#+\s+{re.escape(section_name)}\s*$"
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    # Check if section has content
                    idx = match.end()
                    next_heading = re.search(r"\n#+\s+", content[idx:])
                    if next_heading:
                        section_content = content[idx:idx + next_heading.start()]
                    else:
                        section_content = content[idx:]
                    cleaned = re.sub(r"<!--.*?-->", "", section_content, flags=re.DOTALL).strip()
                    if len(cleaned) < 10:
                        issues.append(f"Critical section '{section_name}' is empty or at template defaults")

    if issues:
        msg = preflight.get("blocked_message", "Document is too incomplete for review.")
        _output({"status": "blocked", "message": msg, "issues": issues})
        return

    # Check for sections to skip
    skip_sections = []
    if preflight.get("check_governance"):
        if args.target:
            target_abs = SCAFFOLD_DIR / args.target
            if target_abs.exists():
                content = target_abs.read_text(encoding="utf-8")
                for section_name in ["Design Invariants", "Decision Anchors"]:
                    match = re.search(rf"^#+\s+{re.escape(section_name)}", content, re.MULTILINE)
                    if not match:
                        skip_sections.append("## Philosophy")
                        break
                    else:
                        idx = match.end()
                        next_heading = re.search(r"\n#+\s+", content[idx:])
                        section_content = content[idx:idx + next_heading.start()] if next_heading else content[idx:]
                        cleaned = re.sub(r"<!--.*?-->", "", section_content, flags=re.DOTALL).strip()
                        if len(cleaned) < 20:
                            skip_sections.append("## Philosophy")
                            break

    result = {"status": "ready", "layer": args.layer}
    if args.target:
        result["target"] = args.target
    if skip_sections:
        result["skip_sections"] = list(set(skip_sections))
    _output(result)


# ---------------------------------------------------------------------------
# Next Action — Start or Resume Session
# ---------------------------------------------------------------------------

def cmd_next_action(args):
    """Determine the next action and write action.json."""
    config = load_layer_config(args.layer)
    if not config:
        _write_action({"action": "blocked", "message": f"No config for layer '{args.layer}'"})
        return

    target = args.target or config.get("target", "")
    session_id = _session_id(args.layer, target)
    session = _load_session(session_id)

    if not session:
        # Create new session
        session = _create_session(args, config, session_id, target)
        _save_session(session_id, session)

    # Determine next action based on session state
    _advance_and_write_action(session, config)


def _create_session(args, config, session_id, target):
    """Create a new review session."""
    # Build the review queue: L3 sections, L2 sections, L1
    queue = []

    # L3 pass
    l3 = config.get("l3_sections", {})
    if args.fast:
        # Batch by parent
        parents = {}
        for heading, defn in l3.items():
            if isinstance(defn, dict):
                parent = defn.get("parent", "")
                if parent not in parents:
                    parents[parent] = []
                parents[parent].append(heading)
        for parent, children in parents.items():
            queue.append({"pass": "l3", "section": parent, "subsections": children, "fast": True})
    else:
        for heading, defn in l3.items():
            if isinstance(defn, dict):
                queue.append({"pass": "l3", "section": heading, "parent": defn.get("parent", "")})

    # L3 apply
    queue.append({"pass": "l3_apply"})

    # L2 pass
    l2 = config.get("l2_sections", {})
    for heading, defn in l2.items():
        if isinstance(defn, dict):
            queue.append({"pass": "l2", "section": heading})

    # L2 apply
    queue.append({"pass": "l2_apply"})

    # L1 pass
    if config.get("l1_questions"):
        queue.append({"pass": "l1"})

    # L1 apply
    queue.append({"pass": "l1_apply"})

    # Report
    queue.append({"pass": "report"})

    # Filter by --sections if provided
    if args.sections:
        section_filter = [s.strip() for s in args.sections.split(",")]
        filtered = []
        for item in queue:
            if item["pass"] in ("l3_apply", "l2_apply", "l1_apply", "l1", "report"):
                filtered.append(item)
            elif item["pass"] == "l3":
                parent = item.get("parent", item.get("section", ""))
                parent_name = parent.replace("## ", "").strip()
                if parent_name in section_filter:
                    filtered.append(item)
            elif item["pass"] == "l2":
                section_name = item["section"].replace("## ", "").strip()
                if section_name in section_filter:
                    filtered.append(item)
        queue = filtered

    return {
        "session_id": session_id,
        "layer": args.layer,
        "target": target,
        "iteration": 1,
        "max_iterations": args.iterations or config.get("defaults", {}).get("max_iterations", 10),
        "max_exchanges": args.max_exchanges or config.get("defaults", {}).get("max_exchanges", 5),
        "focus": args.focus or "",
        "fast": args.fast or False,
        "reviewer": getattr(args, 'reviewer', 'doc'),
        "queue": queue,
        "queue_index": 0,
        "adjudications": [],
        "resolved_root_causes": [],
        "changes_pending": [],
        "changes_applied_total": 0,
        "created": datetime.now().isoformat(),
    }


def _rebuild_queue_for_verification(session, config):
    """Insert a verification pass into the queue — only re-reviews changed sections."""
    changed_sections = session.get("sections_with_changes", [])
    if not changed_sections:
        return

    session["iteration"] = session.get("iteration", 1) + 1
    session["passes_with_changes"] = []
    session["sections_with_changes"] = []  # Reset for next iteration

    queue = session.get("queue", [])
    current_idx = session.get("queue_index", 0)

    verification_items = []
    added_passes = set()

    # Re-queue the L3 subsections that had changes
    for original_item in queue[:current_idx]:
        if original_item.get("pass") == "l3":
            section = original_item.get("section", "")
            if section in changed_sections:
                verification_items.append(dict(original_item))
                added_passes.add("l3")

    # Blast radius expansion: also re-check sibling sections under the same parent
    # (e.g., change in ### Owned State should also re-verify ### Dependencies)
    changed_parents = set()
    for original_item in queue[:current_idx]:
        if original_item.get("pass") == "l3" and original_item.get("section", "") in changed_sections:
            parent = original_item.get("parent", "")
            if parent:
                changed_parents.add(parent)

    # Add sibling L3 sections from changed parents (if not already queued)
    queued_sections = set(changed_sections)
    linked_sections = config.get("linked_sections", {})
    for original_item in queue[:current_idx]:
        if original_item.get("pass") == "l3":
            section = original_item.get("section", "")
            parent = original_item.get("parent", "")
            if section not in queued_sections:
                # Include if: same parent as a changed section, OR explicitly linked
                in_changed_parent = parent in changed_parents
                explicitly_linked = any(
                    section in linked_sections.get(cs, [])
                    for cs in changed_sections
                )
                if in_changed_parent or explicitly_linked:
                    verification_items.append(dict(original_item))
                    queued_sections.add(section)
                    added_passes.add("l3")

    if "l3" in added_passes:
        verification_items.append({"pass": "l3_apply"})

    # Re-queue L2 parent sections of all affected L3 subsections
    for original_item in queue[:current_idx]:
        if original_item.get("pass") == "l2" and original_item.get("section", "") in changed_parents:
            verification_items.append(dict(original_item))
            added_passes.add("l2")

    if "l2" in added_passes:
        verification_items.append({"pass": "l2_apply"})

    # Always re-run L1 after verification (changes may affect document coherence)
    if config.get("l1_questions"):
        verification_items.append({"pass": "l1"})
        verification_items.append({"pass": "l1_apply"})

    verification_items.append({"pass": "report"})

    session["queue"] = queue[:current_idx] + verification_items
    session["queue_index"] = current_idx


def _advance_and_write_action(session, config):
    """Advance to the next queue item and write the appropriate action."""
    idx = session.get("queue_index", 0)
    queue = session.get("queue", [])

    if idx >= len(queue):
        _write_action({"action": "done", "session_id": session["session_id"]})
        return

    item = queue[idx]
    target = session["target"]
    target_abs = SCAFFOLD_DIR / target

    if item["pass"] in ("l3_apply", "l2_apply", "l1_apply"):
        # Apply action
        if session.get("changes_pending"):
            _write_action({
                "action": "apply",
                "session_id": session["session_id"],
                "target_file": target,
                "editable_files": _get_editable_files(config),
                "pass": item["pass"].replace("_apply", ""),
                "changes": session["changes_pending"],
            })
        else:
            # No changes to apply — skip
            session["queue_index"] = idx + 1
            _save_session(session["session_id"], session)
            _advance_and_write_action(session, config)
        return

    if item["pass"] == "report":
        _write_action({
            "action": "report",
            "session_id": session["session_id"],
            "layer": session["layer"],
            "target": target,
            "target_name": Path(target).stem,
            "iterations_completed": session.get("iteration", 1),
            "max_iterations": session.get("max_iterations", 10),
            "changes_applied": session.get("changes_applied_total", 0),
            "adjudications": session.get("adjudications", []),
            "escalations": [a for a in session.get("adjudications", []) if a.get("outcome") in ("escalate", "ambiguous_intent")],
            "resolved_root_causes": session.get("resolved_root_causes", []),
            "final_questions": config.get("report", {}).get("final_questions", []),
            "identity_check": config.get("identity_check"),
            "rating": config.get("report", {}).get("rating", {}),
            "log_name": _build_log_name(config, session),
            "log_path": f"scaffold/decisions/review/{_build_log_name(config, session)}",
        })
        return

    # Review action — need to call adversarial-review.py and get issues
    doc_content = target_abs.read_text(encoding="utf-8") if target_abs.exists() else ""

    if item["pass"] == "l3":
        section_heading = item["section"]
        if item.get("fast"):
            # Fast mode — extract full parent section
            section_content = _extract_section(doc_content, section_heading)
            questions = []
            for sub in item.get("subsections", []):
                sub_def = config.get("l3_sections", {}).get(sub, {})
                if isinstance(sub_def, dict):
                    questions.extend(sub_def.get("questions", []))
        else:
            section_content = _extract_section(doc_content, section_heading)
            section_def = config.get("l3_sections", {}).get(section_heading, {})
            questions = section_def.get("questions", []) if isinstance(section_def, dict) else []

    elif item["pass"] == "l2":
        section_heading = item["section"]
        section_content = _extract_section(doc_content, section_heading)
        section_def = config.get("l2_sections", {}).get(section_heading, {})
        questions = section_def.get("questions", []) if isinstance(section_def, dict) else []

    elif item["pass"] == "l1":
        section_content = doc_content
        questions = config.get("l1_questions", [])
        # Append identity check and bias pack
        identity = config.get("identity_check", {})
        if isinstance(identity, dict) and identity.get("questions"):
            questions = questions + [f"[Identity Check] {q}" for q in identity["questions"]]
        bias = config.get("bias_pack", [])
        if bias:
            questions.append("[Bias Pack] Check for these patterns: " +
                           "; ".join(b.get("name", "") + " — " + b.get("description", "")
                                     for b in bias if isinstance(b, dict)))
    else:
        section_content = ""
        questions = []

    if not section_content:
        # Section not found — skip
        session["queue_index"] = idx + 1
        _save_session(session["session_id"], session)
        _advance_and_write_action(session, config)
        return

    # Sleep between reviewer calls to avoid rate limits
    sleep_seconds = config.get("defaults", {}).get("sleep_between_topics", 10)
    if session.get("_reviewer_calls", 0) > 0 and sleep_seconds > 0:
        time.sleep(sleep_seconds)
    session["_reviewer_calls"] = session.get("_reviewer_calls", 0) + 1
    _save_session(session["session_id"], session)

    # Call adversarial-review.py for the review
    section_heading = item.get("section", "")
    context_files = resolve_context_files(config, target, section_heading)
    issues = _call_reviewer(session, config, section_content, questions, context_files)

    if not issues:
        # No issues — write no_issues action so dispatcher sees progress
        session["queue_index"] = idx + 1
        _save_session(session["session_id"], session)
        section_name = item.get("section", f"queue item {idx}")
        _write_action({
            "action": "no_issues",
            "session_id": session["session_id"],
            "pass": item.get("pass", ""),
            "section": section_name,
            "message": f"No issues found in {section_name}",
        })
        return

    # Filter through review lock
    filtered = []
    for issue in issues:
        root_cause = _extract_root_cause(issue)
        if root_cause and root_cause in session.get("resolved_root_causes", []):
            continue
        filtered.append(issue)

    if not filtered:
        # All issues filtered by review lock
        session["queue_index"] = idx + 1
        _save_session(session["session_id"], session)
        section_name = item.get("section", f"queue item {idx}")
        _write_action({
            "action": "no_issues",
            "session_id": session["session_id"],
            "pass": item.get("pass", ""),
            "section": section_name,
            "message": f"No new issues in {section_name} (all filtered by review lock)",
        })
        return

    # Categorize issues — mechanical issues auto-accept, others go to adjudicate
    auto_accept = []
    needs_adjudication = []
    for issue in filtered:
        severity = issue.get("severity", "MEDIUM").upper()
        suggestion = issue.get("suggestion", "")
        # Auto-accept: LOW severity with concrete suggestion (mechanical quality)
        # Also auto-accept: issues tagged as "mechanical" by reviewer
        if issue.get("category") == "mechanical" or (severity == "LOW" and suggestion):
            auto_accept.append(issue)
        else:
            needs_adjudication.append(issue)

    # Queue auto-accepted issues for direct apply (no adjudication round-trip)
    if auto_accept:
        session.setdefault("auto_accepted_issues", []).extend(auto_accept)

    if not needs_adjudication:
        # All issues were mechanical — skip straight to apply
        session["queue_index"] = idx + 1
        _save_session(session["session_id"], session)
        _advance_and_write_action(session, config)
        return

    # Store issues needing adjudication and write action for the first one
    session["current_issues"] = needs_adjudication
    session["current_issue_index"] = 0
    _save_session(session["session_id"], session)

    _write_adjudicate_action(session, config, needs_adjudication[0], section_content, item)


def _write_adjudicate_action(session, config, issue, section_content, queue_item):
    """Write an adjudicate action for one issue."""
    _write_action({
        "action": "adjudicate",
        "session_id": session["session_id"],
        "pass": queue_item["pass"],
        "section": queue_item["section"] if "section" in queue_item else "",
        "issue": issue,
        "section_content": section_content[:5000],  # Truncate for sanity
        "target_file": session["target"],
        "layer": session["layer"],
        "rules": config.get("rules", []),
        "context_summary": "",  # Could summarize context files here
        "resolved_root_causes": session.get("resolved_root_causes", []),
        "exchange_count": 0,
        "max_exchanges": session.get("max_exchanges", 5),
    })


# ---------------------------------------------------------------------------
# Resolve — Process Sub-Skill Result
# ---------------------------------------------------------------------------

def cmd_resolve(args):
    """Read result.json, process it, write next action.json."""
    session = _load_session(args.session)
    if not session:
        _write_action({"action": "blocked", "message": f"Session '{args.session}' not found."})
        return

    config = load_layer_config(session["layer"])
    result = _read_result()

    # Clean up result file
    if RESULT_FILE.exists():
        RESULT_FILE.unlink()

    # No result.json — this is valid after no_issues actions (no sub-skill ran)
    # Just advance to the next queue item
    if not result:
        _advance_and_write_action(session, config)
        return

    # Determine what to do based on the last action type
    queue = session.get("queue", [])
    idx = session.get("queue_index", 0)
    item = queue[idx] if idx < len(queue) else {}

    if item.get("pass") in ("l3_apply", "l2_apply", "l1_apply"):
        # Apply completed
        applied_count = result.get("applied", 0)
        session["changes_pending"] = []
        session["changes_applied_total"] = session.get("changes_applied_total", 0) + applied_count

        # Track changed pass levels and specific sections (for targeted verification)
        if applied_count > 0:
            changed_passes = session.get("passes_with_changes", [])
            pass_level = item["pass"].replace("_apply", "")
            if pass_level not in changed_passes:
                changed_passes.append(pass_level)
            session["passes_with_changes"] = changed_passes

            # Track which specific sections had changes applied
            changed_sections = session.get("sections_with_changes", [])
            for change in result.get("changes", []):
                section = change.get("section", "")
                if section and section not in changed_sections:
                    changed_sections.append(section)
            session["sections_with_changes"] = changed_sections

        session["queue_index"] = idx + 1
        _save_session(args.session, session)

        # Check if we just finished the last apply (l1_apply) and need verification
        next_idx = idx + 1
        next_item = queue[next_idx] if next_idx < len(queue) else {}
        if next_item.get("pass") == "report" and session.get("passes_with_changes"):
            # Changes were made — check if we should do a verification pass
            iteration = session.get("iteration", 1)
            max_iterations = session.get("max_iterations", 10)
            if iteration < max_iterations:
                # Rebuild queue for verification pass (only changed pass levels)
                _rebuild_queue_for_verification(session, config)
                _save_session(args.session, session)

        _advance_and_write_action(session, config)
        return

    if item.get("pass") == "report":
        # Report completed — done
        session["queue_index"] = idx + 1
        _save_session(args.session, session)
        _write_action({
            "action": "done",
            "session_id": session["session_id"],
            "report_summary": result.get("report_summary", ""),
        })
        return

    # Scope-check result — came back from scope-check sub-skill
    if result.get("overall") in ("pass", "fail"):
        issues = session.get("current_issues", [])
        issue_idx = session.get("current_issue_index", 0)
        issue = issues[issue_idx] if issue_idx < len(issues) else {}

        if result["overall"] == "pass":
            # Scope passed — confirm the accept
            outcome = "accept"
            reasoning = session.get("_pending_accept_reasoning", "")
            fix_desc = session.get("_pending_accept_fix", "")
        else:
            # Scope failed — convert to reject
            outcome = "reject"
            reasoning = f"Scope guard failed: {result.get('tests', [])}"
            fix_desc = ""

        adjudication = {
            "pass": item.get("pass", ""),
            "section": item.get("section", ""),
            "issue": issue,
            "outcome": outcome,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
        }
        session["adjudications"].append(adjudication)

        if outcome == "accept":
            session["changes_pending"].append({
                "section": item.get("section", ""),
                "fix_description": fix_desc,
                "issue_description": issue.get("description", ""),
                "severity": issue.get("severity", "MEDIUM"),
            })

        if outcome in ("accept", "reject"):
            root_cause = _extract_root_cause(issue)
            if root_cause and root_cause not in session["resolved_root_causes"]:
                session["resolved_root_causes"].append(root_cause)

        # Clean up pending accept state
        session.pop("_pending_accept_reasoning", None)
        session.pop("_pending_accept_fix", None)

        # Advance to next issue or next queue item
        session["current_issue_index"] = issue_idx + 1
        _save_session(args.session, session)

        if issue_idx + 1 < len(issues):
            next_issue = issues[issue_idx + 1]
            target_abs = SCAFFOLD_DIR / session["target"]
            doc_content = target_abs.read_text(encoding="utf-8") if target_abs.exists() else ""
            section_content = _extract_section(doc_content, item.get("section", "")) or ""
            _write_adjudicate_action(session, config, next_issue, section_content, item)
        else:
            session["queue_index"] = idx + 1
            _save_session(args.session, session)
            _advance_and_write_action(session, config)
        return

    # Adjudication result
    outcome = result.get("outcome", "")

    if outcome in ("accept", "reject", "escalate", "ambiguous_intent"):
        issues = session.get("current_issues", [])
        issue_idx = session.get("current_issue_index", 0)
        issue = issues[issue_idx] if issue_idx < len(issues) else {}

        # If accept, decide whether scope-check is needed
        if outcome == "accept":
            scope_guard = config.get("scope_guard", {})
            scope_tests = scope_guard.get("tests", [])

            # Skip scope-check for quality-only issues (no cross-doc impact)
            # Only run scope-check when the change touches ownership, authority,
            # contracts, architecture, or cross-system boundaries
            severity = issue.get("severity", "MEDIUM").upper()
            desc_lower = (issue.get("description", "") + " " + result.get("fix_description", "")).lower()
            needs_scope_check = scope_tests and any(
                kw in desc_lower
                for kw in ("ownership", "authority", "contract", "interface",
                           "architecture", "cross-system", "cross-doc", "upstream",
                           "another system", "owned by", "violat")
            )
            # Always scope-check CRITICAL severity
            if severity == "CRITICAL":
                needs_scope_check = bool(scope_tests)

            if needs_scope_check:
                # Stash the accept details and route to scope check
                session["_pending_accept_reasoning"] = result.get("reasoning", "")
                session["_pending_accept_fix"] = result.get("fix_description", "")
                _save_session(args.session, session)
                _write_action({
                    "action": "scope_check",
                    "session_id": session["session_id"],
                    "layer": session["layer"],
                    "change_description": issue.get("description", ""),
                    "fix_description": result.get("fix_description", ""),
                    "section": item.get("section", ""),
                    "scope_guard": scope_guard,
                })
                return
            # else: no scope check needed — accept directly

        # Record adjudication (for non-accept, or accept with no scope tests)
        adjudication = {
            "pass": item.get("pass", ""),
            "section": item.get("section", ""),
            "issue": issue,
            "outcome": outcome,
            "reasoning": result.get("reasoning", ""),
            "timestamp": datetime.now().isoformat(),
        }
        session["adjudications"].append(adjudication)

        # Queue change if accepted (no scope tests case)
        if outcome == "accept":
            session["changes_pending"].append({
                "section": item.get("section", ""),
                "fix_description": result.get("fix_description", ""),
                "issue_description": issue.get("description", ""),
                "severity": issue.get("severity", "MEDIUM"),
            })

        # Lock root cause if accepted or rejected
        if outcome in ("accept", "reject"):
            root_cause = _extract_root_cause(issue)
            if root_cause and root_cause not in session["resolved_root_causes"]:
                session["resolved_root_causes"].append(root_cause)

        # Advance to next issue or next queue item
        session["current_issue_index"] = issue_idx + 1
        _save_session(args.session, session)

        if issue_idx + 1 < len(issues):
            # More issues — write adjudicate for next one
            next_issue = issues[issue_idx + 1]
            target_abs = SCAFFOLD_DIR / session["target"]
            doc_content = target_abs.read_text(encoding="utf-8") if target_abs.exists() else ""
            section_content = _extract_section(doc_content, item.get("section", "")) or ""
            _write_adjudicate_action(session, config, next_issue, section_content, item)
        else:
            # All issues adjudicated — advance queue
            session["queue_index"] = idx + 1
            _save_session(args.session, session)
            _advance_and_write_action(session, config)
        return

    if outcome == "pushback":
        # Send counter-argument to reviewer, get response
        counter = result.get("counter_argument", "")
        response = _send_pushback(session, config, counter)

        if response:
            # Re-present the issue with the reviewer's counter-response
            issues = session.get("current_issues", [])
            issue_idx = session.get("current_issue_index", 0)
            issue = issues[issue_idx] if issue_idx < len(issues) else {}
            # Append reviewer's response to the issue
            issue["reviewer_counter"] = response
            session["current_issues"][issue_idx] = issue
            session["exchange_count"] = session.get("exchange_count", 0) + 1
            _save_session(args.session, session)

            target_abs = SCAFFOLD_DIR / session["target"]
            doc_content = target_abs.read_text(encoding="utf-8") if target_abs.exists() else ""
            section_content = _extract_section(doc_content, item.get("section", "")) or ""

            action = {
                "action": "adjudicate",
                "session_id": session["session_id"],
                "pass": item.get("pass", ""),
                "section": item.get("section", ""),
                "issue": issue,
                "section_content": section_content[:5000],
                "target_file": session["target"],
                "layer": session["layer"],
                "rules": config.get("rules", []),
                "context_summary": "",
                "resolved_root_causes": session.get("resolved_root_causes", []),
                "exchange_count": session.get("exchange_count", 0),
                "max_exchanges": session.get("max_exchanges", 5),
            }
            _write_action(action)
        else:
            # Pushback failed — escalate
            session["current_issue_index"] = session.get("current_issue_index", 0) + 1
            _save_session(args.session, session)
            _advance_and_write_action(session, config)
        return

    # Scope check pass — now write the accept adjudication prompt
    if result.get("overall") == "pass":
        # Scope passed — the issue was pre-accepted, now formally accept
        # The dispatcher should have already routed back to adjudicate
        pass

    # Unknown result — advance
    session["queue_index"] = idx + 1
    _save_session(args.session, session)
    _advance_and_write_action(session, config)


# ---------------------------------------------------------------------------
# Reviewer Interaction
# ---------------------------------------------------------------------------

def _call_reviewer(session, config, section_content, questions, context_files):
    """Call the appropriate reviewer script and return issues list."""
    # Select reviewer script
    reviewer = session.get("reviewer", "doc")
    if reviewer == "code":
        review_script = CODE_REVIEW_SCRIPT
    else:
        review_script = DOC_REVIEW_SCRIPT

    # Build prompt with questions
    prompt_parts = ["Review the following section:\n", section_content, "\n\nEvaluate against these questions:\n"]
    for q in questions:
        prompt_parts.append(f"- {q}\n")

    focus = session.get("focus", "")
    if focus:
        prompt_parts.append(f"\nFOCUS: Concentrate on: {focus}\n")

    prompt_text = "".join(prompt_parts)

    # Write prompt to temp file
    prompt_file = REVIEWS_DIR / f"prompt-{session['session_id']}.md"
    prompt_file.write_text(prompt_text, encoding="utf-8")

    target_abs = SCAFFOLD_DIR / session["target"]
    cmd = [
        sys.executable, str(review_script),
        "review", str(target_abs),
        "--iteration", str(session.get("iteration", 1)),
        "--system-prompt-file", str(prompt_file),
    ]
    if context_files:
        cmd.extend(["--context-files"] + context_files)

    result = _run_doc_review(cmd)

    # Clean up prompt file
    if prompt_file.exists():
        prompt_file.unlink()

    if "error" in result:
        return []

    return result.get("issues", [])


def _send_pushback(session, config, counter_argument):
    """Send pushback to reviewer, return their response."""
    reviewer = session.get("reviewer", "doc")
    review_script = CODE_REVIEW_SCRIPT if reviewer == "code" else DOC_REVIEW_SCRIPT

    msg_file = REVIEWS_DIR / f"pushback-{session['session_id']}.md"
    msg_file.write_text(counter_argument, encoding="utf-8")

    target_abs = SCAFFOLD_DIR / session["target"]
    cmd = [
        sys.executable, str(review_script),
        "respond", str(target_abs),
        "--iteration", str(session.get("iteration", 1)),
        "--message-file", str(msg_file),
    ]

    result = _run_doc_review(cmd)

    if msg_file.exists():
        msg_file.unlink()

    if "error" in result:
        return None

    return result.get("content", result.get("response", ""))


def _run_doc_review(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(SCAFFOLD_DIR))
        stdout = result.stdout.strip()
        if not stdout:
            return {"error": result.stderr.strip() if result.stderr else "No output"}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            for line in stdout.splitlines():
                if line.strip().startswith("{"):
                    try:
                        return json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
            return {"error": "Failed to parse output", "raw": stdout[:500]}
    except subprocess.TimeoutExpired:
        return {"error": "Timed out after 300s"}
    except FileNotFoundError:
        return {"error": f"Reviewer script not found"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_root_cause(issue):
    """Extract a structured root cause tag for deduplication.

    Prefers explicit root_cause field from the reviewer (structured tag like
    'purpose_is_generic' or 'ownership_conflict_with_SYS-003'). Falls back to
    section + normalized first 8 words of description as a stable key.

    The reviewer prompt asks for root_cause tags. When the reviewer provides
    them, deduplication is exact. When it doesn't, the fallback is coarse
    but stable — same section + same opening words = same root cause."""
    if isinstance(issue, dict):
        # Prefer explicit tag from reviewer
        tag = issue.get("root_cause", "")
        if tag:
            return tag.lower().strip()

        # Fallback: section + first 8 words of description (stable, coarse)
        section = issue.get("section", "unknown")
        desc = issue.get("description", "")
        words = re.sub(r"[^a-z0-9\s]", "", desc.lower()).split()[:8]
        return f"{section}:{'_'.join(words)}" if words else section
    return str(issue).lower().strip()


def _get_editable_files(config):
    adj = config.get("adjudication", {})
    files = adj.get("editable_files", [])
    if not files:
        pattern = adj.get("editable_files_pattern", "")
        if pattern:
            files = [str(p.relative_to(SCAFFOLD_DIR)) for p in SCAFFOLD_DIR.glob(pattern)]
    return files


def _build_log_name(config, session):
    report_config = config.get("report", {})
    pattern = report_config.get("log_name_pattern", f"ITERATE-{session['layer']}-{{date}}.md")
    today = datetime.now().strftime("%Y-%m-%d")
    target_stem = Path(session["target"]).stem
    return pattern.format(date=today, target=target_stem)


def _output(data):
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Iterate orchestrator")
    subparsers = parser.add_subparsers(dest="command")

    # preflight
    p_pre = subparsers.add_parser("preflight")
    p_pre.add_argument("--layer", required=True)
    p_pre.add_argument("--target", default="")

    # next-action
    p_next = subparsers.add_parser("next-action")
    p_next.add_argument("--layer", required=True)
    p_next.add_argument("--target", default="")
    p_next.add_argument("--iterations", type=int, default=None)
    p_next.add_argument("--max-exchanges", type=int, default=None)
    p_next.add_argument("--focus", default="")
    p_next.add_argument("--sections", default="")
    p_next.add_argument("--signals", default="")
    p_next.add_argument("--fast", action="store_true")
    p_next.add_argument("--reviewer", default="doc", choices=["doc", "code"],
                       help="Which reviewer to use: doc (adversarial-review.py) or code (code-review.py)")

    # resolve
    p_res = subparsers.add_parser("resolve")
    p_res.add_argument("--session", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "preflight": cmd_preflight,
        "next-action": cmd_next_action,
        "resolve": cmd_resolve,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
