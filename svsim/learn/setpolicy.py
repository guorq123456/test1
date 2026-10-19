"""A move prior over the scaling test's card tokens: which moves the search spends its visits on (the architecture
thread 2026-10-17 11:37Z, step 1: data, network, offline report; nothing in the search uses it yet).

The data is the recorded search: at every decision of a self-play record (learn.scaledata play) the root's visits
per legal move ("visits", learn.netdata._thought). Moves that are the same to the search (search.mcts.action_key:
two copies of a card in hand, say) share one child and so one visit count; they are one move here. The target is
the visit distribution over these distinct moves (tau = 1), or visits ** (1 / tau) normalized (`--tau`;
0.5: the visits squared, a sharper target).

The position is learn.tokens.encode(state, me) of the player to act (the same view as the value net's: their hand,
both fields and leader areas, their deck and the opponent's unseen pool as counts). It goes through the value net's
trunk (learn.setnet: phi per token, sums per zone, rho's two hidden layers), which gives a position vector h and a
vector phi(x_t) per token. A move is
- its kind (KINDS) and its target's kind (TARGET_KINDS), one-hot;
- a few numbers (EXTRAS): cost, play points after it, for an attack whether it kills / dies / hits the leader,
  how many targets, which mode, how many cards it fuses;
- phi of the token of the card that acts (the card played, the attacker, the follower evolved, ...) and of the
  token of its first target, zero when there is none.
So a card enters only through its attribute token, never by its id, and no card has a score of its own.

    score(move) = w . relu(h A + m M + b),    prior = softmax of the scores over the distinct legal moves

Cross entropy against the visit distribution, Adam, early stopping on a game-split validation part, as learn.setnet.
The trunk starts from a value net's weights; `freeze` keeps it (only A, M, b, w are fitted), otherwise it is fitted
too. Plain numpy, saved as .npz without pickle.

    python -m svsim.learn.setpolicy encode --records DIR --out DIR --workers 4
    python -m svsim.learn.setpolicy fit --data DIR --shards ... --init VALUE_NET.npz [--freeze] --out prior.npz
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import time
from pathlib import Path

import numpy as np

from svsim.learn import tokens as T
from svsim.learn.setnet import NZ, _act, _dact, _flush, _segsum, _spans, dynamic, global_scale

KINDS = ("play", "attack", "evolve", "super", "end", "engage", "fuse", "bonus", "other")
TARGET_KINDS = ("none", "enemy_leader", "own_leader", "enemy_card", "own_card", "hand_card")
EXTRAS = ("cost", "pp_after", "kills", "dies", "face", "n_targets", "mode", "n_cards")
TRUNK = ("W1s", "W1d", "b1", "W2", "b2", "V1", "c1", "V2", "c2")
HEAD = ("A", "M", "bh", "w")


# --- a decision as arrays ----------------------------------------------------------------------------------------

def _kind(action) -> int:
    from svsim.core.actions import Attack, EndTurn, Engage, Evolve, Fuse, PlayCard, UseBonusPP
    if isinstance(action, PlayCard):
        return 0
    if isinstance(action, Attack):
        return 1
    if isinstance(action, Evolve):
        return 3 if action.super_ else 2
    if isinstance(action, EndTurn):
        return 4
    if isinstance(action, Engage):
        return 5
    if isinstance(action, Fuse):
        return 6
    if isinstance(action, UseBonusPP):
        return 7
    return 8


def rows_of(state, me: int) -> dict:
    """uid -> the row of its token in T.encode(state, me) (live tokens only; pooled cards have no uid row)."""
    p, o = state.players[me], state.players[1 - me]
    out, r = {}, 0
    for zone in (p.hand, p.field, p.leader_area):
        for c in zone:
            out[c.uid] = r
            r += 1
    r += len({c.defn.card_id for c in p.deck_view()})
    for zone in (o.field, o.leader_area):
        for c in zone:
            out[c.uid] = r
            r += 1
    return out


def distinct(state, legal) -> tuple[list, list]:
    """(one representative action per search.mcts.action_key, in first-seen order; each legal move's group)."""
    from svsim.search.mcts import _locator, action_key
    where = _locator(state, state.active)
    keys: dict = {}
    reps, group = [], []
    for a in legal:
        k = action_key(state, a, where)
        if k not in keys:
            keys[k] = len(reps)
            reps.append(a)
        group.append(keys[k])
    return reps, group


def move_arrays(state, actions, rows: dict):
    """(kind int8 [M], target kind int8 [M], source row int32 [M], target row int32 [M], extras float32 [M, E])."""
    from svsim.core.actions import Attack, Fuse, PlayCard
    from svsim.core.engine import leader_of
    me = state.active
    p = state.players[me]
    hand = {c.uid for c in p.hand}
    n = len(actions)
    kind, tkind = np.zeros(n, np.int8), np.zeros(n, np.int8)
    src, tgt = np.full(n, -1, np.int32), np.full(n, -1, np.int32)
    extras = np.zeros((n, len(EXTRAS)), np.float32)
    for j, a in enumerate(actions):
        kind[j] = _kind(a)
        uid = getattr(a, "uid", None)
        if uid is None:
            uid = getattr(a, "attacker", None)
        card = None
        if uid is not None:
            src[j] = rows.get(uid, -1)
            card = state.in_hand(me, uid) or state.in_play(uid)
        targets = tuple(getattr(a, "targets", ()) or ())
        t = a.target if isinstance(a, Attack) else (targets[0] if targets else None)
        if isinstance(a, Fuse) and a.cards:
            t = a.cards[0]
        tcard = None
        if t is not None:
            side = leader_of(t)
            if side is not None:
                tkind[j] = 2 if side == me else 1
            elif t in hand:
                tkind[j] = 5
                tgt[j] = rows.get(t, -1)
            else:
                tcard = state.in_play(t)
                if tcard is not None:
                    tkind[j] = 4 if tcard.owner == me else 3
                    tgt[j] = rows.get(t, -1)
        cost = card.cost if isinstance(a, PlayCard) and card is not None else 0
        e = extras[j]
        e[0], e[1] = cost / 10.0, (p.pp - cost) / 10.0
        if isinstance(a, Attack) and card is not None:
            if tcard is not None:
                e[2] = float(card.atk >= max(tcard.life, 0))
                e[3] = float(tcard.atk >= card.life)
            elif tkind[j] == 1:
                e[4] = card.atk / 10.0
        e[5] = len(targets) / 3.0
        modes = getattr(a, "modes", ()) or ()
        e[6] = (modes[0] + 1) / 3.0 if modes else 0.0
        e[7] = len(getattr(a, "cards", ()) or ()) / 3.0
    return kind, tkind, src, tgt, extras


def decisions(record: dict, skip_first: int = 0):
    """(step index, state (live, advanced after the yield), legal moves, their distinct representatives, each legal
    move's group, the visit distribution over the representatives, the turn's first decision or not) at each
    searched decision with two distinct moves or more."""
    from svsim.core.engine import legal_actions
    from svsim.core.enums import Phase
    from svsim.tools import records as R
    thoughts = record.get("search") or []
    last_turn = None
    for i, (state, action) in enumerate(R.steps(record)):
        t = thoughts[i] if i < len(thoughts) else None
        start = state.phase == Phase.MAIN and state.turn != last_turn
        if state.phase == Phase.MAIN:
            last_turn = state.turn
        if t is None or state.phase != Phase.MAIN:
            continue
        legal = legal_actions(state)
        if len(legal) != len(t["visits"]):
            continue
        reps, group = distinct(state, legal)
        if len(reps) < 2:
            continue
        v = np.zeros(len(reps))
        for j, g in enumerate(group):
            v[g] = t["visits"][j]                        # the same child: the same count
        if v.sum() <= 0:
            continue
        yield i, state, legal, reps, group, v / v.sum(), start


def _encode_shard(job):
    path, target = job[:2]
    deck = job[2] if len(job) > 2 else None          # one side's decisions only (the mover's deck), or both
    import gzip
    t0 = time.process_time()
    cards, toks, offs, glob, meta = [], [], [0], [], {k: [] for k in ("g", "step", "turn", "start", "n_legal")}
    mk, mt, ms, mg, mx, mp, moff = [], [], [], [], [], [], [0]
    with gzip.open(path, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            for i, state, legal, reps, group, pi, start in decisions(rec):
                me = state.active
                if deck is not None and state.players[me].deck_name != deck:
                    continue
                c, tk, gl = T.encode(state, me)
                kind, tkind, src, tgt, extras = move_arrays(state, reps, rows_of(state, me))
                cards.append(c), toks.append(tk), glob.append(gl)
                offs.append(offs[-1] + len(c))
                mk.append(kind), mt.append(tkind), ms.append(src), mg.append(tgt), mx.append(extras)
                mp.append(pi.astype(np.float32))
                moff.append(moff[-1] + len(reps))
                for k, val in (("g", rec["g"]), ("step", i), ("turn", state.turn), ("start", int(start)),
                               ("n_legal", len(legal))):
                    meta[k].append(val)
    seed = int(os.path.basename(path)[len("rec-"):-len(".jsonl.gz")])
    np.savez_compressed(
        target, cards=np.concatenate(cards).astype(np.int32), tokens=np.concatenate(toks),
        offsets=np.asarray(offs, np.int64), globals=np.stack(glob).astype(np.float32),
        kind=np.concatenate(mk), tkind=np.concatenate(mt), src=np.concatenate(ms), tgt=np.concatenate(mg),
        extras=np.concatenate(mx), pi=np.concatenate(mp), moff=np.asarray(moff, np.int64),
        seed=np.full(len(offs) - 1, seed, np.int64), **{k: np.asarray(v, np.int32) for k, v in meta.items()})
    return str(target), len(offs) - 1, int(moff[-1]), round(time.process_time() - t0, 1)


def encode_main(args) -> None:
    from multiprocessing import Pool
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = []
    for path in sorted(glob.glob(os.path.join(args.records, "rec-*.jsonl.gz"))):
        seed = os.path.basename(path)[len("rec-"):-len(".jsonl.gz")]
        target = out / f"dec-{seed}.npz"
        if not target.exists():
            jobs.append((path, target, args.deck))
    print(json.dumps({"shards_to_encode": len(jobs)}), flush=True)
    with Pool(args.workers) as pool:
        for target, n, m, cpu in pool.imap_unordered(_encode_shard, jobs):
            print(json.dumps({"file": os.path.basename(target), "decisions": n, "moves": m, "cpu_s": cpu}),
                  flush=True)


# --- data --------------------------------------------------------------------------------------------------------

class Decisions:
    """Decisions from dec-*.npz files (encode), with a static table (a token folder's cards.npz, learn.scaledata)."""

    def __init__(self, files, cards_npz):
        parts = [np.load(f) for f in files]
        c = np.load(cards_npz)
        self.card_ids = c["card_id"].astype(np.int64)
        self.static = c["static"].astype(np.float32)
        missing = set(np.unique(np.concatenate([z["cards"] for z in parts])).tolist()) - set(self.card_ids.tolist())
        if missing:
            raise ValueError(f"cards without a static row in {cards_npz}: {sorted(missing)[:10]}")
        self.tokens = np.concatenate([z["tokens"] for z in parts])
        self.cards = np.concatenate([np.searchsorted(self.card_ids, z["cards"].astype(np.int64)).astype(np.int32)
                                     for z in parts])
        self.globals = np.concatenate([z["globals"] for z in parts]) / global_scale("v1")
        o, mo, base, mbase = [np.zeros(1, np.int64)], [np.zeros(1, np.int64)], 0, 0
        for z in parts:
            o.append(z["offsets"][1:] + base)
            mo.append(z["moff"][1:] + mbase)
            base += int(z["offsets"][-1])
            mbase += int(z["moff"][-1])
        self.offsets, self.moff = np.concatenate(o), np.concatenate(mo)
        for k in ("kind", "tkind", "src", "tgt", "extras", "pi"):
            setattr(self, k, np.concatenate([z[k] for z in parts]))
        for k in ("seed", "g", "step", "turn", "start", "n_legal"):
            setattr(self, k, np.concatenate([z[k] for z in parts]))
        self.n = len(self.offsets) - 1

    def games(self) -> np.ndarray:
        return self.seed.astype(np.int64) * 100003 + self.g.astype(np.int64)

    @classmethod
    def split(cls, files, cards_npz, every: int = 20) -> tuple["Decisions", "Decisions"]:
        """(training part, validation part: the games whose key seed * 100003 + g is a multiple of `every`), read
        one file at a time into arrays allocated once, so neither the whole data nor a second copy of a part is
        ever in memory (the same arrays as subset() of the whole by that mask)."""
        sizes = []
        for f in files:                                   # pass 1: what each part takes from each file
            with np.load(f) as z:
                v = (z["seed"].astype(np.int64) * 100003 + z["g"].astype(np.int64)) % every == 0
                tl, ml = np.diff(z["offsets"]), np.diff(z["moff"])
                sizes.append([(int(m.sum()), int(tl[m].sum()), int(ml[m].sum())) for m in (~v, v)])
        out = []
        for side in (0, 1):
            n = sum(x[side][0] for x in sizes)
            t = sum(x[side][1] for x in sizes)
            mv = sum(x[side][2] for x in sizes)
            d = object.__new__(cls)
            d.n, d.offsets, d.moff = n, np.zeros(n + 1, np.int64), np.zeros(n + 1, np.int64)
            d._alloc = (n, t, mv)
            out.append(d)
        pos = [[0, 0, 0], [0, 0, 0]]
        for f in files:                                   # pass 2: fill
            part = cls([f], cards_npz)
            v = part.games() % every == 0
            for side, mask in ((0, ~v), (1, v)):
                sub = part.subset(mask)
                d, (i, ti, mi) = out[side], pos[side]
                if not hasattr(d, "tokens"):
                    n, t, mv = d._alloc
                    d.card_ids, d.static = part.card_ids, part.static
                    d.tokens = np.empty((t,) + sub.tokens.shape[1:], sub.tokens.dtype)
                    d.cards = np.empty(t, sub.cards.dtype)
                    d.globals = np.empty((n,) + sub.globals.shape[1:], sub.globals.dtype)
                    for k in ("kind", "tkind", "src", "tgt", "extras", "pi"):
                        a = getattr(sub, k)
                        setattr(d, k, np.empty((mv,) + a.shape[1:], a.dtype))
                    for k in ("seed", "g", "step", "turn", "start", "n_legal"):
                        setattr(d, k, np.empty(n, getattr(sub, k).dtype))
                d.tokens[ti:ti + len(sub.tokens)] = sub.tokens
                d.cards[ti:ti + len(sub.cards)] = sub.cards
                d.globals[i:i + sub.n] = sub.globals
                d.offsets[i + 1:i + sub.n + 1] = sub.offsets[1:] + ti
                d.moff[i + 1:i + sub.n + 1] = sub.moff[1:] + mi
                for k in ("kind", "tkind", "src", "tgt", "extras", "pi"):
                    getattr(d, k)[mi:mi + len(sub.pi)] = getattr(sub, k)
                for k in ("seed", "g", "step", "turn", "start", "n_legal"):
                    getattr(d, k)[i:i + sub.n] = getattr(sub, k)
                pos[side] = [i + sub.n, ti + len(sub.tokens), mi + len(sub.pi)]
            del part
        for d in out:
            del d._alloc
        return out[0], out[1]

    def sharpen(self, tau: float) -> None:
        """Targets pi ** (1 / tau), normalized per decision (tau = 0.5: visits squared; tau = 1 leaves them)."""
        if tau == 1.0:
            return
        q = self.pi.astype(np.float64) ** (1.0 / tau)
        tot = np.add.reduceat(q, self.moff[:-1])
        self.pi = (q / np.repeat(tot, np.diff(self.moff))).astype(np.float32)

    def subset(self, mask) -> "Decisions":
        out = object.__new__(Decisions)
        out.card_ids, out.static = self.card_ids, self.static
        idx = np.flatnonzero(mask)
        take, lens = _spans(self.offsets, idx)
        out.tokens, out.cards = self.tokens[take], self.cards[take]
        out.offsets = np.concatenate([[0], np.cumsum(lens)]).astype(np.int64)
        out.globals = self.globals[idx]
        mtake, mlens = _spans(self.moff, idx)
        for k in ("kind", "tkind", "src", "tgt", "extras", "pi"):
            setattr(out, k, getattr(self, k)[mtake])
        out.moff = np.concatenate([[0], np.cumsum(mlens)]).astype(np.int64)
        for k in ("seed", "g", "step", "turn", "start", "n_legal"):
            setattr(out, k, getattr(self, k)[idx])
        out.n = len(idx)
        return out

    def batch(self, idx: np.ndarray) -> dict:
        take, lens = _spans(self.offsets, idx)
        tok = self.tokens[take]
        pos = np.repeat(np.arange(len(idx)), lens)
        first = np.concatenate([[0], np.cumsum(lens)[:-1]])
        mtake, mlens = _spans(self.moff, idx)
        mpos = np.repeat(np.arange(len(idx)), mlens)
        src, tgt = self.src[mtake].astype(np.int64), self.tgt[mtake].astype(np.int64)
        return {"cards": self.cards[take], "dyn": dynamic(tok), "count": tok[:, T.TOKEN.index("count")]
                .astype(np.float32), "seg": pos * NZ + tok[:, T.TOKEN.index("zone")].astype(np.int64),
                "glob": self.globals[idx], "mpos": mpos, "mstart": np.concatenate([[0], np.cumsum(mlens)[:-1]]),
                "kind": self.kind[mtake], "tkind": self.tkind[mtake], "extras": self.extras[mtake],
                "src": np.where(src >= 0, src + first[mpos], -1), "tgt": np.where(tgt >= 0, tgt + first[mpos], -1),
                "pi": self.pi[mtake].astype(np.float64)}


def seg_softmax(s: np.ndarray, start: np.ndarray) -> np.ndarray:
    """Softmax of s within the segments that begin at `start` (sorted, the first 0). Indices and counts are the
    platform's (intp): numpy on 32-bit WebAssembly (Pyodide) refuses int64 ones; on 64 bits nothing changes."""
    start = np.asarray(start, dtype=np.intp)
    counts = np.diff(np.append(start, len(s))).astype(np.intp)
    mx = np.maximum.reduceat(s, start)
    e = np.exp(s - np.repeat(mx, counts))
    tot = np.add.reduceat(e, start)
    return e / np.repeat(tot, counts)


# --- the network -------------------------------------------------------------------------------------------------

class SetPolicy:
    PARAMS = TRUNK + HEAD

    def __init__(self, static_width: int, phi=(64, 64), rho=(128, 64), head: int = 64, seed: int = 0, info=None):
        rng = np.random.default_rng(seed)
        D, G = len(dynamic(np.zeros((1, len(T.TOKEN)), np.int16))[0]), len(T.GLOBALS)
        h1, h2 = phi
        r1, r2 = rho
        self.phi, self.rho, self.head = tuple(phi), tuple(rho), int(head)
        fin = static_width + D
        self.W1s = rng.normal(0, np.sqrt(2 / fin), (static_width, h1))
        self.W1d = rng.normal(0, np.sqrt(2 / fin), (D, h1))
        self.b1 = np.zeros(h1)
        self.W2 = rng.normal(0, np.sqrt(2 / h1), (h1, h2))
        self.b2 = np.zeros(h2)
        u = NZ * h2 + G
        self.V1 = rng.normal(0, np.sqrt(2 / u) / 4, (u, r1))
        self.c1 = np.zeros(r1)
        self.V2 = rng.normal(0, np.sqrt(2 / r1), (r1, r2))
        self.c2 = np.zeros(r2)
        mw = self.move_width()
        self.A = rng.normal(0, np.sqrt(1 / r2), (r2, head))
        self.M = rng.normal(0, np.sqrt(1 / mw), (mw, head))
        self.bh = np.zeros(head)
        self.w = rng.normal(0, np.sqrt(1 / head), head)
        self.smean = np.zeros(static_width)
        self.sstd = np.ones(static_width)
        self.card_ids = np.zeros(0, np.int64)
        self.static = np.zeros((0, static_width))
        self.info = dict(info or {})

    def move_width(self) -> int:
        return len(KINDS) + len(TARGET_KINDS) + len(EXTRAS) + 2 * self.phi[1]

    @classmethod
    def from_value_net(cls, net, head: int = 64, seed: int = 0, info=None) -> "SetPolicy":
        """A prior whose trunk is the value net's (learn.setnet.SetNet, v1 inputs, ReLU): phi, the zone sums and
        rho's two hidden layers, with its static standardization. A net with the mid-turn flag gives its trunk at
        flag 0 (V1 without the flag's row)."""
        if net.inputs != "v1" or net.slope != 0.0:
            raise ValueError("the trunk has to be a v1 ReLU value net")
        pol = cls(net.static.shape[1], phi=net.phi, rho=net.rho, head=head, seed=seed, info=info)
        for k in TRUNK:
            setattr(pol, k, np.array(getattr(net, k), dtype=np.float64))
        if getattr(net, "flag", False):          # a mid-turn flagged net (NM2): its trunk at flag 0, the flag's row out
            pol.V1 = pol.V1[:-1].copy()
        pol.smean, pol.sstd = np.array(net.smean), np.array(net.sstd)
        pol.card_ids, pol.static = np.array(net.card_ids), np.array(net.static)
        return pol

    def _S(self) -> np.ndarray:
        return (self.static - self.smean) / self.sstd

    def _moves(self, b: dict, H2: np.ndarray) -> np.ndarray:
        n = len(b["kind"])
        oh = np.zeros((n, len(KINDS) + len(TARGET_KINDS)), np.float64)
        oh[np.arange(n), b["kind"]] = 1.0
        oh[np.arange(n), len(KINDS) + b["tkind"]] = 1.0
        zero = np.zeros((1, H2.shape[1]))
        Hx = np.concatenate([H2, zero])                    # row -1: no card
        return np.concatenate([oh, b["extras"], Hx[b["src"]], Hx[b["tgt"]]], axis=1)

    def forward(self, b: dict, keep: bool = False):
        B = b["glob"].shape[0]
        S = self._S()
        H1 = np.maximum((S @ self.W1s)[b["cards"]] + b["dyn"] @ self.W1d + self.b1, 0)
        H2 = np.maximum(H1 @ self.W2 + self.b2, 0)
        P = _segsum(H2, b["count"], b["seg"], B * NZ).reshape(B, -1)
        U = np.concatenate([P, b["glob"]], axis=1)
        Z1 = np.maximum(U @ self.V1 + self.c1, 0)
        Z2 = np.maximum(Z1 @ self.V2 + self.c2, 0)
        Mv = self._moves(b, H2)
        Ah = np.maximum(Z2[b["mpos"]] @ self.A + Mv @ self.M + self.bh, 0)
        s = Ah @ self.w
        if keep:
            return s, (S, H1, H2, U, Z1, Z2, Mv, Ah)
        return s

    def grads(self, b: dict, l2: float = 0.0, freeze: bool = False):
        B = b["glob"].shape[0]
        s, (S, H1, H2, U, Z1, Z2, Mv, Ah) = self.forward(b, keep=True)
        p = seg_softmax(s, b["mstart"])
        pi = b["pi"]
        loss = float(-np.sum(pi * np.log(p + 1e-12)) / B)
        g = {}
        ds = (p - pi) / B
        g["w"] = Ah.T @ ds
        dA = np.outer(ds, self.w) * (Ah > 0)
        g["bh"] = dA.sum(0)
        g["A"] = Z2[b["mpos"]].T @ dA
        g["M"] = Mv.T @ dA
        if l2:
            for k in ("A", "M", "w"):
                g[k] = g[k] + 2 * l2 * getattr(self, k)
        if freeze:
            return loss, g
        dMv = dA @ self.M.T
        h2 = self.phi[1]
        off = len(KINDS) + len(TARGET_KINDS) + len(EXTRAS)
        dH2 = np.zeros_like(H2)
        for col, rows in ((off, b["src"]), (off + h2, b["tgt"])):
            ok = rows >= 0
            np.add.at(dH2, rows[ok], dMv[ok, col:col + h2])
        dZ2 = np.zeros_like(Z2)
        np.add.at(dZ2, b["mpos"], dA @ self.A.T)
        dZ2 *= Z2 > 0
        g["V2"], g["c2"] = Z1.T @ dZ2, dZ2.sum(0)
        dZ1 = (dZ2 @ self.V2.T) * (Z1 > 0)
        g["V1"], g["c1"] = U.T @ dZ1, dZ1.sum(0)
        dP = (dZ1 @ self.V1.T)[:, :NZ * h2].reshape(B * NZ, h2)
        dH2 = (dH2 + dP[b["seg"]] * b["count"][:, None]) * (H2 > 0)
        g["W2"], g["b2"] = H1.T @ dH2, dH2.sum(0)
        dA1 = (dH2 @ self.W2.T) * (H1 > 0)
        g["W1d"], g["b1"] = b["dyn"].T @ dA1, dA1.sum(0)
        G = np.zeros((len(S), dA1.shape[1]))
        np.add.at(G, b["cards"], dA1)
        g["W1s"] = S.T @ G
        if l2:
            for k in ("W1s", "W1d", "W2", "V1", "V2"):
                g[k] = g[k] + 2 * l2 * getattr(self, k)
        return loss, g

    # --- training ---------------------------------------------------------------------------------------------
    def evaluate(self, data: Decisions, batch: int = 1024) -> np.ndarray:
        """The prior over every decision's distinct moves, in the data's move order."""
        out = np.zeros(len(data.pi))
        for s in range(0, data.n, batch):
            idx = np.arange(s, min(s + batch, data.n))
            b = data.batch(idx)
            lo, hi = data.moff[idx[0]], data.moff[idx[-1] + 1]
            out[lo:hi] = seg_softmax(self.forward(b), b["mstart"])
        return out

    def cross_entropy(self, data: Decisions, p: np.ndarray | None = None) -> float:
        p = self.evaluate(data) if p is None else p
        return float(-np.sum(data.pi * np.log(p + 1e-12)) / data.n)

    def fit(self, data: Decisions, valid: Decisions | None = None, epochs: int = 30, batch: int = 256,
            lr: float = 1e-3, l2: float = 1e-5, patience: int = 4, seed: int = 0, decay: float = 0.5,
            freeze: bool = False, log=print, checkpoint=None, ftz: bool = False) -> dict:
        """learn.setnet.SetNet.fit's loop (Adam, step size times `decay` after an epoch without a better validation
        cross entropy, `patience` such epochs stop it, the best epoch kept, an exact resume from `checkpoint`)
        on the visit distributions; with `freeze` only the head (A, M, bh, w) is fitted."""
        keys = HEAD if freeze else self.PARAMS
        rng = np.random.default_rng(seed)
        m = {k: np.zeros_like(getattr(self, k)) for k in keys}
        v = {k: np.zeros_like(getattr(self, k)) for k in keys}
        t, best, best_params, bad, history, start, stopped = 0, None, None, 0, [], 0, False
        if checkpoint is not None and Path(checkpoint).exists():
            z = np.load(checkpoint, allow_pickle=False)
            meta = json.loads(str(z["meta"]))
            for k in keys:
                setattr(self, k, np.array(z["p_" + k]))
                m[k], v[k] = np.array(z["m_" + k]), np.array(z["v_" + k])
            if meta["has_best"]:
                best_params = {k: np.array(z["b_" + k]) for k in keys}
            t, best, bad, lr, history = meta["t"], meta["best"], meta["bad"], meta["lr"], meta["history"]
            start, stopped = meta["epochs_done"], meta["stopped"]
            rng.bit_generator.state = meta["rng"]
            log(json.dumps({"resumed_after_epoch": start, "stopped": stopped}))
        for epoch in range(start, epochs):
            if stopped:
                break
            t0 = time.time()
            order = rng.permutation(data.n)
            total = 0.0
            for s in range(0, data.n, batch):
                idx = np.sort(order[s:s + batch])
                loss, g = self.grads(data.batch(idx), l2, freeze)
                total += loss * len(idx)
                t += 1
                for k in keys:
                    m[k] = 0.9 * m[k] + 0.1 * g[k]
                    v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
                    step = lr * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8)
                    setattr(self, k, getattr(self, k) - step)
                    if ftz:
                        for arr in (getattr(self, k), m[k], v[k]):
                            _flush(arr)
            row = {"epoch": epoch + 1, "lr": lr, "train_ce": round(total / data.n, 5), "s": round(time.time() - t0, 1)}
            if valid is not None:
                ce = self.cross_entropy(valid)
                row["valid_ce"] = round(ce, 5)
                if best is None or ce < best - 1e-5:
                    best, bad = ce, 0
                    best_params = {k: getattr(self, k).copy() for k in keys}
                    row["best"] = True
                else:
                    bad += 1
                    lr *= decay
            history.append(row)
            log(json.dumps(row))
            stopped = valid is not None and bad >= patience
            if checkpoint is not None:
                arrays = {"p_" + k: getattr(self, k) for k in keys}
                arrays.update({"m_" + k: m[k] for k in keys})
                arrays.update({"v_" + k: v[k] for k in keys})
                if best_params is not None:
                    arrays.update({"b_" + k: best_params[k] for k in keys})
                meta = {"t": t, "best": best, "bad": bad, "lr": lr, "history": history, "epochs_done": epoch + 1,
                        "stopped": stopped, "has_best": best_params is not None, "rng": rng.bit_generator.state}
                tmp = str(checkpoint) + ".tmp.npz"
                np.savez(tmp, meta=np.array(json.dumps(meta)), **arrays)
                os.replace(tmp, checkpoint)
            if stopped:
                break
        if best_params is not None:
            for k, val in best_params.items():
                setattr(self, k, val)
        self.info["history"] = history
        return {"history": history}

    # --- one position -----------------------------------------------------------------------------------------
    def _index(self) -> dict:
        idx = getattr(self, "_idx", None)
        if idx is None or len(idx) != len(self.card_ids):
            idx = self._idx = {int(c): i for i, c in enumerate(self.card_ids)}
        return idx

    def priors(self, state, actions) -> np.ndarray:
        """The prior of each of `actions` (the legal moves of the player to act): a distinct move's probability,
        shared equally by the legal moves that are the same move to the search (search.mcts.action_key), so the
        search's root (which adds them up per key) gets the distinct move's probability back."""
        me = state.active
        reps, group = distinct(state, actions)
        cards, toks, glob = T.encode(state, me)
        index = self._index()
        missing = sorted({int(c) for c in cards if int(c) not in index})
        if missing:                                       # cards never seen in training: their static rows
            defs = {}
            for pl in state.players:
                for c in pl.hand + pl.field + pl.leader_area + pl.deck_view():
                    defs[c.defn.card_id] = c.defn
            self.card_ids = np.concatenate([self.card_ids, np.asarray(missing, np.int64)])
            self.static = np.concatenate([self.static, np.asarray([T.static(defs[c]) for c in missing],
                                                                  dtype=np.float64)])
            index = self._index()
        kind, tkind, src, tgt, extras = move_arrays(state, reps, rows_of(state, me))
        b = {"cards": np.asarray([index[int(c)] for c in cards], np.int64), "dyn": dynamic(toks),
             "count": toks[:, T.TOKEN.index("count")].astype(np.float32),
             "seg": toks[:, T.TOKEN.index("zone")].astype(np.int64), "glob": (glob / global_scale("v1"))[None, :],
             "mpos": np.zeros(len(reps), np.int64), "mstart": np.zeros(1, np.int64), "kind": kind, "tkind": tkind,
             "extras": extras, "src": src.astype(np.int64), "tgt": tgt.astype(np.int64)}
        p = seg_softmax(self.forward(b), b["mstart"])
        counts = np.bincount(group, minlength=len(reps))
        return np.asarray([p[gi] / counts[gi] for gi in group])

    # --- files ------------------------------------------------------------------------------------------------
    def save(self, path) -> None:
        arrays = {k: getattr(self, k) for k in self.PARAMS}
        arrays.update(smean=self.smean, sstd=self.sstd, card_ids=self.card_ids, static=self.static,
                      phi=np.array(self.phi), rho=np.array(self.rho), head=np.array(self.head),
                      info=np.array(json.dumps(self.info)))
        np.savez(path, **arrays)

    @classmethod
    def load(cls, path) -> "SetPolicy":
        z = np.load(path, allow_pickle=False)
        pol = cls(z["static"].shape[1], phi=tuple(int(x) for x in z["phi"]), rho=tuple(int(x) for x in z["rho"]),
                  head=int(z["head"]))
        for k in cls.PARAMS + ("smean", "sstd", "card_ids", "static"):
            setattr(pol, k, np.array(z[k]))
        pol.info = json.loads(str(z["info"]))
        return pol


_CACHE: dict = {}


def load_cached(path) -> SetPolicy:
    """The prior at `path` (relative paths also from the repository root), loaded once per process."""
    p = Path(path)
    if not p.exists() and not p.is_absolute():
        p = Path(__file__).resolve().parents[2] / p
    key = str(p.resolve())
    pol = _CACHE.get(key)
    if pol is None:
        from svsim.learn.setnet import _file
        pol = _CACHE[key] = SetPolicy.load(_file(p))
    return pol


# --- command line ------------------------------------------------------------------------------------------------

def _prior_to_continue(args, card_ids, static) -> SetPolicy:
    """--prior's prior, to go on training from: all its weights and its standardization as they are. Its head width
    must be the command's and its card table the data's (one cards.npz)."""
    import hashlib
    pol = SetPolicy.load(args.prior)
    if pol.head != args.head:
        raise SystemExit(f"--prior {args.prior}: head {pol.head}, not the command's {args.head}")
    if getattr(args, "extend_cards", False):        # a new pairing: the data's cards the prior lacks are added
        return pol
    if not (np.array_equal(pol.card_ids, card_ids) and np.array_equal(pol.static, np.asarray(static, np.float64))):
        raise SystemExit(f"--prior {args.prior}: its card table is not the data's cards.npz")
    pol.info = {"prior": str(args.prior), "prior_sha256": hashlib.sha256(Path(args.prior).read_bytes()).hexdigest(),
                "freeze": args.freeze, "tau": args.tau, "shards": args.shards,
                "deck": pol.info.get("deck"), "opponent": pol.info.get("opponent")}
    return pol


def fit_main(args) -> None:
    from svsim.learn.setnet import SetNet
    folder = Path(args.data)
    files = [folder / f"dec-{s}.npz" for s in args.shards]
    train, valid = Decisions.split(files, args.cards)
    train.sharpen(args.tau)
    valid.sharpen(args.tau)
    card_ids, static = train.card_ids, train.static
    if args.prior:
        pol = _prior_to_continue(args, card_ids, static)
        if getattr(args, "extend_cards", False):
            from svsim.learn.setnet import extend_table
            n0 = len(pol.card_ids)
            table = extend_table(pol, card_ids, static)
            for d in (train, valid):                   # the data's card indices into the prior's (grown) table
                d.cards = table[d.cards]
                d.card_ids, d.static = pol.card_ids, pol.static.astype(np.float32)
            pol.info = {**pol.info, "extended_cards": [int(c) for c in pol.card_ids[n0:]]}
    else:
        net = SetNet.load(args.init)
        pol = SetPolicy.from_value_net(net, head=args.head, seed=args.seed,
                                       info={"init": str(args.init), "freeze": args.freeze, "tau": args.tau, "shards": args.shards,
                                             "deck": net.info.get("deck"), "opponent": net.info.get("opponent"),
                                             "train_decisions": train.n, "valid_decisions": valid.n})
        pol.card_ids, pol.static = card_ids, static.astype(np.float64)
    if args.prior:
        pol.info.update(train_decisions=train.n, valid_decisions=valid.n,
                        init_valid_ce=round(pol.cross_entropy(valid), 5))
    t0 = time.time()
    pol.fit(train, valid, epochs=args.epochs, batch=args.batch, lr=args.lr, l2=args.l2, patience=args.patience,
            seed=args.seed, decay=args.decay, freeze=args.freeze, checkpoint=args.checkpoint, ftz=args.ftz)
    pol.info["report"] = {"fit_s": round(time.time() - t0), "epochs": len(pol.info["history"]),
                          "train_ce": round(pol.cross_entropy(train), 5), "valid_ce": round(pol.cross_entropy(valid), 5)}
    pol.save(args.out)
    print(json.dumps(pol.info["report"]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("encode")
    e.add_argument("--records", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--workers", type=int, default=4)
    e.add_argument("--deck", default=None, help="keep the decisions of the side playing this deck only (a non-mirror "
                                                "pairing's prior; default both sides)")
    f = sub.add_parser("fit")
    f.add_argument("--data", required=True, help="a folder of dec-<seed>.npz")
    f.add_argument("--cards", required=True, help="a token folder's cards.npz (the static rows)")
    f.add_argument("--shards", type=int, nargs="+", required=True)
    start = f.add_mutually_exclusive_group(required=True)
    start.add_argument("--init", help="the value net whose trunk the prior starts from")
    start.add_argument("--prior", help="a prior to go on training from (all its weights; the next cycle after the "
                                       "B players: --prior analysis/scaling/models/prior-elft-ft-t05.npz)")
    f.add_argument("--freeze", action="store_true", help="keep the trunk; fit the head only")
    f.add_argument("--tau", type=float, default=1.0, help="targets visits ** (1 / tau), normalized (0.5: squared)")
    f.add_argument("--head", type=int, default=64)
    f.add_argument("--epochs", type=int, default=60)
    f.add_argument("--patience", type=int, default=4)
    f.add_argument("--decay", type=float, default=0.5)
    f.add_argument("--batch", type=int, default=256)
    f.add_argument("--lr", type=float, default=1e-3)
    f.add_argument("--l2", type=float, default=1e-5)
    f.add_argument("--seed", type=int, default=0)
    f.add_argument("--ftz", action="store_true")
    f.add_argument("--checkpoint", default=None)
    f.add_argument("--extend-cards", action="store_true",
                   help="with --prior: the data's cards the prior has no row for are added by their static rows "
                        "(setnet.extend_table; a new pairing)")
    f.add_argument("--out", required=True)
    args = ap.parse_args()
    {"encode": encode_main, "fit": fit_main}[args.cmd](args)


if __name__ == "__main__":
    main()
