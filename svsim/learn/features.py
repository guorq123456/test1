"""Generic position features for a learned evaluation.

Each side gets the same features (`me_*` for the player the position is scored
for, `op_*` for the opponent): leader defense, the board (followers' attack,
defense and keywords, amulets, crests), the hand (with what a field of
replayable followers is worth to a deck that returns them, evaluate.hand_count), unused evolution points, max
play points, the deck, how much the board threatens the enemy leader, and,
optionally, how much the hand and amulets could deal next turn by the
resource-flow planner (search.combo.next_turn_damage), and with all 10 play
points (what the hand is building towards). Nothing here is about a
particular deck: which features matter for which deck is what gets learned.
"""
from __future__ import annotations

import math

from svsim.core.enums import Keyword
from svsim.core.script import prop
from svsim.core.state import GameState
from svsim.search.evaluate import effective_hp, good_crests, hand_count

SIDE = ["hp", "hp_sqrt", "hp_low", "followers", "atk", "life", "ward", "bane", "drain", "barrier", "evasive",
        "amulets", "amulet_cost", "crests", "hand", "ep", "sep", "max_pp", "deck_low", "deck_out",
        "board_threat", "board_lethal"]
POTENTIAL = ["potential", "potential_lethal", "potential10", "potential10_lethal"]
# Version 2 (the player's verdict on the evaluation, 2026-10-06: it couldn't see what the
# cards are for, what each side has left, or what the field does turn after turn): the
# hand's roles (learn.roles: face damage, removal, heal, draw, ramp, body; the opponent's
# hand as their share of the cards not seen yet, which is all the bot can know), the roles
# left in the deck (the opponent's: hand and deck, card counting from the known list),
# what the field and crests do each round (face, heal, clear), and the turns the leader
# lasts against what comes at it each turn (board attack past Ward, the opponent's field
# damage each round, a crest's burn).
SIDE2 = ["hand_face", "hand_removal", "hand_heal", "hand_draw", "hand_ramp", "hand_body",
         "pool_face", "pool_removal", "pool_heal", "pool_draw", "pool_ramp", "pool_body",
         "rec_face", "rec_heal", "rec_clear", "lasts"]


# Version 3 (2026-10-07; the player: the bot spends its evolution points as soon as it can and runs
# out in the long games; the test session's count of the player's games: they keep a point when a
# card that pays off an evolution is in hand but out of reach this turn, and spend it on that card
# within two turns, ahead or behind alike): each side's unused evolution and super-evolution points
# also enter multiplied by their context:
# - turns since that kind of evolution unlocked;
# - the best payoff (learn.payoff.tier: measured from what evolving the card does, never a card list)
#   of a follower the points could go to on the coming turn (on the field, not yet evolved that way,
#   or in hand and affordable then);
# - the best payoff of a follower in hand that is out of reach on the coming turn;
# - how long the game still looks (own turns, both leaders' defense, both decks);
# - and, as a minor term, the leader-defense gap.
# The coming turn: the current one if it is the side's, else the next (one more play point). No term
# for the hand alone: cards in hand get no value of their own (docs/architecture.md, §9.2).
CONTEXT = ["since_unlock", "payoff_now", "payoff_later", "turn", "hp", "op_hp", "decks", "hp_lead"]
SIDE3 = [f"{pt}_x_{c}" for pt in ("ep", "sep") for c in CONTEXT]


def names(potential: bool, version: int = 1) -> list[str]:
    side = SIDE + (POTENTIAL if potential else []) + (SIDE2 if version >= 2 else [])
    extra = [f"me_{n}" for n in SIDE3] + [f"op_{n}" for n in SIDE3] if version >= 3 else []
    return [f"me_{n}" for n in side] + [f"op_{n}" for n in side] + extra + ["bias"]


# Features whose direction isn't up to the data: more defense for my leader is
# never worse (hp_low counts *low* defense, so it goes the other way), a sure
# lethal on board is never worse, an empty deck never better. Learned from games
# against one opponent, a model can pick up a confound (the learned Ramp model
# liked its own leader at 5 defense or less, from a card that sets its max
# defense to 1), so the fit keeps these signs (fit.fit, `signs`).
MONOTONE = {"hp": 1, "hp_sqrt": 1, "hp_low": -1, "board_lethal": 1, "potential_lethal": 1,
            "potential10_lethal": 1, "deck_out": -1, "lasts": 1}


def signs(potential: bool, version: int = 1) -> list[int]:
    """+1 / -1 where a coefficient must not be negative / positive, 0 where it is free."""
    out = []
    for n in names(potential, version):
        side, _, feature = n.partition("_")
        s = MONOTONE.get(feature, 0)
        out.append(s if side == "me" else -s if side == "op" else 0)
    return out


def _board_threat(state: GameState, side: int) -> int:
    """Attack `side`'s followers could put on the enemy leader next turn, minus enemy Ward defense."""
    p, enemy = state.players[side], state.players[1 - side]
    damage = sum(f.atk * max(1, f.max_attacks) for f in p.followers if not prop(f, "cant_attack"))
    damage -= sum(max(f.life, 0) for f in enemy.followers if f.keywords & Keyword.WARD)
    return max(damage, 0)


def _roles_sum(cards) -> list[float]:
    from svsim.learn.roles import card_roles
    out = [0.0] * 6
    for c in cards:
        for i, v in enumerate(card_roles(c.defn)):
            out[i] += v
    return out


