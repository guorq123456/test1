"""Search the move prior's decisions again with another player (the architecture thread 2026-10-18 12:19Z: relabel
the ramp-t prior's data with A's scorer, no prior, UCB1, N 200, then refit the prior on the new visits).

For each record of a shard, at each decision of learn.setpolicy.decisions (the prior's data: a searched main-phase
decision with two distinct moves or more), the position is searched by a new agent of SPEC and its root visits per
legal move are written in the record's "search" entry, in learn.netdata._thought's format ({"visits", "value",
"center"}). The other entries are None, and so are decisions left out by the thinning (each decision is kept with
probability RATE, from a generator seeded by (SEED_BASE, k)). So setpolicy's encode reads the output as it reads a
self-play shard, and its decisions are the re-searched ones. Everything else in the record is as it was; the record
also gets "relabel": {spec, seed_base, rate}.

The agent of a decision has the seed SEED_BASE + 1000000 k + 1000 g + i (k the shard's index, g the game, i the
action's index). A fresh agent per decision keeps a decision's search independent of the others (search.xprune's
cross-turn memory starts empty).

    python analysis/scaling/relabel.py --records DIR --base 72300000 --stride 2 --shards K0 K1 --spec SPEC \\
        --seed-base B [--rate 1.0] --out DIR [--workers 4]
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import gzip      # noqa: E402
import json      # noqa: E402
import sys       # noqa: E402
import time      # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))


def relabel_record(rec: dict, spec: str, seed_base: int, k: int, rng, rate: float = 1.0) -> tuple[dict, int]:
    """(a copy of rec whose "search" holds the new searches only, the number of decisions searched)."""
    from svsim.core.engine import legal_actions
    from svsim.learn.netdata import _search, _thought
    from svsim.learn.setpolicy import decisions
    from svsim.tools.arena import make_agent
    out = dict(rec)
    search = [None] * len(rec["actions"])
    n = 0
    for i, state, legal, *_ in decisions(rec):
        if rng.random() >= rate:
            continue
        agent = make_agent(spec, seed_base + 1_000_000 * k + 1000 * int(rec["g"]) + i)
        s = state.clone()
        agent.act(s, legal_actions(s))
        search[i] = _thought(state, legal, _search(agent))
        n += 1
    out["search"] = search
    out["relabel"] = {"spec": spec, "seed_base": seed_base, "rate": rate}
    return out, n


def _shard(job):
    path, target, spec, seed_base, k, rate = job
    rng = np.random.default_rng([seed_base, k])
    t0 = time.process_time()
    games = searched = 0
    tmp = str(target) + ".part"
    with gzip.open(path, "rt") as fh, gzip.open(tmp, "wt") as out:
        for line in fh:
            if not line.strip():
                continue
            rec, n = relabel_record(json.loads(line), spec, seed_base, k, rng, rate)
            out.write(json.dumps(rec) + "\n")
            games += 1
            searched += n
    os.replace(tmp, target)
    return str(target), games, searched, round(time.process_time() - t0, 1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", required=True, help="the folder of the shards' rec-<seed>.jsonl.gz")
    ap.add_argument("--base", type=int, required=True)
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--shards", type=int, nargs=2, required=True, metavar=("K0", "K1"), help="k in [K0, K1)")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--seed-base", type=int, required=True)
    ap.add_argument("--rate", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    from multiprocessing import Pool
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = []
    for k in range(*args.shards):
        s = args.base + args.stride * k
        target = out / f"rec-{s}.jsonl.gz"
        if not target.exists():
            jobs.append((str(Path(args.records) / f"rec-{s}.jsonl.gz"), target, args.spec, args.seed_base, k,
                         args.rate))
    print(json.dumps({"spec": args.spec, "seed_base": args.seed_base, "rate": args.rate,
                      "shards_to_search": [Path(j[1]).name for j in jobs]}), flush=True)
    with Pool(args.workers) as pool:
        for target, games, searched, cpu in pool.imap_unordered(_shard, jobs):
            print(json.dumps({"file": Path(target).name, "games": games, "searched": searched, "cpu_s": cpu,
                              "ms_per_search": round(1e3 * cpu / max(searched, 1), 1)}), flush=True)


if __name__ == "__main__":
    main()
