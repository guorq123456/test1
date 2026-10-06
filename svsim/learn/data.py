"""Training data: self-play positions with their outcome, and a player's choices.

- `selfplay(...)`: games between two agents; at the end of each turn the position
  is recorded for the player who ended it (features from their side, their
  deck's craft) and labelled 1 if that player went on to win.
- `choices(record)`: at each decision of the recorded player, the features of the
  position after each legal action (scored as if the turn ended there, as
  ISMCTS scores its leaves) and which one the player chose.
"""
from __future__ import annotations

import random

from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Phase
from svsim.learn.features import features
from svsim.learn.model import deck_craft
from svsim.search.evaluate import after_end_of_turn
from svsim.tools import records


def selfplay_game(job) -> list:
    """One game; returns [(craft, features, won)] for every end of turn."""
    deck_a, deck_b, spec_a, spec_b, seed, potential = job
    from svsim.tools.arena import make_agent
    rng = random.Random(seed)
    swap = rng.random() < 0.5                        # seats and specs alternate with the seed
    decks = (deck_b, deck_a) if swap else (deck_a, deck_b)
    specs = (spec_b, spec_a) if swap else (spec_a, spec_b)
    state = new_game(*decks, seed=seed)
    agents = [make_agent(specs[i], seed * 2 + i) for i in range(2)]
    rows = []
    while not state.over:
        action = agents[state.active].act(state, legal_actions(state))
        if isinstance(action, EndTurn) and state.phase == Phase.MAIN:
            end = after_end_of_turn(state)
            if not end.over:
                rows.append((state.active, int(deck_craft(state, state.active)), features(end, state.active, potential)))
        apply(state, action)
    if state.winner not in (0, 1):
        return []
    return [(craft, x, int(player == state.winner)) for player, craft, x in rows]


def selfplay(deck_a, deck_b, spec_a: str, spec_b: str, games: int, seed: int = 0, potential: bool = True,
             workers: int = 4) -> list:
    jobs = [(deck_a, deck_b, spec_a, spec_b, seed + g, potential) for g in range(games)]
    if workers <= 1:
        return [row for job in jobs for row in selfplay_game(job)]
    from multiprocessing import Pool
    with Pool(workers) as pool:
        return [row for part in pool.imap_unordered(selfplay_game, jobs) for row in part]


def _after(state, action, player: int, potential: bool) -> list | None:
    s = state.clone()
    if isinstance(action, EndTurn):
        s = after_end_of_turn(s)
    else:
        apply(s, action)
    if s.over:
        return None
    return features(s, player, potential)


def choices(record: dict, player: int = 0, potential: bool = True) -> list:
    """[(chosen index, [candidate features])] for each decision of `player` in the
    main phase. Decisions where some move ends the game are left out (the lethal
    search decides those)."""
    out = []
    for state, action in records.steps(record):
        if state.active != player or state.phase != Phase.MAIN:
            continue
        legal = legal_actions(state)
        if action not in legal:
            break
        cands = [_after(state, a, player, potential) for a in legal]
        if any(c is None for c in cands):
            continue
        out.append((legal.index(action), cands))
    return out


def _line_end(state, agent, player: int, potential: bool, max_steps: int = 60) -> list | None:
    """Features at the end of the turn `agent` plays from `state` (None if the game ends)."""
    s = state.clone()
    for _ in range(max_steps):
        if s.over or s.active != player:
            break
        action = agent.act(s, legal_actions(s))
        if isinstance(action, EndTurn):
            break
        apply(s, action)
    if s.over:
        return None
    s = after_end_of_turn(s)
    return None if s.over else features(s, player, potential)


def turn_choices(record: dict, player: int = 0, potential: bool = True, alternatives: tuple = ("end", "greedy",
                 "mcts:50+plan", "random", "random", "random", "random", "random", "random"), seed: int = 0) -> list:
    """[(0, [features at the end of the player's turn, then at the end of the same
    turn played by each alternative])] for each turn of `player` that didn't end
    the game: the player's whole turn should score above the other ways of
    playing it (ending it at once, the AI's ways, random orders)."""
    from svsim.agents.random_agent import RandomAgent
    from svsim.tools.arena import make_agent
    out, start, turn = [], None, None
    for k, (state, action) in enumerate(records.steps(record)):
        if state.phase != Phase.MAIN:
            continue
        if state.active == player and state.turn != turn:
            turn, start = state.turn, state.clone()
        if state.active == player and isinstance(action, EndTurn) and start is not None:
            end = after_end_of_turn(state)
            if not end.over:
                cands = [features(end, player, potential)]
                for j, spec in enumerate(alternatives):
                    if spec == "end":
                        agent = _Ender()
                    elif spec == "random":
                        agent = RandomAgent(seed + 31 * k + j, 0.15)
                    else:
                        agent = make_agent(spec, seed + k)
                    x = _line_end(start, agent, player, potential)
                    if x is not None:
                        cands.append(x)
                if len(cands) > 1:
                    out.append((0, cands))
            start = None
    return out


class _Ender:
    def act(self, state, actions):
        return EndTurn()
