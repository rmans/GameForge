#!/usr/bin/env python3
"""
Implement orchestrator — manages task implementation end-to-end.

Drives the implementation pipeline step-by-step:
  1. Context loading (smart — only loads what the task needs)
  2. Planning (via sub-skill)
  3. Code writing (one task step at a time via sub-skill)
  4. Testing (delegates to existing skills)
  5. Code review (delegates to existing skills)
  6. Rebuild if review changed code
  7. Reference doc sync
  8. Completion

Maintains a file manifest in session state — never lost.
Handles retry loops with limits. Supports task ranges via
dependency-aware parallelization.

Commands:
    preflight    Check if task is ready for implementation.
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
SCAFFOLD_DIR = TOOLS_DIR.parent
REVIEWS_DIR = SCAFFOLD_DIR / ".reviews" / "implement"
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
# Session
# ---------------------------------------------------------------------------

def _session_id(task_id):
    h = hashlib.md5(task_id.encode()).hexdigest()[:8]
    return f"impl-{task_id}-{h}"


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
# Smart Context Loading
# ---------------------------------------------------------------------------

def _load_task_context(task_file):
    """Read a task file and determine what context docs are needed."""
    abs_path = SCAFFOLD_DIR / task_file
    if not abs_path.exists():
        return None, []

    content = abs_path.read_text(encoding="utf-8")

    # Extract metadata
    task_type = ""
    implements = ""
    depends_on = ""
    type_match = re.search(r">\s*\*\*Task Type:\*\*\s*(.+)", content)
    impl_match = re.search(r">\s*\*\*Implements:\*\*\s*(\S+)", content)
    dep_match = re.search(r">\s*\*\*Depends on:\*\*\s*(.+)", content)

    if type_match:
        task_type = type_match.group(1).strip()
    if impl_match:
        implements = impl_match.group(1).strip()
    if dep_match:
        depends_on = dep_match.group(1).strip()

    # Determine needed context based on task type and content
    needed_docs = []

    # Always need architecture
    needed_docs.append("design/architecture.md")

    # Parent spec
    if implements and implements != "—":
        spec_matches = list(SCAFFOLD_DIR.glob(f"specs/{implements}-*.md"))
        if spec_matches:
            needed_docs.append(str(spec_matches[0].relative_to(SCAFFOLD_DIR)))

    # System design (from spec's System field)
    if implements:
        for spec_file in SCAFFOLD_DIR.glob(f"specs/{implements}-*.md"):
            spec_content = spec_file.read_text(encoding="utf-8")
            sys_match = re.search(r">\s*\*\*System:\*\*\s*(\S+)", spec_content)
            if sys_match:
                sys_id = sys_match.group(1)
                for sys_file in SCAFFOLD_DIR.glob(f"design/systems/{sys_id}-*.md"):
                    needed_docs.append(str(sys_file.relative_to(SCAFFOLD_DIR)))

    # Signals — only if task mentions signals
    if re.search(r"signal|emit|connect", content, re.IGNORECASE):
        if (SCAFFOLD_DIR / "reference/signal-registry.md").exists():
            needed_docs.append("reference/signal-registry.md")

    # Entity components — only if task mentions entities
    if re.search(r"entity|component|colonist|structure|building", content, re.IGNORECASE):
        if (SCAFFOLD_DIR / "reference/entity-components.md").exists():
            needed_docs.append("reference/entity-components.md")

    # Interfaces — only if task mentions cross-system
    if re.search(r"interface|contract|cross-system|handoff", content, re.IGNORECASE):
        if (SCAFFOLD_DIR / "design/interfaces.md").exists():
            needed_docs.append("design/interfaces.md")

    # Engine docs — based on task type
    engine_dir = SCAFFOLD_DIR / "engine"
    if engine_dir.exists():
        if task_type == "foundation":
            # Foundation tasks need scene architecture and coding
            for doc in ["*scene-architecture*", "*coding*"]:
                for match in engine_dir.glob(f"{doc}.md"):
                    needed_docs.append(str(match.relative_to(SCAFFOLD_DIR)))
        elif task_type == "UI":
            for doc in ["*ui*"]:
                for match in engine_dir.glob(f"{doc}.md"):
                    needed_docs.append(str(match.relative_to(SCAFFOLD_DIR)))
        elif task_type in ("behavior", "integration", "wiring"):
            for doc in ["*coding*", "*simulation-runtime*"]:
                for match in engine_dir.glob(f"{doc}.md"):
                    needed_docs.append(str(match.relative_to(SCAFFOLD_DIR)))

    # Deduplicate
    needed_docs = list(dict.fromkeys(needed_docs))

    return {
        "task_file": task_file,
        "task_type": task_type,
        "implements": implements,
        "depends_on": depends_on,
        "content": content[:5000],
    }, needed_docs


# ---------------------------------------------------------------------------
# Extract Steps from Task
# ---------------------------------------------------------------------------

def _extract_task_steps(content):
    """Extract numbered steps from the task's Steps section."""
    steps_section = None
    lines = content.splitlines()
    in_steps = False
    step_lines = []

    for line in lines:
        if re.match(r"^###?\s+Steps", line):
            in_steps = True
            continue
        if in_steps and re.match(r"^###?\s+", line):
            break
        if in_steps:
            step_lines.append(line)

    steps = []
    current_step = None
    for line in step_lines:
        match = re.match(r"^\s*(\d+)\.\s+(.+)", line)
        if match:
            if current_step:
                steps.append(current_step)
            current_step = {"number": int(match.group(1)), "text": match.group(2).strip(), "details": []}
        elif current_step and line.strip():
            current_step["details"].append(line.strip())

    if current_step:
        steps.append(current_step)

    return steps


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

