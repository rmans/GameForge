#!/usr/bin/env python3
"""
Seed orchestrator — dependency-aware document generation for scaffold.

Reads upstream docs + project state, generates candidates one at a time,
discovers dependencies, verifies coverage, creates files in order.

Uses the same action.json/result.json pattern as iterate/fix/validate.
Claude handles creative work (proposing candidates, verifying coverage)
via focused sub-skills. Python handles inventory, dependency graphs,
topological sorting, and file creation orchestration.

Commands:
    preflight    Check if layer is ready for seeding.
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
CONFIGS_DIR = TOOLS_DIR / "configs" / "seed"
SCAFFOLD_DIR = TOOLS_DIR.parent
REVIEWS_DIR = SCAFFOLD_DIR / ".reviews" / "seed"
ACTION_FILE = REVIEWS_DIR / "action.json"
RESULT_FILE = REVIEWS_DIR / "result.json"


# ---------------------------------------------------------------------------
# YAML Parser (shared)
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
                        ns = lines[next_i].strip()
                        ni = _count_indent(lines[next_i]) if ns else 0
                        if ns and ni > indent:
                            child, next_i = _parse_yaml_block(lines, next_i, ni)
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
                    ni = _count_indent(lines[next_i])
                    if ni > base_indent:
                        child, next_i = _parse_yaml_block(lines, next_i, ni)
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
    key = f"seed:{layer}:{target or 'all'}"
    h = hashlib.md5(key.encode()).hexdigest()[:8]
    return f"seed-{layer}-{h}"


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
# Project State Inventory
# ---------------------------------------------------------------------------

def _build_inventory(config):
    """Build an inventory of what exists in the project."""
    inventory = {
        "scaffold_docs": {},
        "engine_config": {},
        "file_system": {},
    }

    # Existing scaffold docs by type
    doc_patterns = {
        "systems": "design/systems/SYS-*-*.md",
        "specs": "specs/SPEC-*-*.md",
        "tasks": "tasks/TASK-*-*.md",
        "slices": "slices/SLICE-*-*.md",
        "phases": "phases/PHASE-*-*.md",
        "engine": "engine/*.md",
        "style": "design/style-guide.md",
        "references": "reference/*.md",
    }

    for doc_type, pattern in doc_patterns.items():
        matches = sorted(SCAFFOLD_DIR.glob(pattern))
        inventory["scaffold_docs"][doc_type] = [
            str(m.relative_to(SCAFFOLD_DIR)) for m in matches
        ]

    # Engine configuration detection
    project_root = SCAFFOLD_DIR.parent
    engine_indicators = {
        "godot4": {
            "project_file": "project.godot",
            "gdextension": "*.gdextension",
            "scons": "SConstruct",
            "cpp_src": "src/**/*.cpp",
            "gdscript": "**/*.gd",
        },
        "unity": {
            "project_file": "ProjectSettings/ProjectSettings.asset",
        },
        "unreal": {
            "project_file": "*.uproject",
        },
    }

    for engine, indicators in engine_indicators.items():
        for name, pattern in indicators.items():
            matches = list(project_root.glob(pattern))
            if matches:
                inventory["engine_config"][f"{engine}.{name}"] = True
            else:
                inventory["engine_config"][f"{engine}.{name}"] = False

    # Key directories
    for dir_name in ["src", "game", "scripts", "addons", "data", "tests"]:
        dir_path = project_root / dir_name
        inventory["file_system"][dir_name] = dir_path.exists()

    # Game data directories
    game_dir = project_root / "game"
    if game_dir.exists():
        for sub in ["data/balance", "data/content", "data/display", "translations", "tests"]:
            inventory["file_system"][f"game/{sub}"] = (game_dir / sub).exists()

    # Testing tools detection
    testing_tools = {}

    # Test frameworks
    test_framework_indicators = {
        "gut": ["addons/gut", "game/addons/gut", "addons/GUT"],
        "gdunit4": ["addons/gdUnit4"],
        "pytest": ["pytest.ini", "pyproject.toml", "conftest.py"],
        "jest": ["jest.config.js", "jest.config.ts"],
        "vitest": ["vitest.config.ts", "vitest.config.js"],
        "cargo_test": ["Cargo.toml"],
        "dotnet_test": ["*.csproj"],
        "catch2": ["**/catch2/**", "**/Catch2/**"],
        "gtest": ["**/gtest/**", "**/googletest/**"],
        "doctest": ["**/doctest.h"],
    }

    for framework, patterns in test_framework_indicators.items():
        for pattern in patterns:
            if list(project_root.glob(pattern)):
                testing_tools[framework] = True
                break
        if framework not in testing_tools:
            testing_tools[framework] = False

    # Lint tools
    lint_indicators = {
        "gdlint": [".gdlintrc", "game/.gdlintrc"],
        "eslint": [".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml"],
        "prettier": [".prettierrc", ".prettierrc.js", ".prettierrc.json"],
        "clippy": ["Cargo.toml"],  # clippy comes with rust
        "ruff": ["ruff.toml", "pyproject.toml"],
        "mypy": ["mypy.ini", "pyproject.toml"],
        "cppcheck": [".cppcheck"],
        "clang_tidy": [".clang-tidy"],
    }

    for tool, patterns in lint_indicators.items():
        for pattern in patterns:
            if list(project_root.glob(pattern)):
                testing_tools[f"lint.{tool}"] = True
                break
        if f"lint.{tool}" not in testing_tools:
            testing_tools[f"lint.{tool}"] = False

    # CI detection
    ci_indicators = {
        "github_actions": [".github/workflows/*.yml", ".github/workflows/*.yaml"],
        "gitlab_ci": [".gitlab-ci.yml"],
        "jenkins": ["Jenkinsfile"],
        "circleci": [".circleci/config.yml"],
    }

    for ci, patterns in ci_indicators.items():
        for pattern in patterns:
            if list(project_root.glob(pattern)):
                testing_tools[f"ci.{ci}"] = True
                break
        if f"ci.{ci}" not in testing_tools:
            testing_tools[f"ci.{ci}"] = False

    # Test file locations
    test_dir_indicators = {
        "game/tests": game_dir / "tests" if game_dir.exists() else None,
        "game/scripts/test": game_dir / "scripts" / "test" if game_dir.exists() else None,
        "tests": project_root / "tests",
        "test": project_root / "test",
        "spec": project_root / "spec",
        "__tests__": project_root / "__tests__",
    }

    for name, path in test_dir_indicators.items():
        if path and path.exists():
            testing_tools[f"test_dir.{name}"] = True
        else:
            testing_tools[f"test_dir.{name}"] = False

    inventory["testing_tools"] = testing_tools

    return inventory


# ---------------------------------------------------------------------------
# Upstream Requirement Extraction
# ---------------------------------------------------------------------------

def _extract_upstream_requirements(config, inventory):
    """Extract what needs to be seeded from upstream docs.
    Uses heading-based extraction when extract_sections is specified in config,
    falls back to first 3000 chars otherwise."""
    requirements = []
    upstream_sources = config.get("upstream_sources", [])

    for source in upstream_sources:
        if not isinstance(source, dict):
            continue

        source_type = source.get("type", "")
        glob_pattern = source.get("glob", "")
        extract_from = source.get("extract", "")
        extract_sections = source.get("extract_sections", [])

        if glob_pattern:
            matches = sorted(SCAFFOLD_DIR.glob(glob_pattern))
            for match in matches:
                if not match.exists():
                    continue
                content = match.read_text(encoding="utf-8")

                # Heading-based extraction if sections specified
                if extract_sections:
                    parts = []
                    for heading in extract_sections:
                        section = _extract_section_content(content, heading)
                        if section:
                            parts.append(f"{heading}\n{section}")
                    summary = "\n\n".join(parts) if parts else content[:3000]
                else:
                    summary = content[:3000]

                req = {
                    "source_file": str(match.relative_to(SCAFFOLD_DIR)),
                    "source_type": source_type,
                    "content_summary": summary,
                    "extract_rule": extract_from,
                }
                requirements.append(req)

    return requirements


# ---------------------------------------------------------------------------
# Existing Docs Analysis (Delta Mode)
# ---------------------------------------------------------------------------

def _analyze_existing(config, inventory, requirements):
    """Analyze what already exists for this layer. Returns delta info."""
    layer = config.get("layer", "")
    analysis = {
        "has_existing": False,
        "existing_count": 0,
        "existing_files": [],
        "existing_summaries": [],
        "stale": [],
        "missing_sections": [],
    }

    # Find existing docs for this layer using output_pattern, output_files, or target
    output_pattern = config.get("output_pattern", "")
    output_files = config.get("output_files", [])
    target = config.get("target", "")

    existing_paths = []

    if target:
        # Fixed target (design doc, roadmap)
        target_path = SCAFFOLD_DIR / target
        if target_path.exists():
            existing_paths = [target]

    elif output_files:
        # Explicit file list (references, style, input)
        for f in output_files:
            if (SCAFFOLD_DIR / f).exists():
                existing_paths.append(f)

    elif output_pattern:
        # Glob pattern (systems, specs, tasks, slices, phases, engine)
        matches = sorted(SCAFFOLD_DIR.glob(output_pattern))
        existing_paths = [str(m.relative_to(SCAFFOLD_DIR)) for m in matches]

    if existing_paths:
        analysis["has_existing"] = True
        analysis["existing_count"] = len(existing_paths)
        analysis["existing_files"] = existing_paths

        for f in existing_paths:
            abs_path = SCAFFOLD_DIR / f
            if not abs_path.exists():
                continue
            content = abs_path.read_text(encoding="utf-8")

            # Check status
            status_match = re.search(r">\s*\*\*Status:\*\*\s*(\w+)", content)
            status = status_match.group(1) if status_match else "Unknown"

            # Check traceability references
            implements = re.search(r">\s*\*\*Implements:\*\*\s*(\S+)", content)
            system = re.search(r">\s*\*\*System:\*\*\s*(\S+)", content)

            # Check section fill for fixed-target docs
            summary = {
                "file": f,
                "status": status,
                "implements": implements.group(1) if implements else None,
                "system": system.group(1) if system else None,
            }

            # For fixed-target or small file sets, check section completeness
            if target or len(existing_paths) <= 10:
                headings = [line.strip() for line in content.splitlines() if line.strip().startswith("#")]
                filled = 0
                empty = 0
                for heading in headings:
                    heading_text = re.sub(r"^#+\s+", "", heading)
                    section_content = _extract_section_content(content, heading)
                    if section_content:
                        cleaned = re.sub(r"<!--.*?-->", "", section_content, flags=re.DOTALL).strip()
                        if len(cleaned) > 20:
                            filled += 1
                        else:
                            empty += 1
                            analysis["missing_sections"].append(f"{f}: {heading_text}")
                summary["filled_sections"] = filled
                summary["empty_sections"] = empty

            analysis["existing_summaries"].append(summary)

    # Check for stale references (docs that reference things that no longer exist)
    for f in analysis.get("existing_files", []):
        abs_path = SCAFFOLD_DIR / f
        if abs_path.exists():
            content = abs_path.read_text(encoding="utf-8")
            # Check for references to non-existent docs
            for ref_match in re.finditer(r"(SYS|SPEC|TASK|SLICE|PHASE)-\d+", content):
                ref_id = ref_match.group()
                # Try to find the referenced file
                ref_patterns = {
                    "SYS": "design/systems/SYS-*",
                    "SPEC": "specs/SPEC-*",
                    "TASK": "tasks/TASK-*",
                    "SLICE": "slices/SLICE-*",
                    "PHASE": "phases/PHASE-*",
                }
                prefix = re.match(r"(SYS|SPEC|TASK|SLICE|PHASE)", ref_id).group()
                pattern = ref_patterns.get(prefix, "")
                if pattern:
                    matches = list(SCAFFOLD_DIR.glob(f"{pattern}"))
                    ref_found = any(ref_id in str(m) for m in matches)
                    if not ref_found:
                        analysis["stale"].append({
                            "file": f,
                            "reference": ref_id,
                            "issue": f"References {ref_id} but no matching file found",
                        })

    return analysis


def _extract_section_content(doc_content, heading):
    """Extract content after a heading until the next heading of same or higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    heading_text = heading.lstrip("# ").strip()
    pattern = rf"^{'#' * level}\s+{re.escape(heading_text)}\s*$"

    lines = doc_content.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(pattern, line.strip()):
            start = i + 1
            break
    if start is None:
        return None

    end = len(lines)
    for i in range(start, len(lines)):
        line = lines[i].strip()
        if line.startswith("#"):
            match = re.match(r"^(#+)", line)
            if match and len(match.group(1)) <= level:
                end = i
                break

    return "\n".join(lines[start:end])


