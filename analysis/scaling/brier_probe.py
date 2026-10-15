"""How big is the label noise for a terminal-outcome value target? On recorded self-play games (netdata records),
every turn end (the state before EndTurn, after_end_of_turn applied; the side that ends the turn) gets the installed
evaluator's win probability sigma(evaluate / SCALE) and the side's final result as the label. Reports Brier and
log-loss for: the constant 0.5, the installed evaluator raw, and the installed evaluator recalibrated by a 1-D
logistic fit on even games, read on odd games; by turn buckets too. A probe for setting J90, not a pre-registered
measurement. Condition: the opponent's deck list is known (order and hand not).

    PYTHONPATH=<svsim> python3 brier_probe.py selfplay.jsonl --deck ramp-t --spec v2s [--games 300] [--workers 3]
"""
import argparse
import json
import math
from multiprocessing import Pool

ARGS = None


def _init(args):
    global ARGS, W
    ARGS = args
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    W = _search(make_agent(args.spec, 0)).weights


def _game(line):
    from svsim.cards import decks
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply, new_game
    from svsim.learn.model import SCALE
    from svsim.search.evaluate import after_end_of_turn, evaluate
    from svsim.ui.session import DECKS
    g = json.loads(line)
    cards = decks.build(DECKS[ARGS.deck][1])
    st = new_game(cards, decks.build(DECKS[ARGS.deck][1]), seed=g["seed"])
    out = []
    for data in g["actions"]:
        if st.over:
            break
        act = from_dict(data)
        if isinstance(act, EndTurn):
            me = st.active
            end = after_end_of_turn(st.clone())
            z = evaluate(end, me, W, False)
            out.append((me, st.turn, z / SCALE))
        apply(st, act)
    ok = st.over and st.winner == g["winner"]
    return ok, g["winner"], out


def brier(ps, ys):
    return sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ys)


def logloss(ps, ys):
    e = 1e-6
    return -sum(y * math.log(min(max(p, e), 1 - e)) + (1 - y) * math.log(min(max(1 - p, e), 1 - e))
                for p, y in zip(ps, ys)) / len(ys)


def fit1d(xs, ys, iters=200):
    a, b = 1.0, 0.0
    for _ in range(iters):                       # Newton steps for logistic regression on one input
        ga = gb = haa = hab = hbb = 0.0
        for x, y in zip(xs, ys):
            p = 1 / (1 + math.exp(-max(-60, min(60, a * x + b))))
            r = p - y
            w = p * (1 - p)
            ga += r * x; gb += r; haa += w * x * x; hab += w * x; hbb += w
        det = haa * hbb - hab * hab
        if det <= 0:
            break
        a -= (hbb * ga - hab * gb) / det
        b -= (haa * gb - hab * ga) / det
    return a, b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("--deck", default="ramp-t")
    ap.add_argument("--spec", default="v2s")
    ap.add_argument("--games", type=int, default=0)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    lines = [l for l in open(args.records, encoding="utf-8") if l.strip()]
    if args.games:
        lines = lines[:args.games]
    with Pool(args.workers, initializer=_init, initargs=(args,)) as pool:
        res = pool.map(_game, lines)
    bad = sum(not ok for ok, _, _ in res)
    rows = []                                    # (game index, turn, x = z / SCALE, y)
    for gi, (ok, winner, out) in enumerate(res):
        for me, turn, x in out:
            y = 0.5 if winner is None else (1.0 if winner == me else 0.0)
            rows.append((gi, turn, x, y))
    sig = lambda v: 1 / (1 + math.exp(-max(-60, min(60, v))))
    tr = [r for r in rows if r[0] % 2 == 0]
    te = [r for r in rows if r[0] % 2 == 1]
    a, b = fit1d([r[2] for r in tr], [r[3] for r in tr])
    print(f"条件：对手卡表已知（牌序、手牌未知）。{len(lines)} 局（{args.deck} 镜像，{args.spec}），重放和记录胜负不符 {bad} 局；回合末 {len(rows)} 个")
    print(f"校准（偶数局拟合）：p = sigma({a:.3f} x + {b:.3f})，x = 评估值 / SCALE；在奇数局上读")
    for name, sel in (("全部", lambda r: True), ("第 1～5 回合", lambda r: r[1] <= 5), ("第 6～10 回合", lambda r: 6 <= r[1] <= 10),
                      ("第 11 回合起", lambda r: r[1] >= 11)):
        t = [r for r in te if sel(r)]
        if not t:
            continue
        ys = [r[3] for r in t]
        b0 = brier([0.5] * len(t), ys)
        braw = brier([sig(r[2]) for r in t], ys)
        bcal = brier([sig(a * r[2] + b) for r in t], ys)
        print(f"- {name}（{len(t)} 个）：Brier 常数 0.5 = {b0:.4f}，现装原样 = {braw:.4f}，现装校准 = {bcal:.4f}"
              f"（超出常数的部分 {b0 - bcal:.4f}）；log-loss 常数 {logloss([0.5]*len(t), ys):.4f}，校准 {logloss([sig(a*r[2]+b) for r in t], ys):.4f}")


if __name__ == "__main__":
    main()
