"""Print the cards of one craft with everything needed to script them.

    python -m svsim.tools.card_text --craft forest
    python -m svsim.tools.card_text --craft forest --set 10009 --todo

For each Rotation card (and the cards it generates): id, set, names, type,
cost, stats, keywords, traits, ability text, generated cards, crest / faith /
Accelerate / Crystallize forms, official Q&A, and whether it already has a
script. Reads the local official data (see fetch_cards); card text stays local.
"""
import argparse
import importlib
import json
from pathlib import Path
import re

from svsim.cards.pool import POOL, ROTATION_IDS
from svsim.core.enums import KEYWORD_NAMES, CardType, Craft
from svsim.core.script import has_script

CRAFT_MODULES = ("neutral", "forest", "sword", "rune", "dragon", "abyss", "haven", "portal")
SPECIAL = {1: "CREST", 2: "CRYSTALLIZE", 3: "ACCELERATE", 4: "FAITH"}


def register_all() -> None:
    for name in CRAFT_MODULES:
        try:
            importlib.import_module(f"svsim.cards.{name}")
        except ModuleNotFoundError:
            pass


def clean(text: str) -> str:
    text = re.sub(r"<ev>", "[Evolve-block] ", text or "")
    text = re.sub(r"<sev>", "[Super-Evolve-block] ", text)
    return re.sub(r"<[^>]+>", "", text).replace("\n", " | ").strip()


def load(raw: Path):
    details, specials = {}, {}
    for path in sorted(raw.glob("set_*_en.json")):
        data = json.loads(path.read_text(encoding="utf-8"))["data"]
        if isinstance(data.get("card_details"), dict):
            for d in data["card_details"].values():
                details[d["common"]["card_id"]] = d["common"]
        for key, info in (data.get("specific_effect_card_info") or {}).items():
            specials[int(key)] = info
    return details, specials


def describe(cid: int, details: dict, specials: dict) -> str:
    c, d = POOL[cid], details.get(cid, {})
    status = "DONE" if has_script(cid) else "todo"
    stats = f" {c.atk}/{c.life}" if c.type == CardType.FOLLOWER else ""
    lines = [f"[{cid}] ({status}) {c.name} / {c.name_zh}  set {c.card_set}  "
             f"{c.type.name.lower()} cost {c.cost}{stats}"
             + (f"  keywords: {', '.join(n for n, k in KEYWORD_NAMES.items() if c.keywords & k)}"
                if c.keywords else "")
             + (f"  traits: {', '.join(c.traits)}" if c.traits else "")
             + ("  TOKEN" if c.is_token else "")]
    lines.append(f"    text: {clean(d.get('skill_text'))}")
    for rid in c.related:
        if rid in POOL:
            lines.append(f"    generates [{rid}] {POOL[rid].name} ({'DONE' if has_script(rid) else 'todo'})")
    for special in (c.faith, c.accelerate, c.crystallize):
        if special is not None:
            info = specials.get(special.card_id, {})
            lines.append(f"    {SPECIAL.get(info.get('specific_effect_type'), '?')} [{special.card_id}] "
                         f"cost {special.cost} ({'DONE' if has_script(special.card_id) else 'todo'}): "
                         f"{clean(info.get('skill_text'))}")
    for spec_id, info in specials.items():      # crests are only linked from the special table
        if spec_id // 10 == cid // 10 and info.get("specific_effect_type") == 1:
            lines.append(f"    CREST [{spec_id}] ({'DONE' if has_script(spec_id) else 'todo'}): "
                         f"{clean(info.get('skill_text'))}")
    for q in d.get("questions") or ():
        lines.append(f"    Q&A: {q['question']} -> {q['answer']}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--craft", required=True, choices=[c.name.lower() for c in Craft])
    parser.add_argument("--set", type=int, help="only this card_set_id (e.g. 10009)")
    parser.add_argument("--todo", action="store_true", help="only cards without a script")
    parser.add_argument("--unlimited", action="store_true", help="also list non-Rotation cards")
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    register_all()
    details, specials = load(args.raw)
    craft = Craft[args.craft.upper()]
    cards = sorted((c for c in POOL.values() if c.craft == craft
                    and (args.unlimited or c.card_id in ROTATION_IDS)
                    and c.type not in (CardType.CREST, CardType.FAITH) and c.card_set),
                   key=lambda c: (-c.card_set if c.card_set < 90000 else 0, c.card_id))
    shown = 0
    for c in cards:
        if args.set and c.card_set != args.set:
            continue
        if args.todo and has_script(c.card_id):
            continue
        print(describe(c.card_id, details, specials))
        shown += 1
    print(f"-- {shown} cards")


if __name__ == "__main__":
    main()
