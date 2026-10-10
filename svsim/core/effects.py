"""Effect primitives: the vocabulary card scripts are written in.

Each primitive applies one game action and then destroys any follower left at
0 defense, queueing Last Words. Triggers are only queued here; the engine
resolves the queue (first in, first out) after each action.
"""
from __future__ import annotations

from .carddef import CardDef
from .enums import Keyword
from .script import (LISTEN_IN_DECK, LISTEN_IN_HAND, CardScript, Ctx, Grant, Trigger, prop,
                     _EMPTY, script_for, scripts_of)
from .state import (BANISHED, DESTROYED, FIELD_LIMIT, HAND_LIMIT, LEADER_AREA_LIMIT, MAX_PP,
                    CardInstance, GameState, PlayerState, leader_of, leader_uid)

UNSELECTABLE = Keyword.AMBUSH | Keyword.AURA
OVERFLOW_PP = 7
EARTH_SIGIL = "Earth Sigil"
DEPARTED = "Departed"


# --- triggers -----------------------------------------------------------------

def enqueue(state: GameState, hook: str, source: CardInstance, controller: int,
            script: CardScript | None = None, zone: str | None = "play", **choices) -> None:
    """Queue `hook` on the card's scripts (its own and granted ones) that have it.
    `zone` is where the card must still be when the trigger resolves."""
    if script is not None:
        scripts = (script,)
    elif not source.grants:                # the common case: one script, mostly without this hook
        own = _EMPTY if source.silenced else script_for(source.defn.card_id)
        if getattr(own, hook, None) is None:
            return
        scripts = (own,)
    else:
        scripts = scripts_of(source)
    for s in scripts:
        if getattr(s, hook, None) is None:
            continue
        if hook == "last_words" and source.no_last_words and s is script_for(source.defn.card_id):
            continue                       # its own Last Words were removed; granted ones remain
        ctx = Ctx(state, source, controller, **choices)
        if hook in s.queue_checks and not s.queue_condition(hook, ctx):
            continue
        state.queue.append(Trigger(hook, ctx, s, zone))


def emit(state: GameState, hook: str, player: int | None = None,
         exclude: CardInstance | None = None, **choices) -> None:
    """Queue a listener hook on every card that has it, in trigger order: turn
    player first; leader area, field, then hand and deck (only cards whose
    script listens there); oldest first. `player` limits it to one side."""
    order = (state.active, 1 - state.active)
    for side in order:
        if player is not None and side != player:
            continue
        p = state.players[side]
        for inst in p.leader_area + p.field:
            if inst is not exclude:
                enqueue(state, hook, inst, side, **choices)
        for zone, cards, ids in (("hand", p.hand, LISTEN_IN_HAND), ("deck", p.deck, LISTEN_IN_DECK)):
            if ids:
                for inst in [c for c in cards if c.defn.card_id in ids and c is not exclude]:
                    enqueue(state, hook, inst, side, zone=zone, **choices)


# --- queries --------------------------------------------------------------------

def is_invincible(state: GameState, inst: CardInstance) -> bool:
    """Super-evolved followers take no damage and can't be destroyed by abilities
    during their controller's turn."""
    return inst.super_evolved and state.active == inst.owner


def has_trait(inst: CardInstance, trait: str) -> bool:
    return trait in inst.defn.traits or trait in ((inst.counters or {}).get("traits") or ())


def add_trait(inst: CardInstance, trait: str) -> None:
    traits = counters(inst).setdefault("traits", [])
    if trait not in traits:
        traits.append(trait)


def unselectable(inst: CardInstance) -> bool:
    """Can't be selected by enemy abilities: Ambush, Aura, Earth Sigil amulets."""
    return bool(inst.keywords & UNSELECTABLE) or (inst.defn.is_amulet and has_trait(inst, EARTH_SIGIL))


def selectable_enemies(state: GameState, chooser: int) -> list[CardInstance]:
    """Enemy followers an ability may select."""
    return [c for c in state.players[1 - chooser].followers if not unselectable(c)]


