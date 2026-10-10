"""+alloc=complex (search.mcts ISMCTS._complex_budget, opt-in): a decision's iterations are clip(K x max(n, BETA x
n0)), n its legal moves and n0 those at the turn's first searched decision; nothing changes without it."""
import pytest

from svsim.tools.arena import _alloc_option, make_agent
from svsim.tools.gate import _search


def test_the_option_parses_and_is_off_by_default():
    assert _alloc_option(["alloc=complex:24.5:0.4"]) == ("complex", 24.5, 0.4, 50, 1500)
    assert _alloc_option(["alloc=complex:20:0.5:30:900"]) == ("complex", 20.0, 0.5, 30, 900)
    with pytest.raises(ValueError):
        _alloc_option(["alloc=complex:20"])
    assert _search(make_agent("level-strong", 0)).alloc is None
    assert _search(make_agent("level-strong+complex", 0)).alloc == ("complex", 21.4, 0.4, 50, 1500)


def test_a_wide_turn_keeps_its_budget_on_its_narrower_decisions():
    from svsim.cards import demo
    from svsim.core.engine import legal_actions
    from helpers import give, put, set_pp, start
    search = _search(make_agent("mcts:200+plan+learned+phased+alloc=complex:10:0.5:20:1000", 0))
    s = start()
    for _ in range(6):
        give(s, 0, demo.FOOTMAN)
    put(s, 0, demo.LANCER)
    set_pp(s, 0, 6)
    n0 = len(legal_actions(s))
    assert search._complex_budget(s, 0) == min(1000, max(20, round(10 * n0)))
    s.players[0].hand.clear()                       # the same turn, now narrow: half the turn's start still counts
    n = len(legal_actions(s))
    assert n < n0 and search._complex_budget(s, 0) == min(1000, max(20, round(10 * max(n, 0.5 * n0))))
    s.turn += 2                                     # a new turn starts over
    assert search._complex_budget(s, 0) == min(1000, max(20, round(10 * n)))
