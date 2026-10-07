"""Salem's held turns one by one: what could be evolved, what was kept, what came of it.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> analysis/mirror-regression/salem_games.json \
        analysis/mirror-regression/evolve_probes.json [--md OUT.md] [--results v2=FILE ...]

The method rule, in Salem's words (2026-10-07): 「噪声行号我不回——因为我也无法判断是否为噪声，复杂局面下
不进化和进化往往都是从大量变量下得出的结论，不能简单下定论」. No single turn is judged; only whole cells
are read. So every held turn counts. The exception is a turn where Erntz came down unevolved
(erntz_unevolved in the probes). Salem ruled that another way to use Erntz, as strong as evolving it,
and not a held point; it keeps its row in the table, marked 不计入, and is left out of the baseline.
Sensitivity check only, never used for conclusions or acceptance: the turns whose first evolution in
the next two own turns was a follower that had already lived through an opponent's turn (its payoff
needed the opponent to leave it standing), listed after the table with the baseline without them.
Reported: the Salem baseline (hold rate overall and in the two acceptance cells, "收益牌在手、本回合
够不着" and "只能普通进化"), and each --results file's evolve_hold pass rate (and the erntz_unevolved
probe's, for a run of it).
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mirror-regression"))
from evolve_targets import PAYOFF, name, salem_turns, turn_row  # noqa: E402
from glossary import common, label_first  # noqa: E402
from svsim.core.actions import Evolve  # noqa: E402
from svsim.core.engine import apply, legal_actions  # noqa: E402

ERNTZ = "约束的《正义》·伊兰翠"
SAGATSUMATSU = "断头的斩姬·相枛津"
HEADER = """# Salem 能进化却没进化的 36 个回合

这些回合是 evolve_hold 探针的来源：bot 在同一局面下也不进化，才算通过。

**方法规矩**（Salem 原话，2026-10-07）：「噪声行号我不回——因为我也无法判断是否为噪声，复杂局面下不进化和进化往往都是从大量变量下得出的结论，不能简单下定论」。所以不对单个局面的进化与否下定论，只看整格统计：下面每一行都计入，表里不写对单个回合的判断。

**正义不进化面**：Salem 裁定（2026-10-07）"正义不主动进化在多数情况下是另一种用法，和进化一样强力"。所以正义当回合打出、没进化的 12 行标"不计入"，不算留点，另做一个探针（erntz_unevolved：bot 在同一局面也出正义、不进化它）。evolve_hold 的样本是 36 − 12 = 24 行，全部计入。行号不变。

