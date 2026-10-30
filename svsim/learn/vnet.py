"""The value network for turn ends (ENDED): a set encoder of both fields, the hand by the student's encoder, and a
few scalars, then an MLP, giving the scored player's logit of winning.

The architecture thread 2026-10-09 02:18Z (Salem 02:14Z: the linear fits have little left to give). It replaces
the turn-end evaluation only (agent option +vnet / +vnet=FOLDER, VNetEnded); the in-turn (act) model stays.

What it reads, all from the scored player's side of the table and nothing they can't know:
- each card on either field (FIELD): its card id's embedding, attack, defense, maximum defense, evolved, super
  evolved, the nine keywords, whether it can still hit a follower / the leader this turn, follower or not, its
  countdown; summed per side through one shared layer (relu): order doesn't matter, a side's size shows;
- the hand as the student sees it (learn.handvalue): per card tanh(embedding, roles, base cost) times a gate from
  the position and the card's fit to it, summed. Cards drawn after the search's root count as one of their pool,
  as there. The weights can start from a trained student (from_student);
- scalars (SCALARS): the opponent's hand size, both decks, play points, maximum play points, the bonus point,
  evolution points both sides, leader HP both sides, turns both sides, who went first, whether the scored player
  is to act.
No deck id, deck key or pairing among the inputs (a file per pairing: <deck>-<deck>-vnet.npz).

Training (fit) and inference (logit) share one forward pass: inference is the batch of one. The target is
lambda x the game's result + (1 - lambda) x the search's root value (lam, default 0.5), the loss the binary cross
entropy on sigmoid(logit). Plain numpy, no other dependency; saved as .npz without pickle.

Self-play rows (rows_from_record / the `rows` command): one per search decision (the state at the decision, the
search's root value, the game's result) and one per turn end (the state after the end of turn, the root value of
that turn's last decision), each as the raw encoding (`raw`: vocabulary-free, card ids and numbers), so training
needn't replay games.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from svsim.learn.handvalue import CARD, CTX, FIT, MAX_PP, _card_fit, _card_static, context, unknown_uids

KEYWORDS = ("WARD", "STORM", "RUSH", "BANE", "DRAIN", "AMBUSH", "BARRIER", "INTIMIDATE", "AURA")
FIELD = ("atk", "life", "max_life", "evolved", "super_evolved") + tuple(f"kw_{k.lower()}" for k in KEYWORDS) + \
        ("can_hit_follower", "can_hit_leader", "follower", "countdown")
SCALARS = ("op_hand", "me_deck", "op_deck", "pp", "max_pp", "bonus", "me_ep", "me_sep", "op_ep", "op_sep",
           "me_hp", "op_hp", "me_turns", "op_turns", "went_first", "to_act", "op_bonus")
MAX_FIELD, MAX_HAND = 5, 9


# --- raw encoding: vocabulary-free -----------------------------------------------------------------------------
def _field_card(state, c) -> list:
    from svsim.core.enums import Keyword
    fresh = c.entered_turn == state.turn
    can_attack = c.defn.is_follower and c.attacks_made < c.max_attacks
    return [c.defn.card_id, c.atk / 10, c.life / 10, c.max_life / 10, float(c.evolved), float(c.super_evolved)] + \
        [float(bool(c.keywords & getattr(Keyword, k))) for k in KEYWORDS] + \
        [float(can_attack and (not fresh or c.evolved or bool(c.keywords & (Keyword.STORM | Keyword.RUSH)))),
         float(can_attack and (not fresh or bool(c.keywords & Keyword.STORM))),
         float(c.defn.is_follower), (c.countdown or 0) / 5]


def raw(state, player: int, unknown="search") -> dict:
    """The position for `player`, card ids and numbers only. `unknown` as in HandValue.encode."""
    if unknown == "search":
        unknown = unknown_uids(state, player)
    p, o = state.players[player], state.players[1 - player]
    nxt = min(p.max_pp + 1, MAX_PP)
    hidden = lambda c: unknown == "all" or (unknown is not None and c.uid in unknown)
    hand = [[c.defn.card_id, c.cost, float(hidden(c))] + list(_card_static(c.defn)) for c in p.hand]
    out = {"field_me": [_field_card(state, c) for c in p.field][:MAX_FIELD],
           "field_op": [_field_card(state, c) for c in o.field][:MAX_FIELD],
           "hand": hand[:MAX_HAND], "ctx": list(context(state, player)), "pp": p.pp, "next_pp": nxt,
           "scalars": [len(o.hand) / 9, len(p.deck) / 40, len(o.deck) / 40, p.pp / 10, p.max_pp / 10,
                       float(p.bonus_ready), p.ep / 2, p.sep / 2, o.ep / 2, o.sep / 2, p.leader_hp / 20,
                       o.leader_hp / 20, p.turns_taken / 10, o.turns_taken / 10, float(state.first == player),
                       float(state.active == player), float(o.bonus_ready)]}
    if any(h[2] for h in hand):                    # the pool the unknown cards came from
        out["deck"] = [[c.defn.card_id, c.cost] + list(_card_static(c.defn)) for c in p.deck]
    return out


class ValueNet:
    """logit = w3 . relu(W2 relu(W1 [field_me, field_op, hand, scalars] + b1) + b2) + b3."""

    PARAMS = ("Ef", "Wf", "bf", "Eh", "Wa", "ba", "Wg", "bg", "W1", "b1", "W2", "b2", "w3", "b3")

    def __init__(self, vocab, embed: int = 8, field: int = 32, hand: int = 16, hidden=(128, 64), seed: int = 0,
                 info=None):
        self.vocab = [int(v) for v in vocab]
        self.index = {v: i + 1 for i, v in enumerate(self.vocab)}      # 0: a card id never seen in training
        self.embed, self.field, self.hand, self.hidden = embed, field, hand, tuple(hidden)
        self.info = dict(info or {})
        rng = np.random.default_rng(seed)
        V = len(self.vocab) + 1
        ff, fa, fg = embed + len(FIELD), embed + len(CARD), len(CTX) + len(FIT)
        fx = 2 * field + hand + len(SCALARS)
        h1, h2 = self.hidden
        self.Ef = rng.normal(0, 0.3, (V, embed))
        self.Eh = rng.normal(0, 0.3, (V, embed))
        self.Ef[0] = self.Eh[0] = 0.0
        self.Wf, self.bf = rng.normal(0, math.sqrt(2 / ff), (ff, field)), np.zeros(field)
        self.Wa, self.ba = rng.normal(0, 1 / math.sqrt(fa), (fa, hand)), np.zeros(hand)
        self.Wg, self.bg = rng.normal(0, 1 / math.sqrt(fg), (fg, hand)), np.zeros(hand)
        self.W1, self.b1 = rng.normal(0, math.sqrt(2 / fx), (fx, h1)), np.zeros(h1)
        self.W2, self.b2 = rng.normal(0, math.sqrt(2 / h1), (h1, h2)), np.zeros(h2)
        self.w3, self.b3 = rng.normal(0, 1 / math.sqrt(h2), h2), np.zeros(1)
        self._memo: dict = {}

    def parameters(self) -> int:
        return int(sum(getattr(self, k).size for k in self.PARAMS))

    @classmethod
    def from_student(cls, student, vocab=None, **kw) -> "ValueNet":
        """A network whose hand encoder starts as a trained student's (learn.handvalue.HandValue): its embedding
        rows by card id, its card and gate layers."""
        net = cls(vocab if vocab is not None else student.vocab, embed=student.embed, hand=student.width, **kw)
        for cid, i in net.index.items():
            j = student.index.get(cid)
            if j is not None:
                net.Eh[i] = student.E[j]
        net.Wa, net.ba, net.Wg, net.bg = (np.array(getattr(student, k)) for k in ("Wa", "ba", "Wg", "bg"))
        return net

    # --- tensors -------------------------------------------------------------------------------------------
    def _onehot(self, cid):
        d = np.zeros(len(self.vocab) + 1)
        d[self.index.get(int(cid), 0)] = 1.0
        return d

    def tensors(self, r: dict):
        """One raw encoding as (DF [2, F, V], XF [2, F, FIELD], MF [2, F], DH [H, V], XS [H, CARD], XQ [H, FIT],
        MH [H], Z [CTX], X0 [SCALARS]), padded to MAX_FIELD and MAX_HAND."""
        V = len(self.vocab) + 1
        DF, XF, MF = np.zeros((2, MAX_FIELD, V)), np.zeros((2, MAX_FIELD, len(FIELD))), np.zeros((2, MAX_FIELD))
        for s, side in enumerate(("field_me", "field_op")):
            for n, row in enumerate(r[side][:MAX_FIELD]):
                DF[s, n] = self._onehot(row[0])
                XF[s, n] = row[1:]
                MF[s, n] = 1.0
        DH, XS, XQ, MH = np.zeros((MAX_HAND, V)), np.zeros((MAX_HAND, len(CARD))), np.zeros((MAX_HAND, len(FIT))), \
            np.zeros(MAX_HAND)
        pp, nxt = r["pp"], r["next_pp"]
        unknown = [h for h in r["hand"] if h[2]]
        if unknown:                                # rows: card id, cost, (unknown,) then the card's CARD values
            pool = [(h[0], h[1], h[3:]) for h in unknown] + [(d[0], d[1], d[2:]) for d in r.get("deck", [])]
            pd = sum(self._onehot(cid) for cid, _, _ in pool) / len(pool)
            ps = np.mean([st for _, _, st in pool], axis=0)
            ps[-1] = 1.0
            pq = np.mean([_card_fit(cost, pp, nxt) for _, cost, _ in pool], axis=0)
        for n, row in enumerate(r["hand"][:MAX_HAND]):
            cid, cost, hid = row[:3]
            if hid:
                DH[n], XS[n], XQ[n] = pd, ps, pq
            else:
                DH[n], XS[n], XQ[n] = self._onehot(cid), row[3:], _card_fit(cost, pp, nxt)
            MH[n] = 1.0
        return DF, XF, MF, DH, XS, XQ, MH, np.array(r["ctx"], dtype=float), np.array(r["scalars"], dtype=float)

    @staticmethod
    def stack(items):
        return tuple(np.stack([it[k] for it in items]) for k in range(9))

    # --- forward / backward --------------------------------------------------------------------------------
    def forward(self, DF, XF, MF, DH, XS, XQ, MH, Z, X0, keep: bool = False):
        """Logits [B] of a stacked batch; with keep, also what the backward pass needs."""
        B = DF.shape[0]
        IF = np.concatenate([DF @ self.Ef, XF], axis=3)              # [B, 2, F, ff]
        AF = np.maximum(IF @ self.Wf + self.bf, 0.0) * MF[..., None]
        PF = AF.sum(axis=2).reshape(B, 2 * self.field)
        IA = np.concatenate([DH @ self.Eh, XS], axis=2)              # [B, H, fa]
        A = np.tanh(IA @ self.Wa + self.ba)
        IG = np.concatenate([np.repeat(Z[:, None, :], DH.shape[1], axis=1), XQ], axis=2)
        G = 1 / (1 + np.exp(-(IG @ self.Wg + self.bg)))
        SH = (A * G * MH[..., None]).sum(axis=1)
        X = np.concatenate([PF, SH, X0], axis=1)
        H1 = np.maximum(X @ self.W1 + self.b1, 0.0)
        H2 = np.maximum(H1 @ self.W2 + self.b2, 0.0)
        out = H2 @ self.w3 + self.b3[0]
        if keep:
            return out, (IF, AF, IA, A, IG, G, X, H1, H2)
        return out

    def loss_and_grads(self, batch, y, w=None, l2: float = 0.0):
        DF, XF, MF, DH, XS, XQ, MH, Z, X0 = batch
        B = DF.shape[0]
        w = np.ones(B) if w is None else w
        z, (IF, AF, IA, A, IG, G, X, H1, H2) = self.forward(*batch, keep=True)
        p = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
        weights = [getattr(self, k) for k in ("Wf", "Wa", "Wg", "W1", "W2", "w3")] + [self.Ef[1:], self.Eh[1:]]
        bce = -(y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12))
        loss = float(np.mean(w * bce)) + l2 * sum(float(np.sum(P * P)) for P in weights)
        g = {}
        dz = w * (p - y) / B
        g["w3"], g["b3"] = H2.T @ dz + 2 * l2 * self.w3, np.array([dz.sum()])
        dH2 = dz[:, None] * self.w3 * (H2 > 0)
        g["W2"], g["b2"] = H1.T @ dH2 + 2 * l2 * self.W2, dH2.sum(axis=0)
        dH1 = (dH2 @ self.W2.T) * (H1 > 0)
        g["W1"], g["b1"] = X.T @ dH1 + 2 * l2 * self.W1, dH1.sum(axis=0)
        dX = dH1 @ self.W1.T
        dPF = dX[:, :2 * self.field].reshape(B, 2, 1, self.field)
        dSH = dX[:, 2 * self.field:2 * self.field + self.hand]
        dAF = np.broadcast_to(dPF, AF.shape) * (AF > 0)               # AF > 0 only where unmasked and active
        ff = IF.shape[3]
        g["Wf"] = IF.reshape(-1, ff).T @ dAF.reshape(-1, self.field) + 2 * l2 * self.Wf
        g["bf"] = dAF.sum(axis=(0, 1, 2))
        dIF = dAF @ self.Wf.T
        g["Ef"] = np.einsum("bsnv,bsnd->vd", DF, dIF[..., :self.embed]) + 2 * l2 * self.Ef
        dU = np.repeat(dSH[:, None, :], DH.shape[1], axis=1) * MH[..., None]
        dPA = dU * G * (1 - A ** 2)
        dPG = dU * A * G * (1 - G)
        g["Wa"] = IA.reshape(-1, IA.shape[2]).T @ dPA.reshape(-1, self.hand) + 2 * l2 * self.Wa
        g["ba"] = dPA.sum(axis=(0, 1))
        g["Wg"] = IG.reshape(-1, IG.shape[2]).T @ dPG.reshape(-1, self.hand) + 2 * l2 * self.Wg
        g["bg"] = dPG.sum(axis=(0, 1))
        g["Eh"] = np.einsum("bnv,bnd->vd", DH, (dPA @ self.Wa.T)[..., :self.embed]) + 2 * l2 * self.Eh
        g["Ef"][0] = g["Eh"][0] = 0.0
        return loss, g

    def fit(self, items, y, w=None, iters: int = 3000, lr: float = 3e-3, l2: float = 1e-5, batch: int = 256,
            seed: int = 0, holdout=None) -> dict:
        """Adam on the weighted cross entropy. `items`: tensors(raw) per example; y: targets in [0, 1];
        holdout: (items, y) scored, not fitted."""
        rng = np.random.default_rng(seed)
        y = np.asarray(y, dtype=float)
        w = np.ones(len(y)) if w is None else np.asarray(w, dtype=float) / np.mean(w)
        m = {k: np.zeros_like(getattr(self, k)) for k in self.PARAMS}
        v = {k: np.zeros_like(getattr(self, k)) for k in self.PARAMS}
        b1, b2, eps = 0.9, 0.999, 1e-8
        for step in range(1, iters + 1):
            pick = rng.choice(len(items), size=min(batch, len(items)), replace=False)
            _, g = self.loss_and_grads(self.stack([items[i] for i in pick]), y[pick], w[pick], l2)
            for k in self.PARAMS:
                m[k] = b1 * m[k] + (1 - b1) * g[k]
                v[k] = b2 * v[k] + (1 - b2) * g[k] ** 2
                setattr(self, k, getattr(self, k) - lr * (m[k] / (1 - b1 ** step))
                        / (np.sqrt(v[k] / (1 - b2 ** step)) + eps))
            self.Ef[0] = self.Eh[0] = 0.0
        self._memo.clear()
        report = {"train_loss": self.loss_and_grads(self.stack(items), y)[0], "examples": len(items)}
        if holdout:
            report["holdout_loss"] = self.loss_and_grads(self.stack(holdout[0]), np.asarray(holdout[1], float))[0]
        return report

    # --- inference -----------------------------------------------------------------------------------------
    def logit(self, state, player: int) -> float:
        """The scored player's logit of winning, as the search sees the position (its unknown cards)."""
        r = raw(state, player)
        key = json.dumps(r, sort_keys=True)
        hit = self._memo.get(key)
        if hit is None:
            if len(self._memo) >= 100_000:
                self._memo.clear()
            hit = self._memo[key] = float(self.forward(*self.stack([self.tensors(r)]))[0])
        return hit

    # --- files ---------------------------------------------------------------------------------------------
    def save(self, path) -> None:
        meta = {"vocab": self.vocab, "embed": self.embed, "field": self.field, "hand": self.hand,
                "hidden": list(self.hidden), "FIELD": list(FIELD), "SCALARS": list(SCALARS), "CARD": list(CARD),
                "FIT": list(FIT), "CTX": list(CTX), "info": self.info}
        with open(path, "wb") as f:
            np.savez(f, meta=np.array(json.dumps(meta, ensure_ascii=False)),
                     **{k: getattr(self, k) for k in self.PARAMS})

    @classmethod
    def load(cls, path) -> "ValueNet":
        with np.load(Path(path), allow_pickle=False) as z:
            meta = json.loads(str(z["meta"]))
            for k, names in (("FIELD", FIELD), ("SCALARS", SCALARS), ("CARD", CARD), ("FIT", FIT), ("CTX", CTX)):
                assert meta[k] == list(names), (path, k)
            out = cls(meta["vocab"], meta["embed"], meta["field"], meta["hand"], meta["hidden"],
                      info=meta.get("info"))
            for k in cls.PARAMS:
                setattr(out, k, np.array(z[k], dtype=float))
        return out


