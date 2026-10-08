"""C3's six dims over the existing terms, and their sign side by side (the architecture thread 17:2x): the
residual regressed on the six dims plus both sides' board terms the installed features already hold (leader HP,
followers, attack, total defense, Wards, board threat capped at the enemy's HP, and the nonlinear ones: hp_sqrt,
hp_low, board_lethal, lasts = HP / incoming), with own turn, side and seat fixed; then the same per side (each of the 11), to see whether each dim keeps its sign across cells;
then the linear terms alone (no six dims), overall and per side, to see which existing weights are off and whether
the same way in every cell; last, the evaluator's own logit(p) added as a control (is the residual a scale miscalibration rather than a missing
board quantity), over all sides and for ramp-t vs pirate-t, the C2 harm cell.

    python3 <this> points.jsonl [--boot 200]        (points from board_residual.py)

Condition: the opponent's 40-card list is known (order and hand not).
"""
import json
import math
import sys

from board_residual import _fit

E = lambda x: x["own_turn"] <= 4
M = lambda x: 5 <= x["own_turn"] <= 7
SIX = [("me_pressure（incoming）", lambda x: min(x["op_threat"] / max(x["my_hp"], 1), 1.5)),
       ("op_pressure（outgoing）", lambda x: min(x["my_threat"] / max(x["op_hp"], 1), 1.5)),
       ("me_hp_early", lambda x: float(x["my_hp"]) if E(x) else 0.0),
       ("me_hp_mid", lambda x: float(x["my_hp"]) if M(x) else 0.0),
       ("op_hp_early", lambda x: float(x["op_hp"]) if E(x) else 0.0),
       ("op_hp_mid", lambda x: float(x["op_hp"]) if M(x) else 0.0)]
LINEAR = [(k, (lambda k: lambda x: float(x[k]))(k)) for k in
          ("my_hp", "op_hp", "my_n", "op_n", "my_atk", "op_atk", "my_life", "op_life", "my_ward", "op_ward")] + \
         [("my_threat_capped", lambda x: float(min(x["my_threat"], max(x["op_hp"], 0)))),
          ("op_threat_capped", lambda x: float(min(x["op_threat"], max(x["my_hp"], 0))))]
# the installed features' (learn.features, version >= 2) nonlinear board terms, rebuilt from the points: hp_sqrt,
# hp_low (HP <= 5), board_lethal (threat >= the enemy's HP) and lasts = min(HP / incoming, 10), where incoming is
# the enemy's board threat (the features add the enemy field's recurring face damage and burn, not in the points)
NONLIN = [(f"{a}_{n}", (lambda a, b, f: lambda x: f(x, a, b))(a, b, f)) for a, b in (("my", "op"), ("op", "my"))
          for n, f in (("hp_sqrt", lambda x, a, b: max(x[f"{a}_hp"], 0) ** 0.5),
                       ("hp_low", lambda x, a, b: float(x[f"{a}_hp"] <= 5)),
                       ("board_lethal", lambda x, a, b: float(x[f"{a}_threat"] >= x[f"{b}_hp"])),
                       ("lasts", lambda x, a, b: min(max(x[f"{a}_hp"], 0) / max(x[f"{b}_threat"], 1), 10.0)))]
FEAT = LINEAR + NONLIN