def leaders_turn_order(state: GameState) -> list[int]:
    """Both leaders, turn player first: if one effect drops both to 0, the turn player loses."""
    return [leader_uid(state.active), leader_uid(1 - state.active)]


def overflow(state: GameState, player: int) -> bool:
    return state.players[player].max_pp >= OVERFLOW_PP


def super_evolution_unlocked(state: GameState, player: int) -> bool:
    p = state.players[player]
    return p.turns_taken >= (7 if player == state.first else 6)


def random_sample(state: GameState, items: list, k: int) -> list:
    return state.rng.sample(list(items), min(k, len(items)))


def counters(inst: CardInstance) -> dict:
    if inst.counters is None:
        inst.counters = {}
    return inst.counters


def once_per_turn(ctx: Ctx, key: str = "once") -> bool:
    """True the first time it's asked on a turn (per card and key), False after."""
    c = counters(ctx.source)
    if c.get(key) == ctx.state.turn:
        return False
    c[key] = ctx.state.turn
    return True


def leader_area_card(state: GameState, player: int, defn: CardDef) -> CardInstance | None:
    for inst in state.players[player].leader_area:
        if inst.defn.card_id == defn.card_id:
            return inst
    return None


def no_duplicates_in_deck(p: PlayerState) -> bool:
    ids = [c.defn.card_id for c in p.deck]
    return len(ids) == len(set(ids))


# --- damage, healing, stats -------------------------------------------------------

def hit_follower(state: GameState, inst: CardInstance, amount: int) -> int:
    """Apply damage to one follower without the death check. Returns damage dealt."""
    amount = max(0, amount)
    cap = prop(inst, "damage_cap")
    if cap is not None:
        amount = min(amount, cap)
    if is_invincible(state, inst):
        amount = 0
    if inst.keywords & Keyword.BARRIER:     # any damage event uses it up, even 0 (official Q&A:
        lose_keywords(inst, Keyword.BARRIER)  # a super-evolved follower's Barrier still goes)
        amount = 0
    inst.life -= amount
    enqueue(state, "on_damaged", inst, inst.owner, amount=amount)
    return amount


def hit_leader(state: GameState, player: int, amount: int) -> int:
    p = state.players[player]
    amount = max(0, amount)
    if amount > 0:
        amount += p.extra_damage           # "Takes N more damage"
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
        lose_keywords(source, Keyword.AMBUSH)
    check_deaths(state)
    return total


def split_damage(state: GameState, player: int, amount: int, source: CardInstance | None = None,
                 followers_only: bool = True) -> None:
    """Deal `amount` damage split between `player`'s followers, oldest first, each
    taking up to its defense. Leftover goes to the leader, or to the last follower
    if only followers are affected."""
    followers = list(state.players[player].followers)
    for i, f in enumerate(followers):
        if amount <= 0:
            break
        last = i == len(followers) - 1
        share = amount if (last and followers_only) else min(amount, max(f.life, 0))
        hit_follower(state, f, share)
        amount -= share
    if amount > 0 and not followers_only:
        hit_leader(state, player, amount)
    if source is not None and source.keywords & Keyword.AMBUSH:
        lose_keywords(source, Keyword.AMBUSH)
    check_deaths(state)


def heal_leader(state: GameState, player: int, amount: int) -> int:
    p = state.players[player]
    restored = max(0, min(amount, p.leader_max_hp - p.leader_hp))
    p.leader_hp += restored
    emit(state, "on_leader_healed", player=player, amount=restored)   # fires even when 0 is restored
    return restored


def heal(inst: CardInstance, amount: int) -> int:
    restored = max(0, min(amount, inst.max_life - inst.life))
    inst.life += restored
    return restored


def buff(state: GameState, inst: CardInstance, atk: int, life: int,
         until_turn: int | None = None) -> None:
    """Give +X/+Y (or -X/-Y). Changes defense and max defense; not damage.
    With `until_turn`, it's undone at the end of that global turn."""
    before = inst.atk
    inst.atk = max(0, inst.atk + atk)
    inst.life += life
    inst.max_life += life
    if until_turn is not None:              # undo only the attack actually lost (it floors at 0)
        inst.grants = (inst.grants or []) + [Grant(until_turn=until_turn, atk=inst.atk - before,
                                                   life=life)]
    if (atk > 0 or life > 0) and state.on_field(inst.uid) is inst:
        enqueue(state, "on_buffed", inst, inst.owner)
    check_deaths(state)


