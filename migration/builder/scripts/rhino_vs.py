"""固定跳费龙一方的 AI，只换破魔虫一方，先后手各半。"""
import sys, pickle, random, time
sys.path.insert(0, "/home/user/test1")
from multiprocessing import Pool
from svsim.cards import decks
from svsim.core.engine import apply, legal_actions, new_game
from svsim.tools.arena import make_agent

def play(job):
    rhino_spec, ramp_spec, g = job
    rhino, ramp = decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON)
    R = g % 2                                     # 破魔虫先手 / 后手各半
    d = (rhino, ramp) if R == 0 else (ramp, rhino)
    state = new_game(*d, seed=90000 + g // 2)     # 同一个种子先后手各打一次
    agents = [None, None]
    agents[R] = make_agent(rhino_spec, 1000 + g); agents[1 - R] = make_agent(ramp_spec, 5000 + g)
    clock = [0.0, 0]
    while not state.over:
        t = time.perf_counter()
        a = agents[state.active].act(state, legal_actions(state))
        if state.active == R:
            clock[0] += time.perf_counter() - t; clock[1] += 1
        apply(state, a)
    return state.winner == R, state.turn, clock, getattr(agents[R], "lethals", 0)

if __name__ == "__main__":
    ramp_spec, n = sys.argv[1], int(sys.argv[2])
    out = {}
    for rhino_spec in sys.argv[3:]:
        with Pool(4) as pool:
            res = pool.map(play, [(rhino_spec, ramp_spec, g) for g in range(n)])
        wins = sum(r[0] for r in res); p = wins / n; m = 1.96 * (p * (1 - p) / n) ** .5
        ms = sum(r[2][0] for r in res) / max(1, sum(r[2][1] for r in res)) * 1000
        print(f"破魔虫 {rhino_spec:<24} 对 跳费龙 {ramp_spec}：{wins}/{n} 胜 {p:.0%} ± {m:.0%}，"
              f"每步 {ms:.0f} 毫秒，斩杀 {sum(r[3] for r in res)} 次，平均结束回合 {sum(r[1] for r in res)/n:.1f}", flush=True)
        out[rhino_spec] = res
    pickle.dump(out, open("rhino_vs.pkl", "wb"))
