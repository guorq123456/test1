import sys, json
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.search import combo
from svsim.cards.pool import POOL
games = {r["g"]: r for r in SD._lines(sys.argv[1] + "/selfplay.jsonl")}
rows = {json.loads(l)["game"]: json.loads(l) for l in open("/home/user/test1/analysis/speed/data/ramp_misses.jsonl")}
for g in map(int, sys.argv[2].split(",")):
    r = rows[g]; s = SD._state_at(games[g], r["at"])
    me, op = s.players[s.active], s.players[1 - s.active]
    print("=== g", g, "hp", op.leader_hp, "pp", me.pp, "/", me.max_pp, "ep/sep", me.ep, me.sep, "turns", me.turns_taken)
    print(" hand", [(c.defn.name, c.cost) for c in me.hand])
    print(" field", [(c.defn.name, c.atk, c.life) for c in me.field])
    print(" enemy", [(c.defn.name, c.atk, c.life, str(c.keywords)) for c in op.followers])
    print(" find_lethal line", r["line"])
    p = combo.plan(s, 20000, fix=True, eot=True)
    print(" plan dmg", p.damage, p.steps)
    for n in range(1, len(p.steps) + 1):
        if not combo.realize(s, p.steps[:n], face_first=True):
            print(" realize FAILS at step", n, p.steps[n - 1]); break
    else:
        line = combo.realize(s, p.steps, face_first=True)
        print(" realized; verify", bool(line) and combo.verify(s, line))
    line = combo.realize(s, p.steps, face_first=True)
    from svsim.core.engine import apply, legal_actions
    x = s.clone()
    for a, st in zip(line, p.steps):
        ok = a in legal_actions(x)
        apply(x, a)
        print("   ", st[:2], "->", a, "legal" if ok else "ILLEGAL", "enemy hp", x.players[1 - s.active].leader_hp, "pp", x.players[s.active].pp, "over", x.over)
    print("   hand after", [c.defn.name for c in x.players[s.active].hand])
