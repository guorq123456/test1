"""Pick the whole turn, not the step: at the first decision of each own turn, make several deliberately different
whole-turn plans (search.candidates), score each by its turn end with the evaluator's own turn-end (ENDED) model on
shared determinizations, and play the best one only when it beats the bot's own plan clearly.

The architecture thread 2026-10-09 23:00Z, on the analysis line's diagnosis 7b8bd0c: on step 1's 2000 turn starts,
picking among the generator's plans by the installed ENDED model's mean turn-end win probability (picked on one seed,
measured on the other) roughly halves the regret T measures (about 1.9-2.0 points to 1.0), mostly by "race" and
"second": the search doesn't reach those turns, but the evaluator ranks them above its own.

At the first decision of an own turn (more than one legal action):
1. plans: search.candidates.generate on a determinization of the position (the hidden cards guessed, so no plan sees
   them), kinds "bot", "second", "third", "race" by default and the resource restrictions on request, deduped by
   turn end; the plans' own searches with `iterations` (fewer than the base search's, to save time);
2. each plan's actions as action keys (search.mcts.action_key) replayed on `samples` new determinizations, the same
   ones for every plan (paired); where a key no longer matches (a draw or a random effect came out otherwise), the
   plan's own policy finishes the turn (the continuation search, under the plan's restriction; "end": end the turn);
   V = the mean of sigma(ENDED(turn end)), a game won during the turn 1, lost 0;
3. the best plan replaces the bot's only if V(best) - V(bot) > margin and > z x the paired difference's standard
   error (the B line's rule against the winner's curse); otherwise this turn is the base agent's, step for step;
4. a picked plan is followed key by key on the real position; when a key doesn't match, the base search plays the
   rest of the turn (a restriction kind keeps its veto on the base search for the whole turn, so the lethal search
   outside obeys it too: LethalAgent._veto).

The base agent's own calls are the same as without this wrapper on a turn that isn't switched (the plans use their
own agents and random numbers), so with an unreachable margin it plays as the base agent does.
"""
from __future__ import annotations

import math
import random
import time

from svsim.core.actions import EndTurn
from svsim.core.engine import apply
from svsim.core.enums import Phase
from svsim.core.view import determinize
from svsim.search.mcts import _locator, action_key

KINDS = ("bot", "second", "third", "race")
RESOURCE = ("keep", "save", "noevo")


def keys_of(state, actions: list) -> list:
    """A plan's actions (played from `state`) as action keys, the ending EndTurn as ("T",)."""
    s, out = state.clone(), []
    for a in actions:
        out.append(action_key(s, a, _locator(s, s.active)))
        if isinstance(a, EndTurn) or s.over:
            break
        apply(s, a)
    return out


def match(state, key, legal: list):
    """The legal action with this key, or None."""
    if tuple(key) == ("T",):
        return next((a for a in legal if isinstance(a, EndTurn)), None)
    where = _locator(state, state.active)
    return next((a for a in legal if action_key(state, a, where) == tuple(key)), None)


def turn_value(end, me: int, weights) -> float:
    """sigma(ENDED) of a turn end; a finished game its result."""
    from svsim.learn.model import SCALE
    from svsim.search.evaluate import evaluate
    if end.over:
        return 1.0 if end.winner == me else 0.0 if end.winner == 1 - me else 0.5
    z = evaluate(end, me, weights)
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z / SCALE))))


def paired_better(values: list, base: list, margin: float, z: float) -> bool:
    """Whether `values` beat `base` (paired by determinization) by more than margin and z standard errors."""
    diffs = [a - b for a, b in zip(values, base)]
    n = len(diffs)
    mean = sum(diffs) / n
    se = math.sqrt(sum((d - mean) ** 2 for d in diffs) / max(n - 1, 1) / n) if n > 1 else 0.0
    return mean > margin and mean > z * se


