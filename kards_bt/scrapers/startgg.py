"""Scrape KARDS tournaments hosted on start.gg (KARDS Open VIII-XIV, 2021-2022).

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

TOURNAMENTS_Q = """
query($p: Int) {
  tournaments(query: {perPage: 50, page: $p, sortBy: "startAt asc", filter: {videogameIds: [%d]}}) {
    nodes { id name slug startAt endAt events { id name slug startAt numEntrants videogame { id } } }
  }
}""" % KARDS_VIDEOGAME_ID

SETS_Q = """
query($id: ID!, $p: Int) {
  event(id: $id) {
    sets(page: $p, perPage: 40, sortType: STANDARD) {
      pageInfo { totalPages }
      nodes {
        id round fullRoundText completedAt startedAt winnerId displayScore state
        phaseGroup { displayIdentifier phase { name bracketType } }
        slots {
          entrant { id name participants { gamerTag player { id gamerTag } user { slug } } }
          standing { stats { score { value } } }
        }
      }
    }
  }
}"""


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
            return tours
        tours += nodes
        page += 1


def event_sets(event_id):
    sets, page = [], 1
    while True:
        d = gql(SETS_Q, {"id": event_id, "p": page})["event"]["sets"]
        sets += d["nodes"]
        if page >= (d["pageInfo"]["totalPages"] or 0):
            return sets
        page += 1
        time.sleep(0.5)


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
            events.append({"event": e, "sets": event_sets(e["id"])})
        n = sum(len(e["sets"]) for e in events)
        print(f"{t['name']}: {len(events)} events, {n} sets", file=sys.stderr)
        with open(path, "w") as f:
            json.dump({"tournament": {k: t[k] for k in ("id", "name", "slug", "startAt", "endAt")}, "events": events}, f)


if __name__ == "__main__":
    main()
