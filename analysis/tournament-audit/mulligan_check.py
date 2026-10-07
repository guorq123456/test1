"""Opening hands under three mulligans, without playing games: default (D), the draft's rules (R-A, R-B).

    cd <svsim checkout> && PYTHONPATH=. python3 <this> [--hands 250] [--seed 31000000]

For each tournament deck, against each of the four (its own included), going first and second,
--hands opening hands dealt by the engine (new_game on one seed per hand; both players' mulligans
decided, the other side keeping all), then both sides pass their turns (no plays) to read the hand
at the start of each own turn, so the draws after the mulligan are the engine's own. Three ways to
choose the redraws:
- D: svsim.agents.mulligan.mulligan, as the bots do now;
- R-A: the draft's §7.1 (only the existing Rules: keep / redraw / at_most, threshold 5);
- R-B: the draft's §7.2 with the extensions as the draft defines them (first / second, by opponent,
  partners `needs` = keep only if some partner is kept, an empty set = not by the base rule; overlays
  by opponent > first/second > base, a later layer overriding a card), plus the conditional
  variants of §5b for 曲千代 and 机锋 when switched on (--variants).
Reported per deck and seat: how often each card is kept when dealt, the mean number redrawn, and the
deck's own goal: ramp-t a ramp card (龙之启示, 金银) in hand at own turn 3; elf-t 妖安 at the evolve turn
(own turn 5 first, 4 second); pirate-t a 2-cost follower at own turn 2; nemesis-t a card of 2 or less
other than 机锋 (follower or amulet) at own turn 2. Mirrors analysis/tournament-audit/mulligan_draft.md
at 2678bab; the reference for 1 号's implementation.
"""
import argparse
from collections import Counter, defaultdict

from svsim.agents.mulligan import Rules, by_rules, mulligan
from svsim.cards import decks
from svsim.core.actions import EndTurn, Mulligan
from svsim.core.engine import apply, new_game
from svsim.ui.session import DECKS

DECKS_T = ("elf-t", "nemesis-t", "ramp-t", "pirate-t")
# ids (mulligan_draft.md §7)
THESTAE, WORLD_GAMES, ROOTED, MIROKU, KUCHIYO = 10714110, 10503210, 10912110, 10514120, 10914110
ELF_REDRAW = {10914110, 10913110, 10712110, 10911110, 10614120, 10811130, 10403120, 10513310, 10913310}
CUTTHROAT, BANISHMENT, ENCROACHED = 10974110, 10972310, 10602210
DRAGONSIGN, LUMIORE, ZOOEY = 10042310, 10844120, 10444120
KIMIKA, VORLALAI, PROMOTER, CRESTPETAL, LYRIA, FOXFIRE = 10842120, 10644120, 10741110, 10543310, 10403120, 10843310
QUICKBLADER, SCOUT, YIDMETRA, OPERATIVE, GUNNER, FIRST_MATE = 10021110, 10921110, 10624120, 10722110, 10922110, 10923110
SPLENDOR, LAGE_DOR, SEVERED_TIES, ZETA_BEA, BARBAROS = 10523310, 10923310, 10922310, 10424110, 10924110
EARLY = {QUICKBLADER, SCOUT, YIDMETRA, OPERATIVE, GUNNER, FIRST_MATE}
LOW_FOLLOWERS, TWO_DROPS = {QUICKBLADER, YIDMETRA, OPERATIVE, SCOUT}, {YIDMETRA, OPERATIVE, SCOUT}

RULES_A = {
    "elf-t": Rules(keep=frozenset({THESTAE, WORLD_GAMES, ROOTED, MIROKU}), redraw=frozenset(ELF_REDRAW)),
    "nemesis-t": Rules(keep=frozenset({CUTTHROAT, BANISHMENT})),
    "ramp-t": Rules(keep=frozenset({DRAGONSIGN, LUMIORE, ZOOEY}),
                    redraw=frozenset({KIMIKA, VORLALAI, PROMOTER, CRESTPETAL, LYRIA, FOXFIRE})),
    "pirate-t": Rules(keep=frozenset(EARLY), redraw=frozenset({SEVERED_TIES, ZETA_BEA}), at_most={FIRST_MATE: 1}),
}


