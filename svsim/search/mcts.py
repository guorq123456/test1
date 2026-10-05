"""Information Set Monte Carlo Tree Search (single observer) over one turn.

The searching player can't see the opponent's hand, the deck order or future
random results. Each iteration therefore starts from a fresh determinization
(view.determinize: those unknowns reshuffled into one possible arrangement)
and walks one shared tree:

- tree nodes are the searching player's action sequences this turn; actions
  are matched across determinizations by an abstract key (card ids and
  positions instead of uids, see `action_key`), so a node's children are the
  actions seen so far, each with the number of times it was available;
- selection uses UCB with availability counts (ISMCTS): an action is only
  compared in the iterations where it was legal;
- a new action is expanded in the order a player would try them (attacks on the
  leader, then cards, evolutions, other actions, attacks on followers, ending
  the turn), then the position is scored with `evaluate`, squashed to 0..1;
- ending the turn resolves end-of-turn abilities but not the opponent's turn;
  `evaluate` looks ahead to it through its danger term. With `reply=True` the
  opponent's next turn is played out instead, by a greedy agent holding the
  determinized hand, and the position is scored at the start of the searching
  player's next turn.

The move played is the most visited root action. Lethal is better left to the
exact lethal search (agents wrap this one in LethalAgent).
"""
from __future__ import annotations

import math
import random
import time

from svsim.core.actions import (Attack, EndTurn, Engage, Evolve, Fuse, PlayCard, UseBonusPP)
from svsim.core.engine import _start_turn, apply, legal_actions
from svsim.core.enums import DRAW, Phase
from svsim.core.state import GameState, leader_of
from svsim.core.view import determinize
from svsim.search.evaluate import DEFAULT, evaluate


def _locator(state: GameState, me: int) -> dict:
    """uid -> a key that identifies the card the same way in every determinization."""
    where = {}
    for p in state.players:
        mine = p.index == me
        for i, c in enumerate(p.field):
            where[c.uid] = ("F", mine, i, c.defn.card_id)
        for c in p.hand:
            where[c.uid] = ("H", mine, c.defn.card_id, c.cost)
        for c in p.leader_area:
            where[c.uid] = ("C", mine, c.defn.card_id)
    return where


def action_key(state: GameState, action, where: dict | None = None) -> tuple:
    """An action described by card ids and positions rather than uids."""
    me = state.active
    where = where if where is not None else _locator(state, me)

    def loc(uid):
        side = leader_of(uid)
        return ("L", side == me) if side is not None else where.get(uid, ("?", uid))

    def locs(uids):
        return tuple(loc(u) for u in uids)
    if isinstance(action, PlayCard):
        return ("P", loc(action.uid), locs(action.targets), action.modes)
    if isinstance(action, Attack):
        return ("A", loc(action.attacker), loc(action.target))
    if isinstance(action, Evolve):
        return ("E", loc(action.uid), action.super_, locs(action.targets), action.modes)
    if isinstance(action, Engage):
        return ("G", loc(action.uid), locs(action.targets), action.modes)
    if isinstance(action, Fuse):
        return ("U", loc(action.uid), tuple(sorted(locs(action.cards))))
    if isinstance(action, UseBonusPP):
        return ("B",)
    return ("T",)


def _rank(state: GameState, action) -> tuple:
    if isinstance(action, Attack):
        if action.target < 0:
            attacker = state.on_field(action.attacker)
            return 0, -(attacker.atk if attacker else 0)
        return 4, 0
    if isinstance(action, PlayCard):
        return 1, 0
    if isinstance(action, Evolve):
        return 2, 0
    if isinstance(action, EndTurn):
        return 5, 0
    return 3, 0


class Node:
    __slots__ = ("children", "visits", "total", "avail")

    def __init__(self):
        self.children: dict = {}
        self.visits = 0
        self.total = 0.0
        self.avail = 0


class ISMCTS:
    def __init__(self, iterations: int = 400, seconds: float | None = None, c: float = 0.5,
                 scale: float = 8.0, max_depth: int = 30, seed: int = 0, weights=DEFAULT,
                 reply: bool = False):
        self.iterations = iterations   # per decision (or until `seconds` have passed)
        self.seconds = seconds
        self.c = c                     # exploration constant (values are in 0..1)
        self.scale = scale             # evaluation points per unit of the logistic squash
        self.max_depth = max_depth
        self.rng = random.Random(seed)
        self.weights = weights
        self.reply = reply             # play out the opponent's next turn at the leaves
        self.last_root: Node | None = None
        if reply:
            from svsim.agents.greedy_agent import GreedyAgent
            self.opponent = GreedyAgent(seed=seed + 1, samples=1, weights=weights)

    def value(self, state: GameState, me: int, me_next: bool = False) -> float:
        score = evaluate(state, me, self.weights, player_moves_next=me_next)
        return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, score / self.scale))))

    def choose(self, state: GameState):
        me, root = state.active, Node()
        deadline = time.perf_counter() + self.seconds if self.seconds else None
        for i in range(self.iterations if deadline is None else 10 ** 9):
            if deadline is not None and time.perf_counter() > deadline and i > 0:
                break
            self._iterate(determinize(state, me, self.rng), me, root)
        self.last_root = root
        where = _locator(state, me)
        legal = {action_key(state, a, where): a for a in legal_actions(state)}
        best = max((k for k in legal if k in root.children),
                   key=lambda k: root.children[k].visits, default=None)
        return legal[best] if best is not None else next(iter(legal.values()))

    def _iterate(self, s: GameState, me: int, root: Node) -> None:
        node, path, depth = root, [root], 0
        while not s.over and s.active == me and depth < self.max_depth:
            where = _locator(s, me)
            options = {}
            for a in sorted(legal_actions(s), key=lambda a: _rank(s, a)):
                options.setdefault(action_key(s, a, where), a)
            fresh = None
            for k in options:
                child = node.children.get(k)
                if child is None:
                    if fresh is None:
                        fresh = k
                else:
                    child.avail += 1
            if fresh is not None:                       # expand the first untried action
                child = node.children[fresh] = Node()
                child.avail = 1
                self._step(s, options[fresh])
                path.append(child)
                break
            best, best_ucb = None, -1.0
            for k in options:
                child = node.children[k]
                ucb = child.total / child.visits + self.c * math.sqrt(
                    math.log(child.avail) / child.visits)
                if ucb > best_ucb:
                    best, best_ucb = k, ucb
            node = node.children[best]
            self._step(s, options[best])
            path.append(node)
            depth += 1
        me_next = False
        if self.reply and not s.over and s.active != me:
            _start_turn(s)                       # the opponent's turn, played greedily
            while not s.over and s.active != me:
                apply(s, self.opponent.act(s, legal_actions(s)))
            me_next = not s.over
        v = self.value(s, me, me_next)
        for n in path:
            n.visits += 1
            n.total += v

    @staticmethod
    def _step(s: GameState, action) -> None:
        if not isinstance(action, EndTurn):
            apply(s, action)
            return
        real_limit = s.max_turns
        s.max_turns = s.turn             # resolve the end of turn, but don't start the next one
        apply(s, action)
        if s.winner == DRAW and s.turn <= real_limit:
            s.winner, s.phase = None, Phase.MAIN
        s.max_turns = real_limit
