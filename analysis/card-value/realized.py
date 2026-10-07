"""Does the teacher's keep value predict what keeping a card actually brings, beyond the one-turn search?

    cd <svsim checkout at f492ffe or later> && PYTHONPATH=. python3 <this> RECORDS.jsonl[.gz] [...] \
        --items 1500 [--k 4] [--research 100] [--next-search 0] [--opp-search 0] [--workers 4] --out rows.jsonl

Positions: the first decision of own turns in self-play records (learn.netdata),
sampled at random. At each, the teacher's search (mcts-raw:100+learned+phased
in svsim.agents.crossturn_agent's CrossTurnAgent) reads its principal line;
one card c the line plays is picked at random. Three numbers:
  T  the teacher: keep c this turn minus the line, through the opponent's turn
     and the own next turn (its play-outs), 8 determinizations, ENDED model;
  Q  the control: in the same one-turn tree, the best line that never plays c
     minus the best line that does (the search's own estimates);
  G  what keeping c brings, played for real: on k determinizations (the same
     for both arms), v2 plays the rest of this turn, in one arm never playing
     c; v2 plays the opponent's turn; at the start of the own next turn
     mcts-raw:400+learned+phased searches, and its best move's value (made
     absolute: the search squashes relative to the root) is turned into a win
     probability; G = mean over determinizations of (keep arm - line arm),
     measured on two independent sets of k determinizations (G1, G2: their
     agreement is the noise ceiling; G is the mean of both).
The test (analyse.py): does T explain G once Q is known (partial rank
correlation, the AUC for the sign of G from Q against Q and T), with intervals
from resampling positions, by own turn.
"""
import argparse
import gzip
import json
import math
import random
from multiprocessing import Pool

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import EndTurn, PlayCard, from_dict
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Phase
from svsim.tools import records

V2 = "mcts:100+plan+learned+phased"
JUDGE = "mcts-raw:400+learned+phased"


def lines_of(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [line for line in f if line.strip()]


def turn_starts(record):
    """Action indices of the first decision of each own turn (main phase)."""
    st = records.start(record)
    out, last = [], None
    for i, data in enumerate(record["actions"]):
        if st.phase == Phase.MAIN and (st.turn, st.active) != last:
            out.append(i)
            last = (st.turn, st.active)
        apply(st, from_dict(data))
        if st.over:
            break
    return out


def state_at(record, i):
    st = records.start(record)
    for data in record["actions"][:i]:
        apply(st, from_dict(data))
    return st


def keeps_card(cid):
    def veto(s, a):
        if not isinstance(a, PlayCard):
            return False
        card = s.in_hand(s.active, a.uid)
        return card is not None and card.defn.card_id == cid
    return veto


def agent_with_veto(spec, seed, veto):
    from svsim.tools.arena import make_agent
    agent = make_agent(spec, seed)
    if veto is None:
        return agent
    inner = agent
    while not (hasattr(inner, "search") and hasattr(inner.search, "veto")):
        inner = inner.base
    old = inner.search.veto
    inner.search.veto = (lambda s, a: veto(s, a) or old(s, a)) if old else veto

    class Kept:
        def act(self, state, legal):
            return agent.act(state, [a for a in legal if not veto(state, a)] or legal)
    return Kept()


def judge_value(st, me, seed):
    """Win probability for `me` at the start of their turn by a 400-iteration search."""
    from svsim.learn.model import SCALE
    from svsim.tools.arena import make_agent
    if st.over:
        return 1.0 if st.winner == me else 0.0 if st.winner == 1 - me else 0.5
    agent = make_agent(JUDGE, seed)
    search = agent.search
    search.choose(st)
    best = max(search.last_root.children.values(), key=lambda c: c.visits)
    est = min(max(search.estimate(best), 1e-6), 1 - 1e-6)
    score = search.center + search.scale * math.log(est / (1 - est))     # undo the squash around the root
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, score / SCALE))))


