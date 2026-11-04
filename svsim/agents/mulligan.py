"""Opening-hand redraws (every agent uses `mulligan`).

The first layer that applies wins:

0. What the player's games say (svsim.learn.timing, built by tools.timing for a
   deck against an opponent deck): their own keeps and redraws, with their
   words below as the prior and, for cards they said nothing about, how soon
   they play a copy they hold.
1. The player's rules for a deck they know (`PLAYER_RULES`, their words):
   Rhinoceroach Forest (2026-10-06): its only cards of 5 or more are Glade and
   Bayle. Glade draws, clears and evolves in one card (against midrange decks
   a must-keep); Bayle is only strong once it costs 0, so keeping one is
   usually right (a 0-cost Bayle refills the board mid-game or adds to the
   Rhinoceroach turn) and a second is not wanted. Some cheap cards should go
   back: Baby Carbuncle only pays off after the super-evolution turns, and
   Lambent Cairn, Eradicating Arrow and Virid Lieutenant look cheap but are
   mid-game cards.
2. A deck built around ramp (one card in eight or more raises max play
   points, search.race.ramps) keeps the ramp and redraws the rest, all of it
   if there is none: the player's way with Ramp Dragon against Rhinoceroach
   Forest ("留牌围着跳费走，很多时候全换找跳费").
3. Otherwise, redraw what costs 5 or more.

That is the default ("default"). Two other ways, for one agent at a time (arena `+mull=...`,
`decide`), are compared with it at equal compute before either replaces it:
- "rules[:VARIANT,...]": the test session's rules for the tournament decks (`DRAFT_RULES`, from
  their draft of 2026-10-07 with its sources: players' guides and the player's words), with
  `VARIANTS` switched on by name; a deck without a draft rule plays as by default.
- "sim[:N[:H]]": the bot works the keep out itself (agents.sim_mulligan): every redraw, N short
  play-outs of H turns each, the best on average. The player (2026-10-07): which cheap cards to keep
  "都不能下定论，要看一部分情况".

`Rules` beyond keep / redraw / at_most (the test session's extensions; their defaults are the old
behaviour): `first` / `second` add rules going first or second, `vs` by the opponent's named deck
(itself with first / second), `needs` keeps a card only with partners (`Need`), `need_one_of`
redraws the whole hand when it has none of those cards. Layers go base, side, opponent, the
opponent's side; a layer's keeps leave the layers below's redraws and its redraws their keeps, and
`at_most` and `needs` go by card id (`resolve`).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from svsim.cards import decks, forest, unlimited
from svsim.core.actions import Mulligan


@dataclass(frozen=True)
class Need:
    """A card is kept only if at least `n` other cards of `cards` are kept (`in_hand`: are in the
    opening hand, kept or not). No cards: never kept for its own sake (a layer above may say otherwise)."""
    cards: frozenset = frozenset()
    n: int = 1
    in_hand: bool = False


@dataclass(frozen=True)
class Rules:
    redraw: frozenset = frozenset()       # card ids always sent back
    keep: frozenset = frozenset()         # card ids always kept, whatever they cost
    at_most: dict = field(default_factory=dict)   # card id -> copies worth keeping
    first: "Rules | None" = None          # added going first
    second: "Rules | None" = None         # added going second
    vs: dict = field(default_factory=dict)        # opponent's named deck -> Rules added
    needs: dict = field(default_factory=dict)     # card id -> Need (or a frozenset of partners: Need(it))
    need_one_of: frozenset = frozenset()  # none of these in the hand: redraw it all


def overlay(base: Rules, top: "Rules | None") -> Rules:
    """`top` laid over `base` (their first / second / vs are resolve's business and not kept)."""
    if top is None:
        return base
    return Rules(redraw=(base.redraw - top.keep) | top.redraw, keep=(base.keep - top.redraw) | top.keep,
                 at_most={**base.at_most, **top.at_most}, needs={**base.needs, **top.needs},
                 need_one_of=top.need_one_of or base.need_one_of)


def resolve(rules: Rules, going_first: bool, foe: "str | None") -> Rules:
    """The rules for one game: base, then going first / second, then against `foe`, then its side."""
    side = (lambda r: r.first if going_first else r.second)
    out = overlay(Rules(rules.redraw, rules.keep, rules.at_most, needs=rules.needs,
                        need_one_of=rules.need_one_of), side(rules))
    against = rules.vs.get(foe)
    if against is not None:
        out = overlay(overlay(out, against), side(against))
    return out


PLAYER_RULES = {
    "rhino": Rules(
        redraw=frozenset(c.card_id for c in (unlimited.BABY_CARBUNCLE, unlimited.LAMBENT_CAIRN,
                                              unlimited.ERADICATING_ARROW, forest.VIRID_LIEUTENANT)),
        keep=frozenset({unlimited.GLADE.card_id, unlimited.BAYLE.card_id}),
        at_most={unlimited.BAYLE.card_id: 1}),
}

# The test session's rules for the tournament decks (analysis/tournament-audit/mulligan_draft.md §7.2 on
# branch ccr-da4857cc-rkpgwr 2678bab; each rule's source and confidence are there). Not in PLAYER_RULES:
# they replace the default only for an agent asked to use them ("rules"), until a gate says so.
THESTAE, WORLD_GAMES, ROOTED, MIROKU, QCY = 10714110, 10503210, 10912110, 10514120, 10914110
CUTTHROAT, BANISHMENT, ENCROACHED = 10974110, 10972310, 10602210
DRAGONSIGN, LUMIORE, ZOOEY = 10042310, 10844120, 10444120
KIMIKA, VORLALAI, PROMOTER, CRESTPETAL, LYRIA, FOXFIRE = 10842120, 10644120, 10741110, 10543310, 10403120, 10843310
QUICKBLADER, SCOUT, YIDMETRA, OPERATIVE, GUNNER, FIRST_MATE = (10021110, 10921110, 10624120, 10722110, 10922110,
                                                               10923110)
SPLENDOR, LAGE_DOR, SEVERED_TIES, ZETA_BEA, BARBAROS = 10523310, 10923310, 10922310, 10424110, 10924110
LOW_FOLLOWERS = frozenset({QUICKBLADER, YIDMETRA, OPERATIVE, SCOUT})    # 1-2 play point followers
TWO_DROPS = frozenset({YIDMETRA, OPERATIVE, SCOUT})
EARLY = frozenset({QUICKBLADER, SCOUT, YIDMETRA, OPERATIVE, GUNNER, FIRST_MATE})

DRAFT_RULES = {
    "elf-t": Rules(                                # 妖安, 大游戏世界; else 根延潜伏者, 魅禄; the rest back (Spicies)
        keep=frozenset({THESTAE, WORLD_GAMES, ROOTED, MIROKU}),
        redraw=frozenset({QCY, 10913110, 10712110, 10911110, 10614120, 10811130, 10403120, 10513310, 10913310})),
    "nemesis-t": Rules(
        keep=frozenset({CUTTHROAT, BANISHMENT}),
        vs={"elf-t": Rules(keep=frozenset({ENCROACHED}))}),
    "ramp-t": Rules(
        keep=frozenset({DRAGONSIGN, LUMIORE, ZOOEY, KIMIKA, VORLALAI, LYRIA}),
        redraw=frozenset({PROMOTER, CRESTPETAL, FOXFIRE}),
        needs={KIMIKA: frozenset({VORLALAI}), VORLALAI: frozenset({KIMIKA}), LYRIA: frozenset()},
        first=Rules(needs={KIMIKA: frozenset({VORLALAI, DRAGONSIGN}), VORLALAI: frozenset({KIMIKA, DRAGONSIGN}),
                           LYRIA: frozenset({DRAGONSIGN})}),
        second=Rules(redraw=frozenset({ZOOEY})),
        vs={"elf-t": Rules(second=Rules(keep=frozenset({PROMOTER, CRESTPETAL}), redraw=frozenset({KIMIKA, VORLALAI}))),
            "nemesis-t": Rules(second=Rules(keep=frozenset({PROMOTER}))),
            "ramp-t": Rules(redraw=frozenset({KIMIKA, VORLALAI, LYRIA}))}),
    "pirate-t": Rules(
        keep=EARLY, redraw=frozenset({SEVERED_TIES, ZETA_BEA}), at_most={FIRST_MATE: 1},
        needs={SPLENDOR: EARLY, LAGE_DOR: EARLY},
        vs={"ramp-t": Rules(keep=frozenset({ZETA_BEA, BARBAROS}), at_most={BARBAROS: 1},
                            needs={ZETA_BEA: TWO_DROPS, BARBAROS: LOW_FOLLOWERS}),
            "nemesis-t": Rules(keep=frozenset({SEVERED_TIES}), needs={SEVERED_TIES: TWO_DROPS})}),
}


def _cheap(deck: str, most: int, but=frozenset()) -> frozenset:
    """A tournament deck's cards of at most `most` play points, less `but`."""
    return frozenset(c.card_id for c in decks.build(decks.NAMED[deck]) if c.cost <= most) - but


def _elf_qcy(n: int, foes) -> dict:
    keep_one = Rules(keep=frozenset({QCY}), at_most={QCY: 1},
                     needs={QCY: Need(_cheap("elf-t", 2, frozenset({QCY})), n, in_hand=True)})
    return {"elf-t": Rules(vs={foe: keep_one for foe in foes})}


def _nemesis_early() -> dict:
    early = frozenset(c.card_id for c in decks.build(decks.NAMED["nemesis-t"])
                      if c.cost <= 2 and (c.is_follower or c.is_amulet)) - {CUTTHROAT}
    fours = frozenset(c.card_id for c in decks.build(decks.NAMED["nemesis-t"]) if c.cost == 4)
    return {"nemesis-t": Rules(needs={cid: Need(early, 1, in_hand=True) for cid in fours})}


# Switchable variants of the draft (its §5b): the player's "看情况" written as conditions, each for a gate.
# 曲千代 kept once with 2 (3) other cards of 1-2 play points in the hand against Pirate, Elf or Nemesis
# ("p": Pirate only), never against Ramp; Nemesis redraws its 4s too when the hand has nothing for turns
# 1-2 but 机锋; Ramp redraws the whole hand without a ramp card (the player: 很多时候全换找跳费).
VARIANTS = {
    "qcy2": lambda: _elf_qcy(2, ("pirate-t", "elf-t", "nemesis-t")),
    "qcy3": lambda: _elf_qcy(3, ("pirate-t", "elf-t", "nemesis-t")),
    "qcy2p": lambda: _elf_qcy(2, ("pirate-t",)),
    "qcy3p": lambda: _elf_qcy(3, ("pirate-t",)),
    "nem4": _nemesis_early,
    "allramp": lambda: {"ramp-t": Rules(need_one_of=frozenset({DRAGONSIGN, LUMIORE, ZOOEY}))},
}


def draft_rules(deck: str | None, going_first: bool, foe: str | None, variants=()) -> Rules | None:
    """The draft's rules for `deck` in one game, with `variants` (VARIANTS keys) laid over them."""
    rules = DRAFT_RULES.get(deck)
    if rules is None:
        return None
    out = resolve(rules, going_first, foe)
    for name in variants:
        extra = VARIANTS[name]().get(deck)
        if extra is not None:
            out = overlay(out, resolve(extra, going_first, foe))
    return out


_DECK_KEYS: dict = {}


def _deck_key(cards) -> str | None:
    """Which of the known decks these 40 cards are, if any."""
    if not _DECK_KEYS:
        for key, listing in decks.NAMED.items():                # every named deck (the tournament ones too)
            _DECK_KEYS[tuple(sorted(c.card_id for c in decks.build(listing)))] = key
    return _DECK_KEYS.get(tuple(sorted(c.defn.card_id for c in cards)))


def by_rules(hand, rules: Rules, threshold: int = 5) -> tuple:
    ids = [c.defn.card_id for c in hand]
    if rules.need_one_of and not rules.need_one_of.intersection(ids):
        return tuple(range(len(hand)))
    kept, counts = [], {}
    for i, c in enumerate(hand):
        cid = ids[i]
        if cid in rules.redraw:
            continue
        if cid in rules.at_most and counts.get(cid, 0) >= rules.at_most[cid]:
            continue
        if cid in rules.keep or c.cost < threshold:
            kept.append(i)
            counts[cid] = counts.get(cid, 0) + 1
    changed = True
    while changed:                                # cards without their partners go, until nothing changes
        changed = False
        for i in list(kept):
            need = rules.needs.get(ids[i])
            if need is None:
                continue
            if not isinstance(need, Need):
                need = Need(frozenset(need))
            pool = range(len(hand)) if need.in_hand else kept
            if sum(1 for j in pool if j != i and ids[j] in need.cards) < need.n:
                kept.remove(i)
                changed = True
    return tuple(i for i in range(len(hand)) if i not in kept)


def decide(state, spec: str = "default", threshold: int = 5, seed: int = 0) -> tuple:
    """The hand positions to redraw for the player to act in `state` (at the mulligan), by `spec`:
    "default", "rules[:VARIANT,...]", "sim[:N[:H]]" (see the module's docstring) or "by:DECK=SPEC/DECK=SPEC" (one
    of those per deck key, "default" for the decks not named). Plays no game: the
    test session compares the ways on fixed opening hands with it (`opening` deals one)."""
    kind, _, arg = spec.partition(":")
    if kind == "default":
        return mulligan(state, threshold).indices
    p = state.players[state.active]
    if kind == "by":                               # by:DECK=SPEC/DECK=SPEC: per deck, the default for the others
        ways = dict(part.split("=", 1) for part in arg.split("/") if part)
        return decide(state, ways.get(_deck_key(p.hand + p.deck), "default"), threshold, seed)
    if kind == "rules":
        foe = state.players[1 - state.active]
        rules = draft_rules(_deck_key(p.hand + p.deck), state.active == state.first, _deck_key(foe.hand + foe.deck),
                            tuple(v for v in arg.split(",") if v))
        return by_rules(p.hand, rules, threshold) if rules is not None else mulligan(state, threshold).indices
    if kind == "sim":
        from svsim.agents.sim_mulligan import simulated
        parts = [int(x) for x in arg.split(":") if x]
        return simulated(state, *parts, seed=seed)
    raise ValueError(f"unknown mulligan {spec!r}")


# The opening redraw a deck uses by default where it isn't the agents' own (mulligan). None since
# 2026-10-08 05:27Z: the tournament Combo Forest had the drafted rules from 02:46Z (R - D +2.7% +- 2.1%
# over 1200 pairs against a pool of the four tournament decks), but the re-gate at the deployed state
# (four parts pooled, 1200 pairs) gave R - D +0.5% +- 2.0%, lower end -1.5% <= 0, so it went back to the
# default by the registered rule. Bots measured while it held pin it with "+mull=by:elf-t=rules" (the
# ruler, ruler20261008). Chosen by the deck's name: a way to redraw, not a feature of the evaluation.
BY_DECK: dict = {}


def opening_redraw(state) -> Mulligan:
    """The agents' own opening redraw: BY_DECK's way for the deck the player to act plays, else mulligan."""
    p = state.players[state.active]
    spec = BY_DECK.get(_deck_key(p.hand + p.deck))
    return Mulligan(decide(state, spec)) if spec else mulligan(state)


class MulliganMode:
    """`base` with its opening redraw by `spec` (decide); every other decision is `base`'s."""

    def __init__(self, base, spec: str, seed: int = 0):
        decide_spec_ok(spec)
        self.base, self.spec, self.seed = base, spec, seed

    def act(self, state, actions):
        from svsim.core.enums import Phase
        if state.phase == Phase.MULLIGAN:
            return Mulligan(decide(state, self.spec, seed=self.seed))
        return self.base.act(state, actions)


def decide_spec_ok(spec: str) -> None:
    """ValueError for a mulligan spec decide would not take."""
    kind, _, arg = spec.partition(":")
    if kind == "by":
        for part in arg.split("/"):
            deck, eq, way = part.partition("=")
            if not eq or not deck or way.startswith("by"):
                raise ValueError(f"mulligan by takes by:DECK=SPEC/DECK=SPEC, not {spec!r}")
            decide_spec_ok(way)
    elif kind == "rules":
        bad = [v for v in arg.split(",") if v and v not in VARIANTS]
        if bad:
            raise ValueError(f"unknown mulligan variants {bad}")
    elif kind == "sim":
        if not all(x.isdigit() for x in arg.split(":") if x) or len([x for x in arg.split(":") if x]) > 2:
            raise ValueError(f"mulligan sim takes sim[:N[:H]], not {spec!r}")
    elif kind != "default":
        raise ValueError(f"unknown mulligan {spec!r}")


def opening(deck: str, opponent: str, first: bool, seed: int):
    """A new game of the named decks (ui.session.DECKS) at `deck`'s mulligan, going first or second."""
    from svsim.core.engine import apply, new_game
    from svsim.ui.session import DECKS
    state = new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1]), seed=seed,
                     first=0 if first else 1)
    if state.active != 0:                          # the opponent redraws first: as by default
        apply(state, mulligan(state))
    return state


def mulligan(state, threshold: int = 5) -> Mulligan:
    from svsim.search.race import ramps
    from svsim.learn.timing import load
    p = state.players[state.active]
    cards = p.hand + p.deck
    deck = _deck_key(cards)
    rules = PLAYER_RULES.get(deck)
    foe = state.players[1 - state.active]
    timing = load(deck, _deck_key(foe.hand + foe.deck)) if deck else None
    if timing is not None:
        return Mulligan(timing.keep(p.hand, cards, rules))
    if rules is not None:
        return Mulligan(by_rules(p.hand, rules, threshold))
    if 8 * sum(ramps(c.defn) for c in cards) >= len(cards):
        return Mulligan(tuple(i for i, c in enumerate(p.hand) if not ramps(c.defn)))
    return Mulligan(tuple(i for i, c in enumerate(p.hand) if c.cost >= threshold))
