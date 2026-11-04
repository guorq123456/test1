"""Whole-turn planning: the best way to play the rest of this turn.

Inside one's own turn there is no opponent, so a move is worth the best
position its line can reach by the end of the turn. The planner searches the
turn depth-first, takes the maximum over its own choices and scores each end of
turn with the evaluation, as a win probability (wins 1, losses 0).

Luck and hidden cards: an action whose result used the random number generator
or took cards from a deck is a chance node. It is re-run on a few copies with
fresh random numbers and reshuffled decks, and is worth the average of the best
each copy can go on to (the planner neither knows what it will draw nor counts
on the luckiest draw; averaging probabilities, not scores, keeps a rare random
lethal from outweighing everything else). The evaluation reads only public
information, so planning on the real position doesn't peek.

Speed: positions reached by different orders of the same actions share a
transposition table entry (search.lethal.state_key), dominated moves are left
out (search.moves), and after `max_nodes` positions the rest are scored as if
the turn ended there. `TurnPlanAgent` follows its plan until a chance action,
then plans again.

Only this turn counts. What the end-of-turn evaluation doesn't see (what using
resources now costs on later turns, what the opponent can answer) the planner
can't weigh, and since it optimises harder than ISMCTS, it leans on the
evaluation's blind spots harder too.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
import time

from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import DRAW, Phase
from svsim.core.state import GameState
from svsim.search.evaluate import DEFAULT, evaluate
from svsim.search.lethal import hidden_info, state_key
from svsim.search.mcts import _rank
from svsim.search.moves import worth_trying

EPS = 1e-12


@dataclass
class TurnPlan:
    value: float      # win probability at the end of the turn, playing the plan
    line: list        # the plan, up to and including its first chance action
    complete: bool    # searched within the budget
    nodes: int
    seconds: float


class TurnPlanner:
    def __init__(self, max_nodes: int = 5000, samples: int = 4, max_depth: int = 40, seed: int = 0,
                 weights=DEFAULT, scale: float = 8.0):
        self.max_nodes = max_nodes
        self.samples = samples        # copies at a chance node (halved at each nested one, at least 2)
        self.max_depth = max_depth
        self.weights = weights
        self.scale = scale            # evaluation points per unit of the logistic squash
        self.rng = random.Random(seed)

    def plan(self, state: GameState) -> TurnPlan:
        if state.phase != Phase.MAIN or state.winner is not None:
            raise ValueError("turn planning needs a game in its main phase")
        start = time.perf_counter()
        self.me = state.active
        self.tt: dict = {}
        self.nodes = 0
        self.exhausted = False
        value, line = self._search(state.clone(), 0, 0)
        return TurnPlan(value, line, not self.exhausted, self.nodes, time.perf_counter() - start)

    # --- values ---------------------------------------------------------------------

    def _value(self, state: GameState) -> float:
        if state.winner is not None:
            return 1.0 if state.winner == self.me else 0.0 if state.winner == 1 - self.me else 0.5
        score = evaluate(state, self.me, self.weights)
        return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, score / self.scale))))

    def _after_end(self, sample: GameState) -> float:
        """Value once `sample`'s player ends the turn (end-of-turn abilities resolve,
        the opponent's turn doesn't start)."""
        real_limit = sample.max_turns
        sample.max_turns = sample.turn
        apply(sample, EndTurn())
        if sample.winner == DRAW and sample.turn <= real_limit:
            sample.winner, sample.phase = None, Phase.MAIN
        return self._value(sample)

    # --- the search -----------------------------------------------------------------

    def _search(self, state: GameState, depth: int, chance_depth: int) -> tuple:
        """(value, line) of the best way to finish the turn from `state`."""
        if state.winner is not None:
            return self._value(state), []
        key = state_key(state)
        hit = self.tt.get(key)
        if hit is not None:
            return hit
        if self.nodes >= self.max_nodes or depth >= self.max_depth:
            self.exhausted = True
            return self._after_end(state.clone()), [EndTurn()]
        self.nodes += 1
        best = (-1.0, [])
        actions = sorted(worth_trying(state, legal_actions(state)), key=lambda a: _rank(state, a))
        for action in actions:
            value, line = self._evaluate(state, action, depth, chance_depth)
            if value > best[0] + EPS:
                best = (value, [action] + line)
        self.tt[key] = best
        return best

    def _evaluate(self, state: GameState, action, depth: int, chance_depth: int) -> tuple:
        if isinstance(action, EndTurn):
            probe = state.clone()
            before = hidden_info(probe)
            value = self._after_end(probe)
            if hidden_info(probe) == before:
                return value, []
            return self._chance(state, self._after_end, chance_depth), []
        child = state.clone()
        before = hidden_info(child)
        apply(child, action)
        if hidden_info(child) == before:
            return self._search(child, depth + 1, chance_depth)

        def run(sample):
            apply(sample, action)
            return self._search(sample, depth + 1, chance_depth + 1)[0]
        return self._chance(state, run, chance_depth), []

    def _chance(self, state: GameState, run, chance_depth: int) -> float:
        """Average of `run` over fresh outcomes: new random numbers, reshuffled decks
        (sorted first, so the hidden order can't leak into the result)."""
        k = max(2, self.samples >> chance_depth)
        total = 0.0
        for _ in range(k):
            sample = state.clone()
            sample.rng.seed(self.rng.getrandbits(64))
            for p in sample.players:
                p.deck.sort(key=lambda c: c.defn.card_id)
                sample.rng.shuffle(p.deck)
            total += run(sample)
        return total / k


class TurnPlanAgent:
    """Plays the planner's line; plans again at the start of a turn, after a chance
    action, or when the position isn't the one the plan expected."""

    def __init__(self, max_nodes: int = 5000, samples: int = 4, seed: int = 0, weights=DEFAULT):
        self.planner = TurnPlanner(max_nodes=max_nodes, samples=samples, seed=seed, weights=weights)
        self.line: list = []
        self.expect = None
        self.plans = self.incomplete = self.nodes = 0
        self.seconds = 0.0

    def act(self, state, actions):
        from svsim.agents.greedy_agent import mulligan
        if state.phase != Phase.MAIN:
            return mulligan(state)
        if len(actions) == 1:
            self.line = []
            return actions[0]
        if not (self.line and self.expect == state_key(state) and self.line[0] in actions):
            result = self.planner.plan(state)
            self.plans += 1
            self.incomplete += not result.complete
            self.nodes += result.nodes
            self.seconds += result.seconds
            self.line = list(result.line)
        action = self.line.pop(0) if self.line and self.line[0] in actions else EndTurn()
        self.expect = None
        if self.line and not isinstance(action, EndTurn):
            s = state.clone()
            before = hidden_info(s)
            apply(s, action)
            if hidden_info(s) == before:
                self.expect = state_key(s)
            else:
                self.line = []
        return action
