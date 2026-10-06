"""Moves the search leaves out, and searching relative to the starting position.

The player caught the AI attacking with Sagatsumatsu (Storm) for 5 and evolving
it afterwards, losing 2 damage, twice in one game."""
from svsim.agents.greedy_agent import GreedyAgent
from svsim.cards import dragon, forest
from svsim.core.actions import Attack, EndTurn, Evolve
from svsim.core.engine import apply, legal_actions
from svsim.core.state import leader_uid
from svsim.search.evaluate import DEFAULT, evaluate
from svsim.search.mcts import ISMCTS, action_key
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


def test_a_move_is_worth_the_best_line_after_it_not_the_average():
    state, saga = _saga_ready()
    best_line = state.clone()                            # evolve, attack, end the turn
    apply(best_line, Evolve(saga.uid))
    apply(best_line, Attack(saga.uid, leader_uid(1)))
    estimates = {}
    for backup in ("max", "mean"):
        search = ISMCTS(iterations=300, seed=1, backup=backup, prune=False)
        search.choose(state)
        key = action_key(state, Evolve(saga.uid))
        child = search.last_root.children[key]
        ISMCTS._step(best_line_end := best_line.clone(), EndTurn())
        estimates[backup] = (search.estimate(child), search.value(best_line_end, 0))
    q, best = estimates["max"]
    assert abs(q - best) < 1e-9                          # the best line below it, exactly
    q_mean, _ = estimates["mean"]
    assert q_mean < best - 1e-6                          # the average is dragged down by worse lines


def test_the_win_condition_is_kept_for_finishing_turns():
    # The player: Rhinoceroach is the deck's only way to win; the AI kept trading it with
    # followers and playing it early, and had nothing left to finish with.
    from svsim.cards import demo, unlimited
    from svsim.core.actions import PlayCard
    from svsim.search.moves import finisher, reserved
    from helpers import give
    assert finisher(unlimited.KILLER_RHINOCEROACH) and not finisher(dragon.SAGATSUMATSU)
    state = start()
    rhino = give(state, 0, unlimited.KILLER_RHINOCEROACH)
    raider = give(state, 0, demo.RAIDER)
    state.players[0].pp = state.players[0].max_pp = 10
    assert reserved(state, PlayCard(rhino.uid)) and not reserved(state, PlayCard(raider.uid))
    on_board = put(state, 0, unlimited.KILLER_RHINOCEROACH)
    foe = put(state, 1, demo.FOOTMAN)
    assert reserved(state, Attack(on_board.uid, foe.uid)) and not reserved(state, Attack(on_board.uid, leader_uid(1)))
    search = ISMCTS(iterations=50, seed=0, reserve=True)
    assert not reserved(state, search.choose(state))             # never offered to the search


def test_a_combo_card_waits_for_its_combo():
    # Sprouting Initiate draws at Combo 3: the player drew with it 23 times in 22 plays.
    from svsim.cards import demo
    from svsim.core.actions import PlayCard
    from svsim.search.moves import wasted_combo
    from helpers import give
    state = start()
    sprout = give(state, 0, forest.SPROUTING_INITIATE)
    footman = give(state, 0, demo.FOOTMAN)
    assert wasted_combo(state, PlayCard(sprout.uid)) and not wasted_combo(state, PlayCard(footman.uid))
    state.players[0].combo = 2
    assert not wasted_combo(state, PlayCard(sprout.uid))
