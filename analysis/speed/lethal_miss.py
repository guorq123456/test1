"""Measurement only: at every own-turn start, does the agent's lethal check (the resource-flow planner, then the
screened search: 2000 nodes, screen 200, near-lethal 1000 within 4) find a sure lethal that find_lethal at its
defaults (20000 nodes, unscreened) finds? Over step 1's self-play (RC 6f11111, every own-turn start) and the golden
games' own-turn starts (tests/golden_search.py). One line of JSON per start in OUT (resumable), then a summary.
usage: lethal_miss.py STEP1_DIR OUT.jsonl [WORKERS]"""
import json, sys, time
from multiprocessing import Pool
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
S = sys.argv[1]
sys.path.insert(0, f"{S}/ana")


def agent_finds(st):
    """What LethalAgent (+plan) does at a turn start: the planner's verified line, else the screened search."""
    from svsim.search import combo
    from svsim.search.lethal import LethalSearch
    hp = st.players[1 - st.active].leader_hp
    p = combo.plan(st, 20000)
    if p.damage >= hp and p.steps:
        line = combo.realize(st, p.steps)
        if line and combo.verify(st, line):
            return "planner", p.damage, None
    r = LethalSearch(max_nodes=2000, screen=200, near=(1000, 4), seed=0).solve(st.clone())
    return ("search" if r.sure else None), p.damage, r


def job(item):
    from svsim.search.lethal import LethalSearch, damage_estimate
    src, key, st = item
    t = time.perf_counter()
    full = LethalSearch(max_nodes=20000, seed=0).solve(st.clone())
    t_full = time.perf_counter() - t
    hp = st.players[1 - st.active].leader_hp
    if not full.sure:
        return {"src": src, "key": key, "full": False, "s_full": round(t_full, 3), "full_nodes": full.nodes,
                "complete": full.complete, "hp": hp, "estimate": damage_estimate(st),
                "deck": st.players[st.active].deck_name, "turn": st.players[st.active].turns_taken}
    t = time.perf_counter()
    how, plan_dmg, r = agent_finds(st)
    t_agent = time.perf_counter() - t
    return {"src": src, "key": key, "full": True, "agent": how, "hp": hp, "estimate": damage_estimate(st),
            "planner_damage": plan_dmg, "full_nodes": full.nodes, "screened": None if r is None else r.screened,
            "agent_nodes": None if r is None else r.nodes, "s_full": round(t_full, 3), "s_agent": round(t_agent, 3),
            "deck": st.players[st.active].deck_name, "turn": st.players[st.active].turns_taken}


def golden_items():
    from golden_search import GAMES, SPEC
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.core.enums import Phase
    from svsim.tools.arena import make_agent
    from svsim.ui.session import DECKS
    for deck, opponent, seed, limit in GAMES:
        agents = [make_agent(SPEC, 2 * seed), make_agent(SPEC, 2 * seed + 1)]
        st = new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1]), seed=seed)
        seen, n = set(), 0
        while not st.over and n < limit:
            mark = (st.turn, st.active)
            if st.phase == Phase.MAIN and mark not in seen:
                seen.add(mark)
                yield ("golden", f"{deck}|{opponent}|{seed}|turn{st.turn}", st.clone())
            apply(st, agents[st.active].act(st, legal_actions(st)))
            n += 1


GAMES = None


def _init():
    global GAMES
    import student_data as SD
    GAMES = {rec["g"]: rec for rec in SD._lines(f"{S}/selfplay.jsonl")}


def selfplay_job(key):
    """A self-play start by its (g, at): the worker rebuilds the position (nothing big crosses processes)."""
    import student_data as SD
    g, at = key
    return job(("selfplay", f"g{g}|at{at}", SD._state_at(GAMES[g], at)))


def selfplay_keys():
    import student_data as SD
    return sorted((rec["g"], at) for rec in SD._lines(f"{S}/selfplay.jsonl") for at, _ in SD.own_turn_starts(rec))


if __name__ == "__main__":
    # every start's result goes to OUT as it comes (resumable: starts already in OUT are skipped); the summary
    # is over OUT
    out = Path(sys.argv[2]); workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    done = {json.loads(l)["key"] for l in out.read_text().splitlines() if l.strip()} if out.exists() else set()
    t0 = time.time()
    with out.open("a") as fh:
        if not any(k.startswith(("ramp|", "ramp-t|", "elf-t|", "nemesis-t|")) for k in done):
            for item in golden_items():
                fh.write(json.dumps(job(item)) + "\n"); fh.flush()
        keys = [k for k in selfplay_keys() if f"g{k[0]}|at{k[1]}" not in done]
        with Pool(workers, initializer=_init) as pool:
            for r in pool.imap_unordered(selfplay_job, keys, chunksize=8):
                fh.write(json.dumps(r) + "\n"); fh.flush()
    rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    for src in ("golden", "selfplay", "all"):
        rs = [r for r in rows if src == "all" or r["src"] == src]
        found = [r for r in rs if r["full"]]
        missed = [r for r in found if not r["agent"]]
        print(json.dumps({"summary": src, "starts": len(rs), "full_finds": len(found),
                          "agent_finds": len(found) - len(missed), "agent_misses": len(missed),
                          "miss_rate_of_starts": round(len(missed) / max(len(rs), 1), 5),
                          "miss_rate_of_lethals": round(len(missed) / max(len(found), 1), 4),
                          "by_planner": sum(1 for r in found if r["agent"] == "planner"),
                          "full_seconds_mean": round(sum(r["s_full"] for r in rs) / max(len(rs), 1), 3)}), flush=True)
    print(json.dumps({"seconds_this_run": round(time.time() - t0)}))
