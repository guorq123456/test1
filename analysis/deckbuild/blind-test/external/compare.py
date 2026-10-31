"""Blind-test metrics 1 and 3 against an external reference (README §指标; the reference stands in for the ladder's
mainstream list of each class): for every group of league5/roster.txt (each group's own top deck per class, the
bot's best per class), the cards it shares with the reference deck of its class (by card name: a reprint is the same
card; a card counts min(copies here, copies there)), and the set-10 cards (card_set 10010) per deck.

With several reference decks in a class (e.g. every team's list of one pro-league round) the table gives the mean
overlap over that class's lists (= expected overlap with a list drawn at random, so a popular archetype weighs more),
then the max (the closest single list), then which list is closest. With one list per class all three agree.

    python analysis/deckbuild/blind-test/external/compare.py analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt
    python analysis/deckbuild/blind-test/external/compare.py analysis/deckbuild/blind-test/external/ps10-2026-10-31.txt

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


def clusters(decks: list) -> list:
    """Single-linkage groups of one class's reference decks: two lists join when they share >= 25 cards."""
    groups = [[d] for d in decks]
    merged = True
    while merged:
        merged = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if any(overlap(names(a[1]), names(b[1])) >= 25 for a in groups[i] for b in groups[j]):
                    groups[i] += groups.pop(j)
                    merged = True
                    break
            if merged:
                break
    return sorted(groups, key=len, reverse=True)


def table_for(groups: dict, score) -> dict:
    return {g: [score(c, decks[c][1]) for c in CLASSES] for g, decks in groups.items()}


def print_table(title: str, table: dict) -> None:
    print(title)
    print("组        " + " ".join(f"{ZH[c]:>5}" for c in CLASSES) + "   平均")
    for g, row in table.items():
        print(f"{g:8s} " + " ".join(f"{x:6.1f}" for x in row) + f"   {sum(row) / len(row):5.1f}")


def verdict(table: dict) -> None:
    if "bot" not in table or "control" not in table:
        return
    b, c = table["bot"], table["control"]
    print(f"通过线（bot 对对照）：多的职业 {sum(x > y for x, y in zip(b, c))}/7（要 ≥5），"
          f"平均多 {(sum(b) - sum(c)) / 7:+.1f} 张（要 ≥ +3）")
    for g in table:
        if g in ("bot", "control"):
            continue
        r = table[g]
        print(f"  {g}: 对对照多的职业 {sum(x > y for x, y in zip(r, c))}/7，平均多 {(sum(r) - sum(c)) / 7:+.1f}；"
              f"对 bot 平均多 {(sum(r) - sum(b)) / 7:+.1f}")


def main() -> None:
    refs: dict = {}
    for l, ids in read_seeds(sys.argv[1]):
        refs.setdefault(craft(l), []).append((l, ids))
    roster = read_seeds(str(Path(__file__).resolve().parents[1] / "league5/roster.txt"))
    groups: dict = {}
    for label, ids in roster:
        g = label.split("/", 1)[0]
        groups.setdefault(g, {})[craft(label)] = (label, ids)
    many = any(len(v) > 1 for v in refs.values())
    print(f"参照卡表：{sum(len(v) for v in refs.values())} 副（" +
          "，".join(f"{ZH[c]} {len(refs.get(c, []))}" for c in CLASSES) + "）")

    mean = table_for(groups, lambda c, ids: sum(overlap(names(ids), names(r)) for _, r in refs[c]) / len(refs[c]))
    print_table("指标 1：每个职业和参照卡表共有几张（按卡名，同一张按较少的份数）" +
                ("；同职业有几副参照时取平均" if many else ""), mean)
    verdict(mean)
    if many:
        best = table_for(groups, lambda c, ids: max(overlap(names(ids), names(r)) for _, r in refs[c]))
        print_table("\n同上，但取同职业里最接近的那一副参照", best)
        verdict(best)
        print("\n每组每个职业最接近哪一副参照（共有张数）：")
        for g, decks in groups.items():
            cells = []
            for c in CLASSES:
                n, l = max((overlap(names(decks[c][1]), names(r)), l) for l, r in refs[c])
                cells.append(f"{ZH[c]} {l.split('-')[-1]} {n}")
            print(f"{g:8s} " + "；".join(cells))
        print("\n参照卡表按相似分堆（两副共有 ≥25 张就算一堆，传递）：")
        for c in CLASSES:
            cl = clusters(refs[c])
            print(f"{ZH[c]}：" + " | ".join(
                f"{len(k)} 副 [" + " ".join(l.split('-')[-1] for l, _ in k) + "]" for k in cl))

    newc = {c: [sum(POOL[i].card_set == 10010 for i in r) for _, r in refs[c]] for c in CLASSES}
    print("\n参照自己的新卡（第 10 弹）张数（同职业取平均）：" +
          "，".join(f"{ZH[c]} {sum(v) / len(v):.1f}" for c, v in newc.items()) +
          f"；七个职业平均 {sum(sum(v) / len(v) for v in newc.values()) / 7:.1f}")
    for g, decks in groups.items():
        n = [sum(POOL[i].card_set == 10010 for i in decks[c][1]) for c in CLASSES]
        print(f"{g:8s} 新卡：" + " ".join(f"{x:3d}" for x in n) + f"   平均 {sum(n) / 7:.1f}")


if __name__ == "__main__":
    main()
