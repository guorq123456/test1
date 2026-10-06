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
- the ways to get there, the fastest counts: spend the first j turns
  developing, then deal damage every turn until the leader falls, for every
  j. Developing means playing the cards that raise max play points (ramp,
  told apart by playing them in the engine, not from a card list: Dragonsign,
  Lumiore & Argente's Accelerate) and attacking the leader with the followers
  already out; holding is the same without the ramp. A damage turn either
  finishes (`burst`) or deals the planner's most damage, played in the engine,
  and goes on to the next turn with what is left and what is drawn. So "hold
  everything and burst on turn k", "15 damage now, 5 next turn" and "ramp 3
  into 5 and 5 into 7, then damage turn after turn" (the player's words for
  Ramp Dragon in this matchup) are all counted.

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


def _attack_leader(s: GameState, side: int) -> None:
    """Every allied follower that can hits the enemy leader (nothing if Ward is in the way)."""
    from svsim.core.actions import Attack
    from svsim.core.engine import legal_actions
    from svsim.core.state import leader_uid
    for _ in range(20):
        if s.over:
            return
        attacks = [a for a in legal_actions(s) if isinstance(a, Attack) and a.target == leader_uid(1 - side)]
        if not attacks:
            return
        apply(s, attacks[0])


def develop(s: GameState, side: int, ramp: bool = True) -> None:
    """A turn spent building up (modified in place): play the cards that raise
    max play points, most points per play point paid first, then attack the leader."""
    from svsim.core.actions import PlayCard
    from svsim.core.engine import legal_actions
    for _ in range(10 if ramp else 0):
        if s.over:
            return
        best = None
        for a in legal_actions(s):
            if not isinstance(a, PlayCard):
                continue
            t = s.clone()
            pp, max_pp = t.players[side].pp, t.players[side].max_pp
            apply(t, a)
            gain = t.players[side].max_pp - max_pp
            if gain > 0 and not t.over:
                key = (gain / max(pp - t.players[side].pp, 1), t.players[side].pp)
                if best is None or key > best[0]:
                    best = (key, a)
        if best is None:
            break
        apply(s, best[1])
    if not s.over:
        _attack_leader(s, side)


@dataclass
class Clock:
    turns: int          # side's turns before the killing one (HORIZON + 1: not within the horizon)
    how: str            # "now"; "hold"/"ramp" with the turns developed and the damage turns, e.g. "ramp 2+1"
    damage: list        # the burst found on each turn of the plain holding track


def _chain(s: GameState, side: int, start: int, limit: int, nodes: int) -> int | None:
    """From turn `start` (position `s`, modified): deal damage every turn; the
    turn the leader falls, if before `limit`."""
    for k in range(start, limit):
        if s.over:
            return k if s.winner == side else None
        if burst(s, nodes) >= s.players[1 - side].leader_hp:
            return k
        if k + 1 >= limit:
            return None
        dealt, t = _two_turns(s, side, nodes)
        if t is None:
            return None
        if t.over:
            return k if t.winner == side else None
        s = advance(t, side)
    return None


def clock(state: GameState, side: int, horizon: int = HORIZON, nodes: int = 1000, ramp: bool = True) -> Clock:
    """`side`'s clock if nobody interferes (see the module docstring). If it is
    `side`'s turn, turn 0 is this one as it stands; otherwise its next turn."""
    start = state.clone()
    if not (start.active == side and start.phase == Phase.MAIN):
        advance(start, side)
    best, how, found = horizon + 1, "", []
    tracks = [("hold", start)] + ([("ramp", start.clone())] if ramp else [])
    for j in range(horizon + 1):
        if j >= best:
            break
        for name, s in tracks:
            if name == "ramp" and j == 0:
                continue                         # developing 0 turns: the same as holding
            if s.over:
                if s.winner == side and j < best:
                    best, how = j, "now" if j == 0 else f"{name} {j}+0"
                continue
            if name == "hold":
                found.append(burst(s, nodes))
            k = _chain(s.clone(), side, j, best, nodes)
            if k is not None and k < best:
                best, how = k, "now" if k == 0 else f"{name} {j}+{k - j}"
        if j + 1 >= best:
            break
        for i, (name, s) in enumerate(tracks):
            if not s.over:
                develop(s, side, ramp=name == "ramp")
                tracks[i] = (name, advance(s, side) if not s.over else s)
    return Clock(best, how, found)



_RAMPS: dict = {}


def ramps(defn) -> bool:
    """Whether playing the card in the early game (1 to 7 play points) raises max
    play points, measured in a sandbox (Dragonsign; Zooey; Lumiore & Argente,
    whose Accelerate is what gets played then)."""
    hit = _RAMPS.get(defn.card_id)
    if hit is None:
        hit = _RAMPS[defn.card_id] = _measure_ramp(defn)
    return hit


def _measure_ramp(defn) -> bool:
    from svsim.core import effects as E
    from svsim.core.actions import PlayCard
    from svsim.core.engine import legal_actions
    from svsim.search.combo import _sandbox
    for pp in range(1, 8):
        state, _ = _sandbox(0, pp)
        card = E.add_to_hand(state, 0, defn)
        for a in legal_actions(state):
            if isinstance(a, PlayCard) and a.uid == card.uid:
                t = state.clone()
                apply(t, a)
                if t.players[0].max_pp > pp:
                    return True
    return False
