"""Line A / C gates on one bank: each candidate against B, then candidates against each other paired by seed.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> --deck ramp-t --opponent ramp-t \
        A200=A200_vs_B.jsonl A100=A100_vs_B.jsonl Aq=Aq_vs_B.jsonl C1=C1_vs_A200.jsonl ... \
        [--pairs A200-A100 Aq-A200 ...] [--boot 4000]

Each file is a tools.gate run, in either mode (read from the rows):
- direct (no --versus; the ramp mirror gates of lines A and C): a pair is A against B head to head, A in seat 0
  then seat 1 on the seed's deal; the pair's score is A's mean.
- --versus: a pair is A's two games against C and B's two against C on the same deal; the score 0.5 + A - B.
Per gate: the pair score with its 95% interval (pairs), CR on Salem's scale (236 a logit; steady state 800 x
difference in brackets), the verdict (lower end > 50%: passes), A's score when it went first and second (who goes
first comes from the seed), and the games played move for move alike (direct: both games of a pair alike; versus:
A's game alike B's). The cross-gate check of B's games only applies to --versus gates sharing B and C: B's games
there do not involve A, so on the same seeds and code they must be the same games. In direct gates B plays A, so
once A's first move differs the game forks; only the deals are the same (same seed), and the gate keeps no game
records, so where A first differs cannot be read from the files. Then for each requested pair X-Y of candidates
on the same seeds: the per-seed difference of the pair scores (direct: both against B on the same deals; versus:
both against C, B drops out), with its interval.
Condition: the opponent's 40-card list is known (order and hand not).
"""
import json
import math
import sys

SALEM = 236.0


def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def ci(xs):
    n = len(xs)
    m = sum(xs) / n
    return m, 1.96 * math.sqrt(sum((x - m) ** 2 for x in xs) / max(n - 1, 1) / n)


def first_of(seed, deck, opp):
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.ui.session import DECKS
    return new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opp][1]), seed=seed).first


def main():
    arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    deck, opp = arg("--deck", "ramp-t"), arg("--opponent", "ramp-t")
    files = {a.split("=", 1)[0]: a.split("=", 1)[1] for a in sys.argv[1:] if "=" in a and not a.startswith("--")}
    rows = {n: {d["seed"]: d for d in map(json.loads, open(p, encoding="utf-8")) if d} for n, p in files.items()}
    print(f"条件：对手卡表已知（牌序、手牌未知）。{deck} 对 {opp}；一对的得分：直接对打的门是 A 两局的平均（A 先后坐两个座位、同一副发牌），"
          "带 --versus 的门是 0.5 + A − B（A、B 在同一副发牌上打同一个 C）；区间 95%，按对算；CR 按 Salem 刻度，括号里是稳态式；通过 = 下沿 > 50%。\n")
    print("| 门 | 对数 | 一对的得分（95%） | CR（稳态式） | 判定 | A 的得分 | B 的得分（直接对打时是 1 − A） | A 先手 / 后手 | 逐局相同 |")
    print("|---|---|---|---|---|---|---|---|---|")
    def score(d):
        if "b_points" in d:
            return 0.5 + sum(d["points"]) / 2 - sum(d["b_points"]) / 2
        return sum(d["points"]) / 2
    for n, rs in rows.items():
        xs = [score(d) for d in rs.values()]
        m, h = ci(xs)
        versus = all("b_points" in d for d in rs.values())
        pa = sum(x for d in rs.values() for x in d["points"]) / (2 * len(rs))
        pb = sum(x for d in rs.values() for x in d["b_points"]) / (2 * len(rs)) if versus else 1 - pa
        first, second = [], []
        for d in rs.values():
            f = first_of(d["seed"], deck, opp)
            for seat in (0, 1):
                (first if seat == f else second).append(d["points"][seat])
        same = sum(sum(d["same"]) if isinstance(d.get("same"), list) else 2 * bool(d.get("same")) for d in rs.values())
        verdict = "**通过**" if m - h > 0.5 else "不通过"
        print(f"| {n} | {len(rs)} | {m:.1%} ± {h:.1%}（{m - h:.1%}～{m + h:.1%}） | {SALEM * logit(m):+.0f}（{800 * (m - 0.5):+.0f}） | "
              f"{verdict} | {pa:.1%} | {pb:.1%} | {sum(first) / len(first):.1%} / {sum(second) / len(second):.1%} | {same} / {2 * len(rs)} |")
    names = list(rows)
    vnames = [n for n in names if all("b_points" in d for d in rows[n].values())]
    if len(vnames) > 1:
        print("\n**B 在各门里是否打出同一批局**（只对带 --versus 的门；同种子、同 B、同 C 时应逐座位相同）：")
    for i, x in enumerate(vnames):
        for y in vnames[i + 1:]:
            common = set(rows[x]) & set(rows[y])
            if not common:
                continue
            diff = sum(rows[x][s]["b_points"] != rows[y][s]["b_points"] for s in common)
            print(f"- {x} 与 {y}：共同种子 {len(common)} 个，B 的得分不同的 {diff} 个")
    pairs = [p.split("-", 1) for p in (arg("--pairs", "") or "").split() if "-" in p]
    if pairs:
        print("\n**候选之间按种子配对**（每个种子两道门一对得分之差；直接对打时两边都对 B、同一副发牌）：\n")
        print("| X − Y | 共同种子 | 差（95%，胜率点） | CR |")
        print("|---|---|---|---|")
        for x, y in pairs:
            common = sorted(set(rows[x]) & set(rows[y]))
            if not common:
                print(f"| {x} − {y} | 0 | 没有共同种子，不能配对 | — |")
                continue
            ds = [score(rows[x][s]) - score(rows[y][s]) for s in common]
            m, h = ci(ds)
            px = sum(score(rows[x][s]) for s in common) / len(common)
            py = sum(score(rows[y][s]) for s in common) / len(common)
            print(f"| {x} − {y} | {len(common)} | {m:+.1%} ± {h:.1%} | {SALEM * (logit(px) - logit(py)):+.0f} |")


if __name__ == "__main__":
    main()
