"""Heuristic evaluation of a position, for search and simple agents.

`evaluate(state, player)` scores the position for `player` (positive = good),
assuming the opponent moves next, as at the end of `player`'s turn. It adds up,
for each side and with opposite signs:

- leader defense, worth more per point as it gets low;
- followers (attack, defense and keywords), amulets and crests;
- cards in hand (with the cards a field of replayable followers is worth to a
  deck that returns them to hand, `latent_cards`), unused evolution points,
  max play points;
- a crest that hurts its holder (Burnite, Anathema of Ash's, given to the
  opponent: 2 damage at the start of each of their turns) counts as the
  defense it will take over the next `BURN_TURNS` turns, not as a crest
  (`crest_burn`, measured in a sandbox; the player's Ramp mirror games turned
  on it, and the AI had given that crest 1 time in 120 games);
- danger: whether the opponent's board could kill the player next turn (a big
  penalty), and pressure: whether the player's board threatens the same;
- an empty deck (the next draw loses);
- optionally (weights `setup`, `setup_lethal`, zero by default), the damage the
  player's hand and board could deal on the next turn by the resource-flow
  planner (search.combo.next_turn_damage), whatever the deck: a combo deck
  that keeps its pieces for a lethal turn scores for it.

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
BURN_TURNS = 3       # own turns a crest that hurts its holder is counted for
CREST_EFFECTS = True # False: every crest counts for its holder, as before (for comparisons)


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
    setup: float = 0.0         # per point of damage the player could deal next turn (planner), up to lethal
    setup_lethal: float = 0.0  # that damage is lethal
    setup_nodes: int = 300     # planner budget per position
    setup_board: bool = True   # count the player's followers in it (else hand and amulets only)
    ready: float = 0.0         # per point the hand could deal next turn by the player's formula, up to lethal
    dig: float = 0.0           # per card drawn out of the deck (cards seen: the player digs for Rhinoceroaches)
    own_board: float = 1.0     # scale on the player's own followers (a race deck facing board clears keeps few)
    ready_lethal: float = 0.0  # that is lethal


DEFAULT = Weights()
THREAT = Weights(setup=0.5, setup_lethal=6.0)    # values the next turn's lethal potential
THREAT_HAND = Weights(setup=0.5, setup_lethal=6.0, setup_board=False)   # ... from the hand and amulets


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


_REPLAY: dict = {}
_BOUNCES: dict = {}


def _replay_cards(defn) -> int:
    """Cards a card on the field brings to hand when it is returned and played
    again (Fanfare draws or adds, measured at Combo 3 by search.combo.profile)."""
    hit = _REPLAY.get(defn.card_id)
    if hit is None:
        from svsim.search.combo import at_combo, profile
        hit = _REPLAY[defn.card_id] = max((at_combo(v, 3).drawn + len(at_combo(v, 3).added)
                                           for v in profile(defn)), default=0)
    return hit


def _bounces(defn) -> bool:
    hit = _BOUNCES.get(defn.card_id)
    if hit is None:
        from svsim.search.combo import engage_profile, profile
        eng = engage_profile(defn) if defn.is_amulet else None
        hit = _BOUNCES[defn.card_id] = any(v[0].bounce for v in profile(defn)) or bool(eng and eng.bounce)
    return hit


def latent_cards(p: PlayerState) -> int:
    """Cards `p`'s field is worth in hand to a deck that returns its own cards to
    hand: a follower or amulet whose Fanfare draws or adds cards gives them again
    when it is returned and replayed. The player's example: Sprouting Initiate
    (Combo 3: draw a card) is the 1/1 to destroy first against Rhinoceroach
    Forest, which returns it with Baby Carbuncle and replays it. Nothing for a
    deck without such cards."""
    field = [c for c in p.field if _replay_cards(c.defn)]
    if not field or not any(_bounces(c.defn) for c in p.hand + p.deck):
        return 0
    return sum(_replay_cards(c.defn) for c in field)


def hand_count(p: PlayerState) -> int:
    """Cards in hand for the evaluation, with the cards waiting on the field (latent_cards)."""
    return min(len(p.hand) + latent_cards(p), 9)


_BURN: dict = {}


def crest_burn(defn) -> int:
    """Damage a crest deals to its holder's leader at the start of each of the
    holder's turns, measured in a sandbox (0 for a crest that doesn't hurt it)."""
    hit = _BURN.get(defn.card_id)
    if hit is None:
        from svsim.core import effects as E
        from svsim.core.actions import EndTurn
        from svsim.core.engine import apply
        from svsim.search.combo import _sandbox
        state, _ = _sandbox(0)
        E.add_to_leader_area(state, 1, defn)
        hp = state.players[1].leader_hp
        apply(state, EndTurn())
        hit = _BURN[defn.card_id] = max(hp - state.players[1].leader_hp, 0)
    return hit


def burn(p: PlayerState) -> int:
    """What the crests on `p`'s side take from its leader each of its turns."""
    if not CREST_EFFECTS:
        return 0
    return sum(crest_burn(c.defn) for c in p.leader_area if c.defn.type == CardType.CREST)


