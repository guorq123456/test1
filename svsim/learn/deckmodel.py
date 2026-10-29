"""The deck model: how much a deck scores against another, from what their cards do; no card or deck ids.

    python -m svsim.learn.deckmodel fit --records RUN/deals.jsonl ... --out model.npz
    python -m svsim.learn.deckmodel eval --model model.npz --records RUN/deals.jsonl ...

Why (Salem 2026-10-29 02:22Z): the strong decks change with every pack, so a search that starts from nothing each
time learns nothing; he wants the bot to train a deckbuilding ability that carries to the next pack. A pack's cards
are new, so what carries over can only be what cards do, not which card is good: the model sees each card through
its static row (learn.tokens.static: printed values, keywords, script hooks and properties, the roles and payoffs
measured in the sandbox), the same row the value network reads. A new card is scripted, measured, and scored.

    phi(c) = relu(W1 x_c + b1)                         x_c: the card's static row, standardized
    E(D)   = sum_c n_c(D) phi(c) / 40                  n_c(D): copies of c in the 40-card deck D
    p(D beats O) = sigmoid(v2 . relu(V1 [E(D), E(O), E(D) * E(O)] + c1) + c2)

A card's row is standardized with the training cards' mean and spread, and each column clipped to the range the
training cards span; a column that never varied among them (in the old pool: hook_on_enter, hook_on_engage, which
only set 10's cards have) is read as 0. The model can't know what a feature does that it never saw change, and a
column with a near-0 spread would otherwise put a new card thousands of spreads out (the builder found this in the
value nets, 2026-10-29: +netclip).

So a card's part depends on the deck it sits in only through E (the product term lets a deck's mix meet the
opponent's), and two cards with the same row are the same card to the model. No fixed per-card value either: phi
is a vector whose worth is decided by rho, against a given opponent.

Data: tools.deckbuild's deal records (since 241da436 each carries both lists as deck codes, "deck" and "opp"): a
deal is played from both seats and scores the mean of its two games (1 a win, 0.5 a draw), the label. Each record
also enters mirrored (O against D, 1 - the label). Held out: the deals whose seed hashes to the last tenth.

Use (tools.deckbuild --guide): rank many variants of an incumbent by their predicted mean score against the field,
play the best few; whether a variant replaces the incumbent stays with the games.

`eval` reports the log loss (and against a constant 0.5 and the label's mean), and how well the model orders the
decks of each first halving stage (all of a class's candidates and its incumbent on the same deals): the Spearman
correlation of predicted and measured means per stage, and how often the model's best is the games' best.

Condition of the labels: the opponent's deck list is known (order and hand not).
"""
from __future__ import annotations

import argparse
import json
import math
import zlib
from collections import Counter, defaultdict

import numpy as np

DECK = 40


def decode(code: str) -> list:
    from svsim.cards import deckcode
    return list(deckcode.decode_deck(code)[2])


def load_records(paths) -> list:
    """(deck code, opponent code, label, tag, key, seed) of every deal record with both codes, once per
    (tag, key, seed)."""
    out, seen = [], set()
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:            # a line cut off by a stopped run
                    continue
                if "deck" not in r or "opp" not in r:
                    continue
                k = (path, r["tag"], r["key"], r["seed"])
                if k in seen:
                    continue
                seen.add(k)
                out.append((r["deck"], r["opp"], sum(r["points"]) / len(r["points"]), r["tag"], r["key"], r["seed"]))
    return out


def static_rows(card_ids) -> np.ndarray:
    from svsim.cards.pool import POOL
    from svsim.learn.tokens import static
    return np.stack([static(POOL[i]) for i in card_ids]).astype(np.float64)


