#!/usr/bin/env python3
"""
Review orchestrator — chains local-review.py (fix) then iterate.py (adversarial).

Runs the full review pipeline for a document:
  Phase 1: Fix — mechanical checks via local-review.py
  Phase 2: Iterate — adversarial review via iterate.py → adversarial-review.py

Uses the same action.json/result.json exchange as both sub-orchestrators.
The dispatcher skill calls review.py, which delegates to local-review.py and
iterate.py in sequence.

Commands:
    preflight    Check if both fix and iterate are ready.
    next-action  Write action.json — delegates to whichever phase is active.
    resolve      Read result.json — delegates to whichever phase is active.
"""

import json
import os
import sys
import argparse
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TOOLS_DIR = Path(__file__).parent
SCAFFOLD_DIR = TOOLS_DIR.parent
REVIEWS_DIR = SCAFFOLD_DIR / ".reviews" / "review"
ACTION_FILE = REVIEWS_DIR / "action.json"
RESULT_FILE = REVIEWS_DIR / "result.json"
LOCAL_REVIEW = TOOLS_DIR / "local-review.py"
ITERATE = TOOLS_DIR / "iterate.py"

# Sub-orchestrators use their own action/result files
FIX_ACTION = SCAFFOLD_DIR / ".reviews" / "fix" / "action.json"
FIX_RESULT = SCAFFOLD_DIR / ".reviews" / "fix" / "result.json"
ITERATE_ACTION = SCAFFOLD_DIR / ".reviews" / "iterate" / "action.json"
ITERATE_RESULT = SCAFFOLD_DIR / ".reviews" / "iterate" / "result.json"


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

def _session_id(layer, target):
    key = f"review:{layer}:{target}"
    h = hashlib.md5(key.encode()).hexdigest()[:8]
    name = Path(target).stem if target else layer
    return f"review-{name}-{h}"


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


def _output(data):
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Delegate to sub-orchestrator
# ---------------------------------------------------------------------------

def _run_sub(script, args_list):
    """Run a sub-orchestrator command and return its stdout parsed as JSON."""
    cmd = [sys.executable, str(script)] + args_list
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=str(SCAFFOLD_DIR))
        stdout = result.stdout.strip()
        if stdout:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                pass
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _copy_action_from_sub(sub_action_file):
    """Copy the sub-orchestrator's action.json to our action.json, adding phase tag."""
    if sub_action_file.exists():
        with open(sub_action_file, encoding="utf-8") as f:
            data = json.load(f)
        _write_action(data)
        return data
    return None


