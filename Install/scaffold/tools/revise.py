#!/usr/bin/env python3
"""
Revise orchestrator — detects drift and dispatches updates to scaffold docs.

Reads implementation feedback (ADRs, KIs, triage logs, code review, playtest),
classifies drift as design-led vs implementation-led, auto-applies safe changes,
escalates dangerous changes, and dispatches restabilization loops.

Commands:
    preflight    Check if layer has feedback to process.
    next-action  Write action.json with the next instruction.
    resolve      Read result.json, process it, write next action.json.
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
CONFIGS_DIR = TOOLS_DIR / "configs" / "revise"
SCAFFOLD_DIR = TOOLS_DIR.parent
REVIEWS_DIR = SCAFFOLD_DIR / ".reviews" / "revise"
ACTION_FILE = REVIEWS_DIR / "action.json"
RESULT_FILE = REVIEWS_DIR / "result.json"


# ---------------------------------------------------------------------------
# YAML Parser (shared)
# ---------------------------------------------------------------------------

def _parse_yaml_value(val):
    val = val.strip()
    if val == "" or val == "~" or val == "null":
        return None
    if val in ("true", "True"):
        return True
    if val in ("false", "False"):
        return False
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
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
                    cp = item_text.index(":")
                    key = item_text[:cp].strip()
                    vt = item_text[cp + 1:].strip()
                    item_dict = {key: _parse_yaml_value(vt)} if vt else {key: None}
                    ni = i + 1
                    if ni < len(lines):
                        ns = lines[ni].strip()
                        nind = _count_indent(lines[ni]) if ns else 0
                        if ns and nind > indent:
                            child, ni = _parse_yaml_block(lines, ni, nind)
                            if not vt:
                                item_dict[key] = child
                            i = ni
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
                cp = stripped.index(":")
                key = stripped[:cp].strip()
                vt = stripped[cp + 1:].strip()
                if vt.startswith("[") and vt.endswith("]"):
                    inner = vt[1:-1]
                    result[key] = [_parse_yaml_value(x.strip()) for x in inner.split(",")] if inner.strip() else []
                    i += 1
                    continue
                if vt:
                    result[key] = _parse_yaml_value(vt)
                    i += 1
                    continue
                ni = i + 1
                while ni < len(lines) and not lines[ni].strip():
                    ni += 1
                if ni < len(lines) and _count_indent(lines[ni]) > base_indent:
                    child, ni = _parse_yaml_block(lines, ni, _count_indent(lines[ni]))
                    result[key] = child
                    i = ni
                    continue
                result[key] = None
                i += 1
                continue
        i += 1
    return (result_list, i) if is_list else (result, i)


# ---------------------------------------------------------------------------
# Config & Session
# ---------------------------------------------------------------------------

def load_layer_config(layer):
    config_path = CONFIGS_DIR / f"{layer}.yaml"
    if not config_path.exists():
        return None
    return load_yaml(config_path)


def _session_id(layer, source):
    key = f"revise:{layer}:{source or 'broad'}"
    h = hashlib.md5(key.encode()).hexdigest()[:8]
    return f"revise-{layer}-{h}"


def _session_path(sid):
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    return REVIEWS_DIR / f"session-{sid}.json"


def _load_session(sid):
    p = _session_path(sid)
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def _save_session(sid, data):
    p = _session_path(sid)
    p.parent.mkdir(parents=True, exist_ok=True)
    json.dump(data, open(p, "w", encoding="utf-8"), indent=2)


def _write_action(data):
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    json.dump(data, open(ACTION_FILE, "w", encoding="utf-8"), indent=2)


def _read_result():
    if not RESULT_FILE.exists():
        return None
    return json.load(open(RESULT_FILE, encoding="utf-8"))


def _output(data):
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Feedback Gathering
# ---------------------------------------------------------------------------

def _gather_feedback(config, source=None, signals=None):
    """Gather feedback from all configured sources. Returns list of signals."""
    feedback = []
    sources = config.get("feedback_sources", [])

    for src in sources:
        if not isinstance(src, dict):
            continue
        src_type = src.get("type", "")
        glob_pattern = src.get("glob", "")
        filter_text = src.get("filter", "")

        if glob_pattern:
            for match in sorted(SCAFFOLD_DIR.glob(glob_pattern)):
                content = match.read_text(encoding="utf-8") if match.exists() else ""
                if filter_text and filter_text not in content:
                    continue
                # Extract relevant signals from this feedback source
                rel_path = str(match.relative_to(SCAFFOLD_DIR))
                feedback.append({
                    "source_file": rel_path,
                    "source_type": src_type,
                    "content_summary": content[:2000],
                })

    # Filter by --signals if provided
    if signals:
        signal_list = [s.strip() for s in signals.split(",")]
        filtered = []
        for f in feedback:
            for sig in signal_list:
                if sig in f.get("source_file", "") or sig in f.get("content_summary", ""):
                    filtered.append(f)
                    break
        feedback = filtered

    return feedback


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

def cmd_preflight(args):
    config = load_layer_config(args.layer)
    if not config:
        _output({"status": "error", "message": f"No config for layer '{args.layer}'"})
        return

    preflight = config.get("preflight", {})
    for rel_path in preflight.get("required_files", []):
        if not (SCAFFOLD_DIR / rel_path).exists():
            _output({"status": "blocked", "message": preflight.get("blocked_message", "Preflight failed.")})
            return

    _output({"status": "ready", "layer": args.layer})


# ---------------------------------------------------------------------------
# Next Action
# ---------------------------------------------------------------------------

def cmd_next_action(args):
    config = load_layer_config(args.layer)
    if not config:
        _write_action({"action": "blocked", "message": f"No config for layer '{args.layer}'"})
        return

    sid = _session_id(args.layer, args.source)
    session = _load_session(sid)

    if not session:
        feedback = _gather_feedback(config, args.source, args.signals)

        if not feedback:
            _write_action({
                "action": "done",
                "session_id": sid,
                "message": f"No feedback signals found for {args.layer}. Nothing to revise.",
            })
            return

        session = {
            "session_id": sid,
            "layer": args.layer,
            "source": args.source or "",
            "signals_arg": args.signals or "",
            "feedback": feedback,
            "feedback_index": 0,
            "phase": "classify",
            "classifications": [],
            "auto_updates": [],
            "escalations": [],
            "created": datetime.now().isoformat(),
        }
        _save_session(sid, session)

    _advance(session, config)


def _advance(session, config):
    """Write the next action."""
    phase = session.get("phase", "classify")
    sid = session["session_id"]

    if phase == "classify":
        # Send one feedback signal at a time for classification
        idx = session.get("feedback_index", 0)
        feedback = session.get("feedback", [])

        if idx >= len(feedback):
            # All classified — move to apply auto-updates
            if session.get("auto_updates"):
                session["phase"] = "apply"
            elif session.get("escalations"):
                session["phase"] = "escalate"
            else:
                session["phase"] = "report"
            _save_session(sid, session)
            _advance(session, config)
            return

        signal = feedback[idx]
        _write_action({
            "action": "classify",
            "session_id": sid,
            "layer": session["layer"],
            "signal": signal,
            "signal_index": idx + 1,
            "total_signals": len(feedback),
            "classification_rules": config.get("classification_rules", []),
            "safe_patterns": config.get("safe_patterns", []),
            "escalation_patterns": config.get("escalation_patterns", []),
            "message": f"Classify signal {idx + 1}/{len(feedback)}: {signal.get('source_file', '')}",
        })

    elif phase == "apply":
        # Apply auto-updates
        _write_action({
            "action": "apply",
            "session_id": sid,
            "layer": session["layer"],
            "updates": session["auto_updates"],
            "editable_files": config.get("editable_files", []),
            "message": f"Apply {len(session['auto_updates'])} safe auto-updates.",
        })

    elif phase == "escalate":
        # Present escalations to user
        _write_action({
            "action": "escalate",
            "session_id": sid,
            "layer": session["layer"],
            "escalations": session["escalations"],
            "message": f"{len(session['escalations'])} items require human decision.",
        })

    elif phase == "restabilize":
        # Collect changed sections PER FILE from auto-updates and escalations
        per_file_sections = {}  # file_path → set of section names

        for update in session.get("auto_updates", []):
            sec = update.get("affected_section", "")
            # Try to determine which file was affected
            update_desc = update.get("update_description", "")
            # Look for SYS-###, SPEC-###, etc. in the description
            file_ids = re.findall(r"(SYS|SPEC|TASK|SLICE|PHASE)-\d+", update_desc)
            if not file_ids:
                file_ids = re.findall(r"(SYS|SPEC|TASK|SLICE|PHASE)-\d+",
                                     update.get("signal", {}).get("content_summary", ""))

            if sec:
                parent = sec.lstrip("#").strip().split(" — ")[0].strip()
                for fid in file_ids:
                    per_file_sections.setdefault(fid, set()).add(parent)
                if not file_ids:
                    per_file_sections.setdefault("_unassigned", set()).add(parent)

        for esc in session.get("escalations", []):
            sec = esc.get("affected_section", "")
            esc_desc = esc.get("reason", "")
            file_ids = re.findall(r"(SYS|SPEC|TASK|SLICE|PHASE)-\d+", esc_desc)
            if not file_ids:
                file_ids = re.findall(r"(SYS|SPEC|TASK|SLICE|PHASE)-\d+",
                                     esc.get("signal", {}).get("content_summary", ""))
            if sec:
                for part in sec.split(","):
                    parent = part.strip().lstrip("#").strip()
                    for fid in file_ids:
                        per_file_sections.setdefault(fid, set()).add(parent)
                    if not file_ids:
                        per_file_sections.setdefault("_unassigned", set()).add(parent)

        # Build per-file review commands
        reviews = []
        for file_id, sections in per_file_sections.items():
            if file_id == "_unassigned":
                continue
            sections_arg = ",".join(sorted(sections))
            reviews.append({
                "target": file_id,
                "sections": sections_arg,
            })

        # If no per-file mapping, fall back to layer-wide with all sections
        if not reviews:
            all_sections = set()
            for secs in per_file_sections.values():
                all_sections.update(secs)
            reviews.append({
                "target": "",
                "sections": ",".join(sorted(all_sections)) if all_sections else "",
            })

        _write_action({
            "action": "restabilize",
            "session_id": sid,
            "layer": session["layer"],
            "reviews": reviews,
            "message": f"Restabilize {len(reviews)} file(s) — each scoped to its changed sections only.",
        })

    elif phase == "report":
        _write_action({
            "action": "report",
            "session_id": sid,
            "layer": session["layer"],
            "auto_updates": session.get("auto_updates", []),
            "escalations": session.get("escalations", []),
            "classifications": session.get("classifications", []),
            "message": "Revision complete.",
        })

    else:
        _write_action({"action": "done", "session_id": sid})


# ---------------------------------------------------------------------------
# Resolve
# ---------------------------------------------------------------------------

def cmd_resolve(args):
    session = _load_session(args.session)
    if not session:
        _write_action({"action": "blocked", "message": f"Session not found: {args.session}"})
        return

    config = load_layer_config(session["layer"])
    result = _read_result()
    if RESULT_FILE.exists():
        RESULT_FILE.unlink()

    if not result:
        _advance(session, config)
        return

    sid = session["session_id"]
    phase = session.get("phase", "classify")

    if phase == "classify":
        classification = result.get("classification", "skip")
        signal = session["feedback"][session.get("feedback_index", 0)]

        session["classifications"].append({
            "signal": signal,
            "classification": classification,
            "reasoning": result.get("reasoning", ""),
        })

        if classification == "auto_update":
            session["auto_updates"].append({
                "signal": signal,
                "update_description": result.get("update_description", ""),
                "affected_section": result.get("affected_section", ""),
            })
        elif classification == "escalate":
            session["escalations"].append({
                "signal": signal,
                "reason": result.get("reasoning", ""),
                "options": result.get("options", []),
                "affected_section": result.get("affected_section", ""),
            })
        # skip = no action needed

        session["feedback_index"] = session.get("feedback_index", 0) + 1
        _save_session(sid, session)
        _advance(session, config)

    elif phase == "apply":
        session["phase"] = "escalate" if session.get("escalations") else "restabilize"
        _save_session(sid, session)
        _advance(session, config)

    elif phase == "escalate":
        # User resolved escalations
        session["phase"] = "restabilize"
        _save_session(sid, session)
        _advance(session, config)

    elif phase == "restabilize":
        session["phase"] = "report"
        _save_session(sid, session)
        _advance(session, config)

    elif phase == "report":
        session["phase"] = "done"
        _save_session(sid, session)
        _write_action({
            "action": "done",
            "session_id": sid,
            "report_summary": result.get("report_summary", ""),
        })

    else:
        _advance(session, config)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Revise orchestrator")
    subparsers = parser.add_subparsers(dest="command")

    p_pre = subparsers.add_parser("preflight")
    p_pre.add_argument("--layer", required=True)

    p_next = subparsers.add_parser("next-action")
    p_next.add_argument("--layer", required=True)
    p_next.add_argument("--source", default="")
    p_next.add_argument("--signals", default="")

    p_res = subparsers.add_parser("resolve")
    p_res.add_argument("--session", required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"preflight": cmd_preflight, "next-action": cmd_next_action, "resolve": cmd_resolve}[args.command](args)


if __name__ == "__main__":
    main()
