"""One-ply greedy agent: takes the action whose result evaluates best, and ends
the turn when nothing beats ending it now.

Actions whose result depends on luck or hidden cards are scored on a few
determinized samples (fresh random seed, reshuffled unknown cards) rather than
the simulator's own outcome, so the agent doesn't peek.
"""
import random

from svsim.core.actions import EndTurn, Mulligan
from svsim.core.engine import apply
from svsim.core.enums import Phase
from svsim.core.view import determinize
from svsim.search.evaluate import DEFAULT, after_end_of_turn, evaluate
from svsim.search.lethal import hidden_info
from svsim.search.moves import worth_trying


def mulligan(state, threshold: int = 5) -> Mulligan:
    """The opening redraw (agents.mulligan: the player's rules for decks they
    know, ramp first for ramp decks, else cards costing `threshold` or more; a deck
    in agents.mulligan.BY_DECK redraws its own way, agents.mulligan.opening_redraw)."""
    from svsim.agents.mulligan import mulligan as choose, opening_redraw
    return opening_redraw(state) if threshold == 5 else choose(state, threshold)


class GreedyAgent:
    def __init__(self, seed: int = 0, samples: int = 3, weights=DEFAULT):
        self.rng = random.Random(seed)
        self.samples = samples
        self.weights = weights

    def score(self, state, action) -> float:
        me = state.active
        if isinstance(action, EndTurn):
            return evaluate(after_end_of_turn(state), me, self.weights)
        s = state.clone()
        before = hidden_info(s)
        apply(s, action)
        if hidden_info(s) == before:
            return evaluate(s, me, self.weights)
        total = 0.0
        for _ in range(self.samples):
            sample = determinize(state, me, self.rng)
            apply(sample, action)
            total += evaluate(sample, me, self.weights)
        return total / self.samples

    def act(self, state, actions):
        if state.phase != Phase.MAIN:
            return mulligan(state)
        best, best_score = None, None
        for action in worth_trying(state, actions):
            score = self.score(state, action)
            if best_score is None or score > best_score + 1e-9 or (
                    isinstance(action, EndTurn) and score >= best_score - 1e-9):
                best, best_score = action, score
        return best
