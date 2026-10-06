"""Learn each deck's evaluation from self-play outcomes and a player's choices.

    python -m svsim.tools.learn --decks rhino ramp --games 400 --iterations 2 \\
        --human replays/  --human-deck rhino

Each iteration plays --games games between the two decks (the first iteration
with --agent, later ones with the same agent using the evaluation learned so
far), records every end-of-turn position with its outcome, and fits one
linear model per deck (svsim.learn.fit) on all positions so far. The model for
--human-deck also learns from the recorded games of a player (JSON records
from tools.play / the web page's store): their move should score highest, and
(--turn-weight) the position at the end of each of their turns should score
above the same turn played other ways (ended at once, by the AI, at random).
The models go to svsim/learn/weights/<craft>.json, where "+learned" agents
(tools.arena) find them. Reports the fit and, with --human, how often the
player's move is the model's top choice, on their games held out in turn.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np

from svsim.cards import decks
from svsim.core.enums import Craft
from svsim.learn import data, fit as F
from svsim.learn.features import names, signs
from svsim.learn.model import WEIGHTS, LinearValue

DECKS = {"rhino": decks.RHINO_FOREST, "ramp": decks.RAMP_DRAGON, "pirate": decks.PIRATE_SWORD}


def deck_craft_of(name: str) -> Craft:
    return decks.craft_of(decks.build(DECKS[name]))


def load_records(paths: list[str]) -> list[dict]:
    out = []
    for p in paths:
        files = sorted(Path(p).glob("**/*.json")) if Path(p).is_dir() else [Path(p)]
        for f in files:
            d = json.loads(f.read_text(encoding="utf-8"))
            d = d.get("data", d)
            rec = d.get("record", d)
            if "actions" in rec and rec.get("winner") is not None:
                out.append(rec)
    return out


def held_out_top1(steps_by_game: list, turns_by_game: list, repeat: int, X, y, lam: float, iters: int,
                  potential: bool = True) -> tuple:
    """Train on all games but one, measure on that one: (moves, whole turns) where
    the player's choice ranks first, averaged over decisions."""
    hits = [0.0, 0.0]
    total = [0, 0]
    for k in range(len(steps_by_game)):
        train = [p for j, g in enumerate(steps_by_game) if j != k for p in g]
        train += [p for j, g in enumerate(turns_by_game) if j != k for p in g] * repeat
        w, mean, std, _ = F.fit(X, y, train, lam=lam, iters=iters, signs=signs(potential))
        for i, test in enumerate((steps_by_game[k], turns_by_game[k] if turns_by_game else [])):
            if test:
                hits[i] += F.top1(w, F.choice_groups(test, mean, std)) * len(test)
                total[i] += len(test)
    return tuple(h / t if t else None for h, t in zip(hits, total))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--decks", nargs=2, default=["rhino", "ramp"], choices=sorted(DECKS))
    parser.add_argument("--games", type=int, default=400, help="self-play games per iteration")
    parser.add_argument("--iterations", type=int, default=2)
    parser.add_argument("--agent", default="greedy+plan", help="the self-play agent (tools.arena spec)")
    parser.add_argument("--human", nargs="*", default=[], help="recorded games (files or folders)")
    parser.add_argument("--human-deck", default="rhino", choices=sorted(DECKS))
    parser.add_argument("--lam", type=float, default=1.0, help="weight of the player's choices in the fit")
    parser.add_argument("--turn-weight", type=int, default=3,
                        help="each whole-turn comparison counts this many times (0: moves only)")
    parser.add_argument("--iters", type=int, default=3000)
    parser.add_argument("--out", default=str(WEIGHTS))
    parser.add_argument("--no-potential", action="store_true", help="leave out the planner feature (faster)")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    potential = not args.no_potential
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    os.environ["SVSIM_WEIGHTS"] = str(out)          # "+learned" agents in worker processes read these
    deck_a, deck_b = (decks.build(DECKS[n]) for n in args.decks)
    crafts = {n: deck_craft_of(n) for n in args.decks}
    human = load_records(args.human)
    prefs_by_game = [data.choices(r, 0, potential) for r in human]
    turns_by_game = [data.turn_choices(r, 0, potential, seed=i) for i, r in enumerate(human)] if args.turn_weight else []
    print(f"玩家对局 {len(human)} 局，决策 {sum(len(g) for g in prefs_by_game)} 次，"
          f"整回合比较 {sum(len(g) for g in turns_by_game)} 个")
    rows = []
    for it in range(args.iterations):
        spec = args.agent if it == 0 else args.agent + "+learned"
        start = time.perf_counter()
        rows += data.selfplay(deck_a, deck_b, spec, spec, args.games, seed=10000 * (it + 1), potential=potential,
                              workers=args.workers)
        print(f"第 {it + 1} 轮：{spec} 自对弈 {args.games} 局，累计 {len(rows)} 个局面（{time.perf_counter() - start:.0f} 秒）")
        for name, craft in crafts.items():
            mine = [(x, lab) for c, x, lab in rows if c == int(craft)]
            X = np.array([x for x, _ in mine], dtype=float)
            y = np.array([lab for _, lab in mine], dtype=float)
            prefs = None
            if name == args.human_deck:
                prefs = [p for g in prefs_by_game for p in g] + [p for g in turns_by_game for p in g] * args.turn_weight
            w, mean, std, report = F.fit(X, y, prefs, lam=args.lam, iters=args.iters, signs=signs(potential))
            info = {"deck": name, "positions": len(mine), "win_rate": float(y.mean()) if len(y) else None,
                    "choices": len(prefs or []), "iteration": it + 1, **report}
            if prefs and len(human) > 1:
                moves, turns = held_out_top1(prefs_by_game, turns_by_game, args.turn_weight, X, y, args.lam,
                                             args.iters // 2, potential)
                info["choice_top1_held_out"], info["turn_top1_held_out"] = moves, turns
            model = LinearValue(w.tolist(), mean.tolist(), std.tolist(), potential, info)
            model.save(out / f"{craft.name.lower()}.json")
            print(f"  {name}（{craft.name.lower()}）：{len(mine)} 个局面，胜率 {info['win_rate']:.0%}，"
                  + "，".join(f"{k} {v:.3f}" for k, v in report.items())
                  + (f"，留一局检验：单步命中 {info['choice_top1_held_out']:.0%}" if "choice_top1_held_out" in info else "")
                  + (f"，整回合命中 {info['turn_top1_held_out']:.0%}" if info.get("turn_top1_held_out") is not None else ""))
            top = sorted(model.weights_by_name().items(), key=lambda kv: -abs(kv[1] * (std[names(potential).index(kv[0])])))[:8]
            print("    影响最大的特征：" + "，".join(f"{k} {v:+.3f}" for k, v in top))


if __name__ == "__main__":
    main()
