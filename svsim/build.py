"""Which build of the simulator is running: the git commit it came from.

The web build (tools.web.build) writes the commit into the copy of this file it
ships, since the page has no git; elsewhere it is read from git (with "+" when
the working tree has uncommitted changes). Game records keep it next to the
bot's spec (ui.session), so a game can be tied to the code that played it.
"""
from __future__ import annotations

from pathlib import Path

COMMIT = None                  # tools.web.build replaces this line in the copy it ships
_read: list = []


def git_commit(root: Path | None = None) -> str | None:
    """The short hash of the checkout's HEAD, "+" if tracked files have changed; None without git."""
    import subprocess
    root = root or Path(__file__).resolve().parents[1]
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True,
                              timeout=10)
        if head.returncode != 0:
            return None
        dirty = subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=root, timeout=10).returncode != 0
        return head.stdout.strip() + ("+" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        return None


def commit() -> str | None:
    if COMMIT is not None:
        return COMMIT
    if not _read:
        _read.append(git_commit())
    return _read[0]
