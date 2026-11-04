import sys, time
sys.path.insert(0, "/home/user/test1")
from multiprocessing import Pool
from svsim.cards import decks
from svsim.core.engine import new_game
from svsim.search import race
from svsim.agents.greedy_agent import mulligan as cost_rule
from svsim.ui.text import card_name
def job(seed):
    s = new_game(decks.build(decks.RAMP_DRAGON), decks.build(decks.RHINO_FOREST), seed=seed, first=seed % 2)
    if s.active != 0:
        from svsim.core.engine import apply
        from svsim.core.actions import Mulligan
    hand = s.players[s.active].hand
    t = time.perf_counter()
    m, exp = race.mulligan(s, samples=6, seed=seed)
    names = [card_name(c.defn) for c in hand]
    return (s.active == s.first, names, [names[i] for i in m.indices], [names[i] for i in cost_rule(s).indices], round(exp, 2), round(time.perf_counter() - t, 1))
if __name__ == "__main__":
    with Pool(4) as pool:
        for first, names, clockred, rule, exp, sec in pool.map(job, range(16)):
            print(f"{'先' if first else '后'} 手牌 {'、'.join(names)}\n    时钟换掉: {'、'.join(clockred) or '不换'} (期望 {exp})  | 费用规则换掉: {'、'.join(rule) or '不换'}  {sec}s")
