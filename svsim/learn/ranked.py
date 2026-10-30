"""S1 (ii): the value net trained to rank a decision's children, and labels without the decks' strength (the
architecture thread 2026-10-29: after S1, a better predictor that searched worse, ranked the children of a decision
worse than the hand-written score: top-1 45.4% against 66.8%).

Children. At a searched decision of a record (learn.setpolicy.decisions: main phase, two distinct moves or more),
the teacher's best child is the distinct move with the most recorded visits (a tie at the top: the decision is not
used), and up to `others` other distinct moves are drawn (without replacement, generator seeded by (deal key, step)).
A child is the position after the move (EndTurn: search.evaluate.after_end_of_turn, the turn's end abilities done,
the opponent to act), encoded by learn.tokens.encode from the mover's view, with the mid-turn flag 1 if the mover
still acts there and 0 if not (the branch learn.setnet.SetNetEnded scores it with under +netmid). A child where the
game is over is left out (the search scores it by the result); so is a decision whose best child is, or that keeps no
other child. Only a share `rate` of the decisions is used (each kept with that probability, the same generator), to
keep the files' size near the mid-turn files'.

A stronger teacher (the architecture thread 2026-10-29 18:28Z, S1 (ii) A: the recorded mcts:100+plan is the agent the
net has to beat, so learning its ranking can at best copy it): with `teacher` (an arena spec, e.g. mcts:400+plan) the
visits are not the recorded ones but the teacher's, searching the decision afresh (agent seed: the deal key + the
step, as analysis/sharednet/s1diag.py rank), mapped to the distinct moves by search.mcts.action_key. The decisions
kept for a rate are the same with or without a teacher (the same generator draw comes first), so a smaller rate's are
among a larger one's.

The files (rank-<seed>.npz) have the mid-turn files' layout (learn.midrows), each row a child, plus "flag" (per row),
"group" (the decision, numbered within the file), "best" (the teacher's best child) and "visits" (the child's share
of the visits); "result" is the game's result from the mover's view (not used by the ranking loss). learn.midrows'
loading reads the per-row flag; `load` adds the decisions' offsets.

Advantage labels. A position's label is the game's result from its player's view, y. Part of y is owed to the decks
(analysis/sharednet/s1labels.py: the decks' strength removes 10.9% of the constant's Brier score, the net 21%).
`strength` fits a logistic model on the training games, logit P(seat 0 wins) = s[deck 0] - s[deck 1] + b*(seat 0 went
first) + c (L2 0.5 on s), and `advantage` turns y into 0.5 + (y - p) / 2, p the model's probability for the player:
in [0, 1], 0.5 for a result as the decks predict. Labels only: no deck enters any input.

    python -m svsim.learn.ranked encode --records DIR --out DIR [--rate 0.25] [--others 3] [--workers 4] \
        [--teacher mcts:400+plan]

Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import time
from pathlib import Path

import numpy as np


def teacher_visits(state, legal, reps, spec: str, seed: int) -> np.ndarray:
    """The share of `spec`'s root visits of each distinct move `reps` when it searches `state` (a copy) afresh."""
    from svsim.learn.netdata import _search
    from svsim.search.mcts import _locator, action_key
    from svsim.tools.arena import make_agent
    agent = make_agent(spec, seed)
    agent.act(state.clone(), legal)
    search = _search(agent)
    where = _locator(state, state.active)
    v = np.zeros(len(reps))
    if search is not None and search.last_root is not None:
        for j, a in enumerate(reps):
            child = search.last_root.children.get(action_key(state, a, where))
            v[j] = child.visits if child is not None else 0
    return v / v.sum() if v.sum() > 0 else v


def children(record: dict, rate: float = 0.25, others: int = 3, teacher: str | None = None):
    """[(decision step, mover, [(cards, tokens, globals, flag, best, visits, child), ...]) per decision used] of the
    record."""
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply
    from svsim.learn import tokens as T
    from svsim.learn.setpolicy import decisions
    from svsim.search.evaluate import after_end_of_turn
    key = int(record["seed"])
    out = []
    for i, state, legal, reps, _group, v, _start in decisions(record):
        rng = np.random.default_rng([key, i])
        if rng.random() >= rate:
            continue
        if teacher is not None:
            v = teacher_visits(state, legal, reps, teacher, key + i)
            if v.sum() <= 0:
                continue
        top = float(v.max())
        if int((v == top).sum()) != 1:
            continue
        best = int(np.argmax(v))
        rest = [j for j in range(len(reps)) if j != best]
        if len(rest) > others:
            rest = sorted(rng.choice(rest, size=others, replace=False).tolist())
        me = state.active
        rows = []
        for j in [best] + rest:
            a = reps[j]
            if isinstance(a, EndTurn):
                child = after_end_of_turn(state)
            else:
                child = state.clone()
                apply(child, a)
            if child.winner is not None:
                if j == best:
                    break
                continue
            flag = 1.0 if child.active == me else 0.0
            cids, toks, glob_ = T.encode(child, me)
            rows.append((cids, toks, glob_, flag, j == best, float(v[j]), child))
        if not rows or not rows[0][4] or len(rows) < 2:
            continue
        out.append((i, me, rows))
    return out


