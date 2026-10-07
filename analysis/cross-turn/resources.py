"""What players keep at the end of their turns: Salem, the web bot, v2 self-play.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> \
        --salem analysis/mirror-regression/positions.json \
        --selfplay "v2 (mcts:100)" sharp/v2_selfplay.jsonl \
        --selfplay "v2 (mcts:400)" analysis/selfplay/v2-mcts400-500games.jsonl.gz \
        [--paired turns.jsonl] [--workers 4] [--json out.json]

Every turn that ends with EndTurn is measured with turnlib.kept at the EndTurn
decision (a turn that wins the game is left out, also when it wins at its end:
an evolved Erntz's 8 damage, a crest). --salem reads Salem's 10
mirror games: seat 0 is Salem, seat 1 the web bot Salem played. --selfplay
reads learn.netdata records (both seats). --paired reads play_turns.py output:
Salem and the bots on the same turn starts.
Grouped by the player's own turn (1-3, 4-6, 7+) and by going first / second.
"""
import argparse
import gzip
import json
import math
import statistics
from collections import defaultdict
from multiprocessing import Pool

from svsim.core.actions import EndTurn, from_dict
from svsim.core.engine import apply
from svsim.core.enums import Phase
from svsim.tools import records

import turnlib as T

BUCKETS = ("1-3", "4-6", "7+")


def bucket(own):
    return "1-3" if own <= 3 else "4-6" if own <= 6 else "7+"


def game_rows(args):
    """One row per turn ended with EndTurn by a player in `seats` (kept + where it was)."""
    line, seats = args
    record = json.loads(line) if isinstance(line, str) else line
    st = records.start(record)
    rows, start, turn = [], None, []
    for data in record["actions"]:
        a = from_dict(data)
        if st.phase != Phase.MAIN:
            apply(st, a)
            continue
        me = st.active
        if not turn:
            start = st.clone()
        turn.append((st.clone(), a))
        row = None
        if isinstance(a, EndTurn) and me in seats:
            p = st.players[me]
            row = {"own_turn": p.turns_taken, "first": st.first == me, **T.kept(start, st, me, turn)}
        apply(st, a)
        if row is not None and not (st.over and st.winner == me):   # not a turn won at its end
            rows.append(row)
        if st.over or st.active != me:
            turn = []
    return rows


