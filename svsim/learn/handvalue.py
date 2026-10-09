"""The hand-value student: H(hand | position), a price for the whole hand that depends on the position.

The hand-value line (Salem 2026-10-09 02:01Z; design: docs/hand-value-design.md section 2 on the
claude/bot-architecture-design branch, the analysis line's analysis/card-value/student-plan.md): the teacher
measures T(c | s), how much more holding card c is worth than not holding it in position s; the student learns a
value of the hand such that H(hand) - H(hand without c) ~ T(c | s). Salem's rule: no fixed score per card. The
structure keeps it so: a card's own inputs (its id's embedding, what it does: learn.roles, its base cost) reach the
output only multiplied by a gate read from the position and from how the card fits it (its cost against the play
points now and next turn), and the cards are summed before a small network (DeepSets), so two cards can be worth
more together and nine of a kind less than nine times one.

Inputs never include a deck id, a deck key or the pairing (a model file per pairing is fine): the position (CTX),
and per card its id (an embedding over the card ids seen in training; one never seen gets the zero row and lives on
its roles), its roles and costs (CARD, FIT).

Cards the search can't know are priced as one of the pool they came from: a card drawn after the search's root
(mcts.ISMCTS sets the root, as its `_root_deck`) and every card of a hand that isn't the root player's are encoded
as the mean of the cards in that hand-and-deck pool, so the value doesn't move with what a determinization drew.
Outside a search (fitting, analysis) every card in hand is known, unless `root` says otherwise.

Plain numpy, no other dependency. Fitting: HandValue.fit on (hand, removed card, T, weight) examples, the weight
1 / the variance of T. Used by the evaluation as the named feature set "hand_value" (learn.features), whose
coefficient learn.phased fits like any other.
"""
from __future__ import annotations

import json
import math
from contextlib import contextmanager
from pathlib import Path

import numpy as np

CTX = ("turn", "pp", "max_pp", "next_pp", "bonus", "me_hp", "op_hp", "me_followers", "op_followers", "me_deck",
       "op_deck", "ep", "sep", "hand_size")
CARD = ("face", "removal", "heal", "draw", "ramp", "body", "base_cost", "unknown")
FIT = ("cost", "playable_now", "playable_next", "turns_to_play")
ROLE_SCALE = (8.0, 2.0, 8.0, 3.0, 3.0, 12.0)
MAX_PP = 10
VAR_FLOOR = 1e-5                  # the teacher's own se^2 is about 1e-4 (the architecture thread 02:25Z)
ESS_SHARE = 0.3                   # 1 / var weights whose effective sample size is below this share: equal weights

_ROOT: tuple | None = None        # (player, frozenset of the uids in that player's deck at the search's root)


@contextmanager
def root(player: int, deck_uids):
    """While a search decides for `player`: cards drawn from `deck_uids` (the deck at the root), and every card
    in the other player's hand, are unknown to it."""
    global _ROOT
    before = _ROOT
    _ROOT = (player, frozenset(deck_uids))
    try:
        yield
    finally:
        _ROOT = before


def unknown_uids(state, player: int):
    """None: every card in `player`'s hand is known; else the set of its uids that aren't (or "all")."""
    if _ROOT is None:
        return None
    if _ROOT[0] != player:
        return "all"
    return _ROOT[1]


def context(state, player: int) -> np.ndarray:
    p, o = state.players[player], state.players[1 - player]
    nxt = min(p.max_pp + 1, MAX_PP)
    return np.array([p.turns_taken / 10, p.pp / 10, p.max_pp / 10, nxt / 10, float(p.bonus_ready),
                     p.leader_hp / 20, o.leader_hp / 20, len(p.followers) / 5, len(o.followers) / 5,
                     len(p.deck) / 40, len(o.deck) / 40, p.ep / 2, p.sep / 2, len(p.hand) / 9], dtype=float)


