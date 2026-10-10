"""Measurement only, beside lethal_miss.py (whose data is the original Ramp mirror): the same check at every own-turn
start of N pirate-t mirror games played by level-strong (seeds 99600000 + g, off every bank: an extra sample for the
deck the puzzle came from).
usage: lethal_miss_pirate.py N [WORKERS]"""
import json, sys, time
from multiprocessing import Pool
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "analysis" / "speed"))
sys.argv.insert(1, "/nonexistent")          # lethal_miss reads a STEP1_DIR argument it won't use here
import lethal_miss as LM
del sys.argv[1]


def game(g):
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.core.enums import Phase
    from svsim.tools.arena import make_agent
    seed = 99600000 + g
    agents = [make_agent("level-strong", 2 * seed), make_agent("level-strong", 2 * seed + 1)]
    st = new_game(decks.build(decks.PIRATE_T), decks.build(decks.PIRATE_T), seed=seed)
    out, seen = [], set()
    while not st.over:
        mark = (st.turn, st.active)
        if st.phase == Phase.MAIN and mark not in seen:
            seen.add(mark)
            out.append(LM.job(("pirate-t", f"g{g}|turn{st.turn}", st.clone())))
        apply(st, agents[st.active].act(st, legal_actions(st)))
    return out


if __name__ == "__main__":
    n = int(sys.argv[1]); workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    rows, t0 = [], time.time()
    with Pool(workers) as pool:
        for part in pool.imap_unordered(game, range(n)):
            rows += part
            for r in part:
                if r["full"]:
                    print(json.dumps(r), flush=True)
    found = [r for r in rows if r["full"]]
    missed = [r for r in found if not r["agent"]]
    print(json.dumps({"summary": "pirate-t mirror", "games": n, "starts": len(rows), "full_finds": len(found),
                      "agent_misses": len(missed), "miss_rate_of_starts": round(len(missed) / max(len(rows), 1), 5),
                      "miss_rate_of_lethals": round(len(missed) / max(len(found), 1), 4),
                      "seconds": round(time.time() - t0)}), flush=True)
