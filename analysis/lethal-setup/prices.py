"""M5 (README-m5.md here): the price of resources under three labels on step 1's pairs. For every unmerged plan c
against the bot's plan on a start: the regressors are the mean over the plan's 16 T turn ends (end-of-turn abilities
resolved, the opponent not yet acting) minus the bot's, five resources (EP left, SEP left, max PP, PP left, hand size)
and board / HP / amulet controls; the labels dG_end (WLS by the paired games K; appendix 3's extra games merged), dT,
and the installed ENDED model's dV on the same 16 turn ends; one design for all three, through the origin; intervals
by resampling starts (2000, seed 0). Condition: the opponent's deck list is known (order and hand not).

    python3 prices.py <step 1 dir> <gendmore.jsonl> --out prices.txt [--rows pairs.jsonl]
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "turn-level"))
sys.path.insert(0, os.path.join(HERE, "..", "card-value"))

RES = ("ep", "sep", "max_pp", "pp_left", "hand")
CTRL = ("enemy_hp", "own_hp", "own_followers", "own_stats", "enemy_followers", "enemy_stats", "own_amulets",
        "enemy_amulets")
NAMES = {"ep": "剩余 EP", "sep": "剩余 SEP", "max_pp": "最大 PP", "pp_left": "剩余 PP", "hand": "手牌张数"}


def features(st, me):
    mine, opp = st.players[me], st.players[1 - me]

    def board(p):
        fol = [c for c in p.field if c.defn.is_follower]
        return len(fol), sum(c.atk + max(c.life, 0) for c in fol), sum(1 for c in p.field if c.defn.is_amulet)
    of, os_, oa = board(mine)
    ef, es, ea = board(opp)
    return {"ep": mine.ep, "sep": mine.sep, "max_pp": mine.max_pp, "pp_left": mine.pp, "hand": len(mine.hand),
            "enemy_hp": opp.leader_hp, "own_hp": mine.leader_hp, "own_followers": of, "own_stats": os_,
            "enemy_followers": ef, "enemy_stats": es, "own_amulets": oa, "enemy_amulets": ea}


def build_pairs(d, gendmore):
    import step1
    import student_data as SD
    import teacher_ends as TEN
    W = step1._weights({"i": "v2s"})["i"]
    order = {r["k"]: [p["kind"] for p in r["plans"]] for r in SD._lines(os.path.join(d, "plans.jsonl"))}
    split = {r["k"]: r["split"] for r in SD._lines(os.path.join(d, "starts.jsonl"))}
    T = {}
    for r in SD._lines(os.path.join(d, "teacher.jsonl")):
        for kind, v in r["values"].items():
            T.setdefault((r["k"], kind), []).extend(v)
    G = {r["k"]: r["results"] for r in SD._lines(os.path.join(d, "gend.jsonl"))}
    for r in SD._lines(gendmore):
        G[r["k"]] = {c: v + r["results"].get(c, []) for c, v in G[r["k"]].items()}
    sums = {}
    starts_ = TEN.Starts(os.path.join(d, "selfplay.jsonl"))
    for row in TEN.rows(os.path.join(d, "teacher_ends.jsonl.gz")):
        st = TEN.turn_end(row, starts_, end_of_turn=True)
        f = features(st, row["seat"])
        f["v"] = step1._win(st, row["seat"], W)
        acc = sums.setdefault((row["n"], row["r"]), {"n": 0})
        acc["n"] += 1
        for key, val in f.items():
            acc[key] = acc.get(key, 0.0) + val
    mean = {key: {f: v / acc["n"] for f, v in acc.items() if f != "n"} for key, acc in sums.items()}
    pairs = []
    for k, kinds in order.items():
        if (k, "bot") not in mean:
            continue
        b = mean[(k, "bot")]
        for c in kinds:
            if c == "bot" or (k, c) not in mean:
                continue
            m = mean[(k, c)]
            g = [x - y for x, y in zip(G[k][c], G[k]["bot"])]
            pairs.append({"k": k, "split": split[k], "kind": c.split(":")[0],
                          "x": {f: m[f] - b[f] for f in RES + CTRL},
                          "dT": 100 * (sum(T[(k, c)]) / len(T[(k, c)]) - sum(T[(k, "bot")]) / len(T[(k, "bot")])),
                          "dV": 100 * (m["v"] - b["v"]), "dG": 100 * sum(g) / len(g), "K": len(g)})
    return pairs


def fit(pairs, label, weighted):
    import numpy as np
    X = np.array([[p["x"][f] for f in RES + CTRL] for p in pairs])
    y = np.array([p[label] for p in pairs])
    if weighted:
        w = np.sqrt(np.array([p["K"] for p in pairs], dtype=float))
        X, y = X * w[:, None], y * w
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta[:len(RES)]


def report(pairs, title, out):
    import numpy as np
    from collections import defaultdict
    by = defaultdict(list)
    for p in pairs:
        by[p["k"]].append(p)
    ks = sorted(by)
    est = {lab: fit(pairs, lab, lab == "dG") for lab in ("dG", "dT", "dV")}
    rng = np.random.default_rng(0)
    boots = {lab: [] for lab in est}
    for _ in range(2000):
        sel = [p for i in rng.integers(0, len(ks), len(ks)) for p in by[ks[i]]]
        for lab in est:
            boots[lab].append(fit(sel, lab, lab == "dG"))
    B = {lab: np.array(v) for lab, v in boots.items()}
    ci = lambda a: (np.percentile(a, 2.5), np.percentile(a, 97.5))   # noqa: E731
    out.append(f"\n**{title}**：{len(pairs)} 对、{len(ks)} 个开头（价格：每多一单位，胜率百分点）\n")
    out.append("| 资源 | 不为 0 的对 / |差| ≥ 0.5 的对 | (a) G_end | (b) T | (c) 现装模型 | (a) − (c) | (b) − (c) |")
    out.append("|---|---|---|---|---|---|---|")
    res = {}
    for i, f in enumerate(RES):
        nz = sum(1 for p in pairs if abs(p["x"][f]) > 1e-9)
        big = sum(1 for p in pairs if abs(p["x"][f]) >= 0.5)
        cells = []
        for lab in ("dG", "dT", "dV"):
            lo, hi = ci(B[lab][:, i])
            cells.append(f"{est[lab][i]:+.2f}（{lo:+.2f}～{hi:+.2f}）")
        dac = B["dG"][:, i] - B["dV"][:, i]
        dbc = B["dT"][:, i] - B["dV"][:, i]
        (alo, ahi), (blo, bhi) = ci(dac), ci(dbc)
        rare = " 太少" if big < 30 else ""
        out.append(f"| {NAMES[f]}{rare} | {nz} / {big} | " + " | ".join(cells)
                   + f" | {est['dG'][i] - est['dV'][i]:+.2f}（{alo:+.2f}～{ahi:+.2f}） | "
                   f"{est['dT'][i] - est['dV'][i]:+.2f}（{blo:+.2f}～{bhi:+.2f}） |")
        res[f] = {"a": est["dG"][i], "b": est["dT"][i], "c": est["dV"][i], "ac": (alo, ahi), "bc": (blo, bhi),
                  "rare": big < 30}
    corr = np.corrcoef(np.array([[p["x"][f] for f in RES] for p in pairs]).T)
    out.append("\n五个资源差的相关：")
    out.append("| | " + " | ".join(NAMES[f] for f in RES) + " |")
    out.append("|---|" + "---|" * len(RES))
    for i, f in enumerate(RES):
        out.append(f"| {NAMES[f]} | " + " | ".join(f"{corr[i, j]:+.2f}" for j in range(len(RES))) + " |")
    return res


def judge(res, out):
    out.append("\n**判断**（主读数，不含 end）")
    for f, j in (("ep", "J37"), ("max_pp", "J38")):
        r = res[f]
        ok = r["ac"][0] > 0
        out.append(f"- **{j}**（{NAMES[f]}：G_end 的价格高于现装模型，(a) − (c) 的区间不含 0）→ "
                   + ("不读（太少）" if r["rare"] else ("对" if ok else "错")))
    parts = []
    for f in ("ep", "max_pp"):
        r = res[f]
        between = min(r["a"], r["c"]) <= r["b"] <= max(r["a"], r["c"])
        at_model = r["bc"][0] <= 0 <= r["bc"][1]
        parts.append(between or at_model)
    out.append(f"- **J39**（EP 和最大 PP 两样都是 T 落在模型和 G_end 之间、或就在模型那里）→ {'对' if all(parts) else '错'}"
               f"（EP {'是' if parts[0] else '否'}，最大 PP {'是' if parts[1] else '否'}）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step1")
    ap.add_argument("gendmore")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rows", default=None, help="write the pairs here (and read them from here if it exists)")
    args = ap.parse_args()
    if args.rows and os.path.exists(args.rows):
        pairs = [json.loads(x) for x in open(args.rows, encoding="utf-8") if x.strip()]
    else:
        pairs = build_pairs(args.step1, args.gendmore)
        if args.rows:
            with open(args.rows, "w", encoding="utf-8") as fh:
                for p in pairs:
                    fh.write(json.dumps(p) + "\n")
    out = ["条件：对手卡表已知（牌序、手牌未知）。M5：资源在三把尺子下的价格"]
    main_pairs = [p for p in pairs if p["kind"] != "end"]
    res = report(main_pairs, "不含 end（主读数）", out)
    report(pairs, "含 end", out)
    judge(res, out)
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
