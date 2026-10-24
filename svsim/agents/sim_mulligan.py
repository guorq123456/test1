"""The opening redraw worked out by play: try every redraw, keep the one whose short games go best.

The player (2026-10-07): which cheap cards to keep "都不能下定论，要看一部分情况"; the architecture
session: let the bot work it out. For each subset of the hand to send back (16 for 4 cards),
`simulated` plays N short games from the redraw, H turns for each side, both sides the cheap level
(the one-ply greedy agent on the learned evaluation, one deal per move and no lethal search: about
60 ms a play-out, 16 x 8 of them about 7 s a hand), and scores where each ends with the learned evaluation of the
deck (the turn models, learn.phased, else learn.model); the best mean wins. The same N worlds
(the own deck's order, the opponent's hand and deck dealt from their real 40, the random numbers:
core.view.determinize) serve every subset, so the subsets differ by the redraw, not by luck.
The opponent's 40-card list is known, as in every result here (tools.gate's condition).
"""
from __future__ import annotations

import random
from itertools import combinations

N, H = 8, 5                      # play-outs per redraw, turns per side in each


def simulated(state, n: int = N, horizon: int = H, seed: int = 0) -> tuple:
    """The hand positions to redraw for the player to act in `state` (at their mulligan)."""
    from svsim.agents.greedy_agent import GreedyAgent
    from svsim.core.actions import Mulligan
    from svsim.core.engine import apply
    from svsim.core.view import determinize
    from svsim.learn.model import Learned
    from svsim.learn.phased import PhasedLearned
    from svsim.search.evaluate import DEFAULT, evaluate
    me = state.active
    size = len(state.players[me].hand)
    subsets = [c for k in range(size + 1) for c in combinations(range(size), k)]
    rng = random.Random(seed * 7919 + state.turn)
    worlds = [rng.getrandbits(64) for _ in range(n)]
    weights = PhasedLearned(fallback=Learned())
    play = Learned(fallback=DEFAULT)
    best, best_score = (), None
    for redraw in subsets:
        total = 0.0
        for w in worlds:
            world = random.Random(w)
            s = determinize(state, me, world)
            apply(s, Mulligan(redraw))
            agents = [GreedyAgent(w % 100003 + i, samples=1, weights=play) for i in (0, 1)]
            while not s.over and s.turn <= 2 * horizon:
                apply(s, agents[s.active].act(s, _legal(s)))
            total += evaluate(s, me, weights, player_moves_next=(s.active == me))
        if best_score is None or total > best_score:
            best, best_score = redraw, total
    return best


def _legal(state):
    from svsim.core.engine import legal_actions
    return legal_actions(state)
