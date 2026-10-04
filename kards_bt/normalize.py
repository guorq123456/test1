"""Turn raw Battlefy / start.gg / Challonge dumps into one match table plus a player identity table.

Identity: each platform account (Battlefy user, start.gg player) is a node; nodes
that share a normalized name (KARDS in-game name, Battlefy/Discord name, start.gg
gamer tag) are merged with union-find. data/aliases.csv can force extra merges.
"""
import csv
import glob
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

import phantoms
from scrapers.challonge import tournament_id

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# category -> events matching these name patterns (checked in order)
CATEGORIES = [
    ("open", re.compile(r"^kards open( #?\d+| [ivxl]+\b|$)", re.I)),
    ("open_special", re.compile(r"^(kards open: singleton|operation: kards)", re.I)),
    ("community", re.compile(r"pauper|singleton|skirmish|blitz|brawl", re.I)),
    ("official", re.compile(r"world championship|\bocc\b|officer'?s? club|\bexpansion\b|"
                            r"\b(clash|conflict|ultimate)\b|\b(winter|spring|summer|fall) tournament|seasonal", re.I)),
    ("community", re.compile(r".")),
]


def category(name):
    return next(cat for cat, rx in CATEGORIES if rx.search(name.strip()))


def norm_name(name):
    """'EFT | John_Px#3858' -> 'john_px'; 'xyloser#1918 | xyloser' -> 'xyloser'."""
    if not name:
        return ""
    name = name.split("|")[-1] if "|" in name else name
    name = re.sub(r"#\s*\d*\s*$", "", name.strip())
    return re.sub(r"\s+", "", name).lower()


EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


NOTE = re.compile(r"\s*[\(（\[][^\)）\]]*[\)）\]]\s*$")


def name_keys(display):
    """Keys a display name can be referred to by in aliases.csv: as written, and without a trailing '(note)'."""
    return {k for k in (norm_name(display), norm_name(NOTE.sub("", display or ""))) if k}


def has_letter(name):
    return bool(re.search(r"[^\W\d_]", norm_name(name)))


def iso(ts):
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Challonge stamps carry a local offset ("07:55:55.021-05:00"); convert instead of dropping it
    t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Identities:
    def __init__(self):
        self.parent = {}
        self.names = defaultdict(Counter)  # node -> display names seen
        self.last_seen = {}  # node -> time of latest match
        self.latest = {}  # node -> display name at latest match

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)

    def add(self, node, display, link_names, when):
        self.find(node)
        if EMAIL.search(display):  # some people registered under their email; still link on it, never show it
            display = "Player " + node.split(":", 1)[1][-6:]
        self.names[node][display] += 1
        if when and when > self.last_seen.get(node, ""):
            self.last_seen[node] = when
            self.latest[node] = display
        for n in link_names:
            n = norm_name(n)
            if len(n) >= 3 and has_letter(n):
                self.union(node, "name:" + n)


def load_battlefy(ids):
    rows = []
    for f in sorted(glob.glob(os.path.join(DATA, "raw", "battlefy", "*.json"))):
        d = json.load(open(f))
        t = d["tournament"]
        teams = {x["_id"]: x for x in d["teams"]}
        for s in d["stages"]:
            stage = s["stage"]
            for m in s["matches"]:
                top, bot = m.get("top") or {}, m.get("bottom") or {}
                if m.get("isBye") or not top.get("teamID") or not bot.get("teamID"):
                    continue
                when = iso(m.get("completedAt") or m.get("updatedAt") or stage.get("startTime"))
                side = []
                for slot in (top, bot):
                    team = teams.get(slot["teamID"]) or slot.get("team") or {}
                    uid = team.get("userID") or (team.get("captain") or {}).get("userID") or slot["teamID"]
                    # the custom field is the KARDS in-game name, but some people typed a Discord id
                    kards = [cf.get("value") for cf in team.get("customFields") or [] if has_letter(cf.get("value"))]
                    display = kards[0] if kards else team.get("name", "?")
                    node = "bf:" + uid
                    ids.add(node, re.sub(r"#\s*\d*\s*$", "", display).strip(), [team.get("name", "")] + kards, when)
                    side.append((node, slot))
                (n1, s1), (n2, s2) = side
                reason = phantoms.battlefy_verdict(m)
                winner = 1 if s1.get("winner") else 2 if s2.get("winner") else 0
                event = t["name"].strip()
                wc = re.search(r"world championship (20\d\d)", event, re.I)
                if wc:  # e.g. the 2024 128-player swiss joins the Challonge top 16 as one event
                    event = f"KARDS World Championship {wc.group(1)}"
                rows.append({
                    "source": "battlefy", "event_id": t["_id"], "event": event,
                    "category": category(t["name"]), "stage": stage.get("name"),
                    "stage_type": (stage.get("bracket") or {}).get("type"), "round": m.get("roundNumber"),
                    "time": when, "p1": n1, "p2": n2, "s1": s1.get("score"), "s2": s2.get("score"),
                    "winner": winner, "valid": int(winner > 0 and reason in (None, "real")),
                    "match_id": m["_id"], "note": reason or "",
                })
    return rows


