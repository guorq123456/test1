"""Where A (a candidate with added features) and B (level-strong) first choose differently in ramp-t vs
pirate-t, what the rest of that turn does differently, which features push A there, and what pirate-t does to
ramp-t's leader in the next two turns on each line (the architecture thread 18:39; numbers only).

    cd <checkout the gate ran on> && PYTHONPATH=. python3 <this> rows --games games.jsonl.gz [--rows GATE.jsonl]
         --cand FOLDER --bank NAME --out div.jsonl [--deck D --opp O]     (games from replay.py; without --rows,
         the pre-gate check: no points, every score column reads 0 and is not to be read)
    python3 <this> report div1.jsonl[.gz] div2.jsonl[.gz] ...

Per first split (one per seed and seat whose A and B games differ): the position (own turn, both leaders'
HP, play points); each line's first move; the rest of the turn on each line up to ramp-t's turn end (resolved
the way the search does, without starting the next turn): face damage, enemy followers removed, cards played,
play points left, evolves, bonus PP; both models' logit at both turn ends with each feature's contribution
(coefficient x standardized value) to the difference; ramp-t's leader HP after each of pirate-t's next two
turns and whether it was dead by then; the games' points from the gate's row.

Condition: the opponent's 40-card list is known (order and hand not).
"""
import gzip
import json
import math
import random
import sys
from collections import Counter, defaultdict

DECK, OPP = "ramp-t", "pirate-t"


def _kind(state, d, seat):
    """A move as (type, detail): the card played or evolved, an attack on the leader or a follower."""
    t = d["type"]
    if t == "Attack":
        return t, "打脸" if d["target"] < 0 else "打随从"
    if t in ("PlayCard", "Evolve", "Engage", "Fuse"):
        uid = d["uid"]
        p = state.players[seat]
        for c in p.hand + p.field:
            if c.uid == uid:
                return t + ("(超)" if d.get("super_") else ""), c.defn.name
        return t, "?"
    return t, ""


def _snap(state, seat):
    me, op = state.players[seat], state.players[1 - seat]
    return {"my_hp": me.leader_hp, "op_hp": op.leader_hp, "pp": me.pp, "max_pp": me.max_pp, "hand": len(me.hand),
            "my_n": len(me.followers), "my_atk": sum(c.atk for c in me.followers),
            "my_life": sum(c.life for c in me.followers),
            "op_n": len(op.followers), "op_atk": sum(c.atk for c in op.followers),
            "op_life": sum(c.life for c in op.followers), "ep": me.ep, "sep": me.sep,
            "op_uids": sorted(c.uid for c in op.followers)}


def _sig(state, seat):
    """The turn end, as what the next turn sees: both boards, hands and leaders."""
    me, op = state.players[seat], state.players[1 - seat]
    board = lambda p: sorted((c.defn.card_id, c.atk, c.life, c.evolved) for c in p.field)
    return json.dumps([me.leader_hp, op.leader_hp, board(me), board(op), sorted(c.defn.card_id for c in me.hand),
                       me.pp, me.ep, me.sep, len(op.hand)])


def _contrib(model, state, seat):
    x = model.inputs(state, seat)
    return [c * (v - m) / s for c, v, m, s in zip(model.coef, x, model.mean, model.std)]


def _games(path):
    """The replayed games; a file still being written ends in a cut gzip block, read up to it."""
    fh = gzip.open(path, "rt", encoding="utf-8")
    try:
        for line in fh:
            if line.endswith("\n"):
                yield json.loads(line)
    except EOFError:
        return


