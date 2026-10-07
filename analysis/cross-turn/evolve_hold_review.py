"""Salem's evolve_hold turns one by one: what could be evolved, what was kept, what came of it; noise marked.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> analysis/mirror-regression/salem_games.json \
        analysis/mirror-regression/evolve_probes.json [--md OUT.md] [--marks OUT.json] \
        [--use-marks MARKS.json] [--results v2=FILE ...]

Salem on the holds (2026-10-07, through the architecture thread): some are noise. Holding Erntz on
the field unevolved to evolve it next turn only works because the web bot did not answer it; a
normal opponent never lets it live to the next turn. The same logic for every hold: if what the hold
paid for only came about because the opponent did not remove a follower already on Salem's field,
the hold is marked "疑似噪声" (suspected noise). By the first evolution in Salem's next two own
turns:
- it evolved a follower that was on Salem's field at the end of the hold turn, or one played on the
  turn after and evolved the turn after that (either way it lived through an opponent's turn): 疑似噪声;
- it evolved a card that was in Salem's hand at the end of the hold turn, on the turn it was played:
  保留 (kept for a card in hand);
- it evolved a card drawn or summoned later, on the turn it was played: 保留;
- no evolution in the next two own turns: 看不出 (counted as kept; for Salem to look at).
The marks are written to --marks; Salem's corrections go back in through --use-marks. Reported: the
Salem baseline (hold rate overall and in the two acceptance cells, "收益牌在手、本回合够不着" and
"只能普通进化") and each --results file's evolve_hold pass rate, with every turn and after dropping
the noise.
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

这些回合是 evolve_hold 探针的来源：bot 在同一局面下也不进化，才算通过。表里的"标记"是按一条规则自动打的，请 Salem 直接改。

**规则**：看之后两个自己的回合里第一次进化的是哪张。
- 那张在进化前已经在场、扛过了对手一个回合（例如"正义先不进化、下回合再进化"），记**疑似噪声**：要对手没解掉它才兑现，正常对手不会让它活下来。
- 那张是从手里打出、当回合就进化的，记**保留**。
- 之后两回合没进化，记**看不出**。

**怎么改**：觉得是噪声的行，把标记改成"噪声"或直接划掉；觉得不是噪声的，改成"保留"。理由写一句就够了。

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
    if first is None:
        mark, why = "看不出", "之后两回合没进化"
    elif first[0] == "这回合场上那张":
        mark = "疑似噪声"
        why = "正义先不进化、下回合再进化" if first[1] == ERNTZ else \
            f"下回合进化的是场上那张 {short_name(first[1])}，要对手没解掉它才兑现"
    elif first[2]:
        mark = "疑似噪声"
        why = f"进化的 {short_name(first[1])} 是前一回合出的，要对手没解掉它才兑现"
    elif first[0] == "这回合手里那张":
        mark, why = "保留", f"留给手里的 {short_name(first[1])}"
    else:
        mark, why = "保留", f"之后进化的是后来抽到或新上场的 {short_name(first[1])}"
    ctx = probe["context"]
    s754 = {"hand": any(name(c) == SAGATSUMATSU for c in st0.players[0].hand),
            "field": any(name(c) == SAGATSUMATSU for c in st0.players[0].followers)}
    return {"id": probe["id"], "game": gid, "own_turn": ctx["own_turn"], "first": ctx["first"], "s754": s754,
            "hp": f"{ctx['hp']}/{ctx['opp_hp']}", "targets": "、".join(sorted(set(targets.values()))),
            "super": supers, "kept": kept, "later": "；".join(later), "mark": mark, "why": why,
            "erntz_plain": erntz_plain, "row": turn_row(turn)}


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
    holds = [r for r in rows if r["id"].endswith("evolve_hold")]
    if "--use-marks" in args:
        marks = json.load(open(args[args.index("--use-marks") + 1], encoding="utf-8"))
        for r in holds:
            r["mark"] = marks[r["id"]]["mark"]
    if "--marks" in args:
        json.dump({r["id"]: {"mark": r["mark"], "why": r["why"]} for r in holds},
                  open(args[args.index("--marks") + 1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if "--md" in args:
        s7 = {cat: [r for r in rows if r["id"].endswith(cat)] for cat in ("evolve_hold", "evolve_use")}
        count = lambda cat, k: sum(r["s754"][k] for r in s7[cat])
        either = lambda cat: sum(r["s754"]["hand"] or r["s754"]["field"] for r in s7[cat])
        line754 = (f"**口人魔**（即 754）：没进化的 {len(s7['evolve_hold'])} 个回合里，回合开头手里有它的 {count('evolve_hold', 'hand')} 个、"
                   f"场上有它的 {count('evolve_hold', 'field')} 个（手里或场上 {either('evolve_hold')} 个）；进化了的 "
                   f"{len(s7['evolve_use'])} 个回合里分别是 {count('evolve_use', 'hand')}、{count('evolve_use', 'field')}"
                   f"（{either('evolve_use')}）。它已加进收益牌清单。\n\n")
        body = label_first(HEADER + line754)
        body += ("| # | 对局 | 回合（先/后手，血 我/对） | 当时能进化的目标 | Salem 留下的 | 之后两回合 | 标记 |\n"
                 "|---|---|---|---|---|---|---|\n")
        for i, r in enumerate(holds, 1):
            body += label_first(f"| {i} | {r['game']} | 第 {r['own_turn']} 回合（{'先' if r['first'] else '后'}手，{r['hp']}） | "
                     f"{r['targets']}{'；能超进化' if r['super'] else '；只能普通进化'} | {r['kept']} | {r['later']} | "
                     f"**{r['mark']}**：{r['why']}{'；标签：正义不进化面' if r['erntz_plain'] else ''} |\n")
        with open(args[args.index("--md") + 1], "w", encoding="utf-8") as f:
            f.write(body)
    print("标记：" + "，".join(f"{k} {n}" for k, n in Counter(r["mark"] for r in holds).items()))
    for r in holds:
        if r["mark"] == "疑似噪声":
            print(f"  {r['id']}：{r['why']}")
    noise = {r["id"] for r in holds if "噪声" in r["mark"]}        # "疑似噪声", or Salem's "噪声"
    # the holds where Erntz came down and stayed unevolved (its unevolved side: 8 to two followers, heal 8)
    plain = {r["id"] for r in holds if r["erntz_plain"]}
    print(f"标签「正义不进化面」：{len(plain)} 条（其中疑似噪声 {len(plain & noise)} 条）")
    drops = (("全部", set()), ("去掉疑似噪声", noise), ("去掉正义不进化面", plain), ("两者都去掉", noise | plain))
    print("\nSalem 基线（能进化的回合里忍住的比例）：")
    tables = [(title, rates(rows, d)) for title, d in drops]
    for key in tables[0][1]:
        print(f"  {key:<14} " + "  ".join(f"{title} {t[key][0]}/{t[key][1]}（{t[key][0] / max(t[key][1], 1):.0%}）"
                                         for title, t in tables))
    by_id = {r["id"]: r for r in rows}
    for i, x in enumerate(args):
        if x != "--results":
            continue
        label, path = args[i + 1].split("=", 1)
        res = {}
        for line in open(path, encoding="utf-8"):
            m = re.match(r"(\S+)\s+(\d+)/(\d+)$", line.strip())
            if m and m.group(1) in by_id:
                res[m.group(1)] = (int(m.group(2)), int(m.group(3)))
        print(f"\n{label} 的 evolve_hold 通过率：")
        for key, sel in (("总体", lambda x: True), ("收益牌在手、本回合够不着", lambda x: x["class"] == "收益牌在手、本回合够不着"),
                         ("只能普通进化", lambda x: x["normal_only"])):
            cells = []
            for title, drop in drops:
                ids = [r["id"] for r in holds if r["id"] not in drop and sel(r["row"]) and r["id"] in res]
                ok, n = sum(res[j][0] for j in ids), sum(res[j][1] for j in ids)
                cells.append(f"{title} {ok}/{n}（{ok / max(n, 1):.0%}）")
            print(f"  {key:<14} " + "  ".join(cells))
        use = [j for j in res if j.endswith("evolve_use")]
        print(f"  evolve_use（不变）{sum(res[j][0] for j in use)}/{sum(res[j][1] for j in use)}")


if __name__ == "__main__":
    main()
