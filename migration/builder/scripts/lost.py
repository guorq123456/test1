import sys, json
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.search import combo
games = {r["g"]: r for r in SD._lines(sys.argv[1] + "/selfplay.jsonl")}
for key in sys.argv[2].split(","):
    _, g, at = key.split("|"); s = SD._state_at(games[int(g[1:])], int(at[2:]))
    hp = s.players[1 - s.active].leader_hp
    kw = dict(tickers=True, fix=True, eot=True)
    p0 = combo.plan(s, 20000, **kw); p1 = combo.plan(s, 20000, discard=True, **kw)
    print(key, "hp", hp, "lethal3 dmg", p0.damage, "discard dmg", p1.damage)
    print("  L3:", p0.steps); print("  D :", p1.steps)
    l1 = combo.realize(s, p1.steps, face_first=True, discard=True)
    if l1 is None:
        for n in range(1, len(p1.steps) + 1):
            if not combo.realize(s, p1.steps[:n], face_first=True, discard=True):
                print("  D fails at", n, p1.steps[n-1]); break
    else:
        print("  D realized, verify", combo.verify(s, l1))