def rows(args):
    from pathlib import Path
    from svsim.cards import decks
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply, new_game
    from svsim.learn.model import LinearValue
    from svsim.learn.phased import folder_of
    from svsim.search.mcts import ISMCTS
    from svsim.ui.session import DECKS
    games = args[args.index("--games") + 1]
    gate = {r["k"]: r for r in (json.loads(x) for x in open(args[args.index("--rows") + 1], encoding="utf-8"))} \
        if "--rows" in args else None
    deck = args[args.index("--deck") + 1] if "--deck" in args else DECK
    opp = args[args.index("--opp") + 1] if "--opp" in args else OPP
    cand = args[args.index("--cand") + 1]
    bank = args[args.index("--bank") + 1]
    out = open(args[args.index("--out") + 1], "w", encoding="utf-8")
    ma = LinearValue.load(folder_of(cand) / f"{deck}-{opp}-ended.json")
    mb = LinearValue.load(Path(folder_of(cand)).parent / f"{deck}-{opp}-ended.json")
    names_a, names_b = ma.names(), mb.names()
    new = [n for n in names_a if n not in names_b]
    mine, theirs = decks.build(DECKS[deck][1]), decks.build(DECKS[opp][1])
    n = 0
    for g in _games(games):
        if g["at"] is None:
            continue
        seat, seed = g["seat"], g["seed"]
        cards = [None, None]
        cards[seat], cards[1 - seat] = mine, theirs
        st0 = new_game(cards[0], cards[1], seed=seed)
        for d in g["shared"]:
            apply(st0, from_dict(d))
        assert st0.active == seat
        pos = _snap(st0, seat)
        pos["own_turn"] = st0.players[seat].turns_taken
        pos["went_first"] = st0.first == seat
        row = {"bank": bank, "k": g["k"], "seat": seat, "seed": seed, "pos": pos, "new": new,
               "a_pts": gate[g["k"]]["points"][seat] if gate else None,
               "b_pts": gate[g["k"]]["b_points"][seat] if gate else None}
        ends = {}
        for side in ("A", "B"):
            moves = g[side]
            st = st0.clone()
            row[side + "_first"] = _kind(st, moves[0], seat)
            turn = {"plays": 0, "face_atk": 0, "fol_atk": 0, "evolve": 0, "super": 0, "bonus": 0, "moves": 0}
            i, end = 0, None
            while i < len(moves):
                d = moves[i]
                if st.active != seat:
                    break
                t = d["type"]
                turn["moves"] += 1
                turn["plays"] += t == "PlayCard"
                turn["face_atk"] += t == "Attack" and d["target"] < 0
                turn["fol_atk"] += t == "Attack" and d["target"] >= 0
                turn["evolve"] += t == "Evolve"
                turn["super"] += t == "Evolve" and bool(d.get("super_"))
                turn["bonus"] += t == "UseBonusPP"
                if t == "EndTurn":
                    end = st.clone()
                    ISMCTS._step(end, EndTurn())
                apply(st, from_dict(d))
                i += 1
                if t == "EndTurn" or st.over:
                    break
            if end is None:                        # the game ended inside the turn (a lethal, or a loss)
                end = st.clone()
            e = _snap(end, seat)
            e["won_in_turn"] = end.over and end.winner == seat
            e["killed"] = len(set(pos["op_uids"]) - set(e["op_uids"]))
            e["face"] = pos["op_hp"] - e["op_hp"]
            turn.update(e)
            turn["sig"] = _sig(end, seat)
            ends[side] = end
            # pirate-t's next two turns on this line (the replayed moves stop after its second turn end)
            hp, dead, opp_ended = [], None, 0
            while i < len(moves) and not st.over:
                d = moves[i]
                was_opp = st.active != seat
                apply(st, from_dict(d))
                i += 1
                if was_opp and d["type"] == "EndTurn":
                    opp_ended += 1
                    hp.append(st.players[seat].leader_hp)
                    if opp_ended == 2:
                        break
            if st.over and st.winner == 1 - seat:   # died in pirate-t's turn opp_ended + 1, or as one ended
                dead = opp_ended if hp and hp[-1] <= 0 else min(opp_ended + 1, 2)
            turn["hp_after"] = hp
            turn["dead_in"] = dead                  # pirate-t's 1st or 2nd turn after this one, else None
            turn["over_after"] = st.over
            row[side] = turn
        for tag, m in (("ma", ma), ("mb", mb)):
            ca, cb = _contrib(m, ends["A"], seat), _contrib(m, ends["B"], seat)
            row[tag + "_logit"] = [sum(ca), sum(cb)]
            row[tag + "_diff"] = [x - y for x, y in zip(ca, cb)]
        row["names_a"], row["names_b"] = (names_a, names_b) if n == 0 else (None, None)
        if n == 0:
            row["w_a"], row["w_b"] = ma.weights_by_name(), mb.weights_by_name()
        out.write(json.dumps(row, ensure_ascii=False) + "\n")
        n += 1
    print(f"{bank}: {n} 个分歧点")


