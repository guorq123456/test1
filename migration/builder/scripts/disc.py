import sys, json
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.search import combo
from svsim.cards import dragon
print("discard_face Depths", combo.discard_face(dragon.DEPTHS_OF_THE_ELD_BLADES))
for d in (dragon.SPILLING_RED, dragon.SAGATSUMATSU):
    pf = combo.profile_at(d, False, 10, 10, True)
    print(d.name, [(v[0].discards, v[0].hit, v[0].spread, len(v[0].added)) for v in pf])
games = {r["g"]: r for r in SD._lines(sys.argv[1] + "/selfplay.jsonl")}
rows = {json.loads(l)["game"]: json.loads(l) for l in open("/home/user/test1/analysis/speed/data/ramp_misses.jsonl")}
for g in map(int, sys.argv[2].split(",")):
    s = SD._state_at(games[g], rows[g]["at"])
    hp = s.players[1 - s.active].leader_hp
    for kw in (dict(tickers=True, fix=True, eot=True), dict(tickers=True, fix=True, eot=True, discard=True)):
        p = combo.plan(s, 20000, **kw)
        line, _ = combo.planned_lethal(s, 20000, **kw)
        print(g, "hp", hp, "discard" if kw.get("discard") else "lethal3", "dmg", p.damage, "verified", bool(line))
        if kw.get("discard"):
            print("   ", p.steps)