def load_startgg(ids):
    rows = []
    for f in sorted(glob.glob(os.path.join(DATA, "raw", "startgg", "*.json"))):
        d = json.load(open(f))
        t = d["tournament"]
        for ev in d["events"]:
            verdicts = phantoms.startgg_verdicts(ev["sets"])
            for st in ev["sets"]:
                slots = st.get("slots") or []
                if len(slots) != 2 or any(not s.get("entrant") for s in slots):
                    continue
                when = iso(st.get("completedAt") or st.get("startedAt") or ev["event"].get("startAt") or t["startAt"])
                phase = (st.get("phaseGroup") or {}).get("phase") or {}
                side = []
                for s in slots:
                    e = s["entrant"]
                    p = (e.get("participants") or [{}])[0]
                    pid = (p.get("player") or {}).get("id") or e["id"]
                    display = p.get("gamerTag") or e["name"]
                    node = f"sgg:{pid}"
                    ids.add(node, re.sub(r"#\s*\d*\s*$", "", display.split("|")[-1]).strip(), [e["name"], display], when)
                    score = (((s.get("standing") or {}).get("stats") or {}).get("score") or {}).get("value")
                    side.append((node, e["id"], score))
                (n1, e1, sc1), (n2, e2, sc2) = side
                winner = 1 if st.get("winnerId") == e1 else 2 if st.get("winnerId") == e2 else 0
                reason = verdicts.get(st["id"])
                rows.append({
                    "source": "startgg", "event_id": str(ev["event"]["id"]), "event": t["name"].strip(),
                    "category": category(t["name"]),
                    # WC events have a single event named like the tournament; the phase tells the stage apart
                    "stage": ev["event"]["name"] if ev["event"]["name"] != t["name"] else phase.get("name"),
                    "stage_type": (phase.get("bracketType") or "").lower(), "round": st.get("fullRoundText"),
                    "time": when, "p1": n1, "p2": n2, "s1": sc1, "s2": sc2,
                    "winner": winner, "valid": int(winner > 0 and not reason),
                    "match_id": str(st["id"]), "note": reason or "",
                })
    return rows


# placeholder entrants organisers add to fill a bracket ("BYE", "BYE2", "BYE D", "CPU - Easy")
PLACEHOLDER = re.compile(r"^(bye(\d+| [a-z])?|cpu\b.*)$", re.I)
# organiser tags: "钟离梓 (DQ)", "老虎不发猫 (CN)", "[CN]lgyouch", "(cn)symbol"
TAG = re.compile(r"\s*[\(\[](dq|cn)[\)\]]\s*", re.I)


def load_manual(ids):
    """data/manual_matches.csv: results published only in official news (e.g. the 2021-2023 World Championship
    grand finals played at LAN), keyed to existing platform accounts so they join the right player."""
    path = os.path.join(DATA, "manual_matches.csv")
    if not os.path.exists(path):
        return []
    rows = []
    for m in csv.DictReader(open(path)):
        for side in ("1", "2"):
            if m[f"p{side}_account"] not in ids.parent:
                raise ValueError(f"manual match names an unknown account: {m}")
            ids.add(m[f"p{side}_account"], m[f"p{side}"], [], m["time"])
        s1, s2 = int(m["s1"]), int(m["s2"])
        rows.append({
            "source": "manual", "event_id": "", "event": m["event"], "category": category(m["event"]),
            "stage": m["stage"], "stage_type": m["stage_type"], "round": m["round"], "time": m["time"],
            "p1": m["p1_account"], "p2": m["p2_account"], "s1": s1, "s2": s2,
            "winner": 1 if s1 > s2 else 2, "valid": 1, "match_id": "", "note": "manual: " + m["source"],
        })
    return rows


def series_score(scores_csv):
    """Challonge 'scores_csv' is '2-1' for a series score or '1-0,0-1,1-0' per game."""
    s1 = s2 = 0
    for part in (scores_csv or "").split(","):
        m = re.match(r"^\s*(-?\d+)-(-?\d+)\s*$", part)
        if not m:
            return None, None
        a, b = int(m.group(1)), int(m.group(2))
        if "," in scores_csv:
            s1, s2 = s1 + (a > b), s2 + (b > a)
        else:
            s1, s2 = a, b
    return s1, s2


MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]
ROMAN = {"": "I", "i": "I", "ii": "II", "iii": "III"}


def challonge_event(title, started_at):
    """Group Challonge brackets into events: 'November OCC - Qualifier A' + 'November OCC Top 8' -> 'OCC 2022-11'.

    OCC titles before 2024 carry no year, so the year comes from the bracket's start date.
    Returns (event, stage).
    """
    low = title.lower()
    m = re.search(r"\b(top|final) (\d+)", low)
    if m:
        stage = f"Top {m.group(2)}"
    elif "qualifier" in low:
        q = re.search(r"qualifier(?: - bracket)?\s*([ab])\b", low)
        stage = "Qualifier" + (f" {q.group(1).upper()}" if q else "") + (" (redemption)" if "redemption" in low else "")
    elif "knockout" in low:
        stage = "Knockout"
    else:
        stage = "Main"

    start = datetime.strptime(started_at[:10], "%Y-%m-%d") if started_at else None
    year = re.search(r"\b(20\d\d)\b", title)
    if "ultimate" in low:
        return "OCC Ultimate " + ROMAN[re.search(r"ultimate\s*(i*)\b", low).group(1)], stage
    if re.search(r"\bocc\b", low):
        month = next(i for i, name in enumerate(MONTHS, 1) if name in low)
        if year:
            y = int(year.group(1))
        else:
            y = start.year
            if month == 12 and start.month == 1:
                y -= 1
            elif month == 1 and start.month == 12:
                y += 1
        return f"OCC {y}-{month:02d}", stage
    m = re.search(r"world championship (20\d\d)", low)
    if m:
        return f"KARDS World Championship {m.group(1)}", stage
    m = re.search(r"kards open ([ivxl]+)\b", low)
    if m:
        return f"Kards Open {m.group(1).upper()}", stage
    m = re.match(r"(.+?) expansion\b", title, re.I)
    if m:
        return f"{m.group(1).strip()} Expansion Tournament", stage
    m = re.search(r"\b(winter|spring|summer|fall) tournament (?:20)?(\d\d)\b", low)
    if m:
        return f"KARDS {m.group(1).title()} Tournament 20{m.group(2)}", stage
    m = re.match(r"(pauper\s*[ivx]*)", low)
    if m:
        return m.group(1).strip().title().replace("Ii", "II"), stage
    return title.strip(), stage


def load_challonge(ids):
    # the current event list wins over the copy saved with each download, so edits to it apply
    listed = {}
    events_csv = os.path.join(DATA, "challonge_events.csv")
    if os.path.exists(events_csv):
        listed = {tournament_id(r["url"]): r for r in csv.DictReader(open(events_csv)) if r.get("url")}
    rows = []
    for f in sorted(glob.glob(os.path.join(DATA, "raw", "challonge", "*.json"))):
        d = json.load(open(f))
        t = d["tournament"]
        meta = listed.get(os.path.basename(f)[:-len(".json")], d["kards_meta"])
        # the event list may carry only URLs; fall back to Challonge's own tournament name
        auto_event, auto_stage = challonge_event(t["name"], t.get("started_at") or t.get("start_at") or t.get("created_at"))
        event = (meta.get("event") or auto_event).strip()
        stage = meta.get("stage") or auto_stage
        cat = meta.get("category") or category(t["name"])
        # group-stage matches reference group_player_ids instead of participant ids
        part = {}
        for p in (x["participant"] for x in t.get("participants", [])):
            for pid in [p["id"]] + list(p.get("group_player_ids") or []):
                part[pid] = p
        verdicts = phantoms.challonge_verdicts(t)
        for m in (x["match"] for x in t.get("matches", [])):
            if m.get("state") != "complete" or not m.get("player1_id") or not m.get("player2_id"):
                continue
            when = iso(m.get("completed_at") or m.get("started_at") or t.get("started_at"))
            nodes, placeholder = [], False
            for pid in (m["player1_id"], m["player2_id"]):
                p = part.get(pid, {})
                display = TAG.sub("", p.get("display_name") or p.get("name") or str(pid)).strip()
                if PLACEHOLDER.match(display):
                    # one shared node, never name-linked, so a bye can't merge with a real player
                    placeholder, node = True, "ch:BYE"
                    ids.add(node, "BYE", [], when)
                else:
                    node = "ch:" + (p.get("challonge_username") or norm_name(display) or str(pid))
                    # "老虎不发猫#2880 (Tiger)", "Jking7 (CA)", "Shiva's (dropped)": link on the name outside
                    # the brackets only; the bracketed nickname is too loose to merge on
                    outer = re.sub(r"\s*\([^)]*\)\s*$", "", re.sub(r"#\d+", "", display)).strip()
                    ids.add(node, re.sub(r"\s*#\d+", "", display).strip(), [display, outer], when)
                nodes.append(node)
            s1, s2 = series_score(m.get("scores_csv"))
            winner = 1 if m.get("winner_id") == m["player1_id"] else 2 if m.get("winner_id") == m["player2_id"] else 0
            # byes, forfeits, 0-0 walkovers and organiser-entered no-shows: see phantoms.py
            reason = verdicts.get(m["id"]) or ("placeholder" if placeholder else None)
            rows.append({
                "source": "challonge", "event_id": str(t["id"]), "event": event,
                "category": cat, "stage": stage,
                "stage_type": "group" if m.get("group_id") else t.get("tournament_type"), "round": m.get("round"),
                "time": when, "p1": nodes[0], "p2": nodes[1], "s1": s1, "s2": s2,
                "winner": winner, "valid": int(winner > 0 and not reason),
                "match_id": str(m["id"]), "note": reason or "",
            })
    return rows