def _card_static(defn) -> tuple:
    from svsim.learn.roles import card_roles
    r = card_roles(defn)
    return tuple(v / s for v, s in zip(r, ROLE_SCALE)) + (defn.cost / 10, 0.0)


def _card_fit(cost: int, pp: int, nxt: int) -> tuple:
    return (cost / 10, float(cost <= pp), float(cost <= nxt), max(0, cost - nxt) / 10)


class HandValue:
    """H(hand | position) = w2 . tanh(W1 S + b1), S = sum over the cards of tanh(Wa [E d_c, card_c] + ba) *
    sigmoid(Wg [ctx, fit_c] + bg): d_c is the card's one-hot over `vocab` (the pool's frequencies for an unknown
    card), E the embedding."""

    PARAMS = ("E", "Wa", "ba", "Wg", "bg", "W1", "b1", "w2")

    def __init__(self, vocab, embed: int = 8, width: int = 16, hidden: int = 16, seed: int = 0, info=None):
        self.vocab = [int(v) for v in vocab]
        self.index = {v: i + 1 for i, v in enumerate(self.vocab)}     # 0: a card id never seen in training
        self.embed, self.width, self.hidden = embed, width, hidden
        self.info = dict(info or {})
        rng = np.random.default_rng(seed)
        V, fa, fg = len(self.vocab) + 1, embed + len(CARD), len(CTX) + len(FIT)
        self.E = rng.normal(0, 0.3, (V, embed))
        self.E[0] = 0.0
        self.Wa = rng.normal(0, 1 / math.sqrt(fa), (fa, width))
        self.ba = np.zeros(width)
        self.Wg = rng.normal(0, 1 / math.sqrt(fg), (fg, width))
        self.bg = np.zeros(width)
        self.W1 = rng.normal(0, 1 / math.sqrt(width), (width, hidden))
        self.b1 = np.zeros(hidden)
        self.w2 = rng.normal(0, 1 / math.sqrt(hidden), hidden)
        self._memo: dict = {}

    # --- encoding -------------------------------------------------------------------------------------------
    def encode(self, state, player: int, unknown="search"):
        """(D [n, V], Xs [n, CARD], Xq [n, FIT], z [CTX]) for `player`'s hand. `unknown`: "search" (the root set
        by `root`, if any), None (all known), "all", or a set of uids."""
        if unknown == "search":
            unknown = unknown_uids(state, player)
        p = state.players[player]
        nxt = min(p.max_pp + 1, MAX_PP)
        V = len(self.vocab) + 1
        hidden = [c for c in p.hand if unknown == "all" or (unknown is not None and c.uid in unknown)]
        known = [c for c in p.hand if not (unknown == "all" or (unknown is not None and c.uid in unknown))]
        rows_d, rows_s, rows_q = [], [], []
        for c in known:
            d = np.zeros(V)
            d[self.index.get(c.defn.card_id, 0)] = 1.0
            rows_d.append(d)
            rows_s.append(_card_static(c.defn))
            rows_q.append(_card_fit(c.cost, p.pp, nxt))
        if hidden:                                 # one of the pool they came from, each
            pool = hidden + list(p.deck)
            d = np.zeros(V)
            for c in pool:
                d[self.index.get(c.defn.card_id, 0)] += 1.0 / len(pool)
            s = np.mean([_card_static(c.defn) for c in pool], axis=0)
            s[-1] = 1.0
            q = np.mean([_card_fit(c.cost, p.pp, nxt) for c in pool], axis=0)
            for _ in hidden:
                rows_d.append(d)
                rows_s.append(s)
                rows_q.append(q)
        n = len(rows_d)
        if n == 0:
            return np.zeros((0, V)), np.zeros((0, len(CARD))), np.zeros((0, len(FIT))), context(state, player)
        return np.array(rows_d), np.array(rows_s, dtype=float), np.array(rows_q, dtype=float), context(state, player)

    # --- forward --------------------------------------------------------------------------------------------
    def units(self, D, Xs, Xq, z) -> np.ndarray:
        """Each card's contribution to S, [n, width]."""
        if len(D) == 0:
            return np.zeros((0, self.width))
        A = np.tanh(np.concatenate([D @ self.E, Xs], axis=1) @ self.Wa + self.ba)
        G = 1 / (1 + np.exp(-(np.concatenate([np.repeat(z[None, :], len(D), axis=0), Xq], axis=1) @ self.Wg
                              + self.bg)))
        return A * G

    def head(self, S: np.ndarray) -> float:
        return float(np.tanh(S @ self.W1 + self.b1) @ self.w2)

    def h(self, enc) -> float:
        return self.head(self.units(*enc).sum(axis=0))

    def value(self, state, player: int) -> float:
        """H of `player`'s hand as the search sees it (learn.features "hand_value")."""
        unknown = unknown_uids(state, player)
        p = state.players[player]
        hidden = [c for c in p.hand if unknown == "all" or (unknown is not None and c.uid in unknown)]
        gone = {c.uid for c in hidden}
        key = (tuple(np.round(context(state, player), 6)),
               tuple((c.defn.card_id, c.cost) for c in p.hand if c.uid not in gone),
               len(hidden), tuple(sorted((c.defn.card_id, c.cost) for c in hidden + list(p.deck))) if hidden else ())
        hit = self._memo.get(key)
        if hit is None:
            if len(self._memo) >= 100_000:
                self._memo.clear()
            hit = self._memo[key] = self.h(self.encode(state, player))
        return hit

    def delta(self, state, player: int, uid: int, unknown=None) -> float:
        """H(hand) - H(hand without the card `uid`): the card's worth in this hand and position."""
        D, Xs, Xq, z = self.encode(state, player, unknown)
        U = self.units(D, Xs, Xq, z)
        i = self._slot(state, player, uid, unknown)
        S = U.sum(axis=0)
        return self.head(S) - self.head(S - U[i])

    def _slot(self, state, player, uid, unknown) -> int:
        """Where `uid` sits in encode's rows (known cards first, in hand order, then the unknown ones)."""
        p = state.players[player]
        is_hidden = lambda c: unknown == "all" or (unknown is not None and c.uid in unknown)
        order = [c.uid for c in p.hand if not is_hidden(c)] + [c.uid for c in p.hand if is_hidden(c)]
        return order.index(uid)

    # --- fitting --------------------------------------------------------------------------------------------
    def example(self, state, player: int, uid: int, t: float, weight: float = 1.0, unknown=None):
        """One training example: the hand's encoding, the removed card's row, the label and its weight."""
        enc = self.encode(state, player, unknown)
        return enc, self._slot(state, player, uid, unknown), float(t), float(weight)

    @staticmethod
    def batch(examples):
        """Stack examples, padded to the largest hand: D [B, N, V], Xs, Xq, Z [B, CTX], M [B, N], R, T, W."""
        B = len(examples)
        N = max(1, max(len(e[0][0]) for e in examples))
        V, fs, fq = examples[0][0][0].shape[1], len(CARD), len(FIT)
        D, Xs, Xq = np.zeros((B, N, V)), np.zeros((B, N, fs)), np.zeros((B, N, fq))
        Z, M = np.zeros((B, len(CTX))), np.zeros((B, N))
        R, T, W = np.zeros(B, dtype=int), np.zeros(B), np.zeros(B)
        for b, ((d, s, q, z), r, t, w) in enumerate(examples):
            n = len(d)
            D[b, :n], Xs[b, :n], Xq[b, :n], Z[b], M[b, :n] = d, s, q, z, 1.0
            R[b], T[b], W[b] = r, t, w
        return D, Xs, Xq, Z, M, R, T, W

    def loss_and_grads(self, D, Xs, Xq, Z, M, R, T, W, l2: float = 0.0):
        """Weighted mean of (H(hand) - H(hand without the removed card) - T)^2, plus l2 on the weights; the
        gradients by name."""
        B, N, _ = D.shape
        de = self.embed
        EMB = D @ self.E                                          # [B, N, de]
        IA = np.concatenate([EMB, Xs], axis=2)
        A = np.tanh(IA @ self.Wa + self.ba)
        IG = np.concatenate([np.repeat(Z[:, None, :], N, axis=1), Xq], axis=2)
        G = 1 / (1 + np.exp(-(IG @ self.Wg + self.bg)))
        U = A * G * M[:, :, None]
        S1 = U.sum(axis=1)
        Ur = U[np.arange(B), R]
        S0 = S1 - Ur
        H1h = np.tanh(S1 @ self.W1 + self.b1)
        H0h = np.tanh(S0 @ self.W1 + self.b1)
        d = H1h @ self.w2 - H0h @ self.w2 - T
        params = [getattr(self, k) for k in self.PARAMS if k != "E"] + [self.E[1:]]
        loss = float(np.mean(W * d * d)) + l2 * sum(float(np.sum(P * P)) for P in params)
        g = {}
        dH1 = 2 * W * d / B
        dH0 = -dH1
        g["w2"] = H1h.T @ dH1 + H0h.T @ dH0 + 2 * l2 * self.w2
        dP1 = (dH1[:, None] * self.w2) * (1 - H1h ** 2)
        dP0 = (dH0[:, None] * self.w2) * (1 - H0h ** 2)
        g["W1"] = S1.T @ dP1 + S0.T @ dP0 + 2 * l2 * self.W1
        g["b1"] = dP1.sum(axis=0) + dP0.sum(axis=0)
        dS1, dS0 = dP1 @ self.W1.T, dP0 @ self.W1.T
        dU = np.repeat((dS1 + dS0)[:, None, :], N, axis=1)
        dU[np.arange(B), R] -= dS0
        dU *= M[:, :, None]
        dPA = dU * G * (1 - A ** 2)
        dPG = dU * A * G * (1 - G)
        g["Wa"] = IA.reshape(-1, IA.shape[2]).T @ dPA.reshape(-1, self.width) + 2 * l2 * self.Wa
        g["ba"] = dPA.sum(axis=(0, 1))
        g["Wg"] = IG.reshape(-1, IG.shape[2]).T @ dPG.reshape(-1, self.width) + 2 * l2 * self.Wg
        g["bg"] = dPG.sum(axis=(0, 1))
        dEMB = (dPA @ self.Wa.T)[:, :, :de]
        g["E"] = np.einsum("bnv,bnd->vd", D, dEMB) + 2 * l2 * self.E
        g["E"][0] = 0.0                                            # the never-seen row stays zero
        return loss, g

    def fit(self, examples, iters: int = 2000, lr: float = 0.01, l2: float = 1e-4, batch: int = 256,
            seed: int = 0, holdout=None) -> dict:
        """Adam on the weighted differential loss. `examples`: from `example`; `holdout`: examples scored, not fitted.
        The weights are normalized to mean 1; if their effective sample size (sum w)^2 / sum w^2 is below ESS_SHARE
        of the examples, they are all set to 1 instead (the report says which, and the ESS)."""
        rng = np.random.default_rng(seed)
        w = np.array([e[3] for e in examples], dtype=float)
        ess = float(w.sum() ** 2 / np.sum(w * w))
        equal = ess < ESS_SHARE * len(w)           # a few examples would carry the fit: equal weights instead
        mean_w = float(np.mean(w)) or 1.0
        examples = [(e[0], e[1], e[2], 1.0 if equal else e[3] / mean_w) for e in examples]
        m = {k: np.zeros_like(getattr(self, k)) for k in self.PARAMS}
        v = {k: np.zeros_like(getattr(self, k)) for k in self.PARAMS}
        b1, b2, eps = 0.9, 0.999, 1e-8
        for step in range(1, iters + 1):
            pick = rng.choice(len(examples), size=min(batch, len(examples)), replace=False)
            _, g = self.loss_and_grads(*self.batch([examples[i] for i in pick]), l2=l2)
            for k in self.PARAMS:
                m[k] = b1 * m[k] + (1 - b1) * g[k]
                v[k] = b2 * v[k] + (1 - b2) * g[k] ** 2
                upd = lr * (m[k] / (1 - b1 ** step)) / (np.sqrt(v[k] / (1 - b2 ** step)) + eps)
                setattr(self, k, getattr(self, k) - upd)
            self.E[0] = 0.0
        self._memo.clear()
        report = {"train_loss": self.loss_and_grads(*self.batch(examples))[0], "examples": len(examples),
                  "ess": ess, "ess_share": ess / len(w), "equal_weights": bool(equal)}
        if holdout:
            mw = float(np.mean([e[3] for e in holdout])) or 1.0
            report["holdout_loss"] = self.loss_and_grads(*self.batch([(e[0], e[1], e[2], e[3] / mw)
                                                                        for e in holdout]))[0]
        return report

    # --- files ----------------------------------------------------------------------------------------------
    def save(self, path) -> None:
        meta = {"vocab": self.vocab, "embed": self.embed, "width": self.width, "hidden": self.hidden,
                "ctx": list(CTX), "card": list(CARD), "fit": list(FIT), "info": self.info}
        with open(path, "wb") as f:
            np.savez(f, meta=np.array(json.dumps(meta, ensure_ascii=False)),
                     **{k: getattr(self, k) for k in self.PARAMS})

    @classmethod
    def load(cls, path) -> "HandValue":
        with np.load(Path(path), allow_pickle=False) as z:
            meta = json.loads(str(z["meta"]))
            assert meta["ctx"] == list(CTX) and meta["card"] == list(CARD) and meta["fit"] == list(FIT), path
            out = cls(meta["vocab"], meta["embed"], meta["width"], meta["hidden"], info=meta.get("info"))
            for k in cls.PARAMS:
                setattr(out, k, np.array(z[k], dtype=float))
        return out


