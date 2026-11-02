"""演示：一个局面里每个合法动作在几个维度上的收益（只读，不改项目代码）。"""
import json, sys
sys.path.insert(0, "/home/user/test1/tests")
from svsim.cards import library, dragon  # 注册卡牌脚本
from svsim.tools import records
from svsim.core.engine import apply, legal_actions, _start_turn
from svsim.core.actions import EndTurn
from svsim.core.enums import Phase
from svsim.search.evaluate import after_end_of_turn
from svsim.search.combo import next_turn_damage
from svsim.search.lethal import face_damage
from svsim.ui.text import describe

def board(p):
    return sum(f.atk + max(f.life, 0) for f in p.followers)

def snapshot(s, me):
    m, o = s.players[me], s.players[1 - me]
    return dict(ohp=o.leader_hp, mhp=m.leader_hp, ob=board(o), mb=board(m), hand=len(m.hand), pp=m.pp, ep=m.ep + m.sep, reach=face_damage(s, me))

def turn_start_hits(s, me):
    """结束回合后、对手回合开始时，双方主战者血量的变化（纹章、回合开始效果等）。"""
    e = after_end_of_turn(s)
    if e.over: return 0, 0
    before = (e.players[1 - me].leader_hp, e.players[me].leader_hp)
    t = e.clone(); _start_turn(t)
    return t.players[1 - me].leader_hp - before[0], t.players[me].leader_hp - before[1]

def table(s, title):
    me = s.active
    base = snapshot(s, me)
    base_delay = turn_start_hits(s, me)
    base_pot = next_turn_damage(after_end_of_turn(s), me, 300)
    print(f"\n### {title}（{len(legal_actions(s))} 个合法动作）")
    print("动作 | 敌主战者 | 本回合还能打脸 | 敌场面 | 我场面 | 手牌 | PP | 进化点 | 对手回合开始时敌主战者 | 下回合可打伤害")
    for a in legal_actions(s):
        t = s.clone()
        if isinstance(a, EndTurn):
            d = {k: 0 for k in base}; delay = (0, 0); pot = 0
        else:
            apply(t, a)
            if t.over: print(describe(s, a), "| 直接获胜"); continue
            after = snapshot(t, me); d = {k: after[k] - base[k] for k in base}
            dl = turn_start_hits(t, me); delay = (dl[0] - base_delay[0], dl[1] - base_delay[1])
            pot = next_turn_damage(after_end_of_turn(t), me, 300) - base_pot
        name = "结束回合" if isinstance(a, EndTurn) else describe(s, a)
        print(f"{name} | {d['ohp']:+d} | {d['reach']:+d} | {d['ob']:+d} | {d['mb']:+d} | {d['hand']:+d} | {d['pp']:+d} | {d['ep']:+d} | {delay[0]:+d} | {pot:+d}")

D = "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad"
rec = json.load(open(D + "/game_evolve.json"))
for k, (s, a) in enumerate(records.steps(rec)):
    if k == 32:
        table(s.clone(), "你那局第 10 回合：AI 刚放下相枛津"); break

from helpers import start, put, unlock_evolution
s = start(); unlock_evolution(s, 0); s.players[0].hand.clear()
put(s, 0, dragon.BURNITE)
table(s, "示意局面：场上有焦灰的安纳提玛·班德奈特")
