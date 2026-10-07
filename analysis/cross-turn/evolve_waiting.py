"""Was Salem holding an evolution for a payoff card not yet drawn? Hand, deck and draw odds at each hold.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> analysis/mirror-regression/salem_games.json \
        analysis/mirror-regression/evolve_probes.json

Payoff cards in two tiers (by what their evolution does, cards.dragon):
- tier A: Burnite (super: the crest), Erntz (evolved: 8 to the enemy leader
  every turn), Lumiore & Argente (super: draw 3);
- tier B: Vorlalai (Depths of the Eld Blades), Normagdala and Kimika (the
  Fanfare again).
For each of Salem's turns in evolve_probes.json: what could be evolved (the
best tier among legal Evolve targets of the turn), the payoff cards in hand,
those left in the deck (the deck's actual contents, which Salem knows: the
list minus the cards seen), and the chance of drawing at least one of a tier
in the next 1, 2, 3 own turns (one draw a turn; hypergeometric). For held
turns, the card Salem evolved in the next two own turns: the same card that
was in hand or on the field at the hold, or another one (drawn later, or a
new copy such as Vorlalai summoned by a discard).
"""
import json
import sys
from collections import Counter, defaultdict
from math import comb

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import Evolve, from_dict
from svsim.core.engine import apply, legal_actions
from svsim.tools import records

TIER_A = {"焦灰的安纳提玛·班德奈特", "约束的《正义》·伊兰翠", "金银绚烂·璐米欧儿&雅尔贞特"}
TIER_B = {"古旧天刀·波菈莱", "禁牙的变貌·诺玛格达拉", "满面笑容的烹饪·琪米卡"}


def name(c):
    return c.defn.name_zh or c.defn.name


def tier(n):
    return "A" if n in TIER_A else "B" if n in TIER_B else "-"


def p_draw(deck_size, k, n):
    """At least one of k wanted cards in the next n draws from deck_size."""
    if k <= 0 or deck_size <= 0:
        return 0.0
    n = min(n, deck_size)
    return 1 - comb(deck_size - k, n) / comb(deck_size, n)


def salem_turns(rec):
    acts = [from_dict(a) for a in rec["actions"]]
    st = records.start(rec)
    i, out = 0, []
    while i < len(acts) and not st.over:
        if st.active != 0 or type(acts[i]).__name__ == "Mulligan":
            apply(st, acts[i])
            i += 1
            continue
        start, turn = i, []
        while i < len(acts) and st.active == 0 and not st.over:
            turn.append((st.clone(), acts[i]))
            apply(st, acts[i])
            i += 1
        out.append((start, turn))
    return out


def main():
    games = json.load(open(sys.argv[1], encoding="utf-8"))["records"]
    probes = json.load(open(sys.argv[2], encoding="utf-8"))["positions"]
    cache = {}
    rows = []
    for p in probes:
        if p["game"] not in cache:
            cache[p["game"]] = salem_turns(games[p["game"]])
        turns = cache[p["game"]]
        k = [s for s, _ in turns].index(p["at"])
        turn = turns[k][1]
        st0 = turn[0][0]
        me = st0.players[0]
        best = "-"
        for s, _ in turn:
            for a in legal_actions(s):
                if isinstance(a, Evolve):
                    t = tier(name(s.on_field(a.uid)))
                    best = min(best, t, key=lambda x: {"A": 0, "B": 1, "-": 2}[x])
        hand = Counter(tier(name(c)) for c in me.hand)
        deck = Counter(tier(name(c)) for c in me.deck)
        n = len(me.deck)
        held_uids = {c.uid for c in me.hand} | {c.uid for c in me.field}
        later = []
        for _, t2 in turns[k + 1:k + 3]:
            for s, a in t2:
                if isinstance(a, Evolve):
                    c = s.on_field(a.uid)
                    later.append((tier(name(c)), name(c), "原有那张" if c.uid in held_uids else "另一张（后抽到或新上场）"))
        rows.append({"cat": p["category"], "best_now": best, "hand_A": hand["A"], "hand_B": hand["B"],
                     "deck_A": deck["A"], "deck_B": deck["B"], "deck": n,
                     "pA": [p_draw(n, deck["A"], d) for d in (1, 2, 3)],
                     "pB": [p_draw(n, deck["B"], d) for d in (1, 2, 3)], "later": later})
    for cat in ("evolve_hold", "evolve_use"):
        sub = [r for r in rows if r["cat"] == cat]
        print(f"\n{cat}（{len(sub)} 个回合）")
        bn = Counter(r["best_now"] for r in sub)
        print("  这回合能进化的最好一档：" + "，".join(f"{ {'A': 'A 档', 'B': 'B 档', '-': '只有普通'}[k] } {bn[k]}"
                                            for k in ("A", "B", "-")))
        for k in ("A", "B", "-"):
            g = [r for r in sub if r["best_now"] == k]
            if not g:
                continue
            ha = sum(r["hand_A"] > 0 for r in g)
            mean = lambda xs: sum(xs) / len(xs)
            print(f"   能进化最好是 {k}（{len(g)}）：手里有 A 档 {ha}/{len(g)}；牌库里 A 档平均 {mean([r['deck_A'] for r in g]):.1f} 张"
                  f"（牌库 {mean([r['deck'] for r in g]):.0f} 张），1/2/3 回合内抽到 A 档的概率 "
                  + " / ".join(f"{mean([r['pA'][i] for r in g]):.0%}" for i in range(3))
                  + f"；B 档 " + " / ".join(f"{mean([r['pB'][i] for r in g]):.0%}" for i in range(3)))
        if cat == "evolve_hold":
            later = [x for r in sub for x in r["later"][:1]]
            print(f"  忍住后两回合内的第一次进化：{len(later)} 次。" + "，".join(
                f"{t} 档 {src} {n}" for (t, src), n in Counter((t, src) for t, _, src in later).most_common()))
            waits = [r for r in sub if r["best_now"] != "A" and r["hand_A"] == 0]
            got = [r for r in waits if any(t == "A" for t, _, _ in r["later"])]
            print(f"  这回合没有 A 档可进化、手里也没有 A 档的忍住：{len(waits)} 个；之后两回合内进化了 A 档的 {len(got)} 个，"
                  f"其中那张是后来抽到的 {sum(any(t == 'A' and s != '原有那张' for t, _, s in r['later']) for r in got)} 个")


if __name__ == "__main__":
    main()
