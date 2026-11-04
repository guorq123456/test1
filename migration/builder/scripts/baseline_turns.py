"""对照：整回合比较里，手写评估把你那一回合的结果排第一的比例（候选和训练时一样）。"""
import sys
sys.path.insert(0, "/home/user/test1")
from unittest import mock
from svsim.learn import data
from svsim.search.evaluate import DEFAULT, evaluate
from svsim.tools.learn import load_records
recs = load_records(["/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/human_games"])
# 让 features() 直接返回手写评估分数，从而复用同样的候选生成
with mock.patch.object(data, "features", lambda s, p, potential=True: [evaluate(s, p, DEFAULT)]):
    hits = n = rand = 0.0
    for i, r in enumerate(recs):
        for k, cands in data.turn_choices(r, 0, True, seed=i):
            scores = [c[0] for c in cands]; best = max(scores)
            top = [j for j, v in enumerate(scores) if v >= best - 1e-9]
            hits += (1 / len(top)) if 0 in top else 0; rand += 1 / len(cands); n += 1
print(f"整回合比较 {n:.0f} 个：手写评估把你的回合排第一 {hits / n:.0%}；随机挑选的期望 {rand / n:.0%}")
