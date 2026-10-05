"""Builders for hand-crafted test positions."""
from svsim.cards import demo
from svsim.core import effects as E
from svsim.core.actions import EndTurn, Mulligan, PlayCard
from svsim.core.engine import apply, legal_actions, new_game


def start(first: int = 0, seed: int = 0, deck=None, deck1=None):
    """A game after both mulligans: turn 1, `first` to act. Decks default to Footmen."""
    deck = deck or [demo.FOOTMAN] * 40
    state = new_game(deck, deck1 or deck, seed=seed, first=first)
    apply(state, Mulligan(()))
    apply(state, Mulligan(()))
    return state


def put(state, player: int, defn, ready: bool = True):
    """Place a card on the field. `ready` = entered on an earlier turn (can attack)."""
    inst = E.summon(state, player, defn)
    if ready:
        inst.entered_turn = -1
    return inst


def give(state, player: int, defn):
    """Add a card to a player's hand."""
    return E.add_to_hand(state, player, defn)


def pass_turns(state, n: int) -> None:
    for _ in range(n):
        apply(state, EndTurn())


def set_pp(state, player: int, pp: int) -> None:
    state.players[player].max_pp = pp
    state.players[player].pp = pp


def unlock_evolution(state, player: int) -> None:
    """Let `player` evolve and super-evolve this turn."""
    state.players[player].turns_taken = 8


def plays(state, uid):
    """Legal PlayCard actions for one card."""
    return [a for a in legal_actions(state) if isinstance(a, PlayCard) and a.uid == uid]


def count(cards, defn) -> int:
    return sum(c.defn.card_id == defn.card_id for c in cards)
