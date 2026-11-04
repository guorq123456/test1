"""The leaf contract (search.mcts.search_child, leaf_score, leaf_phase): code outside the search that rebuilds and
scores a decision's children must get exactly the leaves ISMCTS scores (the bot check-up with Codex, 2026-10-31).

Checked against real searches: every depth-1 leaf the search scored (a root move's child, on that iteration's
determinization) is rebuilt from the position the search started the iteration from, and must agree in the
learn.features row (version 2), the score the search used, its phase and its result; and the search scores no
leaf with player_moves_next=True. Separately: the turn limit and the game's end."""
import random

import numpy as np

from svsim.cards import decks
from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import DRAW
from svsim.learn import features as F
from svsim.search import mcts as M
from svsim.search.evaluate import after_end_of_turn, evaluate
from svsim.tools.arena import make_agent
from svsim.tools.gate import _search
from svsim.ui.session import DECKS


def _games():
    names = sorted(DECKS)
    rng = random.Random(7)
    for g in range(3):
        a, b = rng.sample(names, 2)
        yield decks.build(DECKS[a][1]), decks.build(DECKS[b][1]), 500 + g


def _recorded_leaves(state, agent, search):
    """Play the agent's decision at `state`, recording each depth-1 leaf the search scored:
    (determinized start, the move, the leaf, me, me_next, the raw score it used)."""
    rec, cur = [], {"start": None, "acts": []}
    orig_iterate, orig_score = search._iterate, search._score

    def step(s, action):
        cur["acts"].append(action)
        M.ISMCTS._step(s, action)

    def iterate(s, me, root):
        cur["start"], cur["acts"] = s.clone(), []
        return orig_iterate(s, me, root)

    def score(s, me, me_next):
        v = orig_score(s, me, me_next)
        if len(cur["acts"]) == 1:
            rec.append((cur["start"], cur["acts"][0], s.clone(), me, me_next, v))
        return v

    search._step, search._iterate, search._score = step, iterate, score
    try:
        action = agent.act(state, legal_actions(state))
    finally:
        del search._step, search._iterate, search._score
    return action, rec


def test_rebuilt_children_are_the_leaves_the_search_scores():
    seen = {"in_turn": 0, "turn_end": 0, "over": 0}
    for d0, d1, seed in _games():
        state = new_game(d0, d1, seed=seed)
        agents = [make_agent("mcts:30+plan", 2 * seed + k) for k in (0, 1)]
        searches = [_search(a) for a in agents]
        decisions = 0
        while not state.over and decisions < 40:
            side = state.active
            if searches[side] is None or state.phase != 1:
                apply(state, agents[side].act(state, legal_actions(state)))
                continue
            action, rec = _recorded_leaves(state, agents[side], searches[side])
            decisions += 1
            for start, move, leaf, me, me_next, used in rec:
                assert me_next is False                      # no leaf is scored as "the player moves next"
                child = M.search_child(start, move)
                assert np.array_equal(F.features(child, me, potential=False, version=2),
                                      F.features(leaf, me, potential=False, version=2))
                assert M.leaf_score(child, me, searches[side].weights) == used
                assert M.leaf_phase(child, me) == M.leaf_phase(leaf, me)
                assert (child.over, child.winner) == (leaf.over, leaf.winner)
                seen[M.leaf_phase(child, me)] += 1
                if isinstance(move, EndTurn):                # the analysis' older rebuild of an end of turn
                    ended = after_end_of_turn(start)
                    assert np.array_equal(F.features(ended, me, potential=False, version=2),
                                          F.features(child, me, potential=False, version=2))
            apply(state, action)
    assert seen["in_turn"] > 0 and seen["turn_end"] > 0


def test_a_score_inside_the_turn_is_not_the_players_turn_start():
    """The slip the contract exists for: player_moves_next=True gives other scores inside the turn."""
    d0, d1, seed = next(_games())
    state = new_game(d0, d1, seed=seed)
    agents = [make_agent("mcts:30+plan", k) for k in (0, 1)]
    differ = 0
    for _ in range(60):
        if state.over:
            break
        if state.phase == 1:
            me = state.active
            for a in legal_actions(state):
                if not isinstance(a, EndTurn):
                    c = M.search_child(state, a)
                    if not c.over and c.active == me:
                        differ += M.leaf_score(c, me) != evaluate(c, me, player_moves_next=True)
        apply(state, agents[state.active].act(state, legal_actions(state)))
    assert differ > 0


def test_the_last_turns_end_is_a_draw_and_the_one_before_is_not():
    d0, d1, seed = next(_games())
    for limit in (3, 4, 5):
        state = new_game(d0, d1, seed=seed, max_turns=limit)
        agents = [make_agent("greedy", k) for k in (0, 1)]
        ends = []
        while not state.over:
            if state.phase == 1:
                me = state.active
                child = M.search_child(state, EndTurn())
                ended = after_end_of_turn(state)
                assert (child.over, child.winner) == (ended.over, ended.winner)
                assert np.array_equal(F.features(child, me, potential=False, version=2),
                                      F.features(ended, me, potential=False, version=2))
                real = state.clone()
                apply(real, EndTurn())
                ends.append((child.over, real.over and real.winner == DRAW))
            apply(state, agents[state.active].act(state, legal_actions(state)))
        if state.winner == DRAW:
            # the search sees the game end at the limit exactly where the real game ends in a draw
            assert ends[-1] == (True, True)
            assert all(c == r for c, r in ends)


def test_a_winning_move_is_a_finished_leaf():
    found = 0
    for d0, d1, seed in _games():
        state = new_game(d0, d1, seed=seed)
        agents = [make_agent("greedy", k) for k in (0, 1)]
        while not state.over:
            if state.phase == 1:
                me = state.active
                for a in legal_actions(state):
                    c = M.search_child(state, a)
                    if c.over:
                        found += 1
                        real = state.clone()
                        apply(real, a)
                        assert real.over and real.winner == c.winner
                        assert M.leaf_phase(c, me) == "over"
            apply(state, agents[state.active].act(state, legal_actions(state)))
    assert found > 0