def arm(base, me, veto, seed):
    """v2 plays the rest of this turn (never what `veto` forbids), v2 plays the opponent's turn; the judge's
    value at the start of the own next turn."""
    st = base.clone()
    mine = agent_with_veto(V2, seed, veto)
    while not st.over and st.active == me:
        apply(st, mine.act(st, legal_actions(st)))
    from svsim.tools.arena import make_agent
    theirs = make_agent(V2, seed + 1)
    while not st.over and st.active != me:
        apply(st, theirs.act(st, legal_actions(st)))
    return judge_value(st, me, seed + 2)


def measure(job):
    line_text, i, seed, k, cfg = job
    from svsim.agents.crossturn_agent import NONE, CrossTurnAgent, principal_line, restrictions
    from svsim.core.view import determinize
    from svsim.tools.arena import make_agent
    import teacher_eval as TE
    record = json.loads(line_text)
    st = state_at(record, i)
    me = st.active
    extra = {k_: v for k_, v in cfg.items() if v}
    teacher = CrossTurnAgent(make_agent("mcts-raw:100+learned+phased", seed), samples=8, seed=seed,
                             next_turn=True, **extra)
    teacher.search.choose(st)
    root = teacher.search.last_root
    line = principal_line(root)
    keeps = [r for r in restrictions(line) if r.startswith("keep:")]
    if not keeps:
        return None
    rng = random.Random(seed)
    r = rng.choice(keeps)
    cands = [NONE, r]
    out = teacher.outcomes(st, teacher.lines_for(st, line, cands) if cfg.get("research") else line, cands)
    diffs = [a - b for a, b in zip(out[r], out[NONE])]
    n = len(diffs)
    t = sum(diffs) / n
    se = math.sqrt(sum((d - t) ** 2 for d in diffs) / max(n - 1, 1) / n)
    q = TE.control(teacher.search, root, r)
    cid = int(r.split(":")[1])
    gs = []
    for j in range(2 * k):                    # two independent sets of k determinizations: G and G2
        base = determinize(st, me, random.Random(seed * 1000 + j))
        sd = seed * 1000 + 10 * j
        gs.append(arm(base, me, keeps_card(cid), sd) - arm(base, me, None, sd))
    p = st.players[me]
    return {"seed": seed, "i": i, "turn": st.turn, "own_turn": p.turns_taken, "first": st.first == me,
            "card": cid, "T": t, "se": se, "Q": q, "G": sum(gs) / len(gs),
            "G1": sum(gs[:k]) / k, "G2": sum(gs[k:]) / k, "G_samples": gs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records", nargs="+")
    ap.add_argument("--items", type=int, default=1500)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--research", type=int, default=100)
    ap.add_argument("--next-search", type=int, default=0)
    ap.add_argument("--opp-search", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    games = [line for path in args.records for line in lines_of(path)]
    rng = random.Random(args.seed)
    cfg = {"research": args.research, "next_search": args.next_search, "opp_search": args.opp_search}
    picks = []
    while len(picks) < args.items * 2:            # some positions have no card on the line: oversample
        g = rng.randrange(len(games))
        picks.append((g, rng.random()))
    jobs = []
    starts_cache = {}
    for n, (g, u) in enumerate(picks):
        if g not in starts_cache:
            starts_cache[g] = turn_starts(json.loads(games[g]))
        starts = starts_cache[g]
        if not starts:
            continue
        jobs.append((games[g], starts[int(u * len(starts))], args.seed * 100000 + n, args.k, cfg))
    import os
    seen = set()
    if os.path.exists(args.out):                  # resume: the positions already measured are skipped
        seen = {json.loads(line)["seed"] for line in open(args.out, encoding="utf-8") if line.strip()}
    jobs = [j for j in jobs if j[2] not in seen]
    done = len(seen)
    with Pool(args.workers) as pool, open(args.out, "a", encoding="utf-8") as fh:
        for row in pool.imap_unordered(measure, jobs, chunksize=1):
            if row is None:
                continue
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            done += 1
            if done % 50 == 0:
                print(f"  {done} 项", flush=True)
            if done >= args.items:
                pool.terminate()
                break


if __name__ == "__main__":
    main()
