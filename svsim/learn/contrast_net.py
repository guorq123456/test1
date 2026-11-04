"""Turn-level step 1, the network version: the linear turn-end E plus a set encoder of both fields and the hand,
fitted on the same contrast loss (learn.contrast), numpy only.

The architecture thread 2026-10-09 11:12Z. logit(x) = w . standardized linear features (as learn.contrast)
+ w2 . relu(W1 [field_me, field_op, hand] + b1), where
- field_s = sum over side s's field cards of relu(Wf [Ef[card id], FIELD numbers] + bf) (learn.vnet.FIELD: attack,
  defense, keywords, can still hit a follower / the leader, ...), one encoder for both sides;
- hand = sum over the scored player's hand of tanh(Wa [Eh[card id], CARD] + ba) * sigmoid(Wg [ctx, FIT] + bg), the
  hand-value student's encoder (learn.handvalue: roles, costs, the position);
- card ids by vocabulary index (0: never seen, its rows held at zero). No deck id among the inputs.
The opponent's hand is read only as the linear features read it (size and unseen pool). Training and inference
share forward(); `logit(state, player)` is the batch of one.

Turn ends from a determinized play-out are encoded as they stand (all of the mover's hand known); in the search, a
card drawn after the root would be priced as its pool (learn.handvalue), which this trial doesn't do.
"""
from __future__ import annotations

import math

import numpy as np

from svsim.learn.handvalue import CARD, CTX, FIT, MAX_PP, _card_fit, _card_static, context
from svsim.learn.vnet import FIELD, MAX_FIELD, MAX_HAND, _field_card


def encode(state, player: int, linear: list) -> dict:
    """One turn end for `player`: the linear features given, and the set inputs (card ids raw)."""
    p, o = state.players[player], state.players[1 - player]
    nxt = min(p.max_pp + 1, MAX_PP)
    fid = np.zeros((2, MAX_FIELD), np.int64)
    fnum = np.zeros((2, MAX_FIELD, len(FIELD)), np.float32)
    for s, side in enumerate((p, o)):
        for n, c in enumerate(side.field[:MAX_FIELD]):
            row = _field_card(state, c)
            fid[s, n], fnum[s, n] = row[0], row[1:]
    hid = np.zeros(MAX_HAND, np.int64)
    hst = np.zeros((MAX_HAND, len(CARD)), np.float32)
    hfit = np.zeros((MAX_HAND, len(FIT)), np.float32)
    for n, c in enumerate(p.hand[:MAX_HAND]):
        hid[n], hst[n], hfit[n] = c.defn.card_id, _card_static(c.defn), _card_fit(c.cost, p.pp, nxt)
    return {"x": np.asarray(linear, np.float32), "fid": fid, "fnum": fnum, "hid": hid, "hst": hst, "hfit": hfit,
            "ctx": context(state, player).astype(np.float32)}


def stack(encs: list) -> dict:
    return {k: np.stack([e[k] for e in encs]) for k in encs[0]}


