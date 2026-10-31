"""Where the teacher's choice goes wrong, by the kind of move and by the card (a diagnosis of the hand-written score,
not a value for any card: nothing here enters the bot).

For every labelled decision (pilot and m = 4 labels), each of the two moves is named by its kind and, for a move of
a card (play, evolve, engage, fuse, attack), by that card's name. A move's "regret" at a decision is how much better
the other move did: -d when it is the teacher's first, +d when it is the second; so a kind or a card whose mean
regret as the first is clearly above 0 is one the teacher picks when it should not, and one whose mean as the second
is clearly below 0 is one it passes over when it should not. Means in win-rate points, SE over decisions; listed: n of
30 or more and |mean| above 2.5 SE.

    python analysis/playnet/r1_where.py runs/r1/pilot.jsonl runs/r1/labels-m4.jsonl --records runs/s1/rec-p3

Condition: 对手卡表已知（牌序、手牌未知）.
"""
import argparse
import gzip
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def name_of(state, mv) -> str:
    t = mv["type"]
    uid = mv.get("uid", mv.get("attacker"))
    if uid is None:
        return t
    for p in state.players:
        for zone in (p.hand, p.field, p.leader_area):
            for c in zone:
                if c.uid == uid:
                    return f"{t}:{c.defn.name}"
    return t


def main():
    from svsim.tools import records as R
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--records", default="runs/s1/rec-p3")
    args = ap.parse_args()
    rows = [r for p in args.paths for r in map(json.loads, open(p)) if r.get("results") is not None]
    by_file = defaultdict(list)
    for r in rows:
        by_file[r["file"]].append(r)
    first, second, kinds = defaultdict(list), defaultdict(list), defaultdict(list)
    for f, rs in by_file.items():
        want = {r["line"]: r for r in rs}
        with gzip.open(Path(args.records) / f, "rt") as fh:
            for k, text in enumerate(fh):
                if k not in want:
                    continue
                r = want[k]
                rec = json.loads(text)
                for i, (state, _a) in enumerate(R.steps(rec)):
                    if i == r["step"]:
                        break
                n = len(r["results"][0])
                d = (sum(r["results"][0]) - sum(r["results"][1])) / n
                a, b = (name_of(state, mv) for mv in r["moves"])
                first[a].append(-d)
                second[b].append(d)
                kinds[(r["moves"][0]["type"], r["moves"][1]["type"])].append(d)

    def show(title, table, sign_note):
        print(title)
        out = []
        for key, v in table.items():
            if len(v) < 30:
                continue
            m = sum(v) / len(v)
            se = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1) / len(v))
            if se > 0 and abs(m) > 2.5 * se:
                out.append((m / se, key, len(v), m, se))
        for z, key, n, m, se in sorted(out, key=lambda x: -abs(x[0])):
            print(f"  {str(key):60s} n {n:5d}  {100 * m:+6.1f} ± {100 * se:.1f}  {sign_note}")
    print(f"decisions {len(rows)}")
    show("as the teacher's first, mean regret (+: picked when the other was better):", first, "")
    show("as the second, mean regret (-: passed over when it was better):", second, "")
    show("by the pair of kinds (first, second), mean d (+: the teacher's first better):", kinds, "")
    print("condition: 对手卡表已知（牌序、手牌未知）")


if __name__ == "__main__":
    main()
