"""D8 (analysis line, registered in 95dc772 before any prior numbers): how often a second run of the same search,
with another seed, picks the recorded search's most-visited move - a reference for the move prior's top-1 agreement
(O1). The same scan also gives O1's two prior-free baselines (uniform, the current expansion order) on every
holdout decision. Condition: the opponent's deck list is known (order and hand not).

    cd <checkout of 81e3b3f> && PYTHONPATH=. python3 d8.py scan  REC.jsonl.gz --out scan.json --workers 4
    cd <checkout of 81e3b3f> && PYTHONPATH=. python3 d8.py rerun REC.jsonl.gz --scan scan.json --seed-base B \
        --sample-seed 74800000 --points 2000 --out rerun.json --workers 4

Decisions (O1's main population): MAIN phase, record["search"][i] not None, sum of visits > 0, at least two distinct
search.mcts.action_key among the legal moves. Moves are merged by key (the recorded visits repeat a key's count for
each of its legal moves); a key's visits are taken once. start = the turn's first MAIN step (learn.policy.decisions).
Expansion order: ISMCTS._options(state, me, None) of the recorded agent's search (reserve / veto / prune, _rank).
"""
import argparse, gzip, json, os, random
from multiprocessing import Pool

import numpy as np


_CACHE = {}


def _load(path):
    if path not in _CACHE:
        _CACHE[path] = [json.loads(x) for x in gzip.open(path, "rt") if x.strip()]
    return _CACHE[path]


def _spec(rec):
    a, b = rec["ai"].split(" / ")
    assert a == b, rec["ai"]
    return a


def _decisions(rec, search_for_order=None):
    """Yield (i, state (live: use before advancing), legal, keys, key_of_legal, key_visits, start) at every decision of
    the main population."""
    from svsim.core.actions import EndTurn
    from svsim.core.engine import legal_actions
    from svsim.core.enums import Phase
    from svsim.search.mcts import _locator, action_key
    from svsim.tools import records as R
    thoughts = rec.get("search") or []
    last_turn = None
    for i, (state, action) in enumerate(R.steps(rec)):
        t = thoughts[i] if i < len(thoughts) else None
        start = state.phase == Phase.MAIN and state.turn != last_turn
        if state.phase == Phase.MAIN:
            last_turn = state.turn
        if t is None or state.phase != Phase.MAIN:
            continue
        legal = legal_actions(state)
        v = t["visits"]
        if len(legal) != len(v):
            raise RuntimeError(f"g {rec['g']} i {i}: {len(legal)} legal, {len(v)} visits")
        if sum(v) <= 0:
            continue
        where = _locator(state, state.active)
        keys, idx, kv, bad = [], {}, [], 0
        key_of = []
        for a, x in zip(legal, v):
            k = action_key(state, a, where)
            if k not in idx:
                idx[k] = len(keys)
                keys.append(k)
                kv.append(x)
            elif kv[idx[k]] != x:
                bad += 1
            key_of.append(idx[k])
        end = next((key_of[j] for j, a in enumerate(legal) if isinstance(a, EndTurn)), None)
        yield i, state, legal, keys, key_of, kv, start, end, bad, len(legal)


def _scan_game(job):
    path, gs = job
    from svsim.tools.arena import make_agent
    from svsim.learn.netdata import _search
    recs = {r["g"]: r for r in _load(path) if r["g"] in gs}
    out, searches = [], {}
    for g in sorted(recs):
        rec = recs[g]
        spec = _spec(rec)
        if spec not in searches:
            searches[spec] = _search(make_agent(spec, 0))
        search = searches[spec]
        for i, state, legal, keys, key_of, kv, start, end, bad, n_legal in _decisions(rec):
            order = list(search._options(state, state.active, None))
            pos = {k: j for j, k in enumerate(keys)}
            exp = [pos.get(k, -1) for k in order[:2]]
            out.append({"g": g, "i": i, "start": bool(start), "n_legal": n_legal, "visits": kv, "end": end,
                        "exp": exp, "n_options": len(order), "dup_mismatch": bad})
    return out


def scan_main(args):
    recs = _load(args.records)
    games = sorted(r["g"] for r in recs)
    chunks = [(args.records, set(games[k::args.workers * 4])) for k in range(args.workers * 4)]
    rows = []
    with Pool(args.workers) as pool:
        for part in pool.imap_unordered(_scan_game, chunks):
            rows.extend(part)
    rows.sort(key=lambda r: (r["g"], r["i"]))
    json.dump({"records": os.path.basename(args.records), "games": len(games), "rows": rows}, open(args.out, "w"))
    print(len(games), "games,", len(rows), "decisions")


def _rerun_point(job):
    path, j, g, i, seed = job
    from svsim.core.engine import legal_actions
    from svsim.learn.netdata import _search
    from svsim.search.mcts import _locator, action_key
    from svsim.tools.arena import make_agent
    rec = next(r for r in _load(path) if r["g"] == g)
    for i2, state, legal, keys, key_of, kv, start, end, bad, n_legal in _decisions(rec):
        if i2 != i:
            continue
        agent = make_agent(_spec(rec), seed)
        search = _search(agent)
        search.last_root = None
        s = state.clone()
        agent.act(s, legal_actions(s))
        root = search.last_root
        if root is None or not root.children:
            return {"j": j, "g": g, "i": i, "seed": seed, "outer": True}
        where = _locator(state, state.active)
        pos = {k: n for n, k in enumerate(keys)}
        rv = [0] * len(keys)
        for k, child in root.children.items():
            if k in pos:
                rv[pos[k]] = child.visits
        return {"j": j, "g": g, "i": i, "seed": seed, "outer": False, "rerun": rv,
                "unmatched_children": sum(1 for k in root.children if k not in pos)}
    raise RuntimeError(f"point g {g} i {i} not found")


def rerun_main(args):
    scan = json.load(open(args.scan))
    rows = scan["rows"]
    pick = sorted(random.Random(args.sample_seed).sample(range(len(rows)), min(args.points, len(rows))))
    jobs = [(args.records, j, rows[n]["g"], rows[n]["i"], args.seed_base + j) for j, n in enumerate(pick)]
    out = []
    with Pool(args.workers) as pool:
        for k, r in enumerate(pool.imap(_rerun_point, jobs, chunksize=4)):
            out.append(r)
            if (k + 1) % 200 == 0:
                print(k + 1, "points", flush=True)
    json.dump({"records": os.path.basename(args.records), "sample_seed": args.sample_seed,
               "seed_base": args.seed_base, "picked": pick, "points": out}, open(args.out, "w"))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("records")
    s.add_argument("--out", required=True)
    s.add_argument("--workers", type=int, default=4)
    r = sub.add_parser("rerun")
    r.add_argument("records")
    r.add_argument("--scan", required=True)
    r.add_argument("--seed-base", type=int, required=True)
    r.add_argument("--sample-seed", type=int, default=74800000)
    r.add_argument("--points", type=int, default=2000)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    {"scan": scan_main, "rerun": rerun_main}[args.cmd](args)


if __name__ == "__main__":
    main()
