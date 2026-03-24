#!/usr/bin/env python3
"""
Shared utility functions for scaffold orchestrators.

Provides mechanical operations that don't need Claude's judgment:
- complete: mark a document as Complete (status, rename, index)
- build_and_test: run build commands and test suites
- reorder_tasks: topological sort by dependencies
- These can be called as standalone commands or imported by orchestrators.

Commands:
    complete     Mark a scaffold doc as Complete.
    build-test   Run build and test commands.
    reorder      Topological sort tasks by dependency.
"""

import json
import os
import sys
import argparse
import re
import subprocess
from pathlib import Path
from datetime import datetime


TOOLS_DIR = Path(__file__).parent
SCAFFOLD_DIR = TOOLS_DIR.parent
PROJECT_ROOT = SCAFFOLD_DIR.parent


# ---------------------------------------------------------------------------
# Complete — Mark doc as Complete
# ---------------------------------------------------------------------------

def complete_doc(doc_path, scaffold_dir=None, ripple=True):
    """Mark a scaffold document as Complete. Updates status, renames file, updates index.
    If ripple=True, checks parent docs and completes them if all children are done."""
    sd = Path(scaffold_dir) if scaffold_dir else SCAFFOLD_DIR
    abs_path = sd / doc_path if not Path(doc_path).is_absolute() else Path(doc_path)

    if not abs_path.exists():
        return {"status": "error", "message": f"File not found: {doc_path}"}

    result = _complete_single(abs_path, sd)

    # Ripple upward: task → spec → slice → phase
    if ripple:
        rippled = _ripple_complete(abs_path, sd)
        result["rippled"] = rippled

    return result


def _complete_single(abs_path, sd):
    """Mark one doc as Complete. Returns result dict."""
    content = abs_path.read_text(encoding="utf-8")

    # Update status field
    content = re.sub(
        r"(>\s*\*\*Status:\*\*)\s*\w+",
        r"\1 Complete",
        content
    )

    # Update Last Updated
    today = datetime.now().strftime("%Y-%m-%d")
    content = re.sub(
        r"(>\s*\*\*Last Updated:\*\*)\s*[\d-]+",
        rf"\1 {today}",
        content
    )

    # Add changelog entry
    changelog_match = re.search(r"(>\s*\*\*Changelog:\*\*)", content)
    if changelog_match:
        insert_pos = content.find("\n", changelog_match.end())
        if insert_pos != -1:
            entry = f"\n> - {today}: Status → Complete."
            content = content[:insert_pos] + entry + content[insert_pos:]

    abs_path.write_text(content, encoding="utf-8")

    # Rename file — change status suffix
    old_name = abs_path.name
    new_name = re.sub(r"_(draft|review|approved)", "_complete", old_name)
    if new_name != old_name:
        new_path = abs_path.parent / new_name
        abs_path.rename(new_path)
        abs_path = new_path

    # Update index
    index_files = list(abs_path.parent.glob("_index.md"))
    if index_files:
        index_path = index_files[0]
        index_content = index_path.read_text(encoding="utf-8")
        index_content = index_content.replace(old_name, new_name)
        index_content = re.sub(
            rf"(\|\s*\[?{re.escape(old_name.split('_')[0])}[^\|]*\|[^\|]*\|)\s*\w+\s*\|",
            rf"\1 Complete |",
            index_content
        )
        index_path.write_text(index_content, encoding="utf-8")

    return {
        "status": "ok",
        "file": str(abs_path.relative_to(sd)),
        "old_name": old_name,
        "new_name": new_name,
    }


