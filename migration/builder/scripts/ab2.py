"""对照：破魔虫 新/旧 搜索（同一个旧跳费龙对手）；跳费龙学习版 投影后/投影前。"""
import sys
from collections import defaultdict
from multiprocessing import Pool
from svsim.agents.lethal_agent import LethalAgent
from svsim.agents.mcts_agent import MCTSAgent
from svsim.cards import decks
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Craft
from svsim.learn.model import Learned, LinearValue
from svsim.search.evaluate import DEFAULT
from svsim.ui.session import DECKS

BEFORE = "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/dragon_before_projection.json"


def agent(kind, iters, model, seed):
    from pathlib import Path
    w = DEFAULT if model is None else Learned(fallback=DEFAULT) if model == "now" else \
        Learned(models={Craft.DRAGON: LinearValue.load(Path(BEFORE))}, fallback=DEFAULT)
    flag = kind == "new"
    return LethalAgent(MCTSAgent(iters, seed=seed, weights=w, center=flag, prune=flag), seed=seed, planner=True)


def play(job):
    name, (da, ka, ia, la), (db, kb, ib, lb), g = job
    seat = g % 2
    ds = [None, None]; ds[seat] = decks.build(DECKS[da][1]); ds[1 - seat] = decks.build(DECKS[db][1])
    s = new_game(*ds, seed=888000 + g, first=(g // 2) % 2)
    ag = [None, None]; ag[seat] = agent(ka, ia, la, 6000 + 2 * g); ag[1 - seat] = agent(kb, ib, lb, 6001 + 2 * g)
    while not s.over:
        apply(s, ag[s.active].act(s, legal_actions(s)))
    return name, 0.5 if s.winner not in (0, 1) else float(s.winner == seat)


MATCHES = {
    "破魔虫(新) vs 手写跳费龙 mcts:200+plan(旧)": (("rhino", "new", 200, None), ("ramp", "old", 200, None)),
    "破魔虫(旧) vs 手写跳费龙 mcts:200+plan(旧)": (("rhino", "old", 200, None), ("ramp", "old", 200, None)),
    "学习版跳费龙 投影后 vs 投影前（都用新搜索，镜像）": (("ramp", "new", 100, "now"), ("ramp", "new", 100, "before")),
    "学习版跳费龙 投影后 vs 破魔虫 mcts:200+plan（新）": (("ramp", "new", 100, "now"), ("rhino", "new", 200, None)),
}
if __name__ == "__main__":
    n = int(sys.argv[1])
    jobs = [(name, a, b, g) for name, (a, b) in MATCHES.items() for g in range(n)]
    score = defaultdict(lambda: [0.0, 0])
    with Pool(4) as pool:
        for name, x in pool.imap_unordered(play, jobs):
            score[name][0] += x; score[name][1] += 1
    for name in MATCHES:
        w, k = score[name]; p = w / k
        print(f"{name}: {w:g}/{k} = {p:.0%} ± {1.96 * (p * (1 - p) / k) ** 0.5:.0%}", flush=True)