class ContrastNet:
    PARAMS = ("w", "Ef", "Wf", "bf", "Eh", "Wa", "ba", "Wg", "bg", "W1", "b1", "w2")

    def __init__(self, vocab, mean, std, bias: int, embed: int = 8, field: int = 16, hand: int = 16,
                 hidden: int = 32, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.vocab = [int(v) for v in vocab]
        self.index = {v: i + 1 for i, v in enumerate(self.vocab)}
        self.mean, self.std, self.bias = np.asarray(mean, float), np.asarray(std, float), bias
        self.embed, self.field, self.hand, self.hidden = embed, field, hand, hidden
        V, n = len(self.vocab) + 1, len(self.mean)
        ff, fa, fg, fx = embed + len(FIELD), embed + len(CARD), len(CTX) + len(FIT), 2 * field + hand
        self.w = np.zeros(n)
        self.Ef, self.Eh = rng.normal(0, 0.3, (V, embed)), rng.normal(0, 0.3, (V, embed))
        self.Ef[0] = self.Eh[0] = 0.0
        self.Wf, self.bf = rng.normal(0, math.sqrt(2 / ff), (ff, field)), np.zeros(field)
        self.Wa, self.ba = rng.normal(0, 1 / math.sqrt(fa), (fa, hand)), np.zeros(hand)
        self.Wg, self.bg = rng.normal(0, 1 / math.sqrt(fg), (fg, hand)), np.zeros(hand)
        self.W1, self.b1 = rng.normal(0, math.sqrt(2 / fx), (fx, hidden)), np.zeros(hidden)
        self.w2 = np.zeros(hidden)                 # the network starts at 0: the fit starts as the linear model

    def parameters(self) -> int:
        return int(sum(getattr(self, k).size for k in self.PARAMS))

    def indices(self, ids):
        f = np.vectorize(lambda c: self.index.get(int(c), 0) if c else 0, otypes=[np.int64])
        return f(ids) if np.size(ids) else np.zeros_like(ids)

    def prepare(self, batch: dict) -> dict:
        """Card ids to vocabulary indices and the linear features standardized (once per data set)."""
        out = dict(batch)
        out["fi"], out["hi"] = self.indices(batch["fid"]), self.indices(batch["hid"])
        out["xs"] = ((batch["x"].astype(float) - self.mean) / self.std).astype(np.float32)
        return out

    def forward(self, b: dict, keep: bool = False):
        fi, hi = b["fi"], b["hi"]
        FM, HM = (fi > 0).astype(np.float32), (hi > 0).astype(np.float32)
        IF = np.concatenate([self.Ef[fi], b["fnum"]], axis=-1)                # [B, 2, F, ff]
        PF = IF @ self.Wf + self.bf
        AF = np.maximum(PF, 0) * FM[..., None]
        SF = AF.sum(axis=2).reshape(len(fi), -1)                             # [B, 2 * field]
        IA = np.concatenate([self.Eh[hi], b["hst"]], axis=-1)                 # [B, H, fa]
        A = np.tanh(IA @ self.Wa + self.ba)
        IG = np.concatenate([np.repeat(b["ctx"][:, None, :], hi.shape[1], axis=1), b["hfit"]], axis=-1)
        G = 1 / (1 + np.exp(-(IG @ self.Wg + self.bg)))
        SH = (A * G * HM[..., None]).sum(axis=1)
        X1 = np.concatenate([SF, SH], axis=1)
        H1 = np.maximum(X1 @ self.W1 + self.b1, 0)
        z = b["xs"] @ self.w + H1 @ self.w2
        if keep:
            return z, (FM, HM, IF, PF, AF, IA, A, IG, G, X1, H1)
        return z

    def backward(self, b: dict, cache, dz) -> dict:
        FM, HM, IF, PF, AF, IA, A, IG, G, X1, H1 = cache
        g = {"w": b["xs"].T.astype(float) @ dz, "w2": H1.T @ dz}
        dH1 = dz[:, None] * self.w2 * (H1 > 0)
        g["W1"], g["b1"] = X1.T @ dH1, dH1.sum(axis=0)
        dX1 = dH1 @ self.W1.T
        B = len(dz)
        dSF = dX1[:, :2 * self.field].reshape(B, 2, 1, self.field)
        dSH = dX1[:, 2 * self.field:]
        dPF = np.broadcast_to(dSF, AF.shape) * (PF > 0) * FM[..., None]
        g["Wf"] = IF.reshape(-1, IF.shape[-1]).T @ dPF.reshape(-1, self.field)
        g["bf"] = dPF.sum(axis=(0, 1, 2))
        dEf = (dPF @ self.Wf.T)[..., :self.embed]
        g["Ef"] = np.zeros_like(self.Ef)
        np.add.at(g["Ef"], b["fi"].reshape(-1), dEf.reshape(-1, self.embed))
        dU = np.repeat(dSH[:, None, :], A.shape[1], axis=1) * HM[..., None]
        dPA, dPG = dU * G * (1 - A ** 2), dU * A * G * (1 - G)
        g["Wa"], g["ba"] = IA.reshape(-1, IA.shape[-1]).T @ dPA.reshape(-1, self.hand), dPA.sum(axis=(0, 1))
        g["Wg"], g["bg"] = IG.reshape(-1, IG.shape[-1]).T @ dPG.reshape(-1, self.hand), dPG.sum(axis=(0, 1))
        dEh = (dPA @ self.Wa.T)[..., :self.embed]
        g["Eh"] = np.zeros_like(self.Eh)
        np.add.at(g["Eh"], b["hi"].reshape(-1), dEh.reshape(-1, self.embed))
        g["Ef"][0] = g["Eh"][0] = 0.0
        return g

    def loss_and_grads(self, A: dict, B: dict, dT, w, C: dict | None = None, y=None, mu: float = 0.0,
                       l2: float = 0.0, keep=None, signs=None):
        """The contrast loss (learn.contrast.contrast_loss) for the network, with its gradients by name."""
        s = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))
        za, ca = self.forward(A, keep=True)
        zb, cb = self.forward(B, keep=True)
        pa, pb = s(za), s(zb)
        d = pa - pb - dT
        W = float(np.sum(w))
        loss = float(np.sum(w * d * d)) / W
        ga = self.backward(A, ca, 2 * w * d * pa * (1 - pa) / W)
        gb = self.backward(B, cb, -2 * w * d * pb * (1 - pb) / W)
        g = {k: ga[k] + gb[k] for k in ga}
        if C is not None and mu > 0 and len(y):
            zc, cc = self.forward(C, keep=True)
            loss += mu * float(np.mean(np.logaddexp(0, zc) - y * zc))
            gc = self.backward(C, cc, mu * (s(zc) - y) / len(y))
            g = {k: g[k] + gc[k] for k in g}
        for k in ("w", "Wf", "Wa", "Wg", "W1", "w2", "Ef", "Eh"):
            P = getattr(self, k)
            mask = np.ones_like(P)
            if k == "w":
                mask[self.bias] = 0.0
            loss += l2 * float(np.sum((P * mask) ** 2))
            g[k] = g[k] + 2 * l2 * P * mask
        if keep is not None:
            g["w"] = g["w"] * np.where(np.arange(len(self.w)) == self.bias, 1.0, keep)
        return loss, g

    def fit(self, A, B, dT, w=None, C=None, y=None, mu: float = 0.03, l2: float = 1e-4, epochs: int = 6,
            batch: int = 2048, lr: float = 3e-3, seed: int = 0, keep=None, signs=None, report=None) -> dict:
        """Minibatch Adam over the pairs (the calibration rows sampled alongside, in proportion). `signs` as
        learn.fit (on the linear part)."""
        from svsim.learn.fit import project
        rng = np.random.default_rng(seed)
        n = len(dT)
        w = np.ones(n) if w is None else np.asarray(w, float)
        m = {k: np.zeros_like(getattr(self, k)) for k in self.PARAMS}
        v = {k: np.zeros_like(getattr(self, k)) for k in self.PARAMS}
        t = 0
        take = lambda D, idx: {k: val[idx] for k, val in D.items()}
        nc = 0 if C is None else len(y)
        for _ in range(epochs):
            order = rng.permutation(n)
            for i in range(0, n, batch):
                idx = order[i:i + batch]
                cidx = rng.integers(0, nc, size=max(1, len(idx) * nc // max(n, 1))) if nc else None
                _, g = self.loss_and_grads(take(A, idx), take(B, idx), dT[idx], w[idx],
                                           take(C, cidx) if nc else None, y[cidx] if nc else None, mu, l2, keep)
                t += 1
                for k in self.PARAMS:
                    m[k] = 0.9 * m[k] + 0.1 * g[k]
                    v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
                    setattr(self, k, getattr(self, k) - lr * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8))
                if signs is not None:
                    held = self.w[self.bias]
                    self.w = project(self.w, signs)
                    self.w[self.bias] = held
                self.Ef[0] = self.Eh[0] = 0.0
            if report is not None:
                report(self)
        return {"steps": t}

    def logit(self, state, player: int, linear: list) -> float:
        """Inference on one turn end (the batch of one)."""
        return float(self.forward(self.prepare(stack([encode(state, player, linear)])))[0])
