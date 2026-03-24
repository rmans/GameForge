#!/usr/bin/env python3
"""
Validate orchestrator — runs deterministic structural checks on scaffold documents.

Read-only: never edits files. Runs checks defined in per-scope YAML configs,
produces pass/fail/warn reports. Absorbs validate-refs.py functionality.

Uses action.json/result.json for report output only (no adjudication or apply).

Commands:
    preflight    Check if scope is ready for validation.
    run          Execute all checks for the given scope, write action.json with report data.
"""

import json
import os
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TOOLS_DIR = Path(__file__).parent
CONFIGS_DIR = TOOLS_DIR / "configs" / "validate"
SCAFFOLD_DIR = TOOLS_DIR.parent
REVIEWS_DIR = SCAFFOLD_DIR / ".reviews" / "validate"
ACTION_FILE = REVIEWS_DIR / "action.json"


# ---------------------------------------------------------------------------
# YAML Parser (shared — minimal, no dependencies)
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
                    item_dict = {key: _parse_yaml_value(val_text)} if val_text else {key: None}
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
# Config
# ---------------------------------------------------------------------------

def load_scope_config(scope):
    config_path = CONFIGS_DIR / f"{scope}.yaml"
    if not config_path.exists():
        return None
    return load_yaml(config_path)


# ---------------------------------------------------------------------------
# Check Runners
# ---------------------------------------------------------------------------

def _run_checks(scope, config, target_range=None):
    """Run all checks defined in config. Returns list of results."""
    results = []
    checks = config.get("checks", {})

    # Deterministic checks
    deterministic = checks.get("deterministic", [])
    for check in deterministic:
        if not isinstance(check, dict):
            continue
        result = _run_single_check(check, config, target_range)
        if result:
            results.extend(result)

    # Heuristic checks
    heuristic = checks.get("heuristic", [])
    for check in heuristic:
        if not isinstance(check, dict):
            continue
        result = _run_single_check(check, config, target_range)
        if result:
            for r in result:
                r["confidence"] = "Medium"
                if check.get("label") == "[ADVISORY]":
                    r["confidence"] = "Low"
            results.extend(result)

    return results


