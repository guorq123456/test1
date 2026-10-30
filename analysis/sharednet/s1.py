"""S1, the first shared value net (the architecture thread 2026-10-29 03:33Z): its hold-out and its hold-out readings.

    python analysis/sharednet/s1.py holdout --pool analysis/sharednet/fields/C-r0-pool.txt --base 85830000 \
        --shards 20 --per-shard 1000 --out analysis/sharednet/s1/holdout
    python analysis/sharednet/s1.py eval --records runs/s1/rec --holdout analysis/sharednet/s1/holdout-games.json \
        --net analysis/scaling/models/net-s1.npz --fit-games 600 --out analysis/sharednet/s1/eval.json

`holdout`: one deck per class of the pool is held out (the class's label with the smallest sha256); every game whose
pool draw (learn.scaledata.pool_pair, a function of (seed, g) alone) has a held-out deck on either side is a
validation game. Writes <out>-decks.json (the labels) and <out>-games.json (the games' keys, seed·100003 + g, for
train_mid.py --split games:FILE). No game of a held-out deck is in training.

`eval`: on the validation games' rows, both kinds (turn ends: learn.netdata.rows phase ENDED, the player who ended
the turn; mid-turn: learn.setpolicy.decisions, the mover), the log loss and Brier score of
- the shared net (its turn-end branch at turn ends, its mid-turn branch inside the mover's turn), and
- the hand-written score (search.evaluate.evaluate with the default weights, what mcts:100+plan searches with;
  player_moves_next as the search asks: False at a turn end, True for the mover), which is no probability: it is
  calibrated by a one-variable logistic regression (a·x + b) fitted on the rows of --fit-games training games (the
  first ones by key, the same kind of row), then read on the validation rows.

Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def held_out_decks(pool: list) -> list:
    """One label per class: the smallest sha256 among the class's labels."""
    from svsim.cards.pool import POOL
    from svsim.cards import decks
    by_class: dict = {}
    for label, ids in pool:
        craft = decks.craft_of([POOL[i] for i in ids])
        by_class.setdefault(int(craft), []).append(label)
    return sorted(min(labels, key=lambda s: hashlib.sha256(s.encode()).hexdigest()) for labels in by_class.values())


def holdout_main(args) -> None:
    from svsim.learn.scaledata import pool_of, pool_pair
    pool = pool_of(args.pool)
    held = set(held_out_decks(pool))
    keys = []
    for k in range(args.shards):
        seed = args.base + args.stride * k
        for g in range(args.per_shard):
            a, b = pool_pair(pool, seed, g)
            if a[0] in held or b[0] in held:
                keys.append(seed * 100003 + g)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out + "-decks.json").write_text(json.dumps(sorted(held), indent=1) + "\n", encoding="utf-8")
    Path(args.out + "-games.json").write_text(json.dumps(keys) + "\n", encoding="utf-8")
    total = args.shards * args.per_shard
    print(json.dumps({"held_out": sorted(held), "validation_games": len(keys), "of": total,
                      "share": round(len(keys) / total, 4)}))


def _rows(record):
    """(kind, state, player, result, player_moves_next) for every row of the game."""
    from svsim.learn.netdata import ENDED, rows
    from svsim.learn.setpolicy import decisions
    for phase, player, state, result in rows(record):
        if phase == ENDED:
            yield "end", state, player, result, False
    winner = record.get("winner")
    for _i, state, *_rest, _start in decisions(record):
        me = state.active
        yield "mid", state.clone(), me, 0.5 if winner is None else float(winner == me), True


def _records(folder: str):
    for path in sorted(glob.glob(str(Path(folder) / "rec-*.jsonl.gz"))):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    yield json.loads(line)


def _logistic(x: np.ndarray, y: np.ndarray) -> tuple:
    """(a, b) of P = sigmoid(a·x + b) by Newton's method (y may be 0.5 for a draw)."""
    s = float(np.std(x)) or 1.0
    z = x / s
    a = b = 0.0
    for _ in range(50):
        p = 1 / (1 + np.exp(-(a * z + b)))
        g = np.array([np.sum((p - y) * z), np.sum(p - y)])
        w = p * (1 - p)
        h = np.array([[np.sum(w * z * z), np.sum(w * z)], [np.sum(w * z), np.sum(w)]]) + 1e-9 * np.eye(2)
        step = np.linalg.solve(h, g)
        a, b = a - step[0], b - step[1]
        if np.abs(step).max() < 1e-10:
            break
    return a / s, b


def _scores(p: np.ndarray, y: np.ndarray) -> dict:
    p = np.clip(p, 1e-7, 1 - 1e-7)
    return {"log_loss": round(float(np.mean(-(y * np.log(p) + (1 - y) * np.log(1 - p)))), 5),
            "brier": round(float(np.mean((p - y) ** 2)), 5), "n": int(len(y))}


def eval_main(args) -> None:
    from svsim.learn.setnet import SetNet
    from svsim.search.evaluate import evaluate
    held = set(json.loads(Path(args.holdout).read_text(encoding="utf-8")))
    net = SetNet.load(args.net)
    fit = {"end": ([], []), "mid": ([], [])}
    val = {"end": ([], [], []), "mid": ([], [], [])}         # hand-written x, net p, y
    fitted = 0
    for record in _records(args.records):
        key = record["seed"]                                  # the deal seed: seed·100003 + g
        valid = key in held
        if not valid:
            if fitted >= args.fit_games:
                continue
            fitted += 1
        for kind, state, player, result, moves_next in _rows(record):
            x = evaluate(state, player, player_moves_next=moves_next)
            if valid:
                logit = net.logit(state, player, mid=kind == "mid")
                val[kind][0].append(x)
                val[kind][1].append(1 / (1 + math.exp(-logit)))
                val[kind][2].append(result)
            else:
                fit[kind][0].append(x)
                fit[kind][1].append(result)
    out = {"net": args.net, "net_sha256": hashlib.sha256(Path(args.net).read_bytes()).hexdigest(),
           "holdout": args.holdout, "fit_games": fitted, "condition": "对手卡表已知（牌序、手牌未知）"}
    for kind in ("end", "mid"):
        a, b = _logistic(np.asarray(fit[kind][0], float), np.asarray(fit[kind][1], float))
        x, p, y = (np.asarray(v, float) for v in val[kind])
        out[kind] = {"net": _scores(p, y), "hand_written": _scores(1 / (1 + np.exp(-(a * x + b))), y),
                     "hand_written_fit": {"a": a, "b": b, "rows": len(fit[kind][0])},
                     "base_rate": _scores(np.full(len(y), float(np.mean(fit[kind][1]))), y)}
    text = json.dumps(out, indent=1, ensure_ascii=False)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("holdout")
    h.add_argument("--pool", required=True)
    h.add_argument("--base", type=int, required=True)
    h.add_argument("--stride", type=int, default=2)
    h.add_argument("--shards", type=int, required=True)
    h.add_argument("--per-shard", type=int, default=1000)
    h.add_argument("--out", required=True)
    e = sub.add_parser("eval")
    e.add_argument("--records", required=True)
    e.add_argument("--holdout", required=True, help="the validation games' keys (holdout's -games.json)")
    e.add_argument("--net", required=True)
    e.add_argument("--fit-games", type=int, default=600, help="training games whose rows calibrate the hand-written score")
    e.add_argument("--out", default=None)
    args = ap.parse_args()
    {"holdout": holdout_main, "eval": eval_main}[args.cmd](args)


if __name__ == "__main__":
    main()