def good_crests(p: PlayerState) -> int:
    """Crests on `p`'s side that don't hurt it."""
    return sum(c.defn.type == CardType.CREST and not (CREST_EFFECTS and crest_burn(c.defn)) for c in p.leader_area)


def effective_hp(p: PlayerState) -> int:
    """Leader defense less what crests that hurt the leader will take over `BURN_TURNS` turns."""
    return max(p.leader_hp - BURN_TURNS * burn(p), 0)


def side_value(p: PlayerState, w: Weights = DEFAULT) -> float:
    hp = effective_hp(p)
    value = w.hp * hp + w.hp_sqrt * math.sqrt(hp)
    for c in p.field:
        value += follower_value(c, w) if c.defn.is_follower else w.amulet * c.defn.cost + 0.5
    value += w.crest * good_crests(p)
    value += w.hand * hand_count(p)
    value += w.ep * p.ep + w.sep * p.sep + w.max_pp * p.max_pp
    if w.dig and len(p.deck) > 5:
        value -= w.dig * len(p.deck)
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


_SCALED: dict = {}


def _scaled_board(w: Weights) -> Weights:
    hit = _SCALED.get(w)
    if hit is None:
        from dataclasses import replace
        k = w.own_board
        hit = _SCALED[w] = replace(w, atk=w.atk * k, life=w.life * k, ward=w.ward * k, bane=w.bane * k,
                                   drain=w.drain * k, barrier=w.barrier * k, ambush=w.ambush * k, aura=w.aura * k,
                                   intimidate=w.intimidate * k, own_board=1.0)
    return hit


def evaluate(state: GameState, player: int, w: Weights = DEFAULT,
             player_moves_next: bool = False) -> float:
    """Score for `player`. By default the opponent moves next (the end of
    `player`'s turn); with `player_moves_next` (the start of `player`'s turn)
    danger and pressure swap weights."""
    if hasattr(w, "score"):                       # a learned evaluation (svsim.learn.model)
        return w.score(state, player, player_moves_next)
    if state.winner is not None:
        return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
    me, opp = state.players[player], state.players[1 - player]
    mine = w if w.own_board == 1.0 else _scaled_board(w)
    score = side_value(me, mine) - side_value(opp, w)
    danger, pressure = (w.pressure, w.danger) if player_moves_next else (w.danger, w.pressure)
    if threat(state, 1 - player) >= me.leader_hp:
        score -= danger
    if threat(state, player) >= opp.leader_hp:
        score += pressure
    if w.ready or w.ready_lethal:
        from svsim.search.formula import next_turn
        potential = next_turn(state, player)
        score += w.ready * min(potential, opp.leader_hp)
        if potential >= opp.leader_hp:
            score += w.ready_lethal
    if w.setup or w.setup_lethal:
        from svsim.search.combo import next_turn_damage
        potential = next_turn_damage(state, player, w.setup_nodes, w.setup_board)
        score += w.setup * min(potential, opp.leader_hp)
        if potential >= opp.leader_hp:
            score += w.setup_lethal
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
    s.max_turns = state.max_turns
    return s
