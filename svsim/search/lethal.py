"""Lethal search: can the player to act win this turn, and how?

Depth-first search over the current player's actions within the turn, on
clones of the state. A position's value is the chance to win this turn: 1 for
a line that wins whatever happens.

Randomness and hidden information. The simulator knows the deck order and the
random number generator's next numbers; a player doesn't. So an action whose
result depends on either (it used the RNG, or took cards from a deck) is a
chance node: instead of the simulator's own outcome, it is re-run on
`samples` copies with fresh RNG seeds and reshuffled decks, and its value is
the average. Only a line without chance nodes counts as a sure lethal. The
opponent's hand is used as it is (it rarely matters on your own turn).

Ending the turn is an action too: end-of-turn abilities can win, and so can an
opponent who has to draw from an empty deck. Wins later in the opponent's turn
don't count.

Speed: positions reached by different orders of the same actions share one
entry in a transposition table (keyed by everything that matters except card
uids and the RNG state); attacks on the leader are tried first; the search
stops at the first sure lethal, or when the node budget runs out.

Screening (optional, `screen=N`): most positions have no lethal, and proving
that is what costs time. `damage_estimate` guesses the most damage this turn
(face attacks, plus each card, Engage or evolution tried on its own); when that
falls short of the opponent's defense, only N nodes are searched. It is a guess,
not a bound: combos (buffs that only pay off together, extra attacks, damage
from effects other than hitting the leader) can beat it. Measured on 1,181
positions with 122 sure lethals (found with 20,000 nodes): 2,000 nodes each
missed 5 of them; with screen=200 it was about 5x faster and missed 7.
`near=(N2, K)`: a screened position whose estimate falls short by K or less gets
N2 nodes instead (the architecture session, 2026-10-07: the smoke games' screen
misses that 1,000 nodes find were all 1 to 4 short; screening everything at
1,000 cost 81%-95% more time per turn).
"""
from __future__ import annotations

from dataclasses import dataclass
import random
import time

from svsim.core.actions import Attack, EndTurn, Engage, Evolve, PlayCard, UseBonusPP
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import DRAW, Keyword, Phase
from svsim.core.script import prop
from svsim.core.state import CHECK as COW_CHECK, CardInstance, GameState, sweep
from svsim.core.view import shuffle

EPS = 1e-9


@dataclass
class LethalResult:
    probability: float   # chance to win this turn with the best line found
    line: list           # actions: the whole line if sure, else up to its first chance action
    sure: bool           # the line wins whatever the deck order and random results
    nodes: int           # positions searched
    complete: bool       # the search finished within its budget (else a lethal may be missed)
    seconds: float
    screened: bool = False   # the damage estimate fell short, so only a quick search ran

    @property
    def found(self) -> bool:
        return self.sure


def _card_key(c: CardInstance, turn: int) -> tuple:
    return (c.defn.card_id, c.cost, c.atk, c.life, c.max_life, int(c.keywords), c.countdown,
            c.evolved, c.super_evolved, c.attacks_made, c.max_attacks, c.entered_turn == turn,
            c.engaged_turn == turn, c.fused_turn == turn, c.silenced, c.no_last_words,
            repr(sorted(c.counters.items())) if c.counters else "",
            tuple((type(g.script).__name__ if g.script else "", g.until_turn, g.atk, g.life,
                   int(g.keywords)) for g in c.grants) if c.grants else (),
            tuple(c.cost_mods) if c.cost_mods else ())


def state_key(state: GameState) -> tuple:
    """Everything that decides what can happen next, except card uids and the RNG
    state: positions with the same key play out the same."""
    turn = state.turn
    sides = []
    for p in state.players:
        sides.append((
            p.leader_hp, p.leader_max_hp, p.pp, p.max_pp, p.ep, p.sep, p.turns_taken,
            p.evolved_this_turn, p.bonus_ready, p.bonus_active, p.combo, p.rally, p.shadows,
            p.evolutions, p.attacked_leader_this_turn, p.damage_cap, p.damage_cap_until,
            p.extra_damage, tuple(sorted(p.entered.items())), frozenset(p.played_base_costs),
            tuple(d.card_id for d in p.destroyed), tuple(d.card_id for d in p.destroyed_amulets),
            tuple(_card_key(c, turn) for c in p.field),
            tuple(_card_key(c, turn) for c in p.leader_area),
            tuple(sorted(_card_key(c, turn) for c in p.hand)),
            tuple(sorted(c.defn.card_id for c in p.deck_view())),
        ))
    return state.turn, state.active, tuple(sides)


