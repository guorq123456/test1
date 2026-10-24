"""Two value-net arms on the same validation rows (train_mid.py's split: every 20, its mid-row rate and seed), paired
over the validation games: the Brier difference A - B and its spread over game resamples (the architecture thread
2026-10-20 01:23Z: an interval clear of 0 picks the better arm, one across 0 picks the fresh arm).

    python analysis/scaling/arm_paired.py --tokens TOK --end BASE:K ... --mid-dir MID --mid BASE:K ... \
        --a NET_A --b NET_B [--split key] [--resamples 2000] --out OUT.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_mid import align, seeds_of   # noqa: E402

from svsim.learn import midrows as MR   # noqa: E402
from svsim.learn.setnet import SetNet   # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens", required=True)
    ap.add_argument("--end", nargs="+", action="extend", required=True)
    ap.add_argument("--mid-dir", required=True)
    ap.add_argument("--mid", nargs="+", action="extend", required=True)
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--split", default="key")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resamples", type=int, default=2000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    tok, mid = Path(args.tokens), Path(args.mid_dir)
    end_files = [tok / f"tok-{s}.npz" for s in seeds_of(args.end)]
    mid_files = [mid / f"mid-{s}.npz" for s in seeds_of(args.mid)]
    n_end = sum(len(np.load(f)["result"]) for f in end_files)
    n_mid = sum(len(np.load(f)["result"]) for f in mid_files)
    rate = min(1.0, n_end / n_mid)                       # as train_mid.py
    plan = MR._plan(end_files, mid_files, 20, rate, args.seed, args.split)
    games = []                                           # the game of every validation row, in _assemble's order
    for f, _flag, keep, valid in plan:
        with np.load(f) as z:
            key = z["seed"].astype(np.int64) * 100003 + z["g"].astype(np.int64)
        games.append(key[keep & valid])
    games = np.concatenate(games)
    out = {"rows": int(len(games)), "games": int(len(np.unique(games))), "a": args.a, "b": args.b}
    err = {}
    for name in ("a", "b"):
        data = MR._assemble(plan, tok / "cards.npz", "valid")
        net = SetNet.load(getattr(args, name))
        align(net, data)
        p = net.predict(data)
        err[name] = (p - data.result) ** 2
        flag = data.flag
        out[f"brier_{name}"] = {"end": round(float(err[name][flag == 0].mean()), 5),
                                "mid": round(float(err[name][flag == 1].mean()), 5),
                                "both": round(float(err[name].mean()), 5)}
    uniq, inv = np.unique(games, return_inverse=True)
    d = np.bincount(inv, weights=err["a"] - err["b"])    # per game: summed difference, and its rows
    n = np.bincount(inv).astype(float)
    rng = np.random.default_rng(0)
    draws = []
    for _ in range(args.resamples):
        pick = rng.integers(0, len(uniq), len(uniq))
        draws.append(d[pick].sum() / n[pick].sum())
    draws = np.array(draws)
    out["a_minus_b"] = round(float(d.sum() / n.sum()), 5)
    out["sd"] = round(float(draws.std()), 5)
    out["ci95"] = [round(float(np.percentile(draws, 2.5)), 5), round(float(np.percentile(draws, 97.5)), 5)]
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
