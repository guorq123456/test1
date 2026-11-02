"""我的整回合规划在学习版跳费龙镜像里：搜不完的比例，以及计划是否因预算耗尽而提前结束回合。"""
from multiprocessing import Pool
from svsim.cards import decks, library
from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Phase
from svsim.tools.arena import make_agent
from svsim.search import turnplan

def game(g):
    s = new_game(decks.build(decks.RAMP_DRAGON), decks.build(decks.RAMP_DRAGON), seed=4242 + g)
    a = [make_agent("turn:3000+plan+learned", 10 + g), make_agent("mcts:200+plan+learned", 20 + g)]
    planner_agent = a[0].base                      # LethalAgent wraps the TurnPlanAgent
    stats = dict(plans=0, incomplete=0, early_end=0, ends=0)
    orig = planner_agent.planner.plan
    def plan(state):
        r = orig(state)
        stats["plans"] += 1
        if not r.complete:
            stats["incomplete"] += 1
            if r.line and isinstance(r.line[-1], EndTurn) and len(legal_actions(state)) > 1:
                stats["early_end"] += 1
        return r
    planner_agent.planner.plan = plan
    while not s.over:
        apply(s, a[s.active].act(s, legal_actions(s)))
    return stats

if __name__ == "__main__":
    tot = {}
    with Pool(4) as p:
        for st in p.imap_unordered(game, range(8)):
            for k, v in st.items(): tot[k] = tot.get(k, 0) + v
    print(tot, f"搜不完 {tot['incomplete']/tot['plans']:.0%}")
