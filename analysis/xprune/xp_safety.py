"""+xprune's safety (the architecture thread 2026-10-10 16:57Z): how often the discard pruning (search.xprune) leaves
out the move a stronger player chooses. Condition: the opponent's deck list is known (order and hand not).

1. **The installed mcts:1043** (mcts:1043+plan+learned+phased, the whole agent, without +xprune) plays the turn from
   step 1's 28 starts (bench.py's: the first 30 training starts, the 28 with more than one legal move; seed = index)
   and from every puzzle of the bank (seeds 1-3). The report set.
2. **Salem's own choices**: every decision of his in his trainer games (analysis/salem-games, seat 0). The orders
   other than the first ("when") were looked at on these first: a development set.

At each decision with a discard choice among the legal moves, for each setting (m 2 / 3 x order when / cost / value,
search.xprune.XPrune): how many moves it leaves out, and whether the chosen move is one of them. The rate that
counts: among the decisions where the setting leaves something out and the chosen move is itself a discard choice,
the share whose chosen discard it leaves out.

    python3 xp_safety.py STEP1_DIR OUT.json GAME_DIR [GAME_DIR ...] [--workers 3]
"""
import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SPEC = "mcts:1043+plan+learned+phased"
SETTINGS = [(m, order) for order in ("when", "cost", "value") for m in (2, 3)]


def _check(state, action, xps):
    """None if no legal move is a discard choice; else the decision's row."""
    from svsim.core.engine import _signature, legal_actions
    from svsim.search import xprune as X
    legal = legal_actions(state)
    p = state.players[state.active]
    hand = {c.uid for c in p.hand}
    n_discard = 0
    for a in legal:
        t = [u for u in getattr(a, "targets", ()) or () if u in hand]
        if t and X.discards(state, a, t):
            n_discard += 1
    if not n_discard:
        return None
    t = [u for u in getattr(action, "targets", ()) or () if u in hand]
    is_discard = bool(t) and X.discards(state, action, t)
    names = {c.uid: (c.defn.name, c.cost) for c in p.hand}
    row = {"legal": len(legal), "discard_choices": n_discard, "chosen": repr(action), "chosen_discards": is_discard,
           "discarded": [names[u] for u in t] if is_discard else None,
           "by": names.get(getattr(action, "uid", None)) if is_discard else None,
           "hand": [names[c.uid] for c in p.hand], "pp": p.pp, "max_pp": p.max_pp, "settings": {}}
    for key, xp in xps.items():
        cut = sum(bool(xp(state, a)) for a in legal)
        if cut == len(legal):                   # the search falls back to every move then (ISMCTS._options)
            cut = 0
        r = {"left_out": cut, "chosen_left_out": bool(cut) and bool(xp(state, action))}   # (copies judged the same)
        if is_discard:
            allowed = xp.allowed(state, action, len(t))
            r["kept_to"] = sorted({names[c.uid] for c in p.hand if _signature(c) in allowed})
        row["settings"][key] = r
    return row


def _xps():
    from svsim.search.xprune import XPrune
    return {f"m{m} {order}": XPrune(m, 3, order) for m, order in SETTINGS}


def _play_job(item):
    label, build_kind, arg, seed = item
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.tools.arena import make_agent
    if build_kind == "start":
        sys.path.insert(0, f"{arg[0]}/ana")
        import student_data as SD
        games = {r["g"]: r for r in SD._lines(f"{arg[0]}/selfplay.jsonl")}
        state = SD._state_at(games[arg[1]["game"]], arg[1]["at"])
    else:
        from svsim.tools.puzzles import puzzles
        state = {n: b for n, b, a in puzzles()}[arg](seed)
    me, agent, xps, rows = state.active, make_agent(SPEC, seed), _xps(), []
    while not state.over and state.active == me:
        a = agent.act(state, legal_actions(state))
        row = _check(state, a, xps)
        if row is not None:
            rows.append(row | {"where": label})
        if isinstance(a, EndTurn):
            break
        apply(state, a)
    return label, rows


def _salem_job(path):
    from svsim.core.actions import from_dict
    from svsim.core.enums import Phase
    from svsim.tools.records import steps
    from svsim.ui.session import deck_names
    rec = json.loads(Path(path).read_text(encoding="utf-8"))["record"]
    names = "/".join(deck_names(rec))
    xps, rows = _xps(), []
    for state, action in steps(rec):
        if state.phase == Phase.MULLIGAN or state.active != 0:
            continue
        row = _check(state, from_dict(action) if isinstance(action, dict) else action, xps)
        if row is not None:
            rows.append(row | {"pairing": names, "game": Path(path).stem, "turn": state.turn})
    return rows


def _sum(rows):
    out = {"decisions_with_a_discard_choice": len(rows),
           "chosen_move_discards": sum(r["chosen_discards"] for r in rows)}
    for key in rows[0]["settings"] if rows else ():
        pruned = [r for r in rows if r["settings"][key]["left_out"]]
        disc = [r for r in pruned if r["chosen_discards"]]
        lost = sum(r["settings"][key]["chosen_left_out"] for r in disc)
        moves = [(r["legal"], r["legal"] - r["settings"][key]["left_out"]) for r in pruned]
        out[key] = {"pruned_decisions": len(pruned), "of_them_chosen_discards": len(disc), "chosen_left_out": lost,
                    "share_left_out": round(lost / len(disc), 4) if disc else None,
                    "mean_moves_before_after": [round(sum(a for a, _ in moves) / len(moves), 1),
                                                round(sum(b for _, b in moves) / len(moves), 1)] if moves else None}
    return out


def main():
    from multiprocessing import Pool
    step1, out = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 3
    dirs = [d for d in sys.argv[3:] if not d.startswith("--") and not d.isdigit()]
    sys.path.insert(0, f"{step1}/ana")
    import student_data as SD
    from svsim.core.engine import legal_actions
    from svsim.tools.puzzles import puzzles
    games = {r["g"]: r for r in SD._lines(f"{step1}/selfplay.jsonl")}
    starts = [r for r in SD._lines(f"{step1}/starts.jsonl") if r["split"] == "train"][:30]
    starts = [r for r in starts if len(legal_actions(SD._state_at(games[r["game"]], r["at"]))) > 1]
    jobs = [(f"start {i}", "start", (step1, r), i) for i, r in enumerate(starts)]
    jobs += [(f"{n} seed {s}", "puzzle", n, s) for n, _, _ in puzzles() for s in (1, 2, 3)]
    files = [f for d in dirs for f in sorted(glob.glob(os.path.join(d, "1*.json")))]
    with Pool(workers) as pool:
        played = pool.map(_play_job, jobs, chunksize=1)
        salem = [r for rows in pool.map(_salem_job, files, chunksize=1) for r in rows]
    starts_rows = [r for lab, rows in played if lab.startswith("start") for r in rows]
    bank_rows = [r for lab, rows in played if not lab.startswith("start") for r in rows]
    res = {"spec": SPEC, "starts": len(starts), "bank_runs": len(jobs) - len(starts),
           "mcts:1043 (report)": {"28 starts": _sum(starts_rows), "bank": _sum(bank_rows),
                                  "together": _sum(starts_rows + bank_rows)},
           "salem (development)": {"all": _sum(salem)} | {p: _sum([r for r in salem if r["pairing"] == p])
                                                         for p in sorted({r["pairing"] for r in salem})},
           "rows": {"mcts:1043": starts_rows + bank_rows, "salem": salem}}
    Path(out).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
