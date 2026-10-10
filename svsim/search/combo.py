"""Resource-flow lethal planning: understand how a hand turns play points into
damage, plan on that, and let the engine check the plan.

The player's idea, for combo decks such as Rhinoceroach Forest, where exact
search drowns in orderings: a strong player doesn't try every order, they
count resources ("10 play points: three 1-cost cards, Rhinoceroach for 4,
Bug Alert it back, Rhinoceroach again for 6"). This module does the same in
three steps.

1. Profile each card by playing it in a sandbox (`profile`): net play points,
   cards it adds to hand, cards it draws, whether it returns another allied
   card on the field to hand, direct damage to the enemy leader, damage to
   enemy followers (to a selected one, split oldest first, to all, or to a
   random one), and, for a follower, its attack as base + per_combo * Combo,
   its defense and whether it can attack this turn (the leader, or followers
   only). Effects are measured at Combo 1, 3 and 5. Engage and evolve effects
   are profiled the same way, and cards in hand that get cheaper when an
   allied follower leaves the field (`leave_discount`). Nothing here is
   written per card: the engine measures it.
2. Search an abstract position made only of those resources (play points,
   Combo, hand, allied followers, amulets that can be engaged, evolution and
   bonus play points, enemy followers with their Ward) for the most damage
   this turn. Enemy Ward must be removed before anything hits the leader:
   by attacks (a super-evolved follower takes no damage on its turn, and
   knocks back 1 when it destroys a follower), by targeted or split damage,
   and by random damage only when there is a single enemy follower. Drawn
   cards take a hand slot but are never played (they are unknown), and a
   card with Fuse (Garden's Allure) can take cards from a full hand to make
   room.
3. Translate the best plan back into real actions and play them in the
   engine; only a plan that wins there counts. If it drew cards or hit random
   targets, it must win on 16 other deck orders and random outcomes too.

Limits: abilities of cards already in play that react to the plan (listeners)
are not modelled, except cost reductions in hand; nor returning amulets to
hand. When a plan fails, `solve` falls back to exact search.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from itertools import combinations
import random
import time

from svsim.cards import demo
from svsim.cards.pool import POOL
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Engage, Evolve, Fuse, Mulligan, PlayCard, UseBonusPP
from svsim.core.carddef import CardDef
from svsim.core.engine import (BONUS_REFRESH_TURN, EVOLVE_TURN, SUPER_EVOLVE_TURN, _signature, apply,
                               legal_actions, new_game, resolve_queue)
from svsim.core.enums import Keyword, Phase
from svsim.core.script import prop, script_for
from svsim.core.state import FIELD_LIMIT, HAND_LIMIT, MAX_PP, CardInstance, GameState, leader_uid
from svsim.search.lethal import LethalSearch, hidden_info


@dataclass(frozen=True)
class Effect:
    """One way of playing (or engaging, evolving) a card, as measured."""
    paid: int                 # play points paid
    recovered: int            # play points recovered
    added: tuple              # (card id, cost) of cards added to hand (not drawn)
    bounce: bool              # returns another allied card on the field to hand
    face: int                 # direct damage to the enemy leader
    base: int = 0             # (follower) attack: base + per_combo * Combo
    per_combo: int = 0
    attacks: int = 0          # (follower) attacks it has this turn
    buff: int = 0             # attack given to the selected allied follower
    modes: tuple = ()
    gone: bool = False        # (Engage) the amulet destroys itself
    life: int = 0             # (follower) defense when it lands
    reach: int = 0            # (follower) 0: can't attack this turn, 1: followers only, 2: the leader too
    drawn: int = 0            # cards drawn from the deck
    hit: int = 0              # damage (or defense lost) dealt to enemy followers:
    hit_per_combo: int = 0    #   hit + hit_per_combo * Combo (+ hit_per_hand * cards in hand)
    hit_per_hand: int = 0
    spread: str = ""          # how it lands: "target", "split" (oldest first), "all", "random"
    pierce: bool = False      # it lowers defense without dealing damage, so Barrier doesn't stop it


# --- profiling -------------------------------------------------------------------------

def _sandbox(combo: int, pp: int = 10, hand: int = 0, max_pp: int | None = None):
    """Player 0 to act with `pp` play points, an allied follower to return to hand
    (the anchor), two harmless enemy followers (0/30, oldest first) to see how
    damage to followers lands, and `hand` cards in hand."""
    state = new_game([demo.FOOTMAN] * 40, [demo.FOOTMAN] * 40, seed=0, first=0)
    apply(state, Mulligan(()))
    apply(state, Mulligan(()))
    p = state.players[0]
    p.hand.clear()
    state.players[1].hand.clear()
    p.max_pp = p.pp = pp
    if max_pp is not None:                 # play points left below the maximum (profile_at: Overflow reads the max)
        p.max_pp = max(max_pp, pp)
    p.combo = combo
    p.turns_taken = 10                     # evolution unlocked
    anchor = E.summon(state, 0, demo.FOOTMAN)
    anchor.entered_turn = -1
    for _ in range(2):
        dummy = E.summon(state, 1, demo.FOOTMAN)
        dummy.atk, dummy.life, dummy.max_life = 0, 30, 30
    for _ in range(hand):
        E.add_to_hand(state, 0, demo.FOOTMAN)
    return state, anchor


def _reach(state: GameState, f: CardInstance) -> int:
    """0: can't attack this turn, 1: followers only, 2: the leader too (Ward aside)."""
    if prop(f, "cant_attack"):
        return 0
    if f.entered_turn != state.turn or f.keywords & Keyword.STORM:
        return 2
    return 1 if f.evolved or f.keywords & Keyword.RUSH else 0


def _measure(before: GameState, after: GameState, anchor: CardInstance, deck_uids: set,
             played: CardInstance | None, targets: tuple = ()) -> dict:
    me, now = before.players[0], after.players[0]
    old_hand = {c.uid for c in me.hand}
    new = [c for c in now.hand if c.uid not in old_hand]
    drawn = sum(1 for c in new if c.uid in deck_uids)
    added = tuple(sorted((c.defn.card_id, c.cost) for c in new
                         if c.uid not in deck_uids and c.defn.card_id != anchor.defn.card_id))
    bounce = after.on_field(anchor.uid) is None and any(
        c.defn == anchor.defn and c.uid not in deck_uids for c in new)
    follower = None
    if played is not None:
        inst = after.on_field(played.uid)
        if inst is not None and inst.defn.is_follower:
            follower = (inst.atk, inst.life, max(0, inst.max_attacks - inst.attacks_made), _reach(after, inst))
    foes = before.players[1].followers
    hits = [(d.life - after.on_field(d.uid).life) if after.on_field(d.uid) is not None else 99 for d in foes]
    hit, spread = 0, ""
    if any(hits):
        chosen = [i for i, d in enumerate(foes) if d.uid in targets]
        if chosen:
            hit, spread = hits[chosen[0]], "target"
        elif before.rng.getstate() != after.rng.getstate():
            hit, spread = sum(hits), "random"
        elif len(set(hits)) == 1:
            hit, spread = hits[0], "all"
        else:
            hit, spread = sum(hits), "split"
    anchor_after = after.on_field(anchor.uid)
    return dict(added=added, drawn=drawn, bounce=bounce, follower=follower, hit=hit, spread=spread,
                face=before.players[1].leader_hp - after.players[1].leader_hp,
                buff=(anchor_after.atk - anchor.atk) if anchor_after is not None else 0)


