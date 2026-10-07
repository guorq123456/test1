"""Choose the turn by its impact on winning (search.impact), not by the end-of-turn score.

At the start of a turn (and whenever the chosen line can't be followed, after
a draw changed the hand), the agent lays out a few ways of playing the rest of
the turn: the base agent's, the base agent's after each of its next-best first
moves, and ending the turn at once. The lines are played on a determinized
copy (the hidden cards reshuffled, so drawing doesn't peek). Each line's end is
then assessed against the same sampled futures: the opponent's answer played
by an opponent model, then both race clocks and the evaluation. The line with
the best race share wins (ties: the evaluation), and the agent follows it.

The point (the player's): the end-of-turn evaluation can't see what a turn
does to the race; a line that leaves fewer points on the board but brings the
lethal turn closer should win.
"""
from __future__ import annotations

import random

from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Phase
from svsim.core.view import determinize
from svsim.search import impact
from svsim.search.mcts import _locator, action_key


def score(i: impact.Impact) -> float:
    """Race share first, the evaluation as a tie-breaker, minus the chance of being killed."""
    return i["race"] + 0.25 * i["value"] - i["killed"]


class ImpactAgent:
    def __init__(self, base, alternatives: int = 2, samples: int = 4, opponent: str = "greedy+plan+learned",
                 seed: int = 0, max_steps: int = 60):
        self.base = base                     # plays the lines (an agent with an ISMCTS `search`)
        self.alternatives = alternatives     # next-best first moves tried besides the base agent's
        self.samples = samples
        self.opponent = opponent
        self.max_steps = max_steps
        self.rng = random.Random(seed)
        self.line: list = []
        self.choices = self.switched = 0     # turns weighed; times a line other than the base agent's won

    def _search(self):
        return getattr(getattr(self.base, "base", self.base), "search", None)

    def _first_moves(self, state) -> list:
        """The base agent's move, then its next most visited root moves."""
        first = self.base.act(state, legal_actions(state))
        moves = [first]
        search = self._search()
        root = getattr(search, "last_root", None)
        if root is not None and self.alternatives:
            where = _locator(state, state.active)
            legal = {action_key(state, a, where): a for a in legal_actions(state)}
            ranked = sorted((k for k in root.children if k in legal), key=lambda k: -root.children[k].visits)
            for k in ranked:
                if len(moves) > self.alternatives:
                    break
                if legal[k] not in moves and not isinstance(legal[k], EndTurn):
                    moves.append(legal[k])
        return moves

    def _line(self, state, first) -> tuple:
        """(actions, position before ending the turn) playing `first`, then the base agent."""
        s, line, me = determinize(state, state.active, self.rng), [], state.active
        action = first
        for _ in range(self.max_steps):
            if isinstance(action, EndTurn):
                break
            line.append(action)
            apply(s, action)
            if s.over or s.active != me:
                return line, s
            action = self.base.act(s, legal_actions(s))
        return line + [EndTurn()], s

    def _choose(self, state) -> list:
        lines, ends = [], []
        for first in self._first_moves(state):
            line, end = self._line(state, first)
            if end.over and end.winner == state.active:
                return line                  # a line that wins on the spot
            if not end.over:
                lines.append(line)
                ends.append(end)
        lines.append([EndTurn()])            # end the turn now
        ends.append(state)
        self.choices += 1
        out = impact.assess(state, ends, samples=self.samples, seed=self.rng.getrandbits(32),
                            opponent=self.opponent)
        best = max(range(len(out)), key=lambda i: score(out[i]))
        self.switched += best != 0
        return lines[best]

    def act(self, state, actions):
        from svsim.agents.greedy_agent import mulligan
        if state.phase != Phase.MAIN:
            return mulligan(state)
        if len(actions) == 1:
            self.line = []
            return actions[0]
        if not (self.line and self.line[0] in actions):
            self.line = self._choose(state)       # a new turn, or the line no longer fits
        if self.line and self.line[0] in actions:
            return self.line.pop(0)
        self.line = []
        return self.base.act(state, actions)
