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


def restrictions(line: list) -> list:
    """The candidates' restrictions for a principal line: none, keep each card it plays, keep the bonus
    play point, don't evolve."""
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
                 max_steps: int = 40, next_turn: bool = False):
        self.base = base                     # an MCTSAgent (the lethal search stays outside)
        self.search: ISMCTS = base.search
        if policy is None:
            from svsim.learn.policy import MatchupPrior
            policy = MatchupPrior()
        self.policy = policy
        self.samples = samples
        self.margin = margin
        self.max_steps = max_steps
        self.next_turn = next_turn           # score after the own next turn (policy head) with the ENDED model
        self.rng = random.Random(seed)
        self.turn = None
        self.restriction = NONE
        self._veto = self.search.veto        # the base search's own veto, kept under a restriction
        self.picked: dict = {}               # restriction kind -> turns (statistics)
        self.values: dict = {}

    # --- the play-outs ------------------------------------------------------------------------

    def _top(self, s, allowed):
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

    def _their_turn(self, s, me: int) -> None:
        if not s.over and s.active == me:
            apply(s, EndTurn())
        for _ in range(self.max_steps * 2):
            if s.over or s.active == me:
                return
            legal = legal_actions(s)
            a = self._top(s, legal) if len(legal) > 1 else legal[0]
            apply(s, a if a is not None else legal[-1])

    def _value(self, s, me: int) -> float:
        from svsim.learn.model import SCALE
        from svsim.search.evaluate import evaluate
        moves_next = True                          # the start of the own next turn: the ACT model (+phased)
        if self.next_turn and not s.over:          # ... or play it with the policy head: the ENDED model
            self._own_turn(s, me, [], None)
            if not s.over and s.active == me:
                ISMCTS._step(s, EndTurn())         # end-of-turn effects, not the opponent's turn
            moves_next = False
        if s.over:
            return 1.0 if s.winner == me else 0.0 if s.winner == 1 - me else 0.5
        score = evaluate(s, me, self.search.weights, player_moves_next=moves_next)
        return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, score / SCALE))))

    def assess(self, state, line: list, candidates: list) -> dict:
        me = state.active
        seeds = [self.rng.getrandbits(64) for _ in range(self.samples)]
        totals = {r: 0.0 for r in candidates}
        for sd in seeds:
            base = determinize(state, me, random.Random(sd))
            for r in candidates:
                s = base.clone()
                self._own_turn(s, me, line, forbids(r))
                self._their_turn(s, me)
                totals[r] += self._value(s, me)
        return {r: v / len(seeds) for r, v in totals.items()}

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
            candidates = restrictions(line)
            if len(candidates) == 1:
                return choice
            values = self.assess(state, line, candidates)
            self.values = values
            best = max(candidates, key=lambda r: (values[r], r == NONE))
            if best == NONE or values[best] <= values[NONE] + self.margin:
                self.picked[NONE] = self.picked.get(NONE, 0) + 1
                return choice
            kind = best.split(":")[0]
            self.picked[kind] = self.picked.get(kind, 0) + 1
            self._set(best)
            veto = forbids(best)
            if not veto(state, choice):
                return choice
            # the search's move is now left out: the most visited root move that is allowed
            where = _locator(state, state.active)
            allowed = {action_key(state, a, where): a for a in actions if not veto(state, a)}
            ranked = sorted((k for k in allowed if k in root.children), key=lambda k: -root.children[k].visits)
            return allowed[ranked[0]] if ranked else next(iter(allowed.values()), choice)
        if len(actions) == 1:
            return actions[0]
        return self.base.act(state, actions)
