"""Per-match timeline table straight from the raw dumps (data/match_timeline.csv).

One row per raw match on every platform, with the signals needed to tell a
played result from an admin-entered walkover: bracket type, round, DQ tags and
platform flags, scores, when the match opened / went underway / was completed,
how long that took compared with the other matches of the same round, how
long since each player's previous result in the bracket, and how many results
the admin entered in the same burst. Player names are the raw registration
names; identity merging happens later in normalize.py.
"""
import csv
import glob
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from statistics import median

from normalize import challonge_event

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
DQ_TAG = re.compile(r"\((?:dq|drop(?:ped)?|withdrawn?)\)|\[(?:dq|drop(?:ped)?)\]", re.I)
BURST_SECONDS = 30


def parse_time(v):
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v, timezone.utc)
    return datetime.fromisoformat(v.replace("Z", "+00:00")).astimezone(timezone.utc)


def minutes(a, b):
    return round((b - a).total_seconds() / 60, 2) if a and b else None


def challonge_rows():
    for f in sorted(glob.glob(os.path.join(DATA, "raw", "challonge", "*.json"))):
        t = json.load(open(f))["tournament"]
        event, stage = challonge_event(t["name"], t.get("started_at") or t.get("start_at") or t.get("created_at"))
        part = {}
        for p in (x["participant"] for x in t.get("participants", [])):
            for pid in [p["id"]] + list(p.get("group_player_ids") or []):
                part[pid] = p
        for m in (x["match"] for x in t.get("matches", [])):
            p1, p2 = part.get(m.get("player1_id"), {}), part.get(m.get("player2_id"), {})
            s = re.match(r"^\s*(-?\d+)-(-?\d+)\s*$", m.get("scores_csv") or "")
            yield {
                "source": "challonge", "bracket": os.path.basename(f)[:-5], "bracket_name": t["name"],
                "event": event, "stage": stage,
                "bracket_type": "round robin" if m.get("group_id") else t.get("tournament_type"),
                "group": m.get("group_id") or "", "round": m.get("round"), "match_id": m["id"],
                "p1_key": m.get("player1_id"), "p2_key": m.get("player2_id"),
                "p1": p1.get("display_name") or p1.get("name") or "", "p2": p2.get("display_name") or p2.get("name") or "",
                "p1_flag": "inactive" if p1 and p1.get("active") is False else "",
                "p2_flag": "inactive" if p2 and p2.get("active") is False else "",
                "s1": s.group(1) if s else "", "s2": s.group(2) if s else "", "scores_raw": m.get("scores_csv") or "",
                "winner": 1 if m.get("winner_id") and m["winner_id"] == m.get("player1_id") else
                          2 if m.get("winner_id") and m["winner_id"] == m.get("player2_id") else 0,
                "state": m.get("state"), "forfeited": int(bool(m.get("forfeited"))),
                "opened": parse_time(m.get("started_at")), "underway": parse_time(m.get("underway_at")),
                "completed": parse_time(m.get("completed_at")),
            }


def startgg_rows():
    for f in sorted(glob.glob(os.path.join(DATA, "raw", "startgg", "*.json"))):
        d = json.load(open(f))
        for ev in d["events"]:
            for st in ev["sets"]:
                slots = st.get("slots") or []
                if len(slots) != 2:
                    continue
                ents = [s.get("entrant") or {} for s in slots]
                scores = [(((s.get("standing") or {}).get("stats") or {}).get("score") or {}).get("value") for s in slots]
                phase = (st.get("phaseGroup") or {}).get("phase") or {}
                yield {
                    "source": "startgg", "bracket": f"{d['tournament']['id']}/{ev['event']['id']}",
                    "bracket_name": f"{d['tournament']['name']} / {ev['event']['name']}",
                    "event": d["tournament"]["name"], "stage": phase.get("name") or ev["event"]["name"],
                    "bracket_type": (phase.get("bracketType") or "").lower().replace("_", " "),
                    "group": (st.get("phaseGroup") or {}).get("displayIdentifier") or "", "round": st.get("round"),
                    "match_id": st["id"], "p1_key": ents[0].get("id"), "p2_key": ents[1].get("id"),
                    "p1": ents[0].get("name") or "", "p2": ents[1].get("name") or "",
                    "p1_flag": "dq" if st.get("displayScore") == "DQ" and scores[0] == -1 else "",
                    "p2_flag": "dq" if st.get("displayScore") == "DQ" and scores[1] == -1 else "",
                    "s1": "" if scores[0] is None else scores[0], "s2": "" if scores[1] is None else scores[1],
                    "scores_raw": st.get("displayScore") or "",
                    "winner": 1 if st.get("winnerId") and st["winnerId"] == ents[0].get("id") else
                              2 if st.get("winnerId") and st["winnerId"] == ents[1].get("id") else 0,
                    "state": st.get("state"), "forfeited": int(st.get("displayScore") == "DQ"),
                    "opened": parse_time(st.get("startedAt")), "underway": None,
                    "completed": parse_time(st.get("completedAt")),
                }


