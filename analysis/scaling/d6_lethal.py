"""D6: is the lethal screen worth its time? (the architecture thread 2026-10-17 06:26Z; an analysis script, the agents
are not changed). Condition: the opponent's deck list is known (order and hand not).

    python analysis/scaling/d6_lethal.py split   MIRROR --seed S --games G             # 1. the time split
    python analysis/scaling/d6_lethal.py points  MIRROR REC.jsonl.gz ... --want 200 --out P.json   # 2a. lethal starts
    python analysis/scaling/d6_lethal.py convert MIRROR P.json --record-dirs DIR ... --seed-base B --out C.json

MIRROR is ramp (net-gen3-30000, mcts:120) or elft (net-elft-10000, mcts:105): the agents of the J118 timing.

1. `split` plays G self-play games (deal seed S, game g) with the installed-style agent and times, per decision of the
   lethal agent's player: the planner (search.combo via LethalAgent._planned), and the exact search by the budget it
   ran with: full (max_nodes 2000, the damage estimate reaches the opponent's defense), near (1000 nodes, short by 4 or
   less), screen (200 nodes, short by more). The rest of the decision is "other" (the tree search, mostly).
2. `points` replays recorded games and finds every turn's first decision where the lethal agent played a sure lethal
   (the record's search entry is None: no tree search decided it; a fresh lethal agent of the record's own options
   finds a sure line there, and its first step is the recorded action). Each point is tagged with the block that
   found it: planner, full, near or screen. The order is fixed (the analysis line's 92c3292): files by their first
   seed ascending, games by g, decisions by action number. All points are collected; if there are more than --want,
   random.Random(73900000).sample picks --want of them, and they are kept in that fixed order. Point j is the j-th of
   the kept list (j = 0, 1, ...).
   `convert` plays the rest of that turn from each point with the bare tree search (mcts-raw: the same evaluation
   and net, no lethal agent) at the iterations the lethal agent's time buys (ramp 160 = 120 / 0.75, elft 140), once per
   agent seed, and records whether the turn's player won before the turn ended. Point j's agent seeds are
   --seed-base + 3j + r, r = 0..2 (registered: ramp 73900000, elft 73950000).
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import gzip  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

REST = "+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
MIRRORS = {
    "ramp": {"deck": "ramp-t", "net": "analysis/scaling/models/net-gen3-30000.npz", "n": 120, "bare": 160},
    "elft": {"deck": "elf-t", "net": "analysis/scaling/models/net-elft-10000.npz", "n": 105, "bare": 140},
}


def spec(mirror: str, n: int | None = None, raw: bool = False) -> str:
    m = MIRRORS[mirror]
    return f"mcts{'-raw' if raw else ''}:{n or m['n']}{REST}+setnet={m['net']}+neteot"


def _lethal_agent(agent):
    from svsim.agents.lethal_agent import LethalAgent
    a = agent
    for _ in range(6):
        if isinstance(a, LethalAgent):
            return a
        a = getattr(a, "base", None)
        if a is None:
            break
    raise ValueError("no lethal agent in the chain")


def _block(search) -> str:
    """Which budget the last LethalSearch.solve ran with."""
    if search.budget == search.max_nodes:
        return "full"
    if search.near is not None and search.budget == search.near[0]:
        return "near"
    return "screen"


# --- 1. the time split -------------------------------------------------------------------------------------------

def split_main(args) -> None:
    from svsim.agents.lethal_agent import LethalAgent
    from svsim.learn.scaledata import _play
    from svsim.search.lethal import LethalSearch
    acc = {"decision": 0.0, "planner": 0.0, "full": 0.0, "near": 0.0, "screen": 0.0}
    calls = {k: 0 for k in acc}
    plain_planned, plain_solve, plain_act = LethalAgent._planned, LethalSearch.solve, LethalAgent.act

    def planned(self, state):
        t = time.perf_counter()
        r = plain_planned(self, state)
        acc["planner"] += time.perf_counter() - t
        calls["planner"] += 1
        return r

    def solve(self, state):
        t = time.perf_counter()
        r = plain_solve(self, state)
        b = _block(self)
        acc[b] += time.perf_counter() - t
        calls[b] += 1
        return r

    def act(self, state, actions):
        t = time.perf_counter()
        r = plain_act(self, state, actions)
        acc["decision"] += time.perf_counter() - t
        calls["decision"] += 1
        return r

    LethalAgent._planned, LethalSearch.solve, LethalAgent.act = planned, solve, act
    deck = MIRRORS[args.mirror]["deck"]
    for g in range(args.games):
        _play((args.seed, g, deck, deck, spec(args.mirror)))
    total = acc["decision"]
    parts = {k: acc[k] for k in ("planner", "full", "near", "screen")}
    out = {"mirror": args.mirror, "spec": spec(args.mirror), "seed": args.seed, "games": args.games,
           "decisions": calls["decision"], "ms_per_decision": round(1e3 * total / calls["decision"], 2),
           "share_of_decision_time": {**{k: round(v / total, 4) for k, v in parts.items()},
                                      "other": round(1 - sum(parts.values()) / total, 4)},
           "calls": {k: calls[k] for k in parts}}
    _write(args.out, out)


# --- 2a. sure-lethal starts in recorded games ----------------------------------------------------------------------

def _scan(path: str) -> tuple:
    """(points in game / decision order, games, decisions where a lethal exists but another move was recorded)."""
    from svsim.core.engine import legal_actions
    from svsim.core.enums import Phase
    from svsim.search import combo
    from svsim.tools import records as R
    from svsim.tools.arena import make_agent
    agents: dict = {}
    with gzip.open(path, "rt") as fh:
        recs = sorted((json.loads(x) for x in fh if x.strip()), key=lambda r: r["g"])
    points, misplayed = [], 0
    for rec in recs:
        thoughts = rec.get("search") or []
        found_turn = None
        for i, (state, action) in enumerate(R.steps(rec)):
            if state.phase != Phase.MAIN or (i < len(thoughts) and thoughts[i] is not None):
                continue
            if found_turn == (state.turn, state.active):
                continue                                 # the rest of a lethal line already counted
            ai = rec["ai"].split(" / ")[state.active]
            if ai not in agents:                         # _planned and solve keep no state between calls here
                agents[ai] = _lethal_agent(make_agent(ai, 0))
            la = agents[ai]
            line, _ = la._planned(state)
            block = "planner" if line else None
            if not line:
                result = la.search.solve(state)
                if result.sure:
                    line, block = result.line, _block(la.search)
            if not line:
                continue
            first = combo.listed(state, line[0], legal_actions(state))
            if first is None or repr(first) != repr(action):
                misplayed += 1
                continue
            found_turn = (state.turn, state.active)
            points.append({"file": os.path.basename(path), "seed": rec["seed"], "g": rec["g"], "i": i,
                           "turn": state.turn, "player": state.active, "block": block, "line_length": len(line)})
    return points, len(recs), misplayed


def _first_seed(path: str) -> int:
    return int(os.path.basename(path)[len("rec-"):].split(".")[0])


def points_main(args) -> None:
    import random
    from multiprocessing import Pool
    files = sorted(args.records, key=_first_seed)
    with Pool(args.workers) as pool:
        scans = pool.map(_scan, files)                   # in file order
    every = [p for pts, _, _ in scans for p in pts]
    games = sum(n for _, n, _ in scans)
    misplayed = sum(m for _, _, m in scans)
    if args.want and len(every) > args.want:
        keep = sorted(random.Random(73900000).sample(range(len(every)), args.want))
        chosen = [every[k] for k in keep]
    else:
        chosen = every
    for j, p in enumerate(chosen):
        p["j"] = j
    by: dict = {}
    for p in chosen:
        by[p["block"]] = by.get(p["block"], 0) + 1
    found: dict = {}
    for p in every:
        found[p["block"]] = found.get(p["block"], 0) + 1
    _write(args.out, {"mirror": args.mirror, "records": [os.path.basename(f) for f in files], "games": games,
                      "points_found": len(every), "points_per_game": round(len(every) / max(1, games), 3),
                      "found_by_block": found, "not_the_recorded_move": misplayed, "want": args.want,
                      "points": len(chosen), "by_block": by, "list": chosen})


# --- 2b. the bare search on them -----------------------------------------------------------------------------------

def convert_main(args) -> None:
    from svsim.core.engine import apply, legal_actions
    from svsim.tools import records as R
    from svsim.tools.arena import make_agent
    data = json.loads(Path(args.points).read_text())
    folders = [Path(f) for f in args.record_dirs]
    cache: dict = {}

    def record(fname, seed, g):
        if fname not in cache:
            src = next(d / fname for d in folders if (d / fname).exists())
            with gzip.open(src, "rt") as fh:
                cache[fname] = {(r["seed"], r["g"]): r for r in (json.loads(x) for x in fh if x.strip())}
        return cache[fname][(seed, g)]

    n = args.iterations or MIRRORS[args.mirror]["bare"]
    bare = spec(args.mirror, n, raw=True)
    rows = []
    for p in data["list"][:args.limit or None]:
        rec = record(p["file"], p["seed"], p["g"])
        start = next(s for i, (s, a) in enumerate(R.steps(rec)) if i == p["i"])
        me, wins = start.active, []
        seeds = [args.seed_base + 3 * p["j"] + r for r in range(3)]
        for seed in seeds:
            s = start.clone()
            agent = make_agent(bare, seed)
            steps = 0
            while s.winner is None and s.active == me and s.turn == start.turn and steps < 60:
                apply(s, agent.act(s, legal_actions(s)))
                steps += 1
            wins.append(int(s.winner == me))
        rows.append({**{k: p[k] for k in ("j", "file", "seed", "g", "i", "block")}, "agent_seeds": seeds,
                     "wins": wins})
    by: dict = {}
    for r in rows:
        b = by.setdefault(r["block"], [0, 0])
        b[0] += sum(r["wins"])
        b[1] += len(r["wins"])
    total = [sum(v[0] for v in by.values()), sum(v[1] for v in by.values())]
    _write(args.out, {"mirror": args.mirror, "bare_spec": bare, "seed_base": args.seed_base, "points": len(rows),
                      "converted": {k: {"won": v[0], "of": v[1], "rate": round(v[0] / v[1], 4)}
                                    for k, v in sorted(by.items())},
                      "all": {"won": total[0], "of": total[1], "rate": round(total[0] / max(1, total[1]), 4)},
                      "rows": rows})


def _write(path, out) -> None:
    text = json.dumps(out, indent=1) + "\n"
    if path:
        Path(path).write_text(text)
    print(json.dumps({k: v for k, v in out.items() if k not in ("list", "rows")}, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split")
    s.add_argument("mirror", choices=sorted(MIRRORS))
    s.add_argument("--seed", type=int, required=True)
    s.add_argument("--games", type=int, default=10)
    s.add_argument("--out")
    p = sub.add_parser("points")
    p.add_argument("mirror", choices=sorted(MIRRORS))
    p.add_argument("records", nargs="+")
    p.add_argument("--want", type=int, default=200)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--out")
    c = sub.add_parser("convert")
    c.add_argument("mirror", choices=sorted(MIRRORS))
    c.add_argument("points")
    c.add_argument("--record-dirs", nargs="+", required=True)
    c.add_argument("--seed-base", type=int, required=True, help="point j's seeds: B + 3j + r, r = 0..2")
    c.add_argument("--iterations", type=int, default=0)
    c.add_argument("--limit", type=int, default=0)
    c.add_argument("--out")
    args = ap.parse_args()
    {"split": split_main, "points": points_main, "convert": convert_main}[args.cmd](args)


if __name__ == "__main__":
    main()
