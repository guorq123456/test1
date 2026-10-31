"""An external reference group in the simulator: each of its decks against every deck of league5/roster.txt (the 56
of metric 5: bot, control, six Claude groups), 10 deals a pair, both seats per deal, both sides the cheap bot
(mcts:100+plan), as metric 5's first pass (tools.deckbuild.play_deal: agent seeds as there). Evaluation only: the
reference decks never enter a search, the self-play pool or training data.

Seeds: 85980000 + (reference deck index x 56 + roster index) x 10 + k (claimed 10-31 for this use).
Resumable: deals already in --out are skipped.

    python analysis/deckbuild/blind-test/external/league.py analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt \
        --out runs/external/dfm-cheap.jsonl --workers 4
    python analysis/deckbuild/blind-test/external/league.py ... --report

Condition: 对手卡表已知（牌序、手牌未知）.
"""
import argparse
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from svsim.tools import deckbuild as DB  # noqa: E402

ROSTER = Path(__file__).resolve().parents[1] / "league5/roster.txt"
SEED = 85980000
CONDITION = "对手卡表已知（牌序、手牌未知）"


def jobs(ref, roster, deals, spec):
    out = []
    for k in range(deals):
        for i, (rl, rids) in enumerate(ref):
            for j, (ol, oids) in enumerate(roster):
                out.append(((rl, ol), rids, oids, SEED + (i * len(roster) + j) * 10 + k, spec))
    return out


def report(rows, ref, roster):
    by = {}
    for r in rows:
        by.setdefault((r["ref"], r["opp"]), []).append(r["score"])
    groups = []
    for l, _ in roster:
        g = l.split("/", 1)[0]
        if g not in groups:
            groups.append(g)
    specs = sorted({r["spec"] for r in rows})
    print(f"条件：{CONDITION}；两边都由 {'、'.join(specs)} 操作；每对 10 个发牌（20 局）")
    print("参照卡组对各组的得分（行：参照卡组；列：对手组）")
    print(" " * 24 + " ".join(f"{g:>7}" for g in groups) + "    全部")
    allm = []
    for rl, _ in ref:
        cells, every = [], []
        for g in groups:
            v = [s for (a, o), ss in by.items() if a == rl and o.startswith(g + "/") for s in ss]
            cells.append(sum(v) / len(v) if v else float("nan"))
            every += v
        m = sum(every) / len(every)
        se = math.sqrt(sum((x - m) ** 2 for x in every) / (len(every) - 1) / len(every))
        allm.append(m)
        print(f"{rl:24s}" + " ".join(f"{100 * x:7.1f}" for x in cells) + f"   {100 * m:5.1f} ± {196 * se:.1f}")
    print(f"参照组平均：{100 * sum(allm) / len(allm):.1f}")
    print("各组对参照组的平均得分（= 1 − 参照组对它的得分）：")
    for g in groups:
        v = [s for (a, o), ss in by.items() if o.startswith(g + "/") for s in ss]
        print(f"  {g:8s} {100 * (1 - sum(v) / len(v)):5.1f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ref")
    ap.add_argument("--out", default="runs/external/dfm-cheap.jsonl")
    ap.add_argument("--deals", type=int, default=10)
    ap.add_argument("--spec", default="mcts:100+plan")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    ref = DB.read_seeds(args.ref)
    roster = DB.read_seeds(str(ROSTER))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(t) for t in out.read_text().splitlines() if t.strip()] if out.exists() else []
    if args.report:
        report(rows, ref, roster)
        return
    done = {(r["ref"], r["opp"], r["seed"]) for r in rows}
    todo = [j for j in jobs(ref, roster, args.deals, args.spec) if (j[0][0], j[0][1], j[3]) not in done]
    print(f"{len(done)} done, {len(todo)} to play", flush=True)
    with out.open("a") as fh, Pool(args.workers, initializer=DB._nice) as pool:
        for n, res in enumerate(pool.imap_unordered(DB.play_deal, todo, chunksize=2), 1):
            rl, ol = res["key"]
            fh.write(json.dumps({"ref": rl, "opp": ol, "seed": res["seed"], "spec": args.spec,
                                 "points": res["points"], "score": sum(res["points"]) / 2}, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 200 == 0:
                print(f"{n}/{len(todo)}", flush=True)


if __name__ == "__main__":
    main()
