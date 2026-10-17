"""How cards plug abilities into the engine.

A CardScript describes one card's behaviour: which choices it needs when
played, evolved or engaged, which hooks fire when, and a few static
properties. Scripts are stateless singletons registered by card_id; anything a
card must remember goes in CardInstance.counters.

    @register(1234)
    class Archer(CardScript):
        play_targets = (TargetSpec(Target.ENEMY_FOLLOWER),)

        def fanfare(self, ctx):
            effects.damage(ctx.state, ctx.chosen(), 1, ctx.source)

Effects can also give a card extra abilities (a Grant), optionally until the
end of a given turn; the engine treats a granted script's hooks and properties
like the card's own.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, Callable

from .enums import Keyword

if TYPE_CHECKING:
    from .state import CardInstance, GameState, PlayerState


class Target(IntEnum):
    ENEMY_FOLLOWER = 1
    ALLIED_FOLLOWER = 2
    ANY_FOLLOWER = 3
    ENEMY_FOLLOWER_OR_LEADER = 4
    HAND_CARD = 5            # a card in the controller's hand (not the one being played)
    ENEMY_CARD = 6           # an enemy follower or amulet on the field
    ALLIED_CARD = 7          # an allied follower or amulet on the field
    ANY_CARD = 8             # any card on the field
    ALLIED_AMULET = 9


@dataclass(frozen=True, slots=True)
class TargetSpec:
    kind: Target
    count: int = 1
    filter: Callable | None = None   # filter(state, chooser, card) -> bool, e.g. "costs 5 or less"
    other: bool = False              # "another": exclude the card using the ability


@dataclass(slots=True)
class Ctx:
    """Everything a hook needs: the state, the card, and the choices made for it."""
    state: GameState
    source: CardInstance
    controller: int
    targets: tuple[int, ...] = ()
    modes: tuple[int, ...] = ()
    enhanced: int = 0                    # Enhance cost paid, 0 if not enhanced
    other: CardInstance | None = None    # the other card in Strike / Clash / listener hooks
    as_spell: bool = False               # on_play: the played card was played as a spell
    super_: bool = False                 # evolve hooks: it was a super-evolution
    cards: tuple = ()                    # cards involved, e.g. the ones fused
    amount: int = 0                      # damage taken, defense restored, ...
    target: int = 0                      # on_attack: what was attacked (uid or leader uid)

    @property
    def me(self) -> PlayerState:
        return self.state.players[self.controller]

    @property
    def opponent(self) -> PlayerState:
        return self.state.players[1 - self.controller]

    def chosen(self) -> list:
        """Selected targets still in play: field instances, or leader uids."""
        result = []
        for uid in self.targets:
            if uid < 0:
                result.append(uid)
            else:
                inst = self.state.on_field(uid)
                if inst is not None:
                    result.append(inst)
        return result

    def chosen_hand(self) -> list:
        """Selected cards still in the controller's hand."""
        return [c for uid in self.targets for c in self.me.hand if c.uid == uid]


class CardScript:
    # --- choices, folded into the action that uses them ---
    play_targets: tuple[TargetSpec, ...] = ()
    evolve_targets: tuple[TargetSpec, ...] = ()
    super_evolve_targets: tuple[TargetSpec, ...] | None = None   # None = same as evolve_targets
    engage_targets: tuple[TargetSpec, ...] = ()
    enhance: tuple[int, ...] = ()        # Enhance costs; the highest affordable one is paid
    modes: tuple[int, int] | None = None  # (number of options, how many to pick)
    evolve_modes: tuple[int, int] | None = None   # for "Evolve: replicate this card's Fanfare"
    super_evolve_modes: tuple[int, int] | None = None   # None = same as evolve_modes
    engage_modes: tuple[int, int] | None = None
    modes_all_when_enhanced: bool = False          # "Enhance (N): Activate all of them instead"

    # --- static properties ---
    attacks_per_turn: int = 1
    engage_cost: int | None = None       # Engage (N); None = no Engage ability
    fuse_filter: Callable | None = None  # fuse_filter(card) -> bool: what can be fused to it
    skybound: bool = False               # has a Skybound Art: count evolutions while in hand
    listen_in_hand: bool = False         # "Activates in hand": listener hooks fire from hand
    listen_in_deck: bool = False         # "Activates in deck"
    invoke_at: str | None = None         # "turn_start" / "turn_end": when can_invoke is checked
    unplayable: bool = False             # "Can't be played"
    indestructible: bool = False         # "Can't be destroyed by abilities"
    damage_cap: int | None = None        # "Can't take more than N damage at a time"
    cant_attack: bool = False            # "Can't attack followers or leaders"
    banish_on_leave: bool = False        # "When this card leaves the field, banish it"
    ignores_ward: bool = False           # "Ignores Ward": can attack past enemy Ward
    suppresses_fanfare: bool = False     # in play: allied followers' Fanfare and Enhance don't activate
    queue_checks: tuple[str, ...] = ()   # hooks whose condition is checked when they trigger

    def queue_condition(self, hook: str, ctx: Ctx) -> bool:
        """For hooks in queue_checks: whether the ability triggers at all. Checked
        when the trigger is queued ("At the end of your turn, if this follower is
        evolved"), not when it resolves."""
        return True

    def all_modes(self, state, card, enhanced: int) -> bool:
        """Whether every mode activates ("... Activate all of them instead")."""
        return self.modes_all_when_enhanced and bool(enhanced)

    def can_invoke(self, state, card) -> bool:
        return False

    # --- hooks on the card itself (None, or a method taking a Ctx) ---
    fanfare = None           # follower / amulet played from hand
    cast = None              # spell played (or a card played in its Accelerate form)
    last_words = None        # destroyed (not banished)
    on_evolve = None         # "Evolve:" evolved or super-evolved with points
    on_super_evolve = None   # "Super-Evolve:" super-evolved with points (after on_evolve)
    on_evolved = None        # "When this follower evolves": any evolution; ctx.super_
    strike = None            # this follower attacks (anything); ctx.other / ctx.target
    follower_strike = None   # this follower attacks a follower; ctx.other = defender
    leader_strike = None     # this follower attacks a leader
    clash = None             # this follower attacks or is attacked by a follower
    engage = None            # the Engage ability (pay engage_cost first)
    on_turn_start = None     # start of controller's turn
    on_turn_end = None       # end of controller's turn
    on_opponent_turn_start = None
    on_opponent_turn_end = None
    on_discard = None        # discarded from hand
    on_drawn = None          # "When you draw this card"
    on_spellboost = None     # spellboosted in hand
    on_fuse = None           # cards were fused to this card; ctx.cards
    on_invoked = None        # "When this card is Invoked"
    on_buffed = None         # given +attack or +defense on the field
    on_damaged = None        # took damage (even 0); ctx.amount
    on_enter = None          # "When this card enters the field": played, summoned or invoked

    # --- listener hooks: cards in play (or in hand / deck if listen_in_*) ---
    on_play = None           # controller played another card; ctx.other, ctx.enhanced, ctx.as_spell
    on_ally_enter = None     # another allied follower entered the field; ctx.other
    on_enemy_enter = None    # an enemy follower entered the field; ctx.other
    on_ally_evolve = None    # another allied follower evolved; ctx.other, ctx.super_
    on_attack = None         # a follower (either side) attacked; ctx.other = attacker, ctx.target
    on_card_destroyed = None  # a card (either side) was destroyed; ctx.other
    on_ally_leave = None     # an allied follower left the field (destroyed, banished, returned); ctx.other
    on_engage = None         # controller engaged an amulet; ctx.other
    on_earth_rite = None     # controller performed an Earth Rite; ctx.amount = sigils spent
    on_draw = None           # controller drew a card; ctx.other
    on_leader_healed = None  # controller's leader had defense restored (even by 0); ctx.amount