def _pierces(state: GameState, action) -> bool:
    """Whether the action still lowers enemy followers' defense when they have Barrier
    (Eradicating Arrow's -0/-1 does; damage doesn't)."""
    s = state.clone()
    for d in s.players[1].followers:
        d.keywords |= Keyword.BARRIER
    lives = {d.uid: d.life for d in s.players[1].followers}
    apply(s, action)
    return any(s.on_field(uid) is None or s.on_field(uid).life < life for uid, life in lives.items())


COMBO_STEPS = (1, 3, 5)     # Combo values (counting the card) at which cards are measured


def _slope(values: list) -> int:
    """Per-Combo growth if the measurements lie on a line through COMBO_STEPS, else 0."""
    span = COMBO_STEPS[-1] - COMBO_STEPS[0]
    rise = values[-1] - values[0]
    if rise <= 0 or rise % span:
        return 0
    k = rise // span
    ok = all(v == values[0] + k * (c - COMBO_STEPS[0]) for c, v in zip(COMBO_STEPS, values))
    return k if ok else 0


def _fuse_copy(state: GameState, card: CardInstance) -> bool:
    """Fuse a second copy of the card into it, if its Fuse takes it."""
    script = script_for(card.defn.card_id)
    if script.fuse_filter is None:
        return False
    fodder = E.add_to_hand(state, 0, card.defn)
    if not script.fuse_filter(fodder):
        state.players[0].hand.remove(fodder)
        return False
    apply(state, Fuse(card.uid, (fodder.uid,)))
    return True


@lru_cache(maxsize=None)
def profile(defn: CardDef, fused: bool = False) -> tuple[tuple[Effect, ...], ...]:
    """The ways of playing `defn` (one per mode / target choice), each as Effects
    measured at Combo 1, 3 and 5 in a sandbox with 10 play points, so Combo
    thresholds and Combo scaling show up. Use `at_combo` to pick one. With
    `fused`, the card has had a card fused to it first."""
    return _profile(defn, fused, 10, True)


@lru_cache(maxsize=None)
def profile_at(defn: CardDef, fused: bool, pp: int, cap: int = 10) -> tuple[tuple[Effect, ...], ...]:
    """`profile` measured with `pp` play points (at most 10), its play points as the engine spends them: Enhance
    is forced when affordable, so a 0-cost card with Enhance (1) costs 1 and does its enhanced effect when there is
    a play point, and its plain one when there isn't (`recovered` goes below 0 for the extra paid). The ticker
    search's (_Tickers); the plain search keeps `profile`. `cap`: the maximum play points (Overflow and the like
    read it, not the play points left)."""
    return _profile(defn, fused, max(0, min(pp, 10)), False, min(max(cap, pp), 10))


def _profile(defn: CardDef, fused: bool, pp_avail: int, clamp: bool, max_pp: int | None = None):
    measured = []
    for combo_after in COMBO_STEPS:
        state, anchor = _sandbox(combo_after - 1, pp_avail, max_pp=max_pp)
        card = E.add_to_hand(state, 0, defn)
        if fused and not _fuse_copy(state, card):
            return _profile(defn, False, pp_avail, clamp, max_pp)
        rows = {}
        for action in legal_actions(state):
            if not isinstance(action, PlayCard) or action.uid != card.uid:
                continue
            s = state.clone()
            deck = {c.uid for c in s.players[0].deck_view()}
            pp = s.players[0].pp
            apply(s, action)
            m = _measure(state, s, anchor, deck, card, action.targets)
            m["pierce"] = m["hit"] > 0 and _pierces(state, action)
            m["paid"] = card.cost
            m["recovered"] = max(0, s.players[0].pp - (pp - card.cost)) if clamp else s.players[0].pp - (pp - card.cost)
            rows[(action.modes, action.targets)] = m
        measured.append(rows)
    out = []
    for key, first in measured[0].items():
        ms = [rows.get(key, first) for rows in measured]
        fs = [m["follower"] for m in ms]
        per_combo = _slope([f[0] for f in fs]) if all(fs) else 0
        hit_per_combo = _slope([m["hit"] for m in ms])
        variants = []
        for combo_after, m, f in zip(COMBO_STEPS, ms, fs):
            variants.append(Effect(
                m["paid"], m["recovered"], m["added"], m["bounce"], m["face"],
                base=(f[0] - per_combo * combo_after) if f else 0, per_combo=per_combo if f else 0,
                attacks=f[2] if f else 0, buff=m["buff"], modes=key[0], life=f[1] if f else 0,
                reach=f[3] if f else 0, drawn=m["drawn"], hit=m["hit"] - hit_per_combo * combo_after,
                hit_per_combo=hit_per_combo, spread=m["spread"], pierce=m["pierce"]))
        out.append(tuple(variants))
    return tuple(dict.fromkeys(out))


def at_combo(variants: tuple[Effect, ...], combo_after: int) -> Effect:
    """The measured Effect for the highest measured Combo not above `combo_after`."""
    best = variants[0]
    for step, e in zip(COMBO_STEPS, variants):
        if step <= combo_after:
            best = e
    return best


@lru_cache(maxsize=None)
def engage_profile(defn: CardDef) -> Effect | None:
    script = script_for(defn.card_id)
    if script.engage is None or script.engage_cost is None:
        return None
    state, anchor = _sandbox(0)
    amulet = E.summon(state, 0, defn)
    resolve_queue(state)                    # what entering does (Analyzing Artifact draws) first
    best = None
    for action in legal_actions(state):
        if not isinstance(action, Engage) or action.uid != amulet.uid:
            continue
        s = state.clone()
        deck = {c.uid for c in s.players[0].deck_view()}
        apply(s, action)
        m = _measure(state, s, anchor, deck, None, action.targets)
        e = Effect(script.engage_cost, 0, m["added"], m["bounce"], m["face"], buff=m["buff"],
                   gone=s.in_play(amulet.uid) is None, drawn=m["drawn"])
        if best is None or (e.bounce, e.buff, e.face) > (best.bounce, best.buff, best.face):
            best = e
    return best