def layer(base, *overlays):
    """keep / redraw / at_most / needs, later layers overriding a card."""
    keep, redraw = set(base.get("keep", ())), set(base.get("redraw", ()))
    at_most, needs = dict(base.get("at_most", {})), dict(base.get("needs", {}))
    for o in overlays:
        if not o:
            continue
        for c in o.get("keep", ()):
            keep.add(c)
            redraw.discard(c)
        for c in o.get("redraw", ()):
            redraw.add(c)
            keep.discard(c)
            needs.pop(c, None)
        at_most.update(o.get("at_most", {}))
        needs.update(o.get("needs", {}))
    return keep, redraw, at_most, needs


def rules_b(deck, opp, first, variants):
    if deck == "elf-t":
        base = {"keep": {THESTAE, WORLD_GAMES, ROOTED, MIROKU}, "redraw": ELF_REDRAW}
        vs = {}
        if variants:                                          # §5b: 曲千代 with two cheap cards, not against ramp
            if opp != "ramp-t":
                vs = {"keep": {KUCHIYO}, "at_most": {KUCHIYO: 1}, "count": {KUCHIYO: ("cheap", 2)}}
        return layer(base, vs), base.get("need_one_of")
    if deck == "nemesis-t":
        base = {"keep": {CUTTHROAT, BANISHMENT}}
        vs = {"keep": {ENCROACHED}} if opp == "elf-t" else {}
        return layer(base, vs), None
    if deck == "ramp-t":
        base = {"keep": {DRAGONSIGN, LUMIORE, ZOOEY, KIMIKA, VORLALAI, LYRIA}, "redraw": {PROMOTER, CRESTPETAL, FOXFIRE},
                "needs": {KIMIKA: {VORLALAI}, VORLALAI: {KIMIKA}, LYRIA: set()}}
        seat = ({"needs": {KIMIKA: {VORLALAI, DRAGONSIGN}, VORLALAI: {KIMIKA, DRAGONSIGN}, LYRIA: {DRAGONSIGN}}}
                if first else {"redraw": {ZOOEY}})
        vs = {"elf-t": None if first else {"keep": {PROMOTER, CRESTPETAL}, "redraw": {KIMIKA, VORLALAI}},
              "nemesis-t": None if first else {"keep": {PROMOTER}},
              "ramp-t": {"redraw": {KIMIKA, VORLALAI, LYRIA}}}.get(opp)
        return layer(base, seat, vs), None
    base = {"keep": EARLY, "redraw": {SEVERED_TIES, ZETA_BEA}, "at_most": {FIRST_MATE: 1},
            "needs": {SPLENDOR: EARLY, LAGE_DOR: EARLY}}
    vs = ({"keep": {ZETA_BEA, BARBAROS}, "at_most": {BARBAROS: 1}, "needs": {ZETA_BEA: TWO_DROPS, BARBAROS: LOW_FOLLOWERS}}
          if opp == "ramp-t" else None)
    return layer(base, vs), None


def decide_b(hand, deck, opp, first, variants, threshold=5):
    (keep, redraw, at_most, needs), _ = rules_b(deck, opp, first, variants)
    keep_idx = set()
    counts = Counter()
    for i, c in enumerate(hand):
        cid = c.defn.card_id
        if cid in redraw:
            continue
        if cid in at_most and counts[cid] >= at_most[cid]:
            continue
        if cid in keep or (c.cost < threshold and cid not in needs):
            keep_idx.add(i)
            counts[cid] += 1
    changed = True                                       # partners: drop a kept card whose partners are all gone
    while changed:
        changed = False
        kept_ids = {hand[i].defn.card_id for i in keep_idx}
        for i in sorted(keep_idx):
            cid = hand[i].defn.card_id
            if cid in needs and not (set(needs[cid]) & (kept_ids - {cid} if list(kept_ids).count(cid) < 2 else kept_ids)):
                keep_idx.discard(i)
                changed = True
                break
    if variants and deck == "elf-t":                     # 曲千代 needs two other cards of cost 1-2 kept
        cheap = sum(1 for i in keep_idx if hand[i].cost <= 2 and hand[i].defn.card_id != KUCHIYO)
        if cheap < 2:
            keep_idx -= {i for i in keep_idx if hand[i].defn.card_id == KUCHIYO}
    if variants and deck == "nemesis-t":                 # no play for turns 1-2 but 机锋: 4-costs go back too
        early = sum(1 for i in keep_idx if hand[i].cost <= 2 and hand[i].defn.card_id != CUTTHROAT
                    and (hand[i].defn.is_follower or hand[i].defn.is_amulet))
        if not early:
            keep_idx -= {i for i in keep_idx if hand[i].cost == 4}
    return tuple(i for i in range(len(hand)) if i not in keep_idx)


