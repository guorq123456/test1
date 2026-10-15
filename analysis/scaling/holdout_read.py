"""The scaling test's held-out read (README sections 2, 3, 5): on the same held-out turn ends, each model's Brier,
log-loss and skill = Brier(0.5) - Brier(model); differences in skill (tier to tier, net - linear refit, against the
installed evaluator); 95% intervals from 2000 resamples of whole held-out games (numpy default_rng(0)), every
difference paired on the same resample; turn buckets by the turn just ended (1-5, 6-10, 11+).
`--wide` adds the secondary rows (README, the twice-as-wide net): wide - fixed net and wide - linear refit per tier,
wide tier to tier, and the wide skill ratio (described, not judged).
The installed evaluator's probability is recalibrated as pre-registered: p = sigma(a * logit + b), a and b fitted by
1-D logistic regression on 10^4 training turn ends (`--calib` rows from installed_logits.py).
Condition: the opponent's deck list is known (order and hand not).

    python3 holdout_read.py --linear holdout-linear.npz --net 1000=holdout-net-1000.npz 10000=holdout-net-10000.npz \
        --calib train_k0_logits.jsonl --out read.txt [--wide 10000=holdout-net-wide-10000.npz ...]
"""
import argparse
import json
import math

import numpy as np


def fit1d(x, y, iters=50):
    a, b = 1.0, 0.0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(a * x + b, -60, 60)))
        r, w = p - y, p * (1 - p)
        g = np.array([np.sum(r * x), np.sum(r)])
        H = np.array([[np.sum(w * x * x), np.sum(w * x)], [np.sum(w * x), np.sum(w)]])
        step = np.linalg.solve(H, g)
        a, b = a - step[0], b - step[1]
        if np.max(np.abs(step)) < 1e-10:
            break
    return float(a), float(b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--linear", required=True)
    ap.add_argument("--net", nargs="+", required=True, help="SIZE=path")
    ap.add_argument("--wide", nargs="*", default=[], help="SIZE=path (secondary rows)")
    ap.add_argument("--calib", required=True)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    lin = np.load(args.linear, allow_pickle=True)
    seed, g, turn, y = lin["seed"].astype(np.int64), lin["g"].astype(np.int64), lin["turn"], lin["result"].astype(np.float64)
    names = [str(m) for m in lin["models"]]
    P = {}
    for j, m in enumerate(names):
        P["installed (raw)" if m == "installed" else m.replace("lin-", "linear ")] = lin["p"][:, j].astype(np.float64)
    sizes, wides = [], []
    for kind, specs, into in (("net", args.net, sizes), ("wide", args.wide, wides)):
        for spec in specs:
            size, path = spec.split("=")
            d = np.load(path, allow_pickle=True)
            assert (d["seed"].astype(np.int64) == seed).all() and (d["g"] == g).all() and (d["turn"] == turn).all() \
                and (d["result"] == lin["result"]).all(), f"{path} not aligned"
            P[f"{kind} {size}"] = d["p"].astype(np.float64)
            into.append(size)

    cal = [json.loads(l) for l in open(args.calib, encoding="utf-8") if l.strip()]
    cx = np.array([r["x"] for r in cal])
    cy = np.array([r["y"] for r in cal])
    a, b = fit1d(cx, cy)
    p0 = np.clip(P["installed (raw)"], 1e-12, 1 - 1e-12)
    P["installed (calibrated)"] = 1 / (1 + np.exp(-(a * np.log(p0 / (1 - p0)) + b)))

    keys = seed * 100003 + g
    ug, gi = np.unique(keys, return_inverse=True)
    G = len(ug)
    n_g = np.bincount(gi, minlength=G).astype(np.float64)
    e0 = (0.5 - y) ** 2

    def per_game(v):
        return np.bincount(gi, weights=v, minlength=G)

    order = (["installed (raw)", "installed (calibrated)"] + [f"linear {s}" for s in sizes] + [f"net {s}" for s in sizes]
             + [f"wide {s}" for s in wides])
    order = [m for m in order if m in P]
    E, L = {}, {}
    for m in order:
        p = np.clip(P[m], 1e-6, 1 - 1e-6)
        E[m] = per_game((p - y) ** 2)
        L[m] = per_game(-(y * np.log(p) + (1 - y) * np.log(1 - p)))
    E0 = per_game(e0)

    rng = np.random.default_rng(0)
    W = np.stack([np.bincount(rng.integers(0, G, G), minlength=G) for _ in range(args.boot)]).astype(np.float64)
    Wn = W @ n_g

    def boot(v):                                  # v: per-game sums -> resampled means
        return (W @ v) / Wn

    def point(v):
        return v.sum() / n_g.sum()

    def ci(arr):
        return np.percentile(arr, 2.5), np.percentile(arr, 97.5)

    skill_pt = {m: point(E0) - point(E[m]) for m in order}
    skill_bs = {m: boot(E0) - boot(E[m]) for m in order}
    out = ["条件：对手卡表已知（牌序、手牌未知）。缩放测试的留出读数（analysis/scaling/README.md 第 2、3、5 节）", "",
           f"- 留出回合末 {len(y)} 个，{G} 局；常数 0.5 的 Brier {point(E0):.4f}。",
           f"- 现装评估器的校准：在 10⁴ 训练集第 0 片的 {len(cy)} 个回合末上拟合 p = σ({a:.4f} · logit + {b:+.4f})。",
           f"- 区间：整局重抽 {args.boot} 次（numpy default_rng(0)），差在同一次重抽上成对算。", "",
           "| 模型 | Brier | log-loss | skill（95%） |", "|---|---|---|---|"]
    for m in order:
        lo, hi = ci(skill_bs[m])
        out.append(f"| {m} | {point(E[m]):.4f} | {point(L[m]):.4f} | {skill_pt[m]:.4f}（{lo:.4f}～{hi:.4f}） |")
    out += ["", "**skill 的差**（正数 = 前者好）", "", "| 差 | 点估计 | 95% |", "|---|---|---|"]
    pairs = []
    for i in range(1, len(sizes)):
        pairs.append((f"net {sizes[i]}", f"net {sizes[i-1]}"))
        pairs.append((f"linear {sizes[i]}", f"linear {sizes[i-1]}"))
    for s in sizes:
        pairs.append((f"net {s}", f"linear {s}"))
    for s in sizes:
        pairs.append((f"net {s}", "installed (calibrated)"))
    pairs.append((f"linear {sizes[-1]}", "installed (calibrated)"))
    for i in range(1, len(wides)):
        pairs.append((f"wide {wides[i]}", f"wide {wides[i-1]}"))
    for s in wides:
        pairs.append((f"wide {s}", f"net {s}"))
        pairs.append((f"wide {s}", f"linear {s}"))
    for x1, x2 in pairs:
        d_pt = skill_pt[x1] - skill_pt[x2]
        lo, hi = ci(skill_bs[x1] - skill_bs[x2])
        out.append(f"| {x1} − {x2} | {d_pt:+.4f} | {lo:+.4f}～{hi:+.4f} |")
    if len(sizes) >= 2:
        s1, s2 = sizes[-2], sizes[-1]
        r_pt = skill_pt[f"net {s2}"] / skill_pt[f"net {s1}"]
        lo, hi = ci(skill_bs[f"net {s2}"] / skill_bs[f"net {s1}"])
        out += ["", f"- skill(net {s2}) ÷ skill(net {s1}) = **{r_pt:.3f}**（{lo:.3f}～{hi:.3f}）"]
    if len(wides) >= 2:
        s1, s2 = wides[-2], wides[-1]
        r_pt = skill_pt[f"wide {s2}"] / skill_pt[f"wide {s1}"]
        lo, hi = ci(skill_bs[f"wide {s2}"] / skill_bs[f"wide {s1}"])
        out += [f"- 次要行，只描述：skill(wide {s2}) ÷ skill(wide {s1}) = {r_pt:.3f}（{lo:.3f}～{hi:.3f}）"]
    out += ["", "**分段**（刚结束的回合：token 文件的 turn − 1）", "", "| 段 | 局面 | " + " | ".join(order) + " |",
            "|---|---|" + "---|" * len(order)]
    t0 = turn - 1
    for name, sel in (("第 1～5 回合", (t0 >= 1) & (t0 <= 5)), ("第 6～10 回合", (t0 >= 6) & (t0 <= 10)), ("第 11 回合起", t0 >= 11)):
        cells = []
        for m in order:
            p = np.clip(P[m], 1e-6, 1 - 1e-6)
            cells.append(f"{np.mean((p[sel] - y[sel]) ** 2):.4f}")
        out.append(f"| {name} | {int(sel.sum())} | " + " | ".join(cells) + " |")
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
