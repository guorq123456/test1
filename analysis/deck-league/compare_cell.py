"""One non-mirror league cell before and after a change, paired by seed: the first deck's score, by who went first.

    python3 <this> --pair elf-t/ramp-t base=league_v2s_f631e14.jsonl.gz nomodel=FILE model=FILE

A pair is one seed's two games with the decks' seats swapped (league.py). Per version: the first deck's score
(a pair's two games averaged, then over pairs, 95% interval), its score in the games it went first and in those
it went second (by game), the game length (turns, both sides), and how many pairs' two games came out the same
as in the first version; between consecutive versions (and the last against the first) the paired difference
over the seeds both have, and the CR that a score change is worth (Salem's scale, 236 a logit, from the earlier
version's own score; the steady-state figure 800 x difference in brackets). Condition: the opponent's 40-card
list is known (order and hand not).
"""
import argparse
import gzip
import json
import math

SALEM = 236.0


def load(paths, pairing):
    latest = {}
    for path in paths:
        for line in gzip.open(path, "rt", encoding="utf-8"):
            g = json.loads(line)
            if g["pair"] == pairing:
                latest[(g["k"], g["seat_a"])] = g
    return latest


def pts(g):
    return 0.5 if g["winner"] is None else 1.0 if g["winner"] == g["seat_a"] else 0.0


def ci(xs):
    n = len(xs)
    m = sum(xs) / n
    return m, 1.96 * math.sqrt(sum((x - m) ** 2 for x in xs) / max(n - 1, 1) / n)


def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("versions", nargs="+", help="label=file[+file...]")
    args = ap.parse_args()
    vs = [(v.split("=", 1)[0], load(v.split("=", 1)[1].split("+"), args.pair)) for v in args.versions]
    a, b = args.pair.split("/")
    print(f"条件：对手卡表已知（牌序、手牌未知）。{args.pair}，{a} 的得分；一对 = 同一个种子、换座位的两局。\n")
    print(f"{'版本':<16}{'对数':>5}   {a} 得分（95%，按对）   它先手时   它后手时   局长（双方合计）")
    per = {}
    for label, d in vs:
        ks = sorted({k for k, _ in d if (k, 0) in d and (k, 1) in d})
        pair_score = {k: (pts(d[(k, 0)]) + pts(d[(k, 1)])) / 2 for k in ks}
        length = {k: (d[(k, 0)]["turns"] + d[(k, 1)]["turns"]) / 2 for k in ks}
        games = [d[(k, s)] for k in ks for s in (0, 1)]
        first = [pts(g) for g in games if g["first"] == g["seat_a"]]
        second = [pts(g) for g in games if g["first"] != g["seat_a"]]
        m, h = ci(list(pair_score.values()))
        t, ht = ci(list(length.values()))
        per[label] = (pair_score, length, d)
        print(f"{label:<16}{len(ks):>5}   {m:.1%} ± {h:.1%}            {sum(first) / len(first):.1%}     "
              f"{sum(second) / len(second):.1%}     {t:.1f} ± {ht:.1f}")
    print("\n配对差（同一批种子）：")
    pairs = list(zip(vs, vs[1:])) + ([(vs[0], vs[-1])] if len(vs) > 2 else [])
    for (la, _), (lb, _) in pairs:
        sa, ta, da = per[la]
        sb, tb, db = per[lb]
        ks = sorted(set(sa) & set(sb))
        dm, dh = ci([sb[k] - sa[k] for k in ks])
        tm, th = ci([tb[k] - ta[k] for k in ks])
        base = sum(sa[k] for k in ks) / len(ks)
        cr = SALEM * (logit(base + dm) - logit(base))
        same = sum(da[(k, s)]["record"]["actions"] == db[(k, s)]["record"]["actions"] for k in ks for s in (0, 1))
        print(f"  {lb} − {la}：{len(ks)} 对，{a} 得分 {dm:+.1%} ± {dh:.1%}（CR {cr:+.0f}，稳态式 {800 * dm:+.0f}），"
              f"局长 {tm:+.1f} ± {th:.1f}；{2 * len(ks)} 局里 {same} 局逐步相同")


if __name__ == "__main__":
    main()