def _run_single_check(check, config, target_range=None):
    """Run a single check. Returns list of findings (may be empty)."""
    check_id = check.get("id", "")
    detection = check.get("detection", "")
    severity = check.get("severity", "WARN")
    description = check.get("description", check_id)
    findings = []

    # File existence checks
    if detection == "file_exists":
        target_files = _resolve_target_files(check, config, target_range)
        for f in target_files:
            if not (SCAFFOLD_DIR / f).exists():
                findings.append({
                    "check_id": check_id,
                    "status": severity,
                    "description": description,
                    "detail": f"File not found: {f}",
                    "confidence": "High",
                })

    # Index registration checks
    elif detection == "index_registration":
        index_file = SCAFFOLD_DIR / check.get("index_file", "")
        glob_pattern = check.get("glob_pattern", "")
        if index_file.exists() and glob_pattern:
            index_content = index_file.read_text(encoding="utf-8")
            for match in sorted(SCAFFOLD_DIR.glob(glob_pattern)):
                # Extract ID from filename
                id_match = re.search(check.get("id_pattern", r"(SYS|SPEC|TASK|SLICE|P)\S+"), match.name)
                if id_match:
                    doc_id = id_match.group()
                    if doc_id not in index_content:
                        findings.append({
                            "check_id": check_id,
                            "status": severity,
                            "description": description,
                            "detail": f"{doc_id} ({match.name}) not registered in {check.get('index_file', '')}",
                            "confidence": "High",
                        })

    # Section structure checks
    elif detection == "section_structure":
        target_files = _resolve_target_files(check, config, target_range)
        required_sections = check.get("required_sections", [])
        for f in target_files:
            abs_path = SCAFFOLD_DIR / f
            if abs_path.exists():
                content = abs_path.read_text(encoding="utf-8")
                headings = [line.strip() for line in content.splitlines() if line.strip().startswith("#")]
                heading_texts = [re.sub(r"^#+\s+", "", h) for h in headings]
                for req in required_sections:
                    if req not in heading_texts:
                        findings.append({
                            "check_id": check_id,
                            "status": severity,
                            "description": description,
                            "detail": f"Missing section '{req}' in {f}",
                            "confidence": "High",
                        })

    # Section health checks
    elif detection == "section_health":
        target_files = _resolve_target_files(check, config, target_range)
        fail_threshold = check.get("fail_threshold", 0.4)
        warn_threshold = check.get("warn_threshold", 0.65)
        for f in target_files:
            abs_path = SCAFFOLD_DIR / f
            if abs_path.exists():
                content = abs_path.read_text(encoding="utf-8")
                health = _calculate_health(content)
                if health < fail_threshold:
                    findings.append({
                        "check_id": check_id,
                        "status": "FAIL",
                        "description": description,
                        "detail": f"{f}: health {health:.0%} (< {fail_threshold:.0%} threshold)",
                        "confidence": "High",
                    })
                elif health < warn_threshold:
                    findings.append({
                        "check_id": check_id,
                        "status": "WARN",
                        "description": description,
                        "detail": f"{f}: health {health:.0%} (< {warn_threshold:.0%} threshold)",
                        "confidence": "High",
                    })

    # Status-filename sync
    elif detection == "status_filename_sync":
        target_files = _resolve_target_files(check, config, target_range)
        for f in target_files:
            abs_path = SCAFFOLD_DIR / f
            if abs_path.exists():
                content = abs_path.read_text(encoding="utf-8")
                status_match = re.search(r">\s*\*\*Status:\*\*\s*(\w+)", content)
                if status_match:
                    internal_status = status_match.group(1).lower()
                    filename = Path(f).stem
                    for suffix in ["_draft", "_review", "_approved", "_complete", "_deprecated"]:
                        if filename.endswith(suffix):
                            file_status = suffix[1:]  # strip leading _
                            if file_status != internal_status:
                                findings.append({
                                    "check_id": check_id,
                                    "status": severity,
                                    "description": description,
                                    "detail": f"{f}: filename says '{file_status}' but Status field says '{internal_status}'",
                                    "confidence": "High",
                                })
                            break

    # Glossary compliance
    elif detection == "glossary_not_column":
        not_terms = _load_glossary()
        target_files = _resolve_target_files(check, config, target_range)
        for f in target_files:
            abs_path = SCAFFOLD_DIR / f
            if abs_path.exists():
                content = abs_path.read_text(encoding="utf-8")
                for bad_term, canonical in not_terms.items():
                    pattern = rf"\b{re.escape(bad_term)}\b"
                    if re.search(pattern, content, re.IGNORECASE):
                        findings.append({
                            "check_id": check_id,
                            "status": severity,
                            "description": description,
                            "detail": f"{f}: uses '{bad_term}' (canonical: '{canonical}')",
                            "confidence": "Medium" if check.get("label") == "[ADVISORY]" else "High",
                        })

    # Review freshness
    elif detection == "review_freshness":
        target_files = _resolve_target_files(check, config, target_range)
        review_dir = SCAFFOLD_DIR / "decisions" / "review"
        for f in target_files:
            abs_path = SCAFFOLD_DIR / f
            if abs_path.exists():
                file_mtime = abs_path.stat().st_mtime
                # Find matching review log
                stem = Path(f).stem
                review_pattern = check.get("review_pattern", f"ITERATE-*{stem}*")
                reviews = sorted(review_dir.glob(review_pattern)) if review_dir.exists() else []
                if not reviews:
                    findings.append({
                        "check_id": check_id,
                        "status": severity,
                        "description": description,
                        "detail": f"{f}: no review log found",
                        "confidence": "High",
                    })
                else:
                    latest_review = reviews[-1]
                    review_mtime = latest_review.stat().st_mtime
                    if file_mtime > review_mtime:
                        findings.append({
                            "check_id": check_id,
                            "status": severity,
                            "description": description,
                            "detail": f"{f}: modified after last review ({latest_review.name})",
                            "confidence": "High",
                        })

    # Generic pattern check
    elif detection == "pattern_absent" or detection == "pattern_present":
        target_files = _resolve_target_files(check, config, target_range)
        pattern = check.get("pattern", "")
        if pattern:
            for f in target_files:
                abs_path = SCAFFOLD_DIR / f
                if abs_path.exists():
                    content = abs_path.read_text(encoding="utf-8")
                    found = bool(re.search(pattern, content, re.MULTILINE | re.IGNORECASE))
                    if detection == "pattern_absent" and found:
                        findings.append({
                            "check_id": check_id,
                            "status": severity,
                            "description": description,
                            "detail": f"{f}: pattern should be absent: {pattern}",
                            "confidence": check.get("confidence", "High"),
                        })
                    elif detection == "pattern_present" and not found:
                        findings.append({
                            "check_id": check_id,
                            "status": severity,
                            "description": description,
                            "detail": f"{f}: pattern not found: {pattern}",
                            "confidence": check.get("confidence", "High"),
                        })

    # If no specific handler, return empty
    return findings if findings else []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_target_files(check, config, target_range=None):
    """Resolve which files a check applies to."""
    glob_pattern = check.get("glob_pattern", config.get("glob_pattern", ""))
    target_files = check.get("target_files", [])

    if target_files:
        return target_files

    if glob_pattern:
        matches = sorted(SCAFFOLD_DIR.glob(glob_pattern))
        files = [str(m.relative_to(SCAFFOLD_DIR)) for m in matches]
        # Apply range filter if specified
        if target_range:
            files = [f for f in files if _in_range(f, target_range)]
        return files

    return []


