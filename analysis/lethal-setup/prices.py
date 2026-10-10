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


def fit(pairs, label, weighted, full=False):
    import numpy as np
    X = np.array([[p["x"][f] for f in RES + CTRL] for p in pairs])
    y = np.array([p[label] for p in pairs])
    if weighted:
        w = np.sqrt(np.array([p["K"] for p in pairs], dtype=float))
        X, y = X * w[:, None], y * w
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta if full else beta[:len(RES)]


CNAMES = {"enemy_hp": "对手 HP", "own_hp": "我方 HP", "own_followers": "我方随从张数", "own_stats": "我方随从属性和",
          "enemy_followers": "对手随从张数", "enemy_stats": "对手随从属性和", "own_amulets": "我方护符张数",
          "enemy_amulets": "对手护符张数"}


def report_controls(pairs, title, out):
    """The control coefficients of the same regressions (architecture thread 07:18Z follow-up), with intervals."""
    import numpy as np
    from collections import defaultdict
    by = defaultdict(list)
    for p in pairs:
        by[p["k"]].append(p)
    ks = sorted(by)
    est = {lab: fit(pairs, lab, lab == "dG", True) for lab in ("dG", "dT", "dV")}
    rng = np.random.default_rng(0)
    B = {lab: [] for lab in est}
    for _ in range(2000):
        sel = [p for i in rng.integers(0, len(ks), len(ks)) for p in by[ks[i]]]
        for lab in est:
            B[lab].append(fit(sel, lab, lab == "dG", True))
    B = {lab: np.array(v) for lab, v in B.items()}
    ci = lambda a: (np.percentile(a, 2.5), np.percentile(a, 97.5))   # noqa: E731
    out.append(f"\n**控制项的系数，{title}**：{len(pairs)} 对（每多一单位，胜率百分点）\n")
    out.append("| 量 | 不为 0 的对 | (a) G_end | (b) T | (c) 现装模型 | (a) − (c) | (b) − (c) |")
    out.append("|---|---|---|---|---|---|---|")
    for i, f in enumerate(RES + CTRL):
        if f in RES:
            continue
        nz = sum(1 for p in pairs if abs(p["x"][f]) > 1e-9)
        cells = []
        for lab in ("dG", "dT", "dV"):
            lo, hi = ci(B[lab][:, i])
            cells.append(f"{est[lab][i]:+.2f}（{lo:+.2f}～{hi:+.2f}）")
        (alo, ahi), (blo, bhi) = ci(B["dG"][:, i] - B["dV"][:, i]), ci(B["dT"][:, i] - B["dV"][:, i])
        out.append(f"| {CNAMES[f]} | {nz} | " + " | ".join(cells)
                   + f" | {est['dG'][i] - est['dV'][i]:+.2f}（{alo:+.2f}～{ahi:+.2f}） | "
                   f"{est['dT'][i] - est['dV'][i]:+.2f}（{blo:+.2f}～{bhi:+.2f}） |")


def halves(pairs, games, out_json):
    """Per-half prices for cross-fitted labels: training starts only (held-out starts kept out), end out, the
    halves by the start's game parity (game % 2, so a game's starts stay together); G_end (WLS by K) and T prices
    of all five resources on each half, and on all training starts."""
    sel = [p for p in pairs if p["split"] == "train" and p["kind"] != "end"]
    out = {"rule": "half = game % 2 of the start (step 1 starts.jsonl); training starts only; end plans out; "
                   "price per unit in win points; the label's own half should use the OTHER half's prices",
           "resources": list(RES), "halves": {}}
    for name, part in (("0", [p for p in sel if games[p["k"]] % 2 == 0]),
                       ("1", [p for p in sel if games[p["k"]] % 2 == 1]), ("all", sel)):
        bg, bt, bv = fit(part, "dG", True), fit(part, "dT", False), fit(part, "dV", False)
        out["halves"][name] = {"pairs": len(part), "starts": len({p["k"] for p in part}),
                               "G_end": dict(zip(RES, map(float, bg))), "T": dict(zip(RES, map(float, bt))),
                               "model": dict(zip(RES, map(float, bv)))}
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    return out


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


