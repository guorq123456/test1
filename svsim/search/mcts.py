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
  moves that another order of the same moves always beats are left out
  (search.moves: evolving a follower after its attack);
- the squash is centred on the position the search starts from (scored the same
  way): it compares how much better or worse each line leaves things, so an
  evaluation that thinks the game is already won or lost (scores far from 0,
  where the squash is flat) still tells a good line from a bad one;
- values back up as the best of the player's own choices, averaged over luck:
  inside one's own turn there is no opponent, so a move is worth the best that
  can follow it, not the average of everything tried after it (which made moves
  that pay off only with the right follow-up, evolving before attacking,
  playing cheap cards for Combo, returning a card to play it again, look worse
  than ending the turn). A node remembers which moves were open at it in each
  determinization (hidden cards and random results can change them) and is
  worth, averaged over those, the best current estimate among the open moves;
  a node nothing was searched below is worth the average of its evaluations.
  Luck is averaged, never maximised (`backup="mean"`: the plain average of
  everything below, as before);
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
from svsim.search.moves import reserved, worth_trying


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


_PAYOFF: dict = {}


def _combo_payoff(defn) -> bool:
    """Whether the card does more when played later in the turn (Combo): Sprouting
    Initiate draws only at Combo 3. The player's drew a card 23 times in 22 plays,
    the AI's 27 in 58, playing it first."""
    hit = _PAYOFF.get(defn.card_id)
    if hit is None:
        from svsim.search.combo import at_combo, profile
        hit = False
        for v in profile(defn):
            lo, hi = at_combo(v, 1), at_combo(v, 3)
            if (hi.drawn, len(hi.added), hi.face, hi.hit) > (lo.drawn, len(lo.added), lo.face, lo.hit):
                hit = True
        _PAYOFF[defn.card_id] = hit
    return hit


def _rank(state: GameState, action) -> tuple:
    if isinstance(action, Attack):
        if action.target < 0:
            attacker = state.on_field(action.attacker)
            return 0, -(attacker.atk if attacker else 0)
        return 4, 0
    if isinstance(action, PlayCard):
        card = state.in_hand(state.active, action.uid)
        if card is not None and state.players[state.active].combo < 2 and _combo_payoff(card.defn):
            return 1, 1              # a Combo card is better played after others: tried after them
        return 1, 0
    if isinstance(action, Evolve):
        return 2, 0
    if isinstance(action, EndTurn):
        return 5, 0
    return 3, 0


class Node:
    __slots__ = ("children", "visits", "total", "avail", "options", "value")

    def __init__(self):
        self.children: dict = {}
        self.visits = 0
        self.total = 0.0               # sum of leaf evaluations (a node not yet searched below)
        self.avail = 0
        self.options = None            # {frozenset of open moves: times seen} once searched below
        self.value = 0.0               # the node's estimate (see ISMCTS._refresh)


class ISMCTS:
    def __init__(self, iterations: int = 400, seconds: float | None = None, c: float = 0.5,
                 scale: float = 8.0, max_depth: int = 30, seed: int = 0, weights=DEFAULT,
                 reply: bool = False, center: bool = True, prune: bool = True, backup: str = "max",
                 reserve: bool = False, veto=None, reply_after: int = 0):
        self.iterations = iterations   # per decision (or until `seconds` have passed)
        self.seconds = seconds
        self.c = c                     # exploration constant (values are in 0..1)
        self.scale = scale             # evaluation points per unit of the logistic squash
        self.max_depth = max_depth
        self.rng = random.Random(seed)
        self.weights = weights
        self.reply = reply             # play out the opponent's next turn at the leaves
        self.reply_after = reply_after # ... only at a turn-end leaf visited this many times already
                                       # (before that it is scored as it stands: learn.net scores both)
        self.centered = center         # squash relative to the starting position (False: absolute)
        self.prune = prune             # leave out dominated moves (search.moves)
        self.reserve = reserve         # keep the win condition for finishing turns (search.moves.reserved)
        self.veto = veto               # veto(state, action) -> True to leave the action out (e.g. learn.timing.Pace)
        if backup not in ("max", "mean"):
            raise ValueError(f"unknown backup {backup!r}")
        self.backup = backup           # "max": best own choice, luck averaged; "mean": plain average
        self.center = 0.0              # score of the position the search started from
        self.last_root: Node | None = None
        if reply:
            from svsim.agents.greedy_agent import GreedyAgent
            self.opponent = GreedyAgent(seed=seed + 1, samples=1, weights=weights)

    def value(self, state: GameState, me: int, me_next: bool = False) -> float:
        score = evaluate(state, me, self.weights, player_moves_next=me_next) - self.center
        return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, score / self.scale))))

    def choose(self, state: GameState):
        me, root = state.active, Node()
        self.center = 0.0
        if self.centered:
            self.center = evaluate(state, me, self.weights)
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
        offered = []                     # the moves open at each node on the path, this determinization
        while not s.over and s.active == me and depth < self.max_depth:
            where = _locator(s, me)
            options = {}
            legal = legal_actions(s)
            if self.reserve:
                legal = [a for a in legal if not reserved(s, a)] or legal
            if self.veto is not None:
                legal = [a for a in legal if not self.veto(s, a)] or legal
            for a in sorted(worth_trying(s, legal) if self.prune else legal, key=lambda a: _rank(s, a)):
                options.setdefault(action_key(s, a, where), a)
            offered.append(options)
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
                ucb = self.estimate(child) + self.c * math.sqrt(math.log(child.avail) / child.visits)
                if ucb > best_ucb:
                    best, best_ucb = k, ucb
            node = node.children[best]
            self._step(s, options[best])
            path.append(node)
            depth += 1
        me_next = False
        if self.reply and not s.over and s.active != me and path[-1].visits >= self.reply_after:
            _start_turn(s)                       # the opponent's turn, played greedily
            while not s.over and s.active != me:
                apply(s, self.opponent.act(s, legal_actions(s)))
            me_next = not s.over
        v = self.value(s, me, me_next)
        if self.backup == "mean":
            for n in path:
                n.visits += 1
                n.total += v
            return
        leaf = path[-1]
        leaf.visits += 1
        leaf.total += v
        self._refresh(leaf)
        for n, options in zip(reversed(path[:-1]), reversed(offered)):
            n.visits += 1
            if n.options is None:
                n.options = {}
            seen = frozenset(options)
            n.options[seen] = n.options.get(seen, 0) + 1
            self._refresh(n)

    def estimate(self, node: Node) -> float:
        """A node's value as this search backs up (see `backup`)."""
        return node.value if self.backup == "max" else node.total / node.visits

    @staticmethod
    def _refresh(node: Node) -> None:
        """A node's estimate: over the sets of moves open at it (weighted by how
        often each was seen), the best current estimate among the open moves;
        the average evaluation if nothing was searched below it yet."""
        if not node.options:
            node.value = node.total / node.visits
            return
        total = count = 0
        for moves, times in node.options.items():
            values = [node.children[k].value for k in moves if k in node.children and node.children[k].visits]
            if values:
                total += times * max(values)
                count += times
        node.value = total / count if count else node.total / max(node.visits, 1)

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
