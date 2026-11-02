import sys, time, random
sys.path.insert(0, "/home/user/test1")
from svsim.cards import decks
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.actions import EndTurn
from svsim.agents.greedy_agent import GreedyAgent
from svsim.search import combo as C

rhino, ramp = decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON)
states = []
for g in range(12):
    s = new_game(rhino, ramp, seed=g)
    agents = [GreedyAgent(g), GreedyAgent(g + 100)]
    while not s.over:
        a = agents[s.active].act(s, legal_actions(s))
        if isinstance(a, EndTurn) and s.active == 0 and s.players[0].turns_taken >= 3:
            states.append(s.clone())
        apply(s, a)
print(len(states), "个破魔虫回合结束局面")
ref = {}
for budget in (200000, 20000, 3000, 1000, 300):
    C._NEXT_TURN.clear()
    t = time.perf_counter(); vals = []
    times = []
    for i, s in enumerate(states):
        t0 = time.perf_counter()
        vals.append(C.next_turn_damage(s, 0, budget))
        times.append(time.perf_counter() - t0)
    if budget == 200000: ref = vals
    exact = sum(v == r for v, r in zip(vals, ref))
    times.sort()
    print(f"预算 {budget:>6}: 中位数 {times[len(times)//2]*1000:.1f} ms, 90% {times[int(.9*len(times))]*1000:.0f} ms, 最长 {times[-1]*1000:.0f} ms; "
          f"和 20 万节点结果一致 {exact}/{len(vals)}, 平均差 {sum(r - v for v, r in zip(vals, ref))/len(vals):.2f}")
