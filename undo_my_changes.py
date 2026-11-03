"""Undo every change made during the build-out and restore the original project files.

The original tree was snapshotted before any edit into
    <parent>/Sales-Operations-Intelligence-Copilot_BACKUP_<timestamp>/original/project-files.tar.gz

This script extracts that snapshot, restores the files it contains, and removes the
files that did not exist back then (the whole `web/` site, `scripts/`, and the two new
test modules). Local-only folders (.venv, logs, caches) are left untouched.

Usage (from the project root):

    python undo_my_changes.py --dry-run    # show exactly what would change
    python undo_my_changes.py --yes        # perform the restore
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKUP_GLOB = f"{PROJECT_ROOT.name}_BACKUP_*"

# Folders that hold local state only — never restored, never deleted.
PROTECTED_DIRS = {".venv", "__pycache__", ".pytest_cache", "logs", "node_modules", ".git"}

# Files that are not part of the backup but must survive the restore.
PROTECTED_FILES = {Path(__file__).name, ".DS_Store"}


def find_backup() -> Path:
    """Return the newest backup archive next to the project folder."""
    candidates = sorted(
        (path for path in PROJECT_ROOT.parent.glob(BACKUP_GLOB) if path.is_dir()),
        key=lambda path: path.name,
    )
    for directory in reversed(candidates):
        archive = directory / "original" / "project-files.tar.gz"
        if archive.exists():
            return archive
    raise FileNotFoundError(
        f"No backup archive found. Expected {PROJECT_ROOT.parent / BACKUP_GLOB / 'original/project-files.tar.gz'}"
    )


def is_protected(path: Path) -> bool:
    """True when a project-relative path lives in a local-only folder or file."""
    relative = path.relative_to(PROJECT_ROOT)
    if relative.name in PROTECTED_FILES or relative.parts[0] in PROTECTED_FILES:
        return True
    return any(part in PROTECTED_DIRS for part in relative.parts)


def collect_current_files() -> set[Path]:
    return {
        path.relative_to(PROJECT_ROOT)
        for path in PROJECT_ROOT.rglob("*")
        if path.is_file() and not is_protected(path)
    }


def collect_archive_files(extracted: Path) -> set[Path]:
    return {
        path.relative_to(extracted)
        for path in extracted.rglob("*")
        if path.is_file()
    }


def prune_empty_dirs() -> None:
    for directory in sorted(
        (path for path in PROJECT_ROOT.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        relative = directory.relative_to(PROJECT_ROOT)
        if any(part in PROTECTED_DIRS for part in relative.parts):
            continue
        try:
            next(directory.iterdir())
        except StopIteration:
            directory.rmdir()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backup", type=Path, help="Explicit path to project-files.tar.gz")
    parser.add_argument("--dry-run", action="store_true", help="Report the plan without touching files")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")
    args = parser.parse_args()

    archive = args.backup or find_backup()
    print(f"Backup archive : {archive}")

    with tempfile.TemporaryDirectory() as tmp:
        extracted = Path(tmp)
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(extracted)

        original_files = collect_archive_files(extracted)
        current_files = collect_current_files()

        to_write = sorted(original_files)
        to_delete = sorted(current_files - original_files)

        print(f"Files in backup: {len(to_write)}")
        print(f"Files to remove: {len(to_delete)}")
        for path in to_delete:
            print(f"  - {path}")

        if args.dry_run:
            print("\nDry run complete — nothing was modified.")
            return 0

        if not args.yes:
            answer = input("\nRestore the project to its original state? [y/N] ").strip().lower()
            if answer not in {"y", "yes"}:
                print("Aborted.")
                return 1

        for relative in to_write:
            source = extracted / relative
            target = PROJECT_ROOT / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        for relative in to_delete:
            (PROJECT_ROOT / relative).unlink(missing_ok=True)

        prune_empty_dirs()

    print("\nRestored. The original files are back and the added site/scripts are gone.")
    print("Remaining: delete this script (and the backup folder) when you are satisfied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
