"""Like-for-like reading of the external simulator league (league.py): each external deck against the six
Claude-built groups (42 decks), next to the bot's and the control's deck of the same class against the same 42 decks
in the metric-5 cheap league (both mcts:100+plan, 10 deals per pair; different deals, so each cell carries its own
noise), and the external decks head to head with the bot's and the control's seven.

    python analysis/deckbuild/blind-test/external/league_vs_roster.py runs/external/dfm-cheap.jsonl

Condition: 对手卡表已知（牌序、手牌未知）. Comparison only: the external decks never enter search or training.
"""
import gzip
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
L5 = HERE.parent / "league5/cheap/league-deals.jsonl.gz"
CLASSES = ("FOREST", "SWORD", "RUNE", "DRAGON", "ABYSS", "HAVEN", "PORTAL")
ZH = dict(zip(CLASSES, ("精灵", "皇家护卫", "巫师", "龙族", "梦魇", "主教", "超越者")))
CLAUDE = ("g1", "g2", "g3", "p2-g1", "p2-g2", "p2-g3")


def craft(label):
    return next(c for c in CLASSES if c in label.upper())


def grp(label):
    return label.split("/", 1)[0]


def mean_se(xs_by_opp):
    """Mean over all games, standard error from per-opponent means (opponent decks are the unit)."""
    per = [sum(v) / len(v) for v in xs_by_opp.values()]
    allx = [x for v in xs_by_opp.values() for x in v]
    m = sum(allx) / len(allx)
    sd = math.sqrt(sum((p - sum(per) / len(per)) ** 2 for p in per) / max(1, len(per) - 1))
    return m, sd / math.sqrt(len(per))


def main():
    ext = defaultdict(lambda: defaultdict(list))        # ref -> opp -> scores
    for t in open(sys.argv[1]):
        if t.strip():
            r = json.loads(t)
            ext[r["ref"]][r["opp"]].append(r["score"])
    l5 = defaultdict(lambda: defaultdict(list))         # deck -> opp -> scores (both seats folded)
    with gzip.open(L5, "rt") as fh:
        for t in fh:
            r = json.loads(t)
            l5[r["a"]][r["b"]].append(r["score"])
            l5[r["b"]][r["a"]].append(1 - r["score"])
    roster = {d for d in l5}
    print("条件：对手卡表已知（牌序、手牌未知）；两边都由 mcts:100+plan 操作；每对 10 个发牌")
    print("一、对 Claude 六组 42 副卡组的平均得分（同样的对手；外部卡组和 bot、对照用的是不同的发牌）")
    print(f"{'职业':6s} {'外部卡组':22s} {'外部':>11s} {'bot 同职业':>11s} {'对照同职业':>11s}")
    tot = defaultdict(list)
    for ref in sorted(ext, key=lambda l: CLASSES.index(craft(l))):
        c = craft(ref)
        row = []
        for who in ("ext", "bot", "control"):
            if who == "ext":
                src = {o: v for o, v in ext[ref].items() if grp(o) in CLAUDE}
            else:
                deck = next(d for d in roster if grp(d) == who and craft(d) == c)
                src = {o: v for o, v in l5[deck].items() if grp(o) in CLAUDE}
            m, se = mean_se(src)
            tot[who].append(m)
            row.append(f"{100 * m:5.1f}±{196 * se:4.1f}")
        print(f"{ZH[c]:6s} {ref:22s} " + " ".join(f"{x:>11s}" for x in row))
    print("平均（七个职业）：" + "，".join(f"{k} {100 * sum(v) / len(v):.1f}" for k, v in tot.items()))
    print("\n二、外部卡组直接对 bot 七副、对照七副（行方得分）")
    for ref in sorted(ext, key=lambda l: CLASSES.index(craft(l))):
        c = craft(ref)
        cells = []
        for g in ("bot", "control"):
            src = {o: v for o, v in ext[ref].items() if grp(o) == g}
            m, se = mean_se(src)
            same = next(o for o in src if craft(o) == c)
            s = src[same]
            cells.append(f"对 {g} 七副 {100 * m:5.1f}±{196 * se:4.1f}（其中同职业 {100 * sum(s) / len(s):5.1f}）")
        print(f"{ZH[c]:6s} {ref:22s} " + "；".join(cells))
    allbot = [x for ref in ext for o, v in ext[ref].items() if grp(o) == "bot" for x in v]
    allctl = [x for ref in ext for o, v in ext[ref].items() if grp(o) == "control" for x in v]
    print(f"外部七副合计：对 bot 七副 {100 * sum(allbot) / len(allbot):.1f}，对对照七副 {100 * sum(allctl) / len(allctl):.1f}"
          f"（局数 {len(allbot)}、{len(allctl)}）")


if __name__ == "__main__":
    main()
