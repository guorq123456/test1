"""Effect primitives: the vocabulary card scripts are written in.

Each primitive applies one game action and then destroys any follower left at
0 defense, queueing Last Words. Triggers are only queued here; the engine
resolves the queue (first in, first out) after each action.
"""
from __future__ import annotations

from .carddef import CardDef
from .enums import Keyword
from .script import Ctx, Trigger, script_for
from .state import (BANISHED, DESTROYED, FIELD_LIMIT, HAND_LIMIT, MAX_PP, CardInstance,
                    GameState, leader_of, leader_uid)

UNSELECTABLE = Keyword.AMBUSH | Keyword.AURA


# --- triggers -----------------------------------------------------------------

def enqueue(state: GameState, hook: str, source: CardInstance, controller: int, **choices) -> None:
    if getattr(script_for(source.defn.card_id), hook) is not None:
        state.queue.append(Trigger(hook, Ctx(state, source, controller, **choices)))


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


def random_sample(state: GameState, items: list, k: int) -> list:
    return state.rng.sample(items, min(k, len(items)))


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
    amount = max(0, amount)
    p = state.players[player]
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


# --- zones -------------------------------------------------------------------------

def check_deaths(state: GameState) -> None:
    """Destroy followers at 0 or less defense: turn player's side first, oldest first."""
    for inst in [c for c in state.field_order() if c.defn.is_follower and c.life <= 0]:
        destroy(state, inst, by_ability=False)


def _leave_field(state: GameState, inst: CardInstance) -> bool:
    field = state.players[inst.owner].field
    for i, c in enumerate(field):
        if c is inst:
            del field[i]
            return True
    return False


def destroy(state: GameState, inst: CardInstance, by_ability: bool = True) -> bool:
    if by_ability and is_invincible(state, inst):
        return False
    if not _leave_field(state, inst):
        return False
    inst.fate = DESTROYED
    owner = state.players[inst.owner]
    owner.shadows += 1
    if inst.defn.is_follower:
        owner.destroyed.append(inst.defn.card_id)
    enqueue(state, "last_words", inst, inst.owner)
    return True


def banish(state: GameState, inst: CardInstance) -> bool:
    """Remove from the field: no shadow, no Last Words."""
    if not _leave_field(state, inst):
        return False
    inst.fate = BANISHED
    return True


def enter_field(state: GameState, inst: CardInstance, count_rally: bool = True) -> bool:
    p = state.players[inst.owner]
    if len(p.field) >= FIELD_LIMIT:
        return False
    inst.entered_turn = state.turn
    inst.order = state.next_order
    state.next_order += 1
    p.field.append(inst)
    if inst.defn.is_follower:
        if count_rally:
            p.rally += 1
        for other in list(p.field):
            if other is not inst:
                enqueue(state, "on_ally_enter", other, other.owner, other=inst)
    return True


def summon(state: GameState, owner: int, defn: CardDef) -> CardInstance | None:
    """Create a card directly on the field. Does nothing if the field is full."""
    if len(state.players[owner].field) >= FIELD_LIMIT:
        return None
    inst = state.new_instance(defn, owner)
    enter_field(state, inst)
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


def add_to_hand(state: GameState, player: int, defn: CardDef) -> CardInstance | None:
    p = state.players[player]
    if len(p.hand) >= HAND_LIMIT:
        p.shadows += 1
        return None
    inst = state.new_instance(defn, player)
    p.hand.append(inst)
    return inst


# --- play points -------------------------------------------------------------------

def gain_max_pp(state: GameState, player: int, n: int = 1) -> None:
    """Ramp: the new point is empty until the next turn's refill."""
    p = state.players[player]
    p.max_pp = min(MAX_PP, p.max_pp + n)


def recover_pp(state: GameState, player: int, n: int) -> None:
    p = state.players[player]
    cap = p.max_pp + (1 if p.bonus_active else 0)
    p.pp = min(cap, p.pp + n)
