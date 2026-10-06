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

from svsim.core.enums import CardType, Keyword
from svsim.core.script import prop
from svsim.core.state import GameState
from svsim.search.evaluate import hand_count

SIDE = ["hp", "hp_sqrt", "hp_low", "followers", "atk", "life", "ward", "bane", "drain", "barrier", "evasive",
        "amulets", "amulet_cost", "crests", "hand", "ep", "sep", "max_pp", "deck_low", "deck_out",
        "board_threat", "board_lethal"]
POTENTIAL = ["potential", "potential_lethal", "potential10", "potential10_lethal"]


def names(potential: bool) -> list[str]:
    side = SIDE + (POTENTIAL if potential else [])
    return [f"me_{n}" for n in side] + [f"op_{n}" for n in side] + ["bias"]


# Features whose direction isn't up to the data: more defense for my leader is
# never worse (hp_low counts *low* defense, so it goes the other way), a sure
# lethal on board is never worse, an empty deck never better. Learned from games
# against one opponent, a model can pick up a confound (the learned Ramp model
# liked its own leader at 5 defense or less, from a card that sets its max
# defense to 1), so the fit keeps these signs (fit.fit, `signs`).
MONOTONE = {"hp": 1, "hp_sqrt": 1, "hp_low": -1, "board_lethal": 1, "potential_lethal": 1,
            "potential10_lethal": 1, "deck_out": -1}


def signs(potential: bool) -> list[int]:
    """+1 / -1 where a coefficient must not be negative / positive, 0 where it is free."""
    out = []
    for n in names(potential):
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


def side_features(state: GameState, side: int, potential: bool) -> list[float]:
    p, enemy = state.players[side], state.players[1 - side]
    hp = max(p.leader_hp, 0)
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
           sum(1 for c in p.leader_area if c.defn.type == CardType.CREST),
           hand_count(p), p.ep, p.sep, p.max_pp, float(len(p.deck) <= 3), float(not p.deck),
           min(threat, max(enemy.leader_hp, 0)), float(threat >= enemy.leader_hp)]
    if potential:
        from svsim.search.combo import next_turn_damage
        hp = max(enemy.leader_hp, 0)
        dmg = next_turn_damage(state, side, 300, board=False)
        full = next_turn_damage(state, side, 300, board=False, pp=10)
        out += [min(dmg, hp), float(dmg >= hp), min(full, hp), float(full >= hp)]
    return out


def features(state: GameState, player: int, potential: bool = True) -> list[float]:
    """The features of `state` scored for `player` (the opponent moves next)."""
    return side_features(state, player, potential) + side_features(state, 1 - player, potential) + [1.0]
