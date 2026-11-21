"""The numeric rules of the task spec, in one place: CR settlement (§3), matching window and weights, removal (§4.2).

Every number here is one of Salem's parameters (the spec's summary table). Do not change them without his say-so;
a change is a change to locked infrastructure once phase 1 is accepted.

CR (§3): d = my CR - the opponent's, k = floor(|d| / 25).
    0 <= d <= 175: win +(16 - k), loss -(16 + k)
    -175 <= d < 0: win +(16 + k), loss -(16 - k)
    d > 175: win +8, loss -24;  d < -175: win +24, loss -8
    zero-sum; CR always an integer (every step above is an integer).
Steady win rate in bin k: (16 + k) / 32; past 175: 75%. On average 1 point of win rate is 8 CR, in steps.
(Phase 0, LD-06: with the per-game noise the mean gap of two members runs about 9 CR per point; report the 8 and
note the 9.)
"""
from __future__ import annotations

# Salem's parameters (task spec, summary table). Keys mirror the table.
ENTRY_CR = 1500            # §4.1 every new member enters at 1500, whatever mu is
WINDOW = 200               # §3 / §4.2 matched only within 200
CAP = 175                  # §3 past 175: +8 / -24
STEP = 25                  # §3 every full 25 of |d| moves the change by 1
BASE = 16                  # §3
FAR_WIN, FAR_LOSS = 8, 24  # §3 the higher side past CAP
WEIGHT_FLOOR = 0.2         # §4.2 matching weight at mu - 300
DOWNWEIGHT_FROM = 200      # §4.2 weight falls below mu - 200 ...
REMOVE_AT = 300            # §4.2 ... to WEIGHT_FLOOR at mu - 300; CR <= mu - 300 is removed (outside protection)


def step_k(d: int) -> int:
    """k = floor(|d| / 25)."""
    return abs(int(d)) // STEP


def delta(mine: int, theirs: int, won: bool) -> int:
    """The points one decided game moves my CR (§3). Any gap is allowed: §4.2's nearest-member fallback can match
    beyond 200, and past 175 the change is the fixed +8 / -24 (or +24 / -8)."""
    if not (isinstance(mine, int) and isinstance(theirs, int)):
        raise TypeError("CR is always an integer")
    d = mine - theirs
    if d > CAP:
        return FAR_WIN if won else -FAR_LOSS
    if d < -CAP:
        return FAR_LOSS if won else -FAR_WIN
    k = step_k(d)
    if d >= 0:
        return BASE - k if won else -(BASE + k)
    return BASE + k if won else -(BASE - k)


def settle(cr_a: int, cr_b: int, a_won: bool) -> tuple[int, int]:
    """Both CRs after a decided game between a and b (zero-sum). Draws are not settled here (assumption A3)."""
    da = delta(cr_a, cr_b, a_won)
    db = delta(cr_b, cr_a, not a_won)
    if da + db != 0:                                   # cannot happen with the rules above; guard the invariant
        raise AssertionError(f"not zero-sum: {cr_a} vs {cr_b}, {da} + {db}")
    return cr_a + da, cr_b + db


def steady_rate(d: int) -> float:
    """The win rate at which my expected change is zero at gap d (>= 0 side; symmetric below)."""
    if d > CAP:
        return FAR_LOSS / (FAR_WIN + FAR_LOSS)          # 0.75
    if d < -CAP:
        return FAR_WIN / (FAR_WIN + FAR_LOSS)           # 0.25
    k = step_k(d)
    return (BASE + k) / (2 * BASE) if d >= 0 else (BASE - k) / (2 * BASE)


def pp_to_cr(pp: float) -> float:
    """§3's average conversion: 1 point of win rate = 8 CR (32 CR per 4 points; steps of 25 per 3.125 points)."""
    return pp * STEP / (100 / (2 * BASE))            # 25 / 3.125 = 8


def within_window(mine: int, theirs: int) -> bool:
    return abs(mine - theirs) <= WINDOW


def match_weight(cr: float, mu: float) -> float:
    """§4.2: 1 at CR >= mu - 200, falling linearly to 0.2 at mu - 300 (and held there; below that the member is
    removed unless protected, and a protected member keeps weight 1, see `effective_weight`)."""
    gap = mu - cr
    if gap <= DOWNWEIGHT_FROM:
        return 1.0
    if gap >= REMOVE_AT:
        return WEIGHT_FLOOR
    return 1.0 - (1.0 - WEIGHT_FLOOR) * (gap - DOWNWEIGHT_FROM) / (REMOVE_AT - DOWNWEIGHT_FROM)


def effective_weight(cr: float, mu: float, protected: bool) -> float:
    """§4.5: inside the protection period the weight is not lowered."""
    return 1.0 if protected else match_weight(cr, mu)


def to_remove(cr: float, mu: float, protected: bool) -> bool:
    """§4.2: CR <= mu - 300 is removed at once, except inside the protection period."""
    return (not protected) and cr <= mu - REMOVE_AT
