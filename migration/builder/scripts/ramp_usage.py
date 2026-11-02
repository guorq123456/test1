"""跳费龙一方：龙之启示第一次打出是自己第几回合、前 4 回合 PP 利用率、胜率（对固定的破魔虫 AI）。"""
import sys, statistics
sys.path.insert(0, "/home/user/test1")
from multiprocessing import Pool
from svsim.cards import decks
from svsim.core.actions import PlayCard, EndTurn
from svsim.core.engine import apply, legal_actions, new_game
from svsim.tools.arena import make_agent

def play(job):
    ramp_spec, rhino_spec, g = job
    R = g % 2                                         # 跳费龙的座位
    d = (decks.build(decks.RAMP_DRAGON), decks.build(decks.RHINO_FOREST))
    state = new_game(*(d if R == 0 else d[::-1]), seed=70000 + g // 2)
    agents = [None, None]; agents[R] = make_agent(ramp_spec, g); agents[1 - R] = make_agent(rhino_spec, 9000 + g)
    first_rev, used, avail = None, 0, 0
    while not state.over:
        p = state.players[state.active]
        a = agents[state.active].act(state, legal_actions(state))
        if state.active == R:
            if isinstance(a, PlayCard) and first_rev is None and state.in_hand(R, a.uid).defn.name_zh == "龙之启示":
                first_rev = p.turns_taken
            if isinstance(a, EndTurn) and p.turns_taken <= 4:
                used += p.max_pp - p.pp; avail += p.max_pp
        apply(state, a)
    return state.winner == R, first_rev, used / max(avail, 1)

if __name__ == "__main__":
    ramp_spec, rhino_spec, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    with Pool(4) as pool:
        res = pool.map(play, [(ramp_spec, rhino_spec, g) for g in range(n)])
    revs = [r[1] for r in res if r[1] is not None]
    print(f"跳费龙 {ramp_spec} 对 破魔虫 {rhino_spec}：胜 {sum(r[0] for r in res)}/{n}；"
          f"龙之启示第一次打出：中位数自己第 {statistics.median(revs) if revs else '-'} 回合（{len(revs)}/{n} 局打出过）；"
          f"前 4 回合 PP 利用率 {statistics.mean(r[2] for r in res):.0%}")
