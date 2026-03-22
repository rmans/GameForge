#!/usr/bin/env python3
"""
Iterate orchestrator — manages adversarial review sessions for scaffold documents.

Coordinates between Claude (adjudicator) and doc-review.py (external LLM reviewer).
Handles one document at a time. The calling skill handles range loops.

Commands:
    preflight    Check if a layer is ready for review.
    start        Begin a topic review — calls doc-review.py, returns first issue.
    adjudicate   Record Claude's decision on an issue, return next issue.
    respond      Send pushback to the reviewer, return their counter-argument.
    scope-check  Run mechanical scope guard tests on a proposed change.
    apply        Apply all accepted fixes for the current session.
    convergence  Check if another iteration is needed.
    report       Generate the review log and report summary.

Session state is saved to .reviews/iterate/ so commands can be called sequentially.
No pip dependencies — uses Python standard library only.
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
DOC_REVIEW_SCRIPT = TOOLS_DIR / "doc-review.py"


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
    # Strip quotes
    if (val.startswith('"') and val.endswith('"')) or \
       (val.startswith("'") and val.endswith("'")):
        return val[1:-1]
    return val


def _count_indent(line):
    """Count leading spaces."""
    return len(line) - len(line.lstrip())


def load_yaml(path):
    """Minimal YAML loader supporting nested dicts, lists, and scalars.

    Handles the subset of YAML used by iterate configs:
    - Key: value pairs
    - Nested dicts (indented)
    - Lists with - prefix
    - Multi-line strings are not supported (use single-line values)
    - Inline lists [a, b, c] are supported
    - Comments with #
    """
    path = Path(path)
    if not path.exists():
        return None

    lines = path.read_text(encoding="utf-8").splitlines()
    return _parse_yaml_block(lines, 0, 0)[0]


def _parse_yaml_block(lines, start, base_indent):
    """Parse a YAML block starting at the given line and indent level.
    Returns (parsed_dict_or_list, next_line_index).
    """
    result = {}
    i = start
    is_list = False
    result_list = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = _count_indent(line)

        # If we've dedented past our block, we're done
        if indent < base_indent:
            break

        # If this is at our indent level
        if indent == base_indent:
            # List item
            if stripped.startswith("- "):
                is_list = True
                item_text = stripped[2:].strip()

                # Check if list item is a key: value (dict in list)
                if ":" in item_text and not item_text.startswith('"'):
                    colon_pos = item_text.index(":")
                    key = item_text[:colon_pos].strip()
                    val_text = item_text[colon_pos + 1:].strip()

                    if val_text:
                        item_dict = {key: _parse_yaml_value(val_text)}
                    else:
                        item_dict = {key: None}

                    # Check for continuation lines at deeper indent
                    next_i = i + 1
                    if next_i < len(lines):
                        next_stripped = lines[next_i].strip()
                        next_indent = _count_indent(lines[next_i]) if next_stripped else 0
                        if next_stripped and next_indent > indent:
                            child, next_i = _parse_yaml_block(lines, next_i, next_indent)
                            if val_text:
                                item_dict[key] = _parse_yaml_value(val_text)
                            else:
                                item_dict[key] = child
                            # Merge any sibling keys from continuation
                            if isinstance(child, dict) and not val_text:
                                item_dict[key] = child
                            i = next_i
                            result_list.append(item_dict)
                            continue

                    i += 1
                    result_list.append(item_dict)
                    continue
                else:
                    # Simple list item (scalar)
                    result_list.append(_parse_yaml_value(item_text))
                    i += 1
                    continue

            # Key: value pair
            if ":" in stripped:
                colon_pos = stripped.index(":")
                key = stripped[:colon_pos].strip()
                val_text = stripped[colon_pos + 1:].strip()

                # Handle inline lists [a, b, c]
                if val_text.startswith("[") and val_text.endswith("]"):
                    inner = val_text[1:-1]
                    if inner.strip():
                        items = [_parse_yaml_value(x.strip()) for x in inner.split(",")]
                    else:
                        items = []
                    result[key] = items
                    i += 1
                    continue

                # Value on the same line
                if val_text:
                    result[key] = _parse_yaml_value(val_text)
                    i += 1
                    continue

                # Value on next lines (nested block)
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

        # Indented beyond our level — shouldn't happen at top level
        i += 1

    if is_list:
        return result_list, i
    return result, i


# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------

def _session_id(layer, target, topic=None, iteration=None):
    """Generate a deterministic session ID."""
    key = f"{layer}:{target}"
    h = hashlib.md5(key.encode()).hexdigest()[:8]
    name = Path(target).stem if target else layer
    return f"iter-{name}-{h}"


def _session_path(session_id):
    """Path to session state file."""
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    return REVIEWS_DIR / f"{session_id}.json"


def _load_session(session_id):
    """Load session state."""
    path = _session_path(session_id)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_session(session_id, data):
    """Save session state."""
    path = _session_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Config Loading
# ---------------------------------------------------------------------------

def load_layer_config(layer):
    """Load the YAML config for a layer."""
    config_path = CONFIGS_DIR / f"{layer}.yaml"
    if not config_path.exists():
        return None
    return load_yaml(config_path)


# ---------------------------------------------------------------------------
# Context File Resolution
# ---------------------------------------------------------------------------

def resolve_context_files(config, target_path):
    """Resolve the list of context files for a review.

    Returns list of absolute paths that exist.
    """
    files = []

    # Static context files
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

    # Dynamic context files (glob patterns with optional filters)
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
                    # Apply filter if specified (e.g., "status: Accepted")
                    filter_str = entry.get("filter", "")
                    if filter_str and match.exists():
                        content = match.read_text(encoding="utf-8")
                        if filter_str not in content:
                            continue
                    files.append(str(match))
        elif isinstance(entry, str):
            abs_path = SCAFFOLD_DIR / entry
            if abs_path.exists():
                files.append(str(abs_path))

    # Always include the target itself
    target_abs = SCAFFOLD_DIR / target_path if not Path(target_path).is_absolute() else Path(target_path)
    if target_abs.exists() and str(target_abs) not in files:
        files.insert(0, str(target_abs))

    return files


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

def cmd_preflight(args):
    """Check if a layer is ready for review."""
    config = load_layer_config(args.layer)
    if not config:
        _output({"status": "error", "message": f"No config found for layer '{args.layer}'"})
        return

    preflight = config.get("preflight", {})
    required = preflight.get("required_files", [])
    issues = []

    # Check required files exist
    for rel_path in required:
        abs_path = SCAFFOLD_DIR / rel_path
        if not abs_path.exists():
            issues.append(f"Required file missing: {rel_path}")

    if issues:
        msg = preflight.get("blocked_message", "Preflight failed.")
        _output({"status": "blocked", "message": msg, "issues": issues})
        return

    # Check minimum content percentage
    min_pct = preflight.get("min_content_pct", 0)
    if min_pct > 0:
        target = config.get("target", "")
        if target:
            abs_target = SCAFFOLD_DIR / target
            if abs_target.exists():
                content = abs_target.read_text(encoding="utf-8")
                # Count non-empty, non-comment sections
                sections = re.findall(r"^## .+", content, re.MULTILINE)
                filled = 0
                for section_match in sections:
                    # Find content between this heading and the next
                    idx = content.index(section_match)
                    next_heading = re.search(r"\n## ", content[idx + len(section_match):])
                    if next_heading:
                        section_content = content[idx + len(section_match):idx + len(section_match) + next_heading.start()]
                    else:
                        section_content = content[idx + len(section_match):]
                    # Check if section has real content (not just template placeholders)
                    cleaned = re.sub(r"<!--.*?-->", "", section_content, flags=re.DOTALL).strip()
                    if len(cleaned) > 20:
                        filled += 1
                if sections:
                    pct = (filled / len(sections)) * 100
                    if pct < min_pct:
                        msg = preflight.get("incomplete_message", f"Document is only {pct:.0f}% complete.")
                        _output({"status": "blocked", "message": msg, "content_pct": pct})
                        return

    # Check governance readiness
    skip_topics = []
    if preflight.get("check_governance"):
        target = config.get("target", "")
        if target:
            abs_target = SCAFFOLD_DIR / target
            if abs_target.exists():
                content = abs_target.read_text(encoding="utf-8")
                governance_sections = ["Design Invariants", "Decision Anchors"]
                governance_empty = True
                for section_name in governance_sections:
                    pattern = rf"## .*{re.escape(section_name)}"
                    match = re.search(pattern, content)
                    if match:
                        idx = match.end()
                        next_heading = re.search(r"\n## ", content[idx:])
                        if next_heading:
                            section_content = content[idx:idx + next_heading.start()]
                        else:
                            section_content = content[idx:]
                        cleaned = re.sub(r"<!--.*?-->", "", section_content, flags=re.DOTALL).strip()
                        if len(cleaned) > 20:
                            governance_empty = False
                            break
                if governance_empty:
                    # Find which topic to skip
                    topics = config.get("topics", {})
                    for tid, tdef in topics.items():
                        if isinstance(tdef, dict) and tdef.get("skip_if") == "governance_empty":
                            skip_topics.append(int(tid))

    result = {"status": "ready", "layer": args.layer}
    if skip_topics:
        result["skip_topics"] = skip_topics
        result["note"] = f"Topics {skip_topics} will be skipped — governance sections are empty."
    _output(result)


# ---------------------------------------------------------------------------
# Start — Begin a Topic Review
# ---------------------------------------------------------------------------

def cmd_start(args):
    """Start a topic review. Calls doc-review.py, returns first issue."""
    config = load_layer_config(args.layer)
    if not config:
        _output({"status": "error", "message": f"No config found for layer '{args.layer}'"})
        return

    target = args.target or config.get("target", "")
    if not target:
        _output({"status": "error", "message": "No target specified and layer has no default target."})
        return

    # Generate or reuse session
    session_id = _session_id(args.layer, target)
    session = _load_session(session_id)

    if not session:
        session = {
            "session_id": session_id,
            "layer": args.layer,
            "target": target,
            "iteration": args.iteration,
            "topic": args.topic,
            "max_iterations": args.iterations or config.get("defaults", {}).get("max_iterations", 10),
            "max_exchanges": args.max_exchanges or config.get("defaults", {}).get("max_exchanges", 5),
            "focus": args.focus or "",
            "issues": [],
            "current_issue_idx": 0,
            "adjudications": [],
            "resolved_root_causes": [],
            "exchanges": 0,
            "topics_completed": [],
            "iterations_completed": 0,
            "changes_to_apply": [],
            "created": datetime.now().isoformat(),
        }

    # Update session for this topic/iteration
    session["topic"] = args.topic
    session["iteration"] = args.iteration
    session["current_issue_idx"] = 0
    session["exchanges"] = 0

    # Build context files
    context_files = resolve_context_files(config, target)

    # Build the topic prompt
    topics = config.get("topics", {})
    topic_def = topics.get(str(args.topic)) or topics.get(args.topic)
    if not topic_def:
        _output({"status": "error", "message": f"Topic {args.topic} not found in {args.layer} config."})
        return

    # Build system prompt with topic criteria
    topic_prompt = _build_topic_prompt(config, topic_def, args.focus)

    # Call doc-review.py
    target_abs = SCAFFOLD_DIR / target
    cmd = [
        sys.executable, str(DOC_REVIEW_SCRIPT),
        "review", str(target_abs),
        "--iteration", str(args.iteration),
    ]
    if context_files:
        cmd.extend(["--context-files"] + context_files)
    if args.focus:
        cmd.extend(["--focus", args.focus])

    # Write topic prompt to a temp file for doc-review.py to use
    topic_prompt_file = REVIEWS_DIR / f"{session_id}-topic-prompt.md"
    topic_prompt_file.parent.mkdir(parents=True, exist_ok=True)
    topic_prompt_file.write_text(topic_prompt, encoding="utf-8")
    cmd.extend(["--system-prompt-file", str(topic_prompt_file)])

    result = _run_doc_review(cmd)

    if "error" in result:
        session["last_error"] = result["error"]
        _save_session(session_id, session)
        _output({"status": "error", "session": session_id, "message": result["error"],
                 "fallback": result.get("fallback")})
        return

    # Extract issues
    issues = result.get("issues", [])

    # Filter through review lock
    filtered_issues = []
    for issue in issues:
        root_cause = _extract_root_cause(issue)
        if root_cause and root_cause in session.get("resolved_root_causes", []):
            # Skip — already resolved
            continue
        filtered_issues.append(issue)

    session["issues"] = filtered_issues
    session["current_issue_idx"] = 0
    session["review_summary"] = result.get("summary", "")
    _save_session(session_id, session)

    # Return first issue or indicate no issues
    if filtered_issues:
        issue = filtered_issues[0]
        topic_name = topic_def.get("name", f"Topic {args.topic}") if isinstance(topic_def, dict) else f"Topic {args.topic}"
        _output({
            "status": "issue",
            "session": session_id,
            "topic": args.topic,
            "topic_name": topic_name,
            "iteration": args.iteration,
            "summary": result.get("summary", ""),
            "issue": issue,
            "issue_index": 0,
            "remaining": len(filtered_issues) - 1,
            "total_issues": len(filtered_issues),
        })
    else:
        topic_name = topic_def.get("name", f"Topic {args.topic}") if isinstance(topic_def, dict) else f"Topic {args.topic}"
        session["topics_completed"].append(args.topic)
        _save_session(session_id, session)
        _output({
            "status": "clean",
            "session": session_id,
            "topic": args.topic,
            "topic_name": topic_name,
            "iteration": args.iteration,
            "summary": result.get("summary", "No issues found."),
            "total_issues": 0,
        })


def _build_topic_prompt(config, topic_def, focus=""):
    """Build a focused prompt for a specific topic."""
    if not isinstance(topic_def, dict):
        return ""

    parts = []
    name = topic_def.get("name", "Review Topic")
    core_q = topic_def.get("core_question", "")
    mode = topic_def.get("mode", "structural")

    parts.append(f"# Review Topic: {name}")
    parts.append(f"Mode: {mode}")
    if core_q:
        parts.append(f"\nCore question: *{core_q}*")

    # Reviewer instruction override (e.g., for stress test topics)
    if topic_def.get("reviewer_instruction"):
        parts.append(f"\n**Reviewer instruction:** {topic_def['reviewer_instruction']}")

    # Criteria
    criteria = topic_def.get("criteria", [])
    if criteria:
        parts.append("\n## Evaluation Criteria\n")
        for c in criteria:
            if isinstance(c, dict):
                parts.append(f"### {c.get('name', 'Criterion')}")
                parts.append(c.get("prompt", ""))
                parts.append("")
            elif isinstance(c, str):
                parts.append(f"- {c}")

    # Bias pack
    bias_pack = config.get("bias_pack")
    if bias_pack:
        parts.append("\n## Detection Patterns (Bias Pack)\n")
        if isinstance(bias_pack, list):
            for bp in bias_pack:
                if isinstance(bp, dict):
                    parts.append(f"- **{bp.get('name', '')}**: {bp.get('description', '')}")
                elif isinstance(bp, str):
                    parts.append(f"- {bp}")

    # Focus
    if focus:
        parts.append(f"\n## Review Focus\nConcentrate on: {focus}")
        parts.append("Only flag issues outside the focus area if they are HIGH severity.")

    # Rules from config
    rules = config.get("rules", [])
    if rules:
        parts.append("\n## Rules\n")
        for rule in rules:
            if isinstance(rule, str):
                parts.append(f"- {rule}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Adjudicate — Record Decision, Return Next Issue
# ---------------------------------------------------------------------------

def cmd_adjudicate(args):
    """Record Claude's decision on the current issue, return next issue."""
    session = _load_session(args.session)
    if not session:
        _output({"status": "error", "message": f"Session '{args.session}' not found."})
        return

    issues = session.get("issues", [])
    idx = session.get("current_issue_idx", 0)

    if idx >= len(issues):
        _output({"status": "error", "message": "No current issue to adjudicate."})
        return

    current_issue = issues[idx]

    # Record adjudication
    adjudication = {
        "issue_index": idx,
        "issue": current_issue,
        "outcome": args.outcome,
        "reasoning": args.reasoning or "",
        "topic": session.get("topic"),
        "iteration": session.get("iteration"),
        "timestamp": datetime.now().isoformat(),
    }

    session["adjudications"].append(adjudication)

    # If accepted, queue the change
    if args.outcome == "accept":
        session["changes_to_apply"].append({
            "issue": current_issue,
            "reasoning": args.reasoning or "",
        })

    # If accepted or rejected, lock the root cause
    if args.outcome in ("accept", "reject"):
        root_cause = _extract_root_cause(current_issue)
        if root_cause and root_cause not in session["resolved_root_causes"]:
            session["resolved_root_causes"].append(root_cause)

    # Advance to next issue
    session["current_issue_idx"] = idx + 1
    _save_session(args.session, session)

    # Return next issue or indicate topic complete
    if idx + 1 < len(issues):
        next_issue = issues[idx + 1]
        _output({
            "status": "issue",
            "session": args.session,
            "issue": next_issue,
            "issue_index": idx + 1,
            "remaining": len(issues) - (idx + 2),
            "total_issues": len(issues),
        })
    else:
        topic = session.get("topic")
        if topic not in session.get("topics_completed", []):
            session["topics_completed"].append(topic)
            _save_session(args.session, session)

        # Tally for this topic
        topic_adj = [a for a in session["adjudications"] if a.get("topic") == topic]
        accepted = sum(1 for a in topic_adj if a["outcome"] == "accept")
        rejected = sum(1 for a in topic_adj if a["outcome"] == "reject")
        escalated = sum(1 for a in topic_adj if a["outcome"] == "escalate")
        ambiguous = sum(1 for a in topic_adj if a["outcome"] == "ambiguous_intent")

        _output({
            "status": "topic_complete",
            "session": args.session,
            "topic": topic,
            "summary": {
                "total": len(topic_adj),
                "accepted": accepted,
                "rejected": rejected,
                "escalated": escalated,
                "ambiguous": ambiguous,
            },
        })


