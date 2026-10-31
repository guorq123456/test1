"""The bot check-up, step B: diagnostics on R1's 753 pilot decisions, now a development set (not a final test).

B1, continuation sensitivity. R1's label d = Q(first) - Q(second) played both children on with mcts:100+plan on
both sides. Here the same children are played on with another continuation, --spec (mcts-reply:100+plan: the
opponent's next turn played out at the leaves), j = 0 .. m-1 with R1's own common random numbers (the seed
85960000, R1's playout seeds), so playout j is the same deal under both policies.

B2, candidate coverage. On the subset fixed before the run (the pilot's drawn games whose key % 3 == 0, the
key being the game's record seed), the teacher's 3rd and 4th most-visited distinct moves are played on m = 12
times with R1's seeds and policy (mcts:100+plan), to set beside the stored first and second. The same subset's
games whose drawn decision was skipped by R1 for a tie at the top of the visits are added: there the 1st to 4th
are all played.

    python analysis/checkup/b_dev.py b2 --out runs/checkup/b2.jsonl --workers 4
    python analysis/checkup/b_dev.py b1 --m 4 --out runs/checkup/b1.jsonl --workers 4
    python analysis/checkup/b_dev.py report --b1 runs/checkup/b1.jsonl --b2 runs/checkup/b2.jsonl

Resumable: decisions already in --out are skipped. Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import math
import os
import random
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
VERSION = "checkup-b-1"
PILOT_SEED = 85960000
CONDITION = "对手卡表已知（牌序、手牌未知）"


def _labels():
    spec = importlib.util.spec_from_file_location("r1_labels", ROOT / "analysis/playnet/r1_labels.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = _labels()
RECORDS = ROOT / "runs/s1/rec-p3"


def _record(name: str, line: int) -> dict:
    with gzip.open(RECORDS / name, "rt") as fh:
        for k, text in enumerate(fh):
            if k == line:
                return json.loads(text)
    raise ValueError((name, line))


def _pilot() -> list:
    with gzip.open(ROOT / "analysis/playnet/pilot.jsonl.gz", "rt") as fh:
        return [json.loads(t) for t in fh]


def _ps(j: int, key: int) -> int:
    return PILOT_SEED * 1000 + j * 7919 + int(key) % 1000003           # r1_labels.label's playout seed


def _play(children, me, spec, key, m, j0=0):
    out = [[] for _ in children]
    cpu = 0.0
    for j in range(j0, j0 + m):
        for c, child in enumerate(children):
            if child.over:
                out[c].append(0.5 if child.winner not in (0, 1) else float(child.winner == me))
                continue
            r, t = L.playout(child, me, spec, _ps(j, key))
            out[c].append(r)
            cpu += t
    return out, cpu


def job_b1(job) -> dict:
    row, spec, m = job
    from svsim.core.actions import from_dict
    record = _record(row["file"], row["line"])
    got = L.pick(record, PILOT_SEED)
    i, state, legal, reps, v = got
    assert i == row["step"]
    me = state.active
    children = [L._child(state, from_dict(mv)) for mv in row["moves"]]
    res, cpu = _play(children, me, spec, row["key"], m)
    return {"version": VERSION, "kind": "b1", "file": row["file"], "line": row["line"], "key": row["key"],
            "spec": spec, "results": res, "cpu": round(cpu, 2)}


def job_b2(job) -> dict:
    row, spec, m = job
    from svsim.core.actions import to_dict
    record = _record(row["file"], row["line"])
    key = record["seed"]
    # pick() returns None on a tie at the top; redo its draw to find the tie decision
    from svsim.learn.setpolicy import decisions
    found = [i for i, *_ in decisions(record)]
    if not found:
        return {"version": VERSION, "kind": "b2", "file": row["file"], "line": row["line"], "skip": "no decision"}
    want = random.Random(f"r1:{PILOT_SEED}:{record['seed']}").choice(found)
    for i, state, legal, reps, _g, v, _s in decisions(record):
        if i == want:
            state = state.clone()
            break
    me = state.active
    order = sorted(range(len(reps)), key=lambda j: -v[j])
    tie = bool(v[order[0]] == v[order[1]])
    labelled = row.get("results") is not None
    if labelled:
        assert [to_dict(reps[j]) for j in order[:2]] == row["moves"], "the stored first and second"
        play = order[2:4]
    elif tie:
        play = order[:4]
    else:
        return {"version": VERSION, "kind": "b2", "file": row["file"], "line": row["line"], "key": key,
                "skip": "not labelled, no tie (a top-2 child ends the game)"}
    children = [L._child(state, reps[j]) for j in play]
    res, cpu = _play(children, me, spec, key, m)
    return {"version": VERSION, "kind": "b2", "file": row["file"], "line": row["line"], "key": key, "tie": tie,
            "labelled": labelled, "n_moves": len(reps), "ranks": [order.index(j) + 1 for j in play],
            "visits": [round(float(v[j]), 4) for j in order[:4]], "moves": [to_dict(reps[j]) for j in play],
            "spec": spec, "results": res, "cpu": round(cpu, 2), "turn": state.turn}


def _done(out: Path) -> set:
    done = set()
    if out.exists():
        for t in out.read_text().splitlines():
            try:
                r = json.loads(t)
            except json.JSONDecodeError:
                continue
            done.add((r["file"], r["line"]))
    return done


def run(kind: str, args) -> None:
    pilot = _pilot()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = _done(out)
    if kind == "b1":
        rows = [r for r in pilot if r.get("results") is not None]
        fn = job_b1
    else:
        rows = []
        for r in pilot:
            key = r.get("key")
            if key is None:                                   # a skipped draw: its key is the record's seed
                rows.append(r)
            elif int(key) % 3 == 0:
                rows.append(r)
        fn = job_b2
    if kind == "b2":                                          # skipped draws: keep those whose key % 3 == 0
        keep = []
        for r in rows:
            if r.get("key") is None:
                key = _record(r["file"], r["line"])["seed"]
                if int(key) % 3 != 0:
                    continue
            keep.append(r)
        rows = keep
    todo = [(r, args.spec, args.m) for r in rows if (r["file"], r["line"]) not in done]
    print(f"{VERSION} {kind}: {len(rows)} decisions, {len(todo)} to play, spec {args.spec}, m {args.m}", flush=True)
    t0, n = time.time(), 0
    with Pool(args.workers) as pool, out.open("a") as fh:
        for r in pool.imap_unordered(fn, todo):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            n += 1
            if n % 20 == 0:
                print(f"{n}/{len(todo)} {time.time() - t0:.0f} s", flush=True)


# --- report ----------------------------------------------------------------------------------------------------

def _load(path):
    return [json.loads(t) for t in open(path) if t.strip()] if path and Path(path).exists() else []


def report_b1(rows_b1, pilot) -> dict:
    by = {(r["file"], r["line"]): r for r in pilot if r.get("results") is not None}
    d0, d0m, d1, se0, rel_halves1, rel_halves0 = [], [], [], [], [], []
    for r in rows_b1:
        p = by[(r["file"], r["line"])]
        m = len(r["results"][0])
        A0, B0 = np.array(p["results"][0], float), np.array(p["results"][1], float)
        A1, B1 = np.array(r["results"][0], float), np.array(r["results"][1], float)
        D0, D1 = A0 - B0, A1 - B1
        d0.append(D0.mean())
        d0m.append(D0[:m].mean())                            # the same playouts j < m under the old policy
        d1.append(D1.mean())
        rel_halves1.append((D1[0::2].mean(), D1[1::2].mean()))
        rel_halves0.append((D0[0::2].mean(), D0[1::2].mean()))
    d0, d0m, d1 = map(np.array, (d0, d0m, d1))

    def reliability(halves):
        h = np.array(halves)
        r = np.corrcoef(h[:, 0], h[:, 1])[0, 1]
        return 2 * r / (1 + r)                                # Spearman-Brown, whole from halves

    rel0, rel1 = reliability(rel_halves0), reliability(rel_halves1)
    raw = float(np.corrcoef(d0, d1)[0, 1])
    rng = np.random.default_rng(85971998)
    boot = []
    for _ in range(1000):
        k = rng.integers(0, len(d0), len(d0))
        boot.append(np.corrcoef(d0[k], d1[k])[0, 1] / math.sqrt(max(1e-9, reliability(np.array(rel_halves0)[k]) *
                                                                     reliability(np.array(rel_halves1)[k]))))
    return {"decisions": len(d0), "mean_d_old": float(d0.mean()), "mean_d_new": float(d1.mean()),
            "mean_d_new_minus_old_same_playouts": float((d1 - d0m).mean()),
            "se": float((d1 - d0m).std(ddof=1) / math.sqrt(len(d0))),
            "corr_raw": raw, "reliability_old": float(rel0), "reliability_new": float(rel1),
            "corr_disattenuated": float(raw / math.sqrt(rel0 * rel1)),
            "corr_disattenuated_95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
            "teacher_first_worse_old": float((d0 < 0).mean()), "teacher_first_worse_new": float((d1 < 0).mean())}


def report_b2(rows_b2, pilot) -> dict:
    by = {(r["file"], r["line"]): r for r in pilot if r.get("results") is not None}
    lab = [r for r in rows_b2 if r.get("labelled")]
    ties = [r for r in rows_b2 if r.get("tie") and not r.get("labelled")]
    gains_cov, gains_top2, clear_better, n3 = [], [], 0, 0
    for r in lab:
        p = by[(r["file"], r["line"])]
        Q = [np.array(p["results"][0], float), np.array(p["results"][1], float)] + \
            [np.array(x, float) for x in r["results"]]
        if len(Q) > 2:
            n3 += 1
        for k in range(2, len(Q)):
            D = Q[k] - Q[0]
            if D.mean() > 2 * D.std(ddof=1) / math.sqrt(len(D)) and D.std() > 0 or (D.std() == 0 and D.mean() > 0):
                clear_better += 1
                break
        # split-half: choose by one half of the playouts, value on the other (both ways)
        for a, b in ((slice(0, None, 2), slice(1, None, 2)), (slice(1, None, 2), slice(0, None, 2))):
            means_a = [q[a].mean() for q in Q]
            best2 = int(np.argmax(means_a[:2]))
            best4 = int(np.argmax(means_a))
            gains_cov.append(Q[best4][b].mean() - Q[best2][b].mean())
            gains_top2.append(Q[best2][b].mean() - Q[0][b].mean())
    gc = np.array(gains_cov).reshape(-1, 2).mean(axis=1) if gains_cov else np.zeros(0)
    gt = np.array(gains_top2).reshape(-1, 2).mean(axis=1) if gains_top2 else np.zeros(0)
    tie_d = []
    for r in ties:
        Q = [np.array(x, float) for x in r["results"]]
        tie_d.append(float((Q[0] - Q[1]).mean()))
    out = {"labelled": len(lab), "with_3rd": n3, "third_or_fourth_clearly_beats_first": clear_better,
           "coverage_gain": float(gc.mean()) if len(gc) else None,
           "coverage_gain_se": float(gc.std(ddof=1) / math.sqrt(len(gc))) if len(gc) > 1 else None,
           "top2_oracle_gain": float(gt.mean()) if len(gt) else None,
           "top2_oracle_gain_se": float(gt.std(ddof=1) / math.sqrt(len(gt))) if len(gt) > 1 else None,
           "ties": len(ties), "tie_mean_abs_d12": float(np.mean(np.abs(tie_d))) if tie_d else None}
    return out


def report(args) -> None:
    pilot = _pilot()
    res = {"version": VERSION, "condition": CONDITION}
    b1 = [r for r in _load(args.b1) if r.get("version") == VERSION]
    b2 = [r for r in _load(args.b2) if r.get("version") == VERSION and "results" in r]
    if b1:
        res["b1"] = report_b1(b1, pilot)
    if b2:
        res["b2"] = report_b2(b2, pilot)
    text = json.dumps(res, indent=1, ensure_ascii=False)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, spec, m in (("b1", "mcts-reply:100+plan", 4), ("b2", "mcts:100+plan", 12)):
        p = sub.add_parser(name)
        p.add_argument("--spec", default=spec)
        p.add_argument("--m", type=int, default=m)
        p.add_argument("--workers", type=int, default=4)
        p.add_argument("--out", required=True)
    p = sub.add_parser("report")
    p.add_argument("--b1")
    p.add_argument("--b2")
    p.add_argument("--out")
    args = ap.parse_args()
    if args.cmd == "report":
        report(args)
    else:
        run(args.cmd, args)


if __name__ == "__main__":
    main()
