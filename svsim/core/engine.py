"""Rules engine: match setup, legal actions, and applying actions.

The engine is a set of functions over a GameState:

    state = new_game(deck0, deck1, seed=1)
    while not state.over:
        apply(state, choose(legal_actions(state)))

apply() mutates the state in place; call state.clone() first to branch.
"""
from __future__ import annotations

from itertools import chain, combinations, product
import random
from typing import NamedTuple

from . import effects as E
from .actions import Action, Attack, EndTurn, Engage, Evolve, Fuse, Mulligan, PlayCard, UseBonusPP
from .carddef import CardDef
from .enums import DRAW, Keyword, Phase
from .script import (INVOKERS, LISTEN_IN_HAND, CardScript, Ctx, Target, TargetSpec, Trigger, prop,
                     script_for)
from .state import (DESTROYED, FIELD_LIMIT, MAX_PP, CardInstance, GameState, PlayerState,
                    leader_of, leader_uid)

OPENING_HAND = 4
EVOLVE_TURN = {True: 5, False: 4}         # own turn evolution unlocks: going first / second
SUPER_EVOLVE_TURN = {True: 7, False: 6}
BONUS_REFRESH_TURN = 6                    # second player's Bonus PP refreshes on own turn 6
MAX_FUSE_CHOICES = 32                     # cap on distinct fuse combinations offered


def new_game(deck0: list[CardDef], deck1: list[CardDef], seed: int | None = None,
             first: int | None = None, max_turns: int = 60) -> GameState:
    from svsim.cards.decks import identify
    rng = random.Random(seed)
    if first is None:
        first = rng.randrange(2)
    state = GameState(players=[PlayerState(0), PlayerState(1)], rng=rng, first=first,
                      active=first, max_turns=max_turns)
    for i, deck in enumerate((deck0, deck1)):
        p = state.players[i]
        p.deck = [state.new_instance(defn, i) for defn in deck]
        p.deck_name = identify(deck) or ""
        rng.shuffle(p.deck)
        p.hand = [p.deck.pop() for _ in range(OPENING_HAND)]
        faiths = {d.faith.card_id: d.faith for d in deck if d.faith is not None}
        for faith in faiths.values():      # one of each faith in the deck starts in the leader area
            E.add_to_leader_area(state, i, faith)
    state.players[1 - first].bonus_ready = True
    return state


# --- legal actions -----------------------------------------------------------------

def legal_actions(state: GameState) -> list[Action]:
    if state.phase == Phase.OVER:
        return []
    p = state.players[state.active]
    if state.phase == Phase.MULLIGAN:
        n = len(p.hand)
        return [Mulligan(c) for k in range(n + 1) for c in combinations(range(n), k)]
    actions: list[Action] = []
    actions += _play_actions(state, p)
    actions += _attack_actions(state, p)
    actions += _evolve_actions(state, p)
    actions += _engage_actions(state, p)
    actions += _fuse_actions(state, p)
    if p.bonus_ready and not p.bonus_active:
        actions.append(UseBonusPP())
    actions.append(EndTurn())
    return actions


class PlayForm(NamedTuple):
    paid: int               # PP paid
    script: CardScript      # whose ability resolves
    enhanced: int           # Enhance cost paid, 0 if none
    as_spell: bool          # played as a spell (a spell, or an Accelerate form)
    alt: CardDef | None     # the Accelerate / Crystallize form used, if any


def play_form(p: PlayerState, card: CardInstance) -> PlayForm | None:
    """How `card` would be played right now, or None if it can't be. Enhance is
    forced when affordable; Accelerate / Crystallize only when the normal cost
    can't be paid, using the highest payable one."""
    script = script_for(card.defn.card_id)
    if prop(card, "unplayable"):
        return None
    if card.cost <= p.pp:
        enhanced = max((cost for cost in script.enhance if cost <= p.pp), default=0)
        if enhanced and card.defn.is_follower and fanfare_suppressed(p):
            enhanced = 0
        return PlayForm(enhanced or card.cost, script, enhanced, card.defn.is_spell, None)
    alts = [a for a in (card.defn.accelerate, card.defn.crystallize) if a is not None and a.cost <= p.pp]
    if alts:
        alt = max(alts, key=lambda a: a.cost)
        return PlayForm(alt.cost, script_for(alt.card_id), 0, alt.is_spell, alt)
    return None


