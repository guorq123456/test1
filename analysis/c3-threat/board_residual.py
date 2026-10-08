"""C3 (opponent board threat): which board quantities the installed evaluator's turn-end residual still has a
slope on (the architecture thread 17:1x).

    cd <svsim checkout with the installed models (352ae51 or later)> && PYTHONPATH=. python3 <this> \
        --games A.jsonl.gz+B.jsonl.gz --out points.jsonl [--workers 4]
    python3 <this> --report points.jsonl [--boot 200]

Every league game is replayed; at the end of each player's turn the installed evaluation (learn.phased.PhasedLearned,
that pairing's "ended" model; since 352ae51 the ramp-t mirror, the elf-t mirror and elf-t vs nemesis-t are the C2
models) gives that player's win chance p = 1 / (1 + exp(-score / 8)); the residual is the game's result minus p,
as in analysis/evaluator-gaps/calibration.py. Each point keeps board quantities of both sides at that moment (the
opponent moves next): followers, the attack they can make next turn (not "can't attack"; a follower's extra attacks
counted), their total defense, Wards, the board threat as learn.features computes it (attack past the enemy's Ward
defense), leader HP, and the removal role of the player's own hand (learn.roles), plus controls (seat, own turn,
cards in hand, cards it cannot pay for next turn), and since the bonus-PP check (the architecture thread 17:44) each
side's bonus play point still available (`bonus`) and the player's own cards in hand costing 2 or less (`cheap`).
The report regresses the residual on each quantity's slope in each stage of the game (1-4, 5-7, 8+) with the
own turn and the side (deck, opponent) held fixed, then on derived candidates; 95% intervals, games resampled.
Only sides with a pairing model (the 11 of analysis/evaluator-gaps) are used.
Condition: the opponent's 40-card list is known (order and hand not).
"""
import gzip
import json
import math
import random
import sys
from multiprocessing import Pool

MODELED = {("elf-t", "elf-t"), ("elf-t", "nemesis-t"), ("elf-t", "ramp-t"), ("nemesis-t", "elf-t"),
           ("nemesis-t", "ramp-t"), ("pirate-t", "elf-t"), ("pirate-t", "pirate-t"), ("ramp-t", "elf-t"),
           ("ramp-t", "nemesis-t"), ("ramp-t", "pirate-t"), ("ramp-t", "ramp-t")}
STAGES = ((1, 4), (5, 7), (8, 99))


def stage(t):
    return next(i for i, (lo, hi) in enumerate(STAGES) if lo <= t <= hi)


def _side(st, side, prop, Keyword, threat):
    p = st.players[side]
    fs = p.followers
    return {"hp": p.leader_hp, "n": len(fs),
            "atk": sum(f.atk * max(1, f.max_attacks) for f in fs if not prop(f, "cant_attack")),
            "life": sum(max(f.life, 0) for f in fs), "ward": sum(1 for f in fs if f.keywords & Keyword.WARD),
            "threat": threat(st, side), "bonus": int(p.bonus_ready)}


def game_points(g):
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply
    from svsim.core.enums import Keyword
    from svsim.core.script import prop
    from svsim.learn.features import _board_threat
    from svsim.learn.phased import PhasedLearned
    from svsim.learn.roles import card_roles
    from svsim.tools import records
    global _EVAL
    if "_EVAL" not in globals():
        _EVAL = PhasedLearned()
    rec = g["record"]
    st = records.start(rec)
    names = rec.get("names") or [None, None]
    out = []
    for a in rec["actions"]:
        act = from_dict(a)
        p = st.active
        apply(st, act)
        if isinstance(act, EndTurn) and not st.over and st.active != p:
            if (names[p], names[1 - p]) not in MODELED:
                continue
            me = st.players[p]
            score = _EVAL.score(st, p, player_moves_next=False)
            prob = 1 / (1 + math.exp(-max(min(score / 8.0, 60.0), -60.0)))
            result = 0.5 if g["winner"] is None else 1.0 if g["winner"] == p else 0.0
            mine = _side(st, p, prop, Keyword, _board_threat)
            theirs = _side(st, 1 - p, prop, Keyword, _board_threat)
            x = {"pair": g["pair"], "k": g["k"], "seat_a": g["seat_a"], "deck": names[p], "opp": names[1 - p],
                 "first": int(st.first == p), "own_turn": me.turns_taken, "p": prob, "result": result,
                 "hand": len(me.hand), "dead": sum(1 for c in me.hand if c.defn.cost > me.max_pp + 1),
                 "removal": sum(card_roles(c.defn)[1] for c in me.hand),
                 "cheap": sum(1 for c in me.hand if c.cost <= 2)}
            x.update({f"my_{k}": v for k, v in mine.items()})
            x.update({f"op_{k}": v for k, v in theirs.items()})
            out.append(x)
    return out


def collect(paths, out, workers):
    games = [json.loads(line) for path in paths for line in gzip.open(path, "rt", encoding="utf-8")]
    n = 0
    with open(out, "w", encoding="utf-8") as f, Pool(workers) as pool:
        for pts in pool.imap_unordered(game_points, games, chunksize=8):
            for x in pts:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
            n += len(pts)
    print(f"{len(games)} games, {n} turn-end points (sides with a pairing model) -> {out}")


BASE = ("my_hp", "op_hp", "my_n", "op_n", "my_atk", "op_atk", "my_life", "op_life", "my_ward", "op_ward",
        "my_threat", "op_threat", "removal")
