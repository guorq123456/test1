"""M3 (README.md here): the direction of the turns where Salem's line differs from level-strong's. The 85 stage-0 turns
where his line is a candidate of its own (turn-level step 0, RC 84d735e), both turn ends rebuilt on the real start;
the Salem - bot differences in generic fields only, a class by the rule fixed beforehand, and per class the share
where T and G_end favour Salem (as step 0 counted them). Descriptive, no judgement. Condition: the opponent's deck list
is known (order and hand not).

    python3 direction.py m3 <step 0 data folder> --out m3_rows.jsonl [--m2 m2_rows.jsonl]
"""
import argparse
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import setup_prob as SP          # noqa: E402  (the step-0 starts, the lines' replay)
import turn_level as TL          # noqa: E402

FIELDS = ("enemy_hp", "enemy_followers", "enemy_stats", "enemy_amulets", "own_followers", "own_stats",
          "own_amulets", "hand", "pp_left", "ep", "sep", "shadows", "evolutions", "own_countdowns", "leader_area")


def snapshot(state, actions):
    """The fields at a turn end: pp_left just before the turn's EndTurn, the rest once the end-of-turn abilities
    have resolved (search.evaluate.after_end_of_turn), the opponent's turn not started."""
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply
    from svsim.search.evaluate import after_end_of_turn
    s = state.clone()
    me = s.active
    for a in actions:
        a = from_dict(a) if isinstance(a, dict) else a
        if isinstance(a, EndTurn):
            break
        apply(s, a)
        if s.over:
            break
    pp_left = s.players[me].pp
    end = s if s.over else after_end_of_turn(s)
    mine, theirs = end.players[me], end.players[1 - me]

    def board(p):
        fol = [c for c in p.field if c.defn.is_follower]
        return len(fol), sum(c.atk + c.life for c in fol), sum(1 for c in p.field if c.defn.is_amulet)
    ef, es, ea = board(theirs)
    of, os_, oa = board(mine)
    return {"enemy_hp": theirs.leader_hp, "enemy_followers": ef, "enemy_stats": es, "enemy_amulets": ea,
            "own_followers": of, "own_stats": os_, "own_amulets": oa, "hand": len(mine.hand), "pp_left": pp_left,
            "ep": mine.ep, "sep": mine.sep, "shadows": mine.shadows, "evolutions": mine.evolutions,
            "own_countdowns": sum(c.countdown or 0 for c in mine.field if c.defn.is_amulet),
            "leader_area": len(mine.leader_area), "over": end.over}


def classify(d, d_pnl=None):
    """The rule fixed beforehand (README M3): what Salem's line did more of."""
    hits = []
    if d["enemy_hp"] <= -2:
        hits.append("race")
    if d["enemy_stats"] <= -3 or d["enemy_followers"] <= -1:
        hits.append("clear")
    if d["own_stats"] >= 3 or d["own_followers"] >= 1:
        hits.append("develop")
    if d["hand"] >= 1 or d["pp_left"] >= 2 or d["ep"] >= 1 or d["sep"] >= 1:
        hits.append("conserve")
    if d_pnl is not None and d_pnl >= 0.125:
        hits.append("setup")
    return (hits[0] if len(hits) == 1 else "mixed" if hits else "small"), hits


def m3(args):
    from collections import Counter, defaultdict
    TL.REC.update(TL._records(os.path.join(args.step0, "selfplay.jsonl")))
    starts, plans = SP._starts(args.step0)
    T = defaultdict(lambda: defaultdict(list))
    for r in SP._lines(os.path.join(args.step0, "teacher.jsonl")):
        for kind, v in r["values"].items():
            T[r["k"]][kind] += v
    G = {r["k"]: r["results"] for r in SP._lines(os.path.join(args.step0, "gend.jsonl"))}
    pnl = {}
    if args.m2:
        for r in SP._lines(args.m2):
            if r["salem"] is not None and r["bot"] is not None:
                pnl[r["k"]] = r["salem"] - r["bot"]
    rows = []
    for st in starts:
        k = st["k"]
        kinds = [p["kind"] for p in plans[k]["plans"]]
        if "salem" not in kinds or k not in G or "salem" not in G[k]:
            continue
        state, rec = TL._start_state(st)
        salem = TL._salem_turn(rec, st["at"])
        bot = next(p for p in plans[k]["plans"] if p["kind"] == "bot")["actions"]
        a, b = snapshot(state, salem), snapshot(state, bot)
        d = {f: a[f] - b[f] for f in FIELDS}
        cls, hits = classify(d)
        mean = statistics.mean
        t_fav = mean(T[k]["salem"]) > mean(T[k]["bot"])
        gs, gb = mean(G[k]["salem"]), mean(G[k]["bot"])
        row = {"k": k, "own_turn": st["own_turn"], "diff": d, "class": cls, "hits": hits, "t_favours_salem": t_fav,
               "g_favours_salem": 1.0 if gs > gb else 0.5 if gs == gb else 0.0, "salem_over": a["over"],
               "bot_over": b["over"]}
        if k in pnl:
            row["d_pnl"] = pnl[k]
            row["class_setup"], row["hits_setup"] = classify(d, pnl[k])
        rows.append(row)
    with open(args.out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print("条件：对手卡表已知（牌序、手牌未知）。M3：Salem 和 bot 打法不同的回合，往哪个方向走\n")
    print(f"- 开头 {len(rows)} 个（第 0 步 Salem 的线自成候选、有 G_end 的）")

    def table(key, hits_key):
        cnt = Counter(r[key] for r in rows if key in r)
        order = ["race", "clear", "develop", "conserve", "setup", "mixed", "small"]
        print("\n| 类 | 个数 | T 偏向 Salem | G_end 偏向 Salem |\n|---|---|---|---|")
        for c in order:
            sel = [r for r in rows if r.get(key) == c]
            if not sel:
                continue
            t = statistics.mean(float(r["t_favours_salem"]) for r in sel)
            g = statistics.mean(r["g_favours_salem"] for r in sel)
            print(f"| {c} | {len(sel)} | {t:.1%} | {g:.1%} |")
        sel = [r for r in rows if key in r]
        print(f"| 全部 | {len(sel)} | {statistics.mean(float(r['t_favours_salem']) for r in sel):.1%} | "
              f"{statistics.mean(r['g_favours_salem'] for r in sel):.1%} |")
        combos = Counter("+".join(r[hits_key]) for r in rows if r.get(key) == "mixed")
        if combos:
            print("- mixed 的组合：" + "、".join(f"{c} {n}" for c, n in combos.most_common()))
    print("\n**归类（不含 setup）**")
    table("class", "hits")
    if pnl:
        print("\n**归类（加上 setup，M2 的 P_NL 差 ≥ 0.125）**")
        table("class_setup", "hits_setup")
    print("\n**各字段的差（Salem − bot）**：平均 / 中位 / 非零的个数")
    for f in FIELDS:
        v = [r["diff"][f] for r in rows]
        print(f"- {f}：{statistics.mean(v):+.2f} / {statistics.median(v):+.1f} / {sum(1 for x in v if x)}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("m3")
    a.add_argument("step0")
    a.add_argument("--out", required=True)
    a.add_argument("--m2", default=None, help="M2's rows (setup_prob.py run): adds the setup class")
    args = ap.parse_args()
    {"m3": m3}[args.cmd](args)


if __name__ == "__main__":
    main()
