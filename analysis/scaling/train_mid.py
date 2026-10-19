"""Train a value net with the mid-turn flag (learn.midrows; the architecture thread 2026-10-18 07:53Z).

The net starts from a candidate (SetNet.flagged_from: its weights, card table and standardization, V1 one zero row
longer, so at the start it is the candidate at flag 0 and the candidate on the raw position at flag 1). It is trained
on turn-end rows (learn.scaledata tok- files, flag 0) and mid-turn rows (learn.midrows mid- files, flag 1) together,
with the training settings of every scaling-test net (setnet.SetNet.fit: Adam, lr 1e-3, decay 0.5, patience 4, l2
1e-5, batch 256, --ftz). The validation part is the games with seed·100003 + g a multiple of 20, inside the training
shards, both kinds of row.

The two kinds weigh the same: the mid-turn rows are thinned (each kept with probability n_end / n_mid, from a
generator seeded per shard) so that both kinds have about as many rows. A turn has several decisions and one end, so
the thinning also keeps the training data's size and memory near a turn-end net's.

    python analysis/scaling/train_mid.py --deck ramp-t --opponent ramp-t \\
        --init analysis/scaling/models/net-gen3-30000.npz --tokens TOK --end 70100000:10 ... \\
        --mid-dir MID --mid 72300000:40 ... --holdout 71600018 ... --name NAME --checkpoint CKPT

Writes models/net-<NAME>.npz and data/net-<NAME>.json.
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse      # noqa: E402
import hashlib       # noqa: E402
import json          # noqa: E402
import sys           # noqa: E402
import time          # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np   # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from svsim.learn import midrows as MR  # noqa: E402
from svsim.learn.setnet import SetNet, score  # noqa: E402


def seeds_of(specs) -> list:
    """BASE:K (shards BASE + 2k, k < K) for each spec, in order."""
    out = []
    for spec in specs:
        base, k = (int(x) for x in spec.split(":"))
        out += [base + 2 * j for j in range(k)]
    return out


def align(net: SetNet, data) -> None:
    """data's card indices into the net's table, in place; every card of the data must be in it with the same
    static row (the net reads only what a card is)."""
    index = {int(c): i for i, c in enumerate(net.card_ids)}
    missing = [int(c) for c in data.card_ids if int(c) not in index]
    if missing:
        raise SystemExit(f"cards not in the net's table: {missing[:5]}")
    rows = [index[int(c)] for c in data.card_ids]
    if not np.array_equal(net.static[rows], data.static):
        raise SystemExit("the net's static rows differ from the tokens' cards.npz")
    data.cards = np.asarray(rows, dtype=np.int32)[data.cards]
    if hasattr(data, "hand_cards"):
        data.hand_cards = np.asarray(rows, dtype=np.int32)[data.hand_cards]


def by_kind(net: SetNet, data) -> dict:
    p = net.predict(data)
    return {kind: score(p[data.flag == f], data.result[data.flag == f]) for kind, f in (("end", 0.0), ("mid", 1.0))}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--deck", required=True)
    ap.add_argument("--opponent", required=True)
    ap.add_argument("--init", help="the candidate value net to start from (a flagged one goes on training)")
    ap.add_argument("--fresh", action="store_true",
                    help="no start: a new flagged net of the default structure (constructor seed --seed), its card "
                         "table and standardization from the training data (as train.py's nets); NM1's control arm")
    ap.add_argument("--tokens", required=True, help="the tok- files' folder, with its cards.npz")
    ap.add_argument("--end", action="append", required=True, metavar="BASE:K", help="turn-end shards")
    ap.add_argument("--mid-dir", required=True, help="the mid- files' folder (learn.midrows encode)")
    ap.add_argument("--mid", action="append", required=True, metavar="BASE:K", help="mid-turn shards")
    ap.add_argument("--holdout", type=int, nargs="+", default=[], help="seeds that must be in no training shard")
    ap.add_argument("--name", required=True)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--patience", type=int, default=4)
    ap.add_argument("--decay", type=float, default=0.5)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--l2", type=float, default=1e-5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--checkpoint", default=None)
    ap.add_argument("--hand-dir", default=None,
                    help="the hand- files (midrows encode-hand): add the opponent-hand zone (a diagnostic, SetNet "
                         "ophand), its rows 0 at the start")
    ap.add_argument("--v2a", action="store_true",
                    help="the start grown to v2a inputs (SetNet.with_v2a_from: V2_EXTRA's rows W1x, 0 at the start); "
                         "--tokens and --mid-dir then hold v2a files")
    ap.add_argument("--wide", action="store_true",
                    help="the start grown to twice its width with a trainable leaky ReLU (learn.widenet.WideSetNet."
                         "grown_from: the new blocks into old units 0, the slopes 0 at the start)")
    ap.add_argument("--extend-cards", action="store_true",
                    help="cards of the data the start has no row for are added by their static rows (setnet."
                         "extend_table; a new pairing's start)")
    ap.add_argument("--pairs", nargs="+", default=None, metavar="DECK:OPPONENT",
                    help="the orders of the pairing the net answers for (info pairs; default --deck:--opponent)")
    args = ap.parse_args()
    if bool(args.init) == args.fresh:
        raise SystemExit("give --init or --fresh")
    end_seeds, mid_seeds = seeds_of(args.end), seeds_of(args.mid)
    held = set(args.holdout) & (set(end_seeds) | set(mid_seeds))
    if held:
        raise SystemExit(f"holdout in the training shards: {sorted(held)}")
    tok, mid = Path(args.tokens), Path(args.mid_dir)
    end_files = [tok / f"tok-{s}.npz" for s in end_seeds]
    mid_files = [mid / f"mid-{s}.npz" for s in mid_seeds]
    missing = [str(f) for f in end_files + mid_files if not f.exists()]
    if missing:
        raise SystemExit(f"missing: {missing[:5]}")
    n_end = sum(len(np.load(f)["result"]) for f in end_files)
    n_mid = sum(len(np.load(f)["result"]) for f in mid_files)
    rate = min(1.0, n_end / n_mid)
    train, valid = MR.phase_split(end_files, mid_files, tok / "cards.npz", every=20, mid_rate=rate, seed=args.seed,
                                  hand_dir=args.hand_dir)
    if args.fresh:
        base = SetNet(train.static.shape[1], seed=args.seed, flag=True)
        base.set_cards(train.card_ids, train.static, np.bincount(train.cards, minlength=len(train.card_ids)) + 1)
    else:
        base = SetNet.load(args.init)
    if base.inputs != "v1" or base.slope != 0.0 or base.ophand:
        raise SystemExit("the start has to be a v1 ReLU net without the opponent-hand zone")
    info = {"deck": args.deck, "opponent": args.opponent, "flag": True, "inputs": "v1", "name": args.name,
            "init": "fresh" if args.fresh else str(args.init),
            "init_sha256": None if args.fresh else hashlib.sha256(Path(args.init).read_bytes()).hexdigest(),
            "end_shards": end_seeds, "mid_shards": mid_seeds, "shards": sorted(set(end_seeds) | set(mid_seeds)),
            "mid_rate": round(rate, 6), "end_rows": n_end, "mid_rows": n_mid,
            "train_positions": train.n, "valid_positions": valid.n,
            "train_by_kind": {"end": int((train.flag == 0).sum()), "mid": int((train.flag == 1).sum())},
            "valid_by_kind": {"end": int((valid.flag == 0).sum()), "mid": int((valid.flag == 1).sum())},
            "continued": base.flag, "ophand": bool(args.hand_dir), "v2a": bool(args.v2a), "wide": bool(args.wide)}
    if base.flag:                                 # a flagged net goes on training as it is
        net = base
        net.info = info
    else:
        net = SetNet.flagged_from(base, info=info)
    if args.hand_dir:
        net = SetNet.with_ophand_from(net, info=info)
    if args.v2a:
        net = SetNet.with_v2a_from(net, info=info)
        info["inputs"] = "v2a"
    if args.wide:
        from svsim.learn.widenet import WideSetNet
        net = WideSetNet.grown_from(net, info=info)
        info["extra"] = list(net.extra)
    if args.pairs:
        info["pairs"] = [p.split(":") for p in args.pairs]
    info["deck"], info["opponent"] = args.deck, args.opponent
    if args.extend_cards:
        from svsim.learn.setnet import extend_table
        n0 = len(net.card_ids)
        extend_table(net, train.card_ids, train.static)
        info["extended_cards"] = [int(c) for c in net.card_ids[n0:]]
    if train.inputs != net.inputs or valid.inputs != net.inputs:
        raise SystemExit(f"the data's inputs ({train.inputs}) are not the net's ({net.inputs})")
    for d in (train, valid):
        align(net, d)
    net.info["init_valid"] = by_kind(net, valid)
    print(json.dumps({k: v for k, v in net.info.items() if not k.endswith("shards")}), flush=True)
    t0 = time.time()
    net.fit(train, valid, epochs=args.epochs, batch=args.batch, lr=args.lr, l2=args.l2, patience=args.patience,
            seed=args.seed, decay=args.decay, checkpoint=args.checkpoint, ftz=True)
    report = {"name": args.name, "fit_s": round(time.time() - t0), "epochs": len(net.info["history"]),
              "lr": args.lr, "decay": args.decay, "patience": args.patience, "l2": args.l2, "batch": args.batch,
              "ftz": True, "train": by_kind(net, train), "valid": by_kind(net, valid),
              "init_valid": net.info["init_valid"], "mid_rate": net.info["mid_rate"]}
    net.info["report"] = report
    (HERE / "models").mkdir(exist_ok=True)
    net.save(HERE / f"models/net-{args.name}.npz")
    (HERE / f"data/net-{args.name}.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