def cmd_preflight(args):
    task_file = _resolve_task(args.task)
    if not task_file:
        _output({"status": "blocked", "message": f"Task file not found for {args.task}"})
        return

    abs_path = SCAFFOLD_DIR / task_file
    content = abs_path.read_text(encoding="utf-8")

    # Check status
    status_match = re.search(r">\s*\*\*Status:\*\*\s*(\w+)", content)
    status = status_match.group(1) if status_match else "Unknown"
    if status == "Complete":
        _output({"status": "blocked", "message": f"{args.task} is already Complete."})
        return

    if status not in ("Draft", "Approved"):
        _output({"status": "blocked", "message": f"{args.task} has status '{status}' — must be Draft or Approved."})
        return

    # Check dependencies
    dep_match = re.search(r">\s*\*\*Depends on:\*\*\s*(.+)", content)
    if dep_match:
        deps = dep_match.group(1).strip()
        if deps != "—" and deps != "None":
            for dep_id in re.findall(r"TASK-\d+", deps):
                dep_files = list(SCAFFOLD_DIR.glob(f"tasks/{dep_id}-*.md"))
                if dep_files:
                    dep_content = dep_files[0].read_text(encoding="utf-8")
                    dep_status = re.search(r">\s*\*\*Status:\*\*\s*(\w+)", dep_content)
                    if dep_status and dep_status.group(1) != "Complete":
                        _output({"status": "blocked", "message": f"Dependency {dep_id} is not Complete (status: {dep_status.group(1)})."})
                        return

    _output({"status": "ready", "task": args.task, "file": task_file})


# ---------------------------------------------------------------------------
# Next Action
# ---------------------------------------------------------------------------

def cmd_next_action(args):
    task_file = _resolve_task(args.task)
    if not task_file:
        _write_action({"action": "blocked", "message": f"Task not found: {args.task}"})
        return

    sid = _session_id(args.task)
    session = _load_session(sid)

    if not session:
        # Load context
        task_info, needed_docs = _load_task_context(task_file)
        if not task_info:
            _write_action({"action": "blocked", "message": f"Cannot read task: {task_file}"})
            return

        steps = _extract_task_steps(task_info["content"])

        session = {
            "session_id": sid,
            "task_id": args.task,
            "task_file": task_file,
            "task_info": task_info,
            "context_docs": needed_docs,
            "steps": steps,
            "phase": "plan",
            "step_index": 0,
            "file_manifest": [],
            "build_attempts": 0,
            "max_build_attempts": args.max_retries or 3,
            "code_review_iterations": args.cri or 10,
            "review_changed_files": False,
            "results": {
                "files_created": [],
                "files_modified": [],
                "tests_added": 0,
                "build_status": None,
                "review_stats": None,
            },
            "created": datetime.now().isoformat(),
        }
        _save_session(sid, session)

    _advance(session)


