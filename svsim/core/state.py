"""Mutable game state.

Everything that changes during a match lives here, and nothing else does:
card scripts are stateless, so cloning a GameState is enough to branch a game
for search, and a seed plus an action list is enough to replay one.
"""
from collections import deque
from dataclasses import dataclass, field as dc_field
import os
import random

_new_object = object.__new__
_new_random = random.Random.__new__

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
    engaged_turn: int = -1        # global turn of the last Engage
    fused_turn: int = -1          # global turn of the last Fuse to this card
    silenced: bool = False        # "remove all abilities": its own script no longer applies
    no_last_words: bool = False   # "remove Last Words": its own Last Words don't activate
    counters: dict | None = None  # per-card script state (e.g. a stack count)
    grants: list | None = None    # script.Grant: abilities and stats given by effects
    cost_mods: list | None = None # (op, value, until_turn) cost changes, applied in order

    @classmethod
    def create(cls, uid: int, defn: CardDef, owner: int) -> "CardInstance":
        return cls(uid=uid, defn=defn, owner=owner, cost=defn.cost, atk=defn.atk,
                   life=defn.life, max_life=defn.life, keywords=defn.keywords,
                   countdown=defn.countdown)

    def copy(self) -> "CardInstance":
        # Field by field: about 10x faster than copy.copy, and search clones a lot.
        # tests/test_state.py checks that every field is copied.
        clone = _new_object(CardInstance)
        clone.uid = self.uid
        clone.defn = self.defn
        clone.owner = self.owner
        clone.cost = self.cost
        clone.atk = self.atk
        clone.life = self.life
        clone.max_life = self.max_life
        clone.keywords = self.keywords
        clone.countdown = self.countdown
        clone.evolved = self.evolved
        clone.super_evolved = self.super_evolved
        clone.entered_turn = self.entered_turn
        clone.attacks_made = self.attacks_made
        clone.max_attacks = self.max_attacks
        clone.order = self.order
        clone.fate = self.fate
        clone.engaged_turn = self.engaged_turn
        clone.fused_turn = self.fused_turn
        clone.silenced = self.silenced
        clone.no_last_words = self.no_last_words
        counters, grants, cost_mods = self.counters, self.grants, self.cost_mods
        clone.counters = None if counters is None else {k: (list(v) if isinstance(v, list) else v)
                                                        for k, v in counters.items()}
        clone.grants = None if grants is None else list(grants)
        clone.cost_mods = None if cost_mods is None else list(cost_mods)
        return clone

    def has(self, keyword: Keyword) -> bool:
        return bool(self.keywords & keyword)

    def __repr__(self) -> str:
        stats = f" {self.atk}/{self.life}" if self.defn.is_follower else ""
        return f"<{self.defn.name}#{self.uid}{stats}>"


# Copy on write of deck cards, checked (SVSIM_COW_CHECK=1): every card is fingerprinted when it is first shared,
# and the fingerprint is verified when its deck is cloned or copied, at the end of every search iteration and in a
# sweep after every decision (search.mcts, search.lethal). A shared card must never change: whoever changes one must
# own its deck first (PlayerState.deck).
CHECK = bool(os.environ.get("SVSIM_COW_CHECK"))
_SHARED: dict = {}                     # id(card) -> (card, fingerprint)


def fingerprint(c: CardInstance) -> tuple:
    return (id(c.defn), c.uid, c.owner, c.cost, c.atk, c.life, c.max_life, int(c.keywords), c.countdown,
            c.evolved, c.super_evolved, c.entered_turn, c.attacks_made, c.max_attacks, c.order, c.fate,
            c.engaged_turn, c.fused_turn, c.silenced, c.no_last_words,
            None if c.counters is None else repr(sorted(c.counters.items())),
            None if c.grants is None else tuple(c.grants),
            None if c.cost_mods is None else tuple(c.cost_mods))


def _register(cards) -> None:
    for c in cards:
        hit = _SHARED.get(id(c))
        if hit is None:
            _SHARED[id(c)] = (c, fingerprint(c))
        elif hit[1] != fingerprint(c):
            raise AssertionError(f"shared deck card {c!r} changed")


def _verify(cards) -> None:
    for c in cards:
        hit = _SHARED.get(id(c))
        if hit is not None and hit[1] != fingerprint(c):
            raise AssertionError(f"shared deck card {c!r} changed")


def verify_state(state) -> None:
    """Check mode: the cards in `state`'s decks are as they were when shared."""
    if CHECK:
        for p in state.players:
            _verify(p._deck)


