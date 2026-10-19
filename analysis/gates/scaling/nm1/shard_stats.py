"""Per-shard stats of non-mirror self-play records with ramp-t on one side (NM1 ramp-t vs elf-t, NM2 ramp-t vs nemesis-t): games, distinct g, draws, ramp-t
wins, first-seat wins, how often ramp-t moved first and sat in seat 0, mean actions, searched decisions.

    python shard_stats.py REC.jsonl.gz ...      (writes REC.stats.json beside each; prints one line per shard)
"""
import gzip
import json
import sys


def stats(path):
    n = draws = ramp_wins = first_wins = ramp_first = ramp_seat0 = actions = searched = 0
    gs, opponents = [], {}
    for line in gzip.open(path, "rt", encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        n += 1
        gs.append(r["g"])
        ramp = r["deck_keys"].index("ramp-t")
        other = r["deck_keys"][1 - ramp]
        assert other != "ramp-t" and opponents.setdefault(other, True), r["deck_keys"]
        draws += r["winner"] not in (0, 1)
        ramp_wins += r["winner"] == ramp
        first_wins += r["winner"] == r["first"]
        ramp_first += r["first"] == ramp
        ramp_seat0 += ramp == 0
        actions += len(r["actions"])
        searched += sum(t is not None for t in r.get("search") or [])
    assert len(opponents) == 1, opponents
    return {"opponent": next(iter(opponents)), "games": n, "g_unique": len(set(gs)), "g_range": [min(gs), max(gs)], "draws": draws,
            "ramp_t_wins": ramp_wins, "first_seat_wins": first_wins, "ramp_t_first": ramp_first,
            "ramp_t_seat0": ramp_seat0, "actions": actions, "searched_decisions": searched}


if __name__ == "__main__":
    for p in sys.argv[1:]:
        s = stats(p)
        with open(p[:-len(".jsonl.gz")] + ".stats.json", "w") as fh:
            fh.write(json.dumps(s) + "\n")
        print(p.rsplit("/", 1)[-1], json.dumps(s))
