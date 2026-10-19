"""NM1 new-net holdout report (registered in README 6ba8429): the two arms' logits on the rows of brier_ref.py's dumps
(the same replay: learn.netdata.rows' ENDED rows with flag 0, learn.setpolicy.decisions' rows with flag 1), joined
with those dumps row by row (seed, g, i, kind checked), then Brier / log-loss / ece by kind and the scored side's deck,
and paired differences with a 95% bootstrap of games (2000, rng 0).

    python holdout_new.py --records DIR --ref DIR --net NAME=PATH ... --seed S ... --out OUT.json --dump DIR [--workers 4]
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import gzip      # noqa: E402
import hashlib   # noqa: E402
import json      # noqa: E402
from multiprocessing import Pool  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402


def sig(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60, 60)))


def ece(p, y):
    b = np.minimum((p * 10).astype(int), 9)
    return float(sum((b == k).sum() / len(p) * abs(p[b == k].mean() - y[b == k].mean()) for k in range(10)
                     if (b == k).any()))


def judged(p, y):
    q = np.clip(p, 1e-7, 1 - 1e-7)
    return {"n": int(len(y)), "brier": round(float(((p - y) ** 2).mean()), 5),
            "log_loss": round(float((-(y * np.log(q) + (1 - y) * np.log(1 - q))).mean()), 5),
            "ece": round(ece(p, y), 5), "mean_p": round(float(p.mean()), 4), "win_rate": round(float(y.mean()), 4)}


def shard(job):
    path, nets, target = job
    from svsim.learn.netdata import ENDED, rows
    from svsim.learn.setnet import SetNet
    from svsim.learn.setpolicy import decisions
    loaded = {k: SetNet.load(p) for k, p in nets.items()}
    out = {k: [] for k in ("g", "i", "kind", *loaded)}
    with gzip.open(path, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            for i, (phase, me, state, _y) in rows(rec, index=True):
                if phase != ENDED:
                    continue
                out["g"].append(rec["g"]); out["i"].append(i); out["kind"].append(0)
                for k, net in loaded.items():
                    out[k].append(net.logit(state, me))
            for i, state, *_rest in decisions(rec):
                me = state.active
                out["g"].append(rec["g"]); out["i"].append(i); out["kind"].append(1)
                for k, net in loaded.items():
                    out[k].append(net.logit(state, me, mid=True))
    arrays = {k: np.asarray(v) for k, v in out.items()}
    np.savez_compressed(str(target) + ".tmp.npz", **arrays)
    os.replace(str(target) + ".tmp.npz", target)
    return str(target)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", required=True)
    ap.add_argument("--ref", required=True, help="brier_ref.py's dump folder (ref-<seed>.npz)")
    ap.add_argument("--net", action="append", required=True, metavar="NAME=PATH")
    ap.add_argument("--seed", type=int, action="append", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dump", required=True)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    nets = dict(s.split("=", 1) for s in args.net)
    dump = Path(args.dump)
    dump.mkdir(parents=True, exist_ok=True)
    jobs = [(str(Path(args.records) / f"rec-{s}.jsonl.gz"), nets, dump / f"new-{s}.npz") for s in args.seed
            if not (dump / f"new-{s}.npz").exists()]
    with Pool(args.workers) as pool:
        for t in pool.imap_unordered(shard, jobs):
            print("done", t, flush=True)
    parts = []
    for s in args.seed:
        r, n = dict(np.load(Path(args.ref) / f"ref-{s}.npz")), dict(np.load(dump / f"new-{s}.npz"))
        for k in ("g", "i", "kind"):
            if not np.array_equal(r[k], n[k]):
                raise SystemExit(f"{s}: rows differ from the reference dump ({k})")
        r.update({k: n[k] for k in nets})
        r["seed"] = np.full(len(r["y"]), s)
        parts.append(r)
    d = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    gid = d["seed"].astype(np.int64) * 100000 + d["g"]
    games, inv = np.unique(gid, return_inverse=True)
    idx = np.random.default_rng(0).integers(0, len(games), (2000, len(games)))
    names = list(nets)
    report = {"nets": {k: {"path": p, "sha256": hashlib.sha256(Path(p).read_bytes()).hexdigest()} for k, p in nets.items()},
              "seeds": args.seed, "games": int(len(games)), "scores": {}, "paired": {}}

    def boot(e, m):
        cnt = np.bincount(inv[m], minlength=len(games))[idx].sum(1)
        se = np.bincount(inv[m], weights=e[m], minlength=len(games))[idx].sum(1)
        return [round(float(e[m].mean()), 5)] + [round(float(x), 5) for x in np.percentile(se / cnt, [2.5, 97.5])]

    for kind, kname in ((0, "end"), (1, "mid")):
        refs = ["v2skx"] + (["v2skx_eot"] if kind == 1 else [])
        for deck in sorted(set(d["deck"].tolist()), key=lambda x: x != "ramp-t") + ["both"]:
            m = (d["kind"] == kind) & ((d["deck"] == deck) if deck != "both" else True)
            y = d["y"]
            report["scores"][f"{kname}/{deck}"] = {k: judged(sig(d[k][m]), y[m]) for k in names + refs}
            err = {k: (sig(d[k]) - y) ** 2 for k in names + refs}
            pr = {}
            for a in names:
                for b in refs:
                    pr[f"{b} - {a}"] = boot(err[b] - err[a], m)          # positive: the net is better
            if len(names) == 2:
                pr[f"{names[0]} - {names[1]}"] = boot(err[names[0]] - err[names[1]], m)  # positive: names[1] better
            report["paired"][f"{kname}/{deck}"] = pr
            print(kname, deck, json.dumps({k: v["brier"] for k, v in report["scores"][f"{kname}/{deck}"].items()}),
                  json.dumps(pr), flush=True)
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
