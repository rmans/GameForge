#!/usr/bin/env python3
"""
Meta-validate — checks that YAML configs reference headings that actually
exist in templates. Catches config drift before any skill runs.

Run at install, upgrade, or any time configs/templates change.

Usage:
    python scaffold/tools/meta-validate.py [--fix-report]

Exit code 0 if clean, 1 if mismatches found.
"""

import re
import sys
import json
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
SCAFFOLD_DIR = TOOLS_DIR.parent
CONFIGS_DIR = TOOLS_DIR / "configs"
TEMPLATES_DIR = SCAFFOLD_DIR / "templates"


# ---------------------------------------------------------------------------
# Template heading extraction
# ---------------------------------------------------------------------------

def extract_headings(template_path):
    """Extract all markdown headings from a template file."""
    if not template_path.exists():
        return set()
    content = template_path.read_text(encoding="utf-8")
    headings = set()
    for line in content.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+)", line.strip())
        if match:
            level = len(match.group(1))
            text = match.group(1) + " " + match.group(2).strip()
            headings.add(text)
            # Also add without the template variable parts
            clean = re.sub(r"\[.*?\]", "", match.group(2)).strip()
            if clean:
                headings.add(match.group(1) + " " + clean)
    return headings


def build_template_map():
    """Map layer names to their template files and extract headings."""
    # Direct mappings from config layer to template
    layer_templates = {
        "design": "design-doc-template.md",
        "systems": "system-template.md",
        "spec": "spec-template.md",
        "task": "task-template.md",
        "slice": "slice-template.md",
        "phase": "phase-template.md",
        "roadmap": None,  # no template — singleton doc
        "references": None,  # multiple docs, no single template
        "engine": None,  # multiple engine templates
        "style": None,  # multiple docs
        "input": None,  # multiple docs
        "adr": "decision-template.md",
        "ki": "known-issue-entry-template.md",
        "dd": "design-debt-entry-template.md",
    }

    template_headings = {}
    for layer, template_name in layer_templates.items():
        if template_name:
            path = TEMPLATES_DIR / template_name
            template_headings[layer] = extract_headings(path)
        else:
            template_headings[layer] = set()

    return template_headings


# ---------------------------------------------------------------------------
# YAML config heading extraction
# ---------------------------------------------------------------------------

def extract_config_heading_refs(config_path):
    """Extract heading references from a YAML config file.
    Distinguishes between:
    - 'self' refs: headings that should exist in the TARGET template
      (l3_sections, l2_sections, per_section keys, linked_sections)
    - 'other' refs: headings in OTHER docs (context sections, per_target sections)
      These reference upstream/adjacent docs and can't be checked against the target template."""
    if not config_path.exists():
        return []

    content = config_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    refs = []

    # Pattern 1: l3_sections and l2_sections keys — these ARE target template headings
    in_l3 = False
    in_l2 = False
    in_linked = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "l3_sections:":
            in_l3 = True
            in_l2 = False
            in_linked = False
            continue
        if stripped == "l2_sections:":
            in_l2 = True
            in_l3 = False
            in_linked = False
            continue
        if stripped == "linked_sections:":
            in_linked = True
            in_l3 = False
            in_l2 = False
            continue
        # Exit section on unindented non-empty line
        if stripped and not line.startswith(" ") and not line.startswith("\t"):
            if stripped not in ("l3_sections:", "l2_sections:", "linked_sections:"):
                in_l3 = False
                in_l2 = False
                in_linked = False

        if (in_l3 or in_l2 or in_linked):
            match = re.match(r'\s+"(#{1,6}\s+[^"]+)"', line)
            if match:
                refs.append({
                    "heading": match.group(1).strip(),
                    "line": i + 1,
                    "file": str(config_path),
                    "ref_type": "self",
                })

    # We intentionally DO NOT check context/per_target/per_section sections entries
    # because those reference OTHER docs (upstream systems, architecture, etc.)

    return refs


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def determine_layer(config_path):
    """Determine which layer a config file belongs to."""
    stem = config_path.stem
    # Map config stems to template layer names
    stem_map = {
        "spec": "spec",
        "task": "task",
        "systems": "systems",
        "design": "design",
        "slice": "slice",
        "phase": "phase",
        "roadmap": "roadmap",
        "references": "references",
        "engine": "engine",
        "style": "style",
        "input": "input",
        "adr": "adr",
        "ki": "ki",
        "dd": "dd",
        "code": None,  # code review — no template
        "cross-cutting": None,
        "doc-authority": None,
        "glossary": None,
        "playtest-feedback": None,
        "playtest-session": None,
    }
    return stem_map.get(stem)


def validate_all():
    """Check all configs against their templates. Returns list of issues."""
    template_headings = build_template_map()
    issues = []

    # Scan all config directories
    for config_dir in sorted(CONFIGS_DIR.iterdir()):
        if not config_dir.is_dir():
            continue
        for config_file in sorted(config_dir.glob("*.yaml")):
            layer = determine_layer(config_file)
            if layer is None:
                continue  # no template to check against

            headings = template_headings.get(layer, set())
            if not headings:
                continue  # layer has no single template (refs, engine, style, input)

            refs = extract_config_heading_refs(config_file)
            for ref in refs:
                heading = ref["heading"]
                # Check if the heading exists in the template
                if heading not in headings:
                    # Try without leading # marks for flexibility
                    bare = re.sub(r"^#+\s+", "", heading)
                    found = any(bare in h for h in headings)
                    if not found:
                        issues.append({
                            "config": str(config_file.relative_to(TOOLS_DIR)),
                            "line": ref["line"],
                            "heading": heading,
                            "layer": layer,
                            "message": f"Heading '{heading}' not found in {layer} template",
                        })

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    issues = validate_all()

    if not issues:
        print("meta-validate: PASS — all config heading references resolve to template headings.")
        sys.exit(0)

    print(f"meta-validate: FAIL — {len(issues)} heading reference(s) don't match templates.\n")
    for issue in issues:
        print(f"  {issue['config']}:{issue['line']} — {issue['message']}")

    print(f"\nTotal: {len(issues)} issue(s)")
    print("Fix: update the config heading or the template section name to match.")
    sys.exit(1)


if __name__ == "__main__":
    main()