# --- the evaluator ---------------------------------------------------------------------------------------------
def load_vnets(folder) -> dict:
    """{(deck, opponent deck): ValueNet} from a folder's <deck>-<deck>-vnet.npz files."""
    from svsim.learn.model import split_keys
    out = {}
    for path in sorted(Path(folder).glob("*-vnet.npz")):
        try:
            keys = split_keys(path.name[:-len("-vnet.npz")])
        except (KeyError, ValueError):
            continue
        if len(keys) == 2:
            out[tuple(keys)] = ValueNet.load(path)
    return out


VNETS = Path(__file__).resolve().parent / "vnets"


class VNetEnded:
    """The turn-end score from the pairing's value network where there is one; everything else (the in-turn
    score, pairings without a network) from `base`."""

    def __init__(self, base, nets: dict | None = None, aliases=None):
        self.base = base
        self.nets = nets if nets is not None else load_vnets(VNETS)
        self.aliases = aliases

    def score(self, state, player: int, player_moves_next: bool = False) -> float:
        from svsim.learn.model import SCALE, matchup_keys
        from svsim.search.evaluate import WIN
        if state.winner is not None:
            return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
        if not player_moves_next:
            net = next((self.nets[k] for k in matchup_keys(state, player, self.aliases) if k in self.nets), None)
            if net is not None:
                return SCALE * net.logit(state, player)
        return self.base.score(state, player, player_moves_next)


