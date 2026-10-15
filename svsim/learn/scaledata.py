"""The scaling test's data (the architecture thread 2026-10-15 17:27Z): strong self-play on the ramp-t mirror,
recorded in shards by seed, then every turn end encoded as card tokens (learn.tokens) with its labels.

    python -m svsim.tools.host svsim.learn.scaledata play --base S --stride 2 --shards 10 100 --out DIR --workers 11
    python -m svsim.learn.scaledata encode --records DIR --out TOKDIR --workers 4
    python -m svsim.learn.scaledata merge --inputs DIR1 DIR2 ... --out DIR
    python -m svsim.learn.scaledata check DIR

`play`: shard k is netdata seed S + stride * k, games g = 0 .. --per-shard - 1 (default 1000), each one learn.netdata.play
with SPEC on both sides, no exploration. A game is fixed by (seed, g): deal seed * 100003 + g, agent seeds
seed * 1000 + 2g + i, seat g % 2 for --deck (stride 2 keeps the agent seeds of
1000-game shards apart: the analysis line, 2f981bb). Each finished game is appended to DIR/rec-<seed>.part.jsonl at
once (one JSON record per line, with "cpu": the seconds of CPU time its worker spent on it, one core); a complete
shard is compressed to DIR/rec-<seed>.jsonl.gz and its part file removed. Stopped at any point, the same command
picks up where it left off (a cut-off last line is dropped and its game played again; complete shards are skipped).
Shards and games are independent, so any machine can play any shard and `merge` puts them together.

`merge`: every rec-*.jsonl.gz under --inputs into --out, one game per (seed, g); a game found twice must be the
same record apart from "date" and "cpu" (a determinism check across machines), else it is reported (the first
one is kept). Part files are not merged.

`encode`: each record shard to TOKDIR/tok-<seed>.npz (skipped if there): every turn end of every game
(learn.netdata.rows, phase ENDED: the moment the installed turn-end evaluator scores) for the player who ended
the turn, as learn.tokens.encode, with
- result: 1 if that player won, 0 if they lost, 0.5 for a draw;
- linear: the installed evaluator's logit there (SPEC's turn-end model, PhasedLearned.score / SCALE);
- seed, g, i (the action index of the turn's end), turn, player, actions (the game's length).
Arrays: tokens int16 [sum T, len(TOKEN)], cards int32 [sum T] (each token's card id, to look up its static row in
cards.npz), offsets int64 [N + 1] (position n's tokens are
tokens[offsets[n]:offsets[n + 1]]), globals float32 [N, len(GLOBALS)], and the labels. TOKDIR/cards.npz: the
static rows (learn.tokens.static) of every card id seen, its names, and the token and global names.

Condition: the opponent's deck list is known (order and hand not).
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import time
from pathlib import Path

SPEC = "mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"   # v2skx (analysis/install)
VOLATILE = ("date", "cpu")                       # fields that may differ between two plays of the same game


def _play(job):
    from svsim.learn.netdata import play
    seed, g, deck, opponent, spec = job
    t0 = time.process_time()
    record = play((g, seed, deck, opponent, spec, 0.0))
    record["cpu"] = round(time.process_time() - t0, 3)
    return seed, record


def _read_part(path: Path) -> list:
    """The complete records of a part file; rewrites it without a cut-off last line."""
    if not path.exists():
        return []
    good, cut = [], False
    with open(path, "rb") as fh:
        lines = fh.read().split(b"\n")
    for n, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            good.append(json.loads(line))
        except json.JSONDecodeError:
            if n < len(lines) - 2:
                raise SystemExit(f"{path}: line {n + 1} is broken but not the last one; look at it")
            cut = True
    if cut:
        with open(path, "w", encoding="utf-8") as fh:
            for r in good:
                fh.write(json.dumps(r) + "\n")
    return good


def _finish(out: Path, seed: int, n: int) -> bool:
    part, done = out / f"rec-{seed}.part.jsonl", out / f"rec-{seed}.jsonl.gz"
    records = {r["g"]: r for r in _read_part(part)}
    if len(records) < n:
        return False
    tmp = out / f"rec-{seed}.jsonl.gz.tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        for g in range(n):
            fh.write(json.dumps(records[g]) + "\n")
    os.replace(tmp, done)
    part.unlink()
    return True


def play_main(args) -> None:
    from multiprocessing import Pool
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    todo, seeds = [], []
    for k in range(args.shards[0], args.shards[1]):
        seed = args.base + args.stride * k
        if (out / f"rec-{seed}.jsonl.gz").exists():
            continue
        if _finish(out, seed, args.per_shard):
            continue
        have = {r["g"] for r in _read_part(out / f"rec-{seed}.part.jsonl")}
        seeds.append(seed)
        todo += [(seed, g, args.deck, args.opponent, args.spec) for g in range(args.per_shard) if g not in have]
    print(json.dumps({"spec": args.spec, "deck": args.deck, "opponent": args.opponent, "base": args.base,
                      "stride": args.stride, "shards": args.shards, "per_shard": args.per_shard, "open_shards": seeds, "games_to_play": len(todo),
                      "workers": args.workers}), flush=True)
    if not todo:
        return
    left = {s: sum(1 for j in todo if j[0] == s) for s in seeds}
    handles = {s: open(out / f"rec-{s}.part.jsonl", "a", encoding="utf-8") for s in seeds}
    t0, cpu = time.time(), 0.0
    try:
        with Pool(args.workers) as pool:
            for n, (seed, record) in enumerate(pool.imap_unordered(_play, todo, chunksize=1), 1):
                fh = handles[seed]
                fh.write(json.dumps(record) + "\n")
                fh.flush()
                cpu += record["cpu"]
                left[seed] -= 1
                if left[seed] == 0:
                    fh.close()
                    _finish(out, seed, args.per_shard)
                if n % args.every == 0 or n == len(todo):
                    wall = time.time() - t0
                    print(json.dumps({"games": n, "of": len(todo), "wall_s": round(wall), "cpu_s_per_game":
                                      round(cpu / n, 2), "games_per_hour": round(3600 * n / max(wall, 1e-9))}),
                          flush=True)
    finally:
        for fh in handles.values():
            if not fh.closed:
                fh.close()


def _records(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def _stable(record) -> str:
    return json.dumps({k: v for k, v in record.items() if k not in VOLATILE}, sort_keys=True)


def merge_main(args) -> None:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    games: dict = {}                                 # seed -> {g: record}
    seen = dup = 0
    mismatches = []
    for root in args.inputs:
        for path in sorted(glob.glob(os.path.join(root, "rec-*.jsonl.gz"))):
            for r in _records(path):
                seen += 1
                shard = games.setdefault(r["seed"] // 100003 if "seed" in r else None, {})
                key = r["g"]
                if key in shard:
                    dup += 1
                    if _stable(shard[key]) != _stable(r):
                        mismatches.append({"deal_seed": r["seed"], "g": key, "file": path})
                    continue
                shard[key] = r
    written = {}
    for seed, shard in sorted(games.items()):
        target = out / f"rec-{seed}.jsonl.gz"
        tmp = out / f"rec-{seed}.jsonl.gz.tmp"
        with gzip.open(tmp, "wt", encoding="utf-8") as fh:
            for g in sorted(shard):
                fh.write(json.dumps(shard[g]) + "\n")
        os.replace(tmp, target)
        written[seed] = len(shard)
    print(json.dumps({"records_read": seen, "duplicates": dup, "mismatched_duplicates": len(mismatches),
                      "mismatches": mismatches[:20], "shards": len(written), "games": sum(written.values()),
                      "per_shard": written}, indent=1))


def check_main(args) -> None:
    rows = []
    for path in sorted(glob.glob(os.path.join(args.dir, "rec-*.jsonl.gz"))):
        rs = list(_records(path))
        gs = [r["g"] for r in rs]
        rows.append({"file": os.path.basename(path), "games": len(rs), "g_unique": len(set(gs)),
                     "g_range": [min(gs), max(gs)] if gs else None,
                     "first_seat_wins": sum(r["winner"] == r["first"] for r in rs),
                     "draws": sum(r["winner"] not in (0, 1) for r in rs),
                     "cpu_s_per_game": round(sum(r.get("cpu", 0.0) for r in rs) / max(len(rs), 1), 2),
                     "actions_mean": round(sum(len(r["actions"]) for r in rs) / max(len(rs), 1), 1)})
    parts = sorted(os.path.basename(p) for p in glob.glob(os.path.join(args.dir, "rec-*.part.jsonl")))
    print(json.dumps({"shards": rows, "games": sum(r["games"] for r in rows), "open_parts": parts}, indent=1))


_EVAL = {}


def _linear(state, player: int) -> float:
    from svsim.learn.model import SCALE
    from svsim.learn.netdata import _search
    from svsim.tools.arena import make_agent
    weights = _EVAL.get("w")
    if weights is None:
        weights = _EVAL["w"] = _search(make_agent(_EVAL.get("spec", SPEC), 0)).weights
    return weights.score(state, player, False) / SCALE


def encode_game(record) -> list:
    """[(cards, tokens, globals, labels dict, {card id: CardDef in the position})] for every turn end of the game (module docstring)."""
    from svsim.learn import tokens as T
    from svsim.learn.netdata import ENDED, rows
    out = []
    for i, (phase, player, state, result) in rows(record, index=True):
        if phase != ENDED:
            continue
        cids, toks, glob_ = T.encode(state, player)
        defs = {}
        for p in state.players:
            for c in p.hand + p.field + p.leader_area + p.deck_view():
                defs[c.defn.card_id] = c.defn
        out.append((cids, toks, glob_, {"result": result, "linear": _linear(state, player), "i": i, "turn": state.turn,
                                  "player": player}, defs))
    return out


def _encode_shard(job):
    import numpy as np
    from svsim.learn import tokens as T
    path, target, spec = job
    _EVAL["spec"] = spec
    cids, toks, offs, globs = [], [], [0], []
    lab = {k: [] for k in ("result", "linear", "seed", "g", "i", "turn", "player", "actions")}
    cards = {}
    t0 = time.process_time()
    games = 0
    for record in _records(path):
        games += 1
        deal = record["seed"]
        for c, t, g, d, defs in encode_game(record):
            cards.update(defs)
            cids.append(c)
            toks.append(t)
            offs.append(offs[-1] + len(t))
            globs.append(g)
            for k in ("result", "linear", "i", "turn", "player"):
                lab[k].append(d[k])
            lab["seed"].append(deal // 100003)
            lab["g"].append(record["g"])
            lab["actions"].append(len(record["actions"]))
    arrays = {"tokens": np.concatenate(toks) if toks else np.zeros((0, len(T.TOKEN)), np.int16),
              "cards": np.concatenate(cids) if cids else np.zeros(0, np.int32),
              "offsets": np.asarray(offs, np.int64), "globals": np.stack(globs).astype(np.float32),
              "result": np.asarray(lab["result"], np.float32), "linear": np.asarray(lab["linear"], np.float32)}
    for k in ("seed", "g", "i", "turn", "player", "actions"):
        arrays[k] = np.asarray(lab[k], np.int32)
    ids = sorted(cards)
    arrays["card_id"] = np.asarray(ids, np.int32)            # the static rows of the cards in this shard's tokens
    arrays["static"] = np.stack([T.static(cards[c]) for c in ids]) if ids else np.zeros((0, len(T.static_names())))
    tmp = str(target) + ".tmp.npz"
    np.savez_compressed(tmp, **arrays)
    os.replace(tmp, target)
    return str(target), games, len(globs), round(time.process_time() - t0, 1)


def encode_main(args) -> None:
    from multiprocessing import Pool
    import numpy as np
    from svsim.learn import tokens as T
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = []
    for path in sorted(glob.glob(os.path.join(args.records, "rec-*.jsonl.gz"))):
        seed = os.path.basename(path)[len("rec-"):-len(".jsonl.gz")]
        target = out / f"tok-{seed}.npz"
        if not target.exists():
            jobs.append((path, target, args.spec))
    print(json.dumps({"shards_to_encode": len(jobs)}), flush=True)
    with Pool(args.workers) as pool:
        for target, games, n, cpu in pool.imap_unordered(_encode_shard, jobs):
            print(json.dumps({"file": os.path.basename(target), "games": games, "positions": n, "cpu_s": cpu}),
                  flush=True)
    static = {}
    for path in sorted(glob.glob(str(out / "tok-*.npz"))):
        with np.load(path) as z:
            for cid, row in zip(z["card_id"], z["static"]):
                if int(cid) in static and not np.array_equal(static[int(cid)], row):
                    raise SystemExit(f"card {cid}: static rows differ between shards ({path})")
                static[int(cid)] = row
    card_ids = np.asarray(sorted(static), np.int32)
    rows = np.stack([static[int(c)] for c in card_ids])
    np.savez_compressed(out / "cards.npz", card_id=card_ids, static=rows,
                        static_names=np.asarray(T.static_names()), token_names=np.asarray(T.TOKEN),
                        global_names=np.asarray(T.GLOBALS), zones=np.asarray(T.ZONES))
    print(json.dumps({"cards": len(card_ids), "static_width": int(rows.shape[1])}), flush=True)


def main() -> None:
    from svsim.ui.session import DECKS
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("play")
    p.add_argument("--base", type=int, required=True, help="netdata seed of shard 0 (from the analysis line)")
    p.add_argument("--shards", type=int, nargs=2, required=True, metavar=("FROM", "TO"),
                   help="shards FROM .. TO - 1")
    p.add_argument("--stride", type=int, default=2, help="shard k is seed BASE + STRIDE * k")
    p.add_argument("--per-shard", type=int, default=1000)
    p.add_argument("--deck", default="ramp-t", choices=sorted(DECKS))
    p.add_argument("--opponent", default="ramp-t", choices=sorted(DECKS))
    p.add_argument("--spec", default=SPEC)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--every", type=int, default=50, help="print progress every this many games")
    p.add_argument("--out", required=True)
    e = sub.add_parser("encode")
    e.add_argument("--records", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--spec", default=SPEC, help="the agent whose turn-end model gives the 'linear' label")
    e.add_argument("--workers", type=int, default=4)
    m = sub.add_parser("merge")
    m.add_argument("--inputs", nargs="+", required=True)
    m.add_argument("--out", required=True)
    c = sub.add_parser("check")
    c.add_argument("dir")
    args = parser.parse_args()
    {"play": play_main, "encode": encode_main, "merge": merge_main, "check": check_main}[args.cmd](args)


if __name__ == "__main__":
    main()