# ---------------------------------------------------------------------------
# Respond — Send Pushback to Reviewer
# ---------------------------------------------------------------------------

def cmd_respond(args):
    """Send Claude's pushback to the reviewer, return their counter-argument."""
    session = _load_session(args.session)
    if not session:
        _output({"status": "error", "message": f"Session '{args.session}' not found."})
        return

    max_exchanges = session.get("max_exchanges", 5)
    exchanges = session.get("exchanges", 0)

    if exchanges >= max_exchanges:
        _output({
            "status": "max_exchanges",
            "session": args.session,
            "message": f"Max exchanges ({max_exchanges}) reached. Escalate or adjudicate.",
            "exchanges": exchanges,
        })
        return

    # Read the message from file
    message = ""
    if args.message_file:
        msg_path = Path(args.message_file)
        if msg_path.exists():
            message = msg_path.read_text(encoding="utf-8")
    if not message and args.message:
        message = args.message

    if not message:
        _output({"status": "error", "message": "No message provided for respond."})
        return

    # Call doc-review.py respond
    target_abs = SCAFFOLD_DIR / session["target"]
    cmd = [
        sys.executable, str(DOC_REVIEW_SCRIPT),
        "respond", str(target_abs),
        "--iteration", str(session.get("iteration", 1)),
        "--message-file", str(args.message_file) if args.message_file else "",
    ]

    # If message was inline, write to temp file
    if not args.message_file and message:
        temp_msg = REVIEWS_DIR / f"{args.session}-pushback.md"
        temp_msg.write_text(message, encoding="utf-8")
        cmd[-1] = str(temp_msg)

    result = _run_doc_review(cmd)

    session["exchanges"] = exchanges + 1
    _save_session(args.session, session)

    if "error" in result:
        _output({"status": "error", "session": args.session, "message": result["error"]})
        return

    _output({
        "status": "response",
        "session": args.session,
        "response": result.get("content", result.get("response", str(result))),
        "exchange": exchanges + 1,
        "max_exchanges": max_exchanges,
    })


