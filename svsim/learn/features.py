"""Generic position features for a learned evaluation.

Each side gets the same features (`me_*` for the player the position is scored
for, `op_*` for the opponent): leader defense, the board (followers' attack,
defense and keywords, amulets, crests), the hand (with what a field of
replayable followers is worth to a deck that returns them, evaluate.hand_count), unused evolution points, max
play points, the deck, how much the board threatens the enemy leader, and,
optionally, how much the hand and amulets could deal next turn by the
resource-flow planner (search.combo.next_turn_damage), and with all 10 play
points (what the hand is building towards). Nothing here is about a
particular deck: which features matter for which deck is what gets learned.
"""
from __future__ import annotations

import math

from svsim.core.enums import Keyword
from svsim.core.script import prop
from svsim.core.state import MAX_PP, GameState
from svsim.search.evaluate import effective_hp, good_crests, hand_count

SIDE = ["hp", "hp_sqrt", "hp_low", "followers", "atk", "life", "ward", "bane", "drain", "barrier", "evasive",
        "amulets", "amulet_cost", "crests", "hand", "ep", "sep", "max_pp", "deck_low", "deck_out",
        "board_threat", "board_lethal"]
POTENTIAL = ["potential", "potential_lethal", "potential10", "potential10_lethal"]
# Version 2 (the player's verdict on the evaluation, 2026-10-06: it couldn't see what the
# cards are for, what each side has left, or what the field does turn after turn): the
# hand's roles (learn.roles: face damage, removal, heal, draw, ramp, body; the opponent's
# hand as their share of the cards not seen yet, which is all the bot can know), the roles
# left in the deck (the opponent's: hand and deck, card counting from the known list),
# what the field and crests do each round (face, heal, clear), and the turns the leader
# lasts against what comes at it each turn (board attack past Ward, the opponent's field
# damage each round, a crest's burn).
SIDE2 = ["hand_face", "hand_removal", "hand_heal", "hand_draw", "hand_ramp", "hand_body",
         "pool_face", "pool_removal", "pool_heal", "pool_draw", "pool_ramp", "pool_body",
         "rec_face", "rec_heal", "rec_clear", "lasts"]


# Version 3 (2026-10-07; the player: the bot spends its evolution points as soon as it can and runs
# out in the long games; the test session's count of the player's games: they keep a point when a
# card that pays off an evolution is in hand but out of reach this turn, and spend it on that card
# within two turns, ahead or behind alike): each side's unused evolution and super-evolution points
# also enter multiplied by their context:
# - turns since that kind of evolution unlocked;
# - what spending the points on the coming turn could buy, split by kind (learn.payoff.evolve_parts:
#   measured from what evolving the card does, never a card list; the player: evolving a Storm
#   follower is 2 to the face, worth a lot when racing): the best face payoff and the best value
#   payoff of a follower the points could go to (on the field, not yet evolved that way, or in hand
#   and affordable then; a follower on the field that can still attack the leader gains its plain
#   attack), the face one also times "racing" (the enemy leader at 10 or less, or the board threatening
#   half its defense) and the value one also times the game's length (both leaders' defense);
# - the same for a follower in hand out of reach on the coming turn, divided by the turns until it
#   comes within reach (one play point a turn): a point is worth keeping most when the card can be
#   played the turn after;
# - a payoff follower still in the deck (the player: a point is also kept for a card not drawn yet):
#   over the next three turns, the chance it is first drawn that turn (one draw a turn, from the deck's
#   known contents; the opponent's from its cards not seen yet) times its payoff, times 1 if it is
#   affordable then (one more play point a turn) or 1 / the turns still missing, discounted 0.7 a turn;
#   the best such card;
# - how long the game still looks (own turns, both leaders' defense, both decks);
# - and, as a minor term, the leader-defense gap.
# The coming turn: the current one if it is the side's, else the next (one more play point). No term
# for the hand alone: cards in hand get no value of their own (docs/architecture.md, §9.2).
CONTEXT = ["since_unlock", "face_now", "face_now_race", "value_now", "value_now_long", "face_later",
           "value_later", "payoff_deck", "turn", "hp", "op_hp", "decks", "hp_lead"]
