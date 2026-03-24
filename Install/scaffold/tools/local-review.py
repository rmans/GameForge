#!/usr/bin/env python3
"""
Fix orchestrator — manages mechanical fix sessions for scaffold documents.

Runs mechanical checks (regex, pattern matching) in Python.
Routes judgment checks to Claude via scaffold-review-adjudicate.
Uses the same file-based exchange as iterate.py:
  - action.json: local-review.py writes the next instruction for Claude
  - result.json: Claude's sub-skill writes its response

Commands:
    preflight    Check if a layer/target is ready for fixing.
    next-action  Write action.json with the next instruction.
    resolve      Read result.json, process it, write next action.json.

Session state persists in .reviews/fix/session-<id>.json.
No pip dependencies — uses Python standard library only.
"""

import json
import os
import sys
import argparse
import hashlib
import re
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TOOLS_DIR = Path(__file__).parent
CONFIGS_DIR = TOOLS_DIR / "configs" / "fix"
SCAFFOLD_DIR = TOOLS_DIR.parent
REVIEWS_DIR = SCAFFOLD_DIR / ".reviews" / "fix"
ACTION_FILE = REVIEWS_DIR / "action.json"
RESULT_FILE = REVIEWS_DIR / "result.json"


# ---------------------------------------------------------------------------
# YAML Parser (shared with iterate.py — minimal, no dependencies)
# ---------------------------------------------------------------------------

def _parse_yaml_value(val):
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
    """Load a YAML file. Uses PyYAML if available, falls back to custom parser."""
    path = Path(path)
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        lines = content.splitlines()
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
                    items = [_parse_yaml_value(x.strip()) for x in inner.split(",")] if inner.strip() else []
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
    key = f"fix:{layer}:{target}"
    h = hashlib.md5(key.encode()).hexdigest()[:8]
    name = Path(target).stem if target else layer
    return f"fix-{name}-{h}"


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


def _output(data):
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Glossary Loading
# ---------------------------------------------------------------------------

def _load_glossary():
    """Load glossary NOT-column terms for compliance checking."""
    glossary_path = SCAFFOLD_DIR / "design" / "glossary.md"
    if not glossary_path.exists():
        return {}
    content = glossary_path.read_text(encoding="utf-8")
    not_terms = {}
    # Find table rows with NOT column
    for line in content.splitlines():
        if "|" in line and line.count("|") >= 3:
            cells = [c.strip() for c in line.split("|")]
            # Typical format: | Term | Definition | NOT: bad1, bad2 |
            for cell in cells:
                if cell.lower().startswith("not:") or cell.lower().startswith("not "):
                    canonical = cells[1].strip() if len(cells) > 1 else ""
                    bad_terms = cell.split(":", 1)[-1].strip() if ":" in cell else ""
                    for bt in bad_terms.split(","):
                        bt = bt.strip()
                        if bt and canonical:
                            not_terms[bt.lower()] = canonical
    return not_terms


# ---------------------------------------------------------------------------
# Template Loading
# ---------------------------------------------------------------------------

def _load_template_headings(config):
    """Load expected headings from the template file."""
    template_path = SCAFFOLD_DIR / (config.get("template", "") or "")
    if not template_path.exists():
        return []
    content = template_path.read_text(encoding="utf-8")
    headings = []
    for line in content.splitlines():
        if line.strip().startswith("#"):
            headings.append(line.strip())
    return headings


# ---------------------------------------------------------------------------
# Mechanical Check Runners
# ---------------------------------------------------------------------------