def hidden_info(state: GameState) -> tuple:
    """What a player can't know: the RNG state and the deck order. If an action
    changes it, its result depended on luck or on hidden cards."""
    return (state.rng.getstate(), tuple(c.uid for c in state.players[0].deck_view()),
            tuple(c.uid for c in state.players[1].deck_view()))


def face_damage(state: GameState, player: int) -> int:
    """Attack damage `player`'s followers could still deal to the leader this turn,
    ignoring Ward."""
    total = 0
    for f in state.players[player].followers:
        left = f.max_attacks - f.attacks_made
        if left <= 0 or prop(f, "cant_attack"):
            continue
        if f.entered_turn == state.turn and not f.keywords & Keyword.STORM:
            continue
        total += f.atk * left
    return total


def damage_estimate(state: GameState) -> float:
    """A guess at the most damage the player to act can deal this turn: face
    attacks, plus the best evolution and the best set of cards and Engages within
    the play points, each tried on its own (direct damage plus new face attacks).
    Not a bound: effects that only pay off together are missed."""
    me, opp = state.active, 1 - state.active
    if not state.players[opp].deck_view() or state.players[opp].extra_damage:
        return float("inf")              # deck-out at their draw; extra damage per hit
    hp, face, pp = state.players[opp].leader_hp, face_damage(state, me), state.players[me].pp
    items, evolve_best, bonus = {}, 0, 0
    for action in legal_actions(state):
        if isinstance(action, (Attack, EndTurn)):
            continue
        if isinstance(action, UseBonusPP):
            bonus = 1
            continue
        s = state.clone()
        apply(s, action)
        if s.winner == me:
            return float("inf")
        gain = (hp - s.players[opp].leader_hp) + (face_damage(s, me) - face)
        if isinstance(action, Evolve):
            evolve_best = max(evolve_best, gain)
            continue
        key = (type(action) is Engage, action.uid)        # a card (played or fused to) or an amulet
        if gain > items.get(key, (0, 0))[0]:
            items[key] = (gain, max(0, pp - s.players[me].pp))
    budget = pp + bonus
    best = [0] * (budget + 1)            # 0/1 knapsack over play points
    for gain, cost in items.values():
        for b in range(budget, cost - 1, -1):
            best[b] = max(best[b], best[b - cost] + gain)
    return face + evolve_best + best[budget]


