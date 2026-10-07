"""E0 gate: how much the bot loses when it infers the opponent's list instead of knowing it.

    cd <svsim checkout> && PYTHONPATH=.:<test1>/analysis/deck-inference python3 <this> --lists DIR \
        --phase sprt --seed 36000000 --workers 4 --out sprt.jsonl
    ... --phase fixed --pairs 300 --seed 36500000 --out fixed.jsonl
    python3 <this> --report sprt.jsonl [fixed.jsonl]

Spec (the architecture thread, 21:09Z): ramp-t against pirate-t (one side's list is pinned down in a
few turns, the other's stays about 7% off in roles: E step v2); A = the opponent's list from the E
step's posterior mixture, B = the known list as now; the same search and iterations on both sides
(--agent, v2s by default); paired, one seed bank; SPRT (50 / 55, at most 1200 games) and then a fixed
run on new seeds; split by who actually went first and by which deck the inferring side played.

The pairing. A seed s fixes the deal with ramp-t in seat 0 and pirate-t in seat 1, and three games
are played on it, the agents' seeds by seat (2s, 2s+1) in all three:
  game 1: A plays ramp-t, B plays pirate-t;
  game 2: B plays ramp-t, A plays pirate-t (the agents swap seats, the decks stay);
  game 3: B on both sides (the control: both know the list, as in the deck league).
A's pair score is the mean of its points in games 1 and 2: 0.5 when knowing the list makes no
difference, whatever the matchup. The SPRT runs on B's pair scores (H0 0.50, H1 0.55, alpha = beta =
0.05, tools.gate's normal approximation). The loss for each deck the inferring side plays is its
points in game 1 (or 2) minus that deck's points in game 3, paired by seed.

A's search. Every determinization A's search makes (search.mcts, through core.view.determinize) keeps
the opponent's hand size and deck size and the cards it can't have from a list (tokens, cards made by
effects) and deals the rest afresh: one tournament list drawn from the posterior over the lists of the
opponent's class (infer.py's likelihood on the cards the opponent has played so far; prior: the lists'
shares), minus the cards played so far, shuffled. The class is public. Nothing else changes: B's
searches, A's mulligan and the rest of A are untouched (the module attribute is replaced only while
A acts).
Condition line: A 对手卡表由揭示牌推断（后验混合），B 已知（牌序、手牌未知）. Premise: each of the four
tournament decks is one of the tournament lists, 40/40, so this is the best case for inference.
"""
import argparse
import json
import math
import os
import random
import sys
import time
from collections import Counter
from multiprocessing import Pool

RAMP, PIRATE = "ramp-t", "pirate-t"
CONDITION = "A 对手卡表由揭示牌推断（后验混合），B 已知（牌序、手牌未知）"
_LISTS = None
CURRENT = None                 # the inferring side's context while it acts: (seat, weights, revealed, valid)


def lists(folder):
    global _LISTS
    if _LISTS is None:
        from infer import load_lists
        ls = load_lists(folder)
        craft_of = {a: Counter(c for _, _, c in v).most_common(1)[0][0] for a, v in ls.items()}
        _LISTS = {}
        for a, v in ls.items():
            _LISTS.setdefault(craft_of[a], {})[a] = [d for _, d, _ in v]
    return _LISTS


def deck_craft(cards):
    return Counter(c.craft for c in cards if c.craft).most_common(1)[0][0]


def inferring_determinize(original):
    def determinize(state, player, rng):
        s = original(state, player, rng)
        if CURRENT is None or CURRENT[0] != player:
            return s
        from svsim.cards.pool import POOL
        from svsim.core.state import CardInstance
        _, weights, revealed, valid = CURRENT
        opp = s.players[1 - player]
        pool = opp.hand + opp.deck
        slots = [i for i, c in enumerate(pool) if c.defn.card_id in valid]
        x, acc, pick = rng.random(), 0.0, weights[-1][0]
        for d, w in weights:
            acc += w
            if x < acc:
                pick = d
                break
        rem = list((pick - revealed).elements())
        rng.shuffle(rem)
        while rem and len(rem) < len(slots):                 # fewer left than unseen slots: draw again from the list
            rem.append(rng.choice(list(pick.elements())))
        for i, cid in zip(slots, rem):
            pool[i] = CardInstance.create(pool[i].uid, POOL[cid], pool[i].owner)
        opp.hand, opp.deck = pool[:len(opp.hand)], pool[len(opp.hand):]
        return s
    return determinize


