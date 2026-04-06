"""
Auto-commit hook for tracking project changes.
Runs every hour to scan, analyze, and commit changes.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_git_status():
    """Get current git status."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_changed_files_summary():
    """Get summary of changed files with their status."""
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def analyze_changes(changes: str) -> dict:
    """Analyze changes to determine commit type and scope."""
    if not changes:
        return {"type": None, "scope": None, "has_changes": False}

    lines = changes.split("\n")
    added = modified = deleted = renamed = 0

    for line in lines:
        if not line:
            continue
        status = line[:2]
        if "A" in status or "??" in status:
            added += 1
        if "M" in status:
            modified += 1
        if "D" in status:
            deleted += 1
        if "R" in status:
            renamed += 1

    # Determine commit type based on changes
    if deleted > added + modified:
        commit_type = "chore"
    elif added > modified + deleted:
        commit_type = "feat"
    elif modified > added + deleted:
        commit_type = "refactor"
    else:
        commit_type = "chore"

    return {
        "type": commit_type,
        "added": added,
        "modified": modified,
        "deleted": deleted,
        "renamed": renamed,
        "has_changes": True,
    }


def generate_commit_message(analysis: dict) -> str:
    """Generate English commit message based on analysis."""
    if not analysis["has_changes"]:
        return None

    commit_type = analysis["type"]
    parts = []

    if analysis["added"]:
        parts.append(f"add {analysis['added']} file(s)")
    if analysis["modified"]:
        parts.append(f"update {analysis['modified']} file(s)")
    if analysis["deleted"]:
        parts.append(f"remove {analysis['deleted']} file(s)")
    if analysis["renamed"]:
        parts.append(f"rename {analysis['renamed']} file(s)")

    description = ", ".join(parts)

    # Format: type(scope): description
    return f"{commit_type}: {description.capitalize()}"


def auto_commit():
    """Main auto-commit function."""
    os.chdir(PROJECT_ROOT)

    # Check if there are changes
    changes = get_changed_files_summary()
    if not changes:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No changes detected.")
        return

    # Analyze changes
    analysis = analyze_changes(changes)

    # Generate commit message
    commit_message = generate_commit_message(analysis)

    # Stage all changes
    subprocess.run(["git", "add", "-A"], check=True)

    # Commit
    subprocess.run(
        ["git", "commit", "-m", commit_message],
        check=True,
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Auto-committed: {commit_message}")

    # Note: Push is not automatic to avoid conflicts
    print("[auto-commit] Changes committed locally. Use 'git push' to sync.")


if __name__ == "__main__":
    auto_commit()
