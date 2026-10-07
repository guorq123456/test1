"""A small value network for any moment of a turn (learn.encode), trained and run with numpy.

`ValueNet`: standardized inputs -> tanh layer -> tanh layer -> logit of the
win probability of the player the position is scored for, added to a prior:
the installed linear model's logit (its coefficients are kept in the file)
times a learned scale (the linear models are overconfident: their logits
alone score a worse log loss than a coin flip, so without the scale the
network spent itself shrinking them and lost their ranking), so the network
starts as the linear model (the last layer starts at zero) and learns
corrections where the data supports them. Unlike the linear
models (learn.model), it is fitted on every position the search can be asked
to score (learn.netdata.rows: each decision point and each turn's end), the
moment being one of its inputs, so it can score the positions the search
reaches inside a turn and, with the opponent's turn played out
(`mcts-reply`), at the start of the next one.

`NetLearned` is the evaluation the agents use (`+net` in the arena specs): the
matchup's network where there is one (svsim/learn/nets/<craft>-<craft>.npz, or
$SVSIM_NETS), the learned linear models otherwise. Scores are SCALE * logit,
as models.Learned.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from svsim.core.enums import Craft
from svsim.learn import encode as E
from svsim.learn.model import SCALE, Learned, deck_craft

NETS = Path(__file__).resolve().parent / "nets"


class ValueNet:
    PRIOR = ("prior_coef", "prior_mean", "prior_std")

    def __init__(self, params: dict, mean, std, vocab: list, info: dict | None = None):
        self.p = {k: np.asarray(v, dtype=np.float64) for k, v in params.items()}
        self.prior = all(k in self.p for k in self.PRIOR)
        self.mean, self.std = np.asarray(mean, dtype=np.float64), np.asarray(std, dtype=np.float64)
        self.vocab_list = [int(c) for c in vocab]
        self.vocab = {c: i for i, c in enumerate(self.vocab_list)}
        self.info = info or {}

    # --- inference ----------------------------------------------------------------------------

    def forward(self, X):
        """Logits for rows of raw (unstandardized) inputs."""
        h = np.tanh(((X - self.mean) / self.std) @ self.p["W1"] + self.p["b1"])
        h = np.tanh(h @ self.p["W2"] + self.p["b2"])
        return h @ self.p["w3"] + self.p["b3"] + self.prior_logit(X)

    def prior_logit(self, X):
        if not self.prior:
            return 0.0
        n = len(self.p["prior_coef"])
        scale = float(self.p["prior_scale"]) if "prior_scale" in self.p else 1.0
        return scale * (((X[..., :n] - self.p["prior_mean"]) / self.p["prior_std"]) @ self.p["prior_coef"])

    def logit(self, state, player: int) -> float:
        x = E.vectorize(E.raw(state, player), self.vocab)
        return float(self.forward(np.asarray(x, dtype=np.float64)[None, :])[0])

    # --- files --------------------------------------------------------------------------------

    def save(self, path: Path) -> None:
        np.savez(path, mean=self.mean, std=self.std, vocab=np.array(self.vocab_list, dtype=np.int64),
                 info=np.array(json.dumps(self.info, ensure_ascii=False)), **self.p)

    @classmethod
    def load(cls, path: Path) -> "ValueNet":
        d = np.load(path, allow_pickle=False)
        params = {k: d[k] for k in ("W1", "b1", "W2", "b2", "w3", "b3", "prior_scale") + cls.PRIOR if k in d}
        return cls(params, d["mean"], d["std"], d["vocab"].tolist(), json.loads(str(d["info"])))

    # --- training -----------------------------------------------------------------------------

    @classmethod
    def train(cls, X, y, vocab: list, X_val=None, y_val=None, hidden=(128, 64), epochs: int = 40,
              batch: int = 512, lr: float = 1e-3, l2: float = 1e-4, patience: int = 4, seed: int = 0,
              info: dict | None = None, prior=None, weights=None, say=print) -> "ValueNet":
        """Fits the logistic loss on soft labels y (1 win, 0 loss, 0.5 draw) by minibatch Adam,
        keeping the epoch with the lowest validation loss (stopping after `patience` worse ones).
        `prior`: a LinearValue on the version-2 features (the first inputs) whose logit is added.
        `weights`: a weight per training row (the loss is their weighted mean)."""
        rng = np.random.default_rng(seed)
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        wts = np.ones(len(X)) if weights is None else np.asarray(weights, dtype=np.float64) / np.mean(weights)
        mean, std = X.mean(axis=0), X.std(axis=0)
        std[std < 1e-3] = 1.0
        Xs = (X - mean) / std
        Vs = (np.asarray(X_val, dtype=np.float64) - mean) / std if X_val is not None else None
        d, (h1, h2) = X.shape[1], hidden
        p = {"W1": rng.normal(0, 1 / np.sqrt(d), (d, h1)), "b1": np.zeros(h1),
             "W2": rng.normal(0, 1 / np.sqrt(h1), (h1, h2)), "b2": np.zeros(h2),
             "w3": np.zeros(h2) if prior is not None else rng.normal(0, 1 / np.sqrt(h2), h2), "b3": np.zeros(())}
        if prior is not None:
            p["prior_scale"] = np.ones(())
        fixed = {}
        if prior is not None:
            fixed = {"prior_coef": np.asarray(prior.coef, dtype=np.float64),
                     "prior_mean": np.asarray(prior.mean, dtype=np.float64),
                     "prior_std": np.asarray(prior.std, dtype=np.float64)}
        base = cls(dict(fixed, prior_scale=np.ones(())), mean, std, vocab) if fixed else None
        z0 = base.prior_logit(X) if fixed else np.zeros(len(X))
        v0 = base.prior_logit(np.asarray(X_val, dtype=np.float64)) if fixed and X_val is not None else np.zeros(
            0 if X_val is None else len(X_val))
        m = {k: np.zeros_like(v) for k, v in p.items()}
        v2 = {k: np.zeros_like(v) for k, v in p.items()}

        def loss_of(A, t, params, offset):
            a1 = np.tanh(A @ params["W1"] + params["b1"])
            a2 = np.tanh(a1 @ params["W2"] + params["b2"])
            z = a2 @ params["w3"] + params["b3"] + float(params.get("prior_scale", 1.0)) * offset
            return float(np.mean(np.logaddexp(0, z) - t * z))

        best, best_p, worse, step = float("inf"), None, 0, 0
        for epoch in range(epochs):
            order = rng.permutation(len(Xs))
            for i in range(0, len(order), batch):
                idx = order[i:i + batch]
                A, t = Xs[idx], y[idx]
                a1 = np.tanh(A @ p["W1"] + p["b1"])
                a2 = np.tanh(a1 @ p["W2"] + p["b2"])
                z = a2 @ p["w3"] + p["b3"] + float(p.get("prior_scale", 1.0)) * z0[idx]
                dz = wts[idx] * (1 / (1 + np.exp(-z)) - t) / len(idx)
                g = {"w3": a2.T @ dz, "b3": dz.sum()}
                if "prior_scale" in p:
                    g["prior_scale"] = dz @ z0[idx]
                d2 = np.outer(dz, p["w3"]) * (1 - a2 ** 2)
                g["W2"], g["b2"] = a1.T @ d2, d2.sum(0)
                d1 = (d2 @ p["W2"].T) * (1 - a1 ** 2)
                g["W1"], g["b1"] = A.T @ d1, d1.sum(0)
                step += 1
                for k in p:
                    gk = g[k] + (l2 * p[k] if k in ("W1", "W2", "w3") else 0.0)
                    m[k] = 0.9 * m[k] + 0.1 * gk
                    v2[k] = 0.999 * v2[k] + 0.001 * gk * gk
                    p[k] = p[k] - lr * (m[k] / (1 - 0.9 ** step)) / (np.sqrt(v2[k] / (1 - 0.999 ** step)) + 1e-8)
            if epoch == 0 and fixed:
                start = loss_of(Vs, np.asarray(y_val, dtype=np.float64), dict(p, w3=np.zeros(h2)), v0) \
                    if Vs is not None else None
                say(f"  the prior alone: validation {start:.4f}" if start is not None else "  (prior)")
            train_loss = loss_of(Xs, y, p, z0)
            val_loss = loss_of(Vs, np.asarray(y_val, dtype=np.float64), p, v0) if Vs is not None else train_loss
            say(f"  epoch {epoch + 1}: train {train_loss:.4f}, validation {val_loss:.4f}"
                + (f", prior scale {float(p['prior_scale']):.3f}" if "prior_scale" in p else ""))
            if val_loss < best - 1e-5:
                best, best_p, worse = val_loss, {k: v.copy() for k, v in p.items()}, 0
            else:
                worse += 1
                if worse >= patience:
                    break
        info = dict(info or {}, validation_loss=best, hidden=list(hidden), prior=prior is not None)
        return cls(dict(best_p, **fixed), mean, std, vocab, info)


def load_nets(folder: Path | None = None) -> dict:
    """{(craft, opponent craft): ValueNet} from <craft>-<craft>.npz files."""
    folder = folder or Path(os.environ.get("SVSIM_NETS") or NETS)
    out = {}
    if not folder.exists():
        return out
    for path in folder.glob("*.npz"):
        try:
            mine, theirs = (Craft[part.upper()] for part in path.stem.split("-"))
        except (KeyError, ValueError):
            continue
        out[(mine, theirs)] = ValueNet.load(path)
    return out


class NetLearned:
    """The matchup's value network where there is one; `fallback` (the learned linear models) otherwise."""

    def __init__(self, nets: dict | None = None, fallback=None):
        self.nets = nets if nets is not None else load_nets()
        self.fallback = fallback or Learned()

    def score(self, state, player: int, player_moves_next: bool = False) -> float:
        from svsim.search.evaluate import WIN
        if state.winner is not None:
            return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
        net = self.nets.get((deck_craft(state, player), deck_craft(state, 1 - player)))
        if net is None:
            return self.fallback.score(state, player, player_moves_next)
        return SCALE * net.logit(state, player)
