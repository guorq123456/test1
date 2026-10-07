"""What the cross-turn planner chose in a gate's games: kinds, z, and the situation it chose them in.

    python3 plans_report.py RECORDS.jsonl[.gz] [...]

Reads the gate's side file of game records (record["plans"]: the planner's
measurements at the turn starts it measured). Only the planner's own seat.
For each chosen restriction (not "line"): its kind, the paired z of (it minus
the line) over the determinizations, and the situation of the turn:
- life: own leader defense minus the opponent's (ahead at +4, behind at -4);
- the planner's own estimate: the line's mean play-out value (<0.4 behind,
  >0.6 ahead, even between).
"""
import gzip
import json
import math
import statistics
import sys
from collections import Counter, defaultdict


def lines_of(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def z_of(values, base):
    d = [a - b for a, b in zip(values, base)]
    n = len(d)
    m = sum(d) / n
    se = math.sqrt(sum((x - m) ** 2 for x in d) / max(n - 1, 1) / n)
    return m, (m / se if se > 0 else (float("inf") if m > 0 else 0.0))


def report(path):
    recs = lines_of(path)
    chosen, measured = [], 0
    for r in recs:
        a, b = r["ai"].split(" / ")
        seat = 0 if "cross" in a else 1
        won = r["winner"] == seat
        for p in r.get("plans") or []:
            if p["player"] != seat:
                continue
            measured += 1
            line = p["samples"]["line"]
            est = statistics.mean(line)
            life = p["hp"] - p["opp_hp"]
            situation = {"life": "领先" if life >= 4 else "落后" if life <= -4 else "均势",
                         "est": "领先" if est > 0.6 else "落后" if est < 0.4 else "均势"}
            if p["chosen"] == "line":
                chosen.append({"kind": "line", **situation, "won": won})
                continue
            m, z = z_of(p["samples"][p["chosen"]], line)
            chosen.append({"kind": p["chosen"].split(":")[0], "gain": m, "z": z, **situation, "won": won})
    picks = [c for c in chosen if c["kind"] != "line"]
    print(f"== {path.rsplit('/', 1)[-1]}：{len(recs)} 局记录，规划器测量 {measured} 次，推翻主线 {len(picks)} 次"
          f"（{len(picks) / max(measured, 1):.0%}）")
    print("  种类：" + "，".join(f"{k} {n}" for k, n in Counter(c["kind"] for c in picks).most_common()))
    zs = sorted(c["z"] for c in picks if math.isfinite(c["z"]))
    if zs:
        q = lambda p: zs[min(len(zs) - 1, int(p * len(zs)))]
        print(f"  被选中的 z 分位 10/25/50/75/90%：{q(.1):.2f} / {q(.25):.2f} / {q(.5):.2f} / {q(.75):.2f} / {q(.9):.2f}；"
              f"z<2 {sum(z < 2 for z in zs) / len(zs):.0%}，z<3 {sum(z < 3 for z in zs) / len(zs):.0%}")
    for axis, title in (("life", "按血量差"), ("est", "按规划器自估的主线胜率")):
        allc = Counter(c[axis] for c in chosen)
        pc = Counter(c[axis] for c in picks)
        cells = [f"{s} {pc[s]}/{allc[s]}（{pc[s] / max(allc[s], 1):.0%}）" for s in ("领先", "均势", "落后")]
        print(f"  推翻率，{title}：" + "  ".join(cells))


if __name__ == "__main__":
    for path in sys.argv[1:]:
        report(path)
