"""Self-play games for the value network, and every position in them as training rows.

    python -m svsim.learn.netdata --games 2000 --out games.jsonl          # play (resumable)

Games are stored as records (tools.records: the deal and the actions), one per
line, so positions can be encoded again with other features without playing
again. Each decision the search made also keeps what the search thought
(record["search"][i], aligned with record["actions"]; None where the lethal
search or the planner chose): the visits of each legal move in
legal_actions order ("visits"), and the search's value of its best move
("value", squashed against the starting position's score "center"), the
targets of a policy head and of a value trained on search values. With probability `explore` a move is replaced by a random legal one, so
the network also sees the positions that bad moves lead to: the search scores
every move it tries, most of them moves the bot would never play, and an
evaluation that has only seen its own good positions guesses wildly there (the
hidden-layer model of 2026-10-06 lost 22 to 78).

`rows(record)` replays a game and yields every position the search can be
asked to score, labelled with the game's result for the player scoring it:
each decision point, for the player to act (phase ACT: inside their turn,
its start included), and the position after each turn's end-of-turn
abilities, before the next turn starts, for the player who ended it (phase
ENDED; MCTS stops a line there). With the opponent's turn played out
(`mcts-reply`), the leaf is the start of the player's next turn, an ACT
position.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import time
from multiprocessing import Pool

ACT, ENDED = 0, 1


def play(job) -> dict:
    """One self-play game (`spec` on both sides) as a record, with exploration."""
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools import records as R
    from svsim.tools.arena import make_agent
    from svsim.ui.session import DECKS
    g, seed, deck, opponent, spec, explore = job
    rng = random.Random(seed * 7919 + g)
    seat = g % 2
    cards = [None, None]
    cards[seat], cards[1 - seat] = decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1])
    agents = [make_agent(spec, seed * 1000 + 2 * g + i) for i in (0, 1)]
    state = new_game(cards[0], cards[1], seed=seed * 100003 + g)
    record = R.new_record(cards[0], cards[1], seed * 100003 + g, state.first, f"{spec} / {spec}")
    record["g"], record["explore"] = g, explore
    record["names"] = [deck, opponent] if seat == 0 else [opponent, deck]   # ui.session.DECKS keys by seat
    record["search"] = []
    while not state.over:
        legal = legal_actions(state)
        search = _search(agents[state.active])
        if search is not None:
            search.last_root = None
        planner = _planner(agents[state.active])
        if planner is not None:
            planner.last_plan = None
        action = agents[state.active].act(state, legal)
        record["search"].append(_thought(state, legal, search))
        if planner is not None and planner.last_plan is not None:      # a cross-turn planner measured
            record.setdefault("plans", []).append(_plan(state, len(record["actions"]), planner.last_plan,
                                                        record["names"]))
        if explore and len(legal) > 1 and state.players[state.active].turns_taken >= 1 and rng.random() < explore:
            action = rng.choice(legal)
        R.add(record, action)
        apply(state, action)
    record["winner"] = state.winner
    return record


def _planner(agent):
    """The cross-turn planner inside an agent (agents.crossturn_agent), if there is one."""
    inner = agent
    for _ in range(5):
        if hasattr(inner, "last_plan"):
            return inner
        inner = getattr(inner, "base", None)
        if inner is None:
            return None
    return None


def _plan(state, i: int, plan: dict, names: list) -> dict:
    """A turn start's measurements by the cross-turn planner, with the position's context: the
    value of each candidate (the search's line, keep a card, keep the bonus play point, don't evolve)
    on each determinization, in record["plans"] (the position itself is record["actions"][:i]
    replayed). keep:<card id> minus line is the card's keep value (agents.crossturn_agent.keep_value)."""
    me = state.active
    p, o = state.players[me], state.players[1 - me]
    side = lambda cards: [[c.defn.card_id, c.atk, c.life, 2 if c.super_evolved else 1 if c.evolved else 0]
                          for c in cards if c.defn.is_follower]
    return {"i": i, "player": me, "turn": state.turn, "own_turn": p.turns_taken,
            "pp": p.max_pp, "next_pp": min(p.max_pp + 1, 10), "bonus": p.bonus_ready, "ep": p.ep, "sep": p.sep,
            "hand": [c.defn.card_id for c in p.hand], "board": side(p.field), "opp_board": side(o.field),
            "hp": p.leader_hp, "opp_hp": o.leader_hp, "opp_hand": len(o.hand), "deck": names[me],
            "opp_deck": names[1 - me], "line": plan["line"], "chosen": plan["chosen"],
            "next_turn": plan["next_turn"], "static": plan.get("static", False),
            "samples": {r: [round(v, 5) for v in vs] for r, vs in plan["samples"].items()}}


