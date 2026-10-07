"""Goldfish profiles of the four tournament standard decks and the simulator's Game8 builds.

    cd <checkout> && PYTHONPATH=. python3 analysis/universal-bot/goldfish_run.py HASHES GAMES SPEC OUT.json [WALL [wipe]]
HASHES: one standard-deck hash per line, in the order elf-t, nemesis-t, ramp-t, pirate-t
(analysis/tournament-decks-2026-10-07.md)."""
import json
import sys

import numpy as np

from svsim.cards import decks, library  # noqa: F401
from svsim.learn.goldfish import goldfish, profile, profile_names

hashes = [l.strip() for l in open(sys.argv[1]) if l.strip()]
games, spec, out = int(sys.argv[2]), sys.argv[3], sys.argv[4]
wall = int(sys.argv[5]) if len(sys.argv) > 5 else 0
wipe = len(sys.argv) > 6 and sys.argv[6] == "wipe"
named = dict(zip(["elf-t", "nemesis-t", "ramp-t", "pirate-t"], [decks.from_hash(h) for h in hashes]))
named.update({"ramp(G8)": decks.build(decks.RAMP_DRAGON), "pirate(G8)": decks.build(decks.PIRATE_SWORD),
              "combo(G8)": decks.build(decks.COMBO_FOREST)})
res = {}
for name, deck in named.items():
    recs = goldfish(deck, games, spec, seed=1, workers=4, wall=wall, wipe=wipe)
    p = profile(recs)
    res[name] = {"profile": dict(zip(profile_names(), map(float, p))),
                 "kills": [r["kill"] for r in recs],
                 "turn_of": {}}
    agg = {}
    for r in recs:
        for cid, ts in r["turn_of"].items():
            agg.setdefault(cid, []).extend(ts)
    res[name]["turn_of"] = {str(c): [len(ts) / games, float(np.mean(ts))] for c, ts in agg.items()}
    print(name, {k: round(v, 2) for k, v in res[name]["profile"].items() if k.startswith(("damage", "max_pp", "plays", "burst"))}, flush=True)
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
