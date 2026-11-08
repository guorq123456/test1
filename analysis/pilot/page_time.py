"""A pilot's time per decision against the generic bot of the same level, in the page's runtime (Pyodide): the
install N of the bot decks' pilots (ui.session.PILOTS; Salem 2026-11-08 「那就帮我都装进去吧」).

The hero gate's time match (tools.herogate --time) without its process pool, so it runs inside Pyodide: pair k is the
hero against the field's (k mod 6)-th other deck on deal seed + k, from both seats, X then the baseline piloting the
hero, the opponent's agent the same (tools.herogate.play_pair). The CPU and wall time of the hero's searched decisions
are summed per arm; in Pyodide (one thread) the two agree. Timing only: the games' results are not read.
The gates' rule: inside 0.97-1.03 N stays, else N = round(N / ratio), once.

    python analysis/pilot/page_time.py --hero bot/T1-SWORD-1 --field analysis/pilot/fields/bot-frozen7.txt \
        --x SPEC --base mcts:100+plan --opp mcts:100+plan --seed S --pairs K --out OUT.json
    node analysis/scaling/web_sim/run_py.js DIST analysis/pilot/page_time_in_pyodide.py \
        analysis/pilot/page_time.py=/home/pyodide/page_time.py ARGS.json=/home/pyodide/args.json \
        analysis/pilot/fields/bot-frozen7.txt=/home/pyodide/field.txt      # ARGS.json: this tool's arguments

Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import argparse
import json
import time


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hero", required=True)
    ap.add_argument("--field", required=True)
    ap.add_argument("--x", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--opp", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--pairs", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    from svsim.tools.deckgate import read_field
    from svsim.tools.herogate import budget, opponents, play_pair, time_match
    field = read_field(args.field)
    labels = [label for label, _ in field]
    hero, opps = labels.index(args.hero), opponents(field, args.hero)
    rows = {"x": {"cpu": 0.0, "wall": 0.0, "moves": 0}, "base": {"cpu": 0.0, "wall": 0.0, "moves": 0}}
    pairs = []
    t0 = time.perf_counter()
    for k in range(args.pairs):
        opp = opps[k % len(opps)]
        res = play_pair((k, args.seed + k, opp, field[hero][1], field[opp][1], args.x, args.base, args.opp))
        for g in res["games"]:
            r = rows[g["arm"]]
            r["cpu"] += g["hero_cpu"]
            r["wall"] += g["hero_wall"]
            r["moves"] += g["hero_moves"]
        pairs.append({"k": k, "seed": args.seed + k, "opp": labels[opp]})
        print(f"pair {k} done, {time.perf_counter() - t0:.0f}s", flush=True)
    per = {arm: {"cpu_ms": round(1000 * r["cpu"] / max(r["moves"], 1), 2),
                 "wall_ms": round(1000 * r["wall"] / max(r["moves"], 1), 2), "decisions": r["moves"]}
           for arm, r in rows.items()}
    ratio = (rows["x"]["wall"] / max(rows["x"]["moves"], 1)) / max(rows["base"]["wall"] / max(rows["base"]["moves"], 1),
                                                                    1e-12)
    n = budget(args.x)
    out = {"hero": args.hero, "x": args.x, "base": args.base, "opp": args.opp, "seed": args.seed, "pairs": pairs,
           "per_decision": per, "ratio_wall": round(ratio, 3), "n": n,
           "n_matched": time_match(n, ratio) if n is not None else None,
           "seconds": round(time.perf_counter() - t0, 1), "condition": "对手卡表已知（牌序、手牌未知）"}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("hero", "per_decision", "ratio_wall", "n", "n_matched")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