_LOADED: dict = {}


def load_cached(path) -> HandValue:
    key = str(Path(path).resolve())
    if key not in _LOADED:
        _LOADED[key] = HandValue.load(key)
    return _LOADED[key]


def default_student(state, player: int) -> HandValue:
    """The student for `extra_features(state, me, ("hand_value",))` called without one: SVSIM_HV, a student file or
    a models folder (its <pairing>-hv.npz, by the pairing's keys as the models are found), else the installed
    folder's. None found: ValueError."""
    import os
    from svsim.learn.model import ALIASES, matchup_keys
    where = os.environ.get("SVSIM_HV")
    if where and Path(where).is_file():
        return load_cached(where)
    folders = [Path(where)] if where else []
    folders.append(Path(__file__).resolve().parent / "phased_models")
    for folder in folders:
        for k in matchup_keys(state, player, ALIASES):
            names = [x if isinstance(x, str) else x.name.lower() for x in k]
            path = folder / f"{names[0]}-{names[1]}-hv.npz"
            if path.is_file():
                return load_cached(path)
    raise ValueError("the hand_value feature found no student: set SVSIM_HV to a student file or a models folder")


def examples_from(records_path, labels_path, model: HandValue, every: int = 0, keep_out: bool = False) -> list:
    """Training examples from game records (JSON lines) and labels (JSON lines, one per (position, card)):
    {"g": the game's "g" (its line if the record has none), "i": the action index the position is before, "player",
    "uid": the card, "t": T(c | s), and "var" (or "seeds": the per-seed T, whose variance is used, floored at
    VAR_FLOOR)}. The weight is 1 / var. Cards drawn this turn are unknown as in the search (the record's turn_starts).
    `every` > 0: only games whose line % every != 0 (keep_out: only those == 0), the hold-out split."""
    from svsim.tools import records as R
    games = {}
    for n, line in enumerate(open(records_path, encoding="utf-8")):
        if line.strip():
            rec = json.loads(line)
            games[rec.get("g", n)] = rec
    by_game: dict = {}
    for line in open(labels_path, encoding="utf-8"):
        lab = json.loads(line)
        if every and ((lab["g"] % every == 0) != keep_out):
            continue
        by_game.setdefault(lab["g"], []).append(lab)
    out = []
    for g, labs in sorted(by_game.items()):
        record = games[g]
        want = {}
        for lab in labs:
            want.setdefault(lab["i"], []).append(lab)
        starts = record.get("turn_starts") or []
        for i, (state, _) in enumerate(R.steps(record)):
            if i not in want:
                continue
            for lab in want[i]:
                start = max((s for s in starts if s["player"] == lab["player"] and s["i"] <= i),
                            key=lambda s: s["i"], default=None)
                unknown = set(start["deck"]) if start else None
                var = lab.get("var")
                if var is None and lab.get("seeds"):
                    var = float(np.var(lab["seeds"], ddof=1)) if len(lab["seeds"]) > 1 else 1.0
                w = 1.0 / max(var if var is not None else 1.0, VAR_FLOOR)
                out.append(model.example(state, lab["player"], lab["uid"], lab["t"], w, unknown))
            if i >= max(want):
                break
    return out