def _in_range(filepath, target_range):
    """Check if a file falls within a target range (e.g., SYS-001-SYS-020)."""
    if not target_range or "-" not in target_range:
        return True
    parts = target_range.split("-", 2)
    if len(parts) >= 4:
        # Range format: PREFIX-NNN-PREFIX-NNN
        prefix = parts[0]
        try:
            start = int(parts[1])
            end = int(parts[3])
        except (ValueError, IndexError):
            return True
        # Extract ID from filepath
        match = re.search(rf"{prefix}-(\d+)", filepath)
        if match:
            file_id = int(match.group(1))
            return start <= file_id <= end
    return True


def _calculate_health(content):
    """Calculate section health score for a document."""
    sections = {}
    current = None
    current_lines = []

    for line in content.splitlines():
        if line.strip().startswith("## "):
            if current:
                sections[current] = "\n".join(current_lines)
            current = line.strip()
            current_lines = []
        elif current:
            current_lines.append(line)

    if current:
        sections[current] = "\n".join(current_lines)

    if not sections:
        return 0.0

    total = 0.0
    for heading, body in sections.items():
        cleaned = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()
        if len(cleaned) < 10:
            total += 0.0  # Empty
        elif re.search(r"TODO|TBD|\*TODO:", cleaned) or len(cleaned) < 50:
            total += 0.5  # Partial
        else:
            total += 1.0  # Complete

    return total / len(sections)


def _load_glossary():
    """Load NOT-column terms from glossary."""
    glossary_path = SCAFFOLD_DIR / "design" / "glossary.md"
    if not glossary_path.exists():
        return {}
    content = glossary_path.read_text(encoding="utf-8")
    not_terms = {}
    for line in content.splitlines():
        if "|" in line and line.count("|") >= 3:
            cells = [c.strip() for c in line.split("|")]
            for cell in cells:
                if cell.lower().startswith("not:") or cell.lower().startswith("not "):
                    canonical = cells[1].strip() if len(cells) > 1 else ""
                    bad_terms = cell.split(":", 1)[-1].strip() if ":" in cell else ""
                    for bt in bad_terms.split(","):
                        bt = bt.strip()
                        if bt and canonical:
                            not_terms[bt.lower()] = canonical
    return not_terms


def _write_action(data):
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ACTION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _output(data):
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

