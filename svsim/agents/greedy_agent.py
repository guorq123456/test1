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
    """Redraw the opening-hand cards that cost `threshold` or more. A deck built
    around ramp (at least one card in eight raises max play points, search.race.ramps)
    keeps the ramp and redraws everything else, all of it if there is none: the
    player's way with Ramp Dragon against Rhinoceroach Forest ("留牌围着跳费走，
    很多时候全换找跳费"; ramping 3 into 5 and 5 into 7 is what lines up the damage turns)."""
    from svsim.search.race import ramps
    p = state.players[state.active]
    cards = p.hand + p.deck
    if 8 * sum(ramps(c.defn) for c in cards) >= len(cards):
        return Mulligan(tuple(i for i, c in enumerate(p.hand) if not ramps(c.defn)))
    return Mulligan(tuple(i for i, c in enumerate(p.hand) if c.cost >= threshold))


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
