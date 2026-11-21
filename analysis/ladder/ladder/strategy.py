"""Strategies behind the base (phase 1 minimal form; phase 2 widens it into the players' interface).

A strategy is an object with
    act(pos: base.PublicPosition, actions: list) -> one of `actions`
    guess(pos) -> [(cards, weight), ...]   its guess at the opponent's list (for the referee's out-of-guess count)
It never sees the real state. `actions` are the real legal actions (they hold only uids of cards the seat can see).

`BotStrategy` is the default strategy (the generic normal bot, mcts:100+plan) behind the base: at every decision it
draws one state from its guess (`base.sample`) and lets the unchanged bot decide on it. The bot's own search then
reshuffles that state's hidden cards each iteration, so its sampling stays inside the guess.
"""
from __future__ import annotations

import random

from svsim.core.engine import legal_actions

from . import base

DEFAULT_SPEC = "mcts:100+plan"      # Salem's default strategy (task spec §5.5, plan 阶段 2)


class BotStrategy:
    def __init__(self, spec: str = DEFAULT_SPEC, seed: int = 0, guess_fn=None):
        from svsim.tools.arena import make_agent
        self.spec = spec
        self.agent = make_agent(spec, seed)
        self.rng = random.Random(seed * 1_000_003 + 7)        # the sampler's own stream, separate from the bot's
        self.guess_fn = guess_fn

    def guess(self, pos: base.PublicPosition):
        return self.guess_fn(pos) if self.guess_fn else base.default_guess(pos.opp_craft)

    def act(self, pos: base.PublicPosition, actions: list):
        s, _ = base.sample(pos, self.guess(pos), self.rng)
        mine = legal_actions(s)
        choice = self.agent.act(s, mine)
        if choice not in actions:                 # a sample must never offer a move the real position lacks
            raise RuntimeError(f"sampled state offered {choice!r}, not legal in the real position")
        return choice


def play(deck0, deck1, strategies, seed: int, first: int | None = None, on_decision=None, max_turns: int = 60):
    """A refereed game: each strategy sees only its public position. Returns (winner, state, tracker).
    `on_decision(state, seat, tracker, pos, action)` is called before each action is applied (for checks)."""
    from svsim.core.engine import apply, new_game
    state = new_game(deck0, deck1, seed=seed, first=first, max_turns=max_turns)
    tracker = base.Tracker(state)
    while not state.over:
        seat = state.active
        actions = legal_actions(state)
        pos = base.public_position(state, seat, tracker)
        action = strategies[seat].act(pos, actions)
        if on_decision:
            on_decision(state, seat, tracker, pos, action)
        tracker.before(state)
        apply(state, action)
        tracker.after(state)
    return state.winner, state, tracker