SIDE3 = [f"{pt}_x_{c}" for pt in ("ep", "sep") for c in CONTEXT]


def names(potential: bool, version: int = 1) -> list[str]:
    side = SIDE + (POTENTIAL if potential else []) + (SIDE2 if version >= 2 else [])
    extra = [f"me_{n}" for n in SIDE3] + [f"op_{n}" for n in SIDE3] if version >= 3 else []
    return [f"me_{n}" for n in side] + [f"op_{n}" for n in side] + extra + ["bias"]


# Features whose direction isn't up to the data: more defense for my leader is
# never worse (hp_low counts *low* defense, so it goes the other way), a sure
# lethal on board is never worse, an empty deck never better. Learned from games
# against one opponent, a model can pick up a confound (the learned Ramp model
# liked its own leader at 5 defense or less, from a card that sets its max
# defense to 1), so the fit keeps these signs (fit.fit, `signs`).
MONOTONE = {"hp": 1, "hp_sqrt": 1, "hp_low": -1, "board_lethal": 1, "potential_lethal": 1,
            "potential10_lethal": 1, "deck_out": -1, "lasts": 1}


def signs(potential: bool, version: int = 1) -> list[int]:
    """+1 / -1 where a coefficient must not be negative / positive, 0 where it is free."""
    out = []
    for n in names(potential, version):
        side, _, feature = n.partition("_")
        s = MONOTONE.get(feature, 0)
        out.append(s if side == "me" else -s if side == "op" else 0)
    return out


def _board_threat(state: GameState, side: int) -> int:
    """Attack `side`'s followers could put on the enemy leader next turn, minus enemy Ward defense."""
    p, enemy = state.players[side], state.players[1 - side]
    damage = sum(f.atk * max(1, f.max_attacks) for f in p.followers if not prop(f, "cant_attack"))
    damage -= sum(max(f.life, 0) for f in enemy.followers if f.keywords & Keyword.WARD)
    return max(damage, 0)


def _roles_sum_ordered(cards) -> list[float]:
    from svsim.learn.roles import _ROLES, card_roles
    # unrolled, the additions in the same order as a loop over the six (the same floats bit for bit)
    a0 = a1 = a2 = a3 = a4 = a5 = 0.0
    get = _ROLES.get
    for c in cards:
        d = c.defn
        r = get(d.card_id)
        if r is None:
            r = card_roles(d)
        a0 += r[0]
        a1 += r[1]
        a2 += r[2]
        a3 += r[3]
        a4 += r[4]
        a5 += r[5]
    return [a0, a1, a2, a3, a4, a5]


# _roles_sum by the multiset of card ids (speed round 3). Exact: every role value is a multiple of 1/8 (learn.roles:
# face, heal, draw and body are whole numbers, ramp counts halves, removal eighths, FOE_LIFE = 8), and adding such
# numbers well below 2**49 is exact in any order, so the sum doesn't depend on the cards' order (a deck reshuffled
# by determinize sums the same). _EIGHTHS checks each card's values once; a set with a card that isn't in eighths
# is summed in its own order as before and not kept.
_ROLE_SUMS: dict = {}
_ROLE_SUMS_MAX = 100_000
_EIGHTHS: dict = {}                   # card id -> whether its role values are multiples of 1/8 (and small)


def _in_eighths(defn) -> bool:
    hit = _EIGHTHS.get(defn.card_id)
    if hit is None:
        from svsim.learn.roles import card_roles
        hit = _EIGHTHS[defn.card_id] = all(abs(v) < 2 ** 20 and (v * 8).is_integer() for v in card_roles(defn))
    return hit


def _roles_sum(cards) -> list[float]:
    ids = [c.defn.card_id for c in cards]
    ids.sort()
    key = tuple(ids)
    hit = _ROLE_SUMS.get(key)
    if hit is None:
        hit = _roles_sum_ordered(cards)
        if all(_in_eighths(c.defn) for c in cards):
            if len(_ROLE_SUMS) >= _ROLE_SUMS_MAX:
                _ROLE_SUMS.clear()
            _ROLE_SUMS[key] = tuple(hit)
        return hit
    return list(hit)


