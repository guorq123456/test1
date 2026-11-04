"""R1 pilot (the architecture thread 2026-10-30): labels that say which of two sibling moves is better, measured by
playing both on.

Every shared play net so far learned either the game's result (a better predictor of who wins that ranked a
decision's children worse than the hand-written score) or the recorded mcts:100+plan's choices (at best a copy of the
gate's own opponent). R1 asks for labels that carry something the teacher does not know: at a searched decision, the
teacher's two most-visited distinct moves are both played, and the game is played on from each child to the end `m`
times by mcts:100+plan on both sides. The j-th playout of the two children shares its randomness (common random
numbers): both decks reshuffled by the same generator, the same engine seed, the same agent seeds. The label is the
difference of the mover's mean results, d = Q(first) - Q(second): where d is clearly negative, the teacher's choice was
worse than its runner-up, and a score that learns d improves on the teacher instead of copying it.

The pilot's questions (registered in the design note before the run): how often the teacher's first is clearly worse
than its second (d < -2 SE), how strongly paired playouts agree, and whether the hand-written score's order of the two
children agrees with d where d is clear.

Decisions: one per game at most, from the P3 self-play records (pool decks only; neither the blind-test decks nor any
held-out deck), drawn by a generator seeded with the game's key; a decision with a tie at the top of the visits, or
whose children end the game, is skipped. Playouts start from the true position (both hands as they were): only the
order of both decks and future random effects are redrawn.

    python analysis/playnet/r1_labels.py --records 'runs/s1/rec-p3/*.jsonl.gz' --decisions 600 --m 8 \
        --seed 85960000 --workers 4 --out runs/r1/pilot.jsonl

Resumable: decisions already in --out are skipped. --exclude leaves out the games of another label file.

Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _child(state, action):
    from svsim.core.engine import apply
    child = state.clone()
    apply(child, action)
    return child


def _hand(state, action, me: int) -> float:
    """The hand-written score of the child for the mover, as the search scores it (learn.ranked.children)."""
    from svsim.core.actions import EndTurn
    from svsim.search.evaluate import after_end_of_turn, evaluate
    child = after_end_of_turn(state) if isinstance(action, EndTurn) else _child(state, action)
    return float(evaluate(child, me, player_moves_next=child.active == me))


def playout(child, me: int, spec: str, seed: int) -> tuple[float, float]:
    """The mover's result (1, 0.5 for a draw, 0) of one game played on from `child`, and its CPU seconds."""
    from svsim.core.engine import legal_actions, apply
    from svsim.core.view import shuffle
    from svsim.tools.arena import make_agent
    t0 = time.process_time()
    s = child.clone(copy_rng=False)
    rng = random.Random(seed)
    for p in s.players:
        shuffle(rng, p._deck)
    s.rng.seed(rng.getrandbits(64))
    agents = [make_agent(spec, seed * 2 + k) for k in (0, 1)]
    while not s.over:
        apply(s, agents[s.active].act(s, legal_actions(s)))
    r = 0.5 if s.winner not in (0, 1) else float(s.winner == me)
    return r, time.process_time() - t0


def pick(record: dict, seed: int):
    """(step, state, legal, reps, visits) of the game's one drawn decision, or None."""
    import numpy as np
    from svsim.learn.setpolicy import decisions
    found = []
    for i, state, legal, reps, _group, v, _start in decisions(record):
        found.append(i)
    if not found:
        return None
    rng = random.Random(f"r1:{seed}:{record['seed']}")
    want = rng.choice(found)
    for i, state, legal, reps, _group, v, _start in decisions(record):
        if i == want:
            order = np.argsort(-v, kind="stable")
            if v[order[0]] == v[order[1]]:
                return None
            return i, state.clone(), legal, reps, v
    return None


def label(job) -> dict | None:
    from svsim.core.actions import to_dict
    path, line, record, m, spec, seed = job
    got = pick(record, seed)
    if got is None:
        return None
    i, state, legal, reps, v = got
    order = sorted(range(len(reps)), key=lambda j: -v[j])[:2]
    me = state.active
    children = [_child(state, reps[j]) for j in order]
    if any(c.over for c in children):
        return None
    out = {"file": os.path.basename(path), "line": line, "key": record["seed"], "step": i, "turn": state.turn,
           "mover": me, "names": record.get("names"), "moves": [to_dict(reps[j]) for j in order],
           "visits": [round(float(v[j]), 4) for j in order], "n_moves": len(reps),
           "hand": [round(_hand(state, reps[j], me), 3) for j in order], "results": [[], []], "cpu": 0.0}
    for j in range(m):
        ps = seed * 1000 + j * 7919 + int(record["seed"]) % 1000003
        for c, child in enumerate(children):
            r, cpu = playout(child, me, spec, ps)
            out["results"][c].append(r)
            out["cpu"] += cpu
    out["cpu"] = round(out["cpu"], 2)
    out["condition"] = "对手卡表已知（牌序、手牌未知）"
    return out


def jobs(pattern: str, n: int, m: int, spec: str, seed: int, done: set):
    files = sorted(glob.glob(pattern))
    rng = random.Random(f"r1-files:{seed}")
    rows = []
    for path in files:
        with gzip.open(path, "rt") as fh:
            for k, _ in enumerate(fh):
                rows.append((path, k))
    rng.shuffle(rows)
    taken = 0
    by_file: dict = {}
    for path, k in rows:
        by_file.setdefault(path, set()).add(k)
        taken += 1
        if taken >= int(n * 1.5) + 10:      # some draws are skipped (ties, game-ending children: 28% in the pilot)
            break
    for path in sorted(by_file):
        with gzip.open(path, "rt") as fh:
            for k, text in enumerate(fh):
                if k in by_file[path] and (os.path.basename(path), k) not in done:
                    yield path, k, json.loads(text), m, spec, seed


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--records", required=True)
    ap.add_argument("--decisions", type=int, default=600)
    ap.add_argument("--m", type=int, default=8)
    ap.add_argument("--spec", default="mcts:100+plan")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    ap.add_argument("--exclude", action="append", default=[], help="label files whose games are left out (a "
                    "held-out set, e.g. the pilot)")
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done, kept = set(), 0
    if out.exists():
        for text in out.read_text().splitlines():
            r = json.loads(text)
            done.add((r["file"], r["line"]))
            kept += r.get("results") is not None
    for path in args.exclude:
        for text in open(path):
            r = json.loads(text)
            done.add((r["file"], r["line"]))
    todo = list(jobs(args.records, args.decisions, args.m, args.spec, args.seed, done))
    print(f"{len(done)} done, {len(todo)} to draw from, want {args.decisions}", flush=True)
    from multiprocessing import Pool
    t0 = time.time()
    with Pool(args.workers) as pool, out.open("a") as fh:
        for job, r in zip(todo, pool.imap(label, todo)):
            fh.write(json.dumps(r if r is not None else {"file": os.path.basename(job[0]), "line": job[1],
                                                         "results": None}) + "\n")
            fh.flush()
            if r is not None:
                kept += 1
                if kept % 20 == 0:
                    print(f"{kept} decisions, {time.time() - t0:.0f} s", flush=True)
            if kept >= args.decisions:
                pool.terminate()
                break


if __name__ == "__main__":
    main()
