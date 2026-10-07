"""Linear models by moment: one for turn ends, one for the start of a turn reached by playing out the reply.

Separates two questions the value network mixed up (2026-10-07): does playing
the opponent's turn out help the search (mcts-reply), and is the network's
score too jumpy for it (its score of a line moves with the cards drawn in it
in 28% of turns, the linear model's in 1%). `PhasedLearned` scores turn ends
and positions inside the turn with the ENDED model (as the linear models
always did) and the start of a turn the search reached by playing out the
opponent's reply with the ACT model; both are fitted the same way on the same
self-play positions (learn.netdata.rows), the player's own hand and deck
roles left out as in the installed model, so their scores compare.

    python -m svsim.learn.phased --games games.jsonl --out folder
writes <craft>-<craft>-ended.json and <craft>-<craft>-act.json into folder;
agents load them from $SVSIM_PHASED, else svsim/learn/phased_models (`+phased`;
the Ramp mirror's, fitted on 2000 self-play games of the installed bot, are
there).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from svsim.learn.model import SCALE, Learned, LinearValue, matchup_keys, parse_key

STOCK = ("me_hand_", "me_pool_")


def _rows(job) -> list:
    from svsim.learn.features import features
    from svsim.learn.netdata import rows
    line, version = job if isinstance(job, tuple) else (job, 2)
    record = json.loads(line)
    return [(record.get("g", 0), phase, features(state, me, False, version), result, q)
            for phase, me, state, result, q in rows(record, with_search=True)]


def load(folder: Path | None = None) -> dict:
    """{(deck, opponent deck, "act" | "ended"): LinearValue, or a learn.net.ValueNet from an .npz file
    (the same logit(state, player); the smooth network can stand in for either moment). Files are
    <deck>-<deck>-<moment> for named decks (cards.decks.NAMED) or <craft>-<craft>-<moment>."""
    folder = folder or Path(os.environ.get("SVSIM_PHASED") or Path(__file__).resolve().parent / "phased_models")
    out = {}
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("*-*-*.json")) + sorted(folder.glob("*-*-*.npz")):
        mine, theirs, moment = path.stem.split("-")
        try:
            key = (parse_key(mine), parse_key(theirs), moment)
        except KeyError:
            continue
        if path.suffix == ".npz":
            from svsim.learn.net import ValueNet
            out[key] = ValueNet.load(path)                # a network overrides a linear model of the same name
        else:
            out.setdefault(key, LinearValue.load(path))
    return out


class PhasedLearned:
    def __init__(self, models: dict | None = None, fallback=None):
        self.models = models if models is not None else load()
        self.fallback = fallback or Learned()

    def score(self, state, player: int, player_moves_next: bool = False) -> float:
        from svsim.search.evaluate import WIN
        if state.winner is not None:
            return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
        moment = "act" if player_moves_next else "ended"
        model = next((self.models[k + (moment,)] for k in matchup_keys(state, player) if k + (moment,) in self.models),
                     None)
        if model is None:
            return self.fallback.score(state, player, player_moves_next)
        return SCALE * model.logit(state, player)


def main() -> None:
    import numpy as np
    from multiprocessing import Pool
    from svsim.learn import fit as F
    from svsim.learn.encode import ACT, ENDED
    from svsim.learn.features import names, signs
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--matchup", default="ramp-ramp", help="<deck>-<deck> (cards.decks.NAMED keys)")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--q-weight", type=float, default=0.0,
                        help="label = (1 - w) * result + w * the search's value where the search decided")
    parser.add_argument("--version", type=int, default=2, help="features version (3: held evolution points "
                        "by context, learn.features.SIDE3)")
    args = parser.parse_args()
    lines = [line for path in args.games for line in open(path, encoding="utf-8")]
    with Pool(args.workers) as pool:
        data = [r for part in pool.imap(_rows, [(line, args.version) for line in lines], chunksize=4)
                for r in part]
    N = names(False, args.version)
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in N])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for phase, label in ((ENDED, "ended"), (ACT, "act")):
        rows = [r for r in data if r[1] == phase and r[3] != 0.5]
        X = np.array([r[2] for r in rows], float)
        y = np.array([r[3] if r[4] is None else (1 - args.q_weight) * r[3] + args.q_weight * r[4]
                      for r in rows], float)
        w, mean, std, report = F.fit(X * keep, y, None, iters=2500, signs=signs(False, args.version))
        w = w * keep
        mine, theirs = args.matchup.split("-")
        LinearValue([float(v) for v in w], [float(v) for v in mean], [float(v) for v in std], False,
                    {"deck": mine, "opponent": theirs, "moment": label, "positions": len(X),
                     "q_weight": args.q_weight, "games": args.games,
                     "report": {k: float(v) for k, v in report.items()}}, version=args.version
                    ).save(out / f"{args.matchup}-{label}.json")
        print(f"{label}: {len(X)} positions, {report}", flush=True)


if __name__ == "__main__":
    main()
