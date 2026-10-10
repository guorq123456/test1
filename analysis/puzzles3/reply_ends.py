"""The opponent's turn played out from Salem's turn end and from the bot's (the architecture thread 2026-10-10
13:15Z; J60), at k 329 and 455: does the installed evaluation rank Salem's end first once the opponent has replied?
Condition: the opponent's deck list is known (order and hand not).

For each turn end (ops.turn_end: end-of-turn abilities resolved, the opponent's turn not started; Salem's, and each
distinct end of the eight mcts:1043+plan+learned+phased runs in rows_329_455.jsonl):
- D determinizations (seeds SEED + j, the same for every end): the opponent's hand and deck dealt from their unseen
  pool, sorted first so every end of a start deals them the same cards for the same j; my deck reshuffled with its
  own generator; the game's generator reseeded;
- the opponent's turn is started as the search's reply does (engine._start_turn) and played to its end by
  (a) greedy: search.mcts's reply opponent (GreedyAgent, samples 1, the installed weights), and
  (b) mcts:1043+plan+learned+phased (the whole agent, lethal check included; it determinizes my hand itself);
- when my turn comes (or the game is over), the installed evaluation scores it for me: sigma(evaluate(.., me,
  weights, True) / SCALE) (the model for the player to move), 1 / 0 for a won / lost game;
- "cleared": I had a follower at my turn end and none when my turn comes.
Means with a 95% interval (normal), and Salem − bot paired by j.

    python3 reply_ends.py STEP0_DIR ANA_DIR ROWS_329_455.jsonl [--dets 16] [--workers 4] [--out rows.jsonl]
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis/puzzles3"))
KS = (329, 455)
SEED = 66130000
BOT = "mcts:1043+plan+learned+phased"
G = {}


def _init(step0, ana, rows_path):
    import ops
    ops._init(step0, ana)
    G["rows"] = [json.loads(x) for x in open(rows_path) if x.strip()]


def _ends(k):
    """(state at the turn start, me, [(label, turn end, runs)]): Salem's end, then the 1043 runs' distinct ends."""
    import ops
    import turn_level as TL
    from svsim.core.actions import from_dict
    from svsim.search.lethal import state_key
    st = ops.G["starts"][k]
    state, rec = TL._start_state(st)
    me = state.active
    out = [("salem", ops.turn_end(state, TL._salem_turn(rec, st["at"])), 1)]
    seen = {}
    for r in G["rows"]:
        if r["k"] == k and r["spec"] == BOT:
            e = ops.turn_end(state, [from_dict(a) for a in r["actions"]])
            key = state_key(e)
            if key in seen:
                seen[key][2] += 1
            else:
                seen[key] = [f"bot{len(seen)}", e, 1]
    return state, me, out + [tuple(v) for v in seen.values()]


def _deal(end, me, j):
    from svsim.core.view import shuffle
    s = end.clone()
    opp, mine = s.players[1 - me], s.players[me]
    pool = sorted(opp.hand + opp.deck, key=lambda c: (c.defn.card_id, c.cost, c.uid))
    rng = random.Random(SEED + j)
    shuffle(rng, pool)
    n = len(opp.hand)
    opp.hand, opp._deck, opp._deck_shared = [c.copy() for c in pool[:n]], [c.copy() for c in pool[n:]], False
    deck = mine.deck
    shuffle(random.Random(SEED + 500 + j), deck)
    s.rng.seed(SEED + 1000 + j)
    return s


def _job(job):
    from svsim.agents.greedy_agent import GreedyAgent
    from svsim.core.engine import _start_turn, apply, legal_actions
    from svsim.learn.model import SCALE
    from svsim.search.evaluate import evaluate
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    k, label, j, kind = job
    if "ends" not in G:
        G["ends"] = {kk: _ends(kk) for kk in KS}
        G["W"] = _search(make_agent("level-strong", 0)).weights
    W = G["W"]
    _, me, ends = G["ends"][k]
    end = next(e for lab, e, _ in ends if lab == label)
    s = _deal(end, me, j)
    had = len(s.players[me].followers)
    if not s.over and s.active != me:
        _start_turn(s)
        agent = (GreedyAgent(seed=SEED + j + 1, samples=1, weights=W) if kind == "greedy"
                 else make_agent(BOT, SEED + j))
        while not s.over and s.active != me:
            apply(s, agent.act(s, legal_actions(s)))
    if s.over:
        p = 1.0 if s.winner == me else 0.0 if s.winner == 1 - me else 0.5
    else:
        z = evaluate(s, me, W, True)
        p = 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z / SCALE))))
    return {"k": k, "end": label, "j": j, "reply": kind, "p": p, "had_followers": had,
            "cleared": had > 0 and len(s.players[me].followers) == 0, "over": s.over,
            "our_hp": s.players[me].leader_hp, "enemy_hp": s.players[1 - me].leader_hp}


def _ci(xs):
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) if n > 1 else 0.0
    return m, 1.96 * sd / math.sqrt(n)


def main():
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("step0")
    ap.add_argument("ana")
    ap.add_argument("rows")
    ap.add_argument("--dets", type=int, default=16)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out")
    args = ap.parse_args()
    _init(args.step0, args.ana, args.rows)
    labels = {k: [(lab, runs) for lab, _, runs in _ends(k)[2]] for k in KS}
    jobs = [(k, lab, j, kind) for k in KS for lab, _ in labels[k] for kind in ("greedy", "mcts1043")
            for j in range(args.dets)]
    with Pool(args.workers, initializer=_init, initargs=(args.step0, args.ana, args.rows)) as pool:
        rows = pool.map(_job, jobs, chunksize=1)
    if args.out:
        with open(args.out, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
    print("条件：对手卡表已知（牌序、手牌未知）。对手应完一回合以后，现装评估器（我方视角）给的胜率")
    out = {}
    for k in KS:
        print(f"\nk {k}（1043 的 8 次运行有 {len(labels[k]) - 1} 个不同回合末："
              + "，".join(f"{lab} × {runs}" for lab, runs in labels[k][1:]) + "）")
        for kind in ("greedy", "mcts1043"):
            sel = [r for r in rows if r["k"] == k and r["reply"] == kind]
            sal = {r["j"]: r for r in sel if r["end"] == "salem"}
            ms, hs = _ci([r["p"] for r in sal.values()])
            # the bot's: each run's end weighted by its runs, paired by j
            bot_j = {}
            for j in range(args.dets):
                tot = sum(runs * next(r["p"] for r in sel if r["end"] == lab and r["j"] == j)
                          for lab, runs in labels[k][1:])
                bot_j[j] = tot / sum(runs for _, runs in labels[k][1:])
            mb, hb = _ci(list(bot_j.values()))
            md, hd = _ci([sal[j]["p"] - bot_j[j] for j in range(args.dets)])
            clr = {}
            for lab, _ in labels[k]:
                rr = [r for r in sel if r["end"] == lab and r["had_followers"]]
                clr[lab] = (sum(r["cleared"] for r in rr), len(rr))
            per_end = {lab: round(sum(r["p"] for r in sel if r["end"] == lab) / args.dets, 3) for lab, _ in labels[k]}
            print(f"  应手 {kind:8s}：Salem {ms:.3f} ± {hs:.3f}，bot {mb:.3f} ± {hb:.3f}，差 {md:+.3f} ± {hd:.3f} → "
                  f"{'Salem 在前' if md > 0 else 'bot 在前'}；清场 " + "，".join(f"{lab} {a}/{b}" for lab, (a, b) in clr.items())
                  + f"；各回合末均值 {per_end}")
            out.setdefault(k, {})[kind] = {"salem": [round(ms, 4), round(hs, 4)], "bot": [round(mb, 4), round(hb, 4)],
                                           "diff": [round(md, 4), round(hd, 4)], "cleared": clr, "per_end": per_end}
    print("\n" + json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
