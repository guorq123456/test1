import json, sys
sys.path.insert(0, "/home/user/test1")
from collections import Counter
from svsim.tools import records
from svsim.core.actions import Attack, EndTurn
from svsim.core.engine import legal_actions, apply
from svsim.tools.arena import make_agent
from svsim.ui.text import card_name, describe, render_state
G = "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/db_v4/games/"
r = json.load(open(G + "1791263900463.json"))["record"]
for k, (state, action) in enumerate(records.steps(r)):
    if k == 18: state = state.clone(); break
# back up to the start of the AI's turn 6
for k, (s, a) in enumerate(records.steps(r)):
    if s.turn == 6 and s.active == 1: start = s.clone(); break
print(render_state(start, viewer=1))
spec = sys.argv[1] if len(sys.argv) > 1 else "mcts:200+plan+learned"
killed = Counter()
for seed in range(int(sys.argv[2]) if len(sys.argv) > 2 else 6):
    agent = make_agent(spec, seed)
    s = start.clone(); line = []
    for _ in range(30):
        if s.over or s.active != 1: break
        a = agent.act(s, legal_actions(s))
        if isinstance(a, EndTurn): break
        line.append(describe(s, a)); apply(s, a)
    left = tuple(sorted(card_name(c.defn) for c in s.players[0].followers))
    killed[left] += 1
    print(seed, " → ".join(line), "| 你场上剩下:", left)
print(killed)
