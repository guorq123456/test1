"""The gate: is agent A stronger than agent B? Paired games and a sequential test.

    python -m svsim.tools.gate --a "mcts:100+plan+learned" --b "mcts:100+plan" --deck ramp --opponent ramp
    python -m svsim.tools.gate --a mcts:100+plan+learned --model-a new.json --b mcts:100+plan+learned

Why (2026-10-07): most conclusions so far rested on 100 games (a 95% margin of
about 10%), so 51%, 55%, 45% and 46% all meant "no change" and each cost a
round of work. This tool replaces the guess of how many games to play:

- a fixed bank of opening seeds (seed bank: --seed + i); each seed is played
  twice with the seats swapped (a pair), so both agents get the same deals
  and the luck of the draw cancels out; every comparison starts from the same
  seeds;
- a sequential probability ratio test on the pair scores (each pair scores
  0, 0.25, 0.5, 0.75 or 1 for A): H0 = A scores --h0 (0.5: no change), H1 =
  A scores --h1 (0.55), error rates --alpha / --beta (0.05);
  the log-likelihood ratio uses the normal approximation with the pairs'
  observed variance (as engine testing does with pentanomial results). It
  stops as soon as either hypothesis is accepted, at --max games at most;
  a large gap stops in a few hundred games, no gap is called "no gain";
- results go to a JSON-lines file (--out) one pair at a time, and a rerun
  with the same arguments resumes from it (the cloud container restarts).

A's and B's matchup models can be replaced with --model-a / --model-b (a
LinearValue JSON file used as the model for A's / B's deck against its
opponent, as models.Learned looks it up). Reports A's score (per game, from
the pairs) with a 95% interval and the test's verdict; beside them, the gap
in class rating (CR, the ladder's rating: learn.rating) at which that score
keeps a player's CR steady, 800 x (score - 1/2), with its interval, given
only inside the ladder's matching window (a score of 28%-72%, a gap of
175 CR at most); past it the stronger side keeps climbing until nobody is in
reach, and the rules can't say by how much more ("out of the window").

No Elo (the player, 2026-10-07; class rating is the yardstick instead): chess's
400-point logistic doesn't hold in a card game. Luck puts a ceiling on win rates (around 75%-85% however strong a
side is), and the ladder only matches players within 200 points, so a rating
difference is defined only inside that window: "82% means +263" is an
extrapolation outside it, and such differences don't add up across pairs.
A strength scale, when there is a pool of three or more versions that have
all played each other, should be fitted on the pool's own games with its
slope free (Bradley-Terry), or with a luck ceiling, and read only within the
range that was measured.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from multiprocessing import Pool
from pathlib import Path


def llr(scores: list[float], h0: float, h1: float) -> float:
    """Log-likelihood ratio of H1 (mean pair score h1) against H0 (h0), normal approximation."""
    n = len(scores)
    if n < 2:
        return 0.0
    mean = sum(scores) / n
    var = sum((x - mean) ** 2 for x in scores) / n
    var = max(var, 1e-4)
    return n * (h1 - h0) * (2 * mean - h0 - h1) / (2 * var)


def bounds(alpha: float, beta: float) -> tuple[float, float]:
    return math.log(beta / (1 - alpha)), math.log((1 - beta) / alpha)


def cr_gap(score: float) -> float | None:
    """The CR gap at which `score` keeps a player's CR steady (learn.rating), or None outside
    the matching window (|gap| > 175)."""
    from svsim.learn.rating import CAP
    gap = 800 * (score - 0.5)
    return gap if abs(gap) <= CAP else None


def cr_text(score: float, margin: float) -> str:
    gap = cr_gap(score)
    if gap is None:
        return f"CR 分差超出匹配窗口（{'>+175' if score > 0.5 else '<−175'}）"
    lo, hi = cr_gap(score - margin), cr_gap(score + margin)
    show = lambda g, side: f"{g:+.0f}" if g is not None else ("<−175" if side < 0 else ">+175")
    return f"CR 分差约 {gap:+.0f}（区间 {show(lo, -1)}～{show(hi, 1)}，窗口内）"


def summary(scores: list[float]) -> tuple[float, float]:
    """A's mean score per game and the 95% margin, from the pairs."""
    n = len(scores)
    mean = sum(scores) / n
    var = sum((x - mean) ** 2 for x in scores) / max(n - 1, 1)
    return mean, 1.96 * math.sqrt(var / n)


def _agent(spec: str, seed: int, model: str | None, phased: str | None = None):
    from svsim.tools.arena import make_agent
    agent = make_agent(spec, seed)
    if phased:                                     # the agent's linear models by moment from this folder
        from svsim.learn.phased import PhasedLearned, load
        inner = agent
        while not (hasattr(inner, "search") and hasattr(inner.search, "weights")):
            inner = inner.base
        if isinstance(inner.search.weights, PhasedLearned):
            inner.search.weights.models = load(Path(phased))
            if inner.search.reply:
                inner.search.opponent.weights = inner.search.weights
    if model:
        from svsim.learn.model import Learned, LinearValue, load_all
        inner = agent
        while not (hasattr(inner, "search") and hasattr(inner.search, "weights")):
            inner = inner.base
        models = dict(load_all())
        loaded = LinearValue.load(Path(model))
        for key in _keys(loaded):
            models[key] = loaded
        inner.search.weights = Learned(models=models)
    return agent