def _run_mechanical_checks(session, config, doc_content, doc_path):
    """Run all mechanical checks and return categorized findings."""
    findings = []
    auto_fixes = []

    mechanical = config.get("mechanical_checks", {})

    # -- Completeness checks --
    completeness = mechanical.get("completeness", [])
    template_headings = _load_template_headings(config)

    for check in completeness:
        if not isinstance(check, dict):
            continue
        check_id = check.get("id", "")

        if check_id == "missing_sections":
            doc_headings = [line.strip() for line in doc_content.splitlines()
                           if line.strip().startswith("#")]
            doc_heading_texts = [re.sub(r"^#+\s+", "", h) for h in doc_headings]
            for th in template_headings:
                th_text = re.sub(r"^#+\s+", "", th)
                if th_text not in doc_heading_texts and not th_text.startswith("["):
                    if check.get("auto_fix"):
                        auto_fixes.append({
                            "check_id": check_id,
                            "category": "completeness",
                            "description": f"Missing section: {th}",
                            "fix": f"Add section heading '{th}' with template comment",
                        })
                    else:
                        findings.append({
                            "check_id": check_id,
                            "category": "completeness",
                            "description": f"Missing section: {th}",
                            "requires_user": True,
                        })

        elif check_id == "stale_seeded_markers":
            pattern = check.get("pattern", "<!-- SEEDED")
            min_len = check.get("min_content_length", 50)
            sections = _split_into_sections(doc_content)
            for heading, content in sections.items():
                if pattern in content:
                    cleaned = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL).strip()
                    if len(cleaned) >= min_len:
                        if check.get("auto_fix"):
                            auto_fixes.append({
                                "check_id": check_id,
                                "category": "completeness",
                                "description": f"Stale SEEDED marker in {heading}",
                                "fix": f"Remove SEEDED marker from {heading}",
                                "section": heading,
                            })

    # -- Terminology checks --
    terminology = mechanical.get("terminology", [])
    not_terms = _load_glossary()

    for check in terminology:
        if not isinstance(check, dict):
            continue
        check_id = check.get("id", "")

        if check_id == "glossary_compliance" and not_terms:
            for bad_term, canonical in not_terms.items():
                # Case-insensitive word boundary search
                pattern = rf"\b{re.escape(bad_term)}\b"
                matches = list(re.finditer(pattern, doc_content, re.IGNORECASE))
                for match in matches:
                    # Check if in excluded context (rough heuristic)
                    line_start = doc_content.rfind("\n", 0, match.start()) + 1
                    line = doc_content[line_start:doc_content.find("\n", match.end())]
                    if _is_excluded_context(line):
                        continue
                    if check.get("auto_fix"):
                        auto_fixes.append({
                            "check_id": check_id,
                            "category": "terminology",
                            "description": f"NOT-column term '{bad_term}' used — canonical is '{canonical}'",
                            "fix": f"Replace '{match.group()}' with '{canonical}'",
                            "location": match.start(),
                        })

        elif check_id == "index_registration":
            index_file = SCAFFOLD_DIR / check.get("index_file", "")
            if index_file.exists():
                index_content = index_file.read_text(encoding="utf-8")
                doc_name = Path(doc_path).name
                sys_match = re.search(r"SYS-\d+", doc_name)
                if sys_match:
                    sys_id = sys_match.group()
                    if sys_id not in index_content:
                        if check.get("auto_fix"):
                            auto_fixes.append({
                                "check_id": check_id,
                                "category": "terminology",
                                "description": f"{sys_id} missing from index",
                                "fix": f"Add {sys_id} to {check.get('index_file', '')}",
                            })

    # -- Implementation language checks --
    impl_checks = mechanical.get("implementation_language", [])
    for check in impl_checks:
        if not isinstance(check, dict):
            continue
        check_id = check.get("id", "")
        patterns = check.get("patterns", [])

        for pat in patterns:
            if isinstance(pat, str):
                matches = list(re.finditer(pat, doc_content))
                for match in matches:
                    # Skip if inside HTML comment
                    before = doc_content[:match.start()]
                    if before.rfind("<!--") > before.rfind("-->"):
                        continue
                    if check.get("auto_fix"):
                        auto_fixes.append({
                            "check_id": check_id,
                            "category": "implementation_language",
                            "description": f"Implementation term found: '{match.group()}'",
                            "fix": f"Replace '{match.group()}' with design-level language",
                            "location": match.start(),
                        })
                    elif check.get("signal"):
                        findings.append({
                            "check_id": check_id,
                            "category": "signal",
                            "signal_type": check["signal"],
                            "description": f"Layer breach: '{match.group()}'",
                        })

    # -- Structural quality mechanical checks --
    structural = mechanical.get("structural_quality", [])
    for check in structural:
        if not isinstance(check, dict):
            continue
        check_id = check.get("id", "")

        if check_id == "owned_state_columns":
            section = check.get("section", "### Owned State")
            section_content = _extract_section(doc_content, section)
            if section_content:
                req_cols = check.get("required_columns", [])
                # Check if table exists and has required columns
                table_lines = [l for l in section_content.splitlines() if "|" in l and l.strip().startswith("|")]
                if table_lines:
                    header = table_lines[0]
                    for col in req_cols:
                        if col.lower() not in header.lower():
                            if check.get("auto_fix"):
                                auto_fixes.append({
                                    "check_id": check_id,
                                    "category": "structural_quality",
                                    "description": f"Owned State table missing '{col}' column",
                                    "fix": f"Add '{col}' column to Owned State table",
                                    "section": section,
                                })

    return auto_fixes, findings


