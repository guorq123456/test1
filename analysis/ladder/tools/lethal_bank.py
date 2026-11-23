"""2.2: the lethal puzzle bank's acceptance (plan 阶段 2: 「精确的斩杀检测 ... 建一个斩杀题库来验收：题目取自模拟器里
能穷举验证的局面，有斩杀的题必须全部找到」).

    python analysis/ladder/tools/lethal_bank.py --source ladder --seeds LO HI --games N --out DIR [--tries 3]
                                                [--nodes 300000] [--workers 4]
    python analysis/ladder/tools/lethal_bank.py --source bank --out DIR       (tests/puzzles, kind "lethal")

Positions: the first decision of every turn (main phase, after the draw) of games played through the referee, the
base's Tracker kept from the first move (so the seat's public position is the one it has in a real game):
- ladder: the default strategy against itself on the ladder's lists (submit.public_lists: the seven baselines and the
  public lists, a class and a list of it drawn for each side);
- random: random play (svsim RandomAgent, end_turn_weight 0.2, as svsim.tools.lethal) on random decks of every class
  (svsim decks.random_deck): more lethals and stranger boards;
- bank: the "lethal" puzzles of the simulator's own bank (tests/puzzles, Salem's), each on --tries build seeds; the
  Tracker starts at the puzzle (the opponent's hand all unknown).
The exact lethal search (svsim.search.lethal.LethalSearch: no screening, sure lethals only, --nodes) decides each
position on the real state: a sure lethal (a line that wins this turn whatever the deck order and the random results)
is a puzzle; a search that finishes without one proves there is none; one that runs out of nodes is counted, not used.
Each puzzle is played from that position to the end of the turn by the default strategy behind the base
(strategy.BotStrategy mcts:100+plan: the ladder's information condition, the opponent's cards drawn from the default
guess) with --tries strategy seeds, on clones of the real state; also by LETHAL "exact" (mcts:100, the interface's
other setting). Found = the opponent's leader at 0 before the turn ends. For every miss: the default's own lethal
budgets (2000 nodes, screen 200, near (1000, 4), svsim.agents.lethal_agent) on the real state, and the exact search on
4 states the seat could be in (base.sample from the default guess): is the lethal sure from what the seat knows?

A measurement of the base only: these games say nothing about strength. The seeds are the host's measurement range.
"""
from __future__ import annotations

import argparse
import copy
import json
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = LADDER.parents[1]
sys.path[:0] = [str(LADDER), str(ROOT)]

MODES = {"planner": "mcts:100+plan", "exact": "mcts:100"}
# --budgets: the lethal search alone at other budgets on every turn start (the real state), its finds and its time
# (what a fuller search would cost; analysis/speed/LETHAL.md measured the same on the Ramp mirror, known lists)
BUDGETS = {"default": (2000, 200, (1000, 4)), "lethal2": (3000, 200, (2000, 4)), "noscreen2000": (2000, None, None),
           "noscreen20000": (20000, None, None)}


def _init():
    sys.path[:0] = [str(LADDER), str(ROOT)]
    import svsim.cards.library  # noqa: F401


def exact(state, nodes: int):
    from svsim.search.lethal import LethalSearch
    r = LethalSearch(max_nodes=nodes, sure_only=True).solve(state.clone())
    return r


def play_turn(state, tracker, spec: str, seed: int, max_actions: int = 80) -> dict:
    """The rest of the mover's turn from here, by `spec` behind the base, on a clone. Won = the opponent's leader at 0
    before the turn passes."""
    from svsim.core.engine import apply, legal_actions
    from ladder import base
    from ladder.strategy import BotStrategy
    s, tr = state.clone(), copy.deepcopy(tracker)
    me, turn = s.active, s.turn
    strat = BotStrategy(spec=spec, seed=seed)
    n = 0
    while not s.over and s.active == me and s.turn == turn and n < max_actions:
        actions = legal_actions(s)
        pos = base.public_position(s, me, tr)
        a = strat.act(pos, actions)
        tr.before(s)
        apply(s, a)
        tr.after(s)
        n += 1
    return {"won": s.winner == me, "actions": n, "enemy_hp": max(0, s.players[1 - me].leader_hp)}