def pregate(d, cand_spec, installed, out):
    """The horizon-corrected candidate's pre-gate check (README-horizon.md): on step 1's held-out starts (end out),
    (1) the candidate's max-PP and hand prices (its dV regressed on the M5 design) against the installed model's:
    both must be higher (G_end prices both above the model); (2) the share of pairs whose dV has dT's sign (dT = 0
    left out, dV = 0 counted half): the candidate's may be at most 1 point below the installed model's."""
    import numpy as np
    import step1
    import student_data as SD
    import teacher_ends as TEN
    W = step1._weights({"inst": installed, "cand": cand_spec})
    order = {r["k"]: [p["kind"] for p in r["plans"]] for r in SD._lines(os.path.join(d, "plans.jsonl"))}
    val = {r["k"] for r in SD._lines(os.path.join(d, "starts.jsonl")) if r["split"] == "val"}
    T = {}
    for r in SD._lines(os.path.join(d, "teacher.jsonl")):
        if r["k"] in val:
            for kind, v in r["values"].items():
                T.setdefault((r["k"], kind), []).extend(v)
    sums = {}
    starts_ = TEN.Starts(os.path.join(d, "selfplay.jsonl"))
    for row in TEN.rows(os.path.join(d, "teacher_ends.jsonl.gz")):
        if row["n"] not in val:
            continue
        st = TEN.turn_end(row, starts_, end_of_turn=True)
        f = features(st, row["seat"])
        f["v_inst"], f["v_cand"] = step1._win(st, row["seat"], W["inst"]), step1._win(st, row["seat"], W["cand"])
        acc = sums.setdefault((row["n"], row["r"]), {"n": 0})
        acc["n"] += 1
        for key, v in f.items():
            acc[key] = acc.get(key, 0.0) + v
    mean = {key: {f: v / acc["n"] for f, v in acc.items() if f != "n"} for key, acc in sums.items()}
    pairs = []
    for k in sorted(val):
        if (k, "bot") not in mean:
            continue
        b = mean[(k, "bot")]
        for c in order[k]:
            if c == "bot" or c.split(":")[0] == "end" or (k, c) not in mean:
                continue
            m = mean[(k, c)]
            pairs.append({"k": k, "x": {f: m[f] - b[f] for f in RES + CTRL},
                          "dT": 100 * (np.mean(T[(k, c)]) - np.mean(T[(k, "bot")])),
                          "dV": 100 * (m["v_inst"] - b["v_inst"]), "dC": 100 * (m["v_cand"] - b["v_cand"])})
    bi, bc = fit(pairs, "dV", False), fit(pairs, "dC", False)

    def agree(key):
        sel = [p for p in pairs if abs(p["dT"]) > 1e-12]
        return np.mean([1.0 if p[key] * p["dT"] > 0 else 0.5 if abs(p[key]) < 1e-12 else 0.0 for p in sel]), len(sel)
    ai, n = agree("dV")
    ac, _ = agree("dC")
    mp, hd = RES.index("max_pp"), RES.index("hand")
    ok1 = bc[mp] > bi[mp] and bc[hd] > bi[hd]
    ok2 = 100 * (ac - ai) >= -1.0
    out.append("条件：对手卡表已知（牌序、手牌未知）。视野修正标签的候选：开门前的检查（留出开头，不含 end）\n")
    out.append(f"- 留出开头的对子 {len(pairs)} 个；候选 `{cand_spec}`，现装 `{installed}`")
    out.append("- 价格（每多一单位，胜率百分点；候选 / 现装）：" + "；".join(
        f"{NAMES[f]} {bc[i]:+.2f} / {bi[i]:+.2f}" for i, f in enumerate(RES)))
    out.append(f"- (1) 最大 PP 和手牌的价格都往 G_end 那边动（候选高于现装）：{'是' if ok1 else '否'}")
    out.append(f"- (2) 和 ΔT 同号的比例（{n} 对）：候选 {ac:.1%}、现装 {ai:.1%}，差 {100 * (ac - ai):+.1f} 个百分点；"
               f"不低于 −1：{'是' if ok2 else '否'}")
    out.append(f"- **开门**：{'开' if ok1 and ok2 else '不开'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step1")
    ap.add_argument("gendmore")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rows", default=None, help="write the pairs here (and read them from here if it exists)")
    ap.add_argument("--controls", action="store_true", help="also report the control coefficients")
    ap.add_argument("--halves", default=None, help="write per-half prices (training starts, game % 2) to this JSON")
    ap.add_argument("--pregate", default=None, help="the horizon-corrected candidate's spec: run the pre-gate check only")
    ap.add_argument("--installed", default="v2s")
    args = ap.parse_args()
    if args.pregate:
        out = []
        pregate(args.step1, args.pregate, args.installed, out)
        open(args.out, "w", encoding="utf-8").write("\n".join(out) + "\n")
        print("\n".join(out))
        return
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
    if args.controls:
        report_controls(main_pairs, "不含 end（主读数）", out)
    if args.halves:
        games = {json.loads(x)["k"]: json.loads(x)["game"]
                 for x in open(os.path.join(args.step1, "starts.jsonl"), encoding="utf-8") if x.strip()}
        h = halves(pairs, games, args.halves)
        out.append("\n**按半分的价格**（训练开头、不含 end、按局号奇偶分两半；写进 " + os.path.basename(args.halves) + "）\n")
        out.append("| 半 | 对 / 开头 | 尺子 | " + " | ".join(NAMES[f] for f in RES) + " |")
        out.append("|---|---|---|" + "---|" * len(RES))
        for name, v in h["halves"].items():
            for lab, key in (("G_end", "G_end"), ("T", "T"), ("模型", "model")):
                out.append(f"| {name} | {v['pairs']} / {v['starts']} | {lab} | "
                           + " | ".join(f"{v[key][f]:+.2f}" for f in RES) + " |")
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
