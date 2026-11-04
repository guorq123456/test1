"""The root's moves kept per decision (search.mcts, the architecture thread 2026-10-10 14:11Z): the same search with
and without the cache, and check mode finding no difference."""
import random

import svsim.search.mcts as M
from svsim.cards import decks
from svsim.core.engine import apply, legal_actions, new_game
from svsim.tools.arena import make_agent
from svsim.tools.gate import _search


def _positions(n=6, seed=3):
    d = decks.build(decks.RAMP_DRAGON)
    s = new_game(d, d, seed=seed)
    g = make_agent("greedy", 0)
    out, rng = [], random.Random(seed)
    while not s.over and len(out) < n:
        legal = legal_actions(s)
        if len(legal) > 3 and s.turn >= 6 and rng.random() < 0.5:
            out.append(s.clone())
        apply(s, g.act(s, legal))
    return out


def _roots(spec, states):
    rows = []
    for i, s in enumerate(states):
        search = _search(make_agent(spec, i))
        search.choose(s.clone())
        rows.append(sorted((repr(k), n.visits, repr(n.value)) for k, n in search.last_root.children.items()))
    return rows


def test_the_cache_leaves_the_search_unchanged(monkeypatch):
    states = _positions()
    assert states
    cached = _roots("mcts:60+plan+learned+phased", states)
    ids = frozenset(c.card_id for c in decks.KNOWN.values())
    monkeypatch.setattr(M, "ROOT_RECOMPUTE", ids)      # every card blocks the cache: moves computed every time
    assert _roots("mcts:60+plan+learned+phased", states) == cached


def test_check_mode_finds_no_difference(monkeypatch):
    monkeypatch.setattr(M, "ROOT_CHECK", True)
    M.ROOT_MISMATCHES.clear()
    M.ROOT_CHECKS[0] = 0
    _roots("mcts:40", _positions(seed=5))
    assert M.ROOT_CHECKS[0] > 50
    assert M.ROOT_MISMATCHES == []
