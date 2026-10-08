"""The hand-oracle gates read: each cell's pair score (direct: A's mean of the two games; --versus: 0.5 + A - B
against C), 95% intervals (normal, as tools.gate reports them), the two cells pooled pair by pair with a bootstrap
stratified by cell, CR on Salem's scale (236 per logit; the steady-state form 800 x (score - 0.5) in brackets), and
A / B milliseconds per searched decision.

    python3 <this> analysis/gates/oracle/ramp-t_ramp-t.jsonl analysis/gates/oracle/elf-t_nemesis-t.jsonl

Condition: A knows the opponent's hand (+oracle); everything else as usual, the opponent's 40-card list known.
"""
import json
import math
import random
import sys


def pair(row):
    a = sum(row["points"]) / len(row["points"])
    return 0.5 + a - sum(row["b_points"]) / len(row["b_points"]) if "b_points" in row else a


def ms(row):
    """(A's ms total, searched decisions), (B's): direct rows keep B in ms_b; --versus rows keep A vs C then B vs C
    in ms (games 0-1 A's, 2-3 B's), A / B the side under test in each game, so only the A or B seat counts."""
    if "ms_b" in row:
        return (sum(x["total"] for x in row["ms"]), sum(x["n"] for x in row["ms"])), \
               (sum(x["total"] for x in row["ms_b"]), sum(x["n"] for x in row["ms_b"]))
    m = row["ms"]
    return (m[0]["total"] + m[1]["total"], m[0]["n"] + m[1]["n"]), (m[2]["total"] + m[3]["total"], m[2]["n"] + m[3]["n"])


def cr(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return 236 * math.log(p / (1 - p))


def main():
    cells = []
    for path in sys.argv[1:]:
        rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
        xs = [pair(r) for r in rows]
        n = len(xs)
        m = sum(xs) / n
        sd = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5
        h = 1.96 * sd / n ** 0.5
        a = [ms(r) for r in rows]
        ma = sum(x[0][0] for x in a) / sum(x[0][1] for x in a)
        mb = sum(x[1][0] for x in a) / sum(x[1][1] for x in a)
        print(f"{path}: {n} pairs, seeds {min(r['seed'] for r in rows)}..{max(r['seed'] for r in rows)}, "
              f"{m:.1%} ± {h:.1%} ({m - h:.1%}..{m + h:.1%}), CR {cr(m):+.0f} ({cr(m - h):+.0f}..{cr(m + h):+.0f}; "
              f"steady-state {800 * (m - 0.5):+.0f}); ms per searched decision A {ma:.2f} / B {mb:.2f} = {ma / mb:.3f}")
        cells.append(xs)
    allx = [x for c in cells for x in c]
    m = sum(allx) / len(allx)
    rng = random.Random(1)
    bs = sorted(sum(sum(rng.choice(c) for _ in c) for c in cells) / len(allx) for _ in range(4000))
    lo, hi = bs[99], bs[3899]
    print(f"pooled pair by pair ({len(allx)} pairs, stratified bootstrap 4000): {m:.1%} ({lo:.1%}..{hi:.1%}), "
          f"CR {cr(m):+.0f} ({cr(lo):+.0f}..{cr(hi):+.0f}; steady-state {800 * (m - 0.5):+.0f})")


if __name__ == "__main__":
    main()