def fanfare_suppressed(p: PlayerState) -> bool:
    """Whether the player's followers' Fanfare and Enhance abilities don't activate."""
    return any(prop(c, "suppresses_fanfare") for c in p.leader_area + p.field)


def selectable(state: GameState, chooser: int, spec: TargetSpec, source: int | None = None) -> list[int]:
    """Uids a player may select for `spec`; `source` is the card using the ability."""
    me = state.players[chooser]
    kind = spec.kind                       # (the enemy lists only for the kinds that read them)
    if kind == Target.HAND_CARD:
        cards = [c for c in me.hand if c.uid != source]
    elif kind in (Target.ENEMY_FOLLOWER, Target.ENEMY_FOLLOWER_OR_LEADER):
        cards = E.selectable_enemies(state, chooser)
    elif kind == Target.ALLIED_FOLLOWER:
        cards = me.followers
    elif kind == Target.ANY_FOLLOWER:
        cards = me.followers + E.selectable_enemies(state, chooser)
    elif kind == Target.ENEMY_CARD:
        cards = [c for c in state.players[1 - chooser].field if not E.unselectable(c)]
    elif kind == Target.ALLIED_CARD:
        cards = list(me.field)
    elif kind == Target.ANY_CARD:
        cards = list(me.field) + [c for c in state.players[1 - chooser].field if not E.unselectable(c)]
    elif kind == Target.ALLIED_AMULET:
        cards = [c for c in me.field if c.defn.is_amulet]
    else:
        raise ValueError(kind)
    if spec.other:
        cards = [c for c in cards if c.uid != source]
    if spec.filter is not None:
        cards = [c for c in cards if spec.filter(state, chooser, c)]
    uids = [c.uid for c in cards]
    if kind == Target.ENEMY_FOLLOWER_OR_LEADER:
        uids.append(leader_uid(1 - chooser))
    return uids


def _signature(card: CardInstance) -> tuple:
    """Cards with the same signature are interchangeable for choosing actions."""
    extra = repr(sorted(card.counters.items())) if card.counters else ""
    return (card.defn.card_id, card.cost, card.atk, card.life, int(card.keywords), extra,
            len(card.grants or ()))


def _distinct(state: GameState, chooser: int, combos: list) -> list:
    """Drop combinations of hand cards that are interchangeable with an earlier one."""
    by_uid = {c.uid: _signature(c) for c in state.players[chooser].hand}
    seen, distinct = set(), []
    for combo in combos:
        key = tuple(sorted(by_uid[uid] for uid in combo))
        if key not in seen:
            seen.add(key)
            distinct.append(combo)
    return distinct


def _target_sets(state: GameState, chooser: int, specs: tuple[TargetSpec, ...],
                 required: bool, source: int | None = None) -> list[tuple[int, ...]]:
    """Ways to choose targets for each spec, concatenated in spec order. Spells need
    every target; Fanfares, Evolves and Engages pick as many as possible, so with
    no candidates they pick none. Interchangeable hand cards count once."""
    groups = []
    for spec in specs:
        candidates = selectable(state, chooser, spec, source)
        if required and len(candidates) < spec.count:
            return []
        combos = list(combinations(candidates, min(spec.count, len(candidates))))
        if spec.kind == Target.HAND_CARD:
            combos = _distinct(state, chooser, combos)
        groups.append(combos)
    return [tuple(chain.from_iterable(parts)) for parts in product(*groups)]


def _mode_sets(modes: tuple[int, int] | None, all_modes: bool) -> list[tuple[int, ...]]:
    if not modes:
        return [()]
    options, picks = modes
    if all_modes:
        return [tuple(range(options))]
    return list(combinations(range(options), picks))


