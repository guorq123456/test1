"""The unrealized lethals of 6f11111 that +lethal2 still misses (lethal_m1.py's rows): for each, find_lethal's line
step by step with where the enemy leader's defense went (which action, which card, the kind of effect), the damage
estimate and the planner's figure, the nodes the full search needed, and the nodes with the spells-first order.
usage: ramp_misses.py STEP1_DIR M1.jsonl ROWS.jsonl"""
import json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "analysis" / "speed"))
S, M1, ROWS = sys.argv[1:4]
sys.path.insert(0, f"{S}/ana")
import student_data as SD
from svsim.core.actions import Attack, EndTurn, Engage, Evolve, PlayCard
from svsim.core.engine import apply
from svsim.search import combo
from svsim.search.lethal import LethalSearch, damage_estimate


def name(st, uid):
    c = st.in_play(uid) or next((x for p in st.players for x in p.hand if x.uid == uid), None)
    return c.defn.name if c is not None else ("leader" if uid < 0 else str(uid))


def describe(st, a):
    if isinstance(a, PlayCard):
        return f"play {name(st, a.uid)} -> {[name(st, t) for t in a.targets]}"
    if isinstance(a, Attack):
        return f"attack {name(st, a.attacker)} -> {name(st, a.target)}"
    if isinstance(a, Evolve):
        return f"{'super-' if a.super_ else ''}evolve {name(st, a.uid)}"
    if isinstance(a, Engage):
        return f"engage {name(st, a.uid)}"
    return type(a).__name__


m1 = [json.loads(l) for l in open(M1)]
rows = {json.loads(l)["key"]: json.loads(l) for l in open(ROWS) if l.strip()}
games = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}
for r in m1:
    if r["source"] != "6f11111" or r["realized"]:
        continue
    row = rows[f"g{r['game']}|at{r['at']}"]
    est, hp = row["estimate"], row["hp"]
    short = hp - est if not (isinstance(est, float) and math.isinf(est)) else -99
    b2 = 3000 if short <= 0 else 2000 if short <= 4 else 200
    if row["full_nodes"] <= b2 or row.get("agent"):
        continue                                   # +lethal2 recovers it
    st = SD._state_at(games[r["game"]], r["at"])
    full = LethalSearch(max_nodes=20000, seed=0).solve(st.clone())
    s, steps = st.clone(), []
    for a in full.line:
        hp0 = s.players[1 - st.active].leader_hp
        d = describe(s, a)
        if isinstance(a, EndTurn):
            from svsim.search.evaluate import after_end_of_turn
            s = after_end_of_turn(s)
        else:
            apply(s, a)
        steps.append(f"{d} [{hp0}->{s.players[1 - st.active].leader_hp}]")
        if s.over:
            break
    me = st.players[st.active]
    print(json.dumps({"game": r["game"], "at": r["at"], "hp": hp, "estimate": est, "planner": row.get("planner_damage"),
                      "full_nodes": row["full_nodes"], "pp": me.pp, "line": steps,
                      "hand": [c.defn.name for c in me.hand], "field": [c.defn.name for c in me.field],
                      "leader_area": [c.defn.name for c in me.leader_area],
                      "enemy": [(f.defn.name, f.atk, f.life, str(f.keywords)) for f in st.players[1 - st.active].followers]},
                     ensure_ascii=False), flush=True)
