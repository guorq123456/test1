"""Resource-flow lethal planning: understand how a hand turns play points into
damage, plan on that, and let the engine check the plan.

The player's idea, for combo decks such as Rhinoceroach Forest, where exact
search drowns in orderings: a strong player doesn't try every order, they
count resources ("10 play points: three 1-cost cards, Rhinoceroach for 4,
Bug Alert it back, Rhinoceroach again for 6"). This module does the same in
three steps.

1. Profile each card by playing it in a sandbox (`profile`): net play points,
   cards it adds to hand, whether it returns another allied card on the field
   to hand, direct damage to the enemy leader, and, for a follower that can
   attack the leader at once, its attack as base + per_combo * Combo (measured
   at two Combo values). Engage and evolve effects are profiled the same way.
   Nothing here is written per card: the engine measures it.
2. Search an abstract position made only of those resources (play points,
   Combo, hand, followers that can attack the leader, amulets that can be
   engaged, evolution and bonus play points) for the most damage this turn.
   It ignores enemy Ward, draws and random effects, so it is optimistic.
3. Translate the best plan back into real actions and play it on a copy of
   the position; only a plan that wins there counts.

Limits: abilities of cards already in play that react to the plan (listeners)
are not modelled, nor cost changes during the turn; when a plan fails (Ward,
say), `solve` falls back to exact search.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import time

from svsim.cards import demo
from svsim.cards.pool import POOL
from svsim.core import effects as E
from svsim.core.actions import Attack, Engage, Evolve, Mulligan, PlayCard, UseBonusPP
from svsim.core.carddef import CardDef
from svsim.core.engine import EVOLVE_TURN, SUPER_EVOLVE_TURN, apply, legal_actions, new_game
from svsim.core.enums import Keyword
from svsim.core.script import prop, script_for
from svsim.core.state import HAND_LIMIT, CardInstance, GameState, leader_uid
from svsim.search.lethal import LethalSearch, hidden_info


@dataclass(frozen=True)
class Effect:
    """One way of playing (or engaging, evolving) a card, as measured."""
    paid: int                 # play points paid
    recovered: int            # play points recovered
    added: tuple              # (card id, cost) of cards added to hand (not drawn)
    bounce: bool              # returns another allied card on the field to hand
    face: int                 # direct damage to the enemy leader
    base: int = 0             # attack if it can hit the leader this turn: base + per_combo * Combo
    per_combo: int = 0
    attacks: int = 0          # attacks it gets this turn (0: can't hit the leader)
    buff: int = 0             # attack given to the selected allied follower
    modes: tuple = ()
    gone: bool = False        # (Engage) the amulet destroys itself


# --- profiling -------------------------------------------------------------------------

def _sandbox(combo: int, pp: int = 10):
    """Player 0 to act with `pp` play points, an allied follower to return to hand
    (the anchor) and no enemy followers, so random enemy effects have no target."""
    state = new_game([demo.FOOTMAN] * 40, [demo.FOOTMAN] * 40, seed=0, first=0)
    apply(state, Mulligan(()))
    apply(state, Mulligan(()))
    p = state.players[0]
    p.hand.clear()
    state.players[1].hand.clear()
    p.max_pp = p.pp = pp
    p.combo = combo
    p.turns_taken = 10                     # evolution unlocked
    anchor = E.summon(state, 0, demo.FOOTMAN)
    anchor.entered_turn = -1
    return state, anchor


def _measure(before: GameState, after: GameState, anchor: CardInstance, deck_uids: set,
             played: CardInstance | None) -> dict:
    me, opp = before.players[0], after.players[0]
    old_hand = {c.uid for c in me.hand}
    added = tuple(sorted((c.defn.card_id, c.cost) for c in opp.hand
                         if c.uid not in old_hand and c.uid not in deck_uids
                         and c.defn.card_id != anchor.defn.card_id))
    bounce = after.on_field(anchor.uid) is None and any(c.defn == anchor.defn for c in opp.hand)
    attack = None
    if played is not None:
        inst = after.on_field(played.uid)
        if inst is not None and inst.defn.is_follower and (
                inst.keywords & Keyword.STORM or inst.entered_turn != after.turn) \
                and not prop(inst, "cant_attack"):
            attack = (inst.atk, inst.max_attacks - inst.attacks_made)
    anchor_after = after.on_field(anchor.uid)
    return dict(added=added, bounce=bounce, attack=attack,
                face=before.players[1].leader_hp - after.players[1].leader_hp,
                buff=(anchor_after.atk - anchor.atk) if anchor_after is not None else 0)


COMBO_STEPS = (1, 3, 5)     # Combo values (counting the card) at which cards are measured


@lru_cache(maxsize=None)
def profile(defn: CardDef) -> tuple[tuple[Effect, ...], ...]:
    """The ways of playing `defn` (one per mode / target choice), each as Effects
    measured at Combo 1, 3 and 5 in a sandbox with 10 play points, so Combo
    thresholds and Combo-scaling attack show up. Use `at_combo` to pick one."""
    measured = []
    for combo_after in COMBO_STEPS:
        state, anchor = _sandbox(combo_after - 1)
        card = E.add_to_hand(state, 0, defn)
        rows = {}
        for action in legal_actions(state):
            if not isinstance(action, PlayCard) or action.uid != card.uid:
                continue
            s = state.clone()
            deck = {c.uid for c in s.players[0].deck}
            pp = s.players[0].pp
            apply(s, action)
            m = _measure(state, s, anchor, deck, card)
            m["paid"] = card.cost
            m["recovered"] = max(0, s.players[0].pp - (pp - card.cost))
            rows[(action.modes, action.targets)] = m
        measured.append(rows)
    out = []
    for key, first in measured[0].items():
        ms = [rows.get(key, first) for rows in measured]
        per_combo = attacks = 0
        if ms[0]["attack"] and ms[-1]["attack"]:
            span = COMBO_STEPS[-1] - COMBO_STEPS[0]
            per_combo = max(0, (ms[-1]["attack"][0] - ms[0]["attack"][0]) // span)
            attacks = ms[0]["attack"][1]
        variants = []
        for combo_after, m in zip(COMBO_STEPS, ms):
            base = (m["attack"][0] - per_combo * combo_after) if m["attack"] else 0
            variants.append(Effect(m["paid"], m["recovered"], m["added"], m["bounce"], m["face"],
                                   base, per_combo, attacks if m["attack"] else 0, m["buff"], key[0]))
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
    best = None
    for action in legal_actions(state):
        if not isinstance(action, Engage) or action.uid != amulet.uid:
            continue
        s = state.clone()
        deck = {c.uid for c in s.players[0].deck}
        apply(s, action)
        m = _measure(state, s, anchor, deck, None)
        e = Effect(script.engage_cost, 0, m["added"], m["bounce"], m["face"], buff=m["buff"],
                   gone=s.in_play(amulet.uid) is None)
        if best is None or (e.bounce, e.buff, e.face) > (best.bounce, best.buff, best.face):
            best = e
    return best


@lru_cache(maxsize=None)
def evolve_profile(defn: CardDef, super_: bool) -> Effect:
    """What evolving a follower of this kind with points does besides +2/+2 (+3/+3):
    play points recovered and direct damage (e.g. Baby Carbuncle: recover 3), for
    the best mode if the evolution picks one (Miroku: replicate the Fanfare)."""
    state, anchor = _sandbox(0)
    state.players[0].pp = 0                 # room to recover play points
    inst = E.summon(state, 0, defn)
    inst.entered_turn = -1
    best = None
    for action in legal_actions(state):
        if not isinstance(action, Evolve) or action.uid != inst.uid or action.super_ != super_:
            continue
        s = state.clone()
        deck = {c.uid for c in s.players[0].deck}
        apply(s, action)
        m = _measure(state, s, anchor, deck, None)
        e = Effect(0, s.players[0].pp, m["added"], m["bounce"], m["face"], modes=action.modes)
        if best is None or (e.recovered, e.face, len(e.added)) > (best.recovered, best.face, len(best.added)):
            best = e
    return best or Effect(0, 0, (), False, 0)


# --- the abstract position -------------------------------------------------------------

@dataclass
class Plan:
    damage: int                # most damage the abstract search found (optimistic)
    steps: list = field(default_factory=list)   # abstract actions, in order
    nodes: int = 0


class _Abstract:
    """Search over resources only. A position is a tuple:
    (pp, cap, combo, hand, followers, amulets, bonus, evolve, field_count) with
    hand = sorted (card id, cost); followers = sorted (card id, atk, attacks left,
    evolved); amulets = sorted card ids that can still be engaged; evolve = (ep, sep)
    or None once used this turn."""

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
        result = (0, [])
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
        self.memo[pos] = result
        return result

    def moves(self, pos):
        pp, cap, combo, hand, followers, amulets, bonus, evolve, count = pos
        # attack the leader: strongest first
        for i, (cid, atk, left, evolved) in sorted(enumerate(followers), key=lambda t: -t[1][1]):
            if left > 0 and atk > 0:
                f = list(followers)
                f[i] = (cid, atk, left - 1, evolved)
                yield ("attack", cid, atk), (pp, cap, combo, hand, tuple(sorted(f)), amulets, bonus,
                                             evolve, count), atk + self.extra
                break                    # attacks commute: one order is enough
        if bonus:
            yield ("bonus",), (pp + 1, cap + 1, combo, hand, followers, amulets, False, evolve, count), 0
        for i, (cid, cost) in enumerate(hand):
            if cost > pp or (i > 0 and hand[i - 1] == (cid, cost)):
                continue
            defn = self.defs[cid]
            rest_hand = hand[:i] + hand[i + 1:]
            new_combo = combo + 1
            for variants in profile(defn):
                e = at_combo(variants, new_combo)
                if defn.goes_to_field and count >= 5:
                    continue
                new_pp = min(cap, pp - cost + e.recovered)
                new_hand = tuple(sorted(rest_hand + e.added[:max(0, HAND_LIMIT - len(rest_hand))]))
                new_f, new_a, new_count = list(followers), list(amulets), count
                if defn.is_follower:
                    atk = e.base + e.per_combo * new_combo if e.attacks else 0
                    new_f.append((cid, atk, e.attacks, False))
                    new_count += 1
                elif defn.is_amulet and engage_profile(defn) is not None:
                    new_a.append(cid)
                    new_count += 1
                elif defn.is_amulet:
                    new_count += 1
                step = ("play", cid, cost, e.modes)
                targets = new_f[:-1] if defn.is_follower else new_f
                if e.bounce and not targets and defn.is_spell:
                    continue                 # a spell needs its target
                if e.bounce:
                    for j, target in enumerate(targets):
                        f2 = new_f[:j] + new_f[j + 1:]
                        h2 = self._returned(new_hand, target[0])
                        yield (step + (("bounce", target),)), (
                            new_pp, cap, new_combo, h2, tuple(sorted(f2)), tuple(sorted(new_a)),
                            bonus, evolve, new_count - 1), e.face
                if not e.bounce or not targets:
                    yield step, (new_pp, cap, new_combo, new_hand, tuple(sorted(new_f)),
                                 tuple(sorted(new_a)), bonus, evolve, new_count), e.face
        for i, cid in enumerate(amulets):
            e = engage_profile(self.defs[cid])
            if e is None or e.paid > pp:
                continue
            rest_a = amulets[:i] + amulets[i + 1:]
            left_count = count - 1 if e.gone else count
            for j, target in enumerate(followers):
                f2 = list(followers)
                if e.bounce:
                    del f2[j]
                    h2 = self._returned(hand, target[0])
                elif e.buff:
                    f2[j] = (target[0], target[1] + e.buff, target[2], target[3])
                    h2 = hand
                else:
                    continue
                yield ("engage", cid, target), (pp - e.paid, cap, combo, h2, tuple(sorted(f2)),
                                                rest_a, bonus, evolve, left_count), e.face
        if evolve is not None:
            ep, sep = evolve
            for i, (cid, atk, left, evolved) in enumerate(followers):
                if evolved:
                    continue
                for super_, have in ((True, sep), (False, ep)):
                    if not have:
                        continue
                    e = evolve_profile(self.defs[cid], super_)
                    f2 = list(followers)
                    f2[i] = (cid, atk + (3 if super_ else 2) if left else atk, left, True)
                    yield ("evolve", cid, super_, e.modes), (min(cap, pp + e.recovered), cap, combo,
                                                             tuple(sorted(hand + e.added)),
                                                             tuple(sorted(f2)), amulets, bonus, None,
                                                             count), e.face

    def _base_cost(self, cid: int) -> int:
        return self.defs[cid].cost

    def _returned(self, hand: tuple, cid: int) -> tuple:
        """A card returned to hand (at its base cost); a full hand destroys it."""
        if len(hand) >= HAND_LIMIT:
            return hand
        return tuple(sorted(hand + ((cid, self._base_cost(cid)),)))


def _abstract_position(state: GameState) -> tuple:
    me = state.players[state.active]
    first = state.active == state.first
    followers = []
    for f in me.followers:
        can_face = (f.keywords & Keyword.STORM or f.entered_turn != state.turn) and not prop(f, "cant_attack")
        left = max(0, f.max_attacks - f.attacks_made) if can_face else 0
        followers.append((f.defn.card_id, f.atk, left, f.evolved))
    amulets = [c.defn.card_id for c in me.field if c.defn.is_amulet
               and engage_profile(c.defn) is not None and c.engaged_turn != state.turn]
    evolve = None
    if not me.evolved_this_turn:
        ep = me.ep > 0 and me.turns_taken >= EVOLVE_TURN[first]
        sep = me.sep > 0 and me.turns_taken >= SUPER_EVOLVE_TURN[first]
        evolve = (ep, sep) if ep or sep else None
    cap = me.max_pp + (1 if me.bonus_active else 0)
    return (me.pp, cap, me.combo, tuple(sorted((c.defn.card_id, c.cost) for c in me.hand)),
            tuple(sorted(followers)), tuple(sorted(amulets)), me.bonus_ready and not me.bonus_active,
            evolve, len(me.field))


def plan(state: GameState, max_nodes: int = 200000) -> Plan:
    """The most damage the hand and board can deal this turn by the resource model,
    with the plan that deals it (stopping once it reaches the enemy leader's defense)."""
    opp = state.players[1 - state.active]
    search = _Abstract(opp.leader_hp, opp.extra_damage, max_nodes)
    me = state.players[state.active]
    for c in me.hand + me.field + me.leader_area:
        search.defs[c.defn.card_id] = c.defn
    pending = [d for d in search.defs.values() if d.goes_to_field or d.is_spell]
    while pending:                       # cards the hand can generate, transitively
        d = pending.pop()
        for e in (e for variants in profile(d) for e in variants):
            for cid, _ in e.added:
                if cid not in search.defs:
                    search.defs[cid] = POOL[cid]
                    pending.append(POOL[cid])
    dmg, steps = search.best(_abstract_position(state))
    return Plan(dmg, steps, search.nodes)


# --- back to real actions ----------------------------------------------------------------

def _find_follower(state: GameState, me: int, key: tuple) -> CardInstance | None:
    cid, atk, left, evolved = key
    best = None
    for f in state.players[me].followers:
        if f.defn.card_id != cid:
            continue
        if f.atk == atk and f.evolved == evolved:
            return f
        best = best or f
    return best


def realize(state: GameState, steps: list) -> list | None:
    """Turn abstract steps into real actions, playing them on a copy; None if a
    step has no matching legal action."""
    s, me, actions = state.clone(), state.active, []
    for step in steps:
        legal = legal_actions(s)
        chosen = None
        kind = step[0]
        if kind == "attack":
            for a in legal:
                if isinstance(a, Attack) and a.target == leader_uid(1 - me):
                    f = s.on_field(a.attacker)
                    if f.defn.card_id == step[1] and f.atk == step[2]:
                        chosen = a
                        break
            if chosen is None:
                chosen = next((a for a in legal if isinstance(a, Attack) and a.target == leader_uid(1 - me)
                               and s.on_field(a.attacker).defn.card_id == step[1]), None)
        elif kind == "bonus":
            chosen = next((a for a in legal if isinstance(a, UseBonusPP)), None)
        elif kind == "play":
            cid, cost, modes = step[1], step[2], step[3]
            bounce = step[4][1] if len(step) > 4 else None
            target = _find_follower(s, me, bounce) if bounce else None
            for a in legal:
                if not isinstance(a, PlayCard) or a.modes != modes:
                    continue
                card = s.in_hand(me, a.uid)
                if card.defn.card_id != cid or card.cost != cost:
                    continue
                if target is not None and target.uid not in a.targets:
                    continue
                chosen = a
                break
        elif kind == "engage":
            target = _find_follower(s, me, step[2])
            chosen = next((a for a in legal if isinstance(a, Engage)
                           and s.on_field(a.uid).defn.card_id == step[1]
                           and (target is None or target.uid in a.targets)), None)
        elif kind == "evolve":
            chosen = next((a for a in legal if isinstance(a, Evolve) and a.super_ == step[2]
                           and a.modes == step[3] and s.on_field(a.uid).defn.card_id == step[1]), None)
        if chosen is None:
            return None
        actions.append(chosen)
        apply(s, chosen)
        if s.over:
            break
    return actions


@dataclass
class ComboResult:
    sure: bool                 # a sure lethal was found (engine-checked)
    line: list                 # its actions
    ceiling: int               # damage the resource model thinks possible
    decided_by: str            # "plan", "ceiling" (model says no lethal), "search"
    seconds: float
    plan_nodes: int = 0
    search_nodes: int = 0
    estimate: object = None    # search.formula.Estimate: the quick count, with its breakdown


def solve(state: GameState, search_nodes: int = 20000) -> ComboResult:
    """Plan first; if the plan wins in the engine without luck, that's the lethal.
    If the resource model can't reach the enemy leader's defense, report no
    lethal. Otherwise (a plan that fails, e.g. on Ward) fall back to exact search."""
    from svsim.search.formula import estimate as quick_count
    start = time.perf_counter()
    me, hp = state.active, state.players[1 - state.active].leader_hp
    count = quick_count(state)           # first: is the damage there at all (the player's formula)
    p = plan(state)                      # then: how, exactly
    if p.damage >= hp and p.steps:
        line = realize(state, p.steps)
        if line is not None:
            s, lucky = state.clone(), False
            for a in line:
                before = hidden_info(s)
                apply(s, a)
                lucky |= hidden_info(s) != before
            if s.winner == me and not lucky:
                return ComboResult(True, line, p.damage, "plan", time.perf_counter() - start, p.nodes,
                                   estimate=count)
    if p.damage < hp:
        return ComboResult(False, [], p.damage, "ceiling", time.perf_counter() - start, p.nodes,
                           estimate=count)
    r = LethalSearch(max_nodes=search_nodes, sure_only=True).solve(state)
    return ComboResult(r.sure, r.line, p.damage, "search", time.perf_counter() - start, p.nodes, r.nodes,
                       estimate=count)
