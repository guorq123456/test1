"""cand-sp's nested read (README-sp.md section 1): the builder's per-pair scores under the outer 5 / inner 4 folds
(7288547, analysis/salem-pref/data/nested_scores.jsonl) read the pre-registered way.
Condition: the opponent's deck list is known (order and hand not).

    python3 sp_nested_read.py sp-nested/nested_scores.jsonl sp-nested/nested.json --out sp-nested/read.txt

- Checks: game j of the sorted game ids sits in outer fold j mod 5; each fold's lambda is the inner CV best on a grid
  holding 0 (ties to the smaller); one Salem end per turn.
- A pair is Salem's end against one of the installed 1043's top 8 (in_top and not Salem's; ends equal to Salem's are
  already merged by state_key). Right when the model scores Salem's end higher, a tie counts half. Pooled over the
  outer held-out games.
- Intervals: games resampled 2000 times (random seed 0), percentiles; cand-sp - cand-kc paired on the same pairs.
"""
import argparse
import json
import random

MODELS = ("cand-sp", "cand-kc", "installed")


def turn_pairs(row):
    """Per model, (right, pairs) for this turn."""
    salem = [c for c in row["candidates"] if c["salem"]]
    assert len(salem) == 1, (row["game"], row["turn"])
    s = salem[0]
    ctrl = [c for c in row["candidates"] if c["in_top"] and not c["salem"]]
    out = {}
    for m in MODELS:
        right = sum(1.0 if s[m] > c[m] else 0.5 if s[m] == c[m] else 0.0 for c in ctrl)
        out[m] = (right, len(ctrl))
    return out


def by_game(rows):
    games = {}
    for r in rows:
        tp = turn_pairs(r)
        g = games.setdefault(r["game"], {m: [0.0, 0] for m in MODELS})
        for m in MODELS:
            g[m][0] += tp[m][0]
            g[m][1] += tp[m][1]
    return games


def acc(games, ids, m):
    right = sum(games[i][m][0] for i in ids)
    n = sum(games[i][m][1] for i in ids)
    return right / n


def read(rows, label, n_boot=2000):
    games = by_game(rows)
    ids = sorted(games)
    point = {m: acc(games, ids, m) for m in MODELS}
    rng = random.Random(0)
    boots = {m: [] for m in MODELS}
    diff = []
    for _ in range(n_boot):
        samp = [rng.choice(ids) for _ in ids]
        a = {m: acc(games, samp, m) for m in MODELS}
        for m in MODELS:
            boots[m].append(a[m])
        diff.append(a["cand-sp"] - a["cand-kc"])

    def ci(xs):
        xs = sorted(xs)
        return xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]

    pairs = sum(games[i]["cand-sp"][1] for i in ids)
    lines = [f"**{label}**：{len(ids)} 局、{len(rows)} 个回合、{pairs} 对", "",
             "| 模型 | 成对准确率 | 按局重抽 95% |", "|---|---|---|"]
    names = {"cand-sp": "cand-sp2（外层折模型）", "cand-kc": "cand-kc", "installed": "现装 ENDED"}
    for m in MODELS:
        lo, hi = ci(boots[m])
        lines.append(f"| {names[m]} | {point[m]:.1%} | {lo:.1%}～{hi:.1%} |")
    lo, hi = ci(diff)
    d = point["cand-sp"] - point["cand-kc"]
    lines += ["", f"- cand-sp2 − cand-kc：**{100 * d:+.1f}** 个百分点（成对重抽 {100 * lo:+.1f}～{100 * hi:+.1f}）", ""]
    return lines, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scores")
    ap.add_argument("nested")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = [json.loads(x) for x in open(args.scores, encoding="utf-8") if x.strip()]
    nested = json.load(open(args.nested, encoding="utf-8"))
    lines = ["条件：对手卡表已知（牌序、手牌未知）。cand-sp 的嵌套读数（README-sp.md 第 1 节的口径；建造线 7288547 的逐对打分）", ""]

    ids = sorted({r["game"] for r in rows}, key=int)
    want = {g: j % 5 for j, g in enumerate(ids)}
    bad = [r for r in rows if r["outer_fold"] != want[r["game"]]]
    held = {str(k): sorted(v["held_games"]) for k, v in nested["outer"].items()}
    held_bad = [k for k in held if held[k] != sorted(g for g in ids if want[g] == int(k))]
    lam_bad = []
    for k, v in nested["outer"].items():
        grid = {float(x): y for x, y in v["inner_pairwise"].items()}
        best = max(grid.values())
        pick = min(x for x, y in grid.items() if y == best)
        if 0.0 not in grid or pick != v["lambda"]:
            lam_bad.append(k)
    lam_rows = sorted({(r["outer_fold"], r["lambda"]) for r in rows})
    lines += ["**核对**",
              f"- 分折：对局号排序后第 j 局进第 j mod 5 折，{len(rows)} 个回合里不符的 {len(bad)} 个；nested.json 的各折留出局不符的折 {len(held_bad)} 个。",
              f"- λ：网格 {sorted(float(x) for x in nested['outer']['0']['inner_pairwise'])}（含 0）；各折按内层成对准确率取最高、并列取小，不符的折 {len(lam_bad)} 个；各折 λ {lam_rows}。",
              "- 每个回合正好一个 Salem 的回合末：是（读的时候逐行断言）。", ""]

    out, d_all = read(rows, "全部")
    lines += out
    out, _ = read([r for r in rows if r["ramp_mirror"]], "跳费龙镜像")
    lines += out
    out, _ = read([r for r in rows if not r["ramp_mirror"]], "其他对位（模型都是跳费龙镜像的）")
    lines += out

    ratio = nested["final"]["val_mse_ratio_vs_cand-kc"]
    folds = nested["val_mse"]["outer folds"]
    kc = nested["val_mse"]["cand-kc"]
    lines += ["**自对局对比误差**（cand-kc 的 val 集，建造线算）",
              f"- 最终模型 {nested['final']['val_mse']:.6f} ÷ cand-kc {kc:.6f} = **{ratio:.2f}**；外层各折 " +
              "、".join(f"{folds[k] / kc:.2f}" for k in sorted(folds)), "",
              "**J75 的两条，按嵌套口径重看**（判定已定为错，这里只核对）",
              f"1. 成对准确率比 cand-kc 高至少 5 个百分点：{100 * d_all:+.1f} → {'成立' if d_all >= 0.05 else '不成立'}",
              f"2. 自对局对比误差变差不到 3%：{ratio:.2f} → {'成立' if ratio < 1.03 else '不成立'}"]
    text = "\n".join(lines)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