def _ripple_complete(completed_path, sd):
    """Check if completing this doc triggers parent completion. Ripples upward.
    Also updates parent docs' tables to reflect the new status."""
    rippled = []
    name = completed_path.name
    completed_id = re.search(r"(TASK|SPEC|SLICE|PHASE)-\d+", name)
    completed_id = completed_id.group() if completed_id else ""

    # Determine doc type and find parent
    if "TASK-" in name:
        # Update parent slice's Tasks table with this task's new status
        _update_parent_table_status(sd, "slices", completed_id, "Complete")

        # Task → Spec: check if all tasks for parent spec are Complete
        parent_spec_id = _find_parent_ref(completed_path, "Implements")
        if parent_spec_id:
            spec_files = list(sd.glob(f"specs/{parent_spec_id}-*.md"))
            if spec_files and _all_children_complete(sd, spec_files[0], "tasks", "Implements"):
                result = _complete_single(spec_files[0], sd)
                rippled.append({"doc": result.get("file", ""), "type": "spec"})
                # Update parent slice's Specs table
                _update_parent_table_status(sd, "slices", parent_spec_id, "Complete")
                # Spec → Slice
                rippled.extend(_ripple_complete(spec_files[0], sd))

    elif "SPEC-" in name:
        # Update parent slice's Specs table
        _update_parent_table_status(sd, "slices", completed_id, "Complete")

        # Spec → Slice: check if all specs in parent slice are Complete
        parent_slice = _find_parent_slice(completed_path, sd)
        if parent_slice:
            if _all_specs_in_slice_complete(sd, parent_slice):
                result = _complete_single(parent_slice, sd)
                rippled.append({"doc": result.get("file", ""), "type": "slice"})
                slice_id = re.search(r"SLICE-\d+", parent_slice.name)
                if slice_id:
                    # Update parent phase's slice references
                    _update_parent_table_status(sd, "phases", slice_id.group(), "Complete")
                # Slice → Phase
                rippled.extend(_ripple_complete(parent_slice, sd))

    elif "SLICE-" in name:
        # Update parent phase
        parent_phase_id = _find_parent_ref(completed_path, "Phase")
        if parent_phase_id:
            _update_parent_table_status(sd, "phases", completed_id, "Complete")

            phase_files = list(sd.glob(f"phases/{parent_phase_id}-*.md"))
            if phase_files and _all_children_complete_by_phase(sd, phase_files[0]):
                result = _complete_single(phase_files[0], sd)
                rippled.append({"doc": result.get("file", ""), "type": "phase"})
                # Update roadmap with phase completion
                _update_roadmap_phase_status(sd, parent_phase_id, "Complete")

    elif "PHASE-" in name:
        # Update roadmap
        _update_roadmap_phase_status(sd, completed_id, "Complete")

    return rippled


def _update_parent_table_status(sd, parent_dir, child_id, new_status):
    """Update a child's status in parent doc tables (e.g., slice's Tasks/Specs table)."""
    for parent_file in sd.glob(f"{parent_dir}/*-*.md"):
        if parent_file.name.startswith("_"):
            continue
        content = parent_file.read_text(encoding="utf-8")
        if child_id in content:
            # Find table rows containing this child ID and update status
            updated = re.sub(
                rf"(\|\s*{re.escape(child_id)}\s*\|.*?\|)\s*\w+\s*\|",
                rf"\1 {new_status} |",
                content
            )
            if updated != content:
                parent_file.write_text(updated, encoding="utf-8")
                return True
    return False


def _update_roadmap_phase_status(sd, phase_id, new_status):
    """Update a phase's status in the roadmap."""
    roadmap = sd / "phases" / "roadmap.md"
    if not roadmap.exists():
        return False
    content = roadmap.read_text(encoding="utf-8")
    updated = re.sub(
        rf"(\|\s*{re.escape(phase_id)}\s*\|.*?\|)\s*\w+\s*\|",
        rf"\1 {new_status} |",
        content
    )
    if updated != content:
        # Also add completion date
        today = datetime.now().strftime("%Y-%m-%d")
        updated = re.sub(
            rf"(\|\s*{re.escape(phase_id)}[^\n]*){new_status}\s*\|",
            rf"\1{new_status} ({today}) |",
            updated
        )
        roadmap.write_text(updated, encoding="utf-8")
        return True
    return False


def _find_parent_ref(doc_path, field_name):
    """Extract a parent reference field (e.g., Implements: SPEC-001) from a doc."""
    if not doc_path.exists():
        return None
    content = doc_path.read_text(encoding="utf-8")
    match = re.search(rf">\s*\*\*{field_name}:\*\*\s*(\S+)", content)
    if match:
        val = match.group(1).strip()
        if val != "—" and val != "None":
            return val
    return None


def _find_parent_slice(spec_path, sd):
    """Find which slice contains this spec by scanning slice files."""
    spec_id = re.search(r"SPEC-\d+", spec_path.name)
    if not spec_id:
        return None
    spec_id = spec_id.group()
    for slice_file in sd.glob("slices/SLICE-*-*.md"):
        content = slice_file.read_text(encoding="utf-8")
        if spec_id in content:
            return slice_file
    return None


