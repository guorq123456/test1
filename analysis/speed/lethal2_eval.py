"""The packaged lethal change (+lethal2: the planner's countdown amulets, near-lethal 2000 within 4, 3000 unscreened)
against level-strong's lethal check, measurement only.
- pirate: the 80 pirate-t mirror games of lethal_miss_pirate.py replayed (level-strong, seeds 99600000 + g: the same
  games), at every own-turn start both checks run on the real position and timed, find_lethal's verdict taken from
  that script's rows, and whether the mover won before the turn ended (realized);
- ramp: 6f11111's rows (lethal_miss.py) through the budget model of lethal_policies.py, after checking that no start
  there has a ticker on the mover's field (then the planner's change is idle and the budget is all that differs).
usage: lethal2_eval.py STEP1_DIR ROWS.jsonl M1.jsonl PIRATE_ROWS.jsonl [WORKERS]"""
import json, math, statistics, sys, time
from multiprocessing import Pool
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
S, ROWS, M1, PIRATE = sys.argv[1:5]
WORKERS = int(sys.argv[5]) if len(sys.argv) > 5 else 4
sys.path.insert(0, f"{S}/ana")


def check(state, tickers: bool, near, max_nodes) -> tuple:
    """LethalAgent's check at a turn start (+plan): (found, how, ms)."""
    from svsim.search import combo
    from svsim.search.lethal import LethalSearch
    t = time.perf_counter()
    hp = state.players[1 - state.active].leader_hp
    p = combo.plan(state, 20000, tickers=tickers)
    if p.damage >= hp and p.steps:
        line = combo.realize(state, p.steps, face_first=p.tickers)
        if line and combo.verify(state, line):
            return True, "planner", (time.perf_counter() - t) * 1000
    r = LethalSearch(max_nodes=max_nodes, screen=200, near=near, seed=0).solve(state.clone())
    return r.sure, ("search" if r.sure else None), (time.perf_counter() - t) * 1000


def pirate_game(g):
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.core.enums import Phase
    from svsim.tools.arena import make_agent
    seed = 99600000 + g
    agents = [make_agent("level-strong", 2 * seed), make_agent("level-strong", 2 * seed + 1)]
    st = new_game(decks.build(decks.PIRATE_T), decks.build(decks.PIRATE_T), seed=seed)
    out, seen, current = [], set(), None
    while not st.over:
        mark = (st.turn, st.active)
        if st.phase == Phase.MAIN and mark not in seen:
            seen.add(mark)
            from svsim.search.combo import tickers_of
            now = check(st, False, (1000, 4), 2000)
            new = check(st, True, (2000, 4), 3000)
            current = {"key": f"g{g}|turn{st.turn}", "mover": st.active, "turn": st.turn, "now": now, "new": new,
                       "tickers": len(tickers_of(st)), "realized": False}
            out.append(current)
        apply(st, agents[st.active].act(st, legal_actions(st)))
        if st.over and current is not None and st.turn == current["turn"] and st.winner == current["mover"]:
            current["realized"] = True
    return out


def p90(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(math.ceil(0.9 * len(xs))) - 1)] if xs else 0.0


if __name__ == "__main__":
    # --- pirate: direct
    pirate_rows = {json.loads(l)["key"]: json.loads(l) for l in open(PIRATE) if l.startswith('{"src')}
    with Pool(WORKERS) as pool:
        starts = [s for part in pool.map(pirate_game, range(80)) for s in part]
    sure = [s for s in starts if s["key"] in pirate_rows]
    missed_now = [s for s in sure if not s["now"][0]]
    found_new = [s for s in sure if s["new"][0]]
    added = [s["new"][2] - s["now"][2] for s in starts]
    pirate = {"starts": len(starts), "sure (find_lethal)": len(sure), "missed at start (level-strong)": len(missed_now),
              "not realized in play": sum(1 for s in sure if not s["realized"]),
              "not realized and missed at start": sum(1 for s in sure if not s["realized"] and not s["now"][0]),
              "lethal2 finds": len(found_new), "lethal2 recovers": sum(1 for s in missed_now if s["new"][0]),
              "lethal2 recovers of the unrealized": sum(1 for s in sure if not s["realized"] and s["new"][0] and not s["now"][0]),
              "lethal2 loses": sum(1 for s in sure if s["now"][0] and not s["new"][0]),
              "found by the ticker planner": sum(1 for s in sure if s["new"][1] == "planner" and s["now"][1] != "planner"),
              "starts with tickers": sum(1 for s in starts if s["tickers"]),
              "sure keys matched": f"{len(sure)}/{len(pirate_rows)}",
              "ms per start now: mean / p90": [round(statistics.mean(s["now"][2] for s in starts), 1), round(p90([s["now"][2] for s in starts]), 1)],
              "added ms per start: mean / p90": [round(statistics.mean(added), 1), round(p90(added), 1)]}
    print(json.dumps({"pirate-t mirror (80 games, direct)": pirate}, indent=1), flush=True)
    # --- ramp: the budget model (no tickers in that deck: checked below)
    rows = [json.loads(l) for l in open(ROWS) if l.strip()]
    rows = [r for r in rows if r["src"] == "selfplay"]
    m1 = {(r["game"], r["at"]): r for r in (json.loads(l) for l in open(M1)) if r["source"] == "6f11111"}
    ms_per_node = 1000 * sum(r["s_full"] for r in rows) / sum(r["full_nodes"] for r in rows)

    def budget(r, max_nodes, near):
        est = r["estimate"]
        short = r["hp"] - est if est is not None and not (isinstance(est, float) and math.isinf(est)) else -1
        return max_nodes if short <= 0 else near[0] if short <= near[1] else 200
    added, rec, rec_unreal = [], 0, 0
    for r in rows:
        planner = r.get("full") and r.get("agent") == "planner"
        b0, b1 = budget(r, 2000, (1000, 4)), budget(r, 3000, (2000, 4))
        if not planner:
            added.append((min(b1, r["full_nodes"]) - min(b0, r["full_nodes"])) * ms_per_node)
        if r.get("full") and not r["agent"] and r["full_nodes"] <= b1:
            rec += 1
            g, at = (int(x[1:]) if x[0] == "g" else int(x[2:]) for x in r["key"].split("|"))
            rec_unreal += not m1[(g, at)]["realized"]
    added += [0.0] * sum(1 for r in rows if r.get("full") and r.get("agent") == "planner")
    from svsim.cards import decks
    from svsim.cards.pool import POOL
    from svsim.search.combo import evolve_summons, summons, ticker_profile
    cards = set(decks.build(decks.RAMP_DRAGON))
    reach = set(cards)
    for c in cards:                          # what they summon, on play and on evolving
        got = list(summons(c)) + ([s for sup in (False, True) for s in evolve_summons(c, sup)] if c.is_follower else [])
        reach |= {POOL[cid] for cid, _ in got if cid in POOL}
    ramp_tickers = sorted(c.name for c in reach if ticker_profile(c))
    print(json.dumps({"ramp mirror 6f11111 (budget model)": {
        "starts": len(rows), "sure": sum(1 for r in rows if r.get("full")),
        "missed at start": sum(1 for r in rows if r.get("full") and not r["agent"]),
        "lethal2 recovers": rec, "of the 27 unrealized": rec_unreal,
        "added ms per start: mean / p90": [round(statistics.mean(added), 1), round(p90(added), 1)],
        "ms per node": round(ms_per_node, 3),
        "tickers among the Ramp deck's cards and what they summon": ramp_tickers}}, indent=1))
