"""Build svsim/cards/data/rotation.json: gameplay stats for the Rotation pool.

    python -m svsim.tools.fetch_cards --lang en
    python -m svsim.tools.fetch_cards --lang chs
    python -m svsim.tools.build_pool

The table holds what the engine needs (cost, stats, keywords, traits, links to
tokens and special forms) and display names, but no ability text or art. It
covers every Rotation card, every card they can generate, and their crests,
faiths and Accelerate / Crystallize forms. Rebuild after each set release or
balance patch.
"""
import argparse
import json
from pathlib import Path

from svsim.cards.official import has_ability, parse_countdown, parse_keywords
from svsim.core.enums import KEYWORD_NAMES, CardType

SPECIAL_TYPES = {1: "crest", 2: "crystallize", 3: "accelerate", 4: "faith"}
TYPE_NAMES = {CardType.FOLLOWER: "follower", CardType.AMULET: "amulet",
              CardType.COUNTDOWN_AMULET: "countdown_amulet", CardType.SPELL: "spell"}


def load(raw_dir: Path, lang: str):
    details, links, specials, tribes = {}, {}, {}, {}
    for path in sorted(raw_dir.glob(f"set_*_{lang}.json")):
        data = json.loads(path.read_text(encoding="utf-8"))["data"]
        if isinstance(data.get("card_details"), dict):
            for detail in data["card_details"].values():
                details[detail["common"]["card_id"]] = detail["common"]
        for key, link in (data.get("cards") or {}).items():
            links[int(key)] = link
        for key, info in (data.get("specific_effect_card_info") or {}).items():
            specials[int(key)] = info
        tribes.update(data.get("tribe_names") or {})
    return details, links, specials, tribes


def keyword_names(skill_text: str) -> list[str]:
    flags = parse_keywords(skill_text)
    return [name for name, flag in KEYWORD_NAMES.items() if flags & flag]


def build(raw_dir: Path) -> list[dict]:
    en, links, specials, tribes = load(raw_dir, "en")
    zh = load(raw_dir, "chs")[0]
    pool = {cid for cid, c in en.items() if c.get("is_include_rotation") and not c.get("is_token")}
    frontier = list(pool)
    while frontier:                      # everything those cards can create, transitively
        for related in (links.get(frontier.pop()) or {}).get("related_card_ids") or ():
            if related in en and related not in pool:
                pool.add(related)
                frontier.append(related)
    records = []
    for cid in sorted(pool):
        c = en[cid]
        skill = c.get("skill_text") or ""
        card_type = CardType(c["type"])
        record = {
            "id": cid, "name": c["name"], "zh": (zh.get(cid) or {}).get("name", ""),
            "craft": c["class"], "type": TYPE_NAMES[card_type], "cost": c["cost"],
            "atk": c["atk"] or 0, "life": c["life"] or 0, "kw": keyword_names(skill),
            "cd": parse_countdown(skill) if card_type == CardType.COUNTDOWN_AMULET else None,
            "traits": [tribes[str(t)] for t in c.get("tribes") or () if str(t) in tribes and t],
            "token": bool(c.get("is_token")), "rot": bool(c.get("is_include_rotation")) and
            not c.get("is_token"), "set": c["card_set_id"], "rarity": c.get("rarity"),
            "related": sorted((links.get(cid) or {}).get("related_card_ids") or ()),
            "ability": has_ability(skill),
        }
        for sid in (links.get(cid) or {}).get("specific_effect_card_ids") or ():
            info = specials.get(sid)
            if not info:
                continue
            kind = SPECIAL_TYPES[info["specific_effect_type"]]
            record[kind] = sid
            records.append({"id": sid, "special": kind, "parent": cid, "name": c["name"],
                            "zh": record["zh"], "craft": c["class"], "cost": info.get("cost") or 0,
                            "cd": parse_countdown(info.get("skill_text") or ""),
                            "ability": has_ability(info.get("skill_text") or "")})
        records.append(record)
    return sorted(records, key=lambda r: r["id"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("svsim/cards/data/rotation.json"))
    args = parser.parse_args()
    records = build(args.raw)
    lines = ",\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in records)
    args.out.write_text("[\n" + lines + "\n]\n", encoding="utf-8")
    specials = sum(1 for r in records if "special" in r)
    print(f"{args.out}: {len(records) - specials} cards, {specials} special forms")


if __name__ == "__main__":
    main()
