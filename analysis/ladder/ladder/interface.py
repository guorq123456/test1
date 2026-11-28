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
- turn_start(pos) -> None: once at the first decision of each own turn (phase MAIN, the first time this object is
  asked in a global turn it hasn't seen), before that decision's guess, sample and search, so that decision already
  plays by what it leaves on self. Not called unless the class overrides it (an instance attribute of that name is
  not an override): a strategy that doesn't plays exactly as before, no random stream touched. For planning: look a
  turn or two ahead on samples (the helpers below), keep the plan on self, marked with pos.state.turn and written by
  card ids (an unseen card's uid differs from sample to sample), and carry it out through veto, prior or search.
  Its CPU is that first decision's: the turn-start budget (Limits). An object built mid-turn (the arena's resumed
  games, the puzzles, tools/lethal_bank.py) runs it at the first decision it is asked, which may be mid-turn.
- guess(pos) -> [(cards, weight), ...]: the strategy's guess at the opponent's 40-card list, as weighted lists of
  card definitions. The base updates the weights by the cards the opponent has shown (base.posterior). Default:
  the opponent plays the baseline list of its class (base.default_guess).
- mulligan(state) -> a Mulligan action: the opening redraw. Default: the generic bot's (svsim.agents.greedy_agent
  .mulligan).
- weights(pos) -> svsim.search.evaluate.Weights: the hand-set evaluation's numbers, per decision (so per opponent
  class, per turn). Default: DEFAULT.
- evaluate(state, me, me_next) -> float: replaces the whole evaluation (positive = good for `me`; `me_next`: `me`
  moves next). Override it or `weights`, not both. Default: not overridden (the evaluation with `weights`).
- veto(state, action) -> bool: True leaves the move out of the search (at every node). The lethal search and its
  planner find their lines without it, but each step of a line is put to it before it is played: a step it leaves
  out ends the line there (the steps before it are already played) and the search takes over. If it leaves every
  move out, the search keeps all. Default: not overridden (nothing left out).
- prior(state, actions) -> probabilities over `actions` (summing to 1), or None: a move-order bonus at the root
  (c_prior x P x sqrt(root visits) / (1 + visits), c_prior 0.3). Default: not overridden (no prior).
- search(pos) -> dict: the search's settings for this decision, any of iterations (default 100), c (exploration,
  0.5), scale (evaluation points per unit of the squash, 8.0), max_depth (30), c_prior (0.3). Default: {}.
Class attribute LETHAL: "planner" (default: the lethal search with its planner, as +plan), "exact" (the lethal search
only), "off" (no lethal search).
Class attributes LETHAL_NODES, LETHAL_SCREEN (Salem 11-23 16:53Z, S18; 2.2, LD-60: the default's lethal search has a
budget and misses some lethals): LETHAL_NODES is the most positions it searches (default 2000, at most
LETHAL_NODES_MAX); LETHAL_SCREEN is (n, n2, k): when a quick estimate of this turn's damage falls short of the enemy's
defense, only n positions, or n2 when it is short by k or less (default (200, 1000, 4)); None: no estimate, always
LETHAL_NODES. The estimate counts each card on its own, so damage that needs several cards together (Last Words,
countdowns advanced by spells, buffs that pay off together) is beyond it. A bigger budget costs compute at nearly
every decision, not only a turn's first: the lethal layer searches again whenever the hidden information it sees
changed, and each decision's fresh sample has its own deck order and RNG (2 games: 32 of 34 turn-start decisions
searched, 102 of 104 in-turn ones). So it raises the in-turn part as much as the turn-start part, and the in-turn
part's 1.15 is the one it passes first (Limits); K pays for none of it. A deeper lethal search on K is a turn_start
of the strategy's own (svsim.search.lethal.LethalSearch on samples, the line kept on self, played through prior or
veto).

