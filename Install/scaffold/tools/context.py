#!/usr/bin/env python3
"""
Context resolver — hierarchical, budget-aware context loading for scaffold skills.

Resolves context at four levels:
  1. base      — minimal context every review needs (e.g., the target doc)
  2. target    — docs specific to the target being reviewed (parent system, parent spec)
  3. section   — docs needed for a specific heading/question being reviewed
  4. on_demand — docs available for escalation if ambiguity is detected

Each context entry can specify:
  - file:      path relative to scaffold/
  - class:     canonical | constraint | adjacent | upstream | evidence
  - sections:  list of headings to extract (omit = whole file)
  - priority:  1-5 (1 = essential, 5 = nice-to-have). Used for budget trimming.
  - condition: optional gate (exists, task_type:X, has_section:X)

Budget enforcement:
  - max_total_chars: hard cap on total context characters
  - When over budget, drop entries by priority (5 first), then by class
    (evidence > adjacent > constraint > upstream > canonical)

YAML config format:

    context:
      budget: 30000                    # max chars total (default 50000)

      base:                            # always loaded
        - file: design/glossary.md
          class: constraint
          sections: ["## Terms"]       # extract only this section
          priority: 3

      per_target:                      # resolved from target doc metadata
        - type: parent_system          # follow target's System: SYS-### field
          sections: ["### Purpose", "### Owned State", "### Asset Needs"]
          priority: 2
        - type: parent_spec            # follow target's Implements: SPEC-### field
          sections: ["### Acceptance Criteria", "### Steps"]
          priority: 2
        - type: parent_slice           # follow target's slice membership
          priority: 3

      per_section:                     # keyed by the heading being reviewed
        "### Owned State":
          - file: design/authority.md
            class: constraint
            sections: ["## Authority Table"]
            priority: 1
        "### Purpose":
          - file: design/design-doc.md
            class: canonical
            sections: ["## Identity"]
            priority: 2

      on_demand:                       # available if reviewer flags ambiguity
        - file: design/interfaces.md
          class: adjacent
          priority: 4
"""

import re
from pathlib import Path


SCAFFOLD_DIR = Path(__file__).parent.parent
DEFAULT_BUDGET = 50000  # chars


# ---------------------------------------------------------------------------
# Section Extraction
# ---------------------------------------------------------------------------

def extract_section(content, heading):
    """Extract content under a heading (including the heading line).
    Returns the heading + content until the next heading of same or higher level.
    Returns None if heading not found."""
    # Determine heading level from the pattern
    stripped = heading.lstrip("# ")
    level = len(heading) - len(heading.lstrip("#"))
    if level == 0:
        level = 2  # default to ## if no # prefix

    pattern = rf"^{'#' * level}\s+{re.escape(stripped)}\s*$"
    lines = content.splitlines()
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

    return "\n".join(lines[start:end])


def extract_sections(content, headings):
    """Extract multiple sections from a document. Returns concatenated text."""
    parts = []
    for h in headings:
        section = extract_section(content, h)
        if section:
            parts.append(section)
    return "\n\n".join(parts) if parts else None


# ---------------------------------------------------------------------------
# Target Metadata Extraction
# ---------------------------------------------------------------------------

