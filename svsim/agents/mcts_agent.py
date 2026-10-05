"""The full-game agent: ISMCTS for each decision, wrapped so that a sure lethal
found by the exact lethal search is always played."""
from svsim.agents.greedy_agent import mulligan
from svsim.agents.lethal_agent import LethalAgent
from svsim.core.enums import Phase
from svsim.search.mcts import ISMCTS


class MCTSAgent:
    def __init__(self, iterations: int = 400, seconds: float | None = None, seed: int = 0, **options):
        self.search = ISMCTS(iterations=iterations, seconds=seconds, seed=seed, **options)

    def act(self, state, actions):
        if state.phase != Phase.MAIN:
            return mulligan(state)
        if len(actions) == 1:
            return actions[0]
        return self.search.choose(state)


def full_game_agent(iterations: int = 400, seconds: float | None = None, seed: int = 0,
                    **options) -> LethalAgent:
    """ISMCTS plus lethal search: the strongest agent so far."""
    return LethalAgent(MCTSAgent(iterations, seconds, seed, **options), seed=seed)
