"""Host stand-ins for tools/compute_noise.py (LD-57) and for the turn-start budget's checks (A68, Salem 11-27: compute
by turns): honest strategies whose cost against the default's changes with the position, and planners of each kind
the receipt's two rules (submit.compute_verdict) must tell apart.

- Adaptive: the default search, its iterations growing with how far the game is (50 at the start, +4 per card the
  opponent has shown, at most 160): cheap early, dear late, so long games cost more than short ones.
- Overhead: the default plus a fixed piece of pure-Python work before every decision (about 3 ms in the container):
  a large ratio on cheap positions, a small one on dear ones.
- Planner: the turn-start budget used as meant. At each own turn's start (turn_start) PLAN_SEARCHES searches of the
  default's own size (100 iterations) on states sampled with self.random; the moves they pick kept on self (by
  action_key) and not acted on: a stand-in for the cost. Every other part of each decision is the default's own
  (nothing touches self.rng, self.agent or self.tree), so its in-turn pool is the default's. PLAN_SEARCHES is
  SEARCHES_PER_TURN x submit.TURN_K: about TURN_K default turns at the turn starts (SEARCHES_PER_TURN, a default turn
  in such searches, is the container's rough figure: set it again from the PC's extra_turns, the receipt's).
- PlannerOver: the Planner with 1.3 times the work (refused by the turn rule once the noise is known).
- Spread: the Planner's work over every MAIN decision instead (PLAN_SEARCHES / DECISIONS_PER_TURN each, the remainder
  carried): the same total, refused by both rules.
- Hoarder: the Planner's work every other own turn, twice as much (the same mean: the budget is an average).
- PlanUses: a cheap planner that acts on its plan (a prior on the moves its own small searches picked at the turn's
  start): honest, for the extended peek check's false alarms.
- PlanPeeky: reads the referee's real state off the call stack in its turn-start hook only and plays by it at the
  turn's later decisions (what submit.peek_turn must catch; the code reader refuses it: sys).
- Memory: keeps a module-level book from game to game, read by its search settings (what the determinism replay of
  late games must catch; the code reader lets it in).

Measurement tools only: these say nothing about strength.
"""
from __future__ import annotations

import sys

from ladder.interface import PlayerStrategy, action_key, sample_states
from ladder.submit import TURN_K
from svsim.core.enums import Phase
from svsim.core.state import GameState
from svsim.search.mcts import ISMCTS

SEARCHES_PER_TURN = 5        # a default turn in 100-iteration searches on samples: the container's rough figure (two
                             # games, 11-28: 12 a turn added 2.2 default turns); set again from the PC's
DECISIONS_PER_TURN = 3.9     # the default's decisions an own turn (the cloud probe, 180 turns)


class Adaptive(PlayerStrategy):
    def search(self, pos):
        return {"iterations": int(min(160, 50 + 4 * len(pos.opp_log)))}


class Overhead(PlayerStrategy):
    WORK = 40000

    def act(self, pos, actions):
        x = 0
        for i in range(self.WORK):
            x = (x * 31 + i) % 1000003
        self.last_work = x
        return super().act(pos, actions)


class Planner(PlayerStrategy):
    PLAN_SEARCHES = round(SEARCHES_PER_TURN * TURN_K)
    PLAN_ITERATIONS = 100

    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self.planner = ISMCTS(iterations=self.PLAN_ITERATIONS, seed=self.random.getrandbits(31))
        self.picked = (None, [])

    def think(self, pos, searches: int) -> None:
        picks = []
        for s in sample_states(pos, self.guess(pos), self.random, searches):
            picks.append(action_key(s, self.planner.choose(s)))
        self.picked = (pos.state.turn, picks)

    def turn_start(self, pos):
        self.think(pos, self.PLAN_SEARCHES)


class PlannerOver(Planner):
    PLAN_SEARCHES = round(1.3 * SEARCHES_PER_TURN * TURN_K)


class Spread(Planner):
    """No turn-start work; the same total in every MAIN decision (a mulligan is not one)."""

    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self.owed = 0.0

    def act(self, pos, actions):
        if pos.state.phase == Phase.MAIN:
            self.owed += self.PLAN_SEARCHES / DECISIONS_PER_TURN
            n = int(self.owed)
            self.owed -= n
            if n:
                self.think(pos, n)
        return super().act(pos, actions)

    def turn_start(self, pos):
        return None


class Hoarder(Planner):
    """Twice the Planner's work on every second own turn, none on the others."""

    def turn_start(self, pos):
        if pos.state.players[pos.me].turns_taken % 2 == 0:
            self.think(pos, 2 * self.PLAN_SEARCHES)


class PlanUses(Planner):
    """Cheap, and acting on its plan: the moves its own small searches picked at the turn's start get a prior."""
    LETHAL = "exact"
    PLAN_SEARCHES = 2
    PLAN_ITERATIONS = 20

    def search(self, pos):
        return {"iterations": 4}

    def prior(self, state, actions):
        turn, picks = self.picked
        if turn != state.turn or not picks:
            return None
        w = [3.0 if action_key(state, a) in picks else 1.0 for a in actions]
        return [x / sum(w) for x in w]


class PlanPeeky(PlayerStrategy):
    """Peeks only in turn_start: the real state's opponent hand and deck top, off the call stack (any local called
    `state` that is a GameState and not the public one), kept as a number; the turn's later decisions play
    actions[number % len]. The turn's first decision is the plain search, so the plain peek check finds nothing."""
    LETHAL = "exact"

    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self.mark = (None, None)

    def search(self, pos):
        return {"iterations": 4}

    def act(self, pos, actions):
        turn, bias = self.mark
        if pos.state.phase == Phase.MAIN and turn == pos.state.turn and bias is not None:
            return actions[bias % len(actions)]
        return super().act(pos, actions)

    def turn_start(self, pos):
        f = sys._getframe(1)
        while f is not None:
            s = f.f_locals.get("state")
            if isinstance(s, GameState) and s is not pos.state:
                opp = s.players[1 - pos.me]
                bias = sum(c.defn.card_id for c in opp.hand) + sum(c.defn.card_id for c in opp.deck_view()[-3:])
                self.mark = (pos.state.turn, bias)
                return
            f = f.f_back
        self.mark = (pos.state.turn, None)


_BOOK = {}                   # Memory's: one count per own-turn number, kept for as long as the process lives


class Memory(PlayerStrategy):
    """Counts, in a module-level book, how often it has started its n-th own turn (in this process: every game the
    worker played); its search's iterations follow the count, so a worker's later games choose otherwise than a
    fresh process replaying them."""
    LETHAL = "exact"

    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self.extra = 0

    def turn_start(self, pos):
        n = pos.state.players[pos.me].turns_taken
        _BOOK[n] = _BOOK.get(n, 0) + 1
        self.extra = _BOOK[n] % 3

    def search(self, pos):
        return {"iterations": 4 + self.extra}
