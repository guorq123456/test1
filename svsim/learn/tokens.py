"""A turn-end position as a set of card tokens plus a few globals, for a set network (DeepSets) whose only view of
a card is what the card is and does: no card-id embedding, no fixed score per card, no deck or pairing id.

The scaling test (the architecture thread 2026-10-15 17:27Z). The moment and the view are the installed turn-end
evaluator's (learn.netdata.rows, phase ENDED): the position after the player who ended the turn ("me") has had
their end-of-turn abilities resolve, before the next turn starts, seen from me:
- my hand, field, leader area and deck (the deck as what is left in it, order unknown);
- the opponent's field and leader area;
- the opponent's hand as a count only, and their hand and deck as one pool of unseen cards (card counting from
  their known list, the same pool learn.features uses), each card at its printed values.

A token is one card in one zone (ZONES; the side is part of the zone). Cards in a deck or in the unseen pool are
one token per card id with a count; every other card is a token of its own (count 1). A token holds:
- its zone and count (TOKEN);
- what the card is now (DYNAMIC): cost, attack, defense, maximum defense, evolved, super-evolved, whether it can
  still hit a follower / the leader this turn, attacks left, countdown, the sum of its script counters, its
  current keywords (one bit each), silenced, given abilities or stats by an effect, entered this turn.

`static(defn)` is the card's printed attributes and what its abilities do, measured or read from its definition
and script, never a hand-made table (STATIC): cost, attack, defense, type, craft, keywords, countdown, token or
not; which script hooks it has (core.script.HOOKS) and its static script properties (Enhance, choices, targets,
Engage, Skybound Art, Invoke, Accelerate / Crystallize costs); learn.roles' measured roles of playing it and what
it does on the field each round (plain and evolved); learn.payoff's measured payoff of evolving and super-evolving.

The globals (GLOBALS) are both leaders' defense, both players' play points (mine left and maximum, theirs maximum),
evolution and super-evolution points, turn counts, deck and hand counts, the bonus play point, who went first, the
cemetery and the turn number.

`encode(state, me)` -> (cards: int32 [T], tokens: int16 [T, len(TOKEN)], globals: float32 [len(GLOBALS)]). A
token's card id (cards) is there only to look up the card's static row (`static`), never an input of its own.

Input versions (`inputs`, the architecture thread 2026-10-17 01:30Z; "v1", the default, is the encoding above,
unchanged, and every net trained before has it):
- "v2": three more columns on every token (V2_EXTRA), and the attack state of field tokens as of the owner's next
  turn. The owner is me in my zones and the opponent in theirs.
  - share: for a pooled token, my deck: the chance that my next draw is this card (count / deck size); the
    opponent's unseen pool: the expected copies of this card in their hand (hand size x count / pool size). Both
    are in thousandths. Other tokens: 0.
  - next_pp: the owner's play points on their next turn (maximum + 1, at most 10).
  - next_evolve: 1 if the owner can evolve on their next turn (an evolution point left, and the evolution turn
    reached by then).
  - attack state: at a turn end, attacks_left / can_hit_* still describe the turn just played; a follower's
    attacks are reset at its owner's next turn start. In v2, a field follower that can attack at all (not
    cant_attack) has its full attacks and can hit both followers and the leader on that turn. Hand and leader-area
    tokens are as in v1.
- "v2kc": v2 plus seven globals (GLOBALS_KC), learn.features' lethal clock ("kclock") of the player who ended the turn.
- "v2a": v2's three columns, with v1's attack state (the ablation of the architecture thread 2026-10-17 04:21Z).
"""
from __future__ import annotations

import numpy as np

ZONES = ("my_hand", "my_field", "my_leader", "my_deck", "op_field", "op_leader", "op_unseen")
DYNAMIC = ("cost", "atk", "life", "max_life", "evolved", "super_evolved", "can_hit_follower", "can_hit_leader",
           "attacks_left", "countdown", "counters", "keywords", "silenced", "granted", "fresh")
TOKEN = ("zone", "count") + DYNAMIC
GLOBALS = ("my_hp", "op_hp", "my_max_hp", "op_max_hp", "my_pp", "my_max_pp", "op_max_pp", "my_ep", "my_sep",
           "op_ep", "op_sep", "my_turns", "op_turns", "turn", "my_deck", "op_deck", "my_hand", "op_hand",
           "my_bonus", "op_bonus", "went_first", "my_shadows", "op_shadows", "my_evolutions", "op_evolutions")
