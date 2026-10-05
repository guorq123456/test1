"""Player actions.

Every choice a card needs (targets, modes) is folded into the action that
plays it, so the engine never pauses mid-resolution. Cards are referenced by
uid, which survives GameState.clone(), so an action list can be replayed on a
copy. Leaders use negative uids (state.leader_uid).
"""
from dataclasses import dataclass


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


@dataclass(frozen=True, slots=True)
class UseBonusPP:
    pass


@dataclass(frozen=True, slots=True)
class EndTurn:
    pass


Action = Mulligan | PlayCard | Attack | Evolve | UseBonusPP | EndTurn
