"""Scrape KARDS tournaments hosted on start.gg (KARDS Open VIII-XIV, World Championship 2021-2022).

Uses the same GraphQL endpoint the start.gg website calls, which serves
public tournament data without an API token.
"""
import json
import os
import subprocess
import sys
import time

GQL = "https://www.start.gg/api/-/gql"
KARDS_VIDEOGAME_ID = 38917
HEADERS = [
    "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
    "-H", "Content-Type: application/json",
    "-H", "client-version: 20",
    "-H", "Origin: https://www.start.gg",
    "-H", "Referer: https://www.start.gg/",
    "-H", "x-web-source: gg-web-gql-client, gg-web-rest",
]
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "data", "raw", "startgg")

# unlisted tournaments: they don't show up under the Kards videogame listing
EXTRA_SLUGS = ["kards-world-championship-2021", "kards-world-championship-2022"]

TOURNAMENT_FIELDS = "id name slug startAt endAt events { id name slug startAt numEntrants videogame { id } phases { phaseGroups(query: {perPage: 64}) { nodes { id } } } }"

TOURNAMENTS_Q = """
query($p: Int) {
  tournaments(query: {perPage: 50, page: $p, sortBy: "startAt asc", filter: {videogameIds: [%d]}}) {
    nodes { %s }
  }
}""" % (KARDS_VIDEOGAME_ID, TOURNAMENT_FIELDS)

TOURNAMENT_BY_SLUG_Q = "query($s: String) { tournament(slug: $s) { %s } }" % TOURNAMENT_FIELDS

SET_FIELDS = """
        id round fullRoundText completedAt startedAt winnerId displayScore state
        phaseGroup { displayIdentifier phase { name bracketType } }
        slots {
          entrant { id name participants { gamerTag player { id gamerTag } user { slug } } }
          standing { stats { score { value } } }
        }"""

SETS_Q = """
query($id: ID!, $p: Int) {
  event(id: $id) {
    sets(page: $p, perPage: 30, sortType: STANDARD) { pageInfo { totalPages } nodes { %s } }
  }
}""" % SET_FIELDS

GROUP_SETS_Q = """
query($id: ID!, $p: Int) {
  phaseGroup(id: $id) {
    sets(page: $p, perPage: 30, sortType: STANDARD) { pageInfo { totalPages } nodes { %s } }
  }
}""" % SET_FIELDS


def gql(query, variables, retries=5):
    body = json.dumps({"query": query, "variables": variables})
    for i in range(retries):
        out = subprocess.run(["curl", "-sS", "--fail", *HEADERS, "-d", body, GQL], capture_output=True, text=True)
        if out.returncode == 0:
            d = json.loads(out.stdout)
            if "errors" not in d:
                return d["data"]
            err = d["errors"]
        else:
            err = out.stderr
        time.sleep(2 ** (i + 1))
    raise RuntimeError(f"GraphQL failed: {err}")


def list_tournaments():
    tours, page = [], 1
    while True:
        nodes = gql(TOURNAMENTS_Q, {"p": page})["tournaments"]["nodes"]
        if not nodes:
            break
        tours += nodes
        page += 1
    for slug in EXTRA_SLUGS:
        t = gql(TOURNAMENT_BY_SLUG_Q, {"s": slug})["tournament"]
        if t and t["id"] not in {x["id"] for x in tours}:
            tours.append(t)
    return tours


def paged_sets(query, key, id_):
    sets, page = [], 1
    while True:
        d = gql(query, {"id": id_, "p": page})[key]["sets"]
        sets += d["nodes"]
        if page >= (d["pageInfo"]["totalPages"] or 0):
            return sets
        page += 1
        time.sleep(0.5)


def event_sets(event):
    sets = paged_sets(SETS_Q, "event", event["id"])
    if sets:
        return sets
    # some events (e.g. WC 2022) return no sets at the event level; walk the bracket groups instead
    for phase in event.get("phases") or []:
        for group in phase["phaseGroups"]["nodes"]:
            sets += paged_sets(GROUP_SETS_Q, "phaseGroup", group["id"])
    return sets


def main():
    os.makedirs(RAW, exist_ok=True)
    for t in list_tournaments():
        path = os.path.join(RAW, f"{t['id']}.json")
        if os.path.exists(path):
            continue
        events = []
        for e in t["events"]:
            if (e.get("videogame") or {}).get("id") != KARDS_VIDEOGAME_ID:
                continue
            sets = event_sets(e)
            e = {k: v for k, v in e.items() if k != "phases"}
            events.append({"event": e, "sets": sets})
        n = sum(len(e["sets"]) for e in events)
        print(f"{t['name']}: {len(events)} events, {n} sets", file=sys.stderr)
        with open(path, "w") as f:
            json.dump({"tournament": {k: t[k] for k in ("id", "name", "slug", "startAt", "endAt")}, "events": events}, f)


if __name__ == "__main__":
    main()
