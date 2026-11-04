"""整回合规划 vs 现在的 MCTS：胜率 + 每回合行为统计（手牌、进化点、PP 浪费）。"""
import json, sys, time, random
from collections import defaultdict
from multiprocessing import Pool
from svsim.cards import decks, library
from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Phase
from svsim.tools.arena import make_agent
from svsim.ui.session import DECKS


def play(job):
    name, (da, sa), (db, sb), g = job
    seat = g % 2
    ds = [None, None]; ds[seat] = decks.build(DECKS[da][1]); ds[1 - seat] = decks.build(DECKS[db][1])
    s = new_game(*ds, seed=555000 + g, first=(g // 2) % 2)
    specs = [None, None]; specs[seat] = sa; specs[1 - seat] = sb
    ag = [make_agent(specs[i], 9000 + 2 * g + i) for i in range(2)]
    clock = [0.0, 0.0]; moves = [0, 0]; turns = []
    while not s.over:
        me = s.active
        t0 = time.perf_counter(); a = ag[me].act(s, legal_actions(s)); clock[me] += time.perf_counter() - t0; moves[me] += 1
        if isinstance(a, EndTurn) and s.phase == Phase.MAIN:
            p = s.players[me]
            turns.append(dict(side="a" if me == seat else "b", n=p.turns_taken, hand=len(p.hand), pp_left=p.pp,
                              max_pp=p.max_pp, ep=p.ep + p.sep, board=len(p.followers)))
        apply(s, a)
    win = 0.5 if s.winner not in (0, 1) else float(s.winner == seat)
    return dict(name=name, win=win, turns=turns, ms=[clock[seat] / max(moves[seat], 1) * 1000,
                                                       clock[1 - seat] / max(moves[1 - seat], 1) * 1000],
                length=s.turn)


MATCHES = {
    "跳费龙镜像·学习版：整回合规划 vs MCTS200": (("ramp", "turn:3000+plan+learned"), ("ramp", "mcts:200+plan+learned")),
    "跳费龙镜像·手写：整回合规划 vs MCTS200": (("ramp", "turn:3000+plan"), ("ramp", "mcts:200+plan")),
    "破魔虫(整回合规划) vs 跳费龙 mcts:200+plan": (("rhino", "turn:3000+plan"), ("ramp", "mcts:200+plan")),
    "破魔虫(MCTS200，对照) vs 跳费龙 mcts:200+plan": (("rhino", "mcts:200+plan"), ("ramp", "mcts:200+plan")),
}

if __name__ == "__main__":
    n = int(sys.argv[1]); out = sys.argv[2]
    jobs = [(name, a, b, g) for name, (a, b) in MATCHES.items() for g in range(n)]
    results = []
    with Pool(4) as pool:
        for k, r in enumerate(pool.imap_unordered(play, jobs), 1):
            results.append(r)
            if k % 20 == 0:
                json.dump(results, open(out, "w"), ensure_ascii=False); print(k, flush=True)
    json.dump(results, open(out, "w"), ensure_ascii=False)
    print("done", flush=True)
