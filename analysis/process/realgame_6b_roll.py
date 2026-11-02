"""Item 6b, part 2: judge each divergence by playing both lines out (pre-registration and results: REALGAME.md).

For every position where the bot's cards differ from Salem's (from realgame_6b.py's output), and for each of K seeds:
rebuild the position with that seed (Salem's remaining deck and the opponent's hidden cards change with the seed),
then play the turn two ways from the same state:
  - "salem": Salem's cards and evolves, forced in his order;
  - "bot": the bot's cards and evolves from the 6b run, forced in its order.
A forced card whose play has several modes or targets takes the one the hand-set evaluator scores best right after it.
Then the bot attacks with Salem's hand, evolve points and bonus PP set aside (so neither branch adds cards), and both
sides finish the game with bots: Salem's side with the 6b pilot for his deck, the opponent with mcts:100+plan.
A pair (same seed, both branches) scores salem_win - bot_win. Check only, never training.

    python analysis/process/realgame_6b_roll.py --tracker DIR --positions 6b-all.jsonl --k 12 --out ROLL.jsonl
"""
import argparse
import collections
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import realgame_6b as R  # noqa: E402
from svsim.core.actions import EndTurn, Evolve, PlayCard, UseBonusPP  # noqa: E402
from svsim.core.engine import apply, legal_actions  # noqa: E402
from svsim.core.state import Phase  # noqa: E402
from svsim.search.evaluate import evaluate  # noqa: E402
from svsim.tools.arena import make_agent  # noqa: E402

OPP_SPEC = "mcts:100+plan"
SEED_BASE = 86400000          # 86400000 + 10000 * game + 1000 * turn + k (seed ledger: next free was 86400000)
MAX_STEPS = 4000

_GAMES = None


def base(c):
    return c - 2 if str(c).endswith("2") else c


def best(st, acts):
    """The candidate the hand-set evaluator likes best right after it (player 0's view)."""
    if len(acts) == 1:
        return acts[0]
    scored = []
    for a in acts:
        c = st.clone()
        apply(c, a)
        scored.append((evaluate(c, 0), a))
    return max(scored, key=lambda x: x[0])[1]


def force(st, line, notes):
    """Play a line's cards and evolves (in its order) for player 0; returns False if the game ended."""
    p = st.players[0]
    for kind, cid in line:
        if st.phase == Phase.OVER:
            return False
        if kind == "出牌":
            want = {cid, base(cid)}
            for attempt in range(2):
                acts = [a for a in legal_actions(st) if isinstance(a, PlayCard)
                        and R.card_of(st, a.uid) is not None and R.card_of(st, a.uid).defn.card_id in want]
                if acts:
                    apply(st, best(st, acts))
                    break
                if attempt == 0 and any(isinstance(a, UseBonusPP) for a in legal_actions(st)):
                    apply(st, UseBonusPP())
                    continue
                if any(c.defn.card_id in want for c in p.hand):
                    notes["unplayable"] += 1
                else:
                    notes["missing"] += 1    # a created card or a summon logged as a play
                break
        elif kind in ("进化", "超进化"):
            sup = kind == "超进化"
            acts = [a for a in legal_actions(st) if isinstance(a, Evolve) and a.super_ == sup
                    and R.card_of(st, a.uid) is not None and base(R.card_of(st, a.uid).defn.card_id) == base(cid)]
            if acts:
                apply(st, best(st, acts))
            else:
                notes["evolve_skipped"] += 1
    return st.phase != Phase.OVER


def attacks(st, agent):
    """The bot finishes player 0's turn with no cards, evolve points or bonus PP to spend, then ends it."""
    p = st.players[0]
    saved = (p.hand, p.ep, p.sep, p.bonus_ready)
    p.hand, p.ep, p.sep, p.bonus_ready = [], 0, 0, False
    try:
        for _ in range(60):
            if st.phase == Phase.OVER or st.active != 0:
                return
            a = agent.act(st, legal_actions(st))
            if isinstance(a, EndTurn):
                break
            apply(st, a)
    finally:
        p.hand, p.ep, p.sep, p.bonus_ready = saved
    if st.phase != Phase.OVER and st.active == 0:
        apply(st, EndTurn())


def finish(st, agents):
    for _ in range(MAX_STEPS):
        if st.phase == Phase.OVER:
            return 1.0 if st.winner == 0 else 0.0 if st.winner == 1 else 0.5
        pi = st.active
        apply(st, agents[pi].act(st, legal_actions(st)))
    return 0.5


def init(tracker):
    global _GAMES
    games, arch = R.load_games(tracker)
    _GAMES = ({gi + 1: (gi, g, r) for gi, g, r in games}, arch, R.read_lists(R.DFM))


def run_one(job):
    pos, k = job
    try:
        os.nice(10)
    except (OSError, AttributeError):
        pass
    by, arch, lists = _GAMES
    gi, g, r = by[pos["game"]]
    rec, _ = R.hands(g)
    seed = SEED_BASE + 10000 * pos["game"] + 1000 * pos["turn"] + k
    st, info, _ = R.build(r, g, rec, pos["turn"], arch, lists, seed)
    out = {"game": pos["game"], "turn": pos["turn"], "deck": pos["deck"], "k": k, "seed": seed}
    if st is None:
        out["skip"] = info
        return out
    lines = {"salem": [x for x in map(tuple, pos["salem"]) if x[0] in ("出牌", "进化", "超进化")],
             "bot": [x for x in map(tuple, pos["bot"]) if x[0] in ("出牌", "进化", "超进化")]}
    for name, line in lines.items():
        s = st.clone()
        notes = collections.Counter()
        me = make_agent(R.BOT[pos["deck"]], seed)
        opp = make_agent(OPP_SPEC, seed + 1)
        if force(s, line, notes):
            attacks(s, me)
        out[name] = finish(s, [me, opp]) if s.phase != Phase.OVER else (1.0 if s.winner == 0 else 0.0)
        out[name + "_notes"] = dict(notes)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", required=True)
    ap.add_argument("--positions", required=True)
    ap.add_argument("--k", type=int, default=12)
    ap.add_argument("--turns", default="1,2,3,4,5")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    turns = {int(x) for x in a.turns.split(",")}
    with open(a.positions, encoding="utf-8") as f:
        pos = [json.loads(x) for x in f]
    div = [p for p in pos if "bot" in p and p["turn"] in turns and R.key(p["salem"]) != R.key(p["bot"])]
    done = set()
    if os.path.exists(a.out):
        with open(a.out, encoding="utf-8") as f:
            done = {(x["game"], x["turn"], x["k"]) for x in map(json.loads, f)}
    jobs = [(p, k) for p in div for k in range(a.k) if (p["game"], p["turn"], k) not in done]
    print(f"{len(div)} 处分歧，{len(jobs)} 对要打", flush=True)
    with Pool(a.workers, initializer=init, initargs=(a.tracker,)) as pool, open(a.out, "a", encoding="utf-8") as f:
        for x in pool.imap_unordered(run_one, jobs, chunksize=1):
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
            f.flush()


if __name__ == "__main__":
    main()
