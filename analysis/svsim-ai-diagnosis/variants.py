"""Max-backup ISMCTS on top of the current search (centring and pruning kept)."""
from svsim.cards import library as _lib, decks as _decks  # register every card script
import math
from svsim.core.engine import apply, legal_actions
from svsim.core.view import determinize
from svsim.search.evaluate import evaluate
from svsim.search.mcts import ISMCTS, Node, _locator, _rank, action_key
from svsim.search.moves import worth_trying


class MaxISMCTS(ISMCTS):
    """Nodes keep the best leaf value seen below them instead of the mean: inside
    one's own turn there is no adversary, so a move is worth its best follow-up."""

    def choose(self, state):
        me, root = state.active, Node()
        self.center = evaluate(state, me, self.weights) if self.centered else 0.0
        for _ in range(self.iterations):
            self._iterate(determinize(state, me, self.rng), me, root)
        self.last_root = root
        where = _locator(state, me)
        legal = {action_key(state, a, where): a for a in legal_actions(state)}
        best = max((k for k in legal if k in root.children), key=lambda k: root.children[k].total, default=None)
        return legal[best] if best is not None else next(iter(legal.values()))

    def _iterate(self, s, me, root):
        node, path, depth = root, [root], 0
        while not s.over and s.active == me and depth < self.max_depth:
            where = _locator(s, me)
            options = {}
            legal = legal_actions(s)
            for a in sorted(worth_trying(s, legal) if self.prune else legal, key=lambda a: _rank(s, a)):
                options.setdefault(action_key(s, a, where), a)
            fresh = None
            for k in options:
                child = node.children.get(k)
                if child is None:
                    if fresh is None:
                        fresh = k
                else:
                    child.avail += 1
            if fresh is not None:
                child = node.children[fresh] = Node()
                child.avail = 1
                self._step(s, options[fresh])
                path.append(child)
                break
            best, best_ucb = None, -1.0
            for k in options:
                child = node.children[k]
                ucb = child.total + self.c * math.sqrt(math.log(child.avail) / child.visits)
                if ucb > best_ucb:
                    best, best_ucb = k, ucb
            node = node.children[best]
            self._step(s, options[best])
            path.append(node)
            depth += 1
        v = self.value(s, me, False)
        for n in path:
            n.total = v if n.visits == 0 else max(n.total, v)
            n.visits += 1


class Agent:
    def __init__(self, search):
        self.search = search

    def act(self, state, actions):
        from svsim.agents.greedy_agent import mulligan
        from svsim.core.enums import Phase
        if state.phase != Phase.MAIN:
            return mulligan(state)
        if len(actions) == 1:
            return actions[0]
        return self.search.choose(state)
