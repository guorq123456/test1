"""+discard on top of +lethal3 (the architecture thread 2026-10-10 08:30Z: the planner's hidden mechanics), against
+lethal3's own check, measurement only, run directly at every own-turn start of both samples (no budget model):
- ramp: 6f11111's self-play, every own-turn start (find_lethal's verdict from lethal_miss.py's rows, realized from
  lethal_m1.py's);
- pirate: the 80 pirate-t mirror games of lethal_miss_pirate.py replayed (level-strong, seeds 99600000 + g),
  find_lethal's verdict from that script's rows, realized as the mover winning before the turn ended.
At each start both checks run on the real position as LethalAgent runs them (planner, realize, verify; else the
screened search) and are timed.
Besides the verdicts, per start: whether the hand holds a card with a discarding way to play (exposure), and whether
+discard's verified planner line discards a card (the mechanism used). "now" here is +lethal3, "new" +lethal3+discard.
usage: discard_eval.py STEP1_DIR ROWS.jsonl M1.jsonl PIRATE_ROWS.jsonl OUT.jsonl [WORKERS]"""
import json, math, statistics, sys, time
from multiprocessing import Pool
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
S, ROWS, M1, PIRATE, OUT = sys.argv[1:6]
WORKERS = int(sys.argv[6]) if len(sys.argv) > 6 else 4
sys.path.insert(0, f"{S}/ana")
NOW = dict(tickers=True, fix=True, eot=True, max_nodes=3000, near=(2000, 4))
NEW = dict(tickers=True, fix=True, eot=True, discard=True, max_nodes=3000, near=(2000, 4))
GAMES = None


def _discards(state, line) -> int:
    """Cards the line discards from hand (a play's target that is a card in hand)."""
    from svsim.core.actions import PlayCard
    from svsim.core.engine import apply
    s, me, n = state.clone(), state.active, 0
    for a in line:
        if isinstance(a, PlayCard):
            hand = {c.uid for c in s.players[me].hand}
            n += sum(1 for t in a.targets if t in hand and t != a.uid)
        apply(s, a)
        if s.over:
            break
    return n


def _exposed(state) -> bool:
    from svsim.search import combo
    me = state.players[state.active]
    return any(e.discards for c in me.hand for v in combo.profile_at(c.defn, False, 10, 10, True) for e in v)


def check(state, tickers, fix, eot, max_nodes, near, discard=False) -> list:
    """LethalAgent's check at a turn start (+plan): [found, how, ms, cards the planner's line discards]."""
    from svsim.search import combo
    from svsim.search.lethal import LethalSearch
    t = time.perf_counter()
    line, _ = combo.planned_lethal(state, 20000, tickers=tickers, fix=fix, eot=eot, discard=discard)
    if line:
        return [True, "planner", round((time.perf_counter() - t) * 1000, 2), _discards(state, line)]
    r = LethalSearch(max_nodes=max_nodes, screen=200, near=near, seed=0).solve(state.clone())
    return [r.sure, "search" if r.sure else None, round((time.perf_counter() - t) * 1000, 2), 0]


def both(key, state) -> dict:
    return {"key": key, "now": check(state, **NOW), "new": check(state, **NEW), "exposed": _exposed(state)}


def init():
    global GAMES
    import student_data as SD
    GAMES = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}


def ramp_job(k):
    import student_data as SD
    g, at = k
    return both(f"ramp|g{g}|at{at}", SD._state_at(GAMES[g], at))


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
            current = both(f"pirate|g{g}|turn{st.turn}", st.clone())
            current.update(mover=st.active, turn=st.turn, realized=False)
            out.append(current)
        apply(st, agents[st.active].act(st, legal_actions(st)))
        if st.over and current is not None and st.turn == current["turn"] and st.winner == current["mover"]:
            current["realized"] = True
    return out


def p90(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(math.ceil(0.9 * len(xs))) - 1)] if xs else 0.0


