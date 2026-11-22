"""Batch runner (phase 1, item 1.3): many refereed games in parallel, every game logged so it can be replayed.

    python -m ladder.runner --jobs jobs.jsonl --out games.jsonl --workers 23 [--mask 0x3FC3FC] [--step-limit 30]

(run from analysis/ladder, or with analysis/ladder on PYTHONPATH). A job is one JSON line:
    {"id": "g-000001", "seed": 87xxxxxx, "first": 0 | 1 | null,
     "decks": [deck code or card ids, ...two], "strategies": [spec, spec], "strategy_seeds": [int, int],
     "labels": {...anything kept in the log: member ids, versions...}}
Strategy specs: "bot:<arena spec>" (the base's BotStrategy over that bot, e.g. "bot:mcts:100+plan"),
"mix:<eps>:<arena spec>" (the same with a random legal move at rate eps: host-made weaker versions for the
known-strength checks), or "py:<module>:<factory>" (a factory called with seed=...; e.g. a player's submission).

Rules it applies (task spec §4.2): a strategy that raises loses (crash); one that returns a move not in the legal
list loses (illegal: judged on the referee's own list; the strategy is handed fresh copies of the moves, never the
referee's objects; anything that isn't exactly one of those moves, or can't even be compared, is illegal; LD-37,
LD-38's review); one whose single decision runs past --step-limit seconds of wall time, judging the returned move
included, loses (timeout: the worker is killed and replaced). "Raises" includes SystemExit and KeyboardInterrupt from
the strategy's own call (LD-36): only a real Ctrl+C, marked by its signal handler, stops the tool (`host_ctrl_c`);
one raised in the end-of-game guess leaves the result alone. Text a strategy controls (error messages, the shown
move) is cleaned of lone surrogates before it is kept, so it can always be written. An engine error, while
applying a legal move or around it, can't be pinned on either side: the game is void. So is a worker that dies outright
(os._exit, killed): code of either side can do that. The 60-turn cap gives a draw (assumption A3).

Limits (Salem's computer): Salem S10 (11-22 08:49Z) allows all cores ("这个项目你可以全核开跑"): at most 23 worker
processes (+ this one = the 24 logical CPUs), below normal priority, and on Windows the affinity mask given by --mask
if any; workers inherit both. Runs that compare per-step compute between games (submit receive, gate, the pilot tool)
take --mask 0x3FC3FC (the 16 E-cores, at most 15 workers) so that every game runs on one core type (A44). Before
S10: at most 11 workers, E-cores only (plan 红线 8, A6). BLAS threads are pinned to 1 and PYTHONHASHSEED to 0 in every worker.

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
import re
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent            # analysis/ladder/ladder
ROOT = HERE.parents[2]                             # repository root
MAX_WORKERS = 23                                  # Salem S10: all 24 logical CPUs, with this process
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


# --- log lines -----------------------------------------------------------------------------------------------

_SEPARATORS = {"\u2028": "\\u2028", "\u2029": "\\u2029", "\x85": "\\u0085"}
_SURROGATES = re.compile("[\ud800-\udfff]")


def jsonl(obj) -> str:
    """One JSON line with Chinese kept readable, and with the three characters str.splitlines() also breaks lines at
    (U+2028, U+2029, U+0085; json.dumps already escapes the control characters) escaped: a strategy's error message
    holding one must not split a log line in two (11-22 third pass, LD-37)."""
    text = json.dumps(obj, ensure_ascii=False)
    for raw, esc in _SEPARATORS.items():
        text = text.replace(raw, esc)
    return clean(text) + "\n"


def clean(text: str) -> str:
    """`text` with lone surrogates (U+D800-U+DFFF, which no UTF-8 file can take) turned into U+FFFD. A strategy's
    error message or repr can hold them; left in, the log write raises and the whole run stops on every resume
    (11-22 fourth pass)."""
    return _SURROGATES.sub("\ufffd", text)


def tb(limit=8) -> str:
    """The current exception's traceback, cleaned (it can carry a strategy's own message)."""
    return clean(traceback.format_exc(limit=limit))


# --- strategies ----------------------------------------------------------------------------------------------

def make_strategy(spec: str, seed: int):
    if spec.startswith("bot:"):
        from ladder.strategy import BotStrategy
        return BotStrategy(spec[4:], seed=seed)
    if spec.startswith("mix:"):                       # host-made weaker versions for the known-strength checks
        from ladder.strategy import MixStrategy
        _, eps, bot = spec.split(":", 2)
        return MixStrategy(float(eps), bot, seed=seed)
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

_CTRL_C = [False]                                  # set by a real Ctrl+C while `host_ctrl_c` is on


def _on_ctrl_c(signum, frame):
    _CTRL_C[0] = True
    raise KeyboardInterrupt


class host_ctrl_c:
    """While a game is played in a process that doesn't ignore Ctrl+C (the host's own: a replay, a submission check;
    an arena worker), a real Ctrl+C goes through a handler that marks it before raising, so `host_interrupt` can tell
    it from a KeyboardInterrupt a strategy raised itself (11-22 fourth pass: judging by the handler setting alone
    made a strategy's own KeyboardInterrupt stop the replay of its logged crash). Where SIGINT is ignored (the runner's
    workers) nothing is installed and every KeyboardInterrupt is a strategy's; off the main thread nothing can be."""
    def __enter__(self):
        _CTRL_C[0] = False
        self.prev = None
        try:
            cur = signal.getsignal(signal.SIGINT)
            if cur is not signal.SIG_IGN:
                signal.signal(signal.SIGINT, _on_ctrl_c)
                self.prev = cur if cur is not None else signal.SIG_DFL
        except ValueError:                             # not the main thread
            pass
        return self

    def __exit__(self, *exc):
        if self.prev is not None:
            signal.signal(signal.SIGINT, self.prev)
        return False


