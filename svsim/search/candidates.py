"""Candidate whole-turn plans from one turn start, deliberately different (turn-level policy iteration, step 0).

The architecture thread 2026-10-09 02:32Z (Salem 02:26Z: the bot's decisions should be counted by the turn, not by
the step): from the same turn start, play several whole-turn plans; later each gets a paired play-out label, and the
turn-end evaluation learns from the differences between plans of one start. This module only makes the plans.

Kinds (`generate`):
1. "bot": the bot's own turn (the agent `spec`, level-strong by default).
2. "second", "third": the bot's search's second and third most visited first move at the root, then the bot.
3. "race": the turn the whole-turn planner (search.turnplan) finds when an end of turn is scored by how many turns
   my lethal clock (search.race.clock) still needs, fewer better; ties broken by the bot's evaluation. The impact
   section's next step: let the search propose a turn that sets up the kill.
4. resource keeping: the bot's turn under one restriction of crossturn_agent (the teacher's): "keep:<card id>"
   (the dearest card the bot's line plays, or the `max_keeps` dearest), "save" (the bonus play point, if the line
   uses it), "noevo" (if the line evolves).
5. "end": end the turn at once.
6. "salem": a given list of actions (Salem's turn in his game), played as it is while it stays legal.

Every plan is played on its own copy of the position (the same random numbers and deck order, so equal prefixes
meet the same luck); an agent decides each step, so a chance action is followed by deciding again from what came
out, as TurnPlanAgent does. A plan ends where it ends the turn; its turn end (`end`) is the position after the
end-of-turn abilities, before the opponent's turn. Plans with the same turn end (search.lethal.state_key) are
merged: the first kind keeps it, the others are listed in `merged`.

`summary` over many positions: the mean seconds per kind, and how often "race" ends elsewhere than "bot".
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Phase

BOT = "v2s"                       # level-strong (ui.session.LEVELS["strong"])


@dataclass
class Candidate:
    kind: str
    actions: list                 # the turn's actions, the ending EndTurn included
    end: object                   # GameState: the turn end (search.evaluate.after_end_of_turn)
    key: tuple                    # search.lethal.state_key(end)
    seconds: float
    merged: list = field(default_factory=list)    # the kinds merged into this one (the same turn end)
    times: dict = field(default_factory=dict)     # seconds by kind, this one's and the merged ones


class ClockScore:
    """A score for the whole-turn planner: minus (my lethal clock's turns x per_turn), plus `tiebreak` x the base
    evaluation. Kept by position."""

    def __init__(self, base, horizon: int = 4, nodes: int = 200, per_turn: float = 24.0, tiebreak: float = 0.25):
        self.base, self.horizon, self.nodes = base, horizon, nodes
        self.per_turn, self.tiebreak = per_turn, tiebreak
        self._memo: dict = {}

    def score(self, state, player: int, player_moves_next: bool = False) -> float:
        from svsim.search.evaluate import WIN, evaluate
        from svsim.search.lethal import state_key
        from svsim.search.race import clock
        if state.winner is not None:
            return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
        key = (state_key(state), player, player_moves_next)
        hit = self._memo.get(key)
        if hit is None:
            turns = clock(state, player, self.horizon, self.nodes).turns
            hit = self._memo[key] = -self.per_turn * turns + self.tiebreak * evaluate(state, player, self.base,
                                                                                      player_moves_next)
        return hit


def _search_of(agent):
    from svsim.tools.gate import _search
    return _search(agent)


def play_turn(state, decide, first=None) -> tuple:
    """Play the turn of the player to act on a copy: `first` (an action) if given, then decide(s) each step, until
    the turn is ended. (actions, turn end)."""
    from svsim.search.evaluate import after_end_of_turn
    s = state.clone()
    me, actions = s.active, []
    pending = [first] if first is not None else []
    while not s.over and s.active == me and s.phase == Phase.MAIN:
        legal = legal_actions(s)
        a = pending.pop(0) if pending else decide(s, legal)
        if a not in legal:
            a = EndTurn()
        actions.append(a)
        if isinstance(a, EndTurn):
            return actions, after_end_of_turn(s)
        apply(s, a)
    return actions, s


def _agent_decider(spec: str, seed: int, veto=None):
    from svsim.tools.arena import make_agent
    agent = make_agent(spec, seed)
    if veto is not None:
        search = _search_of(agent)
        search.veto = veto
    return lambda s, legal: agent.act(s, legal)


def root_alternatives(state, spec: str = BOT, seed: int = 0, count: int = 2) -> list:
    """The bot's search's 2nd, 3rd, ... most visited first moves at the root, as actions of `state`."""
    from svsim.search.mcts import _locator, action_key
    from svsim.tools.arena import make_agent
    search = _search_of(make_agent(spec, seed))
    search.choose(state.clone())
    root = search.last_root
    ranked = sorted(root.children.items(), key=lambda kv: -kv[1].visits)
    where = _locator(state, state.active)
    by_key = {}
    for a in legal_actions(state):
        by_key.setdefault(action_key(state, a, where), a)
    out = [by_key[k] for k, c in ranked[1:] if c.visits > 0 and k in by_key]
    return out[:count]


def generate(state, spec: str = BOT, seed: int = 0, salem=None, max_keeps: int = 1, race_nodes: int = 300,
             race_clock_nodes: int = 200, kinds=("bot", "second", "third", "race", "resource", "end", "salem")):
    """The candidate plans for the player to act at `state` (a main-phase position, ideally a turn start), deduped
    by turn end. `salem`: a list of actions for the "salem" kind."""
    from svsim.agents.crossturn_agent import forbids, restrictions
    from svsim.search.lethal import state_key
    from svsim.search.mcts import action_key, _locator
    if state.phase != Phase.MAIN or state.over:
        raise ValueError("candidate plans need a main-phase position")
    out = []

    def add(kind, run):
        t = time.perf_counter()
        actions, end = run()
        out.append(Candidate(kind, actions, end, state_key(end), time.perf_counter() - t))

    if "bot" in kinds:
        add("bot", lambda: play_turn(state, _agent_decider(spec, seed)))
    if {"second", "third"} & set(kinds):
        t = time.perf_counter()
        alts = root_alternatives(state, spec, seed, 2)
        spent = time.perf_counter() - t
        for name, a in zip(("second", "third"), alts):
            if name in kinds:
                add(name, lambda a=a: play_turn(state, _agent_decider(spec, seed), first=a))
                out[-1].seconds += spent / len(alts)
    if "race" in kinds:
        from svsim.search.turnplan import TurnPlanAgent
        from svsim.tools.arena import make_agent
        base = _search_of(make_agent(spec, seed)).weights
        planner = TurnPlanAgent(max_nodes=race_nodes, samples=2, seed=seed,
                                weights=ClockScore(base, nodes=race_clock_nodes))
        add("race", lambda: play_turn(state, planner.act))
    if "resource" in kinds and out and out[0].kind == "bot":
        s, keys = state.clone(), []
        for a in out[0].actions:                   # the bot's line as keys, for the teacher's restrictions
            keys.append(action_key(s, a, _locator(s, s.active)))
            if isinstance(a, EndTurn):
                break
            apply(s, a)
        for r in restrictions(keys, max_keeps=max_keeps):
            if r == "line":
                continue
            add(r, lambda r=r: play_turn(state, _agent_decider(spec, seed, forbids(r))))
    if "end" in kinds:
        add("end", lambda: play_turn(state, lambda s, legal: EndTurn()))
    if "salem" in kinds and salem:
        moves = list(salem)
        add("salem", lambda: play_turn(state, lambda s, legal: moves.pop(0) if moves else EndTurn()))
    merged, by_key = [], {}
    for c in out:
        if c.key in by_key:
            by_key[c.key].merged.append(c.kind)
            by_key[c.key].times[c.kind] = c.seconds
        else:
            c.times[c.kind] = c.seconds
            by_key[c.key] = c
            merged.append(c)
    return merged


def summary(results: list) -> dict:
    """Over a list of generate() results: {"seconds": {kind: mean seconds (keep:<id> as "keep"), merged plans
    included}, "race_differs": the share of positions
    whose "race" plan ends elsewhere than "bot" (merged counts as the same), "candidates": mean plans kept}."""
    times: dict = {}
    differs, n = 0, 0
    for cands in results:
        kinds = {}
        for c in cands:
            for k, t in (c.times or {c.kind: c.seconds}).items():
                times.setdefault(k.split(":")[0], []).append(t)
            kinds[c.kind] = c
            for k in c.merged:
                kinds[k] = c
        if "race" in kinds and "bot" in kinds:
            n += 1
            differs += kinds["race"] is not kinds["bot"]
    return {"seconds": {k: sum(v) / len(v) for k, v in times.items()},
            "race_differs": differs / n if n else None,
            "candidates": sum(len(c) for c in results) / len(results) if results else None}


def main() -> None:
    """python -m svsim.search.candidates <records.jsonl> --positions N [--spec v2s] [--out plans.jsonl]: the plans at
    the first N own-turn starts (the first decision of each own turn, game by game), one line per position (the
    plans' kinds, merged kinds, actions and seconds), then the summary."""
    import argparse
    import json
    from svsim.core.actions import to_dict
    from svsim.tools import records as R
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("records")
    parser.add_argument("--positions", type=int, default=50)
    parser.add_argument("--spec", default=BOT)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--race-nodes", type=int, default=300)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    results, out = [], open(args.out, "w", encoding="utf-8") if args.out else None
    for line in open(args.records, encoding="utf-8"):
        if len(results) >= args.positions:
            break
        record, seen = json.loads(line), set()
        for i, (state, _) in enumerate(R.steps(record)):
            if len(results) >= args.positions:
                break
            key = (state.active, state.turn)
            if state.phase != Phase.MAIN or key in seen:
                continue
            seen.add(key)
            cands = generate(state, spec=args.spec, seed=args.seed, race_nodes=args.race_nodes)
            results.append(cands)
            if out:
                out.write(json.dumps({"g": record.get("g"), "i": i, "player": state.active,
                                      "plans": [{"kind": c.kind, "merged": c.merged, "times": c.times,
                                                 "actions": [to_dict(a) for a in c.actions]} for c in cands]}) + "\n")
    print(json.dumps(summary(results), ensure_ascii=False))


if __name__ == "__main__":
    main()