PERMANENT_KEYWORDS = "kw"   # counters key: keywords given with no time limit


def give_keywords(inst: CardInstance, keywords: Keyword, until_turn: int | None = None) -> None:
    inst.keywords |= keywords
    if until_turn is not None:
        inst.grants = (inst.grants or []) + [Grant(until_turn=until_turn, keywords=keywords)]
    else:                           # remembered so an expiring copy of the keyword doesn't take it
        c = counters(inst)
        c[PERMANENT_KEYWORDS] = c.get(PERMANENT_KEYWORDS, 0) | int(keywords)


def lose_keywords(inst: CardInstance, keywords: Keyword) -> None:
    """The card loses keywords (removed, or used up like Barrier and Ambush)."""
    inst.keywords &= ~keywords
    if inst.counters and inst.counters.get(PERMANENT_KEYWORDS):
        inst.counters[PERMANENT_KEYWORDS] &= ~int(keywords)


remove_keywords = lose_keywords


def silence(inst: CardInstance) -> None:
    """"Remove all abilities": keywords, its own abilities (Last Words included)
    and abilities given to it so far. Stat changes stay; it can gain abilities again."""
    inst.silenced = True
    inst.keywords = Keyword.NONE
    if inst.counters:
        inst.counters.pop(PERMANENT_KEYWORDS, None)
    if inst.grants:
        inst.grants = [Grant(until_turn=g.until_turn, atk=g.atk, life=g.life)
                       for g in inst.grants if g.atk or g.life] or None
    inst.max_attacks = 1


def remove_last_words(inst: CardInstance) -> None:
    """"Remove Last Words from it": its own Last Words; ones given later still work."""
    inst.no_last_words = True


def has_last_words(inst: CardInstance) -> bool:
    base = script_for(inst.defn.card_id)
    return any(s.last_words is not None and not (s is base and inst.no_last_words)
               for s in scripts_of(inst))


def grant(inst: CardInstance, script: CardScript, until_turn: int | None = None) -> None:
    """Give a card an ability: a script whose hooks and properties count as its own."""
    inst.grants = (inst.grants or []) + [Grant(script=script, until_turn=until_turn)]
    inst.max_attacks = max(inst.max_attacks, script.attacks_per_turn)


def expire(state: GameState, turn: int) -> None:
    """Undo grants and cost changes lasting until the end of `turn`."""
    for p in state.players:
        for inst in p.field + p.hand + p.leader_area + p.deck:
            if inst.grants and any(g.until_turn is not None and g.until_turn <= turn for g in inst.grants):
                kept = [g for g in inst.grants if g.until_turn is None or g.until_turn > turn]
                still = Keyword((inst.counters or {}).get(PERMANENT_KEYWORDS, 0))
                if not inst.silenced:
                    still |= inst.defn.keywords
                for g in kept:
                    still |= g.keywords
                for g in inst.grants:
                    if g.until_turn is not None and g.until_turn <= turn:
                        inst.atk = max(0, inst.atk - g.atk)
                        inst.max_life -= g.life
                        inst.life = min(inst.life, inst.max_life)
                        inst.keywords &= ~(g.keywords & ~still)
                inst.grants = kept or None
                inst.max_attacks = prop(inst, "attacks_per_turn")
            if inst.cost_mods and any(u is not None and u <= turn for _, _, u in inst.cost_mods):
                inst.cost_mods = [m for m in inst.cost_mods if m[2] is None or m[2] > turn] or None
                recompute_cost(inst)
    check_deaths(state)


