"""Opponent hand inference (+infer=ALPHA[:TAU], off by default): a card the opponent could have played last turn
and clearly should have is less likely to be in their hand.

At my turn the opponent's hand is the one they ended their turn with, and their play points left are still in
`pp` (engine._start_turn refills them only at their next turn). For each kind of card in their hand and deck
(their deck list is known), unplayed_weights asks: could they pay for it from what they left (`pp`), was it legal,
and does playing it score at least TAU above passing, from their side, with the search's own evaluator? Such
cards get weight ALPHA, the others 1, and core.view.determinize draws their hand by those weights (without
replacement). It reads only the rules, the costs and the evaluator: no card ids as features, nothing beyond the
deck list. The check runs on the position of my turn's first decision (my turn's start effects and draw have
happened: close to theirs at their turn's end) and is kept for the turn.
"""
from __future__ import annotations


def unplayed_weights(state, player: int, alpha: float, tau: float, weights) -> dict:
    """{uid: weight} for the opponent's hand and deck cards: ALPHA for a kind they could have played with the
    play points they left and that scores at least TAU above passing for them, 1 otherwise (absent: 1)."""
    if alpha == 1.0:
        return {}
    gains = unplayed_gains(state, player, weights)
    them = state.players[1 - player]
    return {c.uid: alpha for c in them.hand + them.deck if gains.get(c.defn.card_id, -1e9) >= tau}


def unplayed_gains(state, player: int, weights) -> dict:
    """{card id: how much more than passing the opponent's best play of it scores for them} for the kinds in their
    hand and deck they could pay for from the play points they left and could legally play."""
    from svsim.core.actions import PlayCard
    from svsim.core.engine import apply, legal_actions
    from svsim.search.evaluate import evaluate
    opp = 1 - player
    them = state.players[opp]
    pool = them.hand + them.deck
    if not them.hand:
        return {}
    out = {}
    for card_id in {c.defn.card_id for c in pool}:
        card = next(c for c in pool if c.defn.card_id == card_id)
        if card.cost > them.pp:
            continue
        view = state.clone()
        view.active = opp
        hand, deck = view.players[opp].hand, view.players[opp].deck
        mine = next((c for c in hand + deck if c.uid == card.uid), None)
        if mine in deck:                           # put it in their hand in place of the first card
            i = deck.index(mine)
            deck[i], hand[0] = hand[0], mine
        try:
            base = evaluate(view, opp, weights)
            plays = [a for a in legal_actions(view) if isinstance(a, PlayCard) and a.uid == card.uid]
            for action in plays[:6]:
                after = view.clone()
                apply(after, action)
                gain = evaluate(after, opp, weights) - base
                out[card_id] = max(out.get(card_id, gain), gain)
        except Exception:                          # a position the rules can't take from this side: no inference
            continue
    return out
