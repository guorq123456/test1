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

from svsim.learn.model import ALIASES, SCALE, Learned, LinearValue, matchup_keys, split_keys

STOCK = ("me_hand_", "me_pool_")


def _rows(job) -> list:
    from svsim.learn.features import features
    from svsim.learn.netdata import rows
    from svsim.learn.netdata import ACT
    defaults = (None, 2, 1.0, 1.0, 1.0, None, None)   # line, version, weight, unlock, act_hold, phases, side
    job = tuple(job) + defaults[len(job):] if isinstance(job, tuple) else (job,) + defaults[1:]
    line, version, weight, unlock, act_hold, phases, side = job[:7]
    record = json.loads(line)
    names = record.get("names")                    # the named decks by seat: `side` keeps (mine, theirs) only
    branch = record.get("branch") or {}
    hold = branch.get("kind") == "hold"
    start = branch.get("i", 0) if hold else 0     # the shared start counts once
    if branch.get("trigger") == "unlock":          # a third of these kept points for a follower already on the field
        weight *= unlock
    out = []
    for phase, me, state, result, q in rows(record, with_search=True, start=start):
        if phases is not None and phase not in phases:   # a moment not being fitted: no features
            continue
        if side is not None and names and (names[me], names[1 - me]) != tuple(side):
            continue
        w = weight * (act_hold if hold and phase == ACT else 1.0)
        if w > 0:
            out.append((record.get("g", 0), phase, features(state, me, False, version), result, q, w))
    return out


def folder_of(name: str) -> Path:
    """A models folder by name: a path to one, else svsim/learn/phased_models/<name> (candidates kept beside
    the installed models, which sit in phased_models itself)."""
    path = Path(name)
    if path.is_dir():
        return path
    path = Path(__file__).resolve().parent / "phased_models" / name
    if not path.is_dir():
        raise ValueError(f"no phased models folder {name}")
    return path


def load(folder: Path | None = None) -> dict:
    """{(deck, opponent deck, "act" | "ended"): LinearValue, or a learn.net.ValueNet from an .npz file
    (the same logit(state, player); the smooth network can stand in for either moment). Files are
    <deck>-<deck>-<moment> for named decks (cards.decks.NAMED) or <craft>-<craft>-<moment>."""
    folder = folder or Path(os.environ.get("SVSIM_PHASED") or Path(__file__).resolve().parent / "phased_models")
    out = {}
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("*-*-*.json")) + sorted(folder.glob("*-*-*.npz")):
        pair, _, moment = path.stem.rpartition("-")
        try:
            keys = split_keys(pair)
        except KeyError:
            continue
        if len(keys) != 2:
            continue
        key = (keys[0], keys[1], moment)
        if path.suffix == ".npz":
            from svsim.learn.net import ValueNet
            out[key] = ValueNet.load(path)                # a network overrides a linear model of the same name
        else:
            out.setdefault(key, LinearValue.load(path))
    return out


class PhasedLearned:
    def __init__(self, models: dict | None = None, fallback=None, aliases: dict | None = ALIASES):
        self.models = models if models is not None else load()
        self.fallback = fallback or Learned(aliases=aliases)
        self.aliases = aliases                     # learn.model.ALIASES: a mirror's stand-in models

    def score(self, state, player: int, player_moves_next: bool = False) -> float:
        from svsim.search.evaluate import WIN
        if state.winner is not None:
            return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
        moment = "act" if player_moves_next else "ended"
        model = next((self.models[k + (moment,)] for k in matchup_keys(state, player, self.aliases)
                      if k + (moment,) in self.models),
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
    parser.add_argument("--file-weights", type=float, nargs="+", default=None,
                        help="a weight for each --games file's positions (default 1 each)")
    parser.add_argument("--unlock-weight", type=float, default=1.0,
                        help="weight of the forked games started at an evolution unlock (learn.netdata --fork)")
    parser.add_argument("--moments", nargs="+", default=["ended", "act"], choices=("ended", "act"),
                        help="the models to fit (the architecture session's F4 refits only the turn-end one and keeps "
                             "the installed in-turn model)")
    parser.add_argument("--act-hold-weight", type=float, default=1.0,
                        help="weight of a fork's keeping branch in the in-turn (act) model, 0 to leave it out: a "
                             "branch made to keep its points loses more, which the in-turn model may pin on what "
                             "the keeping made it play (the architecture session's F3b); the turn-end model "
                             "keeps it all")
    args = parser.parse_args()
    weights = args.file_weights or [1.0] * len(args.games)
    assert len(weights) == len(args.games)
    phases = tuple({"ended": ENDED, "act": ACT}[m] for m in args.moments)
    keys = split_keys(args.matchup)                # named decks: only that side's positions (elf-t-ramp-t: the
    side = tuple(keys) if all(isinstance(k, str) for k in keys) else None   # elf-t player's, against ramp-t)
    jobs = [(line, args.version, w, args.unlock_weight, args.act_hold_weight, phases, side)
            for path, w in zip(args.games, weights) for line in open(path, encoding="utf-8")]
    with Pool(args.workers) as pool:
        data = [r for part in pool.imap(_rows, jobs, chunksize=4) for r in part]
    N = names(False, args.version)
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in N])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for phase, label in ((ENDED, "ended"), (ACT, "act")):
        if label not in args.moments:
            continue
        rows = [r for r in data if r[1] == phase and r[3] != 0.5]
        X = np.array([r[2] for r in rows], float)
        y = np.array([r[3] if r[4] is None else (1 - args.q_weight) * r[3] + args.q_weight * r[4]
                      for r in rows], float)
        rw = np.array([r[5] for r in rows], float)
        w, mean, std, report = F.fit(X * keep, y, None, iters=2500, signs=signs(False, args.version),
                                     weights=None if np.all(rw == 1.0) else rw)
        w = w * keep
        mine, theirs = (k if isinstance(k, str) else k.name.lower() for k in split_keys(args.matchup))
        LinearValue([float(v) for v in w], [float(v) for v in mean], [float(v) for v in std], False,
                    {"deck": mine, "opponent": theirs, "moment": label, "positions": len(X),
                     "q_weight": args.q_weight, "games": args.games, "file_weights": weights,
                     "unlock_weight": args.unlock_weight, "act_hold_weight": args.act_hold_weight,
                     "report": {k: float(v) for k, v in report.items()}}, version=args.version
                    ).save(out / f"{args.matchup}-{label}.json")
        print(f"{label}: {len(X)} positions, {report}", flush=True)


if __name__ == "__main__":
    main()