# --- self-play rows --------------------------------------------------------------------------------------------
def rows_from_record(record: dict) -> list:
    """One row per search decision and per turn end of a game record (learn.netdata's, with "search"):
    {"g", "i", "moment" ("act" | "ended"), "player", "raw", "q" (the search's root value for that player, the last
    decision's for a turn end; None where the search didn't decide), "result" (1 win, 0 loss, 0.5 draw)}.
    Cards drawn during the turn are unknown at a turn end, as in the search (the record's turn_starts)."""
    from svsim.core.actions import EndTurn
    from svsim.core.enums import Phase
    from svsim.learn.handvalue import root
    from svsim.learn.netdata import search_value
    from svsim.search.evaluate import after_end_of_turn
    from svsim.tools import records as R
    winner = record["winner"]
    result = lambda p: 1.0 if winner == p else 0.0 if winner in (0, 1) else 0.5
    thoughts = record.get("search") or []
    starts = record.get("turn_starts") or []
    out, last_q = [], {}
    for i, (state, action) in enumerate(R.steps(record)):
        if state.phase != Phase.MAIN:
            continue
        me = state.active
        q = search_value(thoughts[i] if i < len(thoughts) else None)
        if q is not None:
            last_q[me] = q
            out.append({"g": record.get("g", 0), "i": i, "moment": "act", "player": me, "raw": raw(state, me, None),
                        "q": q, "result": result(me)})
        if isinstance(action, EndTurn):
            ended = after_end_of_turn(state)
            if ended.over:
                continue
            start = max((s for s in starts if s["player"] == me and s["i"] <= i), key=lambda s: s["i"],
                        default=None)
            if start is None:
                r = raw(ended, me, None)
            else:
                with root(me, start["deck"]):
                    r = raw(ended, me)
            out.append({"g": record.get("g", 0), "i": i, "moment": "ended", "player": me, "raw": r,
                        "q": last_q.get(me), "result": result(me)})
            last_q.pop(me, None)
    return out