NAMES = {"my_hp": "我方领袖 HP", "op_hp": "对方领袖 HP", "my_n": "我方随从数", "op_n": "对方随从数",
         "my_atk": "我方下回合可攻击总攻击", "op_atk": "对方下回合可攻击总攻击", "my_life": "我方随从总体力",
         "op_life": "对方随从总体力", "my_ward": "我方守护数", "op_ward": "对方守护数",
         "my_threat": "我方场面威胁（过守护后能打脸的攻击）", "op_threat": "对方场面威胁（过我方守护后能打我脸的攻击）",
         "removal": "我方手牌的解场量（roles）"}


def _fit(pts, cols, nboot, seed=17):
    """OLS of the residual on `cols` (functions of a point) plus own-turn and side dummies and the seat;
    coefficients of `cols` with 95% intervals, games resampled."""
    import numpy as np
    sides = sorted({(x["deck"], x["opp"]) for x in pts})
    X = []
    for x in pts:
        t = min(x["own_turn"], 12)
        X.append([f(x) for _, f in cols] + [float(x["first"])] + [1.0 if t == u else 0.0 for u in range(2, 13)]
                 + [1.0 if (x["deck"], x["opp"]) == sd else 0.0 for sd in sides[1:]] + [1.0])
    X = np.array(X)
    y = np.array([x["result"] - x["p"] for x in pts])
    k = len(cols)
    beta = np.linalg.lstsq(X, y, rcond=None)[0][:k]
    idx = {}
    for i, x in enumerate(pts):
        idx.setdefault((x["pair"], x["k"], x["seat_a"]), []).append(i)
    keys = list(idx)
    rng = random.Random(seed)
    bs = []
    for _ in range(nboot):
        rows = [i for _ in keys for i in idx[keys[rng.randrange(len(keys))]]]
        bs.append(np.linalg.lstsq(X[rows], y[rows], rcond=None)[0][:k])
    bs = np.array(bs)
    return beta, np.percentile(bs, 2.5, axis=0), np.percentile(bs, 97.5, axis=0)


def _print(title, cols, beta, lo, hi):
    print(f"\n**{title}**\n")
    print("| 量 | 系数（95%） | |")
    print("|---|---|---|")
    for (name, _), b, l, h in zip(cols, beta, lo, hi):
        mark = "**" if l > 0 or h < 0 else ""
        print(f"| {name} | {mark}{b:+.4f}（{l:+.4f}～{h:+.4f}）{mark} | {'不含 0' if mark else ''} |")


def report(path, nboot):
    pts = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    print(f"条件：对手卡表已知（牌序、手牌未知）。{len(pts)} 个回合末的点（有配对模型的 11 个一方）；残差 = 实际结果 − 装机评估器的胜率；"
          f"固定自己的第几回合、卡组 · 对手和先后手；区间 95%，按局重抽 {nboot} 次。")
    # 1. the base quantities, all at once
    cols = [(NAMES[k], (lambda k: lambda x: float(x[k]))(k)) for k in BASE] + \
           [("手牌张数", lambda x: float(x["hand"])), ("下回合付不起的手牌张数", lambda x: float(x["dead"]))]
    _print("1. 基础量同时回归", cols, *_fit(pts, cols, nboot))
    # 2. each base quantity's slope by stage (one quantity at a time, controls as above)
    print("\n**2. 每个量分回合段的斜率**（一次一个量，三段各一个斜率；控制量同上）\n")
    print("| 量 | 前期 1–4 | 中期 5–7 | 后期 8+ |")
    print("|---|---|---|---|")
    for k in BASE:
        c = [(f"{k}@{i}", (lambda k, i: lambda x: float(x[k]) if stage(x["own_turn"]) == i else 0.0)(k, i))
             for i in range(3)]
        b, l, h = _fit(pts, c, nboot)
        cells = []
        for j in range(3):
            mark = "**" if l[j] > 0 or h[j] < 0 else ""
            cells.append(f"{mark}{b[j]:+.4f}（{l[j]:+.4f}～{h[j]:+.4f}）{mark}")
        print(f"| {NAMES[k]} | " + " | ".join(cells) + " |")
    # 3. derived candidates (functional, no deck ids)
    derived = [
        ("对方威胁 ÷ 我方 HP（封顶 1.5）", lambda x: min(x["op_threat"] / max(x["my_hp"], 1), 1.5)),
        ("对方威胁 ≥ 我方 HP（下回合场面斩杀）", lambda x: float(x["op_threat"] >= x["my_hp"])),
        ("对方随从数 ≥ 3", lambda x: float(x["op_n"] >= 3)),
        ("对方随从总体力 − 我方手牌解场量 × 3（正部）", lambda x: max(x["op_life"] - 3 * x["removal"], 0.0)),
        ("对方随从数 − 我方随从数", lambda x: float(x["op_n"] - x["my_n"])),
        ("对方下回合可攻击总攻击 × 后期", lambda x: float(x["op_atk"]) if x["own_turn"] >= 8 else 0.0),
        ("我方威胁 ÷ 对方 HP（封顶 1.5）", lambda x: min(x["my_threat"] / max(x["op_hp"], 1), 1.5)),
    ]
    _print("3. 派生候选，一次一个（控制量同上）", [], [], [], [])
    print("| 候选 | 系数（95%） | |")
    print("|---|---|---|")
    for name, f in derived:
        b, l, h = _fit(pts, [(name, f)], nboot)
        mark = "**" if l[0] > 0 or h[0] < 0 else ""
        print(f"| {name} | {mark}{b[0]:+.4f}（{l[0]:+.4f}～{h[0]:+.4f}）{mark} | {'不含 0' if mark else ''} |")


def main():
    if "--report" in sys.argv:
        nboot = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 200
        report(sys.argv[sys.argv.index("--report") + 1], nboot)
        return
    paths = sys.argv[sys.argv.index("--games") + 1].split("+")
    out = sys.argv[sys.argv.index("--out") + 1]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    collect(paths, out, workers)


if __name__ == "__main__":
    main()