def evolve(state: GameState, inst: CardInstance, super_: bool = False, notify: bool = True) -> None:
    """Evolve stats and flags. Evolve / Super-Evolve abilities fire only for
    point-based evolution, which the engine handles; "when this follower evolves"
    and "whenever an allied follower evolves" fire for any evolution. An evolved
    follower can't evolve again."""
    if inst.evolved:
        return
    bonus = 3 if super_ else 2
    buff(state, inst, bonus, bonus)
    inst.evolved = True
    inst.super_evolved = super_
    p = state.players[inst.owner]
    p.evolutions += 1
    for card in p.hand:                       # Skybound Art gauges count evolutions in hand
        if prop(card, "skybound"):
            counters(card)["skybound"] = counters(card).get("skybound", 0) + 1
    if notify:
        notify_evolved(state, inst, super_)


def notify_evolved(state: GameState, inst: CardInstance, super_: bool) -> None:
    enqueue(state, "on_evolved", inst, inst.owner, super_=super_)
    emit(state, "on_ally_evolve", player=inst.owner, exclude=inst, other=inst, super_=super_)


def set_leader_max_hp(state: GameState, player: int, value: int) -> None:
    p = state.players[player]
    p.leader_max_hp = value
    p.leader_hp = min(p.leader_hp, value)
    if p.leader_hp <= 0 and state.winner is None:
        state.winner = 1 - player


def give_leader_damage_cap(state: GameState, player: int, cap: int, until_turn: int) -> None:
    """Leader "can't take more than `cap` damage at a time" until the end of global turn `until_turn`."""
    p = state.players[player]
    p.damage_cap = cap
    p.damage_cap_until = until_turn


# --- costs ---------------------------------------------------------------------------

def recompute_cost(inst: CardInstance) -> None:
    """Apply cost changes in the order received: +/-N, set to N, halve (rounding
    up; 1 stays 1). Reductions can run below 0; the cost shown is never below 0."""
    running = inst.defn.cost
    for op, value, _ in inst.cost_mods or ():
        if op == "add":
            running += value
        elif op == "set":
            running = value
        elif op == "half":
            running = (max(running, 0) + 1) // 2
    inst.cost = max(0, running)


def add_cost(inst: CardInstance, n: int, until_turn: int | None = None) -> None:
    """Increase (n > 0) or reduce (n < 0) a card's cost."""
    inst.cost_mods = (inst.cost_mods or []) + [("add", n, until_turn)]
    recompute_cost(inst)


def set_cost(inst: CardInstance, n: int, until_turn: int | None = None) -> None:
    inst.cost_mods = (inst.cost_mods or []) + [("set", n, until_turn)]
    recompute_cost(inst)


def halve_cost(inst: CardInstance, until_turn: int | None = None) -> None:
    inst.cost_mods = (inst.cost_mods or []) + [("half", 0, until_turn)]
    recompute_cost(inst)


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


def _remove_from(cards: list, inst: CardInstance) -> bool:
    for i, c in enumerate(cards):
        if c is inst:
            del cards[i]
            return True
    return False


def destroy(state: GameState, inst: CardInstance, by_ability: bool = True) -> bool:
    if state.in_play(inst.uid) is not inst:
        return False
    if by_ability and (is_invincible(state, inst) or prop(inst, "indestructible")
                       or (inst.defn.is_amulet and has_trait(inst, EARTH_SIGIL))):
        return False
    if prop(inst, "banish_on_leave"):
        return banish(state, inst)
    if not _remove_from_play(state, inst):
        return False
    inst.fate = DESTROYED
    owner = state.players[inst.owner]
    if inst.defn.goes_to_field:          # followers and amulets leave a shadow; crests don't
        owner.shadows += 1
    if inst.defn.is_follower:
        owner.destroyed.append(inst.defn)
    elif inst.defn.is_amulet:
        owner.destroyed_amulets.append(inst.defn)
    enqueue(state, "last_words", inst, inst.owner, zone=None)
    emit(state, "on_card_destroyed", other=inst)
    _left_field(state, inst)
    return True


def _left_field(state: GameState, inst: CardInstance) -> None:
    """A follower left the field (not by transforming): tell its owner's cards."""
    if inst.defn.is_follower:
        emit(state, "on_ally_leave", player=inst.owner, other=inst)


