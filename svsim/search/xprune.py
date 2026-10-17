"""+xprune: which hand cards a "select a card in your hand and discard it" choice may discard, by a cross-turn
judgment (Salem 2026-10-10: "跨回合算法判断哪些牌在接下来的对局里价值不够高，哪些牌价值在近几回合一定不会出";
the architecture thread 16:57Z). Off by default; with it the search leaves out every discard choice but the
`m` most discardable cards' (m + k - 1 for a choice of k cards), at every node of its own turn.

What a discard is: an action (play, evolve, engage) whose targets include cards in the player's hand that its
resolution discards (core.effects.discard), found once per card and action kind by resolving it on a copy.

How discardable a hand card is, computed from costs, the play-point curve and the position (no card list, no
fixed value per card; docs/architecture.md §9.2):
1. **Discarding it gains something:** it has a "when discarded" ability (on_discard).
2. **It won't come out soon:** the turns from now (0 = this turn) in which the hand would play it if each turn
   plays the most play points' worth of the hand it can: this turn's budget is the play points left after the
   discarding card (plus the Bonus Play Point if it is still to use), turn t's is min(10, max play points + t);
   the cards' current costs (reductions included). A card not played within `horizon` turns (default 3) is
   horizon + 1. Later is more discardable. The cards drawn meanwhile are unknown and not counted.
3. **It is worth less later:** the lower cost.
`order` sets how 2 and 3 combine (1 always comes first):
- "when" (the default): 2, then 3;
- "cost": 3, then 2;
- "value": the cost discounted by 0.8 per turn until the card is played (0 if not within the horizon), then 2.
Ties go by the card's signature (core.engine._signature), so the choice is the same on every copy of the position.
Only the player's own visible cards and play points are read: the same at every determinization of a decision.
"""
from __future__ import annotations

from svsim.core import effects as E
from svsim.core.actions import Engage, Evolve, PlayCard
from svsim.core.engine import _signature, apply, play_form
from svsim.core.script import script_for
from svsim.core.state import MAX_PP

_DISCARDS: dict = {}          # (action kind, card id, super) -> whether its hand targets are discarded


def _source(p, action):
    uid = action.uid
    for zone in (p.hand, p.field):
        for c in zone:
            if c.uid == uid:
                return c
    return None


def discards(state, action, targeted) -> bool:
    """Whether `action` discards its hand targets `targeted` (resolved once on a copy per card and kind)."""
    p = state.players[state.active]
    src = _source(p, action)
    if src is None:
        return False
    key = (type(action).__name__, src.defn.card_id, getattr(action, "super_", None))
    hit = _DISCARDS.get(key)
    if hit is None:
        seen, real = [], E.discard

        def spy(st, inst):
            seen.append(inst.uid)
            return real(st, inst)

        E.discard = spy
        try:
            apply(state.clone(), action)
            hit = all(t in seen for t in targeted)
        except Exception:                       # noqa: BLE001 (a probe: anything odd is "not a discard")
            hit = False
        finally:
            E.discard = real
        _DISCARDS[key] = hit
    return hit


def _gains_on_discard(card) -> bool:
    return getattr(script_for(card.defn.card_id), "on_discard", None) is not None and not card.silenced


def schedule(costs: list, budgets: list) -> list:
    """For each card (by its cost), the first budget's index in which it is played if each budget in turn plays
    the most play points' worth of the cards left (0/1 knapsack, ties to the earlier cards in `costs`' order);
    len(budgets) for a card never played."""
    when = [len(budgets)] * len(costs)
    left = list(range(len(costs)))
    for t, b in enumerate(budgets):
        if not left or b < 0:
            continue
        best = {0: ()}                          # total -> the earliest subset (indices into left) reaching it
        for j, i in enumerate(left):
            c = costs[i]
            for total, picked in sorted(best.items(), reverse=True):
                n = total + c
                if n <= b and n not in best:
                    best[n] = picked + (j,)
        chosen = best[max(best)]
        for j in chosen:
            when[left[j]] = t
        left = [i for j, i in enumerate(left) if j not in set(chosen)]
    return when


class XPrune:
    """veto(state, action) for ISMCTS: True for a discard choice outside the most discardable cards."""

    def __init__(self, m: int = 2, horizon: int = 3, order: str = "when"):
        self.m, self.horizon, self.order = m, horizon, order
        self._allowed: dict = {}
        self.calls = self.cut = 0               # vetoes asked / given (a reading)

    def __call__(self, state, action) -> bool:
        if not isinstance(action, (PlayCard, Evolve, Engage)) or not action.targets:
            return False
        p = state.players[state.active]
        hand = {c.uid: c for c in p.hand}
        targeted = [t for t in action.targets if t in hand]
        if not targeted or not discards(state, action, targeted):
            return False
        self.calls += 1
        allowed = self.allowed(state, action, len(targeted))
        out = any(_signature(hand[t]) not in allowed for t in targeted)
        self.cut += out
        return out

    def allowed(self, state, action, k: int) -> set:
        """The signatures of the m + k - 1 most discardable hand cards (the discarding card left out)."""
        p = state.players[state.active]
        key = (state.active, tuple((c.uid, c.cost, c.silenced) for c in p.hand), p.pp, p.max_pp, p.bonus_ready,
               p.bonus_active, action.uid, type(action).__name__, k)
        hit = self._allowed.get(key)
        if hit is not None:
            return hit
        if len(self._allowed) > 20000:
            self._allowed.clear()
        cards = [c for c in p.hand if c.uid != action.uid]
        paid = 0
        if isinstance(action, PlayCard):
            src = _source(p, action)
            form = play_form(p, src) if src is not None else None
            paid = form.paid if form is not None else 0
        now = p.pp - paid + (1 if p.bonus_ready and not p.bonus_active else 0)
        budgets = [now] + [min(MAX_PP, p.max_pp + t) for t in range(1, self.horizon + 1)]
        order = sorted(range(len(cards)), key=lambda i: (-cards[i].cost, _signature(cards[i])))
        when_sorted = schedule([cards[i].cost for i in order], budgets)
        when = {order[j]: w for j, w in enumerate(when_sorted)}
        H = self.horizon
        if self.order == "when":                # won't come out soon first, then the cheaper
            rank = lambda i: (-when[i], cards[i].cost)                                  # noqa: E731
        elif self.order == "cost":              # the cheaper first, then won't come out soon
            rank = lambda i: (cards[i].cost, -when[i])                                  # noqa: E731
        else:                                   # "value": cost discounted by the turns until played, 0 if not
            rank = lambda i: (cards[i].cost * 0.8 ** when[i] if when[i] <= H else 0.0, -when[i])   # noqa: E731
        ranked = sorted(range(len(cards)), key=lambda i: (not _gains_on_discard(cards[i]), rank(i),
                                                          _signature(cards[i])))
        out, sigs = set(), self.m + k - 1
        for i in ranked:
            if len(out) >= sigs:
                break
            out.add(_signature(cards[i]))
        self._allowed[key] = out
        return out