@lru_cache(maxsize=None)
def evolve_profile(defn: CardDef, super_: bool) -> tuple[Effect, ...]:
    """What evolving a follower of this kind with points does besides +2/+2 (+3/+3),
    one Effect per choice of mode and target: play points recovered (Baby
    Carbuncle: 3), cards added or drawn, damage (Glade: split, as much as the
    cards in hand, measured with 0 and 4 cards in hand)."""
    rows = []
    for hand in (0, 4):
        state, anchor = _sandbox(0, hand=hand)
        state.players[0].pp = 0             # room to recover play points
        inst = E.summon(state, 0, defn)
        resolve_queue(state)                # its entering effects first: a state is cloned between actions
        inst.entered_turn = -1
        found = {}
        for action in legal_actions(state):
            if not isinstance(action, Evolve) or action.uid != inst.uid or action.super_ != super_:
                continue
            s = state.clone()
            deck = {c.uid for c in s.players[0].deck_view()}
            apply(s, action)
            m = _measure(state, s, anchor, deck, None, action.targets)
            m["pierce"] = m["hit"] > 0 and _pierces(state, action)
            found[(action.modes, action.targets)] = (m, s.players[0].pp)
        rows.append(found)
    out = []
    for key, (m, pp) in rows[0].items():
        m4 = rows[1].get(key, (m, pp))[0]
        per_hand = max(0, (m4["hit"] - m["hit"]) // 4)
        out.append(Effect(0, pp, m["added"], m["bounce"], m["face"], buff=m["buff"], modes=key[0],
                          drawn=m["drawn"], hit=m["hit"], hit_per_hand=per_hand,
                          spread=m["spread"] or m4["spread"], pierce=m["pierce"] or m4["pierce"]))
    return tuple(dict.fromkeys(out)) or (Effect(0, 0, (), False, 0),)


def recovery(defn: CardDef, super_: bool) -> int:
    """Most play points evolving (super_: super-evolving) this follower recovers."""
    return max(e.recovered for e in evolve_profile(defn, super_))


@lru_cache(maxsize=None)
def leave_discount(defn: CardDef) -> int:
    """How much cheaper this card gets in hand when an allied follower leaves the
    field (Bayle: 1)."""
    state, anchor = _sandbox(0)
    card = E.add_to_hand(state, 0, defn)
    before = card.cost
    E.destroy(state, anchor)
    resolve_queue(state)
    return max(0, before - card.cost)


@lru_cache(maxsize=None)
def fuses(card: CardDef, fodder: CardDef) -> bool:
    """Whether `fodder` can be fused to `card`."""
    script = script_for(card.card_id)
    if script.fuse_filter is None:
        return False
    state, _ = _sandbox(0)
    return bool(script.fuse_filter(E.add_to_hand(state, 0, fodder)))


# --- countdown amulets (opt-in: plan(..., tickers=True)) -------------------------------------
# An allied countdown amulet whose Last Words hit the enemy leader, and whose count our own plays advance (Dread
# Pirate's Flag: each spell played advances it by 1; at 0 it is destroyed and deals 2 to the enemy leader): a
# "ticker". Measured like everything here, in the sandbox, not written per card: how far one play of a spell, a
# follower or an amulet advances its count, and what destroying it does to the enemy leader. With it, what cards
# summon onto the allied field (Roughwater First Mate's Fanfare summons a flag) is measured too, because field
# slots decide which plays are possible (a full field blocks the summon; a ticker that pops frees its slot).

@dataclass(frozen=True)
class Ticker:
    spell: int                # count advanced by playing a spell
    follower: int             # ... a follower
    amulet: int               # ... an amulet
    pop: int                  # damage to the enemy leader when it is destroyed


@lru_cache(maxsize=None)
def ticker_profile(defn: CardDef) -> Ticker | None:
    """The amulet as a ticker, or None if it isn't one (no countdown, its count doesn't move with our plays, or
    its destruction doesn't hurt the enemy leader)."""
    if not defn.is_amulet or defn.countdown is None:
        return None
    advance = {}
    for kind, card in (("spell", demo.BACKFIRE), ("follower", demo.FOOTMAN), ("amulet", demo.TOTEM)):
        state, _ = _sandbox(0)
        inst = E.summon(state, 0, defn)
        resolve_queue(state)
        inst.countdown = 50
        c = E.add_to_hand(state, 0, card)
        play = next((a for a in legal_actions(state) if isinstance(a, PlayCard) and a.uid == c.uid), None)
        if play is None:
            advance[kind] = 0
            continue
        apply(state, play)
        now = state.in_play(inst.uid)
        advance[kind] = 50 - now.countdown if now is not None and now.countdown is not None else 0
    state, _ = _sandbox(0)
    inst = E.summon(state, 0, defn)
    resolve_queue(state)
    hp = state.players[1].leader_hp
    E.destroy(state, inst, by_ability=False)
    resolve_queue(state)
    pop = hp - state.players[1].leader_hp
    if pop <= 0 or not any(v > 0 for v in advance.values()):
        return None
    return Ticker(advance["spell"], advance["follower"], advance["amulet"], pop)


def _summoned(before: GameState, after: GameState, exclude: set) -> tuple:
    """(card id, countdown) of the cards that came onto the allied field, the played card and the anchor aside."""
    old = {c.uid for c in before.players[0].field} | exclude
    return tuple(sorted((c.defn.card_id, c.countdown if c.countdown is not None else -1)
                        for c in after.players[0].field if c.uid not in old))


@lru_cache(maxsize=None)
def summons(defn: CardDef, modes: tuple = ()) -> tuple:
    """What playing `defn` (in these modes) summons onto the allied field, besides itself."""
    state, anchor = _sandbox(1)
    card = E.add_to_hand(state, 0, defn)
    for action in legal_actions(state):
        if isinstance(action, PlayCard) and action.uid == card.uid and action.modes == modes:
            s = state.clone()
            apply(s, action)
            return _summoned(state, s, {card.uid, anchor.uid})
    return ()


@lru_cache(maxsize=None)
def evolve_summons(defn: CardDef, super_: bool, modes: tuple = ()) -> tuple:
    """What evolving (super_: super-evolving) a follower of this kind summons onto the allied field."""
    state, anchor = _sandbox(0)
    inst = E.summon(state, 0, defn)
    resolve_queue(state)
    inst.entered_turn = -1
    for action in legal_actions(state):
        if isinstance(action, Evolve) and action.uid == inst.uid and action.super_ == super_ and action.modes == modes:
            s = state.clone()
            apply(s, action)
            return _summoned(state, s, {inst.uid, anchor.uid})
    return ()


# --- the abstract position -------------------------------------------------------------

UNKNOWN = (0, 99)            # a drawn card: takes a hand slot, never played
WARD, UNREACHABLE, BARRIER = 1, 2, 4   # enemy follower flags (UNREACHABLE: can't be attacked or selected)


@dataclass
class Plan:
    damage: int                # most damage the abstract search found
    steps: list = field(default_factory=list)   # abstract actions, in order
    nodes: int = 0
    tickers: bool = False      # planned by the ticker search
    face_first: bool = False   # realize it with face_first (the ticker search's, and the fixed one's)


def _damage(enemies: tuple, j: int, amount: int, pierce: bool = False) -> tuple:
    """Enemy follower j takes `amount` (Barrier stops damage once, not a pierce)."""
    atk, life, flags = enemies[j]
    if flags & BARRIER and not pierce:
        return enemies[:j] + ((atk, life, flags & ~BARRIER),) + enemies[j + 1:]
    if life <= amount:
        return enemies[:j] + enemies[j + 1:]
    return enemies[:j] + ((atk, life - amount, flags),) + enemies[j + 1:]


class _Abstract:
    """Search over resources only. A position is a tuple
    (pp, cap, combo, hand, followers, amulets, bonus, evolve, count, enemies):
    hand = sorted (card id, cost), with a card that has had a card fused to it as
    (-card id, cost) and a drawn card as UNKNOWN; followers = sorted (card id, atk,
    life, attacks left, reach, evolved: 0, 1, or 2 if super-evolved); amulets =
    sorted card ids that can still be engaged; evolve = (ep, sep), or None once
    used this turn; count = cards on the allied field; enemies = enemy followers
    oldest first as (atk, life, flags)."""

    def __init__(self, target: int, extra: int, max_nodes: int):
        self.target, self.extra, self.max_nodes = target, extra, max_nodes
        self.memo: dict = {}
        self.nodes = 0
        self.defs: dict[int, CardDef] = {}

    def best(self, pos) -> tuple[int, list]:
        hit = self.memo.get(pos)
        if hit is not None:
            return hit
        self.nodes += 1
        end = self._terminal(pos)               # ending the turn here (0 in the plain search: nothing to add)
        result = (end, [("end",)]) if end > 0 else (0, [])
        if end >= self.target:
            self.memo[pos] = result
            return result
        if self.nodes <= self.max_nodes:
            for step, nxt, gained in self.moves(pos):
                if gained >= self.target:
                    result = (gained, [step])
                    break
                dmg, rest = self.best(nxt)
                if gained + dmg > result[0]:
                    result = (gained + dmg, [step] + rest)
                    if result[0] >= self.target:
                        break
                if self.nodes > self.max_nodes:      # out of budget: keep what was found
                    break
        self.memo[pos] = result
        return result

    def moves(self, pos):
        pp, cap, combo, hand, followers, amulets, bonus, evolve, count, enemies = pos
        wards = [j for j, e in enumerate(enemies) if e[2] & WARD]
        # attack the leader (no Ward): strongest first; attacks commute, one order is enough
        if not wards:
            for i, f in sorted(enumerate(followers), key=lambda t: -t[1][1]):
                cid, atk, life, left, reach, evo = f
                if left > 0 and atk > 0 and reach == 2:
                    f2 = list(followers)
                    f2[i] = (cid, atk, life, left - 1, reach, evo)
                    yield ("attack", f), (pp, cap, combo, hand, tuple(sorted(f2)), amulets, bonus,
                                          evolve, count, enemies), atk + self.extra
                    break
        # attack a follower: Ward first; without Ward only for a knockback
        targets = wards or [j for j, e in enumerate(enemies) if not e[2] & UNREACHABLE]
        tried = set()
        for i, f in enumerate(followers):
            cid, atk, life, left, reach, evo = f
            if left <= 0 or atk <= 0 or reach == 0 or f in tried:
                continue
            tried.add(f)
            if not wards and not (evo == 2 and reach == 1):
                continue
            seen = set()
            for j in targets:
                ea, el, flags = enemies[j]
                if (not wards and el > atk) or enemies[j] in seen:
                    continue
                seen.add(enemies[j])
                kill = atk >= el and not flags & BARRIER
                f2, n = list(followers), count
                if evo == 2 or life > ea:        # super-evolved: no damage on its own turn
                    f2[i] = (cid, atk, life if evo == 2 else life - ea, left - 1, reach, evo)
                    h2 = hand
                else:
                    del f2[i]
                    n -= 1
                    h2 = self._left(hand)
                gain = 1 + self.extra if kill and evo == 2 else 0
                yield ("strike", f, j, enemies[j]), (pp, cap, combo, h2, tuple(sorted(f2)), amulets, bonus,
                                                     evolve, n, _damage(enemies, j, atk)), gain
        if bonus:
            yield ("bonus",), (pp + 1, cap + 1, combo, hand, followers, amulets, False, evolve, count,
                               enemies), 0
        # fuse cards to a Fuse card to make room in a full hand
        if len(hand) >= HAND_LIMIT - 1:
            for i, (cid, cost) in enumerate(hand):
                if cid <= 0 or (i > 0 and hand[i - 1] == hand[i]) or script_for(cid).fuse_filter is None:
                    continue
                rest = hand[:i] + hand[i + 1:]
                ok = [k for k, (c2, _) in enumerate(rest) if c2 > 0 and fuses(self.defs[cid], self.defs[c2])]
                options = {(rest[k],) for k in ok} | {(rest[a], rest[b]) for a, b in combinations(ok, 2)}
                for fodder in sorted(options):
                    h2 = list(rest)
                    for c in fodder:
                        h2.remove(c)
                    yield ("fuse", (cid, cost), fodder), (pp, cap, combo, tuple(sorted(h2 + [(-cid, cost)])),
                                                          followers, amulets, bonus, evolve, count, enemies), 0
        for i, (cid, cost) in enumerate(hand):
            if cid == 0 or cost > pp or (i > 0 and hand[i - 1] == hand[i]):
                continue
            defn = self.defs[abs(cid)]
            if defn.goes_to_field and count >= FIELD_LIMIT:
                continue
            rest_hand = hand[:i] + hand[i + 1:]
            new_combo = combo + 1
            for variants in self._profiles(defn, cid < 0, pp, cap):
                e = at_combo(variants, new_combo)
                new_pp = min(cap, pp - cost + e.recovered)
                new_hand = self._add(rest_hand, e.added, e.drawn)
                new_f, new_a, new_count = list(followers), list(amulets), count
                if defn.is_follower:
                    new_f.append((abs(cid), e.base + e.per_combo * new_combo, e.life, e.attacks, e.reach, 0))
                    new_count += 1
                elif defn.is_amulet:
                    if engage_profile(defn) is not None:
                        new_a.append(abs(cid))
                    new_count += 1
                step = ("play", cid, cost, e.modes)
                bounce_targets = new_f[:-1] if defn.is_follower else new_f
                if e.bounce and not bounce_targets and defn.is_spell:
                    continue                 # a spell needs its target
                hit = e.hit + e.hit_per_combo * new_combo
                for new_enemies, hit_step in self._hits(enemies, hit, e.spread, e.pierce):
                    if e.bounce:
                        for j, target in enumerate(bounce_targets):
                            if target in bounce_targets[:j]:
                                continue
                            f2 = new_f[:j] + new_f[j + 1:]
                            h2 = self._returned(self._left(new_hand), target[0])
                            yield step + (target, hit_step), (
                                new_pp, cap, new_combo, h2, tuple(sorted(f2)), tuple(sorted(new_a)),
                                bonus, evolve, new_count - 1, new_enemies), e.face
                    if e.bounce and not bounce_targets and defn.is_follower and count > len(followers):
                        # No other follower, but an amulet: the engine makes the Fanfare select it, and
                        # it goes back to hand (Baby Carbuncle with only Godwood Staff out).
                        for k, acid in enumerate(new_a):
                            if acid in new_a[:k]:
                                continue
                            yield step + (("A", acid), hit_step), (
                                new_pp, cap, new_combo, self._returned(new_hand, acid), tuple(sorted(new_f)),
                                tuple(sorted(new_a[:k] + new_a[k + 1:])), bonus, evolve, new_count - 1,
                                new_enemies), e.face
                        if count - len(followers) > len(amulets):    # one the plan doesn't track: lost to it
                            yield step + (("A", None), hit_step), (
                                new_pp, cap, new_combo, new_hand, tuple(sorted(new_f)), tuple(sorted(new_a)),
                                bonus, evolve, new_count - 1, new_enemies), e.face
                        continue
                    if not e.bounce or not bounce_targets:
                        yield step + (None, hit_step), (new_pp, cap, new_combo, new_hand, tuple(sorted(new_f)),
                                                        tuple(sorted(new_a)), bonus, evolve, new_count,
                                                        new_enemies), e.face
        for i, cid in enumerate(amulets):
            e = engage_profile(self.defs[cid])
            if e is None or e.paid > pp or (i > 0 and amulets[i - 1] == cid):
                continue
            rest_a = amulets[:i] + amulets[i + 1:]
            left_count = count - 1 if e.gone else count
            for j, target in enumerate(followers):
                if target in followers[:j]:
                    continue
                f2 = list(followers)
                if e.bounce:
                    del f2[j]
                    h2 = self._returned(self._left(hand), target[0])
                    n = left_count - 1
                elif e.buff:
                    t = target
                    f2[j] = (t[0], t[1] + e.buff, t[2] + e.buff, t[3], t[4], t[5])
                    h2, n = hand, left_count
                else:
                    continue
                yield ("engage", cid, target), (pp - e.paid, cap, combo, h2, tuple(sorted(f2)), rest_a, bonus,
                                                evolve, n, enemies), e.face
        if evolve is not None:
            ep, sep = evolve
            for i, f in enumerate(followers):
                cid, atk, life, left, reach, evo = f
                if evo or f in followers[:i]:
                    continue
                for super_, have in ((True, sep), (False, ep)):
                    if not have:
                        continue
                    plus = 3 if super_ else 2
                    f2 = list(followers)
                    f2[i] = (cid, atk + plus, life + plus, left, max(reach, 1), 2 if super_ else 1)
                    f2 = tuple(sorted(f2))
                    for e in evolve_profile(self.defs[cid], super_):
                        h2 = self._add(hand, e.added, e.drawn)
                        hit = e.hit + e.hit_per_hand * len(hand)
                        for new_enemies, hit_step in self._hits(enemies, hit, e.spread, e.pierce):
                            yield ("evolve", f, super_, e.modes, hit_step), (
                                min(cap, pp + e.recovered), cap, combo, h2, f2, amulets, bonus, None, count,
                                new_enemies), e.face

    def _profiles(self, defn: CardDef, fused: bool, pp: int, cap: int):
        """The ways of playing a card (profile); the ticker and fixed searches measure them at the play points they
        have (profile_at)."""
        return profile(defn, fused)

    def _terminal(self, pos) -> int:
        """Damage to the enemy leader from ending the turn in `pos` (the +eot searches: _EndOfTurn)."""
        return 0

    @staticmethod
    def _hits(enemies: tuple, amount: int, spread: str, pierce: bool):
        """(enemies after the damage, the selected enemy as (index, follower) or None)."""
        if amount <= 0 or not enemies or not spread:
            yield enemies, None
            return
        if spread == "target":
            seen = set()
            for j, e in enumerate(enemies):
                if not e[2] & UNREACHABLE and e not in seen:
                    seen.add(e)
                    yield _damage(enemies, j, amount, pierce), (j, e)
            if not seen:
                yield enemies, None
        elif spread == "random":                 # counted only when it has one place to land
            yield (_damage(enemies, 0, amount, pierce) if len(enemies) == 1 else enemies), None
        elif spread == "all":
            out = enemies
            for j in reversed(range(len(enemies))):
                out = _damage(out, j, amount, pierce)
            yield out, None
        else:                                    # split, oldest first; the last takes the rest
            out = enemies
            shares = []
            for k, (a, l, fl) in enumerate(enemies):
                share = amount if k == len(enemies) - 1 else min(amount, max(l, 0))
                amount -= share
                shares.append(share)
            for j in reversed(range(len(enemies))):
                if shares[j] > 0:
                    out = _damage(out, j, shares[j], pierce)
            yield out, None

    def _add(self, hand: tuple, added: tuple, drawn: int) -> tuple:
        """Cards added, then drawn; cards beyond the hand limit are lost."""
        room = HAND_LIMIT - len(hand)
        new = list(added[:max(0, room)])
        new += [UNKNOWN] * max(0, min(drawn, room - len(new)))
        return tuple(sorted(hand + tuple(new))) if new else hand

    def _left(self, hand: tuple) -> tuple:
        """An allied follower left the field: cards in hand that get cheaper for it do."""
        if not any(c and leave_discount(self.defs[abs(c)]) for c, _ in hand):
            return hand
        return tuple(sorted((c, max(0, cost - leave_discount(self.defs[abs(c)])) if c else cost)
                            for c, cost in hand))

    def _returned(self, hand: tuple, cid: int) -> tuple:
        """A card returned to hand (at its base cost); a full hand destroys it."""
        if len(hand) >= HAND_LIMIT:
            return hand
        return tuple(sorted(hand + ((cid, self.defs[cid].cost),)))


def _evo(f: CardInstance) -> int:
    return 2 if f.super_evolved else 1 if f.evolved else 0


def _hand_key(state: GameState, c: CardInstance) -> tuple:
    fused = bool((c.counters or {}).get("fused"))
    return (-c.defn.card_id if fused else c.defn.card_id), c.cost


def _abstract_position(state: GameState) -> tuple:
    me, opp = state.players[state.active], state.players[1 - state.active]
    first = state.active == state.first
    followers = tuple(sorted((f.defn.card_id, f.atk, f.life, max(0, f.max_attacks - f.attacks_made),
                              _reach(state, f), _evo(f)) for f in me.followers))
    amulets = [c.defn.card_id for c in me.field if c.defn.is_amulet
               and engage_profile(c.defn) is not None and c.engaged_turn != state.turn]
    enemies = []
    for f in opp.followers:
        if f.keywords & (Keyword.AMBUSH | Keyword.INTIMIDATE):
            flags = UNREACHABLE
        else:
            flags = WARD if f.keywords & Keyword.WARD else 0
        if f.keywords & Keyword.BARRIER:
            flags |= BARRIER
        enemies.append((f.atk, f.life, flags))
    evolve = None
    if not me.evolved_this_turn:
        ep = me.ep > 0 and me.turns_taken >= EVOLVE_TURN[first]
        sep = me.sep > 0 and me.turns_taken >= SUPER_EVOLVE_TURN[first]
        evolve = (ep, sep) if ep or sep else None
    cap = me.max_pp + (1 if me.bonus_active else 0)
    return (me.pp, cap, me.combo, tuple(sorted(_hand_key(state, c) for c in me.hand)), followers,
            tuple(sorted(amulets)), me.bonus_ready and not me.bonus_active, evolve, len(me.field),
            tuple(enemies))


def _search_for(state: GameState, side: int, max_nodes: int, cls=None) -> _Abstract:
    """An abstract search for `side` against the enemy leader, knowing every card
    `side` has and can generate."""
    opp = state.players[1 - side]
    search = (cls or _Abstract)(opp.leader_hp, opp.extra_damage, max_nodes)
    me = state.players[side]
    for c in me.hand + me.field + me.leader_area:
        search.defs[c.defn.card_id] = c.defn
    pending = [d for d in search.defs.values() if d.goes_to_field or d.is_spell]
    while pending:                       # cards the hand can generate, transitively
        d = pending.pop()
        effects = [e for variants in profile(d) for e in variants]
        if d.is_follower:
            effects += [e for s in (False, True) for e in evolve_profile(d, s)]
        for e in effects:
            for cid, _ in e.added:
                if cid not in search.defs:
                    search.defs[cid] = POOL[cid]
                    pending.append(POOL[cid])
    return search


class _Digger(_Abstract):
    """The same resources searched for the most cards drawn this turn (plus play
    points taken off cards that get cheaper when allied followers leave, such as
    Bayle), without playing the cards in `keep` and without attacking: what a
    setup turn of the player's looks like (they drew about four cards a turn,
    the AI two to three, and held Bayle until it cost 0 or 2)."""

    def __init__(self, keep: set, max_nodes: int):
        super().__init__(99, 0, max_nodes)
        self.keep = keep

    def _discounted(self, hand: tuple) -> int:
        """Play points the cards that get cheaper when allied followers leave (Bayle) still cost."""
        return sum(cost for cid, cost in hand if cid and leave_discount(self.defs[abs(cid)]))

    def moves(self, pos):
        before = pos[3].count(UNKNOWN)
        cost_before = self._discounted(pos[3])
        for step, nxt, _ in super().moves(pos):
            if step[0] in ("attack", "strike") or (step[0] == "play" and abs(step[1]) in self.keep):
                continue
            # a card drawn, or a play point off Bayle (the player's lethal turns play two at 0)
            yield step, nxt, nxt[3].count(UNKNOWN) - before + max(0, cost_before - self._discounted(nxt[3]))


@lru_cache(maxsize=None)
def end_turn_damage(defn: CardDef, evo: int) -> int:
    """Damage an allied follower of this kind (evo: 0 unevolved, 1 evolved, 2 super-evolved) deals to the enemy
    leader when the turn ends, measured in the sandbox (search.evaluate.after_end_of_turn); one that depends on
    luck counts its smaller outcome over two random seeds (Erntz: evolved, 8; unevolved, its 8 go to random enemy
    followers: 0)."""
    from svsim.search.evaluate import after_end_of_turn
    if not defn.is_follower:
        return 0
    state, _ = _sandbox(0)
    inst = E.summon(state, 0, defn)
    resolve_queue(state)
    if evo:
        E.evolve(state, inst, super_=evo == 2)
        resolve_queue(state)
    hp = state.players[1].leader_hp
    outcomes = []
    for seed in (1, 2):
        s = state.clone()
        s.rng.seed(seed)
        s = after_end_of_turn(s)
        outcomes.append(hp - s.players[1].leader_hp if s.winner != 1 else 0)
    return max(0, min(outcomes))


class _EndOfTurn:
    """Mixed into a search (+eot): ending the turn counts what the allied followers' end-of-turn abilities deal to
    the enemy leader (end_turn_damage), as a last step ("end",) that realize plays as EndTurn."""

    def _terminal(self, pos) -> int:
        total = 0
        for cid, atk, life, left, reach, evo in pos[4]:
            d = self.defs.get(cid) or POOL.get(cid)
            dmg = end_turn_damage(d, evo) if d is not None else 0
            total += dmg + self.extra if dmg > 0 else 0
        return total


class _Fixed(_Abstract):
    """The plain search with its cards measured at the play points it has (profile_at: a 0-cost card with Enhance
    costs its Enhance when it can be paid, and does its plain effect when it can't): +plannerfix."""

    def _profiles(self, defn: CardDef, fused: bool, pp: int, cap: int):
        return profile_at(defn, fused, pp, cap)


class _Tickers(_Abstract):
    """The resource search with allied tickers (ticker_profile): a position is the base search's ten fields plus
    the tickers as a sorted tuple of (count, card id). After every play its kind (spell, follower, amulet)
    advances each ticker; one that reaches 0 pops (its damage counts, its field slot frees), and what the play
    summons takes a slot if one is free (a summoned ticker joins in). Evolving summons too (Roughwater First Mate's
    Evolve replicates its Fanfare). The engine still checks every plan (realize, verify)."""

    def _profiles(self, defn: CardDef, fused: bool, pp: int, cap: int):
        return profile_at(defn, fused, pp, cap)

    def _defn(self, cid: int) -> CardDef:
        d = self.defs.get(cid)
        if d is None:
            d = self.defs[cid] = POOL[cid]
        return d

    def _advance(self, tickers: list, kind: str) -> tuple:
        """(tickers left, damage of those that popped, slots freed)."""
        left, damage, freed = [], 0, 0
        for count, cid in tickers:
            tp = ticker_profile(self._defn(cid))
            count -= getattr(tp, kind)
            if count <= 0:
                damage += tp.pop + self.extra
                freed += 1
            else:
                left.append((count, cid))
        return left, damage, freed

    def _summon(self, tickers: list, count: int, summoned: tuple) -> tuple:
        for cid, countdown in summoned:
            if count >= FIELD_LIMIT:
                break
            count += 1
            if countdown > 0 and ticker_profile(self._defn(cid)) is not None:
                tickers.append((countdown, cid))
        return tickers, count

    def moves(self, pos):
        base, tickers = pos[:10], pos[10]
        for step, nxt, gained in super().moves(base):
            kind = step[0]
            t, count = list(tickers), nxt[8]
            if kind == "play":
                defn = self._defn(abs(step[1]))
                t, count = self._summon(t, count, summons(defn, step[3]))
                t, damage, freed = self._advance(t, "spell" if defn.is_spell else
                                                 "follower" if defn.is_follower else "amulet")
                gained += damage
                count -= freed
            elif kind == "evolve":
                t, count = self._summon(t, count, evolve_summons(self._defn(step[1][0]), step[2], step[3]))
            yield step, nxt[:8] + (count,) + nxt[9:] + (tuple(sorted(t)),), gained


_EOT_CLASSES: dict = {}


def _with_eot(cls):
    """`cls` with end-of-turn damage counted (_EndOfTurn first in its bases)."""
    hit = _EOT_CLASSES.get(cls)
    if hit is None:
        hit = _EOT_CLASSES[cls] = type(f"_EndOfTurn{cls.__name__}", (_EndOfTurn, cls), {})
    return hit


def tickers_of(state: GameState) -> tuple:
    """The allied tickers on the field as (count, card id), sorted."""
    me = state.players[state.active]
    return tuple(sorted((c.countdown, c.defn.card_id) for c in me.field
                        if c.defn.is_amulet and c.countdown is not None and ticker_profile(c.defn) is not None))


def dig(state: GameState, keep: set, max_nodes: int = 2000) -> Plan:
    """The line that draws the most cards this turn by the resource model, keeping
    the cards in `keep` (card ids) in hand."""
    base = _search_for(state, state.active, max_nodes)
    digger = _Digger(keep, max_nodes)
    digger.defs = base.defs
    drawn, steps = digger.best(_abstract_position(state))
    return Plan(drawn, steps, digger.nodes)


def plan(state: GameState, max_nodes: int = 200000, tickers: bool = False, fix: bool = False,
         eot: bool = False) -> Plan:
    """The most damage the hand and board can deal this turn by the resource model,
    with the plan that deals it (stopping once it reaches the enemy leader's defense).
    With `tickers`, allied countdown amulets that hit the enemy leader (ticker_profile) are modelled too, when
    there are any on the field; otherwise the search is the plain one. With `fix` (+plannerfix), the plain search
    measures cards at the play points it has (profile_at) and its plan is realized face first, as the ticker search
    does. With `eot` (+eot), ending the turn counts the allied followers' end-of-turn damage to the enemy leader."""
    ticking = tickers_of(state) if tickers else ()
    if ticking:
        search = _search_for(state, state.active, max_nodes, _with_eot(_Tickers) if eot else _Tickers)
        dmg, steps = search.best(_abstract_position(state) + (ticking,))
        return Plan(dmg, steps, search.nodes, tickers=True, face_first=True)
    cls = _Fixed if fix else None
    if eot:
        cls = _with_eot(cls or _Abstract)
    search = _search_for(state, state.active, max_nodes, cls)
    dmg, steps = search.best(_abstract_position(state))
    return Plan(dmg, steps, search.nodes, face_first=fix)


def planned_lethal(state: GameState, max_nodes: int = 20000, tickers: bool = False, fix: bool = False,
                   eot: bool = False) -> tuple:
    """(the planner's lethal line, realized and checked in the engine, or None; the plan searched first). A ticker
    plan that doesn't realize or check falls back to the search without tickers (the countdown model can be wrong
    where the plain one is right: pirate-t g14 turn 19, analysis/speed/LETHAL.md); without tickers on the field
    this is one plan, as before."""
    hp = state.players[1 - state.active].leader_hp
    first = p = plan(state, max_nodes, tickers=tickers, fix=fix, eot=eot)
    while True:
        if p.damage >= hp and p.steps:
            line = realize(state, p.steps, face_first=p.face_first)
            if line and verify(state, line):
                return line, first
        if not p.tickers:
            return None, first
        p = plan(state, max_nodes, fix=fix, eot=eot)


def next_turn_position(state: GameState, side: int, board: bool = True, pp: int | None = None) -> tuple:
    """The abstract position at the start of `side`'s next turn if nothing changes
    before it: one more max play point, Combo 0, every follower ready to attack,
    evolution as it will be unlocked, the card drawn unknown. Without `board`,
    `side`'s followers are left out (the opponent's turn may well remove them):
    what the hand and amulets can do. With `pp`, that many play points instead
    (10: what the hand could do once the play points are all there)."""
    p, opp = state.players[side], state.players[1 - side]
    first = side == state.first
    turns = p.turns_taken + 1
    followers = tuple(sorted((f.defn.card_id, f.atk, f.life, max(1, f.max_attacks),
                              0 if prop(f, "cant_attack") else 2, _evo(f)) for f in p.followers)) if board else ()
    amulets = tuple(sorted(c.defn.card_id for c in p.field
                           if c.defn.is_amulet and engage_profile(c.defn) is not None))
    enemies = []
    for f in opp.followers:
        flags = UNREACHABLE if f.keywords & (Keyword.AMBUSH | Keyword.INTIMIDATE) else (
            WARD if f.keywords & Keyword.WARD else 0)
        enemies.append((f.atk, f.life, flags | (BARRIER if f.keywords & Keyword.BARRIER else 0)))
    ep = p.ep > 0 and turns >= EVOLVE_TURN[first]
    sep = p.sep > 0 and turns >= SUPER_EVOLVE_TURN[first]
    hand = tuple(sorted(_hand_key(state, c) for c in p.hand))
    if len(hand) < HAND_LIMIT:
        hand = tuple(sorted(hand + (UNKNOWN,)))
    pp = min(MAX_PP, p.max_pp + 1) if pp is None else pp
    bonus = p.bonus_ready or p.bonus_active or (not first and turns == BONUS_REFRESH_TURN)
    count = len(p.field) if board else len(p.field) - len(p.followers)
    return (pp, pp, 0, hand, followers, amulets, bonus, (ep, sep) if ep or sep else None, count,
            tuple(enemies))


_NEXT_TURN: dict = {}


def next_turn_damage(state: GameState, side: int, max_nodes: int = 2000, board: bool = True,
                     pp: int | None = None) -> int:
    """The most damage `side` could deal on its next turn by the resource model, if
    nothing changes before it (stops counting at the enemy leader's defense; with a
    small `max_nodes` it is what the search found within that budget). Without
    `board`: from the hand and amulets only."""
    opp = state.players[1 - side]
    pos = next_turn_position(state, side, board, pp)
    key = (pos, opp.leader_hp, opp.extra_damage, max_nodes)
    hit = _NEXT_TURN.get(key)
    if hit is None:
        if len(_NEXT_TURN) > 50000:
            _NEXT_TURN.clear()
        hit = _NEXT_TURN[key] = _search_for(state, side, max_nodes).best(pos)[0]
    return hit


# --- back to real actions ----------------------------------------------------------------

def _followers_like(state: GameState, me: int, key: tuple, exact: bool = False) -> list:
    """Allied followers of the key's card, the closest match first. With `exact` (the fixed realize), the attacks
    it has left and its reach come first: of identical followers, the one the plan means is the one that hasn't
    attacked yet (Ramp g127: an evolution went to a Promoter that had attacked)."""
    cid, atk, life, left, reach, evo = key
    found = [f for f in state.players[me].followers if f.defn.card_id == cid]
    if exact:
        return sorted(found, key=lambda f: (max(0, f.max_attacks - f.attacks_made) != left,
                                            _reach(state, f) != reach, f.atk != atk, _evo(f) != evo,
                                            f.life != life))
    return sorted(found, key=lambda f: (f.atk != atk, _evo(f) != evo, f.life != life))


def _enemies_like(state: GameState, me: int, j: int, key: tuple) -> list:
    atk, life, _ = key
    foes = state.players[1 - me].followers
    return sorted(foes, key=lambda f: (f.atk != atk, f.life != life, abs(foes.index(f) - j)))


def _rank(items: list, uid) -> int:
    return next((k for k, c in enumerate(items) if c.uid == uid), len(items))


def _fuse_legal(state: GameState, action: Fuse) -> bool:
    p = state.players[state.active]
    card = state.in_hand(p.index, action.uid)
    if card is None or card.fused_turn == state.turn or state.phase != Phase.MAIN:
        return False
    script = script_for(card.defn.card_id)
    fodder = [c for c in p.hand if c.uid in action.cards and c is not card]
    return script.fuse_filter is not None and len(fodder) == len(set(action.cards)) == len(action.cards) \
        and all(script.fuse_filter(c) for c in fodder)


def _legal(state: GameState, action) -> bool:
    if isinstance(action, Fuse):         # built directly: the engine lists only some fuse choices
        return _fuse_legal(state, action)
    if isinstance(action, PlayCard):     # the engine lists one of identical cards: any copy will do
        card = state.in_hand(state.active, action.uid)
        if card is None:
            return False
        sig = _signature(card)
        twin = next(c for c in state.players[state.active].hand if _signature(c) == sig)
        return PlayCard(twin.uid, action.targets, action.modes) in legal_actions(state)
    return action in legal_actions(state)


def listed(state: GameState, action, actions: list):
    """The action as the engine lists it, if it does: for a card in hand, the listed
    identical copy. Otherwise the action itself when it is legal (a fuse choice
    the engine doesn't list), else None."""
    if action in actions:
        return action
    if isinstance(action, PlayCard):
        card = state.in_hand(state.active, action.uid)
        if card is not None:
            sig = _signature(card)
            for a in actions:
                if isinstance(a, PlayCard) and (a.targets, a.modes) == (action.targets, action.modes):
                    twin = state.in_hand(state.active, a.uid)
                    if twin is not None and _signature(twin) == sig:
                        return a
    return action if _legal(state, action) else None


def realize(state: GameState, steps: list, face_first: bool = False) -> list | None:
    """Turn abstract steps into real actions, playing them on a copy; None if a
    step has no matching legal action. Cards drawn on the way are never used:
    the plan doesn't know them. With `face_first` (a ticker plan's), a play that hits no enemy follower in the
    plan takes the enemy leader as its target when it can (the plan counted that way's damage), and allied
    followers are matched on the attacks they have left too (_followers_like's `exact`)."""
    s, me, actions = state.clone(), state.active, []
    unknown = {c.uid for p in s.players for c in p.deck_view()}
    for step in steps:
        legal = legal_actions(s)
        chosen = None
        kind = step[0]
        if kind == "attack":
            ready = {a.attacker for a in legal if isinstance(a, Attack) and a.target == leader_uid(1 - me)}
            f = next((f for f in _followers_like(s, me, step[1], face_first) if f.uid in ready), None)
            chosen = Attack(f.uid, leader_uid(1 - me)) if f else None
        elif kind == "strike":
            attacks = {(a.attacker, a.target) for a in legal if isinstance(a, Attack)}
            for foe in _enemies_like(s, me, step[2], step[3]):
                f = next((f for f in _followers_like(s, me, step[1], face_first) if (f.uid, foe.uid) in attacks), None)
                if f is not None:
                    chosen = Attack(f.uid, foe.uid)
                    break
        elif kind == "bonus":
            chosen = next((a for a in legal if isinstance(a, UseBonusPP)), None)
        elif kind == "end":                      # the plan ends the turn for its end-of-turn damage (+eot)
            chosen = next((a for a in legal if isinstance(a, EndTurn)), None)
        elif kind == "play":
            _, cid, cost, modes, bounce, hit = step
            amulet_back = None
            if bounce and bounce[0] == "A":              # an amulet goes back (see _Abstract.moves)
                amulet_back = {c.uid for c in s.players[me].field
                               if c.defn.is_amulet and (bounce[1] is None or c.defn.card_id == bounce[1])}
                bounce = None
            allies = _followers_like(s, me, bounce, face_first) if bounce else []
            foes = _enemies_like(s, me, *hit) if hit else []
            best = None
            known = {}                   # the engine lists one of identical cards; use a known copy
            for c in s.players[me].hand:
                if c.uid not in unknown:
                    known.setdefault(_signature(c), c.uid)
            for listed in legal:
                if not isinstance(listed, PlayCard) or listed.modes != modes:
                    continue
                card = s.in_hand(me, listed.uid)
                if _hand_key(s, card) != (cid, cost) or _signature(card) not in known:
                    continue
                a = PlayCard(known[_signature(card)], listed.targets, listed.modes)
                rank = (min((_rank(allies, t) for t in a.targets), default=len(allies)) if bounce else 0,
                        min((_rank(foes, t) for t in a.targets), default=len(foes)) if hit else 0,
                        0 if not face_first or hit or leader_uid(1 - me) in a.targets else 1)
                if (bounce and rank[0] >= len(allies)) or (hit and rank[1] >= len(foes)):
                    continue
                if amulet_back is not None and not any(t in amulet_back for t in a.targets):
                    continue
                if best is None or rank < best[0]:
                    best = (rank, a)
            chosen = best[1] if best else None
        elif kind == "fuse":
            _, card_key, fodder_keys = step
            hand = [c for c in s.players[me].hand if c.uid not in unknown]
            card = next((c for c in hand if _hand_key(s, c) == card_key and c.fused_turn != s.turn), None)
            uids = []
            for key in fodder_keys:
                c = next((c for c in hand if _hand_key(s, c) == key and c is not card and c.uid not in uids), None)
                if c is not None:
                    uids.append(c.uid)
            if card is not None and len(uids) == len(fodder_keys):
                chosen = Fuse(card.uid, tuple(uids))
                if not _fuse_legal(s, chosen):
                    chosen = None
        elif kind == "engage":
            allies = _followers_like(s, me, step[2], face_first)
            options = [a for a in legal if isinstance(a, Engage) and s.on_field(a.uid).defn.card_id == step[1]]
            options.sort(key=lambda a: min((_rank(allies, t) for t in a.targets), default=len(allies)))
            chosen = options[0] if options else None
        elif kind == "evolve":
            _, key, super_, modes, hit = step
            uids = [f.uid for f in _followers_like(s, me, key, face_first)]
            foes = _enemies_like(s, me, *hit) if hit else []
            options = [a for a in legal if isinstance(a, Evolve) and a.super_ == super_ and a.modes == modes
                       and a.uid in uids]
            options.sort(key=lambda a: (uids.index(a.uid),
                                        min((_rank(foes, t) for t in a.targets), default=len(foes))))
            chosen = options[0] if options else None
        if chosen is None:
            return None
        actions.append(chosen)
        apply(s, chosen)
        if s.over:
            break
    return actions


def verify(state: GameState, line: list, samples: int = 16, seed: int = 0) -> bool:
    """Whether the line wins this turn. A line that touches nothing hidden is
    checked once; one that draws cards or hits random targets must also win on
    `samples` other deck orders and random outcomes."""
    me = state.active

    def wins(s: GameState) -> bool:
        for a in line:
            if s.over:
                break
            if not _legal(s, a):
                return False
            apply(s, a)
        return s.winner == me

    s, luck = state.clone(), False
    for a in line:
        if s.over:
            break
        if not _legal(s, a):
            return False
        before = hidden_info(s)
        apply(s, a)
        luck |= hidden_info(s) != before
    if s.winner != me:
        return False
    rng = random.Random(seed)
    for _ in range(samples if luck else 0):
        t = state.clone()
        t.rng.seed(rng.getrandbits(64))
        for p in t.players:
            t.rng.shuffle(p.deck)
        if not wins(t):
            return False
    return True


@dataclass
class ComboResult:
    sure: bool                 # a lethal was found and checked in the engine
    line: list                 # its actions
    ceiling: int               # damage the resource model thinks possible
    decided_by: str            # "plan", "ceiling" (model says no lethal), "search"
    seconds: float
    plan_nodes: int = 0
    search_nodes: int = 0
    estimate: object = None    # search.formula.Estimate: the quick count, with its breakdown


def solve(state: GameState, search_nodes: int = 20000, plan_nodes: int = 200000) -> ComboResult:
    """Plan first; if the plan wins in the engine (whatever is drawn or hit at
    random), that's the lethal. If the resource model can't reach the enemy
    leader's defense, report no lethal. Otherwise (a plan the engine rejects)
    fall back to exact search."""
    from svsim.search.formula import estimate as quick_count
    start = time.perf_counter()
    hp = state.players[1 - state.active].leader_hp
    count = quick_count(state)           # first: is the damage there at all (the player's formula)
    p = plan(state, plan_nodes)          # then: how, exactly
    if p.damage >= hp and p.steps:
        line = realize(state, p.steps)
        if line is not None and verify(state, line):
            return ComboResult(True, line, p.damage, "plan", time.perf_counter() - start, p.nodes,
                               estimate=count)
    if p.damage < hp:
        return ComboResult(False, [], p.damage, "ceiling", time.perf_counter() - start, p.nodes,
                           estimate=count)
    if search_nodes <= 0:
        return ComboResult(False, [], p.damage, "plan-failed", time.perf_counter() - start, p.nodes,
                           estimate=count)
    r = LethalSearch(max_nodes=search_nodes, sure_only=True).solve(state)
    return ComboResult(r.sure, r.line, p.damage, "search", time.perf_counter() - start, p.nodes, r.nodes,
                       estimate=count)
