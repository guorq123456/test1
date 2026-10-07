"""Shadow prices (search.prices): resources valued by what they buy."""
from svsim.cards import demo
from svsim.core.actions import EndTurn
from svsim.core.engine import apply
from svsim.search.evaluate import DEFAULT, evaluate, follower_value
from svsim.search.prices import Priced

from helpers import put, start


def _bare():
    state = start()
    for p in state.players:
        p.hand.clear()
    return state


def test_the_last_evolution_point_is_worth_what_it_adds_to_next_turn():
    state = _bare()
    put(state, 0, demo.RAIDER)                        # 2/1 Storm: hits for 2 next turn, 5 super-evolved
    me = state.players[0]
    me.turns_taken = 6                                # going first: super-evolution unlocks next turn
    priced = Priced(survival=False)
    for ep, sep, price in ((2, 2, 3), (0, 1, 3), (1, 0, 2), (0, 0, 0)):
        me.ep, me.sep = ep, sep
        assert priced.points_price(state, 0) == price, (ep, sep)
    me.sep = 2
    assert priced.points_price(state, 0) == priced.points_price(state, 0)   # cached, points restored
    assert (me.ep, me.sep) == (0, 2)
    me.turns_taken = 3                                # nothing unlocked next turn: no price
    assert priced.points_price(state, 0) == 0


def test_followers_count_for_what_survives_the_opponents_turn():
    class Answered:                                   # a matchup where 1-defense followers never survive
        def chance(self, turn, life):
            return 0.0 if life <= 1 else 1.0

    state = _bare()
    raider = put(state, 0, demo.RAIDER)
    put(state, 0, demo.SHIELDBEARER)                  # 3 defense: stays
    priced = Priced(points=False, profiles={})
    assert priced.board_discount(state, 0) == 0.0     # no games for the matchup: no discount
    from svsim.learn.model import deck_craft
    key = (deck_craft(state, 0), deck_craft(state, 1))
    priced = Priced(points=False, profiles={key: Answered()})
    assert priced.board_discount(state, 0) == follower_value(raider, DEFAULT)
    base = evaluate(state, 0)
    assert priced.score(state, 0) == base - follower_value(raider, DEFAULT)
    assert priced.score(state, 0, player_moves_next=True) == evaluate(state, 0, player_moves_next=True)
    apply(state, EndTurn())                           # the opponent's turn under way
    assert priced.board_discount(state, 0) == follower_value(raider, DEFAULT)
