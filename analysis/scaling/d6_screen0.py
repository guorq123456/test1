"""D6 follow-up (the architecture thread 2026-10-17): what "+screen=0:1000:4" leaves. On recorded positions (no agent
seeds), each main-phase step: the cost of solve at screen budget 0 and 200 where the estimate is short by more than 4,
and the same result at near / unscreened positions (in the first 40 games). GAMES=N games from the first file."""
import gzip, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from svsim.core.enums import Phase
from svsim.search.lethal import LethalSearch, damage_estimate
from svsim.tools import records as R

files = sys.argv[1:]
a = LethalSearch(max_nodes=2000, screen=200, near=(1000, 4))
b = LethalSearch(max_nodes=2000, screen=0, near=(1000, 4))
t = {"est": 0.0, "s200": 0.0, "s0": 0.0}
n = {"screen": 0, "near": 0, "full": 0, "screen_found_200": 0}
same = {"near": 0, "full": 0}
games = 0
for f in files:
    with gzip.open(f, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line); games += 1
            for s, act in R.steps(rec):
                if s.phase != Phase.MAIN or s.winner is not None:
                    continue
                t0 = time.perf_counter(); short = s.players[1 - s.active].leader_hp - damage_estimate(s); t["est"] += time.perf_counter() - t0
                kind = "full" if short <= 0 else "near" if short <= 4 else "screen"
                n[kind] += 1
                if kind == "screen":
                    t0 = time.perf_counter(); ra = a.solve(s); t["s200"] += time.perf_counter() - t0
                    t0 = time.perf_counter(); rb = b.solve(s); t["s0"] += time.perf_counter() - t0
                    assert rb.nodes == 0 and not rb.sure and rb.screened and b.budget == 0
                    n["screen_found_200"] += ra.sure
                elif games <= 40:            # result equality on near / full positions (a subset, for time)
                    ra, rb = a.solve(s), b.solve(s)
                    assert (ra.probability, repr(ra.line), ra.sure, ra.nodes, ra.complete) == (rb.probability, repr(rb.line), rb.sure, rb.nodes, rb.complete)
                    same[kind] += 1
            if games >= int(__import__("os").environ.get("GAMES", "100")):
                break
    if games >= int(__import__("os").environ.get("GAMES", "100")):
        break
print(json.dumps({"file": files[0].split("/")[-1], "games": games, "positions": n, "identical_checked": same,
                  "us_per_screened_position": {"damage_estimate": round(1e6 * t["est"] / sum(v for k, v in n.items() if k != "screen_found_200"), 1),
                                               "solve_200": round(1e6 * t["s200"] / n["screen"], 1),
                                               "solve_0": round(1e6 * t["s0"] / n["screen"], 1)}}))
