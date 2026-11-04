"""Root-parallel ISMCTS (+par=K; the architecture thread 2026-10-10 10:01Z): K independent trees on the same decision,
each with its own seed (so its own determinizations) and the spec's full iteration count, their root children's
visits summed, the most visited move chosen. The wall time per decision is about one tree's; the CPU is K times.

- The trees run in a resident process pool, one per spec (spawn start method, as on Windows): each worker builds the
  spec's search once (svsim.tools.arena.make_agent without +par) and runs one tree per request.
- The seeds come from the calling search's own random numbers, so a fixed seed replays the same decisions.
- The lethal check and everything else around the search stay in the calling process (LethalAgent wraps the
  search as before); only ISMCTS.choose is spread.
- Each decision records the trees' CPU seconds summed (`last_cpu`) and their iterations summed
  (`last_iterations`).
- A script that uses it must keep its work under `if __name__ == "__main__":`: spawned workers import the main
  module, and without the guard each would run the script again (its pool's workers die and are restarted forever).
"""
from __future__ import annotations

import multiprocessing as mp
import random
import time

_POOLS: dict = {}
_WORKER: dict = {}


def _init(spec: str) -> None:
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    _WORKER["search"] = _search(make_agent(spec, 0))


def _tree(job) -> tuple:
    """One tree on `state` with `seed`: ({move key: (visits, estimate)}, iterations, CPU seconds)."""
    state, seed = job
    search = _WORKER["search"]
    search.rng = random.Random(seed)
    t = time.process_time()
    search.choose(state)
    cpu = time.process_time() - t
    root = search.last_root
    kids = {k: (n.visits, search.estimate(n)) for k, n in root.children.items()} if root is not None else {}
    return kids, search.last_iterations or 0, cpu


def pool(spec: str, k: int):
    """The resident pool of `k` workers for `spec` (created once)."""
    key = (spec, k)
    p = _POOLS.get(key)
    if p is None:
        p = _POOLS[key] = mp.get_context("spawn").Pool(k, initializer=_init, initargs=(spec,))
    return p


def shutdown() -> None:
    for p in _POOLS.values():
        p.terminate()
    _POOLS.clear()


def choose(search, state):
    """The move of `search` (an ISMCTS with parallel > 1 and par_spec set) on `state`: the K trees' summed visits."""
    from svsim.core.engine import legal_actions
    from svsim.search.mcts import Node, _locator, action_key
    seeds = [search.rng.randrange(2 ** 31) for _ in range(search.parallel)]
    results = pool(search.par_spec, search.parallel).map(_tree, [(state, sd) for sd in seeds])
    merged: dict = {}
    for kids, _, _ in results:
        for key, (visits, value) in kids.items():
            v, total = merged.get(key, (0, 0.0))
            merged[key] = (v + visits, total + visits * value)
    root = Node()
    for key, (visits, total) in merged.items():
        child = root.children[key] = Node()
        child.visits, child.total = visits, total
        child.value = total / visits if visits else 0.0
    root.visits = sum(v for v, _ in merged.values())
    search.last_root = root
    search.last_iterations = sum(it for _, it, _ in results)
    search.last_tree_cpu = [cpu for _, _, cpu in results]
    search.last_cpu = sum(search.last_tree_cpu)
    where = _locator(state, state.active)
    legal = {action_key(state, a, where): a for a in legal_actions(state)}
    best = max((k for k in legal if k in merged), key=lambda k: merged[k][0], default=None)
    return legal[best] if best is not None else next(iter(legal.values()))