def _play_actions(state: GameState, p: PlayerState) -> list[Action]:
    actions, seen = [], set()
    for card in p.hand:
        signature = _signature(card)
        if signature in seen:              # identical copies give identical actions
            continue
        seen.add(signature)
        form = play_form(p, card)
        if form is None:
            continue
        if not form.as_spell and len(p.field) >= FIELD_LIMIT:
            continue
        script = form.script
        target_sets = _target_sets(state, p.index, script.play_targets, required=form.as_spell,
                                   source=card.uid)
        mode_sets = _mode_sets(script.modes, script.all_modes(state, card, form.enhanced))
        actions += [PlayCard(card.uid, t, m) for t in target_sets for m in mode_sets]
    return actions


def _attack_actions(state: GameState, p: PlayerState) -> list[Action]:
    enemy = state.players[1 - p.index]
    attackable = [c for c in enemy.followers
                  if not c.keywords & (Keyword.AMBUSH | Keyword.INTIMIDATE)]
    wards = [c for c in attackable if c.keywords & Keyword.WARD]
    actions = []
    for f in p.followers:
        if f.attacks_made >= f.max_attacks or prop(f, "cant_attack"):
            continue
        blocked = bool(wards) and not prop(f, "ignores_ward")
        fresh = f.entered_turn == state.turn
        if not fresh or f.evolved or f.keywords & (Keyword.STORM | Keyword.RUSH):
            actions += [Attack(f.uid, t.uid) for t in (wards if blocked else attackable)]
        if not blocked and (not fresh or f.keywords & Keyword.STORM):
            actions.append(Attack(f.uid, leader_uid(enemy.index)))
    return actions


def _evolve_actions(state: GameState, p: PlayerState) -> list[Action]:
    if p.evolved_this_turn:
        return []
    going_first = p.index == state.first
    can_evolve = p.ep > 0 and p.turns_taken >= EVOLVE_TURN[going_first]
    can_super = p.sep > 0 and p.turns_taken >= SUPER_EVOLVE_TURN[going_first]
    if not (can_evolve or can_super):
        return []
    actions = []
    for f in p.followers:
        if f.evolved:
            continue
        script = script_for(f.defn.card_id)
        for super_ in (False, True):
            if not (can_super if super_ else can_evolve):
                continue
            specs, modes = script.evolve_targets, script.evolve_modes
            if super_ and script.super_evolve_targets is not None:
                specs = script.super_evolve_targets
            if super_ and script.super_evolve_modes is not None:
                modes = script.super_evolve_modes
            mode_sets = _mode_sets(modes, False)
            for targets in _target_sets(state, p.index, specs, required=False, source=f.uid):
                actions += [Evolve(f.uid, super_, targets, modes) for modes in mode_sets]
    return actions


def _engage_actions(state: GameState, p: PlayerState) -> list[Action]:
    actions = []
    for amulet in p.field:
        script = script_for(amulet.defn.card_id)
        if (script.engage is None or script.engage_cost is None or script.engage_cost > p.pp
                or amulet.engaged_turn == state.turn):
            continue
        target_sets = _target_sets(state, p.index, script.engage_targets, required=False,
                                   source=amulet.uid)
        mode_sets = _mode_sets(script.engage_modes, False)
        actions += [Engage(amulet.uid, t, m) for t in target_sets for m in mode_sets]
    return actions


def _fuse_actions(state: GameState, p: PlayerState) -> list[Action]:
    actions = []
    for card in p.hand:
        script = script_for(card.defn.card_id)
        if script.fuse_filter is None or card.fused_turn == state.turn:
            continue
        candidates = [c.uid for c in p.hand if c is not card and script.fuse_filter(c)]
        combos = []
        for k in range(1, len(candidates) + 1):
            combos += combinations(candidates, k)
        for combo in _distinct(state, p.index, combos)[:MAX_FUSE_CHOICES]:
            actions.append(Fuse(card.uid, combo))
    return actions


# --- applying actions ----------------------------------------------------------------

