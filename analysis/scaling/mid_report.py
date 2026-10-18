"""Holdout report for a value net with the mid-turn flag (the architecture thread 2026-10-18 07:53Z, item 4).

On each holdout shard, for both kinds of position:
- turn ends (tok- file): the new net's turn-end branch (flag 0) against the candidate;
- mid-turn decisions (mid- file, learn.midrows): the new net's mid-turn branch (flag 1) against "end the turn now
  and score with the candidate". That is what +neteot does: search.evaluate.after_end_of_turn on a copy, a won or
  lost game scored 1 / 0, otherwise the candidate's logit for the mover. The new net's turn-end branch after the
  same turn end is also given ("new +neteot").
For each: Brier, log-loss and the calibration in 10 bins of the predicted win chance (rows, mean prediction, win rate;
"ece" is the row-weighted mean gap). The baseline replays the records (learn.setpolicy.decisions, the mid- file's
rows in order, checked by game and action index).

    python analysis/scaling/mid_report.py --net NEW --base CANDIDATE --tokens TOK --mid-dir MID --records DIR \\
        --holdout NAME:SEED ... [--end-holdout NAME:SEED,SEED,...] --out OUT [--dump DIR]
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import gzip      # noqa: E402
import json      # noqa: E402
import sys       # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from svsim.learn import midrows as MR  # noqa: E402
from svsim.learn.setnet import SetNet, score  # noqa: E402


def calibration(p, y, bins: int = 10) -> dict:
    p, y = np.asarray(p, np.float64), np.asarray(y, np.float64)
    k = np.minimum((p * bins).astype(int), bins - 1)
    rows = []
    gap = 0.0
    for b in range(bins):
        m = k == b
        n = int(m.sum())
        if n:
            mp, wr = float(p[m].mean()), float(y[m].mean())
            gap += n * abs(mp - wr)
            rows.append({"bin": f"{b / bins:.1f}-{(b + 1) / bins:.1f}", "n": n, "mean_p": round(mp, 4),
                         "win_rate": round(wr, 4)})
        else:
            rows.append({"bin": f"{b / bins:.1f}-{(b + 1) / bins:.1f}", "n": 0})
    return {"ece": round(gap / max(len(p), 1), 5), "bins": rows}


def judged(p, y) -> dict:
    return {**score(p, y), "calibration": calibration(p, y)}


def _aligned(net: SetNet, data):
    index = {int(c): i for i, c in enumerate(net.card_ids)}
    out = object.__new__(type(data))
    out.__dict__.update(data.__dict__)
    out.cards = np.array([index[int(c)] for c in data.card_ids], dtype=np.int32)[data.cards]
    return out


def predict(net: SetNet, data, flagged: bool):
    """net's win chances on data (whose globals end in the flag column); a net without the flag sees the globals
    without that column."""
    d = _aligned(net, data)
    if not flagged:
        d.globals = d.globals[:, :-1]
    return net.predict(d)


def eot_baseline(records: Path, mid_file: Path, base: SetNet, new: SetNet):
    """(candidate after the turn end, new net's turn-end branch after it) per row of mid_file."""
    from svsim.learn.setpolicy import decisions
    from svsim.search.evaluate import after_end_of_turn
    z = np.load(mid_file)
    keys = list(zip(z["g"].tolist(), z["i"].tolist()))
    pb, pn, seen = [], [], []
    with gzip.open(records, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            for i, state, *_ in decisions(rec):
                me = state.active
                ended = after_end_of_turn(state)
                if ended.winner is not None:
                    v = 1.0 if ended.winner == me else (0.0 if ended.winner == 1 - me else 0.5)
                    pb.append(v)
                    pn.append(v)
                else:
                    pb.append(1 / (1 + np.exp(-base.logit(ended, me))))
                    pn.append(1 / (1 + np.exp(-new.logit(ended, me))))
                seen.append((rec["g"], i))
    if seen != keys:
        raise SystemExit(f"{mid_file}: the replayed decisions are not the file's rows")
    return np.asarray(pb), np.asarray(pn)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--net", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--tokens", required=True)
    ap.add_argument("--mid-dir", required=True)
    ap.add_argument("--records", required=True, help="a folder with rec-<seed>.jsonl.gz of the --holdout seeds")
    ap.add_argument("--holdout", action="append", default=[], metavar="NAME:SEED")
    ap.add_argument("--end-holdout", action="append", default=[], metavar="NAME:SEED[,SEED]",
                    help="turn ends only (no records with the search's decisions)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dump", default=None, help="a folder for the per-position probabilities (<holdout>-end.npz, "
                                                 "<holdout>-mid.npz; the analysis line's recheck)")
    args = ap.parse_args()
    dump = Path(args.dump) if args.dump else None
    if dump:
        dump.mkdir(parents=True, exist_ok=True)
    new, base = SetNet.load(args.net), SetNet.load(args.base)
    if not new.flag or base.flag:
        raise SystemExit("--net needs the flag, --base none")
    trained = set(new.info.get("shards") or ())
    tok, mid = Path(args.tokens), Path(args.mid_dir)
    report = {"net": str(args.net), "base": str(args.base), "holdouts": {}}
    for spec in args.end_holdout:
        name, seeds = spec.split(":")
        seeds = [int(s) for s in seeds.split(",")]
        if set(seeds) & trained:
            raise SystemExit(f"{name}: in the net's training shards")
        d = MR.phase_data([tok / f"tok-{s}.npz" for s in seeds], [], tok / "cards.npz")
        p_new, p_base = predict(new, d, True), predict(base, d, False)
        report["holdouts"][name] = {"seeds": seeds, "end": {"new": judged(p_new, d.result),
                                                            "candidate": judged(p_base, d.result)}}
        if dump:
            i = np.concatenate([np.load(tok / f"tok-{s}.npz")["i"] for s in seeds])
            np.savez_compressed(dump / f"{name}-end.npz", seed=d.seed, g=d.g, i=i, turn=d.turn, y=d.result,
                                p_new=p_new, p_candidate=p_base)
        print(json.dumps({name: {k: v["brier"] for k, v in report["holdouts"][name]["end"].items()}}), flush=True)
    for spec in args.holdout:
        name, s = spec.split(":")
        s = int(s)
        if s in trained:
            raise SystemExit(f"{name}: in the net's training shards")
        d_end = MR.phase_data([tok / f"tok-{s}.npz"], [], tok / "cards.npz")
        d_mid = MR.phase_data([], [mid / f"mid-{s}.npz"], tok / "cards.npz")
        pb, pn = eot_baseline(Path(args.records) / f"rec-{s}.jsonl.gz", mid / f"mid-{s}.npz", base, new)
        e_new, e_base = predict(new, d_end, True), predict(base, d_end, False)
        m_new, m_raw = predict(new, d_mid, True), predict(base, d_mid, False)
        report["holdouts"][name] = {
            "seeds": [s],
            "end": {"new": judged(e_new, d_end.result), "candidate": judged(e_base, d_end.result)},
            "mid": {"new": judged(m_new, d_mid.result),
                    "candidate_after_turn_end": judged(pb, d_mid.result),
                    "new_after_turn_end": judged(pn, d_mid.result),
                    "candidate_as_is": judged(m_raw, d_mid.result)}}
        if dump:
            zt, zm = np.load(tok / f"tok-{s}.npz"), np.load(mid / f"mid-{s}.npz")
            np.savez_compressed(dump / f"{name}-end.npz", seed=d_end.seed, g=d_end.g, i=zt["i"], turn=d_end.turn,
                                y=d_end.result, p_new=e_new, p_candidate=e_base)
            np.savez_compressed(dump / f"{name}-mid.npz", seed=d_mid.seed, g=d_mid.g, i=zm["i"], turn=d_mid.turn,
                                start=zm["start"], y=d_mid.result, p_new=m_new, p_candidate_after_turn_end=pb,
                                p_new_after_turn_end=pn, p_candidate_as_is=m_raw)
        print(json.dumps({name: {kind: {k: v["brier"] for k, v in r.items()}
                                 for kind, r in report["holdouts"][name].items() if kind != "seeds"}}), flush=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
