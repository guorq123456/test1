"""learn.setpolicy with each replayed state's deck names taken from the record's "names" (seat order).

Pool self-play records (scaledata play --pool) replay with empty deck names, so `setpolicy encode --deck LABEL`
finds no decision. This sets them before setpolicy sees a state; nothing else changes.

    python analysis/pilot/setpolicy_named.py encode --records DIR --out DIR --workers 2 --deck dfm/RUNE-ユーリ
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import svsim.tools.arena  # noqa: E402,F401  (card scripts)
from svsim.tools import records as R  # noqa: E402

_steps = R.steps


def steps(record):
    names = record.get("names") or []
    for state, action in _steps(record):
        for i, name in enumerate(names[:len(state.players)]):
            state.players[i].deck_name = name
        yield state, action


R.steps = steps

from svsim.learn import setpolicy  # noqa: E402

if __name__ == "__main__":
    setpolicy.main()
