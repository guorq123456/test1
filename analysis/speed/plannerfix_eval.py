"""+plannerfix (and +eot) against the plain planner at every own-turn start, measurement only: 6f11111's self-play
(every start) and the 80 pirate-t mirror games of lethal_miss_pirate.py (replayed). At each start the planner step
of the lethal agent (plan, realize, verify) in three modes: plain, fix, fix+eot (no tickers: the plain planner's
own fixes). A start where a mode's planner loses a lethal the plain one verified is searched with the agent's
screen (2000 / 200 / near 1000:4) to see whether the agent still finds it.
usage: plannerfix_eval.py STEP1_DIR OUT.jsonl [WORKERS]"""
import json, sys, time
from multiprocessing import Pool
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
S, OUT = sys.argv[1:3]
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 4
sys.path.insert(0, f"{S}/ana")
MODES = {"plain": {}, "fix": {"fix": True}, "fix+eot": {"fix": True, "eot": True}}
GAMES = None


def planner(state, **kw):
    from svsim.search import combo
    t = time.perf_counter()
    hp = state.players[1 - state.active].leader_hp
    p = combo.plan(state, 20000, **kw)
    found, line = False, None
    if p.damage >= hp and p.steps:
        line = combo.realize(state, p.steps, face_first=p.face_first)
        found = bool(line) and combo.verify(state, line)
    return found, (repr(line) if found else None), p.damage, (time.perf_counter() - t) * 1000


def measure(key, state):
    from svsim.search.lethal import LethalSearch
    out = {"key": key}
    for name, kw in MODES.items():
        found, line, dmg, ms = planner(state, **kw)
        out[name] = [found, line, dmg, round(ms, 1)]
    if out["plain"][0] and not all(out[m][0] for m in MODES):
        out["screen"] = LethalSearch(max_nodes=2000, screen=200, near=(1000, 4), seed=0).solve(state.clone()).sure
    return out


def init():
    global GAMES
    import student_data as SD
    GAMES = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}


def ramp_job(k):
    import student_data as SD
    g, at = k
    return measure(f"ramp|g{g}|at{at}", SD._state_at(GAMES[g], at))


def pirate_game(g):
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
            out.append(measure(f"pirate|g{g}|turn{st.turn}", st.clone()))
        apply(st, agents[st.active].act(st, legal_actions(st)))
    return out


if __name__ == "__main__":
    import student_data as SD
    keys = sorted((rec["g"], at) for rec in SD._lines(f"{S}/selfplay.jsonl") for at, _ in SD.own_turn_starts(rec))
    with open(OUT, "w") as fh, Pool(WORKERS, initializer=init) as pool:
        for r in pool.imap_unordered(ramp_job, keys, chunksize=16):
            fh.write(json.dumps(r) + "\n")
        for part in pool.imap_unordered(pirate_game, range(80)):
            for r in part:
                fh.write(json.dumps(r) + "\n")
    rows = [json.loads(l) for l in open(OUT)]
    for deck in ("ramp", "pirate"):
        rs = [r for r in rows if r["key"].startswith(deck)]
        summary = {"deck": deck, "starts": len(rs), "plain finds": sum(r["plain"][0] for r in rs)}
        for m in ("fix", "fix+eot"):
            gained = [r for r in rs if r[m][0] and not r["plain"][0]]
            lost = [r for r in rs if r["plain"][0] and not r[m][0]]
            changed = [r for r in rs if r["plain"][0] and r[m][0] and r["plain"][1] != r[m][1]]
            summary[m] = {"finds": sum(r[m][0] for r in rs), "gained": len(gained), "lost at the planner": len(lost),
                          "lost by the agent (the screen doesn't find it either)": sum(1 for r in lost if not r.get("screen")),
                          "same verdict, other line": len(changed),
                          "added ms per start": round(sum(r[m][3] - r["plain"][3] for r in rs) / len(rs), 2)}
        print(json.dumps(summary))
