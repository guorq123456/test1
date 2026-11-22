"""2.5: the trained pilots in both information conditions (plan 阶段 2: 「驾驶员改成默认猜测条件，在两种条件下各测一次，
两个数都报」).

    python tools/pilot_conditions.py --seeds LO HI --games-per-opponent 20 --out DIR [--pilots T1-SWORD-1 ...]
                                     [--workers 11 --mask 0x3FC3FC]

Each pilot plays its own list (the bot frozen seven list of its class) at its equal-CPU N (svsim.ui.session.
pilot_native_spec) against a field of lists played by the default bot mcts:100+plan; on the same games the default
bot plays the pilot's list too (the reference: what the pilot adds over the generic bot on the same list).
The field (`--field`): "others" (default) = the bot's 12 lists outside the frozen seven; "frozen7"; "wgpq" = the
WGP Qualifier pro lists. Against the frozen seven the two conditions nearly coincide: the default guess IS the
opponent's real list there (LEDGER LD-31), so the measurement uses lists the guess gets wrong.
- 默认猜测 (the ladder's condition): both sides behind the base (`bot:<spec>`): each decision is made on a state
  drawn from the default guess (the opponent's class baseline list), never the real state. Played by the runner.
- 原生 (the pilots' own condition, L2): the agents act on the real state, so their sampling knows the opponent's
  real list. Played here, one process per game, the same deals (the same sealed job) and the same agent seeds.
Game i against opponent j of the field (n lists): seed LO + 100 * (n * pilot + j) + i, the pilot's side in seat
i % 2.
Report: per pilot and condition, the win rate of the pilot and of the reference over the same games, their paired
difference with a 95% interval, and the per-decision compute of the pilot's side over the reference's.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = LADDER.parents[1]
sys.path[:0] = [str(LADDER), str(ROOT)]

REF = "mcts:100+plan"
FROZEN7 = ROOT / "analysis/pilot/fields/bot-frozen7.txt"


def decks7():
    return [l.strip().split("|") for l in FROZEN7.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]


def field_of(kind):
    frozen = decks7()
    if kind == "frozen7":
        return frozen
    if kind == "others":
        codes = {c for _, c in frozen}
        rows = [l.strip().split("|")[:2] for l in (ROOT / "svsim/ui/bot_decks.txt").read_text(encoding="utf-8")
                .splitlines() if l.strip() and not l.startswith("#")]
        return [(f"bot/{n}", c) for n, c in rows if c not in codes]
    if kind == "wgpq":
        rows = [l.strip().split("|")[:2] for l in (LADDER / "decklists/wgpq-2026-11-14.txt").read_text(
            encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
        seen, out = set(), []
        for n, c in rows:
            if c not in seen:
                seen.add(c)
                out.append((n, c))
        return out
    raise SystemExit(f"unknown field {kind}")


def jobs_for(pilots, lo, hi, games, field_kind="others"):
    from svsim.ui.session import pilot_native_spec
    by_name = {n.split("/")[-1]: c for n, c in decks7()}
    field = field_of(field_kind)
    out = []
    for p_i, key in enumerate(pilots):
        spec = pilot_native_spec(key)
        if spec is None or key not in by_name:
            raise SystemExit(f"no pilot or list for {key}")
        for j, (oname, ocode) in enumerate(field):
            for i in range(games):
                seed = lo + 100 * (len(field) * p_i + j) + i
                if seed >= hi or i >= 100:
                    raise SystemExit("seed range too small, or more than 100 games per opponent")
                seat = i % 2
                for who, s in (("pilot", spec), ("ref", REF)):
                    sides = [(by_name[key], s), (ocode, REF)]
                    if seat == 1:
                        sides.reverse()
                    out.append({"id": f"{key}-{oname.split('/')[-1]}-{i:03d}-{who}", "seed": seed, "first": None,
                                "decks": [d for d, _ in sides], "specs": [x for _, x in sides],
                                "labels": {"pilot": key, "opp": oname, "game": i, "who": who, "seat": seat}})
    return out


def _native(job):
    """One game with both agents on the real state (the pilots' own condition)."""
    import random  # noqa: F401
    from svsim.core.engine import apply, legal_actions
    from svsim.tools.arena import make_agent
    from ladder import deal
    agents = [make_agent(s, x) for s, x in zip(job["specs"], job["strategy_seeds"])]
    _, state = deal.start(job, first="first")
    cpu = [0, 0]
    steps = [0, 0]
    while not state.over:
        seat = state.active
        t0 = time.thread_time_ns()
        a = agents[seat].act(state, legal_actions(state))
        cpu[seat] += time.thread_time_ns() - t0
        steps[seat] += 1
        apply(state, a)
    return {"id": job["id"], "labels": job["labels"], "winner": state.winner if state.winner in (0, 1) else None,
            "cpu": cpu, "steps": steps}


def _init():
    sys.path[:0] = [str(LADDER), str(ROOT)]
    import svsim.cards.library  # noqa: F401


def _wilson_diff(a, b):
    """Paired difference of two 0/1 lists in percentage points, 95% normal interval."""
    n = len(a)
    d = [x - y for x, y in zip(a, b)]
    m = sum(d) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1)) if n > 1 else float("nan")
    h = 1.96 * sd / math.sqrt(n)
    return round(100 * m, 2), round(100 * (m - h), 2), round(100 * (m + h), 2)


