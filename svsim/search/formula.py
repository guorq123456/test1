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
- the same counting works for 1, 3 or 4 finisher plays.

Checked against the planner on 120 positions, two more terms came up and are
counted too: evolving the last finisher itself (+3 super, +2 normal; the one
evolution of the turn, so instead of recovering play points with it), and an
amulet that is first a card to play and then engaged to give the finisher +1
(Lambent Cairn).

"First check whether the damage is enough, then work out how": `estimate`
gives the most damage this arithmetic allows and a breakdown in those terms;
search.combo then finds and checks the actual line. Cards are classified from
their measured profiles (search.combo.profile), not from a card list.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from svsim.core.engine import EVOLVE_TURN, SUPER_EVOLVE_TURN
from svsim.core.enums import Keyword
from svsim.core.state import GameState
from svsim.search.combo import at_combo, engage_profile, evolve_profile, profile
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
        if e.per_combo >= 1 and e.attacks >= 1:
            return e.base, e.per_combo
    return None


def _net_cost(defn) -> tuple[int, tuple]:
    """Cheapest way to play a card: (net play points, cards it adds), counting the
    cards it adds as reached at Combo 3."""
    best = None
    for variants in profile(defn):
        e = at_combo(variants, 3)
        key = (e.paid - e.recovered, -len(e.added))
        if best is None or key < best[0]:
            best = (key, e)
    e = best[1]
    return e.paid - e.recovered, e.added


def estimate(state: GameState) -> Estimate:
    me, opp = state.players[state.active], state.players[1 - state.active]
    first = state.active == state.first
    wards = any(f.keywords & Keyword.WARD for f in opp.followers)
    finishers, fodder, bounces, recoverers, cairns_in_hand = [], [], [], [], []
    for c in me.hand:
        fin = _finisher(c.defn)
        if fin:
            finishers.append((c, fin))
            continue
        variants = profile(c.defn)
        if any(v[0].bounce for v in variants):
            bounces.append((c.cost, 1, card_name(c.defn), c.defn))
            continue
        eng = engage_profile(c.defn) if c.defn.is_amulet else None
        if eng is not None and eng.bounce:
            bounces.append((c.cost + eng.paid, 1, card_name(c.defn) + "（下场后启动）", c.defn))
            continue
        net, added = _net_cost(c.defn)
        fodder.append([net - (c.defn.cost - c.cost)] + sorted(cost for _, cost in added))
        if eng is not None and eng.buff > 0:
            cairns_in_hand.append(net)
    for c in me.field:
        eng = engage_profile(c.defn) if c.defn.is_amulet and c.engaged_turn != state.turn else None
        if eng is not None and eng.bounce:
            bounces.append((eng.paid, 0, card_name(c.defn) + "（场上启动）", c.defn))
    buffs = sum(1 for c in me.field if c.defn.is_amulet and c.engaged_turn != state.turn
                and (engage_profile(c.defn) or None) and engage_profile(c.defn).buff > 0)
    ready = [f for f in me.followers if (f.keywords & Keyword.STORM or f.entered_turn != state.turn)
             and f.attacks_made < f.max_attacks]
    field_attack = 0 if wards else sum(f.atk for f in ready)
    rhino_on_field = any(_finisher(f.defn) for f in me.followers)
    can_evolve = not me.evolved_this_turn and me.ep > 0 and me.turns_taken >= EVOLVE_TURN[first]
    can_super = not me.evolved_this_turn and me.sep > 0 and me.turns_taken >= SUPER_EVOLVE_TURN[first]
    for c in me.hand:
        for super_, ok in ((True, can_super), (False, can_evolve)):
            if ok and c.defn.is_follower and not _finisher(c.defn):
                gain = evolve_profile(c.defn, super_).recovered
                if gain:
                    recoverers.append((gain, f"{'超进化' if super_ else '进化'}{card_name(c.defn)}回 {gain} 费"))
    pp = me.pp + (1 if me.bonus_ready and not me.bonus_active else 0)
    base, per = finishers[0][1] if finishers else (0, 1)
    best = Estimate(field_attack, "没有能打脸的破魔虫：只算场上的攻击",
                    [("场上随从打脸", field_attack)] if field_attack else [])
    bounces.sort(key=lambda b: (b[0], -b[1]))
    fodder.sort(key=lambda bundle: sum(bundle) / len(bundle))   # a card with what it adds, cheapest per card first
    evo_options = [(0, "", 0)] + [(g, d, 0) for g, d in recoverers]
    if can_super or can_evolve:                    # or evolve the last finisher itself
        evo_options.append((0, f"{'超进化' if can_super else '进化'}最后一只破魔虫", 3 if can_super else 2))
    for k in range(1, 5):
        for h in range(0, min(k, len(finishers)) + 1):
            b = k - h
            if (h == 0 and not rhino_on_field) or b > len(bounces):
                continue
            used = bounces[:b]
            for gain, evo_desc, evo_dmg in evo_options:
                budget = pp + gain - 3 * h - sum(u[0] for u in used)
                replays = sum(1 for u in used)          # finishers returned and played again
                budget -= 3 * replays
                if budget < 0:
                    continue
                taken, spent = [], 0
                for bundle in fodder:              # the card itself first, then what it adds
                    if spent + bundle[0] > budget:
                        continue
                    for cost in bundle:
                        if spent + cost <= budget:
                            taken.append(cost)
                            spent += cost
                f = len(taken)
                plays = k
                start_combo = me.combo + f + 1
                combo_sum = plays * start_combo + plays * (plays - 1) // 2
                between = 0                              # played return-to-hand cards
                for i, u in enumerate(used):
                    if u[1]:
                        between += plays - (h + i)        # adds 1 to this replay and later ones
                played_cairns = min(len(cairns_in_hand), sum(1 for c in taken if c >= 2))
                dmg = per * (combo_sum + between) + base * plays + field_attack + buffs + evo_dmg + played_cairns
                terms = [(f"{plays} 次下场的基础连击（{start_combo - f}"
                          + "".join(f"+{start_combo - f + i}" for i in range(1, plays)) + "）",
                          per * (plays * (start_combo - f) + plays * (plays - 1) // 2))]
                if f:
                    zeros = sum(1 for c in taken if c <= 0)
                    terms.append((f"先打的垫牌 {f} 张（其中 0 费 {zeros} 张），每张 ×{plays}", per * plays * f))
                if between:
                    terms.append((f"回手牌 {sum(1 for u in used if u[1])} 张（夹在两次下场之间）", per * between))
                if gain:
                    terms.append((evo_desc + "（相当于多出的费用拿去垫牌）", 0))
                if evo_dmg:
                    terms.append((evo_desc, evo_dmg))
                if played_cairns:
                    terms.append((f"打出的辉岩再启动给破魔虫加攻 {played_cairns} 次", played_cairns))
                if field_attack:
                    terms.append(("场上随从打脸", field_attack))
                if buffs:
                    terms.append(("场上辉岩启动给破魔虫加攻", buffs))
                if dmg > best.damage:
                    src = f"手出 {h}" + (f"、回手 {b}" if b else "")
                    best = Estimate(dmg, f"{plays} 虫（{src}）" + ("；对手有守护，场上攻击不算" if wards else ""),
                                    terms)
    if can_super and best.damage and any(0 < f.life <= 5 for f in opp.followers) \
            and not any("最后一只破魔虫" in d for d, _ in best.terms):
        best.damage += 1
        best.terms.append(("超进化撞死一个随从（击退）", 1))
    return best
