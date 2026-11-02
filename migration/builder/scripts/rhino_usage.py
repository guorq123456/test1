"""AI 怎么用破魔虫：每次下场的连击数、打了多少、回合结束时破魔虫在哪。"""
import sys
sys.path.insert(0, "/home/user/test1")
from multiprocessing import Pool
from collections import Counter
from svsim.cards import decks, unlimited as U
from svsim.core.actions import PlayCard, Attack, EndTurn
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.state import leader_uid
from svsim.tools.arena import make_agent

def play(job):
    spec, g = job
    rhino, ramp = decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON)
    R = g % 2
    state = new_game(*((rhino, ramp) if R == 0 else (ramp, rhino)), seed=90000 + g // 2)
    agents = [None, None]
    agents[R] = make_agent(spec, 1000 + g); agents[1 - R] = make_agent("mcts:200+plan", 5000 + g)
    plays, ends, first_rhino_turn, face = [], Counter(), None, 0
    while not state.over:
        me = state.players[R]
        a = agents[state.active].act(state, legal_actions(state))
        if state.active == R:
            if isinstance(a, PlayCard) and state.in_hand(R, a.uid).defn == U.KILLER_RHINOCEROACH:
                plays.append((me.turns_taken, me.combo + 1))
            if isinstance(a, Attack) and a.target == leader_uid(1 - R):
                f = state.on_field(a.attacker)
                if f.defn == U.KILLER_RHINOCEROACH:
                    face += f.atk
            if isinstance(a, EndTurn):
                ends["场上"] += sum(1 for f in me.followers if f.defn == U.KILLER_RHINOCEROACH)
            if first_rhino_turn is None and any(c.defn == U.KILLER_RHINOCEROACH for c in me.hand):
                first_rhino_turn = me.turns_taken
        apply(state, a)
    return state.winner == R, plays, ends, first_rhino_turn, face

if __name__ == "__main__":
    spec, n = sys.argv[1], int(sys.argv[2])
    with Pool(4) as pool:
        res = pool.map(play, [(spec, g) for g in range(n)])
    plays = [p for r in res for p in r[1]]
    combos = Counter(c for _, c in plays)
    print(f"{spec}：{n} 局，胜 {sum(r[0] for r in res)}；破魔虫下场 {len(plays)} 次（每局 {len(plays)/n:.1f}）")
    print("  下场时的连击数分布:", sorted(combos.items()))
    print("  下场时是自己第几回合:", sorted(Counter(t for t, _ in plays).items()))
    print(f"  破魔虫打脸总伤害 {sum(r[4] for r in res)}，每局 {sum(r[4] for r in res)/n:.1f}")
    print(f"  回合结束时留在场上的破魔虫（会被对手处理）共 {sum(r[2]['场上'] for r in res)} 只次")
    t = [r[3] for r in res if r[3] is not None]
    print(f"  第一次手里有破魔虫：自己第 {sorted(t)[len(t)//2] if t else '-'} 回合（中位数），{n - len(t)} 局整局没摸到")
