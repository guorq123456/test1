"""Tables for teacher_eval.py's rows: sign agreement and ranking agreement with Salem, teacher against control.

    python3 report.py ROWS_JSON TURNS_JSONL [--probes CROSS_TURN_JSON]

TURNS_JSONL (analysis/cross-turn/play_turns.py output) says which of Salem's
turns won the game: those are left out (what Salem kept on a winning turn
says nothing about keeping). The two seeds of a measurement are averaged.
Ranking agreement (AUC): within one restriction (the same card, or save, or
noevo), over pairs (a turn where Salem kept, a turn where Salem used), the
share where the value is higher on the kept side (ties half): does the value
move with the situation the way Salem's choice does. 95% intervals from
resampling turns (2000 times).
"""
import json
import random
import statistics
import sys
from collections import defaultdict


def load(rows_path, turns_path):
    won = set()
    for line in open(turns_path, encoding="utf-8"):
        r = json.loads(line)
        if r["salem"]["won"]:
            won.add((r["game"], r["at"]))
    agg = defaultdict(list)
    for r in json.load(open(rows_path, encoding="utf-8")):
        agg[(r["game"], r["at"], r["restriction"])].append(r)
    items = []
    for (g, a, res), rs in agg.items():
        if (g, a) in won:
            continue
        cs = [x["control"] for x in rs if x["control"] is not None]
        items.append({"turn": (g, a), "res": res, "salem": rs[0]["salem"],
                      "t": statistics.mean(x["teacher"] for x in rs), "c": statistics.mean(cs) if cs else None})
    return items


def auc(items, key):
    num = den = 0.0
    groups = defaultdict(list)
    for it in items:
        if it[key] is not None:
            groups[it["res"]].append(it)
    for g in groups.values():
        kept = [x[key] for x in g if x["salem"] == "kept"]
        used = [x[key] for x in g if x["salem"] == "used"]
        for a in kept:
            for b in used:
                den += 1
                num += 1.0 if a > b else 0.5 if a == b else 0.0
    return (num / den if den else float("nan")), int(den)


def sign(items, key):
    s = [x for x in items if x[key] is not None]
    hits = sum(1.0 if x[key] != 0 and (x[key] > 0) == (x["salem"] == "kept") else 0.5 if x[key] == 0 else 0.0
               for x in s)
    return hits / len(s) if s else float("nan")


def boot(items, samples=2000, seed=3):
    turns = sorted({i["turn"] for i in items})
    by = defaultdict(list)
    for i in items:
        by[i["turn"]].append(i)
    rng = random.Random(seed)
    t, c, d = [], [], []
    for _ in range(samples):
        pick = [x for k in (rng.choice(turns) for _ in turns) for x in by[k]]
        a, _ = auc(pick, "t")
        b, _ = auc([x for x in pick if x["c"] is not None], "c")
        t.append(a)
        c.append(b)
        d.append(a - b)

    def q(v):
        v = sorted(x for x in v if x == x)
        return (v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]) if v else (float("nan"),) * 2
    return q(t), q(c), q(d)


def table(title, items):
    print(f"\n{title}：{len({i['turn'] for i in items})} 个回合，{len(items)} 项")
    print(f"{'限制':<8}{'项':>5}{'排序一致 老师':>16}{'对照':>16}{'差':>18}{'对':>6}{'正负一致 老师':>14}{'对照':>6}")
    for kind, f in (("keep", lambda i: i["res"].startswith("keep")), ("save", lambda i: i["res"] == "save"),
                    ("noevo", lambda i: i["res"] == "noevo"), ("全部", lambda i: True)):
        s = [i for i in items if f(i)]
        if not s:
            continue
        ta, n = auc(s, "t")
        ca, _ = auc([i for i in s if i["c"] is not None], "c")
        (tl, th), (cl, ch), (dl, dh) = boot(s)
        print(f"{kind:<8}{len(s):>5}{f'{ta:.0%}（{tl:.0%}～{th:.0%}）':>16}{f'{ca:.0%}（{cl:.0%}～{ch:.0%}）':>16}"
              f"{f'{ta - ca:+.0%}（{dl:+.0%}～{dh:+.0%}）':>18}{n:>6}{sign(s, 't'):>14.0%}{sign(s, 'c'):>6.0%}")


def main():
    items = load(sys.argv[1], sys.argv[2])
    table("Salem 没在当回合斩杀的回合", items)
    if "--probes" in sys.argv:
        path = sys.argv[sys.argv.index("--probes") + 1]
        probe = {(q["game"], q["at"]) for q in json.load(open(path, encoding="utf-8"))["positions"]
                 if q["confidence"] in ("高", "中")}
        table("其中探针集（验收用的 20 个）的回合（太少，只作参考）", [i for i in items if i["turn"] in probe])


if __name__ == "__main__":
    main()