def banish(state: GameState, inst: CardInstance) -> bool:
    """Remove from play (or from hand or deck): no shadow, no Last Words."""
    p = state.players[inst.owner]
    if _remove_from_play(state, inst):
        inst.fate = BANISHED
        _left_field(state, inst)
        return True
    if not (_remove_from(p.hand, inst) or _remove_from(p.deck, inst)):
        return False
    inst.fate = BANISHED
    return True


def advance_countdown(state: GameState, inst: CardInstance, n: int = 1) -> None:
    """Advance a countdown by n (negative n delays it); destroyed when it reaches 0."""
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
    inst.max_attacks = max(inst.max_attacks, prop(inst, "attacks_per_turn"))
    if inst.defn.is_amulet and has_trait(inst, EARTH_SIGIL):
        sigils = counters(inst).get("sigils") or 1      # merge the earth sigils already on the field
        for other in [c for c in p.field if c.defn.is_amulet and has_trait(c, EARTH_SIGIL)]:
            sigils += counters(other).get("sigils", 0)
            banish(state, other)
        counters(inst)["sigils"] = sigils
    p.field.append(inst)
    if inst.defn.is_follower:
        p.entered[inst.defn.card_id] = p.entered.get(inst.defn.card_id, 0) + 1
        if count_rally:
            p.rally += 1
        if notify:
            notify_entered(state, inst)
    return True


def notify_entered(state: GameState, inst: CardInstance) -> None:
    """Queue reactions to a follower entering the field: its own "when this
    follower enters the field", then other cards' "whenever ... enters"."""
    enqueue(state, "on_enter", inst, inst.owner)
    emit(state, "on_ally_enter", player=inst.owner, exclude=inst, other=inst)
    emit(state, "on_enemy_enter", player=1 - inst.owner, other=inst)


def summon(state: GameState, owner: int, defn: CardDef) -> CardInstance | None:
    """Create a card directly on the field. Does nothing if the field is full."""
    if len(state.players[owner].field) >= FIELD_LIMIT:
        return None
    inst = state.new_instance(defn, owner)
    enter_field(state, inst)
    return inst


def exact_copy(state: GameState, inst: CardInstance, owner: int | None = None) -> CardInstance:
    """A new card identical to `inst` (damage, buffs, evolution, granted abilities),
    except for whether it attacked or engaged this turn."""
    clone = inst.copy()
    clone.uid = state.next_uid
    state.next_uid += 1
    clone.owner = inst.owner if owner is None else owner
    clone.attacks_made = 0
    clone.engaged_turn = -1
    clone.fate = 0
    return clone


def summon_copy(state: GameState, owner: int, inst: CardInstance) -> CardInstance | None:
    """Summon an exact copy of a card."""
    if len(state.players[owner].field) >= FIELD_LIMIT:
        return None
    clone = exact_copy(state, inst, owner)
    enter_field(state, clone)
    return clone


def summon_from_deck(state: GameState, player: int, predicate, k: int = 1,
                     distinct_names: bool = False) -> list[CardInstance]:
    """Summon k random cards from the deck that match `predicate`."""
    p = state.players[player]
    summoned = []
    for _ in range(k):
        names = {c.defn.name for c in summoned}
        matches = [c for c in p.deck if predicate(c) and not (distinct_names and c.defn.name in names)]
        if not matches or len(p.field) >= FIELD_LIMIT:
            break
        card = state.rng.choice(matches)
        _remove_from(p.deck, card)
        enter_field(state, card)
        summoned.append(card)
    return summoned


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


def transform(state: GameState, inst: CardInstance, defn: CardDef) -> CardInstance:
    """Turn a card into another, wherever it is. It keeps its place (and uid) but
    nothing else; on the field it can't attack until next turn. Not leaving the
    field: no Last Words, no Fanfare."""
    inst.defn = defn
    inst.cost = defn.cost
    inst.atk, inst.life, inst.max_life = defn.atk, defn.life, defn.life
    inst.keywords = defn.keywords
    inst.countdown = defn.countdown
    inst.evolved = inst.super_evolved = False
    inst.silenced = inst.no_last_words = False
    inst.counters = inst.grants = inst.cost_mods = None
    inst.attacks_made = 0
    inst.max_attacks = script_for(defn.card_id).attacks_per_turn
    inst.engaged_turn = -1
    if state.on_field(inst.uid) is inst:
        inst.entered_turn = state.turn
    return inst


