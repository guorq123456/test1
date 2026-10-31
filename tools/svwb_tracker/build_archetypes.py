"""把职业联赛卡表和盲测对照卡表整理成「套路参照表」archetypes.json，供 svwb_tracker 判断对手套路。
只是标签用途：从对手出过的牌猜它是哪个套路。永远不进搜索、自对弈和训练。

    python build_archetypes.py REPO_ROOT > archetypes.json
"""
import collections
import json
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, str(root))
from svsim.cards.deckcode import decode_deck  # noqa: E402

CLS = {1: "精灵", 2: "皇家护卫", 3: "巫师", 4: "龙族", 5: "梦魇", 6: "主教", 7: "超越者"}
# 套路名：按 2026-10-31 的比对报告（shadowverse/blind-test-vs-dfm-2026-10-31.md）和与对照卡表的重合度定
NAMES = {
    "ps/FOREST-RID": "达斯特迪兹精灵", "ps/FOREST-DFM": "达斯特迪兹精灵", "ps/FOREST-MRG": "达斯特迪兹精灵",
    "ps/FOREST-ZETA": "达斯特迪兹精灵", "ps/FOREST-RC": "达斯特迪兹精灵", "ps/FOREST-VL": "达斯特迪兹精灵",
    "ps/SWORD-RID": "连携皇", "ps/SWORD-DFM": "证据连携皇", "ps/SWORD-MRG": "证据连携皇", "ps/SWORD-RC": "证据连携皇",
    "ps/SWORD-VL": "证据连携皇", "ps/SWORD-ZETA": "海贼旗皇",
    "ps/RUNE-RID": "实验体法", "ps/RUNE-DFM": "法术秘术", "ps/RUNE-RC": "法术秘术", "ps/RUNE-VL": "法术秘术",
    "ps/RUNE-LVH": "法术秘术", "ps/RUNE-MRG": "法术林克尔", "ps/RUNE-ZETA": "法术林克尔",
    "ps/DRAGON-RID": "跳费龙", "ps/DRAGON-DFM": "跳费龙", "ps/DRAGON-MRG": "跳费龙", "ps/DRAGON-ZETA": "跳费龙",
    "ps/DRAGON-RC": "跳费龙", "ps/DRAGON-VL": "跳费龙", "ps/DRAGON-LVH": "跳费龙",
    "ps/ABYSS-RID": "中速梦魇", "ps/ABYSS-DFM": "中速梦魇", "ps/ABYSS-MRG": "中速梦魇", "ps/ABYSS-ZETA": "中速梦魇",
    "ps/ABYSS-RC": "中速梦魇", "ps/ABYSS-LVH": "中速梦魇",
    "ps/HAVEN-RID": "兔子主教", "ps/HAVEN-DFM": "兔子主教", "ps/HAVEN-ZETA": "兔子主教", "ps/HAVEN-VL": "兔子主教",
    "ps/HAVEN-LVH": "兔子主教", "ps/HAVEN-MRG": "护符主教", "ps/HAVEN-RC": "护符主教",
    "ps/PORTAL-DFM": "融合超越者", "ps/PORTAL-MRG": "融合超越者", "ps/PORTAL-RC": "融合超越者", "ps/PORTAL-VL": "融合超越者",
    "ps/PORTAL-RID": "疾走造物鱼", "ps/PORTAL-ZETA": "疾走造物鱼", "ps/PORTAL-LVH": "疾走造物鱼",
    "control-FOREST": "达斯特迪兹精灵", "control-SWORD": "连携皇", "control-RUNE": "实验体法", "control-DRAGON": "跳费龙",
    "control-ABYSS": "中速梦魇", "control-HAVEN": "监狱教", "control-PORTAL": "疾走造物鱼",
}
files = [root / "analysis/deckbuild/blind-test/external/ps10-2026-10-31.txt", root / "analysis/deckbuild/blind-test/control.txt"]
decks = []
for f in files:
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        label, code = line.split("|", 1)
        if label not in NAMES:
            continue
        fmt, craft, ids = decode_deck(code)
        decks.append({"label": label, "name": NAMES[label], "cls": CLS[craft], "cards": dict(collections.Counter(str(i) for i in ids))})
json.dump({"note": "套路参照表，只用于给对手套路贴标签", "built": "2026-10-31", "decks": decks}, sys.stdout, ensure_ascii=False, indent=0)
