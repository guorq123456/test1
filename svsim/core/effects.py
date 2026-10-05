"""Effect primitives: the vocabulary card scripts are written in.

Each primitive applies one game action and then destroys any follower left at
0 defense, queueing Last Words. Triggers are only queued here; the engine
resolves the queue (first in, first out) after each action.
"""
from __future__ import annotations

from .carddef import CardDef
from .enums import Keyword
from .script import CardScript, Ctx, Trigger, script_for
from .state import (BANISHED, DESTROYED, FIELD_LIMIT, HAND_LIMIT, LEADER_AREA_LIMIT, MAX_PP,
                    CardInstance, GameState, leader_of, leader_uid)

UNSELECTABLE = Keyword.AMBUSH | Keyword.AURA
OVERFLOW_PP = 7


# --- triggers -----------------------------------------------------------------

def enqueue(state: GameState, hook: str, source: CardInstance, controller: int,
            script: CardScript | None = None, **choices) -> None:
    script = script or script_for(source.defn.card_id)
    if getattr(script, hook) is not None:
        state.queue.append(Trigger(hook, Ctx(state, source, controller, **choices), script))


def emit(state: GameState, hook: str, player: int | None = None,
         exclude: CardInstance | None = None, **choices) -> None:
    """Queue a listener hook on every card in play that has it, in trigger order
    (turn player first, leader area before field, oldest first). `player`
    limits it to one side."""
    for inst in state.listeners():
        if inst is exclude or (player is not None and inst.owner != player):
            continue
        enqueue(state, hook, inst, inst.owner, **choices)


# --- queries --------------------------------------------------------------------

def is_invincible(state: GameState, inst: CardInstance) -> bool:
    """Super-evolved followers take no damage and can't be destroyed by abilities
    during their controller's turn."""
    return inst.super_evolved and state.active == inst.owner


def selectable_enemies(state: GameState, chooser: int) -> list[CardInstance]:
    """Enemy followers an ability may select (Ambush and Aura can't be selected)."""
    return [c for c in state.players[1 - chooser].followers if not c.keywords & UNSELECTABLE]


def leaders_turn_order(state: GameState) -> list[int]:
    """Both leaders, turn player first: if one effect drops both to 0, the turn player loses."""
    return [leader_uid(state.active), leader_uid(1 - state.active)]


def overflow(state: GameState, player: int) -> bool:
    return state.players[player].max_pp >= OVERFLOW_PP


def random_sample(state: GameState, items: list, k: int) -> list:
    return state.rng.sample(items, min(k, len(items)))


def counters(inst: CardInstance) -> dict:
    if inst.counters is None:
        inst.counters = {}
    return inst.counters


def leader_area_card(state: GameState, player: int, defn: CardDef) -> CardInstance | None:
    for inst in state.players[player].leader_area:
        if inst.defn.card_id == defn.card_id:
            return inst
    return None


# --- damage, healing, stats -------------------------------------------------------

def hit_follower(state: GameState, inst: CardInstance, amount: int) -> int:
    """Apply damage to one follower without the death check. Returns damage dealt."""
    amount = max(0, amount)
    if is_invincible(state, inst):
        amount = 0
    if inst.keywords & Keyword.BARRIER:
        inst.keywords &= ~Keyword.BARRIER
        amount = 0
    inst.life -= amount
    return amount


def hit_leader(state: GameState, player: int, amount: int) -> int:
    p = state.players[player]
    amount = max(0, amount)
    if p.damage_cap is not None:
        amount = min(amount, p.damage_cap)
    p.leader_hp -= amount
    if p.leader_hp <= 0 and state.winner is None:
        state.winner = 1 - player
    return amount


def damage(state: GameState, targets: list, amount: int, source: CardInstance | None = None) -> int:
    """Deal `amount` damage to each target (field instances or leader uids) in order."""
    total = 0
    for target in targets:
        if state.winner is not None:
            break
        if isinstance(target, int):
            total += hit_leader(state, leader_of(target), amount)
        elif state.on_field(target.uid) is target:
            total += hit_follower(state, target, amount)
    if source is not None and total > 0 and source.keywords & Keyword.AMBUSH:
        source.keywords &= ~Keyword.AMBUSH
    check_deaths(state)
    return total


def heal_leader(state: GameState, player: int, amount: int) -> int:
    p = state.players[player]
    restored = max(0, min(amount, p.leader_max_hp - p.leader_hp))
    p.leader_hp += restored
    emit(state, "on_leader_healed", player=player)   # fires even when 0 is restored
    return restored


def heal(inst: CardInstance, amount: int) -> int:
    restored = max(0, min(amount, inst.max_life - inst.life))
    inst.life += restored
    return restored


def buff(state: GameState, inst: CardInstance, atk: int, life: int) -> None:
    """Give +X/+Y (or -X/-Y). Changes defense and max defense; not damage."""
    inst.atk = max(0, inst.atk + atk)
    inst.life += life
    inst.max_life += life
    check_deaths(state)


def evolve(state: GameState, inst: CardInstance, super_: bool = False) -> None:
    """Evolve stats and flags only. Evolve / Super-Evolve abilities fire only for
    point-based evolution, which the engine handles."""
    bonus = 3 if super_ else 2
    buff(state, inst, bonus, bonus)
    inst.evolved = True
    inst.super_evolved = super_


def set_leader_max_hp(state: GameState, player: int, value: int) -> None:
    p = state.players[player]
    p.leader_max_hp = value
    p.leader_hp = min(p.leader_hp, value)