"""


def short_name(n):
    """How Salem names the card (the glossary's common name); its first mention in each row gets the cost and
    stats (glossary.label_first)."""
    return common(n)


def counted(names):
    c = Counter(short_name(n) for n in names)
    return "、".join(f"{n}×{k}" if k > 1 else n for n, k in c.items()) or "无"


def end_state(turn):
    st = turn[-1][0].clone()
    if type(turn[-1][1]).__name__ != "EndTurn":
        apply(st, turn[-1][1])
    return st


def review(games, probe, cache):
    gid = probe["game"]
    if gid not in cache:
        cache[gid] = salem_turns(games[gid])
    turns = cache[gid]
    starts = [s for s, _ in turns]
    k = starts.index(probe["at"])
    turn = turns[k][1]
    st0 = turn[0][0]
    field0 = {c.uid for c in st0.players[0].followers}
    targets, supers = {}, False
    for s, _ in turn:
        for a in legal_actions(s):
            if isinstance(a, Evolve):
                c = s.on_field(a.uid)
                targets[a.uid] = f"{short_name(name(c))}（{'场上' if a.uid in field0 else '本回合出'}）"
                supers |= a.super_
    end = end_state(turn)
    me = end.players[0]
    field_end = {c.uid: name(c) for c in me.followers}
    hand_end = {c.uid: name(c) for c in me.hand}
    kept = f"进化点 {me.ep}、超进化点 {me.sep}；场上没进化：{counted(n for u, n in field_end.items() if not end.on_field(u).evolved)}" \
           f"；手里的随从：{counted(c.defn.name_zh or c.defn.name for c in me.hand if c.defn.is_follower)}"
    erntz_plain = any(name(c) == ERNTZ and not c.evolved and c.uid not in field0 for c in me.followers)
    if erntz_plain:
        kept += "；正义用的是不进化那面（回合结束打两个随从各 8、回 8 血）"
    later, first = [], None
    if k + 1 < len(turns):
        nxt = turns[k + 1][1][0][0]
        alive = {c.uid for c in nxt.players[0].followers}
        gone = [n for u, n in field_end.items() if u not in alive]
        later.append(f"对手回合解掉 {counted(gone)}" if gone else "对手回合没解掉 Salem 场上的随从" if field_end
                     else "Salem 场上本来就空")
        for j, (_, t2) in enumerate(turns[k + 1:k + 3]):
            evo = []
            standing = {c.uid for c in t2[0][0].players[0].followers}     # on the field when that turn began
            for s, a in t2:
                if isinstance(a, Evolve):
                    c = s.on_field(a.uid)
                    src = "这回合场上那张" if a.uid in field_end else "这回合手里那张" if a.uid in hand_end else "后来抽到或新上场的"
                    if a.uid in standing and a.uid not in field_end:
                        src += "，前一回合已出"
                    evo.append(f"{'超进化' if a.super_ else '进化'} {short_name(name(c))}（{src}）")
                    if first is None:
                        first = (src, name(c), a.uid in standing)
            later.append(f"{'下回合' if j == 0 else '再下回合'}：{'、'.join(evo) if evo else '没进化'}")
    else:
        later.append("对局在对手回合结束")
    # sensitivity check only: the first evolution after the hold went to a follower that had lived through an
    # opponent's turn (on the field at the end of the hold turn, or played the turn after and evolved the turn
    # after that), so what the hold paid for needed the opponent to leave it standing
    survivor = first is not None and (first[0] == "这回合场上那张" or first[2])
    ctx = probe["context"]
    s754 = {"hand": any(name(c) == SAGATSUMATSU for c in st0.players[0].hand),
            "field": any(name(c) == SAGATSUMATSU for c in st0.players[0].followers)}
    return {"id": probe["id"], "game": gid, "own_turn": ctx["own_turn"], "first": ctx["first"], "s754": s754,
            "hp": f"{ctx['hp']}/{ctx['opp_hp']}", "targets": "、".join(sorted(set(targets.values()))), "survivor": survivor,
            "super": supers, "kept": kept, "later": "；".join(later),
            "erntz_plain": erntz_plain, "row": turn_row(turn)}


def old_id(i):
    """The id an erntz_unevolved turn had while it was an evolve_hold (results and marks made before the split)."""
    return i.replace("-erntz_unevolved", "-evolve_hold")


def rates(rows, drop):
    keep = [r for r in rows if r["id"] not in drop]
    out = {}
    held = [r for r in keep if r["row"]["held"]]
    out["总体"] = (len(held), len(keep))
    for key, sel in (("收益牌在手、本回合够不着", lambda x: x["class"] == "收益牌在手、本回合够不着"),
                     ("只能普通进化", lambda x: x["normal_only"])):
        sub = [r for r in keep if sel(r["row"])]
        out[key] = (sum(r["row"]["held"] for r in sub), len(sub))
    return out


def main():
    args = sys.argv
    games = json.load(open(args[1], encoding="utf-8"))["records"]
    probes = json.load(open(args[2], encoding="utf-8"))["positions"]
    cache = {}
    rows = [review(games, p, cache) for p in probes]
    # the table keeps its 36 rows (Salem marks them by row number): the evolve_hold turns and the turns where
    # Erntz came down unevolved, which Salem ruled another way to use it, not a held point (erntz_unevolved)
    holds = [r for r in rows if r["id"].endswith(("evolve_hold", "erntz_unevolved"))]
    plain = {r["id"] for r in holds if r["id"].endswith("erntz_unevolved")}
    for r in holds:
        r["mark"] = "不计入：正义不进化面（Salem 裁定：和进化一样强力的另一种用法，不是留点）" if r["id"] in plain else "计入"
    survivors = [i for i, r in enumerate(holds, 1) if r["survivor"] and r["id"] not in plain]
    if "--md" in args:
        s7 = {"hold": holds, "use": [r for r in rows if r["id"].endswith("evolve_use")]}
        count = lambda cat, k: sum(r["s754"][k] for r in s7[cat])
        either = lambda cat: sum(r["s754"]["hand"] or r["s754"]["field"] for r in s7[cat])
        line754 = (f"**口人魔**（即 754）：没进化的 {len(s7['hold'])} 个回合里，回合开头手里有它的 {count('hold', 'hand')} 个、"
                   f"场上有它的 {count('hold', 'field')} 个（手里或场上 {either('hold')} 个）；进化了的 "
                   f"{len(s7['use'])} 个回合里分别是 {count('use', 'hand')}、{count('use', 'field')}"
                   f"（{either('use')}）。它已加进收益牌清单。\n\n")
        body = label_first(HEADER + line754)
        body += ("| # | 对局 | 回合（先/后手，血 我/对） | 当时能进化的目标 | Salem 留下的 | 之后两回合 | 标记 |\n"
                 "|---|---|---|---|---|---|---|\n")
        for i, r in enumerate(holds, 1):
            body += label_first(f"| {i} | {r['game']} | 第 {r['own_turn']} 回合（{'先' if r['first'] else '后'}手，{r['hp']}） | "
                     f"{r['targets']}{'；能超进化' if r['super'] else '；只能普通进化'} | {r['kept']} | {r['later']} | "
                     f"{r['mark']} |\n")
        t_all, t_s = rates(rows, plain), rates(rows, plain | {holds[i - 1]["id"] for i in survivors})
        pct = lambda t, k: f"{t[k][0]}/{t[k][1]}（{t[k][0] / max(t[k][1], 1):.0%}）"
        body += ("\n**附：敏感性对照**（不用于结论和验收）。之后第一次进化的那张，进化前已经扛过对手一个回合的行："
                 + ("、".join(f"第 {i} 行" for i in survivors) or "无")
                 + f"。24 行全量：忍住率总体 {pct(t_all, '总体')}、只能普通进化 {pct(t_all, '只能普通进化')}、"
                 f"收益牌在手够不着 {pct(t_all, '收益牌在手、本回合够不着')}；去掉这些行：总体 {pct(t_s, '总体')}、"
                 f"只能普通进化 {pct(t_s, '只能普通进化')}、收益牌在手够不着 {pct(t_s, '收益牌在手、本回合够不着')}。\n")
        with open(args[args.index("--md") + 1], "w", encoding="utf-8") as f:
            f.write(body)
    print(f"evolve_hold 样本 {len(holds) - len(plain)} 条全部计入；正义不进化面 {len(plain)} 条不计入")
    sens = {holds[i - 1]["id"] for i in survivors}
    print(f"敏感性对照（不用于结论）：之后进化的那张已扛过对手一个回合的行 {survivors}")
    drops = (("旧：含正义不进化面", set()), ("(b) 基线：24 条全量", plain), ("敏感性：再去掉上面几行", sens | plain))
    print("\nSalem 基线（能进化的回合里忍住的比例）：")
    tables = [(title, rates(rows, d)) for title, d in drops]
    for key in tables[0][1]:
        print(f"  {key:<14} " + "  ".join(f"{title} {t[key][0]}/{t[key][1]}（{t[key][0] / max(t[key][1], 1):.0%}）"
                                         for title, t in tables))
    for i, x in enumerate(args):
        if x != "--results":
            continue
        label, path = args[i + 1].split("=", 1)
        res = {}
        for line in open(path, encoding="utf-8"):
            m = re.match(r"(\d+-t\d+-\S+)\s+(\d+)/(\d+)$", line.strip())    # probe rows, not the totals by category
            if m:
                res[m.group(1)] = (int(m.group(2)), int(m.group(3)))
        if any(j.endswith("erntz_unevolved") for j in res):     # a run of the erntz_unevolved probe itself
            e = [j for j in res if j.endswith("erntz_unevolved")]
            ok, n = sum(res[j][0] for j in e), sum(res[j][1] for j in e)
            print(f"\n{label} 的 erntz_unevolved 通过率（也出正义、也不进化它）：{ok}/{n}（{ok / max(n, 1):.0%}）")
            continue
        # the evolve_hold check (no evolution) of each held turn; the Erntz turns were run under their old id
        got = {r["id"]: res.get(r["id"]) or res.get(old_id(r["id"])) for r in holds}
        print(f"\n{label} 的 evolve_hold 通过率（不进化）：")
        for key, sel in (("总体", lambda x: True), ("收益牌在手、本回合够不着", lambda x: x["class"] == "收益牌在手、本回合够不着"),
                         ("只能普通进化", lambda x: x["normal_only"])):
            cells = []
            for title, drop in drops:
                ids = [r["id"] for r in holds if r["id"] not in drop and sel(r["row"]) and got[r["id"]]]
                ok, n = sum(got[j][0] for j in ids), sum(got[j][1] for j in ids)
                cells.append(f"{title} {ok}/{n}（{ok / max(n, 1):.0%}）")
            print(f"  {key:<14} " + "  ".join(cells))
        use = [j for j in res if j.endswith("evolve_use")]
        print(f"  evolve_use（不变）{sum(res[j][0] for j in use)}/{sum(res[j][1] for j in use)}")

if __name__ == "__main__":
    main()
