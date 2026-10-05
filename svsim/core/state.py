"""Mutable game state.

Everything that changes during a match lives here, and nothing else does:
card scripts are stateless, so cloning a GameState is enough to branch a game
for search, and a seed plus an action list is enough to replay one.
"""
from collections import deque
from dataclasses import dataclass, field as dc_field
import copy
import random

from .carddef import CardDef
from .enums import Keyword, Phase

HAND_LIMIT = 9
FIELD_LIMIT = 5
LEADER_AREA_LIMIT = 5
MAX_PP = 10
LEADER_HP = 20

# CardInstance.fate: how a card left the field
IN_PLAY, DESTROYED, BANISHED = 0, 1, 2


def leader_uid(player: int) -> int:
    """Leaders are addressed by negative uids so actions can target them like cards."""
    return -(player + 1)


def leader_of(uid: int) -> int | None:
    return -uid - 1 if uid < 0 else None


@dataclass(slots=True)
class CardInstance:
    uid: int
    defn: CardDef
    owner: int
    cost: int
    atk: int
    life: int
    max_life: int
    keywords: Keyword
    countdown: int | None = None
    evolved: bool = False
    super_evolved: bool = False
    entered_turn: int = -1        # global turn number it entered the field
    attacks_made: int = 0
    max_attacks: int = 1
    order: int = 0                # field entry sequence: lower = older = resolves first
    fate: int = IN_PLAY
    counters: dict | None = None  # per-card script state (e.g. a stack count)

    @classmethod
    def create(cls, uid: int, defn: CardDef, owner: int) -> "CardInstance":
        return cls(uid=uid, defn=defn, owner=owner, cost=defn.cost, atk=defn.atk,
                   life=defn.life, max_life=defn.life, keywords=defn.keywords,
                   countdown=defn.countdown)

    def copy(self) -> "CardInstance":
        clone = copy.copy(self)
        if self.counters is not None:
            clone.counters = dict(self.counters)
        return clone

    def has(self, keyword: Keyword) -> bool:
        return bool(self.keywords & keyword)

    def __repr__(self) -> str:
        stats = f" {self.atk}/{self.life}" if self.defn.is_follower else ""
        return f"<{self.defn.name}#{self.uid}{stats}>"


@dataclass(slots=True)
class PlayerState:
    index: int
    leader_hp: int = LEADER_HP
    leader_max_hp: int = LEADER_HP
    max_pp: int = 0
    pp: int = 0
    ep: int = 2                   # evolution points
    sep: int = 2                  # super-evolution points
    turns_taken: int = 0          # own turn count; evolution unlocks depend on it
    evolved_this_turn: bool = False
    bonus_ready: bool = False     # second player's Bonus Play Point button
    bonus_active: bool = False
    combo: int = 0                # cards played this turn
    rally: int = 0                # allied followers that entered the field this match
    shadows: int = 0              # cemetery count
    deck: list[CardInstance] = dc_field(default_factory=list)   # top of deck = last element
    hand: list[CardInstance] = dc_field(default_factory=list)
    field: list[CardInstance] = dc_field(default_factory=list)  # oldest first
    leader_area: list[CardInstance] = dc_field(default_factory=list)  # crests and faiths, oldest first
    destroyed: list[int] = dc_field(default_factory=list)       # card_ids of allied followers destroyed (Reanimate)
    damage_cap: int | None = None  # leader "can't take more than N damage at a time"
    damage_cap_until: int = 0      # global turn at whose end damage_cap expires

    def copy(self) -> "PlayerState":
        clone = copy.copy(self)
        clone.deck = [c.copy() for c in self.deck]
        clone.hand = [c.copy() for c in self.hand]
        clone.field = [c.copy() for c in self.field]
        clone.leader_area = [c.copy() for c in self.leader_area]
        clone.destroyed = list(self.destroyed)
        return clone

    @property
    def followers(self) -> list[CardInstance]:
        return [c for c in self.field if c.defn.is_follower]


@dataclass(slots=True)
class GameState:
    players: list[PlayerState]
    rng: random.Random
    first: int                    # player who went first
    active: int                   # player whose turn (or mulligan) it is
    turn: int = 0                 # global turn counter, 1 = first player's first turn
    phase: Phase = Phase.MULLIGAN
    winner: int | None = None     # 0 / 1, or enums.DRAW
    next_uid: int = 1
    next_order: int = 1
    max_turns: int = 60           # safety cap on global turns (draw); not a confirmed game rule
    queue: deque = dc_field(default_factory=deque)  # pending triggers; always empty between actions

    def clone(self) -> "GameState":
        assert not self.queue, "clone only between actions"
        rng = random.Random()
        rng.setstate(self.rng.getstate())
        return GameState(players=[p.copy() for p in self.players], rng=rng, first=self.first,
                         active=self.active, turn=self.turn, phase=self.phase,
                         winner=self.winner, next_uid=self.next_uid,
                         next_order=self.next_order, max_turns=self.max_turns)

    def new_instance(self, defn: CardDef, owner: int) -> CardInstance:
        inst = CardInstance.create(self.next_uid, defn, owner)
        self.next_uid += 1
        return inst

    def on_field(self, uid: int) -> CardInstance | None:
        for p in self.players:
            for c in p.field:
                if c.uid == uid:
                    return c
        return None

    def in_play(self, uid: int) -> CardInstance | None:
        """A card on either field or in either leader area."""
        for p in self.players:
            for c in p.field:
                if c.uid == uid:
                    return c
            for c in p.leader_area:
                if c.uid == uid:
                    return c
        return None

    def in_hand(self, player: int, uid: int) -> CardInstance | None:
        for c in self.players[player].hand:
            if c.uid == uid:
                return c
        return None

    def field_order(self) -> list[CardInstance]:
        """All field cards in trigger order: turn player first, oldest first."""
        a = self.players[self.active].field
        b = self.players[1 - self.active].field
        return list(a) + list(b)

    def listeners(self) -> list[CardInstance]:
        """Everything that can react to an event, in trigger order: turn player's
        leader area, then field, then the other player's leader area and field."""
        a, b = self.players[self.active], self.players[1 - self.active]
        return a.leader_area + a.field + b.leader_area + b.field

    @property
    def over(self) -> bool:
        return self.phase == Phase.OVER