def _is_excluded_context(line):
    """Check if a line is in an excluded context for glossary checking."""
    stripped = line.strip()
    # Inside HTML comment
    if "<!--" in stripped:
        return True
    # Changelog entry
    if stripped.startswith("- ") and re.match(r"- \d{4}-\d{2}-\d{2}", stripped):
        return True
    # Blockquote (metadata)
    if stripped.startswith(">"):
        return True
    return False


def _split_into_sections(doc_content):
    """Split document into heading → content dict."""
    sections = {}
    current_heading = None
    current_lines = []

    for line in doc_content.splitlines():
        if line.strip().startswith("#"):
            if current_heading:
                sections[current_heading] = "\n".join(current_lines)
            current_heading = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading:
        sections[current_heading] = "\n".join(current_lines)

    return sections


def _extract_section(doc_content, heading):
    """Extract content under a specific heading."""
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
# Signal Detection
# ---------------------------------------------------------------------------

def _detect_signals(session, config, doc_content, doc_path):
    """Detect design signals — reported, never fixed."""
    signals_found = []
    signal_defs = config.get("signals", {})

    # Ownership signals
    ownership = signal_defs.get("ownership", [])
    for sig in ownership:
        if not isinstance(sig, dict):
            continue
        sig_id = sig.get("id", "")

        if sig_id == "owned_state_gameplay":
            section = _extract_section(doc_content, "### Owned State")
            if section:
                impl_patterns = [
                    r"\bcache\b", r"\bregistry\b", r"\bnode\b", r"\bscene\b",
                    r"\bdictionary\b", r"\barray\b", r"\bhashmap\b",
                ]
                for pat in impl_patterns:
                    if re.search(pat, section, re.IGNORECASE):
                        signals_found.append({
                            "signal_id": sig_id,
                            "category": "ownership",
                            "description": f"Owned State may contain implementation structures",
                            "section": "### Owned State",
                        })
                        break

    return signals_found


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

def cmd_preflight(args):
    config = load_layer_config(args.layer)
    if not config:
        _output({"status": "error", "message": f"No config found for layer '{args.layer}'"})
        return

    preflight = config.get("preflight", {})
    issues = []

    for rel_path in preflight.get("required_files", []):
        abs_path = SCAFFOLD_DIR / rel_path
        if not abs_path.exists():
            issues.append(f"Required file missing: {rel_path}")

    if args.target:
        target_abs = SCAFFOLD_DIR / args.target
        if not target_abs.exists():
            issues.append(f"Target not found: {args.target}")

    if issues:
        _output({"status": "blocked", "message": preflight.get("blocked_message", "Preflight failed."), "issues": issues})
        return

    result = {"status": "ready", "layer": args.layer}
    if args.target:
        result["target"] = args.target
    _output(result)