# ---------------------------------------------------------------------------
# Asset Requirement Extraction (for task seeding)
# ---------------------------------------------------------------------------

# Asset types that map to art vs audio tasks
_ART_TYPES = {"sprite", "mesh", "icon", "ui element", "concept art", "texture", "tileset", "ui mockup"}
_AUDIO_TYPES = {"sfx", "music", "ambience", "voice"}


def _extract_asset_requirements_from_specs(config):
    """Scan approved specs for Asset Requirements with Status: Needed.
    Returns a list of synthetic asset task candidates."""
    if config.get("layer") != "tasks":
        return []

    asset_candidates = []
    specs = sorted(SCAFFOLD_DIR.glob("specs/SPEC-*_approved*.md"))

    for spec_file in specs:
        content = spec_file.read_text(encoding="utf-8")
        spec_rel = str(spec_file.relative_to(SCAFFOLD_DIR))

        # Extract spec ID
        spec_id_match = re.search(r"(SPEC-\d+)", spec_file.name)
        if not spec_id_match:
            continue
        spec_id = spec_id_match.group(1)

        # Extract spec name from the H1 heading
        h1_match = re.search(r"^#\s+SPEC-\d+\s*—\s*(.+)", content, re.MULTILINE)
        spec_name = h1_match.group(1).strip() if h1_match else spec_id

        # Find the Asset Requirements section
        ar_section = _extract_section_content(content, "### Asset Requirements")
        if not ar_section:
            continue

        # Parse table rows for Status: Needed
        art_assets = []
        audio_assets = []
        vague_assets = []  # entries too vague to synthesize a task

        for line in ar_section.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|") or stripped.startswith("|---") or "Requirement" in stripped:
                continue

            cols = [c.strip() for c in stripped.split("|")]
            # | Requirement | Type | Description | Source Section | Satisfied By | Status |
            # cols[0] empty, cols[1]=Req, cols[2]=Type, cols[3]=Desc, cols[4]=Source, cols[5]=Satisfied, cols[6]=Status
            if len(cols) < 7:
                continue

            status = cols[6].strip().lower() if len(cols) > 6 else ""
            if "needed" not in status:
                continue

            asset_type = cols[2].strip().lower()
            description = cols[3].strip()

            # Specificity gate: skip vague entries that can't produce a delivery table
            # A description must be >10 chars and not just template/placeholder text
            if len(description) < 10 or description in ("...", "—", "TODO", "TBD", ""):
                vague_assets.append({"requirement": cols[1], "type": cols[2], "description": description, "spec": spec_id})
                continue

            asset_entry = {
                "requirement": cols[1],
                "type": cols[2],
                "description": description,
                "source_section": cols[4] if len(cols) > 4 else "",
            }

            if asset_type in _ART_TYPES:
                art_assets.append(asset_entry)
            elif asset_type in _AUDIO_TYPES:
                audio_assets.append(asset_entry)

        # Track vague assets for reporting
        if vague_assets:
            asset_candidates.append({
                "_vague_warning": True,
                "spec": spec_id,
                "vague_assets": vague_assets,
            })

        # Create art task candidate if needed
        if art_assets:
            slug = re.sub(r"[^a-z0-9]+", "-", spec_name.lower()).strip("-")
            asset_candidates.append({
                "name": f"{spec_name} Art",
                "proposed_id": None,  # assigned during confirm
                "source": spec_id,
                "source_file": spec_rel,
                "task_type": "art",
                "name_suffix": "_art",
                "depends_on": [],
                "assets": art_assets,
                "prompt_context_docs": ["design/style-guide.md", "design/color-system.md"],
                "_synthetic": True,
            })

        # Create audio task candidate if needed
        if audio_assets:
            slug = re.sub(r"[^a-z0-9]+", "-", spec_name.lower()).strip("-")
            asset_candidates.append({
                "name": f"{spec_name} Audio",
                "proposed_id": None,
                "source": spec_id,
                "source_file": spec_rel,
                "task_type": "audio",
                "name_suffix": "_audio",
                "depends_on": [],
                "assets": audio_assets,
                "prompt_context_docs": ["design/style-guide.md", "design/audio-direction.md"],
                "_synthetic": True,
            })

    return asset_candidates


