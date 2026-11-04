"""在玩家记下的局面上反复让 AI 重走，统计“先打脸后进化”的比例。"""
import json, sys
from collections import Counter
from svsim.tools import records
from svsim.tools.arena import make_agent
from svsim.core.engine import apply, legal_actions
from svsim.core.actions import Attack, Evolve, EndTurn
from svsim.core.enums import Phase

D = "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad"
rec = json.load(open(D + "/game_evolve.json"))
specs = sys.argv[1].split(",")
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 20


def position(at):
    for k, (s, a) in enumerate(records.steps(rec)):
        if k == at:
            return s.clone()


def turn_line(state, agent):
    """The AI plays the rest of its turn; returns the order of attack/evolve and the face damage."""
    s = state.clone(); me = s.active; hp0 = s.players[1 - me].leader_hp; order = []
    for _ in range(40):
        if s.over or s.active != me or s.phase != Phase.MAIN:
            break
        a = agent.act(s, legal_actions(s))
        if isinstance(a, Attack):
            order.append("打")
        elif isinstance(a, Evolve):
            order.append("进化")
        if isinstance(a, EndTurn):
            break
        apply(s, a)
    return "→".join(order), hp0 - s.players[1 - me].leader_hp


for at in (32, 48):
    base = position(at)
    for spec in specs:
        c, dmg = Counter(), Counter()
        for seed in range(runs):
            line, d = turn_line(base, make_agent(spec, 1000 + seed))
            c[line] += 1; dmg[d] += 1
        print(f"动作{at} {spec}: {dict(c)} 打脸伤害 {dict(sorted(dmg.items()))}", flush=True)
