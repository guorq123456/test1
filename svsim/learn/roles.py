"""What a card does, measured in a sandbox: its roles in hand and its effect each turn on the field.

The player's verdict on the evaluation (2026-10-06): with both Ramp Dragons
ramping at the same pace, the game is about exchanging resources and planning
ahead, judged from what each side has; the score the bot searched with counted
cards in hand, follower stats and play points as plain totals, and couldn't
tell a hand of Justice and Burnite from one of Spilling Red and Kimika.
These measurements let the evaluation see what the cards are for, for any
deck, without a word written per card:

- `card_roles(defn)`: what playing it does at 10 play points (Enhance paid if
  it can be), the best way of playing it for each role: damage to the enemy
  leader (face), enemy followers taken out (removal, counted in followers of 8
  defense: damage capped at 8 each, so destroying one counts 1), defense
  restored to the leader (heal), cards drawn or added (draw), play points
  gained or recovered (ramp, recovered points count half), and the attack plus
  defense it puts on the field (body);
- `recurring(defn, evolved)`: what it does by itself on the field over one
  round of turns (its end of turn, the opponent's turn starting and ending,
  its own turn starting): face damage, heal, and enemy followers taken out
  (Justice: unevolved, 2 followers and 8 defense back; evolved, 8 to the
  enemy leader). Crests count on the side that holds them.
"""
from __future__ import annotations

ROLES = ("face", "removal", "heal", "draw", "ramp", "body")
RECURRING = ("face", "heal", "clear")
FOE_LIFE = 8                     # defense of the sandbox's enemy followers

_ROLES: dict = {}
_RECURRING: dict = {}


def _sandbox():
    from svsim.cards import demo
    from svsim.core import effects as E
    from svsim.core.actions import Mulligan
    from svsim.core.engine import apply, new_game
    state = new_game([demo.FOOTMAN] * 40, [demo.FOOTMAN] * 40, seed=0, first=0)
    apply(state, Mulligan(()))
    apply(state, Mulligan(()))
    for p in state.players:
        p.hand.clear()
        p.leader_hp = 10                         # room to heal, out of reach of lethal
    me = state.players[0]
    me.max_pp = me.pp = 10
    me.turns_taken = 10                          # evolution unlocked
    anchor = E.summon(state, 0, demo.FOOTMAN)
    anchor.entered_turn = -1
    for _ in range(2):
        foe = E.summon(state, 1, demo.FOOTMAN)
        foe.atk, foe.life, foe.max_life = 0, FOE_LIFE, FOE_LIFE
    return state


def _measure(before, after, me: int = 0) -> dict:
    b, a = before.players, after.players
    gone = 0.0
    alive = {f.uid: f for f in a[1 - me].followers}
    for f in b[1 - me].followers:
        g = alive.get(f.uid)
        gone += 1.0 if g is None else min(max(f.life - g.life, 0), FOE_LIFE) / FOE_LIFE
    return {"face": max(b[1 - me].leader_hp - a[1 - me].leader_hp, 0),
            "removal": gone,
            "heal": max(a[me].leader_hp - b[me].leader_hp, 0)}


def card_roles(defn) -> tuple:
    """(face, removal, heal, draw, ramp, body) for playing `defn` (see the module docstring)."""
    hit = _ROLES.get(defn.card_id)
    if hit is not None:
        return hit
    from svsim.core import effects as E
    from svsim.core.actions import PlayCard
    from svsim.core.engine import apply, legal_actions
    best = dict.fromkeys(ROLES, 0.0)
    try:
        state = _sandbox()
        card = E.add_to_hand(state, 0, defn)
        plays = [a for a in legal_actions(state) if isinstance(a, PlayCard) and a.uid == card.uid]
        for action in plays[:8]:
            t = state.clone()
            me = t.players[0]
            hand, max_pp, field = len(me.hand) - 1, me.max_pp, {f.uid for f in me.followers}
            pp_left = me.pp
            apply(t, action)
            m = t.players[0]
            got = _measure(state, t)
            got["draw"] = max(len(m.hand) - hand, 0)
            got["ramp"] = max(m.max_pp - max_pp, 0) + 0.5 * max(m.pp - (pp_left - _paid(state, card)), 0)
            got["body"] = sum(f.atk + max(f.life, 0) for f in m.followers if f.uid not in field)
            for k in ROLES:
                best[k] = max(best[k], float(got[k]))
    except Exception:                                # a card the sandbox can't play: no roles
        pass
    hit = _ROLES[defn.card_id] = tuple(best[k] for k in ROLES)
    return hit


def _paid(state, card) -> int:
    from svsim.core.engine import play_form
    try:
        return play_form(state.players[card.owner], card).paid
    except Exception:
        return card.cost


def recurring(defn, evolved: bool = False) -> tuple:
    """(face, heal, clear) one round of turns does with `defn` on its holder's field
    (a follower or amulet; a crest in its leader area), evolved or not."""
    key = (defn.card_id, evolved)
    hit = _RECURRING.get(key)
    if hit is not None:
        return hit
    from svsim.core import effects as E
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, resolve_queue
    from svsim.core.enums import CardType
    out = (0.0, 0.0, 0.0)
    try:
        state = _sandbox()
        if defn.type == CardType.CREST:
            E.add_to_leader_area(state, 0, defn)
        else:
            inst = E.summon(state, 0, defn)
            if evolved and defn.is_follower:
                E.evolve(state, inst, False)
        resolve_queue(state)                         # entering and evolving effects first
        before = state.clone()
        for _ in range(2):                           # my end of turn, the opponent's turn, my turn starting
            if state.over:
                break
            apply(state, EndTurn())
        got = _measure(before, state)
        out = (float(got["face"]), float(got["heal"]), float(got["removal"]))
    except Exception:
        pass
    _RECURRING[key] = out
    return out