def install():
    """Route every module's `determinize` (the view's) through the inferring version."""
    import svsim.core.view as view
    original = getattr(view, "_e0_original", view.determinize)
    view._e0_original = original
    patched = getattr(view, "_e0_patched", None) or inferring_determinize(original)
    view._e0_patched = patched
    for mod in list(sys.modules.values()):
        if mod is not None and getattr(mod, "determinize", None) is original:
            mod.determinize = patched


def posterior(revealed, craft, folder):
    """[(list Counter, weight)] over the class's tournament lists, given the cards played so far."""
    from infer_roles import list_weights
    archs = lists(folder)[craft]
    total = sum(len(v) for v in archs.values())
    prior = {a: len(v) / total for a, v in archs.items()}
    valid = {c for v in archs.values() for d in v for c in d}
    seen = Counter({c: k for c, k in revealed.items() if c in valid})
    return [(d, w) for _, d, w in list_weights(seen, archs, prior, len(valid))], valid, seen


def play(seed, who, spec, folder, keep):
    """One game on seed `seed`, ramp-t in seat 0 and pirate-t in seat 1; who[seat] is "A" or "B"."""
    global CURRENT
    from svsim.cards import decks
    from svsim.core.actions import PlayCard
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools import records
    from svsim.tools.arena import VERSIONS, make_agent
    from svsim.ui.session import DECKS
    spec = VERSIONS.get(spec, spec)
    cards = [decks.build(DECKS[RAMP][1]), decks.build(DECKS[PIRATE][1])]
    agents = [make_agent(spec, 2 * seed + i) for i in (0, 1)]
    state = new_game(cards[0], cards[1], seed=seed)
    rec = records.new_record(cards[0], cards[1], seed, state.first, f"{who[0]} / {who[1]}") if keep else None
    revealed = {0: Counter(), 1: Counter()}            # cards each seat has played
    think = [0.0, 0.0]
    cache = {}
    t0 = time.perf_counter()
    while not state.over:
        me = state.active
        if who[me] == "A" and state.phase.name == "MAIN":
            n = sum(revealed[1 - me].values())
            if (me, n) not in cache:
                cache[(me, n)] = posterior(revealed[1 - me], deck_craft(cards[1 - me]), folder)
            weights, valid, seen = cache[(me, n)]
            install()
            CURRENT = (me, weights, seen, valid)
        t = time.perf_counter()
        try:
            action = agents[me].act(state, legal_actions(state))
        finally:
            CURRENT = None
        think[me] += time.perf_counter() - t
        if isinstance(action, PlayCard) and state.phase.name == "MAIN":
            c = state.in_hand(me, action.uid)
            if c is not None:
                revealed[me][c.defn.card_id] += 1
        if rec is not None:
            records.add(rec, action)
        apply(state, action)
    out = {"winner": state.winner, "first": state.first, "turns": state.turn,
           "seconds": time.perf_counter() - t0, "think": think}
    if rec is not None:
        rec["winner"] = state.winner
        out["record"] = rec
    return out


def play_seed(job):
    k, seed, spec, folder, keep = job
    games = {name: play(seed, who, spec, folder, keep)
             for name, who in (("g1", ("A", "B")), ("g2", ("B", "A")), ("g3", ("B", "B")))}
    return {"k": k, "seed": seed, **games}


def pts(g, seat):
    return 0.5 if g["winner"] not in (0, 1) else 1.0 if g["winner"] == seat else 0.0


def a_pair(r):
    """A's pair score: its points in game 1 (seat 0) and game 2 (seat 1)."""
    return (pts(r["g1"], 0) + pts(r["g2"], 1)) / 2


def ci(xs):
    n = len(xs)
    m = sum(xs) / n
    return m, 1.96 * math.sqrt(sum((x - m) ** 2 for x in xs) / max(n - 1, 1) / n)