_RECURRING_SUMS: dict = {}           # (card id, evolved) of the field and crests, in order -> the sums


def recurring_sum(p) -> list[float]:
    """What `p`'s field and crests do by themselves each round: (face, heal, clear). Kept by the cards' ids and
    evolved flags in order, which is all it reads (the same additions in the same order)."""
    from svsim.core.enums import CardType
    cards = list(p.field) + [c for c in p.leader_area if c.defn.type == CardType.CREST]
    key = tuple((c.defn.card_id, bool(getattr(c, "evolved", False))) for c in cards)
    hit = _RECURRING_SUMS.get(key)
    if hit is None:
        from svsim.learn.roles import recurring
        out = [0.0, 0.0, 0.0]
        for cid_evolved, c in zip(key, cards):
            for i, v in enumerate(recurring(c.defn, cid_evolved[1])):
                out[i] += v
        if len(_RECURRING_SUMS) >= 50_000:
            _RECURRING_SUMS.clear()
        hit = _RECURRING_SUMS[key] = tuple(out)
    return list(hit)


def resources(state: GameState, side: int, hidden: bool) -> list[float]:
    """The version-2 features of `side` (see SIDE2); `hidden`: its hand is unknown to the
    player the position is scored for."""
    from svsim.search.evaluate import burn, effective_hp
    p, enemy = state.players[side], state.players[1 - side]
    if hidden:
        pool = p.hand + p.deck_view()
        total = _roles_sum(pool)
        share = len(p.hand) / len(pool) if pool else 0.0
        hand = [v * share for v in total]
    else:
        hand, total = _roles_sum(p.hand), _roles_sum(p.deck_view())
    rec = recurring_sum(p)
    incoming = _board_threat(state, 1 - side) + recurring_sum(enemy)[0] + burn(p)
    lasts = min(effective_hp(p) / max(incoming, 1.0), 10.0)
    return hand + total + rec + [lasts]


def side_features(state: GameState, side: int, potential: bool, version: int = 1, hidden: bool = False) -> list[float]:
    p, enemy = state.players[side], state.players[1 - side]
    hp = effective_hp(p)                 # a crest that hurts its holder: the defense it will take
    followers = p.followers
    k = [f.keywords for f in followers]
    threat = _board_threat(state, side)
    out = [hp, math.sqrt(hp), float(hp <= 5), len(followers),
           sum(f.atk * (0.3 if prop(f, "cant_attack") else 1.0) for f in followers),
           sum(max(f.life, 0) for f in followers),
           sum(1 for x in k if x & Keyword.WARD), sum(1 for x in k if x & Keyword.BANE),
           sum(f.atk for f in followers if f.keywords & Keyword.DRAIN),
           sum(1 for x in k if x & Keyword.BARRIER),
           sum(1 for x in k if x & (Keyword.AMBUSH | Keyword.AURA | Keyword.INTIMIDATE)),
           sum(1 for c in p.field if c.defn.is_amulet), sum(c.defn.cost for c in p.field if c.defn.is_amulet),
           good_crests(p),
           hand_count(p), p.ep, p.sep, p.max_pp, float(len(p.deck_view()) <= 3), float(not p.deck_view()),
           min(threat, max(enemy.leader_hp, 0)), float(threat >= enemy.leader_hp)]
    if potential:
        from svsim.search.combo import next_turn_damage
        hp = max(enemy.leader_hp, 0)
        dmg = next_turn_damage(state, side, 300, board=False)
        full = next_turn_damage(state, side, 300, board=False, pp=10)
        out += [min(dmg, hp), float(dmg >= hp), min(full, hp), float(full >= hp)]
    if version >= 2:
        out += resources(state, side, hidden)
    return out


def context(state: GameState, side: int, hidden: bool, super_: bool = False) -> list[float]:
    """The CONTEXT values of `side`'s evolution points (super-evolution points with `super_`), each about
    0..1; `hidden`: its hand is unknown to the scorer (its share of the cards not seen yet stands in)."""
    return contexts(state, side, hidden)[1 if super_ else 0]