# ---------------------------------------------------------------------------
# Dependency Graph
# ---------------------------------------------------------------------------

def _topological_sort(candidates):
    """Sort candidates by dependencies. Returns ordered list."""
    # Build adjacency
    id_to_candidate = {c.get("proposed_id", f"c{i}"): c for i, c in enumerate(candidates)}
    in_degree = {cid: 0 for cid in id_to_candidate}
    graph = {cid: [] for cid in id_to_candidate}

    for cid, candidate in id_to_candidate.items():
        for dep in candidate.get("depends_on", []):
            if dep in graph:
                graph[dep].append(cid)
                in_degree[cid] = in_degree.get(cid, 0) + 1

    # Kahn's algorithm
    queue = [cid for cid, deg in in_degree.items() if deg == 0]
    result = []

    while queue:
        node = queue.pop(0)
        result.append(id_to_candidate[node])
        for neighbor in graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # If there are remaining nodes, there's a cycle — append them anyway with warning
    remaining = [id_to_candidate[cid] for cid in id_to_candidate if cid not in [c.get("proposed_id") for c in result]]
    for r in remaining:
        r["_cycle_warning"] = True
        result.append(r)

    return result


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
        if not (SCAFFOLD_DIR / rel_path).exists():
            issues.append(f"Required file missing: {rel_path}")

    if issues:
        _output({"status": "blocked", "message": preflight.get("blocked_message", "Preflight failed."), "issues": issues})
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

    session_id = _session_id(args.layer, args.target)
    session = _load_session(session_id)

    if not session:
        # Build inventory and extract requirements
        inventory = _build_inventory(config)
        requirements = _extract_upstream_requirements(config, inventory)

        # Analyze existing docs for this layer (delta mode)
        existing_analysis = _analyze_existing(config, inventory, requirements)

        # For task seeding: extract asset requirements from specs
        asset_candidates = _extract_asset_requirements_from_specs(config)

        session = {
            "session_id": session_id,
            "layer": args.layer,
            "target": args.target or "",
            "phase": "confirm_inventory",
            "inventory": inventory,
            "requirements": requirements,
            "existing_analysis": existing_analysis,
            "requirement_index": 0,
            "candidates": list(asset_candidates),  # pre-seed with synthetic asset candidates
            "confirmed_candidates": [],
            "created_docs": [],
            "dependency_graph": {},
            "coverage_gaps": [],
            "assumptions": [],
            "asset_candidates": asset_candidates,  # track separately for reporting
            "auto_fill": getattr(args, 'auto_fill', False),
            "created": datetime.now().isoformat(),
        }
        _save_session(session_id, session)

    _advance(session, config)


