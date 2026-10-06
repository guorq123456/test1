"""Race clocks: how many turns each side still needs to kill the other.

The player's point (2026-10-06): in a matchup where the followers barely
interact, such as Rhinoceroach Forest against Ramp Dragon, turns are the
currency. Drawing a card is worth what it does to the turn you can kill on
(it may find damage, or cards that use all the play points); spending a damage
card now is worth it only if it doesn't push that turn back and hand the
opponent more turns. So instead of fixed exchange rates between cards, damage
and board, this module counts turns, position by position.

`clock(state, side)` is the number of `side`'s turns before the one it can kill
on (0: it can kill on its current or next turn), if nobody interferes:

- `side`'s turns are projected with the engine (`advance`): play points grow,
  cards are drawn from the deck as it lies (determinize first, so this doesn't
  peek), countdowns tick, start-of-turn abilities resolve; nothing happens on
  the opponent's turns;
- each turn, `burst` is the most damage `side` could deal: the player's
  formula (search.formula, for finishers whose attack grows with Combo) or the
  resource-flow planner (search.combo), whichever finds more;
- two ways to get there: hold everything and burst on turn k (followers already
  on the field hit the leader on the turns before), or deal the planner's most
  damage on turn k (played in the engine) and finish on turn k+1 with what is
  left and what is drawn (a 15-damage turn and a 5-damage turn).

What it leaves out, so read it as "if unanswered": the opponent's removal,
Ward, healing and the damage they deal in between; cards drawn during the
burst turn (unknown, never played); keeping the hand under the limit by
cycling (the projection burns what doesn't fit, as the rules do). The
opponent's answer is what `search.impact` adds, by playing their turn.
"""
from __future__ import annotations

from dataclasses import dataclass

from svsim.core.actions import EndTurn
from svsim.core.engine import _start_turn, apply
from svsim.core.enums import DRAW, Keyword, Phase
from svsim.core.script import prop
from svsim.core.state import GameState

HORIZON = 5          # turns looked ahead; a clock of HORIZON + 1 means "not within the horizon"


def _end_without_next(s: GameState) -> None:
    """End the current turn (its end-of-turn abilities resolve) without starting the next."""
    real = s.max_turns
    s.max_turns = s.turn
    apply(s, EndTurn())
    if s.winner == DRAW and s.turn <= real:
        s.winner, s.phase = None, Phase.MAIN
    s.max_turns = real


def advance(s: GameState, side: int) -> GameState:
    """Start `side`'s next turn on `s` (modified and returned); if it is `side`'s
    turn now, the opponent's turn in between passes with nothing happening."""
    if s.active == side:
        _end_without_next(s)
        if s.over:
            return s
        s.turn += 1
        s.active = side
    else:
        _end_without_next(s)
        if s.over:
            return s
    _start_turn(s)
    return s


def board_chip(state: GameState, side: int) -> int:
    """What `side`'s followers on the field hit the enemy leader for in a turn
    (each attacks as often as it can), minus enemy Ward defense."""
    p, enemy = state.players[side], state.players[1 - side]
    dmg = sum(f.atk * max(1, f.max_attacks) for f in p.followers if not prop(f, "cant_attack"))
    dmg -= sum(max(f.life, 0) for f in enemy.followers if f.keywords & Keyword.WARD)
    return max(dmg, 0)


def burst(state: GameState, nodes: int = 1000) -> int:
    """The most damage the player to act could deal this turn (formula or planner)."""
    from svsim.search import combo, formula
    hp = state.players[1 - state.active].leader_hp
    best = formula.estimate(state).damage
    if best < hp:
        best = max(best, combo.plan(state, nodes).damage)
    return best


def _two_turns(s: GameState, side: int, nodes: int) -> tuple[int, GameState | None]:
    """Play the planner's most damaging line this turn in the engine: (damage dealt, the position after)."""
    from svsim.search import combo
    plan = combo.plan(s, nodes)
    line = None
    for n in range(len(plan.steps), 0, -1):          # the longest start of the plan the engine accepts
        line = combo.realize(s, plan.steps[:n])
        if line:
            break
    if not line:
        return 0, None
    t = s.clone()
    hp = t.players[1 - side].leader_hp
    for a in line:
        if t.over:
            break
        apply(t, a)
    return hp - t.players[1 - side].leader_hp, t


@dataclass
class Clock:
    turns: int          # side's turns before the killing one (HORIZON + 1: not within the horizon)
    how: str            # "now", "hold" (hold and burst), "two" (damage, then finish), ""
    damage: list        # the burst found on each turn looked at


def clock(state: GameState, side: int, horizon: int = HORIZON, nodes: int = 1000) -> Clock:
    """`side`'s clock if nobody interferes (see the module docstring). If it is
    `side`'s turn, turn 0 is this one as it stands; otherwise its next turn."""
    s = state.clone()
    if not (s.active == side and s.phase == Phase.MAIN):
        advance(s, side)
    chip = 0                       # damage the followers already out deal on the turns held
    found = []
    for k in range(horizon + 1):
        if s.over:
            won = s.winner == side
            return Clock(k if won else horizon + 1, "now" if won else "", found)
        hp = s.players[1 - side].leader_hp
        dmg = burst(s, nodes)
        found.append(dmg)
        if dmg + chip >= hp:
            return Clock(k, "now" if k == 0 else "hold", found)
        if k < horizon:
            dealt, t = _two_turns(s, side, nodes)
            if t is not None and not t.over:
                advance(t, side)
                if not t.over and chip + dealt + burst(t, nodes) >= hp:
                    return Clock(k + 1, "two", found)
            elif t is not None and t.winner == side:
                return Clock(k, "now", found)
            chip += board_chip(s, side)
            advance(s, side)
    return Clock(horizon + 1, "", found)