def _advance(session):
    """Write the next action based on session phase."""
    phase = session.get("phase", "plan")
    sid = session["session_id"]

    if phase == "plan":
        _write_action({
            "action": "plan",
            "session_id": sid,
            "task_id": session["task_id"],
            "task_file": session["task_file"],
            "task_info": session["task_info"],
            "context_docs": session["context_docs"],
            "steps": session["steps"],
            "message": f"Plan implementation for {session['task_id']}. Read context docs, produce 5-10 line outline.",
        })

    elif phase == "code":
        idx = session.get("step_index", 0)
        steps = session.get("steps", [])

        if idx >= len(steps):
            session["phase"] = "test"
            _save_session(sid, session)
            _advance(session)
            return

        step = steps[idx]
        _write_action({
            "action": "code",
            "session_id": sid,
            "task_id": session["task_id"],
            "task_file": session["task_file"],
            "step": step,
            "step_number": idx + 1,
            "total_steps": len(steps),
            "file_manifest": session["file_manifest"],
            "context_docs": session["context_docs"],
            "plan": session.get("plan", ""),
            "message": f"Implement step {idx + 1}/{len(steps)}: {step.get('text', '')}",
        })

    elif phase == "test":
        # Tests are written as a code step — same as other implementation steps
        _write_action({
            "action": "code",
            "session_id": sid,
            "task_id": session["task_id"],
            "step": {"number": 0, "text": "Add regression tests for all implemented functionality", "details": [
                "Cover layers 1-6 from the task template",
                "Test each public API method",
                "Test edge cases from the parent spec",
                "Test cross-system integration points",
            ]},
            "step_number": "test",
            "total_steps": "test",
            "file_manifest": session["file_manifest"],
            "context_docs": session["context_docs"],
            "plan": session.get("plan", ""),
            "message": f"Write regression tests for {session['task_id']}. {len(session['file_manifest'])} implementation files.",
        })

    elif phase == "build":
        # Run build directly via utils — no sub-skill needed
        from utils import build_and_test
        attempts = session.get("build_attempts", 0)
        max_attempts = session.get("max_build_attempts", 3)
        build_result = build_and_test(session["file_manifest"])

        session["build_attempts"] = attempts + 1
        if build_result.get("passed"):
            session["results"]["build_status"] = "PASS"
            session["phase"] = "review"
            session["build_attempts"] = 0
        elif session["build_attempts"] >= max_attempts:
            session["results"]["build_status"] = "FAIL (max retries)"
            session["phase"] = "stuck"
            _save_session(sid, session)
            _write_action({
                "action": "stuck",
                "session_id": sid,
                "task_id": session["task_id"],
                "phase": "build",
                "attempts": session["build_attempts"],
                "last_error": build_result.get("error", ""),
                "message": f"Build failed after {session['build_attempts']} attempts.",
            })
            return
        else:
            # Build failed but retries remain — write a build_failed action
            # so Claude can see the error and fix the code
            session["last_build_error"] = build_result.get("error", "")
            _save_session(sid, session)
            _write_action({
                "action": "build_failed",
                "session_id": sid,
                "task_id": session["task_id"],
                "attempt": attempts + 1,
                "max_attempts": max_attempts,
                "error": build_result.get("error", ""),
                "steps": build_result.get("steps", []),
                "file_manifest": session["file_manifest"],
                "message": f"Build failed (attempt {attempts + 1}/{max_attempts}). Fix the error and resolve.",
            })
            return

        _save_session(sid, session)
        _advance(session)

    elif phase == "review":
        _write_action({
            "action": "review",
            "session_id": sid,
            "task_id": session["task_id"],
            "file_manifest": session["file_manifest"],
            "iterations": session.get("code_review_iterations", 10),
            "reviewer": "code",
            "layer": "code",
            "message": f"Code review {len(session['file_manifest'])} files via iterate.py --reviewer code.",
        })

    elif phase == "rebuild":
        # Run rebuild directly via utils — same as build
        from utils import build_and_test
        attempts = session.get("build_attempts", 0)
        max_attempts = session.get("max_build_attempts", 3)
        build_result = build_and_test(session["file_manifest"])

        session["build_attempts"] = attempts + 1
        if build_result.get("passed"):
            session["results"]["build_status"] = "PASS"
            session["phase"] = "sync"
            session["build_attempts"] = 0
        elif session["build_attempts"] >= max_attempts:
            session["results"]["build_status"] = "FAIL (max retries)"
            session["phase"] = "stuck"
            _save_session(sid, session)
            _write_action({
                "action": "stuck",
                "session_id": sid,
                "task_id": session["task_id"],
                "phase": "rebuild",
                "attempts": session["build_attempts"],
                "last_error": build_result.get("error", ""),
                "message": f"Post-review build failed after {session['build_attempts']} attempts.",
            })
            return
        else:
            session["last_build_error"] = build_result.get("error", "")
            _save_session(sid, session)
            _write_action({
                "action": "build_failed",
                "session_id": sid,
                "task_id": session["task_id"],
                "attempt": attempts + 1,
                "max_attempts": max_attempts,
                "error": build_result.get("error", ""),
                "file_manifest": session["file_manifest"],
                "is_post_review": True,
                "message": f"Post-review build failed (attempt {attempts + 1}/{max_attempts}). Fix and resolve.",
            })
            return

        _save_session(sid, session)
        _advance(session)

    elif phase == "sync":
        # Run sync directly via utils — no sub-skill needed
        from utils import sync_reference_docs
        sync_result = sync_reference_docs(session["file_manifest"])
        session["results"]["sync_updates"] = sync_result.get("count", 0)
        session["phase"] = "complete"
        _save_session(sid, session)
        _advance(session)

    elif phase == "complete":
        # Run complete directly via utils — no sub-skill needed
        from utils import complete_doc
        complete_result = complete_doc(session["task_file"])
        session["results"]["complete_status"] = complete_result.get("status", "error")
        session["phase"] = "done"
        _save_session(sid, session)
        _write_action({
            "action": "done",
            "session_id": sid,
            "task_id": session["task_id"],
            "results": session["results"],
            "file_manifest": session["file_manifest"],
            "complete_result": complete_result,
        })

    else:
        _write_action({"action": "done", "session_id": sid, "results": session.get("results", {})})