def _encode_shard(job):
    from svsim.learn import tokens as T
    path, target, rate, others = job[:4]
    teacher = job[4] if len(job) > 4 else None
    t0 = time.process_time()
    cids, toks, offs, globs = [], [], [0], []
    lab = {k: [] for k in ("result", "seed", "g", "i", "turn", "player", "flag", "group", "best", "visits")}
    cards = {}
    games = decs = 0
    with gzip.open(path, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            games += 1
            winner = record.get("winner")
            for i, me, rows in children(record, rate, others, teacher):
                for c, t, g, flag, best, visits, child in rows:
                    for p in child.players:
                        for card in p.hand + p.field + p.leader_area + p.deck_view():
                            cards[card.defn.card_id] = card.defn
                    cids.append(c)
                    toks.append(t)
                    offs.append(offs[-1] + len(t))
                    globs.append(g)
                    lab["result"].append(0.5 if winner is None else float(winner == me))
                    lab["seed"].append(int(record["seed"]) // 100003)
                    lab["g"].append(record["g"])
                    lab["i"].append(i)
                    lab["turn"].append(child.turn)
                    lab["player"].append(me)
                    lab["flag"].append(flag)
                    lab["group"].append(decs)
                    lab["best"].append(best)
                    lab["visits"].append(visits)
                decs += 1
    arrays = {"tokens": np.concatenate(toks) if toks else np.zeros((0, len(T.token_names("v1"))), np.int16),
              "cards": np.concatenate(cids) if cids else np.zeros(0, np.int32),
              "offsets": np.asarray(offs, np.int64),
              "globals": np.stack(globs).astype(np.float32) if globs else np.zeros((0, len(T.global_names("v1"))),
                                                                                    np.float32),
              "result": np.asarray(lab["result"], np.float32), "linear": np.zeros(len(globs), np.float32),
              "flag": np.asarray(lab["flag"], np.float32), "best": np.asarray(lab["best"], bool),
              "visits": np.asarray(lab["visits"], np.float32)}
    for k in ("seed", "g", "i", "turn", "player", "group"):
        arrays[k] = np.asarray(lab[k], np.int32)
    ids = sorted(cards)
    arrays["card_id"] = np.asarray(ids, np.int32)
    arrays["static"] = np.stack([T.static(cards[c]) for c in ids]) if ids else np.zeros((0, len(T.static_names())))
    tmp = str(target) + ".tmp.npz"
    np.savez_compressed(tmp, **arrays)
    os.replace(tmp, target)
    return str(target), games, decs, len(globs), round(time.process_time() - t0, 1)


def encode_main(args) -> None:
    from multiprocessing import Pool
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = []
    for path in sorted(glob.glob(os.path.join(args.records, "rec-*.jsonl.gz"))):
        seed = os.path.basename(path)[len("rec-"):-len(".jsonl.gz")]
        target = out / f"rank-{seed}.npz"
        if not target.exists():
            jobs.append((path, target, args.rate, args.others, args.teacher))
    print(json.dumps({"shards_to_encode": len(jobs), "rate": args.rate, "others": args.others,
                      "teacher": args.teacher}), flush=True)
    with Pool(args.workers) as pool:
        for target, games, decs, n, cpu in pool.imap_unordered(_encode_shard, jobs):
            print(json.dumps({"file": os.path.basename(target), "games": games, "decisions": decs, "children": n,
                              "cpu_s": cpu}), flush=True)


def load(files, cards_npz, every: int = 20, split: str = "key"):
    """(training, validation) learn.setnet.Data of the files' children (learn.midrows' loading, the per-row flag
    appended), each with n_dec, dec_offsets (decision j's children are rows dec_offsets[j]:dec_offsets[j + 1]) and
    best. Split by game as learn.midrows.phase_split (`split`: learn.setnet.in_valid's)."""
    from svsim.learn import midrows as MR
    from svsim.learn.setnet import in_valid
    plan = []
    for f in files:
        with np.load(f) as z:
            games = z["seed"].astype(np.int64) * 100003 + z["g"].astype(np.int64)
            plan.append((f, 0.0, np.ones(len(games), bool), in_valid(games, every, split)))
    parts = []
    for part in ("train", "valid"):
        d = MR._assemble(plan, cards_npz, part)
        groups, best = [], []
        base = 0
        for f, _flag, keep, valid in plan:
            sel = keep & ~valid if part == "train" else keep & valid
            with np.load(f) as z:
                groups.append(z["group"][sel].astype(np.int64) + base)
                best.append(z["best"][sel])
                base += int(z["group"].max()) + 1 if len(z["group"]) else 0
        group = np.concatenate(groups) if groups else np.zeros(0, np.int64)
        d.best = np.concatenate(best) if best else np.zeros(0, bool)
        starts = np.flatnonzero(np.r_[True, group[1:] != group[:-1]]) if len(group) else np.zeros(0, np.int64)
        d.dec_offsets = np.r_[starts, len(group)].astype(np.int64)
        d.n_dec = len(starts)
        if len(group) and not np.array_equal(np.add.reduceat(d.best.astype(np.int64), starts), np.ones(d.n_dec)):
            raise ValueError("a decision without exactly one best child")
        parts.append(d)
    return tuple(parts)


# --- advantage labels -------------------------------------------------------------------------------------------

def games_of(folder: str) -> dict:
    """{deal key: (deck of seat 0, deck of seat 1, seat that went first, winner)} of the records in folder."""
    out = {}
    for path in sorted(glob.glob(str(Path(folder) / "rec-*.jsonl.gz"))):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    out[int(r["seed"])] = (r["names"][0], r["names"][1], int(r["first"]), r.get("winner"))
    return out


def strength(games: dict, keys, l2: float = 0.5, iters: int = 300, lr: float = 0.5) -> dict:
    """The decks' strength model on the games `keys` (analysis/sharednet/s1labels.py's): {"s": {deck: s}, "b", "c"},
    logit P(seat 0 wins) = s[deck 0] - s[deck 1] + b * (seat 0 went first) + c, by gradient descent; a draw is 0.5."""
    rows = [games[k] for k in keys]
    decks = {d: i for i, d in enumerate(sorted({r[0] for r in rows} | {r[1] for r in rows}))}
    a = np.array([decks[r[0]] for r in rows])
    o = np.array([decks[r[1]] for r in rows])
    f = np.array([float(r[2] == 0) for r in rows])
    y = np.array([1.0 if r[3] == 0 else 0.0 if r[3] == 1 else 0.5 for r in rows])
    s = np.zeros(len(decks))
    b = c = 0.0
    n = len(rows)
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(s[a] - s[o] + b * f + c)))
        g = p - y
        gs = np.bincount(a, g, len(decks)) - np.bincount(o, g, len(decks))
        s -= lr * (gs / n * len(decks) / 2 + l2 * s / n * len(decks) / 2)
        b -= lr * float(np.mean(g * f))
        c -= lr * float(np.mean(g))
    return {"s": {d: float(s[i]) for d, i in decks.items()}, "b": float(b), "c": float(c)}


