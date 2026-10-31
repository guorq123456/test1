"""Blind-test metrics 1 and 3 against an external reference (README §指标; the reference stands in for the ladder's
mainstream list of each class): for every group of league5/roster.txt (each group's own top deck per class, the
bot's best per class), the cards it shares with the reference deck of its class (by card name: a reprint is the same
card; a card counts min(copies here, copies there)), and the set-10 cards (card_set 10010) per deck.

    python analysis/deckbuild/blind-test/external/compare.py analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt

Condition of every simulator result elsewhere: 对手卡表已知（牌序、手牌未知）; this file plays no games.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from svsim.cards.pool import POOL  # noqa: E402
from svsim.tools.deckbuild import read_seeds  # noqa: E402

CLASSES = ("FOREST", "SWORD", "RUNE", "DRAGON", "ABYSS", "HAVEN", "PORTAL")
ZH = dict(zip(CLASSES, ("精灵", "皇家护卫", "巫师", "龙族", "梦魇", "主教", "超越者")))


def craft(label: str) -> str:
    return next(c for c in CLASSES if c in label.upper())


def names(ids) -> Counter:
    return Counter(POOL[i].name for i in ids)


def overlap(a: Counter, b: Counter) -> int:
    return sum(min(a[k], b[k]) for k in a)


def main() -> None:
    ref = {craft(l): ids for l, ids in read_seeds(sys.argv[1])}
    roster = read_seeds(str(Path(__file__).resolve().parents[1] / "league5/roster.txt"))
    groups: dict = {}
    for label, ids in roster:
        g = label.split("/", 1)[0]
        groups.setdefault(g, {})[craft(label)] = (label, ids)
    print("指标 1：每个职业和参照卡表共有几张（按卡名，同一张按较少的份数）")
    print("组        " + " ".join(f"{ZH[c]:>5}" for c in CLASSES) + "   平均")
    table = {}
    for g, decks in groups.items():
        row = [overlap(names(decks[c][1]), names(ref[c])) for c in CLASSES]
        table[g] = row
        print(f"{g:8s} " + " ".join(f"{x:6d}" for x in row) + f"   {sum(row) / len(row):5.1f}")
    print("参照自己的新卡（第 10 弹）张数：" + "，".join(f"{ZH[c]} {sum(POOL[i].card_set == 10010 for i in ref[c])}"
                                            for c in CLASSES) +
          f"；平均 {sum(sum(POOL[i].card_set == 10010 for i in ref[c]) for c in CLASSES) / 7:.1f}")
    for g, decks in groups.items():
        n = [sum(POOL[i].card_set == 10010 for i in decks[c][1]) for c in CLASSES]
        print(f"{g:8s} 新卡：" + " ".join(f"{x:3d}" for x in n) + f"   平均 {sum(n) / 7:.1f}")
    if "bot" in table and "control" in table:
        b, c = table["bot"], table["control"]
        print(f"通过线（bot 对对照）：多的职业 {sum(x > y for x, y in zip(b, c))}/7（要 ≥5），"
              f"平均多 {(sum(b) - sum(c)) / 7:+.1f} 张（要 ≥ +3）")
        for g in table:
            if g in ("bot", "control"):
                continue
            r = table[g]
            print(f"  {g}: 对对照多的职业 {sum(x > y for x, y in zip(r, c))}/7，平均多 {(sum(r) - sum(c)) / 7:+.1f}；"
                  f"对 bot 平均多 {(sum(r) - sum(b)) / 7:+.1f}")


if __name__ == "__main__":
    main()
