"""Agents for the centring check on the svsim whole-turn planner (search.turnplan, 14aee57).

    PYTHONPATH=<svsim at 14aee57 or later>:. python duel.py turn:3000+plan+learned mcts:200+plan+learned mirror 200 11
    (duel.py imports `make` from turnplan; for this check, point it at centering_check instead)


'tpc:N' is the repo's TurnPlanAgent with one change: the logistic squash is centred
on the position the plan starts from (as ISMCTS does since ad12b71), so chance
nodes average win probabilities around 0.5 instead of in the flat, saturated
tails of an over-confident evaluation. Anything else goes to tools.arena.
"""
from svsim.cards import library as _lib, decks as _decks  # register every card script
import math
from svsim.search.evaluate import DEFAULT, evaluate
from svsim.search.turnplan import TurnPlanAgent, TurnPlanner


class CenteredTurnPlanner(TurnPlanner):
    def plan(self, state):
        self.center = evaluate(state, state.active, self.weights)
        return super().plan(state)

    def _value(self, state):
        if state.winner is not None:
            return 1.0 if state.winner == self.me else 0.0 if state.winner == 1 - self.me else 0.5
        score = evaluate(state, self.me, self.weights) - self.center
        return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, score / self.scale))))


def make(spec, seed):
    spec = spec.split("#")[0]
    from svsim.tools.arena import make_agent
    if not spec.startswith("tpc"):
        return make_agent(spec, seed)
    from svsim.agents.lethal_agent import LethalAgent
    head, *opts = spec.split("+")
    w = DEFAULT
    if "learned" in opts:
        from svsim.learn.model import Learned
        w = Learned(fallback=DEFAULT)
    agent = TurnPlanAgent(int(head.partition(":")[2] or 5000), seed=seed, weights=w)
    agent.planner.__class__ = CenteredTurnPlanner
    return LethalAgent(agent, seed=seed, planner="plan" in opts)
