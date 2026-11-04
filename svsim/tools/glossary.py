"""Card names the way the player reads them: the community name and the cost and stats.

    python -m svsim.tools.glossary 10544110 ...       # print the names of these card ids

analysis/card-glossary.md (kept by the architecture session's naming thread, copied here unchanged)
lists for each card its common name (a community nickname where one is known, else the part of the
official name after "·") and its cost and stats. Everything written for the player names a card
`common(defn)`, e.g. "口人魔（7费 5/4）"; code, card ids and internal tables keep the official names.
A card the glossary doesn't list gets the same form from its own data.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

GLOSSARY = Path(__file__).resolve().parents[2] / "analysis" / "card-glossary.md"
_ROW = re.compile(r"^\|\s*\*\*(?P<common>[^*]+)\*\*\s*\|\s*(?P<stats>[^|]+?)\s*\|\s*(?P<full>[^|]+?)\s*\|")
_NAMES: dict | None = None


def names(path: Path = GLOSSARY) -> dict[str, tuple[str, str]]:
    """{official Chinese name: (common name, cost and stats)} from the glossary ({} without the file)."""
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            m = _ROW.match(line)
            if m:
                out[m["full"]] = (m["common"].strip(), m["stats"])
    return out


def stats(defn) -> str:
    """"7费 5/4" for a follower, "2费 法术" and the like for the rest (the glossary's column)."""
    from svsim.core.enums import CardType
    if defn.is_follower:
        return f"{defn.cost}费 {defn.atk}/{defn.life}"
    kind = {CardType.SPELL: "法术", CardType.AMULET: "倒数护符" if defn.countdown else "护符"}.get(defn.type, "")
    return f"{defn.cost}费 {kind or defn.type.name.lower()}"


def common(defn) -> str:
    """The player's name for a card: "常用名（费用身材）"."""
    global _NAMES
    if _NAMES is None:
        _NAMES = names()
    full = defn.name_zh or defn.name
    if full in _NAMES:
        name, cost = _NAMES[full]
    else:
        name, cost = full.split("·")[-1].strip(), stats(defn)
    return f"{name}（{cost}）"


def main() -> None:
    from svsim.cards.pool import POOL
    for arg in sys.argv[1:]:
        d = POOL.get(int(arg))
        print(arg, common(d) if d is not None else "?")


if __name__ == "__main__":
    main()
