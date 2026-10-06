"""When each card gets used, learned from a player's games.

The player's way of keeping an opening hand, and of not spending a card
before its time, comes down to timing (2026-10-06): Baby Carbuncle only pays
off after the super-evolution turns, Lambent Cairn and Eradicating Arrow are
mid-game cards however cheap, Bayle is wanted once, at 0 cost. Their ten games
against Ramp Dragon show it in numbers: the cards they keep are the ones they
play in their first four turns, the ones they send back are played on their
seventh or eighth.

`collect(records)` counts, for the deck the player used against one opponent
deck, card by card and own turn by own turn: how many copies were in the
player's hand during the turn and how many were played (`hazard`: the chance a
copy in hand gets played that turn), and at the opening redraw, how many were
kept or sent back (first copy of a card in the hand apart from later copies).
`Timing.keep` turns that into a redraw decision, card by card:

- what the player said about a card (agents.mulligan.PLAYER_RULES) is the
  prior when there is one; otherwise how often a copy kept in hand gets played
  in the first turns (`early`), against the same for a card drawn instead;
- the player's own keeps and redraws then move it, like a coin's record moves
  a guess about the coin (two pseudo-games for the prior).

Nothing here is written per card: another deck or matchup needs only games.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from svsim.core.actions import Mulligan, PlayCard
from svsim.core.enums import Phase

TURNS = 10                      # own turns counted; later ones go with the 10th
EARLY = 4                       # "the first turns" for keeping a card
PRIOR = 2.0                     # pseudo-games behind the prior
FOLDER = Path(__file__).with_name("timing")


@dataclass
class CardStats:
    in_hand: list = field(default_factory=lambda: [0] * (TURNS + 1))   # by own turn (index 1..TURNS)
    played: list = field(default_factory=lambda: [0] * (TURNS + 1))
    kept: list = field(default_factory=lambda: [0, 0])                  # first copy, later copies
    redrawn: list = field(default_factory=lambda: [0, 0])


@dataclass
class Timing:
    deck: str
    opponent: str
    games: int = 0
    cards: dict = field(default_factory=dict)          # card id -> CardStats

    # --- what the counts say ------------------------------------------------------------

    def _stats(self, cid: int) -> CardStats:
        return self.cards.get(cid) or CardStats()

    def hazard(self, cid: int, turn: int) -> float:
        """Chance a copy in hand during own turn `turn` is played that turn (smoothed
        towards the card's rate over all turns)."""
        s = self._stats(cid)
        t = max(1, min(turn, TURNS))
        overall = (sum(s.played) + 0.5) / (sum(s.in_hand) + 1.0)
        return (s.played[t] + overall) / (s.in_hand[t] + 1.0)

    def early(self, cid: int, turns: int = EARLY) -> float:
        """Chance a copy in hand from the start is played within the first `turns` own turns."""
        miss = 1.0
        for t in range(1, turns + 1):
            miss *= 1.0 - self.hazard(cid, t)
        return 1.0 - miss

    def hold(self, cid: int, turn: int) -> float:
        """Chance the player would still be holding a copy they have had since the
        start, at the end of own turn `turn` (the card isn't due yet)."""
        key = (cid, turn)
        cache = self.__dict__.setdefault("_hold", {})
        if key not in cache:
            keep = 1.0
            for t in range(1, max(1, min(turn, TURNS)) + 1):
                keep *= 1.0 - self.hazard(cid, t)
            cache[key] = keep
        return cache[key]

    def median_turn(self, cid: int) -> float | None:
        s = self._stats(cid)
        plays = [t for t in range(1, TURNS + 1) for _ in range(s.played[t])]
        if not plays:
            return None
        plays.sort()
        mid = len(plays) // 2
        return plays[mid] if len(plays) % 2 else (plays[mid - 1] + plays[mid]) / 2

    def keep(self, hand, deck_cards, rules=None) -> tuple:
        """Indices of `hand` to redraw. `deck_cards`: the 40 cards (to know what a
        redraw would bring)."""
        counts: dict = {}
        for c in deck_cards:
            counts[c.defn.card_id] = counts.get(c.defn.card_id, 0) + 1
        total = sum(counts.values())
        baseline = sum(n * self.early(cid) for cid, n in counts.items()) / max(total, 1)
        redraw, seen = [], {}
        for i, c in enumerate(hand):
            cid = c.defn.card_id
            copy = min(seen.get(cid, 0), 1)
            seen[cid] = seen.get(cid, 0) + 1
            if self.keep_chance(cid, copy, baseline, rules) < 0.5:
                redraw.append(i)
        return tuple(redraw)

    def keep_chance(self, cid: int, copy: int, baseline: float, rules=None) -> float:
        """How likely the player keeps this copy: the prior (their words, else timing),
        moved by their recorded keeps and redraws."""
        prior = None
        if rules is not None:
            if cid in rules.redraw:
                prior = 0.1
            elif cid in rules.at_most and copy >= rules.at_most[cid]:
                prior = 0.1
            elif cid in rules.keep:
                prior = 0.9
        if prior is None:
            prior = 0.75 if self.early(cid) > baseline else 0.25
            if copy:
                prior = min(prior, 0.5)
        s = self._stats(cid)
        kept, redrawn = s.kept[copy], s.redrawn[copy]
        return (kept + PRIOR * prior) / (kept + redrawn + PRIOR)

    # --- storage ------------------------------------------------------------------------

    def to_json(self) -> dict:
        return {"deck": self.deck, "opponent": self.opponent, "games": self.games,
                "cards": {str(cid): vars(s) for cid, s in sorted(self.cards.items())}}

    @classmethod
    def from_json(cls, d: dict) -> "Timing":
        return cls(d["deck"], d["opponent"], d["games"],
                   {int(cid): CardStats(**s) for cid, s in d["cards"].items()})

    def save(self, folder: Path = FOLDER) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{self.deck}-{self.opponent}.json"
        path.write_text(json.dumps(self.to_json(), ensure_ascii=False, indent=1), encoding="utf-8")
        return path


_LOADED: dict = {}


def load(deck: str, opponent: str, folder: Path = FOLDER) -> Timing | None:
    key = (deck, opponent, str(folder))
    if key not in _LOADED:
        path = folder / f"{deck}-{opponent}.json"
        _LOADED[key] = Timing.from_json(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else None
    return _LOADED[key]


def collect(records: list, deck: str, opponent: str, player: int = 0) -> Timing:
    """Count the player's card timing in the records where they used `deck` against `opponent`."""
    from svsim.tools import records as R
    from svsim.ui.session import DECKS, deck_names
    names = {DECKS[k][0]: k for k in DECKS}
    out = Timing(deck, opponent)
    for record in records:
        sides = [names.get(n) for n in deck_names(record)]
        if sides[player] != deck or sides[1 - player] != opponent:
            continue
        out.games += 1
        turn, seen = None, set()
        for state, action in R.steps(record):
            if state.active != player:
                continue
            p = state.players[player]
            if state.phase == Phase.MULLIGAN and isinstance(action, Mulligan):
                copies: dict = {}
                for i, c in enumerate(p.hand):
                    cid = c.defn.card_id
                    k = min(copies.get(cid, 0), 1)
                    copies[cid] = copies.get(cid, 0) + 1
                    s = out.cards.setdefault(cid, CardStats())
                    (s.redrawn if i in action.indices else s.kept)[k] += 1
                continue
            if state.phase != Phase.MAIN:
                continue
            t = min(p.turns_taken, TURNS)
            if state.turn != turn:
                turn, seen = state.turn, set()
            for c in p.hand:
                if c.uid not in seen:
                    seen.add(c.uid)
                    out.cards.setdefault(c.defn.card_id, CardStats()).in_hand[t] += 1
            if isinstance(action, PlayCard):
                c = state.in_hand(player, action.uid)
                out.cards.setdefault(c.defn.card_id, CardStats()).played[t] += 1
    return out


def by_crafts(folder: Path = FOLDER) -> dict:
    """The saved profiles by (deck craft, opponent deck craft)."""
    from svsim.cards import decks
    from svsim.ui.session import DECKS
    out = {}
    for path in folder.glob("*.json"):
        t = Timing.from_json(json.loads(path.read_text(encoding="utf-8")))
        if t.deck in DECKS and t.opponent in DECKS:
            out[(decks.craft_of(decks.build(DECKS[t.deck][1])),
                 decks.craft_of(decks.build(DECKS[t.opponent][1])))] = t
    return out


class Timed:
    """An evaluation plus what holding a card is worth before the player would
    play it: for each card in hand, `weight` times the chance the player would
    still be holding it at this turn (Timing.hold), for each side whose deck and
    matchup have a profile, mine minus the opponent's. Playing Bayle on turn 4
    gives that up (the player plays it around turn 8); playing Sprouting
    Initiate on turn 3 hardly does."""

    def __init__(self, base=None, weight: float = 1.0, profiles: dict | None = None):
        from svsim.search.evaluate import DEFAULT
        self.base = base if base is not None else DEFAULT
        self.weight = weight
        self.profiles = profiles if profiles is not None else by_crafts()

    def hold(self, state, side: int) -> float:
        from svsim.learn.model import deck_craft
        profile = self.profiles.get((deck_craft(state, side), deck_craft(state, 1 - side)))
        if profile is None:
            return 0.0
        p = state.players[side]
        return sum(profile.hold(c.defn.card_id, max(1, p.turns_taken)) for c in p.hand)

    def score(self, state, player: int, player_moves_next: bool = False) -> float:
        from svsim.search.evaluate import evaluate
        value = evaluate(state, player, self.base, player_moves_next)
        if state.winner is not None or not self.weight:
            return value
        return value + self.weight * (self.hold(state, player) - self.hold(state, 1 - player))
