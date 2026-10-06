"""Moves a search can leave out because another order of the same moves is never worse.

Evolving a follower after it has used up its attacks this turn: evolving it
first and then attacking gives the same evolved follower, more damage, and more
defense in the fight, so "attack, then evolve" is never better than "evolve,
then attack". The order can matter when the evolution does something besides
the stats (an Evolve or "when this follower evolves" ability on the card, or an
allied card that reacts to evolutions), so those evolutions stay in.

The player caught the AI attacking with Sagatsumatsu for 5 and evolving it
afterwards, twice in one game: its learned evaluation, sure it was winning,
couldn't tell the two orders apart. Whatever the evaluation, the search
shouldn't be offered the worse order.
"""
from __future__ import annotations

from svsim.core.actions import Attack, Evolve, PlayCard
from svsim.core.script import LISTEN_IN_DECK, LISTEN_IN_HAND, scripts_of
from svsim.core.state import GameState, leader_of

EVOLVE_HOOKS = ("on_evolve", "on_super_evolve", "on_evolved")


def _listens(card, hooks) -> bool:
    return any(getattr(s, h) is not None for s in scripts_of(card) for h in hooks)


def _evolving_matters(state: GameState, follower) -> bool:
    if _listens(follower, EVOLVE_HOOKS):
        return True
    p = state.players[follower.owner]
    cards = p.leader_area + p.field + [c for c in p.hand if c.defn.card_id in LISTEN_IN_HAND] \
        + [c for c in p.deck if c.defn.card_id in LISTEN_IN_DECK]
    return any(c is not follower and _listens(c, ("on_ally_evolve",)) for c in cards)


def dominated(state: GameState, action) -> bool:
    """True for an evolution that evolving before attacking would have beaten."""
    if not isinstance(action, Evolve):
        return False
    follower = next((c for c in state.players[state.active].field if c.uid == action.uid), None)
    if follower is None or follower.attacks_made == 0 or follower.attacks_made < follower.max_attacks:
        return False
    return not _evolving_matters(state, follower)


def worth_trying(state: GameState, actions: list) -> list:
    """The actions minus the dominated ones (never empty: ending the turn stays)."""
    kept = [a for a in actions if not dominated(state, a)]
    return kept or list(actions)


_FINISHERS: dict = {}


def finisher(defn) -> bool:
    """A follower whose attack grows with Combo and that can hit the leader the
    turn it is played (Killer Rhinoceroach), measured by search.formula."""
    hit = _FINISHERS.get(defn.card_id)
    if hit is None:
        from svsim.search.formula import _finisher
        hit = _FINISHERS[defn.card_id] = _finisher(defn) is not None
    return hit


def reserved(state: GameState, action) -> bool:
    """Spending the win condition outside a finishing turn: playing a finisher, or
    a finisher attacking a follower. The player's Rhinoceroaches (25 plays in ten
    games) all went to the leader, 22 of 25 from their sixth turn on; the AI's
    went early (22 of 56 before its sixth turn) and 22 of 56 traded with
    followers, leaving nothing to finish with. Lethal and burst lines (the
    lethal agent) still play them."""
    if isinstance(action, PlayCard):
        card = state.in_hand(state.active, action.uid)
        return card is not None and finisher(card.defn)
    if isinstance(action, Attack) and leader_of(action.target) is None:
        attacker = state.on_field(action.attacker)
        return attacker is not None and finisher(attacker.defn)
    return False


def wasted_combo(state: GameState, action) -> bool:
    """Playing a Combo card before its Combo is reached: Sprouting Initiate (draws at
    Combo 3) as the turn's first or second card. The player drew with it 23 times in
    22 plays; the AI, 28 in 55."""
    if not isinstance(action, PlayCard):
        return False
    card = state.in_hand(state.active, action.uid)
    if card is None:
        return False
    from svsim.search.mcts import _combo_payoff
    if not _combo_payoff(card.defn):
        return False
    from svsim.search.combo import at_combo, profile
    combo = state.players[state.active].combo + 1
    if combo >= 3:
        return False
    for v in profile(card.defn):
        now, later = at_combo(v, combo), at_combo(v, 3)
        if (later.drawn, len(later.added)) > (now.drawn, len(now.added)):
            return True
    return False