def _keys(model) -> list:
    """The keys a model file stands for: a pair of named decks, or its classes and every pair of
    named decks of those classes (as Learned looked up a class pair before decks were told apart)."""
    from svsim.cards import decks
    from svsim.core.enums import Craft
    deck, opp = model.info.get("deck"), model.info.get("opponent")
    if not deck:
        return []
    if deck in decks.NAMED and opp in decks.NAMED:
        return [(deck, opp)]
    if not opp:
        return [Craft[deck.upper()]]
    mine, theirs = Craft[deck.upper()], Craft[opp.upper()]
    named = {k: decks.craft_of(decks.build(listing)) for k, listing in decks.NAMED.items()}
    return [(mine, theirs)] + [(a, b) for a in named for b in named if named[a] == mine and named[b] == theirs]


def play_pair(job) -> dict:
    """Seed `seed` twice, A in seat 0 then in seat 1; A's points (win 1, draw 0.5)."""
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.learn.netdata import _plan, _planner
    from svsim.tools import records as R
    from svsim.ui.session import DECKS
    k, seed, a, b, model_a, model_b, deck, opponent, phased_a, phased_b = job
    mine, theirs = decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1])
    points, games = [], []
    for seat in (0, 1):
        agents = [None, None]
        agents[seat] = _agent(a, 2 * seed + seat, model_a, phased_a)
        agents[1 - seat] = _agent(b, 2 * seed + 1 - seat + 7919, model_b, phased_b)
        planners = [_planner(x) for x in agents]
        cards = [None, None]
        cards[seat], cards[1 - seat] = mine, theirs
        state = new_game(cards[0], cards[1], seed=seed)
        record = R.new_record(cards[0], cards[1], seed, state.first, f"{a} / {b}" if seat == 0 else f"{b} / {a}")
        record["names"] = [deck, opponent] if seat == 0 else [opponent, deck]
        while not state.over:
            planner = planners[state.active]
            if planner is not None:
                planner.last_plan = None
            action = agents[state.active].act(state, legal_actions(state))
            if planner is not None and planner.last_plan is not None:   # the planner's measurements, kept
                record.setdefault("plans", []).append(_plan(state, len(record["actions"]), planner.last_plan,
                                                            record["names"]))
            R.add(record, action)
            apply(state, action)
        record["winner"] = state.winner
        if record.get("plans"):
            games.append(record)
        points.append(1.0 if state.winner == seat else 0.5 if state.winner not in (0, 1) else 0.0)
    return {"k": k, "seed": seed, "points": points, "games": games}


def main() -> None:
    from svsim.ui.session import DECKS
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--a", required=True, help="the agent under test (arena spec)")
    parser.add_argument("--b", required=True, help="the agent it must beat")
    parser.add_argument("--model-a", default=None)
    parser.add_argument("--model-b", default=None)
    parser.add_argument("--phased-a", default=None, help="folder of A's linear models by moment (+phased)")
    parser.add_argument("--phased-b", default=None)
    parser.add_argument("--deck", default="ramp", choices=sorted(DECKS), help="A's deck")
    parser.add_argument("--opponent", default="ramp", choices=sorted(DECKS), help="B's deck")
    parser.add_argument("--h0", type=float, default=0.5)
    parser.add_argument("--h1", type=float, default=0.55)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--beta", type=float, default=0.05)
    parser.add_argument("--max", type=int, default=2000, help="games at most (pairs = max / 2)")
    parser.add_argument("--seed", type=int, default=1_000_000, help="first seed of the bank")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", default=None, help="results file (JSON lines; resumed if it exists)")
    args = parser.parse_args()
    import hashlib
    key = json.dumps([args.a, args.b, args.model_a, args.model_b, args.deck, args.opponent, args.seed,
                      args.phased_a, args.phased_b])
    out = args.out or f"gate-{hashlib.sha1(key.encode()).hexdigest()[:10]}.jsonl"
    done = {}
    if os.path.exists(out):
        for line in open(out, encoding="utf-8"):
            d = json.loads(line)
            done[d["k"]] = d
    lo, hi = bounds(args.alpha, args.beta)
    pairs = args.max // 2
    t0 = time.time()

    def report(final: bool = False) -> str | None:
        scores = [sum(d["points"]) / 2 for _, d in sorted(done.items())]
        if not scores:
            return None
        value = llr(scores, args.h0, args.h1)
        mean, margin = summary(scores)
        verdict = "H1（A 更强）" if value >= hi else "H0（没有变强）" if value <= lo else None
        line = (f"{2 * len(scores)} 局：A 得分 {mean:.1%} ± {margin:.1%}"
                f"（95% 区间 {mean - margin:.1%}～{mean + margin:.1%}），{cr_text(mean, margin)}，"
                f"LLR {value:+.2f}（判定线 {lo:.2f} / {hi:.2f}）→ {verdict or '未判定'}")
        if final or verdict:
            print(line, flush=True)
        return verdict

    if not report(final=True):
        todo = [(k, args.seed + k, args.a, args.b, args.model_a, args.model_b, args.deck, args.opponent,
                 args.phased_a, args.phased_b)
                for k in range(pairs) if k not in done]
        side = out[:-len(".jsonl")] if out.endswith(".jsonl") else out
        with Pool(args.workers) as pool, open(out, "a", encoding="utf-8") as fh:
            for res in pool.imap_unordered(play_pair, todo):
                games = res.pop("games", [])
                if games:                                  # games with a cross-turn planner's measurements
                    with open(side + ".records.jsonl", "a", encoding="utf-8") as rf:
                        for g in games:
                            rf.write(json.dumps(g) + "\n")
                done[res["k"]] = res
                fh.write(json.dumps(res) + "\n")
                fh.flush()
                if len(done) % 25 == 0:
                    print(f"  …{2 * len(done)} 局 {time.time() - t0:.0f}s", flush=True)
                    if report(final=True):
                        pool.terminate()
                        break
    report(final=True)


if __name__ == "__main__":
    main()
