import sys
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.search import combo
from svsim.core.engine import apply, legal_actions
games = {r["g"]: r for r in SD._lines(sys.argv[1] + "/selfplay.jsonl")}
for key, n in (("g80|at54", 2), ("g210|at41", 2)):
    g, at = key.split("|"); s = SD._state_at(games[int(g[1:])], int(at[2:]))
    p = combo.plan(s, 20000, tickers=True, fix=True, eot=True, discard=True)
    line = combo.realize(s, p.steps[:n], face_first=True, discard=True)
    x = s.clone()
    for a in line: apply(x, a)
    me = x.active
    unknown = {c.uid for c in s.players[me].deck_view()}
    print(key, "hand", [(c.uid, c.defn.name, c.cost, c.uid in unknown) for c in x.players[me].hand])
    print("  enemy", [(c.uid, c.defn.name, c.atk, c.life, str(c.keywords)) for c in x.players[1-me].followers])
    print("  step", p.steps[n])
    for a in legal_actions(x):
        if type(a).__name__ == "PlayCard" and x.in_hand(me, a.uid).defn.name.startswith("Spilling"):
            print("   ", a)