def _all_children_complete(sd, parent_path, child_dir, ref_field):
    """Check if all children referencing this parent are Complete.
    Returns False if there are zero children (no vacuous truth — a spec
    with no tasks is not 'done')."""
    parent_id = re.search(r"(SYS|SPEC|TASK|SLICE|PHASE)-\d+", parent_path.name)
    if not parent_id:
        return False
    parent_id = parent_id.group()

    found_any = False
    for child_file in sd.glob(f"{child_dir}/*-*.md"):
        if child_file.name.startswith("_"):
            continue
        content = child_file.read_text(encoding="utf-8")
        # Check if this child references our parent
        if parent_id in content:
            ref_match = re.search(rf">\s*\*\*{ref_field}:\*\*\s*{re.escape(parent_id)}", content)
            if ref_match:
                found_any = True
                status_match = re.search(r">\s*\*\*Status:\*\*\s*(\w+)", content)
                if status_match and status_match.group(1) != "Complete":
                    return False

    return found_any  # False if no children exist


def _all_specs_in_slice_complete(sd, slice_path):
    """Check if all specs listed in a slice's Specs Included table are Complete.
    Returns False if no specs found (empty slice can't be Complete)."""
    content = slice_path.read_text(encoding="utf-8")
    # Extract spec IDs only from the Specs Included section, not the whole file
    specs_section = ""
    in_section = False
    for line in content.splitlines():
        if "### Specs Included" in line:
            in_section = True
            continue
        if in_section and line.strip().startswith("##"):
            break
        if in_section:
            specs_section += line + "\n"

    spec_ids = set(re.findall(r"SPEC-\d+", specs_section))
    if not spec_ids:
        return False  # no specs = not complete

    for spec_id in spec_ids:
        spec_files = list(sd.glob(f"specs/{spec_id}-*.md"))
        if spec_files:
            spec_content = spec_files[0].read_text(encoding="utf-8")
            status = re.search(r">\s*\*\*Status:\*\*\s*(\w+)", spec_content)
            if status and status.group(1) != "Complete":
                return False
        else:
            return False  # spec file missing = not complete
    return True


def _all_children_complete_by_phase(sd, phase_path):
    """Check if all slices in a phase are Complete.
    Returns False if no slices found (empty phase can't be Complete)."""
    phase_id = re.search(r"PHASE-\d+", phase_path.name)
    if not phase_id:
        return False
    phase_id = phase_id.group()

    found_any = False
    for slice_file in sd.glob("slices/SLICE-*-*.md"):
        content = slice_file.read_text(encoding="utf-8")
        if phase_id in content:
            phase_ref = re.search(rf">\s*\*\*Phase:\*\*\s*{re.escape(phase_id)}", content)
            if phase_ref:
                found_any = True
                status = re.search(r">\s*\*\*Status:\*\*\s*(\w+)", content)
                if status and status.group(1) != "Complete":
                    return False

    return found_any  # False if no slices exist for this phase


# ---------------------------------------------------------------------------
# Build and Test — Run build commands
# ---------------------------------------------------------------------------

def build_and_test(files=None, skip_unit=False, skip_lint=False, project_root=None):
    """Run build and test commands. Returns pass/fail with details."""
    root = Path(project_root) if project_root else PROJECT_ROOT
    results = {"passed": True, "steps": [], "error": ""}

    # Detect build system
    if (root / "SConstruct").exists():
        # Godot/SCons build
        build_cmd = ["scons", "-j4"]
        result = _run_cmd(build_cmd, root)
        results["steps"].append({"name": "scons build", "passed": result["passed"], "output": result["output"][:500]})
        if not result["passed"]:
            results["passed"] = False
            results["error"] = result["output"][:1000]
            return results

    elif (root / "Cargo.toml").exists():
        result = _run_cmd(["cargo", "build"], root)
        results["steps"].append({"name": "cargo build", "passed": result["passed"], "output": result["output"][:500]})
        if not result["passed"]:
            results["passed"] = False
            results["error"] = result["output"][:1000]
            return results

    # Lint
    if not skip_lint:
        if (root / ".gdlintrc").exists() or (root / "game" / ".gdlintrc").exists():
            lint_files = files or []
            gd_files = [f for f in lint_files if f.endswith(".gd")]
            if gd_files:
                for gd_file in gd_files:
                    result = _run_cmd(["gdlint", gd_file], root)
                    results["steps"].append({"name": f"gdlint {gd_file}", "passed": result["passed"]})
                    if not result["passed"]:
                        results["passed"] = False
                        results["error"] += f"\ngdlint {gd_file}: {result['output'][:200]}"

    # Tests
    if not skip_unit:
        # GUT tests
        gut_dirs = list(root.glob("**/addons/gut")) + list(root.glob("**/addons/GUT"))
        if gut_dirs:
            result = _run_cmd(["godot", "--headless", "--script", "addons/gut/gut_cmdln.gd"], root)
            results["steps"].append({"name": "GUT tests", "passed": result["passed"], "output": result["output"][:500]})
            if not result["passed"]:
                results["passed"] = False
                results["error"] += f"\nGUT: {result['output'][:500]}"

        # Cargo tests
        if (root / "Cargo.toml").exists():
            result = _run_cmd(["cargo", "test"], root)
            results["steps"].append({"name": "cargo test", "passed": result["passed"]})
            if not result["passed"]:
                results["passed"] = False
                results["error"] += f"\ncargo test: {result['output'][:500]}"

    return results


