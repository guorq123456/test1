"""Scaling test, step 2: the DeepSets value net (learn.setnet) and the linear refits at 10^3 / 10^4 / 10^5 games,
scored on the same game-split holdout (the analysis line's 2f981bb: shards s_k = 70100000 + 2k of 1000 games;
10^3 = shard 0, 10^4 = shards 0-9, 10^5 = all 100; holdout: 5 shards of 1000 games, s_h = 70200000 + 2h).
Condition: the opponent's deck list is known (order and hand not).

Positions: every turn end (learn.netdata.rows phase ENDED: EndTurn and after_end_of_turn), seen by the player who
ended the turn; the label is the game's result for them. Every model is scored by Brier (main) and log-loss on
the same positions.

    python analysis/scaling/train.py net --size 1000 --tokens TOKDIR
    python analysis/scaling/train.py holdout-net --size 1000 --tokens TOKDIR      # a trained net, holdout later
    python analysis/scaling/train.py linear --size 1000 --records RECDIR
    python analysis/scaling/train.py holdout-linear --records RECDIR --tokens TOKDIR
    python analysis/scaling/train.py contrib --size 100000 --tokens TOKDIR
    python analysis/scaling/train.py --deck elf-t --opponent elf-t --base B --holdout-base H net ...   # another pairing

- `net`: trains on the size's shards; 1 game in 20 of them (game key seed * 100003 + g, key % 20 == 0) is the
  validation part for early stopping, the rest the training part. Writes models/net-<size>.npz and
  data/net-<size>.json: Brier and log-loss on the training part, the validation part and the holdout, and the
  epochs. Writes data/holdout-net-<size>.npz: the net's probability at every holdout turn end, with its keys.
  `--name NAME` (a variant, e.g. the wider net "wide"): every file is net-NAME-<size>.* instead.
- `linear`: refits the installed turn-end model's recipe on the size's games (learn.phased: features version 2 +
  hand, hpphase, turn ends only, the result as target, draws left out, l2 1e-3, sign constraints as installed):
  models/lin-<size>/<deck>-<opponent>-ended.json.
- `holdout-linear`: every linear model (the refits found and the installed <deck>-<opponent>-ended.json) at every
  holdout turn end, and at up to 20000 turn ends of each refit's own training games (a sample, seed 0):
  data/holdout-linear.npz and data/linear.json.
- `contrib`: does a card's part in the net's value depend on the position? Over holdout turn ends (a sample of
  3000, seed 0), the change in the net's logit when one copy of a card is taken out of a zone (my hand, my
  field, the opponent's field), grouped by card and zone: its mean, spread and range across positions. A model
  with a fixed score per card would show no spread at all. data/contrib-<size>.json.
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")    # the BLAS threads fight the self-play processes otherwise
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse      # noqa: E402
import gzip          # noqa: E402
import json          # noqa: E402
import subprocess    # noqa: E402
import sys           # noqa: E402
import tempfile      # noqa: E402
import time          # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np   # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from svsim.learn.setnet import NZ, Data, SetNet, score  # noqa: E402

BASE, STRIDE, HOLDOUT_BASE = 70100000, 2, 70200000
HOLDOUT = [HOLDOUT_BASE + STRIDE * h for h in range(5)]
PAIR = ("ramp-t", "ramp-t")      # the net's pairing (info deck / opponent; SetNetEnded scores only this one)
SIZES = {1000: 1, 10000: 10, 100000: 100, 20000: 10, 30000: 10,   # 20000 / 30000: 10^4 of v2skx plus --add (gen 2, 3)
         39000: 10, 131000: 100,   # 39000: 10^4 plus gen 2, 3, 4 (k 0-8); 131000: 10^5 plus those and sp-net100000
         29000: 0}   # 29000: self-play only (gen 2, 3, 4 k 0-8 through --add), no v2skx


def shards(size: int, add=()) -> list:
    """The size's training shards (the first SIZES[size] of BASE), plus --add BASE:K's K shards of another base."""
    out = [BASE + STRIDE * k for k in range(SIZES[size])]
    for spec in add or ():
        base, k = (int(x) for x in spec.split(":"))
        out += [base + STRIDE * j for j in range(k)]
    return out


def _files(folder, seeds, prefix: str, suffix: str) -> list:
    files = [Path(folder) / f"{prefix}{s}{suffix}" for s in seeds]
    missing = [str(f) for f in files if not f.exists()]
    if missing:
        raise SystemExit(f"missing: {missing[:5]}{' ...' if len(missing) > 5 else ''}")
    return files


def _align(net: SetNet, data: Data) -> Data:
    """data's card indices into the net's own static table (a tokens folder's cards.npz may list more cards)."""
    index = {int(c): i for i, c in enumerate(net.card_ids)}
    data.cards = np.array([index[int(c)] for c in data.card_ids], dtype=np.int32)[data.cards]
    return data


def _keys(d: Data) -> dict:
    return {"seed": d.seed, "g": d.g, "turn": d.turn, "result": d.result}


def _tag(args) -> str:
    """The files' name: <size>, or <name>-<size> for a variant (--name), so a variant never overwrites the fixed net."""
    return f"{args.name}-{args.size}" if args.name else str(args.size)


def net_main(args) -> None:
    tok = Path(args.tokens)
    data = Data(_files(tok, shards(args.size, args.add), "tok-", ".npz"), tok / "cards.npz")
    valid_mask = data.games() % 20 == 0
    train, valid = data.subset(~valid_mask), data.subset(valid_mask)
    net = SetNet(data.static.shape[1], phi=args.phi, rho=args.rho, seed=args.seed, slope=args.slope,
                 info={"deck": PAIR[0], "opponent": PAIR[1], "size": args.size, "shards": shards(args.size, args.add),
                       "train_positions": train.n, "name": args.name or None,
                       "valid_positions": valid.n})
    net.set_cards(data.card_ids, data.static, np.bincount(train.cards, minlength=len(data.card_ids)) + 1)
    t0 = time.time()
    net.fit(train, valid, epochs=args.epochs, batch=args.batch, lr=args.lr, l2=args.l2, patience=args.patience,
            seed=args.seed, decay=args.decay, checkpoint=args.checkpoint, ftz=args.ftz)
    report = {"size": args.size, "name": args.name or None, "ftz": args.ftz, "slope": args.slope, "phi": list(args.phi), "rho": list(args.rho), "lr": args.lr, "decay": args.decay,
              "patience": args.patience, "l2": args.l2,
              "batch": args.batch, "fit_s": round(time.time() - t0), "epochs": len(net.info["history"]),
              "train": score(net.predict(train), train.result), "valid": score(net.predict(valid), valid.result),
              "train_installed_linear": score(1 / (1 + np.exp(-train.linear)), train.result)}
    net.info["report"] = report
    (HERE / "models").mkdir(exist_ok=True)
    net.save(HERE / f"models/net-{_tag(args)}.npz")
    _holdout_net(net, tok, _tag(args), report, args.extra_holdout)


def _holdout_net(net: SetNet, tok: Path, tag: str, report: dict, extra=()) -> None:
    """The net on the holdout (when its 5 token files are there), into the report; writes the report. extra:
    NAME:SEED[,SEED...] further holdout sets (e.g. a generation's held-out self-play shard), as holdout_NAME."""
    hold = [tok / f"tok-{s}.npz" for s in HOLDOUT]
    if all(f.exists() for f in hold):
        h = _align(net, Data(hold, tok / "cards.npz"))
        p = net.predict(h)
        report["holdout"] = score(p, h.result)
        report["holdout_installed_linear"] = score(1 / (1 + np.exp(-h.linear)), h.result)
        np.savez_compressed(HERE / f"data/holdout-net-{tag}.npz", p=p.astype(np.float32), **_keys(h))
    for spec in extra or ():
        name, seeds = spec.split(":")
        seeds = [int(x) for x in seeds.split(",")]
        if set(seeds) & set(net.info.get("shards") or ()):
            raise SystemExit(f"holdout {name}: {seeds} is in the net's training shards")
        h = _align(net, Data(_files(tok, seeds, "tok-", ".npz"), tok / "cards.npz"))
        p = net.predict(h)
        report[f"holdout_{name}"] = {"seeds": seeds, **score(p, h.result),
                                     "installed_linear": score(1 / (1 + np.exp(-h.linear)), h.result)}
        np.savez_compressed(HERE / f"data/holdout-{name}-net-{tag}.npz", p=p.astype(np.float32), **_keys(h))
    (HERE / f"data/net-{tag}.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))


def holdout_net_main(args) -> None:
    """A trained net (models/net-<size>.npz) on the holdout, once the holdout is there."""
    net = SetNet.load(HERE / f"models/net-{_tag(args)}.npz")
    written = HERE / f"data/net-{_tag(args)}.json"     # keeps what was added to the written report (e.g. a note)
    report = {**net.info["report"], **(json.loads(written.read_text()) if written.exists() else {})}
    _holdout_net(net, Path(args.tokens), _tag(args), report, args.extra_holdout)


def linear_main(args) -> None:
    files = _files(args.records, shards(args.size), "rec-", ".jsonl.gz")
    out = HERE / f"models/lin-{args.size}"
    with tempfile.TemporaryDirectory() as tmp:
        plain = Path(tmp) / f"train-{args.size}.jsonl"
        with open(plain, "w", encoding="utf-8") as fh:
            for f in files:
                with gzip.open(f, "rt", encoding="utf-8") as src:
                    for line in src:
                        if line.strip():
                            fh.write(line if line.endswith("\n") else line + "\n")
        cmd = [sys.executable, "-m", "svsim.learn.phased", "--games", str(plain), "--out", str(out), "--matchup",
               f"{PAIR[0]}-{PAIR[1]}", "--features", "hand,hpphase", "--moments", "ended", "--workers", str(args.workers)]
        print(" ".join(cmd), flush=True)
        subprocess.run(cmd, cwd=ROOT, check=True)


def _linear_rows(job):
    """[(seed, g, turn, result, [logit of each model])] for the turn ends of one game."""
    from svsim.learn.model import LinearValue
    from svsim.learn.netdata import ENDED, rows
    line, paths = job
    record = json.loads(line)
    models = _MODELS.get(tuple(paths))
    if models is None:
        models = _MODELS[tuple(paths)] = [LinearValue.load(Path(p)) for p in paths]
    out = []
    for phase, player, state, result in rows(record):
        if phase == ENDED:
            out.append((record["seed"] // 100003, record["g"], state.turn, result,
                        [m.logit(state, player) for m in models]))
    return out


_MODELS: dict = {}


def _score_games(lines, paths, workers: int):
    from multiprocessing import Pool
    with Pool(workers) as pool:
        got = [r for part in pool.imap(_linear_rows, [(ln, paths) for ln in lines], chunksize=8) for r in part]
    keys = np.array([r[:4] for r in got], dtype=np.float64)
    logits = np.array([r[4] for r in got], dtype=np.float64).reshape(len(got), len(paths))
    return keys, logits


def _lines(files):
    for f in files:
        with gzip.open(f, "rt", encoding="utf-8") as src:
            for line in src:
                if line.strip():
                    yield line


def holdout_linear_main(args) -> None:
    names, paths = ["installed"], [str(ROOT / f"svsim/learn/phased_models/{PAIR[0]}-{PAIR[1]}-ended.json")]
    for size in SIZES:
        p = HERE / f"models/lin-{size}/{PAIR[0]}-{PAIR[1]}-ended.json"
        if p.exists():
            names.append(f"lin-{size}")
            paths.append(str(p))
    hold = _files(args.records, HOLDOUT, "rec-", ".jsonl.gz")
    keys, logits = _score_games(list(_lines(hold)), paths, args.workers)
    probs = 1 / (1 + np.exp(-logits))
    report = {"models": names, "holdout": {n: score(probs[:, i], keys[:, 3]) for i, n in enumerate(names)}}
    toks = [Path(args.tokens) / f"tok-{s}.npz" for s in HOLDOUT]
    if all(f.exists() for f in toks):                # the same positions as the nets', in the same order
        zs = [np.load(f) for f in toks]
        cat = {k: np.concatenate([z[k] for z in zs]) for k in ("seed", "g", "turn", "linear", "result")}
        same = (len(cat["result"]) == len(keys) and np.array_equal(cat["seed"], keys[:, 0])
                and np.array_equal(cat["g"], keys[:, 1]) and np.array_equal(cat["turn"], keys[:, 2]))
        report["aligned_with_tokens"] = bool(same)
        if same:
            report["installed_matches_token_label"] = float(np.max(np.abs(cat["linear"] - logits[:, 0])))
    report["train_sample"] = {}
    rng = np.random.default_rng(0)
    for i, n in enumerate(names[1:], 1):
        size = int(n.split("-")[1])
        lines = list(_lines(_files(args.records, shards(size), "rec-", ".jsonl.gz")))
        rng.shuffle(lines)
        k, lg = _score_games(lines[:max(1, 20000 // 19)], [paths[i]], args.workers)
        report["train_sample"][n] = score(1 / (1 + np.exp(-lg[:, 0])), k[:, 3])
    np.savez_compressed(HERE / "data/holdout-linear.npz", p=probs.astype(np.float32), models=np.array(names),
                        seed=keys[:, 0].astype(np.int64), g=keys[:, 1].astype(np.int32),
                        turn=keys[:, 2].astype(np.int32), result=keys[:, 3].astype(np.float32))
    (HERE / "data/linear.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))


def contributions(net: SetNet, data: Data, idx, zones=(0, 1, 4)) -> list:
    """[(card id, zone, position, delta logit)] for taking one copy of each card out of `zones`."""
    from svsim.learn import tokens as T
    out = []
    S = net._S()
    for n in idx:
        cards, dyn, count, seg, glob = data.batch(np.array([n]))
        A1 = (S @ net.W1s)[cards] + dyn @ net.W1d + net.b1
        H2 = np.maximum(np.maximum(A1, 0) @ net.W2 + net.b2, 0)
        P = np.zeros((NZ, H2.shape[1]))
        np.add.at(P, seg, H2 * count[:, None])
        base = np.concatenate([P.reshape(-1), glob[0]])
        pick = [t for t in range(len(cards)) if seg[t] in zones]
        if not pick:
            continue
        U = np.repeat(base[None, :], len(pick) + 1, axis=0)
        for r, t in enumerate(pick, 1):
            z = int(seg[t])
            U[r, z * H2.shape[1]:(z + 1) * H2.shape[1]] -= H2[t]
        Z1 = np.maximum(U @ net.V1 + net.c1, 0)
        Z2 = np.maximum(Z1 @ net.V2 + net.c2, 0)
        logit = Z2 @ net.v3 + net.c3[0]
        for r, t in enumerate(pick, 1):
            out.append((int(net.card_ids[cards[t]]), T.ZONES[int(seg[t])], int(n), float(logit[0] - logit[r])))
    return out


def contrib_main(args) -> None:
    tok = Path(args.tokens)
    net = SetNet.load(HERE / f"models/net-{_tag(args)}.npz")
    h = _align(net, Data([tok / f"tok-{s}.npz" for s in HOLDOUT], tok / "cards.npz"))
    rng = np.random.default_rng(0)
    idx = rng.choice(h.n, size=min(args.sample, h.n), replace=False)
    rows = contributions(net, h, idx)
    groups: dict = {}
    for cid, zone, n, d in rows:
        groups.setdefault((cid, zone), []).append(d)
    names = {}
    try:
        from svsim.cards.pool import card
        names = {cid: (card(cid).name_zh or card(cid).name) for cid, _ in groups}
    except Exception:
        pass
    table = []
    for (cid, zone), ds in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(ds) < 20:
            continue
        a = np.array(ds)
        table.append({"card": cid, "name": names.get(cid, ""), "zone": zone, "positions": len(a),
                      "mean": round(float(a.mean()), 4), "sd": round(float(a.std()), 4),
                      "p05": round(float(np.percentile(a, 5)), 4), "p95": round(float(np.percentile(a, 95)), 4),
                      "share_positive": round(float(np.mean(a > 0)), 3)})
    report = {"size": args.size, "positions": len(idx), "deltas": len(rows),
              "note": "delta = logit(position) - logit(position without one copy of the card); a fixed score per "
                      "card would give sd 0", "table": table}
    (HERE / f"data/contrib-{_tag(args)}.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n",
                                                         encoding="utf-8")
    print(json.dumps(report, indent=1, ensure_ascii=False)[:4000])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--deck", default="ramp-t", help="the pairing's decks (default the ramp-t mirror); the net's info")
    ap.add_argument("--opponent", default="ramp-t")
    ap.add_argument("--base", type=int, default=70100000, help="seed of training shard 0 (shard k: BASE + 2k)")
    ap.add_argument("--holdout-base", type=int, default=70200000, help="seed of holdout shard 0 (5 shards)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("net")
    n.add_argument("--size", type=int, choices=sorted(SIZES), required=True)
    n.add_argument("--tokens", required=True)
    n.add_argument("--phi", type=int, nargs=2, default=(64, 64))
    n.add_argument("--rho", type=int, nargs=2, default=(128, 64))
    n.add_argument("--epochs", type=int, default=60)
    n.add_argument("--patience", type=int, default=4)
    n.add_argument("--decay", type=float, default=0.5, help="step size factor after an epoch without improvement")
    n.add_argument("--batch", type=int, default=256)
    n.add_argument("--lr", type=float, default=1e-3)
    n.add_argument("--l2", type=float, default=1e-5)
    n.add_argument("--seed", type=int, default=0)
    n.add_argument("--name", default="", help="a variant's name: files net-<name>-<size>.* (the fixed net: none)")
    n.add_argument("--slope", type=float, default=0.0, help="leaky ReLU's negative slope (0: ReLU, the fixed net)")
    n.add_argument("--ftz", action="store_true",
                   help="set subnormal weights and Adam moments to 0 after every step (setnet.SetNet.fit ftz)")
    n.add_argument("--checkpoint", default=None,
                   help="a file for the fit's state after every epoch; the same command again goes on from it")
    n.add_argument("--add", action="append", default=[], metavar="BASE:K",
                   help="also train on K shards of BASE (BASE + 2k): generation 2 is --size 20000 --add 70800000:10")
    hn = sub.add_parser("holdout-net")
    hn.add_argument("--size", type=int, choices=sorted(SIZES), required=True)
    hn.add_argument("--tokens", required=True)
    hn.add_argument("--name", default="")
    for q in (n, hn):
        q.add_argument("--extra-holdout", action="append", default=[], metavar="NAME:SEED[,SEED]",
                       help="also score on these token files, as holdout_NAME (gen 4's k = 9: selfplay:71600018)")
    li = sub.add_parser("linear")
    li.add_argument("--size", type=int, choices=sorted(SIZES), required=True)
    li.add_argument("--records", required=True)
    li.add_argument("--workers", type=int, default=4)
    hl = sub.add_parser("holdout-linear")
    hl.add_argument("--records", required=True)
    hl.add_argument("--tokens", required=True)
    hl.add_argument("--workers", type=int, default=4)
    c = sub.add_parser("contrib")
    c.add_argument("--size", type=int, choices=sorted(SIZES), required=True)
    c.add_argument("--tokens", required=True)
    c.add_argument("--sample", type=int, default=3000)
    c.add_argument("--name", default="")
    args = ap.parse_args()
    global BASE, HOLDOUT, PAIR
    BASE, PAIR = args.base, (args.deck, args.opponent)
    HOLDOUT = [args.holdout_base + STRIDE * h for h in range(5)]
    (HERE / "data").mkdir(exist_ok=True)
    {"net": net_main, "holdout-net": holdout_net_main, "linear": linear_main, "holdout-linear": holdout_linear_main,
     "contrib": contrib_main}[args.cmd](args)


if __name__ == "__main__":
    main()
