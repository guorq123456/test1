"""The search's keys for one's own hand cards (search.mcts._locator, S32 / LD-81 in analysis/ladder): copies with
the same card id and cost but a different state are different moves; interchangeable copies stay one move.

Before 11-25 a hand card was keyed by (card id, cost) only: with a Guileless Newsie swapped by a Clue in hand (2/2)
and a plain one (2/1), the search tried the first copy and the root played the last, the 2/1 that dies attacking a
Footman."""
import svsim.cards.library  # noqa: F401  (card scripts)
from svsim.cards import demo, sword
from svsim.core import effects as E
from svsim.core.actions import PlayCard
from svsim.core.engine import legal_actions
from svsim.search.mcts import ISMCTS, _locator, action_key

from helpers import give, put, set_pp, start


def _two_newsies():
    state = start(first=0, seed=0)
    state.players[0].hand.clear()
    swapped, plain = give(state, 0, sword.GUILELESS_NEWSIE), give(state, 0, sword.GUILELESS_NEWSIE)
    sword._swap_stats(swapped)                     # what its Clue script does in hand: swap, then +1/+0
    swapped.atk += 1
    set_pp(state, 0, 2)
    return state, swapped, plain


def _play_key(state, uid):
    where = _locator(state, state.active)
    return next(action_key(state, a, where) for a in legal_actions(state) if isinstance(a, PlayCard) and a.uid == uid)


def test_copies_in_different_states_are_different_moves():
    state, swapped, plain = _two_newsies()
    assert (swapped.atk, swapped.life) == (2, 2) and (plain.atk, plain.life) == (2, 1)
    k1, k2 = _play_key(state, swapped.uid), _play_key(state, plain.uid)
    assert k1 != k2
    assert k2 == ("P", ("H", True, sword.GUILELESS_NEWSIE.card_id, 2), (), ())       # a fresh copy: as before
    assert k1[1][:4] == k2[1][:4] and len(k1[1]) == 5                                # id and cost in place
    tried = ISMCTS(iterations=10, seed=0)._options(state, 0, None)
    assert k1 in tried and k2 in tried and tried[k1].uid == swapped.uid and tried[k2].uid == plain.uid


def test_the_search_plays_the_copy_it_searched():
    state, swapped, plain = _two_newsies()
    put(state, 1, demo.FOOTMAN)                    # 1/2: the 2/1 copy dies attacking it, the 2/2 one doesn't
    for seed in range(3):
        search = ISMCTS(iterations=200, seed=seed)
        action = search.choose(state)
        assert isinstance(action, PlayCard) and action.uid == swapped.uid, (seed, action)


def test_interchangeable_copies_stay_one_move():
    state = start(first=0, seed=0)
    state.players[0].hand.clear()
    a, b = give(state, 0, sword.GUILELESS_NEWSIE), give(state, 0, sword.GUILELESS_NEWSIE)
    set_pp(state, 0, 2)
    assert _locator(state, 0)[a.uid] == _locator(state, 0)[b.uid]   # (the engine lists one play for the two)
    E.spellboost(state, 0, 1, cards=[a])          # counted on every hand card, read by no card script
    where = _locator(state, 0)
    assert where[a.uid] == where[b.uid] == ("H", True, sword.GUILELESS_NEWSIE.card_id, 2)
    sword._swap_stats(a); sword._swap_stats(b)     # the same change to both: still one move
    a.atk += 1; b.atk += 1
    where = _locator(state, 0)
    assert where[a.uid] == where[b.uid] and len(where[a.uid]) == 5


def test_counters_and_grants_count_and_are_hashable():
    state = start(first=0, seed=0)
    state.players[0].hand.clear()
    a, b, c = (give(state, 0, sword.GUILELESS_NEWSIE) for _ in range(3))
    E.counters(a)["fused"] = [10131320, 10803310]        # a list value
    E.counters(b)["x"] = 2
    where = _locator(state, 0)
    assert len({where[a.uid], where[b.uid], where[c.uid]}) == 3
    hash(where[a.uid]); hash(where[b.uid])


def test_the_opponents_hand_keeps_id_and_cost():
    state = start(first=0, seed=0)
    x = give(state, 1, sword.GUILELESS_NEWSIE)
    x.atk += 3
    assert _locator(state, 0)[x.uid] == ("H", False, sword.GUILELESS_NEWSIE.card_id, x.cost)


def test_a_fuse_of_two_changed_copies_has_a_key():
    """(11-25 review) A Fuse's cards are sorted into its key; two changed copies whose states hold None where the
    other holds a value (a buff until the end of the turn, a Grant, against a permanent one) don't compare."""
    from svsim.cards import rune
    from svsim.core.actions import Fuse
    state = start(first=0, seed=0)
    state.players[0].hand.clear()
    give(state, 0, rune.ECSTATIC_SCHOLAR)
    a, b = give(state, 0, rune.OBSESSED_TEST_SUBJECT), give(state, 0, rune.OBSESSED_TEST_SUBJECT)
    E.buff(state, a, 1, 0, until_turn=state.turn)
    E.buff(state, b, 1, 0)
    set_pp(state, 0, 3)
    fuses = [x for x in legal_actions(state) if isinstance(x, Fuse) and len(x.cards) == 2]
    assert fuses
    where = _locator(state, 0)
    assert all(len(action_key(state, x, where)[2]) == 2 for x in fuses)
    ISMCTS(iterations=20, seed=0).choose(state)
