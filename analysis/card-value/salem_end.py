"""The discrimination experiment: on Salem's own turns, does the real game result agree with what Salem kept?

    cd <svsim checkout> && PYTHONPATH=.:<this folder> python3 <this> POSITIONS_JSON TEACHER_ROWS_JSON \
        [--k 16] [--workers 4] --out salem_end_rows.jsonl
    python3 <this> --report salem_end_rows.jsonl TEACHER_ROWS_JSON [--boot 2000]

The teacher falls short of the one-turn control on Salem's keep choices (62-66% against 70%), yet it
tracks real game results in self-play (true-score correlation 0.58). To tell the two readings apart
(the architecture thread, docs/hand-value-design.md section 6): for each "keep" item of
teacher_eval.py (one of Salem's turn starts and one card c of the teacher's principal line; Salem kept
it or played it), the value of keeping c is measured by playing to the end: on 2 x k determinizations
from Salem's seat (common random numbers: the same determinization, deck order and agent seeds for
both arms), v2 plays the rest of the turn never playing c in one arm and freely in the other, then v2
against v2 to the end; G_end = mean of (keep arm's result - free arm's result). Then the keep AUC
(does a higher value go with Salem keeping it) of G_end, of the teacher T and of the control Q on the
same items, with 95% intervals from resampling Salem's turns; Salem's winning turns are left out, as
in report.py.
- G_end disagrees with Salem too: the bot's world (how it plays on, how it answers) differs from
  Salem's: a distribution problem.
- G_end agrees with Salem and the teacher does not: the teacher's approximation is too short.
- Both agree within overlapping intervals: the ruler (80 turns) is too small.
"""
import argparse
import json
import random
from collections import defaultdict
from multiprocessing import Pool

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import from_dict
from svsim.core.engine import apply
from svsim.tools import records

import realized as R
from realized_end import play_out

RECORDS = {}


def state_at(rec, at):
    st = records.start(rec)
    for a in rec["actions"][:at]:
        apply(st, from_dict(a))
    return st


def salem_won_turn(rec, at):
    st = state_at(rec, at)
    me = st.active
    for a in rec["actions"][at:]:
        if st.over or st.active != me:
            break
        apply(st, from_dict(a))
    return st.over and st.winner == me


def measure(job):
    from svsim.core.view import determinize
    game, at, cid, k, seed = job
    st = state_at(RECORDS[game], at)
    me = st.active
    outs = []
    for j in range(2 * k):
        base = determinize(st, me, random.Random(seed * 1000 + j))
        sd = seed * 1000 + 10 * j
        outs.append(play_out(base, me, R.keeps_card(cid), sd) - play_out(base, me, None, sd))
    return {"game": game, "at": at, "card": cid, "seed": seed, "G_end": sum(outs) / len(outs),
            "G_end1": sum(outs[:k]) / k, "G_end2": sum(outs[k:]) / k, "G_end_samples": outs}


def keep_items(teacher_rows):
    """(game, at, card) -> Salem's label and the teacher's and control's values (mean over the teacher's seeds)."""
    items = defaultdict(lambda: {"T": [], "Q": []})
    for r in teacher_rows:
        if not r["restriction"].startswith("keep:"):
            continue
        key = (r["game"], r["at"], int(r["restriction"].split(":")[1]))
        items[key]["salem"] = r["salem"]
        items[key]["T"].append(r["teacher"])
        items[key]["Q"].append(r["control"])
    return {k: {"salem": v["salem"], "T": sum(v["T"]) / len(v["T"]), "Q": sum(v["Q"]) / len(v["Q"])}
            for k, v in items.items()}


def auc(scores, labels):
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    if not pos or not neg:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def report(rows_path, teacher_path, boots):
    items = keep_items(json.load(open(teacher_path, encoding="utf-8")))
    rows = [json.loads(line) for line in open(rows_path, encoding="utf-8") if line.strip()]
    data = []
    for r in rows:
        it = items[(r["game"], r["at"], r["card"])]
        data.append({"turn": (r["game"], r["at"]), "y": it["salem"] == "kept", "G_end": r["G_end"],
                     "G_end1": r["G_end1"], "G_end2": r["G_end2"], "T": it["T"], "Q": it["Q"]})
    turns = sorted({d["turn"] for d in data})
    by_turn = defaultdict(list)
    for d in data:
        by_turn[d["turn"]].append(d)
    keys = ("G_end", "T", "Q", "G_end1", "G_end2")
    point = {k: auc([d[k] for d in data], [d["y"] for d in data]) for k in keys}
    rng = random.Random(13)
    samples = {k: [] for k in keys}
    diffs = {"G_end − Q": [], "G_end − T": [], "T − Q": []}
    for _ in range(boots):
        pick = [d for t in (turns[rng.randrange(len(turns))] for _ in turns) for d in by_turn[t]]
        a = {k: auc([d[k] for d in pick], [d["y"] for d in pick]) for k in keys}
        for k in keys:
            samples[k].append(a[k])
        diffs["G_end − Q"].append(a["G_end"] - a["Q"])
        diffs["G_end − T"].append(a["G_end"] - a["T"])
        diffs["T − Q"].append(a["T"] - a["Q"])
    ci = lambda xs: (sorted(xs)[int(0.025 * len(xs))], sorted(xs)[int(0.975 * len(xs)) - 1])
    print(f"{len(data)} 项（Salem 留 {sum(d['y'] for d in data)}、打出 {sum(not d['y'] for d in data)}），{len(turns)} 个回合")
    names = {"G_end": "打到终局 G_end", "T": "老师 T", "Q": "单回合 Q", "G_end1": "G_end 第一组", "G_end2": "G_end 第二组"}
    for k in keys:
        lo, hi = ci(samples[k])
        print(f"  {names[k]:<12} 留牌 AUC {point[k]:.3f}（{lo:.3f}～{hi:.3f}）")
    for k, xs in diffs.items():
        a, b = k.split(" − ")
        lo, hi = ci(xs)
        print(f"  差 {k:<10} {point[a] - point[b]:+.3f}（{lo:+.3f}～{hi:+.3f}）")


def main():
    if "--report" in __import__("sys").argv:
        ap = argparse.ArgumentParser()
        ap.add_argument("--report", required=True)
        ap.add_argument("teacher")
        ap.add_argument("--boot", type=int, default=2000)
        a = ap.parse_args()
        report(a.report, a.teacher, a.boot)
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("positions")
    ap.add_argument("teacher")
    ap.add_argument("--k", type=int, default=16)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    RECORDS.update(json.load(open(args.positions, encoding="utf-8"))["records"])
    items = keep_items(json.load(open(args.teacher, encoding="utf-8")))
    jobs = [(g, at, cid, args.k, 900000 + n) for n, (g, at, cid) in enumerate(sorted(items))
            if not salem_won_turn(RECORDS[g], at)]
    import os
    done = set()
    if os.path.exists(args.out):
        done = {json.loads(line)["seed"] for line in open(args.out, encoding="utf-8") if line.strip()}
    jobs = [j for j in jobs if j[4] not in done]
    print(f"{len(items)} 个留牌项，要量 {len(jobs)} 个（已完成 {len(done)}）", flush=True)
    with Pool(args.workers) as pool, open(args.out, "a", encoding="utf-8") as fh:
        for n, row in enumerate(pool.imap_unordered(measure, jobs, chunksize=1), 1):
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            if n % 10 == 0:
                print(f"  {n} / {len(jobs)}", flush=True)


if __name__ == "__main__":
    main()
