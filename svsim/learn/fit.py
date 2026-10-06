"""Fitting a linear evaluation to outcomes and choices.

Minimizes, over standardized features,
    mean log-loss of P(win) = logistic(w . x) on self-play positions
  + lam * mean over a player's decisions of -log softmax(w . x_candidates)[chosen]
  + l2 * |w|^2 (not on the bias)
by full-batch Adam. The two terms share one scale: the choice term asks the
same win-probability model to rank the player's move above the alternatives.
"""
from __future__ import annotations

import numpy as np


def standardize(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean, std = X.mean(axis=0), X.std(axis=0)
    std[std < 1e-9] = 1.0
    mean[-1], std[-1] = 0.0, 1.0                # the bias column stays a constant 1
    return mean, std


def fit(X: np.ndarray, y: np.ndarray, prefs: list | None = None, lam: float = 1.0, l2: float = 1e-3,
        iters: int = 3000, lr: float = 0.05, mean=None, std=None) -> tuple:
    """Returns (coef, mean, std, report) for features standardized with mean, std."""
    if mean is None:
        mean, std = standardize(X)
    Xs = (X - mean) / std if len(X) else np.zeros((0, len(mean)))
    groups = None
    if prefs:
        C = np.vstack([np.asarray(c) for _, c in prefs])
        Cs = (C - mean) / std
        starts = np.cumsum([0] + [len(c) for _, c in prefs[:-1]])
        chosen = starts + np.array([k for k, _ in prefs])
        groups = (Cs, starts, chosen)
    w = np.zeros(Xs.shape[1])
    m, v = np.zeros_like(w), np.zeros_like(w)
    mask = np.ones_like(w)
    mask[-1] = 0.0

    def loss_grad(w):
        loss, grad = 0.0, l2 * 2 * w * mask
        loss += l2 * float(np.sum((w * mask) ** 2))
        if len(Xs):
            z = Xs @ w
            p = 1 / (1 + np.exp(-z))
            loss += float(np.mean(np.logaddexp(0, z) - y * z))
            grad = grad + Xs.T @ (p - y) / len(Xs)
        if groups is not None:
            Cs, starts, chosen = groups
            z = Cs @ w
            zmax = np.maximum.reduceat(z, starts)
            sizes = np.diff(np.append(starts, len(z)))
            e = np.exp(z - np.repeat(zmax, sizes))
            denom = np.add.reduceat(e, starts)
            lse = np.log(denom) + zmax
            loss += lam * float(np.mean(lse - z[chosen]))
            soft = e / np.repeat(denom, sizes)
            g = (Cs * soft[:, None]).sum(axis=0) - Cs[chosen].sum(axis=0)   # sum of E_softmax[x] - x_chosen
            grad = grad + lam * g / len(starts)
        return loss, grad

    for t in range(1, iters + 1):
        loss, g = loss_grad(w)
        m = 0.9 * m + 0.1 * g
        v = 0.999 * v + 0.001 * g * g
        w -= lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
    report = {"loss": loss}
    if len(Xs):
        report["value_accuracy"] = float(np.mean(((Xs @ w) > 0) == (y > 0.5)))
    if groups is not None:
        report["choice_top1"] = top1(w, groups)
    return w, mean, std, report


def top1(w, groups) -> float:
    """How often the chosen move scores highest among its candidates (a tie for
    the top between k moves counts 1/k)."""
    Cs, starts, chosen = groups
    z = Cs @ w
    sizes = np.diff(np.append(starts, len(z)))
    hits = 0.0
    for s, n, c in zip(starts, sizes, chosen):
        best = np.max(z[s:s + n])
        if z[c] >= best - 1e-9:
            hits += 1.0 / np.sum(z[s:s + n] >= best - 1e-9)
    return hits / len(starts)


def choice_groups(prefs: list, mean, std):
    C = np.vstack([np.asarray(c) for _, c in prefs])
    starts = np.cumsum([0] + [len(c) for _, c in prefs[:-1]])
    return ((C - mean) / std, starts, starts + np.array([k for k, _ in prefs]))
