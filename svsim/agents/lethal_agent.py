"""An agent that never misses a lethal it can find.

It wraps another agent. Before each decision it runs the lethal search; when
the search finds a sure lethal it plays the line out, otherwise the wrapped
agent decides.

The search is skipped when it can't find anything new: once a full search
found no sure lethal, actions whose results don't depend on luck or hidden
cards can't create one (the search already looked past them), so it only runs
again on a new turn or after a draw or random effect. (After a search that ran
out of budget this is a shortcut, not a guarantee.)
"""
from svsim.core.enums import Phase
from svsim.search.lethal import LethalSearch, hidden_info


class LethalAgent:
    def __init__(self, base, max_nodes: int = 2000, seed: int = 0):
        self.base = base
        self.search = LethalSearch(max_nodes=max_nodes, seed=seed)
        self.plan: list = []
        self.plan_turn = None
        self.checked = None          # (turn, hidden info) of the last search without a lethal
        self.lethals = 0             # sure lethals found (for statistics)

    def act(self, state, actions):
        if state.phase != Phase.MAIN:
            return self.base.act(state, actions)
        if self.plan and self.plan_turn == state.turn and self.plan[0] in actions:
            return self.plan.pop(0)
        self.plan = []
        stamp = (state.turn, state.active, hidden_info(state))
        if stamp != self.checked:
            result = self.search.solve(state)
            if result.sure and result.line:
                self.lethals += 1
                self.plan, self.plan_turn = list(result.line[1:]), state.turn
                return result.line[0]
            self.checked = stamp
        return self.base.act(state, actions)