def predicted(model: dict, games: dict, keys, player) -> np.ndarray:
    """The model's probability that `player` wins game `keys` (per row; a deck it has no strength for counts 0)."""
    out = np.zeros(len(keys))
    for n, (k, pl) in enumerate(zip(keys, player)):
        d0, d1, first, _ = games[int(k)]
        z = model["s"].get(d0, 0.0) - model["s"].get(d1, 0.0) + model["b"] * float(first == 0) + model["c"]
        p0 = 1 / (1 + np.exp(-z))
        out[n] = p0 if int(pl) == 0 else 1 - p0
    return out


def advantage(result, p) -> np.ndarray:
    """0.5 + (y - p) / 2: the result against what the decks predict, in [0, 1]."""
    return (0.5 + (np.asarray(result, np.float64) - np.asarray(p, np.float64)) / 2).astype(np.float32)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("encode")
    e.add_argument("--records", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--rate", type=float, default=0.25, help="the share of decisions used")
    e.add_argument("--others", type=int, default=3, help="other children drawn beside the teacher's best")
    e.add_argument("--workers", type=int, default=4)
    e.add_argument("--teacher", default=None, help="an arena spec searching each kept decision afresh for the visits "
                                                    "(default: the recorded search's)")
    args = ap.parse_args()
    {"encode": encode_main}[args.cmd](args)


if __name__ == "__main__":
    main()