def sweep(keep=None) -> None:
    """Check mode: every card shared so far is as it was; then forget all but `keep`'s deck cards (a state still
    in use, verified too), so the record doesn't grow without end."""
    if not CHECK:
        return
    for c, f in _SHARED.values():
        if fingerprint(c) != f:
            raise AssertionError(f"shared deck card {c!r} changed")
    kept = {} if keep is None else {id(c): _SHARED[id(c)] for p in keep.players for c in p._deck if id(c) in _SHARED}
    _SHARED.clear()
    _SHARED.update(kept)


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
    _deck: list[CardInstance] = dc_field(default_factory=list)  # top of deck = last element (`deck`)
    hand: list[CardInstance] = dc_field(default_factory=list)
    field: list[CardInstance] = dc_field(default_factory=list)  # oldest first
    leader_area: list[CardInstance] = dc_field(default_factory=list)  # crests and faiths, oldest first
    destroyed: list[CardDef] = dc_field(default_factory=list)   # allied followers destroyed (Reanimate)
    destroyed_amulets: list[CardDef] = dc_field(default_factory=list)
    played_base_costs: set[int] = dc_field(default_factory=set)  # base costs of cards played this match
    evolutions: int = 0            # allied evolutions this match (any method)
    attacked_leader_this_turn: bool = False
    attacked_leader_last_turn: bool = False    # "if an allied follower attacked a leader on your last turn"
    damage_cap: int | None = None  # leader "can't take more than N damage at a time"
    damage_cap_until: int = 0      # global turn at whose end damage_cap expires
    extra_damage: int = 0          # leader "takes N more damage"
    entered: dict = dc_field(default_factory=dict)   # card_id -> allied follower entries this match
    deck_name: str | None = None   # the named deck registered (cards.decks.NAMED), "" for another; set by new_game
    _deck_shared: bool = dc_field(default=False, compare=False, repr=False)   # see `deck`

    def copy(self) -> "PlayerState":
        # Field by field, as CardInstance.copy (copy.copy goes through __reduce_ex__: several times slower);
        # tests/test_state.py checks that every field is copied.
        clone = _new_object(PlayerState)
        clone.index = self.index
        clone.leader_hp = self.leader_hp
        clone.leader_max_hp = self.leader_max_hp
        clone.max_pp = self.max_pp
        clone.pp = self.pp
        clone.ep = self.ep
        clone.sep = self.sep
        clone.turns_taken = self.turns_taken
        clone.evolved_this_turn = self.evolved_this_turn
        clone.bonus_ready = self.bonus_ready
        clone.bonus_active = self.bonus_active
        clone.combo = self.combo
        clone.rally = self.rally
        clone.shadows = self.shadows
        # the deck's cards are shared, copied on write (`deck`): most clones never touch a card in a deck
        clone._deck = list(self._deck)
        clone._deck_shared = self._deck_shared = True
        if CHECK:
            _register(self._deck)
        clone.hand = [c.copy() for c in self.hand]
        clone.field = [c.copy() for c in self.field]
        clone.leader_area = [c.copy() for c in self.leader_area]
        clone.destroyed = list(self.destroyed)
        clone.destroyed_amulets = list(self.destroyed_amulets)
        clone.played_base_costs = set(self.played_base_costs)
        clone.evolutions = self.evolutions
        clone.attacked_leader_this_turn = self.attacked_leader_this_turn
        clone.attacked_leader_last_turn = self.attacked_leader_last_turn
        clone.damage_cap = self.damage_cap
        clone.damage_cap_until = self.damage_cap_until
        clone.extra_damage = self.extra_damage
        clone.entered = dict(self.entered)
        clone.deck_name = self.deck_name
        return clone

    @property
    def deck(self) -> list[CardInstance]:
        """The deck (top = last), this player's own to change: cards it still shares with a clone or the state it
        was cloned from (`copy`) are copied first. Code that only reads, and keeps nothing, may use `deck_view`."""
        if self._deck_shared:
            self._own_deck()
        return self._deck

    @deck.setter
    def deck(self, cards: list[CardInstance]) -> None:
        self._deck = cards
        self._deck_shared = False

    def deck_view(self) -> list[CardInstance]:
        """The deck without copying shared cards: to read only (neither the list nor its cards may change, and
        no card may be kept or moved elsewhere)."""
        return self._deck

    def draw_top(self) -> CardInstance:
        """deck.pop(), copying only the card taken if it is shared (the rest of the deck stays shared)."""
        if not self._deck_shared:
            return self._deck.pop()
        card = self._deck.pop()                   # the list is this player's own; the card may be shared
        if CHECK:
            _verify((card,))
        return card.copy()

    def _own_deck(self) -> None:
        if CHECK:
            _verify(self._deck)
        self._deck = [c.copy() for c in self._deck]
        self._deck_shared = False

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

    def clone(self, copy_rng: bool = True) -> "GameState":
        """An independent copy. copy_rng=False leaves the copy's generator unseeded, for a caller that seeds it
        at once (core.view.determinize): copying a state the seed then overwrites is wasted time."""
        assert not self.queue, "clone only between actions"
        if CHECK:
            for p in self.players:
                _verify(p._deck)
        rng = _new_random(random.Random)          # not random.Random(): that seeds itself from the OS first
        if copy_rng:
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

    def in_zone(self, inst: CardInstance, zone: str | None) -> bool:
        """Whether `inst` is still in `zone` ("play", "hand", "deck"; None = anywhere)."""
        if zone is None:
            return True
        if zone == "play":
            return self.in_play(inst.uid) is inst
        cards = self.players[inst.owner].hand if zone == "hand" else self.players[inst.owner].deck
        return any(c is inst for c in cards)

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
