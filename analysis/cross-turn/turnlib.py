"""What a player kept at the end of a turn, and a readable list of the turn's moves.

Shared by play_turns.py (Salem's turns, and a bot's from the same starts) and
resources.py (whole games). Runs inside an svsim checkout (PYTHONPATH=.).
"""
from svsim.cards import library, decks  # noqa: F401  (registers card scripts)
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard, UseBonusPP
from svsim.core.engine import legal_actions
from svsim.core.state import leader_uid

ERNTZ, BURNITE, RED = "约束的《正义》·伊兰翠", "焦灰的安纳提玛·班德奈特", "赤流"
KEY = (ERNTZ, BURNITE, RED)


def name(c):
    return c.defn.name_zh or c.defn.name


def describe(s, a, me):
    """One move as text, from the state before it (the format of positions.json's salem_turn)."""
    if isinstance(a, PlayCard):
        c = s.in_hand(me, a.uid)
        hand_t = [name(x) for x in s.players[me].hand if x.uid in a.targets]
        tgt = [s.on_field(t) for t in a.targets if s.on_field(t)]
        return (f"play {name(c)}" + (f" discard {hand_t}" if hand_t else "")
                + (f" -> {[name(t) for t in tgt]}" if tgt else ""))
    if isinstance(a, Evolve):
        return ("super-evolve " if a.super_ else "evolve ") + name(s.on_field(a.uid))
    if isinstance(a, Attack):
        t = "leader" if a.target == leader_uid(1 - me) else name(s.on_field(a.target))
        return f"{name(s.on_field(a.attacker))} attacks {t}"
    if isinstance(a, UseBonusPP):
        return "bonus PP"
    if isinstance(a, EndTurn):
        return "end turn"
    return type(a).__name__


def kept(start, end, me, turn):
    """What the player still had when they ended the turn.

    start: the state at the turn's first decision; end: the state at the
    EndTurn decision (before it); turn: the (state, action) pairs of the turn.
    - pp_left: unspent PP, not counting an activated but unspent bonus PP
      (the engine gives that back);
    - bonus: "none" (no bonus PP this turn), "kept" or "used";
    - playable: cards in hand that could still be played (a legal PlayCard)
      without the bonus PP;
    - evo_left / se_left: an evolution / super-evolution was still possible;
    - evolved: what the turn evolved ("evo" / "se", card);
    - key: Erntz, Burnite and Spilling Red still in hand.
    """
    p = end.players[me]
    refund = 1 if p.bonus_active and p.pp >= 1 else 0
    legal = legal_actions(end)
    playable = sorted({name(end.in_hand(me, a.uid)) for a in legal if isinstance(a, PlayCard)
                       and end.in_hand(me, a.uid) is not None})
    playable_n = len({a.uid for a in legal if isinstance(a, PlayCard)})
    had_bonus = start.players[me].bonus_ready
    hand = [name(c) for c in p.hand]
    return {
        "max_pp": p.max_pp,
        "pp_left": p.pp - refund,
        "bonus": "none" if not had_bonus else ("kept" if (p.bonus_ready or refund) else "used"),
        "playable": playable_n,
        "playable_names": playable,
        "evo_left": any(isinstance(a, Evolve) and not a.super_ for a in legal),
        "se_left": any(isinstance(a, Evolve) and a.super_ for a in legal),
        "evolved": [("se" if a.super_ else "evo", name(s.on_field(a.uid)))
                    for s, a in turn if isinstance(a, Evolve)],
        "ep": p.ep, "sep": p.sep,
        "hand": len(hand),
        "key": {k: hand.count(k) for k in KEY},
    }