def apply_overrides(rows, players):
    """data/overrides.csv (event,player,actual,note): within one event, credit a player's results to
    whoever really played them (e.g. someone else piloting the account). Unknown names fail loudly."""
    path = os.path.join(DATA, "overrides.csv")
    if not os.path.exists(path):
        return
    pid_by_name = {}
    for p in players:
        for name in p["aliases"].split(" / ") + [p["name"]]:
            pid_by_name.setdefault(norm_name(name), p["player_id"])
    events = {r["event"] for r in rows}
    for o in csv.DictReader(open(path)):
        src, dst = pid_by_name.get(norm_name(o["player"])), pid_by_name.get(norm_name(o["actual"]))
        if not src or not dst or o["event"] not in events:
            raise ValueError(f"override does not match the data: {o}")
        for r in rows:
            if r["event"] == o["event"]:
                r["p1"] = dst if r["p1"] == src else r["p1"]
                r["p2"] = dst if r["p2"] == src else r["p2"]


def main():
    ids = Identities()
    rows = load_battlefy(ids) + load_startgg(ids) + load_challonge(ids)
    rows += load_manual(ids)

    alias_path = os.path.join(DATA, "aliases.csv")
    canonical_names = []
    if os.path.exists(alias_path):
        accounts_by_name = defaultdict(set)
        for node, names in ids.names.items():
            for display in names:
                for key in name_keys(display):
                    accounts_by_name[key].add(node)
        for r in csv.DictReader(open(alias_path)):
            canonical_names.append(r["canonical"])
            ids.union("name:" + norm_name(r["alias"]), "name:" + norm_name(r["canonical"]))
            # names too short to link automatically (two-character names) are merged through the accounts that used them
            nodes = sorted(accounts_by_name[norm_name(r["alias"])] | accounts_by_name[norm_name(r["canonical"])])
            for a, b in zip(nodes, nodes[1:]):
                ids.union(a, b)

    # canonical id = root of the merged component; display name = latest name used
    groups = defaultdict(list)
    for node in list(ids.parent):
        if not node.startswith("name:"):
            groups[ids.find(node)].append(node)
    player_of, players = {}, []
    for root, nodes in groups.items():
        latest = max(nodes, key=lambda n: ids.last_seen.get(n, ""))
        display = ids.latest.get(latest) or ids.names[latest].most_common(1)[0][0]
        # a manually merged player is shown under the canonical name given in aliases.csv
        known = {n for node in nodes for d in ids.names[node] for n in name_keys(d)}
        display = next((c for c in canonical_names if norm_name(c) in known), display)
        aliases = sorted({n for node in nodes for n in ids.names[node]})
        # prefer Battlefy / start.gg accounts so ids stay stable when Challonge accounts join
        pid = min(nodes, key=lambda n: (n.startswith("ch:"), n))
        for n in nodes:
            player_of[n] = pid
        players.append({"player_id": pid, "name": display, "aliases": " / ".join(aliases), "accounts": " ".join(sorted(nodes))})

    for r in rows:
        r["p1"], r["p2"] = player_of[r["p1"]], player_of[r["p2"]]
    apply_overrides(rows, players)
    for r in rows:
        if r["p1"] == r["p2"]:
            r["valid"] = 0
    rows.sort(key=lambda r: (r["time"] or "", r["event"]))

    with open(os.path.join(DATA, "matches.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(DATA, "players.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(players[0]))
        w.writeheader()
        w.writerows(sorted(players, key=lambda p: p["name"].lower()))

    valid = [r for r in rows if r["valid"]]
    print(f"{len(rows)} matches ({len(valid)} valid), {len(players)} players")
    print(Counter((r["category"]) for r in valid))


if __name__ == "__main__":
    main()
