"""Bundle the rating timeline into a self-contained HTML page (site/index.html)."""
import csv
import json
import os
import re
from bt import RATED
from placements import MAIN, stage_name
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

    # main-stage record (Top 8 / Top 16 / grand finals / invitationals / knockouts), official events only
    main_rec = defaultdict(lambda: [0, 0])
    for m in csv.DictReader(open(os.path.join(DATA, "matches.csv"))):
        if m["valid"] == "1" and m["category"] in RATED and stage_name(m["event"], m["stage"], m["stage_type"]) in MAIN:
            w, l = (m["p1"], m["p2"]) if m["winner"] == "1" else (m["p2"], m["p1"])
            main_rec[w][0] += 1
            main_rec[l][1] += 1

    # actual - expected wins (residuals.py): [career diff, career z, recent matches, recent diff, recent z]
    resid = {}
    if os.path.exists(os.path.join(DATA, "residuals.csv")):
        for r in csv.DictReader(open(os.path.join(DATA, "residuals.csv"))):
            resid[r["player_id"]] = [float(r["diff"]), float(r["z"]), int(r["recent_n"]), float(r["recent_diff"]), float(r["recent_z"])]

    # career peaks with hindsight (peaks.py): [score, rating, se, date, event, rank then, matches]
    peaks = {}
    if os.path.exists(os.path.join(DATA, "peaks.csv")):
        for r in csv.DictReader(open(os.path.join(DATA, "peaks.csv"))):
            peaks[r["player_id"]] = [round(float(r["peak_score"])), round(float(r["peak_elo"])), round(float(r["peak_se"])),
                                     r["peak_date"], re.sub(r"^Kards ", "KARDS ", r["peak_event"]), int(r["rank_then"]), int(r["results"])]

    matches = [m for m in csv.DictReader(open(os.path.join(DATA, "matches.csv")))]
    used = [m for m in matches if m["valid"] == "1" and m["category"] in RATED]
    per_event = Counter(m["event"] for m in used)

    payload = {
        "snaps": [{"d": d, "e": re.sub(r"^Kards ", "KARDS ", e), "n": per_event.get(e, 0)} for d, e in snaps],
        "players": [
            {"id": pid, "n": players[pid]["name"], "a": players[pid]["aliases"], "p": pts, "m": main_rec.get(pid, [0, 0]),
             **({"r": resid[pid]} if pid in resid else {}), **({"k": peaks[pid]} if pid in peaks else {})}
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
