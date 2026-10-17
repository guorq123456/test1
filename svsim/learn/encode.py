"""What the value network sees of a position: only what `me` can know, at any moment of a turn.

Three parts, all from `me`'s side of the table:

- the version-2 features (learn.features: board totals, keywords, the hand's
  and the deck's roles, the field's effects each round, how long each leader
  lasts; the opponent's hand as their share of the cards not seen yet);
- the moment: ACT (`me` is to act, inside their turn or at its start) or
  ENDED (`me` has just ended the turn, end-of-turn abilities resolved, the
  opponent's turn not started), the play points left, whether `me` evolved
  this turn, who went first, the turn counts. The linear models were fitted
  on ENDED positions only and the search scored ACT positions with them
  too; the network learns both;
- which cards are where, counted by card: `me`'s hand and deck, both fields
  (evolved followers apart), both leader areas, and the cards of the
  opponent not seen yet (their hand and deck together: card counting from
  their list, the same pool the version-2 features use). A card's identity
  says what totals can't: Justice on the field is not just 8 attack.

`raw(state, me)` gives the parts before a vocabulary is chosen (dense values,
card ids per zone); `vectorize(raw, vocab)` turns them into one vector with
the model's vocabulary (card id -> index; unknown cards are left out).
"""
from __future__ import annotations

ACT, ENDED = 0, 1
ZONES = ("my_hand", "my_deck", "my_field", "my_field_evolved", "op_field", "op_field_evolved",
         "my_leader", "op_leader", "op_unseen")


def phase(state, me: int) -> int:
    return ACT if state.active == me else ENDED


def dense_names() -> list[str]:
    from svsim.learn.features import names
    return names(False, 2) + ["phase_act", "phase_ended", "pp_left", "evolved_this_turn", "went_first",
                              "my_turns", "op_turns"]


def raw(state, me: int) -> tuple[list[float], list[list[int]]]:
    from svsim.learn.features import features
    p, op = state.players[me], state.players[1 - me]
    ph = phase(state, me)
    dense = features(state, me, False, 2) + [
        float(ph == ACT), float(ph == ENDED), p.pp / 10.0 if ph == ACT else 0.0,
        float(ph == ACT and p.evolved_this_turn), float(state.first == me),
        p.turns_taken / 10.0, op.turns_taken / 10.0]
    evolved = lambda c: bool(getattr(c, "evolved", False))
    zones = [[c.defn.card_id for c in p.hand], [c.defn.card_id for c in p.deck],
             [c.defn.card_id for c in p.field if not evolved(c)], [c.defn.card_id for c in p.field if evolved(c)],
             [c.defn.card_id for c in op.field if not evolved(c)], [c.defn.card_id for c in op.field if evolved(c)],
             [c.defn.card_id for c in p.leader_area], [c.defn.card_id for c in op.leader_area],
             [c.defn.card_id for c in op.hand + op.deck]]
    return dense, zones


def width(vocab: dict) -> int:
    return len(dense_names()) + len(ZONES) * len(vocab)


def vectorize(parts, vocab: dict, out=None):
    """One vector (a numpy array if numpy is there, else a list) from raw()'s parts."""
    dense, zones = parts
    v = len(vocab)
    try:
        import numpy as np
        x = np.zeros(width(vocab), dtype=np.float32) if out is None else out
    except ImportError:
        x = [0.0] * width(vocab)
    x[:len(dense)] = dense
    base = len(dense)
    for z, ids in enumerate(zones):
        off = base + z * v
        for cid in ids:
            k = vocab.get(cid)
            if k is not None:
                x[off + k] += 1.0
    return x


def encode(state, me: int, vocab: dict):
    return vectorize(raw(state, me), vocab)
