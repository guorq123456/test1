"""An agent that never misses a lethal it can find.

It wraps another agent. Before each decision it runs the lethal search; when
the search finds a sure lethal it plays the line out, otherwise the wrapped
agent decides.

The search is skipped when it can't find anything new: once a full search
found no sure lethal, actions whose results don't depend on luck or hidden
cards can't create one (the search already looked past them), so it only runs
again on a new turn or after a draw or random effect. (After a search that ran
out of budget this is a shortcut, not a guarantee.)

With `planner`, the resource-flow planner (search.combo) goes first: it finds
the long combo turns exact search drowns in (Rhinoceroach Forest), checked in
the engine. With `trust_planner` too, a turn the planner's resource model
can't make lethal skips the exact search.

With `macro` (and an ISMCTS base agent), the planner also proposes its
most-damage line on turns without lethal: long combo turns (play the cheap
cards, Rhinoceroach, return it, play it again) are deeper than the tree search
sees. The position after the line and the end of the turn is scored with the
search's own evaluation, and the line is played if that beats the search's
best move.
"""
import random

from svsim.core.engine import apply
from svsim.core.enums import Phase
from svsim.core.view import determinize
from svsim.search import combo
from svsim.search.evaluate import after_end_of_turn
from svsim.search.lethal import LethalSearch, hidden_info


class LethalAgent:
    """`screen`: node budget for positions whose damage estimate falls short of the
    opponent's defense (see search.lethal); None searches every position fully."""

    def __init__(self, base, max_nodes: int = 2000, screen: int | None = 200, seed: int = 0,
                 planner: bool = False, plan_nodes: int = 20000, trust_planner: bool = False,
                 macro: bool = False):
        self.base = base
        self.search = LethalSearch(max_nodes=max_nodes, screen=screen, seed=seed)
        self.planner, self.plan_nodes, self.trust_planner = planner, plan_nodes, trust_planner
        self.plan: list = []
        self.plan_turn = None
        self.checked = None          # (turn, hidden info) of the last search without a lethal
        self.lethals = 0             # sure lethals found (for statistics)
        self.planned = 0             # ... of them found by the planner
        self.macro = macro
        self.macro_checked = None    # stamp of the last turn state the macro line was weighed on
        self.macros = 0              # macro lines played
        self.rng = random.Random(seed)

    def act(self, state, actions):
        if state.phase != Phase.MAIN:
            return self.base.act(state, actions)
        if self.plan and self.plan_turn == state.turn:
            step = combo.listed(state, self.plan[0], actions)
            if step is not None:
                self.plan.pop(0)
                return step
        self.plan = []
        stamp = (state.turn, state.active, hidden_info(state))
        if stamp != self.checked:
            line, hopeless = self._planned(state)
            if not line and not hopeless:
                result = self.search.solve(state)
                line = result.line if result.sure else []
            step = combo.listed(state, line[0], actions) if line else None
            if step is not None:
                self.lethals += 1
                self.plan, self.plan_turn = list(line[1:]), state.turn
                return step
            self.checked = stamp
        me = state.players[state.active]
        progress = stamp + (me.pp, len(me.hand), len(me.field))
        if self.macro and progress != self.macro_checked:
            self.macro_checked = progress
            line = self._macro_line(state, actions)
            if line:
                self.macros += 1
                self.plan, self.plan_turn = list(line[1:]), state.turn
                return combo.listed(state, line[0], actions)
            return self.base_choice
        return self.base.act(state, actions)

    def _macro_line(self, state, actions) -> list:
        """The planner's most-damage line if the search's evaluation prefers it to
        the search's own best move (which is kept in `base_choice`)."""
        self.base_choice = self.base.act(state, actions)
        search = getattr(self.base, "search", None)
        root = getattr(search, "last_root", None)
        if root is None or not root.children:
            return []
        p = combo.plan(state, self.plan_nodes)
        if p.damage <= 0 or not p.steps:
            return []
        line = combo.realize(state, p.steps)
        if not line or combo.listed(state, line[0], actions) is None:
            return []
        s = determinize(state, state.active, self.rng)   # judge it without seeing hidden cards
        for a in line:
            if s.over:
                break
            if not combo._legal(s, a):
                return []
            apply(s, a)
        if not s.over:
            s = after_end_of_turn(s)
        best = max(root.children.values(), key=lambda n: n.visits)
        return line if search.value(s, state.active) > search.estimate(best) else []

    def _planned(self, state) -> tuple[list, bool]:
        """(the planner's checked lethal line or [], whether the model rules lethal out)."""
        if not self.planner:
            return [], False
        hp = state.players[1 - state.active].leader_hp
        p = combo.plan(state, self.plan_nodes)
        if p.damage >= hp and p.steps:
            line = combo.realize(state, p.steps)
            if line and combo.verify(state, line):
                self.planned += 1
                return line, False
        return [], self.trust_planner and p.damage < hp