def _advance(session, config):
    """Determine and write the next action based on session phase."""
    phase = session.get("phase", "propose")

    if phase == "confirm_inventory":
        # Present detected project state for user confirmation
        inventory = session.get("inventory", {})
        testing = inventory.get("testing_tools", {})

        # Build a human-readable summary of detected tools
        detected = {k: v for k, v in testing.items() if v is True}
        not_found = {k: v for k, v in testing.items() if v is False}

        _write_action({
            "action": "confirm_inventory",
            "session_id": session["session_id"],
            "layer": session["layer"],
            "detected": detected,
            "not_found": list(not_found.keys()),
            "engine_config": inventory.get("engine_config", {}),
            "file_system": inventory.get("file_system", {}),
            "message": "Review detected project state. Confirm, correct, or add missing tools before seeding.",
        })
        return

    if phase == "review_existing":
        # Present what already exists and the delta
        existing = session.get("existing_analysis", {})
        _write_action({
            "action": "review_existing",
            "session_id": session["session_id"],
            "layer": session["layer"],
            "existing_count": existing.get("existing_count", 0),
            "existing_files": existing.get("existing_files", []),
            "existing_summaries": existing.get("existing_summaries", []),
            "stale_references": existing.get("stale", []),
            "missing_sections": existing.get("missing_sections", []),
            "total_requirements": len(session.get("requirements", [])),
            "message": f"Found {existing.get('existing_count', 0)} existing docs. Review what exists, what's stale, and what's missing.",
        })
        return

    elif phase == "propose":
        # Send one upstream requirement at a time for candidate proposal
        idx = session.get("requirement_index", 0)
        requirements = session.get("requirements", [])

        if idx >= len(requirements):
            # All requirements processed — move to confirm
            session["phase"] = "confirm"
            _save_session(session["session_id"], session)
            _advance(session, config)
            return

        req = requirements[idx]
        _write_action({
            "action": "propose",
            "session_id": session["session_id"],
            "layer": session["layer"],
            "requirement": req,
            "inventory": session["inventory"],
            "existing_candidates": session["candidates"],
            "template": config.get("template", ""),
            "dependency_checks": config.get("dependency_checks", []),
            "message": f"Propose candidates for requirement {idx + 1}/{len(requirements)}: {req.get('source_file', '')}",
        })

    elif phase == "confirm":
        # Present candidates for user confirmation
        # If coming from gap-fill, only present new gap-fill candidates
        gap_candidates = session.pop("_gap_fill_candidates", None)
        candidates = gap_candidates if gap_candidates else session.get("candidates", [])

        if not candidates:
            session["phase"] = "report" if gap_candidates is not None else "done"
            _save_session(session["session_id"], session)
            if session["phase"] == "done":
                _write_action({
                    "action": "done",
                    "session_id": session["session_id"],
                    "message": "No candidates to create.",
                    "created_docs": [],
                })
            else:
                _advance(session, config)
            return

        # Topological sort
        sorted_candidates = _topological_sort(candidates)
        session["sorted_candidates"] = sorted_candidates
        _save_session(session["session_id"], session)

        is_gap_fill = gap_candidates is not None
        _write_action({
            "action": "confirm",
            "session_id": session["session_id"],
            "layer": session["layer"],
            "candidates": sorted_candidates,
            "total": len(sorted_candidates),
            "assumptions": session.get("assumptions", []),
            "is_gap_fill": is_gap_fill,
            "message": f"Confirm {len(sorted_candidates)} {'gap-fill ' if is_gap_fill else ''}candidates for creation (sorted by dependencies).",
        })

    elif phase == "create":
        # Create docs one at a time in dependency order
        confirmed = session.get("confirmed_candidates", [])
        create_idx = session.get("create_index", 0)

        if create_idx >= len(confirmed):
            # All created — move to verify
            session["phase"] = "verify"
            _save_session(session["session_id"], session)
            _advance(session, config)
            return

        candidate = confirmed[create_idx]
        _write_action({
            "action": "create",
            "session_id": session["session_id"],
            "layer": session["layer"],
            "candidate": candidate,
            "inventory": session["inventory"],
            "created_so_far": session["created_docs"],
            "template": config.get("template", ""),
            "index_file": config.get("index_file", ""),
            "message": f"Create {create_idx + 1}/{len(confirmed)}: {candidate.get('proposed_id', '')} — {candidate.get('name', '')}",
        })

    elif phase == "verify":
        # Coverage verification
        _write_action({
            "action": "verify",
            "session_id": session["session_id"],
            "layer": session["layer"],
            "requirements": session["requirements"],
            "created_docs": session["created_docs"],
            "inventory": session["inventory"],
            "coverage_rules": config.get("coverage_rules", []),
            "message": "Verify coverage — check all upstream requirements are covered.",
        })

    elif phase == "review_gaps":
        # Present gaps to user for decision: fill / defer / dismiss
        gaps = session.get("coverage_gaps", [])
        _write_action({
            "action": "review_gaps",
            "session_id": session["session_id"],
            "layer": session["layer"],
            "gaps": gaps,
            "total": len(gaps),
            "message": f"Coverage verification found {len(gaps)} gap(s). For each: fill (create docs), defer (track as known issue), or dismiss.",
        })

    elif phase == "fill_gaps":
        # Fill gaps found by verification
        gaps = session.get("coverage_gaps", [])
        gap_idx = session.get("gap_index", 0)

        if gap_idx >= len(gaps):
            # All gap proposals collected — check if new candidates exist
            # that haven't been confirmed/created yet
            gap_candidates = [c for c in session.get("candidates", [])
                            if c.get("proposed_id", "") not in
                            [d.get("candidate", {}).get("proposed_id", "") for d in session.get("created_docs", [])]]

            if gap_candidates:
                # New candidates from gap-fill — go through confirm → create → verify
                session["phase"] = "confirm"
                # Only present the new gap-fill candidates, not already-created ones
                session["_gap_fill_candidates"] = gap_candidates
                _save_session(session["session_id"], session)
                _advance(session, config)
            else:
                # No new candidates — gaps were informational only, proceed to report
                session["phase"] = "report"
                _save_session(session["session_id"], session)
                _advance(session, config)
            return

        gap = gaps[gap_idx]
        _write_action({
            "action": "propose",
            "session_id": session["session_id"],
            "layer": session["layer"],
            "requirement": gap,
            "inventory": session["inventory"],
            "existing_candidates": session["created_docs"],
            "template": config.get("template", ""),
            "dependency_checks": config.get("dependency_checks", []),
            "is_gap_fill": True,
            "message": f"Fill gap {gap_idx + 1}/{len(gaps)}: {gap.get('description', '')}",
        })

    elif phase == "report":
        _write_action({
            "action": "report",
            "session_id": session["session_id"],
            "layer": session["layer"],
            "created_docs": session["created_docs"],
            "assumptions": session.get("assumptions", []),
            "coverage_gaps": session.get("coverage_gaps", []),
            "dependency_graph": session.get("dependency_graph", {}),
        })

    else:
        _write_action({"action": "done", "session_id": session["session_id"]})