# ---------------------------------------------------------------------------
# Next Action
# ---------------------------------------------------------------------------

def cmd_next_action(args):
    config = load_layer_config(args.layer)
    if not config:
        _write_action({"action": "blocked", "message": f"No config for layer '{args.layer}'"})
        return

    target = args.target or config.get("target", "")
    session_id = _session_id(args.layer, target)
    session = _load_session(session_id)

    if not session:
        session = {
            "session_id": session_id,
            "layer": args.layer,
            "target": target,
            "iteration": 1,
            "max_iterations": args.iterations or config.get("defaults", {}).get("max_iterations", 10),
            "queue": [],
            "queue_index": 0,
            "auto_fixes_all": [],
            "auto_fixes": [],
            "findings": [],
            "signals": [],
            "adjudications": [],
            "changes_pending": [],
            "changes_applied_total": 0,
            "changes_this_iteration": 0,
            "rejected_judgment_ids": [],
            "created": datetime.now().isoformat(),
        }

    # Run mechanical checks
    target_abs = SCAFFOLD_DIR / target
    if not target_abs.exists():
        _write_action({"action": "blocked", "message": f"Target file not found: {target}"})
        return

    doc_content = target_abs.read_text(encoding="utf-8")
    auto_fixes, findings = _run_mechanical_checks(session, config, doc_content, target)
    signals = _detect_signals(session, config, doc_content, target)

    session["auto_fixes"] = auto_fixes
    session["auto_fixes_all"] = session.get("auto_fixes_all", []) + auto_fixes
    session["findings"] = findings
    session["signals"] = signals
    session["changes_this_iteration"] = 0

    # Build queue: auto-fixes first, then judgment checks, then apply, then report
    queue = []

    # Auto-fixes go directly to apply (no adjudication needed)
    if auto_fixes:
        queue.append({"phase": "auto_apply", "fixes": auto_fixes})

    # Judgment checks need adjudication — skip checks already rejected in previous iterations
    rejected_ids = session.get("rejected_judgment_ids", [])
    judgment = config.get("judgment_checks", {})
    for category, checks in judgment.items():
        if isinstance(checks, list):
            for check in checks:
                if isinstance(check, dict):
                    check_id = check.get("id", "")
                    if check_id in rejected_ids:
                        continue
                    queue.append({
                        "phase": "judgment",
                        "check": check,
                        "category": category,
                    })

    # Apply any accepted judgment fixes
    queue.append({"phase": "judgment_apply"})

    # Convergence check
    queue.append({"phase": "convergence"})

    # Report
    queue.append({"phase": "report"})

    session["queue"] = queue
    session["queue_index"] = 0
    _save_session(session_id, session)

    _advance_and_write_action(session, config)


