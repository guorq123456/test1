"""The player's own decks in the page (web/index.html's deck editor): the card pool, deck checks and deck codes.

The page keeps the player's decks itself (the browser and the page's store) and sends a deck to the session as
{"name": ..., "code": ...}, the game's deck code ("1.<class>.<card>..."; deckcode). This module turns a code into
cards and says, in Chinese, what makes a deck illegal: 40 cards, at most 3 of a card, one class and Neutral, the
current Rotation (set 10 in, set 4 out; pool.collectible), no tokens.

The bot's own decks (BOT_DECKS, one "name|code" per line, the deckbuild seed format) are offered as opponents.
A deck the AI has no trained model for plays the generic levels (session.GENERIC): per-deck nets don't carry to an
unseen deck (2026-10-29: 22-26% against the hand-set evaluator), so a custom deck gets the hand-set evaluator, the
same bot the deck search used.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from svsim.cards import deckcode
from svsim.cards.decks import DECK_SIZE, MAX_COPIES, build
from svsim.cards.pool import POOL, collectible
from svsim.core.enums import CardType, Craft
from svsim.core.script import script_for
from svsim.ui.text import card_name, keywords_zh

HERE = Path(__file__).resolve().parent
BOT_DECKS = HERE / "bot_decks.txt"
NICKNAMES = HERE / "nicknames.json"        # {card id: community name}, from analysis/card-glossary.md
NEW_SET = 10010                            # Deicide in Nacreheim (2026-10-28)
CLASS_ZH = {Craft.NEUTRAL: "中立", Craft.FOREST: "精灵", Craft.SWORD: "皇家", Craft.RUNE: "巫师", Craft.DRAGON: "龙族",
            Craft.ABYSS: "梦魇", Craft.HAVEN: "主教", Craft.PORTAL: "超越者"}
_TYPE_ZH = {CardType.FOLLOWER: "随从", CardType.SPELL: "法术", CardType.AMULET: "护符",
            CardType.COUNTDOWN_AMULET: "倒数护符"}


def _nicknames() -> dict:
    try:
        return {int(k): v for k, v in json.loads(NICKNAMES.read_text(encoding="utf-8")).items()}
    except (OSError, ValueError):
        return {}


def _text(defn) -> str:
    doc = " ".join((type(script_for(defn.card_id)).__doc__ or "").split())
    if not doc or doc.startswith("A card's abilities"):
        doc = defn.text or ""
    return doc


def pool() -> dict:
    """Every card a Rotation deck may hold, for the editor: id, names, class, cost, type, stats, keywords, set,
    the simulator's text of it (English, the card scripts' own), and the classes' Chinese names."""
    nick = _nicknames()
    cards = []
    for c in collectible():
        if c.is_token or c.type in (CardType.CREST, CardType.FAITH):
            continue
        entry = {"id": c.card_id, "name": card_name(c), "en": c.name, "craft": int(c.craft), "cost": c.cost,
                 "type": _TYPE_ZH.get(c.type, ""), "set": c.card_set, "new": c.card_set == NEW_SET,
                 "kw": keywords_zh(c.keywords), "text": _text(c)}
        if c.is_follower:
            entry.update(atk=c.atk, life=c.life)
        if c.card_id in nick and nick[c.card_id] != entry["name"]:
            entry["nick"] = nick[c.card_id]
        cards.append(entry)
    return {"cards": cards, "classes": {int(k): v for k, v in CLASS_ZH.items()}, "size": DECK_SIZE,
            "max_copies": MAX_COPIES, "new_set": NEW_SET}


