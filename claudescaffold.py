#!/usr/bin/env python3
"""ClaudeScaffold — install, upgrade, or remove the scaffold pipeline."""

import argparse
import json
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

VERSION = "2.23.0"
GITHUB_ZIP_URL = "https://github.com/rmans/ClaudeScaffold/archive/refs/heads/{branch}.zip"
EXCLUDE_DIRS = {"__pycache__"}
SCAFFOLD_SKILL_PREFIX = "scaffold-"
EXPECTED_SKILLS = 78

# Upgrade mode: these scaffold/ subdirectories are infrastructure and get fully replaced
UPGRADE_REPLACE_DIRS = {"theory", "templates", "tools"}
# Upgrade mode: these scaffold/ root files are infrastructure and get replaced
UPGRADE_REPLACE_ROOT_FILES = {"_index.md", "doc-authority.md", "WORKFLOW.md", "README.md", "SKILLS.md"}
# Upgrade mode: these subdir files are infrastructure and get replaced
UPGRADE_REPLACE_SUBDIR_FILES = {
    "reviews/TEMPLATE-review.md",
    "assets/_index.md",
    "assets/entities/_index.md",
    "assets/ui/_index.md",
    "assets/environment/_index.md",
    "assets/music/_index.md",
    "assets/shared/_index.md",
    "assets/concept/_index.md",
    "assets/promo/_index.md",
    "prototypes/_index.md",
}


# ---------------------------------------------------------------------------
# Shared helpers (unchanged from original)
# ---------------------------------------------------------------------------

def log(msg, verbose_only=False, *, verbose=False):
    if verbose_only and not verbose:
        return
    print(msg)


def is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    if path.suffix == ".pyc":
        return True
    return False


def collect_files(src: Path, rel_base: Path = None) -> list:
    """Collect all files under src, returning (absolute, relative) pairs."""
    if rel_base is None:
        rel_base = src
    result = []
    for item in sorted(src.rglob("*")):
        if item.is_file() and not is_excluded(item.relative_to(rel_base)):
            result.append((item, item.relative_to(rel_base)))
    return result


