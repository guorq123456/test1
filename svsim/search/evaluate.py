"""Heuristic evaluation of a position, for search and simple agents.

`evaluate(state, player)` scores the position for `player` (positive = good),
assuming the opponent moves next, as at the end of `player`'s turn. It adds up,
for each side and with opposite signs:

- leader defense, worth more per point as it gets low;
- followers (attack, defense and keywords), amulets and crests;
- cards in hand, unused evolution points, max play points;
- danger: whether the opponent's board could kill the player next turn (a big
  penalty), and pressure: whether the player's board threatens the same;
- an empty deck (the next draw loses).

The weights are hand-set starting values (`Weights`), meant to be tuned by
self-play later; a learned value network can replace the whole function.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from svsim.core.engine import EVOLVE_TURN, SUPER_EVOLVE_TURN
from svsim.core.enums import CardType, Keyword
from svsim.core.script import prop
from svsim.core.state import GameState, PlayerState

WIN = 1000.0


@dataclass(frozen=True)
class Weights:
    hp: float = 0.6            # per point of leader defense ...
    hp_sqrt: float = 2.0       # ... plus this times its square root (low defense matters more)
    atk: float = 1.0           # per point of follower attack
    life: float = 0.8          # per point of follower defense
    ward: float = 1.0
    bane: float = 1.5
    drain: float = 0.3         # per point of attack
    barrier: float = 1.0
    ambush: float = 0.5
    aura: float = 0.5
    intimidate: float = 0.5
    amulet: float = 0.6        # per point of base cost
    crest: float = 2.0
    hand: float = 1.2          # per card in hand
    ep: float = 1.0            # per unused evolution point
    sep: float = 1.5           # per unused super-evolution point
    max_pp: float = 0.4        # per max play point
    danger: float = 12.0       # the opponent's board could kill the player next turn
    pressure: float = 4.0      # the player's board could kill the opponent the turn after
    deck_out: float = 30.0     # an empty deck


DEFAULT = Weights()


def follower_value(c, w: Weights = DEFAULT) -> float:
    atk = c.atk * (0.3 if prop(c, "cant_attack") else 1.0)
    value = w.atk * atk + w.life * max(c.life, 0)
    k = c.keywords
    if k & Keyword.WARD:
        value += w.ward
    if k & Keyword.BANE:
        value += w.bane
    if k & Keyword.DRAIN:
        value += w.drain * c.atk
    if k & Keyword.BARRIER:
        value += w.barrier
    if k & Keyword.AMBUSH:
        value += w.ambush
    if k & Keyword.AURA:
        value += w.aura
    if k & Keyword.INTIMIDATE:
        value += w.intimidate
    return value


def side_value(p: PlayerState, w: Weights = DEFAULT) -> float:
    hp = max(p.leader_hp, 0)
    value = w.hp * hp + w.hp_sqrt * math.sqrt(hp)
    for c in p.field:
        value += follower_value(c, w) if c.defn.is_follower else w.amulet * c.defn.cost + 0.5
    value += w.crest * sum(c.defn.type == CardType.CREST for c in p.leader_area)
    value += w.hand * min(len(p.hand), 9)
    value += w.ep * p.ep + w.sep * p.sep + w.max_pp * p.max_pp
    if not p.deck:
        value -= w.deck_out
    return value


def threat(state: GameState, side: int) -> int:
    """Rough damage `side` could deal to the enemy leader on its next turn: all its
    followers attack (they will all be ready), plus an evolution; enemy Ward soaks
    up damage equal to its defense."""
    p, enemy = state.players[side], state.players[1 - side]
    followers = [f for f in p.followers if not prop(f, "cant_attack")]
    if not followers:
        return 0
    damage = sum(f.atk * max(1, f.max_attacks) for f in followers)
    first = side == state.first
    turn = p.turns_taken + 1
    if p.sep > 0 and turn >= SUPER_EVOLVE_TURN[first]:
        damage += 3
    elif p.ep > 0 and turn >= EVOLVE_TURN[first]:
        damage += 2
    damage -= sum(max(f.life, 0) for f in enemy.followers if f.keywords & Keyword.WARD)
    return max(damage, 0)


def evaluate(state: GameState, player: int, w: Weights = DEFAULT,
             player_moves_next: bool = False) -> float:
    """Score for `player`. By default the opponent moves next (the end of
    `player`'s turn); with `player_moves_next` (the start of `player`'s turn)
    danger and pressure swap weights."""
    if state.winner is not None:
        return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
    me, opp = state.players[player], state.players[1 - player]
    score = side_value(me, w) - side_value(opp, w)
    danger, pressure = (w.pressure, w.danger) if player_moves_next else (w.danger, w.pressure)
    if threat(state, 1 - player) >= me.leader_hp:
        score -= danger
    if threat(state, player) >= opp.leader_hp:
        score += pressure
    return score


def after_end_of_turn(state: GameState) -> GameState:
    """A copy of the position once the player to act ends the turn: end-of-turn
    abilities resolve, but the opponent's turn doesn't start."""
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply
    from svsim.core.enums import DRAW, Phase
    s = state.clone()
    s.max_turns = s.turn                  # the engine stops at the turn limit before the next turn
    apply(s, EndTurn())
    if s.winner == DRAW and state.turn < state.max_turns:
        s.winner, s.phase = None, Phase.MAIN
    return s
