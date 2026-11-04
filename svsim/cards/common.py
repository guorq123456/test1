"""Helpers shared by the card modules (target specs, durations, earth sigils)."""
from svsim.cards.pool import card
from svsim.core import effects as E
from svsim.core.script import Ctx, Target, TargetSpec
from svsim.core.state import leader_uid

MAGIC_SEDIMENT = card(90031210)

# Common target specs, for play_targets / evolve_targets / engage_targets.
ENEMY_FOLLOWER = (TargetSpec(Target.ENEMY_FOLLOWER),)
ALLIED_FOLLOWER = (TargetSpec(Target.ALLIED_FOLLOWER),)
OTHER_ALLIED_FOLLOWER = (TargetSpec(Target.ALLIED_FOLLOWER, other=True),)
ANY_FOLLOWER = (TargetSpec(Target.ANY_FOLLOWER),)
ENEMY_FOLLOWER_OR_LEADER = (TargetSpec(Target.ENEMY_FOLLOWER_OR_LEADER),)
HAND_CARD = (TargetSpec(Target.HAND_CARD),)


def enemy_leader(ctx: Ctx) -> int:
    return leader_uid(1 - ctx.controller)


def own_leader(ctx: Ctx) -> int:
    return leader_uid(ctx.controller)


def end_of_turn(ctx: Ctx) -> int:
    """`until_turn` for "until the end of the turn"."""
    return ctx.state.turn


def end_of_opponents_turn(ctx: Ctx) -> int:
    """`until_turn` for "until the end of your opponent's turn" (the controller's opponent)."""
    return ctx.state.turn + 1 if ctx.state.active == ctx.controller else ctx.state.turn


def gain_earth_sigils(ctx: Ctx, n: int) -> None:
    E.gain_earth_sigils(ctx.state, ctx.controller, n, MAGIC_SEDIMENT)


def during_your_turn(ctx: Ctx) -> bool:
    return ctx.state.active == ctx.controller
