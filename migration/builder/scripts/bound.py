"""Damage upper-bound estimate (the player's idea) and its evaluation."""
import sys, pickle, time, glob
sys.path.insert(0, "/home/user/test1")
from svsim.cards import library  # noqa
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard, Engage, Fuse, UseBonusPP
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Keyword
from svsim.core.script import prop
from svsim.search.lethal import LethalSearch

INF = 10 ** 6


def face_potential(state, me):
    total = 0
    for f in state.players[me].followers:
        if prop(f, "cant_attack"):
            continue
        left = f.max_attacks - f.attacks_made
        if left <= 0:
            continue
        if f.entered_turn == state.turn and not f.keywords & Keyword.STORM:
            continue
        total += f.atk * left
    return total


def bound(state):
    me, opp = state.active, 1 - state.active
    if not state.players[opp].deck:
        return INF
    base_hp, base_face = state.players[opp].leader_hp, face_potential(state, me)
    pp = state.players[me].pp
    items, evolve_best, bonus = {}, 0, 0
    for a in legal_actions(state):
        if isinstance(a, (Attack, EndTurn)):
            continue
        if isinstance(a, UseBonusPP):
            bonus = 1
            continue
        s = state.clone()
        apply(s, a)
        if s.winner == me:
            return INF
        gain = (base_hp - s.players[opp].leader_hp) + (face_potential(s, me) - base_face)
        if isinstance(a, Evolve):
            evolve_best = max(evolve_best, gain)
            continue
        cost = max(0, pp - s.players[me].pp)
        key = ("card", a.uid) if isinstance(a, (PlayCard, Fuse)) else ("engage", a.uid)
        if gain > items.get(key, (0, 0))[0]:
            items[key] = (gain, cost)
    budget = pp + bonus
    best = [0] * (budget + 1)               # 0/1 knapsack: max gain within the PP budget
    for gain, cost in items.values():
        for b in range(budget, cost - 1, -1):
            best[b] = max(best[b], best[b - cost] + gain)
    return base_face + evolve_best + best[budget]


if __name__ == "__main__":
    rows = []
    for path in sorted(glob.glob(sys.argv[1])):
        rows += pickle.load(open(path, "rb"))
    print(len(rows), "positions")
    small = LethalSearch(max_nodes=int(sys.argv[2]) if len(sys.argv) > 2 else 200)
    full = LethalSearch(max_nodes=2000)
    stats = dict(lethal=0, missed=0, missed_hybrid=0, filtered=0)
    t_full = t_filter = t_hybrid = t_bound = 0.0
    missed_examples = []
    for state, sure, prob, complete, secs, nodes in rows:
        t0 = time.perf_counter(); b = bound(state); tb = time.perf_counter() - t0
        t_bound += tb
        r = full.solve(state)
        t_full += r.seconds
        ok = b >= state.players[1 - state.active].leader_hp
        if ok:
            t_filter += tb + r.seconds
            t_hybrid += tb + r.seconds
        else:
            stats["filtered"] += 1
            t_filter += tb
            rs = small.solve(state)
            t_hybrid += tb + rs.seconds
        if sure:
            stats["lethal"] += 1
            if not ok:
                stats["missed"] += 1
                missed_examples.append((state, b))
                if not rs.sure:
                    stats["missed_hybrid"] += 1
    print(stats)
    print(f"time: full search {t_full:.1f}s | filter only {t_filter:.1f}s | filter + small search {t_hybrid:.1f}s | bound itself {t_bound:.1f}s")
    pickle.dump(missed_examples, open(sys.argv[1] + ".missed", "wb"))
