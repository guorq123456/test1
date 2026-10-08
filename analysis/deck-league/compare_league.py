"""The whole league before and after, cell by cell, paired by seed: one row a pairing.

    python3 <this> base=league_v2s_f631e14.jsonl.gz+league_v2s_f631e14_mirror2.jsonl.gz \
        new=part1.jsonl.gz+part2.jsonl.gz+part3.jsonl.gz [--note elf-t=起手 D→R] [--timing-base FILE[+FILE...]]

Each version is one or more league files (a later file replaces a game of the same pairing, pair and seat, as in
league.py's report); the pairings both versions have are compared, on the seeds both have. A pair is one seed's
two games with the decks' seats swapped. Per pairing:
  non-mirror: the first deck's score in each version (a pair's two games averaged, then over pairs), the paired
    difference with its 95% interval and the CR it is worth (Salem's scale, 236 a logit, from the base's own
    score; the steady-state figure 800 x difference in brackets), the score when the first deck went first and
    when it went second (by game) in each version;
  mirror: the first player's score instead (a pair's distinct games averaged: with the same agent on both sides
    the two games are often the same game), and its paired difference;
  both: the game length (turns, both sides; paired difference with its interval), time per turn (the games' wall
    time over their turns, both sides), and how many of the games came out move for move the same in both versions.
Time per turn is only comparable on the same machine at the same load, so with --timing-base (league files of
the base's code run where and as the new version ran, a few pairs a cell) the base's time comes from those and
the new version's from the same seeds; without it only the new version's time is printed.
Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import gzip
import json
import math

SALEM = 236.0


def load(paths):
    latest = {}
    for path in paths:
        for line in gzip.open(path, "rt", encoding="utf-8"):
            g = json.loads(line)
            latest[(g["pair"], g["k"], g["seat_a"])] = g
    cells = {}
    for (pair, k, s), g in latest.items():
        cells.setdefault(pair, {}).setdefault(k, {})[s] = g
    return {p: {k: gs for k, gs in ks.items() if len(gs) == 2} for p, ks in cells.items()}


def pts(g):
    return 0.5 if g["winner"] is None else 1.0 if g["winner"] == g["seat_a"] else 0.0


def first_pts(g):
    return 0.5 if g["winner"] is None else 1.0 if g["winner"] == g["first"] else 0.0


def ci(xs):
    n = len(xs)
    if n == 0:
        return float("nan"), float("nan")
    m = sum(xs) / n
    return m, 1.96 * math.sqrt(sum((x - m) ** 2 for x in xs) / max(n - 1, 1) / n)


def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def per_pair(gs, mirror):
    """(score, length) of one pair: the first deck's score, or in a mirror the first player's over the distinct games."""
    games = [gs[0], gs[1]]
    if mirror and games[0]["record"]["actions"] == games[1]["record"]["actions"]:
        games = games[:1]
    f = first_pts if mirror else pts
    return sum(f(g) for g in games) / len(games), sum(g["turns"] for g in games) / len(games)


def split(cell, ks):
    games = [cell[k][s] for k in ks for s in (0, 1)]
    first = [pts(g) for g in games if g["first"] == g["seat_a"]]
    second = [pts(g) for g in games if g["first"] != g["seat_a"]]
    return sum(first) / len(first), sum(second) / len(second)


def ms_per_turn(cell, ks):
    games = [cell[k][s] for k in ks for s in (0, 1) if k in cell]
    return 1000 * sum(g["seconds"] for g in games) / sum(g["turns"] for g in games) if games else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("versions", nargs=2, help="label=file[+file...], the base first")
    ap.add_argument("--note", nargs="*", default=[], help="DECK=text, printed beside every pairing with that deck")
    ap.add_argument("--timing-base", default=None, help="the base's code run on the new version's machine: file[+file...]")
    ap.add_argument("--timing-label", default="本机 f631e14 每格 20 对，与重跑同机同进程数")
    args = ap.parse_args()
    (la, fa), (lb, fb) = (v.split("=", 1) for v in args.versions)
    a, b = load(fa.split("+")), load(fb.split("+"))
    tb = load(args.timing_base.split("+")) if args.timing_base else None
    notes = dict(n.split("=", 1) for n in args.note)
    print(f"条件：对手卡表已知（牌序、手牌未知）。{lb} 对 {la}，同一批种子按对配对；区间 95%，按对算。")
    print("非镜像看前一个卡组的得分，镜像看先手得分（同一对两局逐步相同只算一局）。CR 按 Salem 刻度（236 / logit，"
          f"从 {la} 自己的得分算），括号里是稳态式 800 × 差。\n")
    rows = []
    for pair in sorted(set(a) & set(b)):
        x, y = a[pair], b[pair]
        ks = sorted(set(x) & set(y))
        d1, d2 = pair.split("/")
        mirror = d1 == d2
        px = {k: per_pair(x[k], mirror) for k in ks}
        py = {k: per_pair(y[k], mirror) for k in ks}
        sx, _ = ci([px[k][0] for k in ks])
        sy, _ = ci([py[k][0] for k in ks])
        ds, hs = ci([py[k][0] - px[k][0] for k in ks])
        tx, _ = ci([px[k][1] for k in ks])
        ty, _ = ci([py[k][1] for k in ks])
        dt, ht = ci([py[k][1] - px[k][1] for k in ks])
        same = sum(x[k][s]["record"]["actions"] == y[k][s]["record"]["actions"] for k in ks for s in (0, 1))
        note = "；".join(notes[d] for d in dict.fromkeys((d1, d2)) if d in notes)
        if tb is None:
            ms = (None, ms_per_turn(y, ks), len(ks))
        else:
            tk = sorted(set(tb.get(pair, {})) & set(y))
            ms = (ms_per_turn(tb.get(pair, {}), tk), ms_per_turn(y, tk), len(tk))
        rows.append((pair, mirror, len(ks), sx, sy, ds, hs, tx, ty, dt, ht, same, note,
                     None if mirror else (split(x, ks), split(y, ks)), ms))
    print("| 组合 | 对数 | 看的是 | " + la + " | " + lb + " | 差（95%） | CR（稳态式） | 局长 " + la + " → " + lb +
          " | 局长差 | 逐步相同的局 | 备注 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for pair, mirror, n, sx, sy, ds, hs, tx, ty, dt, ht, same, note, _, _ in rows:
        what = "先手得分" if mirror else "前者得分"
        cr = "—" if mirror else f"{SALEM * (logit(sx + ds) - logit(sx)):+.0f}（{800 * ds:+.0f}）"
        print(f"| {pair} | {n} | {what} | {sx:.1%} | {sy:.1%} | {ds:+.1%} ± {hs:.1%} | {cr} | {tx:.1f} → {ty:.1f} | "
              f"{dt:+.1f} ± {ht:.1f} | {same} / {2 * n} | {note} |")
    print("\n先后手拆分（非镜像，前一个卡组的得分，按局算）和每回合用时（整局墙钟 ÷ 回合数，双方合计）：\n")
    head = f"每回合用时：基线（{args.timing_label}）→ {lb}（同一批种子）" if tb else f"每回合用时 {lb}（用时基线待补，不和 {la} 比）"
    print(f"| 组合 | {la} 它先手 / 后手 | {lb} 它先手 / 后手 | {head} |")
    print("|---|---|---|---|")
    for pair, mirror, n, *_, sp, ms in rows:
        s1 = "（镜像）" if mirror else f"{sp[0][0]:.1%} / {sp[0][1]:.1%}"
        s2 = "（镜像）" if mirror else f"{sp[1][0]:.1%} / {sp[1][1]:.1%}"
        if ms[0] is None:
            t = f"{ms[1]:.0f} ms"
        elif ms[2] == 0:
            t = "用时基线里没有这一格"
        else:
            t = f"{ms[0]:.0f} → {ms[1]:.0f} ms（{ms[1] / ms[0] - 1:+.0%}，{ms[2]} 对）"
        print(f"| {pair} | {s1} | {s2} | {t} |")
    only = sorted(set(a) ^ set(b))
    if only:
        print(f"\n只在一边有的组合（没比）：{' '.join(only)}")
    print("\n注意：每回合用时只有在同一台机器、同样负载下跑的才可比" + (f"；用时基线为{args.timing_label}。" if tb else "。"))


if __name__ == "__main__":
    main()