def contexts(state: GameState, side: int, hidden: bool) -> tuple[list[float], list[float]]:
    """context() for the evolution points and for the super-evolution points, in one pass."""
    from svsim.core.engine import EVOLVE_TURN, SUPER_EVOLVE_TURN
    from svsim.learn.payoff import PLAIN, both_parts
    from svsim.search.evaluate import threat
    p, enemy = state.players[side], state.players[1 - side]
    first = state.first == side
    coming = p.turns_taken + (0 if state.active == side else 1)
    pp = p.max_pp if state.active == side else min(p.max_pp + 1, 10)
    pp += 1 if p.bonus_ready else 0
    scale = 6.0                                    # payoff points to about 0..1
    best = [[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]   # per kind: face now, value now, face later, value later
    mine = state.active == side
    for f in p.followers:                          # on the field, not yet evolved that way
        parts = both_parts(f.defn)
        # can hit the enemy leader on the coming turn (this turn: not yet attacked, and not just played
        # unless it has Storm; next turn: any): its plain attack gain is that much to the face
        hits = not prop(f, "cant_attack") and (not mine or (
            f.attacks_made == 0 and (f.entered_turn != state.turn or bool(f.keywords & Keyword.STORM))))
        for k, super_ in ((0, False), (1, True)):
            if f.super_evolved or (f.evolved and not super_):
                continue
            face, value = parts[k]
            if hits:
                face = max(face, PLAIN[super_] / 2)
            b = best[k]
            b[0], b[1] = max(b[0], face), max(b[1], value)
    if hidden:                                     # the unseen cards: the same all turn, whatever the deal
        pool = p.hand + p.deck_view()
        key = (True, len(pool), len(p.hand), pp, _fingerprint(pool))
        hit = _UNSEEN.get(key)
        if hit is None:
            share = len(p.hand) / len(pool) if pool else 0.0
            hit = _remember(key, (_from_cards([(c, share) for c in pool if c.defn.is_follower], pp),
                                  deck_payoff(pool, pp, len(p.hand)) / 2.0))
        from_cards, in_deck = hit
    else:
        from_cards = _from_cards([(c, 1.0) for c in p.hand if c.defn.is_follower], pp)
        key = (False, len(p.deck_view()), 0, pp, _fingerprint(p.deck_view()))
        in_deck = _UNSEEN.get(key)
        if in_deck is None:
            in_deck = _remember(key, deck_payoff(p.deck_view(), pp) / 2.0)
    for b, c in zip(best, from_cards):
        b[:] = [max(x, y) for x, y in zip(b, c)]
    hp, op_hp = effective_hp(p), effective_hp(enemy)
    racing = float(op_hp <= 10 or threat(state, side) >= op_hp / 2)
    long = (hp + op_hp) / 40.0
    tail = [p.turns_taken / 10.0, hp / 20.0, op_hp / 20.0, (len(p.deck_view()) + len(enemy.deck_view())) / 60.0,
            (hp - op_hp) / 20.0]
    out = []
    for k, unlock in ((0, EVOLVE_TURN[first]), (1, SUPER_EVOLVE_TURN[first])):
        fn, vn, fl, vl = (x / scale for x in best[k])
        out.append([max(coming - unlock, 0) / 5.0 if coming >= unlock else 0.0,
                    fn, fn * racing, vn, vn * long, fl, vl, in_deck] + tail)
    return out[0], out[1]


_UNSEEN: dict = {}                     # contexts' card parts by (hidden, cards, hand, pp, fingerprint)


def _fingerprint(cards) -> tuple:
    """Which cards (id and current cost) are in `cards`, in any order: equal exactly for equal multisets.
    (A sum of tuple hashes was not: two Ramp decks of 31 differing in four cards each summed alike, and the
    cache gave one the other's value, 2026-10-07.)"""
    return tuple(sorted(c.defn.card_id * 1024 + c.cost for c in cards))


def _remember(key, value):
    """Keep `value` for contexts (the search asks the same deck and unseen cards again and again: about
    half of the version-3 features' time, docs/architecture.md §9.2 "留进化点")."""
    if len(_UNSEEN) > 50000:
        _UNSEEN.clear()
    _UNSEEN[key] = value
    return value


def _from_cards(cards, pp: int) -> list[list[float]]:
    """The best (face now, value now, face later, value later) over (card, weight) pairs, for evolving and
    super-evolving: playable with `pp` play points counts now, the rest later, less the further away."""
    from svsim.learn.payoff import both_parts
    best = [[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]
    for c, w in cards:
        soon = 1.0 if c.cost <= pp else 1.0 / (c.cost - pp)
        parts = both_parts(c.defn)
        for k in (0, 1):
            face, value = parts[k]
            b = best[k]
            if c.cost <= pp:
                b[0], b[1] = max(b[0], w * face), max(b[1], w * value)
            else:
                b[2], b[3] = max(b[2], w * face * soon), max(b[3], w * value * soon)
    return best


def first_draw(copies: int, size: int, turns: int = 3) -> list[float]:
    """The chance that the first of `copies` cards in a deck of `size` comes on each of the next `turns`
    draws (one a turn)."""
    out, none_yet = [], 1.0
    for k in range(turns):
        left = size - k
        if left <= 0 or none_yet <= 0:
            out.append(0.0)
            continue
        p = min(copies / left, 1.0)
        out.append(none_yet * p)
        none_yet *= 1 - p
    return out


def deck_payoff(deck, pp: int, skip: int = 0, turns: int = 3, discount: float = 0.7) -> float:
    """The best payoff follower still to be drawn from `deck` (see CONTEXT's payoff_deck): over the next
    `turns` turns, the chance it is first drawn then times its tier times its affordability then, discounted.
    `skip`: draws already known to go elsewhere (a hidden hand's cards among the unseen ones)."""
    from svsim.learn.payoff import tier
    counts = {}
    for c in deck:
        t = tier(c.defn)
        if t > 0:
            key = (c.defn.card_id, c.cost)          # copies at another cost count apart: any order, the same
            counts[key] = (counts[key][0] + 1, t, c.cost) if key in counts else (1, t, c.cost)
    best = 0.0
    size = len(deck) - skip
    for copies, t, cost in counts.values():
        value = 0.0
        for k, chance in enumerate(first_draw(copies, max(size, copies), turns)):
            short = cost - (pp + k)
            value += discount ** k * chance * t * (1.0 if short <= 0 else 1.0 / short)
        best = max(best, value)
    return best


def held_points(state: GameState, side: int, hidden: bool) -> list[float]:
    """The version-3 features of `side` (SIDE3)."""
    p = state.players[side]
    evo, sup = contexts(state, side, hidden)
    return [p.ep * c for c in evo] + [p.sep * c for c in sup]


def features(state: GameState, player: int, potential: bool = True, version: int = 1) -> list[float]:
    """The features of `state` scored for `player` (the opponent moves next)."""
    extra = held_points(state, player, False) + held_points(state, 1 - player, True) if version >= 3 else []
    return (side_features(state, player, potential, version) +
            side_features(state, 1 - player, potential, version, hidden=True) + extra + [1.0])


# Feature sets added by name (the C track, 2026-10-08, as registered in the analysis thread's audit of where the
# installed evaluators miss, analysis/evaluator-gaps/README.md section 4: the side to move second is overrated by
# about 9 points in the middle and late game, every card in hand that can't be paid next turn by about 2).
# Outside every version: a model that uses one records it (LinearValue.extras) and is encoded with it; models
# without it are unchanged. Both only read the position, and only my side.
# - "tempo" (3): t = min(the opponent's maximum play points on their coming turn, 10) - my maximum play points
#   this turn (0 at the end of the first player's turn, +1 at the end of the second player's), t x [my own turn
#   5-7] and t x [my own turn 8 or later].
# - "hand" (6): my hand's six role values (as me_hand_*) again with each card times min(1, (maximum play points
#   + 1) / its current cost), the play points capped at 10; the plain ones stay. The opponent's hand: not added.
EXTRAS = {
    "tempo": ["me_tempo", "me_tempo_x_mid", "me_tempo_x_late"],
    "hand": [f"me_handplay_{r}" for r in ("face", "removal", "heal", "draw", "ramp", "body")],
    "board": ["me_pressure", "me_hp_early", "me_hp_mid", "op_pressure", "op_hp_early", "op_hp_mid"],
    "hpphase": ["me_hp_early", "me_hp_mid", "op_hp_early", "op_hp_mid"],
    "hand_value": ["hand_value"],     # not me_hand_*: learn.phased.STOCK zeroes that prefix
    "clock": ["me_burst", "op_burst", "me_clock", "op_clock", "clock_lead"],
    "kclock": ["me_kill_turns", "op_kill_turns", "kill_lead", "op_hp_x_kill_lead", "me_hp_x_kill_lead",
               "op_hp_x_me_near", "me_hp_x_op_near"],
}
# - "board" (6, C3, the analysis thread's analysis/c3-threat/README.md section 4, 09f7ca2): for each side s (mine,
#   then the opponent's; e its enemy) pressure = min(_board_threat(e) / max(s's leader HP, 1), 1.5), then s's leader
#   HP x [the scored player's own turn <= 4] and x [5 <= that turn <= 7] (both sides by the scored player's turn).
#   The residuals: the existing features take HP and the incoming threat linearly, while their worth isn't.
#   Superseded by "hpphase" (analysis 3e6b4f2, section 6: with the existing board terms in the regression the
#   pressure slopes go away); kept for the cand-c3-board-* folders, for reference only.
# - "hpphase" (4, C3 revised): board without the two pressures: my HP x [the scored player's own turn <= 4] and
#   x [5 <= that turn <= 7], then the opponent's.
# - "hand_value" (1, the hand-value line, 2026-10-09; named hand_value, not me_hand_value, which STOCK's
#   me_hand_ prefix would zero in fitting): the student's H of my hand (learn.handvalue), the cards the
#   search can't know priced as one of their pool. It needs the student: the model that uses it carries one
#   (LinearValue.hv, read from <pairing>-hv.npz beside the model's file), learn.phased --hand-value for fitting;
#   called without one (extra_features(state, me, ("hand_value",))), SVSIM_HV names it (learn.handvalue.default_student).


def extra_names(extras) -> list[str]:
    return [n for e in extras for n in EXTRAS[e]]


def tempo_gap(state: GameState, player: int) -> int:
    from svsim.core.state import MAX_PP
    me, op = state.players[player], state.players[1 - player]
    return min(op.max_pp + 1, MAX_PP) - me.max_pp


_HAND_MEMO: dict = {}               # (play points, card id, cost, card id, cost, ...) -> the six sums
_HAND_MEMO_MAX = 200_000


def playable_hand_roles(state: GameState, player: int) -> list[float]:
    """Read at every leaf of the search, and a hand changes little within a decision: kept by (play points, each
    card's id and current cost in hand order), which is all the sums read. Summed in hand order from 0.0 as
    before, so the values are bit for bit the same (tests/test_learn.py)."""
    p = state.players[player]
    pp = p.max_pp + 1
    if pp > MAX_PP:
        pp = MAX_PP
    key = [pp]
    for c in p.hand:
        key.append(c.defn.card_id)
        key.append(c.cost)
    key = tuple(key)
    hit = _HAND_MEMO.get(key)
    if hit is None:
        if len(_HAND_MEMO) >= _HAND_MEMO_MAX:
            _HAND_MEMO.clear()
        hit = _HAND_MEMO[key] = _hand_sums(p.hand, pp)
    return list(hit)


def _hand_sums(hand, pp: int) -> tuple:
    from svsim.learn.roles import card_roles
    out = [0.0] * 6
    for c in hand:
        f = 1.0 if c.cost <= 0 else min(1.0, pp / c.cost)
        for i, v in enumerate(card_roles(c.defn)):
            out[i] += v * f
    return tuple(out)


def _tempo_values(state: GameState, player: int) -> list[float]:
    t = float(tempo_gap(state, player))
    turn = state.players[player].turns_taken
    return [t, t * (5 <= turn <= 7), t * (turn >= 8)]


# Each named set's values for `player`, in the order of its names in EXTRAS. A new set (C3's "board", once the
# analysis thread fixes its dimensions) is one function here and its names in EXTRAS: learn.phased --features,
# LinearValue.extras (recorded with the model and read back by name) and the hold-out split need nothing more.
def _board_values(state: GameState, player: int) -> list[float]:
    turn = state.players[player].turns_taken
    early, mid = float(turn <= 4), float(5 <= turn <= 7)
    out = []
    for side in (player, 1 - player):
        hp = state.players[side].leader_hp
        out += [min(_board_threat(state, 1 - side) / max(hp, 1), 1.5), hp * early, hp * mid]
    return out


def _hpphase_values(state: GameState, player: int) -> list[float]:
    turn = state.players[player].turns_taken
    early, mid = float(turn <= 4), float(5 <= turn <= 7)
    me, op = state.players[player].leader_hp, state.players[1 - player].leader_hp
    return [me * early, me * mid, op * early, op * mid]


EXTRA_FNS = {"tempo": _tempo_values, "hand": playable_hand_roles, "board": _board_values,
             "hpphase": _hpphase_values}


def _hand_value(state: GameState, player: int, hv=None) -> list[float]:
    if hv is None:                                 # called without a model (the analysis line's checks)
        from svsim.learn.handvalue import default_student
        hv = default_student(state, player)
    return [hv.value(state, player)]


EXTRA_FNS["hand_value"] = _hand_value


# - "clock" (5, turn-level step 1, the architecture thread 2026-10-09 11:12Z): each side's burst on its next turn,
#   roughly - the attack of its followers that can attack, plus the most direct damage (learn.roles' face value,
#   plus a Storm follower's attack) it can pay for with next turn's play points: mine from my hand (a knapsack over
#   at most 9 cards and 10 points), the opponent's as their hand size times the mean affordable direct damage of
#   their unseen pool (their hand and deck as one pool: never the determinized hand), capped at 20; then the turns
#   each side needs to kill at that rate (the other leader's HP / the burst, at most 10) and the lead (the
#   opponent's turns minus mine). No search; a few microseconds a leaf.
_DIRECT: dict = {}


def _direct(defn) -> float:
    hit = _DIRECT.get(defn.card_id)
    if hit is None:
        from svsim.core.enums import Keyword
        from svsim.learn.roles import card_roles
        hit = float(card_roles(defn)[0])
        if defn.is_follower and defn.keywords & Keyword.STORM:
            hit += defn.atk
        _DIRECT[defn.card_id] = hit
    return hit


def _best_direct(cards, budget: int) -> float:
    """The most direct damage of a subset of (cost, damage) whose costs fit the budget (0/1 knapsack)."""
    best = [0.0] * (budget + 1)
    for cost, dmg in cards:
        if dmg <= 0 or cost > budget:
            continue
        cost = max(cost, 0)
        for b in range(budget, cost - 1, -1):
            v = best[b - cost] + dmg
            if v > best[b]:
                best[b] = v
    return best[budget]


def _clock_values(state: GameState, player: int) -> list[float]:
    from svsim.core.script import prop
    me, op = state.players[player], state.players[1 - player]
    board = lambda p: float(sum(f.atk for f in p.followers if not prop(f, "cant_attack")))
    me_burst = board(me) + _best_direct([(c.cost, _direct(c.defn)) for c in me.hand], min(me.max_pp + 1, MAX_PP))
    pool = op.hand + op.deck_view()
    op_burst = board(op)
    if pool and op.hand:
        budget = min(op.max_pp + 1, MAX_PP)
        mean = sum(_direct(c.defn) for c in pool if c.cost <= budget) / len(pool)
        op_burst += min(len(op.hand) * mean, 20.0)
    me_clock = min(op.leader_hp / max(me_burst, 1.0), 10.0)
    op_clock = min(me.leader_hp / max(op_burst, 1.0), 10.0)
    return [me_burst, op_burst, me_clock, op_clock, op_clock - me_clock]


EXTRA_FNS["clock"] = _clock_values


# - "kclock" (7, the lethal clock, the architecture thread 2026-10-10 10:38Z; the scored player has just ended the
#   turn, so the opponent's turn comes first): the turns each side needs to kill the other at its next turn's damage,
#   the difference, and crosses with the leaders' defense, so a point of face damage is worth more or less with the
#   clock. No card ids and no card values set by hand: a card's damage is the planner's own measurement of it
#   (search.combo.profile_at: face damage, and a Storm follower's attacks). The planner's whole search
#   (combo.next_turn_damage) costs about 0.85 ms a turn end at 300 nodes, ten times the version-2 features, so it is
#   not used here.
#   - A side's damage: the attack of its followers that can attack, less the defense of the enemy's Ward followers,
#     plus the hand's: mine, the most direct damage of a subset of my hand I can pay for next turn (a knapsack, as
#     "clock"); the opponent's, their hand size times the mean direct damage of the cards of their unseen pool (hand
#     and deck as one pool, never the determinized hand) they could pay for, capped at 20.
#   - turns = the other leader's defense / max(damage, 1), at most 10; lead = the opponent's turns - mine; then each
#     leader's defense x lead, and each leader's defense x near(the turns the other side needs to kill it), with
#     near(t) = min(max(3 - t, 0), 2) / 2 (1 at one turn or less, 0 from three turns on).
_FACE_AT: dict = {}


def _face_at(defn, pp: int) -> float:
    """The most direct damage to the enemy leader of one play of `defn` with `pp` play points (combo.profile_at)."""
    key = (defn.card_id, pp)
    hit = _FACE_AT.get(key)
    if hit is None:
        from svsim.search.combo import COMBO_STEPS, profile_at
        hit = 0.0
        for variants in profile_at(defn, False, pp):
            e = variants[0]
            storm = (e.base + e.per_combo * COMBO_STEPS[0]) * max(e.attacks, 1) if e.reach == 2 else 0
            hit = max(hit, float(e.face + max(storm, 0)))
        _FACE_AT[key] = hit
    return hit


def _near(t: float) -> float:
    return min(max(3.0 - t, 0.0), 2.0) / 2.0


def _board_damage(p, enemy) -> float:
    atk = sum(f.atk for f in p.followers if not prop(f, "cant_attack"))
    wall = sum(max(f.life, 0) for f in enemy.followers if f.keywords & Keyword.WARD)
    return float(max(atk - wall, 0))


def _kclock_values(state: GameState, player: int) -> list[float]:
    me, op = state.players[player], state.players[1 - player]
    me_hp, op_hp = float(max(effective_hp(me), 0)), float(max(effective_hp(op), 0))
    budget = min(me.max_pp + 1, MAX_PP)
    me_dmg = _board_damage(me, op) + _best_direct([(c.cost, _face_at(c.defn, budget)) for c in me.hand], budget)
    op_dmg = _board_damage(op, me)
    pool = op.hand + op.deck_view()
    if pool and op.hand:
        budget = min(op.max_pp + 1, MAX_PP)
        mean = sum(_face_at(c.defn, budget) for c in pool if c.cost <= budget) / len(pool)
        op_dmg += min(len(op.hand) * mean, 20.0)
    me_turns = min(op_hp / max(me_dmg, 1.0), 10.0)
    op_turns = min(me_hp / max(op_dmg, 1.0), 10.0)
    lead = op_turns - me_turns
    return [me_turns, op_turns, lead, op_hp * lead, me_hp * lead, op_hp * _near(me_turns), me_hp * _near(op_turns)]


EXTRA_FNS["kclock"] = _kclock_values


def extra_features(state: GameState, player: int, extras, hv=None) -> list[float]:
    """The named feature sets' values for `player` (EXTRAS), in the order of extra_names. `hv`: the student
    "hand_value" reads (learn.handvalue.HandValue)."""
    out = []
    for e in extras:
        if e not in EXTRA_FNS:
            raise ValueError(f"unknown feature set {e!r}")
        values = EXTRA_FNS[e](state, player, hv) if e == "hand_value" else EXTRA_FNS[e](state, player)
        assert len(values) == len(EXTRAS[e]), e
        out += values
    return out
