"""Baseline agents and a match runner."""
import random

from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions
from svsim.core.state import GameState


class RandomAgent:
    """Picks a legal action at random. `end_turn_weight` < 1 makes it act more
    before passing, which gives more varied games for fuzzing."""

    def __init__(self, seed: int | None = None, end_turn_weight: float = 1.0):
        self.rng = random.Random(seed)
        self.end_turn_weight = end_turn_weight

    def act(self, state: GameState, actions: list):
        if len(actions) > 1 and self.end_turn_weight != 1.0:
            weights = [self.end_turn_weight if isinstance(a, EndTurn) else 1.0 for a in actions]
            return self.rng.choices(actions, weights)[0]
        return self.rng.choice(actions)


def play_game(state: GameState, agents, on_action=None) -> int:
    """Run a match to the end. Returns the winner (0, 1, or DRAW)."""
    while not state.over:
        actions = legal_actions(state)
        action = agents[state.active].act(state, actions)
        apply(state, action)
        if on_action:
            on_action(state, action)
    return state.winner
