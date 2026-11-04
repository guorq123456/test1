import json, glob, sys
sys.path.insert(0, "/home/user/test1")
from svsim.tools import records
from svsim.core.actions import PlayCard, EndTurn
from svsim.core.engine import legal_actions, play_form
from svsim.core.enums import Phase
from svsim.tools.arena import make_agent
from svsim.search.mcts import action_key
from svsim.ui.text import describe, card_name
G = "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/db_v3/games/"
LUM = 10844120
for f in sorted(glob.glob(G + "*.json")):
    r = json.load(open(f))["record"]
    turn_plays, chances = {}, []
    for state, action in records.steps(r):
        if state.active != 1 or state.phase != Phase.MAIN:
            continue
        if not isinstance(action, EndTurn):
            turn_plays.setdefault(state.turn, []).append(describe(state, action))
        if state.turn in [c.turn for c in chances]:
            continue
        p = state.players[1]
        lum = [c for c in p.hand if c.defn.card_id == LUM]
        if lum:
            form = play_form(p, lum[0])
            if form is not None and form.alt is not None:
                chances.append(state.clone())
    for state in chances:
        p = state.players[1]
        agent = make_agent(r["ai"], 7)
        agent.act(state, legal_actions(state))
        search = getattr(agent.base, "search", None)
        if search is None or search.last_root is None:
            print(f[-18:-5], state.turn, "(lethal agent decided)"); continue
        root = search.last_root
        legal = {action_key(state, x): x for x in legal_actions(state)}
        est = {k: (root.children[k].visits, search.estimate(root.children[k])) for k in root.children if k in legal}
        acc = next(k for k, x in legal.items() if isinstance(x, PlayCard) and state.in_hand(1, x.uid).defn.card_id == LUM)
        best = max(est, key=lambda k: est[k][1])
        print(f"{f[-18:-5]} t{state.turn:2d} {r['ai']:22s} maxPP {p.max_pp} PP {p.pp} | accelerate {est.get(acc, (0, 0))[0]:3d} visits {est.get(acc,(0,0))[1]:.3f} | best {est[best][1]:.3f} {describe(state, legal[best])[:30]}")
        print("      played that turn:", " / ".join(turn_plays.get(state.turn, ["结束回合"]))[:150])
