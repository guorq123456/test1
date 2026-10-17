"""Check self-play shards: g 0..n-1 once, deal seed s*100003+g, agent seeds s*1000+2g+i, one agent string on both
sides, the given deck on both sides, explore 0, no draws; first-player win rate."""
import gzip, json, sys
spec, deck, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
for path in sys.argv[4:]:
    s = int(path.split("rec-")[1].split(".")[0])
    rows = [json.loads(l) for l in gzip.open(path, "rt") if l.strip()]
    gs = sorted(r["g"] for r in rows)
    bad = []
    if gs != list(range(n)):
        bad.append("g")
    first_wins = 0
    for r in rows:
        g = r["g"]
        if r["seed"] != s * 100003 + g: bad.append(f"seed g{g}")
        if r.get("agent_seeds") != [s * 1000 + 2 * g, s * 1000 + 2 * g + 1]: bad.append(f"agent_seeds g{g}")
        if r["ai"] != f"{spec} / {spec}": bad.append(f"ai g{g}")
        if r.get("names") != [deck, deck]: bad.append(f"names g{g}")
        if r.get("explore", 0) != 0: bad.append(f"explore g{g}")
        if r["winner"] not in (0, 1): bad.append(f"draw g{g}")
        first_wins += r["winner"] == r["first"]
    print(path.split("/")[-1], len(rows), "games, problems:", bad[:5] if bad else "none", f"first-player win {100*first_wins/len(rows):.1f}%")