def _run_cmd(cmd, cwd):
    """Run a shell command and return result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(cwd))
        return {
            "passed": result.returncode == 0,
            "output": result.stdout + result.stderr,
        }
    except FileNotFoundError:
        return {"passed": False, "output": f"Command not found: {cmd[0]}"}
    except subprocess.TimeoutExpired:
        return {"passed": False, "output": f"Timeout after 300s: {' '.join(cmd)}"}


# ---------------------------------------------------------------------------
# Reorder Tasks — Topological sort by dependency
# ---------------------------------------------------------------------------

def reorder_tasks(task_dir=None, scaffold_dir=None):
    """Topological sort tasks by Depends on field. Returns ordered list."""
    sd = Path(scaffold_dir) if scaffold_dir else SCAFFOLD_DIR
    tdir = sd / (task_dir or "tasks")

    tasks = {}
    for task_file in sorted(tdir.glob("TASK-*-*.md")):
        content = task_file.read_text(encoding="utf-8")
        task_id_match = re.search(r"TASK-\d+", task_file.name)
        if not task_id_match:
            continue
        task_id = task_id_match.group()

        deps = []
        dep_match = re.search(r">\s*\*\*Depends on:\*\*\s*(.+)", content)
        if dep_match:
            dep_text = dep_match.group(1).strip()
            if dep_text != "—" and dep_text != "None":
                deps = re.findall(r"TASK-\d+", dep_text)

        tasks[task_id] = {
            "id": task_id,
            "file": str(task_file.relative_to(sd)),
            "depends_on": deps,
        }

    # Kahn's algorithm
    in_degree = {tid: 0 for tid in tasks}
    graph = {tid: [] for tid in tasks}

    for tid, task in tasks.items():
        for dep in task["depends_on"]:
            if dep in graph:
                graph[dep].append(tid)
                in_degree[tid] += 1

    queue = sorted([tid for tid, deg in in_degree.items() if deg == 0])
    ordered = []

    while queue:
        node = queue.pop(0)
        ordered.append(tasks[node])
        for neighbor in sorted(graph.get(node, [])):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Cycle detection
    remaining = [tasks[tid] for tid in tasks if tid not in [t["id"] for t in ordered]]
    for r in remaining:
        r["_cycle"] = True
        ordered.append(r)

    return ordered


# ---------------------------------------------------------------------------
# Sync Reference Docs — Update refs from code/doc changes
# ---------------------------------------------------------------------------

def sync_reference_docs(changed_files=None, scaffold_dir=None):
    """Sync reference docs with implementation changes.
    Updates signal-registry, entity-components, authority when code changes
    introduce new signals, entities, or state ownership."""
    sd = Path(scaffold_dir) if scaffold_dir else SCAFFOLD_DIR
    updates = []

    # Scan changed files for new signals
    signal_registry = sd / "reference" / "signal-registry.md"
    if signal_registry.exists() and changed_files:
        registry_content = signal_registry.read_text(encoding="utf-8")
        for f in changed_files:
            abs_f = (sd.parent / f) if not Path(f).is_absolute() else Path(f)
            if abs_f.exists() and abs_f.suffix in (".cpp", ".h", ".gd"):
                code = abs_f.read_text(encoding="utf-8")
                # Find signal definitions
                for match in re.finditer(r'ADD_SIGNAL\(MethodInfo\("(\w+)"', code):
                    signal_name = match.group(1)
                    if signal_name not in registry_content:
                        updates.append({
                            "doc": "reference/signal-registry.md",
                            "type": "new_signal",
                            "detail": f"Signal '{signal_name}' found in {f} but not in registry",
                        })

    # Scan for new entity properties
    entity_doc = sd / "reference" / "entity-components.md"
    if entity_doc.exists() and changed_files:
        entity_content = entity_doc.read_text(encoding="utf-8")
        for f in changed_files:
            abs_f = (sd.parent / f) if not Path(f).is_absolute() else Path(f)
            if abs_f.exists() and abs_f.suffix in (".cpp", ".h"):
                code = abs_f.read_text(encoding="utf-8")
                for match in re.finditer(r'ClassDB::bind_method.*"(get|set)_(\w+)"', code):
                    prop = match.group(2)
                    if prop not in entity_content:
                        updates.append({
                            "doc": "reference/entity-components.md",
                            "type": "new_property",
                            "detail": f"Property '{prop}' found in {f} but not in entity-components",
                        })

    # Confidence filter: only surface findings that are likely real
    # Keep: concrete declarations (ADD_SIGNAL, bind_method) — these are always real
    # Keep: findings that appear across ≥2 files
    # Filter: single-file vague pattern matches
    confident_updates = []
    name_counts = {}
    for u in updates:
        # Extract the identifier name from the detail string
        name_match = re.search(r"'(\w+)'", u.get("detail", ""))
        name = name_match.group(1) if name_match else u.get("detail", "")
        key = f"{u['type']}:{name}"
        name_counts[key] = name_counts.get(key, 0) + 1

    for u in updates:
        name_match = re.search(r"'(\w+)'", u.get("detail", ""))
        name = name_match.group(1) if name_match else u.get("detail", "")
        key = f"{u['type']}:{name}"
        # Concrete declarations are always kept; vague matches need ≥2 occurrences
        if u["type"] in ("new_signal", "new_property") or name_counts.get(key, 0) >= 2:
            confident_updates.append(u)

    return {"updates": confident_updates, "count": len(confident_updates),
            "filtered_out": len(updates) - len(confident_updates)}


# ---------------------------------------------------------------------------
# Sync Glossary — Scan docs for unglosseried terms
# ---------------------------------------------------------------------------

def sync_glossary(scope="all", scaffold_dir=None):
    """Scan scaffold docs for domain terms not in the glossary.
    Returns proposed additions."""
    sd = Path(scaffold_dir) if scaffold_dir else SCAFFOLD_DIR
    glossary_path = sd / "design" / "glossary.md"

    if not glossary_path.exists():
        return {"status": "error", "message": "No glossary found."}

    glossary_content = glossary_path.read_text(encoding="utf-8")

    # Extract existing terms (case-insensitive)
    existing_terms = set()
    for line in glossary_content.splitlines():
        if "|" in line and line.count("|") >= 3:
            cells = [c.strip() for c in line.split("|")]
            if len(cells) > 1 and cells[1] and not cells[1].startswith("-"):
                existing_terms.add(cells[1].lower())

    # Scan docs for capitalized domain terms not in glossary
    scan_dirs = {
        "all": ["design/systems", "specs", "tasks", "slices", "phases"],
        "design": ["design"],
        "systems": ["design/systems"],
        "references": ["reference"],
        "style": ["design"],
        "input": ["inputs"],
    }

    dirs = scan_dirs.get(scope, scan_dirs["all"])
    found_terms = {}

    for dir_name in dirs:
        scan_dir = sd / dir_name
        if not scan_dir.exists():
            continue
        for doc_file in scan_dir.glob("*.md"):
            if doc_file.name.startswith("_"):
                continue
            content = doc_file.read_text(encoding="utf-8")
            # Find capitalized multi-word terms that look like domain concepts
            for match in re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', content):
                term = match.group(1)
                if term.lower() not in existing_terms and len(term) > 5:
                    if term not in found_terms:
                        found_terms[term] = []
                    found_terms[term].append(str(doc_file.relative_to(sd)))

    # Deduplicate and sort by frequency
    proposals = []
    for term, sources in sorted(found_terms.items(), key=lambda x: -len(x[1])):
        proposals.append({
            "term": term,
            "frequency": len(sources),
            "sources": sources[:3],
        })

    return {"proposals": proposals[:50], "total_found": len(proposals)}


# ---------------------------------------------------------------------------
# Approve — Lifecycle gate for planning docs
# ---------------------------------------------------------------------------

def approve_doc(doc_path, scaffold_dir=None):
    """Approve a scaffold document. Checks preconditions, updates status, renames file."""
    sd = Path(scaffold_dir) if scaffold_dir else SCAFFOLD_DIR
    abs_path = sd / doc_path if not Path(doc_path).is_absolute() else Path(doc_path)

    if not abs_path.exists():
        return {"status": "error", "message": f"File not found: {doc_path}"}

    content = abs_path.read_text(encoding="utf-8")

    # Check current status
    status_match = re.search(r">\s*\*\*Status:\*\*\s*(\w+)", content)
    current_status = status_match.group(1) if status_match else "Unknown"

    if current_status == "Approved":
        return {"status": "skip", "message": f"Already Approved: {doc_path}"}
    if current_status == "Complete":
        return {"status": "skip", "message": f"Already Complete: {doc_path}"}
    if current_status not in ("Draft", "Review"):
        return {"status": "error", "message": f"Cannot approve — status is '{current_status}'"}

    # Check for review freshness (iterate log exists and is newer than file)
    doc_mtime = abs_path.stat().st_mtime
    review_dir = sd / "decisions" / "review"
    doc_stem = abs_path.stem.split("_")[0]
    reviews = sorted(review_dir.glob(f"ITERATE-*{doc_stem}*")) if review_dir.exists() else []

    if not reviews:
        return {"status": "blocked", "message": f"No review log found for {doc_path}. Run /scaffold-review first."}

    latest_review = reviews[-1]
    if doc_mtime > latest_review.stat().st_mtime:
        return {"status": "blocked", "message": f"File modified after last review. Run /scaffold-review again."}

    # Update status
    content = re.sub(r"(>\s*\*\*Status:\*\*)\s*\w+", r"\1 Approved", content)

    today = datetime.now().strftime("%Y-%m-%d")
    content = re.sub(r"(>\s*\*\*Last Updated:\*\*)\s*[\d-]+", rf"\1 {today}", content)

    changelog_match = re.search(r"(>\s*\*\*Changelog:\*\*)", content)
    if changelog_match:
        insert_pos = content.find("\n", changelog_match.end())
        if insert_pos != -1:
            content = content[:insert_pos] + f"\n> - {today}: Status → Approved." + content[insert_pos:]

    abs_path.write_text(content, encoding="utf-8")

    # Rename
    old_name = abs_path.name
    new_name = re.sub(r"_(draft|review)", "_approved", old_name)
    if new_name != old_name:
        new_path = abs_path.parent / new_name
        abs_path.rename(new_path)

    # Update index
    index_files = list(abs_path.parent.glob("_index.md"))
    if index_files:
        idx_content = index_files[0].read_text(encoding="utf-8")
        idx_content = idx_content.replace(old_name, new_name)
        index_files[0].write_text(idx_content, encoding="utf-8")

    return {"status": "ok", "file": new_name, "old_status": current_status}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Scaffold utility functions")
    subparsers = parser.add_subparsers(dest="command")

    # complete
    p_comp = subparsers.add_parser("complete", help="Mark a doc as Complete")
    p_comp.add_argument("doc", help="Document path relative to scaffold/")

    # build-test
    p_build = subparsers.add_parser("build-test", help="Run build and tests")
    p_build.add_argument("--files", nargs="*", default=[], help="Files to lint")
    p_build.add_argument("--skip-unit", action="store_true")
    p_build.add_argument("--skip-lint", action="store_true")

    # reorder
    p_reorder = subparsers.add_parser("reorder", help="Topological sort tasks")
    p_reorder.add_argument("--task-dir", default="tasks")

    # sync-refs
    p_sync = subparsers.add_parser("sync-refs", help="Sync reference docs with code changes")
    p_sync.add_argument("--files", nargs="*", default=[], help="Changed files to scan")

    # sync-glossary
    p_gloss = subparsers.add_parser("sync-glossary", help="Scan for unglosseried terms")
    p_gloss.add_argument("--scope", default="all")

    # approve
    p_approve = subparsers.add_parser("approve", help="Approve a scaffold doc")
    p_approve.add_argument("doc", help="Document path relative to scaffold/")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "complete":
        result = complete_doc(args.doc)
        print(json.dumps(result, indent=2))
    elif args.command == "build-test":
        result = build_and_test(args.files, args.skip_unit, args.skip_lint)
        print(json.dumps(result, indent=2))
    elif args.command == "reorder":
        result = reorder_tasks(args.task_dir)
        print(json.dumps(result, indent=2))
    elif args.command == "sync-refs":
        result = sync_reference_docs(args.files)
        print(json.dumps(result, indent=2))
    elif args.command == "sync-glossary":
        result = sync_glossary(args.scope)
        print(json.dumps(result, indent=2))
    elif args.command == "approve":
        result = approve_doc(args.doc)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
