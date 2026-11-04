"""M1 for the analysis line (J30), from lethal_miss.py's rows: for every own-turn start where find_lethal at its
defaults (20000 nodes, 8 samples, seed 0, unscreened) is sure on the real position, whether the record's turn
realized it (the mover won before the turn ended), and two diagnostics: level-strong's lethal check at the start
(lethal_miss.py's "agent": the planner, then 2000 nodes / screen 200 / near 1000:4), and for a turn not realized,
whether find_lethal is still sure at its last decision (the EndTurn) - left standing, or spoiled earlier.
Step 1's self-play records are level-strong's own games; the golden games are mcts:30 (+plan+learned+phased, the
same lethal agent), played again from their seeds past the recorded decisions to finish each turn.
usage: lethal_m1.py STEP1_DIR ROWS.jsonl OUT.jsonl"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
S, ROWS, OUT = sys.argv[1:4]
sys.path.insert(0, f"{S}/ana")
from svsim.core.actions import EndTurn, from_dict
from svsim.core.engine import apply, legal_actions
from svsim.search.lethal import find_lethal


def ends_won(state) -> bool:
    """Whether ending the turn here wins, as find_lethal counts it: the end-of-turn abilities finish the opponent,
    or the opponent must then draw from an empty deck (search.lethal.LethalSearch._end_turn)."""
    from svsim.core.enums import DRAW
    me = state.active
    s = state.clone()
    s.max_turns = s.turn                       # stop before the opponent's turn starts
    apply(s, EndTurn())
    if s.winner == me:
        return True
    return s.winner == DRAW and state.turn < state.max_turns and not s.players[1 - me].deck_view()


def turn_outcome(state, actions):
    """Play the mover's turn from `state` by `actions` (the record's): (realized, the state at its EndTurn when not
    realized, else None)."""
    me = state.active
    for a in actions:
        if state.over or state.active != me:
            break
        if isinstance(a, EndTurn):
            return (True, None) if ends_won(state) else (False, state.clone())
        apply(state, a)
    return state.over and state.winner == me, None


def selfplay(rows):
    import student_data as SD
    games = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}
    for r in rows:
        g, at = (int(x[1:]) if x[0] == "g" else int(x[2:]) for x in r["key"].split("|"))
        rec = games[g]
        st = SD._state_at(rec, at)
        seat, own = st.active, st.players[st.active].turns_taken
        realized, end = turn_outcome(st, [from_dict(a) for a in rec["actions"][at:]])
        yield r, {"source": "6f11111", "game": g, "at": at, "seat": seat, "own_turn": own}, realized, end


def golden(rows):
    from golden_search import GAMES, SPEC
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.tools.arena import make_agent
    from svsim.ui.session import DECKS
    want = {r["key"]: r for r in rows}
    for deck, opponent, seed, limit in GAMES:
        agents = [make_agent(SPEC, 2 * seed), make_agent(SPEC, 2 * seed + 1)]
        st = new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1]), seed=seed)
        n, pending = 0, None
        while not st.over and n < limit + 40:
            key = f"{deck}|{opponent}|{seed}|turn{st.turn}"
            if key in want and pending is None and n < limit:
                pending = (want.pop(key), {"source": "golden", "game": f"{deck}|{opponent}|{seed}", "at": n,
                                           "seat": st.active, "own_turn": st.players[st.active].turns_taken},
                           st.active, st.turn)
            a = agents[st.active].act(st, legal_actions(st))
            if pending is not None and isinstance(a, EndTurn) and st.active == pending[2]:
                won = ends_won(st)
                yield pending[0], pending[1], won, None if won else st.clone()
                pending = None
            apply(st, a)
            n += 1
            if pending is not None and st.over:
                yield pending[0], pending[1], st.winner == pending[2], None
                pending = None
            elif n >= limit and pending is None:
                break


rows = [json.loads(l) for l in open(ROWS) if l.strip()]
sure = [r for r in rows if r.get("full")]
with open(OUT, "w") as fh:
    for gen, src in ((selfplay, "selfplay"), (golden, "golden")):
        for r, head, realized, end in gen([x for x in sure if x["src"] == src]):
            out = {**head, "sure": True, "probability": 1.0, "complete": True, "nodes": r["full_nodes"],
                   "realized": realized, "agent_check": r["agent"], "agent_screened": r.get("screened"),
                   "estimate": r.get("estimate"), "hp": r.get("hp"), "planner_damage": r.get("planner_damage")}
            if not realized and end is not None:
                last = find_lethal(end)
                out["sure_at_last_decision"] = last.sure
            fh.write(json.dumps(out) + "\n")
    unknown = [r for r in rows if not r.get("full") and r.get("complete") is False]
    print(json.dumps({"incomplete_without_sure": len(unknown),
                      "by_source": {s: sum(1 for r in unknown if r["src"] == s) for s in ("selfplay", "golden")}}))