KEYWORDS = ("WARD", "STORM", "RUSH", "BANE", "DRAIN", "AMBUSH", "BARRIER", "INTIMIDATE", "AURA")
TYPES = ("FOLLOWER", "AMULET", "COUNTDOWN_AMULET", "SPELL", "CREST", "FAITH")
CRAFTS = ("NEUTRAL", "FOREST", "SWORD", "RUNE", "DRAGON", "ABYSS", "HAVEN", "PORTAL")
PROPS = ("enhance_max", "enhance_n", "modes", "evolve_modes", "play_targets", "evolve_targets", "engage_cost",
         "attacks_per_turn", "skybound", "invoke", "accelerate_cost", "crystallize_cost", "listen_in_hand",
         "unplayable", "indestructible", "cant_attack", "ignores_ward", "related")
V2_EXTRA = ("share", "next_pp", "next_evolve")
TOKEN_V2 = TOKEN + V2_EXTRA
KCLOCK = ("me_kill_turns", "op_kill_turns", "kill_lead", "op_hp_x_kill_lead", "me_hp_x_kill_lead",
          "op_hp_x_me_near", "me_hp_x_op_near")
GLOBALS_KC = GLOBALS + KCLOCK
INPUTS = ("v1", "v2", "v2kc", "v2a")


def token_names(inputs: str = "v1") -> tuple:
    return TOKEN if inputs == "v1" else TOKEN_V2


def global_names(inputs: str = "v1") -> tuple:
    return GLOBALS_KC if inputs == "v2kc" else GLOBALS


ROLES = ("face", "removal", "heal", "draw", "ramp", "body")
RECURRING = ("face", "heal", "clear")


def static_names() -> list[str]:
    from svsim.core.script import HOOKS
    return (["cost", "atk", "life", "countdown", "is_token"] + [f"type_{t.lower()}" for t in TYPES]
            + [f"craft_{c.lower()}" for c in CRAFTS] + [f"kw_{k.lower()}" for k in KEYWORDS]
            + [f"hook_{h}" for h in HOOKS] + [f"prop_{p}" for p in PROPS] + [f"role_{r}" for r in ROLES]
            + [f"each_round_{r}" for r in RECURRING] + [f"each_round_evolved_{r}" for r in RECURRING]
            + ["evolve_face", "evolve_value", "super_face", "super_value"])


_STATIC: dict = {}


def static(defn) -> np.ndarray:
    """The card's static row (static_names()), float32; the same for every copy of the card, in any zone."""
    hit = _STATIC.get(defn.card_id)
    if hit is not None:
        return hit
    from svsim.core.enums import CardType, Craft, Keyword
    from svsim.core.script import HOOKS, script_for
    from svsim.learn import payoff, roles
    s = script_for(defn.card_id)
    row = [defn.cost, defn.atk, defn.life, defn.countdown or 0, float(defn.is_token)]
    row += [float(defn.type == getattr(CardType, t)) for t in TYPES]
    row += [float(defn.craft == getattr(Craft, c)) for c in CRAFTS]
    row += [float(bool(defn.keywords & getattr(Keyword, k))) for k in KEYWORDS]
    row += [float(getattr(s, h, None) is not None) for h in HOOKS]
    row += [max(s.enhance, default=0), len(s.enhance), (s.modes or (0, 0))[0], (s.evolve_modes or (0, 0))[0],
            len(s.play_targets), len(s.evolve_targets), s.engage_cost if s.engage_cost is not None else 0,
            s.attacks_per_turn, float(s.skybound), float(bool(s.invoke_at)),
            defn.accelerate.cost if defn.accelerate is not None else 0,
            defn.crystallize.cost if defn.crystallize is not None else 0, float(s.listen_in_hand),
            float(s.unplayable), float(s.indestructible), float(s.cant_attack), float(s.ignores_ward),
            len(defn.related)]
    row += list(roles.card_roles(defn))
    on_field = defn.goes_to_field or defn.type == CardType.CREST
    row += list(roles.recurring(defn)) if on_field else [0.0] * 3
    row += list(roles.recurring(defn, evolved=True)) if defn.is_follower else [0.0] * 3
    if defn.is_follower:
        try:
            row += list(payoff.evolve_parts(defn)) + list(payoff.evolve_parts(defn, True))
        except Exception:                        # a card the sandbox can't evolve: no payoff
            row += [0.0] * 4
    else:
        row += [0.0] * 4
    hit = _STATIC[defn.card_id] = np.asarray(row, dtype=np.float32)
    return hit


