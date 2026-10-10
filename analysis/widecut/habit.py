"""Which discard habit is right (the architecture thread 2026-10-10 18:45Z, J84)? The strongest tier's discard against
the one it picks once +xprune=3:3:cost leaves its own choice out, each played out to the end.
Condition: the opponent's deck list is known (order and hand not).

**Positions:** collect.py's wide decisions (data/wide.jsonl) where the strongest tier chose a discard and
xprune=3:3:cost cuts it (rules.py, data/rules.json: 45). Rebuilt from the start and the action list (the real
position).

**Branches:**
- (a) the strongest tier's move;
- (b) mcts:1043+plan+learned+phased+xprune=3:3:cost (the whole agent, the collection's seed) choosing on the same
  position, so among the moves the rule keeps.
- Positions where (a) and (b) lead to the same position (state_key) are left out.

**Play-out:**
- Both branches start from the same K = 32 worlds: seed 68600000 + 1000 x j + k for position j and world k.
- Each world draws the hidden cards from the side to move's view (core.view.determinize: the opponent's hand
  and both decks' order), as opsgap's direction_rollout does. Then the branch's move is applied.
- Both sides play on with level-strong (mcts:200+plan+learned+phased, seeded by the world) to the end.
- Win 1, draw 0.5, loss 0, for the side that discarded.

**Report:**
- The mean over positions of (b) - (a), with a 95% interval from 2000 resamples of positions (seed 0).
- The same in two groups, fixed before the run: "big" where the strongest tier's discard includes a card of cost 7
  or more (正义 / 班德 / 诺玛格达拉 / 相枛津 / 金银 class), and the others.
- The 3 positions with the largest |(b) - (a)| (game, turn).
- J84 (the architecture thread): (b) - (a) > 0 on the point estimate, 55%.

    python3 habit.py STEP1_DIR OUT.json [--workers 9] [--k 32]
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis/widecut"))
BANK, K = 68600000, 32
PLAY = "mcts:200+plan+learned+phased"
PICK = "mcts:1043+plan+learned+phased+xprune=3:3:cost"
STEP1 = None
GAMES = {}


def _init(step1):
    global STEP1
    STEP1 = step1
    sys.path.insert(0, f"{step1}/ana")
    import student_data as SD
    GAMES.update({r["g"]: r for r in SD._lines(f"{step1}/selfplay.jsonl")})


def _positions():
    data = ROOT / "analysis/widecut/data"
    rows = [json.loads(l) for l in open(data / "wide.jsonl", encoding="utf-8") if l.strip()]
    kept = json.loads((data / "rules.json").read_text())["rows"]["xprune m3 cost"]
    return [r for r, x in zip(rows, kept) if r["max_kind"] == "discard" and not x["kept"]]


def _pick(job):
    """(position index, (a), (b), same, big, discarded names)."""
    from rules import rebuild
    from collect import _after
    from svsim.core.actions import from_dict, to_dict
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    j, row = job
    s = rebuild(STEP1, GAMES, row)
    a = from_dict(row["max"])
    b = make_agent(PICK, row["start"]).act(s.clone(), legal_actions(s))
    p = s.players[s.active]
    hand = {c.uid: c for c in p.hand}
    disc = [hand[u] for u in a.targets if u in hand]
    return {"j": j, "a": to_dict(a), "b": to_dict(b), "same": _after(s, a) == _after(s, b),
            "big": any(c.cost >= 7 for c in disc), "discarded": [c.defn.name for c in disc],
            "b_discarded": [hand[u].defn.name for u in getattr(b, "targets", ()) or () if u in hand],
            "game": row["game"], "turn": row["turn"], "start": row["start"]}


def _world(job):
    """One world k of position j, branch move `act`: the discarding side's result."""
    from rules import rebuild
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply, legal_actions
    from svsim.core.view import determinize
    from svsim.tools.arena import make_agent
    j, row, act, branch, k = job
    s = rebuild(STEP1, GAMES, row)
    me = s.active
    sd = BANK + 1000 * j + k
    w = determinize(s, me, random.Random(sd))
    apply(w, from_dict(act))
    agents = {me: make_agent(PLAY, sd), 1 - me: make_agent(PLAY, sd + 500)}
    n = 0
    while not w.over and n < 3000:
        apply(w, agents[w.active].act(w, legal_actions(w)))
        n += 1
    r = 1.0 if w.winner == me else 0.0 if w.winner == 1 - me else 0.5
    return j, branch, k, r


def main():
    from multiprocessing import Pool
    step1, out = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 9
    k = int(sys.argv[sys.argv.index("--k") + 1]) if "--k" in sys.argv else K
    _init(step1)
    pos = _positions()
    with Pool(workers, initializer=_init, initargs=(step1,)) as pool:
        picks = pool.map(_pick, list(enumerate(pos)), chunksize=1)
        live = [p for p in picks if not p["same"]]
        jobs = [(p["j"], pos[p["j"]], p[br], br, kk) for p in live for br in ("a", "b") for kk in range(k)]
        res = {}
        for j, br, kk, r in pool.imap_unordered(_world, jobs, chunksize=2):
            res.setdefault(j, {}).setdefault(br, {})[kk] = r
    for p in live:
        ra, rb = res[p["j"]]["a"], res[p["j"]]["b"]
        p["a_win"] = sum(ra.values()) / k
        p["b_win"] = sum(rb.values()) / k
        p["diff"] = p["b_win"] - p["a_win"]
        p["worlds"] = {"a": [ra[i] for i in range(k)], "b": [rb[i] for i in range(k)]}
    rng = random.Random(0)

    def boot(xs):
        if not xs:
            return None
        means = []
        for _ in range(2000):
            pick = [xs[rng.randrange(len(xs))] for _ in xs]
            means.append(sum(pick) / len(pick))
        means.sort()
        return [round(sum(xs) / len(xs), 4), round(means[49], 4), round(means[1949], 4), len(xs)]
    summary = {"positions": len(pos), "same_left_out": len(pos) - len(live), "k": k,
               "b_minus_a_all": boot([p["diff"] for p in live]),
               "b_minus_a_big": boot([p["diff"] for p in live if p["big"]]),
               "b_minus_a_other": boot([p["diff"] for p in live if not p["big"]]),
               "a_win_mean": round(sum(p["a_win"] for p in live) / len(live), 4) if live else None,
               "b_win_mean": round(sum(p["b_win"] for p in live) / len(live), 4) if live else None,
               "largest": [{k2: p[k2] for k2 in ("game", "turn", "start", "discarded", "b_discarded", "a_win",
                                                 "b_win", "diff")}
                           for p in sorted(live, key=lambda p: -abs(p["diff"]))[:3]]}
    Path(out).write_text(json.dumps({"summary": summary, "positions": picks}, ensure_ascii=False, indent=1))
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
