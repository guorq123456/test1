from svsim.cards import demo
from svsim.core.actions import Attack, EndTurn, Evolve
from svsim.core.engine import apply, legal_actions
from svsim.core.state import leader_uid

from helpers import put, start


def evolves(state):
    return [a for a in legal_actions(state) if isinstance(a, Evolve)]


def advance_to_own_turn(state, player, turn):
    while not (state.active == player and state.players[player].turns_taken == turn):
        apply(state, EndTurn())


def test_unlock_turns_first_and_second_player():
    for player, evo, super_ in ((0, 5, 7), (1, 4, 6)):
        state = start(first=0)
        advance_to_own_turn(state, player, evo - 1)
        put(state, player, demo.FOOTMAN)
        assert not evolves(state)
        advance_to_own_turn(state, player, evo)
        assert evolves(state) and not any(a.super_ for a in evolves(state))
        advance_to_own_turn(state, player, super_)
        assert any(a.super_ for a in evolves(state))


def test_evolve_stats_and_one_per_turn():
    state = start(first=1)
    advance_to_own_turn(state, 0, 4)                # player 0 goes second: evolves from own turn 4
    fresh = put(state, 0, demo.FOOTMAN, ready=False)
    enemy = put(state, 1, demo.FOOTMAN)
    apply(state, Evolve(fresh.uid))
    assert (fresh.atk, fresh.life) == (3, 4) and state.players[0].ep == 1
    targets = {a.target for a in legal_actions(state) if isinstance(a, Attack)}
    assert enemy.uid in targets and leader_uid(1) not in targets   # evolved: Rush-like
    put(state, 0, demo.FOOTMAN)
    assert not evolves(state)                       # one evolution per turn


def test_super_evolve_invincible_on_own_turn_and_knockback():
    state = start(first=0)
    advance_to_own_turn(state, 0, 7)
    lancer = put(state, 0, demo.LANCER)             # 3/2 -> 6/5
    giant = put(state, 1, demo.GIANT)               # 5/5
    apply(state, Evolve(lancer.uid, super_=True))
    assert (lancer.atk, lancer.life) == (6, 5)
    apply(state, Attack(lancer.uid, giant.uid))
    assert lancer.life == 5                         # no damage during own turn
    assert giant.fate == 1
    assert state.players[1].leader_hp == 19         # knockback
    apply(state, EndTurn())
    put(state, 1, demo.LANCER)
    attacker = state.players[1].field[-1]
    apply(state, Attack(attacker.uid, lancer.uid))
    assert lancer.life == 2                         # opponent's turn: takes damage


def test_evolve_ability_fires_with_points():
    state = start(first=0)
    advance_to_own_turn(state, 0, 5)
    giant = put(state, 0, demo.GIANT)
    victims = [put(state, 1, demo.FOOTMAN), put(state, 1, demo.SHIELDBEARER)]
    apply(state, Evolve(giant.uid))
    assert [v.life for v in victims] == [0, 1] and victims[0].fate == 1
