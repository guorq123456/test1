"""Equal compute for a gate: how much longer the search takes per decision with a folder of phased models
than with the installed ones (v2), on the same positions, and the iteration count that evens it out.

    python -m svsim.tools.search_cost svsim/learn/phased_models/<folder> <self-play>.jsonl
    python -m svsim.tools.search_cost <folder> <games>.jsonl --positions 180 --iterations 100 200

The way b1's gate was set (2026-10-07): every 7th main-phase step of the self-play records until there
are --positions of them, a bare ISMCTS (no planner, no lethal check) with each set of models, each timed
twice and the faster pass kept; A's iterations = round(iterations x v2's time / the folder's time).
Run it with nothing else on the machine: it measures wall time.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def positions(path: str, n: int) -> list:
    from svsim.core.enums import Phase
    from svsim.tools import records as R
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            for i, (state, _) in enumerate(R.steps(json.loads(line))):
                if state.phase == Phase.MAIN and i % 7 == 3:
                    out.append(state.clone())
            if len(out) >= n:
                break
    return out


def cost(folder: Path, states: list, iterations: int) -> tuple[float, float]:
    """(seconds per decision with the installed models, with `folder`'s), best of two passes each."""
    from svsim.learn import features as F
    from svsim.learn.model import Learned
    from svsim.learn.phased import PhasedLearned, load
    from svsim.search.mcts import ISMCTS
    models = {"v2": load(), "new": load(folder)}
    best = {}
    for name in ("v2", "new", "v2", "new"):
        F._UNSEEN.clear()
        search = ISMCTS(iterations=iterations, seed=1, weights=PhasedLearned(models=models[name], fallback=Learned()))
        t = time.perf_counter()
        for state in states:
            search.choose(state)
        best[name] = min(best.get(name, 9e9), (time.perf_counter() - t) / len(states))
    return best["v2"], best["new"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder")
    parser.add_argument("games", help="self-play records (learn.netdata) of the pairing the folder is for")
    parser.add_argument("--positions", type=int, default=180)
    parser.add_argument("--iterations", type=int, nargs="+", default=[100])
    args = parser.parse_args()
    folder = Path(args.folder)
    states = positions(args.games, args.positions)
    for its in args.iterations:
        v2, new = cost(folder, states, its)
        print(f"{its} iterations ({len(states)} positions): v2 {v2 * 1000:.1f} ms, {folder.name} {new * 1000:.1f} ms "
              f"({1 - v2 / new:.0%} fewer iterations) -> equal compute {round(its * v2 / new)}", flush=True)


if __name__ == "__main__":
    main()