# ------------------------------------------------------------------------------------------------ report

def _boot(vals, by, nboot=2000, seed=1):
    """Mean and 95% interval, resampling games (seed, bank)."""
    groups = defaultdict(list)
    for v, g in zip(vals, by):
        groups[g].append(v)
    keys = list(groups)
    rng = random.Random(seed)
    means = []
    for _ in range(nboot):
        s = c = 0
        for _ in keys:
            gv = groups[keys[rng.randrange(len(keys))]]
            s += sum(gv)
            c += len(gv)
        means.append(s / c)
    means.sort()
    return sum(vals) / len(vals), means[int(0.025 * nboot)], means[int(0.975 * nboot)]


def _fmt(t):
    m, lo, hi = t
    return f"{m:+.3f}（{lo:+.3f}～{hi:+.3f}）"


def report(paths):
    opener = lambda p: gzip.open(p, "rt", encoding="utf-8") if p.endswith(".gz") else open(p, encoding="utf-8")
    R = [json.loads(x) for p in paths for x in opener(p)]
    if any(r["a_pts"] is None for r in R):             # the pre-gate check: no gate, no points
        print("**门前检查：没有门的得分。下面所有「A − B 得分」列都记成 0，不读。**\n")
        for r in R:
            r["a_pts"] = r["b_pts"] = 0.0
    names = {}
    for r in R:
        if r["names_a"]:
            names[r["bank"]] = (r["names_a"], r["names_b"])
    banks = sorted({r["bank"] for r in R}, key=lambda b: [r["bank"] for r in R].index(b))
    print("条件：对手卡表已知（牌序、手牌未知）。A = 加了特征的候选，B = level-strong，C = level-strong 打 pirate-t；"
          "每个分歧点 = 同一副发牌、同一座位上 A 和 B 第一次选得不一样的局面（之前两局逐步相同）。"
          "区间 95%，按局（种子 × 座位 × 库）重抽 2000 次。\n")
    print("## 1. 分歧点在哪\n")
    print("| 库 | 分歧点 | 自己的第几回合（中位） | 回合分布 1-2 / 3-4 / 5-6 / 7+ | 先手占 | A 得分 − B 得分（每局） |")
    print("|---|---|---|---|---|---|")
    for b in banks + ["合计"]:
        rs = [r for r in R if b == "合计" or r["bank"] == b]
        t = sorted(r["pos"]["own_turn"] for r in rs)
        bins = [sum(1 for x in t if lo <= x <= hi) for lo, hi in ((0, 2), (3, 4), (5, 6), (7, 99))]
        d = _boot([r["a_pts"] - r["b_pts"] for r in rs], [(r["bank"], r["k"], r["seat"]) for r in rs])
        print(f"| {b} | {len(rs)} | {t[len(t) // 2]} | {' / '.join(map(str, bins))} | "
              f"{sum(r['pos']['went_first'] for r in rs) / len(rs):.0%} | {_fmt(d)} |")

    print("\n## 2. 第一步的类别（A 的第一步 × B 的第一步，各库合计）\n")
    kinds = ["PlayCard", "Attack", "Evolve", "Evolve(超)", "UseBonusPP", "EndTurn", "Mulligan", "其他"]
    norm = lambda k: k if k in kinds else "其他"
    tab = Counter((norm(r["A_first"][0]), norm(r["B_first"][0])) for r in R)
    print("| A \\ B | " + " | ".join(kinds) + " |")
    print("|---|" + "---|" * len(kinds))
    for a in kinds:
        if any(tab[(a, b)] for b in kinds):
            print(f"| {a} | " + " | ".join(str(tab[(a, b)]) for b in kinds) + " |")
    att = [r for r in R if r["A_first"][0] == "Attack" and r["B_first"][0] == "Attack"]
    print(f"\n两边第一步都是攻击的 {len(att)} 个里：A 打脸 B 打随从 "
          f"{sum(1 for r in att if r['A_first'][1] == '打脸' and r['B_first'][1] == '打随从')}，"
          f"A 打随从 B 打脸 {sum(1 for r in att if r['A_first'][1] == '打随从' and r['B_first'][1] == '打脸')}，"
          f"同类不同目标 {sum(1 for r in att if r['A_first'][1] == r['B_first'][1])}。")
    print("\n**最常见的第一步组合（带牌名）**\n")
    print("| A 的第一步 | B 的第一步 | 个数 | 回合（中位） | A − B 每局得分 |")
    print("|---|---|---|---|---|")
    det = defaultdict(list)
    for r in R:
        det[(" ".join(r["A_first"]).strip(), " ".join(r["B_first"]).strip())].append(r)
    for (x, y), rs in sorted(det.items(), key=lambda kv: -len(kv[1]))[:15]:
        t = sorted(r["pos"]["own_turn"] for r in rs)
        print(f"| {x} | {y} | {len(rs)} | {t[len(t) // 2]} | "
              f"{sum(r['a_pts'] - r['b_pts'] for r in rs) / len(rs):+.2f} |")

    miss = lambda r: r["B_first"][0] == "PlayCard" and r["A_first"] != r["B_first"]
    card = Counter(r["B_first"][1] for r in R if miss(r)).most_common(1)[0][0]
    print(f"\n**最大的一类：B 第一步出 {card}、A 第一步没出它**（逐库；「占全部」= 这类分歧点上 A − B 的得分之和 ÷ 全部分歧点之和，"
          f"全部分歧点之和就是门里 A、B 两边总得分之差）\n")
    print("| 库 | 个数 | 回合（中位） | A 改成：结束回合 / 出别的牌 / 其他 | A − B 得分之和 | 全部分歧点之和 | 占全部 | "
          "me_bane 的推力（A − B 模型，logit） |")
    print("|---|---|---|---|---|---|---|---|")
    for b in banks + ["合计"]:
        allr = [r for r in R if b == "合计" or r["bank"] == b]
        rs = [r for r in allr if miss(r) and r["B_first"][1] == card]
        if not rs:
            continue
        t = sorted(r["pos"]["own_turn"] for r in rs)
        alt = Counter("结束回合" if r["A_first"][0] == "EndTurn" else "出别的牌" if r["A_first"][0] == "PlayCard" else "其他"
                      for r in rs)
        push = []
        for r in rs:
            na, nb = names[r["bank"]]
            if "me_bane" in na and "me_bane" in nb:
                push.append(r["ma_diff"][na.index("me_bane")] - r["mb_diff"][nb.index("me_bane")])
        tot, part = sum(r["a_pts"] - r["b_pts"] for r in allr), sum(r["a_pts"] - r["b_pts"] for r in rs)
        print(f"| {b} | {len(rs)} | {t[len(t) // 2]} | {alt['结束回合']} / {alt['出别的牌']} / {alt['其他']} | {part:+.0f} | "
              f"{tot:+.0f} | {part / tot if tot else float('nan'):.0%} | {sum(push) / len(push):+.3f} |")

    print("\n## 3. 回合内差在哪（从分歧点到这一回合结束，A 线减 B 线）\n")
    full = [r for r in R if "sig" in r["A"]]
    same = [r for r in full if r["A"]["sig"] == r["B"]["sig"]]
    diff = [r for r in full if r["A"]["sig"] != r["B"]["sig"]]
    print(f"- 回合末局面完全相同（只差顺序）：{len(same)} / {len(full)}（{len(same) / len(full):.0%}）；"
          f"下面都只看回合末不同的 {len(diff)} 个。\n")
    by = [(r["bank"], r["k"], r["seat"]) for r in diff]
    print("| 量 | A − B 的均值（95%） | A 多 / 一样 / B 多 |")
    print("|---|---|---|")
    for key, label in (("face", "打脸伤害（对方 HP 少了多少）"), ("killed", "解掉的对方随从数"),
                       ("op_atk", "回合末对方场上总攻击"), ("op_life", "回合末对方场上总体力"),
                       ("plays", "出牌张数"), ("pp", "回合末剩下的 PP"), ("hand", "回合末手牌张数"),
                       ("evolve", "进化次数（含超进化）"), ("super", "超进化次数"), ("bonus", "用额外 PP 次数"),
                       ("my_n", "回合末我方随从数"), ("my_atk", "回合末我方总攻击"), ("my_life", "回合末我方总体力"),
                       ("my_hp", "回合末我方 HP")):
        v = [r["A"][key] - r["B"][key] for r in diff]
        print(f"| {label} | {_fmt(_boot(v, by))} | {sum(x > 0 for x in v)} / {sum(x == 0 for x in v)} / "
              f"{sum(x < 0 for x in v)} |")
    print("\n**按类别**（一个分歧点可以落进几类；「A − B 每局得分」是这类分歧点上 A 那局减 B 那局的得分）\n")
    print("| 类别 | 个数 | A − B 每局得分（95%） |")
    print("|---|---|---|")
    cats = [("A 偏打脸（打脸多、解场不多）", lambda r: r["A"]["face"] > r["B"]["face"] and r["A"]["killed"] <= r["B"]["killed"]),
            ("A 偏解场（解场多、打脸不多）", lambda r: r["A"]["killed"] > r["B"]["killed"] and r["A"]["face"] <= r["B"]["face"]),
            ("A 留牌（出牌少）", lambda r: r["A"]["plays"] < r["B"]["plays"]),
            ("A 多出牌", lambda r: r["A"]["plays"] > r["B"]["plays"]),
            ("A 进化、B 不（这回合进化次数多）", lambda r: r["A"]["evolve"] > r["B"]["evolve"]),
            ("B 进化、A 不", lambda r: r["A"]["evolve"] < r["B"]["evolve"]),
            ("A 用额外 PP、B 不", lambda r: r["A"]["bonus"] > r["B"]["bonus"]),
            ("B 用额外 PP、A 不", lambda r: r["A"]["bonus"] < r["B"]["bonus"]),
            ("出牌数、打脸、解场、进化、额外 PP 都一样（出的牌或目标不同）",
             lambda r: all(r["A"][k] == r["B"][k] for k in ("plays", "face", "killed", "evolve", "bonus")))]
    for label, f in cats:
        rs = [r for r in diff if f(r)]
        if rs:
            d = _boot([r["a_pts"] - r["b_pts"] for r in rs], [(r["bank"], r["k"], r["seat"]) for r in rs])
            print(f"| {label} | {len(rs)} | {_fmt(d)} |")
        else:
            print(f"| {label} | 0 | |")
    rs = same
    if rs:
        d = _boot([r["a_pts"] - r["b_pts"] for r in rs], [(r["bank"], r["k"], r["seat"]) for r in rs])
        print(f"| （对照）回合末相同、只差顺序 | {len(rs)} | {_fmt(d)} |")

    print("\n**逐库**（回合末不同的分歧点；A − B 的均值）\n")
    print("| 库 | 个数 | 打脸 | 解场数 | 出牌数 | 剩 PP | 进化 | 额外 PP | 回合末对方总攻击 | 我方 HP |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for b in banks:
        rs = [r for r in diff if r["bank"] == b]
        mean = lambda k: sum(r["A"][k] - r["B"][k] for r in rs) / len(rs)
        print(f"| {b} | {len(rs)} | " + " | ".join(f"{mean(k):+.2f}" for k in
                                                ("face", "killed", "plays", "pp", "evolve", "bonus", "op_atk", "my_hp")) + " |")

    print("\n## 4. 哪个特征把 A 推向它那一步（回合末两局面的 logit 差，逐特征贡献 = 系数 × 标准化值之差）\n")
    for b in banks:
        w = next(r for r in R if r["bank"] == b and r.get("w_a"))
        wa, wb = w["w_a"], w["w_b"]
        print(f"**{b} 的模型：每 1 点领袖 HP 值多少 logit**（回合末模型；= hp 的线性项 + hp_sqrt 在该 HP 处的斜率 + "
              f"hpphase 的段系数；hp_low、lasts 不算在内）\n")
        print("| 一方 | HP | 段 | A 模型 | B 模型 | A ÷ B |")
        print("|---|---|---|---|---|---|")
        for side in ("me", "op"):
            for hp in (8, 14, 20):
                for band, key in (("1～4", "early"), ("5～7", "mid"), ("8～", None)):
                    va = wa.get(f"{side}_hp", 0) + wa.get(f"{side}_hp_sqrt", 0) / (2 * hp ** 0.5) + \
                        (wa.get(f"{side}_hp_{key}", 0) if key else 0)
                    vb = wb.get(f"{side}_hp", 0) + wb.get(f"{side}_hp_sqrt", 0) / (2 * hp ** 0.5) + \
                        (wb.get(f"{side}_hp_{key}", 0) if key else 0)
                    print(f"| {'我方' if side == 'me' else '对方'} | {hp} | {band} | {va:+.3f} | {vb:+.3f} | "
                          f"{va / vb if vb else float('nan'):.2f} |")
        diffw = sorted(((n, wa.get(n, 0), wb.get(n, 0)) for n in wb if n != "bias"),
                       key=lambda t: -abs((t[1] - t[2])))[:12]
        print(f"\n旧特征里每单位系数变化最大的（A − B，原始单位）：" +
              "；".join(f"{n} {x:+.3f}→{y:+.3f}" for n, y, x in diffw) + "（箭头：B → A）\n")
    for b in banks:
        rs = [r for r in diff if r["bank"] == b]
        na, nb = names[b]
        new = [x for x in na if x not in nb]
        ia = {x: i for i, x in enumerate(na)}
        ib = {x: i for i, x in enumerate(nb)}
        by = [(r["bank"], r["k"], r["seat"]) for r in rs]
        dA = [r["ma_logit"][0] - r["ma_logit"][1] for r in rs]
        dB = [r["mb_logit"][0] - r["mb_logit"][1] for r in rs]
        newpart = [sum(r["ma_diff"][ia[x]] for x in new) for r in rs]
        oldpart = [sum(r["ma_diff"][ia[x]] - r["mb_diff"][ib[x]] for x in nb) for r in rs]
        print(f"**{b}**（新特征：{', '.join(new)}；{len(rs)} 个回合末不同的分歧点）\n")
        print(f"- A 模型给 A 线回合末比 B 线高多少（logit）：{_fmt(_boot(dA, by))}；A 模型偏向自己那一步的 "
              f"{sum(x > 0 for x in dA)} / {len(dA)}")
        print(f"- B 模型给 A 线比 B 线高多少：{_fmt(_boot(dB, by))}；B 模型偏向 B 那一步的 {sum(x < 0 for x in dB)} / {len(dB)}")
        flip = [i for i in range(len(rs)) if dA[i] > 0 > dB[i]]
        print(f"- 两个模型意见相反（A 模型偏 A 线、B 模型偏 B 线）的 {len(flip)} 个")
        print(f"- 差（A 模型 − B 模型）= 新特征的贡献 + 旧特征重新拟合后的变化：新特征 {_fmt(_boot(newpart, by))}，"
              f"旧特征 {_fmt(_boot(oldpart, by))}")
        if flip:
            fb = [by[i] for i in flip]
            print(f"  - 只看意见相反的：新特征 {_fmt(_boot([newpart[i] for i in flip], fb))}，"
                  f"旧特征 {_fmt(_boot([oldpart[i] for i in flip], fb))}")
        contrib = {}
        for x in new:
            contrib[x + "（新）"] = [r["ma_diff"][ia[x]] for r in rs]
        for x in nb:
            contrib[x] = [r["ma_diff"][ia[x]] - r["mb_diff"][ib[x]] for r in rs]
        top = sorted(contrib.items(), key=lambda kv: -abs(sum(kv[1]) / len(kv[1])))[:10]
        print("\n| 特征（新特征：A 模型的贡献；旧特征：A 模型 − B 模型的贡献） | 均值（95%） | 推向 A 线 / 推向 B 线 |")
        print("|---|---|---|")
        for x, v in top:
            print(f"| {x} | {_fmt(_boot(v, by))} | {sum(y > 0 for y in v)} / {sum(y < 0 for y in v)} |")
        for title, sub in (("B 第一步出某张牌、A 第一步没出这张：按 B 出的牌", None),):
            groups = defaultdict(list)
            for i, r in enumerate(rs):
                if r["B_first"][0] == "PlayCard" and r["A_first"] != r["B_first"]:
                    groups[r["B_first"][1]].append(i)
            print(f"\n**{title}**（回合末不同的分歧点；每组列出推得最多的 3 个特征，新特征是 A 模型的贡献，旧特征是 A − B 模型的贡献）\n")
            print("| B 出的牌 | 个数 | 回合（中位） | A − B 每局得分 | 推得最多的特征（均值） |")
            print("|---|---|---|---|---|")
            for card, ii in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:6]:
                means = sorted(((x, sum(contrib[x][i] for i in ii) / len(ii)) for x in contrib), key=lambda t: -abs(t[1]))[:3]
                t = sorted(rs[i]["pos"]["own_turn"] for i in ii)
                print(f"| {card} | {len(ii)} | {t[len(t) // 2]} | {sum(rs[i]['a_pts'] - rs[i]['b_pts'] for i in ii) / len(ii):+.2f} | "
                      + "；".join(f"{x} {v:+.3f}" for x, v in means) + " |")
        if flip and new:
            top_new = lambda i: max(new, key=lambda x: rs[i]["ma_diff"][ia[x]])
            tally = Counter(top_new(i) if rs[i]["ma_diff"][ia[top_new(i)]] > 1e-9 else "（没有新特征推向 A 线）"
                            for i in flip)
            print(f"\n意见相反的 {len(flip)} 个里，推向 A 线最多的新特征：" +
                  "，".join(f"{x} {c}" for x, c in tally.most_common()))
        print("\n**按分歧点所在的回合段**（hpphase 的三段：自己的第 1～4、5～7、8 回合起）\n")
        print("| 回合段 | 个数 | 意见相反 | A 模型偏 A 线（logit） | B 模型偏 A 线 | 新特征贡献 | 旧特征重拟合变化 | "
              "|新特征| 均值 | |旧特征变化| 均值 | A − B 每局得分 |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for lo, hi in ((0, 4), (5, 7), (8, 99)):
            ii = [i for i, r in enumerate(rs) if lo <= r["pos"]["own_turn"] <= hi]
            if not ii:
                continue
            m = lambda v: sum(v[i] for i in ii) / len(ii)
            pts = _boot([rs[i]["a_pts"] - rs[i]["b_pts"] for i in ii], [by[i] for i in ii])
            print(f"| {lo if lo else 1}～{hi if hi < 99 else ''} | {len(ii)} | {sum(1 for i in ii if i in set(flip))} | "
                  f"{m(dA):+.3f} | {m(dB):+.3f} | {m(newpart):+.3f} | {m(oldpart):+.3f} | "
                  f"{sum(abs(newpart[i]) for i in ii) / len(ii):.3f} | {sum(abs(oldpart[i]) for i in ii) / len(ii):.3f} | "
                  f"{_fmt(pts)} |")
        print()

    print("## 5. 之后旗皇那边打掉我方多少（A 线、B 线各自打下去）\n")
    print("| 库 | 个数 | 回合末我方 HP（A − B） | 旗皇下一回合后 HP（A − B） | 下一回合掉血（A − B） | "
          "第二回合后 HP（A − B） | 一回合内被杀 A / B | 两回合内被杀 A / B |")
    print("|---|---|---|---|---|---|---|---|")
    for b in banks + ["合计"]:
        rs = [r for r in diff if (b == "合计" or r["bank"] == b) and not r["A"]["won_in_turn"] and not r["B"]["won_in_turn"]]
        by = [(r["bank"], r["k"], r["seat"]) for r in rs]
        h1 = [(r, r["A"]["hp_after"][0] if r["A"]["hp_after"] else (0 if r["A"]["dead_in"] == 1 else None),
               r["B"]["hp_after"][0] if r["B"]["hp_after"] else (0 if r["B"]["dead_in"] == 1 else None)) for r in rs]
        h1 = [(r, a, bb) for r, a, bb in h1 if a is not None and bb is not None]
        hp_end = _boot([r["A"]["my_hp"] - r["B"]["my_hp"] for r in rs], by)
        after1 = _boot([max(a, 0) - max(bb, 0) for _, a, bb in h1], [(r["bank"], r["k"], r["seat"]) for r, _, _ in h1])
        loss1 = _boot([(r["A"]["my_hp"] - max(a, 0)) - (r["B"]["my_hp"] - max(bb, 0)) for r, a, bb in h1],
                      [(r["bank"], r["k"], r["seat"]) for r, _, _ in h1])
        h2 = [(r, r["A"]["hp_after"][1] if len(r["A"]["hp_after"]) > 1 else (0 if r["A"]["dead_in"] else None),
               r["B"]["hp_after"][1] if len(r["B"]["hp_after"]) > 1 else (0 if r["B"]["dead_in"] else None)) for r in rs]
        h2 = [(r, a, bb) for r, a, bb in h2 if a is not None and bb is not None]
        after2 = _boot([max(a, 0) - max(bb, 0) for _, a, bb in h2], [(r["bank"], r["k"], r["seat"]) for r, _, _ in h2])
        d1 = (sum(r["A"]["dead_in"] == 1 for r in rs), sum(r["B"]["dead_in"] == 1 for r in rs))
        d2 = (sum(r["A"]["dead_in"] in (1, 2) for r in rs), sum(r["B"]["dead_in"] in (1, 2) for r in rs))
        print(f"| {b} | {len(rs)} | {_fmt(hp_end)} | {_fmt(after1)} | {_fmt(loss1)} | {_fmt(after2)} | "
              f"{d1[0]} / {d1[1]} | {d2[0]} / {d2[1]} |")

    print("\n**按回合段**（各库合计，回合末不同、这回合没赢下的分歧点）\n")
    print("| 回合段 | 个数 | 下一回合掉血（A − B） | 两回合内被杀 A / B | A − B 每局得分 |")
    print("|---|---|---|---|---|")
    for lo, hi in ((0, 4), (5, 7), (8, 99)):
        rs = [r for r in diff if lo <= r["pos"]["own_turn"] <= hi and not r["A"]["won_in_turn"] and not r["B"]["won_in_turn"]]
        if not rs:
            continue
        h1 = [(r, r["A"]["hp_after"][0] if r["A"]["hp_after"] else (0 if r["A"]["dead_in"] == 1 else None),
               r["B"]["hp_after"][0] if r["B"]["hp_after"] else (0 if r["B"]["dead_in"] == 1 else None)) for r in rs]
        h1 = [(r, a, bb) for r, a, bb in h1 if a is not None and bb is not None]
        loss1 = _boot([(r["A"]["my_hp"] - max(a, 0)) - (r["B"]["my_hp"] - max(bb, 0)) for r, a, bb in h1],
                      [(r["bank"], r["k"], r["seat"]) for r, _, _ in h1])
        pts = _boot([r["a_pts"] - r["b_pts"] for r in rs], [(r["bank"], r["k"], r["seat"]) for r in rs])
        print(f"| {lo if lo else 1}～{hi if hi < 99 else ''} | {len(rs)} | {_fmt(loss1)} | "
              f"{sum(r['A']['dead_in'] in (1, 2) for r in rs)} / {sum(r['B']['dead_in'] in (1, 2) for r in rs)} | {_fmt(pts)} |")

    print("\n**「低估旗皇的斩杀速度」的检查**：所有回合末局面（A 线、B 线都算）上，A 模型和 B 模型的胜率估计，"
          "按之后两回合内有没有被杀分开。A 模型对「两回合内被杀」的局面比 B 模型更乐观，就是低估了斩杀速度。\n")
    print("| 库 | 两回合内被杀的局面数 | 这些局面 A 模型 p / B 模型 p | 没被杀的局面数 | 这些局面 A 模型 p / B 模型 p | "
          "logit 差（A − B）：被杀 − 没被杀 |")
    print("|---|---|---|---|---|---|")
    sig = lambda z: 1 / (1 + math.exp(-z))
    for b in banks:
        pts = []
        for r in diff:
            if r["bank"] != b:
                continue
            for j, side in enumerate(("A", "B")):
                if r[side]["won_in_turn"]:
                    continue
                pts.append((r[side]["dead_in"] in (1, 2), r["ma_logit"][j], r["mb_logit"][j], (r["bank"], r["k"], r["seat"])))
        dead = [p for p in pts if p[0]]
        live = [p for p in pts if not p[0]]
        gap = [(p[1] - p[2]) * (1 if p[0] else 0) for p in pts]
        dd = sum(p[1] - p[2] for p in dead) / max(len(dead), 1) - sum(p[1] - p[2] for p in live) / max(len(live), 1)
        print(f"| {b} | {len(dead)} | {sum(sig(p[1]) for p in dead) / max(len(dead), 1):.3f} / "
              f"{sum(sig(p[2]) for p in dead) / max(len(dead), 1):.3f} | {len(live)} | "
              f"{sum(sig(p[1]) for p in live) / max(len(live), 1):.3f} / {sum(sig(p[2]) for p in live) / max(len(live), 1):.3f} | "
              f"{dd:+.3f} |")


if __name__ == "__main__":
    if sys.argv[1] == "rows":
        rows(sys.argv[2:])
    else:
        report(sys.argv[2:])
