import sys, json, random
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.search import combo
from svsim.core.engine import apply
games = {r["g"]: r for r in SD._lines(sys.argv[1] + "/selfplay.jsonl")}
s = SD._state_at(games[109], 73)
p = combo.plan(s, 20000, fix=True, eot=True)
line = combo.realize(s, p.steps, face_first=True)
rng = random.Random(0)
for i in range(16):
    t = s.clone(); t.rng.seed(rng.getrandbits(64))
    for pl in t.players: t.rng.shuffle(pl.deck)
    me = t.active; log = []
    for a in line:
        if t.over: break
        if not combo._legal(t, a):
            log.append(f"ILLEGAL {a}"); break
        hand = [c.defn.name for c in t.players[me].hand]
        apply(t, a)
        log.append(f"{a} hp={t.players[1-me].leader_hp}")
    if t.winner != me:
        print(i, "FAIL", log[-3:], [c.defn.name for c in t.players[me].hand]); 
