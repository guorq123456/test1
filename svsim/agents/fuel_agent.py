"""Choosing each turn's line by the fuel it leaves (the player's turns as the yardstick).

Scoring the player's ten games against Ramp Dragon turn by turn (their line
against the AI's from the same start, 2026-10-06): the evaluation the search
uses preferred the AI's line 47 times to 13, the race clocks mostly couldn't
tell them apart (integer turns), and "fuel" picked the player's line 39 times
to 16: after the opponent's reply (sampled on reshuffled hands), play two more
own turns digging the way search.race does (the resource planner's most-drawing
line, followers answered at the matchup's learned rate) and take the most
damage one turn could then deal (search.race.burst, uncapped). It sees what
the player builds towards: cards seen, a full hand, Bayle's cost going down,
0-cost cards banked, the last super-evolution point kept.

`FuelAgent` plays the line with the most fuel among a few candidates, every
turn anew (the plan is re-made from what the opponent did and what was
drawn):

- the base agent's own turn (a LethalAgent: a lethal it finds ends the game,
  which scores above everything);
- digging first (search.combo.dig, finishers and Bayle kept), then an ordinary
  turn by a quick greedy agent that keeps the finishers;
- the planner's most-damage line (a burst, for two-turn kills);
- passing at once.

A line the reply kills the player on scores below everything.
"""
from __future__ import annotations

import random

from svsim.agents.greedy_agent import mulligan
from svsim.agents.turns_agent import _Keeper, dig_line, kill_line
from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Phase

WON, LOST = 1000.0, -1000.0


def fuel(state, me: int, turns: int = 2, nodes: int = 600, seed: int = 0) -> float:
    """From the start of `me`'s turn: the most damage one turn could deal after `turns`
    more own turns spent digging (followers answered at the matchup's learned rate)."""
    from svsim.learn.survival import Removal
    from svsim.search import race
    t = state.clone()
    removal = Removal.matchup(t, me, seed=seed)
    for _ in range(turns):
        if t.over:
            break
        race.develop(t, me, ramp=False, digging=True)
        if t.over:
            break
        race.advance(t, me, removal)
    if t.over:
        return WON if t.winner == me else LOST
    t.players[1 - me].leader_hp = 99
    return float(race.burst(t, nodes))


class FuelAgent:
    def __init__(self, base, opponent: str = "greedy+plan+learned", samples: int = 3, turns: int = 2,
                 seed: int = 0):
        self.base = base
        self.opponent = opponent
        self.samples = samples
        self.turns = turns
        self.rng = random.Random(seed)
        self.keeper = _Keeper(seed=seed, samples=1)
        self.turn = None
        self.line: list = []
        self.following = False
        self.picked = {}

    # --- candidates ---------------------------------------------------------------------------

    def _record(self, state, first: list, agent) -> tuple[list, object]:
        """Play `first` (a start of a line), then `agent` to the end of the turn, on a copy:
        (the actions, the position before ending the turn)."""
        s, me, out = state.clone(), state.active, []
        for a in first:
            if s.over or a not in legal_actions(s):
                break
            apply(s, a)
            out.append(a)
        for _ in range(80):
            if s.over or s.active != me:
                break
            a = agent.act(s, legal_actions(s))
            if isinstance(a, EndTurn):
                break
            apply(s, a)
            out.append(a)
        return out, s

    def candidates(self, state) -> dict:
        lines = {"base": self._record(state, [], self.base)}
        dig = dig_line(state)
        if dig:
            lines["dig"] = self._record(state, dig, self.keeper)
        burst = kill_line(state)
        if burst:
            lines["burst"] = self._record(state, burst, self.keeper)
        lines["pass"] = ([], state.clone())
        return lines

    # --- scoring ------------------------------------------------------------------------------

    def score(self, end, me: int, seeds: list) -> float:
        from svsim.core.view import determinize
        from svsim.search.impact import _canonical, reply
        from svsim.tools.arena import make_agent
        if end.over:
            return WON if end.winner == me else LOST
        base, total = _canonical(end, me), 0.0
        for sd in seeds:
            s = determinize(base, me, random.Random(sd))
            s, _ = reply(s, me, make_agent(self.opponent, sd % 100000))
            if s.over:
                total += WON if s.winner == me else LOST
                continue
            total += fuel(s, me, self.turns, seed=sd)
        return total / len(seeds)

    def choose(self, state) -> list:
        seeds = [self.rng.getrandbits(48) for _ in range(self.samples)]
        lines = self.candidates(state)
        scored = {name: self.score(end, state.active, seeds) for name, (_, end) in lines.items()}
        self.scores = scored
        best = max(scored, key=lambda k: (scored[k], k == "base"))
        self.picked[best] = self.picked.get(best, 0) + 1
        return list(lines[best][0])

    # --- playing ------------------------------------------------------------------------------

    def act(self, state, actions):
        if state.phase != Phase.MAIN:
            return mulligan(state)
        if state.turn != self.turn:
            self.turn = state.turn
            self.line = self.choose(state)
            self.following = True
        if self.following:
            if not self.line:                    # the chosen line is played out: end the turn there
                self.following = False
                return EndTurn()
            a = self.line.pop(0)
            if a in actions:
                return a
            self.following = False               # the turn went differently (random effects): play on normally
        return self.base.act(state, actions)