def summary(rs, sure_of, realized_of) -> dict:
    sure = [r for r in rs if sure_of(r)]
    unreal = [r for r in sure if not realized_of(r)]
    now = [r["now"][2] for r in rs]
    new = [r["new"][2] for r in rs]
    added = [b - a for a, b in zip(now, new)]
    return {"starts": len(rs), "sure (find_lethal 20000)": len(sure),
            "found +lethal3": sum(r["now"][0] for r in rs), "found +lethal3+discard": sum(r["new"][0] for r in rs),
            "gained, find_lethal sure": sum(1 for r in sure if r["new"][0] and not r["now"][0]),
            "gained beyond find_lethal": sum(1 for r in rs if not sure_of(r) and r["new"][0] and not r["now"][0]),
            "lost": sum(1 for r in rs if r["now"][0] and not r["new"][0]),
            "sure missed +lethal3": sum(1 for r in sure if not r["now"][0]),
            "sure missed +lethal3+discard": sum(1 for r in sure if not r["new"][0]),
            "same verdict, other line": sum(1 for r in rs if r["now"][0] and r["new"][0] and r["now"][1:2] != r["new"][1:2]),
            "starts with a discarding card in hand": sum(1 for r in rs if r["exposed"]),
            "lethals whose planner line discards": sum(1 for r in rs if r["new"][0] and r["new"][3] > 0),
            "unrealized": len(unreal), "unrealized recovered": sum(1 for r in unreal if r["new"][0] and not r["now"][0]),
            "unrealized missed by both": sum(1 for r in unreal if not r["new"][0] and not r["now"][0]),
            "by the planner +lethal3 / +discard": [sum(r["now"][1] == "planner" for r in rs), sum(r["new"][1] == "planner" for r in rs)],
            "ms per start +lethal3: mean / p90": [round(statistics.mean(now), 1), round(p90(now), 1)],
            "ms per start +discard: mean / p90": [round(statistics.mean(new), 1), round(p90(new), 1)],
            "added ms per start: mean / p90": [round(statistics.mean(added), 1), round(p90(added), 1)]}


if __name__ == "__main__":
    import student_data as SD
    keys = sorted((rec["g"], at) for rec in SD._lines(f"{S}/selfplay.jsonl") for at, _ in SD.own_turn_starts(rec))
    done = set()
    if Path(OUT).exists():
        done = {json.loads(l)["key"] for l in open(OUT) if l.strip()}
    with open(OUT, "a") as fh, Pool(WORKERS, initializer=init) as pool:
        todo = [k for k in keys if f"ramp|g{k[0]}|at{k[1]}" not in done]
        for r in pool.imap_unordered(ramp_job, todo, chunksize=8):
            fh.write(json.dumps(r) + "\n"); fh.flush()
        for part in pool.imap_unordered(pirate_game, [g for g in range(80) if not any(d.startswith(f"pirate|g{g}|") for d in done)]):
            for r in part:
                fh.write(json.dumps(r) + "\n")
            fh.flush()
    rows = [json.loads(l) for l in open(OUT) if l.strip()]
    lm = {r["key"]: r for r in (json.loads(l) for l in open(ROWS) if l.strip()) if r["src"] == "selfplay"}
    m1 = {(r["game"], r["at"]): r for r in (json.loads(l) for l in open(M1)) if r["source"] == "6f11111"}
    pir = {r["key"]: r for r in (json.loads(l) for l in open(PIRATE) if l.startswith('{"src'))}

    def gat(r):
        g, at = r["key"].split("|")[1:]
        return int(g[1:]), int(at[2:])
    ramp = [r for r in rows if r["key"].startswith("ramp|")]
    pirate = [r for r in rows if r["key"].startswith("pirate|")]
    out = {"ramp mirror 6f11111": summary(ramp, lambda r: bool(lm.get(r["key"].split("|", 1)[1], {}).get("full")),
                                         lambda r: m1[gat(r)]["realized"]),
           "pirate-t mirror (80 games)": summary(pirate, lambda r: bool(pir.get(r["key"].split("|", 1)[1], {}).get("full")),
                                                 lambda r: r["realized"])}
    print(json.dumps(out, indent=1))