class LethalSearch:
    def __init__(self, max_nodes: int = 20000, samples: int = 8, max_depth: int = 40,
                 seed: int = 0, screen: int | None = None, sure_only: bool = False,
                 near: tuple[int, int] | None = None):
        self.max_nodes = max_nodes
        self.samples = samples        # outcomes sampled at a chance node (halved at each nested one)
        self.max_depth = max_depth    # actions in one line
        self.seed = seed
        self.screen = screen          # node budget when damage_estimate falls short (None: off)
        self.sure_only = sure_only    # only look for sure lethals: don't expand chance nodes
        self.near = near              # (nodes, K): the budget when the estimate is short by K or less

    def solve(self, state: GameState) -> LethalResult:
        if state.phase != Phase.MAIN or state.winner is not None:
            raise ValueError("lethal search needs a game in its main phase")
        start = time.perf_counter()
        short = (state.players[1 - state.active].leader_hp - damage_estimate(state)
                 if self.screen is not None else 0)
        screened = short > 0
        self.budget = (self.max_nodes if not screened else
                       self.near[0] if self.near is not None and short <= self.near[1] else self.screen)
        self.me = state.active
        self.tt: dict = {}
        self.nodes = 0
        self.exhausted = False
        self.rng = random.Random(self.seed)
        value, line, sure = self._search(state, 0, 0)
        if COW_CHECK:                              # check mode (core.state): no shared deck card changed
            sweep(keep=state)
        return LethalResult(value, line, sure and value >= 1 - EPS, self.nodes,
                            not self.exhausted, time.perf_counter() - start, screened)

    # --- the search -----------------------------------------------------------------

    def _search(self, state: GameState, depth: int, chance_depth: int) -> tuple:
        """(value, line, sure) for the player to act, who is self.me."""
        if state.winner is not None:
            won = state.winner == self.me
            return (1.0 if won else 0.0), [], won
        key = state_key(state)
        hit = self.tt.get(key)
        if hit is not None:
            return hit
        if self.nodes >= self.budget or depth >= self.max_depth:
            self.exhausted = True
            return 0.0, [], False
        self.nodes += 1
        best = (0.0, [], False)
        info = hidden_info(state)          # what every child starts from (a clone has the same)
        for action in self._ordered(state):
            value, line, sure = self._evaluate(state, action, depth, chance_depth, best[0], info)
            if value > best[0] + EPS or (sure and not best[2] and value >= best[0] - EPS):
                best = (value, [action] + line, sure)
                if sure and value >= 1 - EPS:
                    break
        self.tt[key] = best
        return best

    def _evaluate(self, state, action, depth, chance_depth, alpha, before=None) -> tuple:
        if isinstance(action, EndTurn):
            return self._end_turn(state, chance_depth, alpha, before)
        child = state.clone()
        if before is None:
            before = hidden_info(child)
        apply(child, action)
        if hidden_info(child) == before:
            return self._search(child, depth + 1, chance_depth)
        if self.sure_only:                # a line through a chance node is never sure
            return 0.0, [], False

        def run(sample):
            apply(sample, action)
            return self._search(sample, depth + 1, chance_depth + 1)[0]
        return self._chance(state, run, chance_depth, alpha), [], False

    def _end_turn(self, state, chance_depth, alpha, before=None) -> tuple:
        """Ending the turn wins if end-of-turn abilities finish the opponent, or if
        the opponent then has to draw from an empty deck."""
        def run(sample) -> float:
            sample.max_turns = sample.turn            # stop before the opponent's turn starts
            apply(sample, EndTurn())
            if sample.winner == self.me:
                return 1.0
            if sample.winner == DRAW and state.turn < state.max_turns:
                return 1.0 if not sample.players[1 - self.me].deck_view() else 0.0
            return 0.0

        probe = state.clone()
        if before is None:
            before = hidden_info(probe)
        value = run(probe)
        if hidden_info(probe) == before:
            return value, [], value >= 1 - EPS
        if self.sure_only:
            return 0.0, [], False
        return self._chance(state, run, chance_depth, alpha), [], False

    def _chance(self, state, run, chance_depth, alpha) -> float:
        """Average of `run` over fresh outcomes: new RNG seeds, reshuffled decks.
        Stops early once it can't beat `alpha`."""
        k = max(2, self.samples >> chance_depth)
        total = 0.0
        for i in range(k):
            if (total + (k - i)) / k <= alpha + EPS:
                break
            sample = state.clone(copy_rng=False)          # seeded at once
            sample.rng.seed(self.rng.getrandbits(64))
            for p in sample.players:
                shuffle(sample.rng, p._deck)               # core.view: rng.shuffle, written out (the clone's own list)
            total += run(sample)
        return total / k

    def _ordered(self, state: GameState) -> list:
        """Legal actions, likeliest to win first: attacks on the leader (strongest
        first), cards, evolutions, other actions, attacks on followers, ending the turn."""
        def rank(action):
            if isinstance(action, Attack):
                if action.target < 0:
                    attacker = state.on_field(action.attacker)
                    return 0, -(attacker.atk if attacker else 0)
                return 4, 0
            if isinstance(action, PlayCard):
                return 1, 0
            if isinstance(action, Evolve):
                return 2, 0
            if isinstance(action, EndTurn):
                return 5, 0
            return 3, 0
        return sorted(legal_actions(state), key=rank)


def find_lethal(state: GameState, max_nodes: int = 20000, samples: int = 8,
                seed: int = 0, screen: int | None = None) -> LethalResult:
    """Search the current player's turn for a lethal line."""
    return LethalSearch(max_nodes=max_nodes, samples=samples, seed=seed, screen=screen).solve(state)
