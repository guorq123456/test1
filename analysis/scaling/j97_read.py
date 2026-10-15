"""J97 (README, generation 2): how net-10000 does on the turn ends of the games it played itself (generation 2, D1's
agent) against the held-out v2skx games. Per position, from the side that just ended the turn: bias = mean(p) - mean
(result), Brier, log-loss; the same for the installed linear evaluator (raw sigma(logit), and recalibrated as in
holdout_read.py). 95% intervals from 2000 resamples of whole games (numpy default_rng(0)); the gen-2 - holdout
differences resample the two sets independently (different games). Turn buckets by the turn just ended.
Condition: the opponent's deck list is known (order and hand not).

    python3 j97_read.py --gen2 net_logit-gen2.npz --holdout-net holdout-net-10000.npz --holdout-linear holdout-linear.npz \
        --calib train_k0_logits.jsonl --out read_j97.txt
"""
import argparse
import json

import numpy as np

from holdout_read import fit1d


def sig(x):
    return 1 / (1 + np.exp(-x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen2", required=True)
    ap.add_argument("--holdout-net", required=True)
    ap.add_argument("--holdout-linear", required=True)
    ap.add_argument("--calib", required=True)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cal = [json.loads(l) for l in open(args.calib, encoding="utf-8") if l.strip()]
    a, b = fit1d(np.array([r["x"] for r in cal]), np.array([r["y"] for r in cal]))

    g2 = np.load(args.gen2, allow_pickle=True)
    hn = np.load(args.holdout_net, allow_pickle=True)
    hl = np.load(args.holdout_linear, allow_pickle=True)
    assert (hn["seed"] == hl["seed"]).all() and (hn["g"] == hl["g"]).all() and (hn["turn"] == hl["turn"]).all()
    j = [str(m) for m in hl["models"]].index("installed")
    p_inst_h = hl["p"][:, j].astype(np.float64)
    x_inst_h = np.log(np.clip(p_inst_h, 1e-12, 1 - 1e-12) / (1 - np.clip(p_inst_h, 1e-12, 1 - 1e-12)))
    sets = {
        "gen2": {"y": g2["result"].astype(np.float64), "t": g2["turn"] - 1,
                 "key": g2["seed"].astype(np.int64) * 100003 + g2["g"],
                 "P": {"net-10000": sig(g2["net_logit"].astype(np.float64)),
                       "installed (raw)": sig(g2["linear"].astype(np.float64)),
                       "installed (calibrated)": sig(a * g2["linear"].astype(np.float64) + b)}},
        "holdout": {"y": hn["result"].astype(np.float64), "t": hn["turn"] - 1,
                    "key": hn["seed"].astype(np.int64) * 100003 + hn["g"],
                    "P": {"net-10000": hn["p"].astype(np.float64),
                          "installed (raw)": p_inst_h,
                          "installed (calibrated)": sig(a * x_inst_h + b)}},
    }
    rng = np.random.default_rng(0)
    out = ["条件：对手卡表已知（牌序、手牌未知）。J97：net-10000 在第 2 代（它自己走出来的）回合末上，对照留出集（v2skx 的局）", "",
           f"- 现装评估器的校准同 holdout_read.py：p = σ({a:.4f} · logit {b:+.4f})。",
           f"- 区间：整局重抽 {args.boot} 次（numpy default_rng(0)）；第 2 代 − 留出 的差，两组各自独立重抽。", ""]
    stats = {}
    for name, d in sets.items():
        ug, gi = np.unique(d["key"], return_inverse=True)
        G = len(ug)
        n_g = np.bincount(gi, minlength=G).astype(np.float64)
        W = np.stack([np.bincount(rng.integers(0, G, G), minlength=G) for _ in range(args.boot)]).astype(np.float64)
        Wn = W @ n_g
        y = d["y"]
        stats[name] = {"n": len(y), "G": G, "mean_y": y.mean()}
        for m, p in d["P"].items():
            p = np.clip(p, 1e-6, 1 - 1e-6)
            per = {"bias": p - y, "brier": (p - y) ** 2, "logloss": -(y * np.log(p) + (1 - y) * np.log(1 - p))}
            for k, v in per.items():
                s = np.bincount(gi, weights=v, minlength=G)
                stats[name][(m, k)] = (v.mean(), (W @ s) / Wn)
            for lo, hi, label in ((1, 5, "第 1～5 回合"), (6, 10, "第 6～10 回合"), (11, 99, "第 11 回合起")):
                sel = (d["t"] >= lo) & (d["t"] <= hi)
                stats[name][(m, "bucket", label)] = (int(sel.sum()), float(np.mean(p[sel] - y[sel])),
                                                     float(np.mean((p[sel] - y[sel]) ** 2)))

    def ci(arr):
        return np.percentile(arr, 2.5), np.percentile(arr, 97.5)

    for name in sets:
        st = stats[name]
        out += [f"**{'第 2 代' if name == 'gen2' else '留出集'}**：{st['n']} 个回合末，{st['G']} 局，实际胜率（刚结束回合那一方）{st['mean_y']:.4f}", "",
                "| 模型 | 平均偏差 mean(p) − 胜率（95%） | Brier（95%） | log-loss |", "|---|---|---|---|"]
        for m in sets[name]["P"]:
            bp, bb = st[(m, "bias")]
            ep, eb = st[(m, "brier")]
            lp, _ = st[(m, "logloss")]
            out.append(f"| {m} | {bp:+.4f}（{ci(bb)[0]:+.4f}～{ci(bb)[1]:+.4f}） | {ep:.4f}（{ci(eb)[0]:.4f}～{ci(eb)[1]:.4f}） | {lp:.4f} |")
        out.append("")
    out += ["**第 2 代 − 留出集**（两组独立重抽）", "", "| 模型 | 偏差之差 | Brier 之差 |", "|---|---|---|"]
    for m in sets["gen2"]["P"]:
        (b1, B1), (b2, B2) = stats["gen2"][(m, "bias")], stats["holdout"][(m, "bias")]
        (e1, E1), (e2, E2) = stats["gen2"][(m, "brier")], stats["holdout"][(m, "brier")]
        lo1, hi1 = ci(B1 - B2)
        lo2, hi2 = ci(E1 - E2)
        out.append(f"| {m} | {b1 - b2:+.4f}（{lo1:+.4f}～{hi1:+.4f}） | {e1 - e2:+.4f}（{lo2:+.4f}～{hi2:+.4f}） |")
    out += ["", "**分段**（平均偏差 / Brier）", "", "| 段 | 组 | 局面 | net-10000 | installed (calibrated) |", "|---|---|---|---|---|"]
    for label in ("第 1～5 回合", "第 6～10 回合", "第 11 回合起"):
        for name in sets:
            n, bn, en = stats[name][("net-10000", "bucket", label)]
            _, bc, ec = stats[name][("installed (calibrated)", "bucket", label)]
            out.append(f"| {label} | {'第 2 代' if name == 'gen2' else '留出'} | {n} | {bn:+.4f} / {en:.4f} | {bc:+.4f} / {ec:.4f} |")
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