Helpers for turn_start (module functions; their CPU is the calling decision's):
- sample_states(pos, guess, rng, n) -> [state, ...]: n independent full states for `pos` (base.sample each), the
  opponent's unknown cards drawn from `guess` (pass self.guess(pos) and self.random).
- to_next_turn(pos, guess, rng, line=(), mine=None, opponent=None, max_actions=200) -> (state, info): on a state of
  its own drawn for `pos` (never pos.state itself: its opponent deck holds only the cards seen, a draw from it loses
  on the spot), plays `line` (actions, stopping at the first one that isn't legal there), then `mine` finishes the
  turn (None: end it at once), then `opponent` (default GreedyAgent(seed=rng.getrandbits(31), samples=1)) plays its
  whole turn; it stops before the first decision of my next turn, or when the game is over, or after max_actions
  moves. Only the engine's apply and legal_actions move the state (the next turn starts as in a game: its draw, PP,
  countdowns, start-of-turn effects); an agent's move that isn't legal is played as EndTurn; nothing is applied once
  the game is over. info: stopped ("next_turn", "over", "max_actions"), line (moves of `line` played), line_ok (all
  of it), actions (moves played in all), winner (the state's, None while not over). To compare candidates on the
  same futures, give each a random.Random made from the same seed (drawn from self.random): the same seed draws the
  same state and the same opponent.
- action_key(state, action) -> tuple: the action by card ids and places instead of uids (svsim.search.mcts
  .action_key), the same in every sample: a plan's moves kept as keys are matched in veto / prior.

Randomness: a strategy that needs random numbers uses `self.random` (seeded from the game's strategy seed, separate
from the search's and the sampler's streams), never the time or the global `random`: games are replayed. turn_start
too: self.rng (the sampler's), self.agent and self.tree belong to the decisions, and using them there changes the
default's choices; nothing that changes a choice is kept from one game to the next. A budget is a count (samples,
positions, iterations), never a time: no time module, no search's seconds= and no result's .seconds (the reader
refuses them: codecheck.TIMED_CALLS).

Limits (checked outside this module, which reports nothing about the strategy: a strategy could rewrite it): compute
is the host's measure of the logged decisions, a turn's first decision told from the log, the other decisions (the
mulligan included) are the in-turn ones; each against the default strategy on the same positions, pooled over the
submission's smoke games (submit.py; compute_audit.py at a period's end). Accepted when either holds: the old rule,
all decisions together at most 1.08 times the default's (refused over 1.15: A5, A25, S15); or the turn rule, the
in-turn decisions at most that and the turn-start decisions at most 1.08 times the default's on them plus K times
the default's CPU over the whole of those own turns (K = submit.TURN_K; refused over 1.15 / 1.08 times that line).
Budget not spent is gone; under the turn rule neither part lends to the other. Every decision, turn_start included,
is on the step clock (30 s: runner). The gate compares an update's compute with its old version's (S16; gate.py).
No trained model or pilot (A12: the reader refuses the svsim modules that load one and, by function, the svsim
helpers that load one when called, codecheck.A12_FUNCTIONS); no reading anything but what the hooks get (the
submission check, item 2.3).
"""
from __future__ import annotations

import random

from svsim.agents.greedy_agent import GreedyAgent
from svsim.agents.greedy_agent import mulligan as default_mulligan
from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Phase
from svsim.search.evaluate import DEFAULT
from svsim.search.mcts import action_key as _action_key

from . import base

INTERFACE_VERSION = "interface-2"          # interface-2 (11-28): turn_start and its helpers, compute by the turn
LETHAL_NODES_MAX = 100_000
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


def _lethal_budget(nodes, screen) -> tuple:
    """LETHAL_NODES and LETHAL_SCREEN checked: (nodes, None or (n, n2, k))."""
    def whole(x, lo, hi):
        return type(x) is int and lo <= x <= hi
    if not whole(nodes, 1, LETHAL_NODES_MAX):
        raise ValueError(f"LETHAL_NODES is a whole number from 1 to {LETHAL_NODES_MAX}")
    if screen is None:
        return nodes, None
    if not (isinstance(screen, tuple) and len(screen) == 3 and whole(screen[0], 1, nodes)
            and whole(screen[1], 1, nodes) and whole(screen[2], 0, 100)):
        raise ValueError("LETHAL_SCREEN is None or (n, n2, k): whole numbers, n and n2 at most LETHAL_NODES")
    return nodes, tuple(screen)


def _overridden(obj, name: str) -> bool:
    return getattr(type(obj), name) is not getattr(PlayerStrategy, name)


class PlayerStrategy:
    LETHAL = "planner"
    ITERATIONS = 100            # the default search's iterations; a decision may change it through `search`
    LETHAL_NODES = 2000         # the lethal search's budget (svsim LethalAgent's defaults; module docstring)
    LETHAL_SCREEN = (200, 1000, 4)

    # --- hooks ----------------------------------------------------------------------------------------------

    def turn_start(self, pos: base.PublicPosition) -> None:        # not called unless overridden
        return None

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
        nodes, screen = _lethal_budget(self.LETHAL_NODES, self.LETHAL_SCREEN)
        self.spec = LETHAL_SPECS[self.LETHAL].format(n=int(self.ITERATIONS))
        self.agent = make_agent(self.spec, seed)                     # the same construction as the default
        if self.LETHAL != "off":                                     # the defaults leave it exactly as built
            ls = self.agent.search
            ls.max_nodes = nodes
            ls.screen, ls.near = (None, None) if screen is None else (screen[0], (screen[1], screen[2]))
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
        self.__hook = _overridden(self, "turn_start")               # by the class, as the hooks above
        self.__turn = None                                          # the global turn turn_start last ran in

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
        if self.__hook and pos.state.phase == Phase.MAIN and pos.state.turn != self.__turn:
            self.__turn = pos.state.turn      # the global turn moves only at the mulligans' end and at EndTurn: once
            self.turn_start(pos)              # per own turn, at its first decision, before anything else of it
        s, _ = base.sample(pos, self.guess(pos), self.rng)
        if s.phase != Phase.MAIN:
            choice = self.mulligan(s)
        else:
            self._settings(pos)
            choice = self.agent.act(s, legal_actions(s))
        if choice not in actions:                 # a sample must never offer a move the real position lacks
            raise RuntimeError(f"sampled state offered {choice!r}, not legal in the real position")
        return choice


# --- helpers for turn_start (module docstring) -------------------------------------------------------------------

def sample_states(pos: base.PublicPosition, guess, rng: random.Random, n: int) -> list:
    """`n` independent full states for `pos` (base.sample each, in turn from `rng`); `pos` is not changed."""
    if type(n) is not int or n < 0:
        raise ValueError("n is a whole number, 0 or more")
    return [base.sample(pos, guess, rng)[0] for _ in range(n)]


def to_next_turn(pos: base.PublicPosition, guess, rng: random.Random, line=(), mine=None, opponent=None,
                 max_actions: int = 200) -> tuple:
    """From `pos` (a decision of my own turn) to the first decision of my next turn, on a state of its own drawn
    from `guess` with `rng` (module docstring). Returns (state, info); `pos` is not changed. `rng` is used for the
    state, then (opponent None) one getrandbits(31) for the opponent's seed, whatever happens after."""
    if pos.state.over or pos.state.phase != Phase.MAIN or pos.state.active != pos.me:
        raise ValueError("to_next_turn starts at a decision of your own turn (phase MAIN)")
    if type(max_actions) is not int or max_actions < 0:
        raise ValueError("max_actions is a whole number, 0 or more")
    me = pos.me
    s, _ = base.sample(pos, guess, rng)
    if opponent is None:
        opponent = GreedyAgent(seed=rng.getrandbits(31), samples=1)
    info = {"stopped": "max_actions", "line": 0, "line_ok": False, "actions": 0, "winner": None}

    def play(action) -> None:
        apply(s, action)
        info["actions"] += 1

    for action in line:
        if s.over or s.active != me or info["actions"] >= max_actions or action not in legal_actions(s):
            break
        play(action)
        info["line"] += 1
    else:
        info["line_ok"] = True
    while not s.over and s.active == me and info["actions"] < max_actions:
        legal = legal_actions(s)
        action = EndTurn() if mine is None else mine.act(s, legal)
        play(action if action in legal else EndTurn())
    ended = s.over or s.active != me                # my turn is over (else max_actions stopped it)
    while ended and not s.over and s.active != me and info["actions"] < max_actions:
        legal = legal_actions(s)
        action = opponent.act(s, legal)
        play(action if action in legal else EndTurn())
    if s.over:
        info["stopped"], info["winner"] = "over", s.winner
    elif ended and s.active == me:
        info["stopped"] = "next_turn"
    return s, info


def action_key(state, action) -> tuple:
    """`action` on `state` by card ids and places instead of uids (svsim.search.mcts.action_key): the same key for
    the same move in every sample of a position, so a plan kept as keys can be matched in veto / prior."""
    return _action_key(state, action)