def apply(state: GameState, action: Action) -> None:
    if state.phase == Phase.OVER:
        raise ValueError("game is over")
    if isinstance(action, Mulligan):
        _mulligan(state, action)
    elif isinstance(action, PlayCard):
        _play(state, action)
    elif isinstance(action, Attack):
        _attack(state, action)
    elif isinstance(action, Evolve):
        _evolve(state, action)
    elif isinstance(action, Engage):
        _engage(state, action)
    elif isinstance(action, Fuse):
        _fuse(state, action)
    elif isinstance(action, UseBonusPP):
        p = state.players[state.active]
        p.pp += 1
        p.bonus_active = True
        p.bonus_ready = False
    elif isinstance(action, EndTurn):
        _end_turn(state)
    else:
        raise TypeError(action)
    if state.winner is not None:
        state.phase = Phase.OVER


def resolve_queue(state: GameState) -> None:
    """Resolve queued triggers first in, first out. Triggers queued while resolving
    go to the back. A trigger fizzles if its source is no longer where it was
    (in play, in hand, ...); Last Words, spells and "when discarded" always resolve."""
    while state.queue and state.winner is None:
        trigger = state.queue.popleft()
        if not state.in_zone(trigger.ctx.source, trigger.zone):
            continue
        getattr(trigger.script, trigger.hook)(trigger.ctx)
        E.check_deaths(state)
    if state.winner is not None:
        state.queue.clear()


def _mulligan(state: GameState, action: Mulligan) -> None:
    p = state.players[state.active]
    chosen = set(action.indices)
    returned = [c for i, c in enumerate(p.hand) if i in chosen]
    p.hand = [c for i, c in enumerate(p.hand) if i not in chosen]
    p.hand += [p.deck.pop() for _ in returned]   # set aside, draw, then shuffle back
    p.deck += returned
    state.rng.shuffle(p.deck)
    if state.active == state.first:
        state.active = 1 - state.first
    else:
        state.active = state.first
        state.phase = Phase.MAIN
        state.turn = 1
        _start_turn(state)


def _turn_hooks(state: GameState, hook: str, p: PlayerState) -> None:
    """Queue a turn hook on a player's leader area and field, then on cards in
    hand that are active there ("Activates in hand")."""
    for card in p.leader_area + p.field:
        E.enqueue(state, hook, card, p.index)
    for card in [c for c in p.hand if c.defn.card_id in LISTEN_IN_HAND]:
        E.enqueue(state, hook, card, p.index, zone="hand")


class _EndOfTurnInvoke(CardScript):
    def check(self, ctx):
        _invoke(ctx.state, ctx.me, "turn_end")


_END_OF_TURN_INVOKE = _EndOfTurnInvoke()


def _invoke(state: GameState, p: PlayerState, when: str) -> None:
    """Invoke cards from the deck whose condition holds (one copy of each card)."""
    invoked = set()
    for card in [c for c in p.deck if c.defn.card_id in INVOKERS]:
        script = script_for(card.defn.card_id)
        if (script.invoke_at == when and card.defn.card_id not in invoked
                and len(p.field) < FIELD_LIMIT and script.can_invoke(state, card)):
            invoked.add(card.defn.card_id)
            p.deck.remove(card)
            E.enter_field(state, card)
            # Resolves even if the card has left the field by then (confirmed: a
            # Sandalphon destroyed by Trap in the Woods still gives its crest).
            E.enqueue(state, "on_invoked", card, p.index, zone=None)


def _start_turn(state: GameState) -> None:
    p = state.players[state.active]
    other = state.players[1 - state.active]
    p.turns_taken += 1
    p.max_pp = min(MAX_PP, p.max_pp + 1)
    p.pp = p.max_pp
    if p.index != state.first and p.turns_taken == BONUS_REFRESH_TURN:
        p.bonus_ready = True
    p.evolved_this_turn = False
    p.attacked_leader_this_turn = False
    p.combo = 0
    for card in p.field:
        card.attacks_made = 0
    for card in p.leader_area + p.field:          # leader area first, then field; oldest first
        if card.countdown is not None:
            card.countdown -= 1
            if card.countdown <= 0:
                E.destroy(state, card, by_ability=False)
                continue
        E.enqueue(state, "on_turn_start", card, p.index)
    for card in [c for c in p.hand if c.defn.card_id in LISTEN_IN_HAND]:
        E.enqueue(state, "on_turn_start", card, p.index, zone="hand")
    _turn_hooks(state, "on_opponent_turn_start", other)
    _invoke(state, p, "turn_start")
    resolve_queue(state)
    E.draw(state, p.index)
    resolve_queue(state)


