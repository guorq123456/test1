"""Phase 1 on real games (item 1.8 and the sanity checks), meant for Salem's computer. Every step resumes.

    python tools/phase1_checks.py all --runs RUNS [--workers 11 --mask 0x3FC3FC] [--scale 1.0]
    python tools/phase1_checks.py <step> --runs RUNS ...        step: baseline replay gate known fluct

Steps, in this order (each writes RUNS/<step>/summary.json and probe/p1-<step>.json):
1. baseline (1.8): the real initial pool. Seven baseline members (bot-frozen7, the default strategy mcts:100+plan
   behind the base with the default guess), period 0, formal-ladder seeds 89500000-90999999, until every member has
   `--games-each` decided games (3000). Then the first leaderboard, the zero-sum check, and the frozen snapshot of
   the baselines (fixed at their last-1000 mean) kept as the anchor (RUNS/baseline/frozen.json).
2. replay: 20 games of the baseline ladder drawn at random (seed 1), replayed move by move and decision by decision.
3. gate (检验工具自检, real half): on the Swordcraft baseline in the frozen pool, a clearly stronger update
   (mcts:100+plan over mix:0.35:mcts:100+plan) must pass, the reverse must not, identical versions must come out
   "every decision the same". Its own ledger (RUNS/gate/), not the pool's: these are not member updates.
4. known (已知强弱检查): four host-made Swordcraft members on the Swordcraft baseline list, the default strategy with
   a random legal move at rate 0, 0.15, 0.35, 0.6, in a check pool with the six other baselines. Two runs: all at
   1500, and the four at reversed starting CRs (1300 / 1433 / 1567 / 1700). The leaderboard must order them, both
   runs must agree, the frozen-pool evaluator (3 repeats each) must order them, and their gaps are compared with
   their head-to-head win rates (400 games per neighbouring pair, mirror matches) converted by §3. The check pool is
   thrown away after (never the real pool).
5. fluct (波动检查): the Swordcraft baseline evaluated 20 times in the frozen baseline pool (each evaluation 5
   repeats x 1200 games, last 600, §4.4); the spread of the 20 results over the mean reported standard error should
   be in 0.7-1.4.
6. known2 (已知强弱, finer round, A26): as `known` with random-move rates 0, 0.04, 0.08, 0.15. In `known` the two
   weakest versions won under 25% against everyone, where §3 gives no floor (flat +8/-24 past 175), and their CRs
   walked off by thousands (LD-17); this round keeps every version inside the field. Summaries of both rounds also
   give each member's mean relative CR over the two halves of its window (a drifting CR shows there).

Seeds: baseline from the formal-ladder range; everything else from the host-measurement range 92300000-92799999,
split: fluct 92300000-92499999 (10000 per evaluation), known 92500000-92649999 (check pools 92500000-92549999,
head-to-head 92550000-92559999, evaluator 92560000-92639999), gate 92650000-92699999, known2 92700000-92795999
(pools 92700000-92753999, head-to-head 92754000-92755999, evaluator 92756000-92795999) (SEEDS.md).
`--scale` multiplies every game count (0.02 for a quick dry run in the container).
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics as st
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = LADDER.parents[1]
sys.path[:0] = [str(LADDER), str(ROOT)]

from ladder import evaluator as E  # noqa: E402
from ladder import gate as G  # noqa: E402
from ladder import leaderboard as L  # noqa: E402
from ladder import pool as P  # noqa: E402
from ladder import rules  # noqa: E402
from ladder.replay import replay_decisions, replay_moves  # noqa: E402
from ladder.runner import load_deck  # noqa: E402

LADDER_SEEDS = (89500000, 91000000)
FLUCT_SEEDS = (92300000, 92500000)
KNOWN_SEEDS = (92500000, 92650000)       # pools 92500000-92549999, head-to-head 92550000-92559999, evaluator
KNOWN_POOL = {"all-1500": (92500000, 92525000), "reversed": (92525000, 92550000)}
KNOWN_H2H = (92550000, 92560000)
KNOWN_EVAL = 92560000                    # + 20000 per candidate
GATE_SEEDS = (92650000, 92700000)
DEFAULT = "bot:mcts:100+plan"
SCALE = [1.0]
SWORD = 2
EPS = (0.0, 0.15, 0.35, 0.6)
# The second, finer round (A26): the first one's two weakest versions fell beyond what §3 can place (past 175 the
# change is a flat +8/-24, so a member winning under 25% against its nearest opponents has no floor and its CR walks
# off; LD-17). Small gaps instead, all inside the field: about 7, 13 and 25 points below the default in mirror games.
KNOWN = {
    "known": {"eps": EPS, "pools": KNOWN_POOL, "h2h": KNOWN_H2H, "eval": KNOWN_EVAL, "eval_span": 20000},
    "known2": {"eps": (0.0, 0.04, 0.08, 0.15),
               "pools": {"all-1500": (92700000, 92727000), "reversed": (92727000, 92754000)},
               "h2h": (92754000, 92756000), "eval": 92756000, "eval_span": 10000},   # up to 92795999
}


def baseline_codes():
    lines = [l.strip().split("|") for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(
        encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    return [(name, code) for name, code in lines]


def save(runs: Path, step: str, out: dict):
    d = runs / step
    d.mkdir(parents=True, exist_ok=True)
    text = json.dumps(out, ensure_ascii=False, indent=1, default=lambda x: None)
    (d / "summary.json").write_text(text, encoding="utf-8")
    if SCALE[0] == 1.0:                                  # a dry run never lands in the repository's records
        (LADDER / "probe").mkdir(exist_ok=True)
        (LADDER / "probe" / f"p1-{step}.json").write_text(text, encoding="utf-8")
    print(text, flush=True)
    return out


def ladder_until(pool: P.Pool, each: int, workers, mask, members=None):
    """Play until every member in `members` (default all) has `each` decided games."""
    while True:
        ms = [pool.members[m] for m in members] if members else pool.active()
        short = min(m.games for m in ms)
        if short >= each:
            return
        need = max(len(ms), int((each - short) * len(pool.active()) / 2 * 0.6))
        pool.ladder(workers=workers, games=need, mask=mask, quiet=True)


def zero_sum(pool: P.Pool) -> dict:
    return {"sum_of_changes": pool.cr_sum_check, "lost_to_removal": pool.lost_to_removal,
            "total_cr": pool.total_cr(), "expected_total": 1500 * len(pool.active()),
            "ok": pool.cr_sum_check == 0 and pool.total_cr() == 1500 * len(pool.active())
            and pool.lost_to_removal == 0}


# --- 1. baseline ---------------------------------------------------------------------------------------------

def step_baseline(runs: Path, a) -> dict:
    d = runs / "baseline" / "pool"
    each = max(60, int(3000 * a.scale))
    if (d / "events.jsonl").exists():
        pool = P.Pool(d)
    else:
        pool = P.Pool.create(d, LADDER_SEEDS, note="phase-1 baseline pool (the real initial pool)")
        for name, code in baseline_codes():
            ids = [c.card_id for c in load_deck(code)]
            pool.enter(ids, DEFAULT, "baseline", deck_code=code, note=name)
    t0 = time.time()
    ladder_until(pool, each, a.workers, a.mask)
    pool, series = L.load(d)
    board = L.board(pool, series, window=min(L.WINDOW_GAMES, each - max(10, each // 6)))
    frozen = E.freeze(d)
    (runs / "baseline" / "frozen.json").write_text(json.dumps(frozen, ensure_ascii=False, indent=1),
                                                    encoding="utf-8")
    names = {m.mid: m.note for m in pool.active()}
    return save(runs, "baseline", {
        "games": pool.settled, "seconds": round(time.time() - t0), "mu": round(pool.mu, 2),
        "zero_sum": zero_sum(pool),
        "board": [{"member": names[r["mid"]], "craft": r["craft"], "games": r["games"],
                   "rel_cr": round(r["rel_cr"], 1), "ci": [round(r["lo"], 1), round(r["hi"], 1)],
                   "tau": round(r["tau"], 1), "se_batch": round(r["se_batch"], 2)} for r in board],
        "frozen_hash": frozen["hash"],
        "frozen": [{"member": names[f["mid"]], "cr": f["cr"], "from_games": f["cr_from"]} for f in frozen["members"]],
        "draws": sum(m.draws for m in pool.active())})


# --- 2. replay -------------------------------------------------------------------------------------------------

def step_replay(runs: Path, a) -> dict:
    logs = [json.loads(l) for l in (runs / "baseline" / "pool" / "games.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    pick = random.Random(1).sample(logs, min(max(3, int(20 * min(1, a.scale * 50))), len(logs)))
    bad = []
    for log in pick:
        ok, why = replay_moves(log)
        if ok:
            ok, why = replay_decisions(log)
        if not ok:
            bad.append({"id": log["id"], "why": why})
    return save(runs, "replay", {"checked": len(pick), "failed": bad, "ok": not bad,
                                 "machine": pick[0].get("provenance") if pick else None})


# --- 3. gate self-check -----------------------------------------------------------------------------------------

def sword_mid(frozen_path) -> str:
    frozen, _ = E.load_frozen(frozen_path)
    return next(f.mid for f in frozen if f.craft == SWORD)


def step_gate(runs: Path, a) -> dict:
    fz = runs / "baseline" / "frozen.json"
    mid = sword_mid(fz)
    root = runs / "gate"
    root.mkdir(parents=True, exist_ok=True)
    done = {(r["new"], r["old"], r["kind"]): r for r in G.read_ledger(root)}
    weak = "mix:0.35:mcts:100+plan"
    plan = [("strong passes", DEFAULT, weak, "better", True), ("weak is rejected", weak, DEFAULT, "better", True),
            ("identical: same decisions", DEFAULT, DEFAULT, "same", False)]
    out = []
    for label, new, old, kind, compute_point in plan:
        rec = done.get((new, old, kind))
        if rec is None:
            dry = a.scale < 1                            # a dry run: a huge H1 and a given share, a few pairs
            g = G.Gate(fz, mid, new, old, kind, change=f"self-check: {label}", prediction=label, seeds=GATE_SEEDS,
                       out_dir=root, delta=20.0 if dry else 5.0, share=0.5 if dry else None,
                       pairs=max(6, int(50 * min(1, a.scale * 10))) if kind == "same" else None,
                       compute_is_the_point=compute_point, ledger_root=root, rng_seed=len(out) + 1)
            rec = g.run(workers=a.workers, mask=a.mask)
        out.append({"check": label, "verdict": rec["verdict"], "pairs": rec["pairs"],
                    "expected_pairs": rec.get("expected_pairs"), "share": rec.get("discordant_share"),
                    "discordant": rec.get("discordant"), "compute_ratio": rec.get("compute_ratio")})
    ok = (out[0]["verdict"] == "passed" and out[1]["verdict"] != "passed" and
          out[2]["verdict"].startswith("passed"))
    return save(runs, "gate", {"member": mid, "results": out, "ok": ok})


# --- 4. known strengths -------------------------------------------------------------------------------------------

def check_pool(d: Path, starts, seeds, eps_list=EPS) -> tuple[P.Pool, list[str]]:
    if (d / "events.jsonl").exists():
        pool = P.Pool(d)
        return pool, [m.mid for m in pool.active() if m.owner == "check"]
    pool = P.Pool.create(d, seeds, note="phase-1 known-strength check pool (thrown away)", check=True)
    codes = baseline_codes()
    sword_code = next(c for n, c in codes if "SWORD" in n)
    for name, code in codes:
        if "SWORD" not in name:
            pool.enter([c.card_id for c in load_deck(code)], DEFAULT, "baseline", deck_code=code, note=name)
    ids = [c.card_id for c in load_deck(sword_code)]
    mids = []
    for eps, cr in zip(eps_list, starts):
        spec = DEFAULT if eps == 0 else f"mix:{eps}:mcts:100+plan"
        mids.append(pool.enter(ids, spec, "check", note=f"eps {eps}", cr=cr))
    return pool, mids


def head_to_head(runs: Path, a, step="known") -> list[dict]:
    cfg = KNOWN[step]
    eps_list = cfg["eps"]
    from ladder import runner
    codes = baseline_codes()
    sword = next(c for n, c in codes if "SWORD" in n)
    n = max(4, int(400 * a.scale))
    out = []
    rng = random.Random(7)
    used = set()
    for i in range(len(eps_list) - 1):
        hi, lo = eps_list[i], eps_list[i + 1]
        specs = [DEFAULT if e == 0 else f"mix:{e}:mcts:100+plan" for e in (hi, lo)]
        jobs = []
        for k in range(n):
            while True:
                seed = rng.randrange(*cfg["h2h"])
                if seed not in used:
                    used.add(seed)
                    break
            ss = specs if k % 2 == 0 else specs[::-1]
            jobs.append({"id": f"h2h-{i}-{k:04d}", "seed": seed, "first": None, "decks": [sword, sword],
                         "strategies": ss, "strategy_seeds": [rng.randrange(1, 2 ** 31), rng.randrange(1, 2 ** 31)],
                         "labels": {"better_seat": k % 2}})
        path = runs / step / f"h2h-{i}.jsonl"
        runner.run(jobs, str(path), workers=a.workers, mask=a.mask, quiet=True)
        logs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        dec = [l for l in logs if l.get("winner") in (0, 1)]
        wins = sum(1 for l in dec if l["winner"] == l["labels"]["better_seat"])
        p = wins / len(dec)
        se = math.sqrt(p * (1 - p) / len(dec))
        out.append({"pair": f"eps {hi} vs {lo}", "games": len(dec), "win_rate": round(p, 4),
                    "ci": [round(p - 1.96 * se, 4), round(p + 1.96 * se, 4)],
                    "cr_gap_8_per_pp": round(rules.pp_to_cr(100 * (p - 0.5)), 1)})
    return out


def halves(series, mid, window) -> list[float]:
    """Mean relative CR over the first and the second half of the member's window: a drifting CR shows here."""
    rel = [cr - mu for cr, mu in series.points[mid][-window:]]
    h = len(rel) // 2
    return [round(sum(rel[:h]) / max(1, h), 1), round(sum(rel[h:]) / max(1, len(rel) - h), 1)]


