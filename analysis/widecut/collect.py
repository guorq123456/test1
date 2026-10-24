"""Wide decisions in the Ramp mirror, by kind (the architecture thread 2026-10-10 18:37Z): where else could a rule on
visible information prune, as +xprune does for discards? Condition: the opponent's deck list is known (order and
hand not).

**Positions:** step 1's turn starts (RC 6f11111, Ramp mirror self-play), training split, starts 100 to 100 + N.
- The "strongest" tier (mcts:1043+plan+learned+phased, the whole agent, seed = start index) plays the turn.
- At each of its decisions with 9 or more legal moves, level-strong (mcts:200+plan+learned+phased, same seed) also
  chooses, on a copy.
- Same choice: the two moves lead to the same position (lethal.state_key after applying each on a copy, the copy's
  random numbers the same). Interchangeable cards and orders then count as the same.

**Per decision:**
- the legal moves by kind;
- each tier's choice and its kind;
- the action list from the start, so the position can be rebuilt (the real position, no determinization).

**Kinds** (svsim.core.actions; "discard" by search.xprune.discards):
- discard: a play / evolve / engage whose hand targets are discarded;
- choose: a play with modes (Choose);
- play_target: a play with targets on the board;
- play: a play without a choice;
- evolve, super (with or without targets);
- attack_leader, attack_follower;
- bonus, end, other.

    python3 collect.py STEP1_DIR OUT.jsonl [N] [--workers 3]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
MAX, STRONG, WIDE = "mcts:1043+plan+learned+phased", "mcts:200+plan+learned+phased", 9


def kind(state, a) -> str:
    from svsim.core.actions import Attack, EndTurn, Engage, Evolve, PlayCard, UseBonusPP
    from svsim.core.state import leader_uid
    from svsim.search.xprune import discards
    p = state.players[state.active]
    hand = {c.uid for c in p.hand}
    targets = getattr(a, "targets", ()) or ()
    t = [u for u in targets if u in hand]
    if t and isinstance(a, (PlayCard, Evolve, Engage)) and discards(state, a, t):
        return "discard"
    if isinstance(a, PlayCard):
        if a.modes:
            return "choose"
        return "play_target" if targets else "play"
    if isinstance(a, Evolve):
        return "super" if a.super_ else "evolve"
    if isinstance(a, Attack):
        return "attack_leader" if a.target == leader_uid(1 - state.active) else "attack_follower"
    if isinstance(a, UseBonusPP):
        return "bonus"
    if isinstance(a, EndTurn):
        return "end"
    return "other"


def _after(state, a):
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply
    from svsim.search.lethal import state_key
    s = state.clone()
    if isinstance(a, EndTurn):
        return "end"
    apply(s, a)
    return state_key(s)


def job(item):
    i, step1, start = item
    sys.path.insert(0, f"{step1}/ana")
    import student_data as SD
    from svsim.core.actions import EndTurn, to_dict
    from svsim.core.engine import apply, legal_actions
    from svsim.tools.arena import make_agent
    games = {r["g"]: r for r in SD._lines(f"{step1}/selfplay.jsonl")} if not hasattr(job, "games") else job.games
    job.games = games
    state = SD._state_at(games[start["game"]], start["at"])
    me, agent, done, rows = state.active, make_agent(MAX, i), [], []
    while not state.over and state.active == me:
        legal = legal_actions(state)
        a = agent.act(state, legal)
        if len(legal) >= WIDE:
            b = make_agent(STRONG, i).act(state.clone(), legal)
            kinds = {}
            for x in legal:
                k = kind(state, x)
                kinds[k] = kinds.get(k, 0) + 1
            rows.append({"start": i, "game": start["game"], "at": start["at"], "prefix": list(done),
                         "turn": state.turn, "legal": len(legal), "kinds": kinds,
                         "max": to_dict(a), "max_kind": kind(state, a), "strong": to_dict(b),
                         "strong_kind": kind(state, b), "same": _after(state, a) == _after(state, b),
                         "pp": state.players[me].pp, "max_pp": state.players[me].max_pp})
        if isinstance(a, EndTurn):
            break
        done.append(to_dict(a))
        apply(state, a)
    return rows


def main():
    from multiprocessing import Pool
    step1, out = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 180
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 3
    sys.path.insert(0, f"{step1}/ana")
    import student_data as SD
    starts = [r for r in SD._lines(f"{step1}/starts.jsonl") if r["split"] == "train"][100:100 + n]
    total = 0
    with Pool(workers) as pool, open(out, "w", encoding="utf-8") as fh:
        for rows in pool.imap(job, [(100 + j, step1, r) for j, r in enumerate(starts)]):
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            total += len(rows)
            fh.flush()
    print(json.dumps({"starts": len(starts), "wide_decisions": total}))


if __name__ == "__main__":
    main()
