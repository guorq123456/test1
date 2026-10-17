"""The card pool: gameplay stats for every card the simulator knows.

Loaded from data/rotation.json (the Rotation pool and what it generates) and
data/unlimited.json (every other card), which `python -m svsim.tools.build_pool`
generates from local official data. It has no ability text: abilities live in
the script modules, registered by card id. Every Rotation card has a script;
Unlimited cards only have one where a supported Unlimited deck needs it.
"""
import json
from pathlib import Path

from svsim.core.carddef import CardDef
from svsim.core.enums import KEYWORD_NAMES, CardType, Craft, Keyword

_DATA = Path(__file__).with_name("data")
_TYPES = {"follower": CardType.FOLLOWER, "amulet": CardType.AMULET,
          "countdown_amulet": CardType.COUNTDOWN_AMULET, "spell": CardType.SPELL}
_SPECIAL_TYPES = {"crest": CardType.CREST, "faith": CardType.FAITH,
                  "accelerate": CardType.SPELL, "crystallize": CardType.AMULET}
_SPECIAL_NAMES = {"crest": "Crest: {}", "faith": "Faith of {}", "accelerate": "{} (Accelerate)",
                  "crystallize": "{} (Crystallize)"}


def _keywords(names: list[str]) -> Keyword:
    result = Keyword.NONE
    for name in names:
        result |= KEYWORD_NAMES[name]
    return result


def _load(path: Path, cards: dict[int, CardDef]) -> set[int]:
    """Add one table's cards to `cards`; returns their ids."""
    records = json.loads(path.read_text(encoding="utf-8"))
    for r in records:                       # special forms first: cards link to them
        if "special" in r:
            kind = r["special"]
            card_type = _SPECIAL_TYPES[kind]
            if kind == "crystallize" and r["cd"]:
                card_type = CardType.COUNTDOWN_AMULET
            cards[r["id"]] = CardDef(r["id"], _SPECIAL_NAMES[kind].format(r["name"]), Craft(r["craft"]),
                                     card_type, r["cost"], countdown=r["cd"], name_zh=r["zh"],
                                     has_ability=r["ability"])
    for r in records:
        if "special" in r:
            continue
        cards[r["id"]] = CardDef(
            r["id"], r["name"], Craft(r["craft"]), _TYPES[r["type"]], r["cost"], r["atk"], r["life"],
            _keywords(r["kw"]), countdown=r["cd"], traits=tuple(r["traits"]), is_token=r["token"],
            related=tuple(r["related"]), faith=cards.get(r.get("faith")),
            accelerate=cards.get(r.get("accelerate")), crystallize=cards.get(r.get("crystallize")),
            name_zh=r["zh"], card_set=r["set"], rotation=r["rot"], has_ability=r["ability"])
    return {r["id"] for r in records}


POOL: dict[int, CardDef] = {}
ROTATION_IDS: frozenset[int] = frozenset(_load(_DATA / "rotation.json", POOL))
UNLIMITED_IDS: frozenset[int] = frozenset(_load(_DATA / "unlimited.json", POOL))
_BY_NAME = {c.name: c for c in POOL.values() if c.type not in (CardType.CREST, CardType.FAITH)}


def card(card_id: int) -> CardDef:
    return POOL[card_id]


def by_name(name: str) -> CardDef:
    return _BY_NAME[name]


def collectible(craft: Craft | None = None, unlimited: bool = False) -> list[CardDef]:
    """Deck-buildable cards (Rotation, or every set with `unlimited`), optionally
    for one craft (plus Neutral)."""
    cards = [c for c in POOL.values() if c.rotation or (
        unlimited and c.card_set and not c.is_token and c.type not in (CardType.CREST, CardType.FAITH))]
    if craft is not None:
        cards = [c for c in cards if c.craft in (craft, Craft.NEUTRAL)]
    return sorted(cards, key=lambda c: c.card_id)