def battlefy_rows():
    for f in sorted(glob.glob(os.path.join(DATA, "raw", "battlefy", "*.json"))):
        d = json.load(open(f))
        t = d["tournament"]
        teams = {x["_id"]: x for x in d["teams"]}
        for s in d["stages"]:
            stage = s["stage"]
            for m in s["matches"]:
                top, bot = m.get("top") or {}, m.get("bottom") or {}
                names = [(teams.get(x.get("teamID")) or x.get("team") or {}).get("name", "") for x in (top, bot)]
                ready = [parse_time(x.get("readyAt")) for x in (top, bot)]
                yield {
                    "source": "battlefy", "bracket": f"{t['_id']}/{stage['_id']}", "bracket_name": f"{t['name']} / {stage.get('name')}",
                    "event": t["name"].strip(), "stage": stage.get("name"), "bracket_type": (stage.get("bracket") or {}).get("type"),
                    "group": "", "round": m.get("roundNumber"), "match_id": m["_id"],
                    "p1_key": top.get("teamID"), "p2_key": bot.get("teamID"), "p1": names[0], "p2": names[1],
                    "p1_flag": "disqualified" if top.get("disqualified") else "",
                    "p2_flag": "disqualified" if bot.get("disqualified") else "",
                    "s1": "" if top.get("score") is None else top["score"], "s2": "" if bot.get("score") is None else bot["score"],
                    "scores_raw": "", "winner": 1 if top.get("winner") else 2 if bot.get("winner") else 0,
                    "state": "bye" if m.get("isBye") else "complete" if m.get("isComplete") else "open",
                    "forfeited": int(bool(m.get("doubleLoss"))),
                    "opened": max([r for r in ready if r], default=None), "underway": None,
                    "completed": parse_time(m.get("completedAt") or m.get("updatedAt")),
                }


def main():
    rows = list(challonge_rows()) + list(startgg_rows()) + list(battlefy_rows())
    for r in rows:
        r["dq_tag"] = "/".join(str(i) for i, side in ((1, r["p1"]), (2, r["p2"])) if DQ_TAG.search(side or ""))
        r["duration_min"] = minutes(r["underway"] or r["opened"], r["completed"])

    # typical completion time of the round, and admin bursts (results entered within seconds of each other)
    by_round, by_bracket = defaultdict(list), defaultdict(list)
    for r in rows:
        by_bracket[r["bracket"]].append(r)
        if r["duration_min"] is not None and r["completed"]:
            by_round[(r["bracket"], r["group"], r["round"])].append(r["duration_min"])
    for r in rows:
        durs = by_round.get((r["bracket"], r["group"], r["round"]), [])
        r["round_median_min"] = round(median(durs), 2) if durs else None
        r["round_n"] = len(durs)

    for bracket, ms in by_bracket.items():
        done = sorted((r for r in ms if r["completed"]), key=lambda r: r["completed"])
        times = [r["completed"] for r in done]
        j0 = 0
        for i, r in enumerate(done):
            while (r["completed"] - times[j0]).total_seconds() > BURST_SECONDS:
                j0 += 1
            j1 = i
            while j1 + 1 < len(times) and (times[j1 + 1] - r["completed"]).total_seconds() <= BURST_SECONDS:
                j1 += 1
            r["burst_size"] = j1 - j0 + 1
        # each player's previous result in this bracket, and their record so far
        last, losses = {}, defaultdict(int)
        for r in done:
            for side in (1, 2):
                key = r[f"p{side}_key"]
                prev = last.get(key)
                r[f"p{side}_since_prev_min"] = minutes(prev, r["completed"]) if prev else None
                r[f"p{side}_losses_before"] = losses[key]
            for side in (1, 2):
                last[r[f"p{side}_key"]] = r["completed"]
            if r["winner"] in (1, 2):
                losses[r[f"p{3 - r['winner']}_key"]] += 1

    cols = ["source", "bracket", "bracket_name", "event", "stage", "bracket_type", "group", "round", "match_id",
            "p1", "p2", "p1_flag", "p2_flag", "dq_tag", "s1", "s2", "scores_raw", "winner", "state", "forfeited",
            "opened", "underway", "completed", "duration_min", "round_median_min", "round_n", "burst_size",
            "p1_since_prev_min", "p2_since_prev_min", "p1_losses_before", "p2_losses_before", "p1_key", "p2_key"]
    with open(os.path.join(DATA, "match_timeline.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["source"], r["bracket"], str(r["group"]), str(r["round"]), str(r["completed"]))):
            w.writerow({k: (v.strftime("%Y-%m-%dT%H:%M:%SZ") if isinstance(v, datetime) else v) for k, v in r.items()})
    print(f"data/match_timeline.csv: {len(rows)} matches")


if __name__ == "__main__":
    main()
