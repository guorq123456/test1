"""+adaptive on top of +lethal3+discard (the architecture thread 2026-10-10 08:30Z, item 3), measurement only, from
discard_eval.py's rows: +adaptive only accepts more planner lines (a plan whose fixed targets a random outcome breaks
but which, realized again on each sampled outcome, still wins), so a start +lethal3+discard already finds stays found
and only the others are run again: the planner with adaptive=True. Where it finds a line, its verify failed and
verify_steps passed (the mechanism used); the screened search after it is the same as in discard_eval's row.
usage: adaptive_eval.py STEP1_DIR DISCARD_ROWS.jsonl ROWS.jsonl M1.jsonl PIRATE_ROWS.jsonl OUT.jsonl [WORKERS]"""
import json, sys, time
from multiprocessing import Pool
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
S, DROWS, ROWS, M1, PIRATE, OUT = sys.argv[1:7]
WORKERS = int(sys.argv[7]) if len(sys.argv) > 7 else 4
sys.path.insert(0, f"{S}/ana")
KW = dict(tickers=True, fix=True, eot=True, discard=True)
GAMES = None


def run(state):
    from svsim.search import combo
    t = time.perf_counter()
    line, _ = combo.planned_lethal(state, 20000, adaptive=True, **KW)
    return bool(line), round((time.perf_counter() - t) * 1000, 2)


def init():
    global GAMES
    import student_data as SD
    GAMES = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}


def ramp_job(key):
    import student_data as SD
    _, g, at = key.split("|")
    found, ms = run(SD._state_at(GAMES[int(g[1:])], int(at[2:])))
    return {"key": key, "adaptive": found, "ms": ms}


def pirate_game(args):
    g, keys = args
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
            key = f"pirate|g{g}|turn{st.turn}"
            if key in keys:
                found, ms = run(st.clone())
                out.append({"key": key, "adaptive": found, "ms": ms})
        apply(st, agents[st.active].act(st, legal_actions(st)))
    return out


if __name__ == "__main__":
    rows = {json.loads(l)["key"]: json.loads(l) for l in open(DROWS) if l.strip()}
    todo = [k for k, r in rows.items() if not r["new"][0]]
    ramp = [k for k in todo if k.startswith("ramp|")]
    pir = {}
    for k in todo:
        if k.startswith("pirate|"):
            pir.setdefault(int(k.split("|")[1][1:]), set()).add(k)
    with open(OUT, "w") as fh, Pool(WORKERS, initializer=init) as pool:
        for r in pool.imap_unordered(ramp_job, ramp, chunksize=8):
            fh.write(json.dumps(r) + "\n")
        for part in pool.imap_unordered(pirate_game, sorted(pir.items())):
            for r in part:
                fh.write(json.dumps(r) + "\n")
    got = {json.loads(l)["key"]: json.loads(l) for l in open(OUT) if l.strip()}
    lm = {r["key"]: r for r in (json.loads(l) for l in open(ROWS) if l.strip()) if r["src"] == "selfplay"}
    m1 = {(r["game"], r["at"]): r for r in (json.loads(l) for l in open(M1)) if r["source"] == "6f11111"}
    pr = {r["key"]: r for r in (json.loads(l) for l in open(PIRATE) if l.startswith('{"src'))}
    out = {}
    for deck, n_games in (("ramp", 1000), ("pirate", 80)):
        rs = [r for k, r in rows.items() if k.startswith(deck + "|")]
        gained = [k for k, r in got.items() if k.startswith(deck + "|") and r["adaptive"]]

        def sure(k):
            sub = k.split("|", 1)[1]
            return bool((lm if deck == "ramp" else pr).get(sub, {}).get("full"))

        def unrealized(k):
            if deck == "ramp":
                _, g, at = k.split("|")
                return sure(k) and not m1[(int(g[1:]), int(at[2:]))]["realized"]
            return sure(k) and not rows[k].get("realized", True)
        out[deck] = {"starts": len(rs), "found +lethal3+discard": sum(r["new"][0] for r in rs),
                     "found +adaptive": sum(r["new"][0] for r in rs) + len(gained),
                     "gained, find_lethal sure": sum(1 for k in gained if sure(k)),
                     "gained beyond find_lethal": sum(1 for k in gained if not sure(k)),
                     "gained among the unrealized": sum(1 for k in gained if unrealized(k)),
                     "lost": 0, "mechanism used (starts)": len(gained),
                     "per 100 games": round(100 * len(gained) / n_games, 2),
                     "extra ms on the starts run again, mean": round(
                         sum(r["ms"] for k, r in got.items() if k.startswith(deck + "|")) / max(1, len(rs)), 2)}
    print(json.dumps(out, indent=1))
