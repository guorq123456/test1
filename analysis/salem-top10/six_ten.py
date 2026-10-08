"""Salem's answers to positions 6-10 of the top-10 (17:13Z): what level-strong and the ruler choose there, how the
evaluation values Salem's move against level-strong's (and which features make the difference), and for position 9,
where Salem puts the divergence at the bot's first turn (the coin spent on Polaris), every option of that turn.

    cd <svsim checkout (64ab2fe)> && PYTHONPATH=. python3 <this> <analysis dir> [--seeds 5]

Same data and method as five.py (positions: picks.txt lines 6-10). Condition: the opponent's 40-card list is known
(order and hand not). Both sides play the original ramp deck.
"""
import json
import random
import sys
from collections import Counter

sys.path.insert(0, __import__("os").path.dirname(__file__))
import five  # noqa: E402

A = sys.argv[1]
SEEDS = int(sys.argv[sys.argv.index("--seeds") + 1]) if "--seeds" in sys.argv else 5
K = 8
five.A = A
five.PICKS = [("1791306333962", 28), ("1791306269709", 21), ("1791385824342", 32), ("1791384258804", 31),
              ("1791317687161", 35)]
# Salem's move per position (17:13Z): 6 his own (= deep), 7 his own (neither: Fate of the World), 8 "the same as
# deep" (his own order: Lyria first), 9 deep (coin then Burnite), 10 his own (= deep)
SALEM = {6: ("deep",), 7: ("actual",), 8: ("deep", "actual"), 9: ("deep",), 10: ("deep",)}
SAID = {6: "我正确（= 深搜）", 7: "我正确（出《世界》，两步都不是）", 8: "和深搜相同（他先用露莉亚）", 9: "跳币龙安（= 深搜）；分歧在第一回合",
        10: "我对（= 深搜）"}


def texts(st, rec, at, row, kinds):
    from svsim.core.actions import from_dict
    out = []
    for k in kinds:
        out.append(row["deep"] if k == "deep" else row["shallow"] if k == "shallow" else
                   five.describe(st, from_dict(rec["actions"][at])))
    return out


def value_lines(st, p, moves, seed):
    """Each move then the rest of the turn by v2s, K determinizations: mean win chance and mean feature terms."""
    from svsim.core.view import determinize
    from svsim.learn.model import matchup_keys
    from svsim.learn.phased import PhasedLearned
    ev = PhasedLearned()
    model = next(ev.models[k + ("ended",)] for k in matchup_keys(st, p, ev.aliases) if k + ("ended",) in ev.models)
    agent, search = five.finish_agent()
    out = {}
    for lab, mv in moves.items():
        acc, ps = Counter(), []
        for j in range(K):
            d = determinize(st, p, random.Random(seed + j))
            t, _ = five.play_out(agent, search, d, mv, seed + 700 + j, p)
            if t.over:
                ps.append(1.0 if t.winner == p else 0.0)
                continue
            ps.append(five.prob(ev.score(t, p, False)))
            for n, v in five.contributions(model, t, p).items():
                acc[n] += v / K
        out[lab] = (sum(ps) / K, acc)
    return out


