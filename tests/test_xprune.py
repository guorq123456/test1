"""+xprune (search.xprune; the architecture thread 2026-10-10 16:57Z): discard choices kept to the most discardable
hand cards by a cross-turn judgment. Off by default."""
from svsim.core.actions import Attack, EndTurn
from svsim.core.engine import legal_actions
from svsim.search.xprune import XPrune, discards, schedule
from svsim.tools.arena import make_agent
from svsim.tools.gate import _search
from svsim.tools.puzzles import puzzles

PUZZLES = {n: b for n, b, a in puzzles()}


def _discarded(state, action):
    hand = {c.uid: c.defn.name for c in state.players[state.active].hand}
    return [hand[t] for t in getattr(action, "targets", ()) or () if t in hand]


def test_schedule_plays_the_most_points_each_turn():
    # budgets 3, then 4: the 3 now; next turn 4 points either way, the earlier card (the 4) first; the 2s never
    assert schedule([4, 3, 2, 2], [3, 4]) == [1, 0, 2, 2]
    assert schedule([3, 2, 2], [0, 4]) == [2, 1, 1]
    assert schedule([10, 1], [1, 10]) == [1, 0]
    assert schedule([5], [-1, 5]) == [1]


def test_discard_choices_are_found_by_resolving_them():
    s = PUZZLES["ramp-erntz-normagdala"](1)
    hand = {c.uid for c in s.players[s.active].hand}
    found = [a for a in legal_actions(s) if any(t in hand for t in getattr(a, "targets", ()) or ())]
    assert found and all(discards(s, a, [t for t in a.targets if t in hand]) for a in found)


def test_puzzle_2_keeps_the_discard_salem_made():
    s = PUZZLES["ramp-erntz-normagdala"](1)
    legal, xp = legal_actions(s), XPrune()
    kept = [a for a in legal if not xp(s, a)]
    assert (len(legal), len(kept)) == (56, 20)
    spilling = [a for a in kept if hasattr(a, "uid") and s.in_hand(s.active, a.uid) is not None
                and s.in_hand(s.active, a.uid).defn.name == "Spilling Red"]
    assert {n for a in spilling for n in _discarded(s, a)} == {"Vorlalai, Eld Blades", "Kimika, Cook of Happiness"}


def test_puzzle_3_cuts_the_bots_discard_pair():
    s = PUZZLES["ramp-erntz-spilling"](1)
    legal, xp = legal_actions(s), XPrune()
    kept = [a for a in legal if not xp(s, a)]
    assert (len(legal), len(kept)) == (15, 10)
    pairs = [sorted(_discarded(s, a)) for a in kept if len(_discarded(s, a)) == 2]
    assert ["Erntz, Governing Justice", "Sloth of the Crestpetal"] not in pairs      # level-strong's line
    assert any("Vorlalai, Eld Blades" in _discarded(s, a) for a in kept)


def test_other_moves_are_never_vetoed():
    s = PUZZLES["ramp-erntz-normagdala"](1)
    xp = XPrune()
    assert not any(xp(s, a) for a in legal_actions(s) if isinstance(a, (Attack, EndTurn)) or not
                   getattr(a, "targets", ()))


def test_flag_off_by_default_and_parsed():
    assert _search(make_agent("mcts:20+plan+learned+phased", 0)).veto is None
    on = _search(make_agent("mcts:20+plan+learned+phased+xprune=3:2", 0))
    assert on.veto is not None
    s = PUZZLES["ramp-erntz-spilling"](1)
    assert sum(not on.veto(s, a) for a in legal_actions(s)) > 10        # m 3 keeps more than m 2's 10


def test_orders_and_wider_m():
    s = PUZZLES["ramp-erntz-normagdala"](1)
    legal = legal_actions(s)
    for order in ("when", "cost", "value"):
        assert sum(not XPrune(3, 3, order)(s, a) for a in legal) == 26
    xp = XPrune(3, 3, "cost")
    kept = {n for a in legal if not xp(s, a) for n in _discarded(s, a)}
    assert "Vorlalai, Eld Blades" in kept and "Erntz, Governing Justice" not in kept
