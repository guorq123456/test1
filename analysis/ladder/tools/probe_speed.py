"""Phase-0 speed probe (read-only measurement, no strategy work).

    python analysis/ladder/tools/probe_speed.py --spec mcts:100+plan --games 84 --workers 12 \
        --mask 0x3FC3FC --out probe.jsonl

Plays the frozen-7 bot decks (analysis/pilot/fields/bot-frozen7.txt) against each other, both sides the same
spec, every ordered pair of different decks in turn, deal seed = --seed + game index. Records per game: decks,
seed, first player, winner, turns, decisions, wall seconds, CPU seconds (time.process_time, this worker process
only), and per decision the CPU seconds. On Windows --mask sets the process affinity mask (default: leave it)
and the priority class goes to below normal before any worker starts; workers inherit both. Prints a summary.

The measurement is about speed only: these seeds and games are not for any conclusion about strength.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as S
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIELD = ROOT / "analysis" / "pilot" / "fields" / "bot-frozen7.txt"


def load7():
    out = []
    for line in FIELD.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            name, code = line.strip().split("|")
            out.append((name, code))
    return out


def _limit(mask: int | None) -> dict:
    """Below normal priority and (optionally) an affinity mask for this process; read back."""
    if os.name != "nt":
        if hasattr(os, "nice"):
            os.nice(10)
        return {"os": os.name, "cpus": len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None}
    import ctypes
    sys.path.insert(0, str(ROOT))
    from svsim.tools.host import BELOW_NORMAL, _kernel32
    k = _kernel32()
    h = k.GetCurrentProcess()
    if not k.SetPriorityClass(h, BELOW_NORMAL):
        raise OSError(ctypes.get_last_error(), "SetPriorityClass failed")
    if mask is not None and not k.SetProcessAffinityMask(h, mask):
        raise OSError(ctypes.get_last_error(), "SetProcessAffinityMask failed")
    p, s = ctypes.c_size_t(), ctypes.c_size_t()
    k.GetProcessAffinityMask(h, ctypes.byref(p), ctypes.byref(s))
    pri = k.GetPriorityClass(h)
    if pri != BELOW_NORMAL or (mask is not None and p.value != mask):
        raise RuntimeError(f"settings didn't hold: priority {pri:#x}, mask {p.value:#x}")
    return {"os": "nt", "mask": hex(p.value), "system_mask": hex(s.value), "cpus": bin(p.value).count("1"),
            "priority": "below normal"}


def one(job):
    i, a, b, seed, spec = job
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    from svsim.cards.decks import from_hash
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools.arena import make_agent
    decks = load7()
    agents = [make_agent(spec, seed * 2 + 1), make_agent(spec, seed * 2 + 2)]
    st = new_game(from_hash(decks[a][1]), from_hash(decks[b][1]), seed=seed)
    cpus, side = [], []
    w0, c0 = time.perf_counter(), time.process_time()
    while not st.over:
        acts = legal_actions(st)
        c = time.process_time()
        act = agents[st.active].act(st, acts)
        cpus.append(round(time.process_time() - c, 5))
        side.append(st.active)
        apply(st, act)
    return dict(i=i, a=decks[a][0], b=decks[b][0], seed=seed, first=st.first, winner=st.winner, turn=st.turn,
                n=len(cpus), wall=round(time.perf_counter() - w0, 4), cpu=round(time.process_time() - c0, 4),
                cpus=cpus, side=side, pid=os.getpid())


def summary(rows, total_wall, workers, info, spec):
    allc = sorted(c for r in rows for c in r["cpus"])
    q = lambda f: 1000 * allc[min(len(allc) - 1, int(f * len(allc)))]
    return {
        "spec": spec, "games": len(rows), "workers": workers, "limits": info,
        "draws": sum(1 for r in rows if r["winner"] not in (0, 1)),
        "decisions_per_game_mean": round(S.mean(r["n"] for r in rows), 1),
        "game_wall_s_mean": round(S.mean(r["wall"] for r in rows), 3),
        "game_cpu_s_mean": round(S.mean(r["cpu"] for r in rows), 3),
        "decision_cpu_ms": {"mean": round(1000 * S.mean(allc), 2), "median": round(q(0.5), 2),
                            "p90": round(q(0.9), 2), "p99": round(q(0.99), 2), "max": round(1000 * allc[-1], 1)},
        "total_wall_s": round(total_wall, 1),
        "games_per_hour": round(3600 * len(rows) / total_wall),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="mcts:100+plan")
    ap.add_argument("--games", type=int, default=84)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=99_000_000, help="first deal seed (phase-0 probe bank)")
    ap.add_argument("--mask", default=None, help="Windows affinity mask, e.g. 0x3FC3FC")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.workers > 12:
        raise SystemExit("at most 12 processes (Salem's rule)")
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[var] = "1"              # one thread per process, so CPU time is this game's own
    info = _limit(int(args.mask, 16) if args.mask else None)
    print("limits:", info, flush=True)
    jobs, k = [], 0
    while len(jobs) < args.games:
        for a in range(7):
            for b in range(7):
                if a != b and len(jobs) < args.games:
                    jobs.append((k, a, b, args.seed + k, args.spec))
                    k += 1
    t0 = time.perf_counter()
    rows = []
    with Pool(args.workers) as pool, open(args.out, "w", encoding="utf-8") as f:
        for r in pool.imap_unordered(one, jobs):
            rows.append(r)
            f.write(json.dumps(r) + "\n")
            f.flush()
    s = summary(rows, time.perf_counter() - t0, args.workers, info, args.spec)
    Path(args.out).with_suffix(".summary.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
    print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
