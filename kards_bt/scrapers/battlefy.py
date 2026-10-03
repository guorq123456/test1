"""Scrape KARDS tournaments hosted on Battlefy (983 Media's KARDS Open series, 2020-2021).

Battlefy's public read API answers browser-origin requests only, so we send
the same Origin/Referer headers the website does.
"""
import json
import os
import subprocess
import sys
import time

API = "https://dtmwra1jsgyb0.cloudfront.net"
SEARCH = "https://search.battlefy.com"
KARDS_GAME_ID = "5a18a24430e2150013d37c00"
ORG_983_MEDIA = "5d8931d8d5014c471f1cb94d"
HEADERS = [
    "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "-H", "Origin: https://battlefy.com",
    "-H", "Referer: https://battlefy.com/",
]
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "data", "raw", "battlefy")


def get(url, retries=4):
    for i in range(retries):
        out = subprocess.run(["curl", "-sS", "--fail", *HEADERS, url], capture_output=True, text=True)
        if out.returncode == 0:
            return json.loads(out.stdout)
        time.sleep(2 ** (i + 1))
    raise RuntimeError(f"GET failed: {url}: {out.stderr}")


def list_org_tournaments(org_id):
    tours, page = [], 1
    while True:
        d = get(f"{SEARCH}/tournament/organization/{org_id}/past?page={page}&size=50")
        if not d.get("tournaments"):
            return tours
        tours += d["tournaments"]
        page += 1


def scrape_tournament(tid):
    t = get(f"{API}/tournaments/{tid}?extend%5Bstages%5D=true")[0]
    teams = get(f"{API}/tournaments/{tid}/teams")
    stages = []
    for s in t.get("stages", []):
        bracket = s.get("bracket", {})
        rounds = bracket.get("roundsCount") or 0
        matches = []
        if bracket.get("type") == "swiss":
            # the plain /matches endpoint only returns round 1 for swiss stages
            for r in range(1, rounds + 1):
                matches += get(f"{API}/stages/{s['_id']}/rounds/{r}/matches")
        else:
            matches = get(f"{API}/stages/{s['_id']}/matches")
        stages.append({"stage": {k: s.get(k) for k in ("_id", "name", "startTime", "bracket")}, "matches": matches})
    return {
        "tournament": {k: t.get(k) for k in ("_id", "name", "slug", "startTime", "organizationID", "gameID")},
        "teams": teams,
        "stages": stages,
    }


def main():
    os.makedirs(RAW, exist_ok=True)
    tours = [t for t in list_org_tournaments(ORG_983_MEDIA) if t.get("gameID") == KARDS_GAME_ID]
    print(f"{len(tours)} KARDS tournaments in 983 Media org", file=sys.stderr)
    for t in tours:
        path = os.path.join(RAW, f"{t['_id']}.json")
        if os.path.exists(path):
            continue
        data = scrape_tournament(t["_id"])
        n = sum(len(s["matches"]) for s in data["stages"])
        print(f"{t.get('startTime', '')[:10]} {t['name']}: {len(data['stages'])} stages, {n} matches", file=sys.stderr)
        with open(path, "w") as f:
            json.dump(data, f)


if __name__ == "__main__":
    main()