def problems(ids: list, craft: int | None = None) -> list[str]:
    """What makes the deck `ids` illegal in Rotation, in Chinese (empty: legal). `craft`: the class it is for
    (default: the one its class cards have)."""
    out = []
    unknown = [i for i in ids if i not in POOL]
    if unknown:
        out.append(f"模拟器里没有这些卡：{', '.join(map(str, sorted(set(unknown))))}")
    cards = [POOL[i] for i in ids if i in POOL]
    crafts = {c.craft for c in cards} - {Craft.NEUTRAL}
    if craft is None:
        craft = crafts.pop() if len(crafts) == 1 else None
    if craft is not None:
        craft = Craft(int(craft))
    if craft is None or craft == Craft.NEUTRAL:
        out.append("一副卡组只能有一个职业（加中立卡）" if len(crafts) > 1 else "还没有职业卡，选不出职业")
    if len(ids) != DECK_SIZE:
        out.append(f"现在 {len(ids)} 张，要正好 {DECK_SIZE} 张")
    for c, n in sorted(Counter(cards).items(), key=lambda x: x[0].card_id):
        name = card_name(c)
        if n > MAX_COPIES:
            out.append(f"{name} 有 {n} 张，同名卡最多 {MAX_COPIES} 张")
        if c.is_token or c.type in (CardType.CREST, CardType.FAITH):
            out.append(f"{name} 是衍生卡，不能放进卡组")
        elif not c.rotation:
            out.append(f"{name} 不在现在的轮替环境里（第 4 弹已退环境）")
        if craft not in (None, Craft.NEUTRAL) and c.craft not in (Craft.NEUTRAL, craft):
            out.append(f"{name} 是{CLASS_ZH[c.craft]}卡，不能放进{CLASS_ZH[craft]}卡组")
    return out


def parse_code(text: str) -> list[int]:
    """Card ids from a deck code, or from a deck-builder link that carries one (…?hash=1.2.xxxx…)."""
    return decode(text)[1]


def decode(text: str) -> tuple[int, list[int]]:
    """(class, card ids) of a deck code or a link carrying one."""
    text = text.strip()
    if "hash=" in text:
        text = text.split("hash=", 1)[1].split("&", 1)[0].split("#", 1)[0]
    try:
        _, craft, ids = deckcode.decode_deck(text)
        Craft(craft)
    except (ValueError, KeyError):
        raise ValueError("看不懂这个卡组代码：应该像 1.2.cEZs.dmj6…（点号隔开，第二段是职业编号）") from None
    return craft, ids


def check(code_or_ids, craft: int | None = None) -> dict:
    """A deck from the editor (a code, a link, or a list of ids; `craft`: the class the editor holds it for): its ids,
    class, code, problems, and the names of its cards the editor's pool lacks (out of Rotation): "others"."""
    if isinstance(code_or_ids, str):
        craft, ids = decode(code_or_ids)
        craft = craft or None                 # class 0 (Neutral) says nothing
    else:
        ids = [int(i) for i in code_or_ids]
    craft = craft or None
    if craft is None:
        crafts = {POOL[i].craft for i in ids if i in POOL} - {Craft.NEUTRAL}
        craft = crafts.pop() if len(crafts) == 1 else None
    found = problems(ids, craft)
    code = deckcode.encode_deck(deckcode.ROTATION, int(craft or 0), sorted(ids)) if craft is not None else None
    others = {}
    for i in set(ids):
        c = POOL.get(i)
        if c is not None and not c.rotation:
            others[i] = {"id": i, "name": card_name(c), "en": c.name, "craft": int(c.craft), "cost": c.cost,
                         "type": _TYPE_ZH.get(c.type, ""), "set": c.card_set, "text": "不在现在的轮替环境里，不能用。"}
    return {"ids": sorted(ids), "craft": int(craft) if craft is not None else None, "code": code, "problems": found,
            "others": others}


def deck_from(spec: dict) -> list:
    """The cards of a deck the page sends ({"name", "code"}); ValueError when it is illegal."""
    craft, ids = decode(spec["code"])
    found = problems(ids, craft or None)
    if found:
        raise ValueError(f"卡组「{spec.get('name') or '未命名'}」不合法：" + "；".join(found))
    return build(Counter(POOL[i] for i in ids))


def bot_decks() -> dict:
    """The bot's own decks (BOT_DECKS): {"note": the file's first comment line, "decks": [{key, name, craft, code}]}.
    A line is "key|code" or "key|code|display name"; '#' lines are comments."""
    note, out = "", []
    try:
        lines = BOT_DECKS.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {"note": "", "decks": []}
    for line in lines:
        line = line.strip()
        if line.startswith("#"):
            note = note or line.lstrip("# ").strip()
            continue
        if not line:
            continue
        key, code, *name = line.split("|")
        ids = parse_code(code)
        crafts = {POOL[i].craft for i in ids if i in POOL} - {Craft.NEUTRAL}
        craft = crafts.pop() if len(crafts) == 1 else Craft.NEUTRAL
        out.append({"key": key, "name": name[0] if name else f"bot 的{CLASS_ZH[craft]}", "craft": int(craft),
                    "code": code, "problems": problems(ids)})
    return {"note": note, "decks": out}