def diagnose(state, tracker, nodes: int, seed: int) -> dict:
    """Why a miss: the default's own budgets on the real state; the exact search on states the seat could be in."""
    from svsim.agents.lethal_agent import NEAR
    from svsim.search.lethal import LethalSearch, damage_estimate
    from ladder import base
    r = LethalSearch(max_nodes=2000, screen=200, near=NEAR, seed=seed).solve(state.clone())
    pos = base.public_position(state, state.active, tracker)
    rng = random.Random(seed)
    guess = base.default_guess(pos.opp_craft)
    sure = []
    for _ in range(4):
        s, _ = base.sample(pos, guess, rng)
        sure.append(bool(exact(s, nodes).sure))
    est = damage_estimate(state)
    return {"default_budget_finds": bool(r.sure), "default_screened": bool(r.screened), "default_nodes": r.nodes,
            "estimate_short": None if est == float("inf") else round(state.players[1 - state.active].leader_hp - est, 1),
            "sure_on_samples": sure}


def budgets(state, seed: int) -> dict:
    from svsim.search.lethal import LethalSearch
    out = {}
    for name, (nodes, screen, near) in BUDGETS.items():
        t0 = time.perf_counter()
        r = LethalSearch(max_nodes=nodes, screen=screen, near=near, seed=seed).solve(state.clone())
        out[name] = [bool(r.sure), round((time.perf_counter() - t0) * 1000, 1)]
    return out


def examine(state, tracker, ctx: dict, where: dict) -> dict:
    if ctx.get("budgets"):
        me = state.active
        return dict(where, turn=state.turn, me=me, enemy_hp=state.players[1 - me].leader_hp,
                    budgets=budgets(state, ctx["seed"] * 1000 + state.turn * 10))
    t0 = time.perf_counter()
    r = exact(state, ctx["nodes"])
    me = state.active
    rec = dict(where, turn=state.turn, me=me, enemy_hp=state.players[1 - me].leader_hp,
               lethal=bool(r.sure), complete=bool(r.complete), nodes=r.nodes,
               search_s=round(time.perf_counter() - t0, 2))
    if not r.sure:
        return rec
    rec["line"] = len(r.line)
    rec["tries"] = {}
    base_seed = ctx["seed"] * 1000 + state.turn * 10
    for mode, spec in MODES.items():
        rec["tries"][mode] = [play_turn(state, tracker, spec, base_seed + t) for t in range(ctx["tries"])]
    if not all(t["won"] for ts in rec["tries"].values() for t in ts):
        rec["why"] = diagnose(state, tracker, ctx["nodes"], base_seed)
    return rec


def _decks(source: str, rng: random.Random):
    from ladder.runner import load_deck  # noqa: F401
    from svsim.cards.pool import card
    if source == "ladder":
        from ladder.submit import public_lists
        lists = public_lists()
        crafts = sorted(lists)
        out = []
        for _ in range(2):
            ids = rng.choice(lists[rng.choice(crafts)])
            out.append([card(i) for i in ids])
        return out
    from svsim.cards import decks
    from svsim.core.enums import Craft
    crafts = [c for c in Craft if c != Craft.NEUTRAL]
    return [decks.random_deck(rng.choice(crafts), rng) for _ in range(2)]


def game(job: dict) -> dict:
    """One game; every turn start examined."""
    from svsim.agents.random_agent import RandomAgent
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.core.enums import Phase
    from ladder import base
    from ladder.strategy import BotStrategy
    seed, source = job["seed"], job["source"]
    rng = random.Random(f"lethal-bank:{source}:{seed}")
    d0, d1 = _decks(source, rng)
    state = new_game(d0, d1, seed=seed)
    tracker = base.Tracker(state)
    if source == "ladder":
        drivers = [BotStrategy(seed=2 * seed + i) for i in (0, 1)]
    else:
        drivers = [RandomAgent(2 * seed + i, 0.2) for i in (0, 1)]
    recs, last = [], None
    t0 = time.perf_counter()
    while not state.over:
        seat = state.active
        actions = legal_actions(state)
        if state.phase == Phase.MAIN and (state.turn, seat) != last:
            last = (state.turn, seat)
            recs.append(examine(state, tracker, job, {"game": seed, "source": source}))
            if recs[-1].get("lethal"):
                recs[-1]["in_game"] = None              # filled at the turn's end below
        if source == "ladder":
            a = drivers[seat].act(base.public_position(state, seat, tracker), actions)
        else:
            a = drivers[seat].act(state, actions)
        tracker.before(state)
        apply(state, a)
        tracker.after(state)
        if recs and recs[-1].get("in_game", 0) is None and (state.over or state.active != seat
                                                             or state.turn != recs[-1]["turn"]):
            recs[-1]["in_game"] = state.winner == seat
    if recs and recs[-1].get("in_game", 0) is None:
        recs[-1]["in_game"] = state.winner == recs[-1]["me"]
    return {"seed": seed, "source": source, "winner": state.winner, "turns": state.turn,
            "seconds": round(time.perf_counter() - t0, 1), "positions": recs}


