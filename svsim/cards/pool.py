"""The Rotation card pool: gameplay stats for every card the simulator knows.

Loaded from data/rotation.json, which `python -m svsim.tools.build_pool`
generates from local official data. It has no ability text: abilities live in
the per-craft script modules, registered by card id.
"""
import json
from pathlib import Path

from svsim.core.carddef import CardDef
from svsim.core.enums import KEYWORD_NAMES, CardType, Craft, Keyword

_PATH = Path(__file__).with_name("data") / "rotation.json"
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


def _load() -> dict[int, CardDef]:
    records = json.loads(_PATH.read_text(encoding="utf-8"))
    cards: dict[int, CardDef] = {}
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
    return cards


POOL: dict[int, CardDef] = _load()
_BY_NAME = {c.name: c for c in POOL.values() if c.type not in (CardType.CREST, CardType.FAITH)}


def card(card_id: int) -> CardDef:
    return POOL[card_id]


def by_name(name: str) -> CardDef:
    return _BY_NAME[name]


def collectible(craft: Craft | None = None) -> list[CardDef]:
    """Deck-buildable Rotation cards, optionally for one craft (plus Neutral)."""
    cards = [c for c in POOL.values() if c.rotation]
    if craft is not None:
        cards = [c for c in cards if c.craft in (craft, Craft.NEUTRAL)]
    return sorted(cards, key=lambda c: c.card_id)
