"""One non-mirror league cell in a 2 x 2 of two changes, paired by seed: each change's effect at either level of
the other, and their interaction.

    python3 <this> --pair elf-t/pirate-t --a 起手 --b 模型 \
        00=league_v2s_f631e14.jsonl.gz 10=x-nomodel-R.jsonl.gz 01=x-model-D.jsonl.gz 11=part1.jsonl.gz

The keys are (change a, change b), 0 off and 1 on. A pair is one seed's two games with the decks' seats swapped;
the score is the first deck's (a pair's two games averaged). Per cell: the score over the seeds all four cells
have (95% interval over pairs), the score when the first deck went first and when it went second (by game), the
game length (turns, both sides). Effects, each a paired difference over the same seeds with its 95% interval and
the CR it is worth (Salem's scale, 236 a logit, from the cell it starts from; the steady-state figure 800 x
difference in brackets): a with b off (10 - 00), a with b on (11 - 01), b with a off (01 - 00), b with a on
(11 - 10), both (11 - 00), and the interaction (11 - 10 - 01 + 00, per pair). Each interval two ways: paired by
seed (the seed fixes the deal and who goes first, so a seed's pairs in two cells are the same deal played under two
conditions; the variance of the per-seed difference), and as independent samples (each cell's own variance over
pairs, added: wider when the cells are positively correlated by seed, as they are). Also: how many games are
move for move the same between each two cells, and the time per turn (the games' wall time over their turns, both
sides; over all pairs and over the first 20 seeds, comparable only for runs on one machine at one load).
Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import gzip
import json
import math

SALEM = 236.0


def load(paths, pairing):
    latest = {}
    for path in paths:
        for line in gzip.open(path, "rt", encoding="utf-8"):
            g = json.loads(line)
            if g["pair"] == pairing:
                latest[(g["k"], g["seat_a"])] = g
    return {k: (latest[(k, 0)], latest[(k, 1)]) for k, _ in latest if (k, 0) in latest and (k, 1) in latest}


def pts(g):
    return 0.5 if g["winner"] is None else 1.0 if g["winner"] == g["seat_a"] else 0.0


def ci(xs):
    n = len(xs)
    m = sum(xs) / n
    return m, 1.96 * math.sqrt(sum((x - m) ** 2 for x in xs) / max(n - 1, 1) / n)


def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("--a", default="a", help="the name of the first change")
    ap.add_argument("--b", default="b", help="the name of the second change")
    ap.add_argument("cells", nargs=4, help="00=file[+file...] 10=... 01=... 11=...")
    args = ap.parse_args()
    cells = {c.split("=", 1)[0]: load(c.split("=", 1)[1].split("+"), args.pair) for c in args.cells}
    assert set(cells) == {"00", "10", "01", "11"}, "the keys are 00 10 01 11"
    ks = sorted(set.intersection(*(set(v) for v in cells.values())))
    first = args.pair.split("/")[0]
    score = {c: {k: (pts(v[k][0]) + pts(v[k][1])) / 2 for k in ks} for c, v in cells.items()}
    name = {c: f"{args.a}{'开' if c[0] == '1' else '关'}、{args.b}{'开' if c[1] == '1' else '关'}" for c in cells}
    print(f"条件：对手卡表已知（牌序、手牌未知）。{args.pair}，{first} 的得分；一对 = 同一个种子、换座位的两局；"
          f"四格共有的 {len(ks)} 对。\n")
    print(f"| 格 | {first} 得分（95%，按对） | 它先手 / 后手 | 局长（双方合计） |")
    print("|---|---|---|---|")
    for c in ("00", "10", "01", "11"):
        games = [g for k in ks for g in cells[c][k]]
        f = [pts(g) for g in games if g["first"] == g["seat_a"]]
        s = [pts(g) for g in games if g["first"] != g["seat_a"]]
        m, h = ci(list(score[c].values()))
        t, ht = ci([(cells[c][k][0]["turns"] + cells[c][k][1]["turns"]) / 2 for k in ks])
        print(f"| {c}（{name[c]}） | {m:.1%} ± {h:.1%} | {sum(f) / len(f):.1%} / {sum(s) / len(s):.1%} | {t:.1f} ± {ht:.1f} |")
    var = {c: ci(list(score[c].values()))[1] ** 2 for c in score}          # (1.96 se)^2 of each cell's mean
    print(f"\n效应（95% 区间两种算法：独立样本 = 两格各自按对的方差相加；按种子配对 = 每个种子两格之差的方差。"
          f"CR 按 Salem 刻度，从起点那格自己的得分算，括号里是稳态式 800 × 差）：")
    for label, hi, lo in ((f"{args.a}，{args.b}关（10 − 00）", "10", "00"), (f"{args.a}，{args.b}开（11 − 01）", "11", "01"),
                          (f"{args.b}，{args.a}关（01 − 00）", "01", "00"), (f"{args.b}，{args.a}开（11 − 10）", "11", "10"),
                          (f"两样一起（11 − 00）", "11", "00")):
        d, h = ci([score[hi][k] - score[lo][k] for k in ks])
        base = sum(score[lo].values()) / len(ks)
        print(f"  {label}：{d:+.1%}，独立样本 ± {math.sqrt(var[hi] + var[lo]):.1%}，按种子配对 ± {h:.1%}"
              f"（CR {SALEM * (logit(base + d) - logit(base)):+.0f}，稳态式 {800 * d:+.0f}）")
    d, h = ci([score["11"][k] - score["10"][k] - score["01"][k] + score["00"][k] for k in ks])
    print(f"  交互（11 − 10 − 01 + 00）：{d:+.1%}，独立样本 ± {math.sqrt(sum(var.values())):.1%}，按种子配对 ± {h:.1%}")
    print("\n两格之间逐步相同的局（共 " + str(2 * len(ks)) + " 局）：")
    cs = ("00", "10", "01", "11")
    for i, x in enumerate(cs):
        for y in cs[i + 1:]:
            same = sum(cells[x][k][s]["record"]["actions"] == cells[y][k][s]["record"]["actions"] for k in ks for s in (0, 1))
            print(f"  {x} 和 {y}：{same}")
    print("\n每回合用时（整局墙钟 ÷ 回合数，双方合计）：")
    for c in cs:
        out = []
        for sub in (ks, [k for k in ks if k < 20]):
            games = [g for k in sub for g in cells[c][k]]
            out.append(1000 * sum(g["seconds"] for g in games) / sum(g["turns"] for g in games))
        print(f"  {c}：全部 {out[0]:.0f} ms，前 20 个种子 {out[1]:.0f} ms")

if __name__ == "__main__":
    main()
