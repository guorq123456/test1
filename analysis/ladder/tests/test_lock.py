"""The files locked at 1.9 (LOCK.md) are as locked: changing one needs Salem's consent first (LEDGER, LOCK.md)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import check_lock  # noqa: E402


def test_the_locked_files_are_as_locked():
    assert len(check_lock.recorded()) == 14
    assert check_lock.differs() == []
