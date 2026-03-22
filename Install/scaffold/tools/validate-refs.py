#!/usr/bin/env python3
"""
Referential integrity checker for scaffold documents.

Validates cross-document references: system IDs, authority ownership,
signal emitters/consumers, interface endpoints, state machine authorities,
glossary NOT-column violations, design-doc bidirectional sync, spec-slice
coverage, and task-spec references.

Usage:
    python scaffold/tools/validate-refs.py [--format json|text]

Exit code 0 if no errors, 1 if errors found.
No pip dependencies — stdlib only.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Scaffold Root Discovery
# ---------------------------------------------------------------------------

def find_scaffold_root():
    """Find the scaffold root by looking for scaffold/ from script dir upward, then CWD."""
    # Try walking up from the script's own directory
    anchor = Path(__file__).resolve().parent
    for _ in range(10):
        candidate = anchor / "scaffold"
        if candidate.is_dir() and (candidate / "_index.md").exists():
            return anchor
        if anchor.parent == anchor:
            break
        anchor = anchor.parent

    # Fall back to CWD
    cwd = Path.cwd()
    if (cwd / "scaffold").is_dir():
        return cwd

    return None


# ---------------------------------------------------------------------------
# Issue Collector
# ---------------------------------------------------------------------------

class Issues:
    """Collects validation issues with severity, message, file, and line."""

    def __init__(self):
        self.items = []

    def add(self, check, severity, message, file=None, line=None):
        self.items.append({
            "check": check,
            "severity": severity,
            "message": message,
            "file": str(file) if file else None,
            "line": line,
        })

    def has_errors(self):
        return any(i["severity"] == "ERROR" for i in self.items)


# ---------------------------------------------------------------------------
# File Helpers
# ---------------------------------------------------------------------------

def read_file(path):
    """Read a file, returning (content, lines) or (None, None) if missing."""
    if not path.exists():
        return None, None
    text = path.read_text(encoding="utf-8")
    return text, text.splitlines()


def warn_missing(issues, check, path, description):
    """Record a WARNING for a missing file and return True if missing."""
    if not path.exists():
        issues.add(check, "WARNING", f"File not found: {description}", file=path)
        return True
    return False


# ---------------------------------------------------------------------------
# Table Parsing
# ---------------------------------------------------------------------------

def parse_table_rows(lines, start_after_header=True):
    """
    Parse markdown table rows.  Returns list of dicts mapping
    header-name -> cell-value for each data row.

    Skips the separator line (|---|---|) and placeholder rows containing
    '*None yet*'.
    """
    rows = []
    header_cols = None
    separator_seen = False

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if header_cols is not None:
                # Table ended
                break
            continue

        cells = [c.strip() for c in stripped.split("|")[1:-1]]

        if header_cols is None:
            header_cols = cells
            continue

        # Skip separator line
        if not separator_seen:
            if all(re.match(r"^[-:]+$", c) for c in cells):
                separator_seen = True
                continue

        # Skip placeholder rows
        joined = " ".join(cells)
        if "*None yet*" in joined or joined.replace("—", "").replace("-", "").strip() == "":
            continue

        row = {}
        for idx, hdr in enumerate(header_cols):
            row[hdr] = cells[idx] if idx < len(cells) else ""
        row["_line"] = lineno
        rows.append(row)

    return rows


def find_all_tables(lines):
    """Return every table in the file as a list of parsed row-dicts."""
    tables = []
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|"):
            # Gather contiguous table lines
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            parsed = parse_table_rows(table_lines)
            if parsed:
                tables.append(parsed)
        else:
            i += 1
    return tables


def extract_ids(text, pattern):
    """Extract all IDs matching a regex pattern from raw text."""
    return set(re.findall(pattern, text))


def extract_ids_with_lines(lines, pattern):
    """Extract IDs matching a pattern along with their line numbers."""
    results = []
    for lineno, line in enumerate(lines, 1):
        for match in re.finditer(pattern, line):
            results.append((match.group(0), lineno))
    return results


# ---------------------------------------------------------------------------
# Check: System IDs
# ---------------------------------------------------------------------------

def check_system_ids(root, issues):
    """
    Every SYS-### referenced in authority.md, interfaces.md,
    signal-registry.md, entity-components.md, state-transitions.md
    must exist in systems/_index.md.
    """
    check_name = "system-ids"
    scaffold = root / "scaffold"

    index_path = scaffold / "design" / "systems" / "_index.md"
    if warn_missing(issues, check_name, index_path, "design/systems/_index.md"):
        return set()

    index_text, index_lines = read_file(index_path)
    # Gather registered system IDs from the index table
    registered = extract_ids(index_text, r"SYS-\d+")

    # Files that reference system IDs
    ref_files = [
        (scaffold / "design" / "authority.md", "design/authority.md"),
        (scaffold / "design" / "interfaces.md", "design/interfaces.md"),
        (scaffold / "reference" / "signal-registry.md", "reference/signal-registry.md"),
        (scaffold / "reference" / "entity-components.md", "reference/entity-components.md"),
        (scaffold / "design" / "state-transitions.md", "design/state-transitions.md"),
    ]

    for fpath, label in ref_files:
        if warn_missing(issues, check_name, fpath, label):
            continue
        _, flines = read_file(fpath)
        refs = extract_ids_with_lines(flines, r"SYS-\d+")
        for sys_id, lineno in refs:
            if sys_id not in registered:
                issues.add(
                    check_name, "ERROR",
                    f"{sys_id} referenced in {label} but not registered in design/systems/_index.md",
                    file=fpath, line=lineno,
                )

    return registered


# ---------------------------------------------------------------------------
# Check: Authority <-> Entities
# ---------------------------------------------------------------------------

def check_authority_entities(root, issues):
    """
    Every Authority column entry in entity-components.md (that looks like
    SYS-###) must match an Owning System in authority.md.
    """
    check_name = "authority-entities"
    scaffold = root / "scaffold"

    auth_path = scaffold / "design" / "authority.md"
    ent_path = scaffold / "reference" / "entity-components.md"

    if warn_missing(issues, check_name, auth_path, "design/authority.md"):
        return
    if warn_missing(issues, check_name, ent_path, "reference/entity-components.md"):
        return

    auth_text, auth_lines = read_file(auth_path)
    ent_text, ent_lines = read_file(ent_path)

    # Gather Owning System values from ALL tables in authority.md
    auth_tables = find_all_tables(auth_lines)
    owning_systems = set()
    for table in auth_tables:
        for row in table:
            val = row.get("Owning System", "").strip()
            if val and val != "—":
                owning_systems.add(val)

    # Gather Authority values from entity-components.md tables
    ent_tables = find_all_tables(ent_lines)
    for table in ent_tables:
        for row in table:
            authority_val = row.get("Authority", "").strip()
            if not authority_val or authority_val in ("—", "Static"):
                continue
            # Only check SYS-### references
            if not re.search(r"SYS-\d+", authority_val):
                continue
            if authority_val not in owning_systems:
                issues.add(
                    check_name, "ERROR",
                    f"Authority '{authority_val}' in entity-components.md not found as Owning System in authority.md",
                    file=ent_path, line=row.get("_line"),
                )


# ---------------------------------------------------------------------------
# Check: Signals <-> Systems
# ---------------------------------------------------------------------------

def check_signals_systems(root, issues, registered_systems):
    """
    Every Emitter and Consumer in signal-registry.md must be a registered
    system (SYS-### ID present in the registered set).
    """
    check_name = "signals-systems"
    scaffold = root / "scaffold"

    sig_path = scaffold / "reference" / "signal-registry.md"
    if warn_missing(issues, check_name, sig_path, "reference/signal-registry.md"):
        return

    _, sig_lines = read_file(sig_path)

    # Check both Signals and Intent Objects tables
    tables = find_all_tables(sig_lines)
    for table in tables:
        for row in table:
            # Signals table: Emitter, Consumer(s)
            # Intent table: Sender, Receiver
            for col_name in ("Emitter", "Consumer(s)", "Sender", "Receiver"):
                val = row.get(col_name, "").strip()
                if not val or val == "—":
                    continue
                # Each cell may contain comma-separated entries
                entries = [e.strip() for e in val.split(",")]
                for entry in entries:
                    sys_ids = re.findall(r"SYS-\d+", entry)
                    for sys_id in sys_ids:
                        if sys_id not in registered_systems:
                            issues.add(
                                check_name, "ERROR",
                                f"{sys_id} in signal-registry.md column '{col_name}' is not a registered system",
                                file=sig_path, line=row.get("_line"),
                            )


# ---------------------------------------------------------------------------
# Check: Interfaces <-> Systems
# ---------------------------------------------------------------------------

def check_interfaces_systems(root, issues, registered_systems):
    """
    Every Source System and Target System in interfaces.md must be a
    registered system.
    """
    check_name = "interfaces-systems"
    scaffold = root / "scaffold"

    iface_path = scaffold / "design" / "interfaces.md"
    if warn_missing(issues, check_name, iface_path, "design/interfaces.md"):
        return

    _, iface_lines = read_file(iface_path)
    tables = find_all_tables(iface_lines)

    for table in tables:
        for row in table:
            for col_name in ("Source System", "Target System"):
                val = row.get(col_name, "").strip()
                if not val or val == "—":
                    continue
                sys_ids = re.findall(r"SYS-\d+", val)
                for sys_id in sys_ids:
                    if sys_id not in registered_systems:
                        issues.add(
                            check_name, "ERROR",
                            f"{sys_id} in interfaces.md column '{col_name}' is not a registered system",
                            file=iface_path, line=row.get("_line"),
                        )


# ---------------------------------------------------------------------------
# Check: State Machines <-> Systems
# ---------------------------------------------------------------------------

def check_states_systems(root, issues, registered_systems):
    """
    Every Authority listed in state-transitions.md (in the **Authority:**
    line of each state machine section) must be a registered system.
    """
    check_name = "states-systems"
    scaffold = root / "scaffold"

    st_path = scaffold / "design" / "state-transitions.md"
    if warn_missing(issues, check_name, st_path, "design/state-transitions.md"):
        return

    _, st_lines = read_file(st_path)

    for lineno, line in enumerate(st_lines, 1):
        match = re.match(r"\*\*Authority:\*\*\s*(.+)", line.strip())
        if match:
            authority_val = match.group(1).strip()
            sys_ids = re.findall(r"SYS-\d+", authority_val)
            for sys_id in sys_ids:
                if sys_id not in registered_systems:
                    issues.add(
                        check_name, "ERROR",
                        f"{sys_id} in state-transitions.md Authority line is not a registered system",
                        file=st_path, line=lineno,
                    )


# ---------------------------------------------------------------------------
# Check: Glossary NOT-column violations
# ---------------------------------------------------------------------------

def check_glossary_not_column(root, issues):
    """
    Scans all non-theory docs for terms listed in the glossary's NOT column.
    """
    check_name = "glossary-not-terms"
    scaffold = root / "scaffold"

    glossary_path = scaffold / "design" / "glossary.md"
    if warn_missing(issues, check_name, glossary_path, "design/glossary.md"):
        return

    _, glossary_lines = read_file(glossary_path)
    rows = parse_table_rows(glossary_lines)

    # Build list of forbidden terms with their canonical replacement
    forbidden = []  # (term_lower, canonical_term)
    for row in rows:
        canonical = row.get("Term", "").strip()
        not_col = row.get("NOT (do not use)", "").strip()
        if not not_col or not_col == "—":
            continue
        # NOT column is comma-separated
        for bad_term in not_col.split(","):
            bad_term = bad_term.strip()
            if bad_term:
                forbidden.append((bad_term.lower(), canonical))

    if not forbidden:
        return

    # Context-aware exclusion: if the NOT-term appears as part of a
    # compound word, a known-legitimate phrase, or in a context where
    # it's clearly not being used as a synonym for the canonical term,
    # skip it. This prevents false positives like "wound" in "wound
    # infection" (legitimate) vs "wound" meaning "Scar" (violation).
    def is_false_positive(line_lower, bad_term, canonical, match_obj):
        """Check if a NOT-term match is a false positive based on context."""
        start = match_obj.start()
        end = match_obj.end()

        # 1. Skip if inside a camelCase or PascalCase compound (e.g., "SubRegion")
        if start > 0 and line_lower[start - 1:start].isalpha():
            return True  # preceded by letter without word boundary — shouldn't happen with \b, but safety check

        # 2. Skip if the term appears in a heading definition (defining the term itself)
        stripped = line_lower.strip()
        if stripped.startswith("#") and bad_term in stripped:
            return True

        # 3. Skip if inside a markdown link target or code span
        # Check if we're inside backticks
        before = line_lower[:start]
        if before.count("`") % 2 == 1:  # odd number of backticks = inside code span
            return True

        # 4. Context window check: look at surrounding words to see if the
        # NOT-term is used in its literal/natural meaning vs as a synonym.
        # Extract ~3 words before and after the match for context.
        context_start = max(0, start - 40)
        context_end = min(len(line_lower), end + 40)
        context = line_lower[context_start:context_end]

        # If the canonical term also appears on the same line, the author
        # is likely distinguishing between them — not using one as synonym.
        if canonical.lower() in line_lower:
            return True

        # 5. Skip if the NOT-term is part of a compound with a hyphen or
        # adjacent qualifier that makes it a different concept.
        # E.g., "wound infection" is not using "wound" as synonym for "Scar"
        # E.g., "structural integrity" is not using "integrity" as synonym for "CCR"
        # E.g., "rate modifier" is not using "modifier" as synonym for "Trait"
        # Check for adjective + NOT-term or NOT-term + noun patterns
        after_match = line_lower[end:end + 20].strip()
        before_match = line_lower[max(0, start - 20):start].strip()

        # If there's an adjective before (common compound pattern), likely legitimate
        common_compound_indicators = [
            "structural", "numeric", "rate", "damage", "speed", "mood",
            "regional", "sub", "wound", "base", "total", "current",
            "priority", "skill", "behavior", "behavioral",
        ]
        for indicator in common_compound_indicators:
            if before_match.endswith(indicator):
                return True
            if after_match.startswith(indicator):
                return True

        # If the NOT-term is immediately followed by a noun that forms a
        # compound concept (wound infection, wound healing, etc.), skip it
        compound_followers = [
            "infection", "healing", "treatment", "care", "type", "types",
            "severity", "level", "levels", "system", "model", "value",
            "values", "factor", "factors", "rate", "rates", "effect",
            "effects", "check", "instability", "detection", "boundary",
            "boundaries", "management", "based", "specific", "related",
        ]
        first_word_after = after_match.split()[0] if after_match.split() else ""
        if first_word_after in compound_followers:
            return True

        return False

    # Directories to scan (exclude theory/)
    scan_dirs = [
        scaffold / "design",
        scaffold / "reference",
        scaffold / "inputs",
        scaffold / "phases",
        scaffold / "specs",
        scaffold / "tasks",
        scaffold / "slices",
        scaffold / "engine",
        scaffold / "decisions",
    ]

    for scan_dir in scan_dirs:
        if not scan_dir.is_dir():
            continue
        for md_file in scan_dir.rglob("*.md"):
            # Skip the glossary itself
            if md_file.resolve() == glossary_path.resolve():
                continue
            text, flines = read_file(md_file)
            if text is None:
                continue
            for lineno, line in enumerate(flines, 1):
                # Skip comment lines inside HTML comments
                stripped = line.strip()
                if stripped.startswith("<!--"):
                    continue
                line_lower = line.lower()
                for bad_term, canonical in forbidden:
                    # Word-boundary check to avoid partial matches
                    pattern = r"\b" + re.escape(bad_term) + r"\b"
                    match = re.search(pattern, line_lower)
                    if match and not is_false_positive(line_lower, bad_term, canonical, match):
                        rel = md_file.relative_to(root)
                        issues.add(
                            check_name, "WARNING",
                            f"Glossary NOT-term '{bad_term}' found (use '{canonical}' instead)",
                            file=md_file, line=lineno,
                        )


# ---------------------------------------------------------------------------
# Check: Bidirectional System Registration
# ---------------------------------------------------------------------------

def check_bidirectional_registration(root, issues):
    """
    Every SYS-### in systems/_index.md must also appear in design-doc.md's
    System Design Index, and vice versa.
    """
    check_name = "bidirectional-registration"
    scaffold = root / "scaffold"

    index_path = scaffold / "design" / "systems" / "_index.md"
    dd_path = scaffold / "design" / "design-doc.md"

    if warn_missing(issues, check_name, index_path, "design/systems/_index.md"):
        return
    if warn_missing(issues, check_name, dd_path, "design/design-doc.md"):
        return

    index_text, index_lines = read_file(index_path)
    dd_text, dd_lines = read_file(dd_path)

    # Extract SYS-### from the Registered Systems table in _index.md
    index_ids = set()
    in_table = False
    for lineno, line in enumerate(index_lines, 1):
        stripped = line.strip()
        if "Registered Systems" in stripped:
            in_table = True
            continue
        if in_table and stripped.startswith("|"):
            for sys_id in re.findall(r"SYS-\d+", stripped):
                index_ids.add(sys_id)
        elif in_table and stripped.startswith("#"):
            break

    # Extract SYS-### from the System Design Index section in design-doc.md
    dd_ids = set()
    in_sdi = False
    for lineno, line in enumerate(dd_lines, 1):
        stripped = line.strip()
        if "System Design Index" in stripped:
            in_sdi = True
            continue
        if in_sdi and stripped.startswith("|"):
            for sys_id in re.findall(r"SYS-\d+", stripped):
                dd_ids.add(sys_id)
        elif in_sdi and stripped.startswith("---"):
            break
        elif in_sdi and re.match(r"^#{1,3}\s", stripped):
            break

    # In index but not in design-doc
    for sys_id in sorted(index_ids - dd_ids):
        issues.add(
            check_name, "ERROR",
            f"{sys_id} registered in systems/_index.md but missing from design-doc.md System Design Index",
            file=index_path,
        )

    # In design-doc but not in index
    for sys_id in sorted(dd_ids - index_ids):
        issues.add(
            check_name, "ERROR",
            f"{sys_id} listed in design-doc.md System Design Index but missing from systems/_index.md",
            file=dd_path,
        )


# ---------------------------------------------------------------------------
# Check: Spec <-> Slice Coverage
# ---------------------------------------------------------------------------

def check_spec_slice(root, issues):
    """
    Every SPEC-### in a spec file must be listed in at least one slice's
    Specs Included table.
    """
    check_name = "spec-slice"
    scaffold = root / "scaffold"

    specs_dir = scaffold / "specs"
    slices_dir = scaffold / "slices"

    if not specs_dir.is_dir():
        issues.add(check_name, "WARNING", "specs/ directory not found", file=specs_dir)
        return
    if not slices_dir.is_dir():
        issues.add(check_name, "WARNING", "slices/ directory not found", file=slices_dir)
        return

    # Gather all SPEC-### IDs from spec files
    spec_ids = set()
    for spec_file in specs_dir.glob("SPEC-*.md"):
        ids = extract_ids(spec_file.read_text(encoding="utf-8"), r"SPEC-\d+")
        # The spec's own ID is typically in the filename or first heading
        filename_ids = re.findall(r"SPEC-\d+", spec_file.name)
        spec_ids.update(filename_ids)

    if not spec_ids:
        return

    # Gather all SPEC-### referenced in slice files
    slice_spec_refs = set()
    for slice_file in slices_dir.glob("SLICE-*.md"):
        text = slice_file.read_text(encoding="utf-8")
        refs = re.findall(r"SPEC-\d+", text)
        slice_spec_refs.update(refs)

    # Check coverage
    for spec_id in sorted(spec_ids):
        if spec_id not in slice_spec_refs:
            spec_file = None
            # Find the file for this spec
            for f in specs_dir.glob(f"{spec_id}*.md"):
                spec_file = f
                break
            issues.add(
                check_name, "WARNING",
                f"{spec_id} defined in specs/ but not listed in any slice's Specs Included table",
                file=spec_file or specs_dir,
            )


# ---------------------------------------------------------------------------
# Check: Task <-> Spec References
# ---------------------------------------------------------------------------

def check_task_spec(root, issues):
    """
    Every TASK-### must reference a valid SPEC-### (via its Implements
    header field), and that SPEC must exist as a file.
    """
    check_name = "task-spec"
    scaffold = root / "scaffold"

    tasks_dir = scaffold / "tasks"
    specs_dir = scaffold / "specs"

    if not tasks_dir.is_dir():
        issues.add(check_name, "WARNING", "tasks/ directory not found", file=tasks_dir)
        return

    # Gather existing SPEC-### IDs from filenames
    existing_specs = set()
    if specs_dir.is_dir():
        for spec_file in specs_dir.glob("SPEC-*.md"):
            filename_ids = re.findall(r"SPEC-\d+", spec_file.name)
            existing_specs.update(filename_ids)

    # Also check specs/_index.md table
    specs_index = specs_dir / "_index.md"
    if specs_index.exists():
        text = specs_index.read_text(encoding="utf-8")
        existing_specs.update(re.findall(r"SPEC-\d+", text))

    # Scan task files
    for task_file in sorted(tasks_dir.glob("TASK-*.md")):
        text, flines = read_file(task_file)
        if text is None:
            continue

        task_id_match = re.findall(r"TASK-\d+", task_file.name)
        task_id = task_id_match[0] if task_id_match else task_file.name

        # Look for the Implements field in the blockquote header
        spec_ref = None
        spec_line = None
        for lineno, line in enumerate(flines, 1):
            match = re.search(r"\*\*Implements:\*\*\s*(SPEC-\d+)", line)
            if match:
                spec_ref = match.group(1)
                spec_line = lineno
                break

        if spec_ref is None:
            # Also check the tasks/_index.md Spec column
            idx_path = tasks_dir / "_index.md"
            if idx_path.exists():
                idx_text, idx_lines = read_file(idx_path)
                rows = parse_table_rows(idx_lines)
                for row in rows:
                    row_id = row.get("ID", "").strip()
                    if task_id in row_id:
                        spec_val = row.get("Spec", "").strip()
                        spec_match = re.search(r"SPEC-\d+", spec_val)
                        if spec_match:
                            spec_ref = spec_match.group(0)
                            break

        if spec_ref is None:
            issues.add(
                check_name, "WARNING",
                f"{task_id} does not reference any SPEC-### in its Implements field",
                file=task_file,
            )
        elif existing_specs and spec_ref not in existing_specs:
            issues.add(
                check_name, "ERROR",
                f"{task_id} references {spec_ref} but that spec does not exist",
                file=task_file, line=spec_line,
            )


# ---------------------------------------------------------------------------
# Output Formatting
# ---------------------------------------------------------------------------

def format_text(items):
    """Format issues as human-readable text."""
    if not items:
        return "All referential integrity checks passed."

    lines = []
    errors = [i for i in items if i["severity"] == "ERROR"]
    warnings = [i for i in items if i["severity"] == "WARNING"]

    lines.append(f"Referential Integrity Report: {len(errors)} error(s), {len(warnings)} warning(s)")
    lines.append("=" * 70)

    for item in items:
        sev = item["severity"]
        check = item["check"]
        msg = item["message"]
        loc = ""
        if item["file"]:
            loc = f"  {item['file']}"
            if item["line"]:
                loc += f":{item['line']}"
        lines.append(f"[{sev}] ({check}){loc}")
        lines.append(f"  {msg}")
        lines.append("")

    lines.append("=" * 70)
    lines.append(f"Total: {len(errors)} error(s), {len(warnings)} warning(s)")
    return "\n".join(lines)


def format_json(items):
    """Format issues as a JSON array."""
    return json.dumps(items, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Check referential integrity across scaffold documents."
    )
    parser.add_argument(
        "--format", choices=["json", "text"], default="text",
        help="Output format: json (array of issue objects) or text (human-readable). Default: text."
    )
    args = parser.parse_args()

    root = find_scaffold_root()
    if root is None:
        msg = "Cannot find scaffold root. Run from the project root where scaffold/ exists."
        if args.format == "json":
            print(json.dumps([{"check": "setup", "severity": "ERROR", "message": msg, "file": None, "line": None}]))
        else:
            print(f"ERROR: {msg}")
        sys.exit(1)

    issues = Issues()

    # Run all checks
    registered_systems = check_system_ids(root, issues)
    check_authority_entities(root, issues)
    check_signals_systems(root, issues, registered_systems)
    check_interfaces_systems(root, issues, registered_systems)
    check_states_systems(root, issues, registered_systems)
    check_glossary_not_column(root, issues)
    check_bidirectional_registration(root, issues)
    check_spec_slice(root, issues)
    check_task_spec(root, issues)

    # Output
    if args.format == "json":
        print(format_json(issues.items))
    else:
        print(format_text(issues.items))

    sys.exit(1 if issues.has_errors() else 0)


if __name__ == "__main__":
    main()