def goal(deck, hands_by_turn, first):
    if deck == "ramp-t":
        return any(c.defn.card_id in (DRAGONSIGN, LUMIORE) for c in hands_by_turn[3])
    if deck == "elf-t":
        return any(c.defn.card_id == THESTAE for c in hands_by_turn[5 if first else 4])
    if deck == "pirate-t":
        return any(c.defn.card_id in TWO_DROPS for c in hands_by_turn[2])
    return any(c.cost <= 2 and c.defn.card_id != CUTTHROAT and (c.defn.is_follower or c.defn.is_amulet)
               for c in hands_by_turn[2])


def run_hand(deck, opp, seat, seed, method, variants):
    names = [deck, opp] if seat == 0 else [opp, deck]
    st = new_game(decks.build(DECKS[names[0]][1]), decks.build(DECKS[names[1]][1]), seed=seed)
    first = st.first == seat
    dealt = None
    for _ in range(2):
        p = st.players[st.active]
        if st.active == seat:
            dealt = list(p.hand)
            if method == "D":
                act = mulligan(st)
            elif method == "A":
                act = Mulligan(by_rules(p.hand, RULES_A[deck]))
            else:
                act = Mulligan(decide_b(p.hand, deck, opp, first, variants))
            redrawn = len(act.indices)
            kept_ids = [c.defn.card_id for i, c in enumerate(p.hand) if i not in act.indices]
        else:
            act = Mulligan(())
        apply(st, act)
    hands = {}
    while st.players[seat].turns_taken < 6 and not st.over:
        if st.active == seat:
            hands[st.players[seat].turns_taken] = list(st.players[seat].hand)
        apply(st, EndTurn())
    return first, dealt, kept_ids, redrawn, goal(deck, hands, first)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hands", type=int, default=250)
    ap.add_argument("--seed", type=int, default=31000000)
    ap.add_argument("--variants", action="store_true")
    ap.add_argument("--glossary", default=None, help="card-glossary.md: print the common names")
    args = ap.parse_args()
    from svsim.cards.pool import POOL
    common = {}
    if args.glossary:
        for line in open(args.glossary, encoding="utf-8"):
            if line.startswith("| **"):
                cols = [c.strip() for c in line.strip().strip("|").split("|")]
                common[cols[2]] = f"{cols[0].strip('*')}（{cols[1]}）"
    print("条件：对手卡表已知（牌序、手牌未知）；只比起手，不打对局。")
    for deck in DECKS_T:
        print(f"\n== {deck}（每个对手 × 先后手 {args.hands} 手）")
        res = {m: defaultdict(lambda: [0, 0, 0, 0]) for m in "DAB"}      # (first) -> [hands, redrawn, goal, ...]
        keep_rate = {m: defaultdict(lambda: [0, 0]) for m in "DAB"}
        for opp in DECKS_T:
            for seat in (0, 1):
                for h in range(args.hands):
                    seed = args.seed + h
                    for m in "DAB":
                        first, dealt, kept, redrawn, ok = run_hand(deck, opp, seat, seed, m, args.variants)
                        r = res[m][first]
                        r[0] += 1
                        r[1] += redrawn
                        r[2] += ok
                        dealt_ids = Counter(c.defn.card_id for c in dealt)
                        kept_c = Counter(kept)
                        for cid, n in dealt_ids.items():
                            keep_rate[m][cid][0] += n
                            keep_rate[m][cid][1] += min(kept_c[cid], n)
        for first in (True, False):
            print(f"  {'先手' if first else '后手'}：" + "；".join(
                f"{m} 平均换 {res[m][first][1] / res[m][first][0]:.2f} 张、目标达成 {res[m][first][2] / res[m][first][0]:.1%}"
                for m in "DAB"))
        rows = sorted(keep_rate["D"], key=lambda c: -keep_rate["D"][c][0])
        print("  每张牌发到时留下的比例（D / R-A / R-B）：")
        for cid in rows:
            nm = POOL[cid].name_zh if cid in POOL else str(cid)
            nm = common.get(nm, nm)
            cells = " / ".join(f"{keep_rate[m][cid][1] / max(keep_rate[m][cid][0], 1):.0%}" for m in "DAB")
            print(f"    {nm:<20} {cells}")


if __name__ == "__main__":
    main()