def target(row: dict, lam: float = 0.5) -> float:
    """lam x the result + (1 - lam) x the root value (the result alone where there is no root value)."""
    if row.get("q") is None:
        return float(row["result"])
    return lam * float(row["result"]) + (1 - lam) * float(row["q"])


def main() -> None:
    import argparse
    import hashlib
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("rows", help="self-play records (learn.netdata, with search) -> rows (JSON lines)")
    a.add_argument("records")
    a.add_argument("--out", required=True)
    b = sub.add_parser("fit", help="rows -> <out> (.npz), held out by game: g %% every == 0")
    b.add_argument("rows")
    b.add_argument("--out", required=True)
    b.add_argument("--moment", default="ended", choices=("ended", "act", "both"))
    b.add_argument("--lam", type=float, default=0.5, help="target = lam x result + (1 - lam) x root value")
    b.add_argument("--hold-out-every", type=int, default=11)
    b.add_argument("--student", default=None, help="start the hand encoder from this student (learn.handvalue)")
    b.add_argument("--iters", type=int, default=3000)
    b.add_argument("--lr", type=float, default=3e-3)
    b.add_argument("--l2", type=float, default=1e-5)
    b.add_argument("--batch", type=int, default=256)
    b.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.cmd == "rows":
        with open(args.out, "w", encoding="utf-8") as f:
            for line in open(args.records, encoding="utf-8"):
                if line.strip():
                    for row in rows_from_record(json.loads(line)):
                        f.write(json.dumps(row) + "\n")
        return
    rows = [json.loads(x) for x in open(args.rows, encoding="utf-8") if x.strip()]
    rows = [r for r in rows if args.moment == "both" or r["moment"] == args.moment]
    vocab = sorted({int(c[0]) for r in rows for side in ("field_me", "field_op") for c in r["raw"][side]} |
                   {int(h[0]) for r in rows for h in r["raw"]["hand"]})
    info = {"rows": hashlib.sha256(Path(args.rows).read_bytes()).hexdigest(), "moment": args.moment,
            "lam": args.lam, "hold_out_every": args.hold_out_every, "iters": args.iters, "lr": args.lr,
            "l2": args.l2, "batch": args.batch}
    if args.student:
        from svsim.learn.handvalue import HandValue
        net = ValueNet.from_student(HandValue.load(args.student), vocab, seed=args.seed, info=info)
    else:
        net = ValueNet(vocab, seed=args.seed, info=info)
    k = args.hold_out_every
    train = [r for r in rows if not (k and r["g"] % k == 0)]
    held = [r for r in rows if k and r["g"] % k == 0]
    report = net.fit([net.tensors(r["raw"]) for r in train], [target(r, args.lam) for r in train], iters=args.iters,
                     lr=args.lr, l2=args.l2, batch=args.batch, seed=args.seed,
                     holdout=([net.tensors(r["raw"]) for r in held], [target(r, args.lam) for r in held])
                     if held else None)
    report["parameters"] = net.parameters()
    net.info["report"] = report
    net.save(args.out)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
