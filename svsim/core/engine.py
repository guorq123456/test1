"""Rules engine: match setup, legal actions, and applying actions.

The engine is a set of functions over a GameState:

    state = new_game(deck0, deck1, seed=1)
    while not state.over:
        apply(state, choose(legal_actions(state)))

apply() mutates the state in place; call state.clone() first to branch.
"""
from __future__ import annotations

from itertools import combinations
import random

from . import effects as E
from .actions import Action, Attack, EndTurn, Evolve, Mulligan, PlayCard, UseBonusPP
from .carddef import CardDef
from .enums import DRAW, Keyword, Phase
from .script import Target, TargetSpec, script_for
from .state import DESTROYED, FIELD_LIMIT, MAX_PP, GameState, PlayerState, leader_of, leader_uid

OPENING_HAND = 4
EVOLVE_TURN = {True: 5, False: 4}         # own turn evolution unlocks: going first / second
SUPER_EVOLVE_TURN = {True: 7, False: 6}
BONUS_REFRESH_TURN = 6                    # second player's Bonus PP refreshes on own turn 6


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


def selectable(state: GameState, chooser: int, kind: Target) -> list[int]:
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


def _target_sets(state: GameState, chooser: int, spec: TargetSpec | None,
                 required: bool) -> list[tuple[int, ...]]:
    """Ways to choose targets. Spells need every target; Fanfares and Evolves pick
    as many as possible, so with no candidates they pick none."""
    if spec is None:
        return [()]
    candidates = selectable(state, chooser, spec.kind)
    if required and len(candidates) < spec.count:
        return []
    return list(combinations(candidates, min(spec.count, len(candidates))))


def _play_actions(state: GameState, p: PlayerState) -> list[Action]:
    actions = []
    for card in p.hand:
        if card.cost > p.pp:
            continue
        if card.defn.goes_to_field and len(p.field) >= FIELD_LIMIT:
            continue
        script = script_for(card.defn.card_id)
        target_sets = _target_sets(state, p.index, script.play_target, required=card.defn.is_spell)
        mode_sets = [()]
        if script.modes:
            options, picks = script.modes
            mode_sets = list(combinations(range(options), picks))
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
        target_sets = _target_sets(state, p.index, script_for(f.defn.card_id).evolve_target,
                                   required=False)
        for targets in target_sets:
            if can_evolve:
                actions.append(Evolve(f.uid, False, targets))
            if can_super:
                actions.append(Evolve(f.uid, True, targets))
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
    go to the back. Abilities other than Last Words and spells fizzle if their
    source has left the field."""
    while state.queue and state.winner is None:
        trigger = state.queue.popleft()
        ctx = trigger.ctx
        if trigger.hook not in ("last_words", "cast") and state.on_field(ctx.source.uid) is None:
            continue
        getattr(script_for(ctx.source.defn.card_id), trigger.hook)(ctx)
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
    for card in list(p.field):
        card.attacks_made = 0
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
    for card in list(p.field):
        E.enqueue(state, "on_turn_end", card, p.index)
    resolve_queue(state)
    if p.bonus_active and p.pp >= 1:
        p.bonus_ready = True           # unspent: the use is cancelled, not consumed
    p.bonus_active = False
    if state.winner is not None:
        return
    state.active = 1 - state.active
    state.turn += 1
    if state.turn > state.max_turns:
        state.winner = DRAW
        return
    _start_turn(state)


def _play(state: GameState, action: PlayCard) -> None:
    p = state.players[state.active]
    card = state.in_hand(p.index, action.uid)
    script = script_for(card.defn.card_id)
    enhanced = max((cost for cost in script.enhance if cost <= p.pp), default=0)
    p.pp -= enhanced or card.cost
    p.hand.remove(card)
    p.combo += 1
    choices = dict(targets=action.targets, modes=action.modes, enhanced=enhanced)
    if card.defn.is_spell:
        E.enqueue(state, "cast", card, p.index, **choices)
        resolve_queue(state)
        p.shadows += 1
        return
    E.enqueue(state, "fanfare", card, p.index, **choices)
    E.enter_field(state, card, count_rally=False)
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
    E.enqueue(state, "on_evolve", follower, p.index, targets=action.targets)
    if action.super_:
        E.enqueue(state, "on_super_evolve", follower, p.index, targets=action.targets)
    resolve_queue(state)
