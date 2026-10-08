"""Line A / C gates on one bank: each candidate against B, then candidates against each other paired by seed.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> --deck ramp-t --opponent ramp-t \
        A200=A200_vs_B.jsonl A100=A100_vs_B.jsonl Aq=Aq_vs_B.jsonl C1=C1_vs_A200.jsonl ... \
        [--pairs A200-A100 Aq-A200 ...] [--boot 4000]

Each file is a tools.gate --versus run (a line a pair: A's points in seat 0 and 1, B's in `b_points`, both against
the same C on the same deals). Per gate: the pair score 0.5 + A - B with its 95% interval (pairs), CR on Salem's
scale (236 a logit; steady state 800 x difference in brackets), the verdict (lower end > 50%: passes), A and B
against C, A's score when it went first and second (who goes first comes from the seed), games A and B played
move for move alike. B's own games are checked across the files: a --versus pair is A's two games against C and
B's two against C on the same deal, so B's games do not involve A at all; on the same seeds with the same B, C and
code they must be the same games (same points in every seat). Only gates sharing B are compared (A200, A', A100 share
B = level-strong; C1, C2 share B = A200); a difference means B, C or the code differed between the runs. Then for each requested pair X-Y of
candidates on the same seeds: (A_X - A_Y) per seed, both against the same C, with its interval - B drops out;
for a C gate whose B is A200, X-B is already that difference.
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
    print(f"条件：对手卡表已知（牌序、手牌未知）。{deck} 对 {opp}，每道门一对的得分 = 0.5 + A − B（A、B 在同一副发牌上打同一个 C）；"
          "区间 95%，按对算；CR 按 Salem 刻度，括号里是稳态式；通过 = 下沿 > 50%。\n")
    print("| 门 | 对数 | 一对的得分（95%） | CR（稳态式） | 判定 | A 对 C | B 对 C | A 先手 / 后手 | A、B 逐局相同 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for n, rs in rows.items():
        xs = [0.5 + sum(d["points"]) / 2 - sum(d["b_points"]) / 2 for d in rs.values()]
        m, h = ci(xs)
        pa = sum(x for d in rs.values() for x in d["points"]) / (2 * len(rs))
        pb = sum(x for d in rs.values() for x in d["b_points"]) / (2 * len(rs))
        first, second = [], []
        for d in rs.values():
            f = first_of(d["seed"], deck, opp)
            for seat in (0, 1):
                (first if seat == f else second).append(d["points"][seat])
        same = sum(sum(d.get("same") or [False, False]) for d in rs.values())
        verdict = "**通过**" if m - h > 0.5 else "不通过"
        print(f"| {n} | {len(rs)} | {m:.1%} ± {h:.1%}（{m - h:.1%}～{m + h:.1%}） | {SALEM * logit(m):+.0f}（{800 * (m - 0.5):+.0f}） | "
              f"{verdict} | {pa:.1%} | {pb:.1%} | {sum(first) / len(first):.1%} / {sum(second) / len(second):.1%} | {same} / {2 * len(rs)} |")
    names = list(rows)
    print("\n**B 在各门里是否打出同一批局**（同种子、同 B、同 C 时应逐座位相同）：")
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            common = set(rows[x]) & set(rows[y])
            if not common:
                continue
            diff = sum(rows[x][s]["b_points"] != rows[y][s]["b_points"] for s in common)
            print(f"- {x} 与 {y}：共同种子 {len(common)} 个，B 的得分不同的 {diff} 个")
    pairs = [p.split("-", 1) for p in (arg("--pairs", "") or "").split() if "-" in p]
    if pairs:
        print("\n**候选之间按种子配对**（A_X − A_Y，同一个 C、同一副发牌；B 抵消）：\n")
        print("| X − Y | 共同种子 | 差（95%，胜率点） | CR |")
        print("|---|---|---|---|")
        for x, y in pairs:
            common = sorted(set(rows[x]) & set(rows[y]))
            if not common:
                print(f"| {x} − {y} | 0 | 没有共同种子，不能配对 | — |")
                continue
            ds = [(sum(rows[x][s]["points"]) - sum(rows[y][s]["points"])) / 2 for s in common]
            m, h = ci(ds)
            px = sum(x_ for s in common for x_ in rows[x][s]["points"]) / (2 * len(common))
            py = sum(x_ for s in common for x_ in rows[y][s]["points"]) / (2 * len(common))
            print(f"| {x} − {y} | {len(common)} | {m:+.1%} ± {h:.1%} | {SALEM * (logit(px) - logit(py)):+.0f} |")


if __name__ == "__main__":
    main()