def _no_change(rows: list, cid: int) -> bool:
    """Every seed's keep:<cid> is exactly 0 with se 0: the restriction played the line itself on every
    determinization. That says it changed nothing, not that the card is worth exactly 0 (the architecture
    thread 02:38Z): such labels are left out."""
    got = [r["res"][f"keep:{cid}"] for r in rows if f"keep:{cid}" in r["res"]]
    return bool(got) and all(x.get("teacher") == 0 and x.get("se", 0.0) == 0 for x in got)


def _teacher_label(rows: list, cid: int):
    """(T, var) of keep:<cid> over a position's teacher rows (one per seed): T the mean of the seeds' "teacher",
    var the mean of their se^2 over the number of seeds (floored at VAR_FLOOR); None if no seed has it."""
    got = [r["res"][f"keep:{cid}"] for r in rows if f"keep:{cid}" in r["res"]]
    if not got:
        return None
    t = float(np.mean([x["teacher"] for x in got]))
    var = float(np.mean([x.get("se", 0.0) ** 2 for x in got])) / len(got)
    return t, max(var, VAR_FLOOR)


def examples_from_teacher(model: HandValue, selfplay, positions, teacher, split: str | None = "train",
                          stats: dict | None = None) -> list:
    """Training examples from the analysis line's student data (analysis/card-value/student_data.py): the
    self-play records, positions.jsonl ({"n", "g", "at", "seat", "split"}: own-turn starts) and teacher.jsonl
    ({"n", "s", "res": {"keep:<card id>": {"teacher", "se", ...}}}, a row per seed). Games are matched by their
    records' "g", not by line (netdata writes games as they finish). T(c) = keep:<c>, one copy of
    c taken out of the hand (the first), weight 1 / var. Only cards in hand at the turn start: the teacher's line
    can also play a card drawn or made during the turn, which the student doesn't price; labels whose restriction
    changed nothing (_no_change) are left out too. `split`: "train", "val" or None (both); `stats`, if given,
    counts what was left out ("not_in_hand", "no_change")."""
    from svsim.tools import records as R
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply
    games = {}
    for line in open(selfplay, encoding="utf-8"):
        if line.strip():
            rec = json.loads(line)
            games[rec["g"]] = rec
    pos = {}
    for line in open(positions, encoding="utf-8"):
        if line.strip():
            p = json.loads(line)
            if split is None or p.get("split") == split:
                pos[p["n"]] = p
    rows: dict = {}
    for line in open(teacher, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            if r["n"] in pos:
                rows.setdefault(r["n"], []).append(r)
    out = []
    stats = stats if stats is not None else {}
    stats.setdefault("not_in_hand", 0)
    stats.setdefault("no_change", 0)
    for n in sorted(rows):
        p = pos[n]
        state = R.start(games[p["g"]])
        for a in games[p["g"]]["actions"][:p["at"]]:
            apply(state, from_dict(a))
        me = p["seat"]
        hand = state.players[me].hand
        cids = sorted({int(k.split(":")[1]) for r in rows[n] for k in r["res"] if k.startswith("keep:")})
        for cid in cids:
            card = next((c for c in hand if c.defn.card_id == cid), None)
            if card is None:                       # drawn or made during the turn: not this hand's
                stats["not_in_hand"] += 1
                continue
            if _no_change(rows[n], cid):
                stats["no_change"] += 1
                continue
            label = _teacher_label(rows[n], cid)
            if label is not None:
                ex = model.example(state, me, card.uid, label[0], 1.0 / label[1], None)
                out.append(ex + (n,))
    return out


def spearman(x, y) -> float:
    rx = np.argsort(np.argsort(x, kind="stable"), kind="stable").astype(float)
    ry = np.argsort(np.argsort(y, kind="stable"), kind="stable").astype(float)
    if np.std(rx) == 0 or np.std(ry) == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def predictions(model: HandValue, examples) -> np.ndarray:
    """dH of each example's removed card."""
    out = []
    for (D, Xs, Xq, z), r, _, _ in (e[:4] for e in examples):
        U = model.units(D, Xs, Xq, z)
        S = U.sum(axis=0)
        out.append(model.head(S) - model.head(S - U[r]))
    return np.array(out)


def main() -> None:
    import argparse
    import hashlib
    parser = argparse.ArgumentParser(description="Fit the hand-value student on the analysis line's student data.")
    parser.add_argument("--selfplay", required=True)
    parser.add_argument("--positions", required=True)
    parser.add_argument("--teacher", required=True)
    parser.add_argument("--out", required=True, help="the student file (.npz)")
    parser.add_argument("--embed", type=int, default=8)
    parser.add_argument("--width", type=int, default=16)
    parser.add_argument("--hidden", type=int, default=16)
    parser.add_argument("--iters", type=int, default=3000)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--l2", type=float, default=1e-4)
    parser.add_argument("--batch", type=int, default=256)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    vocab = set()
    for line in open(args.selfplay, encoding="utf-8"):
        if line.strip():
            for deck in json.loads(line)["decks"]:
                vocab.update(int(c) for c in deck)
    sha = {k: hashlib.sha256(Path(getattr(args, k)).read_bytes()).hexdigest()
           for k in ("selfplay", "positions", "teacher")}
    model = HandValue(sorted(vocab), args.embed, args.width, args.hidden, args.seed,
                      info={"data": sha, "iters": args.iters, "lr": args.lr, "l2": args.l2, "batch": args.batch})
    left_out = {"train": {}, "val": {}}
    train = examples_from_teacher(model, args.selfplay, args.positions, args.teacher, "train", left_out["train"])
    val = examples_from_teacher(model, args.selfplay, args.positions, args.teacher, "val", left_out["val"])
    report = model.fit([e[:4] for e in train], args.iters, args.lr, args.l2, args.batch, args.seed,
                       holdout=[e[:4] for e in val] or None)
    for name, ex in (("train", train), ("val", val)):
        if ex:
            report[f"spearman_{name}"] = spearman(predictions(model, ex), np.array([e[2] for e in ex]))
            report[f"{name}_labels"] = len(ex)
    report["left_out"] = left_out
    model.info["report"] = report
    model.save(args.out)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
