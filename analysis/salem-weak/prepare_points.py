"""The weak-reference audit's points (architecture thread 07:09Z): every decision of both seats in the 10 games of
db-export-2026-10-08b (seat 0 Salem playing nemesis-t or pirate-t, seat 1 the bot playing elf-t), and a control
of bot-vs-bot decisions in the same pairings from the league rerun after elf-t's redraw went back to D.

    python3 <this> --games weak_games.json --league league-after-D-20261008-elf.jsonl.gz --out points.json

The Salem / bot points are taken exactly as shallow_deep.py's third design takes them (candidates(), every
decision with more than one legal move); the control: 100 decisions per pairing (elf-t/nemesis-t,
elf-t/pirate-t), either seat, 34 / 33 / 33 by the deciding side's stage, at most one per stage of a game, games
in an order shuffled by a fixed seed. Control ids start at 10000 (the audit's seeds come from the id).
Condition: the opponent's 40-card list is known (order and hand not).
"""
import gzip
import json
import random
import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/ramp-benchmark")
import shallow_deep as sd  # noqa: E402


def main():
    arg = lambda k: sys.argv[sys.argv.index(k) + 1]
    data = json.load(open(arg("--games"), encoding="utf-8"))
    recs, meta = data["records"], {m["game"]: m for m in data["meta"]}
    points = []
    for who, side in (("Salem", 0), ("bot", 1)):
        for gid in sorted(recs):
            for i, s, own in sd.candidates(recs[gid], {side}):
                m = meta[gid]
                points.append({"id": len(points), "who": who, "source": "weak-2026-10-08b", "ref": {"game": gid},
                               "at": i, "side": s, "own_turn": own, "stage": sd.stage_of(own), "record": recs[gid],
                               "salem_deck": m["salem_deck"], "bot_level": m["bot_level"], "started": m["started"]})
    league = {}
    for line in gzip.open(arg("--league"), "rt", encoding="utf-8"):
        g = json.loads(line)
        if g["pair"] in ("elf-t/nemesis-t", "elf-t/pirate-t"):
            rec = g["record"]
            rec["g"] = 2 * g["k"] + g["seat_a"]
            league.setdefault(g["pair"], []).append(rec)
    quota = {"前期 1–4": 34, "中期 5–7": 33, "后期 8+": 33}
    cid = 10000
    for pair in ("elf-t/nemesis-t", "elf-t/pirate-t"):
        rng = random.Random(sd.SAMPLE_SEED + 7)
        games = sorted(league[pair], key=lambda r: r["g"])
        rng.shuffle(games)
        need = dict(quota)
        for rec in games:
            if not any(need.values()):
                break
            by = {}
            for i, s, own in sd.candidates(rec, {0, 1}):
                by.setdefault(sd.stage_of(own), []).append((i, s, own))
            for name in quota:
                if need[name] and by.get(name):
                    i, s, own = rng.choice(by[name])
                    points.append({"id": cid, "who": "ctrl", "source": f"league-after-D {pair}",
                                   "ref": {"pair": pair, "g": rec["g"], "seed": rec["seed"]}, "at": i, "side": s,
                                   "own_turn": own, "stage": name, "record": rec,
                                   "deck": rec["names"][s] if rec.get("names") else None})
                    cid += 1
                    need[name] -= 1
    json.dump(points, open(arg("--out"), "w", encoding="utf-8"))
    n = lambda w: sum(1 for p in points if p["who"] == w)
    print(f"{len(points)} 个点：Salem {n('Salem')}，bot {n('bot')}，对照 {n('ctrl')}")


if __name__ == "__main__":
    main()