def recurring_sum(p) -> list[float]:
    """What `p`'s field and crests do by themselves each round: (face, heal, clear)."""
    from svsim.core.enums import CardType
    from svsim.learn.roles import recurring
    out = [0.0, 0.0, 0.0]
    for c in list(p.field) + [c for c in p.leader_area if c.defn.type == CardType.CREST]:
        for i, v in enumerate(recurring(c.defn, bool(getattr(c, "evolved", False)))):
            out[i] += v
    return out


def resources(state: GameState, side: int, hidden: bool) -> list[float]:
    """The version-2 features of `side` (see SIDE2); `hidden`: its hand is unknown to the
    player the position is scored for."""
    from svsim.search.evaluate import burn, effective_hp
    p, enemy = state.players[side], state.players[1 - side]
    if hidden:
        pool = p.hand + p.deck
        total = _roles_sum(pool)
        share = len(p.hand) / len(pool) if pool else 0.0
        hand = [v * share for v in total]
    else:
        hand, total = _roles_sum(p.hand), _roles_sum(p.deck)
    rec = recurring_sum(p)
    incoming = _board_threat(state, 1 - side) + recurring_sum(enemy)[0] + burn(p)
    lasts = min(effective_hp(p) / max(incoming, 1.0), 10.0)
    return hand + total + rec + [lasts]


def side_features(state: GameState, side: int, potential: bool, version: int = 1, hidden: bool = False) -> list[float]:
    p, enemy = state.players[side], state.players[1 - side]
    hp = effective_hp(p)                 # a crest that hurts its holder: the defense it will take
    followers = p.followers
    k = [f.keywords for f in followers]
    threat = _board_threat(state, side)
    out = [hp, math.sqrt(hp), float(hp <= 5), len(followers),
           sum(f.atk * (0.3 if prop(f, "cant_attack") else 1.0) for f in followers),
           sum(max(f.life, 0) for f in followers),
           sum(1 for x in k if x & Keyword.WARD), sum(1 for x in k if x & Keyword.BANE),
           sum(f.atk for f in followers if f.keywords & Keyword.DRAIN),
           sum(1 for x in k if x & Keyword.BARRIER),
           sum(1 for x in k if x & (Keyword.AMBUSH | Keyword.AURA | Keyword.INTIMIDATE)),
           sum(1 for c in p.field if c.defn.is_amulet), sum(c.defn.cost for c in p.field if c.defn.is_amulet),
           good_crests(p),
           hand_count(p), p.ep, p.sep, p.max_pp, float(len(p.deck) <= 3), float(not p.deck),
           min(threat, max(enemy.leader_hp, 0)), float(threat >= enemy.leader_hp)]
    if potential:
        from svsim.search.combo import next_turn_damage
        hp = max(enemy.leader_hp, 0)
        dmg = next_turn_damage(state, side, 300, board=False)
        full = next_turn_damage(state, side, 300, board=False, pp=10)
        out += [min(dmg, hp), float(dmg >= hp), min(full, hp), float(full >= hp)]
    if version >= 2:
        out += resources(state, side, hidden)
    return out


def context(state: GameState, side: int, hidden: bool, super_: bool = False) -> list[float]:
    """The CONTEXT values of `side`'s evolution points (super-evolution points with `super_`), each about
    0..1; `hidden`: its hand is unknown to the scorer (its share of the cards not seen yet stands in)."""
    from svsim.core.engine import EVOLVE_TURN, SUPER_EVOLVE_TURN
    from svsim.learn.payoff import tier
    p, enemy = state.players[side], state.players[1 - side]
    first = state.first == side
    unlock = (SUPER_EVOLVE_TURN if super_ else EVOLVE_TURN)[first]
    coming = p.turns_taken + (0 if state.active == side else 1)
    pp = p.max_pp if state.active == side else min(p.max_pp + 1, 10)
    pp += 1 if p.bonus_ready else 0
    on_field = [tier(f.defn) for f in p.followers if not (f.super_evolved or (f.evolved and not super_))]
    if hidden:
        pool = p.hand + p.deck
        share = len(p.hand) / len(pool) if pool else 0.0
        now = max([t for t in on_field] + [share * tier(c.defn) for c in pool if c.cost <= pp], default=0)
        later = max([share * tier(c.defn) for c in pool if c.cost > pp], default=0)
    else:
        now = max(on_field + [tier(c.defn) for c in p.hand if c.cost <= pp], default=0)
        later = max([tier(c.defn) for c in p.hand if c.cost > pp], default=0)
    hp, op_hp = effective_hp(p), effective_hp(enemy)
    return [max(coming - unlock, 0) / 5.0 if coming >= unlock else 0.0, now / 2.0, later / 2.0,
            p.turns_taken / 10.0, hp / 20.0, op_hp / 20.0, (len(p.deck) + len(enemy.deck)) / 60.0,
            (hp - op_hp) / 20.0]


def held_points(state: GameState, side: int, hidden: bool) -> list[float]:
    """The version-3 features of `side` (SIDE3)."""
    p = state.players[side]
    return [p.ep * c for c in context(state, side, hidden)] + [p.sep * c for c in context(state, side, hidden, True)]


def features(state: GameState, player: int, potential: bool = True, version: int = 1) -> list[float]:
    """The features of `state` scored for `player` (the opponent moves next)."""
    extra = held_points(state, player, False) + held_points(state, 1 - player, True) if version >= 3 else []
    return (side_features(state, player, potential, version) +
            side_features(state, 1 - player, potential, version, hidden=True) + extra + [1.0])
