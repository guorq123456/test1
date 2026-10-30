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
        + [c for c in p.deck_view() if c.defn.card_id in LISTEN_IN_DECK]
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


_ENHANCE: dict = {}


def enhance_gain(defn, cost: int) -> float:
    """What a card's Enhance at `cost` adds to playing it without, measured in a sandbox:
    cards drawn or added, play points recovered (half each), followers summoned,
    and damage to enemies (a quarter each)."""
    key = (defn.card_id, cost)
    if key not in _ENHANCE:
        _ENHANCE[key] = _play_measure(defn, cost) - _play_measure(defn, defn.cost)
    return _ENHANCE[key]


def _play_measure(defn, pp: int) -> float:
    from svsim.core import effects as E
    from svsim.core.engine import apply, legal_actions
    from svsim.search.combo import _sandbox
    state, _ = _sandbox(0, pp)
    card = E.add_to_hand(state, 0, defn)
    plays = [a for a in legal_actions(state) if isinstance(a, PlayCard) and a.uid == card.uid]
    if not plays:
        return 0.0
    me, foe = state.players[0], state.players[1]
    hand, followers = len(me.hand) - 1, len(me.followers)
    damage = foe.leader_hp + sum(f.life for f in foe.followers)
    best = 0.0
    for a in plays[:6]:
        t = state.clone()
        paid = t.players[0].pp
        apply(t, a)
        m, f = t.players[0], t.players[1]
        recovered = max(m.pp - (paid - (pp if defn.cost < pp else defn.cost)), 0)
        value = ((len(m.hand) - hand) + 0.5 * recovered + (len(m.followers) - followers - (1 if defn.is_follower else 0))
                 + 0.25 * (damage - f.leader_hp - sum(x.life for x in f.followers)))
        best = max(best, value)
    return best


def wasted_enhance(state: GameState, action) -> bool:
    """Playing a card without its Enhance when the Enhance is worth a lot more and the
    play points for it come within two turns: Luria (Enhance 8: draw a big follower,
    recover 7 play points), which the player plays on their sixth turn and the bot
    on its third or fourth as a 1/1."""
    if not isinstance(action, PlayCard):
        return False
    card = state.in_hand(state.active, action.uid)
    if card is None:
        return False
    from svsim.core.script import script_for
    p = state.players[state.active]
    later = [c for c in script_for(card.defn.card_id).enhance if p.pp < c <= p.max_pp + 2]
    return any(enhance_gain(card.defn, c) >= 2.0 for c in later)
