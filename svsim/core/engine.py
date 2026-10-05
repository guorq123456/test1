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

from . import effects as E
from .actions import Action, Attack, EndTurn, Evolve, Mulligan, PlayCard, UseBonusPP
from .carddef import CardDef
from .enums import DRAW, Keyword, Phase
from .script import CardScript, Target, TargetSpec, script_for
from .state import (DESTROYED, FIELD_LIMIT, MAX_PP, CardInstance, GameState, PlayerState,
                    leader_of, leader_uid)

OPENING_HAND = 4
EVOLVE_TURN = {True: 5, False: 4}         # own turn evolution unlocks: going first / second
SUPER_EVOLVE_TURN = {True: 7, False: 6}
BONUS_REFRESH_TURN = 6                    # second player's Bonus PP refreshes on own turn 6
NO_FIZZLE = ("last_words", "cast", "on_discard")   # resolve even though the source is gone


def new_game(deck0: list[CardDef], deck1: list[CardDef], seed: int | None = None,
             first: int | None = None, max_turns: int = 60) -> GameState:
    rng = random.Random(seed)
    if first is None:
        first = rng.randrange(2)
    state = GameState(players=[PlayerState(0), PlayerState(1)], rng=rng, first=first,
                      active=first, max_turns=max_turns)
    for i, deck in enumerate((deck0, deck1)):
        p = state.players[i]
        p.deck = [state.new_instance(defn, i) for defn in deck]
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
    if p.bonus_ready and not p.bonus_active:
        actions.append(UseBonusPP())
    actions.append(EndTurn())
    return actions


def play_form(p: PlayerState, card: CardInstance) -> tuple[int, CardScript, int, bool] | None:
    """How `card` would be played right now: (PP paid, script, Enhance cost paid,
    played as a spell), or None if it can't be paid for. Enhance is forced when
    affordable; Accelerate is used only when the normal cost can't be paid."""
    script = script_for(card.defn.card_id)
    if card.cost <= p.pp:
        enhanced = max((cost for cost in script.enhance if cost <= p.pp), default=0)
        return enhanced or card.cost, script, enhanced, card.defn.is_spell
    alt = card.defn.accelerate
    if alt is not None and alt.cost <= p.pp:
        return alt.cost, script_for(alt.card_id), 0, True
    return None


def selectable(state: GameState, chooser: int, kind: Target, exclude: int | None = None) -> list[int]:
    if kind == Target.HAND_CARD:
        return [c.uid for c in state.players[chooser].hand if c.uid != exclude]
    enemies = [c.uid for c in E.selectable_enemies(state, chooser)]
    allies = [c.uid for c in state.players[chooser].followers]
    if kind == Target.ENEMY_FOLLOWER:
        return enemies
    if kind == Target.ALLIED_FOLLOWER:
        return allies
    if kind == Target.ANY_FOLLOWER:
        return allies + enemies
    if kind == Target.ENEMY_FOLLOWER_OR_LEADER:
        return enemies + [leader_uid(1 - chooser)]
    raise ValueError(kind)


def _signature(card: CardInstance) -> tuple:
    """Cards with the same signature are interchangeable for choosing actions."""
    extra = repr(sorted(card.counters.items())) if card.counters else ""
    return card.defn.card_id, card.cost, int(card.keywords), extra


def _target_sets(state: GameState, chooser: int, specs: tuple[TargetSpec, ...],
                 required: bool, exclude: int | None = None) -> list[tuple[int, ...]]:
    """Ways to choose targets for each spec, concatenated in spec order. Spells need
    every target; Fanfares and Evolves pick as many as possible, so with no
    candidates they pick none. Interchangeable hand cards count once."""
    groups = []
    for spec in specs:
        candidates = selectable(state, chooser, spec.kind, exclude)
        if required and len(candidates) < spec.count:
            return []
        combos = list(combinations(candidates, min(spec.count, len(candidates))))
        if spec.kind == Target.HAND_CARD:
            by_uid = {c.uid: _signature(c) for c in state.players[chooser].hand}
            seen, distinct = set(), []
            for combo in combos:
                key = tuple(sorted(by_uid[uid] for uid in combo))
                if key not in seen:
                    seen.add(key)
                    distinct.append(combo)
            combos = distinct
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
        _, script, enhanced, as_spell = form
        if not as_spell and len(p.field) >= FIELD_LIMIT:
            continue
        target_sets = _target_sets(state, p.index, script.play_targets, required=as_spell,
                                   exclude=card.uid)
        mode_sets = _mode_sets(script.modes, bool(enhanced) and script.modes_all_when_enhanced)
        actions += [PlayCard(card.uid, t, m) for t in target_sets for m in mode_sets]
    return actions


