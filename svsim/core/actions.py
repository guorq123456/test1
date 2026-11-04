"""Player actions.

Every choice a card needs (targets, modes) is folded into the action that
plays it, so the engine never pauses mid-resolution. Cards are referenced by
uid, which survives GameState.clone(), so an action list can be replayed on a
copy. Leaders use negative uids (state.leader_uid).
"""
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class Mulligan:
    indices: tuple[int, ...]      # hand positions to redraw


@dataclass(frozen=True, slots=True)
class PlayCard:
    uid: int
    targets: tuple[int, ...] = ()
    modes: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class Attack:
    attacker: int
    target: int                   # follower uid, or leader_uid(enemy)


@dataclass(frozen=True, slots=True)
class Evolve:
    uid: int
    super_: bool = False
    targets: tuple[int, ...] = ()
    modes: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class Engage:
    uid: int                      # an allied amulet with an Engage ability
    targets: tuple[int, ...] = ()
    modes: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class Fuse:
    uid: int                      # the card in hand being fused to
    cards: tuple[int, ...] = ()   # the hand cards fused to it


@dataclass(frozen=True, slots=True)
class UseBonusPP:
    pass


@dataclass(frozen=True, slots=True)
class EndTurn:
    pass


Action = Mulligan | PlayCard | Attack | Evolve | Engage | Fuse | UseBonusPP | EndTurn


ACTION_TYPES = {cls.__name__: cls for cls in
                (Mulligan, PlayCard, Attack, Evolve, Engage, Fuse, UseBonusPP, EndTurn)}


def to_dict(action) -> dict:
    """A JSON-friendly form of an action, for saving games and positions."""
    return {"type": type(action).__name__, **asdict(action)}


def from_dict(data: dict):
    fields = {k: (tuple(v) if isinstance(v, list) else v) for k, v in data.items() if k != "type"}
    return ACTION_TYPES[data["type"]](**fields)