def download_zip(branch: str, dest_path: Path):
    """Download the GitHub zip archive for the given branch."""
    url = GITHUB_ZIP_URL.format(branch=branch)
    print(f"  Downloading {url}")
    try:
        response = urlopen(url)
    except HTTPError as e:
        if e.code == 404:
            print(f"\nERROR: Branch or tag '{branch}' not found on GitHub.", file=sys.stderr)
            print(f"  URL: {url}", file=sys.stderr)
        else:
            print(f"\nERROR: HTTP {e.code} downloading from GitHub.", file=sys.stderr)
            print(f"  URL: {url}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"\nERROR: Could not connect to GitHub.", file=sys.stderr)
        print(f"  {e.reason}", file=sys.stderr)
        print("  Check your internet connection and try again.", file=sys.stderr)
        sys.exit(1)

    total = response.headers.get("Content-Length")
    downloaded = 0
    chunk_size = 64 * 1024

    with open(dest_path, "wb") as f:
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded * 100 // int(total)
                print(f"\r  Downloaded {downloaded // 1024} KB ({pct}%)", end="", flush=True)
            else:
                print(f"\r  Downloaded {downloaded // 1024} KB", end="", flush=True)

    print()  # newline after progress


def merge_settings(existing_path: Path, new_path: Path, dry_run: bool, verbose: bool):
    """Merge settings.local.json: add scaffold entries, keep existing user entries."""
    try:
        with open(new_path, "r", encoding="utf-8") as f:
            new_settings = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log(f"  WARNING: Could not read source settings: {e}")
        return

    try:
        with open(existing_path, "r", encoding="utf-8") as f:
            existing_settings = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log(f"  WARNING: Could not read existing settings: {e}, will overwrite")
        existing_settings = {}

    # Merge permissions.allow lists (union, preserving order)
    existing_allow = existing_settings.get("permissions", {}).get("allow", [])
    new_allow = new_settings.get("permissions", {}).get("allow", [])
    merged_allow = list(existing_allow)
    for entry in new_allow:
        if entry not in merged_allow:
            merged_allow.append(entry)

    # Merge permissions.deny lists similarly
    existing_deny = existing_settings.get("permissions", {}).get("deny", [])
    new_deny = new_settings.get("permissions", {}).get("deny", [])
    merged_deny = list(existing_deny)
    for entry in new_deny:
        if entry not in merged_deny:
            merged_deny.append(entry)

    merged = dict(existing_settings)
    if "permissions" not in merged:
        merged["permissions"] = {}
    if merged_allow:
        merged["permissions"]["allow"] = merged_allow
    if merged_deny:
        merged["permissions"]["deny"] = merged_deny

    if dry_run:
        log(f"  Would merge settings.local.json ({len(existing_allow)} existing + {len(new_allow)} scaffold entries)")
        return

    existing_path.parent.mkdir(parents=True, exist_ok=True)
    with open(existing_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
        f.write("\n")
    log(f"  Merged settings.local.json ({len(merged_allow)} allow entries)", verbose_only=True, verbose=verbose)


def copy_file(src: Path, dst: Path, dry_run: bool, verbose: bool):
    if dry_run:
        log(f"  Would copy: {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    log(f"  Copied: {dst}", verbose_only=True, verbose=verbose)


# ---------------------------------------------------------------------------
# New helpers
# ---------------------------------------------------------------------------

def write_version_stamp(target: Path, branch: str, mode: str, dry_run: bool):
    """Write .claude/scaffold-version.json with install metadata."""
    stamp = {
        "version": VERSION,
        "installed": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "branch": branch,
        "mode": mode,
    }
    stamp_path = target / ".claude" / "scaffold-version.json"
    if dry_run:
        log(f"  Would write version stamp: {stamp_path}")
        return
    stamp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stamp_path, "w", encoding="utf-8") as f:
        json.dump(stamp, f, indent=2)
        f.write("\n")
    log(f"  Version stamp written: v{VERSION} ({mode})")


def create_removal_backup(target: Path, dry_run: bool) -> str:
    """Create a timestamped zip backup of scaffold files before removal."""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_name = f"claudescaffold-backup-{ts}.zip"
    backup_path = target / backup_name

    items_to_backup = []
    scaffold_dir = target / "scaffold"
    claude_md = target / "CLAUDE.md"
    skills_dir = target / ".claude" / "skills"
    stamp_file = target / ".claude" / "scaffold-version.json"

    if scaffold_dir.is_dir():
        for f in scaffold_dir.rglob("*"):
            if f.is_file():
                items_to_backup.append((f, f.relative_to(target)))
    if claude_md.is_file():
        items_to_backup.append((claude_md, claude_md.relative_to(target)))
    if stamp_file.is_file():
        items_to_backup.append((stamp_file, stamp_file.relative_to(target)))
    if skills_dir.is_dir():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and skill_dir.name.startswith(SCAFFOLD_SKILL_PREFIX):
                for f in skill_dir.rglob("*"):
                    if f.is_file():
                        items_to_backup.append((f, f.relative_to(target)))

    if dry_run:
        log(f"  Would create backup: {backup_name} ({len(items_to_backup)} files)")
        return backup_name

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for abs_path, rel_path in items_to_backup:
            zf.write(abs_path, str(rel_path))
    log(f"  Created backup: {backup_name} ({len(items_to_backup)} files)")
    return backup_name


# ---------------------------------------------------------------------------
# CLI parsing
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="ClaudeScaffold — install, upgrade, or remove the scaffold pipeline.",
        epilog="Example: python claudescaffold.py --install /path/to/your/project",
    )
    parser.add_argument("--version", action="version", version=f"ClaudeScaffold {VERSION}")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--install", action="store_true", help="Install scaffold into the target project")
    mode_group.add_argument("--upgrade", action="store_true", help="Upgrade scaffold infrastructure (preserves user content)")
    mode_group.add_argument("--remove", action="store_true", help="Remove scaffold from the target project")

    parser.add_argument("target", nargs="?", help="Path to the target project directory")
    parser.add_argument("--branch", default="main", help="GitHub branch or tag to download (default: main)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing scaffold/ (install) or confirm removal (remove)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without making changes")
    parser.add_argument("--verbose", action="store_true", help="List every file as it is copied")

    args = parser.parse_args()

    if not args.install and not args.upgrade and not args.remove:
        parser.error("No mode specified. Use --install, --upgrade, or --remove.")

    if not args.target:
        parser.error("Target directory is required.")

    return args


def validate_target(target: Path):
    """Check that the target directory exists and is writable."""
    if not target.is_dir():
        print(f"ERROR: Target directory does not exist: {target}", file=sys.stderr)
        sys.exit(1)
    if not os.access(target, os.W_OK):
        print(f"ERROR: Target directory is not writable: {target}", file=sys.stderr)
        sys.exit(1)


def download_and_extract(branch: str):
    """Download from GitHub, extract, return (tmp_dir, install_dir)."""
    print(f"\n0. Downloading ClaudeScaffold ({branch})")
    tmp_dir = tempfile.mkdtemp(prefix="claudescaffold-")
    zip_path = Path(tmp_dir) / "repo.zip"

    download_zip(branch, zip_path)

    print("  Extracting...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(tmp_dir)

    # Locate the Install/ directory inside the extracted archive
    extracted_dirs = [d for d in Path(tmp_dir).iterdir() if d.is_dir()]
    install_dir = None
    for d in extracted_dirs:
        candidate = d / "Install"
        if candidate.is_dir():
            install_dir = candidate
            break

    if install_dir is None:
        print("ERROR: Could not find Install/ directory in downloaded archive.", file=sys.stderr)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        sys.exit(1)

    print(f"  Source: {install_dir}")
    return tmp_dir, install_dir


def verify_installation(target: Path, dry_run: bool):
    """Verify skills count and key files after install/upgrade."""
    print(f"\n4. Verification")
    if dry_run:
        log("  Skipped (dry run)")
        return

    dst_skills_dir = target / ".claude" / "skills"
    dst_scaffold_dir = target / "scaffold"

    # Count installed skill dirs
    if dst_skills_dir.is_dir():
        installed_skills = [
            d for d in dst_skills_dir.iterdir()
            if d.is_dir() and d.name.startswith(SCAFFOLD_SKILL_PREFIX)
        ]
        skill_count = len(installed_skills)
    else:
        skill_count = 0

    # Verify key files
    key_files = [
        target / "CLAUDE.md",
        dst_scaffold_dir / "_index.md",
        dst_scaffold_dir / "WORKFLOW.md",
    ]
    missing = [str(f.relative_to(target)) for f in key_files if not f.exists()]

    if skill_count == EXPECTED_SKILLS and not missing:
        log(f"  All checks passed: {skill_count} skills, key files present")
    else:
        if skill_count != EXPECTED_SKILLS:
            log(f"  WARNING: Expected {EXPECTED_SKILLS} scaffold skills, found {skill_count}")
        if missing:
            log(f"  WARNING: Missing key files: {', '.join(missing)}")


# ---------------------------------------------------------------------------
# Mode: --install
# ---------------------------------------------------------------------------

def do_install(args):
    target = Path(args.target).resolve()
    validate_target(target)

    tmp_dir, install_dir = download_and_extract(args.branch)

    try:
        # Source paths
        src_claude_md = install_dir / "CLAUDE.md"
        src_claude_dir = install_dir / ".claude"
        src_scaffold_dir = install_dir / "scaffold"
        src_settings = src_claude_dir / "settings.local.json"

        # Target paths
        dst_claude_md = target / "CLAUDE.md"
        dst_claude_dir = target / ".claude"
        dst_scaffold_dir = target / "scaffold"
        dst_settings = dst_claude_dir / "settings.local.json"
        dst_skills_dir = dst_claude_dir / "skills"

        label = "[DRY RUN] " if args.dry_run else ""
        print(f"\n{label}Installing ClaudeScaffold into {target}\n")

        backups_created = []
        files_copied = 0
        skills_installed = 0

        # --- CLAUDE.md ---
        print("1. CLAUDE.md")
        if dst_claude_md.exists():
            backup = target / "CLAUDE.md.bak"
            if args.dry_run:
                log("  Would back up existing CLAUDE.md to CLAUDE.md.bak")
            else:
                shutil.copy2(dst_claude_md, backup)
                log("  Backed up existing CLAUDE.md to CLAUDE.md.bak")
            backups_created.append("CLAUDE.md.bak")
        copy_file(src_claude_md, dst_claude_md, args.dry_run, args.verbose)
        files_copied += 1

        # --- .claude/ directory ---
        print("\n2. .claude/ (skills + settings)")

        # Settings merge
        if dst_settings.exists():
            log("  Existing settings.local.json found — merging")
            merge_settings(dst_settings, src_settings, args.dry_run, args.verbose)
        else:
            copy_file(src_settings, dst_settings, args.dry_run, args.verbose)
        files_copied += 1

        # Skills — copy all scaffold skill dirs, preserve non-scaffold user skills
        src_skills_dir = src_claude_dir / "skills"
        if src_skills_dir.is_dir():
            for skill_dir in sorted(src_skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                if skill_dir.name in EXCLUDE_DIRS:
                    continue
                for src_file in sorted(skill_dir.rglob("*")):
                    if src_file.is_file() and not is_excluded(src_file.relative_to(src_skills_dir)):
                        rel = src_file.relative_to(src_skills_dir)
                        copy_file(src_file, dst_skills_dir / rel, args.dry_run, args.verbose)
                        files_copied += 1
                skills_installed += 1

        # --- scaffold/ directory ---
        print("\n3. scaffold/")
        if dst_scaffold_dir.exists():
            if not args.force:
                print(f"\n  ERROR: scaffold/ already exists at {dst_scaffold_dir}")
                print("  This directory may contain project-specific design data.")
                print("  Use --force to overwrite, or remove it manually first.")
                sys.exit(1)
            else:
                if args.dry_run:
                    log("  Would remove and replace existing scaffold/")
                else:
                    shutil.rmtree(dst_scaffold_dir)
                    log("  Removed existing scaffold/ (--force)")

        scaffold_files = collect_files(src_scaffold_dir, src_scaffold_dir)
        for src_file, rel_path in scaffold_files:
            copy_file(src_file, dst_scaffold_dir / rel_path, args.dry_run, args.verbose)
            files_copied += 1

        # --- Verification ---
        verify_installation(target, args.dry_run)

        # --- Version stamp ---
        print("\n5. Version stamp")
        write_version_stamp(target, args.branch, "install", args.dry_run)

        # --- Summary ---
        print(f"\n{'=' * 50}")
        print(f"{label}Installation summary:")
        print(f"  Source:           github.com/rmans/ClaudeScaffold ({args.branch})")
        print(f"  Files copied:     {files_copied}")
        print(f"  Skills installed: {skills_installed}")
        if backups_created:
            print(f"  Backups created:  {', '.join(backups_created)}")
        print(f"  Target:           {target}")
        print(f"\nNext step: Run /scaffold-new-design to start the pipeline")
        print()

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Mode: --upgrade
# ---------------------------------------------------------------------------

def do_upgrade(args):
    target = Path(args.target).resolve()
    validate_target(target)

    dst_scaffold_dir = target / "scaffold"
    dst_skills_dir = target / ".claude" / "skills"

    # Pre-check: scaffold must already be installed
    has_scaffold = dst_scaffold_dir.is_dir()
    has_skills = dst_skills_dir.is_dir() and any(
        d.is_dir() and d.name.startswith(SCAFFOLD_SKILL_PREFIX)
        for d in dst_skills_dir.iterdir()
    ) if dst_skills_dir.is_dir() else False

    if not has_scaffold and not has_skills:
        print("ERROR: No existing scaffold installation found.", file=sys.stderr)
        print("  Use --install for first-time installation.", file=sys.stderr)
        sys.exit(1)

    tmp_dir, install_dir = download_and_extract(args.branch)

    try:
        src_claude_md = install_dir / "CLAUDE.md"
        src_claude_dir = install_dir / ".claude"
        src_scaffold_dir = install_dir / "scaffold"
        src_settings = src_claude_dir / "settings.local.json"

        dst_claude_md = target / "CLAUDE.md"
        dst_claude_dir = target / ".claude"
        dst_settings = dst_claude_dir / "settings.local.json"

        label = "[DRY RUN] " if args.dry_run else ""
        print(f"\n{label}Upgrading ClaudeScaffold in {target}\n")

        files_replaced = 0
        files_preserved = 0
        dirs_added = 0

        # --- Step 1: CLAUDE.md ---
        print("1. CLAUDE.md")
        if dst_claude_md.exists():
            backup = target / "CLAUDE.md.bak"
            if args.dry_run:
                log("  Would back up existing CLAUDE.md to CLAUDE.md.bak")
            else:
                shutil.copy2(dst_claude_md, backup)
                log("  Backed up existing CLAUDE.md to CLAUDE.md.bak")
        copy_file(src_claude_md, dst_claude_md, args.dry_run, args.verbose)
        files_replaced += 1

        # --- Step 2: .claude/ (skills + settings) ---
        print("\n2. .claude/ (skills + settings)")

        # Delete all existing scaffold-* skill dirs, then copy fresh
        if dst_skills_dir.is_dir():
            for skill_dir in sorted(dst_skills_dir.iterdir()):
                if skill_dir.is_dir() and skill_dir.name.startswith(SCAFFOLD_SKILL_PREFIX):
                    if args.dry_run:
                        log(f"  Would remove: {skill_dir.name}/", verbose_only=True, verbose=args.verbose)
                    else:
                        shutil.rmtree(skill_dir)
                        log(f"  Removed: {skill_dir.name}/", verbose_only=True, verbose=args.verbose)

        src_skills_dir = src_claude_dir / "skills"
        skills_installed = 0
        if src_skills_dir.is_dir():
            for skill_dir in sorted(src_skills_dir.iterdir()):
                if not skill_dir.is_dir() or skill_dir.name in EXCLUDE_DIRS:
                    continue
                for src_file in sorted(skill_dir.rglob("*")):
                    if src_file.is_file() and not is_excluded(src_file.relative_to(src_skills_dir)):
                        rel = src_file.relative_to(src_skills_dir)
                        copy_file(src_file, dst_skills_dir / rel, args.dry_run, args.verbose)
                        files_replaced += 1
                skills_installed += 1

        # Settings merge
        if dst_settings.exists():
            log("  Existing settings.local.json found — merging")
            merge_settings(dst_settings, src_settings, args.dry_run, args.verbose)
        else:
            copy_file(src_settings, dst_settings, args.dry_run, args.verbose)

        # --- Step 3: scaffold/ (replace infrastructure, preserve user content) ---
        print("\n3. scaffold/ (infrastructure upgrade)")

        # 3a: Replace infrastructure directories entirely
        for dir_name in sorted(UPGRADE_REPLACE_DIRS):
            src_dir = src_scaffold_dir / dir_name
            dst_dir = dst_scaffold_dir / dir_name
            if not src_dir.is_dir():
                continue
            if dst_dir.is_dir():
                if args.dry_run:
                    log(f"  Would replace: scaffold/{dir_name}/")
                else:
                    shutil.rmtree(dst_dir)
                    log(f"  Replaced: scaffold/{dir_name}/", verbose_only=True, verbose=args.verbose)
            dir_files = collect_files(src_dir, src_dir)
            for src_file, rel_path in dir_files:
                copy_file(src_file, dst_dir / rel_path, args.dry_run, args.verbose)
                files_replaced += 1

        # 3b: Replace infrastructure root files
        for file_name in sorted(UPGRADE_REPLACE_ROOT_FILES):
            src_file = src_scaffold_dir / file_name
            if not src_file.is_file():
                continue
            dst_file = dst_scaffold_dir / file_name
            if args.dry_run:
                log(f"  Would replace: scaffold/{file_name}")
            else:
                log(f"  Replaced: scaffold/{file_name}", verbose_only=True, verbose=args.verbose)
            copy_file(src_file, dst_file, args.dry_run, args.verbose)
            files_replaced += 1

        # 3c: Replace infrastructure subdir files
        for rel_file in sorted(UPGRADE_REPLACE_SUBDIR_FILES):
            src_file = src_scaffold_dir / rel_file
            if not src_file.is_file():
                continue
            dst_file = dst_scaffold_dir / rel_file
            if args.dry_run:
                log(f"  Would replace: scaffold/{rel_file}")
            else:
                log(f"  Replaced: scaffold/{rel_file}", verbose_only=True, verbose=args.verbose)
            copy_file(src_file, dst_file, args.dry_run, args.verbose)
            files_replaced += 1

        # 3d: Copy any new directories that don't exist in target
        if src_scaffold_dir.is_dir():
            for src_child in sorted(src_scaffold_dir.iterdir()):
                if not src_child.is_dir():
                    continue
                dst_child = dst_scaffold_dir / src_child.name
                if not dst_child.exists():
                    log(f"  New directory: scaffold/{src_child.name}/")
                    child_files = collect_files(src_child, src_child)
                    for src_file, rel_path in child_files:
                        copy_file(src_file, dst_child / rel_path, args.dry_run, args.verbose)
                        files_replaced += 1
                    dirs_added += 1

        # 3e: Count preserved dirs for summary
        if dst_scaffold_dir.is_dir():
            for dst_child in sorted(dst_scaffold_dir.iterdir()):
                if dst_child.is_dir() and dst_child.name not in UPGRADE_REPLACE_DIRS:
                    files_preserved += 1  # count as preserved directories

        # --- Step 4: Verification ---
        verify_installation(target, args.dry_run)

        # --- Step 5: Version stamp ---
        print("\n5. Version stamp")
        write_version_stamp(target, args.branch, "upgrade", args.dry_run)

        # --- Summary ---
        print(f"\n{'=' * 50}")
        print(f"{label}Upgrade summary:")
        print(f"  Source:            github.com/rmans/ClaudeScaffold ({args.branch})")
        print(f"  Files replaced:    {files_replaced}")
        print(f"  Skills refreshed:  {skills_installed}")
        print(f"  User dirs kept:    {files_preserved}")
        if dirs_added:
            print(f"  New dirs added:    {dirs_added}")
        print(f"  Target:            {target}")
        print()

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Mode: --remove
# ---------------------------------------------------------------------------

def do_remove(args):
    target = Path(args.target).resolve()
    validate_target(target)

    dst_scaffold_dir = target / "scaffold"
    dst_skills_dir = target / ".claude" / "skills"
    dst_claude_md = target / "CLAUDE.md"
    dst_stamp = target / ".claude" / "scaffold-version.json"

    # Pre-check: must have something to remove
    has_scaffold = dst_scaffold_dir.is_dir()
    has_skills = dst_skills_dir.is_dir() and any(
        d.is_dir() and d.name.startswith(SCAFFOLD_SKILL_PREFIX)
        for d in dst_skills_dir.iterdir()
    ) if dst_skills_dir.is_dir() else False

    if not has_scaffold and not has_skills:
        print("ERROR: No scaffold installation found to remove.", file=sys.stderr)
        sys.exit(1)

    if not args.force:
        print("ERROR: --force is required for removal.", file=sys.stderr)
        print("  This will remove scaffold/, scaffold skills, and CLAUDE.md.", file=sys.stderr)
        print("  A backup zip will be created first.", file=sys.stderr)
        print(f"\n  Run: python claudescaffold.py --remove --force {args.target}", file=sys.stderr)
        sys.exit(1)

    label = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{label}Removing ClaudeScaffold from {target}\n")

    # --- Step 1: Backup ---
    print("1. Creating backup")
    backup_name = create_removal_backup(target, args.dry_run)

    # --- Step 2: Remove scaffold/ ---
    print("\n2. Removing scaffold/")
    if has_scaffold:
        if args.dry_run:
            log(f"  Would remove: scaffold/")
        else:
            shutil.rmtree(dst_scaffold_dir)
            log("  Removed: scaffold/")
    else:
        log("  Not present, skipping")

    # --- Step 3: Remove scaffold skills ---
    print("\n3. Removing scaffold skills")
    skills_removed = 0
    if dst_skills_dir.is_dir():
        for skill_dir in sorted(dst_skills_dir.iterdir()):
            if skill_dir.is_dir() and skill_dir.name.startswith(SCAFFOLD_SKILL_PREFIX):
                if args.dry_run:
                    log(f"  Would remove: .claude/skills/{skill_dir.name}/")
                else:
                    shutil.rmtree(skill_dir)
                    log(f"  Removed: .claude/skills/{skill_dir.name}/", verbose_only=True, verbose=args.verbose)
                skills_removed += 1
    log(f"  {skills_removed} scaffold skill(s) removed")

    # --- Step 4: Remove CLAUDE.md ---
    print("\n4. Removing CLAUDE.md")
    if dst_claude_md.is_file():
        if args.dry_run:
            log("  Would remove: CLAUDE.md")
        else:
            dst_claude_md.unlink()
            log("  Removed: CLAUDE.md")
    else:
        log("  Not present, skipping")

    # --- Step 5: Remove version stamp ---
    print("\n5. Removing version stamp")
    if dst_stamp.is_file():
        if args.dry_run:
            log("  Would remove: .claude/scaffold-version.json")
        else:
            dst_stamp.unlink()
            log("  Removed: .claude/scaffold-version.json")
    else:
        log("  Not present, skipping")

    # --- Summary ---
    print(f"\n{'=' * 50}")
    print(f"{label}Removal summary:")
    print(f"  Backup:          {backup_name}")
    print(f"  Skills removed:  {skills_removed}")
    print(f"  Preserved:       .claude/settings.local.json, non-scaffold skills")
    print(f"  Target:          {target}")
    print()


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    if args.install:
        do_install(args)
    elif args.upgrade:
        do_upgrade(args)
    elif args.remove:
        do_remove(args)


if __name__ == "__main__":
    main()
