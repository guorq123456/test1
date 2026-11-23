"""The referee without the tripwire, for the host's own strategies only (S17, Salem 11-23 16:44Z: the tripwire, locked in
ladder/watch.py, is not changed; games of host strategies that load a trained model go around it).

Why: a host strategy's prior model (svsim.learn.setpolicy.SetPolicy) adds rows to its own table for cards it has not
met in training. The tripwire takes that for a change to the simulator and voids the game (LD-59). The host's own
measurements with such strategies (the plan's 2.5, and host references in ladder.puzzles) are played here.

What is the same as ladder.runner.run: the game itself (runner.play_job: the keyed deal, base.public_position for
each seat, the offered moves, the referee's legal-move check, the per-decision compute counter, the log line), the
warm-up game before a worker's first job, the memo caches emptied before every game (watch.reset_caches), the job's
seal with the key, below-normal priority and the affinity mask, resuming a log by game id.
What is not: the tripwire (watch.snapshot / changes), the audit hook (guard: a game can't touch the computer), the
wall-clock watchdog (a step past the step limit, a worker idle with no clock on), the lru caches the tripwire finds
(the runner empties them too; here they stay warm after the warm-up game: pure memos keyed on card definitions, they
change no move, only the compute counter by about 1%, the same way for both seats), and the runner's own worker pool
(a worker that dies stops the run here, with the games already written kept: run it again and it resumes). None of
those can matter for host code, and a player's code never comes here: `run` and `map_tasks` refuse any strategy that
is not one of the host's ("bot:", "mix:"). Ctrl+C is as in the runner: the workers ignore it, the parent stops them
and leaves (the games already written are kept).
Every line written here says so: "referee": "outside" (the audit, the reports and the host's copies can tell).
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import signal
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HOST_SPECS = ("bot:", "mix:")
REFEREE = "outside"


class OutsideError(Exception):
    pass


def host_only(specs) -> None:
    bad = [s for s in specs if not (isinstance(s, str) and s.startswith(HOST_SPECS))]
    if bad:
        raise OutsideError(f"only the host's own strategies are played outside the tripwire, not {bad[:3]}")


def _bot_options(spec: str) -> list:
    """The options of a host spec's bot after the named versions are spelled out, as svsim.tools.arena.make_agent
    does (pilot-T1-SWORD-1 is "mcts:N+plan+setnet=...+puct=...")."""
    from svsim.tools.arena import VERSIONS
    bot = spec[len("bot:"):] if spec.startswith("bot:") else spec.split(":", 2)[2] if spec.count(":") >= 2 else ""
    parts = bot.split("+")
    for _ in range(5):                                # make_agent spells out twice; more can only find more
        if not parts or parts[0] not in VERSIONS:
            break
        parts = VERSIONS[parts[0]].split("+") + parts[1:]
    return parts[1:]


def trained(spec: str) -> bool:
    """A host spec that loads a trained move prior (a pilot: svsim.ui.session.pilot_native_spec's setnet= / puct=,
    written out or as a named version such as bot:pilot-T1-SWORD-1)."""
    if not isinstance(spec, str) or not spec.startswith(HOST_SPECS):
        return False
    return any(o.startswith(("setnet=", "puct=")) for o in _bot_options(spec))


def _init():
    signal.signal(signal.SIGINT, signal.SIG_IGN)      # as the runner's workers: Ctrl+C stops the parent, which ends them
    for p in (str(HERE.parent), str(ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    os.chdir(ROOT)                                    # model paths are relative to the repo, as in the runner
    import svsim.cards.library  # noqa: F401
    from ladder import runner, watch
    runner._warm_up()                                 # as the runner's workers (seed runner.WARM_UP_SEED)
    watch.reset_caches()


def _one(job: dict) -> dict:
    from ladder import runner, watch
    watch.reset_caches()                              # nothing one game leaves in the memo caches reaches the next
    try:
        return runner.play_job(job)
    except Exception:
        return {"id": job["id"], "seed": job.get("seed"), "decks": job.get("decks"),
                "strategies": job.get("strategies"), "deal": job.get("deal"), "labels": job.get("labels", {}),
                "result": "void", "error": "runner error:\n" + runner.tb()}


def _task(item):
    import importlib
    from ladder import runner, watch
    fn, task = item
    mod, name = fn.split(":")
    watch.reset_caches()
    try:
        return {"value": getattr(importlib.import_module(mod), name)(task, None)}
    except Exception:
        return {"error": "runner error:\n" + runner.tb()}


def _done(out: Path) -> set:
    done = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip(" \t\r\n\x00")
            if line:
                try:
                    done.add(json.loads(line)["id"])
                except (ValueError, KeyError, TypeError):
                    pass
    return done


def run(jobs: list, out_path, workers: int = 4, mask=None, key="auto", quiet: bool = True) -> dict:
    """Play `jobs` (host strategies only), appending one log line per game to `out_path` (ids already there are
    skipped), as ladder.runner.run does but without the tripwire (module docstring)."""
    from ladder import deal, runner
    if workers > runner.MAX_WORKERS:
        raise SystemExit(f"at most {runner.MAX_WORKERS} workers")
    for j in jobs:
        host_only(j["strategies"])
    out = Path(out_path)
    done = _done(out)
    jobs = [j for j in jobs if j["id"] not in done]
    if not jobs:
        return {"played": 0, "skipped": len(done), "referee": REFEREE}
    the_key = deal.resolve(key)
    for j in jobs:
        deal.require(j, the_key)
    sealed = [deal.seal(j, the_key) for j in jobs]
    limits = runner._limit(mask)
    prov = runner.provenance()
    if out.exists() and out.stat().st_size:
        with out.open("rb") as f:                     # a torn last line stays on its own (as the runner, LD-41)
            f.seek(-1, os.SEEK_END)
            torn = f.read(1) != b"\n"
        if torn:
            with out.open("a", encoding="utf-8") as f:
                f.write("\n")
    t0, counts = time.time(), {}
    ex = _pool(min(workers, len(sealed)))
    try:
        with out.open("a", encoding="utf-8") as f:
            futs = [ex.submit(_one, j) for j in sealed]
            for k, fut in enumerate(as_completed(futs), 1):
                res = fut.result()
                res["provenance"], res["limits"], res["referee"] = prov, limits, REFEREE
                f.write(runner.jsonl(res))
                f.flush()
                counts[res["result"]] = counts.get(res["result"], 0) + 1
                if not quiet and k % 100 == 0:
                    print(f"{k} games, {time.time() - t0:.0f}s", file=sys.stderr, flush=True)
    except BrokenProcessPool as e:
        _stop(ex)
        raise OutsideError(f"a worker died ({e}); the {sum(counts.values())} games written to {out} are kept: "
                           "run the same command again and it goes on from there") from None
    except BaseException:                             # Ctrl+C or an error here: stop the workers, don't wait for
        _stop(ex)                                     # the queued games (they would be played and thrown away)
        raise
    ex.shutdown(wait=True)
    return {"played": len(sealed), "skipped": len(done), "seconds": round(time.time() - t0, 1), "results": counts,
            "deal": deal.key_id(the_key) if the_key else None, "referee": REFEREE}


def map_tasks(fn: str, tasks: list, workers: int = 4, mask=None, specs_of=lambda t: [t.get("spec")]) -> list:
    """fn ("module:function", called as fn(task, None)) over `tasks`, host strategies only, without the tripwire:
    one result per task, in order, {"value": ...} or {"error": ...} (runner.guarded_map's shape)."""
    from ladder import runner
    for t in tasks:
        host_only(specs_of(t))
    if not tasks:
        return []
    runner._limit(mask)
    ex = _pool(min(workers, len(tasks)))
    try:
        res = list(ex.map(_task, [(fn, t) for t in tasks]))
    except BrokenProcessPool as e:
        _stop(ex)
        raise OutsideError(f"a worker died ({e})") from None
    except BaseException:
        _stop(ex)
        raise
    ex.shutdown(wait=True)
    return res


def _pool(n: int) -> ProcessPoolExecutor:
    return ProcessPoolExecutor(max_workers=n, initializer=_init, mp_context=mp.get_context("spawn"))


def _stop(ex: ProcessPoolExecutor) -> None:
    """End the pool now: the queued jobs are dropped and the workers killed (as the runner on Ctrl+C)."""
    procs = list((getattr(ex, "_processes", None) or {}).values())
    ex.shutdown(wait=False, cancel_futures=True)
    for p in procs:
        if p.is_alive():
            p.kill()
    for p in procs:
        p.join(timeout=10)