HOOKS = ("fanfare", "cast", "last_words", "on_evolve", "on_super_evolve", "on_evolved", "strike",
         "follower_strike", "leader_strike", "clash", "engage", "on_turn_start", "on_turn_end",
         "on_opponent_turn_start", "on_opponent_turn_end", "on_discard", "on_drawn",
         "on_spellboost", "on_fuse", "on_invoked", "on_buffed", "on_damaged", "on_enter", "on_play",
         "on_ally_enter", "on_enemy_enter", "on_ally_evolve", "on_attack", "on_card_destroyed",
         "on_ally_leave", "on_engage", "on_earth_rite", "on_draw", "on_leader_healed")

_EMPTY = CardScript()
_SCRIPTS: dict[int, CardScript] = {}
LISTEN_IN_HAND: set[int] = set()   # card ids whose listener hooks fire from hand
LISTEN_IN_DECK: set[int] = set()
INVOKERS: set[int] = set()         # card ids with an Invoke condition


def register(*card_ids: int):
    def decorate(cls):
        instance = cls()
        for card_id in card_ids:
            if card_id in _SCRIPTS:
                raise ValueError(f"card {card_id} already has a script")
            _SCRIPTS[card_id] = instance
            if instance.listen_in_hand:
                LISTEN_IN_HAND.add(card_id)
            if instance.listen_in_deck:
                LISTEN_IN_DECK.add(card_id)
            if instance.invoke_at:
                INVOKERS.add(card_id)
        return cls
    return decorate


def script_for(card_id: int) -> CardScript:
    return _SCRIPTS.get(card_id, _EMPTY)


def has_script(card_id: int) -> bool:
    return card_id in _SCRIPTS


@dataclass(frozen=True, slots=True)
class Grant:
    """Something an effect gave a card: an ability (a script), stats, keywords.
    until_turn: it lasts until the end of that global turn (None = permanently).
    Stats and keywords are undone when it expires."""
    script: CardScript | None = None
    until_turn: int | None = None
    atk: int = 0
    life: int = 0
    keywords: Keyword = Keyword.NONE


def scripts_of(inst: CardInstance) -> list[CardScript]:
    """The card's own script followed by any granted ones. A card whose abilities
    were removed has no script of its own."""
    base = _EMPTY if inst.silenced else script_for(inst.defn.card_id)
    if not inst.grants:
        return [base]
    return [base] + [g.script for g in inst.grants if g.script is not None]


def prop(inst: CardInstance, name: str):
    """A static property of the card, counting granted scripts: the strongest
    value for numbers, True if any script says so for flags."""
    if not inst.grants and not inst.silenced:
        return getattr(script_for(inst.defn.card_id), name)
    values = [getattr(s, name) for s in scripts_of(inst)]
    if name == "damage_cap":
        caps = [v for v in values if v is not None]
        return min(caps) if caps else None
    if name == "attacks_per_turn":
        return max(values)
    return any(values)


@dataclass(slots=True)
class Trigger:
    hook: str
    ctx: Ctx
    script: CardScript   # resolved when queued, so alternate forms (Accelerate) can supply their own
    zone: str | None = "play"   # where the source must still be when it resolves (None = anywhere)
