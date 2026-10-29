"""The scaling test's value network (the architecture thread 2026-10-15 17:27Z): DeepSets over card tokens.

A turn-end position (learn.tokens: the moment and view of the installed turn-end evaluator) is a set of card tokens
and a few globals. Every token goes through one shared network phi; the results are summed per zone (the side is
part of the zone; a pooled deck or unseen-pool token counts as many times as its count); the seven sums and the
globals go through rho, which gives the logit of the player who ended the turn winning.

What phi sees of a card is only what it is and does: its static row (learn.tokens.static: printed values,
keywords, script hooks and properties, measured roles and payoffs) and its state now (learn.tokens.DYNAMIC). No
card-id embedding, no fixed score per card, no deck or pairing id. So a card's part in the value depends on the
position through rho, and two cards that read the same are the same to the network.

    logit = rho([sum_{t in zone z} count_t * phi(x_t)  for z in ZONES] ++ globals)
    phi(x) = relu(W2 relu(W1 x + b1) + b2),  rho(u) = v3 . relu(V2 relu(V1 u + c1) + c2) + c3

Plain numpy (forward, backward, Adam), saved as .npz without pickle, so the search can run it anywhere svsim runs.
Training: binary cross entropy against the game's result (0.5 for a draw), minibatches of positions, early stopping
on a game-split validation part of the training games.

    python -m svsim.learn.setnet fit --tokens TOKDIR --shards 70100000 ... --out net.npz
    python -m svsim.learn.setnet score --net net.npz --tokens TOKDIR --shards ...   # Brier, log-loss
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np

from svsim.learn import tokens as T

NZ = len(T.ZONES)
OP_HAND = NZ           # the zone value of an opponent-hand token (an ophand net's extra zone; not one of T.ZONES)
KW = len(T.KEYWORDS)
# a token's state as phi sees it: DYNAMIC scaled, keywords as bits (zone and count are not inputs of phi)
DYN_NAMES = ("cost", "atk", "life", "max_life", "evolved", "super_evolved", "can_hit_follower", "can_hit_leader",
             "attacks_left", "countdown", "counters", "silenced", "granted", "fresh") + \
    tuple(f"kw_{k.lower()}" for k in T.KEYWORDS)
_DYN_COLS = [T.TOKEN.index(n) for n in DYN_NAMES[:14]]
_DYN_SCALE = np.array([10, 10, 10, 10, 1, 1, 1, 1, 2, 5, 10, 1, 1, 1], dtype=np.float32)
_KW_COL = T.TOKEN.index("keywords")
_ZONE, _COUNT = T.TOKEN.index("zone"), T.TOKEN.index("count")
_GLOBAL_SCALE = np.array([20, 20, 20, 20, 10, 10, 10, 2, 2, 2, 2, 10, 10, 20, 40, 40, 9, 9, 1, 1, 1, 20, 20, 5, 5],
                         dtype=np.float32)
assert len(_GLOBAL_SCALE) == len(T.GLOBALS)
# input versions (learn.tokens INPUTS): v2 adds V2_EXTRA to every token, v2kc also the lethal clock's globals
_V2_COLS = [T.TOKEN_V2.index(n) for n in T.V2_EXTRA]
_V2_SCALE = np.array([1000, 10, 1], dtype=np.float32)
_KC_SCALE = np.array([10, 10, 10, 200, 200, 20, 20], dtype=np.float32)
_GLOBAL_SCALE_KC = np.concatenate([_GLOBAL_SCALE, _KC_SCALE])
assert len(_GLOBAL_SCALE_KC) == len(T.GLOBALS_KC)


def dyn_names(inputs: str = "v1") -> tuple:
    return DYN_NAMES if inputs == "v1" else DYN_NAMES + T.V2_EXTRA


def global_scale(inputs: str = "v1") -> np.ndarray:
    return _GLOBAL_SCALE_KC if inputs == "v2kc" else _GLOBAL_SCALE


def inputs_of(n_token_cols: int, n_globals: int, marked: str | None = None) -> str:
    """The input version of token rows / globals of these widths (a token file's own "inputs" mark first: v2a has
    v2's widths; files written before the mark are v1, v2 or v2kc)."""
    if marked:
        return marked
    if n_token_cols == len(T.TOKEN):
        return "v1"
    if n_token_cols == len(T.TOKEN_V2):
        return "v2kc" if n_globals == len(T.GLOBALS_KC) else "v2"
    raise ValueError(f"tokens with {n_token_cols} columns")


def dynamic(tokens: np.ndarray, inputs: str = "v1") -> np.ndarray:
    """[T, len(dyn_names(inputs))] float32 of int16 tokens [T, len(T.token_names(inputs))]."""
    d = tokens[:, _DYN_COLS].astype(np.float32) / _DYN_SCALE
    kw = tokens[:, _KW_COL].astype(np.int32)
    bits = ((kw[:, None] >> np.arange(KW)) & 1).astype(np.float32)
    if inputs == "v1":
        return np.concatenate([d, bits], axis=1)
    return np.concatenate([d, bits, tokens[:, _V2_COLS].astype(np.float32) / _V2_SCALE], axis=1)


SPLITS = ("key", "hash")


_LISTED: dict = {}


def _listed_games(path: str) -> np.ndarray:
    got = _LISTED.get(path)
    if got is None:
        got = _LISTED[path] = np.asarray(sorted(json.loads(Path(path).read_text(encoding="utf-8"))), np.int64)
    return got


def in_valid(keys, every: int = 20, split: str = "key") -> np.ndarray:
    """The validation games among game keys (seed * 100003 + g). "key": the key a multiple of `every`, every net's
    split before 2026-10-19. With the shards' even seeds (100003 = 3 mod 20) that picks g of one parity only, so one
    seat (netdata.play seats the deck at g % 2). "hash": splitmix64 of the key a multiple of `every`, the same share
    of games with no tie to g's parity (from-scratch nets of new pairings, the architecture thread 2026-10-19).
    "games:FILE": the games whose keys FILE lists (JSON, a list of keys), e.g. every game of a held-out deck of a pool
    (the shared net S1, the architecture thread 2026-10-29 03:33Z); `every` is not used."""
    keys = np.asarray(keys, np.int64)
    if split.startswith("games:"):
        return np.isin(keys, _listed_games(split[len("games:"):]))
    if split == "key":
        return keys % every == 0
    if split != "hash":
        raise ValueError(f"split {split!r}: one of {SPLITS}")
    z = keys.astype(np.uint64) + np.uint64(0x9E3779B97F4A7C15)
    z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    z = z ^ (z >> np.uint64(31))
    return z % np.uint64(every) == 0


class Data:
    """Turn-end positions from tok-*.npz files (learn.scaledata encode), kept compact (int16 tokens)."""

    def __init__(self, files, cards_npz):
        parts = [np.load(f) for f in files]
        c = np.load(cards_npz)
        self.card_ids = c["card_id"].astype(np.int64)
        self.static = c["static"].astype(np.float32)
        self.static_names = [str(s) for s in c["static_names"]]
        toks, cards, glob, lab = [], [], [], {k: [] for k in ("result", "linear", "seed", "g", "turn")}
        for z in parts:
            toks.append(z["tokens"])
            cards.append(np.searchsorted(self.card_ids, z["cards"].astype(np.int64)).astype(np.int32))
            glob.append(z["globals"])
            for k in lab:
                lab[k].append(z[k])
        self.tokens = np.concatenate(toks)
        self.cards = np.concatenate(cards)
        o = [np.zeros(1, np.int64)]
        base = 0
        for z in parts:
            o.append(z["offsets"][1:].astype(np.int64) + base)
            base += int(z["offsets"][-1])
        self.offsets = np.concatenate(o)
        self.inputs = inputs_of(self.tokens.shape[1], parts[0]["globals"].shape[1],
                                str(parts[0]["inputs"]) if "inputs" in parts[0].files else None)
        if any(inputs_of(z["tokens"].shape[1], z["globals"].shape[1], str(z["inputs"]) if "inputs" in z.files
                         else None) != self.inputs for z in parts):
            raise ValueError("token files of different input versions")
        self.globals = np.concatenate(glob) / global_scale(self.inputs)
        for k in lab:
            setattr(self, k, np.concatenate(lab[k]))
        self.n = len(self.result)

    def games(self) -> np.ndarray:
        """A game key per position (seed * 100003 + g)."""
        return self.seed.astype(np.int64) * 100003 + self.g.astype(np.int64)

    def subset(self, mask: np.ndarray) -> "Data":
        out = object.__new__(Data)
        out.card_ids, out.static, out.static_names = self.card_ids, self.static, self.static_names
        out.inputs = getattr(self, "inputs", "v1")
        idx = np.flatnonzero(mask)
        take, lens = _spans(self.offsets, idx)
        out.tokens, out.cards = self.tokens[take], self.cards[take]
        out.offsets = np.concatenate([[0], np.cumsum(lens)]).astype(np.int64)
        out.globals = self.globals[idx]
        for k in ("result", "linear", "seed", "g", "turn"):
            setattr(out, k, getattr(self, k)[idx])
        out.n = len(idx)
        return out

    def batch(self, idx: np.ndarray):
        """(card index [T], dynamic [T, D], count [T], segment [T] = position-in-batch * NZ + zone, globals [B, G])."""
        take, lens = _spans(self.offsets, idx)
        tok = self.tokens[take]
        pos = np.repeat(np.arange(len(idx)), lens)
        seg = pos * NZ + tok[:, _ZONE].astype(np.int64)
        return (self.cards[take], dynamic(tok, getattr(self, "inputs", "v1")), tok[:, _COUNT].astype(np.float32),
                seg, self.globals[idx])

    def hand_batch(self, idx: np.ndarray):
        """The opponent's hand tokens of positions idx (an ophand net, learn.midrows hand- files): (card index [T],
        dynamic [T, D], position in the batch [T])."""
        take, lens = _spans(self.hand_offsets, idx)
        tok = self.hand_tokens[take]
        return self.hand_cards[take], dynamic(tok), np.repeat(np.arange(len(idx)), lens)


def _spans(offsets: np.ndarray, idx: np.ndarray):
    """(the token indices of positions idx, in order; each position's token count)."""
    starts = offsets[idx]
    lens = offsets[idx + 1] - starts
    first = np.concatenate([[0], np.cumsum(lens)[:-1]]).astype(np.int64)
    return np.repeat(starts - first, lens) + np.arange(int(lens.sum())), lens


_TINY = np.finfo(np.float64).tiny


def _flush(a: np.ndarray) -> int:
    """Set the subnormal numbers of `a` to 0 in place; how many there were."""
    sub = (a != 0) & (np.abs(a) < _TINY)
    n = int(sub.sum())
    if n:
        a[sub] = 0.0
    return n


def _act(x: np.ndarray, slope: float) -> np.ndarray:
    """ReLU (slope 0, the same operation as before R3, so earlier nets stay bitwise reproducible) or leaky ReLU."""
    if slope == 0.0:
        return np.maximum(x, 0)
    return np.where(x > 0, x, slope * x)


def _dact(out: np.ndarray, slope: float):
    """The activation's derivative from its output (the output's sign is the input's for slope >= 0)."""
    if slope == 0.0:
        return out > 0
    return np.where(out > 0, 1.0, slope)


class _Printed:
    """A card at its printed values, as tokens._pooled reads one (a CardDef behind `.defn`)."""
    __slots__ = ("defn",)

    def __init__(self, defn):
        self.defn = defn


def _segsum(H: np.ndarray, w: np.ndarray, seg: np.ndarray, nseg: int) -> np.ndarray:
    """sum of w_t * H_t per segment (seg sorted ascending), [nseg, d], empty segments 0."""
    cs = np.cumsum(np.concatenate([np.zeros((1, H.shape[1])), H * w[:, None]]), axis=0)
    bounds = np.searchsorted(seg, np.arange(nseg + 1))
    return cs[bounds[1:]] - cs[bounds[:-1]]


class SetNet:
    PARAMS = ("W1s", "W1d", "b1", "W2", "b2", "V1", "c1", "V2", "c2", "v3", "c3")

    def __init__(self, static_width: int, phi=(64, 64), rho=(128, 64), seed: int = 0, info=None,
                 slope: float = 0.0, inputs: str = "v1", flag: bool = False, ophand: bool = False,
                 xcols: bool = False):
        rng = np.random.default_rng(seed)
        self.slope = float(slope)      # 0: ReLU (the fixed settings); > 0: leaky ReLU with that negative slope (R3)
        self.inputs = inputs           # learn.tokens INPUTS; "v1" for every net before 2026-10-17
        # flag: rho also reads a last global, 1 at a position inside the mover's own turn and 0 at a turn end
        # (learn.midrows; the agent option +netmid). Off for every net before 2026-10-18, whose files are as before
        self.flag = bool(flag)
        if self.flag and inputs not in ("v1", "v2a"):
            raise ValueError("the mid-turn flag is for v1 or v2a inputs")
        # ophand: a diagnostic (the architecture thread 2026-10-18 17:47Z): the opponent's real hand, card by card,
        # as one more zone; its phi sum enters rho through its own rows V1h (U @ V1 + P_hand @ V1h). Off for every
        # net before, whose numbers and files are unchanged
        self.ophand = bool(ophand)
        if self.ophand and inputs != "v1":
            raise ValueError("the opponent-hand zone is for v1 inputs")
        # xcols: a v2a net grown from a v1 one (the architecture thread 2026-10-18 19:38Z, D14a): v1's columns go
        # through W1d as before and V2_EXTRA through rows of their own, W1x, added after (0 at the start, so it
        # scores as the v1 net to the last bit). A v2a net without it (net-in2a-59000) has them in W1d
        self.xcols = bool(xcols)
        if self.xcols and inputs != "v2a":
            raise ValueError("xcols is for v2a inputs")
        if self.ophand:
            self.PARAMS = SetNet.PARAMS + ("V1h",)
        if self.xcols:
            self.PARAMS = SetNet.PARAMS + ("W1x",)
        D, G = len(dyn_names(inputs)), len(T.global_names(inputs))
        h1, h2 = phi
        r1, r2 = rho
        self.phi, self.rho = tuple(phi), tuple(rho)
        fin = static_width + D
        self.W1s = rng.normal(0, np.sqrt(2 / fin), (static_width, h1))
        self.W1d = rng.normal(0, np.sqrt(2 / fin), (D, h1))
        if self.xcols:
            self.W1d = self.W1d[:len(DYN_NAMES)].copy()
            self.W1x = np.zeros((len(T.V2_EXTRA), h1))
        self.b1 = np.zeros(h1)
        self.W2 = rng.normal(0, np.sqrt(2 / h1), (h1, h2))
        self.b2 = np.zeros(h2)
        u = NZ * h2 + G + int(self.flag)
        self.V1 = rng.normal(0, np.sqrt(2 / u) / 4, (u, r1))   # pooled sums are large: start small
        self.c1 = np.zeros(r1)
        self.V2 = rng.normal(0, np.sqrt(2 / r1), (r1, r2))
        self.c2 = np.zeros(r2)
        self.v3 = rng.normal(0, np.sqrt(1 / r2), r2)
        self.c3 = np.zeros(1)
        if self.ophand:
            self.V1h = np.zeros((h2, r1))             # the opponent-hand zone's rows, 0 at the start
        self.smean = np.zeros(static_width)
        self.sstd = np.ones(static_width)
        self.card_ids = np.zeros(0, np.int64)
        self.static = np.zeros((0, static_width))
        self.info = dict(info or {})

    # --- static rows ------------------------------------------------------------------------------------------
    def set_cards(self, card_ids, static, weights=None) -> None:
        """The static table the network looks cards up in, and its standardization (from token frequencies)."""
        static = np.asarray(static, dtype=np.float64)
        w = np.ones(len(static)) if weights is None else np.asarray(weights, dtype=np.float64)
        w = w / w.sum()
        self.smean = (w[:, None] * static).sum(0)
        self.sstd = np.sqrt((w[:, None] * (static - self.smean) ** 2).sum(0)) + 1e-3
        self.card_ids = np.asarray(card_ids, np.int64)
        self.static = static

    def _S(self, static=None) -> np.ndarray:
        s = self.static if static is None else static
        z = (s - self.smean) / self.sstd
        clip = getattr(self, "zclip", None)
        if clip is not None and static is None:       # +netclip: the table's rows within the net's own range
            z = np.clip(z, clip[0], clip[1])
        return z

    def clip_to_own_range(self) -> None:
        """Agent option +netclip (the shared-net test T1, 2026-10-29): from now on, a card's standardized static row
        is clipped, column by column, to the range of the cards the net has now (the ones it was trained on). A
        column that never varied in training has a tiny std, so a card of another class or with an ability the
        training decks never had reads as hundreds of standard deviations there; clipped, it reads as the nearest
        value the net has seen. The net's own cards are unchanged (they are the range)."""
        z = (self.static - self.smean) / self.sstd
        self.zclip = (z.min(0), z.max(0))
        self._table, self._pool, self._zone_sums, self._live_sums = None, {}, {}, {}

    # --- forward / backward -----------------------------------------------------------------------------------
    def _pre1(self, base: np.ndarray, dyn: np.ndarray) -> np.ndarray:
        """base + the dynamic part of phi's first layer (an xcols net: v1's columns as before, then W1x's term)."""
        if not self.xcols:
            return base + dyn @ self.W1d
        n = len(DYN_NAMES)
        return base + np.ascontiguousarray(dyn[..., :n]) @ self.W1d + np.ascontiguousarray(dyn[..., n:]) @ self.W1x

    def forward(self, cards, dyn, count, seg, glob, keep=False, static=None, hand=None):
        """`hand` (an ophand net): (card index, dynamic, position in batch) of the opponent's hand tokens."""
        B = glob.shape[0]
        S = self._S(static)
        A1 = self._pre1((S @ self.W1s)[cards], dyn) + self.b1
        H1 = _act(A1, self.slope)
        A2 = H1 @ self.W2 + self.b2
        H2 = _act(A2, self.slope)
        P = _segsum(H2, count, seg, B * NZ).reshape(B, -1)
        U = np.concatenate([P, glob], axis=1)
        if hand is None:
            Z1 = _act(U @ self.V1 + self.c1, self.slope)
        else:                                          # the base part as without the zone, then the zone's term
            hc, hd, hpos = hand
            Hh1 = _act((S @ self.W1s)[hc] + hd @ self.W1d + self.b1, self.slope)
            Hh2 = _act(Hh1 @ self.W2 + self.b2, self.slope)
            Ph = _segsum(Hh2, np.ones(len(hc)), hpos, B)
            Z1 = _act(U @ self.V1 + Ph @ self.V1h + self.c1, self.slope)
        Z2 = _act(Z1 @ self.V2 + self.c2, self.slope)
        out = Z2 @ self.v3 + self.c3[0]
        if keep:
            if hand is None:
                return out, (S, H1, H2, U, Z1, Z2)
            return out, (S, H1, H2, U, Z1, Z2, (Hh1, Hh2, Ph))
        return out

    def grads(self, batch, y, l2: float = 0.0):
        hand = batch[5] if len(batch) > 5 else None
        cards, dyn, count, seg, glob = batch[:5]
        B = glob.shape[0]
        z, kept = self.forward(*batch[:5], keep=True, hand=hand)
        S, H1, H2, U, Z1, Z2 = kept[:6]
        p = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
        loss = float(np.mean(-(y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12))))
        g = {}
        dz = (p - y) / B
        g["v3"], g["c3"] = Z2.T @ dz, np.array([dz.sum()])
        dZ2 = np.outer(dz, self.v3) * _dact(Z2, self.slope)
        g["V2"], g["c2"] = Z1.T @ dZ2, dZ2.sum(0)
        dZ1 = (dZ2 @ self.V2.T) * _dact(Z1, self.slope)
        g["V1"], g["c1"] = U.T @ dZ1, dZ1.sum(0)
        dU = dZ1 @ self.V1.T
        dP = dU[:, :NZ * self.phi[1]].reshape(B * NZ, self.phi[1])
        dH2 = dP[seg] * count[:, None] * _dact(H2, self.slope)
        g["W2"], g["b2"] = H1.T @ dH2, dH2.sum(0)
        dA1 = (dH2 @ self.W2.T) * _dact(H1, self.slope)
        if self.xcols:
            n = len(DYN_NAMES)
            g["W1d"], g["W1x"], g["b1"] = dyn[:, :n].T @ dA1, dyn[:, n:].T @ dA1, dA1.sum(0)
        else:
            g["W1d"], g["b1"] = dyn.T @ dA1, dA1.sum(0)
        onehot = np.zeros((len(S), len(cards)))
        onehot[cards, np.arange(len(cards))] = 1.0
        g["W1s"] = S.T @ (onehot @ dA1)
        if hand is not None:                           # the opponent-hand zone: its rows and its tokens' phi
            hc, hd, hpos = hand
            Hh1, Hh2, Ph = kept[6]
            g["V1h"] = Ph.T @ dZ1
            dHh2 = (dZ1 @ self.V1h.T)[hpos] * _dact(Hh2, self.slope)
            g["W2"] = g["W2"] + Hh1.T @ dHh2
            g["b2"] = g["b2"] + dHh2.sum(0)
            dAh1 = (dHh2 @ self.W2.T) * _dact(Hh1, self.slope)
            g["W1d"] = g["W1d"] + hd.T @ dAh1
            g["b1"] = g["b1"] + dAh1.sum(0)
            onehot_h = np.zeros((len(S), len(hc)))
            onehot_h[hc, np.arange(len(hc))] = 1.0
            g["W1s"] = g["W1s"] + S.T @ (onehot_h @ dAh1)
        if l2:
            for k in ("W1s", "W1d", "W2", "V1", "V2", "v3") + (("V1h",) if hand is not None else ()) + \
                    (("W1x",) if self.xcols else ()):
                g[k] = g[k] + 2 * l2 * getattr(self, k)
        return loss, g

    # --- training ---------------------------------------------------------------------------------------------
    def fit(self, data: Data, valid: Data | None = None, epochs: int = 30, batch: int = 256, lr: float = 1e-3,
            l2: float = 1e-5, patience: int = 3, seed: int = 0, decay: float = 0.5, log=print,
            checkpoint=None, ftz: bool = False) -> dict:
        """Adam; after each epoch without a better validation log-loss the step size is multiplied by `decay`,
        and `patience` such epochs in a row stop the fit; the best epoch's weights are kept. With `checkpoint` (a
        path), the whole state (weights, Adam's moments and step count, the step size, the best epoch so far, the
        shuffling generator) is written after every epoch and read back at the start, so a stopped fit goes on from
        its last finished epoch exactly as if it had not stopped. With `ftz`, after every step the weights and
        Adam's moments below the smallest normal float64 (subnormal numbers, which l2 decay drives unused weights
        into) are set to 0: they are far below a unit in the last place of anything they are added to, and CPU
        arithmetic on them is many times slower (the 10^5 net's epochs went from 234 s to 990 s). Off by default,
        so the 10^3 / 10^4 nets stay reproducible."""
        self._table, self._pool, self._zone_sums, self._live_sums = None, {}, {}, {}
        rng = np.random.default_rng(seed)
        m = {k: np.zeros_like(getattr(self, k)) for k in self.PARAMS}
        v = {k: np.zeros_like(getattr(self, k)) for k in self.PARAMS}
        t, best, best_params, bad, history = 0, None, None, 0, []
        start, stopped = 0, False
        if checkpoint is not None and Path(checkpoint).exists():
            z = np.load(checkpoint, allow_pickle=False)
            meta = json.loads(str(z["meta"]))
            for k in self.PARAMS:
                setattr(self, k, np.array(z["p_" + k]))
                m[k], v[k] = np.array(z["m_" + k]), np.array(z["v_" + k])
            if meta["has_best"]:
                best_params = {k: np.array(z["b_" + k]) for k in self.PARAMS}
            t, best, bad, lr, history = meta["t"], meta["best"], meta["bad"], meta["lr"], meta["history"]
            start, stopped = meta["epochs_done"], meta["stopped"]
            rng.bit_generator.state = meta["rng"]
            log(json.dumps({"resumed_after_epoch": start, "stopped": stopped}))
        y = data.result.astype(np.float64)
        for epoch in range(start, epochs):
            if stopped:
                break
            t0 = time.time()
            order = rng.permutation(data.n)
            total = 0.0
            for s in range(0, data.n, batch):
                idx = order[s:s + batch]
                loss, g = self.grads(self._batch(data, idx), y[idx], l2)
                total += loss * len(idx)
                t += 1
                for k in self.PARAMS:
                    m[k] = 0.9 * m[k] + 0.1 * g[k]
                    v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
                    step = lr * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8)
                    setattr(self, k, getattr(self, k) - step)
                    if ftz:
                        for arr in (getattr(self, k), m[k], v[k]):
                            _flush(arr)
            row = {"epoch": epoch + 1, "lr": lr, "train_bce": round(total / data.n, 5), "s": round(time.time() - t0, 1)}
            if valid is not None:
                sc = score(self.predict(valid), valid.result)
                row.update({f"valid_{k}": v_ for k, v_ in sc.items()})
                if best is None or sc["log_loss"] < best - 1e-5:
                    best, bad = sc["log_loss"], 0
                    best_params = {k: getattr(self, k).copy() for k in self.PARAMS}
                    row["best"] = True
                else:
                    bad += 1
                    lr *= decay
            history.append(row)
            log(json.dumps(row))
            stopped = valid is not None and bad >= patience
            if checkpoint is not None:
                arrays = {"p_" + k: getattr(self, k) for k in self.PARAMS}
                arrays.update({"m_" + k: m[k] for k in self.PARAMS})
                arrays.update({"v_" + k: v[k] for k in self.PARAMS})
                if best_params is not None:
                    arrays.update({"b_" + k: best_params[k] for k in self.PARAMS})
                meta = {"t": t, "best": best, "bad": bad, "lr": lr, "history": history, "epochs_done": epoch + 1,
                        "stopped": stopped, "has_best": best_params is not None,
                        "rng": rng.bit_generator.state}
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

    def _batch(self, data, idx):
        """data.batch(idx), and for an ophand net the opponent-hand tokens too (data.hand_batch)."""
        b = data.batch(idx)
        return b + (data.hand_batch(idx),) if self.ophand else b

    def predict(self, data: Data, batch: int = 1024) -> np.ndarray:
        out = np.zeros(data.n)
        for s in range(0, data.n, batch):
            idx = np.arange(s, min(s + batch, data.n))
            b = self._batch(data, idx)
            out[idx] = self.forward(*b[:5], hand=b[5] if len(b) > 5 else None)
        return 1 / (1 + np.exp(-np.clip(out, -30, 30)))

    # --- one position (the search) ----------------------------------------------------------------------------
    def logit(self, state, player: int, mid: bool = False) -> float:
        """The logit of `player` winning at turn-end position `state` (learn.tokens' moment and view); the same
        number as the batch forward pass on T.encode(state, player). A pooled card (a deck, the unseen pool) is at
        its printed values, so its phi output is a constant of the card, kept per card id, and a pooled zone's sum
        is kept per zone content (card ids with their counts, in order of first appearance): the sums are added
        in the same order as the batch pass's per-card version, so the result is the same to the last bit
        (tests/test_setnet.py, analysis/scaling/README.md). With `mid` (a flagged net only), the position is inside
        `player`'s own turn, `player` to act, and the flag input is 1."""
        if mid and not self.flag:
            raise ValueError("a net without the mid-turn flag scores turn ends only")
        if self.inputs != "v1":
            return self._logit2(state, player, mid)
        p, o = state.players[player], state.players[1 - player]
        live = [T._live(state, c, 0) for c in p.hand]
        live += [T._live(state, c, 1) for c in p.field]
        live += [T._live(state, c, 2) for c in p.leader_area]
        live += [T._live(state, c, 4) for c in o.field]
        live += [T._live(state, c, 5) for c in o.leader_area]
        pooled = ((3, p.deck_view()), (6, list(o.hand) + list(o.deck_view())))
        keys = []
        for z, cards_ in pooled:
            counts: dict = {}
            for c in cards_:
                cid = c.defn.card_id
                counts[cid] = counts.get(cid, 0) + 1
            keys.append((z, tuple(counts.items())))
        index = self._index()
        missing = {r[0] for r in live if r[0] not in index}
        for _, key in keys:
            missing |= {cid for cid, _ in key if cid not in index}
        if missing:
            self._add_cards(state, sorted(missing))
            index = self._index()
        table = getattr(self, "_table", None)            # the first layer's static part per card, computed once
        if table is None or len(table) != len(self.card_ids):
            table = self._table = self._S() @ self.W1s + self.b1
            self._pool, self._zone_sums, self._live_sums = {}, {}, {}
        P = self._live_part(live, index, table, "v1")
        sums = self._zone_sums
        for (z, cards_), (_, key) in zip(pooled, keys):
            total = sums.get((z, key))
            if total is None:
                total = np.zeros(self.phi[1])
                for cid, n in key:
                    h = self._pool.get(cid)
                    if h is None:
                        d = next(c.defn for c in cards_ if c.defn.card_id == cid)
                        tok = np.asarray(T._pooled([_Printed(d)], z)[0][1:], dtype=np.int16)[None, :]
                        h = self._pool[cid] = _act(
                            _act(table[index[cid]] + dynamic(tok)[0] @ self.W1d, self.slope) @ self.W2 + self.b2,
                            self.slope)
                    total += n * h
                if len(sums) > 50000:
                    sums.clear()
                sums[(z, key)] = total
            P[z] = P[z] + total
        g = T.globals_of(state, player) / _GLOBAL_SCALE
        if self.flag:
            g = np.append(g, np.float32(1.0 if mid else 0.0))
        u = np.concatenate([P.reshape(-1), g])
        if not self.ophand:
            z1 = _act(u @ self.V1 + self.c1, self.slope)
        else:                         # the opponent's hand as the state has it (a guess, or the real one)
            Ph = np.zeros(self.phi[1])
            rows = [T._live(state, c, OP_HAND) for c in o.hand]
            if rows:
                r = np.asarray(rows, dtype=np.int64)
                hidx = []
                for cid in r[:, 0].tolist():
                    if cid not in index:
                        self._add_cards(state, [cid])
                        index = self._index()
                        table = self._table = self._S() @ self.W1s + self.b1
                    hidx.append(index[cid])
                Hh1 = _act(table[hidx] + dynamic(r[:, 1:]) @ self.W1d, self.slope)
                Ph = _act(Hh1 @ self.W2 + self.b2, self.slope).sum(axis=0)
            z1 = _act(u @ self.V1 + Ph @ self.V1h + self.c1, self.slope)
        return float(_act(z1 @ self.V2 + self.c2, self.slope) @ self.v3 + self.c3[0])

    @classmethod
    def flagged_from(cls, net: "SetNet", info=None) -> "SetNet":
        """`net` with the mid-turn flag added: the same weights, card table and standardization, and V1 one row
        longer, that row 0. So at flag 0 (a turn end) it scores as `net` does, and training starts from it."""
        if net.flag:
            raise ValueError("the net has the flag already")
        out = cls(net.static.shape[1], phi=net.phi, rho=net.rho, slope=net.slope, inputs=net.inputs, flag=True,
                  info=info)
        for k in cls.PARAMS + ("smean", "sstd", "card_ids", "static"):
            setattr(out, k, np.array(getattr(net, k)))
        out.V1 = np.concatenate([np.asarray(net.V1, dtype=np.float64), np.zeros((1, net.V1.shape[1]))])
        return out

    @classmethod
    def with_ophand_from(cls, net: "SetNet", info=None) -> "SetNet":
        """`net` with the opponent-hand zone added (a diagnostic): the same weights, card table and standardization,
        and V1h 0, so it scores every position as `net` does, to the last bit, until it is trained."""
        if net.ophand:
            raise ValueError("the net has the opponent-hand zone already")
        out = cls(net.static.shape[1], phi=net.phi, rho=net.rho, slope=net.slope, inputs=net.inputs, flag=net.flag,
                  ophand=True, info=info)
        for k in SetNet.PARAMS + ("smean", "sstd", "card_ids", "static"):
            setattr(out, k, np.array(getattr(net, k)))
        return out

    @classmethod
    def with_v2a_from(cls, net: "SetNet", info=None) -> "SetNet":
        """A v1 `net` grown to v2a (xcols): the same weights, card table and standardization, and W1x (V2_EXTRA's
        rows) 0, so it scores every position as `net` does, to the last bit, until it is trained."""
        if net.inputs != "v1" or net.ophand:
            raise ValueError("a v1 net without the opponent-hand zone grows to v2a")
        out = cls(net.static.shape[1], phi=net.phi, rho=net.rho, slope=net.slope, inputs="v2a", flag=net.flag,
                  xcols=True, info=info)
        for k in SetNet.PARAMS + ("smean", "sstd", "card_ids", "static"):
            setattr(out, k, np.array(getattr(net, k)))
        return out

    def _logit2(self, state, player: int, mid: bool = False) -> float:
        """logit() for the v2 inputs: a pooled token's row also holds its share and its owner's next-turn values,
        so its phi output is kept per (card, row) and a pooled zone's sum per (zone content, share per copy,
        next-turn values)."""
        p, o = state.players[player], state.players[1 - player]
        mine, theirs = T._next(state, player), T._next(state, 1 - player)
        an = self.inputs != "v2a"
        live = [T._live2(state, c, 0, mine, an) for c in p.hand]
        live += [T._live2(state, c, 1, mine, an) for c in p.field]
        live += [T._live2(state, c, 2, mine, an) for c in p.leader_area]
        live += [T._live2(state, c, 4, theirs, an) for c in o.field]
        live += [T._live2(state, c, 5, theirs, an) for c in o.leader_area]
        deck, pool = p.deck_view(), list(o.hand) + list(o.deck_view())
        pooled = ((3, deck, T._pool_per(len(deck), 0, 3), mine),
                  (6, pool, T._pool_per(len(pool), len(o.hand), 6), theirs))
        keys = []
        for z, cards_, per, nxt in pooled:
            counts: dict = {}
            for c in cards_:
                cid = c.defn.card_id
                counts[cid] = counts.get(cid, 0) + 1
            keys.append((z, tuple(counts.items()), per, nxt))
        index = self._index()
        missing = {r[0] for r in live if r[0] not in index}
        for key in keys:
            missing |= {cid for cid, _ in key[1] if cid not in index}
        if missing:
            self._add_cards(state, sorted(missing))
            index = self._index()
        table = getattr(self, "_table", None)
        if table is None or len(table) != len(self.card_ids):
            table = self._table = self._S() @ self.W1s + self.b1
            self._pool, self._zone_sums, self._live_sums = {}, {}, {}
        P = self._live_part(live, index, table, self.inputs)
        sums = self._zone_sums
        for (z, cards_, per, nxt), key in zip(pooled, keys):
            total = sums.get(key)
            if total is None:
                total = np.zeros(self.phi[1])
                for cid, n in key[1]:
                    # the token's phi input is the card's printed values (a function of the card) plus V2_EXTRA,
                    # so (card, share, next-turn values) names it; the row itself is built only on a miss
                    hk = (cid, int(round(1000 * per * n))) + nxt
                    h = self._pool.get(hk)
                    if h is None:
                        d = next(c.defn for c in cards_ if c.defn.card_id == cid)
                        row = T._pooled2([_Printed(d)] * n, z, per, nxt)[0]
                        assert row[-3] == hk[1]
                        tok = np.asarray(row[1:], dtype=np.int16)[None, :]
                        h = self._pool[hk] = _act(_act(self._pre1(table[index[cid]], dynamic(tok, self.inputs)[0]),
                                                       self.slope) @ self.W2 + self.b2, self.slope)
                    total += n * h
                if len(sums) > 50000:
                    sums.clear()
                sums[key] = total
            P[z] = P[z] + total
        g = T.globals_of(state, player, self.inputs) / global_scale(self.inputs)
        if self.flag:
            g = np.append(g, np.float32(1.0 if mid else 0.0))
        u = np.concatenate([P.reshape(-1), g])
        z1 = _act(u @ self.V1 + self.c1, self.slope)
        return float(_act(z1 @ self.V2 + self.c2, self.slope) @ self.v3 + self.c3[0])

    def _live_part(self, live, index, table, inputs) -> np.ndarray:
        """The live tokens' phi sums per zone [NZ, phi out], a fresh array. Memoized on the exact live rows (card ids
        and every value): the same rows give the same matrix products in the same order, so a hit is the same number
        to the last bit (a token computed on its own or in a smaller batch would not be: BLAS sums in a different
        order). The card id in the key is only the memo's key, never an input of the net."""
        memo = getattr(self, "_live_sums", None)
        if memo is None:
            memo = self._live_sums = {}
        key = tuple(map(tuple, live))
        hit = memo.get(key)
        if hit is not None:
            self._live_hits = getattr(self, "_live_hits", 0) + 1
            return hit.copy()
        P = np.zeros((NZ, self.phi[1]))
        if live:
            rows = np.asarray(live, dtype=np.int64)
            cards = [index[c] for c in rows[:, 0].tolist()]
            H1 = _act(self._pre1(table[cards], dynamic(rows[:, 1:], inputs)), self.slope)
            H2 = _act(H1 @ self.W2 + self.b2, self.slope)       # live tokens have count 1
            zones = rows[:, 1 + _ZONE]
            for z in sorted(set(zones.tolist())):
                P[z] = H2[zones == z].sum(axis=0)
        if len(memo) > 50000:
            memo.clear()
        memo[key] = P.copy()
        self._live_misses = getattr(self, "_live_misses", 0) + 1
        return P

    def _index(self) -> dict:
        idx = getattr(self, "_idx", None)
        if idx is None or len(idx) != len(self.card_ids):
            idx = self._idx = {int(c): i for i, c in enumerate(self.card_ids)}
        return idx

    def _add_cards(self, state, missing) -> None:
        """Cards never seen in training: their static rows (the network reads only what a card is)."""
        defs = {}
        for p in state.players:
            for c in p.hand + p.field + p.leader_area + p.deck_view():
                defs[c.defn.card_id] = c.defn
        rows = [T.static(defs[c]) for c in missing]
        self.card_ids = np.concatenate([self.card_ids, np.asarray(missing, np.int64)])
        self.static = np.concatenate([self.static, np.asarray(rows, dtype=np.float64)])

    def flush_subnormals(self) -> int:
        """Set every subnormal weight to 0 (agent option +netftz, at load); how many there were. The net's numbers
        are unchanged where checked (analysis/scaling/README.md); only CPU time on them is saved."""
        n = sum(_flush(getattr(self, k)) for k in self.PARAMS)
        self._table, self._live_sums = None, {}
        return n

    # --- files ------------------------------------------------------------------------------------------------
    def save(self, path) -> None:
        arrays = {k: getattr(self, k) for k in self.PARAMS}
        arrays.update(smean=self.smean, sstd=self.sstd, card_ids=self.card_ids, static=self.static,
                      phi=np.array(self.phi), rho=np.array(self.rho), slope=np.array(self.slope),
                      info=np.array(json.dumps(self.info)))
        if self.inputs != "v1":                  # a v1 net's file is as before
            arrays["inputs"] = np.array(self.inputs)
        if self.flag:                            # so is a net's without the flag
            arrays["flag"] = np.array(True)
        if self.ophand:
            arrays["ophand"] = np.array(True)
        if self.xcols:
            arrays["xcols"] = np.array(True)
        np.savez(path, **arrays)

    @classmethod
    def load(cls, path) -> "SetNet":
        z = np.load(path, allow_pickle=False)
        if "wide" in z.files:                    # a net grown wider (learn.widenet)
            from svsim.learn.widenet import WideSetNet
            return WideSetNet.from_file(z)
        net = cls(z["static"].shape[1], phi=tuple(int(x) for x in z["phi"]), rho=tuple(int(x) for x in z["rho"]),
                  slope=float(z["slope"]) if "slope" in z.files else 0.0,
                  inputs=str(z["inputs"]) if "inputs" in z.files else "v1",
                  flag=bool(z["flag"]) if "flag" in z.files else False,
                  ophand=bool(z["ophand"]) if "ophand" in z.files else False,
                  xcols=bool(z["xcols"]) if "xcols" in z.files else False)
        for k in net.PARAMS + ("smean", "sstd", "card_ids", "static"):
            setattr(net, k, np.array(z[k]))
        net.info = json.loads(str(z["info"]))
        return net


