"""整回合规划的开销：在真实对局的回合开头，不同预算下的节点数、用时、能否搜完。"""
import random, statistics as st, sys
from svsim.cards import decks, library
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Phase
from svsim.tools.arena import make_agent
from svsim.search.turnplan import TurnPlanner
from svsim.search.evaluate import DEFAULT
from svsim.ui.session import DECKS

def starts(da, db, seed, spec="mcts:100+plan"):
    s = new_game(decks.build(DECKS[da][1]), decks.build(DECKS[db][1]), seed=seed)
    ags = [make_agent(spec, seed * 2 + i) for i in range(2)]
    out, turn = [], None
    while not s.over:
        if s.phase == Phase.MAIN and s.turn != turn:
            turn = s.turn; out.append(s.clone())
        apply(s, ags[s.active].act(s, legal_actions(s)))
    return out

pos = {"跳费龙": [], "破魔虫": []}
for g in range(3):
    for s in starts("rhino", "ramp", 100 + g):
        pos["破魔虫" if s.active == 0 else "跳费龙"].append(s)
for name, ps in pos.items():
    ps = [p for p in ps if p.turn >= 5][:24]
    for budget in (1000, 3000, 10000):
        secs, nodes, done = [], [], 0
        for p in ps:
            r = TurnPlanner(max_nodes=budget).plan(p)
            secs.append(r.seconds); nodes.append(r.nodes); done += r.complete
        secs.sort()
        print(f"{name} 预算 {budget:5}: {len(ps)} 个回合，搜完 {done}，用时 中位 {st.median(secs):.2f}s 最慢 {secs[-1]:.2f}s 平均 {st.mean(secs):.2f}s", flush=True)
