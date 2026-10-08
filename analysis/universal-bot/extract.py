"""Positions of the pairing self-play files as arrays, for the held-out comparison of step B.

    cd <checkout> && PYTHONPATH=. python3 analysis/universal-bot/extract.py OUT.npz FILE.jsonl.gz ...

The files are the v2 self-play games the pairing models were fitted on (branches
data/pairings-20261008 @ b0a37df and local/data-pairings-20261008 @ d58a27c, 2000 games each).
Every position learn.phased fits (turn ends and in-turn decisions, learn.netdata.rows) with the
version-2 features of the player it is scored for, that player's deck and the opponent's (record
"names"), the result, and the game it came from (file index, game number) so splits go by game.
Draws are left out, as learn.phased does.
"""
import gzip
import json
import sys
from multiprocessing import Pool

import numpy as np

from svsim.cards import library  # noqa: F401


def rows(job):
    fi, line = job
    from svsim.learn.features import features
    from svsim.learn.netdata import rows as R
    rec = json.loads(line)
    names = rec["names"]
    out = []
    for phase, me, state, result in R(rec):
        if result == 0.5:
            continue
        out.append((fi, rec.get("g", 0), phase, names[me], names[1 - me], result, features(state, me, False, 2)))
    return out


def main():
    out, files = sys.argv[1], sys.argv[2:]
    jobs = [(fi, line) for fi, f in enumerate(files) for line in gzip.open(f, "rt", encoding="utf-8")]
    with Pool(3) as pool:
        data = [r for part in pool.imap(rows, jobs, chunksize=8) for r in part]
    decks = sorted({r[3] for r in data} | {r[4] for r in data})
    np.savez_compressed(out, X=np.array([r[6] for r in data], np.float32), y=np.array([r[5] for r in data], np.int8),
                        phase=np.array([r[2] for r in data], np.int8), me=np.array([decks.index(r[3]) for r in data]),
                        op=np.array([decks.index(r[4]) for r in data]), file=np.array([r[0] for r in data]),
                        game=np.array([r[1] for r in data]), decks=np.array(decks), files=np.array(files))
    print(len(data), "positions", decks)


if __name__ == "__main__":
    main()
