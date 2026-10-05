"""Convert official card database records into CardDefs.

Input is the English (Lang: en) JSON returned by the official card list endpoint (see
svsim/tools/fetch_cards.py), saved locally under data/raw/. Only printed data
is converted: base keywords that appear as a line of their own, and the
countdown of countdown amulets. Every other ability is natural-language text
and needs a hand-written CardScript.
"""
import json
from pathlib import Path
import re

from svsim.core.carddef import CardDef
from svsim.core.enums import KEYWORD_NAMES, CardType, Craft, Keyword

_TAG = re.compile(r"<[^>]+>")
_EVOLVE_BLOCK = re.compile(r"<(ev|sev)>.*?</\1>", re.S)
_COUNTDOWN = re.compile(r"^Countdown \((\d+)\)$")


def plain_text(skill_text: str) -> str:
    return _TAG.sub("", skill_text or "").strip()


def _segments(skill_text: str) -> list[str]:
    """Plain-text ability lines, leaving out Evolve / Super-Evolve blocks."""
    text = _EVOLVE_BLOCK.sub("", skill_text or "")
    return [plain_text(s) for s in re.split(r"\n|<hr>", text) if plain_text(s)]


def parse_keywords(skill_text: str) -> Keyword:
    """Keywords printed on a line of their own, like "Ward". A keyword inside a
    sentence ("Give this follower Storm") is an effect, not a base keyword."""
    result = Keyword.NONE
    for line in _segments(skill_text):
        if line in KEYWORD_NAMES:
            result |= KEYWORD_NAMES[line]
    return result


def parse_countdown(skill_text: str) -> int | None:
    for line in _segments(skill_text):
        match = _COUNTDOWN.match(line)
        if match:
            return int(match.group(1))
    return None


def card_from_record(detail: dict, related: tuple[int, ...] = ()) -> CardDef:
    c = detail["common"]
    card_type = CardType(c["type"])
    skill = c.get("skill_text") or ""
    return CardDef(
        card_id=c["card_id"],
        name=c["name"],
        craft=Craft(c["class"]),
        type=card_type,
        cost=c["cost"],
        atk=c["atk"] or 0,
        life=c["life"] or 0,
        keywords=parse_keywords(skill),
        countdown=parse_countdown(skill) if card_type == CardType.COUNTDOWN_AMULET else None,
        is_token=bool(c.get("is_token")),
        text=plain_text(skill),
        related=related,
    )


def load_cards(paths) -> dict[int, CardDef]:
    """Load CardDefs from saved card list responses (one or more files)."""
    cards: dict[int, CardDef] = {}
    for path in paths:
        data = json.loads(Path(path).read_text(encoding="utf-8"))["data"]
        details = data.get("card_details")
        if not isinstance(details, dict):      # sets with no cards come back as []
            continue
        links = data.get("cards") or {}
        for key, detail in details.items():
            related = tuple((links.get(key) or {}).get("related_card_ids") or ())
            card = card_from_record(detail, related)
            cards[card.card_id] = card
    return cards
