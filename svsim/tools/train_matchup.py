"""Train a deck's evaluation for one matchup (version-2 features, from self-play outcomes).

    python -m svsim.tools.train_matchup --deck ramp --opponent ramp --games 400 --iterations 2

What worked for the Ramp mirror (2026-10-06, docs/architecture.md): version-2
features (learn.roles: what the cards are for, the field's effects each round,
card counting of what the opponent has left, how long the leader lasts), fitted
to self-play outcomes, with the player's own stock left out (their hand's and
deck's roles): with it in, the search hoarded cards and evolution points
(fewer evolutions and plays a game) and lost to the bot it was meant to beat.
The player's choices are not used either: a one-turn search that learns to keep
resources the way the player does, without the plan the player keeps them for,
plays passively. Each iteration plays --games games with the bot using the
models so far (the new matchup model included), refits on all games so far, and
reports the AUC on a held-out set. The model goes to
svsim/learn/weights/<craft>-<opponent craft>.json (models.Learned picks it for
that matchup, the deck's own model otherwise).
"""
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np

from svsim.learn.model import WEIGHTS, LinearValue

STOCK = ("me_hand_", "me_pool_")      # the player's own stock: left out


def auc(scores, labels) -> float:
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores)); ranks[order] = np.arange(1, len(scores) + 1)
    pos = labels > 0.5
    n_pos, n_neg = pos.sum(), (~pos).sum()
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2) / max(n_pos * n_neg, 1))


def main() -> None:
    from svsim.cards import decks
    from svsim.learn import data, fit as F
    from svsim.learn.features import names, signs
    from svsim.ui.session import DECKS
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--deck", default="ramp", choices=sorted(DECKS))
    parser.add_argument("--opponent", default="ramp", choices=sorted(DECKS))
    parser.add_argument("--games", type=int, default=400, help="self-play games per iteration")
    parser.add_argument("--test", type=int, default=100, help="held-out games")
    parser.add_argument("--iterations", type=int, default=2)
    parser.add_argument("--agent", default="mcts:50+plan+learned", help="the deck's self-play agent")
    parser.add_argument("--opponent-agent", default=None, help="the opponent's (default: --agent)")
    parser.add_argument("--seed", type=int, default=50000)
    args = parser.parse_args()
    mine, theirs = decks.build(DECKS[args.deck][1]), decks.build(DECKS[args.opponent][1])
    craft, op_craft = decks.craft_of(mine), decks.craft_of(theirs)
    out = WEIGHTS / f"{craft.name.lower()}-{op_craft.name.lower()}.json"
    folder = Path(tempfile.mkdtemp())
    for f in WEIGHTS.glob("*.json"):
        shutil.copy(f, folder / f.name)
    os.environ["SVSIM_WEIGHTS"] = str(folder)
    other = args.opponent_agent or args.agent
    N = names(False, 2)
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in N])

    def positions(games, seed):
        rows = data.selfplay(mine, theirs, args.agent, other, games, seed=seed, potential=False, version=2)
        rows = [(x, y) for c, x, y in rows if c == int(craft)]
        return np.array([x for x, _ in rows], float), np.array([y for _, y in rows], float)

    Xt, yt = positions(args.test, args.seed + 999_000)
    X = np.zeros((0, len(N))); y = np.zeros(0)
    for it in range(args.iterations):
        Xi, yi = positions(args.games, args.seed + 10_000 * it)
        X, y = np.vstack([X, Xi]), np.concatenate([y, yi])
        w, mean, std, report = F.fit(X * keep, y, None, iters=2500, signs=signs(False, 2))
        w = w * keep
        model = LinearValue([float(v) for v in w], [float(v) for v in mean], [float(v) for v in std], False,
                            {"deck": craft.name.lower(), "opponent": op_craft.name.lower(), "positions": len(X),
                             "iteration": it + 1, "report": {k: float(v) for k, v in report.items()}}, version=2)
        model.save(folder / out.name)
        score = auc(((Xt * keep - np.array(mean)) / np.array(std)) @ w, yt)
        print(f"iteration {it + 1}: {len(X)} positions, held-out AUC {score:.3f}", flush=True)
    shutil.copy(folder / out.name, out)
    print("saved", out)


if __name__ == "__main__":
    main()
