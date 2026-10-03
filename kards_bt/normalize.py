"""Turn raw Battlefy / start.gg dumps into one match table plus a player identity table.

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

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# category -> events matching these name patterns (checked in order)
CATEGORIES = [
    ("open", re.compile(r"^kards open( #?\d+| [ivxl]+\b|$)", re.I)),
    ("open_special", re.compile(r"^(kards open: singleton|operation: kards)", re.I)),
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


def has_letter(name):
    return bool(re.search(r"[^\W\d_]", norm_name(name)))


def iso(ts):
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return ts[:19] + "Z"


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
                forfeit = bool(s1.get("disqualified") or s2.get("disqualified") or m.get("doubleLoss"))
                winner = 1 if s1.get("winner") else 2 if s2.get("winner") else 0
                rows.append({
                    "source": "battlefy", "event_id": t["_id"], "event": t["name"].strip(),
                    "category": category(t["name"]), "stage": stage.get("name"),
                    "stage_type": (stage.get("bracket") or {}).get("type"), "round": m.get("roundNumber"),
                    "time": when, "p1": n1, "p2": n2, "s1": s1.get("score"), "s2": s2.get("score"),
                    "winner": winner, "valid": int(winner > 0 and not forfeit),
                })
    return rows


def load_startgg(ids):
    rows = []
    for f in sorted(glob.glob(os.path.join(DATA, "raw", "startgg", "*.json"))):
        d = json.load(open(f))
        t = d["tournament"]
        for ev in d["events"]:
            for st in ev["sets"]:
                slots = st.get("slots") or []
                if len(slots) != 2 or any(not s.get("entrant") for s in slots):
                    continue
                when = iso(st.get("completedAt") or st.get("startedAt") or ev["event"].get("startAt") or t["startAt"])
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
                forfeit = st.get("displayScore") in (None, "DQ") or (sc1 is not None and sc1 < 0) or (sc2 is not None and sc2 < 0)
                phase = (st.get("phaseGroup") or {}).get("phase") or {}
                rows.append({
                    "source": "startgg", "event_id": str(ev["event"]["id"]), "event": t["name"].strip(),
                    "category": category(t["name"]), "stage": ev["event"]["name"],
                    "stage_type": (phase.get("bracketType") or "").lower(), "round": st.get("fullRoundText"),
                    "time": when, "p1": n1, "p2": n2, "s1": sc1, "s2": sc2,
                    "winner": winner, "valid": int(winner > 0 and not forfeit),
                })
    return rows


def main():
    ids = Identities()
    rows = load_battlefy(ids) + load_startgg(ids)

    alias_path = os.path.join(DATA, "aliases.csv")
    if os.path.exists(alias_path):
        for r in csv.DictReader(open(alias_path)):
            ids.union("name:" + norm_name(r["alias"]), "name:" + norm_name(r["canonical"]))

    # canonical id = root of the merged component; display name = latest name used
    groups = defaultdict(list)
    for node in list(ids.parent):
        if not node.startswith("name:"):
            groups[ids.find(node)].append(node)
    player_of, players = {}, []
    for root, nodes in groups.items():
        latest = max(nodes, key=lambda n: ids.last_seen.get(n, ""))
        display = ids.latest.get(latest) or ids.names[latest].most_common(1)[0][0]
        aliases = sorted({n for node in nodes for n in ids.names[node]})
        pid = sorted(nodes)[0]
        for n in nodes:
            player_of[n] = pid
        players.append({"player_id": pid, "name": display, "aliases": " / ".join(aliases), "accounts": " ".join(sorted(nodes))})

    for r in rows:
        r["p1"], r["p2"] = player_of[r["p1"]], player_of[r["p2"]]
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