def bank_puzzle(job: dict) -> dict:
    from svsim.tools.puzzles import puzzles
    from ladder import base
    name, seed = job["name"], job["seed"]
    build = {n: b for n, b, _ in puzzles()}[name]
    state = build(seed)
    tracker = base.Tracker(state)
    rec = examine(state, tracker, dict(job, tries=job["tries"]), {"puzzle": name, "build_seed": seed})
    return {"puzzle": name, "seed": seed, "positions": [rec]}


def summarize(results: list) -> dict:
    pos = [p for r in results for p in r["positions"]]
    lethal = [p for p in pos if p["lethal"]]
    out = {"games": len(results), "positions": len(pos), "lethal": len(lethal),
           "no_lethal_proven": sum(1 for p in pos if not p["lethal"] and p["complete"]),
           "undecided": sum(1 for p in pos if not p["lethal"] and not p["complete"]),
           "search_seconds_max": max((p["search_s"] for p in pos), default=0)}
    for mode in MODES:
        every = sum(1 for p in lethal if all(t["won"] for t in p["tries"][mode]))
        tries = [t["won"] for p in lethal for t in p["tries"][mode]]
        out[mode] = {"found_every_try": every, "missed_some_try": len(lethal) - every,
                     "tries_won": sum(tries), "tries": len(tries)}
    ig = [p["in_game"] for p in lethal if p.get("in_game") is not None]
    if ig:
        out["in_game"] = {"won_that_turn": sum(ig), "of": len(ig)}
    miss = [p for p in lethal if "why" in p]
    out["misses"] = {
        "positions": len(miss),
        "default_budget_finds_on_real_state": sum(p["why"]["default_budget_finds"] for p in miss),
        "screened": sum(p["why"]["default_screened"] for p in miss),
        "sure_on_every_sample": sum(all(p["why"]["sure_on_samples"]) for p in miss),
        "sure_on_no_sample": sum(not any(p["why"]["sure_on_samples"]) for p in miss)}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["ladder", "random", "bank"], required=True)
    ap.add_argument("--seeds", type=int, nargs=2)
    ap.add_argument("--games", type=int, default=100)
    ap.add_argument("--tries", type=int, default=3)
    ap.add_argument("--nodes", type=int, default=300000)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    ap.add_argument("--budgets", action="store_true", help="only the lethal search at other budgets (no tries)")
    a = ap.parse_args(argv)
    from ladder import runner
    if a.workers > runner.MAX_WORKERS:
        raise SystemExit(f"at most {runner.MAX_WORKERS} workers")
    runner._limit(None)                        # below normal priority; the workers inherit it (no compute compared)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.source == "bank":
        from svsim.tools.puzzles import puzzles
        jobs = [{"name": n, "seed": s, "tries": a.tries, "nodes": a.nodes}
                for n, _, ans in puzzles() if ans["kind"] == "lethal" for s in range(1, a.tries + 1)]
        fn = bank_puzzle
    else:
        if not a.seeds or a.seeds[1] - a.seeds[0] < a.games:
            raise SystemExit("--seeds LO HI with at least --games seeds")
        jobs = [{"seed": a.seeds[0] + i, "source": a.source, "tries": a.tries, "nodes": a.nodes,
                 "budgets": a.budgets} for i in range(a.games)]
        fn = game
    t0 = time.time()
    tag = a.source + ("-budgets" if a.budgets else "")
    path = out / f"{tag}.jsonl"
    results = []
    with ProcessPoolExecutor(max_workers=a.workers, initializer=_init) as ex, open(path, "w", encoding="utf-8") as f:
        for r in ex.map(fn, jobs):
            results.append(r)
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
    if a.budgets:
        print(json.dumps({"games": len(results), "seconds": round(time.time() - t0)}))
        return
    res = {"source": a.source, "seeds": a.seeds, "tries": a.tries, "nodes": a.nodes, "modes": MODES,
           "seconds": round(time.time() - t0), **summarize(results)}
    (out / f"{a.source}-summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