def _extract_metadata(target_path):
    """Read a scaffold doc and extract its metadata fields."""
    abs_path = SCAFFOLD_DIR / target_path if not Path(target_path).is_absolute() else Path(target_path)
    if not abs_path.exists():
        return {}

    content = abs_path.read_text(encoding="utf-8")
    meta = {"_content": content, "_path": str(abs_path)}

    # Standard fields
    patterns = {
        "system": r">\s*\*\*System:\*\*\s*(\S+)",
        "secondary_systems": r">\s*\*\*Secondary Systems:\*\*\s*(.+)",
        "implements": r">\s*\*\*Implements:\*\*\s*(\S+)",
        "depends_on": r">\s*\*\*Depends on:\*\*\s*(.+)",
        "phase": r">\s*\*\*Phase:\*\*\s*(\S+)",
        "task_type": r">\s*\*\*Task Type:\*\*\s*(.+)",
        "layer": r">\s*\*\*Layer:\*\*\s*(.+)",
        "status": r">\s*\*\*Status:\*\*\s*(\w+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            meta[key] = match.group(1).strip()

    return meta


def _resolve_doc_ref(ref_id, doc_type_prefix, glob_dir):
    """Resolve a doc reference like SYS-001 or SPEC-003 to a file path."""
    if not ref_id or ref_id == "—":
        return None
    matches = sorted(SCAFFOLD_DIR.glob(f"{glob_dir}/{ref_id}-*.md"))
    return str(matches[0].relative_to(SCAFFOLD_DIR)) if matches else None


# ---------------------------------------------------------------------------
# Condition Evaluation
# ---------------------------------------------------------------------------

def _eval_condition(condition, meta):
    """Evaluate a context entry condition against target metadata.
    Conditions: 'exists', 'task_type:foundation', 'has_field:system'"""
    if not condition:
        return True

    if condition == "exists":
        return True  # file existence checked during loading

    if condition.startswith("task_type:"):
        required_type = condition.split(":", 1)[1]
        return meta.get("task_type", "").lower() == required_type.lower()

    if condition.startswith("has_field:"):
        field = condition.split(":", 1)[1]
        val = meta.get(field, "")
        return val and val != "—"

    if condition.startswith("not_task_type:"):
        excluded = condition.split(":", 1)[1]
        return meta.get("task_type", "").lower() != excluded.lower()

    return True


# ---------------------------------------------------------------------------
# Per-Target Resolution
# ---------------------------------------------------------------------------

def _resolve_per_target(entries, meta):
    """Resolve per_target entries using target doc metadata."""
    resolved = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue

        target_type = entry.get("type", "")
        sections = entry.get("sections", [])
        priority = entry.get("priority", 3)
        entry_class = entry.get("class", "upstream")

        resolved_path = None

        if target_type == "parent_system":
            sys_id = meta.get("system", "")
            resolved_path = _resolve_doc_ref(sys_id, "SYS", "design/systems")

        elif target_type == "parent_spec":
            spec_id = meta.get("implements", "")
            resolved_path = _resolve_doc_ref(spec_id, "SPEC", "specs")

        elif target_type == "parent_slice":
            # Find slice that contains this spec/task
            doc_id = None
            content = meta.get("_content", "")
            for id_match in re.finditer(r"(SPEC|TASK)-\d+", Path(meta.get("_path", "")).name):
                doc_id = id_match.group()
                break
            if doc_id:
                for slice_file in sorted(SCAFFOLD_DIR.glob("slices/SLICE-*-*.md")):
                    sc = slice_file.read_text(encoding="utf-8")
                    if doc_id in sc:
                        resolved_path = str(slice_file.relative_to(SCAFFOLD_DIR))
                        break

        elif target_type == "parent_phase":
            phase_id = meta.get("phase", "")
            resolved_path = _resolve_doc_ref(phase_id, "PHASE", "phases")

        elif target_type == "interaction_partners":
            # Find systems referenced in dependency/consequence tables
            content = meta.get("_content", "")
            partner_ids = set(re.findall(r"SYS-\d+", content))
            # Remove self
            self_id = re.search(r"(SYS-\d+)", Path(meta.get("_path", "")).name)
            if self_id:
                partner_ids.discard(self_id.group(1))
            for pid in sorted(partner_ids):
                p = _resolve_doc_ref(pid, "SYS", "design/systems")
                if p:
                    resolved.append({
                        "file": p,
                        "sections": sections or ["### Purpose", "### Owned State"],
                        "priority": priority,
                        "class": "adjacent",
                    })
            continue  # already appended

        elif target_type == "referenced_engine":
            # Load engine docs based on task type
            tt = meta.get("task_type", "").lower()
            engine_dir = SCAFFOLD_DIR / "engine"
            if engine_dir.exists():
                patterns_by_type = {
                    "foundation": ["*scene-architecture*", "*coding*"],
                    "ui": ["*ui*"],
                    "behavior": ["*coding*", "*simulation-runtime*"],
                    "integration": ["*coding*", "*simulation-runtime*"],
                    "wiring": ["*coding*"],
                }
                for pat in patterns_by_type.get(tt, []):
                    for match in engine_dir.glob(f"{pat}.md"):
                        resolved.append({
                            "file": str(match.relative_to(SCAFFOLD_DIR)),
                            "sections": sections,
                            "priority": priority,
                            "class": entry_class,
                        })
            continue

        if resolved_path:
            resolved.append({
                "file": resolved_path,
                "sections": sections,
                "priority": priority,
                "class": entry_class,
            })

    return resolved


# ---------------------------------------------------------------------------
# Context Loading
# ---------------------------------------------------------------------------

def _load_entry(entry, budget_remaining):
    """Load a context entry, applying section extraction. Returns (text, chars_used)."""
    file_path = entry.get("file", "")
    if not file_path:
        return None, 0

    abs_path = SCAFFOLD_DIR / file_path
    if not abs_path.exists():
        return None, 0

    content = abs_path.read_text(encoding="utf-8")
    sections = entry.get("sections", [])

    if sections:
        extracted = extract_sections(content, sections)
        if extracted:
            # Add file header for clarity
            text = f"--- {file_path} (sections: {', '.join(sections)}) ---\n{extracted}"
        else:
            # Sections not found — fall back to truncated whole file
            text = f"--- {file_path} (requested sections not found, truncated) ---\n{content[:3000]}"
    else:
        text = f"--- {file_path} ---\n{content}"

    # Enforce budget
    if len(text) > budget_remaining:
        text = text[:budget_remaining] + "\n[...truncated by budget]"

    return text, len(text)


# ---------------------------------------------------------------------------
# Main Resolver
# ---------------------------------------------------------------------------

# Class drop order (last dropped first)
_CLASS_DROP_ORDER = ["evidence", "adjacent", "constraint", "upstream", "canonical"]


def resolve(config, target_path, section_heading=None, extra_meta=None):
    """Resolve context for a review call.

    Args:
        config: parsed YAML config dict (must have 'context' key)
        target_path: path to the doc being reviewed (relative to scaffold/)
        section_heading: specific heading being reviewed (e.g., "### Purpose")
        extra_meta: additional metadata to merge (e.g., from implement.py)

    Returns:
        list of {"file": path, "text": content, "class": class, "priority": N}
    """
    ctx_config = config.get("context", {})
    budget = ctx_config.get("budget", DEFAULT_BUDGET)

    # Extract target metadata
    meta = _extract_metadata(target_path)
    if extra_meta:
        meta.update(extra_meta)

    # Collect all candidate entries with their level
    candidates = []

    # Level 1: base (always)
    for entry in ctx_config.get("base", []):
        if isinstance(entry, dict) and _eval_condition(entry.get("condition"), meta):
            candidates.append({**entry, "_level": "base"})

    # Level 2: per_target (resolved from metadata)
    per_target = ctx_config.get("per_target", [])
    for resolved in _resolve_per_target(per_target, meta):
        candidates.append({**resolved, "_level": "target"})

    # Level 3: per_section (only if section_heading provided)
    if section_heading:
        per_section = ctx_config.get("per_section", {})
        section_entries = per_section.get(section_heading, [])
        for entry in section_entries:
            if isinstance(entry, dict) and _eval_condition(entry.get("condition"), meta):
                candidates.append({**entry, "_level": "section"})

    # Sort by priority (1 first), then by level (base > target > section)
    level_order = {"base": 0, "target": 1, "section": 2}
    candidates.sort(key=lambda e: (e.get("priority", 3), level_order.get(e.get("_level"), 3)))

    # Deduplicate by file+sections
    seen = set()
    deduped = []
    for entry in candidates:
        key = (entry.get("file", ""), tuple(entry.get("sections", [])))
        if key not in seen:
            seen.add(key)
            deduped.append(entry)

    # Load entries within budget
    results = []
    chars_used = 0

    for entry in deduped:
        remaining = budget - chars_used
        if remaining <= 0:
            break

        text, used = _load_entry(entry, remaining)
        if text:
            results.append({
                "file": entry.get("file", ""),
                "text": text,
                "class": entry.get("class", ""),
                "priority": entry.get("priority", 3),
            })
            chars_used += used

    return results


def resolve_as_text(config, target_path, section_heading=None, extra_meta=None):
    """Resolve context and return as a single concatenated string."""
    entries = resolve(config, target_path, section_heading, extra_meta)
    return "\n\n".join(e["text"] for e in entries)


def resolve_as_files(config, target_path, section_heading=None, extra_meta=None):
    """Resolve context and return as a list of file paths (for CLI --context-files).
    Note: this loses section extraction — use resolve_as_text for precise context."""
    entries = resolve(config, target_path, section_heading, extra_meta)
    seen = set()
    files = []
    for e in entries:
        f = e.get("file", "")
        if f and f not in seen:
            abs_path = SCAFFOLD_DIR / f
            if abs_path.exists():
                seen.add(f)
                files.append(str(abs_path))
    return files
