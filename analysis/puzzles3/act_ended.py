"""ACT before ending the turn against ENDED after it, on the same positions (the architecture thread 15:13Z, item 2):
whole turns played by level-strong from the first N step-1 training starts and from the puzzle bank (seeds 1-8);
at each turn's last decision (just before End Turn) the ACT score of the position (the player to move), and the
ENDED score of search.evaluate.after_end_of_turn of it, for the installed model and cand-kc (which shares the
installed ACT); Ramp mirror positions only. Mean and spread of ENDED - ACT, and the ENDED models' difference.
Condition: the opponent's deck list is known (order and hand not).
usage: act_ended.py STEP1_DIR [N]"""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main():
    d = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    sys.path.insert(0, f"{d}/ana")
    import student_data as SD
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.search.evaluate import after_end_of_turn, evaluate
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    from svsim.tools.puzzles import puzzles
    W = {m: _search(make_agent(s, 0)).weights for m, s in
         (("installed", "level-strong"), ("cand-kc", "mcts:200+plan+learned+phased=cand-kc-ramp-ramp"))}
    games = {r["g"]: r for r in SD._lines(f"{d}/selfplay.jsonl")}
    starts = [SD._state_at(games[r["game"]], r["at"])
              for r in SD._lines(f"{d}/starts.jsonl") if r["split"] == "train"][:n]
    starts += [b(seed) for _, b, _ in puzzles() for seed in range(1, 9)]
    # the Ramp mirror only: cand-kc's folder holds only ramp-ramp models (other pairings fall back to another model)
    starts = [s for s in starts if s.players[0].deck_name == s.players[1].deck_name == "ramp"]
    rows = []
    for i, s in enumerate(starts):
        me, agent = s.active, make_agent("level-strong", i)
        while not s.over and s.active == me:
            a = agent.act(s, legal_actions(s))
            if isinstance(a, EndTurn):
                end = after_end_of_turn(s)
                if not end.over:
                    rows.append({m: (evaluate(s, me, w, True), evaluate(end, me, w, False)) for m, w in W.items()})
                break
            apply(s, a)
    out = {"positions": len(rows)}
    for m in W:
        diff = [r[m][1] - r[m][0] for r in rows]
        out[m] = {"ACT mean": round(statistics.mean(r[m][0] for r in rows), 3),
                  "ENDED mean": round(statistics.mean(r[m][1] for r in rows), 3),
                  "ENDED - ACT mean": round(statistics.mean(diff), 3), "ENDED - ACT sd": round(statistics.pstdev(diff), 3)}
    kc = [r["cand-kc"][1] - r["installed"][1] for r in rows]
    out["cand-kc ENDED - installed ENDED"] = {"mean": round(statistics.mean(kc), 3), "sd": round(statistics.pstdev(kc), 3)}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
