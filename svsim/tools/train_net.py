"""Train a matchup's value network (learn.net) on self-play records (learn.netdata).

    python -m svsim.tools.train_net --games games.jsonl --out svsim/learn/nets/dragon-dragon.npz

Every position the search may score is a row (each decision point for the
player to act, each turn's end for the player who ended it), labelled with
the game's result. A tenth of the games (by number) is held out: the fit
keeps the epoch with the lowest held-out loss, and the report gives the
held-out AUC at each moment (ACT / ENDED) by turn, next to the installed
linear model's on the same positions (it was fitted on turn ends only).
"""
from __future__ import annotations

import argparse
import json
import time
from multiprocessing import Pool

import numpy as np


def _rows(line: str) -> list:
    from svsim.learn import encode as E
    from svsim.learn.netdata import rows
    record = json.loads(line)
    out = []
    for phase, me, state, result in rows(record):
        dense, zones = E.raw(state, me)
        out.append((record["g"], phase, state.players[me].turns_taken, dense, zones, result))
    return out


def auc(scores, labels) -> float:
    scores, labels = np.asarray(scores), np.asarray(labels)
    keep = labels != 0.5
    scores, labels = scores[keep], labels[keep] > 0.5
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores))
    ranks[order] = np.arange(1, len(scores) + 1)
    pos, neg = labels.sum(), (~labels).sum()
    return float((ranks[labels].sum() - pos * (pos + 1) / 2) / max(pos * neg, 1))


def main() -> None:
    from pathlib import Path
    from svsim.learn import encode as E
    from svsim.learn.model import WEIGHTS, LinearValue
    from svsim.learn.net import ValueNet
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--hidden", type=int, nargs=2, default=(128, 64))
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--l2", type=float, default=1e-4)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--linear", default=str(WEIGHTS / "dragon-dragon.json"),
                        help="the linear model to compare with (and to start from, the prior)")
    parser.add_argument("--no-prior", action="store_true", help="don't start from the linear model")
    args = parser.parse_args()
    t0 = time.time()
    lines = [line for path in args.games for line in open(path, encoding="utf-8")]
    with Pool(args.workers) as pool:
        data = [r for part in pool.imap(_rows, lines, chunksize=4) for r in part]
    print(f"{len(lines)} games, {len(data)} positions ({time.time() - t0:.0f}s)", flush=True)
    vocab = sorted({cid for row in data for zone in row[4] for cid in zone})
    index = {c: i for i, c in enumerate(vocab)}
    X = np.zeros((len(data), E.width(index)), dtype=np.float32)
    for i, row in enumerate(data):
        E.vectorize((row[3], row[4]), index, out=X[i])
    y = np.array([row[5] for row in data])
    games = np.array([row[0] for row in data])
    phase = np.array([row[1] for row in data])
    turn = np.array([row[2] for row in data])
    val = games % 10 == 0
    lin = LinearValue.load(Path(args.linear))
    net = ValueNet.train(X[~val], y[~val], vocab, X[val], y[val], hidden=tuple(args.hidden), epochs=args.epochs,
                         l2=args.l2, lr=args.lr, prior=None if args.no_prior else lin,
                         info={"games": len(lines), "positions": int(len(X)), "files": args.games})
    net.save(Path(args.out))
    print(f"saved {args.out} ({time.time() - t0:.0f}s)")
    z = net.forward(X[val].astype(np.float64))
    n = len(lin.coef)
    zl = ((X[val][:, :n] - np.array(lin.mean)) / np.array(lin.std)) @ np.array(lin.coef)
    yv, pv, tv = y[val], phase[val], turn[val]
    for ph, name in ((E.ACT, "ACT（轮到自己行动）"), (E.ENDED, "ENDED（刚结束回合）")):
        cells = []
        for lo, hi in ((1, 3), (4, 6), (7, 9), (10, 99)):
            k = (pv == ph) & (tv >= lo) & (tv <= hi)
            if k.sum() > 50:
                cells.append(f"第{lo}-{hi if hi < 99 else '+'}回合 网络 {auc(z[k], yv[k]):.3f} / 线性 {auc(zl[k], yv[k]):.3f}")
        k = pv == ph
        print(f"{name}：全部 网络 {auc(z[k], yv[k]):.3f} / 线性 {auc(zl[k], yv[k]):.3f}；" + "；".join(cells))


if __name__ == "__main__":
    main()
