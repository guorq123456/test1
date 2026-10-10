"""The candidate's own prices and its dT-sign agreement, before any gate (the architecture thread 07:18Z, step 3).
Condition: the opponent's deck list is known (order and hand not).

Exactly M5's column (c) (the analysis line's prices.py, 533a6aa), for several evaluators at once:
- every plan's 16 T turn ends of step 1 are rebuilt (teacher_ends.turn_end, end_of_turn=True);
- for each plan, its M5 regressors (prices.features) and each evaluator's win probability (step1._win with the
  evaluator's search weights) are averaged; a pair is a plan against the bot's plan of the same start (end pairs
  out for the main read);
- the prices are prices.fit's regression of 100 x dV on the regressors, through the origin.
Read on the held-out starts (the main check) and the training starts; G_end (WLS on K, appendix 3's extra games
merged) and T on the same pairs for reference. dT-sign agreement: the share of pairs (dT != 0) where dV has dT's
sign. Intervals: 2000 resamples of starts, seed 0.

    python3 check_h.py STEP1_DIR GENDMORE ANA_DIR --out rows.jsonl [--workers 4] [--eval name=spec ...]
    python3 check_h.py --read rows.jsonl
"""
import argparse
import json
import os
import sys
from collections import defaultdict

EVALS = {"installed": "level-strong",
         "cand-tl": "mcts:200+plan+learned+phased=cand-tl-ramp-ramp",
         "cand-th": "mcts:200+plan+learned+phased=cand-th-ramp-ramp"}
RES = ("ep", "sep", "max_pp", "pp_left", "hand")
CTRL = ("enemy_hp", "own_hp", "own_followers", "own_stats", "enemy_followers", "enemy_stats", "own_amulets",
        "enemy_amulets")
G = {}


def _paths(ana):
    for sub in ("lethal-setup", "turn-level", "card-value"):
        p = os.path.join(ana, sub)
        if p not in sys.path:
            sys.path.insert(0, p)


def _init(d, ana, evals):
    _paths(ana)
    import step1
    import teacher_ends as TEN
    G["W"] = step1._weights(evals)
    G["starts"] = TEN.Starts(os.path.join(d, "selfplay.jsonl"))


def _job(rows):
    import prices
    import step1
    import teacher_ends as TEN
    out = []
    for row in rows:
        st = TEN.turn_end(row, G["starts"], end_of_turn=True)
        f = prices.features(st, row["seat"])
        for e, W in G["W"].items():
            f["v_" + e] = step1._win(st, row["seat"], W)
        out.append(((row["n"], row["r"]), f))
    return out


def run(args):
    from multiprocessing import Pool
    _paths(args.ana)
    import student_data as SD
    import teacher_ends as TEN
    evals = dict(EVALS)
    for e in args.eval or []:
        name, spec = e.split("=", 1)
        evals[name] = spec
    batches, cur = [], []
    for row in TEN.rows(os.path.join(args.step1, "teacher_ends.jsonl.gz")):
        cur.append(row)
        if len(cur) == 64:
            batches.append(cur)
            cur = []
    if cur:
        batches.append(cur)
    sums = {}
    with Pool(args.workers, initializer=_init, initargs=(args.step1, args.ana, evals)) as pool:
        for part in pool.imap_unordered(_job, batches):
            for key, f in part:
                acc = sums.setdefault(key, {"n": 0})
                acc["n"] += 1
                for k, v in f.items():
                    acc[k] = acc.get(k, 0.0) + v
    mean = {key: {f: v / acc["n"] for f, v in acc.items() if f != "n"} for key, acc in sums.items()}
    order = {r["k"]: [p["kind"] for p in r["plans"]] for r in SD._lines(os.path.join(args.step1, "plans.jsonl"))}
    split = {r["k"]: r["split"] for r in SD._lines(os.path.join(args.step1, "starts.jsonl"))}
    T = {}
    for r in SD._lines(os.path.join(args.step1, "teacher.jsonl")):
        for kind, v in r["values"].items():
            T.setdefault((r["k"], kind), []).extend(v)
    Gd = {r["k"]: r["results"] for r in SD._lines(os.path.join(args.step1, "gend.jsonl"))}
    for r in SD._lines(args.gendmore):
        Gd[r["k"]] = {c: v + r["results"].get(c, []) for c, v in Gd[r["k"]].items()}
    with open(args.out, "w", encoding="utf-8") as fh:
        for k, kinds in order.items():
            if (k, "bot") not in mean:
                continue
            b = mean[(k, "bot")]
            for c in kinds:
                if c == "bot" or (k, c) not in mean:
                    continue
                m = mean[(k, c)]
                g = [x - y for x, y in zip(Gd[k][c], Gd[k]["bot"])]
                row = {"k": k, "split": split[k], "kind": c.split(":")[0], "plan": c,
                       "x": {f: m[f] - b[f] for f in RES + CTRL},
                       "dT": 100 * (sum(T[(k, c)]) / len(T[(k, c)]) - sum(T[(k, "bot")]) / len(T[(k, "bot")])),
                       "dG": 100 * sum(g) / len(g), "K": len(g),
                       "dV": {e: 100 * (m["v_" + e] - b["v_" + e]) for e in evals}}
                fh.write(json.dumps(row) + "\n")


