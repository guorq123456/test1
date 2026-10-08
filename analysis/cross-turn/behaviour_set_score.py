"""Discrimination on the behaviour acceptance set (behaviour_set_b.json), under both definitions of the cell.

    python3 <this> analysis/cross-turn/behaviour_set_b.json v2=analysis/mirror-regression/results_evolve_v2_2ab3a8d.txt \
        cand=RESULTS.txt

RESULTS files are analysis/mirror-regression/check.py's output on evolve_probes.json (one line per probe:
"<probe id>  passed/runs"); the first file is the baseline. In each cell and under each definition (by the
line Salem played; by what the position allowed): the hold rate on Salem's held turns (evolve_hold passes:
no evolution) minus the hold rate on the turns he spent a point (1 - evolve_use passes), i.e.
evolve_hold - (100 - evolve_use), the acceptance table's discrimination (the architecture thread, 18:51Z);
then, against the baseline, the paired difference with a 95% interval from resampling the positions of the
cell (4000 times). Only the cells the set covers on both sides are scored: the key cell "A 档在手、够不着".
Condition: the opponent's 40-card list is known (order and hand not).
"""
import json
import random
import re
import sys

KEY = "A 档在手、够不着"


def load(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r"(\d+-t\d+-\S+)\s+(\d+)/(\d+)$", line.strip())
        if m:
            out[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    return out


def rate(res, ids):
    ok, n = sum(res[i][0] for i in ids), sum(res[i][1] for i in ids)
    return 100 * ok / n if n else None


def disc(res, held, spent):
    return rate(res, held) - (100 - rate(res, spent))


def main():
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    runs = [(a.split("=", 1)[0], load(a.split("=", 1)[1])) for a in sys.argv[2:]]
    print(f"条件：{data['condition']}。分辨力 = evolve_hold − (100 − evolve_use)，在关键格「{KEY}」里。")
    for field, title in (("cell_by_line_played", "按实际出法"), ("cell_by_position", "按局面可能")):
        pos = [p for p in data["positions"] if p[field] == KEY and all(p["probe_id"] in r for _, r in runs)]
        held = [p["probe_id"] for p in pos if p["category"] == "evolve_hold"]
        spent = [p["probe_id"] for p in pos if p["category"] == "evolve_use"]
        print(f"\n{title}：留 {len(held)} 个、花 {len(spent)} 个")
        if not held or not spent:
            print("  （一边没有样本，不算）")
            continue
        for label, res in runs:
            print(f"  {label}：忍住 {rate(res, held):.0f}%，Salem 花的回合也忍住 {100 - rate(res, spent):.0f}%，"
                  f"分辨力 {disc(res, held, spent):+.0f}")
        base_label, base = runs[0]
        rng = random.Random(23)
        for label, res in runs[1:]:
            xs = []
            for _ in range(4000):
                h = [held[rng.randrange(len(held))] for _ in held]
                s = [spent[rng.randrange(len(spent))] for _ in spent]
                xs.append(disc(res, h, s) - disc(base, h, s))
            xs.sort()
            print(f"  {label} − {base_label}：分辨力 {disc(res, held, spent) - disc(base, held, spent):+.0f}"
                  f"（95% {xs[100]:+.0f}～{xs[3899]:+.0f}）")


if __name__ == "__main__":
    main()