def summarize(rows, cond):
    out = {}
    pairs = {}
    for r in rows:
        lab = r["labels"]
        pairs.setdefault((lab["pilot"], lab["opp"], lab["game"]), {})[lab["who"]] = r
    by = {}
    for (pilot, _, _), d in pairs.items():
        if set(d) != {"pilot", "ref"}:
            continue
        b = by.setdefault(pilot, {"pilot": [], "ref": [], "cpu": [0, 0], "steps": [0, 0]})
        for who in ("pilot", "ref"):
            r = d[who]
            seat = r["labels"]["seat"]
            b[who].append(1 if r["winner"] == seat else 0)
            b["cpu"][who == "ref"] += r["cpu"][seat]
            b["steps"][who == "ref"] += r["steps"][seat]
    for pilot, b in by.items():
        n = len(b["pilot"])
        per = [b["cpu"][k] / b["steps"][k] if b["steps"][k] else float("nan") for k in (0, 1)]
        out[pilot] = {"condition": cond, "games": n, "pilot_rate": round(sum(b["pilot"]) / n, 4),
                      "ref_rate": round(sum(b["ref"]) / n, 4), "diff_pp": _wilson_diff(b["pilot"], b["ref"]),
                      "compute_ratio": round(per[0] / per[1], 3) if per[1] else None}
    return out


def main(argv=None):
    from svsim.ui.session import PILOT_MODELS
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs=2, required=True)
    ap.add_argument("--games-per-opponent", type=int, default=20)
    ap.add_argument("--pilots", nargs="*", default=sorted(PILOT_MODELS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--mask", type=lambda x: int(x, 0))
    ap.add_argument("--key", default="auto")
    ap.add_argument("--field", default="others", choices=["others", "frozen7", "wgpq"])
    a = ap.parse_args(argv)
    from ladder import deal, runner
    if a.workers > runner.MAX_WORKERS:
        raise SystemExit(f"at most {runner.MAX_WORKERS} workers")
    runner._limit(a.mask)                     # below normal priority (+ E-core mask on Windows); children inherit
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    key = deal.resolve(a.key)
    jobs = [deal.seal(dict(j, strategy_seeds=None), key) for j in jobs_for(a.pilots, *a.seeds, a.games_per_opponent, a.field)]
    for j in jobs:
        if not j.get("strategy_seeds"):
            j["strategy_seeds"] = deal.strategy_seeds(j)
    t0 = time.time()
    # the ladder's condition: through the runner, behind the base
    rjobs = [{"id": j["id"], "seed": j["seed"], "first": None, "decks": j["decks"],
              "strategies": [f"bot:{s}" for s in j["specs"]], "strategy_seeds": j["strategy_seeds"],
              "deal": j.get("deal"), "labels": j["labels"]} for j in jobs]
    runner.run(rjobs, str(out / "guess.jsonl"), workers=a.workers, mask=a.mask, quiet=True, key=key)
    guess = []
    for line in (out / "guess.jsonl").read_text(encoding="utf-8").splitlines():
        g = json.loads(line)
        seat_cpu, seat_steps = [0, 0], [0, 0]
        for s, c, _ in g.get("steps", []):
            seat_cpu[s] += c
            seat_steps[s] += 1
        guess.append({"id": g["id"], "labels": g["labels"], "winner": g.get("winner"), "cpu": seat_cpu,
                      "steps": seat_steps})
    # the pilots' own condition
    with ProcessPoolExecutor(max_workers=a.workers, initializer=_init) as ex:
        native = list(ex.map(_native, jobs, chunksize=4))
    (out / "native.jsonl").write_text("".join(json.dumps(r) + "\n" for r in native), encoding="utf-8")
    res = {"seeds": a.seeds, "field": a.field, "games_per_opponent": a.games_per_opponent, "deal": deal.key_id(key) if key else None,
           "seconds": round(time.time() - t0), "默认猜测": summarize(guess, "默认猜测"),
           "原生": summarize(native, "原生")}
    (out / "result.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
