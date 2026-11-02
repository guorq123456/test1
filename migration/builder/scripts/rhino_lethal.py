"""Lethal search on Rhinoceroach Forest combo positions."""
import sys, random, pickle, time
sys.path.insert(0, "/home/user/test1")
from multiprocessing import Pool
from svsim.agents.random_agent import RandomAgent
from svsim.cards import decks, library, unlimited as U  # noqa
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Phase
from svsim.search.lethal import find_lethal, damage_estimate

RHINO, RAMP = decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON)


def position(seed):
    rng = random.Random(seed)
    while True:
        state = new_game(RHINO, RAMP, seed=seed, first=rng.randrange(2))
        agents = [RandomAgent(seed, 0.2), RandomAgent(seed + 1, 0.2)]
        target_turn = rng.randint(7, 10)
        while not state.over:
            p = state.players[state.active]
            if state.phase == Phase.MAIN and state.active == 0 and p.turns_taken >= target_turn and p.combo == 0 \
                    and p.pp == p.max_pp:
                break
            apply(state, agents[state.active].act(state, legal_actions(state)))
        if state.over:
            seed += 1000
            continue
        p = state.players[0]
        pool = p.hand + p.deck
        rhinos = [c for c in pool if c.defn == U.KILLER_RHINOCEROACH]
        if not rhinos:
            seed += 1000
            continue
        rng.shuffle(pool)
        k = rng.randint(5, 9)
        hand = [rhinos[0]] + [c for c in pool if c is not rhinos[0]][:k - 1]
        p.deck = [c for c in pool if all(c is not h for h in hand)]
        rng.shuffle(p.deck)
        p.hand = hand
        state.players[1].leader_hp = rng.randint(6, 18)
        return state


def run(seed):
    state = position(seed)
    out = {"seed": seed, "hp": state.players[1].leader_hp, "pp": state.players[0].pp,
           "hand": len(state.players[0].hand), "estimate": damage_estimate(state)}
    for budget in (2000, 20000, 100000):
        r = find_lethal(state, max_nodes=budget)
        out[budget] = (r.sure, round(r.probability, 2), r.complete, r.nodes, round(r.seconds, 2), len(r.line))
        if r.complete or r.sure:
            break
    return out


if __name__ == "__main__":
    n = int(sys.argv[1])
    with Pool(4) as pool:
        rows = pool.map(run, range(n))
    pickle.dump(rows, open("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/rhino_rows.pkl", "wb"))
    for r in rows[:12]:
        print(r)
    final = lambda r: r.get(100000) or r.get(20000) or r[2000]
    sure = [r for r in rows if final(r)[0]]
    print(f"{n} positions: sure lethal {len(sure)}; still unknown after 100000 nodes "
          f"{sum(1 for r in rows if not final(r)[0] and not final(r)[2])}")
    for b in (2000, 20000):
        found = sum(1 for r in sure if r.get(b) and r[b][0])
        print(f"  found within {b} nodes: {found}/{len(sure)}")
    times = sorted(sum(v[4] for k, v in r.items() if isinstance(k, int)) for r in rows)
    print(f"  time per position (all budgets tried): median {times[len(times)//2]:.1f}s, max {times[-1]:.1f}s")
    print(f"  generic damage estimate below defense on sure lethals: {sum(1 for r in sure if r['estimate'] < r['hp'])}/{len(sure)}")
    lens = sorted(final(r)[5] for r in sure)
    print(f"  sure lethal line length: median {lens[len(lens)//2] if lens else 0}, max {lens[-1] if lens else 0}")