def main():
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    pos = five.load()
    print("条件：对手卡表已知（牌序、手牌未知）。两边都是 original 跳费龙；强档在这里用 ramp-ramp 模型（C2、hpphase 都不在上面）。\n")
    print("## ① level-strong 和 ruler20261008 各选一步（每档 5 个种子）\n")
    print("| # | 局面 | 谁走 | 浅搜 | 深搜 | 当时实际 | Salem | level-strong | ruler20261008 | 和 Salem 一致？ |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    modal = {}
    for i, (gid, at, rec, st, row) in enumerate(pos, 6):
        p = st.active
        salem = texts(st, rec, at, row, SALEM[i])
        actual = texts(st, rec, at, row, ("actual",))[0]
        cells, agree = [], None
        for spec in ("level-strong", "ruler20261008"):
            c = Counter()
            for s in range(SEEDS):
                a = make_agent(spec, 1000 * i + s).act(st.clone(), legal_actions(st))
                c[five.describe(st, a)] += 1
            if spec == "level-strong":
                modal[i] = c.most_common(1)[0][0]
                agree = sum(v for k, v in c.items() if k in salem)
            lab = lambda d: "浅搜" if d == row["shallow"] else "深搜" if d == row["deep"] else "实际" if d == actual else d
            cells.append("；".join(f"{lab(k)} {v}/{SEEDS}" for k, v in c.most_common()))
        print(f"| {i} | {gid} 第 {at} 步 | {'Salem' if p == 0 else 'bot'} | {row['shallow']} | {row['deep']} | {actual} | "
              f"{SAID[i]} | {cells[0]} | {cells[1]} | {agree}/{SEEDS} |")
    print("\n## ② Salem 的走法和强档的走法：评估器怎么估、差在哪几项\n")
    print("每条线：这一步之后由 v2s 打完这回合，8 次确定化取平均；装机 ramp-ramp ended 模型。\n")
    for i, (gid, at, rec, st, row) in enumerate(pos, 6):
        p = st.active
        salem = texts(st, rec, at, row, SALEM[i])[0]
        if modal[i] in texts(st, rec, at, row, SALEM[i]):
            print(f"- #{i}：强档选的就是 Salem 的走法（{salem}），不比。")
            continue
        moves = {"Salem": five.find(st, salem), "强档": five.find(st, modal[i])}
        res = value_lines(st, p, moves, 60000 + 100 * i)
        (ps, sa), (pm, sm) = res["Salem"], res["强档"]
        diff = {n: sa[n] - sm[n] for n in set(sa) | set(sm)}
        top = sorted(diff, key=lambda n: -abs(diff[n]))[:6]
        print(f"- #{i}：Salem「{salem}」{ps:.0%}，强档「{modal[i]}」{pm:.0%}；Salem − 强档 logit {sum(diff.values()):+.2f}，"
              f"最大的几项：" + "，".join(f"{n} {diff[n]:+.2f}" for n in top))
    print("\n## ③ #9：分歧在更早一步，bot 第一回合（整局第 2 回合，后手，有额外 PP）的各个选项\n")
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply
    gid, at, rec, st9, row = pos[3]
    from svsim.tools import records
    st = records.start(rec)
    k = 0
    while not (st.active == 1 and st.players[1].turns_taken == 1 and st.phase.name == "MAIN"):
        apply(st, from_dict(rec["actions"][k]))
        k += 1
    p = st.active
    me = st.players[p]
    print(f"第 {k} 步，bot 手牌：{', '.join(five.name(c.defn) for c in me.hand)}；PP {me.pp}/{me.max_pp}，额外 PP 可用。"
          f"当时 bot 实际：" + " → ".join(five.describe(st, from_dict(a)) for a in rec["actions"][k:k + 3]) + "。\n")
    c = Counter()
    for s in range(SEEDS):
        c[five.describe(st, make_agent("level-strong", 9000 + s).act(st.clone(), legal_actions(st)))] += 1
    print("现装 level-strong 在这一步选：" + "；".join(f"{a} {v}/{SEEDS}" for a, v in c.most_common()) + "\n")
    # every line of this turn: end now, or the coin then each play (or nothing) then end
    lines = {"不用额外 PP，直接结束回合": [EndTurn()]}
    t0 = st.clone()
    coin = next(a for a in legal_actions(t0) if type(a).__name__ == "UseBonusPP")
    apply(t0, coin)
    for a in legal_actions(t0):
        if isinstance(a, EndTurn):
            lines["用额外 PP，什么都不出，结束（额外 PP 退回）"] = [coin, a]
        elif type(a).__name__ == "PlayCard":
            lines[f"用额外 PP → {five.describe(t0, a)} → 结束"] = [coin, a, EndTurn()]
    for a in legal_actions(st):
        if type(a).__name__ == "PlayCard":
            lines[f"不用额外 PP → {five.describe(st, a)} → 结束"] = [a, EndTurn()]
    from svsim.core.view import determinize
    from svsim.learn.phased import PhasedLearned
    ev = PhasedLearned()
    print("| 这一回合 | 回合末评估（8 次确定化） |")
    print("|---|---|")
    for lab, seq in lines.items():
        ps = []
        for j in range(K):
            t = determinize(st, p, random.Random(91000 + j))
            ok = True
            for a in seq:
                hit = [b for b in legal_actions(t) if five.describe(t, b) == five.describe(st if a is seq[0] else t, a)] \
                    if not isinstance(a, EndTurn) else [EndTurn()]
                if not hit:
                    ok = False
                    break
                apply(t, hit[0])
                if t.active != p:
                    break
            if ok:
                ps.append(five.prob(ev.score(t, p, False)))
        print(f"| {lab} | {sum(ps) / len(ps):.1%}（{len(ps)} 次） |" if ps else f"| {lab} | — |")


if __name__ == "__main__":
    main()
