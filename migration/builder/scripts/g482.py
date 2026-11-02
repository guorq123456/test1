import sys, json
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.search import combo
from svsim.core.engine import apply, legal_actions
games = {r["g"]: r for r in SD._lines(sys.argv[1] + "/selfplay.jsonl")}
s = SD._state_at(games[482], 63)
me, op = s.players[s.active], s.players[1 - s.active]
print("hp", op.leader_hp, "pp", me.pp, me.max_pp, "ep/sep", me.ep, me.sep)
print("hand", [(c.defn.name, c.cost) for c in me.hand]); print("field", [(c.defn.name, c.atk, c.life, c.attacks_made, c.max_attacks) for c in me.field])
print("enemy", [(c.defn.name, c.atk, c.life, str(c.keywords)) for c in op.followers])
p = combo.plan(s, 20000, tickers=True, fix=True, eot=True, discard=True)
for n in range(1, len(p.steps) + 1):
    line = combo.realize(s, p.steps[:n], face_first=True, discard=True)
    if not line:
        print("FAIL at", n, p.steps[n - 1]); break
line = combo.realize(s, p.steps, face_first=True, discard=True)
if line:
    x = s.clone()
    for a, st in zip(line, p.steps):
        apply(x, a); print("  ", st[:2], a, "hp", x.players[1 - s.active].leader_hp, "over", x.over)
line2 = combo.realize(s, p.steps[:2], face_first=True, discard=True)
x = s.clone()
for a in line2: apply(x, a)
me2 = x.players[x.active]
print("hand now", [(c.uid, c.defn.name, c.cost) for c in me2.hand])
for a in legal_actions(x):
    if hasattr(a, "uid") and type(a).__name__ == "PlayCard" and x.in_hand(x.active, a.uid).defn.name.startswith("Spilling"):
        print(a)
print("enemy uids", [(c.uid, c.defn.name) for c in x.players[1 - x.active].followers])