class TurnPickAgent:
    """`base`: an MCTSAgent (the lethal search stays outside, as with CrossTurnAgent). `plan_spec`: the agent spec
    the plans' own searches use (make_agent; the base's evaluator with `iterations` fewer iterations, say)."""

    def __init__(self, base, plan_spec: str, samples: int = 8, margin: float = 0.0, z: float = 1.0,
                 kinds=KINDS, seed: int = 0, race_nodes: int = 300, race_clock_nodes: int = 200,
                 max_keeps: int = 1):
        self.base = base
        self.search = base.search
        self.plan_spec = plan_spec
        self.samples, self.margin, self.z = samples, margin, z
        self.kinds = tuple(kinds)
        self.race_nodes, self.race_clock_nodes, self.max_keeps = race_nodes, race_clock_nodes, max_keeps
        self.rng = random.Random(seed)
        self._own_veto = self.search.veto
        self.turn = None
        self.following: list = []            # the picked plan's keys still to play this turn
        self.picked: dict = {}               # kind -> turns (statistics; "bot" also when none beat it)
        self.turns = 0
        self.seconds = 0.0                   # time spent choosing plans (statistics)
        self.last_pick: dict | None = None   # the last turn start's measurements

    # --- the plans --------------------------------------------------------------------------------------------
    def _decider(self, kind: str, seed: int):
        """A plan's own policy for the rest of a turn when its keys stop matching."""
        if kind == "end":
            return lambda s, legal: next((a for a in legal if isinstance(a, EndTurn)), legal[0])
        from svsim.agents.crossturn_agent import forbids
        from svsim.search.candidates import _agent_decider
        return _agent_decider(self.plan_spec, seed, forbids(kind) if kind.split(":")[0] in RESOURCE else None)

    def plans(self, state) -> list:
        """search.candidates.generate on a determinization of `state`: [(kind, keys)], the bot's first."""
        from svsim.search.candidates import generate
        me = state.active
        seed = self.rng.randrange(2 ** 31)
        guess = determinize(state, me, random.Random(seed))
        kinds = tuple(k for k in self.kinds if k not in RESOURCE) + (("resource",) if set(RESOURCE) & set(self.kinds)
                                                                    else ())
        cands = generate(guess, spec=self.plan_spec, seed=seed, max_keeps=self.max_keeps,
                         race_nodes=self.race_nodes, race_clock_nodes=self.race_clock_nodes, kinds=kinds)
        out = []
        for c in cands:
            kind = c.kind
            if kind.split(":")[0] in RESOURCE and kind.split(":")[0] not in self.kinds:
                continue
            out.append((kind, keys_of(guess, c.actions)))
        out.sort(key=lambda kv: kv[0] != "bot")
        return out

    def values(self, state, plans: list) -> dict:
        """{kind: [V on each determinization]}, the same determinizations for every plan."""
        from svsim.learn.contrast import replay_turn
        me = state.active
        seeds = [self.rng.randrange(2 ** 31) for _ in range(self.samples)]
        out = {}
        for kind, keys in plans:
            decide = self._decider(kind, seeds[0])
            vs = []
            for sd in seeds:
                s = determinize(state, me, random.Random(sd))
                _, end = replay_turn(s, keys, decide)
                vs.append(turn_value(end, me, self.search.weights))
            out[kind] = vs
        return out

    def choose_plan(self, state) -> tuple:
        """(kind, keys) of the turn to play, ("bot", None) to leave the turn to the base agent."""
        plans = self.plans(state)
        if not plans or plans[0][0] != "bot" or len(plans) == 1:
            self.last_pick = {"turn": state.turn, "plans": [k for k, _ in plans], "chosen": "bot"}
            return "bot", None
        vals = self.values(state, plans)
        mean = {k: sum(v) / len(v) for k, v in vals.items()}
        best = max(mean, key=lambda k: (mean[k], k == "bot"))
        if best != "bot" and not paired_better(vals[best], vals["bot"], self.margin, self.z):
            best = "bot"
        self.last_pick = {"turn": state.turn, "plans": [k for k, _ in plans], "values": vals, "chosen": best}
        return best, (None if best == "bot" else dict(plans)[best])

    # --- playing ----------------------------------------------------------------------------------------------
    def _set(self, kind: str | None) -> None:
        from svsim.agents.crossturn_agent import forbids
        extra = forbids(kind) if kind and kind.split(":")[0] in RESOURCE else None
        own = self._own_veto
        self.search.veto = own if extra is None else extra if own is None else (lambda s, a: own(s, a) or extra(s, a))

    def act(self, state, actions):
        if state.phase != Phase.MAIN:
            return self.base.act(state, actions)
        if state.turn != self.turn:
            self.turn = state.turn
            self.turns += 1
            self.following = []
            self._set(None)
            if len(actions) == 1:
                return actions[0]
            t = time.perf_counter()
            kind, keys = self.choose_plan(state)
            self.seconds += time.perf_counter() - t
            self.picked[kind.split(":")[0]] = self.picked.get(kind.split(":")[0], 0) + 1
            if keys is not None:
                self._set(kind)
                self.following = list(keys)
        if self.following:
            a = match(state, self.following.pop(0), actions)
            if a is not None:
                return a
            self.following = []
        return self.base.act(state, actions)
