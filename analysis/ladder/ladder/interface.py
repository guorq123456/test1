"""The players' strategy interface (phase 2, item 2.1): what a player's strategy may change, and nothing else.

A player's strategy is a subclass of `PlayerStrategy` in the player's own module, entered as "py:<module>:<Class>"
(runner.make_strategy calls the class with seed=...). It sits in the same seat as the default strategy: behind the
base (base.py), so it never receives the real game state. At each decision the base draws one full state consistent
with what the seat has seen, the opponent's unknown cards drawn from the strategy's own guess (`guess`), and the
search decides on that sample. Every hook below gets either the public position (`pos`, base.PublicPosition) or such
a sample (`state`): never the real state.

The default strategy is the generic bot mcts:100+plan (ISMCTS, 100 iterations a decision, behind the exact lethal
search with its planner). A subclass that overrides nothing plays exactly the default strategy, decision for
decision (tests/test_interface.py).

Hooks (override any; the default is what the default strategy does):
- guess(pos) -> [(cards, weight), ...]: the strategy's guess at the opponent's 40-card list, as weighted lists of
  card definitions. The base updates the weights by the cards the opponent has shown (base.posterior). Default:
  the opponent plays the baseline list of its class (base.default_guess).
- mulligan(state) -> a Mulligan action: the opening redraw. Default: the generic bot's (svsim.agents.greedy_agent
  .mulligan).
- weights(pos) -> svsim.search.evaluate.Weights: the hand-set evaluation's numbers, per decision (so per opponent
  class, per turn). Default: DEFAULT.
- evaluate(state, me, me_next) -> float: replaces the whole evaluation (positive = good for `me`; `me_next`: `me`
  moves next). Override it or `weights`, not both. Default: not overridden (the evaluation with `weights`).
- veto(state, action) -> bool: True leaves the move out of the search (at every node) and out of the lethal
  search's lines. If it leaves every move out, all are kept. Default: not overridden (nothing left out).
- prior(state, actions) -> probabilities over `actions` (summing to 1), or None: a move-order bonus at the root
  (c_prior x P x sqrt(root visits) / (1 + visits), c_prior 0.3). Default: not overridden (no prior).
- search(pos) -> dict: the search's settings for this decision, any of iterations (default 100), c (exploration,
  0.5), scale (evaluation points per unit of the squash, 8.0), max_depth (30), c_prior (0.3). Default: {}.
Class attribute LETHAL: "planner" (default: the exact lethal search with its planner, as +plan), "exact" (the exact
lethal search only), "off" (no lethal search).

Randomness: a strategy that needs random numbers uses `self.random` (seeded from the game's strategy seed, separate
from the search's and the sampler's streams), never the time or the global `random`: games are replayed.

Limits (checked outside this module): per-step compute at most 1.08 times the default strategy's (A5, A25; the
gate refuses a version over it), no trained model or pilot (A12), no reading anything but what the hooks get (the
submission check, item 2.3).
"""
from __future__ import annotations

import random

from svsim.agents.greedy_agent import mulligan as default_mulligan
from svsim.core.engine import legal_actions
from svsim.core.enums import Phase
from svsim.search.evaluate import DEFAULT

from . import base

INTERFACE_VERSION = "interface-1"
LETHAL_SPECS = {"planner": "mcts:{n}+plan", "exact": "mcts:{n}", "off": "mcts-raw:{n}"}
SEARCH_KNOBS = {"iterations", "c", "scale", "max_depth", "c_prior"}


class _Evaluation:
    """Hands the search's evaluation to the strategy's `evaluate` (svsim.search.evaluate calls `score`)."""
    def __init__(self, fn):
        self.fn = fn

    def score(self, state, player, player_moves_next):
        return float(self.fn(state, player, player_moves_next))


class _Prior:
    def __init__(self, fn):
        self.fn = fn

    def priors(self, state, actions):
        return self.fn(state, actions)


def _overridden(obj, name: str) -> bool:
    return getattr(type(obj), name) is not getattr(PlayerStrategy, name)


class PlayerStrategy:
    LETHAL = "planner"
    ITERATIONS = 100            # the default search's iterations; a decision may change it through `search`

    # --- hooks ----------------------------------------------------------------------------------------------

    def guess(self, pos: base.PublicPosition):
        return base.default_guess(pos.opp_craft)

    def mulligan(self, state):
        return default_mulligan(state)

    def weights(self, pos: base.PublicPosition):
        return DEFAULT

    def evaluate(self, state, me: int, me_next: bool) -> float:    # not called unless overridden
        raise NotImplementedError

    def veto(self, state, action) -> bool:                         # not called unless overridden
        return False

    def prior(self, state, actions):                               # not called unless overridden
        return None

    def search(self, pos: base.PublicPosition) -> dict:
        return {}

    # --- machinery (don't override) ---------------------------------------------------------------------------

    def __init__(self, seed: int = 0):
        from svsim.tools.arena import make_agent
        if self.LETHAL not in LETHAL_SPECS:
            raise ValueError(f"LETHAL is one of {sorted(LETHAL_SPECS)}")
        if _overridden(self, "evaluate") and _overridden(self, "weights"):
            raise ValueError("override evaluate or weights, not both")
        self.spec = LETHAL_SPECS[self.LETHAL].format(n=int(self.ITERATIONS))
        self.agent = make_agent(self.spec, seed)                     # the same construction as the default
        self.rng = random.Random(seed * 1_000_003 + 7)              # the sampler's own stream (as BotStrategy)
        self.random = random.Random(seed * 7_919 + 101)            # the player's own stream (replays need it)
        self.tree = self._search_object()
        self.defaults = {k: getattr(self.tree, k) for k in ("iterations", "c", "scale", "max_depth", "c_prior")}
        if _overridden(self, "evaluate"):
            self.tree.weights = _Evaluation(self.evaluate)
        if _overridden(self, "veto"):
            self.tree.veto = self.veto
        if _overridden(self, "prior"):
            self.tree.prior = _Prior(self.prior)

    def _search_object(self):
        agent = self.agent
        for _ in range(4):
            if hasattr(getattr(agent, "search", None), "iterations"):
                return agent.search
            agent = getattr(agent, "base", None)
        raise RuntimeError("no search inside the agent")

    def _settings(self, pos):
        asked = self.search(pos) or {}
        bad = set(asked) - SEARCH_KNOBS
        if bad:
            raise ValueError(f"search settings {sorted(bad)} are not open (open: {sorted(SEARCH_KNOBS)})")
        for k, default in self.defaults.items():
            setattr(self.tree, k, type(default)(asked[k]) if k in asked else default)
        if not _overridden(self, "evaluate"):
            self.tree.weights = self.weights(pos)

    def act(self, pos: base.PublicPosition, actions: list):
        s, _ = base.sample(pos, self.guess(pos), self.rng)
        if s.phase != Phase.MAIN:
            choice = self.mulligan(s)
        else:
            self._settings(pos)
            choice = self.agent.act(s, legal_actions(s))
        if choice not in actions:                 # a sample must never offer a move the real position lacks
            raise RuntimeError(f"sampled state offered {choice!r}, not legal in the real position")
        return choice
