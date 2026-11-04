import json, sys
sys.path.insert(0, "/home/user/test1")
from svsim.tools import records
from svsim.core.actions import PlayCard
from svsim.core.engine import legal_actions, play_form, apply
from svsim.core.enums import Phase
from svsim.tools.arena import make_agent
from svsim.search.mcts import action_key
from svsim.search.evaluate import evaluate, after_end_of_turn
from svsim.ui.text import describe, render_state
from svsim.learn.model import Learned
G = "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/db_v3/games/"
fname, turn = sys.argv[1], int(sys.argv[2])
r = json.load(open(G + fname))["record"]
for state, action in records.steps(r):
    if state.active == 1 and state.phase == Phase.MAIN and state.turn == turn:
        break
print(render_state(state, viewer=1))
print("actually played:", describe(state, action))
agent = make_agent("mcts:200+plan+learned", 1)
a = agent.act(state, legal_actions(state))
search = agent.base.search
root = search.last_root
legal = {action_key(state, x): x for x in legal_actions(state)}
rows = sorted(((root.children[k].visits, search.estimate(root.children[k]), describe(state, legal[k])) for k in root.children if k in legal), reverse=True)
print("AI picks:", describe(state, a))
for v, e, d in rows[:12]: print(f"  {v:4d} {e:.3f} {d}")
# one-step static scores with the learned evaluation, as if the turn ended after it
L = Learned()
for x in legal_actions(state):
    if isinstance(x, PlayCard) and state.in_hand(1, x.uid).defn.card_id == 10844120:
        s = state.clone(); apply(s, x); e = after_end_of_turn(s)
        print("accelerate then end: learned", round(evaluate(e, 1, L), 3), "| end now:", round(evaluate(after_end_of_turn(state), 1, L), 3))
