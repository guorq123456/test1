"""Positions 2, 5 and 9 of the top-10, where the evaluation itself prefers the deep move (Salem's) but level-strong's
200-iteration search picks the shallow one (the architecture thread 17:24): how often mcts:N+plan+learned+phased picks
the deep move at N = 200, 400, 800 (5 seeds each), numbers only.

    cd <svsim checkout (64ab2fe)> && PYTHONPATH=. python3 <this> <analysis dir> [--seeds 5]

Condition: the opponent's 40-card list is known (order and hand not). Both sides play the original ramp deck.
"""
import sys
from collections import Counter

sys.path.insert(0, __import__("os").path.dirname(__file__))
import five  # noqa: E402

A = sys.argv[1]
SEEDS = int(sys.argv[sys.argv.index("--seeds") + 1]) if "--seeds" in sys.argv else 5
five.A = A
five.PICKS = [("1791387160337", 57), ("1791316540438", 43), ("1791384258804", 31)]
LABELS = ["#2", "#5", "#9"]


def main():
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    pos = five.load()
    print("条件：对手卡表已知（牌序、手牌未知）。每格 5 个搜索种子；「深搜」= 当时 mcts:800 选的那步（也是 Salem 的走法）。\n")
    print("| 局面 | 深搜那步 | 浅搜那步 | 200 次 | 400 次 | 800 次 |")
    print("|---|---|---|---|---|---|")
    for lab, (gid, at, rec, st, row) in zip(LABELS, pos):
        cells = []
        for n in (200, 400, 800):
            c = Counter()
            for s in range(SEEDS):
                a = make_agent(f"mcts:{n}+plan+learned+phased", 5000 + 37 * n + s).act(st.clone(), legal_actions(st))
                d = five.describe(st, a)
                c["深搜" if d == row["deep"] else "浅搜" if d == row["shallow"] else d] += 1
            cells.append(f"深搜 {c['深搜']}/{SEEDS}" + "".join(f"；{k} {v}" for k, v in c.items() if k != "深搜"))
        print(f"| {lab} | {row['deep']} | {row['shallow']} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
