"""Where the installed evaluator's win chances miss the games' results: calibration by seat, and the residual
against candidate quantities the features may not see (the architecture thread 05:45Z, main line C: the
second player's disadvantage, the conditional value of a hand).

    cd <svsim checkout with the installed models> && PYTHONPATH=. python3 <this> --games A.jsonl.gz+B.jsonl.gz \
        --out points.jsonl [--workers 4] [--every 1]
    python3 <this> --report points.jsonl [--boot 1000]
    python3 <this> --multi points.jsonl [--boot 200]       # all candidates at once, stage and pairing fixed

Every game of the league files (league.py's records) is replayed; at the end of each player's turn the
installed evaluation (learn.phased.PhasedLearned, the "ended" model of that pairing, a mirror's alias
included) gives that player's win chance p = 1 / (1 + exp(-score / 8)), the same squash the search uses.
Each point keeps p, the game's result for that player (1 / 0.5 / 0), whether the player went first, its own
turn number, and quantities the features hold only indirectly or not at all: cards in hand, cards in hand it
cannot pay for next turn (cost > max PP + 1), the hand's total cost, evolve points, max PP.
The report: (1) calibration (mean result - mean p) overall, by seat and by seat x stage of the game;
(2) the residual (result - p) regressed on each quantity in turn, within seat, the slope with its interval.
Intervals: 95%, games resampled (the points of one game are not independent).
Condition: the opponent's 40-card list is known (order and hand not).
"""
import gzip
import json
import math
import random
import sys
from multiprocessing import Pool

STAGES = (("前期 1–4", 1, 4), ("中期 5–7", 5, 7), ("后期 8+", 8, 99))


def stage_of(t):
    return next(name for name, lo, hi in STAGES if lo <= t <= hi)


def game_points(g):
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply
    from svsim.learn.phased import PhasedLearned
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
            me = st.players[p]
            score = _EVAL.score(st, p, player_moves_next=False)
            prob = 1 / (1 + math.exp(-max(min(score / 8.0, 60.0), -60.0)))
            result = 0.5 if g["winner"] is None else 1.0 if g["winner"] == p else 0.0
            hand = list(me.hand)
            out.append({"pair": g["pair"], "k": g["k"], "seat_a": g["seat_a"], "deck": names[p], "opp": names[1 - p],
                        "first": st.first == p, "own_turn": me.turns_taken, "p": prob, "result": result,
                        "hand": len(hand), "dead": sum(1 for c in hand if c.defn.cost > me.max_pp + 1),
                        "hand_cost": sum(c.defn.cost for c in hand), "ep": me.ep, "sep": me.sep, "max_pp": me.max_pp,
                        "followers": len(me.followers), "op_followers": len(st.players[1 - p].followers)})
    return out


def collect(paths, out, workers):
    games = []
    for path in paths:
        for line in gzip.open(path, "rt", encoding="utf-8"):
            games.append(json.loads(line))
    n = 0
    with open(out, "w", encoding="utf-8") as f, Pool(workers) as pool:
        for pts in pool.imap_unordered(game_points, games, chunksize=8):
            for x in pts:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
            n += len(pts)
    print(f"{len(games)} 局，{n} 个回合末的点写到 {out}")


def boot_ci(groups, stat, nboot, seed=17):
    rng = random.Random(seed)
    keys = list(groups)
    xs = []
    for _ in range(nboot):
        sample = [x for _ in keys for x in groups[keys[rng.randrange(len(keys))]]]
        v = stat(sample)
        if v is not None:
            xs.append(v)
    xs.sort()
    return xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]


def gap(pts):
    return (sum(x["result"] for x in pts) - sum(x["p"] for x in pts)) / len(pts) if pts else None


def slope(pts, key):
    if len(pts) < 10:
        return None
    xs = [x[key] for x in pts]
    rs = [x["result"] - x["p"] for x in pts]
    mx, mr = sum(xs) / len(xs), sum(rs) / len(rs)
    sxx = sum((a - mx) ** 2 for a in xs)
    return sum((a - mx) * (r - mr) for a, r in zip(xs, rs)) / sxx if sxx else None


