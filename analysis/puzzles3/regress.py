"""Why cand-kc / cand-nl lose puzzles 2 and 3 where the installed model at 1043 wins (the architecture thread
2026-10-10 15:13Z; the analysis line's a993938, README-opsgap.md). Condition: the opponent's deck list is known
(order and hand not).

For each spec and seed (the puzzle bank's positions, tests/puzzles, played as tools.puzzles plays them):
- every searched decision of the turn: the search's centre (the ENDED score of the decision's position), the
  root's children (key, visits, value), the chosen move;
- the turn's line, its end's facts and whether the bank's answer holds (solved);
- the scores (not squashed) the installed and cand-kc models give the turn end (ENDED) and the start position:
  ENDED (what the centre uses), and ACT (the model for the player to move).

    python3 regress.py OUT.jsonl [--specs SPEC ...] [--seeds 8] [--puzzles NAME ...] [--workers 4] [--scale S]

`--scale S`: the search's squash scale (ISMCTS.scale, default 8) set to S, the same as multiplying every score
difference by 8 / S (a diagnostic: a shift of the ENDED model changes nothing, the centre moving with it).
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
PUZZLES = ("ramp-erntz-normagdala", "ramp-erntz-spilling")
SPECS = ("mcts:1043+plan+learned+phased", "mcts:997+plan+learned+phased=cand-kc-ramp-ramp")
MODELS = {"installed": "level-strong", "cand-kc": "mcts:200+plan+learned+phased=cand-kc-ramp-ramp"}


def job(item):
    name, spec, seed, scale = item
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.search.evaluate import after_end_of_turn, evaluate
    from svsim.search.mcts import _locator, action_key
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    from svsim.tools.puzzles import facts, judge, puzzles
    from svsim.ui.text import describe_line
    build, answer = next((b, a) for n, b, a in puzzles() if n == name)
    W = {m: _search(make_agent(s, 0)).weights for m, s in MODELS.items()}
    state = build(seed)
    start = state.clone()
    me = state.active
    agent = make_agent(spec, seed)
    search = _search(agent)
    if scale:
        search.scale = scale
    decisions, actions = [], []
    while not state.over and state.active == me and len(actions) < 60:
        legal = legal_actions(state)
        search.last_root = None
        a = agent.act(state, legal)
        r = search.last_root
        if r is not None and len(legal) > 1:
            where = _locator(state, me)
            kids = sorted(((n.visits, round(n.value, 4), repr(k)) for k, n in r.children.items()), reverse=True)
            decisions.append({"step": len(actions), "center": round(search.center, 3), "chosen": repr(action_key(state, a, where)),
                              "children": kids[:12], "legal": len(legal)})
        actions.append(a)
        if isinstance(a, EndTurn):
            break
        apply(state, a)
    end = state if state.over else after_end_of_turn(state)
    f = facts(end, me)
    scores = {}
    for m, w in W.items():
        scores[m] = {"end ENDED": None if end.over else round(evaluate(end, me, w, False), 3),
                     "start ENDED (centre)": round(evaluate(start, me, w, False), 3),
                     "start ACT": round(evaluate(start, me, w, True), 3)}
    return {"puzzle": name, "spec": spec, "scale": scale, "seed": seed, "solved": judge(answer, f), "facts": f,
            "line": describe_line(start, actions), "decisions": decisions, "scores": scores}


def main():
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--specs", nargs="+", default=list(SPECS))
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--puzzles", nargs="+", default=list(PUZZLES))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--scale", type=float, default=None)
    args = ap.parse_args()
    jobs = [(p, s, seed, args.scale) for p in args.puzzles for s in args.specs for seed in range(1, args.seeds + 1)]
    with Pool(args.workers) as pool, open(args.out, "w") as fh:
        for r in pool.imap_unordered(job, jobs):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            print(r["puzzle"], r["spec"].split("+")[0], r["spec"].split("=")[-1] if "=" in r["spec"] else "installed",
                  r["seed"], "solved" if r["solved"] is True else r["solved"], flush=True)


if __name__ == "__main__":
    main()