# ---------------------------------------------------------------------------
# Scope Check — Mechanical Guard Tests
# ---------------------------------------------------------------------------

def cmd_scope_check(args):
    """Run scope guard tests on a proposed change."""
    session = _load_session(args.session)
    if not session:
        _output({"status": "error", "message": f"Session '{args.session}' not found."})
        return

    config = load_layer_config(session["layer"])
    if not config:
        _output({"status": "error", "message": f"No config for layer '{session['layer']}'"})
        return

    scope_guard = config.get("scope_guard", {})
    tests = scope_guard.get("tests", [])
    change = args.change

    results = []
    all_pass = True

    for test in tests:
        if isinstance(test, dict):
            test_name = test.get("name", "unnamed")
            question = test.get("question", "")
            guidance = test.get("guidance", "")
            # These are prompts for Claude to evaluate — return them for judgment
            results.append({
                "test": test_name,
                "question": question,
                "guidance": guidance,
            })
        elif isinstance(test, str):
            results.append({"test": test, "question": test})

    # The scope guard tests are judgment calls — return them for Claude to evaluate
    _output({
        "status": "scope_check",
        "session": args.session,
        "change": change,
        "tests": results,
        "upward": scope_guard.get("upward"),
        "downward": scope_guard.get("downward"),
    })


