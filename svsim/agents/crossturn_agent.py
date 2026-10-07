"""Cross-turn planning at the root: whether to keep a card, the bonus play point or the evolution for later.

The one-turn search scores each end of turn as it stands, so keeping a card or
a play point for a better turn later looks like a loss (the 52 regression
positions from the player's Ramp mirror games: no level keeps the second
player's bonus play point on their first turn, 0 of 18; the player always does).
Design stage 2 of the architecture plan (2026-10-07): look past the end of the
turn only for the root's turn-end candidates, with the opponent played by the
learned policy head, not greedily.

At the first decision of each own turn, `CrossTurnAgent`:

1. runs the base search as usual and reads its principal line for the turn
   (the most visited move at each node of the tree, as abstract keys,
   search.mcts.action_key);
2. builds the candidates from that line: the line itself, and the line with
   one restriction for the rest of the turn: keep one of the cards it plays
   (`keep:<card id>`), keep the bonus play point (`save`, if it uses it), don't
   evolve (`noevo`, if it evolves);
3. on each of `samples` determinizations (hidden cards reshuffled, the same
   ones for every candidate: common random numbers), plays the candidate's
   turn (the line's moves the restriction allows, in order, where legal, then
   the policy head's top move among the allowed ones until it ends the turn),
   then the opponent's turn with the policy head's top move (learn.policy:
   fitted to the search's visit counts in self-play), and scores the start of
   the next own turn with the evaluation's ACT model (learn.phased: the moment
   "my turn to act"), as a win probability; candidates are compared on the
   mean (luck averaged, never maximised);
4. keeps the best candidate's restriction for the rest of the turn (the base
   search leaves the restricted moves out, ISMCTS.veto) when it beats the
   unrestricted line by more than `margin`; otherwise the turn is the base
   search's, exactly as without this agent.

The cheap version of the scoring (ACT model at the next turn's start); the
dearer one would play the own next turn by the plan and score its end with the
ENDED model. In matchups without a policy head the agent is the base agent.
"""
from __future__ import annotations

import math
import random

from svsim.core.actions import EndTurn, Evolve, PlayCard, UseBonusPP
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Phase
from svsim.core.view import determinize
from svsim.search.mcts import ISMCTS, _locator, action_key

NONE = "line"


def principal_line(root, max_len: int = 40) -> list:
    """The most visited key at each node from the root down (stops at ending the turn or an unvisited node)."""
    out, node = [], root
    while node is not None and node.children and len(out) < max_len:
        key, child = max(node.children.items(), key=lambda kv: kv[1].visits)
        if child.visits <= 0:
            break
        out.append(key)
        if key == ("T",):
            break
        node = child
    return out


def key_forbidden(restriction: str, key) -> bool:
    """Whether a restriction leaves out a move given by its key (search.mcts.action_key)."""
    if restriction == NONE:
        return False
    if restriction == "save":
        return key == ("B",)
    if restriction == "noevo":
        return key[0] == "E"
    cid = int(restriction.split(":")[1])
    return key[0] == "P" and key[1][0] == "H" and key[1][2] == cid


def restricted_line(root, restriction: str, max_len: int = 40) -> list:
    """The principal line among the moves a restriction allows, from a search's tree as it is (the most
    visited allowed key at each node; no new search)."""
    out, node = [], root
    while node is not None and node.children and len(out) < max_len:
        allowed = [(k, c) for k, c in node.children.items() if not key_forbidden(restriction, k) and c.visits > 0]
        if not allowed:
            break
        key, child = max(allowed, key=lambda kc: kc[1].visits)
        out.append(key)
        if key == ("T",):
            break
        node = child
    return out


def _plain(part):
    """A key's part as JSON-friendly data."""
    return [_plain(x) for x in part] if isinstance(part, tuple) else part


