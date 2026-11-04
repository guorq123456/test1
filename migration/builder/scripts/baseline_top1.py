"""对照：手写评估函数（以及随机挑选）在你的决策点上把你的选择排第一的比例。"""
import sys
sys.path.insert(0, "/home/user/test1")
from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Phase
from svsim.search.evaluate import DEFAULT, THREAT_HAND, after_end_of_turn, evaluate
from svsim.tools import records
from svsim.tools.learn import load_records

recs = load_records(["/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/human_games"])
for label, w in (("手写评估", DEFAULT), ("手写评估+手牌斩杀潜力", THREAT_HAND)):
    hits = n = rand = 0.0
    for rec in recs:
        for state, action in records.steps(rec):
            if state.active != 0 or state.phase != Phase.MAIN:
                continue
            legal = legal_actions(state)
            scores, over = [], False
            for a in legal:
                s = state.clone()
                s = after_end_of_turn(s) if isinstance(a, EndTurn) else (apply(s, a) or s)
                over |= s.over
                scores.append(evaluate(s, 0, w))
            if over:
                continue
            best = max(scores); top = [i for i, v in enumerate(scores) if v >= best - 1e-9]
            k = legal.index(action)
            hits += (1 / len(top)) if k in top else 0
            rand += 1 / len(legal); n += 1
    print(f"{label}：{n:.0f} 个决策，把你的选择排第一 {hits / n:.0%}；随机挑选的期望 {rand / n:.0%}")
