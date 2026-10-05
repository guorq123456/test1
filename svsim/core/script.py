"""How cards plug abilities into the engine.

A CardScript describes one card's behaviour: which choices it needs when
played or evolved, and which hooks fire when. Scripts are stateless singletons
registered by card_id; anything a card must remember goes in
CardInstance.counters.

    @register(1234)
    class Archer(CardScript):
        play_target = TargetSpec(Target.ENEMY_FOLLOWER)

        def fanfare(self, ctx):
            effects.damage(ctx.state, ctx.chosen(), 1, ctx.source)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import CardInstance, GameState, PlayerState


class Target(IntEnum):
    ENEMY_FOLLOWER = 1
    ALLIED_FOLLOWER = 2
    ANY_FOLLOWER = 3
    ENEMY_FOLLOWER_OR_LEADER = 4


@dataclass(frozen=True, slots=True)
class TargetSpec:
    kind: Target
    count: int = 1


@dataclass(slots=True)
class Ctx:
    """Everything a hook needs: the state, the card, and the choices made for it."""
    state: GameState
    source: CardInstance
    controller: int
    targets: tuple[int, ...] = ()
    modes: tuple[int, ...] = ()
    enhanced: int = 0                    # Enhance cost paid, 0 if not enhanced
    other: CardInstance | None = None    # the other follower in Strike / Clash / enter-field hooks

    @property
    def me(self) -> PlayerState:
        return self.state.players[self.controller]

    @property
    def opponent(self) -> PlayerState:
        return self.state.players[1 - self.controller]

    def chosen(self) -> list:
        """Selected targets that are still valid: field instances, or leader uids."""
        result = []
        for uid in self.targets:
            if uid < 0:
                result.append(uid)
            else:
                inst = self.state.on_field(uid)
                if inst is not None:
                    result.append(inst)
        return result


class CardScript:
    # Choices made when the card is played / evolved (folded into the action).
    play_target: TargetSpec | None = None
    evolve_target: TargetSpec | None = None
    enhance: tuple[int, ...] = ()        # Enhance costs; the highest affordable one is paid
    modes: tuple[int, int] | None = None  # (number of options, how many to pick)

    # Hooks. Each is either None or a method taking a Ctx.
    fanfare = None           # follower / amulet played from hand
    cast = None              # spell played
    last_words = None        # destroyed (not banished)
    on_evolve = None         # evolved or super-evolved with points
    on_super_evolve = None   # super-evolved with points (fires after on_evolve)
    strike = None            # this follower attacks a follower; ctx.other = defender
    clash = None             # this follower attacks or is attacked by a follower
    on_turn_start = None     # start of controller's turn
    on_turn_end = None       # end of controller's turn
    on_ally_enter = None     # another allied follower entered the field; ctx.other = it


HOOKS = ("fanfare", "cast", "last_words", "on_evolve", "on_super_evolve", "strike",
         "clash", "on_turn_start", "on_turn_end", "on_ally_enter")

_EMPTY = CardScript()
_SCRIPTS: dict[int, CardScript] = {}


def register(*card_ids: int):
    def decorate(cls):
        instance = cls()
        for card_id in card_ids:
            if card_id in _SCRIPTS:
                raise ValueError(f"card {card_id} already has a script")
            _SCRIPTS[card_id] = instance
        return cls
    return decorate


def script_for(card_id: int) -> CardScript:
    return _SCRIPTS.get(card_id, _EMPTY)


def has_script(card_id: int) -> bool:
    return card_id in _SCRIPTS


@dataclass(slots=True)
class Trigger:
    hook: str
    ctx: Ctx