def _advance_and_write_action(session, config):
    """Advance to next queue item and write action."""
    idx = session.get("queue_index", 0)
    queue = session.get("queue", [])

    if idx >= len(queue):
        _write_action({"action": "done", "session_id": session["session_id"]})
        return

    item = queue[idx]
    target = session["target"]

    if item["phase"] == "auto_apply":
        # Auto-fixes — send directly to apply skill
        _write_action({
            "action": "apply",
            "session_id": session["session_id"],
            "target_file": target,
            "editable_files": _get_editable_files(config),
            "pass": "auto_fix",
            "changes": item["fixes"],
        })
        return

    if item["phase"] == "judgment":
        # Judgment check — send to adjudicate skill
        check = item["check"]
        target_abs = SCAFFOLD_DIR / target
        doc_content = target_abs.read_text(encoding="utf-8") if target_abs.exists() else ""
        section_heading = check.get("section", "")
        section_content = _extract_section(doc_content, section_heading) if section_heading else doc_content[:3000]

        _write_action({
            "action": "adjudicate",
            "session_id": session["session_id"],
            "pass": "fix_judgment",
            "section": section_heading,
            "issue": {
                "severity": "MEDIUM",
                "section": section_heading,
                "description": check.get("description", ""),
                "suggestion": "",
                "check_question": check.get("question", ""),
            },
            "section_content": section_content[:5000] if section_content else "",
            "target_file": target,
            "layer": session["layer"],
            "rules": config.get("rules", []),
            "resolved_root_causes": [],
            "exchange_count": 0,
            "max_exchanges": 3,
        })
        return

    if item["phase"] == "judgment_apply":
        if session.get("changes_pending"):
            _write_action({
                "action": "apply",
                "session_id": session["session_id"],
                "target_file": target,
                "editable_files": _get_editable_files(config),
                "pass": "fix_judgment",
                "changes": session["changes_pending"],
            })
        else:
            session["queue_index"] = idx + 1
            _save_session(session["session_id"], session)
            _advance_and_write_action(session, config)
        return

    if item["phase"] == "convergence":
        # Check if we need another pass — based on THIS iteration's changes, not total
        iteration = session.get("iteration", 1)
        max_iter = session.get("max_iterations", 10)
        applied_this_iteration = session.get("changes_this_iteration", 0)

        if applied_this_iteration > 0 and iteration < max_iter:
            # Re-run checks on the updated document
            session["iteration"] = iteration + 1
            session["changes_pending"] = []
            session["queue_index"] = 0
            # Rebuild queue (re-run mechanical + judgment checks)
            _save_session(session["session_id"], session)
            # Re-run next-action will rebuild the queue
            target_abs = SCAFFOLD_DIR / session["target"]
            doc_content = target_abs.read_text(encoding="utf-8") if target_abs.exists() else ""
            auto_fixes, findings = _run_mechanical_checks(session, config, doc_content, session["target"])
            signals = _detect_signals(session, config, doc_content, session["target"])

            # Filter judgment checks — skip already-rejected ones
            rejected_ids = session.get("rejected_judgment_ids", [])
            remaining_judgment = []
            judgment = config.get("judgment_checks", {})
            for category, checks in judgment.items():
                if isinstance(checks, list):
                    for check in checks:
                        if isinstance(check, dict):
                            check_id = check.get("id", "")
                            if check_id not in rejected_ids:
                                remaining_judgment.append({"phase": "judgment", "check": check, "category": category})

            if not auto_fixes and not remaining_judgment:
                # Clean — no more issues
                session["queue_index"] = idx + 1
                _save_session(session["session_id"], session)
                _advance_and_write_action(session, config)
                return

            session["auto_fixes"] = auto_fixes
            session["auto_fixes_all"] = session.get("auto_fixes_all", []) + auto_fixes
            session["findings"] = findings
            session["signals"] = signals
            session["changes_this_iteration"] = 0

            queue = []
            if auto_fixes:
                queue.append({"phase": "auto_apply", "fixes": auto_fixes})
            queue.extend(remaining_judgment)
            queue.append({"phase": "judgment_apply"})
            queue.append({"phase": "convergence"})
            queue.append({"phase": "report"})

            session["queue"] = queue
            session["queue_index"] = 0
            _save_session(session["session_id"], session)
            _advance_and_write_action(session, config)
            return
        else:
            # Done — advance to report
            session["queue_index"] = idx + 1
            _save_session(session["session_id"], session)
            _advance_and_write_action(session, config)
            return

    if item["phase"] == "report":
        today = datetime.now().strftime("%Y-%m-%d")
        _write_action({
            "action": "report",
            "session_id": session["session_id"],
            "layer": session["layer"],
            "target": target,
            "target_name": Path(target).stem,
            "iterations_completed": session.get("iteration", 1),
            "max_iterations": session.get("max_iterations", 10),
            "changes_applied": session.get("changes_applied_total", 0),
            "auto_fixes": session.get("auto_fixes_all", []),
            "findings": session.get("findings", []),
            "signals": session.get("signals", []),
            "adjudications": session.get("adjudications", []),
            "log_name": f"FIX-{session['layer']}-{Path(target).stem}-{today}.md",
            "log_path": f"scaffold/decisions/review/FIX-{session['layer']}-{Path(target).stem}-{today}.md",
        })
        return

    # Unknown phase — skip
    session["queue_index"] = idx + 1
    _save_session(session["session_id"], session)
    _advance_and_write_action(session, config)


