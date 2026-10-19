"""NM1 references (the architecture thread 2026-10-19 01:4xZ, README "NM1 自对弈分工"): on the NM1 holdout shards
(ramp-t vs elf-t, both sides v2skx), the Brier of the scorers that exist today, as the yardstick for the new net.

Positions (the same two kinds as analysis/scaling/mid_report.py, from both seats):
- turn ends: learn.netdata.rows' ENDED rows (after the turn-end abilities, scored for the player who ended), the rows
  of `scaledata encode`'s tok- files;
- mid-turn decisions: learn.setpolicy.decisions' rows (the mover to act), the rows of `midrows encode`'s mid- files.
Scorers, each called directly (search.evaluate's numbers, logit = score / SCALE):
- v2skx: the weights `scaledata encode` labels "linear" with (tools.arena.make_agent(v2skx)'s search weights),
  player_moves_next False; on a mid-turn row that is what v2skx's search does with such a leaf (as is); also
  "v2skx_eot": the turn ended on a copy first (search.evaluate.after_end_of_turn; a finished game 1 / 0);
- net-mid-ramp-t and net-mid-elf-t as they are (SetNet.logit; flag 0 on turn ends, 1 on mid-turn rows). Their pairing
  is a mirror, so in a search of this pairing SetNetEnded never asks them (it falls back to v2skx); here they are
  asked anyway. A card not in a net's table gets its static row (SetNet._add_cards, as in play).
Per holdout shard, kind and the scored player's deck: Brier, log-loss, ece (10 bins); pooled over the shards with a
95% bootstrap of games (2000, rng 0). A per-position dump (npz) for later pairing with the new net.

    python brier_ref.py --records DIR --seed S [--seed S ...] --models DIR --out OUT.json --dump DIR [--games N]
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import gzip      # noqa: E402
import json      # noqa: E402
import math      # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

SCORERS = ("v2skx", "v2skx_eot", "net_ramp", "net_elf")


def sig(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60, 60)))


def ece(p, y):
    b = np.minimum((p * 10).astype(int), 9)
    return float(sum((b == k).sum() / len(p) * abs(p[b == k].mean() - y[b == k].mean()) for k in range(10)
                     if (b == k).any()))


def judged(p, y):
    q = np.clip(p, 1e-7, 1 - 1e-7)
    return {"n": int(len(y)), "brier": round(float(((p - y) ** 2).mean()), 5),
            "log_loss": round(float((-(y * np.log(q) + (1 - y) * np.log(1 - q))).mean()), 5), "ece": round(ece(p, y), 5)}


def shard(path: Path, models: Path, games: int | None):
    from svsim.learn.model import SCALE
    from svsim.learn.netdata import ENDED, rows, _search
    from svsim.learn.scaledata import SPEC
    from svsim.learn.setnet import SetNet
    from svsim.learn.setpolicy import decisions
    from svsim.search.evaluate import after_end_of_turn
    from svsim.tools.arena import make_agent
    w = _search(make_agent(SPEC, 0)).weights
    nets = {"net_ramp": SetNet.load(models / "net-mid-ramp-t.npz"), "net_elf": SetNet.load(models / "net-mid-elf-t.npz")}
    out = {k: [] for k in ("g", "i", "kind", "deck", "turn", "first", "y") + SCORERS}

    def add(rec, i, kind, state, me, y, extra):
        out["g"].append(rec["g"])
        out["i"].append(i)
        out["kind"].append(kind)
        out["deck"].append(state.players[me].deck_name)
        out["turn"].append(state.turn)
        out["first"].append(int(me == rec.get("first", -1)))
        out["y"].append(y)
        for k, v in extra.items():
            out[k].append(v)

    with gzip.open(path, "rt") as fh:
        n = 0
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            n += 1
            if games is not None and n > games:
                break
            winner = rec.get("winner")
            for i, (phase, me, state, y) in rows(rec, index=True):
                if phase != ENDED:
                    continue
                v = w.score(state, me, False) / SCALE
                add(rec, i, 0, state, me, y, {"v2skx": v, "v2skx_eot": v,
                                             **{k: net.logit(state, me) for k, net in nets.items()}})
            for i, state, *_rest in decisions(rec):
                me = state.active
                y = 0.5 if winner is None else float(winner == me)
                ended = after_end_of_turn(state)
                if ended.winner is not None:
                    eot = 60.0 if ended.winner == me else (-60.0 if ended.winner == 1 - me else 0.0)
                else:
                    eot = w.score(ended, me, False) / SCALE
                add(rec, i, 1, state, me, y, {"v2skx": w.score(state, me, False) / SCALE, "v2skx_eot": eot,
                                             **{k: net.logit(state, me, mid=True) for k, net in nets.items()}})
    return {k: np.asarray(v) for k, v in out.items()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", required=True)
    ap.add_argument("--seed", type=int, action="append", required=True)
    ap.add_argument("--models", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dump", required=True)
    ap.add_argument("--games", type=int, default=None, help="the first N games of each shard (a test run)")
    args = ap.parse_args()
    dump = Path(args.dump)
    dump.mkdir(parents=True, exist_ok=True)
    import hashlib
    report = {"seeds": args.seed, "shards": {}, "pooled": {},
              "models_sha256": {f: hashlib.sha256((Path(args.models) / f).read_bytes()).hexdigest()
                                for f in ("net-mid-ramp-t.npz", "net-mid-elf-t.npz")}}
    parts = []
    for s in args.seed:
        target = dump / f"ref-{s}.npz"
        if target.exists() and args.games is None:
            d = dict(np.load(target))
        else:
            d = shard(Path(args.records) / f"rec-{s}.jsonl.gz", Path(args.models), args.games)
            np.savez_compressed(str(target) + ".tmp.npz", seed=np.full(len(d["y"]), s), **d)
            os.replace(str(target) + ".tmp.npz", target)
        d["seed"] = np.full(len(d["y"]), s)
        parts.append(d)
        rep = {}
        for kind, kname in ((0, "end"), (1, "mid")):
            for deck in ("ramp-t", "elf-t", "both"):
                m = (d["kind"] == kind) & ((d["deck"] == deck) if deck != "both" else True)
                rep[f"{kname}/{deck}"] = {k: judged(sig(d[k][m]), d["y"][m]) for k in SCORERS
                                          if not (kind == 0 and k == "v2skx_eot")}
        report["shards"][str(s)] = rep
        print(s, json.dumps({k: {s_: v["brier"] for s_, v in r.items()} for k, r in rep.items()}), flush=True)
    d = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    gid = d["seed"].astype(np.int64) * 100000 + d["g"]
    games, inv = np.unique(gid, return_inverse=True)
    rng = np.random.default_rng(0)
    idx = rng.integers(0, len(games), (2000, len(games)))
    for kind, kname in ((0, "end"), (1, "mid")):
        for deck in ("ramp-t", "elf-t", "both"):
            m = (d["kind"] == kind) & ((d["deck"] == deck) if deck != "both" else True)
            cnt = np.bincount(inv[m], minlength=len(games))[idx].sum(1)
            rec = {}
            for k in SCORERS:
                if kind == 0 and k == "v2skx_eot":
                    continue
                e = (sig(d[k][m]) - d["y"][m]) ** 2
                se = np.bincount(inv[m], weights=e, minlength=len(games))[idx].sum(1)
                rec[k] = {**judged(sig(d[k][m]), d["y"][m]),
                          "brier_ci": [round(float(x), 5) for x in np.percentile(se / cnt, [2.5, 97.5])]}
            report["pooled"][f"{kname}/{deck}"] = rec
            print("pooled", kname, deck, json.dumps({k: [v["brier"]] + v["brier_ci"] for k, v in rec.items()}),
                  flush=True)
    report["games"] = int(len(games))
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
