"""Item 6b part 2: category summary of realgame_6b_roll.py's pairs (the registered scoring, REALGAME.md).

    python analysis/process/realgame_6b_roll_report.py POSITIONS.jsonl ROLL.jsonl
"""
import collections
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from realgame_6b import key

CATS = ["第1回合 bot 不出", "第1回合 出的牌不同", "第2-5回合 bot 不出", "第2-5回合 bot 少出",
        "第2-5回合 bot 多出", "第2-5回合 出的牌不同"]


def category(p):
    s, b = collections.Counter(key(p["salem"])), collections.Counter(key(p["bot"]))
    head = "第1回合" if p["turn"] == 1 else "第2-5回合"
    if not b:
        return f"{head} bot 不出"
    if not (b - s):
        return f"{head} bot 少出"
    if not (s - b):
        return f"{head} bot 多出"
    return f"{head} 出的牌不同"


def mean_se(xs):
    n = len(xs)
    if n == 0:
        return float("nan"), float("nan")
    m = sum(xs) / n
    if n < 2:
        return m, float("nan")
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    return m, math.sqrt(v / n)


def main(pos_path, roll_path):
    with open(pos_path, encoding="utf-8") as f:
        pos = {(p["game"], p["turn"]): p for p in map(json.loads, f) if "bot" in p}
    pairs = collections.defaultdict(list)
    wins = collections.defaultdict(lambda: [0.0, 0.0, 0])
    skipped = collections.Counter()
    notes = collections.Counter()
    with open(roll_path, encoding="utf-8") as f:
        for x in map(json.loads, f):
            if "skip" in x:
                skipped[x["skip"]] += 1
                continue
            k = (x["game"], x["turn"])
            pairs[k].append(x["salem"] - x["bot"])
            w = wins[k]
            w[0] += x["salem"]
            w[1] += x["bot"]
            w[2] += 1
            for b in ("salem", "bot"):
                for n, c in x.get(b + "_notes", {}).items():
                    notes[(b, n)] += c
    by = collections.defaultdict(list)
    for k, d in pairs.items():
        by[category(pos[k])].append((k, sum(d) / len(d)))
    print(f"位置 {len(pairs)}，对数 {sum(len(d) for d in pairs.values())}，跳过 {dict(skipped)}，强制出牌的偏差 {dict(notes)}")
    allpos = []
    for c in CATS + sorted(set(by) - set(CATS)):
        xs = [v for _, v in by.get(c, [])]
        allpos += xs
        m, se = mean_se(xs)
        ws = [wins[k] for k, _ in by.get(c, [])]
        sw = sum(w[0] for w in ws) / max(1, sum(w[2] for w in ws))
        bw = sum(w[1] for w in ws) / max(1, sum(w[2] for w in ws))
        print(f"{c}：{len(xs)} 处，你的打法胜率 {sw:.1%}，bot 的 {bw:.1%}，差 {m:+.3f} ± {se:.3f}（按位置算的标准误）")
    m, se = mean_se(allpos)
    print(f"全部：{len(allpos)} 处，差 {m:+.3f} ± {se:.3f}")
    for k, d in sorted(pairs.items()):
        print(f"  第{k[0]}局第{k[1]}回合 {category(pos[k])}：{len(d)} 对，差 {sum(d) / len(d):+.3f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