def keep_value(state, player: int, card_uid: int, agent=None, samples: int = 8) -> float | None:
    """What keeping a card in hand this turn is worth, against the search's own line that plays it now:
    the mean, over `samples` determinizations, of (keep it this turn, the opponent's turn by the policy
    head, the own next turn by the policy head, which can play it then; ENDED model) minus (the same
    after the line). A win probability difference; None if the line doesn't play the card (or it isn't
    in `player`'s hand, or it isn't their decision). Hand values come only from such plans
    (docs/architecture.md, §9.2: no fixed value per card)."""
    if state.active != player or state.phase != Phase.MAIN:
        return None
    card = state.in_hand(player, card_uid)
    if card is None:
        return None
    if agent is None:
        from svsim.tools.arena import make_agent
        agent = make_agent("mcts-raw:100+learned+phased", 0)
        agent = CrossTurnAgent(agent, samples=samples, next_turn=True, research=100)
    agent.search.choose(state)
    line = principal_line(agent.search.last_root)
    keep = f"keep:{card.defn.card_id}"
    if keep not in restrictions(line):
        return None
    out = agent.outcomes(state, agent.lines_for(state, line, [NONE, keep]), [NONE, keep])
    return sum(a - b for a, b in zip(out[keep], out[NONE])) / len(out[NONE])


KINDS = ("keep", "save", "noevo")


def restrictions(line: list, kinds=KINDS, max_keeps: int = 0) -> list:
    """The candidates' restrictions for a principal line: none, keep each card it plays, keep the bonus
    play point, don't evolve (only those of `kinds`; with `max_keeps`, keep only the line's that many
    dearest cards)."""
    out = [r for r in _restrictions(line) if r == NONE or r.split(":")[0] in kinds]
    if max_keeps:
        cost = {}
        for key in line:
            if key[0] == "P" and key[1][0] == "H":
                cost[f"keep:{key[1][2]}"] = max(cost.get(f"keep:{key[1][2]}", 0), key[1][3])
        keeps = sorted((r for r in out if r.startswith("keep:")), key=lambda r: -cost.get(r, 0))[:max_keeps]
        out = [r for r in out if not r.startswith("keep:") or r in keeps]
    return out


def _restrictions(line: list) -> list:
    out, kept = [NONE], set()
    for key in line:
        if key[0] == "P" and key[1][0] == "H":
            cid = key[1][2]
            if cid not in kept:
                kept.add(cid)
                out.append(f"keep:{cid}")
    if ("B",) in line:
        out.append("save")
    if any(key[0] == "E" for key in line):
        out.append("noevo")
    return out


def forbids(restriction: str):
    """veto(state, action) for a restriction (None for none)."""
    if restriction == NONE:
        return None
    if restriction == "save":
        return lambda s, a: isinstance(a, UseBonusPP)
    if restriction == "noevo":
        return lambda s, a: isinstance(a, Evolve)
    cid = int(restriction.split(":")[1])

    def keep(s, a):
        if not isinstance(a, PlayCard):
            return False
        card = s.in_hand(s.active, a.uid)
        return card is not None and card.defn.card_id == cid
    return keep


