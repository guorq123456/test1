"""Moves the search leaves out, and searching relative to the starting position.

The player caught the AI attacking with Sagatsumatsu (Storm) for 5 and evolving
it afterwards, losing 2 damage, twice in one game."""
from svsim.agents.greedy_agent import GreedyAgent
from svsim.cards import dragon, forest
from svsim.core.actions import Attack, EndTurn, Evolve
from svsim.core.engine import apply, legal_actions
from svsim.core.state import leader_uid
from svsim.search.evaluate import DEFAULT, evaluate
from svsim.search.mcts import ISMCTS
from svsim.search.moves import dominated, worth_trying

from helpers import put, start, unlock_evolution


def _saga_ready():
    state = start()
    unlock_evolution(state, 0)
    state.players[0].hand.clear()
    saga = put(state, 0, dragon.SAGATSUMATSU)
    return state, saga


def test_evolving_after_the_attack_is_left_out():
    state, saga = _saga_ready()
    evolve = Evolve(saga.uid)
    assert evolve in legal_actions(state) and not dominated(state, evolve)       # before attacking: fine
    apply(state, Attack(saga.uid, leader_uid(1)))
    legal = legal_actions(state)
    assert evolve in legal and Evolve(saga.uid, super_=True) in legal          # the rules allow it
    assert dominated(state, evolve) and dominated(state, Evolve(saga.uid, super_=True))
    assert evolve not in worth_trying(state, legal) and EndTurn() in worth_trying(state, legal)


def test_evolutions_that_do_something_stay():
    # Normagdala's evolution repeats its fanfare: the order can matter.
    state = start()
    unlock_evolution(state, 0)
    normagdala = put(state, 0, dragon.NORMAGDALA)
    apply(state, Attack(normagdala.uid, leader_uid(1)))
    evolves = [a for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == normagdala.uid]
    assert evolves and not any(dominated(state, a) for a in evolves)
    # An allied card that reacts to evolutions (Sathanid's faith) keeps them too.
    state, saga = _saga_ready()
    put(state, 0, forest.SATHANID_FAITH)
    apply(state, Attack(saga.uid, leader_uid(1)))
    assert not dominated(state, Evolve(saga.uid))


class Sure:
    """An evaluation sure the game is won: the hand-set score shrunk and pushed far
    up, where the squash is flat (like the learned Ramp model against the player)."""

    def score(self, state, player, player_moves_next=False):
        return 48 + evaluate(state, player, DEFAULT, player_moves_next) / 10


def _first_moves(search, state):
    s, out = state.clone(), []
    for _ in range(4):
        a = search.choose(s)
        if isinstance(a, EndTurn):
            break
        out.append(type(a).__name__)
        apply(s, a)
    return out, s.players[1].leader_hp


def test_a_search_sure_it_is_winning_still_evolves_before_attacking():
    state, saga = _saga_ready()
    for seed in range(3):
        # Even without leaving moves out, comparing with the starting position finds the order.
        moves, hp = _first_moves(ISMCTS(iterations=200, seed=seed, weights=Sure(), prune=False), state)
        assert moves[:2] == ["Evolve", "Attack"] and hp <= state.players[1].leader_hp - (saga.atk + 2)
        moves, _ = _first_moves(ISMCTS(iterations=200, seed=seed, weights=Sure()), state)
        assert moves[:2] == ["Evolve", "Attack"]


def test_the_greedy_agent_never_evolves_a_follower_that_already_attacked():
    state, saga = _saga_ready()
    agent = GreedyAgent(seed=1)
    apply(state, Attack(saga.uid, leader_uid(1)))
    assert not isinstance(agent.act(state, legal_actions(state)), Evolve)
