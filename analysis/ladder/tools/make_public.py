"""Builds the players' reference files in public/ (Salem's S1: every decklist may go to the players; strategies don't):

    python tools/make_public.py

- public/decklists.md: the deck archive — the seven baseline decks (bot frozen seven), the bot's own 19, the WGP
  Qualifier 2026 pro lists (70) and Premier Series 26-27 rounds 10-11 (84 + 28 of round 11 second half). Each with its class, its deck code (what
  svsim.cards.decks.from_hash reads and what a submission's "deck" takes) and the cards in Chinese. Lists the
  simulator can't play (a card it doesn't have, or one with an ability and no script) are marked.
- public/card-glossary.md: a copy of analysis/card-glossary.md (community nicknames <-> full names, 10-07).
"""
from __future__ import annotations

import shutil
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = LADDER.parents[1]
sys.path[:0] = [str(LADDER), str(ROOT)]

CRAFT_ZH = {1: "精灵", 2: "皇家护卫", 3: "巫师", 4: "龙族", 5: "梦魇", 6: "主教", 7: "超越者"}
SOURCES = [
    ("基线成员的卡组（bot 冻结七副）", ROOT / "analysis/pilot/fields/bot-frozen7.txt",
     "池子开始时的七个基线成员用的就是这七副，打法是默认打法。"),
    ("bot 自己构筑的 19 副", ROOT / "svsim/ui/bot_decks.txt", "bot 自己构筑、自己排名（10-30 定稿），T1 在前。"),
    ("WGP 资格赛 2026（2026-11-14 JST）", LADDER / "decklists/wgpq-2026-11-14.txt",
     "职业选手的卡表，35 人每人 2 套。来源：官方 ps.shadowverse-wb.com 的卡组链接，2026-11-15 抓取。"),
    ("职业联赛 26-27 第 10 节、第 11 节前半", LADDER / "decklists/ps1011-2026-11-11.txt",
     "各队赛前公布的卡表。来源：shadowverse-vision.com/decks，2026-11-15 抓取。"),
    ("职业联赛 26-27 第 11 节后半", LADDER / "decklists/ps11b-2026-11-18.txt",
     "11/18 两场四个队赛前公布的卡表（第 3 期特殊期用的就是这 28 副，special-P3.md）。来源：shadowverse-vision.com/decks，"
     "2026-11-24 抓取。"),
]


def rows(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        parts = line.split("|")
        yield parts[0], parts[1]


def describe(code: str) -> tuple[str, str, str]:
    """(class, cards in Chinese, problem or '')."""
    from ladder.runner import load_deck, unscripted
    try:
        deck = load_deck(code)
    except Exception as e:                                   # a card the simulator doesn't have
        craft = CRAFT_ZH.get(int(code.split(".")[1]), "?") if code.count(".") > 2 else "?"
        return craft, "", f"模拟器读不了：{e}"
    from ladder import base
    craft = CRAFT_ZH.get(int(base.craft_of(deck)), "?")
    n = Counter((c.cost, c.name_zh) for c in deck)
    cards = "、".join(f"{name}×{k}" for (cost, name), k in sorted(n.items()))
    miss = unscripted(deck)
    prob = ""
    if miss:
        from svsim.cards.pool import card
        prob = "有效果没脚本（会按白板打，提交会被拒收）：" + "、".join(sorted({card(i).name_zh for i in miss}))
    if len(deck) != 40:
        prob = (prob + "；" if prob else "") + f"不是 40 张（{len(deck)}）"
    return craft, cards, prob


def decklists() -> str:
    out = ["# 存档卡组清单（给选手）", "",
           "按 Salem 的裁定 S1，下面的卡表都可以随意参考，也可以原样当自己的新卡组交（同一张卡表池子里最多 2 个成员）。"
           "这里只有卡表，没有打法。卡组代码就是提交时 `deck` 字段填的那串（`svsim.cards.decks.from_hash` 能读）。"
           "卡名按费用排。", "",
           "由 tools/make_public.py 从模拟器自己的卡牌数据生成；卡池以模拟器为准（基础卡 + 第 5～10 弹）。", ""]
    for title, path, note in SOURCES:
        items = list(rows(path))
        out += [f"## {title}（{len(items)} 副）", "", note, ""]
        by = {}
        for name, code in items:
            craft, cards, prob = describe(code)
            by.setdefault(craft, []).append((name, code, cards, prob))
        for craft in list(CRAFT_ZH.values()) + ["?"]:
            if craft not in by:
                continue
            out += [f"### {craft}", ""]
            for name, code, cards, prob in by[craft]:
                out.append(f"- **{name}**" + (f"　⚠ {prob}" if prob else ""))
                out.append(f"  - 代码：`{code}`")
                if cards:
                    out.append(f"  - {cards}")
            out.append("")
    return "\n".join(out) + "\n"


def main():
    pub = LADDER / "public"
    (pub / "decklists.md").write_text(decklists(), encoding="utf-8")
    src = ROOT / "analysis/card-glossary.md"
    text = src.read_text(encoding="utf-8")
    head = ("<!-- 原样复制自 analysis/card-glossary.md（2026-10-07 版），由 tools/make_public.py 放进公共目录。"
            "范围只到当时的环境卡；没收录的卡看 decklists.md 里的全名。 -->\n\n")
    (pub / "card-glossary.md").write_text(head + text, encoding="utf-8")
    print("public/decklists.md, public/card-glossary.md")


if __name__ == "__main__":
    main()