def _copy_result_to_sub(sub_result_file):
    """Copy our result.json to the sub-orchestrator's result.json."""
    if RESULT_FILE.exists():
        with open(RESULT_FILE, encoding="utf-8") as f:
            data = json.load(f)
        sub_result_file.parent.mkdir(parents=True, exist_ok=True)
        with open(sub_result_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        RESULT_FILE.unlink()
        return data
    return None


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

def cmd_preflight(args):
    """Run preflight for both fix and iterate."""
    fix_result = _run_sub(LOCAL_REVIEW, ["preflight", "--layer", args.layer, "--target", args.target])
    if fix_result and fix_result.get("status") != "ready":
        _output(fix_result)
        return

    iterate_result = _run_sub(ITERATE, ["preflight", "--layer", args.layer, "--target", args.target])
    if iterate_result and iterate_result.get("status") != "ready":
        _output(iterate_result)
        return

    _output({"status": "ready", "layer": args.layer, "target": args.target})


# ---------------------------------------------------------------------------
# Next Action
# ---------------------------------------------------------------------------

def cmd_next_action(args):
    """Start or resume the review session."""
    session_id = _session_id(args.layer, args.target)
    session = _load_session(session_id)

    if not session:
        session = {
            "session_id": session_id,
            "layer": args.layer,
            "target": args.target,
            "phase": "fix",
            "fix_session_id": None,
            "iterate_session_id": None,
            "iterations": args.iterations,
            "max_exchanges": args.max_exchanges,
            "focus": args.focus or "",
            "sections": args.sections or "",
            "fast": args.fast or False,
            "created": datetime.now().isoformat(),
        }
        _save_session(session_id, session)

    phase = session.get("phase", "fix")

    if phase == "fix":
        # Start or resume fix phase
        fix_args = ["next-action", "--layer", args.layer, "--target", args.target]
        if args.iterations:
            fix_args.extend(["--iterations", str(args.iterations)])
        _run_sub(LOCAL_REVIEW, fix_args)

        # Copy fix's action.json to our action.json
        action = _copy_action_from_sub(FIX_ACTION)
        if action and action.get("action") == "done":
            # Fix phase complete — transition to iterate
            session["phase"] = "iterate"
            session["fix_report"] = action.get("report_summary", "")
            _save_session(session_id, session)
            # Write a phase transition action for the dispatcher
            _write_action({
                "action": "phase_complete",
                "session_id": session_id,
                "completed_phase": "fix",
                "next_phase": "iterate",
                "message": "Fix phase complete. Starting adversarial review...",
            })
        return

    if phase == "iterate":
        # Start or resume iterate phase
        iter_args = ["next-action", "--layer", args.layer, "--target", args.target]
        if args.iterations:
            iter_args.extend(["--iterations", str(args.iterations)])
        if args.max_exchanges:
            iter_args.extend(["--max-exchanges", str(args.max_exchanges)])
        if args.focus:
            iter_args.extend(["--focus", args.focus])
        if args.sections:
            iter_args.extend(["--sections", args.sections])
        if args.fast:
            iter_args.append("--fast")
        _run_sub(ITERATE, iter_args)

        # Copy iterate's action.json to our action.json
        action = _copy_action_from_sub(ITERATE_ACTION)
        if action and action.get("action") == "done":
            # Both phases complete
            _write_action({
                "action": "done",
                "session_id": session_id,
                "fix_report": session.get("fix_report", ""),
                "iterate_report": action.get("report_summary", ""),
            })
        return

    # Unknown phase
    _write_action({"action": "done", "session_id": session_id})


# ---------------------------------------------------------------------------
# Resolve
# ---------------------------------------------------------------------------

def cmd_resolve(args):
    """Route result to the active sub-orchestrator."""
    session = _load_session(args.session)
    if not session:
        _write_action({"action": "blocked", "message": f"Session '{args.session}' not found."})
        return

    phase = session.get("phase", "fix")

    if phase == "fix":
        # Copy result to fix's result.json, then call fix resolve
        _copy_result_to_sub(FIX_RESULT)

        # Get fix session ID from the action file
        fix_session_id = session.get("fix_session_id")
        if not fix_session_id:
            # Read it from fix's action.json
            if FIX_ACTION.exists():
                with open(FIX_ACTION, encoding="utf-8") as f:
                    fix_action = json.load(f)
                fix_session_id = fix_action.get("session_id", "")
                session["fix_session_id"] = fix_session_id
                _save_session(args.session, session)

        if fix_session_id:
            _run_sub(LOCAL_REVIEW, ["resolve", "--session", fix_session_id])

        # Copy fix's next action to our action
        action = _copy_action_from_sub(FIX_ACTION)
        if action and action.get("action") == "done":
            # Fix complete — transition to iterate
            session["phase"] = "iterate"
            session["fix_report"] = action.get("report_summary", "")
            _save_session(args.session, session)
            _write_action({
                "action": "phase_complete",
                "session_id": session["session_id"],
                "completed_phase": "fix",
                "next_phase": "iterate",
                "message": "Fix phase complete. Starting adversarial review...",
            })
        return

    if phase == "iterate":
        # Copy result to iterate's result.json, then call iterate resolve
        _copy_result_to_sub(ITERATE_RESULT)

        iterate_session_id = session.get("iterate_session_id")
        if not iterate_session_id:
            if ITERATE_ACTION.exists():
                with open(ITERATE_ACTION, encoding="utf-8") as f:
                    iter_action = json.load(f)
                iterate_session_id = iter_action.get("session_id", "")
                session["iterate_session_id"] = iterate_session_id
                _save_session(args.session, session)

        if iterate_session_id:
            _run_sub(ITERATE, ["resolve", "--session", iterate_session_id])

        # Copy iterate's next action to our action
        action = _copy_action_from_sub(ITERATE_ACTION)
        if action and action.get("action") == "done":
            _write_action({
                "action": "done",
                "session_id": session["session_id"],
                "fix_report": session.get("fix_report", ""),
                "iterate_report": action.get("report_summary", ""),
            })
        return


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Review orchestrator — fix then iterate")
    subparsers = parser.add_subparsers(dest="command")

    p_pre = subparsers.add_parser("preflight")
    p_pre.add_argument("--layer", required=True)
    p_pre.add_argument("--target", default="")

    p_next = subparsers.add_parser("next-action")
    p_next.add_argument("--layer", required=True)
    p_next.add_argument("--target", default="")
    p_next.add_argument("--iterations", type=int, default=None)
    p_next.add_argument("--max-exchanges", type=int, default=None)
    p_next.add_argument("--focus", default="")
    p_next.add_argument("--sections", default="")
    p_next.add_argument("--fast", action="store_true")

    p_res = subparsers.add_parser("resolve")
    p_res.add_argument("--session", required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"preflight": cmd_preflight, "next-action": cmd_next_action, "resolve": cmd_resolve}[args.command](args)


if __name__ == "__main__":
    main()
