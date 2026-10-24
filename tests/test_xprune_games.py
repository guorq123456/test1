"""search.xprune's cache across games (the architecture thread 2026-10-17 19:11Z). The cache is keyed by hand uids,
unique within a game only: a veto kept from one game to the next gives the next game the answers a new one would,
because the cache is emptied when the new game starts (and, without that, an entry left by the earlier game under
the same key would be read)."""
import gzip
import json
from pathlib import Path

from svsim.core.engine import legal_actions
from svsim.core.enums import Phase
from svsim.search.xprune import XPrune
from svsim.tools import records as R

REC = Path(__file__).resolve().parents[1] / "analysis/scaling/data/gen4x/rec/rec-72300000.jsonl.gz"


def _games(n):
    with gzip.open(REC, "rt") as fh:
        return [json.loads(next(fh)) for _ in range(n)]


def _calls(rec):
    """(state, action) for every legal action at every main-phase position of the game, in order."""
    for state, _ in R.steps(rec):
        if state.phase == Phase.MAIN and state.winner is None:
            for a in legal_actions(state):
                yield state.clone(), a


def _cut(veto, state, action):
    before = veto.calls
    out = veto(state, action)
    return out, veto.calls > before


def test_a_veto_kept_for_the_next_game_answers_as_a_new_one():
    first, second = _games(2)
    kept, fresh = XPrune(3, 3, "cost"), XPrune(3, 3, "cost")
    for s, a in _calls(first):
        kept(s, a)
    assert kept._turn > 2 and kept._allowed
    pairs = list(_calls(second))
    assert [kept(s, a) for s, a in pairs] == [fresh(s, a) for s, a in pairs]


def test_an_entry_left_by_the_earlier_game_is_not_read():
    first, second = _games(2)
    pairs = list(_calls(second))
    probe = XPrune(3, 3, "cost")
    target = None                                      # a discard choice the veto works on in the second game
    for s, a in pairs:
        if _cut(probe, s, a)[1]:
            k = len([t for t in a.targets if t in {c.uid for c in s.players[s.active].hand}])
            target = XPrune.key(s, a, k)
            break
    assert target is not None
    want = [XPrune(3, 3, "cost")(s, a) for s, a in pairs]

    def poisoned():
        v = XPrune(3, 3, "cost")
        for s, a in _calls(first):
            v(s, a)
        v._allowed[target] = set()                    # as if the earlier game had left this answer: cut them all
        return v

    v = poisoned()
    assert [v(s, a) for s, a in pairs] == want         # emptied at the new game's first call
    old = poisoned()
    old._turn = 0                                      # the earlier behaviour: never emptied
    assert [old(s, a) for s, a in pairs] != want
