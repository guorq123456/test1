"""Quick lethal arithmetic for combo-finisher decks: the player's formula.

For a finisher whose attack grows with Combo and that can hit the leader at
once (Killer Rhinoceroach: +1 attack per card played this turn, Storm), a
strong player doesn't search, they count (the player's words, 2026-10-05):

- k finisher plays deal the sum of the Combo at each play. A card played
  before all of them is worth k damage; one between two plays (the card that
  returns the finisher to hand) only adds to the later ones. So with two
  Rhinoceroaches, "both from hand" beats "one returned to hand" by 1 for the
  same play points;
- a 0-cost card is worth k; an effect that recovers play points (super-evolving
  Baby Carbuncle, evolving Miroku) works like a "-1 cost card": with a 1-cost
  card it is 2 cards for 0 play points, worth 2k;
- a super-evolved follower that destroys an enemy follower knocks back 1;
- the same counting works for 1, 3 or 4 finisher plays; a return-to-hand card
  that returns a finisher already on the field (after it attacked) comes
  before every play, so it is worth k too.

Checked against the planner on 120 positions, two more terms came up and are
counted too: evolving the last finisher itself (+3 super, +2 normal; the one
evolution of the turn, so instead of recovering play points with it), and an
amulet that is first a card to play and then engaged to give the finisher +1
(Lambent Cairn).

Enemy Ward comes first: before anything hits the leader its defense must be
removed, and the count says with what. Rush followers among the filler cards
(Fairies) attack it for free; cards that damage followers (Bayle, Miroku's
split mode) are played for it; random damage counts only when the Ward is the
only enemy follower, and damage that grows with Combo (Eradicating Arrow) is
played last before the finisher, for the most; the turn's evolution can go to
a follower that then attacks the Ward (a super-evolved one knocks back 1 when
it destroys it; Baby Carbuncle and Miroku also recover play points), or to
Glade, which splits as much damage as there are cards in hand; followers on
the field can attack it instead of the leader; or the first finisher hits it
instead of the leader. Barrier counts as one more defense. The card that
returns a finisher to hand comes too late for this: the first finisher had to
attack before it.

Which filler cards to play is counted exactly, not greedily: the most cards the
play points allow (a card can bring the cards it adds, like Lambent Cairn's
Fairy and its 0-cost Deepwood Bounty), keeping the choice that removes most
Ward defense and the one with most Cairns. A spare card that returns an allied
card to hand is filler too: it returns a cheap follower to play again.

"First check whether the damage is enough, then work out how": `estimate`
gives the most damage this arithmetic allows and a breakdown in those terms;
search.combo then finds and checks the actual line. Cards are classified from
their measured profiles (search.combo.profile), not from a card list.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from itertools import combinations, product

from svsim.core.engine import EVOLVE_TURN, SUPER_EVOLVE_TURN
from svsim.core.enums import Keyword
from svsim.core.state import GameState
from svsim.cards.pool import POOL
from svsim.search.combo import at_combo, engage_profile, evolve_profile, profile, recovery
from svsim.ui.text import card_name


@dataclass
class Estimate:
    damage: int
    pattern: str = ""
    terms: list = field(default_factory=list)    # (description, damage)

    def text(self, hp: int) -> str:
        lines = [self.pattern] + [f"  {d}：{'+' if v >= 0 else ''}{v}" for d, v in self.terms]
        verdict = "打得死" if self.damage >= hp else "打不死"
        return "\n".join(lines + [f"  合计 {self.damage}，对手 {hp} 血：{verdict}"])


def _finisher(defn) -> tuple[int, int] | None:
    """(base, per_combo) if the card is a Combo-scaling follower that can hit the
    leader the turn it is played."""
    if not defn.is_follower:
        return None
    for variants in profile(defn):
        e = variants[-1]
        if e.per_combo >= 1 and e.attacks >= 1 and e.reach == 2:
            return e.base, e.per_combo
    return None


@dataclass(frozen=True)
class _Card:
    """A filler card: played before the finishers."""
    cost: int                   # net play points
    name: str
    removal: int = 0            # Ward defense it takes off: its Rush attack, damage to followers
    scaling: tuple = ()         # (hit, per Combo): random damage growing with Combo, lone Ward only
    cairn: bool = False         # engaged afterwards for +1 attack on the finisher
    atk: int = -1               # attack if it is a follower
    rush: bool = False          # can attack followers the turn it is played (`removal` counts that)


def _card(defn, cost_now: int, lone: bool, most_removal: bool = False) -> tuple:
    """(the card as filler, its Effect): its cheapest way of playing (or the one
    that removes most), measured at Combo 3."""
    best = None
    for variants in profile(defn):
        e = at_combo(variants, 3)
        removal = (e.base + e.per_combo * 3) if e.reach >= 1 and e.attacks else 0
        scaling = ()
        if e.spread in ("target", "split", "all"):
            removal += e.hit + e.hit_per_combo * 3
        elif e.spread == "random" and lone:
            if e.hit_per_combo:
                scaling = (e.hit, e.hit_per_combo)
            else:
                removal += e.hit
        reach = removal + (3 * scaling[1] if scaling else 0)
        key = (-reach, e.paid - e.recovered) if most_removal else (e.paid - e.recovered, -len(e.added))
        if best is None or key < best[0]:
            best = (key, e, removal, scaling)
    _, e, removal, scaling = best
    eng = engage_profile(defn) if defn.is_amulet else None
    card = _Card(cost_now - e.recovered, card_name(defn), removal, scaling, bool(eng and eng.buff > 0),
                 (e.base + e.per_combo * 3) if defn.is_follower else -1, e.reach >= 1 and e.attacks > 0)
    return card, e


def _bundle(defn, cost_now: int, lone: bool) -> tuple:
    """(the card, the cards it adds) as filler."""
    card, e = _card(defn, cost_now, lone)
    return card, tuple(_card(POOL[cid], cost, lone)[0] for cid, cost in e.added if profile(POOL[cid]))


def _removal(cards: list, combo: int) -> int:
    """Ward defense the filler cards take off, those growing with Combo played last
    (`combo`: Combo before the filler)."""
    total = sum(c.removal for c in cards)
    scaling = [c for c in cards if c.scaling]
    first = combo + len(cards) - len(scaling)
    for j, c in enumerate(scaling):
        total += c.scaling[0] + c.scaling[1] * (first + j + 1)
    return total


def _removal_parts(cards: list, combo: int) -> list:
    parts = [(c.name, c.removal) for c in cards if c.removal and not c.scaling]
    scaling = [c for c in cards if c.scaling]
    first = combo + len(cards) - len(scaling)
    parts += [(c.name, c.removal + c.scaling[0] + c.scaling[1] * (first + j + 1)) for j, c in enumerate(scaling)]
    return parts


def _fillers(bundles: list, budget: int, combo: int) -> dict:
    """The ways to spend `budget` play points on filler, per number of cards: the
    one that removes most Ward defense and the one with most Cairns."""
    groups = Counter(bundles)
    keys = [k for k in groups if k[0].cost <= budget]
    out: dict = {}
    for picks in product(*(range(groups[k] + 1) for k in keys)):
        cost = sum(k[0].cost * n for k, n in zip(keys, picks))
        if cost > budget:
            continue
        cards = [k[0] for k, n in zip(keys, picks) for _ in range(n)]
        left = budget - cost
        for add in sorted((a for k, n in zip(keys, picks) for _ in range(n) for a in k[1]),
                          key=lambda a: (a.cost, -a.removal)):
            if add.cost <= left:
                cards.append(add)
                left -= add.cost
        slot = out.setdefault(len(cards), {})
        r, c = _removal(cards, combo), sum(x.cairn for x in cards)
        for key, score in (("removal", (r, c)), ("cairns", (c, r))):
            if key not in slot or score > slot[key][0]:
                slot[key] = (score, cards)
    return {n: [v[1] for v in slot.values()] for n, slot in out.items()}


def _cheapest_cover(values: list, need: int) -> int | None:
    """Smallest sum of some of `values` reaching `need` (None if they can't)."""
    best = None
    for n in range(len(values) + 1):
        for pick in combinations(values, n):
            if sum(pick) >= need and (best is None or sum(pick) < best):
                best = sum(pick)
    return best


@dataclass(frozen=True)
class _Evo:
    """What the turn's one evolution is spent on."""
    gain: int = 0               # play points recovered
    desc: str = ""
    dmg: int = 0                # attack added to the last finisher
    removal: int = 0            # Ward defense its ability takes off (Glade's split damage)
    plus: int = 0               # with Ward: the evolved follower attacks it with this much more attack
    source: int | None = None   # uid of the card in hand it evolves: it has to be played
    knock: bool = False         # super-evolved attacker: knocks back 1 when it destroys the Ward


def _attacker(cards: list, evo: _Evo, own: _Card | None) -> tuple[int, str]:
    """Ward defense the evolved follower's attack adds: the evolving card itself
    (`own`), or the best follower among the filler cards; its Rush attack is
    already counted, so only the evolution's attack then."""
    choices = [own] if own is not None else [c for c in cards if c.atk >= 0]
    best = max(choices, key=lambda c: c.atk + (0 if c.rush else c.atk), default=None)
    if best is None or not evo.plus:
        return 0, ""
    return evo.plus + (0 if best.rush else best.atk), best.name


def estimate(state: GameState) -> Estimate:
    me, opp = state.players[state.active], state.players[1 - state.active]
    first = state.active == state.first
    reachable = [f for f in opp.followers if not f.keywords & (Keyword.AMBUSH | Keyword.INTIMIDATE)]
    wards = [f for f in reachable if f.keywords & Keyword.WARD]
    ward_life = sum(max(f.life, 0) + (1 if f.keywords & Keyword.BARRIER else 0) for f in wards)
    lone = len(opp.followers) == 1
    finishers, bundles, bounces, removers = [], [], [], []
    bundle_of, own = {}, {}                        # by uid: a filler card's bundle; a card as filler
    for c in me.hand:
        fin = _finisher(c.defn)
        if fin:
            finishers.append((c, fin))
            continue
        variants = profile(c.defn)
        if not variants:                       # can't be played without a target the sandbox lacks
            continue
        if any(v[0].bounce for v in variants):
            bounces.append((c.cost, True, card_name(c.defn), c.uid))
            own[c.uid] = _card(c.defn, c.cost, lone)[0]
            continue
        eng = engage_profile(c.defn) if c.defn.is_amulet else None
        if eng is not None and eng.bounce:
            bounces.append((c.cost + eng.paid, True, card_name(c.defn) + "（下场后启动）", c.uid))
            continue
        bundle = _bundle(c.defn, c.cost, lone)
        bundles.append(bundle)
        bundle_of[c.uid], own[c.uid] = bundle, bundle[0]
        if ward_life:
            card, _ = _card(c.defn, c.cost, lone, most_removal=True)
            if _removal([card], 3) > _removal([bundle[0]], 3):    # a way of playing it that removes more
                removers.append((bundle, card))
    for c in me.field:
        eng = engage_profile(c.defn) if c.defn.is_amulet and c.engaged_turn != state.turn else None
        if eng is not None and eng.bounce:
            bounces.append((eng.paid, False, card_name(c.defn) + "（场上启动）", c.uid))
    buffs = sum(1 for c in me.field if c.defn.is_amulet and c.engaged_turn != state.turn
                and (engage_profile(c.defn) or None) and engage_profile(c.defn).buff > 0)
    ready = [f for f in me.followers if f.attacks_made < f.max_attacks]
    to_face = [f.atk for f in ready if f.keywords & Keyword.STORM or f.entered_turn != state.turn]
    to_ward = [f.atk for f in ready if not (f.keywords & Keyword.STORM or f.entered_turn != state.turn)
               and (f.evolved or f.keywords & Keyword.RUSH)]
    field_attack = sum(to_face)
    rhino_on_field = any(_finisher(f.defn) for f in me.followers)
    can_evolve = not me.evolved_this_turn and me.ep > 0 and me.turns_taken >= EVOLVE_TURN[first]
    can_super = not me.evolved_this_turn and me.sep > 0 and me.turns_taken >= SUPER_EVOLVE_TURN[first]
    # the turn's evolution
    evos = [_Evo()]
    for super_, ok in ((True, can_super), (False, can_evolve)):
        if not ok:
            continue
        word, plus = ("超进化", 3) if super_ else ("进化", 2)
        evos.append(_Evo(desc=f"{word}最后一只破魔虫", dmg=plus))
        for c in me.hand:
            if c.defn.is_follower and not _finisher(c.defn) and recovery(c.defn, super_):
                gain = recovery(c.defn, super_)
                evos.append(_Evo(gain, f"{word}{card_name(c.defn)}回 {gain} 费", plus=plus if wards else 0,
                                 source=c.uid, knock=super_ and bool(wards)))
        if not wards:
            continue
        evos.append(_Evo(desc=f"{word}垫牌里的随从去撞守护", plus=plus, knock=super_))
        for c, in_hand in [(f, False) for f in me.followers if not f.evolved] + [(c, True) for c in me.hand]:
            if not c.defn.is_follower or _finisher(c.defn):
                continue
            hand_size = len(me.hand)
            if in_hand:                            # played first: it leaves the hand, adds and draws
                e = at_combo(profile(c.defn)[0], 3)
                hand_size += len(e.added) + e.drawn - 1
            for e in evolve_profile(c.defn, super_):
                if e.spread in ("target", "split", "all") or (e.spread == "random" and lone):
                    x = e.hit + e.hit_per_hand * hand_size
                    if x > 0:
                        evos.append(_Evo(desc=f"{word}{card_name(c.defn)}（伤害 {x}）", removal=x,
                                         source=c.uid if in_hand else None))
    evos = list(dict.fromkeys(evos))
    pp = me.pp + (1 if me.bonus_ready and not me.bonus_active else 0)
    base, per = finishers[0][1] if finishers else (0, 1)
    best = Estimate(0 if wards else field_attack, "没有能打脸的破魔虫：只算场上的攻击",
                    [("场上随从打脸", field_attack)] if field_attack and not wards else [])
    bounces.sort(key=lambda b: (b[0], not b[1]))
    cheap = min((cd for b in bundles for cd in (b[0],) + b[1] if cd.atk >= 0), key=lambda cd: (cd.cost, -cd.removal),
                default=None)
    packages = [((), False)]                       # (removers played for the Ward, first finisher hits it)
    if ward_life:
        packages = [(chosen, hit) for n in range(min(3, len(removers)) + 1)
                    for chosen in combinations(removers, n) for hit in (False, True)]
    cache: dict = {}
    for chosen, rhino_hit in packages:
        forced = [card for _, card in chosen]
        rest = [b for b in bundles if not any(b is c for c, _ in chosen)]
        for k in range(1, 5):
            for h in range(0, min(k, len(finishers)) + 1):
                b = k - h
                if (h == 0 and not rhino_on_field) or b > len(bounces):
                    continue
                used = bounces[:b]
                for evo in evos:
                    # the card the evolution needs: played as filler, or already as a return-to-hand card
                    pool, extra = rest, []
                    if evo.source is not None and not any(u[3] == evo.source for u in used):
                        if evo.source in bundle_of:
                            if not any(bd is bundle_of[evo.source] for bd in rest):
                                continue                 # it's played for the Ward in another way
                            pool = [bd for bd in rest if bd is not bundle_of[evo.source]]
                        extra = [own[evo.source]]
                    spare = [(_Card(u[0], u[2]), (_Card(cheap.cost, cheap.name + "（回手再打）", cheap.removal,
                                                         atk=cheap.atk, rush=cheap.rush),))
                             for u in bounces[b:] if u[1] and cheap is not None and u[3] != evo.source]
                    budget = pp + evo.gain - 3 * h - sum(u[0] for u in used) - 3 * len(used) \
                        - sum(c.cost for c in forced + extra)
                    if budget < 0:
                        continue
                    key = (id(chosen), b, budget, evo.source)
                    if key not in cache:
                        cache[key] = _fillers(pool + spare, budget, me.combo)
                    options = cache[key]
                    for n in sorted(options, reverse=True):
                        found = None
                        for cards in options[n]:
                            found = _count(me, base, per, h, b, used, forced + extra + cards, evo,
                                           own.get(evo.source), rhino_hit, ward_life, to_ward, to_face,
                                           field_attack, buffs, wards, rhino_on_field) or found
                            if found and found.damage > best.damage:
                                best = found
                        if found:
                            break                    # fewer filler cards can't deal more
    if can_super and best.damage and not wards and any(0 < f.life <= 5 for f in reachable) \
            and not any("最后一只破魔虫" in d or "撞" in d or d.startswith("进化") for d, _ in best.terms):
        best.damage += 1
        best.terms.append(("超进化撞死一个随从（击退）", 1))
    return best


def _count(me, base, per, h, b, used, cards, evo, evolving, rhino_hit, ward_life, to_ward, to_face,
           field_attack, buffs, wards, rhino_on_field) -> Estimate | None:
    """The damage of one way of playing the turn, or None if it can't clear the Ward."""
    plays = h + b
    f = len(cards)
    start = me.combo + f + 1
    combo_sum = plays * start + plays * (plays - 1) // 2
    # a played return-to-hand card adds 1 to the replay it makes and the later plays; one that
    # returns the finisher already on the field (after it attacked) comes before all of them
    between = sum(plays - (0 if rhino_on_field and i == 0 else h + i) for i, u in enumerate(used) if u[1])
    cairns = sum(c.cairn for c in cards)
    lost_rhino = lost_field = knock = 0
    ward_terms = []
    if ward_life:
        parts = _removal_parts(cards, me.combo)
        if evo.removal:
            parts.append((evo.desc, evo.removal))
        hit, name = _attacker(cards, evo, evolving)
        if hit:
            parts.append((f"进化后的{name}", hit))
        if rhino_hit:
            lost_rhino = base + per * start
            parts.append(("第一只破魔虫", lost_rhino))
        need = ward_life - sum(v for _, v in parts)
        if need > 0 and to_ward:
            parts.append(("场上能打随从的随从", min(need, sum(to_ward))))
            need -= sum(to_ward)
        if need > 0:
            cover = _cheapest_cover(to_face, need)
            if cover is None:
                return None
            parts.append(("场上随从（不打脸了）", cover))
            lost_field = cover
        knock = 1 if evo.knock and hit else 0
        ward_terms = [(f"拆守护（{ward_life} 血）：" + " + ".join(f"{n} {v}" for n, v in parts), 0)]
        if rhino_hit:
            ward_terms.append(("第一只破魔虫去打守护，不打脸", -lost_rhino))
        if knock:
            ward_terms.append(("超进化的随从撞死守护（击退）", 1))
    dmg = per * (combo_sum + between) + base * plays + field_attack + buffs + evo.dmg + cairns \
        - lost_rhino - lost_field + knock
    terms = list(ward_terms)
    terms.append((f"{plays} 次下场的基础连击（{start - f}" + "".join(f"+{start - f + i}" for i in range(1, plays)) + "）",
                  per * (plays * (start - f) + plays * (plays - 1) // 2)))
    if f:
        zeros = sum(1 for c in cards if c.cost <= 0)
        terms.append((f"先打的垫牌 {f} 张（其中 0 费 {zeros} 张），每张 ×{plays}", per * plays * f))
    if between:
        terms.append((f"回手牌 {sum(1 for u in used if u[1])} 张（夹在两次下场之间）", per * between))
    if evo.gain:
        terms.append((evo.desc + "（相当于多出的费用拿去垫牌）", 0))
    if evo.dmg:
        terms.append((evo.desc, evo.dmg))
    if cairns:
        terms.append((f"打出的辉岩再启动给破魔虫加攻 {cairns} 次", cairns))
    if field_attack - lost_field:
        terms.append(("场上随从打脸", field_attack - lost_field))
    if buffs:
        terms.append(("场上辉岩启动给破魔虫加攻", buffs))
    src = f"手出 {h}" + (f"、回手 {b}" if b else "")
    return Estimate(dmg, f"{plays} 虫（{src}）" + ("；对手有守护，先拆" if wards else ""), terms)
