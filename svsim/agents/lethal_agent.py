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


# The budget for a screened position whose estimate is short of the opponent's defense by 4 or less (the
# architecture session, 2026-10-07): in the smoke games all eight screen misses that 1,000 nodes find were
# 1 to 4 short; it costs 7.8% more time per turn (90th percentile +9.8%), about 0.3 points of win rate by the
# planner's rate of iterations to strength, against about 1 to 1.5 points from the lethals it finds.
NEAR = (1000, 4)


class LethalAgent:
    """`screen`: node budget for positions whose damage estimate falls short of the
    opponent's defense (see search.lethal); None searches every position fully. `near`:
    (nodes, K), the budget instead when the estimate is short by K or less (NEAR; None: off)."""

    def __init__(self, base, max_nodes: int = 2000, screen: int | None = 200, seed: int = 0,
                 near: tuple[int, int] | None = NEAR,
                 planner: bool = False, plan_nodes: int = 20000, trust_planner: bool = False,
                 macro: bool = False, burst: bool = False, burst_reply: int = 0, dig: bool = False,
                 tickers: bool = False):
        self.base = base
        self.search = LethalSearch(max_nodes=max_nodes, screen=screen, seed=seed, near=near)
        self.planner, self.plan_nodes, self.trust_planner = planner, plan_nodes, trust_planner
        self.tickers = tickers           # the planner models allied countdown amulets (search.combo, ticker_profile)
        self.plan: list = []
        self.plan_turn = None
        self.checked = None          # (turn, hidden info) of the last search without a lethal
        self.lethals = 0             # sure lethals found (for statistics)
        self.planned = 0             # ... of them found by the planner
        self.macro = macro
        self.burst = burst           # play the most-damage line when it sets up next turn's kill
        self.burst_reply = burst_reply   # ... and it still does after this many sampled opponent turns
        self.bursts = 0
        self.burst_checked = None
        self.dig = dig               # on setup turns, follow the planner's line that draws the most
        self.dig_slack = 0.1         # ... unless the search rates its own best move this much higher (0..1);
                                     # None: whenever it doesn't leave the leader in reach of the enemy board
        self.digs = 0
        self.macro_checked = None    # stamp of the last turn state the macro line was weighed on
        self.macros = 0              # macro lines played
        self.rng = random.Random(seed)

    def _veto(self):
        """The wrapped search's veto (search.mcts.ISMCTS.veto: a restriction such as crossturn_agent's keep:<card>),
        if any. A line this agent plays must obey it too, or a kept card goes out in a lethal line (the analysis
        line, 2026-10-09: 15 of 400 validation items)."""
        agent = self.base
        for _ in range(4):
            search = getattr(agent, "search", None)
            veto = getattr(search, "veto", None)
            if veto is not None:
                return veto
            agent = getattr(agent, "base", None)
            if agent is None:
                break
        return None

    def act(self, state, actions):
        if state.phase != Phase.MAIN:
            return self.base.act(state, actions)
        veto = self._veto()
        if veto is None:
            return self._act(state, actions)
        step = self._act(state, actions)                # a line's step the restriction forbids: the search decides
        if step is not None and veto(state, step):
            self.plan = []
            return self.base.act(state, actions)
        return step

    def _act(self, state, actions):
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
        if self.burst and progress != self.burst_checked:
            self.burst_checked = progress
            line = self._burst_line(state, actions)
            if line:
                self.bursts += 1
                self.plan, self.plan_turn = list(line[1:]), state.turn
                return combo.listed(state, line[0], actions)
        if self.dig and progress != self.macro_checked:
            self.macro_checked = progress
            line = self._dig_line(state, actions)
            if line:
                self.digs += 1
                self.plan, self.plan_turn = list(line[1:]), state.turn
                return combo.listed(state, line[0], actions)
            return self.base_choice
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

    def _dig_line(self, state, actions) -> list:
        """The planner's most-drawing line (finishers kept), if it draws two cards or
        more and the search's evaluation rates its end no worse than its own best
        move (kept in `base_choice`)."""
        from svsim.search.moves import finisher
        self.base_choice = self.base.act(state, actions)
        search = getattr(self.base, "search", None)
        root = getattr(search, "last_root", None)
        if root is None or not root.children:
            return []
        keep = {c.defn.card_id for c in state.players[state.active].hand if finisher(c.defn)}
        p = combo.dig(state, keep)
        if p.damage < 2 or not p.steps:
            return []
        line = None
        for n in range(len(p.steps), 0, -1):
            line = combo.realize(state, p.steps[:n])
            if line:
                break
        if not line or combo.listed(state, line[0], actions) is None:
            return []
        s = determinize(state, state.active, self.rng)
        for a in line:
            if s.over:
                break
            if not combo._legal(s, a):
                return []
            apply(s, a)
        if s.over:
            return line if s.winner == state.active else []
        end = after_end_of_turn(s)
        if self.dig_slack is None:                   # dig unless it leaves the leader in reach of the enemy board
            from svsim.search.evaluate import threat
            return line if end.over or threat(end, 1 - state.active) < end.players[state.active].leader_hp else []
        best = max(root.children.values(), key=lambda n: n.visits)
        return line if search.value(end, state.active) >= search.estimate(best) - self.dig_slack else []

    def _burst_line(self, state, actions) -> list:
        """The planner's most-damage line, when playing it now means the kill comes
        next turn by the race clock and holding doesn't (the player's two-turn
        finish: 15 damage now, 5 next turn), judged without seeing hidden cards."""
        from svsim.search import race
        me = state.active
        p = combo.plan(state, self.plan_nodes)
        if p.damage <= 0 or not p.steps:
            return []
        line = combo.realize(state, p.steps)
        if not line or combo.listed(state, line[0], actions) is None:
            return []
        s = determinize(state, me, self.rng)
        held = after_end_of_turn(s.clone())
        for a in line:
            if s.over:
                break
            if not combo._legal(s, a):
                return []
            apply(s, a)
        if s.over:
            return line if s.winner == me else []
        after = after_end_of_turn(s)
        if after.over or race.clock(after, me, horizon=1).turns != 0:
            return []
        if race.clock(held, me, horizon=1).turns == 0:
            return []
        if self.burst_reply:
            # The opponent gets a turn in between (healing, Ward, removal): the kill
            # must survive it in every sample, the opponent played by a greedy agent.
            from svsim.agents.greedy_agent import GreedyAgent
            from svsim.search.impact import reply
            for k in range(self.burst_reply):
                t = determinize(s, me, self.rng)
                t, _ = reply(t, me, GreedyAgent(seed=k, samples=1))
                if t.over:
                    if t.winner != me:
                        return []
                    continue
                if race.clock(t, me, horizon=0).turns != 0:
                    return []
        return line

    def _planned(self, state) -> tuple[list, bool]:
        """(the planner's checked lethal line or [], whether the model rules lethal out)."""
        if not self.planner:
            return [], False
        hp = state.players[1 - state.active].leader_hp
        p = combo.plan(state, self.plan_nodes, tickers=self.tickers)
        if p.damage >= hp and p.steps:
            line = combo.realize(state, p.steps, face_first=p.tickers)
            if line and combo.verify(state, line):
                self.planned += 1
                return line, False
        return [], self.trust_planner and p.damage < hp