def give_leader_damage_cap(state: GameState, player: int, cap: int, until_turn: int) -> None:
    """Leader "can't take more than `cap` damage at a time" until the end of global turn `until_turn`."""
    p = state.players[player]
    p.damage_cap = cap
    p.damage_cap_until = until_turn


# --- zones -------------------------------------------------------------------------

def check_deaths(state: GameState) -> None:
    """Destroy followers at 0 or less defense: turn player's side first, oldest first."""
    for inst in [c for c in state.field_order() if c.defn.is_follower and c.life <= 0]:
        destroy(state, inst, by_ability=False)


def _remove_from_play(state: GameState, inst: CardInstance) -> bool:
    p = state.players[inst.owner]
    for zone in (p.field, p.leader_area):
        for i, c in enumerate(zone):
            if c is inst:
                del zone[i]
                return True
    return False


def _remove_from_hand(state: GameState, inst: CardInstance) -> bool:
    hand = state.players[inst.owner].hand
    for i, c in enumerate(hand):
        if c is inst:
            del hand[i]
            return True
    return False


def destroy(state: GameState, inst: CardInstance, by_ability: bool = True) -> bool:
    if by_ability and is_invincible(state, inst):
        return False
    if not _remove_from_play(state, inst):
        return False
    inst.fate = DESTROYED
    owner = state.players[inst.owner]
    if inst.defn.goes_to_field:          # followers and amulets leave a shadow; crests don't
        owner.shadows += 1
    if inst.defn.is_follower:
        owner.destroyed.append(inst.defn.card_id)
    enqueue(state, "last_words", inst, inst.owner)
    return True


def banish(state: GameState, inst: CardInstance) -> bool:
    """Remove from play: no shadow, no Last Words."""
    if not _remove_from_play(state, inst):
        return False
    inst.fate = BANISHED
    return True


def advance_countdown(state: GameState, inst: CardInstance, n: int = 1) -> None:
    """Advance a countdown by n; the card is destroyed when it reaches 0."""
    if inst.countdown is None or state.in_play(inst.uid) is not inst:
        return
    inst.countdown -= n
    if inst.countdown <= 0:
        destroy(state, inst, by_ability=False)


def enter_field(state: GameState, inst: CardInstance, count_rally: bool = True,
                notify: bool = True) -> bool:
    p = state.players[inst.owner]
    if len(p.field) >= FIELD_LIMIT:
        return False
    inst.entered_turn = state.turn
    inst.order = state.next_order
    state.next_order += 1
    inst.max_attacks = max(inst.max_attacks, script_for(inst.defn.card_id).attacks_per_turn)
    p.field.append(inst)
    if inst.defn.is_follower:
        if count_rally:
            p.rally += 1
        if notify:
            emit(state, "on_ally_enter", player=inst.owner, exclude=inst, other=inst)
    return True


def summon(state: GameState, owner: int, defn: CardDef) -> CardInstance | None:
    """Create a card directly on the field. Does nothing if the field is full."""
    if len(state.players[owner].field) >= FIELD_LIMIT:
        return None
    inst = state.new_instance(defn, owner)
    enter_field(state, inst)
    return inst


def add_to_leader_area(state: GameState, player: int, defn: CardDef) -> CardInstance | None:
    """Gain a crest (or place a faith). Fizzles if the area is full or already has one."""
    p = state.players[player]
    if len(p.leader_area) >= LEADER_AREA_LIMIT or leader_area_card(state, player, defn):
        return None
    inst = state.new_instance(defn, player)
    inst.entered_turn = state.turn
    inst.order = state.next_order
    state.next_order += 1
    p.leader_area.append(inst)
    return inst


def draw(state: GameState, player: int, n: int = 1) -> None:
    p = state.players[player]
    for _ in range(n):
        if not p.deck:
            if state.winner is None:
                state.winner = 1 - player
            return
        card = p.deck.pop()
        if len(p.hand) >= HAND_LIMIT:
            p.shadows += 1          # overdraw: the card is destroyed
        else:
            p.hand.append(card)


def draw_matching(state: GameState, player: int, predicate) -> CardInstance | None:
    """Draw a random card from the deck that matches `predicate` (e.g. a follower
    costing 7 or more). Nothing happens if none match."""
    p = state.players[player]
    matches = [c for c in p.deck if predicate(c)]
    if not matches:
        return None
    card = state.rng.choice(matches)
    p.deck.remove(card)
    if len(p.hand) >= HAND_LIMIT:
        p.shadows += 1
        return None
    p.hand.append(card)
    return card


def add_to_hand(state: GameState, player: int, defn: CardDef) -> CardInstance | None:
    p = state.players[player]
    if len(p.hand) >= HAND_LIMIT:
        p.shadows += 1
        return None
    inst = state.new_instance(defn, player)
    p.hand.append(inst)
    return inst


def discard(state: GameState, inst: CardInstance) -> bool:
    """Discard a card from hand: it leaves a shadow and its "when discarded" ability fires."""
    if not _remove_from_hand(state, inst):
        return False
    state.players[inst.owner].shadows += 1
    enqueue(state, "on_discard", inst, inst.owner)
    return True


# --- play points -------------------------------------------------------------------

def gain_max_pp(state: GameState, player: int, n: int = 1) -> None:
    """Ramp: the new point is empty until the next turn's refill."""
    p = state.players[player]
    p.max_pp = min(MAX_PP, p.max_pp + n)


def recover_pp(state: GameState, player: int, n: int) -> None:
    p = state.players[player]
    cap = p.max_pp + (1 if p.bonus_active else 0)
    p.pp = min(cap, p.pp + n)
