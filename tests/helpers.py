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


def mirror_position(seed: int, deck: str, turn: int, first: int, turns: tuple, hp: tuple, pp: tuple, points: tuple,
                    hand: list, mine: list, theirs: list, their_hand: int, decks_left: tuple = (None, None),
                    shadows: tuple = (0, 0), bonus: bool = False):
    """A mirror position for player 0 to act, rebuilt from a record's description (tests/puzzles): `deck` a
    ui.session DECKS key for both sides; `turns` (own turns taken, ours then theirs); `hp`, `pp` ((pp, max) each),
    `points` ((ep, sep) each); `hand` our cards; `mine` / `theirs` the fields as (defn, atk, life, evolved 0/1/2,
    can attack[, keywords as the record shows them: an evolution's own keyword changes don't run here]); their hand `their_hand` cards dealt from their deck by `seed` (unknown to us); `decks_left` the
    deck sizes (trimmed from the top), `shadows`, `bonus` our Bonus Play Point button."""
    from svsim.cards import decks
    from svsim.ui.session import DECKS
    cards = decks.build(DECKS[deck][1])
    st = new_game(list(cards), list(cards), seed=seed, first=first)
    apply(st, Mulligan(()))
    apply(st, Mulligan(()))
    st.active = 0
    st.turn = turn
    for i, p in enumerate(st.players):
        p.hand.clear()
        p.field.clear()
        p.turns_taken = turns[i]
        p.leader_hp = hp[i]
        p.pp, p.max_pp = pp[i]
        p.ep, p.sep = points[i]
        p.shadows = shadows[i]
        if decks_left[i] is not None:
            while len(p.deck_view()) > decks_left[i]:
                p.draw_top()
    for player, field in ((0, mine), (1, theirs)):
        for defn, atk, life, evo, ready, *kw in field:
            inst = put(st, player, defn, ready)
            if evo:
                E.evolve(st, inst, super_=evo == 2, notify=False)
            if kw:
                inst.keywords = kw[0]
            inst.atk, inst.life = atk, life
            inst.max_life = max(inst.max_life, life)
            if not ready:
                inst.attacks_made = inst.max_attacks
    for defn in hand:
        give(st, 0, defn)
    op = st.players[1]
    for _ in range(their_hand):
        op.hand.append(op.draw_top())
    st.players[0].bonus_ready = bonus
    return st
