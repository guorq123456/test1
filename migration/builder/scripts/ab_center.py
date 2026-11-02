"""新旧搜索直接对打：new = 以当前局面为基准 + 跳过攻击后进化；old = 原来的绝对胜率、不跳过。"""
import random, sys
from collections import defaultdict
from multiprocessing import Pool
from svsim.agents.lethal_agent import LethalAgent
from svsim.agents.mcts_agent import MCTSAgent
from svsim.cards import decks
from svsim.core.engine import apply, legal_actions, new_game
from svsim.learn.model import Learned
from svsim.search.evaluate import DEFAULT
from svsim.ui.session import DECKS


def agent(kind, iters, learned, seed):
    w = Learned(fallback=DEFAULT) if learned else DEFAULT
    flag = kind == "new"
    return LethalAgent(MCTSAgent(iters, seed=seed, weights=w, center=flag, prune=flag), seed=seed, planner=True)


def play(job):
    name, (da, ka, ia, la), (db, kb, ib, lb), g = job
    seat = g % 2
    ds = [None, None]; ds[seat] = decks.build(DECKS[da][1]); ds[1 - seat] = decks.build(DECKS[db][1])
    s = new_game(*ds, seed=777000 + g, first=(g // 2) % 2)
    ag = [None, None]; ag[seat] = agent(ka, ia, la, 5000 + 2 * g); ag[1 - seat] = agent(kb, ib, lb, 5001 + 2 * g)
    while not s.over:
        apply(s, ag[s.active].act(s, legal_actions(s)))
    return name, 0.5 if s.winner not in (0, 1) else float(s.winner == seat)


MATCHES = {
    "学习版跳费龙 新 vs 旧（镜像）": (("ramp", "new", 100, True), ("ramp", "old", 100, True)),
    "手写跳费龙 新 vs 旧（镜像）": (("ramp", "new", 100, False), ("ramp", "old", 100, False)),
    "学习版跳费龙(新) vs 破魔虫 mcts:200+plan(新)": (("ramp", "new", 100, True), ("rhino", "new", 200, False)),
    "破魔虫 新 vs 旧 （对手同为旧跳费龙 mcts:200+plan）": None,
}
if __name__ == "__main__":
    n = int(sys.argv[1])
    jobs = [(name, a, b, g) for name, m in MATCHES.items() if m for a, b in [m] for g in range(n)]
    score = defaultdict(lambda: [0.0, 0])
    with Pool(4) as pool:
        for name, x in pool.imap_unordered(play, jobs):
            score[name][0] += x; score[name][1] += 1
    for name, (w, k) in score.items():
        p = w / k
        print(f"{name}: {w:g}/{k} = {p:.0%} ± {1.96 * (p * (1 - p) / k) ** 0.5:.0%}", flush=True)
