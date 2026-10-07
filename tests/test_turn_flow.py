from svsim.cards import demo
from svsim.core.actions import EndTurn, Mulligan, UseBonusPP
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Phase

from helpers import pass_turns, start


def test_opening_hands_and_first_turn_draw():
    state = new_game([demo.FOOTMAN] * 40, [demo.FOOTMAN] * 40, seed=1, first=0)
    assert [len(p.hand) for p in state.players] == [4, 4]
    assert len(legal_actions(state)) == 16          # any subset of 4 cards
    apply(state, Mulligan((0, 2)))
    assert len(state.players[0].hand) == 4 and len(state.players[0].deck) == 36
    apply(state, Mulligan(()))
    assert state.phase == Phase.MAIN and state.turn == 1
    assert len(state.players[0].hand) == 5          # first player also draws on turn 1
    apply(state, EndTurn())
    assert len(state.players[1].hand) == 5          # second player draws 1, not 2


def test_play_points_grow_to_ten():
    state = start()
    pp = []
    for _ in range(24):
        pp.append(state.players[state.active].max_pp)
        apply(state, EndTurn())
    assert pp[:4] == [1, 1, 2, 2]
    assert max(pp) == 10


def test_bonus_pp_second_player_only_and_refund():
    state = start(first=0)
    assert UseBonusPP() not in legal_actions(state)
    apply(state, EndTurn())
    p1 = state.players[1]
    assert UseBonusPP() in legal_actions(state)
    apply(state, UseBonusPP())
    assert p1.pp == 2
    apply(state, EndTurn())                          # ended with PP left: use is refunded
    assert p1.bonus_ready


def test_bonus_pp_spent_then_refreshed_on_turn_six():
    state = start(first=0, deck=[demo.MAGE] * 40)
    pass_turns(state, 5)                             # player 1's third turn: 3 PP
    p1 = state.players[1]
    apply(state, UseBonusPP())
    p1.pp = 0                                        # spend everything
    apply(state, EndTurn())
    assert not p1.bonus_ready
    while p1.turns_taken < 6:
        apply(state, EndTurn())
    assert state.active == 1 and p1.bonus_ready


def test_empty_deck_loses():
    state = start(first=0)
    state.players[1].deck.clear()
    apply(state, EndTurn())
    assert state.over and state.winner == 0


def test_overdraw_burns_card():
    state = start(first=0)
    p1 = state.players[1]
    while len(p1.hand) < 9:
        p1.hand.append(p1.deck.pop())
    deck_before = len(p1.deck)
    apply(state, EndTurn())
    assert len(p1.hand) == 9 and len(p1.deck) == deck_before - 1 and p1.shadows == 1
