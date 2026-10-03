"""Bundle the rating timeline into a self-contained HTML page (site/index.html)."""
import csv
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SITE = os.path.join(HERE, "site")


def main():
    rows = list(csv.DictReader(open(os.path.join(DATA, "ratings_timeline.csv"))))
    players = {r["player_id"]: r for r in csv.DictReader(open(os.path.join(DATA, "players.csv")))}

    snaps = []
    for r in rows:
        key = (r["date"], r["event"])
        if not snaps or snaps[-1] != key:
            if key not in snaps:
                snaps.append(key)
    snap_idx = {s: i for i, s in enumerate(snaps)}

    series = defaultdict(list)
    for r in rows:
        series[r["player_id"]].append([
            snap_idx[(r["date"], r["event"])], float(r["elo"]), float(r["se"]), int(r["results"]), r["last_played"],
        ])

    matches = [m for m in csv.DictReader(open(os.path.join(DATA, "matches.csv")))]
    used = [m for m in matches if m["valid"] == "1" and m["category"] in ("open", "open_special")]
    per_event = Counter(m["event"] for m in used)

    payload = {
        "snaps": [{"d": d, "e": e, "n": per_event.get(e, 0)} for d, e in snaps],
        "players": [
            {"id": pid, "n": players[pid]["name"], "a": players[pid]["aliases"], "p": pts}
            for pid, pts in series.items()
        ],
        "stats": {
            "matches": len(used),
            "players": len({p for m in used for p in (m["p1"], m["p2"])}),
            "first": min(m["time"] for m in used)[:10],
            "last": max(m["time"] for m in used)[:10],
        },
    }
    template = open(os.path.join(SITE, "template.html")).read()
    html = template.replace("/*__DATA__*/null", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    with open(os.path.join(SITE, "index.html"), "w") as f:
        f.write(html)
    print(f"site/index.html: {len(html) / 1024:.0f} KB, {len(snaps)} snapshots, {len(series)} players")


if __name__ == "__main__":
    main()