class CrossTurnAgent:
    def __init__(self, base, policy=None, samples: int = 4, margin: float = 0.0, seed: int = 0,
                 max_steps: int = 40, next_turn: bool = False, z: float = 0.0, static: bool = False,
                 research: int = 0, next_search: int = 0, opp_search: int = 0, kinds=KINDS,
                 max_keeps: int = 0):
        self.base = base                     # an MCTSAgent (the lethal search stays outside)
        self.search: ISMCTS = base.search
        if policy is None:
            from svsim.learn.policy import MatchupPrior
            policy = MatchupPrior()
        self.policy = policy
        self.samples = samples
        self.margin = margin                 # a restriction must beat the line by more than this ...
        self.z = z                           # ... and by more than z standard errors of the paired difference
        self.max_steps = max_steps
        self.next_turn = next_turn           # score after the own next turn (policy head) with the ENDED model
        self.static = static                 # control: score each candidate's own turn end (ENDED), no play-out
        self.research = research             # a restriction's turn from a new search with it, this many iterations
                                             # (0: the principal line without the restricted moves; "tree": the
                                             # restricted principal line of the base search's own tree)
        self._roots: dict = {}
        # the play-outs' own next turn / the opponent's turn by a small search of this many iterations
        # (0: the policy head's top move)
        self.next_search, self.opp_search = next_search, opp_search
        self.kinds = tuple(kinds)            # which restrictions to try (KINDS)
        self.max_keeps = max_keeps           # keep at most this many of the line's dearest cards (0: all)
        self._small = {}
        self.rng = random.Random(seed)
        self.turn = None
        self.restriction = NONE
        self._veto = self.search.veto        # the base search's own veto, kept under a restriction
        self.picked: dict = {}               # restriction kind -> turns (statistics)
        self.values: dict = {}
        self.last_plan: dict | None = None   # the last turn start's measurements (learn.netdata records them)

    # --- the play-outs ------------------------------------------------------------------------

    def _top(self, s, allowed):
        if hasattr(self.policy, "top"):
            return self.policy.top(s, allowed)
        probs = self.policy.priors(s, allowed)
        if probs is None:
            return None
        return allowed[max(range(len(allowed)), key=lambda i: probs[i])]

    def _own_turn(self, s, me: int, line: list, veto) -> None:
        for key in line:
            if s.over or s.active != me:
                return
            if key == ("T",):
                break
            where = _locator(s, me)
            match = next((a for a in legal_actions(s) if action_key(s, a, where) == key), None)
            if match is None or (veto is not None and veto(s, match)):
                continue
            apply(s, match)
        for _ in range(self.max_steps):            # the rest of the turn by the policy head
            if s.over or s.active != me:
                return
            legal = legal_actions(s)
            allowed = [a for a in legal if veto is None or not veto(s, a)] or legal
            a = self._top(s, allowed)
            if a is None or isinstance(a, EndTurn):
                return
            apply(s, a)

    def _searcher(self, iterations: int) -> ISMCTS:
        if iterations not in self._small:
            self._small[iterations] = ISMCTS(iterations=iterations, seed=self.rng.getrandbits(32),
                                             weights=self.search.weights)
        return self._small[iterations]

    def _searched_turn(self, s, player: int, iterations: int, end: bool) -> None:
        """`player`'s turn by a small search; ends the turn (starting the next) only if `end`."""
        search = self._searcher(iterations)
        for _ in range(self.max_steps):
            if s.over or s.active != player:
                return
            legal = legal_actions(s)
            a = legal[0] if len(legal) == 1 else search.choose(s)
            if isinstance(a, EndTurn) and not end:
                return
            apply(s, a)

    def _their_turn(self, s, me: int) -> None:
        if not s.over and s.active == me:
            apply(s, EndTurn())
        if self.opp_search and not s.over:
            self._searched_turn(s, 1 - me, self.opp_search, end=True)
            return
        for _ in range(self.max_steps * 2):
            if s.over or s.active == me:
                return
            legal = legal_actions(s)
            a = self._top(s, legal) if len(legal) > 1 else legal[0]
            apply(s, a if a is not None else legal[-1])

    def _ended(self, s, me: int) -> float:
        """The end of the own turn as the one-turn search scores it (the ENDED model)."""
        from svsim.learn.model import SCALE
        from svsim.search.evaluate import evaluate
        if not s.over and s.active == me:
            ISMCTS._step(s, EndTurn())
        if s.over:
            return 1.0 if s.winner == me else 0.0 if s.winner == 1 - me else 0.5
        score = evaluate(s, me, self.search.weights)
        return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, score / SCALE))))

    def _value(self, s, me: int) -> float:
        from svsim.learn.model import SCALE
        from svsim.search.evaluate import evaluate
        moves_next = True                          # the start of the own next turn: the ACT model (+phased)
        if self.next_turn and not s.over:          # ... or play it with the policy head: the ENDED model
            if self.next_search:
                self._searched_turn(s, me, self.next_search, end=False)
            else:
                self._own_turn(s, me, [], None)
            if not s.over and s.active == me:
                ISMCTS._step(s, EndTurn())         # end-of-turn effects, not the opponent's turn
            moves_next = False
        if s.over:
            return 1.0 if s.winner == me else 0.0 if s.winner == 1 - me else 0.5
        score = evaluate(s, me, self.search.weights, player_moves_next=moves_next)
        return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, score / SCALE))))

    def lines_for(self, state, line: list, candidates: list) -> dict:
        """Each candidate's turn as a line of keys: the principal line; with `research`, a restriction's
        own search's principal line (the best turn that keeps the card, not the line without it)."""
        lines = {r: line for r in candidates}
        self._roots = {}
        if self.research == "tree":                # from the base search's own tree, no new search
            root = self.search.last_root
            return {r: line if r == NONE else restricted_line(root, r) for r in candidates}
        if not self.research:
            return lines
        root, iterations = self.search.last_root, self.search.iterations
        try:
            self.search.iterations = self.research
            for r in candidates:
                if r == NONE:
                    continue
                self._set(r)
                self.search.choose(state)
                self._roots[r] = self.search.last_root
                lines[r] = principal_line(self.search.last_root)
        finally:
            self.search.iterations = iterations
            self._set(NONE)
            self.search.last_root = root
        return lines

    def outcomes(self, state, line, candidates: list) -> dict:
        """{restriction: [value on each determinization]} (the same determinizations for all); `line`
        is the line for all candidates, or {restriction: line} (lines_for)."""
        me = state.active
        lines = line if isinstance(line, dict) else {r: line for r in candidates}
        seeds = [self.rng.getrandbits(64) for _ in range(self.samples)]
        out = {r: [] for r in candidates}
        for sd in seeds:
            base = determinize(state, me, random.Random(sd))
            for r in candidates:
                s = base.clone()
                self._own_turn(s, me, lines[r], forbids(r))
                if self.static:
                    out[r].append(self._ended(s, me))
                    continue
                self._their_turn(s, me)
                out[r].append(self._value(s, me))
        return out

    def assess(self, state, line: list, candidates: list) -> dict:
        return {r: sum(v) / len(v) for r, v in self.outcomes(state, line, candidates).items()}

    def _better(self, values: list, base: list) -> bool:
        """Whether a restriction's values beat the line's by more than the margin and z standard errors."""
        diffs = [a - b for a, b in zip(values, base)]
        n = len(diffs)
        mean = sum(diffs) / n
        se = math.sqrt(sum((d - mean) ** 2 for d in diffs) / max(n - 1, 1) / n) if n > 1 else 0.0
        return mean > self.margin and mean > self.z * se

    # --- playing ------------------------------------------------------------------------------

    def _set(self, restriction: str) -> None:
        self.restriction = restriction
        extra = forbids(restriction)
        own = self._veto
        if extra is None:
            self.search.veto = own
        elif own is None:
            self.search.veto = extra
        else:
            self.search.veto = lambda s, a: own(s, a) or extra(s, a)

    def act(self, state, actions):
        if state.phase != Phase.MAIN:
            return self.base.act(state, actions)
        if state.turn != self.turn:
            self.turn = state.turn
            self._set(NONE)
            if len(actions) == 1:
                return actions[0]
            if self.policy.priors(state, actions) is None:      # no policy head for this matchup
                return self.base.act(state, actions)
            choice = self.base.act(state, actions)
            root = self.search.last_root
            line = principal_line(root) if root is not None else []
            candidates = restrictions(line, self.kinds, self.max_keeps)
            if len(candidates) == 1:
                return choice
            lines = self.lines_for(state, line, candidates)
            samples = self.outcomes(state, lines, candidates)
            values = {r: sum(v) / len(v) for r, v in samples.items()}
            self.values = values
            best = max(candidates, key=lambda r: (values[r], r == NONE))
            if best != NONE and not self._better(samples[best], samples[NONE]):
                best = NONE
            self.last_plan = {"turn": state.turn, "line": [list(map(_plain, k)) for k in line],
                              "samples": samples, "chosen": best,
                              "next_turn": self.next_turn, "static": self.static, "research": self.research}
            if best == NONE:
                self.picked[NONE] = self.picked.get(NONE, 0) + 1
                return choice
            kind = best.split(":")[0]
            self.picked[kind] = self.picked.get(kind, 0) + 1
            self._set(best)
            veto = forbids(best)
            if not veto(state, choice):
                return choice
            # the search's move is now left out: the restricted search's move, else the most visited allowed
            where = _locator(state, state.active)
            if best in self._roots:
                root = self._roots[best]
            allowed = {action_key(state, a, where): a for a in actions if not veto(state, a)}
            ranked = sorted((k for k in allowed if k in root.children), key=lambda k: -root.children[k].visits)
            return allowed[ranked[0]] if ranked else next(iter(allowed.values()), choice)
        if len(actions) == 1:
            return actions[0]
        return self.base.act(state, actions)
