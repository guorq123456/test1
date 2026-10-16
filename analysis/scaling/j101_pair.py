"""J101 (README): J98 - J101 pair by pair on the same seeds (70900000-299): each pair's score (A's mean of its two
games) differenced; 95% interval from 4000 resamples of pairs with random.Random(1), the 100th and 3900th (as
analysis/oracle-hand/pooled.py). Also the in-gate ms ratio of J101's two segments (before and after the container
restart: the first 84 pairs, then the rest; pass 0 to skip). Works for any two gates on the same seeds. Condition: the opponent's deck list is known (order and hand not).

    python3 j101_pair.py analysis/gates/scaling/j98/gate_j98.jsonl analysis/gates/scaling/j101/gate_j101.jsonl 84
"""
import json
import random
import sys
from pathlib import Path


def load(path):
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def ratio(rows):
    at = sum(x["total"] for r in rows for x in r["ms"])
    an = sum(x["n"] for r in rows for x in r["ms"])
    bt = sum(x["total"] for r in rows for x in r["ms_b"])
    bn = sum(x["n"] for r in rows for x in r["ms_b"])
    return at / an, bt / bn, (at / an) / (bt / bn)


def main():
    j98, j101, first = load(sys.argv[1]), load(sys.argv[2]), int(sys.argv[3])
    a = {r["seed"]: r for r in j98}
    b = {r["seed"]: r for r in j101}
    assert set(a) == set(b), "the two gates must share their seeds"
    seeds = sorted(a)
    d = [sum(a[s]["points"]) / len(a[s]["points"]) - sum(b[s]["points"]) / len(b[s]["points"]) for s in seeds]
    m = sum(d) / len(d)
    rng = random.Random(1)
    bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(4000))
    names = [Path(x).stem.replace("gate_", "").upper() for x in sys.argv[1:3]]
    print(f"{names[0]} - {names[1]} pair by pair ({len(d)} pairs): {m:+.1%} ({bs[99]:+.1%}..{bs[3899]:+.1%})")
    if first <= 0:
        return
    order = [r["seed"] for r in j101]                 # file order: the first `first` rows ran before the restart
    seg1, seg2 = set(order[:first]), set(order[first:])
    for name, seg in (("before the restart", seg1), ("after the restart", seg2), ("all", set(order))):
        ma, mb, q = ratio([b[s] for s in seeds if s in seg])
        print(f"J101 {name} ({len(seg)} pairs): ms A {ma:.2f} / B {mb:.2f} = {q:.3f}")


if __name__ == "__main__":
    main()
