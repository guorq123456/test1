import sys, time
from collections import Counter
sys.path.insert(0, "/home/user/test1")
from svsim.agents.random_agent import RandomAgent
from svsim.cards import decks, library  # noqa
from svsim.core.engine import apply, legal_actions, new_game
from svsim.search.lethal import find_lethal

nodes_budget = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
games = int(sys.argv[2]) if len(sys.argv) > 2 else 20
pirate, ramp = decks.build(decks.PIRATE_SWORD), decks.build(decks.RAMP_DRAGON)
stats, times, nodes = Counter(), [], []
for g in range(games):
    state = new_game(pirate, ramp, seed=g) if g % 2 == 0 else new_game(ramp, pirate, seed=g)
    agents = [RandomAgent(2 * g, 0.2), RandomAgent(2 * g + 1, 0.2)]
    last_turn = None
    while not state.over:
        acts = legal_actions(state)
        if state.phase == 1 and state.turn != last_turn:
            last_turn = state.turn
            r = find_lethal(state, max_nodes=nodes_budget)
            times.append(r.seconds); nodes.append(r.nodes)
            kind = "sure" if r.sure else ("chance" if r.probability > 0 else "none")
            stats[kind] += 1
            stats["incomplete"] += not r.complete
        apply(state, agents[state.active].act(state, acts))
times.sort()
print(dict(stats), "positions", len(times))
print(f"time mean {sum(times)/len(times):.3f}s median {times[len(times)//2]:.3f}s p95 {times[int(len(times)*.95)]:.3f}s max {times[-1]:.2f}s")
nodes.sort(); print("nodes median", nodes[len(nodes)//2], "max", nodes[-1])
