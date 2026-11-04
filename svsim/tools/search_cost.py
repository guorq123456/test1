"""Equal compute for a gate: how much longer the search takes per decision with a folder of phased models
than with the installed ones (v2), on the same positions, and the iteration count that evens it out.

    python -m svsim.tools.search_cost svsim/learn/phased_models/<folder> <self-play>.jsonl
    python -m svsim.tools.search_cost <folder> <games>.jsonl --positions 180 --iterations 100 200
    python -m svsim.tools.search_cost - <games>.jsonl [<more>.jsonl] --iterations 200 --fit-alloc   (alloc=legal:K)
    python -m svsim.tools.search_cost - - --whole-games 40 --spec "mcts:200+plan+learned+phased" \
        "mcts:N+plan+learned+phased+alloc=bank" --deck ramp-t --opponent ramp-t       (alloc=bank's N)

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
        getattr(F, "_HAND_MEMO", {}).clear()       # each pass starts cold: the second would see the first's hands
        search = ISMCTS(iterations=iterations, seed=1, weights=PhasedLearned(models=models[name], fallback=Learned()))
        t = time.perf_counter()
        for state in states:
            search.choose(state)
        best[name] = min(best.get(name, 9e9), (time.perf_counter() - t) / len(states))
    return best["v2"], best["new"]


def alloc_cost(states: list, iterations: int, alloc: tuple) -> tuple[float, float, float]:
    """(seconds per decision searching `iterations` each, with the allocation `alloc` (mcts ISMCTS.alloc),
    mean iterations with it), the installed models, best of two passes each. Positions with one legal move
    are left out: the agent plays those without a search either way (agents.mcts_agent)."""
    from svsim.core.engine import legal_actions
    from svsim.learn import features as F
    from svsim.learn.model import Learned
    from svsim.learn.phased import PhasedLearned, load
    from svsim.search.mcts import ISMCTS
    states = [s for s in states if len(legal_actions(s)) > 1]
    models, best, spent = load(), {}, []
    for name in ("uniform", "alloc", "uniform", "alloc"):
        F._UNSEEN.clear()
        getattr(F, "_HAND_MEMO", {}).clear()
        search = ISMCTS(iterations=iterations, seed=1, weights=PhasedLearned(models=models, fallback=Learned()),
                        alloc=alloc if name == "alloc" else None)
        t = time.perf_counter()
        for state in states:
            search.choose(state)
            if name == "alloc":
                spent.append(search.last_iterations)
        best[name] = min(best.get(name, 9e9), (time.perf_counter() - t) / len(states))
    return best["uniform"], best["alloc"], sum(spent) / len(spent)


def fit_alloc(states: list, iterations: int, lo: int = 50, hi: int = 800, tol: float = 0.03) -> float:
    """The K of alloc=legal:K:lo:hi whose time per decision is within `tol` of `iterations` each (bisection on
    log K; prints each step)."""
    import math
    a, b = math.log(2.0), math.log(120.0)
    k = None
    for _ in range(14):
        k = round(math.exp((a + b) / 2), 2)
        uniform, alloc, mean = alloc_cost(states, iterations, ("legal", k, lo, hi))
        print(f"  K {k}: uniform {uniform * 1000:.1f} ms, alloc {alloc * 1000:.1f} ms ({alloc / uniform - 1:+.1%}), "
              f"mean {mean:.0f} iterations", flush=True)
        if abs(alloc / uniform - 1) <= tol:
            break
        a, b = (math.log(k), b) if alloc < uniform else (a, math.log(k))
    return k


def _whole_game(job) -> tuple:
    """One self-play game of `spec` on `seed`: (seconds on searched decisions, searched decisions, all decisions,
    iterations searched, seconds on all decisions). A searched decision is one the search ran (search.last_iterations
    set), as gate's ms / ms_b count: moves with one legal action and lethal-check returns are left out."""
    spec, deck, opponent, seed = job
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    from svsim.ui.session import DECKS
    agents = [make_agent(spec, 2 * seed + i) for i in range(2)]
    searches = [_search(a) for a in agents]
    state = new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1]), seed=seed)
    searched_s, searched, decisions, iterations, all_s = 0.0, 0, 0, 0, 0.0
    while not state.over:
        search = searches[state.active]
        if search is not None:
            search.last_iterations = None
        t = time.perf_counter()
        action = agents[state.active].act(state, legal_actions(state))
        took = time.perf_counter() - t
        all_s += took
        decisions += 1
        if search is not None and search.last_iterations is not None:
            searched_s += took
            searched += 1
            iterations += search.last_iterations
        apply(state, action)
    return searched_s, searched, decisions, iterations, all_s