def extend_table(model, card_ids, static) -> np.ndarray:
    """A start's card table grown to a new pairing's cards (NM1, the architecture thread 2026-10-19 00:34Z): the
    cards of (card_ids, static) that `model` (a SetNet or a setpolicy.SetPolicy) has no row for are appended by their
    static rows, the standardization unchanged, so on the cards it knew the model scores as before. A card in both
    must have the same static row. Returns each of card_ids' index in the model's table."""
    index = {int(c): i for i, c in enumerate(model.card_ids)}
    static = np.asarray(static, dtype=np.float64)
    new = []
    for c, row in zip(np.asarray(card_ids).tolist(), static):
        if c in index:
            if not np.array_equal(model.static[index[c]], row):
                raise ValueError(f"card {c}: its static row differs from the model's")
        elif c not in {n for n, _ in new}:
            new.append((c, row))
    if new:
        model.card_ids = np.concatenate([model.card_ids, np.asarray([c for c, _ in new], np.int64)])
        model.static = np.concatenate([model.static, np.stack([r for _, r in new])])
        for k in ("_table", "_idx"):
            if hasattr(model, k):
                setattr(model, k, None)
        for k in ("_pool", "_zone_sums", "_live_sums"):
            if hasattr(model, k):
                setattr(model, k, {})
        index = {int(c): i for i, c in enumerate(model.card_ids)}
    return np.asarray([index[c] for c in np.asarray(card_ids).tolist()], dtype=np.int32)


