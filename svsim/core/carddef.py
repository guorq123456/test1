"""Immutable card definitions: printed data only, no behaviour.

Behaviour lives in a CardScript registered under the same card_id
(see script.py), so definitions can be loaded straight from the official
database while abilities are implemented and reviewed separately.
"""
from dataclasses import dataclass

from .enums import CardType, Craft, Keyword


@dataclass(frozen=True, slots=True)
class CardDef:
    card_id: int
    name: str
    craft: Craft
    type: CardType
    cost: int
    atk: int = 0
    life: int = 0
    keywords: Keyword = Keyword.NONE
    countdown: int | None = None      # countdown amulets only
    traits: tuple[str, ...] = ()
    is_token: bool = False
    text: str = ""                    # printed ability text, for display and review
    related: tuple[int, ...] = ()     # tokens this card can create (official related_card_ids)
    faith: "CardDef | None" = None    # faith put in the leader area at match start
    accelerate: "CardDef | None" = None  # spell form played when the normal cost can't be paid
    crystallize: "CardDef | None" = None  # amulet form played when the normal cost can't be paid
    name_zh: str = ""                 # official Simplified Chinese name, for display
    card_set: int = 0                 # official card_set_id (10000 = Basic, 90000 = tokens)
    rotation: bool = False            # deck-buildable in Rotation
    has_ability: bool = False         # has abilities beyond keywords, so it needs a script

    @property
    def is_follower(self) -> bool:
        return self.type == CardType.FOLLOWER

    @property
    def is_amulet(self) -> bool:
        return self.type in (CardType.AMULET, CardType.COUNTDOWN_AMULET)

    @property
    def is_spell(self) -> bool:
        return self.type == CardType.SPELL

    def has_trait(self, trait: str) -> bool:
        return trait in self.traits

    @property
    def goes_to_field(self) -> bool:
        return self.type in (CardType.FOLLOWER, CardType.AMULET, CardType.COUNTDOWN_AMULET)
