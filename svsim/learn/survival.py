"""How long followers stay on the field against an opponent, learned from games.

The player's premise for the race clock (2026-10-06): a damage deck shouldn't
count on its followers snowballing, assume the opponent answers them all. Not
every follower alike, though: a Fairy (1/1) played on turn 1 or 2 often gets a
hit in, by mid-game it is always gone.

`collect(records, deck, opponent)` counts, for `deck`'s followers facing
`opponent`: at the end of each of the deck's turns, the followers on its field,
by the opponent's own number for the turn that follows and the follower's
defense; and how many of them are still there when the deck's next turn
starts. `Survival.chance(turn, life)` is that fraction, smoothed towards the
same turn over all defenses, and that towards 0: with no games at all,
everything is answered (the player's premise).

Who does the answering matters: when there are games where the opponent was
played by the player, only those count. The AI's Rhinoceroach Forest leaves
Ramp Dragon's big followers alone, the player doesn't: of Ramp's followers with
5 or more defense at the end of its turn, 1 in 24 lived to Ramp's next turn in
the player's ten games, 113 in 237 in 80 games of the AI (the player kills them
with Mylo and Baby Carbuncle attacks, Glade, Arrow, Insect's Counsel).

`Removal` is what the race clock (search.race) assumes on each opponent turn
it skips: a follower stays with its chance of surviving that turn.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from svsim.core.actions import EndTurn
from svsim.core.enums import Phase

TURNS = 10                      # the opponent's own turns counted; later ones go with the 10th
LIVES = 5                       # defense counted 1..5 (5: 5 or more)
PRIOR = 2.0                     # pseudo-followers behind each smoothing step
FOLDER = Path(__file__).with_name("survival")


def _grid() -> list:
    return [[0] * (LIVES + 1) for _ in range(TURNS + 1)]


def own_turn(state, side: int, turn: int) -> int:
    """`side`'s own number for global turn `turn` (1 = the first player's first turn)."""
    return (turn + 1) // 2 if side == state.first else turn // 2


@dataclass
class Survival:
    deck: str
    opponent: str
    games: int = 0
    seen: list = field(default_factory=_grid)      # [opponent's turn][defense] followers on the field
    kept: list = field(default_factory=_grid)      # ... and still there at the deck's next turn
    by_player: bool = False                        # the opponent was played by the player in these games

    def chance(self, turn: int, life: int) -> float:
        """Chance a follower with `life` defense survives the opponent's own turn `turn`."""
        t, l = max(1, min(turn, TURNS)), max(1, min(life, LIVES))
        row = sum(self.kept[t]) / (sum(self.seen[t]) + PRIOR)
        return (self.kept[t][l] + PRIOR * row) / (self.seen[t][l] + PRIOR)

    def to_json(self) -> dict:
        return {"deck": self.deck, "opponent": self.opponent, "games": self.games,
                "seen": self.seen, "kept": self.kept, "by_player": self.by_player}

    @classmethod
    def from_json(cls, d: dict) -> "Survival":
        return cls(d["deck"], d["opponent"], d["games"], d["seen"], d["kept"], d.get("by_player", False))

    def save(self, folder: Path = FOLDER) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{self.deck}-{self.opponent}.json"
        path.write_text(json.dumps(self.to_json()), encoding="utf-8")
        return path


_LOADED: dict = {}


def load(deck: str, opponent: str, folder: Path = FOLDER) -> Survival | None:
    key = (deck, opponent, str(folder))
    if key not in _LOADED:
        path = folder / f"{deck}-{opponent}.json"
        _LOADED[key] = Survival.from_json(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else None
    return _LOADED[key]


def count(steps, side: int, into: Survival) -> None:
    """Add one game's counts for `side`'s followers; `steps`: (state before the
    action, action) for every action of the game (tools.records.steps)."""
    into.games += 1
    pending = None                       # (opponent's turn, {uid: defense}) at the end of side's turn
    for state, action in steps:
        if state.phase != Phase.MAIN:
            continue
        if pending is not None and state.active == side:
            turn, lives = pending
            alive = {c.uid for c in state.players[side].followers}
            t = min(turn, TURNS)
            for uid, life in lives.items():
                l = max(1, min(life, LIVES))
                into.seen[t][l] += 1
                into.kept[t][l] += uid in alive
            pending = None
        if state.active == side and isinstance(action, EndTurn):
            lives = {c.uid: c.life for c in state.players[side].followers}
            if lives:
                pending = (own_turn(state, 1 - side, state.turn + 1), lives)


def human(record: dict, seat: int) -> bool:
    """Whether the player played `seat` (games against the AI: seat 0; games the AI
    played against itself say so under "players")."""
    players = record.get("players")
    return players[seat] == "human" if players else seat == 0


def games(records: list, deck: str, opponent: str) -> tuple[list, bool]:
    """(record, side) for `deck`'s side in every game against `opponent`, only those
    where the player answered (played `opponent`) if there are any; and whether so."""
    from svsim.ui.session import DECKS, deck_names
    names = {DECKS[k][0]: k for k in DECKS}
    pairs = []
    for record in records:
        sides = [names.get(n) for n in deck_names(record)]
        pairs += [(record, side) for side in (0, 1) if sides[side] == deck and sides[1 - side] == opponent]
    answered = [(r, side) for r, side in pairs if human(r, 1 - side)]
    return (answered, True) if answered else (pairs, False)


def collect(records: list, deck: str, opponent: str) -> Survival:
    """Count `deck`'s followers against `opponent` (see `games` for which games)."""
    from svsim.tools import records as R
    pairs, by_player = games(records, deck, opponent)
    out = Survival(deck, opponent, by_player=by_player)
    for record, side in pairs:
        count(R.steps(record), side, out)
    return out


class Removal:
    """What the race clock assumes the opponent answers on a turn it skips: a
    follower stays with its chance of surviving that turn (Survival.chance),
    drawn once per follower, turn and `seed`, so every line compared from the
    same position meets the same answers; with no profile, nothing stays."""

    def __init__(self, profile: Survival | None = None, seed: int = 0):
        self.profile = profile
        self.seed = seed

    def stays(self, follower, turn: int) -> bool:
        import random
        if self.profile is None:
            return False
        draw = random.Random(f"{self.seed}-{follower.uid}-{turn}").random()
        return draw < self.profile.chance(turn, follower.life)

    @classmethod
    def matchup(cls, state, side: int, seed: int = 0, folder: Path = FOLDER) -> "Removal":
        """The profile for `side`'s deck against the other side's (found by craft, as
        learn.timing does), if there is one."""
        from svsim.learn.model import deck_craft
        return cls(by_crafts(folder).get((deck_craft(state, side), deck_craft(state, 1 - side))), seed)


_CRAFTS: dict = {}


def by_crafts(folder: Path = FOLDER) -> dict:
    """The saved profiles by (deck craft, opponent deck craft)."""
    if str(folder) not in _CRAFTS:
        from svsim.cards import decks
        from svsim.ui.session import DECKS
        out = {}
        for path in folder.glob("*.json"):
            s = Survival.from_json(json.loads(path.read_text(encoding="utf-8")))
            if s.deck in DECKS and s.opponent in DECKS:
                out[(decks.craft_of(decks.build(DECKS[s.deck][1])),
                     decks.craft_of(decks.build(DECKS[s.opponent][1])))] = s
        _CRAFTS[str(folder)] = out
    return _CRAFTS[str(folder)]