def _kw_bits(keywords) -> int:
    return int(keywords) & 0x1FF


def _counters(c) -> int:
    total = 0
    for v in (c.counters or {}).values():
        if isinstance(v, bool):
            total += int(v)
        elif isinstance(v, (int, float)):
            total += int(v)
        elif isinstance(v, (list, tuple, set)):
            total += len(v)
    return max(-100, min(total, 100))


_LAZY: dict = {}


def _lazy():
    """(Keyword, prop), imported once (the search calls _live a few hundred times a decision)."""
    got = _LAZY.get("kp")
    if got is None:
        from svsim.core.enums import Keyword
        from svsim.core.script import prop
        got = _LAZY["kp"] = (Keyword, prop)
    return got


def _live(state, c, zone: int) -> list:
    """A token for a card as it is now (hand, field, leader area)."""
    Keyword, prop = _lazy()
    follower = c.defn.is_follower
    fresh = c.entered_turn == state.turn
    left = max(c.max_attacks - c.attacks_made, 0) if follower and zone in (1, 4) else 0
    can = follower and zone in (1, 4) and left > 0 and not prop(c, "cant_attack")
    storm, rush = bool(c.keywords & Keyword.STORM), bool(c.keywords & Keyword.RUSH)
    return [c.defn.card_id, zone, 1, c.cost, c.atk, c.life, c.max_life, int(c.evolved), int(c.super_evolved),
            int(can and (not fresh or c.evolved or storm or rush)), int(can and (not fresh or storm)), left,
            c.countdown or 0, _counters(c), _kw_bits(c.keywords), int(c.silenced), int(bool(c.grants)),
            int(fresh and zone in (1, 4))]


def _pooled(cards, zone: int) -> list:
    """One token per card id with its count, at printed values (a deck, the unseen pool)."""
    counts: dict = {}
    defs: dict = {}
    for c in cards:
        counts[c.defn.card_id] = counts.get(c.defn.card_id, 0) + 1
        defs[c.defn.card_id] = c.defn
    out = []
    for cid in sorted(counts):
        d = defs[cid]
        out.append([cid, zone, counts[cid], d.cost, d.atk, d.life, d.life, 0, 0, 0, 0, 0, d.countdown or 0, 0,
                    _kw_bits(d.keywords), 0, 0, 0])
    return out


def _next(state, owner: int) -> tuple:
    """(next_pp, next_evolve) of `owner` (v2)."""
    rules = _LAZY.get("rules")
    if rules is None:
        from svsim.core.engine import EVOLVE_TURN, MAX_PP
        rules = _LAZY["rules"] = (EVOLVE_TURN, MAX_PP)
    EVOLVE_TURN, MAX_PP = rules
    pl = state.players[owner]
    return (min(pl.max_pp + 1, MAX_PP),
            int(pl.ep > 0 and pl.turns_taken + 1 >= EVOLVE_TURN[state.first == owner]))


def _live2(state, c, zone: int, nxt: tuple, attack_next: bool = True) -> list:
    """A v2 token for a card as it is now: v1's, the field's attack state as of the owner's next turn (not for
    v2a: attack_next False keeps v1's), and V2_EXTRA (share 0)."""
    row = _live(state, c, zone)
    if attack_next and zone in (1, 4) and c.defn.is_follower:
        prop = _lazy()[1]
        can = not prop(c, "cant_attack") and c.max_attacks > 0
        hf, hl, al = (1 + TOKEN.index(n) for n in ("can_hit_follower", "can_hit_leader", "attacks_left"))
        row[hf], row[hl], row[al] = int(can), int(can), c.max_attacks if can else 0
    return row + [0, nxt[0], nxt[1]]


def _pooled2(cards, zone: int, per: float, nxt: tuple) -> list:
    """v2 pooled tokens: v1's and V2_EXTRA, share = round(1000 x per x count)."""
    return [r + [int(round(1000 * per * r[2])), nxt[0], nxt[1]] for r in _pooled(cards, zone)]


