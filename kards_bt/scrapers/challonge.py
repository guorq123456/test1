"""Fetch official KARDS events (OCC, expansion tournaments, World Championship) from Challonge.

Needs a Challonge API v1 key in the CHALLONGE_API_KEY environment variable
(challonge.com/settings/developer). Events to fetch are listed in
data/challonge_events.csv (only the url column is required); each one costs a
single API request, which matters because free accounts are limited to 500
requests a month.
"""
import csv
import json
import os
import subprocess
import sys
import time
import urllib.parse

API = "https://api.challonge.com/v1"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
RAW = os.path.join(DATA, "raw", "challonge")
EVENTS = os.path.join(DATA, "challonge_events.csv")


def tournament_id(url):
    """'https://challonge.com/iwu8v1m9' -> 'iwu8v1m9'; 'https://kards.challonge.com/occ1' -> 'kards-occ1'."""
    u = urllib.parse.urlparse(url if "//" in url else "https://challonge.com/" + url)
    host = u.hostname or "challonge.com"
    path = [p for p in u.path.split("/") if p and p not in ("en", "zh_CN", "tournaments")]
    slug = path[0] if path else ""
    sub = host.split(".")[0] if host.count(".") >= 2 and not host.startswith("www.") else None
    return f"{sub}-{slug}" if sub else slug


def fetch(tid, key, retries=4):
    url = f"{API}/tournaments/{urllib.parse.quote(tid)}.json"
    params = ["include_participants=1", "include_matches=1", f"api_key={key}"]
    for i in range(retries):
        # pass the key through curl's stdin config so it stays out of process lists
        config = f'url = "{url}"\nget\n' + "".join(f'data = "{p}"\n' for p in params)
        out = subprocess.run(
            ["curl", "-sS", "-w", "\n%{http_code}", "-K", "-"],
            input=config, capture_output=True, text=True,
        )
        body, _, code = out.stdout.rpartition("\n")
        if code == "200":
            return json.loads(body)
        if code in ("401", "403", "404"):
            raise RuntimeError(f"{tid}: HTTP {code} {body[:200]}")
        time.sleep(2 ** (i + 1))
    raise RuntimeError(f"{tid}: gave up after {retries} tries ({out.stderr or code})")


def main():
    key = os.environ.get("CHALLONGE_API_KEY")
    if not key:
        sys.exit("Set CHALLONGE_API_KEY (challonge.com/settings/developer) first.")
    os.makedirs(RAW, exist_ok=True)
    for row in csv.DictReader(open(EVENTS)):
        if not (row.get("url") or "").strip():
            continue
        tid = tournament_id(row["url"])
        path = os.path.join(RAW, f"{tid}.json")
        if os.path.exists(path):
            continue
        try:
            d = fetch(tid, key)
        except RuntimeError as e:
            print(f"skip {row['url']}: {e}", file=sys.stderr)
            continue
        d["kards_meta"] = row
        t = d["tournament"]
        print(f"{t['name']}: {len(t.get('participants', []))} players, {len(t.get('matches', []))} matches", file=sys.stderr)
        with open(path, "w") as f:
            json.dump(d, f)


if __name__ == "__main__":
    main()
