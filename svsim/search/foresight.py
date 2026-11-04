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


# --- playing the game out with a direction ----------------------------------------------------------------------
# `direction_rollout` (the architecture thread 02:17Z, M4 of the analysis line; Salem 02:16Z: 运营 is mostly
# judging the game's direction, the likeliest way to win): from a position where our turn has just ended, the game
# is played to its end on k determinizations, the opponent by `opp_spec`, our side on every own turn with a bias:
# - "race": the lethal-clock line (search.candidates.ClockScore: fewer turns to my lethal first, as candidates'
#   "race" plan);
# - "clear": the line that leaves the enemy board weakest (ClearScore: the enemy followers' attack plus defense
#   first, from the cards' own fields, no table per card);
# - "conserve": the base evaluation with a small bonus for cards kept in hand, play points and evolution points
#   unused (ConserveScore: keep and save where it costs little);
# - "default": the base agent (`our_spec`) unchanged.
# The three biased ones play each turn by the whole-turn planner (search.turnplan, `nodes` per plan) under the
# lethal agent (a lethal is always taken), scored by the bias over our_spec's own evaluation. All directions use the
# same sample seeds (paired).
DIRECTIONS = ("race", "clear", "conserve", "default")


class ClearScore:
    """Minus `per_stat` x the enemy followers' attack plus defense, plus `tiebreak` x the base evaluation."""

    def __init__(self, base, per_stat: float = 8.0, tiebreak: float = 0.25):
        self.base, self.per_stat, self.tiebreak = base, per_stat, tiebreak

    def score(self, state, player: int, player_moves_next: bool = False) -> float:
        from svsim.search.evaluate import WIN, evaluate
        if state.winner is not None:
            return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
        enemy = sum(f.atk + max(f.life, 0) for f in state.players[1 - player].followers)
        return -self.per_stat * enemy + self.tiebreak * evaluate(state, player, self.base, player_moves_next)


class ConserveScore:
    """The base evaluation plus `per_card` per card in hand, `per_pp` per play point left and `per_ep` per
    evolution and super-evolution point left: small, so it only tips lines that are nearly even."""

    def __init__(self, base, per_card: float = 2.0, per_pp: float = 1.0, per_ep: float = 4.0):
        self.base, self.per_card, self.per_pp, self.per_ep = base, per_card, per_pp, per_ep

    def score(self, state, player: int, player_moves_next: bool = False) -> float:
        from svsim.search.evaluate import WIN, evaluate
        if state.winner is not None:
            return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
        p = state.players[player]
        return (evaluate(state, player, self.base, player_moves_next) + self.per_card * len(p.hand)
                + self.per_pp * p.pp + self.per_ep * (p.ep + p.sep))


def _weights_of(agent):
    """The evaluation an agent searches with (its search's, else its own), or the default."""
    from svsim.search.evaluate import DEFAULT
    for _ in range(5):
        if agent is None:
            break
        search = getattr(agent, "search", None)
        if search is not None and hasattr(search, "weights") and not hasattr(search, "solve"):
            return search.weights
        if hasattr(agent, "weights"):
            return agent.weights
        agent = getattr(agent, "base", None)
    return DEFAULT


def direction_agent(direction: str, our_spec: str, seed: int, nodes: int = 300, clock_nodes: int = 200):
    """The agent that plays our turns in `direction` (DIRECTIONS)."""
    from svsim.agents.lethal_agent import LethalAgent
    from svsim.search.candidates import ClockScore
    from svsim.search.turnplan import TurnPlanAgent
    from svsim.tools.arena import make_agent
    if direction == "default":
        return make_agent(our_spec, seed)
    base = _weights_of(make_agent(our_spec, seed))
    score = {"race": lambda: ClockScore(base, nodes=clock_nodes), "clear": lambda: ClearScore(base),
             "conserve": lambda: ConserveScore(base)}[direction]()
    return LethalAgent(TurnPlanAgent(max_nodes=nodes, samples=2, seed=seed, weights=score), seed=seed, planner=True)


def direction_rollout(state, direction="all", k: int = 8, seed: int = 0, opp_spec: str = "level-strong",
                      our_spec: str = "level-strong", opponent_started: bool = True, nodes: int = 300,
                      max_actions: int = 3000) -> dict:
    """{direction: {"win": our mean result (win 1, draw 0.5), "samples": [...], "turns": the mean global turns
    played to the end, "ms": wall time}} for `direction` ("all", one of DIRECTIONS or a list). We are the player
    who just ended the turn (1 - state.active); the position's two forms as next_lethal_prob's."""
    from svsim.tools.arena import make_agent
    me = 1 - state.active
    directions = list(DIRECTIONS) if direction == "all" else [direction] if isinstance(direction, str) else list(direction)
    rng = random.Random(seed)
    seeds = [rng.randrange(2 ** 31) for _ in range(k)]
    out = {}
    for d in directions:
        t0 = time.perf_counter()
        samples, turns = [], []
        for sd in seeds:
            if state.over:
                samples.append(1.0 if state.winner == me else 0.0 if state.winner == 1 - me else 0.5)
                turns.append(0)
                continue
            s = determinize(state, me, random.Random(sd))
            if not opponent_started:
                from svsim.core.engine import _start_turn
                _start_turn(s)
                if s.winner is not None:
                    from svsim.core.enums import Phase
                    s.phase = Phase.OVER
            agents = {me: direction_agent(d, our_spec, sd, nodes), 1 - me: make_agent(opp_spec, sd)}
            n = 0
            while not s.over and n < max_actions:
                apply(s, agents[s.active].act(s, legal_actions(s)))
                n += 1
            samples.append(1.0 if s.winner == me else 0.0 if s.winner == 1 - me else 0.5)
            turns.append(s.turn - state.turn)
        out[d] = {"win": sum(samples) / len(samples) if samples else 0.0, "samples": samples,
                  "turns": sum(turns) / len(turns) if turns else 0.0,
                  "ms": round((time.perf_counter() - t0) * 1000, 1)}
    return out
