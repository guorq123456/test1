"""Offline: what other lethal-screen budgets would find, and cost, from lethal_miss.py's rows. With the same seed and
move order a search of budget B visits the first B nodes of the full search, so it finds a lethal exactly when the
full search found it within B nodes, and spends min(B, the full search's nodes) on any position (the full search
stops at its first sure lethal, at a complete tree, or at 20000). The agent tries the planner first (+plan): a
start it found costs no search under any policy. Milliseconds per node from the rows themselves.
usage: lethal_policies.py ROWS.jsonl M1.jsonl"""
import json, math, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
m1 = {(r["game"], r["at"]): r for r in (json.loads(l) for l in open(sys.argv[2])) if r["source"] == "6f11111"}
rows = [r for r in rows if r["src"] == "selfplay"]
ms_per_node = 1000 * sum(r["s_full"] for r in rows) / sum(r["full_nodes"] for r in rows)


def budget(r, max_nodes=2000, screen=200, near=(1000, 4)):
    est = r["estimate"]
    short = r["hp"] - est if est is not None and not (isinstance(est, float) and math.isinf(est)) else -1
    if screen is None or short <= 0:
        return max_nodes
    return near[0] if near is not None and short <= near[1] else screen


def run(name, **kw):
    found = cost = 0
    rec_miss = rec_unreal = 0
    for r in rows:
        planner = r.get("full") and r.get("agent") == "planner"
        b = budget(r, **kw)
        if not planner:
            cost += min(b, r["full_nodes"])
        if r.get("full"):
            ok = planner or r["full_nodes"] <= b
            found += ok
            if ok and not r["agent"]:
                rec_miss += 1
                key = (int(r["key"].split("|")[0][1:]), int(r["key"].split("|")[1][2:]))
                rec_unreal += not m1[key]["realized"]
    return {"policy": name, "finds": found, "recovers_start_misses": rec_miss, "of_them_not_realized_in_play": rec_unreal,
            "nodes_per_start": round(cost / len(rows), 1), "ms_per_start": round(cost / len(rows) * ms_per_node, 1)}


cur = run("current: 2000 / screen 200 / near 1000 within 4")
sure = [r for r in rows if r.get("full")]
agree = sum(1 for r in sure if bool(r["agent"]) == ((r["agent"] == "planner") or r["full_nodes"] <= budget(r)))
print(json.dumps({"lethal_starts": len(sure), "agent_finds": sum(1 for r in sure if r["agent"]), "model_agrees": agree,
                  "ms_per_node": round(ms_per_node, 3), "starts": len(rows)}))
base = cur["ms_per_start"]
for name, kw in [("current: 2000 / screen 200 / near 1000 within 4", {}),
                 ("near within 8", dict(near=(1000, 8))),
                 ("near 3000 within 4", dict(near=(3000, 4))),
                 ("near 3000 within 8", dict(near=(3000, 8))),
                 ("near 6000 within 8", dict(near=(6000, 8))),
                 ("screen 1000", dict(screen=1000)),
                 ("no screen, 2000", dict(screen=None)),
                 ("no screen, 6000", dict(screen=None, max_nodes=6000)),
                 ("no screen, 20000 (find_lethal)", dict(screen=None, max_nodes=20000))]:
    r = run(name, **kw)
    r["added_ms_per_start"] = round(r["ms_per_start"] - base, 1)
    print(json.dumps(r))
missed = [r for r in sure if not r["agent"]]
print(json.dumps({"start_misses": len(missed),
                  "their_full_nodes": sorted(r["full_nodes"] for r in missed),
                  "their_shortfall": sorted(r["hp"] - r["estimate"] for r in missed)}))
