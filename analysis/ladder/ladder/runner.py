"""Batch runner (phase 1, item 1.3): many refereed games in parallel, every game logged so it can be replayed.

    python -m ladder.runner --jobs jobs.jsonl --out games.jsonl --workers 11 [--mask 0x3FC3FC] [--step-limit 30]

(run from analysis/ladder, or with analysis/ladder on PYTHONPATH). A job is one JSON line:
    {"id": "g-000001", "seed": 87xxxxxx, "first": 0 | 1 | null,
     "decks": [deck code or card ids, ...two], "strategies": [spec, spec], "strategy_seeds": [int, int],
     "labels": {...anything kept in the log: member ids, versions...}}
Strategy specs: "bot:<arena spec>" (the base's BotStrategy over that bot, e.g. "bot:mcts:100+plan"), or
"py:<module>:<factory>" (a factory called with seed=...; e.g. a player's submission).

Rules it applies (task spec §4.2): a strategy that raises loses (crash); one that returns a move not in the legal
list loses (illegal); one whose single decision runs past --step-limit seconds of wall time loses (timeout: the
worker is killed and replaced). An engine error while applying a legal move can't be pinned on either side: the
game is void. The 60-turn cap gives a draw (assumption A3).

Limits (Salem's computer, plan 红线 8 and assumption A6): at most 11 worker processes (+ this one = 12), below
normal priority, and on Windows the affinity mask given by --mask (0x3FC3FC = the 16 E-cores); workers inherit
both. BLAS threads are pinned to 1 and PYTHONHASHSEED to 0 in every worker.

Per-decision compute: on Windows the thread's CPU cycles (QueryThreadCycleTime; time.process_time is only good to
15.6 ms there), elsewhere the thread's CPU nanoseconds. The unit is in every log line.

Resuming: a rerun with the same --out skips the job ids already in it.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import platform
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent            # analysis/ladder/ladder
ROOT = HERE.parents[2]                             # repository root
MAX_WORKERS = 11
for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(var, "1")
os.environ.setdefault("PYTHONHASHSEED", "0")


# --- compute counter -----------------------------------------------------------------------------------------

def _make_counter():
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.GetCurrentThread.restype = wintypes.HANDLE
        k.QueryThreadCycleTime.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_ulonglong)]
        k.QueryThreadCycleTime.restype = wintypes.BOOL
        h = k.GetCurrentThread()
        buf = ctypes.c_ulonglong()

        def cycles() -> int:
            k.QueryThreadCycleTime(h, ctypes.byref(buf))
            return buf.value
        return cycles, "cycles"
    return time.thread_time_ns, "ns"


# --- strategies ----------------------------------------------------------------------------------------------

def make_strategy(spec: str, seed: int):
    if spec.startswith("bot:"):
        from ladder.strategy import BotStrategy
        return BotStrategy(spec[4:], seed=seed)
    if spec.startswith("py:"):
        import importlib
        _, module, attr = spec.split(":", 2)
        return getattr(importlib.import_module(module), attr)(seed=seed)
    raise ValueError(f"unknown strategy spec {spec!r}")


def load_deck(x):
    """A deck from a deck code or a list of card ids. Loads every card script first: the engine silently plays a
    card with no registered script as vanilla, and svsim.cards.decks registers only some classes' scripts
    (ENVIRONMENT 9.4)."""
    import svsim.cards.library  # noqa: F401
    from svsim.cards.decks import from_hash
    from svsim.cards.pool import card
    return from_hash(x) if isinstance(x, str) else [card(i) for i in x]


def unscripted(deck) -> list[int]:
    """Cards in `deck` with an ability but no script (they would play as vanilla)."""
    from svsim.cards.decks import unimplemented
    return [c.card_id for c in unimplemented(deck)]


# --- one game ------------------------------------------------------------------------------------------------

def play_job(job: dict, beat=None) -> dict:
    """Play one job in this process. `beat` (a shared array: seat, step start in ns) lets the parent time a step."""
    from svsim.core.actions import to_dict
    from svsim.core.engine import apply, legal_actions, new_game
    from ladder import base
    counter, unit = _make_counter()
    decks = [load_deck(d) for d in job["decks"]]
    seeds = job.get("strategy_seeds") or [job["seed"] * 2 + 1, job["seed"] * 2 + 2]
    out = {"id": job["id"], "seed": job["seed"], "first_arg": job.get("first"), "decks": job["decks"],
           "strategies": job["strategies"], "strategy_seeds": seeds, "labels": job.get("labels", {}),
           "cpu_unit": unit, "actions": [], "steps": [], "result": None, "winner": None, "loser": None}
    missing = [unscripted(d) for d in decks]
    if any(missing):
        out.update(result="void", error=f"cards with no script (would play as vanilla): {missing}")
        return out
    try:
        strategies = [make_strategy(s, seed) for s, seed in zip(job["strategies"], seeds)]
    except Exception:
        out.update(result="void", error="strategy failed to load:\n" + traceback.format_exc(limit=5))
        return out
    state = new_game(decks[0], decks[1], seed=job["seed"], first=job.get("first"))
    out["first"] = state.first
    tracker = base.Tracker(state)
    while not state.over:
        seat = state.active
        actions = legal_actions(state)
        pos = base.public_position(state, seat, tracker)
        if beat is not None:
            beat[0], beat[1] = seat, time.monotonic_ns()
        w0, c0 = time.perf_counter_ns(), counter()
        try:
            action = strategies[seat].act(pos, actions)
        except Exception:
            out.update(result="crash", loser=seat, winner=1 - seat,
                       error=traceback.format_exc(limit=8))
            break
        finally:
            if beat is not None:
                beat[1] = 0
        c1, w1 = counter(), time.perf_counter_ns()
        out["steps"].append([seat, c1 - c0, (w1 - w0) // 1000])     # seat, compute (cpu_unit), wall in us
        if action not in actions:
            out.update(result="illegal", loser=seat, winner=1 - seat, error=repr(action))
            break
        out["actions"].append(to_dict(action))
        tracker.before(state)
        try:
            apply(state, action)
        except Exception:
            out.update(result="void", error="engine error on a legal move:\n" + traceback.format_exc(limit=8))
            break
        tracker.after(state)
    if out["result"] is None:
        out["winner"] = state.winner if state.winner in (0, 1) else None
        out["result"] = "normal" if out["winner"] is not None else "draw"
    out["turns"] = state.turn
    og = []
    for seat in (0, 1):
        try:
            pos = base.public_position(state, seat, tracker)
            og.append(base.out_of_guess(strategies[seat].guess(pos), tracker.revealed[1 - seat]))
        except Exception:
            og.append(None)
    out["out_of_guess"] = og            # shown opponent cards outside each side's guess, at the end
    return out


# --- workers and the watchdog ----------------------------------------------------------------------------------

def _worker(inq, results_q, beat, wid):
    """One job at a time from its own queue, so the parent always knows which job a worker holds."""
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(ROOT))
    for extra in filter(None, os.environ.get("LADDER_EXTRA_PATH", "").split(os.pathsep)):
        sys.path.insert(0, extra)                     # where submissions (or test strategies) live
    os.chdir(ROOT)
    while True:
        job = inq.get()
        if job is None:
            return
        try:
            res = play_job(job, beat)
        except Exception:
            res = {"id": job["id"], "result": "void", "error": "runner error:\n" + traceback.format_exc(limit=8)}
        res["worker"] = wid
        results_q.put(res)


def _limit(mask):
    """Below normal priority (and the affinity mask on Windows) for this process; workers inherit both."""
    if os.name == "nt":
        sys.path.insert(0, str(ROOT))
        import ctypes
        from svsim.tools.host import BELOW_NORMAL, _kernel32
        k = _kernel32()
        h = k.GetCurrentProcess()
        if not k.SetPriorityClass(h, BELOW_NORMAL):
            raise OSError(ctypes.get_last_error(), "SetPriorityClass failed")
        if mask is not None and not k.SetProcessAffinityMask(h, mask):
            raise OSError(ctypes.get_last_error(), "SetProcessAffinityMask failed")
        p, s = ctypes.c_size_t(), ctypes.c_size_t()
        k.GetProcessAffinityMask(h, ctypes.byref(p), ctypes.byref(s))
        if k.GetPriorityClass(h) != BELOW_NORMAL or (mask is not None and p.value != mask):
            raise RuntimeError("the limits didn't hold")
        return {"priority": "below normal", "mask": hex(p.value)}
    if hasattr(os, "nice") and os.nice(0) < 10:
        os.nice(10 - os.nice(0))
    return {"priority": f"nice {os.nice(0)}" if hasattr(os, "nice") else "unchanged"}


def provenance() -> dict:
    """Code and platform versions, for every log line (replays must run where the games ran: ENVIRONMENT 9.4)."""
    def git(*args):
        try:
            return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                                  timeout=20).stdout.strip()
        except Exception:
            return None
    try:
        import numpy
        npv = numpy.__version__
    except Exception:
        npv = None
    return {"commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain", "--", "svsim", "analysis/ladder/ladder")),
            "python": platform.python_version(), "numpy": npv, "os": platform.platform()}


def run(jobs: list, out_path: str, workers: int = 4, step_limit: float = 30.0, mask=None, quiet=False) -> dict:
    """Play `jobs`, appending one log line per game to `out_path` (skipping ids already there)."""
    if workers > MAX_WORKERS:
        raise SystemExit(f"at most {MAX_WORKERS} workers (12 processes with this one)")
    out = Path(out_path)
    done = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["id"])
    pending = [j for j in jobs if j["id"] not in done]
    if not pending:
        return {"played": 0, "skipped": len(done)}
    limits = _limit(mask)
    prov = provenance()
    ctx = mp.get_context("spawn")
    results_q = ctx.Queue()

    def spawn(wid):
        inq = ctx.Queue()
        beat = ctx.Array("q", [-1, 0], lock=False)               # seat thinking, its step start (monotonic ns)
        p = ctx.Process(target=_worker, args=(inq, results_q, beat, wid), daemon=True)
        p.start()
        return {"proc": p, "inq": inq, "beat": beat, "job": None}

    pool = [spawn(i) for i in range(min(workers, len(pending)))]
    t0, count, counts = time.time(), 0, {}

    def write(f, res):
        nonlocal count
        res["provenance"], res["limits"] = prov, limits
        f.write(json.dumps(res, ensure_ascii=False) + "\n")
        f.flush()
        count += 1
        counts[res["result"]] = counts.get(res["result"], 0) + 1
        if not quiet and count % 100 == 0:
            print(f"{count} games, {time.time() - t0:.0f}s", file=sys.stderr, flush=True)

    def stub(job, result, **kw):
        return {"id": job["id"], "seed": job["seed"], "first_arg": job.get("first"), "decks": job["decks"],
                "strategies": job["strategies"], "strategy_seeds": job.get("strategy_seeds"),
                "labels": job.get("labels", {}), "result": result, **kw}

    with out.open("a", encoding="utf-8") as f:
        while pending or any(w["job"] for w in pool):
            for w in pool:                                          # hand out work
                if w["job"] is None and pending:
                    w["job"] = pending.pop(0)
                    w["inq"].put(w["job"])
            try:
                res = results_q.get(timeout=0.25)
            except Exception:
                res = None
            if res is not None:
                w = pool[res.pop("worker")]
                if w["job"] is not None and w["job"]["id"] == res["id"]:
                    w["job"] = None
                    write(f, res)
                continue
            now = time.monotonic_ns()
            for i, w in enumerate(pool):                            # the watchdog
                job = w["job"]
                if job is None:
                    continue
                started = w["beat"][1]
                if started and (now - started) / 1e9 > step_limit:
                    seat = int(w["beat"][0])
                    w["proc"].kill()
                    w["proc"].join()
                    write(f, stub(job, "timeout", loser=seat, winner=1 - seat,
                                  error=f"one decision ran past {step_limit}s of wall time"))
                    pool[i] = spawn(i)
                elif not w["proc"].is_alive():
                    write(f, stub(job, "void", error=f"worker died (exit code {w['proc'].exitcode})"))
                    pool[i] = spawn(i)
    for w in pool:
        w["inq"].put(None)
    for w in pool:
        w["proc"].join(timeout=10)
    return {"played": count, "skipped": len(done), "seconds": round(time.time() - t0, 1), "results": counts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--step-limit", type=float, default=30.0)
    ap.add_argument("--mask", default=None)
    a = ap.parse_args()
    jobs = [json.loads(l) for l in Path(a.jobs).read_text(encoding="utf-8").splitlines() if l.strip()]
    print(json.dumps(run(jobs, a.out, a.workers, a.step_limit, int(a.mask, 16) if a.mask else None)))


if __name__ == "__main__":
    main()