_CACHE: dict = {}


def _file(p: Path):
    """`p`, or where only "<p>.b64" is there (the in-browser build ships binary models as base64 text,
    tools.web), its decoded bytes as a file object."""
    if p.exists():
        return p
    b64 = Path(str(p) + ".b64")
    if not b64.exists():
        return p
    import base64
    import io
    return io.BytesIO(base64.b64decode(b64.read_text(encoding="ascii")))


def load_cached(path, ftz: bool = False, clip: bool = False) -> SetNet:
    """The net at `path` (relative paths also from the repository root), loaded once per process; with `ftz`, its
    subnormal weights set to 0 at load (a separate copy); with `clip`, SetNet.clip_to_own_range (a separate copy)."""
    p = Path(path)
    if not p.exists() and not p.is_absolute():
        p = Path(__file__).resolve().parents[2] / p
    key = (str(p.resolve()), ftz) + ((True,) if clip else ())
    net = _CACHE.get(key)
    if net is None:
        net = _CACHE[key] = SetNet.load(_file(p))
        if ftz:
            net.flush_subnormals()
        if clip:
            net.clip_to_own_range()
    return net


class SetNetEnded:
    """Search weights: the turn-end score (player_moves_next False) of the net's own pairing (info "deck",
    "opponent": the scored player's deck and the other's, ui.session.DECKS keys) from the net, as SCALE x its
    logit; everything else (in-turn scores, other pairings, finished games) from `base`. With `end_mid_turn`
    (agent option +neteot), a position inside the scored player's own turn (they are to act) is scored after
    search.evaluate.after_end_of_turn on a copy, the moment the net was trained on; off, nothing changes. With
    `mid_turn` (agent option +netmid; a net with the mid-turn flag, learn.midrows), such a position is scored as it
    is by the net's mid-turn branch (flag 1), with no turn end played, and every other position by its turn-end
    branch (flag 0); it takes the place of `end_mid_turn`. With `any_pairing` (agent option +netany), the net
    scores every game, whatever the decks (a shared net, or a pairing net tried on decks it never saw); off, only
    its own pairing, as before."""

    def __init__(self, base, net: SetNet, end_mid_turn: bool = False, mid_turn: bool = False,
                 reply_end: bool = False, any_pairing: bool = False):
        self.base = base
        # +netreply (the architecture thread 2026-10-19 00:37Z): a leaf of +reply's played-out opponent turn, stopped
        # at that turn's end (search.mcts reply_end, after_end_of_turn) and scored with player_moves_next, is the
        # opponent's turn end: SCALE x minus the net's turn-end logit for the opponent. Off: as before
        self.reply_end = reply_end
        self.net = net
        self.end_mid_turn = end_mid_turn         # +neteot: a mid-turn position is first played to its turn end
        self.mid_turn = mid_turn                 # +netmid: a mid-turn position is scored by the mid-turn branch
        if mid_turn and not net.flag:
            raise ValueError("+netmid needs a net with the mid-turn flag (learn.midrows)")
        # +netany (the architecture thread 2026-10-29 02:30Z), or a net trained on a pool of decks (info shared)
        self.any_pairing = any_pairing or bool(net.info.get("shared"))
        self.pair = (net.info.get("deck"), net.info.get("opponent"))
        if None in self.pair and not self.any_pairing:
            raise ValueError("the net names no pairing (info deck / opponent)")
        # a net trained on both sides of a non-mirror pairing (NM1) names both orders in info "pairs"; a net
        # without the key answers for (deck, opponent) only, as before
        self.pairs = {tuple(p) for p in net.info.get("pairs") or [self.pair]}

    def answers_reply(self, state, player: int) -> bool:
        """Whether a +reply leaf where the opponent of `player` ends the turn is scored here (+netreply, the net's
        pairing seen from the opponent)."""
        return self.reply_end and (self.any_pairing or (state.players[1 - player].deck_name,
                                                        state.players[player].deck_name) in self.pairs)

    def score(self, state, player: int, player_moves_next: bool = False) -> float:
        from svsim.learn.model import SCALE
        from svsim.search.evaluate import WIN
        if state.winner is not None:
            return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
        if player_moves_next and state.active == player and self.answers_reply(state, player):
            return -SCALE * self.net.logit(state, 1 - player)
        if not player_moves_next and (self.any_pairing or (state.players[player].deck_name,
                                                           state.players[1 - player].deck_name) in self.pairs):
            if self.mid_turn and state.active == player:
                return SCALE * self.net.logit(state, player, mid=True)
            if self.end_mid_turn and state.active == player:
                # inside the scored player's own turn (a leaf after a move that isn't the turn's end, the root's
                # center): the net has only seen positions after the end-of-turn abilities, so end the turn on a
                # copy first, as learn.netdata.rows does for its turn-end rows
                from svsim.search.evaluate import after_end_of_turn
                state = after_end_of_turn(state)
                if state.winner is not None:
                    return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
            return SCALE * self.net.logit(state, player)
        return self.base.score(state, player, player_moves_next)


def score(p: np.ndarray, y: np.ndarray) -> dict:
    """Brier and log-loss of probabilities p against results y."""
    p = np.clip(np.asarray(p, dtype=np.float64), 1e-7, 1 - 1e-7)
    y = np.asarray(y, dtype=np.float64)
    return {"brier": round(float(np.mean((p - y) ** 2)), 5),
            "log_loss": round(float(np.mean(-(y * np.log(p) + (1 - y) * np.log(1 - p)))), 5), "n": int(len(y))}
