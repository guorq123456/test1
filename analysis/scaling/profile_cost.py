"""Where a decision's time goes (the architecture thread 2026-10-18 17:17Z; report only, nothing changed).

On a holdout's recorded games (no game is played, so no seed is drawn), the spec's agent decides at every
main-phase step, the game going on by the recorded move. There is one agent per side and game (make_agent(spec,
side)), so what an agent keeps between its decisions is kept as in play (`--mode game`, the default). `--mode
positions` instead gives a fresh agent at each searched decision, as puct_cost.py does; it overstates what is
cached across a turn, such as the lethal check's "no lethal this turn" stamp. One pass times agent.act plainly
(the wall per decision). A second pass runs it under cProfile, and each function's own time
goes to a part by where it lives:
- state copy: GameState / card clone and copy functions (svsim/core, copy.*);
- simulator: the rest of svsim/core and svsim/cards (rules, legal moves, applying moves);
- value net: learn/setnet.py and learn/tokens.py (the encoding and the forward pass);
- prior: learn/setpolicy.py (the move prior's forward pass);
- tree search: search/mcts.py (selection, expansion, backup, determinization);
- lethal and plans: search/lethal.py, combo.py, formula.py, turnplan.py, candidates.py, race.py;
- linear models: learn/phased.py, model.py, features.py and search/evaluate.py (the in-turn and other scores);
- other: everything else (search/xprune.py among them).
A C function (a numpy operation, a builtin) has no file of its own, so its time goes to its callers' parts, in
proportion to the time each caller spent in it. The profiler's own overhead lands mostly on code with many small
Python calls, so the shares under it are a guide, and the plain pass gives the wall.

    python analysis/scaling/profile_cost.py --records REC --games 3 --spec NAME=SPEC ... --out OUT
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import cProfile  # noqa: E402
import gzip      # noqa: E402
import json      # noqa: E402
import pstats    # noqa: E402
import sys       # noqa: E402
import time      # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

PARTS = ("state copy", "simulator", "value net", "prior", "tree search", "lethal and plans", "linear models", "other")
_PLANS = ("lethal.py", "combo.py", "formula.py", "turnplan.py", "candidates.py", "race.py")
_LINEAR = ("phased.py", "model.py", "features.py", "evaluate.py")


def part_of(fn: tuple) -> str | None:
    """The part of a profiled function (file, line, name); None for a C function."""
    path, _line, name = fn
    if path == "~" or path.startswith("<"):
        return None
    p = path.replace("\\", "/")
    base = p.rsplit("/", 1)[-1]
    if p.endswith("/copy.py") or ("/svsim/core/" in p and ("clone" in name or "copy" in name)):
        return "state copy"
    if "/svsim/core/" in p or "/svsim/cards/" in p:
        return "simulator"
    if p.endswith("learn/setnet.py") or p.endswith("learn/tokens.py"):
        return "value net"
    if p.endswith("learn/setpolicy.py"):
        return "prior"
    if p.endswith("search/mcts.py"):
        return "tree search"
    if "/svsim/search/" in p and base in _PLANS:
        return "lethal and plans"
    if ("/svsim/learn/" in p or "/svsim/search/" in p) and base in _LINEAR:
        return "linear models"
    return "other"


def parts(stats: pstats.Stats) -> dict:
    """Own time per part, a C function's time split over its callers' parts."""
    raw = stats.stats
    out = {p: 0.0 for p in PARTS}

    def owner(fn, depth=0):
        """The part a function's time goes to (a C function: its callers', weighted)."""
        part = part_of(fn)
        if part is not None:
            return {part: 1.0}
        callers = raw[fn][4]
        total = sum(v[2] for v in callers.values()) or 1.0
        mix: dict = {}
        for caller, v in callers.items():
            if depth > 8 or caller not in raw:
                share = {"other": 1.0}
            else:
                share = owner(caller, depth + 1)
            for k, w in share.items():
                mix[k] = mix.get(k, 0.0) + w * v[2] / total
        return mix or {"other": 1.0}

    for fn, (_cc, _nc, tt, _ct, _callers) in raw.items():
        for k, w in owner(fn).items():
            out[k] += tt * w
    return out


def timers(run) -> dict:
    """Inclusive wall time in a few methods during run(), each wrapped by a timer (no profiler): GameState.clone,
    the value net's SetNet.logit, the prior's SetPolicy.priors, the lethal search's LethalSearch.solve (which
    clones and moves too), view.determinize as the search calls it."""
    from svsim.core.state import GameState
    from svsim.learn.setnet import SetNet
    from svsim.learn.setpolicy import SetPolicy
    from svsim.search import mcts
    from svsim.search.lethal import LethalSearch
    spent = {"GameState.clone": 0.0, "SetNet.logit": 0.0, "SetPolicy.priors": 0.0, "LethalSearch.solve": 0.0,
             "determinize": 0.0}
    timers.calls = {k: 0 for k in spent}
    saved = []

    def wrap(owner, attr, key):
        f = getattr(owner, attr)
        saved.append((owner, attr, f))

        def timed(*a, **k):
            t0 = time.perf_counter()
            try:
                return f(*a, **k)
            finally:
                spent[key] += time.perf_counter() - t0
                timers.calls[key] += 1
        setattr(owner, attr, timed)

    wrap(GameState, "clone", "GameState.clone")
    wrap(SetNet, "logit", "SetNet.logit")
    wrap(SetPolicy, "priors", "SetPolicy.priors")
    wrap(LethalSearch, "solve", "LethalSearch.solve")
    wrap(mcts, "determinize", "determinize")
    t0 = time.perf_counter()
    try:
        run()
    finally:
        for owner, attr, f in saved:
            setattr(owner, attr, f)
    spent["wall"] = time.perf_counter() - t0
    return spent


timers.calls = {}


def decisions_of(records: str, games: int, mode: str):
    """[(game, side or None, state)] in play order: "game", every main-phase step of the first `games` records
    (an agent per side keeps its state through the game, as in play: the lethal check's stamp, search.xprune's
    memory); "positions", the searched decisions of learn.setpolicy.decisions (a fresh agent each, as in
    puct_cost.py)."""
    from svsim.core.enums import Phase
    from svsim.learn import setpolicy as SP
    from svsim.tools import records as R
    out = []
    with gzip.open(records, "rt") as fh:
        for g, line in enumerate(fh):
            if g >= games:
                break
            rec = json.loads(line)
            if mode == "positions":
                out += [(g, None, state.clone()) for _i, state, *_ in SP.decisions(rec)]
            else:
                out += [(g, state.active, state.clone()) for state, _a in R.steps(rec) if state.phase == Phase.MAIN]
    return out


def play_through(spec: str, positions, hook) -> None:
    """hook(agent, state, legal) at each position, on a clone; one agent per (game, side), or a fresh one."""
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    agents = {}
    for g, side, state in positions:
        if side is None:
            agent = make_agent(spec, 0)
        else:
            agent = agents.get((g, side))
            if agent is None:
                agent = agents[(g, side)] = make_agent(spec, side)
        s = state.clone()
        hook(agent, s, legal_actions(s))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", required=True)
    ap.add_argument("--games", type=int, default=3)
    ap.add_argument("--spec", action="append", required=True, metavar="NAME=SPEC")
    ap.add_argument("--mode", choices=("game", "positions"), default="game")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from svsim.tools.arena import make_agent
    specs = [s.split("=", 1) for s in args.spec]
    for _, spec in specs:                                 # load every net once before timing
        make_agent(spec, 0)
    positions = decisions_of(args.records, args.games, args.mode)
    n = len(positions)
    report = {"records": Path(args.records).name, "games": args.games, "mode": args.mode, "decisions": n,
              "specs": {}}
    for name, spec in specs:
        t0 = time.perf_counter()
        play_through(spec, positions, lambda agent, s, legal: agent.act(s, legal))
        wall = time.perf_counter() - t0
        prof = cProfile.Profile()

        def profiled(agent, s, legal):
            prof.enable()
            agent.act(s, legal)
            prof.disable()
        play_through(spec, positions, profiled)
        timed = timers(lambda: play_through(spec, positions, lambda agent, s, legal: agent.act(s, legal)))
        by_part = parts(pstats.Stats(prof))
        total = sum(by_part.values())
        report["specs"][name] = {
            "spec": spec, "ms_per_decision": round(1e3 * wall / n, 2),
            "profiled_ms_per_decision": round(1e3 * total / n, 2),
            "share": {k: round(v / total, 4) for k, v in by_part.items()},
            "ms_per_decision_by_part": {k: round(1e3 * wall / n * v / total, 2) for k, v in by_part.items()},
            "timers_ms_per_decision": {k: round(1e3 * v / n, 2) for k, v in timed.items()},
            "timers_calls_per_decision": {k: round(c / n, 1) for k, c in timers.calls.items()}}
        print(json.dumps({name: report["specs"][name]}, indent=1), flush=True)
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