def known_round(runs: Path, a, step: str) -> dict:
    cfg = KNOWN[step]
    eps_list = cfg["eps"]
    each = max(60, int(2400 * a.scale))                  # 2000 in the window after ~400 to settle
    res, drift = {}, {}
    for name, starts in (("all-1500", (1500, 1500, 1500, 1500)), ("reversed", (1300, 1433, 1567, 1700))):
        d = runs / step / name
        pool, mids = check_pool(d, starts, cfg["pools"][name], eps_list)
        ladder_until(pool, each, a.workers, a.mask, members=mids)
        pool, series = L.load(d)
        window = min(L.WINDOW_GAMES, each - max(10, each // 6))
        rows = {r["mid"]: r for r in L.board(pool, series, window=window)}
        res[name] = [{"eps": eps, "rel_cr": round(rows[m]["rel_cr"], 1),
                      "ci": [round(rows[m]["lo"], 1), round(rows[m]["hi"], 1)], "games": rows[m]["games"]}
                     for eps, m in zip(eps_list, mids)]
        names = {m.mid: m.note for m in pool.active()}
        drift[name] = {names[m.mid]: {"halves": halves(series, m.mid, window), "tau": round(rows[m.mid]["tau"], 1)}
                       for m in pool.active() if m.mid in rows}
    # the evaluator on the four, frozen from the first run
    d1 = runs / step / "all-1500"
    fz = runs / step / "frozen.json"
    if not fz.exists():
        fz.write_text(json.dumps(E.freeze(d1)), encoding="utf-8")
    frozen, _ = E.load_frozen(fz)
    pool1 = P.Pool(d1)
    mids1 = [m.mid for m in pool1.active() if m.owner == "check"]
    evals = []
    span = cfg["eval_span"]
    for k, mid in enumerate(mids1):
        cand = E.candidate_from(frozen, mid=mid)
        lo = cfg["eval"] + span * k                              # each candidate its own slice of the range
        ev = E.Evaluation(fz, runs / step / f"eval-{k}", cand, (lo, lo + span),
                          games=max(10, int(1200 * a.scale)), tail=max(5, int(600 * a.scale)), repeats=3,
                          rng_seed=100 + k)
        r = ev.run(workers=a.workers, mask=a.mask) if not ev.done() else ev.result()
        evals.append({"eps": eps_list[k], "rel_cr": round(r["rel_cr"], 1),
                      "ci": [round(r["lo"], 1), round(r["hi"], 1)]})
    h2h = head_to_head(runs, a, step)
    order = [all(x["rel_cr"] > y["rel_cr"] for x, y in zip(rs, rs[1:])) for rs in res.values()]
    order_eval = all(x["rel_cr"] > y["rel_cr"] for x, y in zip(evals, evals[1:]))
    agree = [abs(x["rel_cr"] - y["rel_cr"]) <= 1.96 * math.hypot((x["ci"][1] - x["ci"][0]) / 3.92,
                                                                 (y["ci"][1] - y["ci"][0]) / 3.92)
             for x, y in zip(res["all-1500"], res["reversed"])]
    gaps = []
    for i, h in enumerate(h2h):
        pool_gap = res["all-1500"][i]["rel_cr"] - res["all-1500"][i + 1]["rel_cr"]
        gaps.append({**h, "pool_gap": round(pool_gap, 1)})
    return save(runs, step, {"eps": list(eps_list), "leaderboard": res, "evaluator": evals, "head_to_head": gaps,
                             "order_right_leaderboard": order, "order_right_evaluator": order_eval,
                             "runs_agree": agree, "drift": drift})


def step_known(runs: Path, a) -> dict:
    return known_round(runs, a, "known")


def step_known2(runs: Path, a) -> dict:
    return known_round(runs, a, "known2")


# --- 5. fluctuation ------------------------------------------------------------------------------------------

def step_fluct(runs: Path, a) -> dict:
    fz = runs / "baseline" / "frozen.json"
    frozen, _ = E.load_frozen(fz)
    mid = sword_mid(fz)
    cand = E.candidate_from(frozen, mid=mid)
    n_evals = a.evals
    span = (FLUCT_SEEDS[1] - FLUCT_SEEDS[0]) // n_evals
    results = []
    for k in range(n_evals):
        lo = FLUCT_SEEDS[0] + span * k
        ev = E.Evaluation(fz, runs / "fluct" / f"eval-{k:02d}", cand, (lo, lo + span),
                          games=max(10, int(1200 * a.scale)), tail=max(5, int(600 * a.scale)), repeats=5,
                          rng_seed=1000 + k)
        r = ev.run(workers=a.workers, mask=a.mask) if not ev.done() else ev.result()
        results.append(r)
        print(f"fluct {k + 1}/{n_evals}: {r['rel_cr']:+.1f} (se {r['se']:.1f})", file=sys.stderr, flush=True)
    means = [r["rel_cr"] for r in results]
    ratio = st.stdev(means) / st.mean(r["se"] for r in results)
    return save(runs, "fluct", {"member": mid, "evaluations": [{"rel_cr": round(r["rel_cr"], 2),
                                                               "se": round(r["se"], 2)} for r in results],
                                "sd_of_evaluations": round(st.stdev(means), 2),
                                "mean_reported_se": round(st.mean(r["se"] for r in results), 2),
                                "ratio": round(ratio, 3), "ok": 0.7 <= ratio <= 1.4})


STEPS = {"baseline": step_baseline, "replay": step_replay, "gate": step_gate, "known": step_known,
         "fluct": step_fluct, "known2": step_known2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["all", *STEPS])
    ap.add_argument("--runs", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--mask")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--evals", type=int, default=20, help="fluct: evaluations (20; fewer only for a dry run)")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):              # Windows: stdout to a file is cp1252 and can't take 中文
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    a.mask = int(a.mask, 16) if a.mask else None
    SCALE[0] = a.scale
    from ladder import runner
    print(json.dumps({"limits": runner._limit(a.mask)}), file=sys.stderr, flush=True)   # this process too
    runs = Path(a.runs)
    runs.mkdir(parents=True, exist_ok=True)
    steps = list(STEPS) if a.step == "all" else [a.step]
    for s in steps:
        t = time.time()
        print(f"== {s} ({time.strftime('%H:%M:%S')})", file=sys.stderr, flush=True)
        STEPS[s](runs, a)
        print(f"== {s} done in {time.time() - t:.0f}s", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
