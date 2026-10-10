"""Looking past the end of our turn, for analysis (not wired into any level).

`next_lethal_prob` (the architecture thread 2026-10-10 02:13Z, M2 of the analysis line): from a position where our
turn has just ended, how often do we have a sure lethal at the start of our next turn? On k determinizations from our
view (the opponent's hand and both decks reshuffled, the random numbers reseeded: nothing hidden is used), the
opponent plays its whole turn with `reply_spec`; if the game goes on, our next turn starts as the engine starts it
(our draw included) and find_lethal runs at its defaults (20000 nodes, 8 samples, seed 0, no screen): a sure lethal
counts 1, anything else 0. Losing during the opponent's turn counts 0, winning in it (their deck runs out, an
effect) 1.

The position may come in two forms: EndTurn applied by the engine, so the opponent's turn has started and they have
drawn (`opponent_started=True`, as in a game record), or a search.evaluate.after_end_of_turn copy, where the turn
has passed but the opponent's turn start hasn't run (`opponent_started=False`, as a candidate plan's turn end): the
tool runs it on each determinization, so their draw comes from the guessed deck.

All randomness comes from `seed`: sample j's determinization and the reply agent's seed are drawn from
random.Random(seed), so two lines given the same seed get the same sample seeds (paired).
"""
from __future__ import annotations

import random
import time

from svsim.core.engine import apply, legal_actions
from svsim.core.view import determinize


def _result(state, me: int) -> float:
    return 1.0 if state.winner == me else 0.0


def _end(state, me: int) -> str:
    return "won" if state.winner == me else "died" if state.winner == 1 - me else "draw"


def next_lethal_prob(state, k: int = 16, seed: int = 0, reply_spec: str = "level-strong",
                     opponent_started: bool = True, nodes: int = 20000, max_actions: int = 200) -> dict:
    """{"p": mean over the samples, "samples": [0/1 each], "ends": [how each sample ended: "died", "won" or "draw"
    (in the opponent's turn), "lethal", "no lethal"], "incomplete": find_lethal runs that hit their node budget without a
    sure lethal, "ms": wall time}. We are the player who just ended the turn (1 - state.active)."""
    from svsim.search.lethal import find_lethal
    from svsim.tools.arena import make_agent
    t0 = time.perf_counter()
    me = 1 - state.active
    rng = random.Random(seed)
    seeds = [rng.randrange(2 ** 31) for _ in range(k)]
    samples, ends, incomplete = [], [], 0
    for sd in seeds:
        if state.over:
            samples.append(_result(state, me))
            ends.append(_end(state, me))
            continue
        s = determinize(state, me, random.Random(sd))
        if not opponent_started:
            from svsim.core.engine import _start_turn
            _start_turn(s)                          # the opponent's turn start, from the guessed deck
            if s.winner is not None:
                from svsim.core.enums import Phase
                s.phase = Phase.OVER
        opponent = make_agent(reply_spec, sd)
        n = 0
        while not s.over and s.active != me and n < max_actions:
            apply(s, opponent.act(s, legal_actions(s)))
            n += 1
        if s.over:
            samples.append(_result(s, me))
            ends.append(_end(s, me))
            continue
        if s.active != me:                          # the opponent never ended its turn: no verdict
            samples.append(0.0)
            ends.append("no lethal")
            continue
        r = find_lethal(s, max_nodes=nodes)
        samples.append(1.0 if r.sure else 0.0)
        ends.append("lethal" if r.sure else "no lethal")
        incomplete += (not r.sure) and (not r.complete)
    return {"p": sum(samples) / len(samples) if samples else 0.0, "samples": samples, "ends": ends,
            "incomplete": incomplete, "ms": round((time.perf_counter() - t0) * 1000, 1)}
