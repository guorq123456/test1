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


# specific_effect_type values in the official data
SPECIAL_CREST, SPECIAL_CRYSTALLIZE, SPECIAL_ACCELERATE, SPECIAL_FAITH = 1, 2, 3, 4


def special_from_record(special_id: int, info: dict, parent_name: str, craft: Craft) -> CardDef:
    """A leader-area object or alternate play form listed under specific_effect_card_info."""
    kind = info.get("specific_effect_type")
    skill = info.get("skill_text") or ""
    if kind == SPECIAL_CREST:
        return CardDef(special_id, f"Crest: {parent_name}", craft, CardType.CREST, 0,
                       countdown=parse_countdown(skill), text=plain_text(skill))
    if kind == SPECIAL_FAITH:
        return CardDef(special_id, f"Faith of {parent_name}", craft, CardType.FAITH, 0,
                       text=plain_text(skill))
    if kind == SPECIAL_ACCELERATE:
        return CardDef(special_id, f"{parent_name} (Accelerate)", craft, CardType.SPELL,
                       info.get("cost") or 0, text=plain_text(skill))
    countdown = parse_countdown(skill)
    card_type = CardType.COUNTDOWN_AMULET if countdown else CardType.AMULET
    return CardDef(special_id, f"{parent_name} (Crystallize)", craft, card_type, info.get("cost") or 0,
                   countdown=countdown, text=plain_text(skill))


def card_from_record(detail: dict, related: tuple[int, ...] = (),
                     specials: tuple[CardDef, ...] = ()) -> CardDef:
    c = detail["common"]
    card_type = CardType(c["type"])
    skill = c.get("skill_text") or ""
    faith = next((d for d in specials if d.type == CardType.FAITH), None)
    accelerate = next((d for d in specials if d.type == CardType.SPELL), None)
    crystallize = next((d for d in specials if d.is_amulet), None)
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
        faith=faith,
        accelerate=accelerate,
        crystallize=crystallize,
    )


def load_cards(paths) -> dict[int, CardDef]:
    """Load CardDefs from saved card list responses (one or more files). Crests,
    faiths and Accelerate / Crystallize forms are included under their own ids."""
    cards: dict[int, CardDef] = {}
    for path in paths:
        data = json.loads(Path(path).read_text(encoding="utf-8"))["data"]
        details = data.get("card_details")
        if not isinstance(details, dict):      # sets with no cards come back as []
            continue
        links = data.get("cards") or {}
        special_info = data.get("specific_effect_card_info") or {}
        for key, detail in details.items():
            link = links.get(key) or {}
            common = detail["common"]
            specials = tuple(
                special_from_record(sid, special_info[str(sid)], common["name"],
                                    Craft(common["class"]))
                for sid in link.get("specific_effect_card_ids") or ()
                if str(sid) in special_info)
            card = card_from_record(detail, tuple(link.get("related_card_ids") or ()), specials)
            cards[card.card_id] = card
            for special in specials:
                cards[special.card_id] = special
    return cards