def game_cost(spec: str, deck: str, opponent: str, games: int, seed: int, workers: int = 1) -> dict:
    """Whole self-play games of `spec` (both seats) on seeds seed .. seed + games - 1: seconds per searched decision
    (the search ran: gate's ms definition), seconds per game searching and in all, searched and all decisions and
    iterations per game. For allocations that carry over between decisions
    (alloc=bank), which single positions can't show; run it on an idle machine."""
    from multiprocessing import Pool
    jobs = [(spec, deck, opponent, seed + g) for g in range(games)]
    if workers > 1:
        with Pool(workers) as pool:
            out = pool.map(_whole_game, jobs)
    else:
        out = [_whole_game(j) for j in jobs]
    secs, searched, decs, its, all_s = (sum(x[i] for x in out) for i in range(5))
    return {"spec": spec, "games": games, "s_per_decision": secs / max(1, searched), "s_per_game": all_s / games,
            "searched_per_game": searched / games, "decisions_per_game": decs / games,
            "iterations_per_game": its / games, "search_s_per_game": secs / games}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder")
    parser.add_argument("games", nargs="+", help="self-play records (learn.netdata) of the pairing the folder is "
                        "for; with several files, --positions from each")
    parser.add_argument("--positions", type=int, default=180)
    parser.add_argument("--iterations", type=int, nargs="+", default=[100])
    parser.add_argument("--alloc", help="legal:K[:LO:HI]: time it against uniform --iterations (the folder unused)")
    parser.add_argument("--fit-alloc", action="store_true", help="find the K of alloc=legal:K that matches "
                        "uniform --iterations within 3%% (the folder unused)")
    parser.add_argument("--whole-games", type=int, metavar="N", help="time N whole self-play games of each --spec "
                        "(both seats) on the same seeds instead (the folder and records unused; alloc=bank's N)")
    parser.add_argument("--spec", nargs="+", default=[], help="with --whole-games: arena specs to compare")
    parser.add_argument("--deck", default="ramp-t")
    parser.add_argument("--opponent", default="ramp-t")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--workers", type=int, default=1, help="with --whole-games (1 for the cleanest timing)")
    args = parser.parse_args()
    if args.whole_games:
        base = None
        for spec in args.spec:
            r = game_cost(spec, args.deck, args.opponent, args.whole_games, args.seed, args.workers)
            base = base or r
            print(f"{spec}: {r['s_per_decision'] * 1000:.1f} ms per searched decision "
                  f"({r['s_per_decision'] / base['s_per_decision'] - 1:+.1%}); per game {r['search_s_per_game']:.1f} s "
                  f"searching ({r['search_s_per_game'] / base['search_s_per_game'] - 1:+.1%}), {r['s_per_game']:.1f} s "
                  f"in all, {r['searched_per_game']:.1f} searched of {r['decisions_per_game']:.1f} decisions, "
                  f"{r['iterations_per_game']:.0f} iterations ({args.whole_games} games, {args.deck} vs "
                  f"{args.opponent}, seeds {args.seed}..)", flush=True)
        return
    if args.alloc or args.fit_alloc:
        from svsim.tools.arena import _alloc_option
        states = [x for path in args.games for x in positions(path, args.positions)]
        its = args.iterations[0]
        if args.fit_alloc:
            lo, hi = _alloc_option([f"alloc={args.alloc}"])[2:] if args.alloc else (50, 800)
            print(f"alloc=legal:{fit_alloc(states, its, lo, hi)} matches {its} iterations", flush=True)
        else:
            uniform, alloc, mean = alloc_cost(states, its, _alloc_option([f"alloc={args.alloc}"]))
            print(f"{its} iterations: {uniform * 1000:.1f} ms; alloc={args.alloc}: {alloc * 1000:.1f} ms "
                  f"({alloc / uniform - 1:+.1%}), mean {mean:.0f} iterations", flush=True)
        return
    folder = Path(args.folder)
    states = [x for path in args.games for x in positions(path, args.positions)]
    for its in args.iterations:
        v2, new = cost(folder, states, its)
        print(f"{its} iterations ({len(states)} positions): v2 {v2 * 1000:.1f} ms, {folder.name} {new * 1000:.1f} ms "
              f"({1 - v2 / new:.0%} fewer iterations) -> equal compute {round(its * v2 / new)}", flush=True)


if __name__ == "__main__":
    main()
