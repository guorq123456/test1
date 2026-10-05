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

    @property
    def is_follower(self) -> bool:
        return self.type == CardType.FOLLOWER

    @property
    def is_amulet(self) -> bool:
        return self.type in (CardType.AMULET, CardType.COUNTDOWN_AMULET)

    @property
    def is_spell(self) -> bool:
        return self.type == CardType.SPELL

    @property
    def goes_to_field(self) -> bool:
        return self.type != CardType.SPELL
