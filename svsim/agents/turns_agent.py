"""Cross-turn planning: what kind of turn to play now, judged by playing out the next turns.

The player's plan with Rhinoceroach Forest spans turns: draw hard for a few
turns while keeping the Rhinoceroaches, answer only what must be answered,
then deal 20 in one turn (or 15 and 5 over two). A search that looks at one
turn at a time can't see it (a night of one-turn fixes left the AI at 6-13%
against the Ramp bot). So each own turn is one of a few kinds (macros):

- KILL: the lethal line if there is one, otherwise the resource planner's
  most-damage line (this spends the finishers);
- DIG: the planner's most-drawing line with the finishers kept
  (search.combo.dig), then the rest of the turn as an ordinary turn;
- DEV: an ordinary turn (the base agent; in the play-outs, a quick greedy
  agent that keeps the finishers and waits for Combo);
- PASS: end the turn at once, keeping every card for a bigger turn later (the
  player's first two turns of a game: nothing played; their fourth: two
  Arrows and two Sprouting Initiates at once, so the second one draws).

At the start of each turn the agent tries each kind for this turn and plays
the next `horizon - 1` own turns the way the plan would (KILL once the
planner says the damage is there, DIG before that), the opponent's turns
played by an opponent model, on a few determinizations (hidden cards
reshuffled, so nothing is peeked). A play-out that kills scores 1, one that
dies 0; otherwise between them: half for how much of the opponent's defence
next turn's damage would cover (search.formula.next_turn), the rest for the
damage already dealt and the defence kept, less a quarter if the enemy board
could kill. The kind with the best average is this turn's.
"""
from __future__ import annotations

import random

from svsim.agents.greedy_agent import GreedyAgent, mulligan
from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Phase
from svsim.core.view import determinize
from svsim.search import combo
from svsim.search.moves import finisher, reserved, wasted_combo

KINDS = ("KILL", "DIG", "DEV", "PASS")


class _Keeper(GreedyAgent):
    """The quick ordinary turn of the play-outs: greedy, finishers kept, Combo cards waiting."""

    def act(self, state, actions):
        kept = [a for a in actions if not reserved(state, a) and not wasted_combo(state, a)]
        return super().act(state, kept or actions)


def _line(state, steps) -> list:
    """The longest start of an abstract plan the engine accepts, as real actions."""
    for n in range(len(steps), 0, -1):
        line = combo.realize(state, steps[:n])
        if line:
            return line
    return []


def kill_line(state, nodes: int = 3000) -> list:
    return _line(state, combo.plan(state, nodes).steps)


def dig_line(state, nodes: int = 2000) -> list:
    from svsim.search.combo import leave_discount
    keep = {c.defn.card_id for c in state.players[state.active].hand
            if finisher(c.defn) or leave_discount(c.defn)}
    p = combo.dig(state, keep, nodes)
    return _line(state, p.steps) if p.damage > 0 else []


def _play(s, line) -> None:
    for a in line:
        if s.over or a not in legal_actions(s):
            return
        apply(s, a)


def _finish_turn(s, me: int, agent, max_steps: int = 60) -> None:
    for _ in range(max_steps):
        if s.over or s.active != me:
            return
        a = agent.act(s, legal_actions(s))
        apply(s, a)
        if isinstance(a, EndTurn):
            return


class TurnsAgent:
    def __init__(self, base, opponent: str = "greedy+plan+learned", samples: int = 4, horizon: int = 2,
                 seed: int = 0):
        self.base = base                 # plays DEV turns and the rest of DIG turns (a LethalAgent)
        self.opponent = opponent
        self.samples = samples
        self.horizon = horizon
        self.rng = random.Random(seed)
        self.keeper = _Keeper(seed=seed, samples=1)
        self.turn = None
        self.kind = "DEV"
        self.line: list = []
        self.kinds = {k: 0 for k in KINDS}

    # --- the play-outs --------------------------------------------------------------------

    def _own_turn(self, s, me: int, kind: str) -> None:
        if kind == "PASS":
            apply(s, EndTurn())
            return
        if kind == "KILL":
            _play(s, kill_line(s))
        elif kind == "DIG":
            _play(s, dig_line(s))
        _finish_turn(s, me, self.keeper)

    def _score(self, s, me: int) -> float:
        from svsim.search.evaluate import threat
        from svsim.search.formula import next_turn
        if s.over:
            return 1.0 if s.winner == me else 0.0
        mine, theirs = s.players[me], s.players[1 - me]
        hp = max(theirs.leader_hp, 1)
        value = (0.5 * min(next_turn(s, me) / hp, 1.0)                  # how much of the kill is in hand
                 + 0.3 * (1.0 - theirs.leader_hp / max(theirs.leader_max_hp, 1))
                 + 0.2 * mine.leader_hp / max(mine.leader_max_hp, 1))
        if threat(s, 1 - me) >= mine.leader_hp:
            value -= 0.25
        return value

    def _playout(self, state, kind: str, seed: int) -> float:
        from svsim.tools.arena import make_agent
        me = state.active
        s = determinize(state, me, random.Random(seed))
        opponent = make_agent(self.opponent, seed % 100000)
        for k in range(self.horizon):
            if s.over:
                break
            if k == 0:
                self._own_turn(s, me, kind)
            else:
                lethal = combo.plan(s, 3000).damage >= s.players[1 - me].leader_hp
                self._own_turn(s, me, "KILL" if lethal else "DIG")
            if s.over or k == self.horizon - 1:
                break
            for _ in range(200):                  # the opponent's turn
                if s.over or s.active == me:
                    break
                apply(s, opponent.act(s, legal_actions(s)))
        return self._score(s, me)

    def choose(self, state) -> str:
        seeds = [self.rng.getrandbits(48) for _ in range(self.samples)]
        values = {k: sum(self._playout(state, k, sd) for sd in seeds) / len(seeds) for k in KINDS}
        self.values = values
        return max(KINDS, key=lambda k: (values[k], -KINDS.index(k) if k != "DEV" else 1))

    # --- playing ----------------------------------------------------------------------------

    def act(self, state, actions):
        if state.phase != Phase.MAIN:
            return mulligan(state)
        if len(actions) == 1:
            return actions[0]
        if state.turn != self.turn:
            self.turn = state.turn
            self.kind = self.choose(state)
            self.kinds[self.kind] += 1
            self.line = kill_line(state) if self.kind == "KILL" else dig_line(state) if self.kind == "DIG" else []
        if self.kind == "PASS":
            return EndTurn()
        if self.line:
            a = self.line.pop(0)
            if a in actions:
                return a
            self.line = []
        return self.base.act(state, actions)