def _end_turn(state: GameState) -> None:
    p = state.players[state.active]
    other = state.players[1 - state.active]
    _turn_hooks(state, "on_turn_end", p)
    _turn_hooks(state, "on_opponent_turn_end", other)
    # End-of-turn Invokes are checked after the end-of-turn abilities resolve but
    # before what they trigger (official Q&A: Azvaldt is destroyed, Zerael is
    # invoked, then Azvaldt's Last Words resolve).
    state.queue.append(Trigger("check", Ctx(state, None, p.index), _END_OF_TURN_INVOKE, None))
    resolve_queue(state)
    if p.bonus_active and p.pp >= 1:
        p.bonus_ready = True           # unspent: the use is cancelled, not consumed
    p.bonus_active = False
    p.attacked_leader_last_turn = p.attacked_leader_this_turn
    E.expire(state, state.turn)        # effects lasting "until the end of the turn"
    for player in state.players:
        if player.damage_cap is not None and player.damage_cap_until <= state.turn:
            player.damage_cap = None
    if state.winner is not None:
        return
    state.active = 1 - state.active
    state.turn += 1
    if state.turn > state.max_turns:
        state.winner = DRAW
        return
    _start_turn(state)


def _play(state: GameState, action: PlayCard) -> None:
    """Order: the card's own ability, then cards reacting to "you played a card"
    (leader area before field), then reactions to a follower entering the field.
    Reactions are queued when the card is played, so cards that appear while it
    resolves don't react to it (confirmed: a flag summoned by L'Age d'Or isn't
    advanced by that L'Age d'Or)."""
    p = state.players[state.active]
    card = state.in_hand(p.index, action.uid)
    form = play_form(p, card)
    p.pp -= form.paid
    p.hand.remove(card)
    p.combo += 1
    p.played_base_costs.add(form.alt.cost if form.alt else card.defn.cost)
    choices = dict(targets=action.targets, modes=action.modes, enhanced=form.enhanced)
    played = dict(other=card, enhanced=form.enhanced, as_spell=form.as_spell)
    if form.as_spell:
        E.enqueue(state, "cast", card, p.index, script=form.script, zone=None, **choices)
        E.emit(state, "on_play", player=p.index, **played)
        resolve_queue(state)
        p.shadows += 1
        E.spellboost(state, p.index)   # every spell spellboosts the hand once, after it resolves
        resolve_queue(state)
        return
    if form.alt is not None:           # Crystallize: it enters the field in its amulet form
        E.transform(state, card, form.alt)
    if not (card.defn.is_follower and fanfare_suppressed(p)):
        E.enqueue(state, "fanfare", card, p.index, script=form.script, **choices)
    E.enter_field(state, card, count_rally=False, notify=False)
    E.emit(state, "on_play", player=p.index, exclude=card, **played)
    if card.defn.is_follower:
        E.notify_entered(state, card)
    resolve_queue(state)
    if card.defn.is_follower:
        p.rally += 1                   # a follower doesn't count toward its own Fanfare's Rally


