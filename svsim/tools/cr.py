"""Rate the AI (and the player) in class rating (CR), the ladder rules the player gave.

    python -m svsim.tools.cr --games 100
    python -m svsim.tools.cr --players ramp:mcts:100+plan+learned rhino:mcts:200+plan --games 200 \\
        --human replays/ --anchor 1600

A player is "<deck>:<agent>" (decks: rhino, ramp, pirate; agents as in
tools.arena). Every pair plays --games games, seats and first player
alternating; results accumulate in --results, so adding a player later only
plays the new pairs. --human adds the recorded games of a person (records from
tools.play or the web page, the person at seat 0), as "你:<deck>" against the
AI that played them. CRs come from svsim.learn.rating.ladder: the person (or,
without --human, the first player) is fixed at --anchor (a CR, or diamond /
sapphire / ruby for the Grand Master starting CR; default 0, so CRs read as
differences), the rest settle where their expected CR change is zero. The 90%
ranges redraw every pair's win rate from what its games allow.
"""
from __future__ import annotations

import argparse
import json
import os
import random
from multiprocessing import Pool

from svsim.cards import decks
from svsim.core.actions import from_dict
from svsim.core.engine import apply, legal_actions, new_game
from svsim.learn import rating
from svsim.tools import records
from svsim.ui.session import DECKS


def split(player: str) -> tuple[str, str]:
    deck, _, spec = player.partition(":")
    if deck not in DECKS or not spec:
        raise ValueError(f"player {player!r} is not <deck>:<agent> with a deck in {sorted(DECKS)}")
    return deck, spec


def label(player: str) -> str:
    if player.startswith("你:"):
        return f"你 {DECKS[player[2:]][0]}"
    deck, spec = split(player)
    return f"AI {DECKS[deck][0]} {spec}"


def play(job) -> tuple:
    """One game; returns (a, b, 1 if a won, 0 if b won, 0.5 for a draw)."""
    a, b, g, seed = job
    (deck_a, spec_a), (deck_b, spec_b) = split(a), split(b)
    game_seed = seed * 1_000_003 + g
    rng = random.Random(game_seed)
    a_seat = g % 2
    seat_decks = [None, None]
    seat_decks[a_seat], seat_decks[1 - a_seat] = decks.build(DECKS[deck_a][1]), decks.build(DECKS[deck_b][1])
    state = new_game(*seat_decks, seed=game_seed, first=(g // 2) % 2)
    from svsim.tools.arena import make_agent
    agents = [None, None]
    agents[a_seat] = make_agent(spec_a, rng.randrange(10 ** 9))
    agents[1 - a_seat] = make_agent(spec_b, rng.randrange(10 ** 9))
    while not state.over:
        apply(state, agents[state.active].act(state, legal_actions(state)))
    score = 0.5 if state.winner not in (0, 1) else float(state.winner == a_seat)
    return a, b, score


def deck_of(ids: list) -> str | None:
    for key, (_, listing) in DECKS.items():
        if sorted(c.card_id for c in decks.build(listing)) == sorted(ids):
            return key
    return None


def human_results(paths: list[str]) -> dict:
    """{(你:<deck>, <deck>:<ai>): [score, games]} from finished records."""
    out: dict = {}
    files = []
    for path in paths:
        if os.path.isdir(path):
            files += [os.path.join(path, f) for f in sorted(os.listdir(path)) if f.endswith(".json")]
        else:
            files.append(path)
    for f in files:
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        record = data.get("record", data)                # the web page's store wraps the record
        if "actions" not in record:
            continue
        state = records.start(record)
        for d in record["actions"]:
            apply(state, from_dict(d))
        if not state.over:
            continue                                     # unfinished
        mine, theirs = deck_of(record["decks"][0]), deck_of(record["decks"][1])
        if mine is None or theirs is None:
            continue
        key = (f"你:{mine}", f"{theirs}:{record['ai']}")
        score = 0.5 if state.winner not in (0, 1) else float(state.winner == 0)
        acc = out.setdefault(key, [0.0, 0])
        acc[0] += score
        acc[1] += 1
    return out


def load(path: str) -> dict:
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return {tuple(k.split(" | ")): v for k, v in json.load(f).items()}


def store(path: str, results: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump({" | ".join(k): v for k, v in results.items()}, f, ensure_ascii=False, indent=1)


def anchor_value(text: str) -> float:
    return float(rating.START[text]) if text in rating.START else float(text)


def report(results: dict, anchor: str, anchor_cr: float) -> None:
    point, span = rating.bootstrap({k: tuple(v) for k, v in results.items()}, {anchor: anchor_cr})
    alone = sorted(set(point) - rating.connected(results, anchor))
    if alone:
        print("注意：这些玩家和基准之间没有对局连起来，它们的 CR 没有意义：" + "、".join(label(x) for x in alone))
    print(f"CR（{label(anchor)} 固定为 {anchor_cr:.0f}；括号里是 90% 区间）：")
    for x in sorted(point, key=lambda x: -point[x]):
        lo, hi = span[x]
        n = sum(v[1] for k, v in results.items() if x in k)
        print(f"  {point[x]:7.0f}  ({lo:6.0f} ~ {hi:6.0f})  {label(x)}  [{n} 局]")
    print("两两对局（胜率，以及这个胜率让 CR 稳定在多大的差距）：")
    for (a, b), (w, n) in sorted(results.items()):
        gap = rating.steady_gap(w / n)
        gap_text = "≥200，匹配不到" if gap == float("inf") else "≤-200，匹配不到" if gap == float("-inf") \
            else f"{gap:+.0f}"
        reach = "" if abs(gap) == float("inf") or rating.can_match(point[a], point[b]) else "（定下来以后匹配不到）"
        print(f"  {label(a)} 对 {label(b)}：{w:g}/{n} = {w / n:.0%}，差距 {gap_text}{reach}")


DEFAULT_PLAYERS = ["ramp:mcts:200+plan", "ramp:mcts:100+plan", "ramp:mcts:100+plan+learned",
                   "ramp:mcts:200+plan+learned", "rhino:mcts:200+plan", "rhino:mcts:100+plan"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--players", nargs="+", default=DEFAULT_PLAYERS)
    parser.add_argument("--games", type=int, default=100, help="games per pair (counting earlier ones)")
    parser.add_argument("--human", nargs="*", default=[], help="folders or files of the person's records")
    parser.add_argument("--anchor", default="0", help="the person's CR, or diamond / sapphire / ruby")
    parser.add_argument("--results", default="replays/cr_results.json")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    for p in args.players:
        split(p)
    results = {k: v for k, v in load(args.results).items() if not k[0].startswith("你")}
    jobs = []
    for i, a in enumerate(args.players):
        for b in args.players[i + 1:]:
            done = results.get((a, b), [0, 0])[1]
            jobs += [(a, b, g, args.seed) for g in range(done, args.games)]
    if jobs:
        print(f"要下 {len(jobs)} 局……")
        with Pool(args.workers) as pool:
            for k, (a, b, score) in enumerate(pool.imap_unordered(play, jobs), 1):
                acc = results.setdefault((a, b), [0.0, 0])
                acc[0] += score
                acc[1] += 1
                if k % 50 == 0 or k == len(jobs):
                    store(args.results, results)
                    print(f"  {k}/{len(jobs)}", flush=True)
    human = human_results(args.human)
    keep = set(args.players)
    chosen = {k: v for k, v in results.items() if k[0] in keep and k[1] in keep}
    chosen.update(human)
    anchor = next(iter(human))[0] if human else args.players[0]
    report(chosen, anchor, anchor_value(args.anchor))


if __name__ == "__main__":
    main()