def host_interrupt(e: BaseException) -> bool:
    """True only for the host's own Ctrl+C (marked by `host_ctrl_c`): that stops the tool. Any other
    KeyboardInterrupt, and SystemExit, came from a strategy's code and counts against it (LD-36, LD-37)."""
    return isinstance(e, KeyboardInterrupt) and _CTRL_C[0]


def legal_choice(action, legal: list):
    """The referee's own element of `legal` that `action` (what a strategy returned) stands for, or None. Only an
    object of exactly an engine action's type that equals one of the referee's moves counts, and any error in
    comparing makes the move illegal (11-22 third pass, LD-37: a strategy could append moves to the list it was
    given, or return an object whose comparison raises to have the game written off). The strategy must have been
    handed `offer(legal)`, not `legal`: the moves are frozen dataclasses, but their __init__ can still rewrite one in
    place, and a rewritten referee object would equal itself here (fourth pass)."""
    t = type(action)
    for a in legal:
        if type(a) is t:
            try:
                if a == action:
                    return a
            except BaseException as e:                 # noqa: BLE001
                if host_interrupt(e):
                    raise
                return None
    return None


def offer(legal: list) -> list:
    """Fresh copies of the referee's moves for a strategy (rebuilt from their dicts, the way a log is replayed)."""
    from svsim.core.actions import from_dict, to_dict
    return [from_dict(to_dict(a)) for a in legal]


def safe_repr(x, limit=300) -> str:
    try:
        return clean(repr(x)[:limit])
    except BaseException as e:                         # noqa: BLE001
        if host_interrupt(e):
            raise
        return "<a returned object that can't be shown>"


def play_job(job: dict, beat=None) -> dict:
    """Play one job in this process. `beat` (a shared array: seat, step start in ns) lets the parent time a step."""
    with host_ctrl_c():
        return _play(job, beat)


