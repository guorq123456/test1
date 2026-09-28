"""A minimal AlphaEvolve-style loop: propose -> evaluate -> keep the best -> mutate.

The searcher never sees the sealed set. It only sees ``EvalResult.composite``
(the leave-one-area-out macro-F1). Swap ``propose`` for an LLM agent that
returns a config dict and nothing else changes: that is the point of
evaluator-first.
"""

from __future__ import annotations

import random
import time
from typing import Any, Callable

from .candidates import build, mutate, random_config
from .evaluator import EvalResult, ForestEvaluator

Proposer = Callable[[list[tuple[dict[str, Any], EvalResult]], random.Random], dict[str, Any]]


def default_proposer(elite: list[tuple[dict[str, Any], EvalResult]], rng: random.Random) -> dict[str, Any]:
    """Random restart 30% of the time, otherwise mutate one of the elite."""
    if not elite or rng.random() < 0.3:
        return random_config(rng)
    parent, _ = rng.choice(elite)
    return mutate(parent, rng)


def evolve(
    ev: ForestEvaluator,
    n_evals: int = 20,
    elite_size: int = 4,
    time_budget_s: float | None = None,
    seed: int = 0,
    proposer: Proposer = default_proposer,
    verbose: bool = True,
) -> list[tuple[dict[str, Any], EvalResult]]:
    rng = random.Random(seed)
    elite: list[tuple[dict[str, Any], EvalResult]] = []
    seen: set[str] = set()
    t0 = time.time()
    for i in range(n_evals):
        if time_budget_s is not None and time.time() - t0 > time_budget_s:
            break
        cfg = proposer(elite, rng)
        # skip exact duplicates
        for _ in range(5):
            r = ev.evaluate(build, cfg, note=f"evolve#{i}")
            if r.fingerprint not in seen:
                break
            cfg = mutate(cfg, rng)
        seen.add(r.fingerprint)
        elite.append((cfg, r))
        elite.sort(key=lambda t: t[1].composite, reverse=True)
        elite = elite[:elite_size]
        if verbose:
            best = elite[0][1]
            print(
                f"[{i:02d}] {r.config['model']:6s} feats={list(r.config['features'])} "
                f"iid={r.iid_macro_f1:.3f} transfer={r.transfer_macro_f1:.3f} "
                f"| best transfer={best.composite:.3f} ({time.time()-t0:.0f}s)",
                flush=True,
            )
    return elite
