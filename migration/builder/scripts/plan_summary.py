import json, sys, statistics as st, glob
from collections import defaultdict
res = json.load(open(sys.argv[1]))
by = defaultdict(list)
for r in res: by[r["name"]].append(r)
def side_stats(games, side):
    hand = [t["hand"] for g in games for t in g["turns"] if t["side"] == side and 4 <= t["n"] <= 10]
    waste = [t["pp_left"] for g in games for t in g["turns"] if t["side"] == side and 3 <= t["n"] <= 10]
    ep8 = [t["ep"] for g in games for t in g["turns"] if t["side"] == side and t["n"] == 8]
    board = [t["board"] for g in games for t in g["turns"] if t["side"] == side and 4 <= t["n"] <= 10]
    f = lambda xs: f"{st.mean(xs):.2f}" if xs else "-"
    return f"手牌 {f(hand)} | 浪费PP {f(waste)} | 第8回合剩进化点 {f(ep8)} | 随从数 {f(board)}"
for name, games in by.items():
    n = len(games); w = sum(g["win"] for g in games); p = w / n
    ms_a = st.mean(g["ms"][0] for g in games); ms_b = st.mean(g["ms"][1] for g in games)
    print(f"\n{name}: 前者 {w:g}/{n} = {p:.0%} ± {1.96*(p*(1-p)/n)**0.5:.0%}，平均 {st.mean(g['length'] for g in games):.1f} 回合")
    print(f"  前者 {ms_a:.0f} ms/步 | {side_stats(games, 'a')}")
    print(f"  后者 {ms_b:.0f} ms/步 | {side_stats(games, 'b')}")
