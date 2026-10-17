"""Train the policy head (learn.policy) on the visit counts recorded in self-play (learn.netdata).

    python -m svsim.tools.train_policy --games games_v1.jsonl --out svsim/learn/policies/ramp-ramp.npz

A tenth of the games is held out; the report gives how often the head's top
move is the search's most-visited one there (at the turn's first decision
and inside the turn), against the share a uniform guess would get.
"""
from __future__ import annotations

import argparse
import json
import time
from multiprocessing import Pool

import numpy as np


def _ids(line: str) -> set:
    """Card ids that are a move's source or target in a game's decisions (the vocabulary)."""
    from svsim.learn.policy import _source, _target, decisions
    out = set()
    for state, legal, pi, start in decisions(json.loads(line)):
        for a in legal:
            src = _source(state, a)
            _, tgt = _target(state, a)
            out.update(c.defn.card_id for c in (src, tgt) if c is not None)
    return out


def _features(job) -> list:
    from svsim.learn import encode as E
    from svsim.learn.policy import decisions, move_features
    line, vocab = job
    record = json.loads(line)
    out = []
    for state, legal, pi, start in decisions(record):
        dense = E.raw(state, state.active)[0]
        out.append((record["g"], start, np.array([dense + move_features(state, a, vocab) for a in legal],
                                                 dtype=np.float32), pi))
    return out


def main() -> None:
    from pathlib import Path
    from svsim.learn.policy import PolicyNet
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--hidden", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    t0 = time.time()
    lines = [line for path in args.games for line in open(path, encoding="utf-8")]
    with Pool(args.workers) as pool:
        vocab_ids = sorted(set().union(*pool.map(_ids, lines, chunksize=8)))
        vocab = {c: i for i, c in enumerate(vocab_ids)}
        feats = [r for part in pool.imap(_features, [(line, vocab) for line in lines], chunksize=4) for r in part]
    print(f"{len(lines)} games, {len(feats)} decisions ({time.time() - t0:.0f}s)", flush=True)

    def pack(rows):
        X = np.vstack([fs for _, _, fs, _ in rows]).astype(np.float64)
        target = np.array([x for _, _, _, pi in rows for x in pi], dtype=np.float64)
        starts = np.cumsum([0] + [len(fs) for _, _, fs, _ in rows[:-1]])
        return X, starts, target
    train = [r for r in feats if r[0] % 10 != 0]
    test = [r for r in feats if r[0] % 10 == 0]
    X, st, tg = pack(train)
    Xv, stv, tgv = pack(test)
    net = PolicyNet.train(X, st, tg, vocab_ids, Xv, stv, tgv, hidden=args.hidden, epochs=args.epochs,
                          info={"games": len(lines), "decisions": len(feats), "files": args.games})
    net.save(Path(args.out))
    z = net.scores_of(Xv)
    sizes = np.diff(np.append(stv, len(z)))
    for label, keep in (("回合开始", True), ("回合中", False)):
        hit = guess = n = 0
        for (g, start, fs, pi), s0, k in zip(test, stv, sizes):
            if start != keep:
                continue
            n += 1
            hit += int(np.argmax(z[s0:s0 + k]) == int(np.argmax(pi)))
            guess += 1.0 / k
        print(f"{label}：策略头首选 = 搜索访问最多的走法 {hit}/{n} = {hit / max(n, 1):.1%}（随便猜 {guess / max(n, 1):.1%}）")
    print(f"saved {args.out} ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
