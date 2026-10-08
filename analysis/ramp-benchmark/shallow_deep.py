"""Ramp benchmark: where a shallow search (v2) and a deep one (mcts:800) part ways on the ramp side's decisions.

    python3 <this> --sample --mirror SELFPLAY.jsonl.gz --league PART1.jsonl.gz+PART2.jsonl.gz --out points.json
    python3 <this> --sample2 --league PART1.jsonl.gz+PART2.jsonl.gz --out points2.json     # the second design
    cd <svsim checkout at 9a6ea1c> && PYTHONPATH=. python3 <this> points.json --workers 4 --out results.jsonl
    python3 <this> --report results.jsonl --glossary card-glossary.md [--top10 OUT.md]

The architecture thread (2026-10-08 03:44Z); the method and the pre-registered reading are in README.md.
- Points: the ramp side's decisions (main phase, more than one legal move), 75 from each of four sources
  (the local ramp mirror self-play; the league rerun's elf-t/ramp-t, nemesis-t/ramp-t, ramp-t/pirate-t),
  25 per stage of the ramp side's own turn (1-4, 5-7, 8+), at most one per stage of a game, games taken in
  an order shuffled by a fixed seed; 50 of them, drawn by a fixed seed, also carry the noise floor.
- At a point: the shallow agent (v2) and the deep one (mcts:800+plan+learned+phased) each choose a move on
  the position; compared by search.mcts.action_key. When they differ, on the same 8 determinizations (from
  the ramp side's view) each move is played, v2s (the whole agent) plays the rest of the turn with the same
  seed on both lines, and the end of the turn is valued once by v2s's evaluation (the game's result if it
  ended). Regret = value after the deep move - value after the shallow one, a fraction of a win.
- The noise floor: on the 50, two deep searches with different seeds, the same regret (seed A - seed B).
The second design (the architecture thread, 03:48Z: the ramp bot as the ruler of the other three): from the
league rerun's three pairings against ramp-t, 100 decisions of each other deck (its own side, 34 / 33 / 33 by
stage) and 100 of ramp-t as the control, from the games those 300 didn't use; the same method; the report
ranks the decks by disagreement rate and mean regret, and the top 10 is each deck's 3 worst and ramp-t's 1.
Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import gzip
import json
import math
import random
import re
import statistics
import sys
from multiprocessing import Pool

SHALLOW = "v2"
DEEP = "mcts:800+plan+learned+phased"
FINISH = "v2s"
K = 8
STAGES = (("前期 1–4", 1, 4), ("中期 5–7", 5, 7), ("后期 8+", 8, 99))
PER_STAGE = 25
SAMPLE_SEED = 20261008
NOISE = 50
CATS = ("① 跳费 vs 铺场/抢节奏", "② 换血 vs 打脸", "③ 进化/超进化时机", "④ 留牌/不出牌", "⑤ 出哪张/先后", "⑥ 其他")


def stage_of(own_turn):
    return next(name for name, lo, hi in STAGES if lo <= own_turn <= hi)


# ---------------------------------------------------------------- sampling

def candidates(rec, sides):
    """(action index, side, own turn) of every decision of `sides` in the record."""
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply, legal_actions
    from svsim.core.enums import Phase
    from svsim.tools import records
    st = records.start(rec)
    out = []
    for i, a in enumerate(rec["actions"]):
        if st.over:
            break
        if st.phase == Phase.MAIN and st.active in sides and len(legal_actions(st)) > 1:
            out.append((i, st.active, st.players[st.active].turns_taken))
        apply(st, from_dict(a))
    return out


def sample(mirror, league, out):
    rng = random.Random(SAMPLE_SEED)
    sources = {"ramp-t/ramp-t": []}
    for line in gzip.open(mirror, "rt", encoding="utf-8"):
        g = json.loads(line)
        sources["ramp-t/ramp-t"].append(({"file": "mirror", "seed": g["seed"]}, g))
    for path in league.split("+"):
        for line in gzip.open(path, "rt", encoding="utf-8"):
            g = json.loads(line)
            if "ramp-t" in g["pair"] and g["pair"] != "ramp-t/ramp-t":
                sources.setdefault(g["pair"], []).append(({"file": path.split("/")[-1], "k": g["k"], "seat_a": g["seat_a"]},
                                                          g["record"]))
    points = []
    for src in sorted(sources):
        games = sources[src]
        rng.shuffle(games)
        need = {name: PER_STAGE for name, _, _ in STAGES}
        for ref, rec in games:
            if not any(need.values()):
                break
            names = rec.get("names") or ["ramp-t", "ramp-t"]
            sides = {p for p in (0, 1) if names[p] == "ramp-t"}
            by_stage = {}
            for i, side, own in candidates(rec, sides):
                by_stage.setdefault(stage_of(own), []).append((i, side, own))
            for name in [n for n, _, _ in STAGES]:
                if need[name] and by_stage.get(name):
                    i, side, own = rng.choice(by_stage[name])
                    points.append({"id": len(points), "source": src, "ref": ref, "at": i, "side": side,
                                   "own_turn": own, "stage": name, "record": rec})
                    need[name] -= 1
        print(f"  {src}：{sum(PER_STAGE - v for v in need.values())} 个点（{len(games)} 局）", flush=True)
    for j in random.Random(SAMPLE_SEED + 1).sample(range(len(points)), NOISE):
        points[j]["noise"] = True
    json.dump(points, open(out, "w", encoding="utf-8"))
    print(f"{len(points)} 个点写到 {out}")


QUOTA2 = {"前期 1–4": 34, "中期 5–7": 33, "后期 8+": 33}
CELLS2 = {"elf-t": "elf-t/ramp-t", "nemesis-t": "nemesis-t/ramp-t", "pirate-t": "ramp-t/pirate-t"}


def sample2(league, out):
    rng = random.Random(SAMPLE_SEED + 2)
    games = {c: [] for c in CELLS2.values()}
    for path in league.split("+"):
        for line in gzip.open(path, "rt", encoding="utf-8"):
            g = json.loads(line)
            if g["pair"] in games:
                games[g["pair"]].append(({"file": path.split("/")[-1], "pair": g["pair"], "k": g["k"],
                                          "seat_a": g["seat_a"]}, g["record"]))
    for c in games:
        games[c].sort(key=lambda x: (x[0]["k"], x[0]["seat_a"]))
        rng.shuffle(games[c])
    points, used = [], set()

    def take(deck, pool):
        need = dict(QUOTA2)
        for ref, rec in pool:
            if not any(need.values()):
                break
            key = (ref["pair"], ref["k"], ref["seat_a"])
            if key in used:
                continue
            side = rec["names"].index(deck)
            by_stage = {}
            for i, sd, own in candidates(rec, {side}):
                by_stage.setdefault(stage_of(own), []).append((i, sd, own))
            took = False
            for name in QUOTA2:
                if need[name] and by_stage.get(name):
                    i, sd, own = rng.choice(by_stage[name])
                    points.append({"id": len(points), "deck": deck, "source": ref["pair"], "ref": ref, "at": i,
                                   "side": sd, "own_turn": own, "stage": name, "record": rec})
                    need[name] -= 1
                    took = True
            if took:
                used.add(key)
        print(f"  {deck}：{sum(QUOTA2.values()) - sum(need.values())} 个点", flush=True)
    for deck, cell in CELLS2.items():
        take(deck, games[cell])
    pooled = [x for c in CELLS2.values() for x in games[c]]
    rng.shuffle(pooled)
    take("ramp-t", pooled)
    for j in random.Random(SAMPLE_SEED + 3).sample(range(len(points)), NOISE):
        points[j]["noise"] = True
    json.dump(points, open(out, "w", encoding="utf-8"))
    print(f"{len(points)} 个点写到 {out}")


# ---------------------------------------------------------------- one point

def inner_search(agent):
    inner = agent
    while not (hasattr(inner, "search") and hasattr(inner.search, "last_root")):
        inner = inner.base
    return inner.search


def describe(s, a, name):
    from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
    me = s.active

    def nm(uid):
        if uid is not None and uid < 0:
            return "对手主战者" if -uid - 1 != me else "自己主战者"
        c = s.on_field(uid) or s.in_hand(me, uid)
        return name(c.defn) if c is not None else str(uid)
    tg = lambda a: ("，目标 " + "、".join(nm(x) for x in a.targets)) if getattr(a, "targets", None) else ""
    if isinstance(a, PlayCard):
        c = s.in_hand(me, a.uid)
        return f"出 {name(c.defn) if c else a.uid}{tg(a)}"
    if isinstance(a, Attack):
        return f"{nm(a.attacker)} 攻击 {nm(a.target)}"
    if isinstance(a, Evolve):
        return f"{'超进化' if a.super_ else '进化'} {nm(a.uid)}{tg(a)}"
    if isinstance(a, EndTurn):
        return "结束回合"
    return {"UseBonusPP": "用额外 PP"}.get(type(a).__name__, type(a).__name__)


def kind(s, a):
    """A move as the categories read it: (what, detail)."""
    from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
    from svsim.search.race import ramps
    if isinstance(a, Evolve):
        return "evolve", None
    if isinstance(a, EndTurn):
        return "end", None
    if isinstance(a, PlayCard):
        c = s.in_hand(s.active, a.uid)
        return ("ramp" if c is not None and ramps(c.defn) else "play"), None
    if isinstance(a, Attack):
        return "attack", "face" if a.target is not None and a.target < 0 else "follower"
    return "other", None


def category(s, a, b):
    (ka, da), (kb, db) = kind(s, a), kind(s, b)
    ks = {ka, kb}
    if "evolve" in ks:
        return CATS[2]
    if "end" in ks and ks & {"play", "ramp"}:
        return CATS[3]
    if "ramp" in ks and ks != {"ramp"}:
        return CATS[0]
    if ka == kb == "attack" and {da, db} == {"face", "follower"}:
        return CATS[1]
    if ks <= {"play", "ramp", "attack"} and ks & {"play", "ramp"}:
        return CATS[4]
    return CATS[5]


def position(s, p, name):
    """The position as Salem reads it: own turn, PP, leaders, hands, boards."""
    me, op = s.players[p], s.players[1 - p]
    unit = lambda c: f"{name(c.defn)} {c.atk}/{c.life}" + ("（已进化）" if c.evolved else "")
    return {"own_turn": me.turns_taken, "pp": f"{me.pp}/{me.max_pp}", "ep": me.ep, "sep": me.sep,
            "hp": me.leader_hp, "opp_hp": op.leader_hp, "hand": [name(c.defn) for c in me.hand],
            "field": [unit(c) for c in me.field], "opp_field": [unit(c) for c in op.field],
            "opp_hand": len(op.hand), "deck": len(me.deck), "opp_deck": len(op.deck)}


def after_value(agent, search, s, move, seed, p, line=None):
    """The ramp side's win chance after `move` on the determinized position `s`, the rest of the turn played
    by v2s, valued once at the turn's end by v2s's evaluation (the game's result if it ends)."""
    from svsim.core.engine import apply, legal_actions
    from svsim.search.evaluate import evaluate
    t = s.clone()
    apply(t, move)
    search.rng = random.Random(seed)
    search._next = None
    while not t.over and t.active == p:
        a = agent.act(t, legal_actions(t))
        if line is not None:
            line.append(describe(t, a, plain_name))
        apply(t, a)
    if t.over:
        return 1.0 if t.winner == p else 0.0 if t.winner == 1 - p else 0.5
    score = evaluate(t, p, search.weights, player_moves_next=False)
    return 1 / (1 + math.exp(-max(min(score / 8.0, 60.0), -60.0)))


def plain_name(defn):
    return defn.name_zh or defn.name


def paired(finish, search, st, p, a, b, seed, lines=False):
    from svsim.core.view import determinize
    va, vb, la, lb = [], [], [], []
    for j in range(K):
        d = determinize(st, p, random.Random(seed * 1000 + 500 + j))
        xa, xb = ([], []) if lines and j == 0 else (None, None)
        va.append(after_value(finish, search, d, a, seed * 1000 + 700 + j, p, xa))
        vb.append(after_value(finish, search, d, b, seed * 1000 + 700 + j, p, xb))
        if xa is not None:
            la, lb = xa, xb
    return sum(va) / K, sum(vb) / K, la, lb


def job(pt):
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply, legal_actions
    from svsim.search.mcts import _locator, action_key
    from svsim.tools import records
    from svsim.tools.arena import make_agent
    rec, p, seed = pt["record"], pt["side"], SAMPLE_SEED * 1000 + pt["id"]
    st = records.start(rec)
    for a in rec["actions"][:pt["at"]]:
        apply(st, from_dict(a))
    assert st.active == p
    legal = legal_actions(st)
    where = _locator(st, p)
    shallow = make_agent(SHALLOW, 2 * seed).act(st.clone(), legal)
    deep = make_agent(DEEP, 2 * seed + 1).act(st.clone(), legal)
    finish = make_agent(FINISH, 7)
    search = inner_search(finish)
    out = {k: pt[k] for k in ("id", "deck", "source", "ref", "at", "side", "own_turn", "stage") if k in pt}
    out.update(legal=len(legal), position=position(st, p, plain_name), shallow=describe(st, shallow, plain_name),
               deep=describe(st, deep, plain_name), differ=action_key(st, shallow, where) != action_key(st, deep, where))
    if out["differ"]:
        vs, vd, ls, ld = paired(finish, search, st, p, shallow, deep, seed, lines=True)
        out.update(v_shallow=vs, v_deep=vd, regret=vd - vs, category=category(st, shallow, deep),
                   line_shallow=ls, line_deep=ld)
    else:
        out.update(regret=0.0, category=None)
    if pt.get("noise"):
        deep2 = make_agent(DEEP, 2 * seed + 7777).act(st.clone(), legal)
        out["noise_differ"] = action_key(st, deep, where) != action_key(st, deep2, where)
        out["noise_deep2"] = describe(st, deep2, plain_name)
        if out["noise_differ"]:
            v2, v1, _, _ = paired(finish, search, st, p, deep2, deep, seed + 3)
            out["noise_regret"] = v1 - v2
            out["noise_category"] = category(st, deep2, deep)
        else:
            out["noise_regret"] = 0.0
    return out


def read_clean(path):
    good = []
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError:
            break
        good.append(line if line.endswith("\n") else line + "\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(good)
    return [json.loads(line) for line in good]


# ---------------------------------------------------------------- report

def glossary(path):
    """official full name -> (common name, cost and stats), from analysis/card-glossary.md (read, not edited)."""
    out = {}
    for line in open(path, encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0].startswith("**") and cells[2]:
            out[cells[2]] = (cells[0].strip("*"), cells[1])
    return out


def salem_text(text, gl, stats_of):
    """Every full card name in `text` as its common name, the first mention of each with its cost and stats; a card
    the glossary doesn't list keeps its official name, marked for Salem to name (only he edits the glossary)."""
    seen = set()

    def sub(m):
        full = m.group(0)
        listed = full in gl
        common, stats = gl.get(full, (full, stats_of.get(full, "")))   # not in the glossary: the official name
        if common in seen or not stats:
            return common
        seen.add(common)
        return f"{common}（{stats}）" if listed else f"{common}（{stats}；词表无此牌，译名待 Salem 定）"
    names = sorted(set(gl) | set(stats_of), key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(n) for n in names if n))
    return pattern.sub(sub, text)


def card_stats():
    """full Chinese name -> cost and stats, for cards the glossary doesn't list (from the card pool)."""
    try:
        from svsim.cards.pool import POOL
        from svsim.core.enums import CardType
    except ImportError:
        return {}
    out = {}
    for d in POOL.values():
        kind = {CardType.SPELL: "法术", CardType.AMULET: "护符", CardType.COUNTDOWN_AMULET: "倒数护符"}.get(d.type)
        if d.type in (CardType.FOLLOWER, CardType.SPELL, CardType.AMULET, CardType.COUNTDOWN_AMULET):
            out[d.name_zh or d.name] = f"{d.cost}费 {kind}" if kind else f"{d.cost}费 {d.atk}/{d.life}"
    return out


def pct(xs, q):
    return sorted(xs)[min(len(xs) - 1, int(q * len(xs)))] if xs else float("nan")


def summary(label, regs):
    if not regs:
        return f"  {label}：没有点"
    return (f"  {label}：{len(regs)} 个点，中位 {statistics.median(regs):+.3f}，p90 {pct(regs, 0.9):+.3f}，"
            f"平均 {sum(regs) / len(regs):+.3f}；≥ 0.05 {sum(r >= 0.05 for r in regs) / len(regs):.0%}，"
            f"≥ 0.10 {sum(r >= 0.10 for r in regs) / len(regs):.0%}（{sum(r >= 0.10 for r in regs)} 个）")


def report(path, gl_path, top10=None):
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    if rows and "deck" in rows[0]:
        return report2(rows, gl_path, top10)
    print(f"条件：对手卡表已知（牌序、手牌未知）。{len(rows)} 个跳费龙决策点；浅 = {SHALLOW}，深 = {DEEP}，"
          f"不同时在同 {K} 个确定化上各走一遍，余下这一回合由 {FINISH} 打完，遗憾 = 深 − 浅（胜率，0.10 = 10 点）。\n")
    print("分歧率（浅、深第一步不同的点）：")
    for name, _, _ in STAGES:
        sub = [r for r in rows if r["stage"] == name]
        print(f"  {name}：{sum(r['differ'] for r in sub)} / {len(sub)}（{sum(r['differ'] for r in sub) / max(len(sub), 1):.0%}）")
    print(f"  合计：{sum(r['differ'] for r in rows)} / {len(rows)}（{sum(r['differ'] for r in rows) / len(rows):.0%}）")
    for src in sorted({r["source"] for r in rows}):
        sub = [r for r in rows if r["source"] == src]
        print(f"  {src}：{sum(r['differ'] for r in sub)} / {len(sub)}")
    print("\n遗憾（全部点，没分歧的算 0）：")
    print(summary("合计", [r["regret"] for r in rows]))
    for name, _, _ in STAGES:
        print(summary(name, [r["regret"] for r in rows if r["stage"] == name]))
    print("只看有分歧的点：")
    print(summary("有分歧", [r["regret"] for r in rows if r["differ"]]))
    noise = [r for r in rows if "noise_regret" in r]
    print(f"\n噪声底（{len(noise)} 个点，两个不同种子的深搜，遗憾 = 种子 A − 种子 B）：")
    print(f"  分歧率 {sum(r['noise_differ'] for r in noise)} / {len(noise)}；同样这些点上浅深分歧 {sum(r['differ'] for r in noise)} / {len(noise)}")
    print(summary("深 − 深", [r["noise_regret"] for r in noise]))
    print(summary("深 − 深，取绝对值", [abs(r["noise_regret"]) for r in noise]))
    print(summary("同样这些点的深 − 浅", [r["regret"] for r in noise]))
    big = [r for r in rows if r["regret"] >= 0.10]
    print(f"\n遗憾 ≥ 0.10 的点：{len(big)} 个，按类型（占比的分母是这 {len(big)} 个）：")
    for c in CATS:
        sub = [r["regret"] for r in big if r["category"] == c]
        share = len(sub) / max(len(big), 1)
        print(f"  {c}：{len(sub)} 个（{share:.0%}）" + (f"，平均遗憾 {sum(sub) / len(sub):.3f}" if sub else ""))
    shares = {c: sum(r["category"] == c for r in big) / max(len(big), 1) for c in CATS}
    four = [shares[c] for c in CATS[:4]]
    if big and max(four) >= 0.40:
        verdict = f"系统性弱点在该类：{CATS[four.index(max(four))]}（{max(four):.0%}）"
    elif big and all(0.15 <= x <= 0.35 for x in four):
        verdict = "无单一类型主导"
    else:
        verdict = "两条都不满足，照实报各类占比"
    extra = [c for c in CATS[4:] if shares[c] >= 0.40]
    print(f"预登记的读法：{verdict}" + (f"；另外 {'、'.join(extra)} 占比 ≥ 40%" if extra else ""))
    print("所有有分歧的点按类型：")
    for c in CATS:
        sub = [r["regret"] for r in rows if r["differ"] and r["category"] == c]
        if sub:
            print(f"  {c}：{len(sub)} 个，平均遗憾 {sum(sub) / len(sub):+.3f}，≥ 0.10 的 {sum(x >= 0.10 for x in sub)} 个")
    if top10:
        write_top10(rows, gl_path, top10)


NAMES = {"elf-t": "连击妖", "nemesis-t": "机锋", "pirate-t": "旗皇", "ramp-t": "跳费龙"}


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def mean_ci(xs):
    n = len(xs)
    m = sum(xs) / n
    return m, 1.96 * math.sqrt(sum((x - m) ** 2 for x in xs) / max(n - 1, 1) / n)


def verdict(stats, label):
    """stats: deck -> (value, low, high). Ramp lowest and its high below the next lowest's low."""
    order = sorted(stats, key=lambda d: stats[d][0])
    ok = order[0] == "ramp-t" and stats["ramp-t"][2] < stats[order[1]][1]
    print(f"  {label} 从低到高：" + "，".join(f"{NAMES[d]} {stats[d][0]:.3f}（{stats[d][1]:.3f}～{stats[d][2]:.3f}）" for d in order))
    print(f"  → {'支持 Salem：跳费龙最简单' if ok else '不支持或分不开'}" +
          ("" if ok else f"（最低的是{NAMES[order[0]]}" + ("" if order[0] != "ramp-t" else f"，但区间上沿 {stats['ramp-t'][2]:.3f} 不低于次低{NAMES[order[1]]}的下沿 {stats[order[1]][1]:.3f}") + "）"))


def report2(rows, gl_path, top10=None):
    decks = ["elf-t", "nemesis-t", "pirate-t", "ramp-t"]
    print(f"条件：对手卡表已知（牌序、手牌未知）。{len(rows)} 个决策点（三套牌对跳费龙各 100，跳费龙 100 作对照）；"
          f"浅 = {SHALLOW}，深 = {DEEP}，不同时在同 {K} 个确定化上各走一遍，余下这一回合由 {FINISH} 打完，"
          f"遗憾 = 深 − 浅（胜率，0.10 = 10 点）。\n")
    print("按牌：分歧率（Wilson 95%）、平均遗憾（95%，没分歧记 0）、遗憾 ≥ 0.10 的点")
    div, reg = {}, {}
    for d in decks:
        sub = [r for r in rows if r["deck"] == d]
        k = sum(r["differ"] for r in sub)
        lo, hi = wilson(k, len(sub))
        m, h = mean_ci([r["regret"] for r in sub])
        div[d], reg[d] = (k / len(sub), lo, hi), (m, m - h, m + h)
        big = sum(r["regret"] >= 0.10 for r in sub)
        print(f"  {NAMES[d]}：{len(sub)} 个，分歧 {k}（{k / len(sub):.0%}，{lo:.0%}～{hi:.0%}），平均遗憾 {m:+.3f} ± {h:.3f}，"
              f"有分歧的点平均 {sum(r['regret'] for r in sub if r['differ']) / max(k, 1):+.3f}，≥ 0.10 的 {big} 个")
        for name, _, _ in STAGES:
            ss = [r for r in sub if r["stage"] == name]
            print(f"      {name}：分歧 {sum(r['differ'] for r in ss)} / {len(ss)}，平均遗憾 {sum(r['regret'] for r in ss) / max(len(ss), 1):+.3f}，"
                  f"≥ 0.10 的 {sum(r['regret'] >= 0.10 for r in ss)} 个")
    print("\n预登记第 2 条（跳费龙是否最简单）：")
    verdict(div, "分歧率")
    verdict(reg, "平均遗憾")
    noise = [r for r in rows if "noise_regret" in r]
    print(f"\n噪声底（{len(noise)} 个点，两个不同种子的深搜，遗憾 = 种子 A − 种子 B）：")
    print(f"  分歧率 {sum(r['noise_differ'] for r in noise)} / {len(noise)}；同样这些点上浅深分歧 {sum(r['differ'] for r in noise)} / {len(noise)}")
    print(summary("深 − 深", [r["noise_regret"] for r in noise]))
    print(summary("深 − 深，取绝对值", [abs(r["noise_regret"]) for r in noise]))
    print(summary("同样这些点的深 − 浅", [r["regret"] for r in noise]))
    big = [r for r in rows if r["regret"] >= 0.10]
    print(f"\n遗憾 ≥ 0.10 的点：{len(big)} 个，按类型（预登记第 1 条，分母是这 {len(big)} 个）：")
    for c in CATS:
        sub = [r["regret"] for r in big if r["category"] == c]
        print(f"  {c}：{len(sub)} 个（{len(sub) / max(len(big), 1):.0%}）" + (f"，平均遗憾 {sum(sub) / len(sub):.3f}" if sub else "")
              + "；按牌 " + "、".join(f"{NAMES[d]} {sum(r['category'] == c and r['deck'] == d for r in big)}" for d in decks))
    shares = {c: sum(r["category"] == c for r in big) / max(len(big), 1) for c in CATS}
    four = [shares[c] for c in CATS[:4]]
    if big and max(four) >= 0.40:
        v = f"系统性弱点在该类：{CATS[four.index(max(four))]}（{max(four):.0%}）"
    elif big and all(0.15 <= x <= 0.35 for x in four):
        v = "无单一类型主导"
    else:
        v = "两条都不满足，照实报各类占比"
    extra = [c for c in CATS[4:] if shares[c] >= 0.40]
    print(f"预登记的读法：{v}" + (f"；另外 {'、'.join(extra)} 占比 ≥ 40%" if extra else ""))
    print("所有有分歧的点按类型：")
    for c in CATS:
        sub = [r["regret"] for r in rows if r["differ"] and r["category"] == c]
        if sub:
            print(f"  {c}：{len(sub)} 个，平均遗憾 {sum(sub) / len(sub):+.3f}，≥ 0.10 的 {sum(x >= 0.10 for x in sub)} 个")
    if top10:
        pick = []
        for d, n in (("elf-t", 3), ("nemesis-t", 3), ("pirate-t", 3), ("ramp-t", 1)):
            pick += sorted((r for r in rows if r["deck"] == d and r["differ"]), key=lambda r: -r["regret"])[:n]
        write_top10(pick, gl_path, top10, by_deck=True)


def write_top10(rows, gl_path, out, by_deck=False):
    gl = glossary(gl_path)
    stats_of = card_stats()
    opp = {"ramp-t/ramp-t": "跳费龙", "elf-t/ramp-t": "连击妖", "nemesis-t/ramp-t": "机锋", "ramp-t/pirate-t": "旗皇"}
    top = rows if by_deck else sorted((r for r in rows if r["differ"]), key=lambda r: -r["regret"])[:10]
    title = ("# 三套牌对跳费龙：浅搜和深搜走法不同、差得最多的局面（每套牌 3 个，跳费龙 1 个，请你判断）" if by_deck
             else "# 跳费龙：浅搜和深搜走法不同、差得最多的 10 个局面（请你判断）")
    where = ("局面来自 400 个决策点：连击妖、机锋、旗皇在联赛里对跳费龙的局各 100 个，跳费龙自己 100 个作对照（全装机态）。"
             if by_deck else "局面来自约 300 个跳费龙决策点（跳费龙镜像自对弈，加上联赛里跳费龙对连击妖、机锋、旗皇各 75 个）。")
    head = [title, "",
            "条件：对手卡表已知（牌序、手牌未知）。",
            f"做法：在同一个局面上，浅搜（v2，每步 100 次模拟）和深搜（每步 800 次模拟）各选一步。两步不一样时，各走一遍，"
            f"这一回合剩下的都由 v2s 打完，比回合结束时 bot 估的胜率。对手没见过的牌按已知卡表发 {K} 次，取平均。",
            "「差多少」是 bot 估的胜率差：深搜那步减去浅搜那步，单位是胜率点。这个差是 bot 自己估的，它也可能估错；哪步更好请你来判。",
            "「后面这样打」是 8 次里第 1 次的走法，只是举例，其他几次可能不同。",
            where, ""]
    body = []
    for n, r in enumerate(top, 1):
        q = r["position"]
        me = NAMES.get(r.get("deck"), "跳费龙")
        them = "跳费龙" if me != "跳费龙" else opp.get(r["source"], r["source"])
        body += [f"## {n}. {me}对{them}，{me}的第 {r['own_turn']} 回合，差 {100 * r['regret']:.0f} 个胜率点",
                 "",
                 f"- 局面：PP {q['pp']}，进化点 {q['ep']}、超进化点 {q['sep']}；自己主战者 {q['hp']} 血，对手 {q['opp_hp']} 血；"
                 f"自己牌库 {q['deck']} 张，对手手牌 {q['opp_hand']} 张。",
                 f"- 自己手牌：{'、'.join(q['hand']) or '无'}",
                 f"- 自己场上：{'、'.join(q['field']) or '无'}",
                 f"- 对手场上：{'、'.join(q['opp_field']) or '无'}",
                 f"- 浅搜：{r['shallow']}" + (f"；后面这样打：{' → '.join(r['line_shallow'])}" if r.get("line_shallow") else ""),
                 f"- 深搜：{r['deep']}" + (f"；后面这样打：{' → '.join(r['line_deep'])}" if r.get("line_deep") else ""),
                 f"- bot 估的胜率：浅搜那步之后 {100 * r['v_shallow']:.0f}%，深搜那步之后 {100 * r['v_deep']:.0f}%。",
                 f"- 出处：{r['source']}，{json.dumps(r['ref'], ensure_ascii=False)}，第 {r['at']} 步。", ""]
    text = "\n".join(head) + "\n" + salem_text("\n".join(body), gl, stats_of)
    open(out, "w", encoding="utf-8").write(text)
    print(f"\n写到 {out}")


def main():
    if "--sample" in sys.argv:
        ap = argparse.ArgumentParser()
        ap.add_argument("--sample", action="store_true")
        ap.add_argument("--mirror", required=True)
        ap.add_argument("--league", required=True)
        ap.add_argument("--out", required=True)
        a = ap.parse_args()
        sample(a.mirror, a.league, a.out)
        return
    if "--sample2" in sys.argv:
        ap = argparse.ArgumentParser()
        ap.add_argument("--sample2", action="store_true")
        ap.add_argument("--league", required=True)
        ap.add_argument("--out", required=True)
        a = ap.parse_args()
        sample2(a.league, a.out)
        return
    if "--report" in sys.argv:
        ap = argparse.ArgumentParser()
        ap.add_argument("--report", required=True)
        ap.add_argument("--glossary", required=True)
        ap.add_argument("--top10", default=None)
        a = ap.parse_args()
        report(a.report, a.glossary, a.top10)
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("points")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", type=int, nargs="*", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    pts = json.load(open(a.points, encoding="utf-8"))
    import os
    done = {r["id"] for r in read_clean(a.out)} if os.path.exists(a.out) else set()
    jobs = [p for p in pts if p["id"] not in done and (a.only is None or p["id"] in a.only)]
    with Pool(a.workers) as pool, open(a.out, "a", encoding="utf-8") as fh:
        for n, r in enumerate(pool.imap_unordered(job, jobs, chunksize=1), 1):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 10 == 0:
                print(f"  {n} / {len(jobs)}", flush=True)


if __name__ == "__main__":
    main()