def _play(job: dict, beat) -> dict:
    from svsim.core.actions import to_dict
    from svsim.core.engine import apply, legal_actions
    from ladder import base, deal
    counter, unit = _make_counter()
    decks = [load_deck(d) for d in job["decks"]]
    seeds = deal.strategy_seeds(job)
    out = {"id": job["id"], "seed": job["seed"], "first_arg": job.get("first"), "decks": job["decks"],
           "strategies": job["strategies"], "strategy_seeds": seeds, "deal": job.get("deal"),
           "labels": job.get("labels", {}),
           "cpu_unit": unit, "actions": [], "steps": [], "result": None, "winner": None, "loser": None}
    missing = [unscripted(d) for d in decks]
    if any(missing):
        out.update(result="void", error=f"cards with no script (would play as vanilla): {missing}")
        return out
    try:
        strategies = [make_strategy(s, seed) for s, seed in zip(job["strategies"], seeds)]
    except BaseException as e:                        # SystemExit too: a factory can't end the worker (LD-36)
        if host_interrupt(e):
            raise
        out.update(result="void", error="strategy failed to load:\n" + tb(5))
        return out
    try:
        _, state = deal.start(job, first="first")      # base-2: the keyed deal when the job carries one (LD-27/29)
    except Exception:
        out.update(result="void", error="engine error at the start:\n" + tb())
        return out
    out["first"] = state.first
    tracker = base.Tracker(state)
    while not state.over:
        seat = state.active
        try:                                          # the engine's and the base's side, not the strategies'
            actions = legal_actions(state)
            offered = offer(actions)                  # fresh objects: the referee's own never leave its hands
            pos = base.public_position(state, seat, tracker)
        except Exception:
            out.update(result="void", error="engine error outside a move:\n" + tb())
            break
        if beat is not None:
            beat[0], beat[1] = seat, time.monotonic_ns()
        crash = shown = chosen = None
        w0, c0 = time.perf_counter_ns(), counter()
        try:
            try:
                action = strategies[seat].act(pos, offered)
            except BaseException as e:                # SystemExit, KeyboardInterrupt too: the strategy's own doing
                if host_interrupt(e):                 # (only the host's marked Ctrl+C stops the tool)
                    raise
                crash = tb()
            else:
                c1, w1 = counter(), time.perf_counter_ns()
                out["steps"].append([seat, c1 - c0, (w1 - w0) // 1000])     # seat, compute (cpu_unit), wall in us
                chosen = legal_choice(action, actions)   # still on the step's clock: judging runs the returned
                if chosen is None:                       # object's own code (its __eq__, its __repr__)
                    shown = safe_repr(action)
        finally:
            if beat is not None:
                beat[1] = 0
        if crash is not None:
            out.update(result="crash", loser=seat, winner=1 - seat, error=crash)
            break
        if chosen is None:
            out.update(result="illegal", loser=seat, winner=1 - seat, error=shown)
            break
        action = chosen                               # from here on the referee's own object
        try:
            out["actions"].append(to_dict(action))
            tracker.before(state)
        except Exception:
            out.update(result="void", error="engine error outside a move:\n" + tb())
            break
        try:
            apply(state, action)
        except Exception:
            out.update(result="void", error="engine error on a legal move:\n" + tb())
            break
        try:
            tracker.after(state)
        except Exception:
            out.update(result="void", error="engine error outside a move:\n" + tb())
            break
    if out["result"] is None:
        out["winner"] = state.winner if state.winner in (0, 1) else None
        out["result"] = "normal" if out["winner"] is not None else "draw"
    out["turns"] = state.turn
    og = []
    for seat in (0, 1):
        try:
            pos = base.public_position(state, seat, tracker)
            og.append(base.out_of_guess(strategies[seat].guess(pos), tracker.revealed[1 - seat]))
        except BaseException as e:                    # SystemExit in a guess can't void a finished game (LD-36)
            if host_interrupt(e):
                raise
            og.append(None)
    out["out_of_guess"] = og            # shown opponent cards outside each side's guess, at the end
    return out


# --- workers and the watchdog ----------------------------------------------------------------------------------

def _worker(inq, results_q, beat, wid):
    """One job at a time from its own queue, so the parent always knows which job a worker holds."""
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)      # Ctrl+C stops the parent, which ends the workers; inside a
    #                                                   worker a KeyboardInterrupt is then a strategy's own (LD-36)
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
            res = {"id": job["id"], "seed": job.get("seed"), "decks": job.get("decks"),
                   "strategies": job.get("strategies"), "deal": job.get("deal"), "labels": job.get("labels", {}),
                   "result": "void", "error": "runner error:\n" + tb()}
        res["worker"] = wid
        results_q.put(res)


E_CORES = 0x3FC3FC                                # the 16 E-cores of Salem's computer (ENVIRONMENT.md)


def one_core_type(mask):
    """A44: a run that compares per-step compute between games must keep every game on one core type (all cores
    since S10 mix P- and E-cores, which differ in speed). On Windows the mask is required; elsewhere it is ignored."""
    if os.name == "nt" and mask is None:
        raise SystemExit(f"this run compares per-step compute: give --mask {hex(E_CORES)} (the E-cores; A44)")
    return None if mask is None else hex(mask)


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


def run(jobs, out_path: str, workers: int = 4, step_limit: float = 30.0, mask=None, quiet=False,
        on_result=None, key="auto") -> dict:
    """Play `jobs`, appending one log line per game to `out_path` (skipping ids already there).

    `key` (base-2, ladder/deal.py): "auto" = $LADDER_KEY_FILE or the host's key file if there is one; None = the
    old deal; bytes or a path. Each job is sealed here, in this process, before a worker gets it.

    `jobs` is a list, or an iterator that is asked for the next job only when a worker is free (the pool manager
    makes each pairing from the CRs of that moment). `on_result(log)` is called in this process, in the order the
    games end, after the line is written (the pool manager settles CR there)."""
    if workers > MAX_WORKERS:
        raise SystemExit(f"at most {MAX_WORKERS} workers ({MAX_WORKERS + 1} processes with this one)")
    out = Path(out_path)
    done = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip(" \t\r\n\x00")
            if line:
                try:                                     # a power cut can leave a half-written last line
                    done.add(json.loads(line)["id"])
                except (ValueError, KeyError):
                    pass
    if isinstance(jobs, list):
        jobs = [j for j in jobs if j["id"] not in done]
        if not jobs:
            return {"played": 0, "skipped": len(done)}
        workers = min(workers, len(jobs))
    source = iter(jobs)
    exhausted = False

    from ladder import deal
    the_key = deal.resolve(key)
    if isinstance(jobs, list):
        for j in jobs:                                   # fail before any worker starts
            deal.require(j, the_key)

    def take():
        nonlocal exhausted
        while not exhausted:
            job = next(source, None)
            if job is None:
                exhausted = True
            elif job["id"] not in done:
                deal.require(job, the_key)
                return deal.seal(job, the_key)
        return None
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

    pool = [spawn(i) for i in range(workers)]
    t0, count, counts = time.time(), 0, {}

    def write(f, res):
        nonlocal count
        res["provenance"], res["limits"] = prov, limits
        f.write(jsonl(res))
        f.flush()
        if on_result is not None:
            on_result(res)
        count += 1
        counts[res["result"]] = counts.get(res["result"], 0) + 1
        if not quiet and count % 100 == 0:
            print(f"{count} games, {time.time() - t0:.0f}s", file=sys.stderr, flush=True)

    def stub(job, result, **kw):
        return {"id": job["id"], "seed": job["seed"], "first_arg": job.get("first"), "decks": job["decks"],
                "strategies": job["strategies"], "strategy_seeds": job.get("strategy_seeds"),
                "deal": job.get("deal"), "labels": job.get("labels", {}), "result": result, **kw}

    try:
        with out.open("a", encoding="utf-8") as f:
            while True:
                for w in pool:                                          # hand out work
                    if w["job"] is None and not exhausted:
                        w["job"] = take()
                        if w["job"] is not None:
                            w["inq"].put(w["job"])
                if exhausted and not any(w["job"] for w in pool):
                    break
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
                        # not pinned on a side: any code in the process (a thread of either strategy) can end it
                        write(f, stub(job, "void", error=f"worker died (exit code {w['proc'].exitcode})"))
                        pool[i] = spawn(i)
    except BaseException:                             # Ctrl+C or an error here: the workers ignore Ctrl+C
        for w in pool:                                # (LD-36), so end them before going
            if w["proc"].is_alive():
                w["proc"].kill()
        raise
    for w in pool:
        w["inq"].put(None)
    for w in pool:
        w["proc"].join(timeout=10)
    return {"played": count, "skipped": len(done), "seconds": round(time.time() - t0, 1), "results": counts,
            "deal": deal.key_id(the_key) if the_key else None}


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