def _search(agent):
    """The ISMCTS inside an agent, if there is one."""
    inner = agent
    for _ in range(5):
        if hasattr(inner, "search") and hasattr(inner.search, "last_root"):
            return inner.search
        inner = getattr(inner, "base", None)
        if inner is None:
            return None
    return None


def _thought(state, legal, search):
    if search is None or search.last_root is None or not search.last_root.children:
        return None
    from svsim.search.mcts import _locator, action_key
    where = _locator(state, state.active)
    root = search.last_root
    visits = []
    for a in legal:
        child = root.children.get(action_key(state, a, where))
        visits.append(child.visits if child is not None else 0)
    best = max(root.children.values(), key=lambda c: c.visits)
    return {"visits": visits, "value": round(search.estimate(best), 5), "center": round(search.center, 4)}


def search_value(thought: dict | None, gain: float = 1.0) -> float | None:
    """The search's win probability for the player to act, from a decision's record["search"] entry:
    ISMCTS squashes (score - center) / 8 with score = 8 * gain * logit (models.SCALE), so the best
    line's logit is logit(value) / gain + center / (8 * gain)."""
    import math
    if not thought:
        return None
    v = min(max(thought["value"], 1e-6), 1 - 1e-6)
    z = math.log(v / (1 - v)) / gain + thought["center"] / (8.0 * gain)
    return 1 / (1 + math.exp(-max(-30.0, min(30.0, z))))


def rows(record: dict, with_search: bool = False):
    """(phase, player, state, result) for every position the search may score (see module docstring);
    result is 1 for a win of `player`, 0 for a loss, 0.5 for a draw. The state is a copy. With
    `with_search`, a fifth item: the search's win probability at that decision (search_value), None
    for turn ends and decisions the search didn't make."""
    from svsim.core.actions import EndTurn
    from svsim.core.enums import Phase
    from svsim.search.evaluate import after_end_of_turn
    from svsim.tools import records as R
    winner = record["winner"]
    result = lambda p: 1.0 if winner == p else 0.0 if winner in (0, 1) else 0.5
    thoughts = record.get("search") or []
    gain = record.get("gain", 1.0)
    for i, (state, action) in enumerate(R.steps(record)):
        if state.phase != Phase.MAIN:
            continue
        me = state.active
        q = search_value(thoughts[i] if i < len(thoughts) else None, gain)
        yield (ACT, me, state.clone(), result(me)) + ((q,) if with_search else ())
        if isinstance(action, EndTurn):
            ended = after_end_of_turn(state)
            if not ended.over:
                yield (ENDED, me, ended, result(me)) + ((None,) if with_search else ())


def main() -> None:
    from svsim.ui.session import DECKS
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", type=int, default=2000)
    parser.add_argument("--deck", default="ramp", choices=sorted(DECKS))
    parser.add_argument("--opponent", default="ramp", choices=sorted(DECKS))
    parser.add_argument("--agent", default="mcts:100+plan+learned")
    parser.add_argument("--explore", type=float, default=0.03, help="chance of a random move at each decision")
    parser.add_argument("--seed", type=int, default=20261007)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    done = set()
    if os.path.exists(args.out):
        for line in open(args.out, encoding="utf-8"):
            done.add(json.loads(line)["g"])
    todo = [(g, args.seed, args.deck, args.opponent, args.agent, args.explore)
            for g in range(args.games) if g not in done]
    t0 = time.time()
    with Pool(args.workers) as pool, open(args.out, "a", encoding="utf-8") as fh:
        for k, record in enumerate(pool.imap_unordered(play, todo), 1):
            fh.write(json.dumps(record) + "\n")
            fh.flush()
            if k % 100 == 0:
                print(f"{len(done) + k} games, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