def lines_of(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [line for line in f if line.strip()]


def share(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def stats(rows):
    """The numbers of one group of turns."""
    if not rows:
        return None
    evo_chance = [r for r in rows if r["evolved"] or r["evo_left"] or r["se_left"]]
    bonus = [r for r in rows if r["bonus"] != "none"]
    return {
        "turns": len(rows),
        "pp_left": statistics.mean(r["pp_left"] for r in rows),
        "pp_left_any": share([r["pp_left"] > 0 for r in rows]),
        "playable": statistics.mean(r["playable"] for r in rows),
        "playable_any": share([r["playable"] > 0 for r in rows]),
        "evo_chances": len(evo_chance),
        "evo_skipped": share([not r["evolved"] for r in evo_chance]),
        "ep_sep": statistics.mean(r["ep"] + r["sep"] for r in rows),
        "bonus_turns": len(bonus),
        "bonus_kept": share([r["bonus"] == "kept" for r in bonus]),
        "hand": statistics.mean(r["hand"] for r in rows),
    }


def table(title, groups):
    print(f"\n{title}")
    print(f"{'来源':<22}{'组':>5}{'回合':>6}{'剩PP':>7}{'剩PP>0':>8}{'可出没出':>9}{'≥1张':>7}"
          f"{'能进化没进化':>12}{'(机会)':>7}{'EP+SEP':>8}{'留额外PP':>10}{'(回合)':>7}{'手牌':>6}")
    for src, rows in groups:
        for g in BUCKETS + ("all",):
            s = stats([r for r in rows if g == "all" or bucket(r["own_turn"]) == g])
            if s is None:
                continue
            print(f"{src:<22}{g:>5}{s['turns']:>6}{s['pp_left']:>7.2f}{s['pp_left_any']:>8.0%}"
                  f"{s['playable']:>9.2f}{s['playable_any']:>7.0%}{s['evo_skipped']:>12.0%}"
                  f"{s['evo_chances']:>7}{s['ep_sep']:>8.2f}"
                  f"{s['bonus_kept'] if s['bonus_turns'] else float('nan'):>10.0%}{s['bonus_turns']:>7}"
                  f"{s['hand']:>6.1f}")


def paired(path):
    """Salem against each bot on the same starts: the mean of (bot - Salem) per turn, 95% interval
    over turns (each bot's seeds averaged first)."""
    rows = [json.loads(line) for line in open(path, encoding="utf-8")]
    specs = list(rows[0]["bots"])
    print(f"\n同一回合开头，bot 减 Salem（{len(rows)} 个回合里双方都没在当回合赢的；bot 每回合的几个种子先平均）")
    keys = (("pp_left", "剩PP"), ("playable", "可出没出"), ("ep_sep", "EP+SEP"), ("evolved", "进化了"),
            ("bonus_kept", "留额外PP"))

    def value(k, kept):
        if k == "ep_sep":
            return kept["ep"] + kept["sep"]
        if k == "evolved":
            return 1.0 if kept["evolved"] else 0.0
        if k == "bonus_kept":
            return None if kept["bonus"] == "none" else float(kept["bonus"] == "kept")
        return kept[k]

    out = {}
    for spec in specs:
        print(f"\n  {spec}")
        for g in BUCKETS + ("all",):
            line = f"    {g:>4}"
            for k, label in keys:
                diffs = []
                for r in rows:
                    if g != "all" and bucket(r["own_turn"]) != g:
                        continue
                    if r["salem"]["kept"] is None:
                        continue
                    sv = value(k, r["salem"]["kept"])
                    bv = [value(k, b["kept"]) for b in r["bots"][spec] if b["kept"] is not None]
                    bv = [v for v in bv if v is not None]
                    if sv is None or not bv:
                        continue
                    diffs.append(statistics.mean(bv) - sv)
                if len(diffs) < 2:
                    line += f"  {label} —"
                    continue
                m = statistics.mean(diffs)
                h = 1.96 * statistics.stdev(diffs) / math.sqrt(len(diffs))
                out[(spec, g, k)] = (m, h, len(diffs))
                line += f"  {label} {m:+.2f}±{h:.2f}"
            n = sum(1 for r in rows if (g == "all" or bucket(r["own_turn"]) == g) and r["salem"]["kept"])
            print(line + f"  （{n} 回合）")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--salem", default=None)
    p.add_argument("--selfplay", nargs=2, action="append", default=[], metavar=("LABEL", "FILE"))
    p.add_argument("--paired", default=None)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--json", default=None)
    args = p.parse_args()
    groups = []
    with Pool(args.workers) as pool:
        if args.salem:
            games = list(json.load(open(args.salem, encoding="utf-8"))["records"].values())
            for seat, label in ((0, "Salem"), (1, "网页 bot（Salem 的对手）")):
                rows = [r for part in pool.map(game_rows, [(g, {seat}) for g in games]) for r in part]
                groups.append((label, rows))
        for label, path in args.selfplay:
            lines = lines_of(path)
            rows = [r for part in pool.imap_unordered(game_rows, [(line, {0, 1}) for line in lines], 8)
                    for r in part]
            groups.append((f"{label} {len(lines)}局", rows))
    if groups:
        table("每个回合结束时（全部）", groups)
        table("先手", [(s, [r for r in rows if r["first"]]) for s, rows in groups])
        table("后手", [(s, [r for r in rows if not r["first"]]) for s, rows in groups])
    if args.paired:
        paired(args.paired)
    if args.json:
        json.dump({s: rows for s, rows in groups}, open(args.json, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