# ---------------------------------------------------------------------------
# Apply — Apply Accepted Fixes
# ---------------------------------------------------------------------------

def cmd_apply(args):
    """Apply all accepted fixes for the current session."""
    session = _load_session(args.session)
    if not session:
        _output({"status": "error", "message": f"Session '{args.session}' not found."})
        return

    changes = session.get("changes_to_apply", [])
    if not changes:
        _output({
            "status": "no_changes",
            "session": args.session,
            "message": "No accepted changes to apply.",
        })
        return

    # Return the changes for Claude to apply (Claude has file editing capability)
    _output({
        "status": "apply",
        "session": args.session,
        "changes": changes,
        "target": session["target"],
        "count": len(changes),
    })

    # Clear the queue after reporting
    session["changes_to_apply"] = []
    session["changes_applied"] = session.get("changes_applied", 0) + len(changes)
    _save_session(args.session, session)


# ---------------------------------------------------------------------------
# Convergence — Check If Another Iteration Needed
# ---------------------------------------------------------------------------

def cmd_convergence(args):
    """Check if another iteration is needed."""
    session = _load_session(args.session)
    if not session:
        _output({"status": "error", "message": f"Session '{args.session}' not found."})
        return

    iteration = session.get("iteration", 1)
    max_iterations = session.get("max_iterations", 10)

    # Count what happened this iteration
    iter_adj = [a for a in session.get("adjudications", [])
                if a.get("iteration") == iteration]
    accepted = sum(1 for a in iter_adj if a["outcome"] == "accept")
    rejected = sum(1 for a in iter_adj if a["outcome"] == "reject")
    escalated = sum(1 for a in iter_adj if a["outcome"] == "escalate")
    total = len(iter_adj)

    # Determine status
    if total == 0:
        # No issues found — clean
        status = "clean"
        reason = "No issues found in this iteration."
    elif accepted == 0 and escalated == 0:
        # All rejected — converged
        status = "converged"
        reason = "All issues were rejected — no changes needed."
    elif accepted > 0 and session.get("changes_applied", 0) > 0:
        # Changes were applied — need verification pass
        if iteration >= max_iterations:
            status = "limit"
            reason = f"Max iterations ({max_iterations}) reached."
        else:
            status = "needs_iteration"
            reason = f"{accepted} changes applied — verification pass required."
    elif escalated > 0 and accepted == 0:
        # Only escalations remain
        status = "human_only"
        reason = "Only escalated issues remain — requires user decision."
    elif iteration >= max_iterations:
        status = "limit"
        reason = f"Max iterations ({max_iterations}) reached."
    else:
        status = "needs_iteration"
        reason = f"{accepted} accepted, {escalated} escalated."

    session["iterations_completed"] = iteration
    _save_session(args.session, session)

    _output({
        "status": status,
        "session": args.session,
        "iteration": iteration,
        "reason": reason,
        "stats": {
            "total": total,
            "accepted": accepted,
            "rejected": rejected,
            "escalated": escalated,
        },
    })


