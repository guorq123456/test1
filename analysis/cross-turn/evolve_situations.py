"""When a player could evolve: did they, and were they ahead, even or behind? Salem against the bots.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> --salem analysis/mirror-regression/salem_games.json \
        [--selfplay LABEL FILE ...] [--json out.json]

Every turn (not won on that turn) at whose decisions an evolution was legal
at least once: whether the player evolved, and the situation at the turn's
start, two coarse ways:
- life: own leader defense minus the opponent's: ahead at +4 or more, behind
  at -4 or less, even between;
- board: the sum of attack + defense of own followers minus the opponent's:
  ahead at +5 or more, behind at -5 or less, even between; at the turn's
  start, and (board_prev) at the end of the player's previous turn, before
  the opponent acted;
- hand: own hand size minus the opponent's: ahead at +2, behind at -2.
Reported: the share of such turns where the player held (did not evolve), by
situation, with 95% Wilson intervals; the situation of the turns where the
player spent the very first point on the turn it unlocked; and holds by life
situation and own-turn segment. The board measure is taken at the start of
the own turn, right after the opponent played, so most turns read "behind".
"""
import argparse
import gzip
import json
import math
from collections import defaultdict

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import EndTurn, Evolve, from_dict
from svsim.core.engine import apply, legal_actions
from svsim.tools import records


def lines_of(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [line for line in f if line.strip()]


def cut(v, k):
    return "领先" if v >= k else "落后" if v <= -k else "均势"


def board_diff(st, me):
    p, o = st.players[me], st.players[1 - me]
    return sum(f.atk + f.life for f in p.followers) - sum(f.atk + f.life for f in o.followers)


def situation(st, me):
    p, o = st.players[me], st.players[1 - me]
    return cut(p.leader_hp - o.leader_hp, 4), cut(board_diff(st, me), 5), cut(len(p.hand) - len(o.hand), 2)


def turns(record, seats):
    """(seat, own turn, first?, situation at the start, could evolve, evolved, first point at unlock)."""
    st = records.start(record)
    out = []
    cur = None
    prev_end = {0: None, 1: None}       # board difference at the end of each player's previous turn
    for data in record["actions"]:
        a = from_dict(data)
        if isinstance(a, EndTurn) and st.phase.name == "MAIN":
            prev_end[st.active] = board_diff(st, st.active)
        if st.phase.name == "MAIN" and (cur is None or (st.turn, st.active) != cur["key"]):
            if cur is not None and cur["seat"] in seats and not (st.over and st.winner == cur["seat"]):
                out.append(cur)
            p = st.players[st.active]
            cur = {"key": (st.turn, st.active), "seat": st.active, "own_turn": p.turns_taken,
                   "first": st.first == st.active, "sit": situation(st, st.active), "could": False,
                   "board_prev": None if prev_end[st.active] is None else cut(prev_end[st.active], 5),
                   "evolved": False, "points": p.ep + p.sep}
        if cur is not None and st.active == cur["seat"] and not cur["could"]:
            cur["could"] = any(isinstance(x, Evolve) for x in legal_actions(st))
        if isinstance(a, Evolve):
            cur["evolved"] = True
        apply(st, a)
        if st.over:
            if cur["seat"] in seats and st.winner != cur["seat"]:
                out.append(cur)
            cur = None
            break
    if cur is not None and cur["seat"] in seats:
        out.append(cur)
    rows = []
    for t in out:
        if not (t["could"] or t["evolved"]):
            continue
        unlock = 5 if t["first"] else 4
        rows.append({"seat": t["seat"], "own_turn": t["own_turn"], "life": t["sit"][0], "board": t["sit"][1],
                     "hand": t["sit"][2], "board_prev": t["board_prev"],
                     "evolved": t["evolved"], "points": t["points"],
                     "first_point_at_unlock": t["evolved"] and t["own_turn"] == unlock and t["points"] == 4})
    return rows


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salem", default=None)
    ap.add_argument("--selfplay", nargs=2, action="append", default=[], metavar=("LABEL", "FILE"))
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    groups = []
    if args.salem:
        data = json.load(open(args.salem, encoding="utf-8"))
        salem, bots = [], defaultdict(list)
        for gid, rec in data["records"].items():
            meta = data.get("meta", {}).get(gid, {})
            for r in turns(rec, (0, 1)):
                (salem if r["seat"] == 0 else bots[meta.get("version") or "旧网页 bot"]).append(r)
        groups.append(("Salem", salem))
        for k, v in bots.items():
            groups.append((f"{k}（对 Salem）", v))
    for label, path in args.selfplay:
        groups.append((label, [r for line in lines_of(path) for r in turns(json.loads(line), (0, 1))]))
    for axis, title in (("life", "按血量差"), ("board", "按场面差（回合开头）"), ("board_prev", "按场面差（自己上回合结束时）"),
                        ("hand", "按手牌数差（±2）")):
        print(f"\n能进化的回合里没进化的比例，{title}（领先 / 均势 / 落后）")
        for label, rows in groups:
            cells = []
            for s in ("领先", "均势", "落后"):
                sub = [r for r in rows if r[axis] == s]
                k = sum(not r["evolved"] for r in sub)
                lo, hi = wilson(k, len(sub))
                cells.append(f"{s} {k}/{len(sub)} {k / len(sub) if sub else float('nan'):.0%}（{lo:.0%}～{hi:.0%}）")
            print(f"  {label:<22}" + "  ".join(cells))
        print(f"\n第一个点在解锁当回合就用掉的回合，{title}的分布")
        for label, rows in groups:
            sub = [r for r in rows if r["first_point_at_unlock"]]
            dist = {s: sum(r[axis] == s for r in sub) for s in ("领先", "均势", "落后")}
            print(f"  {label:<22}{len(sub)} 次：" + "  ".join(f"{s} {n}" for s, n in dist.items()))
    print("\n能进化的回合里没进化的比例，血量差 × 自己的回合段（4～6 / 7～9 / 10+）")
    seg = lambda t: "4～6" if t <= 6 else "7～9" if t <= 9 else "10+"
    for label, rows in groups:
        cells = []
        for s in ("领先", "均势", "落后"):
            for g in ("4～6", "7～9", "10+"):
                sub = [r for r in rows if r["life"] == s and seg(r["own_turn"]) == g]
                k = sum(not r["evolved"] for r in sub)
                cells.append(f"{s}{g} {k}/{len(sub)}")
        print(f"  {label:<22}" + "  ".join(cells))
    if args.json:
        json.dump({label: rows for label, rows in groups}, open(args.json, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
