"""Does a bot spend the second player's bonus PP on its first turn? Random Ramp mirror openings.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> --agent SPEC [--agent SPEC] [--games 200] [--workers 4]

Each game: a Ramp Dragon mirror (the gate's decks) from seed k; the first player's
first turn is played by the first --agent; then each agent plays the second
player's first turn from that same position. "Spent" means the bonus PP is gone
after the turn (pressing it and leaving the point unspent gives it back).
Also reports what the spent turns played, and whether a ramp card (Dragonsign,
Lumiore) left the hand on that turn (played or discarded).
"""
import argparse
from collections import Counter
from multiprocessing import Pool

from svsim.cards import decks
from svsim.core.actions import Mulligan, PlayCard
from svsim.core.engine import apply, legal_actions, new_game
from svsim.tools.arena import make_agent

import turnlib as T

RAMPS = {"龙之启示", "金银绚烂·璐米欧儿&雅尔贞特"}


def opening(k, spec):
    """The position at the second player's first decision of their first turn."""
    st = new_game(decks.build(decks.RAMP_DRAGON), decks.build(decks.RAMP_DRAGON), seed=20000000 + k)
    agents = [make_agent(spec, 7000 + 2 * k + i) for i in range(2)]
    while True:
        p = st.players[st.active]
        if st.active != st.first and p.turns_taken == 1 and not isinstance(legal_actions(st)[0], Mulligan):
            return st
        apply(st, agents[st.active].act(st, legal_actions(st)))


def run(job):
    k, specs = job
    st0 = opening(k, specs[0])
    me = st0.active
    out = {}
    for spec in specs:
        st = st0.clone()
        agent = make_agent(spec, 9000 + k)
        ramps_before = sum(T.name(c) in RAMPS for c in st.players[me].hand)
        played = []
        while st.active == me and not st.over:
            a = agent.act(st, legal_actions(st))
            if isinstance(a, PlayCard):
                played.append(T.name(st.in_hand(me, a.uid)))
            apply(st, a)
        ramps_after = sum(T.name(c) in RAMPS for c in st.players[me].hand)
        out[spec] = {"spent": not st.players[me].bonus_ready, "played": played,
                     "ramp_lost": ramps_after < ramps_before, "had_ramp": ramps_before > 0}
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--agent", action="append", required=True)
    p.add_argument("--games", type=int, default=200)
    p.add_argument("--workers", type=int, default=4)
    args = p.parse_args()
    with Pool(args.workers) as pool:
        res = pool.map(run, [(k, args.agent) for k in range(args.games)])
    for spec in args.agent:
        rows = [r[spec] for r in res]
        spent = [r for r in rows if r["spent"]]
        lost = sum(r["ramp_lost"] for r in spent)
        had = sum(r["had_ramp"] for r in spent)
        what = Counter(" + ".join(r["played"]) or "（无）" for r in spent).most_common(4)
        print(f"{spec}: 第 1 回合用掉额外 PP {len(spent)}/{len(rows)}（{len(spent) / len(rows):.0%}）；"
              f"用掉的回合里手上本有跳费牌 {had} 次，其中跳费牌离手 {lost} 次；打的是 {what}")


if __name__ == "__main__":
    main()
