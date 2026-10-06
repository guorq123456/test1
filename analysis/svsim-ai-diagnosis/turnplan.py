"""A whole-turn planner agent (experiment, not part of svsim).

At each decision: on K determinizations (hidden cards reshuffled, fresh RNG,
so no peeking), search every order of this turn's actions depth-first with a
transposition table (dominated moves pruned by search.moves) and score the
end of the turn with the evaluation. Each
first action gets the best value reachable after it (max, not mean: there is
no adversary inside one's own turn), averaged over the determinizations; the
best first action is played, and the planner runs again at the next decision.
"""
from svsim.cards import library as _lib, decks as _decks  # register every card script
import random
from svsim.agents.greedy_agent import mulligan
from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Phase
from svsim.core.view import determinize
from svsim.search.evaluate import DEFAULT, WIN, after_end_of_turn, evaluate
from svsim.search.lethal import state_key
from svsim.search.mcts import _locator, action_key
from svsim.search.moves import worth_trying


class TurnPlanner:
    def __init__(self, weights=DEFAULT, samples=3, budget=4000, seed=0):
        self.w, self.samples, self.budget = weights, samples, budget
        self.rng = random.Random(seed)

    def _end(self, s, me):
        if s.over:
            return WIN if s.winner == me else -WIN
        return evaluate(after_end_of_turn(s), me, self.w)

    def _best(self, s, me, tt, nodes):
        if s.over:
            return WIN if s.winner == me else -WIN
        if s.active != me:
            return evaluate(s, me, self.w)
        k = state_key(s)
        if k in tt:
            return tt[k]
        nodes[0] += 1
        best = self._end(s, me)
        if nodes[0] < self.budget:
            for a in worth_trying(s, legal_actions(s)):
                if isinstance(a, EndTurn):
                    continue
                t = s.clone(); apply(t, a)
                best = max(best, self._best(t, me, tt, nodes))
        tt[k] = best
        return best

    def choose(self, state):
        me = state.active
        where = _locator(state, me)
        legal = {action_key(state, a, where): a for a in legal_actions(state)}
        total = {k: 0.0 for k in legal}
        count = {k: 0 for k in legal}
        for _ in range(self.samples):
            s = determinize(state, me, self.rng)
            w2 = _locator(s, me)
            tt, nodes = {}, [0]
            for a in legal_actions(s):
                k = action_key(s, a, w2)
                if k not in total:
                    continue
                if isinstance(a, EndTurn):
                    v = self._end(s, me)
                else:
                    t = s.clone(); apply(t, a)
                    v = self._best(t, me, tt, nodes)
                total[k] += v; count[k] += 1
        best = max((k for k in legal if count[k]), key=lambda k: total[k] / count[k], default=None)
        return legal[best] if best is not None else next(iter(legal.values()))


class TurnPlanAgent:
    def __init__(self, **kw):
        self.search = TurnPlanner(**kw)

    def act(self, state, actions):
        if state.phase != Phase.MAIN:
            return mulligan(state)
        if len(actions) == 1:
            return actions[0]
        return self.search.choose(state)


def make(spec, seed):
    """'turnplan[:budget][+learned][+plan]' or any tools.arena spec; '#label' is ignored."""
    spec = spec.split("#")[0]
    from svsim.tools.arena import make_agent
    if spec.startswith("mctsmax"):
        from svsim.agents.lethal_agent import LethalAgent
        from variants import MaxISMCTS, Agent
        head, *opts = spec.split("+")
        w = DEFAULT
        if "learned" in opts:
            from svsim.learn.model import Learned
            w = Learned(fallback=DEFAULT)
        return LethalAgent(Agent(MaxISMCTS(iterations=int(head.partition(":")[2] or 200), seed=seed, weights=w)),
                           seed=seed, planner="plan" in opts)
    if not spec.startswith("turnplan"):
        return make_agent(spec, seed)
    from svsim.agents.lethal_agent import LethalAgent
    head, *opts = spec.split("+")
    budget = int(head.partition(":")[2] or 4000)
    w = DEFAULT
    if "learned" in opts:
        from svsim.learn.model import Learned
        w = Learned(fallback=DEFAULT)
    return LethalAgent(TurnPlanAgent(weights=w, budget=budget, seed=seed), seed=seed, planner="plan" in opts)
