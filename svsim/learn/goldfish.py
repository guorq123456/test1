"""A deck's plan in numbers: it plays against an opponent who does nothing (the "goldfish").

The dynamic half of a deck's description for an evaluation shared by every deck
(docs/universal-bot-plan.md; the static half is learn.deckrep): how fast the deck kills when
nothing stands in its way, how its damage, play points and field grow turn by turn, and how many
cards it plays a turn. An opponent that does nothing can't show how a deck defends (removal and
heal are worth nothing here; learn.deckrep measures those), and the profile is only as good as the
agent playing it: a combo turn the agent can't find makes the deck look slower than it is.

`goldfish(deck, games, spec)` plays the games and returns the per-game records;
`profile(records)` turns them into the vector `profile_names()` names.
"""
from __future__ import annotations

import numpy as np

from svsim.core.actions import EndTurn, Mulligan

TURNS = (3, 4, 5, 6, 7, 8, 10)       # own turns the profile reads damage, play points and field at


class Passive:
    """Keeps its opening hand and ends every turn; with `wipe`, first destroys every follower of the
    other side (by ability: Last Words still fire), so each of the deck's turns starts from its hand."""

    def __init__(self, wipe: bool = False):
        self.wipe = wipe

    def act(self, state, actions):
        for a in actions:
            if isinstance(a, Mulligan):
                return Mulligan(())
        if self.wipe:
            from svsim.core import effects as E
            from svsim.core.engine import resolve_queue
            for f in list(state.players[1 - state.active].followers):
                E.destroy(state, f)
            resolve_queue(state)
        return next(a for a in actions if isinstance(a, EndTurn))


def one_game(deck, spec: str, seed: int, first: int, wall: int = 0, wipe: bool = False, turns: int = 10) -> dict:
    from svsim.cards import demo
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools.arena import make_agent
    state = new_game(list(deck), [demo.FOOTMAN] * 40, seed=seed, first=first)
    agents = [make_agent(spec, seed), Passive(wipe)]
    me, foe = state.players[0], state.players[1]
    if wall:                                   # the enemy leader can't die: the deck's whole curve shows
        foe.leader_hp = foe.leader_max_hp = wall
    start_hp = foe.leader_hp
    rows, played, turn_of = [], 0, {}
    while not state.over and me.turns_taken <= (turns if wall else 16):
        actions = legal_actions(state)
        who = state.active
        action = agents[who].act(state, actions)
        if who == 0 and isinstance(action, EndTurn):
            rows.append((me.turns_taken, start_hp - foe.leader_hp, me.max_pp,
                         sum(f.atk + max(f.life, 0) for f in me.followers), played, len(me.hand)))
            played = 0
        if who == 0 and type(action).__name__ == "PlayCard":
            played += 1
            card = next((c for c in me.hand if c.uid == action.uid), None)
            if card is not None:
                turn_of.setdefault(card.defn.card_id, []).append(me.turns_taken)
        apply(state, action)
    kill = me.turns_taken if state.winner == 0 else 17
    return {"kill": kill, "rows": rows, "first": first, "turn_of": turn_of}


def goldfish(deck, games: int = 200, spec: str = "greedy", seed: int = 0, workers: int = 1,
             wall: int = 0, wipe: bool = False) -> list[dict]:
    """`wall`: the enemy leader's defense instead of the usual (0), so the game runs ten own turns and
    shows the whole curve rather than only how fast an unopposed board kills; `wipe`: the opponent
    destroys the deck's followers every turn, so damage counts what each turn brings from hand."""
    jobs = [(deck, spec, seed * 100003 + g, g % 2, wall, wipe) for g in range(games)]
    if workers <= 1:
        return [one_game(*j) for j in jobs]
    from multiprocessing import Pool
    with Pool(workers) as pool:
        return pool.starmap(one_game, jobs)


def _at(rows, turn, col):
    """The value of column `col` at the end of own turn `turn` (the last one reached if the game ended)."""
    got = [r[col] for r in rows if r[0] <= turn]
    return got[-1] if got else 0.0


def profile(records) -> np.ndarray:
    kills = np.array([r["kill"] for r in records], dtype=float)
    out = [kills.mean(), np.percentile(kills, 10), np.percentile(kills, 90), (kills <= 7).mean()]
    for col in (1, 2, 3):                                    # damage dealt so far, max play points, field
        out += [np.mean([_at(r["rows"], t, col) for r in records]) for t in TURNS]
    plays = np.array([[_at(r["rows"], t, 4) for t in TURNS] for r in records]).mean(axis=0)
    out += list(plays)
    burst = [max((b[1] - a[1] for a, b in zip(r["rows"], r["rows"][1:])), default=0) for r in records]
    out += [float(np.mean(burst))]                           # the most damage dealt in one turn
    return np.array(out, dtype=float)


def profile_names() -> list[str]:
    names = ["kill_mean", "kill_p10", "kill_p90", "kill_by7"]
    for what in ("damage", "max_pp", "field"):
        names += [f"{what}_t{t}" for t in TURNS]
    return names + [f"plays_t{t}" for t in TURNS] + ["burst"]