# ---------------------------------------------------------------------------
# Report — Generate Review Log and Summary
# ---------------------------------------------------------------------------

def cmd_report(args):
    """Generate the review log and report summary."""
    session = _load_session(args.session)
    if not session:
        _output({"status": "error", "message": f"Session '{args.session}' not found."})
        return

    config = load_layer_config(session["layer"])
    if not config:
        _output({"status": "error", "message": f"No config for layer '{session['layer']}'"})
        return

    layer = session["layer"]
    target = session["target"]
    today = datetime.now().strftime("%Y-%m-%d")

    # Build report
    report_config = config.get("report", {})
    log_pattern = report_config.get("log_name_pattern", f"ITERATE-{layer}-{{date}}.md")
    log_name = log_pattern.format(date=today, target=Path(target).stem)

    # Tally by topic
    adjudications = session.get("adjudications", [])
    topics_config = config.get("topics", {})
    topic_rows = []

    all_topics = sorted(set(str(a.get("topic", "")) for a in adjudications))
    for tid in all_topics:
        topic_adj = [a for a in adjudications if str(a.get("topic")) == tid]
        topic_def = topics_config.get(tid) or topics_config.get(int(tid) if tid.isdigit() else tid, {})
        topic_name = topic_def.get("name", f"Topic {tid}") if isinstance(topic_def, dict) else f"Topic {tid}"
        accepted = sum(1 for a in topic_adj if a["outcome"] == "accept")
        rejected = sum(1 for a in topic_adj if a["outcome"] == "reject")
        escalated = sum(1 for a in topic_adj if a["outcome"] in ("escalate", "ambiguous_intent"))
        total = len(topic_adj)
        topic_rows.append(f"| {tid}. {topic_name} | {total} | {accepted} | {rejected} | {escalated} |")

    topic_table = "\n".join(topic_rows) if topic_rows else "| (no topics reviewed) | — | — | — | — |"

    total_accepted = sum(1 for a in adjudications if a["outcome"] == "accept")
    total_rejected = sum(1 for a in adjudications if a["outcome"] == "reject")
    total_escalated = sum(1 for a in adjudications if a["outcome"] in ("escalate", "ambiguous_intent"))
    total_issues = len(adjudications)

    # Final questions from config
    final_questions = report_config.get("final_questions", [])
    final_q_section = ""
    if final_questions:
        final_q_section = "\n### Final Questions\n\n"
        for fq in final_questions:
            if isinstance(fq, dict):
                final_q_section += f"**{fq.get('name', 'Question')}:** [To be filled by Claude]\n\n"
            elif isinstance(fq, str):
                final_q_section += f"**{fq}:** [To be filled by Claude]\n\n"

    # Rating descriptions
    rating_config = report_config.get("rating", {})
    rating_section = ""
    if rating_config:
        scale = rating_config.get("scale", 5)
        rating_section = f"\n**{config.get('display_name', layer)} Strength Rating:** [N]/{scale} — [reason]\n"

    iterations_completed = session.get("iterations_completed", 0)
    max_iterations = session.get("max_iterations", 10)
    changes_applied = session.get("changes_applied", 0)

    report_text = f"""## {config.get('display_name', layer)} Review Complete
{final_q_section}
### Topic Summary

| Topic | Issues | Accepted | Rejected | Escalated |
|-------|--------|----------|----------|-----------|
{topic_table}
{rating_section}
**Iterations:** {iterations_completed} completed / {max_iterations} max
**Changes applied:** {changes_applied}
**Review log:** scaffold/decisions/review/{log_name}
"""

    # Build the review log content
    log_content = f"""# Review Log: {log_name}

> **Layer:** {layer}
> **Target:** {target}
> **Date:** {today}
> **Iterations:** {iterations_completed}
> **Changes Applied:** {changes_applied}

## Summary

{session.get('review_summary', 'No summary available.')}

## Adjudications

| # | Topic | Severity | Issue | Outcome | Reasoning |
|---|-------|----------|-------|---------|-----------|
"""
    for i, adj in enumerate(adjudications, 1):
        issue = adj.get("issue", {})
        severity = issue.get("severity", "—")
        desc = issue.get("description", str(issue))[:80].replace("|", "/").replace("\n", " ")
        outcome = adj.get("outcome", "—")
        reasoning = adj.get("reasoning", "")[:60].replace("|", "/").replace("\n", " ")
        topic = adj.get("topic", "—")
        log_content += f"| {i} | {topic} | {severity} | {desc} | {outcome} | {reasoning} |\n"

    log_content += f"""
## Resolved Root Causes

{chr(10).join('- ' + rc for rc in session.get('resolved_root_causes', [])) or '(none)'}

## Escalations

"""
    escalations = [a for a in adjudications if a["outcome"] in ("escalate", "ambiguous_intent")]
    if escalations:
        for esc in escalations:
            issue = esc.get("issue", {})
            log_content += f"- **{issue.get('description', 'Unknown')}** — {esc.get('reasoning', 'Requires user decision')}\n"
    else:
        log_content += "(none)\n"

    # Output paths for Claude to write
    log_path = f"scaffold/decisions/review/{log_name}"

    _output({
        "status": "report",
        "session": args.session,
        "report": report_text,
        "log_content": log_content,
        "log_path": log_path,
        "stats": {
            "total_issues": total_issues,
            "accepted": total_accepted,
            "rejected": total_rejected,
            "escalated": total_escalated,
            "changes_applied": changes_applied,
            "iterations": iterations_completed,
        },
    })


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_root_cause(issue):
    """Extract a normalized root cause identifier from an issue."""
    if isinstance(issue, dict):
        # Use section + description as a rough root cause key
        section = issue.get("section", "")
        desc = issue.get("description", "")
        key = f"{section}:{desc}".lower().strip()
        # Normalize whitespace
        key = re.sub(r"\s+", " ", key)
        return key
    return str(issue).lower().strip()


