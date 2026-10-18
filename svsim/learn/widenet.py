"""A SetNet grown wider, with a trainable leaky ReLU (D14b, the architecture thread 2026-10-18 19:38Z).

Every layer of phi and rho gets `extra` more units (WideSetNet.grown_from: twice the width, phi 128-128 and rho
256-128 from 64-64 / 128-64). The grown net starts as the net it grows from, to the last bit:
- the old units keep their weights, and every product the old net makes is made as before, on the same arrays;
- what the new units add to an old unit goes through blocks of their own (`*_no`, new inputs to old outputs, and
  v3_n, the new last-layer units to the output), 0 at the start, each added after the old net's own term (x + 0 is
  x);
- the new units' input weights (`*_on`, old inputs to new outputs, and `*_nn`) start random (He, the constructor's
  fixed generator), so they compute from the start and their output weights get gradient;
- the activation is a PReLU, max(z, 0) + a·min(z, 0), with one negative slope `a` per layer (phi 1, phi 2, rho 1,
  rho 2) shared by its old and new units. The slopes start at 0, where it is the old net's ReLU to the last bit,
  and are trained with the weights (no l2).
Inputs v1, with or without the mid-turn flag; no opponent-hand zone. A file has a "wide" key (the extra widths);
SetNet.load reads it as this class.
"""
from __future__ import annotations

import numpy as np

from svsim.learn import setnet as SN
from svsim.learn import tokens as T
from svsim.learn.setnet import NZ, SetNet, _GLOBAL_SCALE, _Printed, _segsum, dynamic

NEW = ("W1s_n", "W1d_n", "b1_n", "W2_no", "W2_on", "W2_nn", "b2_n", "V1_no", "V1_on", "V1_nn", "c1_n",
       "V2_no", "V2_on", "V2_nn", "c2_n", "v3_n", "a")
_L2 = ("W1s", "W1d", "W2", "V1", "V2", "v3", "W1s_n", "W1d_n", "W2_no", "W2_on", "W2_nn", "V1_no", "V1_on",
       "V1_nn", "V2_no", "V2_on", "V2_nn", "v3_n")


def _f(z: np.ndarray, a) -> np.ndarray:
    """PReLU: max(z, 0) + a·min(z, 0); at a = 0 the same numbers as np.maximum(z, 0) (x + 0 is x)."""
    return np.maximum(z, 0) + a * np.minimum(z, 0)


def _df(z: np.ndarray, a) -> np.ndarray:
    return np.where(z > 0, 1.0, a)