# ---------------------------------------------------------------------------
# Resolve
# ---------------------------------------------------------------------------

def cmd_resolve(args):
    session = _load_session(args.session)
    if not session:
        _write_action({"action": "blocked", "message": f"Session '{args.session}' not found."})
        return

    config = load_layer_config(session["layer"])
    result = _read_result()

    if RESULT_FILE.exists():
        RESULT_FILE.unlink()

    # No result.json — advance to next queue item (valid after no_issues actions)
    if not result:
        _advance_and_write_action(session, config)
        return

    queue = session.get("queue", [])
    idx = session.get("queue_index", 0)
    item = queue[idx] if idx < len(queue) else {}

    # Apply result
    if item.get("phase") in ("auto_apply", "judgment_apply"):
        applied = result.get("applied", 0)
        session["changes_pending"] = []
        session["changes_applied_total"] = session.get("changes_applied_total", 0) + applied
        session["changes_this_iteration"] = session.get("changes_this_iteration", 0) + applied
        session["queue_index"] = idx + 1
        _save_session(args.session, session)
        _advance_and_write_action(session, config)
        return

    # Report result
    if item.get("phase") == "report":
        session["queue_index"] = idx + 1
        _save_session(args.session, session)
        _write_action({
            "action": "done",
            "session_id": session["session_id"],
            "report_summary": result.get("report_summary", ""),
        })
        return

    # Judgment adjudication result
    if item.get("phase") == "judgment":
        outcome = result.get("outcome", "")
        check_id = item.get("check", {}).get("id", "")
        adjudication = {
            "phase": "judgment",
            "check_id": check_id,
            "section": item.get("check", {}).get("section", ""),
            "outcome": outcome,
            "reasoning": result.get("reasoning", ""),
            "timestamp": datetime.now().isoformat(),
        }
        session["adjudications"].append(adjudication)

        if outcome == "accept":
            session["changes_pending"].append({
                "section": item.get("check", {}).get("section", ""),
                "fix_description": result.get("fix_description", ""),
                "issue_description": item.get("check", {}).get("description", ""),
                "severity": "MEDIUM",
            })
        elif outcome == "reject":
            # Track rejected judgment check IDs so they're skipped in future iterations
            rejected = session.get("rejected_judgment_ids", [])
            if check_id and check_id not in rejected:
                rejected.append(check_id)
            session["rejected_judgment_ids"] = rejected

        session["queue_index"] = idx + 1
        _save_session(args.session, session)
        _advance_and_write_action(session, config)
        return

    # Unknown — advance
    session["queue_index"] = idx + 1
    _save_session(args.session, session)
    _advance_and_write_action(session, config)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_editable_files(config):
    adj = config.get("editable_files_pattern", "")
    if adj:
        return [str(p.relative_to(SCAFFOLD_DIR)) for p in SCAFFOLD_DIR.glob(adj)]
    return config.get("editable_files", [])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fix orchestrator")
    subparsers = parser.add_subparsers(dest="command")

    p_pre = subparsers.add_parser("preflight")
    p_pre.add_argument("--layer", required=True)
    p_pre.add_argument("--target", default="")

    p_next = subparsers.add_parser("next-action")
    p_next.add_argument("--layer", required=True)
    p_next.add_argument("--target", default="")
    p_next.add_argument("--iterations", type=int, default=None)
    p_next.add_argument("--sections", default="")

    p_res = subparsers.add_parser("resolve")
    p_res.add_argument("--session", required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"preflight": cmd_preflight, "next-action": cmd_next_action, "resolve": cmd_resolve}[args.command](args)


if __name__ == "__main__":
    main()
