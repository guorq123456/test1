"""plannerfix_eval.py's rows read at the agent's level: the agent finds a lethal at a turn start by its planner or,
failing that, by its screened search (unchanged by the planner flags). Joined with lethal_miss.py's rows (find_lethal's
verdict, the search's) and lethal_m1.py's (realized), and the pirate sample's rows.
usage: plannerfix_agent.py PLANNERFIX.jsonl ROWS.jsonl M1.jsonl PIRATE_ROWS.jsonl"""
import json, sys
PF, ROWS, M1, PIR = sys.argv[1:5]
rows = [json.loads(l) for l in open(PF)]
lm = {json.loads(l)["key"]: json.loads(l) for l in open(ROWS) if l.strip()}
pir = {json.loads(l)["key"]: json.loads(l) for l in open(PIR) if l.startswith('{"src')}
m1 = {(r["game"], r["at"]): r for r in (json.loads(l) for l in open(M1)) if r["source"] == "6f11111"}
for deck in ("ramp", "pirate"):
    rs = [r for r in rows if r["key"].startswith(deck)]
    for m in ("fix", "fix+eot"):
        c = {"agent finds, plain": 0, "agent finds, " + m: 0, "gained, find_lethal sure": 0,
             "gained beyond find_lethal (it found none within 20000 nodes)": 0, "lost": 0}
        unreal = 0
        for r in rs:
            k = r["key"].split("|", 1)[1]
            ref = lm.get(k) if deck == "ramp" else pir.get(k)
            sure = bool(ref and ref.get("full"))
            old = (ref.get("agent") is not None) if sure else r["plain"][0]
            search = (sure and ref.get("agent") == "search") or bool(r.get("screen"))
            new = r[m][0] or search
            c["agent finds, plain"] += old
            c["agent finds, " + m] += new
            if new and not old:
                c["gained, find_lethal sure" if sure else "gained beyond find_lethal (it found none within 20000 nodes)"] += 1
                if deck == "ramp" and sure:
                    g, at = (int(x[1:]) if x[0] == "g" else int(x[2:]) for x in k.split("|"))
                    unreal += not m1[(g, at)]["realized"]
            c["lost"] += old and not new
        if deck == "ramp":
            c["of the 27 unrealized"] = unreal
        print(json.dumps({"deck": deck, "mode": m, **c}))