# ---------------------------------------------------------------------------
# Upstream Doc Updates After Creation
# ---------------------------------------------------------------------------

def _update_upstream_after_creation(layer, created_file, candidate, config):
    """Update parent docs' tables after creating a new doc.
    E.g., when a task is created, update the slice's Tasks table."""
    created_path = SCAFFOLD_DIR / created_file
    if not created_path.exists():
        return

    # Extract the new doc's ID
    id_match = re.search(r"(SYS|SPEC|TASK|SLICE|PHASE)-\d+", Path(created_file).name)
    if not id_match:
        return
    new_id = id_match.group()
    doc_name = candidate.get("name", "")

    today = datetime.now().strftime("%Y-%m-%d")

    if layer == "tasks":
        # Add task to parent slice's Tasks table
        spec_id = candidate.get("source", "")
        # Find which slice contains the parent spec
        spec_match = re.search(r"SPEC-\d+", spec_id)
        if spec_match:
            spec_ref = spec_match.group()
            for slice_file in SCAFFOLD_DIR.glob("slices/SLICE-*-*.md"):
                content = slice_file.read_text(encoding="utf-8")
                if spec_ref in content and new_id not in content:
                    # Find the Tasks table and add a row
                    content = _add_table_row(
                        content, "### Tasks",
                        f"| — | {new_id} | {doc_name} | Draft |"
                    )
                    _update_last_updated(content, slice_file, today)
                    break

    elif layer == "specs":
        # Add spec to parent slice's Specs Included table
        source = candidate.get("source", "")
        slice_match = re.search(r"SLICE-\d+", source)
        if slice_match:
            slice_ref = slice_match.group()
            for slice_file in SCAFFOLD_DIR.glob(f"slices/{slice_ref}-*.md"):
                content = slice_file.read_text(encoding="utf-8")
                if new_id not in content:
                    content = _add_table_row(
                        content, "### Specs Included",
                        f"| {new_id} | {doc_name} |"
                    )
                    _update_last_updated(content, slice_file, today)
                    break

    elif layer == "slices":
        # Add slice to parent phase's references
        phase_id = candidate.get("source", "")
        phase_match = re.search(r"PHASE-\d+", phase_id)
        if phase_match:
            phase_ref = phase_match.group()
            for phase_file in SCAFFOLD_DIR.glob(f"phases/{phase_ref}-*.md"):
                content = phase_file.read_text(encoding="utf-8")
                if new_id not in content:
                    content = _add_table_row(
                        content, "### Slice Strategy",
                        f"| {new_id} | {doc_name} | Draft |"
                    )
                    _update_last_updated(content, phase_file, today)
                    break

    elif layer == "systems":
        # Add system to design doc's System Design Index
        design_doc = SCAFFOLD_DIR / "design" / "design-doc.md"
        if design_doc.exists():
            content = design_doc.read_text(encoding="utf-8")
            if new_id not in content:
                content = _add_table_row(
                    content, "## System Design Index",
                    f"| {new_id} | {doc_name} | Draft |"
                )
                _update_last_updated(content, design_doc, today)

        # Add to systems/_index.md
        sys_index = SCAFFOLD_DIR / "design" / "systems" / "_index.md"
        if sys_index.exists():
            idx_content = sys_index.read_text(encoding="utf-8")
            if new_id not in idx_content:
                idx_content = _add_table_row(
                    idx_content, "## Systems",
                    f"| {new_id} | {doc_name} | Draft |"
                )
                sys_index.write_text(idx_content, encoding="utf-8")

    elif layer == "phases":
        # Add phase to roadmap
        roadmap = SCAFFOLD_DIR / "phases" / "roadmap.md"
        if roadmap.exists():
            content = roadmap.read_text(encoding="utf-8")
            if new_id not in content:
                content = _add_table_row(
                    content, "## Phase Overview",
                    f"| {new_id} | {doc_name} | Draft |"
                )
                _update_last_updated(content, roadmap, today)