# ---------------------------------------------------------------------------
# Resolve
# ---------------------------------------------------------------------------

def cmd_resolve(args):
    session = _load_session(args.session)
    if not session:
        _write_action({"action": "blocked", "message": f"Session not found: {args.session}"})
        return

    result = _read_result()
    if RESULT_FILE.exists():
        RESULT_FILE.unlink()

    if not result:
        _advance(session)
        return

    sid = session["session_id"]
    phase = session.get("phase", "plan")

    if phase == "plan":
        session["plan"] = result.get("plan", "")
        session["phase"] = "code"
        session["step_index"] = 0
        _save_session(sid, session)
        _advance(session)

    elif phase == "code":
        # Collect files from this step
        new_files = result.get("files_created", [])
        modified_files = result.get("files_modified", [])
        for f in new_files + modified_files:
            if f not in session["file_manifest"]:
                session["file_manifest"].append(f)

        session["results"]["files_created"].extend(new_files)
        session["results"]["files_modified"].extend(modified_files)
        session["step_index"] = session.get("step_index", 0) + 1
        _save_session(sid, session)
        _advance(session)

    elif phase == "test":
        # Test phase uses the code action — collect files same as code phase
        new_files = result.get("files_created", [])
        modified_files = result.get("files_modified", [])
        for f in new_files + modified_files:
            if f not in session["file_manifest"]:
                session["file_manifest"].append(f)
        session["phase"] = "build"
        session["build_attempts"] = 0
        _save_session(sid, session)
        _advance(session)

    elif phase in ("build", "rebuild"):
        # After build_failed, Claude fixed code and called resolve.
        # Update file manifest with any new/modified files from the fix.
        fixed_files = result.get("files_modified", [])
        for f in fixed_files:
            if f not in session["file_manifest"]:
                session["file_manifest"].append(f)
        # Re-run build (advance will call build_and_test again)
        _save_session(sid, session)
        _advance(session)

    elif phase == "review":
        session["results"]["review_stats"] = result.get("stats", {})
        review_files = result.get("files_modified", [])
        if review_files:
            session["review_changed_files"] = True
            for f in review_files:
                if f not in session["file_manifest"]:
                    session["file_manifest"].append(f)
            session["phase"] = "rebuild"
            session["build_attempts"] = 0
        else:
            session["phase"] = "sync"
        _save_session(sid, session)
        _advance(session)

    elif phase == "complete":
        session["phase"] = "done"
        _save_session(sid, session)
        _write_action({
            "action": "done",
            "session_id": sid,
            "task_id": session["task_id"],
            "results": session["results"],
            "file_manifest": session["file_manifest"],
        })

    else:
        _advance(session)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_task(task_id):
    """Resolve TASK-### to a file path."""
    matches = list(SCAFFOLD_DIR.glob(f"tasks/{task_id}-*.md"))
    if matches:
        return str(matches[0].relative_to(SCAFFOLD_DIR))
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Implement orchestrator")
    subparsers = parser.add_subparsers(dest="command")

    p_pre = subparsers.add_parser("preflight")
    p_pre.add_argument("--task", required=True)

    p_next = subparsers.add_parser("next-action")
    p_next.add_argument("--task", required=True)
    p_next.add_argument("--max-retries", type=int, default=3)
    p_next.add_argument("--cri", type=int, default=10, help="Code review iterations")

    p_res = subparsers.add_parser("resolve")
    p_res.add_argument("--session", required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"preflight": cmd_preflight, "next-action": cmd_next_action, "resolve": cmd_resolve}[args.command](args)


if __name__ == "__main__":
    main()
