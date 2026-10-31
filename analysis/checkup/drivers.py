"""Driver crossover (the bot check-up, step C; agreed with Codex 2026-10-31, Salem's go-ahead 09:22Z).

The question: do Claude's engine decks (ramp 龙族, combo 精灵) lose partly because the hand-written evaluation, the
same in every driver tried so far, misjudges what they build across turns? Deeper in-turn search (mcts:400 against
mcts:100) left the deck ranking unchanged (Spearman 0.985), but the search tree covers one turn only, so that does
not test a cross-turn blind spot.

Design: a test deck is played by a driver D, its opponent always by the fixed mcts:100+plan (--opp). Only the test
side's driver changes, so a change in the test deck's score is the driver's doing. Every driver plays the same
deals: test deck t against opponent o on deal k has one seed (both seats, the engine seed and both agents' seeds as
tools.deckbuild's league: test side 2 x seed + seat, opponent 2 x seed + 1 - seat + 7919), whatever D is. D0 is the
reference driver (the bot as it plays now, mcts:100+plan).

Test decks: the "engine" group (the Claude-built 龙族 and 精灵 lists) and the "control" group (the Claude-built
皇家护卫 lists, tempo decks whose plans live inside a turn). Opponents: the bot's frozen list and the control group
of the blind test (roster groups bot and control). A driver that only plays every deck better lifts both groups;
a cross-turn blind spot shows as the engine group gaining more than the control group (difference in differences).

Recorded per deal (one line of --out, two games): both games' points for the test deck, and each side's CPU seconds
over all its decisions (time.process_time around every act(), the full decision cost, single-thread BLAS) and its
number of decisions. A rerun with the same arguments plays only the deals --out lacks.

    python analysis/checkup/drivers.py run --roster analysis/checkup/roster.txt --deals 10 --seed 85971000 \
        --workers 4 --out runs/checkup/c/deals.jsonl
    python analysis/checkup/drivers.py report runs/checkup/c/deals.jsonl [--out analysis/checkup/c-report.json]

Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

CONDITION = "对手卡表已知（牌序、手牌未知）"
VERSION = "checkup-c-1"
STRIDE = 20                                       # seeds per pair: --deals up to 20 (a preregistered extension)
CLAUDE_GROUPS = ("g1", "g2", "g3", "p2-g1", "p2-g2", "p2-g3")
DRIVERS = {"D0": "mcts:100+plan",                 # the bot as it plays now (reference)
           "D1": "mcts-reply:100+plan",           # leaves scored after playing out the opponent's next turn
           "D2": "mcts:100+plan+threat",          # the evaluation values next turn's lethal potential
           "D3": "fuel:100",                      # the line leaving the most damage after the reply + 2 turns' digging
           "D4": "mcts:400+plan"}                 # four times the in-turn search (more compute, same horizon)


def groups_of(label: str) -> tuple[str, str]:
    """(roster group, test group or '') of a roster label "group/name"."""
    g, _, name = label.partition("/")
    if g in CLAUDE_GROUPS:
        if "-DRAGON-" in f"-{name}-" or "-FOREST-" in f"-{name}-":
            return g, "engine"
        if "-SWORD-" in f"-{name}-":
            return g, "control"
    return g, ""


def craft_of(label: str) -> str:
    for c in ("FOREST", "SWORD", "RUNE", "DRAGON", "ABYSS", "HAVEN", "PORTAL"):
        if c in label:
            return c
    return "?"


def read_roster(path: str):
    from svsim.tools.deckgate import read_field
    return read_field(path)


def play_one(cards, seat: int, test_spec: str, opp_spec: str, seed: int) -> dict:
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools.arena import make_agent
    agents = [None, None]
    agents[seat] = make_agent(test_spec, 2 * seed + seat)
    agents[1 - seat] = make_agent(opp_spec, 2 * seed + 1 - seat + 7919)
    state = new_game(cards[0], cards[1], seed=seed)
    cpu, n = [0.0, 0.0], [0, 0]
    while not state.over:
        side = state.active
        legal = legal_actions(state)
        c0 = time.process_time()
        action = agents[side].act(state, legal)
        cpu[side] += time.process_time() - c0
        n[side] += 1
        apply(state, action)
    points = 1.0 if state.winner == seat else 0.5 if state.winner not in (0, 1) else 0.0
    return {"points": points, "turns": state.turn, "t_cpu": cpu[seat], "t_n": n[seat],
            "o_cpu": cpu[1 - seat], "o_n": n[1 - seat]}


def play_deal(job) -> dict:
    from svsim.cards.pool import POOL
    driver, spec, opp_spec, t_label, t_ids, o_label, o_ids, seed = job
    mine, theirs = [POOL[i] for i in t_ids], [POOL[i] for i in o_ids]
    games = []
    for seat in (0, 1):
        cards = [None, None]
        cards[seat], cards[1 - seat] = mine, theirs
        games.append(play_one(cards, seat, spec, opp_spec, seed))
    return {"driver": driver, "spec": spec, "opp_spec": opp_spec, "test": t_label, "opp": o_label, "seed": seed,
            "points": [g["points"] for g in games], "turns": [g["turns"] for g in games],
            "t_cpu": round(sum(g["t_cpu"] for g in games), 3), "t_n": sum(g["t_n"] for g in games),
            "o_cpu": round(sum(g["o_cpu"] for g in games), 3), "o_n": sum(g["o_n"] for g in games)}


def _nice() -> None:
    try:
        os.nice(10)
    except (OSError, AttributeError):
        pass


def plan(roster, drivers: dict, opp_spec: str, deals: int, seed: int, test_groups=("engine", "control"),
         opp_groups=("bot", "control"), only_tests=None, only_opps=None) -> list:
    """Jobs ordered deal-major (every pair's k-th deal, every driver, before any pair's (k+1)-th), so a stopped run
    leaves every driver with the same deals."""
    tests = [(l, ids) for l, ids in roster if groups_of(l)[1] in test_groups and (not only_tests or l in only_tests)]
    opps = [(l, ids) for l, ids in roster if groups_of(l)[0] in opp_groups and (not only_opps or l in only_opps)]
    assert deals <= STRIDE
    jobs = []
    for k in range(deals):
        for ti, (tl, tids) in enumerate(tests):
            for oi, (ol, oids) in enumerate(opps):
                s = seed + (ti * len(opps) + oi) * STRIDE + k      # k-th deal's seed whatever --deals is
                for d, spec in drivers.items():
                    jobs.append((d, spec, opp_spec, tl, tids, ol, oids, s))
    return jobs


def run(args) -> None:
    roster = read_roster(args.roster)
    drivers = dict(x.split("=", 1) for x in args.drivers) if args.drivers else DRIVERS
    jobs = plan(roster, drivers, args.opp, args.deals, args.seed,
                only_tests=set(args.tests) if args.tests else None, only_opps=set(args.opps) if args.opps else None)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("version") == VERSION:
                done.add((r["driver"], r["spec"], r["opp_spec"], r["test"], r["opp"], r["seed"]))
    todo = [j for j in jobs if (j[0], j[1], j[2], j[3], j[5], j[7]) not in done]
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = ""
    print(f"{VERSION} commit {commit[:12]}; {len(jobs)} deals planned, {len(done)} done, {len(todo)} to play; "
          f"workers {args.workers}; BLAS threads {os.environ.get('OPENBLAS_NUM_THREADS')}", flush=True)
    t0, n = time.time(), 0
    with out.open("a", encoding="utf-8") as fh, Pool(args.workers, initializer=_nice) as pool:
        for r in pool.imap_unordered(play_deal, todo, chunksize=1):
            r["version"], r["commit"] = VERSION, commit[:12]
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            n += 1
            if n % 50 == 0:
                print(f"{n}/{len(todo)} deals, {time.time() - t0:.0f} s", flush=True)
    print(f"done {n} deals in {time.time() - t0:.0f} s", flush=True)


# --- report ----------------------------------------------------------------------------------------------------

def load(path: str) -> list:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("version") == VERSION:
            rows.append(r)
    return rows


def paired(rows: list, ref: str = "D0") -> dict:
    """For each driver D != ref: the per-deal differences (mean of the two seats, D minus ref) on the deals both
    played, keyed by (test, opp, seed)."""
    by = {}
    for r in rows:
        by.setdefault(r["driver"], {})[(r["test"], r["opp"], r["seed"])] = sum(r["points"]) / 2
    out = {}
    for d, m in by.items():
        if d == ref:
            continue
        keys = sorted(set(m) & set(by.get(ref, {})))
        out[d] = {k: m[k] - by[ref][k] for k in keys}
    return out, by


def mean_se(x) -> tuple[float, float, int]:
    n = len(x)
    if n < 2:
        return (float(x[0]) if n else float("nan")), float("nan"), n
    m = sum(x) / n
    v = sum((a - m) ** 2 for a in x) / (n - 1)
    return m, math.sqrt(v / n), n


def deck_boot(diffs: dict, tests_e: list, tests_c: list, reps: int = 2000, seed: int = 85971999) -> tuple:
    """A 95% interval for the difference in differences resampling decks (each group's decks with replacement):
    how far the result depends on which decks were in the groups, not only on the deals."""
    import random
    rng = random.Random(seed)
    per = {}
    for (t, _o, _s), v in diffs.items():
        per.setdefault(t, []).append(v)
    mean = {t: sum(v) / len(v) for t, v in per.items()}
    e = [mean[t] for t in tests_e if t in mean]
    c = [mean[t] for t in tests_c if t in mean]
    if not e or not c:
        return float("nan"), float("nan")
    out = []
    for _ in range(reps):
        be = [rng.choice(e) for _ in e]
        bc = [rng.choice(c) for _ in c]
        out.append(sum(be) / len(be) - sum(bc) / len(bc))
    out.sort()
    return out[int(0.025 * reps)], out[int(0.975 * reps) - 1]


def report(args) -> None:
    rows = load(args.path)
    diffs, by = paired(rows)
    labels = sorted({r["test"] for r in rows})
    group = {t: groups_of(t)[1] for t in labels}
    res = {"version": VERSION, "condition": CONDITION, "deals": len(rows), "drivers": {}}
    print(f"条件：{CONDITION}；被测卡组由各打法操作，对手固定 {rows[0]['opp_spec'] if rows else '?'}")
    cpu = {}
    for r in rows:
        c = cpu.setdefault(r["driver"], [0.0, 0, 0.0, 0, r["spec"]])
        c[0] += r["t_cpu"]
        c[1] += r["t_n"]
        c[2] += r["o_cpu"]
        c[3] += r["o_n"]
    print("打法  每步 CPU 秒（被测方 / 对手）  每局步数（被测方）  被测卡组得分：引擎组 / 对照组")
    for d in sorted(by):
        c = cpu[d]
        sc = {g: mean_se([v for (t, _o, _s), v in by[d].items() if group[t] == g]) for g in ("engine", "control")}
        games = sum(1 for r in rows if r["driver"] == d) * 2
        print(f"{d} {c[4]:24s} {c[0] / max(c[1], 1):.3f} / {c[2] / max(c[3], 1):.3f}   {c[1] / max(games, 1):5.1f}   "
              f"{100 * sc['engine'][0]:.1f}±{196 * sc['engine'][1]:.1f} / {100 * sc['control'][0]:.1f}±"
              f"{196 * sc['control'][1]:.1f}")
        res["drivers"][d] = {"spec": c[4], "cpu_per_decision": c[0] / max(c[1], 1),
                             "opp_cpu_per_decision": c[2] / max(c[3], 1), "decisions_per_game": c[1] / max(games, 1),
                             "score": {g: sc[g][0] for g in sc}, "score_se": {g: sc[g][1] for g in sc}}
    tests_e = [t for t in labels if group[t] == "engine"]
    tests_c = [t for t in labels if group[t] == "control"]
    print("相对 D0 的变化（胜率点，95% 区间；按发牌配对，两座位平均为一个单位）：")
    print("打法  引擎组 Δ           对照组 Δ          差中差（引擎 − 对照）   差中差按卡组重抽的区间")
    for d, dd in sorted(diffs.items()):
        e = mean_se([v for k, v in dd.items() if group[k[0]] == "engine"])
        c = mean_se([v for k, v in dd.items() if group[k[0]] == "control"])
        did, did_se = e[0] - c[0], math.sqrt(e[1] ** 2 + c[1] ** 2)
        lo, hi = deck_boot(dd, tests_e, tests_c)
        print(f"{d}   {100 * e[0]:+5.1f} [{100 * (e[0] - 1.96 * e[1]):+5.1f}, {100 * (e[0] + 1.96 * e[1]):+5.1f}]  "
              f"{100 * c[0]:+5.1f} [{100 * (c[0] - 1.96 * c[1]):+5.1f}, {100 * (c[0] + 1.96 * c[1]):+5.1f}]  "
              f"{100 * did:+5.1f} [{100 * (did - 1.96 * did_se):+5.1f}, {100 * (did + 1.96 * did_se):+5.1f}]   "
              f"[{100 * lo:+5.1f}, {100 * hi:+5.1f}]")
        by_craft = {}
        for (t, _o, _s), v in dd.items():
            by_craft.setdefault(craft_of(t), []).append(v)
        by_deck = {t: mean_se([v for (tt, _o, _s), v in dd.items() if tt == t]) for t in labels}
        res["drivers"][d].update({
            "engine_delta": e[0], "engine_se": e[1], "control_delta": c[0], "control_se": c[1],
            "did": did, "did_se": did_se, "did_deck_boot95": [lo, hi], "pairs_engine": e[2], "pairs_control": c[2],
            "by_craft": {k: mean_se(v)[:2] for k, v in by_craft.items()},
            "by_deck": {t: v[:2] for t, v in by_deck.items()}})
        print("      按职业：" + "；".join(f"{k} {100 * mean_se(v)[0]:+.1f}±{196 * mean_se(v)[1]:.1f}"
                                      for k, v in sorted(by_craft.items())))
    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--roster", default="analysis/checkup/roster.txt")
    r.add_argument("--drivers", nargs="*", help="NAME=SPEC ... (default D0-D4)")
    r.add_argument("--opp", default="mcts:100+plan", help="the opponent's driver, fixed")
    r.add_argument("--deals", type=int, default=10)
    r.add_argument("--seed", type=int, required=True)
    r.add_argument("--tests", nargs="*", help="only these test decks (labels)")
    r.add_argument("--opps", nargs="*", help="only these opponents (labels)")
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--out", required=True)
    p = sub.add_parser("report")
    p.add_argument("path")
    p.add_argument("--out")
    args = ap.parse_args()
    run(args) if args.cmd == "run" else report(args)


if __name__ == "__main__":
    main()