class DeckModel:
    def __init__(self, n_in: int, h: int = 32, h2: int = 32, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.p = {"W1": rng.normal(0, 1 / math.sqrt(n_in), (n_in, h)), "b1": np.zeros(h),
                  "V1": rng.normal(0, 1 / math.sqrt(3 * h), (3 * h, h2)), "c1": np.zeros(h2),
                  "v2": rng.normal(0, 1 / math.sqrt(h2), h2), "c2": np.zeros(1)}
        self.mu = np.zeros(n_in)
        self.sd = np.ones(n_in)
        self.lo = np.full(n_in, -np.inf)
        self.hi = np.full(n_in, np.inf)
        self.info: dict = {}

    def standardize(self, X: np.ndarray) -> np.ndarray:
        return np.clip((X - self.mu) / self.sd, self.lo, self.hi)

    def set_scale(self, X: np.ndarray) -> None:
        """Mean, spread and range from the training cards' rows `X`; a column constant there reads 0."""
        self.mu = X.mean(0)
        sd = X.std(0)
        self.sd = np.where(sd > 1e-9, sd, 1.0)
        Z = (X - self.mu) / self.sd
        self.lo, self.hi = Z.min(0), Z.max(0)

    # --- the cards
    def phi(self, X: np.ndarray) -> tuple:
        pre = self.standardize(X) @ self.p["W1"] + self.p["b1"]
        return np.maximum(pre, 0.0), pre

    # --- forward over count matrices (rows: decks, columns: the batch's card vocabulary, entries copies / 40)
    def forward(self, X, Cm, Co):
        Phi, pre = self.phi(X)
        Em, Eo = Cm @ Phi, Co @ Phi
        u = np.concatenate([Em, Eo, Em * Eo], axis=1)
        zpre = u @ self.p["V1"] + self.p["c1"]
        z = np.maximum(zpre, 0.0)
        logit = z @ self.p["v2"] + self.p["c2"][0]
        return logit, (X, Cm, Co, Phi, pre, Em, Eo, u, zpre, z)

    def backward(self, dlogit, cache) -> dict:
        X, Cm, Co, Phi, pre, Em, Eo, u, zpre, z = cache
        g = {"v2": z.T @ dlogit, "c2": np.array([dlogit.sum()])}
        dz = np.outer(dlogit, self.p["v2"]) * (zpre > 0)
        g["V1"], g["c1"] = u.T @ dz, dz.sum(0)
        du = dz @ self.p["V1"].T
        h = Em.shape[1]
        dEm = du[:, :h] + du[:, 2 * h:] * Eo
        dEo = du[:, h:2 * h] + du[:, 2 * h:] * Em
        dPhi = Cm.T @ dEm + Co.T @ dEo
        dpre = dPhi * (pre > 0)
        g["W1"], g["b1"] = self.standardize(X).T @ dpre, dpre.sum(0)
        return g

    # --- use
    def embed(self, decks_ids: list) -> np.ndarray:
        """E(D) of each deck (a list of card ids)."""
        vocab = sorted({i for d in decks_ids for i in d})
        col = {c: j for j, c in enumerate(vocab)}
        C = np.zeros((len(decks_ids), len(vocab)))
        for r, d in enumerate(decks_ids):
            for c, n in Counter(d).items():
                C[r, col[c]] = n / DECK
        Phi, _ = self.phi(static_rows(vocab))
        return C @ Phi

    def head(self, Em: np.ndarray, Eo: np.ndarray) -> np.ndarray:
        u = np.concatenate([Em, Eo, Em * Eo], axis=1)
        z = np.maximum(u @ self.p["V1"] + self.p["c1"], 0.0)
        return 1.0 / (1.0 + np.exp(-(z @ self.p["v2"] + self.p["c2"][0])))

    def predict(self, mine: list, theirs: list) -> np.ndarray:
        """p(mine[k] beats theirs[k]) for each k (lists of card-id lists)."""
        E = self.embed(list(mine) + list(theirs))
        return self.head(E[:len(mine)], E[len(mine):])

    def save(self, path: str) -> None:
        np.savez(path, mu=self.mu, sd=self.sd, lo=self.lo, hi=self.hi, info=json.dumps(self.info), **self.p)

    @classmethod
    def load(cls, path: str) -> "DeckModel":
        z = np.load(path)
        m = cls(z["W1"].shape[0], z["W1"].shape[1], z["V1"].shape[1])
        m.p = {k: z[k] for k in ("W1", "b1", "V1", "c1", "v2", "c2")}
        m.mu, m.sd, m.lo, m.hi, m.info = z["mu"], z["sd"], z["lo"], z["hi"], json.loads(str(z["info"]))
        return m


def held_out(seed: int) -> bool:
    return zlib.crc32(str(seed).encode()) % 10 == 9


def _matrices(records, decks: dict, vocab_col: dict):
    Cm = np.zeros((len(records), len(vocab_col)))
    Co = np.zeros((len(records), len(vocab_col)))
    for r, (d, o, *_rest) in enumerate(records):
        for c, n in decks[d].items():
            Cm[r, vocab_col[c]] = n / DECK
        for c, n in decks[o].items():
            Co[r, vocab_col[c]] = n / DECK
    return Cm, Co


def bce(p, y) -> float:
    p = np.clip(p, 1e-7, 1 - 1e-7)
    return float(np.mean(-(y * np.log(p) + (1 - y) * np.log(1 - p))))


def fit(records: list, h: int = 8, h2: int = 8, epochs: int = 15, batch: int = 512, lr: float = 3e-3,
        l2: float = 1e-2, seed: int = 0, log=print) -> tuple:
    """Adam on the mirrored training deals; the epoch with the best held-out log loss is kept."""
    codes = sorted({d for r in records for d in r[:2]})
    decks = {c: Counter(decode(c)) for c in codes}
    vocab = sorted({i for c in decks.values() for i in c})
    col = {c: j for j, c in enumerate(vocab)}
    X = static_rows(vocab)
    train = [r for r in records if not held_out(r[5])]
    test = [r for r in records if held_out(r[5])]
    train = train + [(o, d, 1.0 - y, *rest) for d, o, y, *rest in train]
    m = DeckModel(X.shape[1], h, h2, seed)
    m.set_scale(X)
    Cm, Co = _matrices(train, decks, col)
    y = np.array([r[2] for r in train])
    Tm, To = _matrices(test, decks, col)
    ty = np.array([r[2] for r in test])
    adam = {k: (np.zeros_like(v), np.zeros_like(v)) for k, v in m.p.items()}
    rng = np.random.default_rng(seed)
    best, best_p, t = float("inf"), None, 0
    for epoch in range(epochs):
        order = rng.permutation(len(train))
        for s in range(0, len(order), batch):
            idx = order[s:s + batch]
            logit, cache = m.forward(X, Cm[idx], Co[idx])
            p = 1.0 / (1.0 + np.exp(-logit))
            g = m.backward((p - y[idx]) / len(idx), cache)
            t += 1
            for k in m.p:
                gk = g[k] + l2 * m.p[k]
                a, b = adam[k]
                a *= 0.9
                a += 0.1 * gk
                b *= 0.999
                b += 0.001 * gk * gk
                m.p[k] = m.p[k] - lr * (a / (1 - 0.9 ** t)) / (np.sqrt(b / (1 - 0.999 ** t)) + 1e-8)
        tp = 1.0 / (1.0 + np.exp(-m.forward(X, Tm, To)[0])) if len(test) else np.array([])
        loss = bce(tp, ty) if len(test) else float("nan")
        if loss < best:
            best, best_p = loss, {k: v.copy() for k, v in m.p.items()}
        if epoch % 10 == 9 or epoch == epochs - 1:
            log(f"  epoch {epoch + 1}: held-out log loss {loss:.4f} (best {best:.4f})")
    if best_p is not None:
        m.p = best_p
    m.info = {"train_deals": len(train) // 2, "test_deals": len(test), "held_out_log_loss": best,
              "h": h, "h2": h2, "epochs": epochs, "l2": l2}
    return m, test


def evaluate(m: DeckModel, records: list) -> dict:
    """Log loss on `records`, and the ordering of each first halving stage's decks."""
    codes = sorted({d for r in records for d in r[:2]})
    ids = {c: decode(c) for c in codes}
    E = dict(zip(codes, m.embed([ids[c] for c in codes])))
    p = m.head(np.stack([E[r[0]] for r in records]), np.stack([E[r[1]] for r in records]))
    y = np.array([r[2] for r in records])
    out = {"deals": len(records), "log_loss": bce(p, y), "log_loss_half": bce(np.full_like(y, 0.5), y),
           "log_loss_mean": bce(np.full_like(y, y.mean()), y)}
    stages = defaultdict(lambda: defaultdict(list))
    for (d, o, yy, tag, key, seed), pp in zip(records, p):
        if tag.endswith(":s0"):
            stages[tag][key].append((yy, pp))
    rhos, hits = [], []
    for tag, keys in stages.items():
        if len(keys) < 3:
            continue
        meas = {k: np.mean([a for a, _ in v]) for k, v in keys.items()}
        pred = {k: np.mean([b for _, b in v]) for k, v in keys.items()}
        ks = sorted(keys)
        rhos.append(_spearman([meas[k] for k in ks], [pred[k] for k in ks]))
        hits.append(max(ks, key=lambda k: pred[k]) == max(ks, key=lambda k: meas[k]))
    if rhos:
        out.update(stages=len(rhos), spearman=float(np.mean(rhos)),
                   spearman_se=float(np.std(rhos, ddof=1) / math.sqrt(len(rhos))) if len(rhos) > 1 else None,
                   best_hit=float(np.mean(hits)), best_hit_chance=float(np.mean([1 / len(stages[t]) for t in stages
                                                                                if len(stages[t]) >= 3])))
    return out


def _spearman(a, b) -> float:
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    if ra.std() == 0 or rb.std() == 0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit")
    f.add_argument("--records", nargs="+", required=True, help="tools.deckbuild deals.jsonl files")
    f.add_argument("--out", required=True)
    # sizes chosen without new-pool labels: leave one class out of the old-pool search O (its class cards never
    # seen, as a new pack's), 2026-10-29: 32/32, l2 1e-4 0.719 (worse than a constant, 0.693); 8/8, l2 1e-2 0.682
    f.add_argument("--h", type=int, default=8)
    f.add_argument("--h2", type=int, default=8)
    f.add_argument("--epochs", type=int, default=15)
    f.add_argument("--l2", type=float, default=1e-2)
    f.add_argument("--seed", type=int, default=0)
    e = sub.add_parser("eval")
    e.add_argument("--model", required=True)
    e.add_argument("--records", nargs="+", required=True)
    args = ap.parse_args()
    if args.cmd == "fit":
        records = load_records(args.records)
        print(f"{len(records)} deals with both lists", flush=True)
        m, test = fit(records, args.h, args.h2, args.epochs, l2=args.l2, seed=args.seed)
        m.info["records"] = args.records
        m.save(args.out)
        print(json.dumps({"held_out": evaluate(m, test), **m.info}, ensure_ascii=False, indent=1))
    else:
        m = DeckModel.load(args.model)
        print(json.dumps(evaluate(m, load_records(args.records)), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