def _pool_per(n_pool: int, n_hand: int, zone: int) -> float:
    """share per copy: my deck 1 / deck size; the unseen pool hand size / pool size."""
    if n_pool == 0:
        return 0.0
    return (1.0 if zone == 3 else n_hand) / n_pool


def encode(state, me: int, inputs: str = "v1"):
    """(cards int32 [T], tokens int16 [T, len(token_names(inputs))], globals float32 [len(global_names(inputs))])
    of `state` seen by `me` (module docstring)."""
    if inputs != "v1":
        return _encode2(state, me, inputs)
    p, o = state.players[me], state.players[1 - me]
    rows = [_live(state, c, 0) for c in p.hand]
    rows += [_live(state, c, 1) for c in p.field]
    rows += [_live(state, c, 2) for c in p.leader_area]
    rows += _pooled(p.deck_view(), 3)
    rows += [_live(state, c, 4) for c in o.field]
    rows += [_live(state, c, 5) for c in o.leader_area]
    rows += _pooled(list(o.hand) + list(o.deck_view()), 6)
    table = np.asarray(rows, dtype=np.int64).reshape(-1, len(TOKEN) + 1)
    cards = table[:, 0].astype(np.int32)
    tokens = np.clip(table[:, 1:], -32768, 32767).astype(np.int16)
    return cards, tokens, globals_of(state, me)


def _encode2(state, me: int, inputs: str):
    p, o = state.players[me], state.players[1 - me]
    mine, theirs = _next(state, me), _next(state, 1 - me)
    an = inputs != "v2a"
    rows = [_live2(state, c, 0, mine, an) for c in p.hand]
    rows += [_live2(state, c, 1, mine, an) for c in p.field]
    rows += [_live2(state, c, 2, mine, an) for c in p.leader_area]
    deck = p.deck_view()
    rows += _pooled2(deck, 3, _pool_per(len(deck), 0, 3), mine)
    rows += [_live2(state, c, 4, theirs, an) for c in o.field]
    rows += [_live2(state, c, 5, theirs, an) for c in o.leader_area]
    pool = list(o.hand) + list(o.deck_view())
    rows += _pooled2(pool, 6, _pool_per(len(pool), len(o.hand), 6), theirs)
    table = np.asarray(rows, dtype=np.int64).reshape(-1, len(TOKEN_V2) + 1)
    cards = table[:, 0].astype(np.int32)
    tokens = np.clip(table[:, 1:], -32768, 32767).astype(np.int16)
    return cards, tokens, globals_of(state, me, inputs)


def globals_of(state, me: int, inputs: str = "v1") -> np.ndarray:
    """global_names(inputs) of `state` seen by `me`, float32."""
    if inputs == "v2kc":
        from svsim.learn.features import _kclock_values
        return np.concatenate([globals_of(state, me), np.asarray(_kclock_values(state, me), dtype=np.float32)])
    p, o = state.players[me], state.players[1 - me]
    g = [p.leader_hp, o.leader_hp, p.leader_max_hp, o.leader_max_hp, p.pp, p.max_pp, o.max_pp, p.ep, p.sep,
         o.ep, o.sep, p.turns_taken, o.turns_taken, state.turn, len(p.deck_view()), len(o.deck_view()),
         len(p.hand), len(o.hand), float(p.bonus_ready), float(o.bonus_ready), float(state.first == me),
         p.shadows, o.shadows, p.evolutions, o.evolutions]
    return np.asarray(g, dtype=np.float32)


def live_and_pooled(state, me: int):
    """The encoding in two parts, for a caller that handles pooled cards itself (learn.setnet's search path):
    ([live token rows, card id first: hand, field, leader areas], {zone: [CardDef of every pooled card]})."""
    p, o = state.players[me], state.players[1 - me]
    rows = [_live(state, c, 0) for c in p.hand]
    rows += [_live(state, c, 1) for c in p.field]
    rows += [_live(state, c, 2) for c in p.leader_area]
    rows += [_live(state, c, 4) for c in o.field]
    rows += [_live(state, c, 5) for c in o.leader_area]
    return rows, {3: [c.defn for c in p.deck_view()], 6: [c.defn for c in o.hand] + [c.defn for c in o.deck_view()]}