def _add_table_row(content, section_heading, row):
    """Add a row to a markdown table under a section heading."""
    # Find the section
    pattern = rf"^#+\s+{re.escape(section_heading.lstrip('# '))}"
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return content

    # Find the end of the table (next blank line or next heading after table rows)
    section_start = match.end()
    lines = content[section_start:].splitlines()

    # Find the last table row (line starting with |)
    last_table_line = -1
    in_table = False
    insert_pos = section_start
    for i, line in enumerate(lines):
        if line.strip().startswith("|"):
            in_table = True
            last_table_line = i
        elif in_table and not line.strip().startswith("|") and line.strip():
            break

    if last_table_line >= 0:
        # Insert after the last table row
        pos = section_start
        for i in range(last_table_line + 1):
            pos = content.find("\n", pos) + 1
        content = content[:pos] + row + "\n" + content[pos:]
    else:
        # No table found — add one with header
        pos = content.find("\n", section_start) + 1
        content = content[:pos] + "\n" + row + "\n" + content[pos:]

    return content


def _update_last_updated(content, file_path, today):
    """Update Last Updated field and write file."""
    content = re.sub(
        r"(>\s*\*\*Last Updated:\*\*)\s*[\d-]+",
        rf"\1 {today}",
        content
    )
    file_path.write_text(content, encoding="utf-8")


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

    if not result:
        _advance(session, config)
        return

    phase = session.get("phase", "propose")

    if phase == "confirm_inventory":
        # User confirmed/corrected the inventory
        corrections = result.get("corrections", {})
        additions = result.get("additions", {})

        # Apply corrections to inventory
        if corrections:
            for key, value in corrections.items():
                # Update testing_tools, engine_config, or file_system
                for section in ["testing_tools", "engine_config", "file_system"]:
                    if key in session["inventory"].get(section, {}):
                        session["inventory"][section][key] = value
                        break
                else:
                    # New key — add to testing_tools
                    session["inventory"].setdefault("testing_tools", {})[key] = value

        if additions:
            session["inventory"].setdefault("testing_tools", {}).update(additions)

        # If existing docs found, present delta before proposing
        existing = session.get("existing_analysis", {})
        if existing.get("has_existing"):
            session["phase"] = "review_existing"
        else:
            session["phase"] = "propose"
        _save_session(args.session, session)
        _advance(session, config)

    elif phase == "review_existing":
        # User reviewed existing docs — they may have:
        # - confirmed: proceed, only seed what's missing
        # - requested reseed: treat specific docs as if they don't exist
        # - noted stale docs: flag for update during proposal
        reseed_files = result.get("reseed", [])
        skip_files = result.get("skip", [])

        # Remove reseeded files from the existing analysis so proposals treat them as gaps
        if reseed_files:
            existing = session.get("existing_analysis", {})
            existing["existing_files"] = [f for f in existing.get("existing_files", []) if f not in reseed_files]
            existing["existing_count"] = len(existing["existing_files"])
            session["existing_analysis"] = existing

        # Track which existing files to skip (they're fine as-is)
        session["skip_existing"] = skip_files or session.get("existing_analysis", {}).get("existing_files", [])

        session["phase"] = "propose"
        _save_session(args.session, session)
        _advance(session, config)

    elif phase == "propose" or (phase == "fill_gaps"):
        # Proposal result — add candidates
        new_candidates = result.get("candidates", [])
        new_assumptions = result.get("assumptions", [])

        session["candidates"].extend(new_candidates)
        session["assumptions"].extend(new_assumptions)

        # Track dependencies
        for candidate in new_candidates:
            cid = candidate.get("proposed_id", "")
            deps = candidate.get("depends_on", [])
            session["dependency_graph"][cid] = deps

        if phase == "propose":
            session["requirement_index"] = session.get("requirement_index", 0) + 1
        else:
            session["gap_index"] = session.get("gap_index", 0) + 1

        _save_session(args.session, session)
        _advance(session, config)

    elif phase == "confirm":
        # User confirmation result
        confirmed = result.get("confirmed", [])
        removed = result.get("removed", [])

        session["confirmed_candidates"] = confirmed
        session["phase"] = "create"
        session["create_index"] = 0
        _save_session(args.session, session)
        _advance(session, config)

    elif phase == "create":
        # Creation result
        created = result.get("created_file", "")
        if created:
            candidate = session["confirmed_candidates"][session.get("create_index", 0)]
            session["created_docs"].append({
                "file": created,
                "candidate": candidate,
            })
            # Update inventory
            layer = session["layer"]
            docs = session["inventory"].get("scaffold_docs", {}).get(layer, [])
            docs.append(created)
            session["inventory"]["scaffold_docs"][layer] = docs

            # Update upstream doc tables
            _update_upstream_after_creation(session["layer"], created, candidate, config)

        session["create_index"] = session.get("create_index", 0) + 1
        _save_session(args.session, session)
        _advance(session, config)

    elif phase == "review_gaps":
        # User decided which gaps to fill / defer / dismiss
        fill = result.get("fill", [])
        deferred = result.get("deferred", [])
        dismissed = result.get("dismissed", [])

        # Track deferred gaps for the report
        session["deferred_gaps"] = session.get("deferred_gaps", []) + deferred

        if fill:
            session["coverage_gaps"] = fill
            session["phase"] = "fill_gaps"
            session["gap_index"] = 0
        else:
            session["phase"] = "report"

        _save_session(args.session, session)
        _advance(session, config)

    elif phase == "verify":
        # Verification result
        gaps = result.get("gaps", [])
        if gaps:
            session["coverage_gaps"] = gaps
            if session.get("auto_fill"):
                # Auto-fill: skip asking, go straight to proposing gap-fills
                session["phase"] = "fill_gaps"
                session["gap_index"] = 0
            else:
                # Default: ask user which gaps to fill
                session["phase"] = "review_gaps"
        else:
            session["phase"] = "report"

        _save_session(args.session, session)
        _advance(session, config)

    elif phase == "report":
        session["phase"] = "done"
        _save_session(args.session, session)
        _write_action({
            "action": "done",
            "session_id": session["session_id"],
            "report_summary": result.get("report_summary", ""),
            "created_count": len(session.get("created_docs", [])),
        })

    else:
        _advance(session, config)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Seed orchestrator — dependency-aware generation")
    subparsers = parser.add_subparsers(dest="command")

    p_pre = subparsers.add_parser("preflight")
    p_pre.add_argument("--layer", required=True)
    p_pre.add_argument("--target", default="")

    p_next = subparsers.add_parser("next-action")
    p_next.add_argument("--layer", required=True)
    p_next.add_argument("--target", default="")
    p_next.add_argument("--auto-fill", action="store_true", help="Fill coverage gaps automatically without asking")

    p_res = subparsers.add_parser("resolve")
    p_res.add_argument("--session", required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"preflight": cmd_preflight, "next-action": cmd_next_action, "resolve": cmd_resolve}[args.command](args)


if __name__ == "__main__":
    main()
