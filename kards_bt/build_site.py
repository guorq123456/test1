"""Bundle the rating timeline into a self-contained HTML page (site/index.html)."""
import csv
import json
import os
import re
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

    # where the player finished in each event (placements.py); month-start snapshots have no event
    place = {(r["event"], r["player_id"]): r["label"] for r in csv.DictReader(open(os.path.join(DATA, "placements.csv")))}
    series = defaultdict(list)
    for r in rows:
        pts = series[r["player_id"]]
        played = r["event"] and (not pts or int(r["results"]) > pts[-1][3])
        label = (place.get((r["event"], r["player_id"]), "参赛") if played else 0)
        pts.append([
            snap_idx[(r["date"], r["event"])], round(float(r["elo"])), round(float(r["se"])), int(r["results"]), r["last_played"], label,
        ])

    matches = [m for m in csv.DictReader(open(os.path.join(DATA, "matches.csv")))]
    used = [m for m in matches if m["valid"] == "1" and m["category"] in ("open", "open_special", "official")]
    per_event = Counter(m["event"] for m in used)

    payload = {
        "snaps": [{"d": d, "e": re.sub(r"^Kards ", "KARDS ", e), "n": per_event.get(e, 0)} for d, e in snaps],
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
    print(f"site/index.html: {len(html) / 1024:.0f} KB, {sum(1 for _, e in snaps if e)} events, {len(snaps)} snapshots, {len(series)} players")


if __name__ == "__main__":
    main()