class WideSetNet(SetNet):
    PARAMS = SetNet.PARAMS + NEW

    def __init__(self, static_width: int, phi=(64, 64), rho=(128, 64), extra=(64, 64, 128, 64), seed: int = 0,
                 info=None, flag: bool = False):
        super().__init__(static_width, phi=phi, rho=rho, seed=seed, info=info, flag=flag)
        rng = np.random.default_rng(seed)
        self.extra = tuple(int(x) for x in extra)
        n1, n2, m1, m2 = self.extra
        h1, h2 = self.phi
        r1, r2 = self.rho
        D, G = len(SN.DYN_NAMES), len(T.GLOBALS)
        fin = static_width + D
        u = NZ * h2 + G + int(self.flag)            # the old rho input (the zone sums of the old phi units, globals)
        un = NZ * n2                                 # the new phi units' zone sums
        self.W1s_n = rng.normal(0, np.sqrt(2 / fin), (static_width, n1))
        self.W1d_n = rng.normal(0, np.sqrt(2 / fin), (D, n1))
        self.b1_n = np.zeros(n1)
        self.W2_no = np.zeros((n1, h2))
        self.W2_on = rng.normal(0, np.sqrt(2 / (h1 + n1)), (h1, n2))
        self.W2_nn = rng.normal(0, np.sqrt(2 / (h1 + n1)), (n1, n2))
        self.b2_n = np.zeros(n2)
        self.V1_no = np.zeros((un, r1))
        self.V1_on = rng.normal(0, np.sqrt(2 / (u + un)) / 4, (u, m1))
        self.V1_nn = rng.normal(0, np.sqrt(2 / (u + un)) / 4, (un, m1))
        self.c1_n = np.zeros(m1)
        self.V2_no = np.zeros((m1, r2))
        self.V2_on = rng.normal(0, np.sqrt(2 / (r1 + m1)), (r1, m2))
        self.V2_nn = rng.normal(0, np.sqrt(2 / (r1 + m1)), (m1, m2))
        self.c2_n = np.zeros(m2)
        self.v3_n = np.zeros(m2)
        self.a = np.zeros(4)

    @classmethod
    def grown_from(cls, net: SetNet, extra=None, info=None) -> "WideSetNet":
        """`net` (v1, ReLU, no opponent-hand zone) with `extra` more units per layer (default: as many again), the
        new blocks as in the module docstring: it scores every position as `net` does, to the last bit."""
        if net.inputs != "v1" or net.slope != 0.0 or net.ophand or isinstance(net, WideSetNet):
            raise ValueError("a v1 ReLU net without the opponent-hand zone grows wider")
        extra = tuple(extra or (net.phi[0], net.phi[1], net.rho[0], net.rho[1]))
        out = cls(net.static.shape[1], phi=net.phi, rho=net.rho, extra=extra, flag=net.flag, info=info)
        for k in SetNet.PARAMS + ("smean", "sstd", "card_ids", "static"):
            setattr(out, k, np.array(getattr(net, k)))
        return out

    # --- forward / backward -----------------------------------------------------------------------------------
    def forward(self, cards, dyn, count, seg, glob, keep=False, static=None, hand=None):
        if hand is not None:
            raise ValueError("a wide net has no opponent-hand zone")
        a = self.a
        B = glob.shape[0]
        S = self._S(static)
        A1 = (S @ self.W1s)[cards] + dyn @ self.W1d + self.b1
        A1n = (S @ self.W1s_n)[cards] + dyn @ self.W1d_n + self.b1_n
        H1, H1n = _f(A1, a[0]), _f(A1n, a[0])
        A2 = H1 @ self.W2 + self.b2 + H1n @ self.W2_no
        A2n = H1 @ self.W2_on + H1n @ self.W2_nn + self.b2_n
        H2, H2n = _f(A2, a[1]), _f(A2n, a[1])
        P = _segsum(H2, count, seg, B * NZ).reshape(B, -1)
        Pn = _segsum(H2n, count, seg, B * NZ).reshape(B, -1)
        U = np.concatenate([P, glob], axis=1)
        B1 = U @ self.V1 + self.c1 + Pn @ self.V1_no
        B1n = U @ self.V1_on + Pn @ self.V1_nn + self.c1_n
        Z1, Z1n = _f(B1, a[2]), _f(B1n, a[2])
        B2 = Z1 @ self.V2 + self.c2 + Z1n @ self.V2_no
        B2n = Z1 @ self.V2_on + Z1n @ self.V2_nn + self.c2_n
        Z2, Z2n = _f(B2, a[3]), _f(B2n, a[3])
        out = Z2 @ self.v3 + self.c3[0] + Z2n @ self.v3_n
        if keep:
            return out, (S, A1, A1n, H1, H1n, A2, A2n, P, Pn, U, B1, B1n, Z1, Z1n, B2, B2n, Z2, Z2n)
        return out

    def grads(self, batch, y, l2: float = 0.0):
        cards, dyn, count, seg, glob = batch[:5]
        B = glob.shape[0]
        a = self.a
        z, kept = self.forward(cards, dyn, count, seg, glob, keep=True)
        S, A1, A1n, H1, H1n, A2, A2n, P, Pn, U, B1, B1n, Z1, Z1n, B2, B2n, Z2, Z2n = kept
        p = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
        loss = float(np.mean(-(y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12))))
        g = {}
        ga = np.zeros(4)
        dz = (p - y) / B
        g["v3"], g["v3_n"], g["c3"] = Z2.T @ dz, Z2n.T @ dz, np.array([dz.sum()])
        dZ2, dZ2n = np.outer(dz, self.v3), np.outer(dz, self.v3_n)
        ga[3] = (dZ2 * np.minimum(B2, 0)).sum() + (dZ2n * np.minimum(B2n, 0)).sum()
        dB2, dB2n = dZ2 * _df(B2, a[3]), dZ2n * _df(B2n, a[3])
        g["V2"], g["V2_no"], g["V2_on"], g["V2_nn"] = Z1.T @ dB2, Z1n.T @ dB2, Z1.T @ dB2n, Z1n.T @ dB2n
        g["c2"], g["c2_n"] = dB2.sum(0), dB2n.sum(0)
        dZ1 = dB2 @ self.V2.T + dB2n @ self.V2_on.T
        dZ1n = dB2 @ self.V2_no.T + dB2n @ self.V2_nn.T
        ga[2] = (dZ1 * np.minimum(B1, 0)).sum() + (dZ1n * np.minimum(B1n, 0)).sum()
        dB1, dB1n = dZ1 * _df(B1, a[2]), dZ1n * _df(B1n, a[2])
        g["V1"], g["V1_no"], g["V1_on"], g["V1_nn"] = U.T @ dB1, Pn.T @ dB1, U.T @ dB1n, Pn.T @ dB1n
        g["c1"], g["c1_n"] = dB1.sum(0), dB1n.sum(0)
        h2, n2 = self.phi[1], self.extra[1]
        dP = (dB1 @ self.V1.T + dB1n @ self.V1_on.T)[:, :NZ * h2].reshape(B * NZ, h2)
        dPn = (dB1 @ self.V1_no.T + dB1n @ self.V1_nn.T).reshape(B * NZ, n2)
        dH2, dH2n = dP[seg] * count[:, None], dPn[seg] * count[:, None]
        ga[1] = (dH2 * np.minimum(A2, 0)).sum() + (dH2n * np.minimum(A2n, 0)).sum()
        dA2, dA2n = dH2 * _df(A2, a[1]), dH2n * _df(A2n, a[1])
        g["W2"], g["W2_no"], g["W2_on"], g["W2_nn"] = H1.T @ dA2, H1n.T @ dA2, H1.T @ dA2n, H1n.T @ dA2n
        g["b2"], g["b2_n"] = dA2.sum(0), dA2n.sum(0)
        dH1 = dA2 @ self.W2.T + dA2n @ self.W2_on.T
        dH1n = dA2 @ self.W2_no.T + dA2n @ self.W2_nn.T
        ga[0] = (dH1 * np.minimum(A1, 0)).sum() + (dH1n * np.minimum(A1n, 0)).sum()
        dA1, dA1n = dH1 * _df(A1, a[0]), dH1n * _df(A1n, a[0])
        g["W1d"], g["W1d_n"], g["b1"], g["b1_n"] = dyn.T @ dA1, dyn.T @ dA1n, dA1.sum(0), dA1n.sum(0)
        onehot = np.zeros((len(S), len(cards)))
        onehot[cards, np.arange(len(cards))] = 1.0
        g["W1s"], g["W1s_n"] = S.T @ (onehot @ dA1), S.T @ (onehot @ dA1n)
        g["a"] = ga
        if l2:
            for k in _L2:
                g[k] = g[k] + 2 * l2 * getattr(self, k)
        return loss, g

    # --- one position (the search) ----------------------------------------------------------------------------
    def logit(self, state, player: int, mid: bool = False) -> float:
        """SetNet.logit's v1 path with the new units: the old units' numbers are made by the same products in the
        same order, the new units' after them; the same memos (live rows, pooled cards, pooled zones)."""
        if mid and not self.flag:
            raise ValueError("a net without the mid-turn flag scores turn ends only")
        a = self.a
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
        table = getattr(self, "_table", None)
        if table is None or len(table) != len(self.card_ids):
            S = self._S()
            table = self._table = (S @ self.W1s + self.b1, S @ self.W1s_n + self.b1_n)
            self._pool, self._zone_sums, self._live_sums = {}, {}, {}
        P, Pn = self._live_wide(live, index, table)
        sums = self._zone_sums
        for (z, cards_), (_, key) in zip(pooled, keys):
            total = sums.get((z, key))
            if total is None:
                total, total_n = np.zeros(self.phi[1]), np.zeros(self.extra[1])
                for cid, n in key:
                    h = self._pool.get(cid)
                    if h is None:
                        d = next(c.defn for c in cards_ if c.defn.card_id == cid)
                        tok = np.asarray(T._pooled([_Printed(d)], z)[0][1:], dtype=np.int16)[None, :]
                        x = dynamic(tok)[0]
                        h1 = _f(table[0][index[cid]] + x @ self.W1d, a[0])
                        h1n = _f(table[1][index[cid]] + x @ self.W1d_n, a[0])
                        h = self._pool[cid] = (_f(h1 @ self.W2 + self.b2 + h1n @ self.W2_no, a[1]),
                                               _f(h1 @ self.W2_on + h1n @ self.W2_nn + self.b2_n, a[1]))
                    total += n * h[0]
                    total_n += n * h[1]
                if len(sums) > 50000:
                    sums.clear()
                total = sums[(z, key)] = (total, total_n)
            P[z] = P[z] + total[0]
            Pn[z] = Pn[z] + total[1]
        g = T.globals_of(state, player) / _GLOBAL_SCALE
        if self.flag:
            g = np.append(g, np.float32(1.0 if mid else 0.0))
        u, un = np.concatenate([P.reshape(-1), g]), Pn.reshape(-1)
        z1 = _f(u @ self.V1 + self.c1 + un @ self.V1_no, a[2])
        z1n = _f(u @ self.V1_on + un @ self.V1_nn + self.c1_n, a[2])
        z2 = _f(z1 @ self.V2 + self.c2 + z1n @ self.V2_no, a[3])
        z2n = _f(z1 @ self.V2_on + z1n @ self.V2_nn + self.c2_n, a[3])
        return float(z2 @ self.v3 + self.c3[0] + z2n @ self.v3_n)

    def _live_wide(self, live, index, table):
        """(old, new) live phi sums per zone, fresh arrays; memoized on the exact live rows (SetNet._live_part)."""
        memo = getattr(self, "_live_sums", None)
        if memo is None:
            memo = self._live_sums = {}
        key = tuple(map(tuple, live))
        hit = memo.get(key)
        if hit is not None:
            return hit[0].copy(), hit[1].copy()
        a = self.a
        P, Pn = np.zeros((NZ, self.phi[1])), np.zeros((NZ, self.extra[1]))
        if live:
            rows = np.asarray(live, dtype=np.int64)
            cards = [index[c] for c in rows[:, 0].tolist()]
            x = dynamic(rows[:, 1:])
            H1, H1n = _f(table[0][cards] + x @ self.W1d, a[0]), _f(table[1][cards] + x @ self.W1d_n, a[0])
            H2 = _f(H1 @ self.W2 + self.b2 + H1n @ self.W2_no, a[1])
            H2n = _f(H1 @ self.W2_on + H1n @ self.W2_nn + self.b2_n, a[1])
            zones = rows[:, 1 + SN._ZONE]
            for z in sorted(set(zones.tolist())):
                P[z] = H2[zones == z].sum(axis=0)
                Pn[z] = H2n[zones == z].sum(axis=0)
        if len(memo) > 50000:
            memo.clear()
        memo[key] = (P.copy(), Pn.copy())
        return P, Pn

    # --- files ------------------------------------------------------------------------------------------------
    def save(self, path) -> None:
        arrays = {k: getattr(self, k) for k in self.PARAMS}
        arrays.update(smean=self.smean, sstd=self.sstd, card_ids=self.card_ids, static=self.static,
                      phi=np.array(self.phi), rho=np.array(self.rho), slope=np.array(0.0),
                      wide=np.array(self.extra), info=np.array(__import__("json").dumps(self.info)))
        if self.flag:
            arrays["flag"] = np.array(True)
        np.savez(path, **arrays)

    @classmethod
    def from_file(cls, z) -> "WideSetNet":
        import json
        net = cls(z["static"].shape[1], phi=tuple(int(x) for x in z["phi"]), rho=tuple(int(x) for x in z["rho"]),
                  extra=tuple(int(x) for x in z["wide"]), flag=bool(z["flag"]) if "flag" in z.files else False)
        for k in net.PARAMS + ("smean", "sstd", "card_ids", "static"):
            setattr(net, k, np.array(z[k]))
        net.info = json.loads(str(z["info"]))
        return net
