"""A small policy head: which moves the search tends to spend its visits on, as a prior.

Route b of the morning plan (2026-10-07): the search spreads its 100
iterations almost evenly (the most-visited move gets 41% of the visits on
average; 10% of decisions have one move with 80% or more), and it overturns
the greedy first choice in a third of them, most at the start of turns and
late in the game. A prior learned from the recorded visit counts (π,
learn.netdata) should let the same iterations go to the right moves.

A move is encoded from the player's side like search.mcts.action_key (what
kind of move, which card, which target), never by uid:
- kind: play a card, attack, evolve, super-evolve, end the turn, engage,
  fuse, use the bonus play point, other;
- the source card, one-hot over the model's card vocabulary, with its cost
  and the play points left after paying it;
- the target: the enemy leader, an enemy follower, an own follower, none;
  the target card one-hot; for attacks the attacker's attack and the
  target's defense and attack (does it die, does it kill);
plus the position's totals (learn.encode's dense part, no card zones: the
smooth inputs).

`PolicyNet`: one tanh layer on [position, move] -> a score; the policy is
the softmax of the scores over the legal moves, fitted to π by cross
entropy (numpy, trained and run the same way as learn.net).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from svsim.core.actions import Attack, EndTurn, Engage, Evolve, Fuse, PlayCard, UseBonusPP

KINDS = ("play", "attack", "evolve", "super", "end", "engage", "fuse", "bonus", "other")
TARGETS = ("enemy_leader", "enemy_follower", "own_follower", "none")
POLICIES = Path(__file__).resolve().parent / "policies"


def _kind(action) -> str:
    if isinstance(action, PlayCard):
        return "play"
    if isinstance(action, Attack):
        return "attack"
    if isinstance(action, Evolve):
        return "super" if action.super_ else "evolve"
    if isinstance(action, EndTurn):
        return "end"
    if isinstance(action, Engage):
        return "engage"
    if isinstance(action, Fuse):
        return "fuse"
    if isinstance(action, UseBonusPP):
        return "bonus"
    return "other"


def _source(state, action):
    me = state.active
    uid = getattr(action, "uid", None) or getattr(action, "attacker", None)
    if uid is None:
        return None
    return state.in_hand(me, uid) or state.in_play(uid)


def _target(state, action):
    from svsim.core.engine import leader_of
    me = state.active
    uid = getattr(action, "target", None)
    if uid is None:
        targets = getattr(action, "targets", ()) or ()
        uid = targets[0] if targets else None
    if uid is None:
        return "none", None
    side = leader_of(uid)
    if side is not None:
        return ("enemy_leader" if side != me else "own_follower"), None
    card = state.in_play(uid)
    if card is None:
        return "none", None
    return ("enemy_follower" if card.owner != me else "own_follower"), card


def move_width(vocab: dict) -> int:
    return len(KINDS) + 2 * len(vocab) + len(TARGETS) + 6


def move_features(state, action, vocab: dict) -> list[float]:
    me = state.active
    v = len(vocab)
    out = [0.0] * move_width(vocab)
    out[KINDS.index(_kind(action))] = 1.0
    base = len(KINDS)
    src = _source(state, action)
    if src is not None and src.defn.card_id in vocab:
        out[base + vocab[src.defn.card_id]] = 1.0
    base += v
    where, tgt = _target(state, action)
    if tgt is not None and tgt.defn.card_id in vocab:
        out[base + vocab[tgt.defn.card_id]] = 1.0
    base += v
    out[base + TARGETS.index(where)] = 1.0
    base += len(TARGETS)
    p = state.players[me]
    cost = getattr(src, "cost", 0) if isinstance(action, PlayCard) and src is not None else 0
    atk = src.atk if isinstance(action, Attack) and src is not None else 0
    t_life = max(tgt.life, 0) if tgt is not None else 0
    t_atk = tgt.atk if tgt is not None else 0
    out[base:base + 6] = [cost / 10.0, (p.pp - cost) / 10.0, atk / 10.0, t_life / 10.0, t_atk / 10.0,
                          float(isinstance(action, Attack) and tgt is not None and atk >= t_life)]
    return out


class PolicyNet:
    def __init__(self, params: dict, mean, std, vocab: list, info: dict | None = None):
        self.p = {k: np.asarray(x, dtype=np.float64) for k, x in params.items()}
        self.mean, self.std = np.asarray(mean, dtype=np.float64), np.asarray(std, dtype=np.float64)
        self.vocab_list = [int(c) for c in vocab]
        self.vocab = {c: i for i, c in enumerate(self.vocab_list)}
        self.info = info or {}

    def scores_of(self, X):
        h = np.tanh(((X - self.mean) / self.std) @ self.p["W1"] + self.p["b1"])
        return h @ self.p["w2"] + self.p["b2"]

    def scores(self, state, actions) -> np.ndarray:
        """The scores of `actions` (legal moves of the player to act). The first layer is split into the
        position's part, computed once, and each move's part (the same numbers as scores_of)."""
        from svsim.learn import encode as E
        dense = np.asarray(E.raw(state, state.active)[0], dtype=np.float64)
        n = len(dense)
        if not hasattr(self, "_split"):
            W1 = self.p["W1"]
            self._split = (W1[:n] / self.std[:n, None], W1[n:] / self.std[n:, None],
                           self.p["b1"] - (self.mean / self.std) @ W1)
        top, bottom, bias = self._split
        moves = np.array([move_features(state, a, self.vocab) for a in actions], dtype=np.float64)
        h = np.tanh(dense @ top + moves @ bottom + bias)
        return h @ self.p["w2"] + self.p["b2"]

    def priors(self, state, actions) -> np.ndarray:
        """The softmax over `actions` (legal moves of the player to act)."""
        z = self.scores(state, actions)
        z = np.exp(z - z.max())
        return z / z.sum()

    def save(self, path: Path) -> None:
        np.savez(path, mean=self.mean, std=self.std, vocab=np.array(self.vocab_list, dtype=np.int64),
                 info=np.array(json.dumps(self.info, ensure_ascii=False)), **self.p)

    @classmethod
    def load(cls, path: Path) -> "PolicyNet":
        d = np.load(path, allow_pickle=False)
        return cls({k: d[k] for k in ("W1", "b1", "w2", "b2")}, d["mean"], d["std"], d["vocab"].tolist(),
                   json.loads(str(d["info"])))

    @classmethod
    def train(cls, X, starts, target, vocab, X_val=None, starts_val=None, target_val=None, hidden: int = 64,
              epochs: int = 30, lr: float = 2e-3, l2: float = 1e-4, groups_per_batch: int = 256, seed: int = 0,
              info: dict | None = None, say=print) -> "PolicyNet":
        """Cross entropy between π (`target`, per row, summing to 1 within each decision) and the
        softmax of the scores within each decision; decisions are the row ranges starting at `starts`."""
        rng = np.random.default_rng(seed)
        mean, std = X.mean(axis=0), X.std(axis=0)
        std[std < 1e-3] = 1.0
        Xs = (X - mean) / std
        d = X.shape[1]
        p = {"W1": rng.normal(0, 1 / np.sqrt(d), (d, hidden)), "b1": np.zeros(hidden),
             "w2": rng.normal(0, 1 / np.sqrt(hidden), hidden), "b2": np.zeros(())}
        m = {k: np.zeros_like(x) for k, x in p.items()}
        v = {k: np.zeros_like(x) for k, x in p.items()}
        ends = np.append(starts[1:], len(X))

        def loss_of(A, st, tg, params):
            z = np.tanh(A @ params["W1"] + params["b1"]) @ params["w2"] + params["b2"]
            zmax = np.maximum.reduceat(z, st)
            sizes = np.diff(np.append(st, len(z)))
            lse = np.log(np.add.reduceat(np.exp(z - np.repeat(zmax, sizes)), st)) + zmax
            return float(np.sum(tg * (np.repeat(lse, sizes) - z)) / len(st))

        best, best_p, step, worse = float("inf"), None, 0, 0
        Vs = (X_val - mean) / std if X_val is not None else None
        for epoch in range(epochs):
            order = rng.permutation(len(starts))
            for i in range(0, len(order), groups_per_batch):
                gs = np.sort(order[i:i + groups_per_batch])
                idx = np.concatenate([np.arange(starts[g], ends[g]) for g in gs])
                st = np.cumsum([0] + [ends[g] - starts[g] for g in gs[:-1]])
                A, tg = Xs[idx], target[idx]
                h = np.tanh(A @ p["W1"] + p["b1"])
                z = h @ p["w2"] + p["b2"]
                sizes = np.diff(np.append(st, len(z)))
                zmax = np.repeat(np.maximum.reduceat(z, st), sizes)
                e = np.exp(z - zmax)
                soft = e / np.repeat(np.add.reduceat(e, st), sizes)
                dz = (soft - tg) / len(gs)
                g = {"w2": h.T @ dz, "b2": dz.sum()}
                dh = np.outer(dz, p["w2"]) * (1 - h ** 2)
                g["W1"], g["b1"] = A.T @ dh, dh.sum(0)
                step += 1
                for k in p:
                    gk = g[k] + (l2 * p[k] if k in ("W1", "w2") else 0.0)
                    m[k] = 0.9 * m[k] + 0.1 * gk
                    v[k] = 0.999 * v[k] + 0.001 * gk * gk
                    p[k] = p[k] - lr * (m[k] / (1 - 0.9 ** step)) / (np.sqrt(v[k] / (1 - 0.999 ** step)) + 1e-8)
            val = loss_of(Vs, starts_val, target_val, p) if Vs is not None else loss_of(Xs, starts, target, p)
            say(f"  epoch {epoch + 1}: held-out cross entropy {val:.4f}")
            if val < best - 1e-5:
                best, best_p, worse = val, {k: x.copy() for k, x in p.items()}, 0
            else:
                worse += 1
                if worse >= 3:
                    break
        return cls(best_p, mean, std, vocab, dict(info or {}, cross_entropy=best, hidden=hidden))


def decisions(record: dict):
    """(state, legal moves, π, whether it is the turn's first decision) at each decision the search made
    in a self-play record (learn.netdata)."""
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
        if len(legal) != len(t["visits"]) or sum(t["visits"]) <= 0 or len(legal) < 2:
            continue
        total = float(sum(t["visits"]))
        yield state.clone(), legal, [x / total for x in t["visits"]], start


class MatchupPrior:
    """The matchup's policy head as the search's prior (svsim/learn/policies/<craft>-<craft>.npz or
    $SVSIM_POLICY); no prior (None) in matchups without one."""

    def __init__(self, folder: Path | None = None):
        import os
        from svsim.learn.model import split_keys
        folder = folder or Path(os.environ.get("SVSIM_POLICY") or POLICIES)
        self.nets = {}
        if folder.is_dir():
            for path in folder.glob("*.npz"):
                try:
                    key = tuple(split_keys(path.stem))
                except KeyError:
                    continue
                self.nets[key] = PolicyNet.load(path)

    def net_for(self, state):
        from svsim.learn.model import matchup_keys
        return next((self.nets[k] for k in matchup_keys(state, state.active) if k in self.nets), None)

    def priors(self, state, actions):
        net = self.net_for(state)
        return None if net is None else net.priors(state, actions)

    def top(self, state, actions):
        """The highest-scoring of `actions`, or None in a matchup without a policy head."""
        net = self.net_for(state)
        if net is None:
            return None
        z = net.scores(state, actions)
        return actions[int(np.argmax(z))]
