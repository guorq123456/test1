"""Hand-built positions for the acceptance library (lib.py): the zones are set directly, so the position file names
the builder and stores a fingerprint per variant.

bunny_board: Salem's board of 2026-11-01 (analysis/pilot/salem_board_2026_11_01.py, which documents the position and
his reason). The construction is that script's build() and cast(), with the two lists taken from the position file
instead of a list file; each seed is one deal of the opponent's unknown cards. The lines (keep / all / big / small) are
that script's line().
"""
import random

from svsim.cards import deckcode
from svsim.cards.pool import POOL
from svsim.core import effects as E
from svsim.core.actions import Attack, Mulligan, PlayCard, UseBonusPP
from svsim.core.engine import apply, legal_actions, new_game

PROPAGATION, REHAB, TERESA, CLUE, LILIUM = 11062310, 11063110, 10861120, 90001210, 10861110
TICO, TICO_CREST, SEDIMENT, NAPTIME = 10833110, 10833112, 90031210, 10833310


def _build(pos: dict, seed: int):
    """Salem (player 0) to act, turn 14, before 荒废的繁殖 (salem_board_2026_11_01.build)."""
    haven = [POOL[i] for i in deckcode.decode_deck(pos["deck_code"])[2]]
    rune = [POOL[i] for i in deckcode.decode_deck(pos["opponent_code"])[2]]
    st = new_game(haven, rune, seed=seed, first=1)
    apply(st, Mulligan(()))
    apply(st, Mulligan(()))
    me, op = st.players
    rng = random.Random(seed)
    for p in st.players:
        p.deck.extend(p.hand)
        p.hand.clear()
        p.field.clear()
        p.leader_area.clear()
        rng.shuffle(p.deck)
    st.turn = 14
    st.active = 0
    me.turns_taken, op.turns_taken = 7, 7
    me.max_pp, me.pp = 7, 7
    me.bonus_ready, me.bonus_active = True, False
    op.max_pp, op.pp = 7, 0
    me.leader_hp, op.leader_hp = 19, 12
    me.ep, me.sep, op.ep, op.sep = 0, 0, 1, 0

    def take(p, cid):
        card = next((c for c in p.deck if c.defn.card_id == cid), None)
        if card is not None:
            p.deck.remove(card)

    for cid in (PROPAGATION, REHAB, TERESA, LILIUM):
        take(me, cid)
        E.add_to_hand(st, 0, POOL[cid])
    E.add_to_hand(st, 0, POOL[CLUE])
    for _ in range(4):                                    # the four the bunnies banish
        E.set_cost(E.add_to_hand(st, 0, me.deck.pop().defn), 0)
    del me.deck[29:]
    for super_ in (True, False):
        take(op, TICO)
        t = E.summon(st, 1, POOL[TICO])
        t.entered_turn = -1
        E.evolve(st, t, super_=super_, notify=False)
    E.add_to_leader_area(st, 1, POOL[TICO_CREST])
    E.gain_earth_sigils(st, 1, 7, POOL[SEDIMENT])
    clue = E.summon(st, 1, POOL[CLUE])
    E.counters(clue)["clues"] = 3
    for _ in range(2):                                    # two 钢铁的小憩 already played (Salem)
        take(op, NAPTIME)
    for _ in range(8):
        op.hand.append(op.deck.pop())
    del op.deck[21:]
    return st


def _cast(st):
    """Bonus point, then 荒废的繁殖 enhanced (four bunnies) (salem_board_2026_11_01.cast)."""
    apply(st, next(a for a in legal_actions(st) if isinstance(a, UseBonusPP)))
    plays = [a for a in legal_actions(st) if isinstance(a, PlayCard)
             and (st.in_hand(0, a.uid) is not None) and st.in_hand(0, a.uid).defn.card_id == PROPAGATION]
    before = len(st.players[0].field)
    for a in plays:                                       # the enhanced play is the one that summons four
        t = st.clone()
        apply(t, a)
        if len(t.players[0].field) - before == 4:
            apply(st, a)
            return st
    raise RuntimeError("no enhanced play")


def bunny_board(pos: dict, seed: int):
    """(state, seat): the bunnies are in, Salem to decide whether to attack."""
    return _cast(_build(pos, seed)), 0


def bunny_line(st, name: str):
    """keep / all / big / small (salem_board_2026_11_01.line)."""
    me, op = st.players
    bunnies = [c for c in me.field if c.defn.is_follower]
    big, small = sorted([c for c in op.field if c.defn.is_follower], key=lambda c: -c.atk)
    plan = {"keep": [], "all": [big, big, small, small], "big": [big, big], "small": [small, small]}[name]
    for b, target in zip(bunnies, plan):
        if st.on_field(target.uid) is not None and st.on_field(b.uid) is not None:
            apply(st, Attack(b.uid, target.uid))
    return st