def _run_doc_review(cmd):
    """Run doc-review.py and return parsed JSON output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(SCAFFOLD_DIR),
        )
        stdout = result.stdout.strip()
        if not stdout:
            if result.stderr:
                return {"error": f"doc-review.py error: {result.stderr.strip()}"}
            return {"error": f"doc-review.py returned no output (exit code {result.returncode})"}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            # Try to extract JSON from mixed output
            for line in stdout.splitlines():
                line = line.strip()
                if line.startswith("{"):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
            return {"error": "Failed to parse doc-review.py output", "raw": stdout[:500]}
    except subprocess.TimeoutExpired:
        return {"error": "doc-review.py timed out after 300 seconds"}
    except FileNotFoundError:
        return {"error": f"doc-review.py not found at {DOC_REVIEW_SCRIPT}"}


def _output(data):
    """Print JSON output to stdout."""
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Iterate orchestrator — manages adversarial review sessions."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # preflight
    p_pre = subparsers.add_parser("preflight", help="Check if a layer is ready for review")
    p_pre.add_argument("--layer", required=True, help="Layer name (e.g., design, systems, spec)")

    # start
    p_start = subparsers.add_parser("start", help="Start a topic review")
    p_start.add_argument("--layer", required=True, help="Layer name")
    p_start.add_argument("--target", default="", help="Target file path (relative to scaffold/)")
    p_start.add_argument("--topic", type=int, required=True, help="Topic number to review")
    p_start.add_argument("--iteration", type=int, default=1, help="Outer loop iteration number")
    p_start.add_argument("--iterations", type=int, default=None, help="Max iterations override")
    p_start.add_argument("--max-exchanges", type=int, default=None, help="Max exchanges per topic")
    p_start.add_argument("--focus", default="", help="Narrow review to a specific concern")
    p_start.add_argument("--signals", default="", help="Design signals from fix skill")

    # adjudicate
    p_adj = subparsers.add_parser("adjudicate", help="Record adjudication decision")
    p_adj.add_argument("--session", required=True, help="Session ID")
    p_adj.add_argument("--outcome", required=True,
                       choices=["accept", "reject", "escalate", "ambiguous_intent"],
                       help="Adjudication outcome")
    p_adj.add_argument("--reasoning", default="", help="Reasoning for the decision")

    # respond
    p_resp = subparsers.add_parser("respond", help="Send pushback to reviewer")
    p_resp.add_argument("--session", required=True, help="Session ID")
    p_resp.add_argument("--message", default="", help="Pushback message (inline)")
    p_resp.add_argument("--message-file", default="", help="Path to pushback message file")

    # scope-check
    p_scope = subparsers.add_parser("scope-check", help="Run scope guard tests")
    p_scope.add_argument("--session", required=True, help="Session ID")
    p_scope.add_argument("--change", required=True, help="Description of proposed change")

    # apply
    p_apply = subparsers.add_parser("apply", help="Apply accepted fixes")
    p_apply.add_argument("--session", required=True, help="Session ID")

    # convergence
    p_conv = subparsers.add_parser("convergence", help="Check if another iteration needed")
    p_conv.add_argument("--session", required=True, help="Session ID")

    # report
    p_report = subparsers.add_parser("report", help="Generate review log and report")
    p_report.add_argument("--session", required=True, help="Session ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "preflight": cmd_preflight,
        "start": cmd_start,
        "adjudicate": cmd_adjudicate,
        "respond": cmd_respond,
        "scope-check": cmd_scope_check,
        "apply": cmd_apply,
        "convergence": cmd_convergence,
        "report": cmd_report,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
