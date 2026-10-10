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
from svsim.core.state import CHECK as COW_CHECK, GameState, leader_of, sweep, verify_state
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


# alloc=self's prior mean of legal moves at a searched decision (two or more legal moves): 5.83 over the 13388 such
# decisions of analysis/search-sharpness's ramp-t s200 games (300 games, seed 54800000; median 4 as in its table).
SELF_M0 = 5.83


class ISMCTS:
    def __init__(self, iterations: int = 400, seconds: float | None = None, c: float = 0.5,
                 scale: float = 8.0, max_depth: int = 30, seed: int = 0, weights=DEFAULT,
                 reply: bool = False, center: bool = True, prune: bool = True, backup: str = "max",
                 reserve: bool = False, veto=None, reply_after: int = 0, reply_top: int = 0,
                 reply_budget: int = 0, average: int = 1, prior=None, c_prior: float = 0.3,
                 reuse: bool = False, min_new: int = 20, alloc: tuple | None = None, infer: tuple | None = None,
                 oracle: bool = False, normalize: bool = False):
        self.iterations = iterations   # per decision (or until `seconds` have passed)
        self.normalize = normalize     # (+abs) selection on Q min-max normalized over this search's tree (MuZero):
                                       # with absolute values (center=False) a lost or won position's values sit
                                       # near 0 or 1, and the normalization keeps the selection's resolution
        self._qmin = self._qmax = None
        self.alloc = alloc             # ("legal", K, LO, HI): clip(K x legal moves, LO, HI) per decision instead;
                                       # ("bank", CHUNK, STOP, CAP, HI): see _bank_budget
        self._bank, self._bank_turn = 0, None
        self._seen_n, self._seen_k, self._seen_turn = 0, 0, -1     # alloc=self: this game's searched decisions
        self._cx_turn, self._cx_moves = None, 0   # alloc=complex: this turn and its legal moves at its first search
        self.infer = infer             # (ALPHA, TAU): the opponent's hand drawn by search.infer's weights
        self._hand_weights, self._infer_turn = None, None
        self.oracle = oracle           # an experiment: the opponent's real hand in every determinization (core.view)
        self.last_iterations = None    # the iterations the last decision searched
        self.seconds = seconds
        self.c = c                     # exploration constant (values are in 0..1)
        self.scale = scale             # evaluation points per unit of the logistic squash
        self.max_depth = max_depth
        self.rng = random.Random(seed)
        self.weights = weights
        self.reply = reply             # play out the opponent's next turn at the leaves
        self.reply_after = reply_after # ... only at a turn-end leaf visited this many times already
                                       # (before that it is scored as it stands: learn.net scores both)
        self.reply_top = reply_top     # ... only below the root's this many most-visited moves (0: all)
        self.reply_budget = reply_budget   # ... at most this many times per decision (0: no limit)
        self._replies = 0
        self.prior = prior             # prior.priors(state, legal) -> probabilities (learn.policy), at the root
        self.c_prior = c_prior         # weight of the prior's bonus: c * P * sqrt(root visits) / (1 + visits)
        self._root_prior: dict = {}
        self.average = average         # score a leaf as the mean over this many draws of the cards drawn this turn
        self._root_deck: set = set()   # uids in the player's deck at the root (what a draw this turn came from)
        self.centered = center         # squash relative to the starting position (False: absolute)
        self.reuse = reuse             # keep the chosen move's subtree for the next decision of the turn
        self.min_new = min_new         # ... and search at least this many new iterations there
        self._next = None              # (key of the expected next position, subtree, center) when reusing
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
        score = self._score(state, me, me_next) - self.center
        return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, score / self.scale))))

    def _score(self, state: GameState, me: int, me_next: bool) -> float:
        """The evaluation, averaged over `average` redraws of the cards drawn from the deck this turn
        that are still in hand (an evaluation that reads the hand card by card moves with what was
        drawn, and taking the best own choice at each node would take that luck for a better line)."""
        score = evaluate(state, me, self.weights, player_moves_next=me_next)
        if self.average <= 1 or state.over or me_next:
            return score
        p = state.players[me]
        drawn = [i for i, c in enumerate(p.hand) if c.uid in self._root_deck]
        if not drawn or not p.deck:
            return score
        total = score
        for _ in range(self.average - 1):
            t = state.clone()
            q = t.players[me]
            pool = [q.hand[i] for i in drawn] + q.deck
            self.rng.shuffle(pool)
            for j, i in enumerate(drawn):
                q.hand[i] = pool[j]
            q.deck = pool[len(drawn):]
            total += evaluate(t, me, self.weights, player_moves_next=me_next)
        return total / self.average

    def choose(self, state: GameState):
        """The search's move. While it runs, learn.handvalue knows its root: the cards drawn from here on, and the
        opponent's hand, are unknown to the hand-value student."""
        from svsim.learn.handvalue import root
        with root(state.active, [c.uid for c in state.players[state.active].deck_view()]):
            return self._choose(state)

    def _choose(self, state: GameState):
        me, root = state.active, None
        if self.reuse and self._next is not None:
            from svsim.search.lethal import state_key
            key, subtree, center = self._next
            if key == state_key(state):            # the move was played and nothing hidden came out
                root, self.center = subtree, center
        self._next = None
        iterations = self.iterations
        if self.alloc is not None and self.alloc[0] == "legal":    # the same compute on average, given by moves
            _, k, lo, hi = self.alloc
            iterations = min(hi, max(lo, round(k * len(legal_actions(state)))))
        if self.alloc is not None and self.alloc[0] == "self":
            iterations = self._self_budget(state, me)
        if self.alloc is not None and self.alloc[0] == "complex":
            iterations = self._complex_budget(state, me)
        banked = self.alloc is not None and self.alloc[0] == "bank"
        if banked:
            iterations = self._bank_budget(state, me)
        full = iterations
        if self.normalize:
            self._qmin = self._qmax = None          # each search normalizes over its own tree
        if root is None:
            root = Node()
            self.center = 0.0
            if self.centered:
                self.center = evaluate(state, me, self.weights)
        else:                                      # the subtree's values keep the turn start's centre
            iterations = max(self.min_new, full - root.visits)
        deadline = time.perf_counter() + self.seconds if self.seconds else None
        self._replies = 0
        self._root_deck = {c.uid for c in state.players[me].deck_view()}
        self._root_prior = {}
        if self.prior is not None:
            moves = legal_actions(state)
            probs = self.prior.priors(state, moves)
            if probs is not None:
                where0 = _locator(state, me)
                for a, pr in zip(moves, probs):
                    key = action_key(state, a, where0)
                    self._root_prior[key] = self._root_prior.get(key, 0.0) + float(pr)
        hand = None
        if self.infer is not None:                 # once per turn, on its first decision (search.infer)
            turn = (me, state.players[me].turns_taken)
            if turn != self._infer_turn:
                from svsim.search.infer import unplayed_weights
                self._hand_weights, self._infer_turn = unplayed_weights(state, me, *self.infer, self.weights), turn
            hand = self._hand_weights
        done = 0
        for i in range(iterations if deadline is None else 10 ** 9):
            if deadline is not None and time.perf_counter() > deadline and i > 0:
                break
            if self.oracle:
                s = determinize(state, me, self.rng, oracle=True)
            else:
                s = determinize(state, me, self.rng, hand) if hand else determinize(state, me, self.rng)
            self._iterate(s, me, root)
            if COW_CHECK:                          # check mode (core.state): no shared deck card changed
                verify_state(state)
            done += 1
            if banked and done % self.alloc[1] == 0 and self._settled(root, iterations - done):
                break
        if banked:                                 # what this decision didn't use, for the turn's later ones
            self._bank = min(self.alloc[3], max(0, self._bank + self.iterations - done))
        self.last_iterations = done
        self.last_root = root
        if COW_CHECK:
            sweep(keep=state)
        where = _locator(state, me)
        legal = {action_key(state, a, where): a for a in legal_actions(state)}
        best = max((k for k in legal if k in root.children),
                   key=lambda k: root.children[k].visits, default=None)
        if best is None:
            return next(iter(legal.values()))
        if self.reuse and not isinstance(legal[best], EndTurn):
            self._expect(state, legal[best], root.children[best])
        return legal[best]

    def _complex_budget(self, state: GameState, me: int) -> int:
        """+complex (alloc=complex:K:BETA:LO:HI; the architecture thread 2026-10-10 08:58Z): compute moved to the
        complex turns. clip(round(K x max(n, BETA x n0)), LO, HI), n this decision's legal moves and n0 those at
        the turn's first searched decision: a turn that starts wide keeps a share of its budget on its later, narrower
        decisions (the operations puzzle k 518 loses at its second decision). K is set so a game's mean compute is
        level-strong's (analysis/puzzles3)."""
        _, k, beta, lo, hi = self.alloc
        n = len(legal_actions(state))
        if self._cx_turn != (state.turn, me):
            self._cx_turn, self._cx_moves = (state.turn, me), n
        return min(hi, max(lo, round(k * max(n, beta * self._cx_moves))))

    def _self_budget(self, state: GameState, me: int) -> int:
        """Line B1, second try (alloc=self:C:W:LO:HI): clip(round(C x N x n / m), LO, HI), n this decision's legal
        moves and m the mean over this game's earlier searched decisions with a prior of M0 weighing W decisions,
        so the game's iterations average about C x N whatever the deck; C corrects for wide positions costing more
        per iteration (set by tools.search_cost --whole-games). A new game (own turns going back) starts over."""
        _, c, w, lo, hi = self.alloc
        turns = state.players[me].turns_taken
        if turns < self._seen_turn:
            self._seen_n, self._seen_k = 0, 0
        self._seen_turn = turns
        n = len(legal_actions(state))
        m = (SELF_M0 * w + self._seen_n) / (w + self._seen_k)
        self._seen_n, self._seen_k = self._seen_n + n, self._seen_k + 1
        return min(hi, max(lo, round(c * self.iterations * n / m)))

    def _bank_budget(self, state: GameState, me: int) -> int:
        """Line B2: this decision may search the spec's iterations plus what the turn's earlier decisions left
        (the account, at most CAP, emptied when a new turn starts), at most HI; it searches in chunks of CHUNK and
        stops once settled (_settled)."""
        turn = (me, state.players[me].turns_taken)
        if turn != self._bank_turn:
            self._bank, self._bank_turn = 0, turn
        return min(self.alloc[4], self.iterations + self._bank)

    def _settled(self, root: Node, left: int) -> bool:
        """The root's most visited move has STOP of the visits, or the second can't catch it in what is left."""
        visits = sorted((c.visits for c in root.children.values()), reverse=True)
        if not visits or not sum(visits):
            return False
        second = visits[1] if len(visits) > 1 else 0
        return visits[0] >= self.alloc[2] * sum(visits) or visits[0] - second > left

    def _expect(self, state: GameState, action, subtree: Node) -> None:
        """Keep `subtree` for the next decision if `action` reveals nothing (no random numbers, no card
        from a deck): the position after it is then the one every determinization reached."""
        from svsim.search.lethal import hidden_info, state_key
        after = state.clone()
        apply(after, action)
        if hidden_info(after) == hidden_info(state) and not after.over and after.active == state.active:
            self._next = (state_key(after), subtree, self.center)

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
            prior = self._root_prior if depth == 0 and self._root_prior else None
            if prior is not None:                       # the root's moves in the prior's order
                options = dict(sorted(options.items(), key=lambda kv: -prior.get(kv[0], 0.0)))
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
            best, best_ucb = None, -math.inf
            for k in options:
                child = node.children[k]
                q = self.estimate(child)
                if self.normalize and self._qmax is not None and self._qmax - self._qmin > 1e-9:
                    q = (q - self._qmin) / (self._qmax - self._qmin)
                ucb = q + self.c * math.sqrt(math.log(child.avail) / child.visits)
                if prior is not None:
                    ucb += self.c_prior * prior.get(k, 0.0) * math.sqrt(node.visits + 1) / (1 + child.visits)
                if ucb > best_ucb:
                    best, best_ucb = k, ucb
            node = node.children[best]
            self._step(s, options[best])
            path.append(node)
            depth += 1
        me_next = False
        if self.reply and not s.over and s.active != me and self._reply_here(root, path):
            self._replies += 1
            _start_turn(s)                       # the opponent's turn, played greedily
            while not s.over and s.active != me:
                apply(s, self.opponent.act(s, legal_actions(s)))
            me_next = not s.over
        v = self.value(s, me, me_next)
        if self.normalize:
            self._qmin = v if self._qmin is None else min(self._qmin, v)
            self._qmax = v if self._qmax is None else max(self._qmax, v)
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

    def _reply_here(self, root: Node, path: list) -> bool:
        """Whether to play the opponent's turn out at this turn-end leaf (see reply_after, reply_top,
        reply_budget)."""
        if path[-1].visits < self.reply_after:
            return False
        if self.reply_budget and self._replies >= self.reply_budget:
            return False
        if self.reply_top and len(path) > 1:
            first = path[1]
            above = sum(1 for c in root.children.values() if c is not first and c.visits > first.visits)
            if above >= self.reply_top:
                return False
        return True

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