def return_to_hand(state: GameState, inst: CardInstance) -> CardInstance | None:
    """Return a card on the field to its owner's hand, as a fresh copy (damage,
    buffs and cost changes are gone). A full hand destroys it (a shadow)."""
    if state.in_play(inst.uid) is not inst:
        return None
    if prop(inst, "banish_on_leave"):
        banish(state, inst)
        return None
    if not _remove_from_play(state, inst):
        return None
    _left_field(state, inst)
    p = state.players[inst.owner]
    if len(p.hand) >= HAND_LIMIT:
        p.shadows += 1
        return None
    fresh = state.new_instance(inst.defn, inst.owner)
    p.hand.append(fresh)
    return fresh


def return_to_deck(state: GameState, inst: CardInstance) -> None:
    """Put a card from hand into its owner's deck at a random place. It keeps its
    cost changes and counters (spellboosts, Skybound gauge)."""
    p = state.players[inst.owner]
    if _remove_from(p.hand, inst):
        p.deck.insert(state.rng.randrange(len(p.deck) + 1), inst)


def put_into_deck(state: GameState, player: int, defn: CardDef) -> CardInstance:
    p = state.players[player]
    inst = state.new_instance(defn, player)
    p.deck.insert(state.rng.randrange(len(p.deck) + 1), inst)
    return inst


def _to_hand(state: GameState, player: int, card: CardInstance) -> CardInstance | None:
    p = state.players[player]
    if len(p.hand) >= HAND_LIMIT:
        p.shadows += 1               # overdraw: the card is destroyed
        return None
    p.hand.append(card)
    enqueue(state, "on_drawn", card, player, zone="hand")
    emit(state, "on_draw", player=player, other=card)
    return card


def draw(state: GameState, player: int, n: int = 1) -> list[CardInstance]:
    p = state.players[player]
    drawn = []
    for _ in range(n):
        if not p.deck:
            if state.winner is None:
                state.winner = 1 - player
            return drawn
        card = _to_hand(state, player, p.deck.pop())
        if card:
            drawn.append(card)
    return drawn


def draw_matching(state: GameState, player: int, predicate) -> CardInstance | None:
    """Draw a random card from the deck that matches `predicate` (e.g. a follower
    costing 7 or more). Nothing happens if none match."""
    p = state.players[player]
    matches = [c for c in p.deck if predicate(c)]
    if not matches:
        return None
    card = state.rng.choice(matches)
    _remove_from(p.deck, card)
    return _to_hand(state, player, card)


def add_to_hand(state: GameState, player: int, defn: CardDef) -> CardInstance | None:
    p = state.players[player]
    if len(p.hand) >= HAND_LIMIT:
        p.shadows += 1
        return None
    inst = state.new_instance(defn, player)
    p.hand.append(inst)
    return inst


def add_copy_to_hand(state: GameState, player: int, inst: CardInstance) -> CardInstance | None:
    """Add an exact copy of a card (anywhere) to a player's hand."""
    p = state.players[player]
    if len(p.hand) >= HAND_LIMIT:
        p.shadows += 1
        return None
    clone = exact_copy(state, inst, player)
    p.hand.append(clone)
    return clone


def discard(state: GameState, inst: CardInstance) -> bool:
    """Discard a card from hand: it leaves a shadow and its "when discarded" ability fires."""
    if not _remove_from(state.players[inst.owner].hand, inst):
        return False
    state.players[inst.owner].shadows += 1
    enqueue(state, "on_discard", inst, inst.owner, zone=None)
    return True


# --- class mechanics -----------------------------------------------------------------