def _fit(pairs, y, weights=None):
    import numpy as np
    X = np.array([[p["x"][f] for f in RES + CTRL] for p in pairs])
    y = np.asarray(y, float)
    if weights is not None:
        w = np.sqrt(np.asarray(weights, float))
        X, y = X * w[:, None], y * w
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta[:len(RES)]


def read(args):
    import numpy as np
    rows = [json.loads(x) for x in open(args.read) if x.strip()]
    evals = list(rows[0]["dV"])
    print("条件：对手卡表已知（牌序、手牌未知）。候选的价格和 ΔT 同号率（M5 的 (c) 列，同一回归）\n")
    for split in ("val", "train"):
        pairs = [p for p in rows if p["split"] == split and p["kind"] != "end"]
        by = defaultdict(list)
        for p in pairs:
            by[p["k"]].append(p)
        ks = sorted(by)

        def est(sel):
            out = {"G_end": _fit(sel, [p["dG"] for p in sel], [p["K"] for p in sel]),
                   "T": _fit(sel, [p["dT"] for p in sel])}
            for e in evals:
                out[e] = _fit(sel, [p["dV"][e] for p in sel])
            return out

        def agree(sel, e, against="dT"):
            s = [p for p in sel if p[against] != 0]
            return sum(1 for p in s if np.sign(p["dV"][e]) == np.sign(p[against])) / len(s)
        E = est(pairs)
        rng = np.random.default_rng(0)
        boot = defaultdict(list)
        for _ in range(2000):
            sel = [p for i in rng.integers(0, len(ks), len(ks)) for p in by[ks[i]]]
            b = est(sel)
            for e in b:
                boot[e].append(b[e])
            for e in evals:
                boot["agree_" + e].append(agree(sel, e) - agree(sel, "installed"))
        B = {e: np.array(v) for e, v in boot.items()}
        ci = lambda a: (np.percentile(a, 2.5), np.percentile(a, 97.5))   # noqa: E731
        title = "留出开头" if split == "val" else "训练开头"
        print(f"**{title}**：{len(pairs)} 对、{len(ks)} 个开头，不含 end（价格：每多一单位，胜率百分点）\n")
        print("| 资源 | G_end | T | " + " | ".join(evals) + " | " + " | ".join(f"{e} − installed" for e in evals if e != "installed")
              + " |\n|---|---|---|" + "---|" * len(evals) + "---|" * (len(evals) - 1))
        for i, f in enumerate(RES):
            cells = [f"{E['G_end'][i]:+.2f}", f"{E['T'][i]:+.2f}"] + [f"{E[e][i]:+.2f}" for e in evals]
            for e in evals:
                if e == "installed":
                    continue
                lo, hi = ci(B[e][:, i] - B["installed"][:, i])
                cells.append(f"{E[e][i] - E['installed'][i]:+.2f}（{lo:+.2f}～{hi:+.2f}）")
            print(f"| {f} | " + " | ".join(cells) + " |")
        print("\n| 评估器 | ΔT 同号率 | 比 installed（区间） | ΔG_end 同号率 |\n|---|---|---|---|")
        for e in evals:
            lo, hi = ci(B["agree_" + e])
            print(f"| {e} | {agree(pairs, e):.2%} | {agree(pairs, e) - agree(pairs, 'installed'):+.2%}（{lo:+.2%}～{hi:+.2%}） | "
                  f"{agree(pairs, e, 'dG'):.2%} |")
        print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step1", nargs="?")
    ap.add_argument("gendmore", nargs="?")
    ap.add_argument("ana", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--eval", nargs="*")
    ap.add_argument("--read")
    args = ap.parse_args()
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    read(args) if args.read else run(args)


if __name__ == "__main__":
    main()
