"""Mid-turn rows for the value net's mid-turn branch (the architecture thread 2026-10-18 07:53Z).

Under +neteot, learn.setnet.SetNetEnded plays a leaf inside the scored player's own turn to its turn end
(after_end_of_turn, on a copy) and scores that with a net trained on turn ends only. The cards still playable, the
play points left and the attacks not made all count as wasted. A net with the mid-turn flag (SetNet flag: rho reads
one more global, 1 inside the mover's turn, 0 at a turn end) is trained on both kinds of position, and the agent
option +netmid scores such a leaf as it is by the flag-1 branch.

A mid-turn row is a decision of the move prior's data (learn.setpolicy.decisions: a searched main-phase decision
with two distinct moves or more, the mover to act, the turn not ended), encoded by learn.tokens.encode from the
mover's view, labelled with the game's result from the mover's view (1 a win, 0 a loss, 0.5 a draw). The files
have the turn-end token files' layout (learn.scaledata encode: tokens, cards, offsets, globals, result, seed, g,
turn, player, card_id, static), so learn.setnet.Data reads them. "i" is the decision's action index and "start"
whether it is its turn's first decision. "linear" is 0: no turn-end model scores a mid-turn position.

phase_split loads turn-end and mid-turn files into one learn.setnet.Data per part (training / validation by game,
seed·100003 + g a multiple of `every` in validation), with the flag appended to the globals. It fills arrays
allocated once, file by file, so the whole data never sits in memory next to its parts. A mid-turn file's rows
can be thinned to a rate (each row kept with probability `mid_rate`, from a generator seeded by (seed, shard)).

    python -m svsim.learn.midrows encode --records DIR --out DIR [--workers 4] [--inputs v1|v2a]
    python -m svsim.learn.midrows encode-hand --kind end|mid --records DIR --out DIR   # hand-<tok|mid>-<seed>.npz
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import time
from pathlib import Path

import numpy as np


def mid_rows(record: dict, inputs: str = "v1"):
    """[(cards, tokens, globals, labels, {card id: CardDef})] at every decision of learn.setpolicy.decisions, in the
    learn.tokens input version `inputs` (v1, or v2a: v1's columns and V2_EXTRA)."""
    from svsim.learn import tokens as T
    from svsim.learn.setpolicy import decisions
    winner = record.get("winner")
    out = []
    for i, state, *_rest, start in decisions(record):
        me = state.active
        cids, toks, glob_ = T.encode(state, me, inputs)
        defs = {}
        for p in state.players:
            for c in p.hand + p.field + p.leader_area + p.deck_view():
                defs[c.defn.card_id] = c.defn
        result = 0.5 if winner is None else float(winner == me)
        out.append((cids, toks, glob_, {"result": result, "i": i, "turn": state.turn, "player": me,
                                        "start": bool(start)}, defs))
    return out


def _encode_shard(job):
    from svsim.learn import tokens as T
    path, target = job[:2]
    inputs = job[2] if len(job) > 2 else "v1"
    t0 = time.process_time()
    cids, toks, offs, globs = [], [], [0], []
    lab = {k: [] for k in ("result", "seed", "g", "i", "turn", "player", "start")}
    cards = {}
    games = 0
    with gzip.open(path, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            games += 1
            for c, t, g, d, defs in mid_rows(record, inputs):
                cards.update(defs)
                cids.append(c)
                toks.append(t)
                offs.append(offs[-1] + len(t))
                globs.append(g)
                for k in ("result", "i", "turn", "player", "start"):
                    lab[k].append(d[k])
                lab["seed"].append(int(record["seed"]) // 100003)
                lab["g"].append(record["g"])
    arrays = {"tokens": np.concatenate(toks) if toks else np.zeros((0, len(T.token_names(inputs))), np.int16),
              "cards": np.concatenate(cids) if cids else np.zeros(0, np.int32),
              "offsets": np.asarray(offs, np.int64),
              "globals": np.stack(globs).astype(np.float32) if globs else np.zeros((0, len(T.global_names(inputs))),
                                                                                    np.float32),
              "result": np.asarray(lab["result"], np.float32), "linear": np.zeros(len(globs), np.float32),
              "start": np.asarray(lab["start"], bool)}
    if inputs != "v1":                         # as learn.scaledata's v2a files: the file says which (v1: no mark)
        arrays["inputs"] = np.array(inputs)
    for k in ("seed", "g", "i", "turn", "player"):
        arrays[k] = np.asarray(lab[k], np.int32)
    ids = sorted(cards)
    arrays["card_id"] = np.asarray(ids, np.int32)
    arrays["static"] = np.stack([T.static(cards[c]) for c in ids]) if ids else np.zeros((0, len(T.static_names())))
    tmp = str(target) + ".tmp.npz"
    np.savez_compressed(tmp, **arrays)
    os.replace(tmp, target)
    return str(target), games, len(globs), round(time.process_time() - t0, 1)


def encode_main(args) -> None:
    from multiprocessing import Pool
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = []
    for path in sorted(glob.glob(os.path.join(args.records, "rec-*.jsonl.gz"))):
        seed = os.path.basename(path)[len("rec-"):-len(".jsonl.gz")]
        target = out / f"mid-{seed}.npz"
        if not target.exists():
            jobs.append((path, target, args.inputs))
    print(json.dumps({"shards_to_encode": len(jobs)}), flush=True)
    with Pool(args.workers) as pool:
        for target, games, n, cpu in pool.imap_unordered(_encode_shard, jobs):
            print(json.dumps({"file": os.path.basename(target), "games": games, "positions": n, "cpu_s": cpu}),
                  flush=True)


# --- the opponent's hand, card by card (a diagnostic: SetNet ophand; the architecture thread 2026-10-18 17:47Z) ---

def hand_rows(record: dict, kind: str) -> list:
    """[(g, i, cards, tokens)] per position of a tok- file (kind "end": learn.scaledata's turn ends, the player who
    ended the turn as "me") or of a mid- file (kind "mid": this module's decisions, the mover as "me"), in the files'
    order: the tokens (learn.tokens._live, zone setnet.OP_HAND) of the opponent's real hand there."""
    from svsim.learn import tokens as T
    from svsim.learn.setnet import OP_HAND
    out = []

    def of(state, me, i):
        rows = [T._live(state, c, OP_HAND) for c in state.players[1 - me].hand]
        table = np.asarray(rows, dtype=np.int64).reshape(-1, len(T.TOKEN) + 1)
        out.append((record["g"], i, table[:, 0].astype(np.int32),
                    np.clip(table[:, 1:], -32768, 32767).astype(np.int16)))
    if kind == "end":
        from svsim.learn.netdata import ENDED, rows
        for i, (phase, player, state, _result) in rows(record, index=True):
            if phase == ENDED:
                of(state, player, i)
    else:
        from svsim.learn.setpolicy import decisions
        for i, state, *_ in decisions(record):
            of(state, state.active, i)
    return out


def _encode_hand_shard(job):
    from svsim.learn import tokens as T
    path, target, kind = job
    t0 = time.process_time()
    cids, toks, offs, gs, iis = [], [], [0], [], []
    games = 0
    with gzip.open(path, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            games += 1
            for g, i, c, tk in hand_rows(json.loads(line), kind):
                cids.append(c)
                toks.append(tk)
                offs.append(offs[-1] + len(tk))
                gs.append(g)
                iis.append(i)
    arrays = {"tokens": np.concatenate(toks) if toks else np.zeros((0, len(T.TOKEN)), np.int16),
              "cards": np.concatenate(cids) if cids else np.zeros(0, np.int32),
              "offsets": np.asarray(offs, np.int64), "g": np.asarray(gs, np.int32), "i": np.asarray(iis, np.int32)}
    tmp = str(target) + ".tmp.npz"
    np.savez_compressed(tmp, **arrays)
    os.replace(tmp, target)
    return str(target), games, len(gs), round(time.process_time() - t0, 1)


def encode_hand_main(args) -> None:
    from multiprocessing import Pool
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    prefix = {"end": "tok", "mid": "mid"}[args.kind]
    jobs = []
    for path in sorted(glob.glob(os.path.join(args.records, "rec-*.jsonl.gz"))):
        seed = os.path.basename(path)[len("rec-"):-len(".jsonl.gz")]
        target = out / f"hand-{prefix}-{seed}.npz"
        if not target.exists():
            jobs.append((path, target, args.kind))
    print(json.dumps({"shards_to_encode": len(jobs)}), flush=True)
    with Pool(args.workers) as pool:
        for target, games, n, cpu in pool.imap_unordered(_encode_hand_shard, jobs):
            print(json.dumps({"file": os.path.basename(target), "games": games, "positions": n, "cpu_s": cpu}),
                  flush=True)


# --- loading: turn-end and mid-turn rows, the flag appended --------------------------------------------------------

def _plan(end_files, mid_files, every: int, mid_rate: float, seed: int):
    """[(path, flag, rows kept, rows in validation)] per file, from its labels only."""
    plan = []
    for flag, files in ((0.0, end_files), (1.0, mid_files)):
        for f in files:
            with np.load(f) as z:
                n = len(z["result"])
                games = z["seed"].astype(np.int64) * 100003 + z["g"].astype(np.int64)
                shard = int(z["seed"][0]) if n else 0
            keep = np.ones(n, bool)
            if flag and mid_rate < 1.0:
                keep = np.random.default_rng([seed, shard]).random(n) < mid_rate
            valid = games % every == 0 if every else np.zeros(n, bool)
            plan.append((f, flag, keep, valid))
    return plan


def _assemble(plan, cards_npz, part: str, hand_dir=None):
    """One learn.setnet.Data of the plan's rows of `part` ("train": kept and not validation, "valid": kept and
    validation, "all": kept), arrays allocated once and filled file by file."""
    from svsim.learn.setnet import Data, global_scale, inputs_of
    c = np.load(cards_npz)
    out = object.__new__(Data)
    out.card_ids = c["card_id"].astype(np.int64)
    out.static = c["static"].astype(np.float32)
    out.static_names = [str(s) for s in c["static_names"]] if "static_names" in c.files else []
    out.inputs = None

    def rows_of(keep, valid):
        return keep & ~valid if part == "train" else (keep & valid if part == "valid" else keep)

    n_pos = n_tok = 0
    width = n_glob = None
    for f, _flag, keep, valid in plan:
        sel = rows_of(keep, valid)
        with np.load(f) as z:
            lens = np.diff(z["offsets"])
            inputs = inputs_of(z["tokens"].shape[1], z["globals"].shape[1],
                               str(z["inputs"]) if "inputs" in z.files else None)
            if width is None:
                width, n_glob, out.inputs = z["tokens"].shape[1], z["globals"].shape[1], inputs
                if inputs not in ("v1", "v2a"):
                    raise ValueError("the mid-turn flag is for v1 or v2a inputs")
            elif inputs != out.inputs:
                raise ValueError(f"{f}: {inputs} inputs among {out.inputs}")
        n_pos += int(sel.sum())
        n_tok += int(lens[sel].sum())
    out.tokens = np.zeros((n_tok, width), np.int16)
    out.cards = np.zeros(n_tok, np.int32)
    out.offsets = np.zeros(n_pos + 1, np.int64)
    out.globals = np.zeros((n_pos, n_glob + 1), np.float32)
    for k, dt in (("result", np.float32), ("linear", np.float32), ("seed", np.int32), ("g", np.int32),
                  ("turn", np.int32)):
        setattr(out, k, np.zeros(n_pos, dt))
    out.flag = np.zeros(n_pos, np.float32)
    out.inputs = out.inputs or "v1"
    scale = global_scale(out.inputs)
    hands = []                                       # (hand file, rows) per plan entry, when hand_dir is given
    if hand_dir is not None:
        if out.inputs != "v1":
            raise ValueError("the opponent-hand zone is for v1 inputs")
        n_hand = 0
        for f, _flag, keep, valid in plan:
            hf = Path(hand_dir) / f"hand-{Path(f).name}"
            sel = rows_of(keep, valid)
            with np.load(hf) as hz, np.load(f) as z:
                if not (np.array_equal(hz["g"], z["g"]) and np.array_equal(hz["i"], z["i"])):
                    raise ValueError(f"{hf}: its positions are not {f}'s")
                n_hand += int(np.diff(hz["offsets"])[sel].sum())
            hands.append(hf)
        out.hand_tokens = np.zeros((n_hand, width), np.int16)
        out.hand_cards = np.zeros(n_hand, np.int32)
        out.hand_offsets = np.zeros(n_pos + 1, np.int64)
    p = t = h = 0
    for j, (f, flag, keep, valid) in enumerate(plan):
        sel = np.flatnonzero(rows_of(keep, valid))
        if not len(sel):
            continue
        if hands:
            with np.load(hands[j]) as hz:
                offs = hz["offsets"].astype(np.int64)
                starts, lens = offs[sel], offs[sel + 1] - offs[sel]
                first = np.concatenate([[0], np.cumsum(lens)[:-1]]).astype(np.int64)
                take = np.repeat(starts - first, lens) + np.arange(int(lens.sum()), dtype=np.int64)
                k = int(lens.sum())
                out.hand_tokens[h:h + k] = hz["tokens"][take]
                out.hand_cards[h:h + k] = np.searchsorted(out.card_ids, hz["cards"][take].astype(np.int64))
                out.hand_offsets[p + 1:p + len(sel) + 1] = h + np.cumsum(lens)
                h += k
        with np.load(f) as z:
            offs = z["offsets"].astype(np.int64)
            starts, lens = offs[sel], offs[sel + 1] - offs[sel]
            first = np.concatenate([[0], np.cumsum(lens)[:-1]]).astype(np.int64)
            take = np.repeat(starts - first, lens) + np.arange(int(lens.sum()), dtype=np.int64)
            m = len(sel)
            k = int(lens.sum())
            out.tokens[t:t + k] = z["tokens"][take]
            out.cards[t:t + k] = np.searchsorted(out.card_ids, z["cards"][take].astype(np.int64)).astype(np.int32)
            out.offsets[p + 1:p + m + 1] = t + np.cumsum(lens)
            out.globals[p:p + m, :n_glob] = z["globals"][sel] / scale
            out.globals[p:p + m, n_glob] = flag
            for key in ("result", "linear", "seed", "g", "turn"):
                getattr(out, key)[p:p + m] = z[key][sel]
            out.flag[p:p + m] = flag
        p += m
        t += k
    out.n = n_pos
    return out


def phase_split(end_files, mid_files, cards_npz, every: int = 20, mid_rate: float = 1.0, seed: int = 0,
                hand_dir=None):
    """(training, validation) learn.setnet.Data over turn-end files (flag 0) and mid-turn files (flag 1). With
    `hand_dir`, each file's hand-<name> there (encode-hand) adds the opponent's hand tokens (an ophand net)."""
    plan = _plan(end_files, mid_files, every, mid_rate, seed)
    return (_assemble(plan, cards_npz, "train", hand_dir), _assemble(plan, cards_npz, "valid", hand_dir))


def phase_data(end_files, mid_files, cards_npz, hand_dir=None):
    """Every row of the files as one learn.setnet.Data, the flag appended (a holdout)."""
    return _assemble(_plan(end_files, mid_files, 0, 1.0, 0), cards_npz, "all", hand_dir)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("encode")
    e.add_argument("--records", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--workers", type=int, default=4)
    e.add_argument("--inputs", choices=("v1", "v2a"), default="v1", help="v2a: learn.tokens' v2a (a marked file)")
    h = sub.add_parser("encode-hand")
    h.add_argument("--kind", choices=("end", "mid"), required=True, help="end: beside tok- files; mid: beside mid-")
    h.add_argument("--records", required=True)
    h.add_argument("--out", required=True)
    h.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    {"encode": encode_main, "encode-hand": encode_hand_main}[args.cmd](args)


if __name__ == "__main__":
    main()