def _attack(state: GameState, action: Attack) -> None:
    p = state.players[state.active]
    attacker = state.on_field(action.attacker)
    attacker.attacks_made += 1
    E.lose_keywords(attacker, Keyword.AMBUSH)
    enemy = 1 - p.index

    if leader_of(action.target) is not None:
        p.attacked_leader_this_turn = True
        E.enqueue(state, "strike", attacker, p.index, target=action.target)
        E.enqueue(state, "leader_strike", attacker, p.index, target=action.target)
        E.emit(state, "on_attack", other=attacker, target=action.target)
        resolve_queue(state)
        if state.winner is not None or state.on_field(attacker.uid) is not attacker:
            return
        dealt = E.damage(state, [action.target], attacker.atk)
        if attacker.keywords & Keyword.DRAIN and dealt:
            E.heal_leader(state, p.index, dealt)
        resolve_queue(state)
        return

    defender = state.on_field(action.target)
    # Before damage: attacker's Strike and Clash, then defender's Clash if it survived.
    hit = dict(other=defender, target=defender.uid)
    E.enqueue(state, "strike", attacker, p.index, **hit)
    E.enqueue(state, "follower_strike", attacker, p.index, **hit)
    E.enqueue(state, "clash", attacker, p.index, **hit)
    E.emit(state, "on_attack", other=attacker, target=defender.uid)
    resolve_queue(state)
    if state.on_field(defender.uid) is defender:
        E.enqueue(state, "clash", defender, enemy, other=attacker, target=attacker.uid)
        resolve_queue(state)
    if state.winner is not None:
        return
    if state.on_field(defender.uid) is not defender:
        if attacker.super_evolved and defender.fate == DESTROYED:
            E.damage(state, [leader_uid(enemy)], 1)     # knockback
        resolve_queue(state)
        return
    if state.on_field(attacker.uid) is not attacker:
        return

    # Simultaneous damage exchange, then destruction (attacker's side first).
    to_defender = E.hit_follower(state, defender, attacker.atk)
    E.hit_follower(state, attacker, defender.atk)
    if attacker.keywords & Keyword.DRAIN and to_defender:
        E.heal_leader(state, p.index, to_defender)
    for inst, bane in ((attacker, defender.keywords & Keyword.BANE),
                       (defender, attacker.keywords & Keyword.BANE)):
        if inst.life <= 0:
            E.destroy(state, inst, by_ability=False)
        elif bane:
            E.destroy(state, inst, by_ability=True)
    if attacker.super_evolved and defender.fate == DESTROYED:
        E.damage(state, [leader_uid(enemy)], 1)         # knockback, before Last Words resolve
    resolve_queue(state)


def _evolve(state: GameState, action: Evolve) -> None:
    """The card's own Evolve / Super-Evolve abilities resolve before other cards'
    reactions to the evolution."""
    p = state.players[state.active]
    follower = state.on_field(action.uid)
    if action.super_:
        p.sep -= 1
    else:
        p.ep -= 1
    p.evolved_this_turn = True
    E.evolve(state, follower, action.super_, notify=False)
    choices = dict(targets=action.targets, modes=action.modes, super_=action.super_)
    E.enqueue(state, "on_evolve", follower, p.index, **choices)
    if action.super_:
        E.enqueue(state, "on_super_evolve", follower, p.index, **choices)
    E.notify_evolved(state, follower, action.super_)
    resolve_queue(state)


def _engage(state: GameState, action: Engage) -> None:
    p = state.players[state.active]
    amulet = state.on_field(action.uid)
    script = script_for(amulet.defn.card_id)
    p.pp -= script.engage_cost
    amulet.engaged_turn = state.turn
    E.enqueue(state, "engage", amulet, p.index, targets=action.targets, modes=action.modes)
    E.emit(state, "on_engage", player=p.index, other=amulet)
    resolve_queue(state)


def _fuse(state: GameState, action: Fuse) -> None:
    """Fused cards leave the hand without leaving a shadow."""
    p = state.players[state.active]
    card = state.in_hand(p.index, action.uid)
    fodder = [c for uid in action.cards for c in p.hand if c.uid == uid]
    for c in fodder:
        p.hand.remove(c)
    card.fused_turn = state.turn
    E.counters(card).setdefault("fused", []).extend(c.defn.card_id for c in fodder)
    E.enqueue(state, "on_fuse", card, p.index, zone="hand", cards=tuple(fodder))
    resolve_queue(state)