def _attack_actions(state: GameState, p: PlayerState) -> list[Action]:
    enemy = state.players[1 - p.index]
    attackable = [c for c in enemy.followers
                  if not c.keywords & (Keyword.AMBUSH | Keyword.INTIMIDATE)]
    wards = [c for c in attackable if c.keywords & Keyword.WARD]
    if wards:
        attackable = wards
    actions = []
    for f in p.followers:
        if f.attacks_made >= f.max_attacks:
            continue
        fresh = f.entered_turn == state.turn
        if not fresh or f.evolved or f.keywords & (Keyword.STORM | Keyword.RUSH):
            actions += [Attack(f.uid, t.uid) for t in attackable]
        if not wards and (not fresh or f.keywords & Keyword.STORM):
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
        target_sets = _target_sets(state, p.index, script.evolve_targets, required=False)
        mode_sets = _mode_sets(script.evolve_modes, False)
        for targets in target_sets:
            for modes in mode_sets:
                if can_evolve:
                    actions.append(Evolve(f.uid, False, targets, modes))
                if can_super:
                    actions.append(Evolve(f.uid, True, targets, modes))
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
    go to the back. Abilities fizzle if their source is no longer in play, except
    Last Words, spells, and "when discarded" abilities."""
    while state.queue and state.winner is None:
        trigger = state.queue.popleft()
        ctx = trigger.ctx
        if trigger.hook not in NO_FIZZLE and state.in_play(ctx.source.uid) is None:
            continue
        getattr(trigger.script, trigger.hook)(ctx)
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


def _start_turn(state: GameState) -> None:
    p = state.players[state.active]
    p.turns_taken += 1
    p.max_pp = min(MAX_PP, p.max_pp + 1)
    p.pp = p.max_pp
    if p.index != state.first and p.turns_taken == BONUS_REFRESH_TURN:
        p.bonus_ready = True
    p.evolved_this_turn = False
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
    resolve_queue(state)
    E.draw(state, p.index)


def _end_turn(state: GameState) -> None:
    p = state.players[state.active]
    for card in p.leader_area + p.field:
        E.enqueue(state, "on_turn_end", card, p.index)
    resolve_queue(state)
    if p.bonus_active and p.pp >= 1:
        p.bonus_ready = True           # unspent: the use is cancelled, not consumed
    p.bonus_active = False
    for player in state.players:       # effects lasting "until the end of this turn" expire
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
    resolves don't react to it."""
    p = state.players[state.active]
    card = state.in_hand(p.index, action.uid)
    paid, script, enhanced, as_spell = play_form(p, card)
    p.pp -= paid
    p.hand.remove(card)
    p.combo += 1
    choices = dict(targets=action.targets, modes=action.modes, enhanced=enhanced)
    played = dict(other=card, enhanced=enhanced, as_spell=as_spell)
    if as_spell:
        E.enqueue(state, "cast", card, p.index, script=script, **choices)
        E.emit(state, "on_play", player=p.index, **played)
        resolve_queue(state)
        p.shadows += 1
        return
    E.enqueue(state, "fanfare", card, p.index, script=script, **choices)
    E.enter_field(state, card, count_rally=False, notify=False)
    E.emit(state, "on_play", player=p.index, exclude=card, **played)
    if card.defn.is_follower:
        E.emit(state, "on_ally_enter", player=p.index, exclude=card, other=card)
    resolve_queue(state)
    if card.defn.is_follower:
        p.rally += 1                   # a follower doesn't count toward its own Fanfare's Rally


def _attack(state: GameState, action: Attack) -> None:
    p = state.players[state.active]
    attacker = state.on_field(action.attacker)
    attacker.attacks_made += 1
    attacker.keywords &= ~Keyword.AMBUSH
    enemy = 1 - p.index

    if leader_of(action.target) is not None:
        dealt = E.damage(state, [action.target], attacker.atk)
        if attacker.keywords & Keyword.DRAIN and dealt:
            E.heal_leader(state, p.index, dealt)
        resolve_queue(state)
        return

    defender = state.on_field(action.target)
    # Before damage: attacker's Strike and Clash, then defender's Clash if it survived.
    E.enqueue(state, "strike", attacker, p.index, other=defender)
    E.enqueue(state, "clash", attacker, p.index, other=defender)
    resolve_queue(state)
    if state.on_field(defender.uid) is defender:
        E.enqueue(state, "clash", defender, enemy, other=attacker)
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
    p = state.players[state.active]
    follower = state.on_field(action.uid)
    if action.super_:
        p.sep -= 1
    else:
        p.ep -= 1
    p.evolved_this_turn = True
    E.evolve(state, follower, action.super_)
    choices = dict(targets=action.targets, modes=action.modes)
    E.enqueue(state, "on_evolve", follower, p.index, **choices)
    if action.super_:
        E.enqueue(state, "on_super_evolve", follower, p.index, **choices)
    resolve_queue(state)