def cmd_preflight(args):
    """Check if scope is ready for validation."""
    config = load_scope_config(args.scope)
    if not config:
        _output({"status": "error", "message": f"No config found for scope '{args.scope}'"})
        return

    activation = config.get("activation", {})
    required = activation.get("required_files", [])
    issues = []

    for rel_path in required:
        abs_path = SCAFFOLD_DIR / rel_path
        if not abs_path.exists():
            issues.append(f"Required file missing: {rel_path}")

    if issues:
        _output({"status": "skip", "message": activation.get("skip_message", "Preconditions not met."), "issues": issues})
        return

    _output({"status": "ready", "scope": args.scope})


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def cmd_run(args):
    """Execute all checks for the given scope."""
    # Handle --scope all by running all individual scopes
    if args.scope == "all":
        all_results = []
        scope_files = sorted(CONFIGS_DIR.glob("*.yaml"))
        for sf in scope_files:
            scope_name = sf.stem
            if scope_name == "all":
                continue
            config = load_yaml(sf)
            if config:
                results = _run_checks(scope_name, config, args.range)
                all_results.extend(results)
        _write_report(args, all_results)
        return

    config = load_scope_config(args.scope)
    if not config:
        _write_action({"action": "report", "status": "error", "message": f"No config for scope '{args.scope}'"})
        return

    # Check activation
    activation = config.get("activation", {})
    required = activation.get("required_files", [])
    for rel_path in required:
        if not (SCAFFOLD_DIR / rel_path).exists():
            _write_action({
                "action": "report",
                "status": "skip",
                "scope": args.scope,
                "message": activation.get("skip_message", f"Skipped — preconditions not met for {args.scope}"),
                "results": [],
            })
            return

    results = _run_checks(args.scope, config, args.range)
    _write_report(args, results)


def _write_report(args, results):
    """Write the validation report as action.json."""
    # Classify results
    fails = [r for r in results if r.get("status") == "FAIL"]
    warns = [r for r in results if r.get("status") == "WARN"]
    infos = [r for r in results if r.get("status") == "INFO"]
    passes = len(results) == 0

    # Determine verdict
    if fails:
        verdict = "FAIL"
        blocking = True
    elif warns:
        verdict = "WARN"
        blocking = False
    else:
        verdict = "PASS"
        blocking = False

    # Impact classification
    critical = sum(1 for r in results if r.get("impact") == "Critical")
    high = sum(1 for r in results if r.get("impact") == "High")
    medium = sum(1 for r in results if r.get("impact") == "Medium")
    low = sum(1 for r in results if r.get("impact") == "Low")

    today = datetime.now().strftime("%Y-%m-%d")

    _write_action({
        "action": "report",
        "scope": args.scope,
        "date": today,
        "verdict": verdict,
        "blocking": blocking,
        "results": results,
        "summary": {
            "total_checks": len(set(r.get("check_id", "") for r in results)) if results else 0,
            "total_issues": len(results),
            "fails": len(fails),
            "warns": len(warns),
            "infos": len(infos),
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
        },
        "next_step": _suggest_next(args.scope, verdict, results),
    })


def _suggest_next(scope, verdict, results):
    """Suggest the next action based on validation results."""
    if verdict == "PASS":
        return f"Validation passed. Proceed to the next pipeline step."
    elif verdict == "FAIL":
        # Find the highest-impact failing scope
        fail_checks = set(r.get("check_id", "").split("-")[0] for r in results if r.get("status") == "FAIL")
        if fail_checks:
            return f"Run `/scaffold-fix {scope}` to resolve FAIL issues."
        return f"Fix FAIL issues before proceeding."
    else:
        return "Review WARN issues, then proceed if acceptable."


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Validate orchestrator — structural checks")
    subparsers = parser.add_subparsers(dest="command")

    p_pre = subparsers.add_parser("preflight")
    p_pre.add_argument("--scope", required=True)

    p_run = subparsers.add_parser("run")
    p_run.add_argument("--scope", required=True)
    p_run.add_argument("--range", default="")
    p_run.add_argument("--incremental", action="store_true")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"preflight": cmd_preflight, "run": cmd_run}[args.command](args)


if __name__ == "__main__":
    main()
