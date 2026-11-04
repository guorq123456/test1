"""Which followers pay off an evolution point: measured from what evolving them does, never listed by hand.

The player's games (the test session's count, 2026-10-07): they keep their evolution points when a
card that does much more when evolved is in hand but can't be played or evolved this turn, and spend
them on it within two turns; the bot spends points as soon as it can. A held point is worth what it
can be spent on, so the evaluation needs to know which cards are worth spending one on, for any
deck: no table of cards (the player's rule, docs/architecture.md §9.2).

`evolve_payoff(defn, super_)`: in the roles sandbox (learn.roles: 10 play points, two enemy
followers of 8 defense, the enemy leader at 10), the follower is put on the field and evolved (or
super-evolved) with a point, the best of its target choices; what that does beyond a plain
evolution's stats (+2/+2, super +3/+3) is measured in the role units and summed with weights:
damage to the enemy leader 1, enemy followers taken out 4 each (8 defense), defense healed 0.5,
cards drawn 2, play points 2, extra attack and defense 1 each, plus what the field (crests it leaves
included) does more over the three rounds of turns afterwards (face 1, clear 4, heal 0.5), plus a
Storm follower's attack gain; kept apart as face and value (`evolve_parts`): a lasting effect counts
for three turns (the test session's grouping of the player's holds: Bandenat, whose crest
burns 2 a turn, is the card they super-evolve most). `tier(defn)`: 2 at PAYOFF or more, 1 at LIGHT.
"""
from __future__ import annotations

PAYOFF = 5.0                         # points of measured effect beyond a plain evolution: pays off well
LIGHT = 2.0                          # ... pays off some
PLAIN = {False: 4, True: 6}          # attack + defense a plain evolution / super-evolution adds
WEIGHTS = {"face": 1.0, "removal": 4.0, "heal": 0.5, "draw": 2.0, "ramp": 2.0}
_PARTS: dict = {}


def evolve_parts(defn, super_: bool = False) -> tuple[float, float]:
    """(face, value): what evolving (super-evolving) `defn` with a point does beyond a plain evolution,
    split by kind (the player: evolving Sagatsumatsu, a 5/4 with Storm, is 2 to the face at least, which
    is worth a lot when racing; an evolution that draws or clears is worth more the longer the game):
    face = damage to the enemy leader now and from the field over three rounds, plus the plain attack gain
    (2, super 3) if it can attack the leader the turn it is played (Storm); value = everything else
    (removal, draw, play points, heal, extra stats, the field's clearing and healing over three rounds)."""
    key = (defn.card_id, super_)
    hit = _PARTS.get(key)
    if hit is not None:
        return hit
    from svsim.core import effects as E
    from svsim.core.actions import Evolve
    from svsim.core.engine import apply, legal_actions, resolve_queue
    from svsim.core.enums import Keyword
    from svsim.learn.roles import _measure, _sandbox
    best = (0.0, 0.0)
    if defn.is_follower:
        try:
            state = _sandbox()
            me = state.players[0]
            me.ep, me.sep = 2, 2
            inst = E.summon(state, 0, defn)
            resolve_queue(state)                     # entering effects first (Analyzing Artifact draws)
            inst.entered_turn = -1
            evolves = [a for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == inst.uid
                       and a.super_ == super_]
            plain = _round(state)                    # rounds of turns without the evolution
            storm = PLAIN[super_] / 2 if defn.keywords & Keyword.STORM else 0.0
            for action in evolves[:8]:
                t = state.clone()
                m0 = t.players[0]
                hand, max_pp, pp = len(m0.hand), m0.max_pp, m0.pp
                body0 = sum(f.atk + max(f.life, 0) for f in m0.followers)
                apply(t, action)
                m = t.players[0]
                got = _measure(state, t)
                got["draw"] = max(len(m.hand) - hand, 0)
                got["ramp"] = max(m.max_pp - max_pp, 0) + 0.5 * max(m.pp - pp, 0)
                body = sum(f.atk + max(f.life, 0) for f in m.followers) - body0
                face = WEIGHTS["face"] * float(got["face"]) + storm
                value = sum(WEIGHTS[k] * float(got[k]) for k in WEIGHTS if k != "face") + \
                    max(body - PLAIN[super_], 0)
                if not t.over:                       # what the field (crests included) does more afterwards
                    after = _round(t)
                    face += max(after[0] - plain[0], 0)
                    value += 4.0 * max(after[2] - plain[2], 0) + 0.5 * max(after[1] - plain[1], 0)
                if face + value > sum(best):
                    best = (face, value)
        except Exception:                            # a card the sandbox can't evolve: no payoff
            best = (0.0, 0.0)
    _PARTS[key] = best
    return best


def evolve_payoff(defn, super_: bool = False) -> float:
    """The whole measured payoff (face + value)."""
    return sum(evolve_parts(defn, super_))


def parts(defn) -> tuple[float, float]:
    """(face, value) of the evolution or the super-evolution, whichever pays off more."""
    return max(evolve_parts(defn, False), evolve_parts(defn, True), key=sum)


ROUNDS = 3                           # lasting effects (crests, amulets, each-turn triggers) count this many rounds


def _round(state, rounds: int = ROUNDS) -> tuple:
    """(face, heal, clear) of `rounds` rounds of turns from `state` (the holder's end of turn, the opponent's
    turn, the holder's turn starting, ...), its followers kept from attacking: what the field and crests do
    alone, added up (Bandenat's crest deals 2 a turn: 6 over three rounds)."""
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply
    from svsim.learn.roles import _measure
    t = state.clone()
    before = t.clone()
    for _ in range(2 * rounds):
        if t.over:
            break
        apply(t, EndTurn())
    got = _measure(before, t)
    return float(got["face"]), float(got["heal"]), float(got["removal"])


def payoff(defn) -> float:
    """The larger of the evolution's and the super-evolution's measured payoff."""
    return max(evolve_payoff(defn, False), evolve_payoff(defn, True))


_TIERS: dict = {}
_BOTH: dict = {}


def both_parts(defn) -> tuple:
    """(evolve_parts(defn, False), evolve_parts(defn, True)), cached by card."""
    hit = _BOTH.get(defn.card_id)
    if hit is None:
        hit = _BOTH[defn.card_id] = (evolve_parts(defn, False), evolve_parts(defn, True))
    return hit


def tier(defn) -> int:
    """2: pays off an evolution point well (PAYOFF or more), 1: some (LIGHT or more), 0: no more than stats."""
    hit = _TIERS.get(defn.card_id)
    if hit is None:
        v = payoff(defn) if defn.is_follower else 0.0
        hit = _TIERS[defn.card_id] = 2 if v >= PAYOFF else 1 if v >= LIGHT else 0
    return hit


def is_payoff(defn) -> bool:
    return tier(defn) > 0
