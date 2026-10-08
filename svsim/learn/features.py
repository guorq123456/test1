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
from svsim.core.state import GameState
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


def _roles_sum(cards) -> list[float]:
    from svsim.learn.roles import card_roles
    out = [0.0] * 6
    for c in cards:
        for i, v in enumerate(card_roles(c.defn)):
            out[i] += v
    return out


def recurring_sum(p) -> list[float]:
    """What `p`'s field and crests do by themselves each round: (face, heal, clear)."""
    from svsim.core.enums import CardType
    from svsim.learn.roles import recurring
    out = [0.0, 0.0, 0.0]
    for c in list(p.field) + [c for c in p.leader_area if c.defn.type == CardType.CREST]:
        for i, v in enumerate(recurring(c.defn, bool(getattr(c, "evolved", False)))):
            out[i] += v
    return out


def resources(state: GameState, side: int, hidden: bool) -> list[float]:
    """The version-2 features of `side` (see SIDE2); `hidden`: its hand is unknown to the
    player the position is scored for."""
    from svsim.search.evaluate import burn, effective_hp
    p, enemy = state.players[side], state.players[1 - side]
    if hidden:
        pool = p.hand + p.deck
        total = _roles_sum(pool)
        share = len(p.hand) / len(pool) if pool else 0.0
        hand = [v * share for v in total]
    else:
        hand, total = _roles_sum(p.hand), _roles_sum(p.deck)
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
           hand_count(p), p.ep, p.sep, p.max_pp, float(len(p.deck) <= 3), float(not p.deck),
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
        pool = p.hand + p.deck
        key = (True, len(pool), len(p.hand), pp, _fingerprint(pool))
        hit = _UNSEEN.get(key)
        if hit is None:
            share = len(p.hand) / len(pool) if pool else 0.0
            hit = _remember(key, (_from_cards([(c, share) for c in pool if c.defn.is_follower], pp),
                                  deck_payoff(pool, pp, len(p.hand)) / 2.0))
        from_cards, in_deck = hit
    else:
        from_cards = _from_cards([(c, 1.0) for c in p.hand if c.defn.is_follower], pp)
        key = (False, len(p.deck), 0, pp, _fingerprint(p.deck))
        in_deck = _UNSEEN.get(key)
        if in_deck is None:
            in_deck = _remember(key, deck_payoff(p.deck, pp) / 2.0)
    for b, c in zip(best, from_cards):
        b[:] = [max(x, y) for x, y in zip(b, c)]
    hp, op_hp = effective_hp(p), effective_hp(enemy)
    racing = float(op_hp <= 10 or threat(state, side) >= op_hp / 2)
    long = (hp + op_hp) / 40.0
    tail = [p.turns_taken / 10.0, hp / 20.0, op_hp / 20.0, (len(p.deck) + len(enemy.deck)) / 60.0,
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


# Feature sets added by name (the C track, 2026-10-08, from the analysis thread's audit of where the installed
# evaluators miss: the side to move second is overrated by about 9 points in the middle and late game, every
# card in hand that can't be paid next turn by about 2). Outside every version: a model that uses one records
# it (LinearValue.extras) and is encoded with it; models without it are unchanged. Both only read the position.
# - "tempo": the opponent's maximum play points on their coming turn minus mine this turn (0 at the end of the
#   first player's turn, +1 at the end of the second player's; the engine's cap of 10), and that gap times each
#   stage of the game by my own turn count (1-4, 5-7, 8+, the audit's stages).
# - "hand": the hand's roles (learn.roles) with each card discounted by whether it can be played next turn:
#   times min(1, (maximum play points + 1) / its cost), the play points capped at 10; the opponent's hand as its
#   share of the cards not seen yet, as for the version-2 hand roles.
# - "handsplit": the same roles split into the cards payable next turn (cost <= maximum play points + 1) and the
#   others, instead of discounting.
STAGES = (("early", 1, 4), ("mid", 5, 7), ("late", 8, 99))
ROLE_NAMES = ("face", "removal", "heal", "draw", "ramp", "body")
EXTRAS = {
    "tempo": ["tempo"] + [f"tempo_x_{s}" for s, _, _ in STAGES],
    "hand": [f"{side}_handplay_{r}" for side in ("me", "op") for r in ROLE_NAMES],
    "handsplit": [f"{side}_hand{kind}_{r}" for side in ("me", "op") for kind in ("now", "later") for r in ROLE_NAMES],
}


def extra_names(extras) -> list[str]:
    return [n for e in extras for n in EXTRAS[e]]


def tempo_gap(state: GameState, player: int) -> int:
    from svsim.core.state import MAX_PP
    me, op = state.players[player], state.players[1 - player]
    return min(op.max_pp + 1, MAX_PP) - me.max_pp


def _next_pp(p) -> int:
    from svsim.core.state import MAX_PP
    return min(p.max_pp + 1, MAX_PP)


def _hand_roles(state: GameState, side: int, hidden: bool, split: bool) -> list[float]:
    from svsim.learn.roles import card_roles
    p = state.players[side]
    pp = _next_pp(p)
    cards, scale = (p.hand + p.deck, len(p.hand) / max(len(p.hand) + len(p.deck), 1)) if hidden else (p.hand, 1.0)
    now, later = [0.0] * 6, [0.0] * 6
    for c in cards:
        roles = card_roles(c.defn)
        if split:
            target = now if c.cost <= pp else later
            for i, v in enumerate(roles):
                target[i] += v * scale
        else:
            f = 1.0 if c.cost <= 0 else min(1.0, pp / c.cost)
            for i, v in enumerate(roles):
                now[i] += v * f * scale
    return now + later if split else now


def extra_features(state: GameState, player: int, extras) -> list[float]:
    """The named feature sets' values for `player` (EXTRAS), in the order of extra_names."""
    out = []
    for e in extras:
        if e == "tempo":
            gap = tempo_gap(state, player)
            turn = state.players[player].turns_taken
            out += [float(gap)] + [float(gap) * (lo <= turn <= hi) for _, lo, hi in STAGES]
        elif e in ("hand", "handsplit"):
            out += _hand_roles(state, player, False, e == "handsplit") + _hand_roles(state, 1 - player, True,
                                                                                      e == "handsplit")
        else:
            raise ValueError(f"unknown feature set {e!r}")
    return out