def report(path, nboot):
    pts = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    by_game = lambda sel: {key: grp for key, grp in _group(sel).items()}
    print("条件：对手卡表已知（牌序、手牌未知）。每个点是一方回合结束时，装机态评估器给这一方的胜率 p 和这局的实际结果；"
          "差 = 实际 − p 的平均（正：评估器低估了这一方）；区间 95%，按局重抽。\n")
    print("| 范围 | 点数 | 局数 | 平均 p | 实际 | 差（95%） |")
    print("|---|---|---|---|---|---|")
    rows = [("全部", lambda x: True), ("先手方", lambda x: x["first"]), ("后手方", lambda x: not x["first"])]
    rows += [(f"{'先手' if f else '后手'} · {name}", (lambda f, lo, hi: lambda x: x["first"] == f and lo <= x["own_turn"] <= hi)(f, lo, hi))
             for name, lo, hi in STAGES for f in (True, False)]
    for label, sel in rows:
        sub = [x for x in pts if sel(x)]
        g = _group(sub)
        lo, hi = boot_ci(g, gap, nboot)
        print(f"| {label} | {len(sub)} | {len(g)} | {sum(x['p'] for x in sub) / len(sub):.3f} | "
              f"{sum(x['result'] for x in sub) / len(sub):.3f} | {gap(sub):+.3f}（{lo:+.3f}～{hi:+.3f}） |")
    print("\n**先手方 − 后手方的差**（同一批局，按局重抽）：")
    g = _group(pts)
    diff = lambda s: (gap([x for x in s if x["first"]]) or 0) - (gap([x for x in s if not x["first"]]) or 0)
    lo, hi = boot_ci(g, diff, nboot)
    print(f"{diff(pts):+.3f}（{lo:+.3f}～{hi:+.3f}）\n")
    print("**按组合和卡组**（差 = 实际 − p）：\n")
    print("| 卡组（对手） | 先手方的差 | 后手方的差 |")
    print("|---|---|---|")
    for key in sorted({(x["deck"], x["opp"]) for x in pts}):
        cells = []
        for f in (True, False):
            sub = [x for x in pts if (x["deck"], x["opp"]) == key and x["first"] == f]
            lo, hi = boot_ci(_group(sub), gap, nboot)
            cells.append(f"{gap(sub):+.3f}（{lo:+.3f}～{hi:+.3f}，{len(sub)} 点）")
        print(f"| {key[0]}（对 {key[1]}） | {cells[0]} | {cells[1]} |")
    print("\n**残差对候选量的斜率**（残差 = 实际 − p，在先手方、后手方里分别回归；斜率是每多 1 个单位残差变多少）：\n")
    print("| 量 | 先手方的斜率（95%） | 后手方的斜率（95%） |")
    print("|---|---|---|")
    for key, label in (("hand", "手牌张数"), ("dead", "下回合付不起的手牌张数（费用 > 最大 PP + 1）"),
                       ("hand_cost", "手牌总费用"), ("ep", "进化点"), ("sep", "超进化点"), ("max_pp", "最大 PP"),
                       ("own_turn", "自己的第几回合"), ("followers", "己方随从数"), ("op_followers", "对方随从数")):
        cells = []
        for f in (True, False):
            sub = [x for x in pts if x["first"] == f]
            lo, hi = boot_ci(_group(sub), lambda s: slope(s, key), nboot)
            cells.append(f"{slope(sub, key):+.4f}（{lo:+.4f}～{hi:+.4f}）")
        print(f"| {label} | {cells[0]} | {cells[1]} |")


MODELED = {("elf-t", "elf-t"), ("elf-t", "nemesis-t"), ("elf-t", "ramp-t"), ("nemesis-t", "elf-t"), ("nemesis-t", "ramp-t"),
           ("pirate-t", "elf-t"), ("pirate-t", "pirate-t"), ("ramp-t", "ramp-t"), ("ramp-t", "elf-t"),
           ("ramp-t", "nemesis-t"), ("ramp-t", "pirate-t")}       # sides with an installed pairing model (08a02d0)
COVARIATES = (("first", "先手（是 1）"), ("hand", "手牌张数"), ("dead", "下回合付不起的手牌张数"), ("hand_cost", "手牌总费用"),
              ("ep", "进化点"), ("sep", "超进化点"), ("max_pp", "最大 PP（回合固定以后，就是多跳出来的 PP）"),
              ("followers", "己方随从数"), ("op_followers", "对方随从数"))


def multi(pts, nboot, seed=17):
    """The residual regressed on all the candidates at once, with a dummy per own turn (12 and later pooled)
    and per side (deck, opponent): what each candidate adds once the stage and the pairing are held fixed."""
    import numpy as np
    sides = sorted({(x["deck"], x["opp"]) for x in pts})
    def design(sub):
        rows = []
        for x in sub:
            t = min(x["own_turn"], 12)
            rows.append([float(x[k]) for k, _ in COVARIATES] + [1.0 if t == u else 0.0 for u in range(2, 13)]
                        + [1.0 if (x["deck"], x["opp"]) == sd else 0.0 for sd in sides[1:]] + [1.0])
        return np.array(rows), np.array([x["result"] - x["p"] for x in sub])
    X, y = design(pts)
    beta = np.linalg.lstsq(X, y, rcond=None)[0][:len(COVARIATES)]
    g = _group(pts)
    keys = list(g)
    idx = {}
    for i, x in enumerate(pts):
        idx.setdefault((x["pair"], x["k"], x["seat_a"]), []).append(i)
    rng = random.Random(seed)
    bs = []
    for _ in range(nboot):
        rows = [i for _ in keys for i in idx[keys[rng.randrange(len(keys))]]]
        bs.append(np.linalg.lstsq(X[rows], y[rows], rcond=None)[0][:len(COVARIATES)])
    bs = np.array(bs)
    lo, hi = np.percentile(bs, 2.5, axis=0), np.percentile(bs, 97.5, axis=0)
    return beta, lo, hi


def _group(pts):
    g = {}
    for x in pts:
        g.setdefault((x["pair"], x["k"], x["seat_a"]), []).append(x)
    return g


def report_multi(path, nboot):
    pts = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    for label, sub in (("有配对模型的一方（11 个）", [x for x in pts if (x["deck"], x["opp"]) in MODELED]),
                       ("全部", pts)):
        beta, lo, hi = multi(sub, nboot)
        print(f"\n**残差同时对所有候选量回归**（{label}，{len(sub)} 点；固定自己的第几回合和组合，按局重抽 {nboot} 次）：\n")
        print("| 量 | 系数（95%） |")
        print("|---|---|")
        for (k, name), b, l, h in zip(COVARIATES, beta, lo, hi):
            print(f"| {name} | {b:+.4f}（{l:+.4f}～{h:+.4f}） |")


def main():
    if "--multi" in sys.argv:
        nboot = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 200
        report_multi(sys.argv[sys.argv.index("--multi") + 1], nboot)
        return
    if "--report" in sys.argv:
        nboot = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 1000
        report(sys.argv[sys.argv.index("--report") + 1], nboot)
        return
    paths = sys.argv[sys.argv.index("--games") + 1].split("+")
    out = sys.argv[sys.argv.index("--out") + 1]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    collect(paths, out, workers)


if __name__ == "__main__":
    main()
