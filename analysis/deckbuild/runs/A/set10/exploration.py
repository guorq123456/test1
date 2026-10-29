"""Search A: does it try set-10 cards, and how do the variants that do fare? No new games.

条件：对手卡表已知（牌序、手牌未知）

The variants of each class step are replayed offline: every code version A ran on (b5985e4 … 37f84510) seeds
the step's rng as Random(f"{seed}:{round}:{class_index}") and draws the 8 variants from the incumbent first, so
variant(inc, craft, rng) x 8 gives them back. The incumbent is the class's list in the state.json saved at the end
of the previous round (slot order matters). Checks: each replayed variant's deck code equals the deck field of its
deal records (written from r2:RUNE on), and each step's halving winner (changes.jsonl out/in) is one of them.

Writes results.md and variants.jsonl next to this file. Run from the deck-search worktree (it needs svsim.tools.deckbuild):
  PYTHONPATH=<worktree> python -B analysis/deckbuild/runs/A/set10/exploration.py <worktree>/runs/deckbuild-A/deals.jsonl
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from svsim.tools.deckbuild import CLASSES, POOL, deck_hash, legal_cards, variant

HERE = Path(__file__).resolve().parent
RUN = HERE.parent                                        # analysis/deckbuild/runs/A
SEED = 84801000
NEW_SET = "10010"
ROUNDS = (1, 2, 3)
SIMS = 400                                               # random variants per step for the expected share


def is_new(i: int) -> bool:
    return str(POOL[i].card_set) == NEW_SET


def swapped_in(inc: list, var: list) -> list:
    return sorted((Counter(var) - Counter(inc)).elements())


def mean_se(x: list) -> tuple:
    n = len(x)
    if n == 0:
        return 0, float("nan"), float("nan")
    m = sum(x) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1)) if n > 1 else float("nan")
    return n, m, sd / math.sqrt(n)


def main(deals_path: str) -> None:
    fields = {r: json.loads((RUN / f"round{r - 1}" / "state.json").read_text())["field"] for r in ROUNDS}
    changes = {}
    for r in ROUNDS:
        for line in (RUN / f"round{r}" / "changes.jsonl").read_text().splitlines():
            d = json.loads(line)
            changes[(d["round"], d["class"])] = d
    # deal records, one per (tag, key, seed): resumed steps wrote some twice, with the same result
    recs: dict = {}
    for line in open(deals_path, encoding="utf-8"):
        d = json.loads(line)
        rnd = d["tag"].split(":")[0]
        if rnd in {f"r{r}" for r in ROUNDS}:
            recs[(d["tag"], d["key"], d["seed"])] = d

    rows, checks = [], Counter()
    for r in ROUNDS:
        for ci, craft in enumerate(CLASSES):
            name = craft.name
            inc = fields[r][name]
            rng = random.Random(f"{SEED}:{r}:{ci}")
            variants = {f"v{j}": variant(inc, craft, rng) for j in range(8)}
            tag = f"r{r}:{name}"
            # check 1: deck codes, where the records carry them
            for k, ids in variants.items():
                codes = {d.get("deck") for (t, kk, _), d in recs.items() if t == f"{tag}:s0" and kk == k}
                codes.discard(None)
                if codes:
                    checks["deck code match" if codes == {deck_hash(ids)} else "deck code MISMATCH"] += 1
            # check 2: the halving winner's swap is one of the replayed variants
            ch = changes[(r, name)]
            want = (sorted(ch["out"]), sorted(ch["in"]))
            got = [k for k, ids in variants.items()
                   if (sorted((Counter(inc) - Counter(ids)).elements()), swapped_in(inc, ids)) == want]
            checks["winner found" if got else "winner NOT FOUND"] += 1
            winner = got[0] if len(got) == 1 else None
            # stage-by-stage paired differences against the incumbent
            for k, ids in variants.items():
                diffs, reached = {}, 0
                for stage in range(3):
                    st = f"{tag}:s{stage}"
                    seeds = sorted(s for (t, kk, s) in recs if t == st and kk == k)
                    if not seeds:
                        break
                    reached = stage
                    diffs[stage] = [sum(recs[(st, k, s)]["points"]) / 2 - sum(recs[(st, "incumbent", s)]["points"]) / 2
                                    for s in seeds]
                new_in = [i for i in swapped_in(inc, ids) if is_new(i)]
                rows.append({"round": r, "class": name, "key": k, "swaps": len(swapped_in(inc, ids)),
                             "new_in": len(new_in), "stage0": diffs.get(0, []), "reached": reached,
                             "winner": k == winner, "verdict": ch["verdict"] if k == winner else None})
            # expected share of variants with a set-10 card, from the same incumbent and the same variant()
            sim = random.Random(f"sim:{r}:{ci}")
            hits = sum(any(is_new(i) for i in swapped_in(inc, variant(inc, craft, sim))) for _ in range(SIMS))
            rows[-1]["expected_share"] = hits / SIMS
            rows[-1]["pool_share"] = sum(is_new(c.card_id) for c in legal_cards(craft)) / len(legal_cards(craft))

    out = []
    p = out.append
    p("# 搜索 A：变体试没试第 10 弹的卡（不打新对局）")
    p("")
    p("条件：对手卡表已知（牌序、手牌未知）")
    p("")
    p(f"重放核对：{dict(checks)}")
    p("")
    # (a)
    p("## (a) 换上至少一张第 10 弹卡的变体占比")
    p("")
    p("| 轮 | 变体 | 含第 10 弹 | 占比 | 同样的 variant() 随机抽的期望占比 |")
    p("|---|---|---|---|---|")
    for r in ROUNDS:
        rr = [x for x in rows if x["round"] == r]
        exp = [x["expected_share"] for x in rr if "expected_share" in x]
        hit = sum(x["new_in"] > 0 for x in rr)
        p(f"| {r} | {len(rr)} | {hit} | {hit / len(rr):.1%} | {sum(exp) / len(exp):.1%} |")
    allr = rows
    exp = [x["expected_share"] for x in allr if "expected_share" in x]
    hit = sum(x["new_in"] > 0 for x in allr)
    p(f"| 合计 | {len(allr)} | {hit} | {hit / len(allr):.1%} | {sum(exp) / len(exp):.1%} |")
    p("")
    p("各职业可选卡池里第 10 弹卡的占比（本职业 + 中立、有脚本、非衍生）：")
    for ci, craft in enumerate(CLASSES):
        ps = [x["pool_share"] for x in rows if x["class"] == craft.name and "pool_share" in x]
        p(f"- {craft.name}: {ps[0]:.1%}")
    p("")
    # (b)
    p("## (b) 减半第 0 段（所有变体同一批 28 个发牌）对现任的配对差")
    p("")
    p("每个变体先求 28 个发牌的平均差，再按变体平均；标准误按变体之间的差异算。")
    p("")
    p("| 分组 | 变体数 | 平均配对差 | 标准误 |")
    p("|---|---|---|---|")

    def line(label, sel):
        n, m, se = mean_se([sum(x["stage0"]) / len(x["stage0"]) for x in sel if x["stage0"]])
        p(f"| {label} | {n} | {m:+.1%} | {se:.1%} |")
    line("含第 10 弹", [x for x in rows if x["new_in"] > 0])
    line("不含", [x for x in rows if x["new_in"] == 0])
    for k in (1, 2, 3):
        line(f"换 {k} 张，含第 10 弹", [x for x in rows if x["swaps"] == k and x["new_in"] > 0])
        line(f"换 {k} 张，不含", [x for x in rows if x["swaps"] == k and x["new_in"] == 0])
    # difference of the two groups, stratified by number of swaps (weights = harmonic sizes)
    num = den = var = 0.0
    for k in (1, 2, 3):
        a = [sum(x["stage0"]) / len(x["stage0"]) for x in rows if x["swaps"] == k and x["new_in"] > 0 and x["stage0"]]
        b = [sum(x["stage0"]) / len(x["stage0"]) for x in rows if x["swaps"] == k and x["new_in"] == 0 and x["stage0"]]
        if len(a) > 1 and len(b) > 1:
            (na, ma, sa), (nb, mb, sb) = mean_se(a), mean_se(b)
            w = na * nb / (na + nb)
            num += w * (ma - mb)
            den += w
            var += w * w * (sa * sa + sb * sb)
    if den:
        p("")
        p(f"按换卡张数分层后的差（含 − 不含）：{num / den:+.1%} ± {math.sqrt(var) / den:.1%}")
    p("")
    # (c)
    p("## (c) 含第 10 弹卡的变体走到哪一步")
    p("")
    new = [x for x in rows if x["new_in"] > 0]
    p(f"- 含第 10 弹卡的变体 {len(new)} 个：进第 1 段 {sum(x['reached'] >= 1 for x in new)} 个，"
      f"进第 2 段 {sum(x['reached'] >= 2 for x in new)} 个，成为减半胜者 {sum(x['winner'] for x in new)} 个。")
    old = [x for x in rows if x["new_in"] == 0]
    p(f"- 对照：不含的 {len(old)} 个：进第 1 段 {sum(x['reached'] >= 1 for x in old)} 个，"
      f"进第 2 段 {sum(x['reached'] >= 2 for x in old)} 个，成为减半胜者 {sum(x['winner'] for x in old)} 个。")
    p("- 含第 10 弹卡的减半胜者：")
    for x in new:
        if x["winner"]:
            ch = changes[(x["round"], x["class"])]
            names = "、".join(POOL[i].name_zh or POOL[i].name for i in ch["in"])
            extra = f"，复核 {ch['confirm_diff']:+.1%} ± {ch['confirm_se']:.1%}" if "confirm_diff" in ch else ""
            p(f"  - 第 {x['round']} 轮 {x['class']}：换上 {names}；{x['verdict']}{extra}")
    conf = [(changes[(x["round"], x["class"])], x["new_in"] > 0) for x in rows
            if x["winner"] and "confirm_diff" in changes[(x["round"], x["class"])]]
    for flag, label in ((True, "含第 10 弹"), (False, "不含")):
        sel = [c for c, f in conf if f == flag]
        acc = sum(c["verdict"].startswith("accepted") for c in sel)
        p(f"- 进了复核的减半胜者（{label}）：{len(sel)} 个，接受 {acc} 个；"
          + "、".join(f"第 {c['round']} 轮 {c['class']} {c['verdict']}" for c in sel))
    text = "\n".join(out) + "\n"
    (HERE / "results.md").write_text(text, encoding="utf-8")
    (HERE / "variants.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows), encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main(sys.argv[1])