def spellboost(state: GameState, player: int, times: int = 1, cards: list | None = None) -> None:
    """Spellboost the cards in a player's hand (or just `cards`)."""
    for _ in range(times):
        for card in list(state.players[player].hand if cards is None else cards):
            counters(card)["spellboost"] = counters(card).get("spellboost", 0) + 1
            enqueue(state, "on_spellboost", card, player, zone="hand")


def skybound_gauge(state: GameState, card: CardInstance) -> int:
    """Skybound Art gauge: the owner's turn count plus allied evolutions while the
    card was in hand (plus any direct increases)."""
    return state.players[card.owner].turns_taken + counters(card).get("skybound", 0)


def skybound_art(ctx: Ctx) -> bool:
    return skybound_gauge(ctx.state, ctx.source) >= 10


def super_skybound_art(ctx: Ctx) -> bool:
    return skybound_gauge(ctx.state, ctx.source) >= 15


def earth_sigil_amulet(state: GameState, player: int) -> CardInstance | None:
    for c in state.players[player].field:
        if c.defn.is_amulet and has_trait(c, EARTH_SIGIL):
            return c
    return None


def earth_sigils(state: GameState, player: int) -> int:
    amulet = earth_sigil_amulet(state, player)
    return counters(amulet).get("sigils", 0) if amulet else 0


def gain_earth_sigils(state: GameState, player: int, n: int, sediment: CardDef) -> None:
    """Add n earth sigils to the allied Earth Sigil amulet, or summon a Magic
    Sediment (`sediment`) holding n if there isn't one."""
    amulet = earth_sigil_amulet(state, player)
    if amulet is not None:
        counters(amulet)["sigils"] = counters(amulet).get("sigils", 0) + n
        return
    if len(state.players[player].field) < FIELD_LIMIT:
        inst = state.new_instance(sediment, player)
        counters(inst)["sigils"] = n
        enter_field(state, inst)


def earth_rite(state: GameState, player: int, n: int) -> bool:
    """Earth Rite (n): spend n earth sigils if there are enough. Returns whether it happened."""
    amulet = earth_sigil_amulet(state, player)
    if amulet is None or counters(amulet).get("sigils", 0) < n:
        return False
    counters(amulet)["sigils"] -= n
    if counters(amulet)["sigils"] <= 0:
        destroy(state, amulet, by_ability=False)
    emit(state, "on_earth_rite", player=player, amount=n)
    return True


def necromancy(state: GameState, player: int, n: int) -> bool:
    """Necromancy (n): spend n shadows if there are enough."""
    p = state.players[player]
    if p.shadows < n:
        return False
    p.shadows -= n
    return True


def reanimate(state: GameState, player: int, n: int) -> CardInstance | None:
    """Reanimate (n): summon a copy of the allied follower with the highest base
    cost (n or less) destroyed this match, weighted by how often each was
    destroyed. It gets the Departed trait."""
    p = state.players[player]
    eligible = [d for d in p.destroyed if d.cost <= n]
    if not eligible or len(p.field) >= FIELD_LIMIT:
        return None
    top = max(d.cost for d in eligible)
    defn = state.rng.choice([d for d in eligible if d.cost == top])
    inst = state.new_instance(defn, player)
    add_trait(inst, DEPARTED)
    enter_field(state, inst)
    return inst


def faith_value(state: GameState, player: int, faith: CardDef) -> int:
    inst = leader_area_card(state, player, faith)
    return counters(inst).get("value", 0) if inst else 0


def change_faith(state: GameState, player: int, faith: CardDef, n: int) -> None:
    inst = leader_area_card(state, player, faith)
    if inst is not None:
        counters(inst)["value"] = counters(inst).get("value", 0) + n


def spend_faith(state: GameState, player: int, faith: CardDef, n: int) -> bool:
    """"Reduce your faith's value by n to ...": only if it has at least n."""
    if faith_value(state, player, faith) < n:
        return False
    change_faith(state, player, faith, -n)
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


def recover_ep(state: GameState, player: int, n: int = 1) -> None:
    p = state.players[player]
    p.ep = min(2, p.ep + n)


def recover_sep(state: GameState, player: int, n: int = 1) -> None:
    p = state.players[player]
    p.sep = min(2, p.sep + n)
