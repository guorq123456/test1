"""Salem's answers to the first 5 of the top-10 divergence positions (the architecture thread 16:52): what the
trainer's level-strong and the ruler choose there, what the evaluation's turn-end features say on position 3's two
lines, how position 4's three discards are valued, and position 1's next-turn damage with the real hands.

    cd <svsim checkout (64ab2fe: 352ae51 and 242ab33 in it)> && PYTHONPATH=. python3 <this> <analysis dir> [--seeds 5]

Positions: analysis/salem-top10/picks.txt lines 1-5 (game id, action index) in analysis/mirror-regression/
salem_games.json (seat 0 Salem, seat 1 the bot of the time); the shallow / deep moves are the ones recorded in
analysis/ramp-benchmark/salem_games_shallow_deep_results.jsonl (matched by their description). Both sides play the
original ramp deck. Condition: the opponent's 40-card list is known (order and hand not); part 4 alone reads the
real hands after the fact.
"""
import json
import math
import random
import sys
from collections import Counter

A = sys.argv[1]
SEEDS = int(sys.argv[sys.argv.index("--seeds") + 1]) if "--seeds" in sys.argv else 5
K = 8
PICKS = [("1791305120171", 35), ("1791387160337", 57), ("1791317238047", 53), ("1791304981889", 35),
         ("1791316540438", 43)]
SALEM = {1: "深搜对", 2: "深搜对", 3: "浅搜对（出《世界》的呈现）", 4: "两步都不对", 5: "深搜对"}   # the architecture's summary


def name(defn):
    return defn.name_zh or defn.name


