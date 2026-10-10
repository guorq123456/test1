"""Independent recomputation of the builder's J84 read (3d30161, analysis/widecut/data/habit.json): each position's
win rates from the per-world results, (b) - (a) over positions with its interval, the groups, the mcts:1043
play-out check, and signs that the two branches share their worlds.
Condition: the opponent's deck list is known (order and hand not).

    python3 j84_check.py j84/habit.json --out j84/check.txt
"""
import argparse
import json
import math
import random


def boot(xs, rng, n=2000):
    means = sorted(sum(xs[rng.randrange(len(xs))] for _ in xs) / len(xs) for _ in range(n))
    return means[49], means[1949]


def tci(xs):
    m = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
    h = 1.96 * sd / math.sqrt(len(xs))
    return m - h, m + h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("habit")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    d = json.load(open(args.habit, encoding="utf-8"))
    pos, s, chk = d["positions"], d["summary"], d["check"]
    live = [p for p in pos if not p["same"]]
    out = ["条件：对手卡表已知（牌序、手牌未知）。J84 的独立复算（建造线 3d30161 的 habit.json）", ""]

    # 1. per-position win rates from the worlds
    bad = 0
    for p in live:
        a, b = p["worlds"]["a"], p["worlds"]["b"]
        assert len(a) == len(b) == s["k"]
        aw, bw = sum(a) / len(a), sum(b) / len(b)
        bad += abs(aw - p["a_win"]) > 1e-9 or abs(bw - p["b_win"]) > 1e-9 or abs(bw - aw - p["diff"]) > 1e-9
    out += [f"- 局面 {len(pos)} 个，(a) = (b) 去掉 {len(pos) - len(live)} 个，读 {len(live)} 个；每个 K = {s['k']}。"
            f"从每个世界的结果重算胜率和差，和文件里不符的局面 {bad} 个。"]

    groups = [("全部", live), ("大牌组", [p for p in live if p["big"]]), ("其他", [p for p in live if not p["big"]])]
    keys = {"全部": "b_minus_a_all", "大牌组": "b_minus_a_big", "其他": "b_minus_a_other"}

    # 2. their bootstrap replayed (one Random(0) shared by the calls, in their order) and mine (Random(1) per group)
    rng = random.Random(0)
    theirs = {}
    for name, ps in groups:
        theirs[name] = boot([p["diff"] for p in ps], rng)
    out += ["", "| 组 | 局面 | (b) − (a) | 建造线报的区间 | 照它的代码重抽 | 我另抽（种子 1） | 正态近似 |", "|---|---|---|---|---|---|---|"]
    for name, ps in groups:
        xs = [p["diff"] for p in ps]
        m = sum(xs) / len(xs)
        rep = s[keys[name]]
        mine = boot(xs, random.Random(1))
        t = tci(xs)
        out.append(f"| {name} | {len(xs)} | {m:+.4f}（报 {rep[0]:+.4f}） | {rep[1]:+.4f}～{rep[2]:+.4f} | "
                   f"{theirs[name][0]:+.4f}～{theirs[name][1]:+.4f} | {mine[0]:+.4f}～{mine[1]:+.4f} | {t[0]:+.4f}～{t[1]:+.4f} |")
    out.append(f"- 平均胜率：(a) {sum(p['a_win'] for p in live) / len(live):.4f}（报 {s['a_win_mean']}），"
               f"(b) {sum(p['b_win'] for p in live) / len(live):.4f}（报 {s['b_win_mean']}）")
    pos_n = sum(p["diff"] > 0 for p in live)
    neg_n = sum(p["diff"] < 0 for p in live)
    out.append(f"- 按局面数：(b) 好 {pos_n} 个、(a) 好 {neg_n} 个、相等 {len(live) - pos_n - neg_n} 个")
    top = sorted(live, key=lambda p: -abs(p["diff"]))
    drop = [p["diff"] for p in top[1:]]
    out.append(f"- 去掉差最大的一个（{top[0]['diff']:+.3f}，对局 {top[0]['game']} 第 {top[0]['turn']} 回合）后：{sum(drop) / len(drop):+.4f}"
               f"（正态 {tci(drop)[0]:+.4f}～{tci(drop)[1]:+.4f}）")

    # 3. the mcts:1043 play-out check
    big = {str(p["j"]) for p in live if p["big"]}
    cd = []
    for j, v in chk.items():
        a, b = [v["a"][str(i)] for i in range(len(v["a"]))], [v["b"][str(i)] for i in range(len(v["b"]))]
        cd.append(sum(b) / len(b) - sum(a) / len(a))
    rep = s["check_big_mcts1043_playout"]
    same = [p["diff"] for p in live if str(p["j"]) in chk]
    out += ["", f"- 1043 续打核对：{len(chk)} 个局面，和大牌组的局面{'完全一样' if set(chk) == big else '不一样'}；"
            f"每个 K = {len(next(iter(chk.values()))['a'])}。",
            f"  - (b) − (a) = {sum(cd) / len(cd):+.4f}（报 {rep[0]:+.4f}，{rep[1]:+.4f}～{rep[2]:+.4f}）；正态 {tci(cd)[0]:+.4f}～{tci(cd)[1]:+.4f}",
            f"  - 同样这些局面、level-strong 续打：{sum(same) / len(same):+.4f}"]

    # 4. shared worlds: agreement of the two branches world by world
    agree = n = 0
    exp = 0.0
    for p in live:
        a, b = p["worlds"]["a"], p["worlds"]["b"]
        agree += sum(x == y for x, y in zip(a, b))
        n += len(a)
        pa, pb = sum(a) / len(a), sum(b) / len(b)
        exp += len(a) * (pa * pb + (1 - pa) * (1 - pb))
    out += ["", f"- 两分支同一世界结果相同的比例 {agree / n:.1%}；两分支要是各抽各的世界，按各局面胜率算的期望是 {exp / n:.1%}。"
            "高出这么多，说明世界确实共用（代码里抽隐藏牌、本方和续打智能体的种子都只取决于局面 j 和世界 k，不取决于分支）。"]
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