def report(paths):
    for path in paths:
        rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
        if not rows:
            continue
        print(f"== {os.path.basename(path)}：{len(rows)} 个种子，A 对 B {2 * len(rows)} 局，另有对照 {len(rows)} 局")
        print(f"条件：{CONDITION}。前提：四套比赛卡组都和某张比赛卡表 40/40 相同，这是推断的最好情况。")
        m, h = ci([a_pair(r) for r in rows])
        print(f"  A（推断）对 B（已知）的得分：{m:.1%} ± {h:.1%}（按种子配对）；CR 稳态式 {800 * (m - 0.5):+.0f}"
              f"（{800 * (m - h - 0.5):+.0f}～{800 * (m + h - 0.5):+.0f}）")
        for title, game, seat in (("推断方打跳费龙（推断旗皇的卡表）", "g1", 0), ("推断方打旗皇（推断跳费龙的卡表）", "g2", 1)):
            d = [pts(r[game], seat) - pts(r["g3"], seat) for r in rows]
            dm, dh = ci(d)
            same = sum(r[game]["winner"] == r["g3"]["winner"] and r[game]["turns"] == r["g3"]["turns"] for r in rows)
            print(f"  {title}：推断方 {sum(pts(r[game], seat) for r in rows) / len(rows):.1%}，对照（双方已知）"
                  f"{sum(pts(r['g3'], seat) for r in rows) / len(rows):.1%}，差 {dm:+.1%} ± {dh:.1%}"
                  f"（{same} 个种子和对照同胜负同回合数）")
            for first in (True, False):
                sub = [r for r in rows if (r[game]["first"] == seat) == first]
                if sub:
                    dd = [pts(r[game], seat) - pts(r["g3"], seat) for r in sub]
                    a, b = ci(dd)
                    print(f"      推断方{'先' if first else '后'}手：{len(sub)} 局，差 {a:+.1%} ± {b:.1%}")
        ta = sum(r["g1"]["think"][0] + r["g2"]["think"][1] for r in rows)
        tb = sum(r["g1"]["think"][1] + r["g2"]["think"][0] for r in rows)
        print(f"  思考时间 A / B = {ta / max(tb, 1e-9):.3f}（同搜索同迭代数；比值只报告，不调）\n")


def main():
    if "--report" in sys.argv:
        report(sys.argv[sys.argv.index("--report") + 1:])
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--lists", required=True)
    ap.add_argument("--phase", choices=("sprt", "fixed"), required=True)
    ap.add_argument("--agent", default="v2s")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--pairs", type=int, default=600, help="seeds at most (sprt) or exactly (fixed)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--records", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from svsim.tools.gate import bounds, llr
    rows = []
    if os.path.exists(args.out):
        rows = [json.loads(line) for line in open(args.out, encoding="utf-8") if line.strip()]
    done = {r["k"] for r in rows}
    lo, hi = bounds(0.05, 0.05)
    jobs = [(k, args.seed + k, args.agent, args.lists, args.records) for k in range(args.pairs) if k not in done]
    print(f"条件：{CONDITION}", flush=True)
    with Pool(args.workers) as pool, open(args.out, "a", encoding="utf-8") as fh:
        for r in pool.imap_unordered(play_seed, jobs, chunksize=1):
            fh.write(json.dumps(r) + "\n")
            fh.flush()
            rows.append(r)
            if args.phase == "sprt":
                b = [1 - a_pair(x) for x in rows]
                v = llr(b, 0.50, 0.55)
                if len(rows) % 10 == 0:
                    print(f"  {len(rows)} 个种子，B 得分 {sum(b) / len(b):.3f}，LLR {v:+.2f}（{lo:.2f}～{hi:.2f}）", flush=True)
                if v <= lo or v >= hi:
                    print(f"SPRT 停：{'H1（已知卡表强 5 点以上）' if v >= hi else 'H0（看不出差别）'}，"
                          f"{len(rows)} 个种子", flush=True)
                    pool.terminate()
                    break


if __name__ == "__main__":
    main()