def main():
    path = sys.argv[1]
    nboot = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 200
    pts = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    print(f"条件：对手卡表已知（牌序、手牌未知）。{len(pts)} 点；残差同时对 6 维和现有特征里的场面项（双方 HP、随从数、可攻击总攻击、总体力、"
          f"守护数、封顶的场面威胁；hp_sqrt、hp_low、board_lethal、lasts = HP ÷ 来袭）回归，固定自己的第几回合、卡组 · 对手和先后手；"
          f"区间 95%，按局重抽 {nboot} 次。\n")
    b, lo, hi = _fit(pts, SIX + FEAT, nboot)
    print("**全部 11 个一方：6 维在现有特征之上的斜率**\n")
    print("| 维 | 系数（95%） |")
    print("|---|---|")
    for (name, _), x, l, h in list(zip(SIX + FEAT, b, lo, hi))[:len(SIX)]:
        mark = "**" if l > 0 or h < 0 else ""
        print(f"| {name} | {mark}{x:+.4f}（{l:+.4f}～{h:+.4f}）{mark} |")
    b2, lo2, hi2 = _fit(pts, SIX + LINEAR, nboot)
    print("\n（对照：只控制线性项、不加非线性项时，6 维的斜率）\n")
    print("| 维 | 系数（95%） |")
    print("|---|---|")
    for (name, _), x, l, h in list(zip(SIX, b2, lo2, hi2)):
        mark = "**" if l > 0 or h < 0 else ""
        print(f"| {name} | {mark}{x:+.4f}（{l:+.4f}～{h:+.4f}）{mark} |")
    print("\n**逐个一方（同样的回归，每个一方单独拟合）：点估计，括号里标出区间不含 0 的**\n")
    print("| 一方（对手） | 点数 | " + " | ".join(n for n, _ in SIX) + " |")
    print("|---|---|" + "---|" * len(SIX))
    signs = {n: [] for n, _ in SIX}
    for side in sorted({(x["deck"], x["opp"]) for x in pts}):
        sub = [x for x in pts if (x["deck"], x["opp"]) == side]
        bb, ll, hh = _fit(sub, SIX + FEAT, nboot)
        cells = []
        for j, (n, _) in enumerate(SIX):
            sig = ll[j] > 0 or hh[j] < 0
            signs[n].append((bb[j], sig))
            cells.append(f"{'**' if sig else ''}{bb[j]:+.3f}{'**' if sig else ''}")
        print(f"| {side[0]}（对 {side[1]}） | {len(sub)} | " + " | ".join(cells) + " |")
    print("\n**跨格同号**（11 个一方里点估计的符号，以及区间不含 0 的个数）\n")
    print("| 维 | 负 / 正 | 显著为负 / 显著为正 |")
    print("|---|---|---|")
    for n, _ in SIX:
        v = signs[n]
        print(f"| {n} | {sum(1 for x, _ in v if x < 0)} / {sum(1 for x, _ in v if x > 0)} | "
              f"{sum(1 for x, s in v if s and x < 0)} / {sum(1 for x, s in v if s and x > 0)} |")

    print("\n**现有线性项本身的残差斜率**（不加 6 维；全部一方一起拟合，再逐个一方的符号）\n")
    b, lo, hi = _fit(pts, LINEAR, nboot)
    per = {n: [] for n, _ in LINEAR}
    for side in sorted({(x["deck"], x["opp"]) for x in pts}):
        sub = [x for x in pts if (x["deck"], x["opp"]) == side]
        bb, ll, hh = _fit(sub, LINEAR, nboot)
        for j, (n, _) in enumerate(LINEAR):
            per[n].append((bb[j], ll[j] > 0 or hh[j] < 0))
    print("| 量 | 全部（95%） | 负 / 正 | 显著为负 / 显著为正 | ramp-t 对 pirate-t |")
    print("|---|---|---|---|---|")
    rp_i = sorted({(x["deck"], x["opp"]) for x in pts}).index(("ramp-t", "pirate-t"))
    for (n, _), x, l, h in zip(LINEAR, b, lo, hi):
        mark = "**" if l > 0 or h < 0 else ""
        v = per[n]
        r, rs = v[rp_i]
        print(f"| {n} | {mark}{x:+.4f}（{l:+.4f}～{h:+.4f}）{mark} | {sum(1 for y, _ in v if y < 0)} / "
              f"{sum(1 for y, _ in v if y > 0)} | {sum(1 for y, q in v if q and y < 0)} / "
              f"{sum(1 for y, q in v if q and y > 0)} | {'**' if rs else ''}{r:+.4f}{'**' if rs else ''} |")

    logit = [("logit(p)", lambda x: math.log(max(x["p"], 1e-9) / max(1 - x["p"], 1e-9)))]
    print("\n**校准尺度检查**（把评估器自己的 logit(p) 当控制量；logit(p) 的斜率 > 0 = 评估器太保守，< 0 = 太自信）\n")
    print("| 回归 | 量 | 系数（95%） |")
    print("|---|---|---|")
    rp = [x for x in pts if (x["deck"], x["opp"]) == ("ramp-t", "pirate-t")]
    for title, sub, cols, show in (("全部，只有 logit(p)", pts, logit, 1),
                                   ("全部，logit(p) + 6 维 + 现有特征", pts, logit + SIX + FEAT, 1 + len(SIX)),
                                   ("ramp-t 对 pirate-t，只有 logit(p)", rp, logit, 1),
                                   ("ramp-t 对 pirate-t，logit(p) + 线性项", rp, logit + LINEAR, 1 + len(LINEAR))):
        bb, ll, hh = _fit(sub, cols, nboot)
        for j in range(show):
            mark = "**" if ll[j] > 0 or hh[j] < 0 else ""
            print(f"| {title if j == 0 else ''} | {cols[j][0]} | {mark}{bb[j]:+.4f}（{ll[j]:+.4f}～{hh[j]:+.4f}）{mark} |")


if __name__ == "__main__":
    main()
