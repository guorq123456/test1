"""Salem's own turns as preference data (the architecture thread 2026-10-10 16:49Z): for every turn he played in his
trainer games (analysis/salem-games: db-export-2026-10-08, 37 games, and -08b, 10; seat 0 is Salem), the turn's
start, his turn end, and the turn ends the installed strongest search would consider.
Condition: the opponent's deck list is known (order and hand not).

Per Salem turn (main phase; a turn he won during is left out and counted):
- the installed search (ISMCTS of mcts:1043+plan+learned+phased, the search alone) runs once from the turn's start,
  seed 7300000 + 100 x game index + turn;
- every path from the root to an End Turn node gives a turn end; ends that are the same position (lethal.state_key)
  are merged, their End Turn visits summed; the 8 most visited are kept;
- the turn ends in its tree are replayed key by key; where a key isn't legal on the real position (another card
  drawn in the determinization) the line ends its turn there;
- the bot's end: the installed agent (mcts:1043+plan+learned+phased, lethal check included) plays the turn on the
  real position, seed 7400000 + 100 x game index + turn (a turn it wins is kept, as an over position, not scored);
- Salem's end, added when it isn't among them.
Every end is read as version-2 features plus "kclock" for Salem (learn.contrast.features_of), whatever the pairing;
the pairing is recorded (the Ramp mirror is the fit's data, the others are kept apart).

    python3 sp_extract.py OUT.jsonl GAME_DIR [GAME_DIR ...] [--workers 3] [--top 8] [--iters 1043]
"""
import argparse
import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
EXTRAS = ("kclock",)


def _end_of(state, keys):
    """Follow action keys on a copy of `state` to End Turn; where a key isn't legal on the real position (the
    determinization drew another card) the turn ends there (the line cut short, itself a turn end)."""
    from svsim.core.engine import apply, legal_actions
    from svsim.search.evaluate import after_end_of_turn
    from svsim.search.mcts import _locator, action_key
    s = state.clone()
    me = s.active
    for k in keys:
        if s.over or s.active != me:
            return None
        where = _locator(s, me)
        legal = {action_key(s, a, where): a for a in legal_actions(s)}
        if k not in legal or k == ("T",):
            return after_end_of_turn(s)
        apply(s, legal[k])
    return None


def _tree_ends(root):
    """[(keys to End Turn, End Turn visits)] over the whole tree."""
    out, stack = [], [(root, ())]
    while stack:
        node, path = stack.pop()
        for k, child in node.children.items():
            if child.visits <= 0:
                continue
            if k == ("T",):
                out.append((path + (k,), child.visits))
            else:
                stack.append((child, path + (k,)))
    return out


def _bot_end(start, iters, seed):
    """The installed agent (lethal check and search, mcts:ITERS) playing the turn on the real position."""
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.search.evaluate import after_end_of_turn
    from svsim.tools.arena import make_agent
    s, me = start.clone(), start.active
    agent = make_agent(f"mcts:{iters}+plan+learned+phased", seed)
    while not s.over and s.active == me:
        a = agent.act(s, legal_actions(s))
        if isinstance(a, EndTurn):
            return after_end_of_turn(s)
        apply(s, a)
    return s


def job(item):
    gi, path, top, iters = item
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.enums import Phase
    from svsim.learn.contrast import features_of
    from svsim.search.evaluate import after_end_of_turn
    from svsim.search.lethal import state_key
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    from svsim.tools.records import steps
    from svsim.ui.session import deck_names
    rec = json.loads(Path(path).read_text(encoding="utf-8"))["record"]
    names = deck_names(rec)
    out, skipped = [], {"won_during_turn": 0}
    turn_start, salem_actions, t = None, [], 0
    for state, action in steps(rec):
        if state.phase == Phase.MULLIGAN:
            continue
        if state.active == 0 and turn_start is None:
            turn_start, salem_actions = state.clone(), []
        if state.active != 0:
            continue
        salem_actions.append(action)
        if not isinstance(from_dict(action) if isinstance(action, dict) else action, EndTurn):
            continue
        # Salem ends his turn here: his end, then the search from the turn's start
        end = after_end_of_turn(state)
        start = turn_start
        turn_start = None
        if end.over:
            skipped["won_during_turn"] += 1
            continue
        search = _search(make_agent(f"mcts:{iters}+plan+learned+phased", 7300000 + 100 * gi + t))
        search.choose(start.clone())
        root = search.last_root
        cands = {}
        for keys, visits in _tree_ends(root):
            e = _end_of(start, keys)
            if e is None or e.over:
                continue
            k = state_key(e)
            if k in cands:
                cands[k]["visits"] += visits
            else:
                cands[k] = {"visits": visits, "keys": [list(x) if isinstance(x, tuple) else x for x in keys], "end": e}
        ranked = sorted(cands.items(), key=lambda kv: -kv[1]["visits"])[:top]
        rows = []
        for k, c in ranked:
            rows.append({"key": k, "visits": c["visits"], "end": c["end"], "tree": True})
        pv_end = _bot_end(start, iters, 7400000 + 100 * gi + t)
        salem_key = state_key(end)
        pv_key = state_key(pv_end) if pv_end is not None and not pv_end.over else None
        have = {r["key"] for r in rows}
        if pv_key is not None and pv_key not in have:
            rows.append({"key": pv_key, "visits": cands.get(pv_key, {}).get("visits", 0), "end": pv_end, "tree": False})
            have.add(pv_key)
        if salem_key not in have:
            rows.append({"key": salem_key, "visits": cands.get(salem_key, {}).get("visits", 0), "end": end, "tree": False})
        cand_out = []
        for r in rows:
            cand_out.append({"visits": r["visits"], "in_top": r["tree"], "salem": r["key"] == salem_key,
                             "bot": r["key"] == pv_key,
                             "x": [round(v, 6) for v in features_of(r["end"], 0, 2, EXTRAS)]})
        out.append({"game": Path(path).stem, "gi": gi, "turn": t, "global_turn": start.turn,
                    "pairing": list(names), "salem_in_top": salem_key in {r["key"] for r in rows if r["tree"]},
                    "bot_is_salem": pv_key == salem_key, "bot_won": bool(pv_end is not None and pv_end.over),
                    "candidates": cand_out})
        t += 1
    return out, skipped, Path(path).stem


def main():
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--iters", type=int, default=1043)
    args = ap.parse_args()
    files = [f for d in args.dirs for f in sorted(glob.glob(os.path.join(d, "1*.json")))]
    jobs = [(gi, f, args.top, args.iters) for gi, f in enumerate(files)]
    total, skipped = 0, 0
    with Pool(args.workers) as pool, open(args.out, "w", encoding="utf-8") as fh:
        for rows, sk, game in pool.imap_unordered(job, jobs):
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            total += len(rows)
            skipped += sk["won_during_turn"]
            print(game, len(rows), "turns", sk, flush=True)
    print(json.dumps({"games": len(files), "turns": total, "won during the turn (left out)": skipped}))


if __name__ == "__main__":
    main()
