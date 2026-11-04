"""看一局：破魔虫（mcts:200+plan）对跳费龙（mcts:200），逐回合记录。"""
import sys
sys.path.insert(0, "/home/user/test1")
from svsim.cards import decks
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.actions import EndTurn, Mulligan
from svsim.tools.arena import make_agent
from svsim.ui.text import describe, card_name

seed = int(sys.argv[1]); rhino_first = int(sys.argv[2]) if len(sys.argv) > 2 else 0
rhino, ramp = decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON)
d = (rhino, ramp) if rhino_first == 0 else (ramp, rhino)
R = 0 if rhino_first == 0 else 1
state = new_game(*d, seed=seed)
agents = [None, None]
agents[R] = make_agent("mcts:200+plan", seed); agents[1 - R] = make_agent("mcts:200", seed + 1)
last_turn = None
while not state.over:
    p = state.players[state.active]
    a = agents[state.active].act(state, legal_actions(state))
    if state.turn != last_turn:
        last_turn = state.turn
        me, op = state.players[R], state.players[1 - R]
        side = "破魔虫" if state.active == R else "跳费龙"
        print(f"\n== 回合 {state.turn}（{side}）破魔虫 {me.leader_hp} 血 / 龙 {op.leader_hp} 血；PP {p.max_pp}")
        if state.active == R:
            print("   手牌:", [card_name(c.defn) for c in me.hand])
            print("   场上:", [(card_name(c.defn), c.atk, c.life) for c in me.field], "| 敌方:", [(card_name(c.defn), c.atk, c.life) for c in op.followers])
    if not isinstance(a, Mulligan):
        print("   ", "破" if state.active == R else "龙", describe(state, a))
    else:
        print("   换牌", [card_name(p.hand[i].defn) for i in a.indices] if hasattr(a, "indices") else a)
    apply(state, a)
print("\n胜者:", "破魔虫" if state.winner == R else "跳费龙")