def load():
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply
    from svsim.tools import records
    recs = json.load(open(f"{A}/mirror-regression/salem_games.json", encoding="utf-8"))["records"]
    rows = {}
    for line in open(f"{A}/ramp-benchmark/salem_games_shallow_deep_results.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r["source"] == "salem27":
            rows[(r["ref"]["game"], r["at"])] = r
    out = []
    for gid, at in PICKS:
        rec = recs[gid]
        st = records.start(rec)
        for a in rec["actions"][:at]:
            apply(st, from_dict(a))
        out.append((gid, at, rec, st, rows[(gid, at)]))
    return out


def describe(s, a):
    sys.path.insert(0, f"{A}/ramp-benchmark")
    from shallow_deep import describe as d
    return d(s, a, name)


def find(st, text):
    from svsim.core.engine import legal_actions
    hits = [a for a in legal_actions(st) if describe(st, a) == text]
    assert len(hits) >= 1, (text, [describe(st, a) for a in legal_actions(st)])
    return hits[0]


def finish_agent(weights=None):
    from svsim.tools.arena import make_agent
    sys.path.insert(0, f"{A}/ramp-benchmark")
    from shallow_deep import inner_search
    agent = make_agent("v2s", 7)
    search = inner_search(agent)
    if weights is not None:
        search.weights = weights
    return agent, search


def play_out(agent, search, s, move, seed, p):
    """`move` then the rest of the turn by v2s (seeded), as shallow_deep.after_value; the turn-end state."""
    from svsim.core.engine import apply, legal_actions
    t = s.clone()
    apply(t, move)
    search.rng = random.Random(seed)
    search._next = None
    line = []
    while not t.over and t.active == p:
        a = agent.act(t, legal_actions(t))
        line.append(describe(t, a))
        apply(t, a)
    return t, line


def prob(score):
    return 1 / (1 + math.exp(-max(min(score / 8.0, 60.0), -60.0)))


def part1(pos):
    from svsim.core.engine import legal_actions
    from svsim.learn.model import matchup_keys
    from svsim.tools.arena import make_agent
    print("## ① 第 19 版 level-strong 和 ruler20261008 在 5 个局面上各选一步\n")
    print(f"每个局面每个档 {SEEDS} 个搜索种子（搜索有随机性，报每种选法的次数）。浅搜 / 深搜的走法是当时记录的（v2 每步 100 次、"
          f"mcts:800+plan+learned+phased），按走法的文字描述对上。\n")
    print("| # | 局面 | 谁走 | 浅搜 | 深搜 | Salem | level-strong | ruler20261008 |")
    print("|---|---|---|---|---|---|---|---|")
    tally = {}
    for i, (gid, at, rec, st, row) in enumerate(pos, 1):
        p = st.active
        keys = matchup_keys(st, p)
        cells = []
        for spec in ("level-strong", "ruler20261008"):
            c = Counter()
            for s in range(SEEDS):
                a = make_agent(spec, 1000 * i + s).act(st.clone(), legal_actions(st))
                d = describe(st, a)
                c["浅搜" if d == row["shallow"] else "深搜" if d == row["deep"] else f"第三步：{d}"] += 1
            tally[(i, spec)] = c
            cells.append("；".join(f"{k} {v}/{SEEDS}" for k, v in c.most_common()))
        who = "Salem" if p == 0 else "bot"
        print(f"| {i} | {gid} 第 {at} 步（模型键 {keys[0]}） | {who} | {row['shallow']} | {row['deep']} | {SALEM[i]} | "
              f"{cells[0]} | {cells[1]} |")
    return tally


def contributions(model, state, p):
    x = model.inputs(state, p)
    names = model.names()
    return {n: c * (v - m) / s for n, c, v, m, s in zip(names, model.coef, x, model.mean, model.std)}


def part2(pos):
    from svsim.core.view import determinize
    from svsim.learn.phased import PhasedLearned
    from svsim.learn.model import matchup_keys
    gid, at, rec, st, row = pos[2]
    p = st.active
    ev = PhasedLearned()
    model = next(ev.models[k + ("ended",)] for k in matchup_keys(st, p, ev.aliases) if k + ("ended",) in ev.models)
    agent, search = finish_agent()
    print("\n## ② #3（bot 的局面）：两条线回合末的评估分项\n")
    lines = {"浅搜（出《世界》的呈现）": find(st, row["shallow"]), "深搜（出口人魔，弃《世界》的呈现）": find(st, row["deep"])}
    sums, probs, ex = {}, {}, {}
    for lab, mv in lines.items():
        acc, ps = Counter(), []
        for j in range(K):
            d = determinize(st, p, random.Random(53000 + j))
            t, line = play_out(agent, search, d, mv, 53700 + j, p)
            if j == 0:
                ex[lab] = line
            if t.over:
                ps.append(1.0 if t.winner == p else 0.0)
                continue
            ps.append(prob(ev.score(t, p, False)))
            for n, v in contributions(model, t, p).items():
                acc[n] += v / K
        sums[lab], probs[lab] = acc, sum(ps) / K
    a, b = list(lines)
    print(f"装机评估（{matchup_keys(st, p)[0]} 的 ended 模型），{K} 次确定化取平均；回合剩下的由 v2s 打完（同一串种子）。\n")
    for lab in lines:
        print(f"- {lab}：胜率 {probs[lab]:.0%}；第 1 次确定化的走法：{' → '.join(ex[lab])}")
    diff = {n: sums[b][n] - sums[a][n] for n in set(sums[a]) | set(sums[b])}
    total = sum(diff.values())
    print(f"\n深搜 − 浅搜，logit 合计 {total:+.3f}（分数 = 8 × logit）。贡献最大的项（各项 = 系数 × 标准化后的值）：\n")
    print("| 特征 | 浅搜 | 深搜 | 深搜 − 浅搜 |")
    print("|---|---|---|---|")
    for n in sorted(diff, key=lambda n: -abs(diff[n]))[:14]:
        print(f"| {n} | {sums[a][n]:+.3f} | {sums[b][n]:+.3f} | {diff[n]:+.3f} |")
    hand_like = [n for n in diff if any(k in n for k in ("hand", "pool", "deck")) and abs(diff[n]) > 1e-9]
    print(f"\n手牌 / 牌库相关的项合计：{sum(diff[n] for n in hand_like):+.3f}（不为 0 的只有 {', '.join(sorted(hand_like))}）")
    zero = [n for n, c in zip(model.names(), model.coef) if n.startswith(("me_hand_", "me_pool_")) and c == 0.0]
    print(f"这个模型里我方手牌 / 牌池的 12 个角色项系数全是 0（{len(zero)} 个，learn.phased 的 STOCK 掩码），"
          f"所以我方手牌只按张数（me_hand）算，看不出手里、牌库里是哪几张。")
    me = st.players[p]
    is_j = lambda c: name(c.defn).startswith("约束的《正义》")
    from svsim.cards import dragon
    jid = next(getattr(dragon, n).card_id for n in dir(dragon)
               if hasattr(getattr(dragon, n), "card_id") and is_j(type("x", (), {"defn": getattr(dragon, n)})))
    listed = sum(1 for cid in rec["decks"][p] if cid == jid)
    where = {"牌库": sum(map(is_j, me.deck)), "手牌": sum(map(is_j, me.hand)), "场上": sum(map(is_j, me.field))}
    where["已用掉（墓地等）"] = listed - sum(where.values())
    just = where["牌库"]
    print(f"\n当时 bot 牌库 {len(me.deck)} 张。《正义》的去处：" + "，".join(f"{k} {v}" for k, v in where.items())
          + f"（卡表 {listed} 张）。"
          f"《世界》的呈现：抽 2 张，消灭敌方攻击最高的一个随从（随机），增幅 10 再对所有敌方各 4 点。"
          f"这时 bot 有 10 PP，所以出它 = 抽 2、消灭《正义》、4 点打死波菈莱、对手主战者 −4。"
          f"抽 2 张里至少一张《正义》的概率（不放回）= {1 - math.comb(len(me.deck) - just, 2) / math.comb(len(me.deck), 2):.0%}。")


def part3(pos):
    from svsim.core.actions import PlayCard
    from svsim.core.engine import legal_actions
    from svsim.core.view import determinize
    from svsim.learn.model import LinearValue
    from svsim.learn.phased import PhasedLearned, load
    gid, at, rec, st, row = pos[3]
    p = st.active
    me = st.players[p]
    print("\n## ③ #4（bot 的局面）：口人魔弃哪张\n")
    opts = {}
    for a in legal_actions(st):
        if not isinstance(a, PlayCard):
            continue
        c = st.in_hand(p, a.uid)
        if c is None or c.defn.cost != 7:
            continue
        tgt = a.targets[0] if a.targets else None
        tc = st.in_hand(p, tgt) if tgt is not None else None
        key = name(tc.defn) if tc is not None else "（无）"
        opts.setdefault(key, a)
    made = describe(st, __import__("svsim.core.actions", fromlist=["from_dict"]).from_dict(rec["actions"][at]))
    print(f"当时 bot 实际：{made}。口人魔（7费）可以选的弃牌：{', '.join(opts)}。\n")
    folder = __import__("pathlib").Path(__import__("svsim.learn.phased", fromlist=["x"]).__file__).parent / "phased_models"
    c2 = {("ramp", "ramp", m): LinearValue.load(folder / f"ramp-t-ramp-t-{m}.json") for m in ("ended", "act")}
    evals = {"装机（original ramp 镜像的 ramp-ramp 模型，强档在这局面真正用的）": None,
             "C2（ramp-t 镜像的 hand 模型，跨卡组套用到 original ramp）": PhasedLearned(models=c2)}
    print("| 弃 | " + " | ".join(evals) + " |")
    print("|---|" + "---|" * len(evals))
    res = {}
    for lab, w in evals.items():
        agent, search = finish_agent(w)
        ev = w or PhasedLearned()
        for key, mv in opts.items():
            ps = []
            for j in range(K):
                d = determinize(st, p, random.Random(35000 + j))
                t, _ = play_out(agent, search, d, mv, 35700 + j, p)
                ps.append((1.0 if t.winner == p else 0.0) if t.over else prob(ev.score(t, p, False)))
            res[(lab, key)] = sum(ps) / K
    for key in opts:
        print(f"| {key} | " + " | ".join(f"{res[(lab, key)]:.0%}" for lab in evals) + " |")
    print("\n（回合剩下的由 v2s 打完，评估器分别换成该列的那套；8 次确定化取平均。）")


def part4(pos):
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply
    from svsim.search.combo import next_turn_damage
    gid, at, rec, st, row = pos[0]
    p = st.active
    bot = 1 - p
    agent, search = finish_agent()
    print("\n## ④ #1（Salem 的局面）：用存档里 bot 的真实手牌算 bot 下回合的最大伤害（事后对照）\n")
    print(f"bot 当时的真实手牌（事后可看）：{', '.join(name(c.defn) for c in st.players[bot].hand)}；"
          f"bot 超进化点 {st.players[bot].sep}，进化点 {st.players[bot].ep}。\n")
    print("| 这一回合怎么打 | 回合末 Salem HP | bot 下回合最大伤害（真实手牌 + 场面，资源模型） | 斩杀？ | bot 评估器给 Salem 的胜率（真实局面） |")
    print("|---|---|---|---|---|")
    from svsim.learn.phased import PhasedLearned
    ev = PhasedLearned()
    cases = {"浅搜（出《世界》的呈现）": find(st, row["shallow"]), "深搜（用额外 PP，接班德）": find(st, row["deep"])}
    from svsim.core.view import determinize
    ends = {}
    for lab, mv in cases.items():
        t, line = play_out(agent, search, st, mv, 35000, p)
        ends[lab] = t
        dmg = next_turn_damage(t, bot, 2000)
        hp = t.players[p].leader_hp
        print(f"| {lab}：{' → '.join(line)} | {hp} | {dmg} | {'是' if dmg >= hp else '否'} | {prob(ev.score(t, p, False)):.0%} |")
    t = st.clone()
    k = at
    while k < len(rec["actions"]) and t.active == p and not t.over:
        apply(t, from_dict(rec["actions"][k]))
        k += 1
    dmg = next_turn_damage(t, bot, 2000)
    hp = t.players[p].leader_hp
    print(f"| Salem 实际（存档） | {hp} | {dmg} | {'是' if dmg >= hp else '否'} | {prob(ev.score(t, p, False)):.0%} |")
    hp0 = t.players[p].leader_hp
    while k < len(rec["actions"]) and t.active == bot and not t.over:
        apply(t, from_dict(rec["actions"][k]))
        k += 1
    print(f"\n存档里 bot 下回合实际打了 {hp0 - t.players[p].leader_hp} 点（Salem HP {hp0} → {t.players[p].leader_hp}），"
          f"整局 Salem 胜。")
    n = 200
    print(f"\n**按 Salem 当时能看到的信息**：在上面两条线的回合末局面上，把 bot 的手牌从它「手牌 + 牌库」里重抽 {n} 次"
          f"（core.view.determinize，Salem 的视角），每次算 bot 下回合的最大伤害：\n")
    print("| 这一回合怎么打 | 回合末 Salem HP | 重抽手牌里 bot 下回合能斩杀的比例 | 最大伤害的中位数 / 最大 | 评估器给 Salem 的胜率：各次重抽的最小～最大 |")
    print("|---|---|---|---|---|")
    for lab, t in ends.items():
        hp = t.players[p].leader_hp
        dm, sc = [], []
        for j in range(n):
            d = determinize(t, p, random.Random(77000 + j))
            dm.append(next_turn_damage(d, bot, 2000))
            sc.append(prob(ev.score(d, p, False)))
        dm.sort()
        print(f"| {lab} | {hp} | {sum(x >= hp for x in dm) / n:.1%} | {dm[n // 2]} / {dm[-1]} | {min(sc):.1%}～{max(sc):.1%} |")
    print("\n评估器给的胜率在所有重抽里一模一样（J12：对手手牌只按张数和整池进评估），不管对面那手牌下回合能不能斩杀。")


def main():
    pos = load()
    print("条件：对手卡表已知（牌序、手牌未知）；④ 事后读了真实手牌。两边都是 original 跳费龙。\n")
    part1(pos)
    part2(pos)
    part3(pos)
    part4(pos)


if __name__ == "__main__":
    main()
