"""Item 6b: the divergence table for Salem from realgame_6b.py's output (one json line per position).

    python analysis/process/realgame_6b_table.py RESULTS.jsonl OUT.md
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from analysis.process.realgame_6b import key

TABLE = {}
for f in sorted((ROOT / "svsim/cards/data").glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    for c in (d if isinstance(d, list) else d.values()):
        TABLE[c["id"]] = c


def nm(c):
    b = c - 2 if str(c).endswith("2") else c
    x = TABLE.get(c) or TABLE.get(b) or {}
    return x.get("zh", str(c))


def line(ls):
    parts = [("进化 " if k == "进化" else "超进化 " if k == "超进化" else "") + nm(c) for k, c in ls if k != "攻击" and c is not None]
    return "、".join(parts) or "什么都不打"


def unit(c, a, l, e):
    return f"{nm(c)}" + (f" {a}/{l}" if a or l else "") + ("（已进化）" if e else "")


def row(x, verdict=True):
    risky = any(a or l for c, a, l, e in x["opp_board"])
    cells = [f"第{x['game']}局 {x['deck']} 对 {x['opp']}", str(x["turn"]), "先手" if x["first"] else "后手",
             f"{x['pp']}/{x['max_pp']}", "、".join(nm(c) for c in x["hand"]),
             "、".join(unit(*u) for u in x["my_board"]) or "空",
             ("、".join(unit(*u) for u in x["opp_board"]) or "空") + ("（可能有交换）" if risky else ""),
             line(x["salem"]), line(x["bot"])]
    return "| " + " | ".join(cells + ([" "] if verdict else [])) + " |"


HEAD = ("| 局 | 你的第几回合 | 先后 | PP | 手牌（这回合第一手之前） | 我方场上 | 对手场上（假设都还活着） | 你实际打的 | bot 打的 |")


def clean(x):
    return not (x["notes"].get("forced_pp") or x["notes"].get("unplayable") or x["notes"].get("evolve_skipped"))


def calm(x):
    return clean(x) and not any(a or l for c, a, l, e in x["opp_board"])


def main(src, out):
    rows = [json.loads(x) for x in open(src, encoding="utf-8")]
    done = [x for x in rows if "bot" in x]
    div = [x for x in done if key(x["salem"]) != key(x["bot"])]
    t1 = [x for x in div if calm(x) and x["turn"] == 1]
    short = [x for x in div if calm(x) and x["turn"] >= 2]
    rest = [x for x in div if x not in t1 and x not in short]
    parts = ["## 一、第 1 回合（对手场上没有随从）", "",
             HEAD + " 你的评语 |", "|---|---|---|---|---|---|---|---|---|---|"] + [row(x) for x in t1]
    parts += ["", "## 二、第 2 到第 5 回合里还原得最干净的（重演没有出偏差、对手场上没有随从）", "",
              HEAD + " 你的评语 |", "|---|---|---|---|---|---|---|---|---|---|"] + [row(x) for x in short]
    parts += ["", "## 三、其余的分歧（对手场上有随从，或重演时出了偏差，局面可能和真实的不一样；只供参考）", "",
              HEAD, "|---|---|---|---|---|---|---|---|---|"] + [row(x, False) for x in rest]
    Path(out).write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"{len(div)} 处分歧：第 1 回合 {len(t1)}，干净的 {len(short)}，其余 {len(rest)}；写入 {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
