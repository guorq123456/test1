import sys, cProfile, pstats, pickle
sys.path.insert(0, "/home/user/test1")
from svsim.agents.random_agent import RandomAgent
from svsim.cards import decks, library  # noqa
from svsim.core.engine import apply, legal_actions, new_game
from svsim.search.lethal import find_lethal
pirate, ramp = decks.build(decks.PIRATE_SWORD), decks.build(decks.RAMP_DRAGON)
# collect hard positions
positions = []
for g in range(6):
    state = new_game(pirate, ramp, seed=g) if g % 2 == 0 else new_game(ramp, pirate, seed=g)
    agents = [RandomAgent(2 * g, 0.2), RandomAgent(2 * g + 1, 0.2)]
    last = None
    while not state.over:
        acts = legal_actions(state)
        if state.phase == 1 and state.turn != last and state.turn >= 8:
            last = state.turn
            positions.append(state.clone())
        apply(state, agents[state.active].act(state, acts))
pickle.dump(positions, open("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/positions.pkl", "wb"))
print(len(positions))
pr = cProfile.Profile(); pr.enable()
for s in positions[:40]:
    find_lethal(s, max_nodes=1500)
pr.disable()
pstats.Stats(pr).sort_stats("tottime").print_stats(22)
