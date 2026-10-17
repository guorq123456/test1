"""Download official card data into data/raw/ (one JSON file per set and language).

    python -m svsim.tools.fetch_cards --lang en

The data is Cygames' content: keep it local and don't commit it (data/raw is
git-ignored). Requests are spaced out; there is no need to fetch more than
once per card set release.
"""
import argparse
import json
from pathlib import Path
import time
import urllib.request

API = "https://shadowverse-wb.com/web/CardSet/cardList?card_set_id={set_id}"
# 10000 = Basic, 10001-10009 = card sets 1-9, 90000 = tokens. Add new sets as they release.
SETS = [10000, *range(10001, 10010), 90000]
LANGS = ("en", "ja", "chs", "cht", "ko")


def fetch(set_id: int, lang: str) -> dict:
    request = urllib.request.Request(API.format(set_id=set_id),
                                     headers={"Lang": lang, "User-Agent": "svsim-card-fetch"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("data_headers", {}).get("result_code") != 1:
        raise RuntimeError(f"set {set_id}: unexpected response {payload.get('data_headers')}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lang", default="en", choices=LANGS)
    parser.add_argument("--sets", type=int, nargs="*", default=SETS)
    parser.add_argument("--out", type=Path, default=Path("data/raw"))
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for i, set_id in enumerate(args.sets):
        if i:
            time.sleep(args.delay)
        payload = fetch(set_id, args.lang)
        path = args.out / f"set_{set_id}_{args.lang}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        details = payload["data"].get("card_details") or {}
        print(f"{path}: {len(details)} card records")


if __name__ == "__main__":
    main()
