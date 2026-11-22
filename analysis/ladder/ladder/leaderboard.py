"""The leaderboard (phase 1, item 1.6; task spec §4.4).

    python -m ladder.leaderboard POOLDIR [--public] [--out FILE]

For each member: its last 2000 decided games, not reaching back past its last change (entry or strategy update).
The value is the mean of its CR over those games minus the mean of mu at the same moments (A20: mu right after
each of its games). Fewer than 2000 games: "unstable", not ranked.

The interval: consecutive CRs of one member are strongly correlated (a CR moves 8-24 per game around where it
belongs; on made-up pools the integrated autocorrelation time is about 60 games), so the games are not independent
samples. The standard error is sd * sqrt(tau / n), tau the integrated autocorrelation time of the member's relative
CR over the window (Geyer's initial positive sequence), with Student's t on n / tau - 1 degrees of freedom. Batch
means (10 batches) are reported beside it as a cross-check: on made-up pools they came out about 13% too narrow
(batches of 200 games are only ~3 tau long; LEDGER LD-12), tau about 5%. Whether the interval is right on real
games is what the phase-1 fluctuation check measures (GATES.md).

Rank intervals, within each class among the ranked members (plan 阶段 1): best = 1 + the number of members whose
whole interval is above this one's, worst = the number in the class - the number whose whole interval is below.
Overlapping intervals are ties, and ties don't chain.

`--public` gives what players may see (plan 公开与私有; A21): anonymous id, class, relative CR, interval and rank
interval only; no game counts, no unstable mark, no owner, age or version. So that it doesn't show which members are
new or were just updated, the public board ranks every member with at least 2000 games since entry, over its last
2000 games whatever changed in them; the board Salem and the host read is the private one, exactly as §4.4.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from ladder import pool as P  # noqa: E402

WINDOW_GAMES = 2000
PUBLIC_MIN_GAMES = 100             # Salem S7 (11-22): the public board lists a member once it has 100 games
SHORT_TAU_FLOOR = 150              # A38: under 2000 games the public interval uses tau >= 150 games and z = 1.96
BATCHES = 10
LINE = 250                         # §4.4 the line: relative CR >= +250
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 14: 2.145, 19: 2.093, 24: 2.064, 29: 2.045, 39: 2.023, 49: 2.010}


def t975(df: int) -> float:
    if df in T975:
        return T975[df]
    keys = sorted(T975)
    if df > keys[-1]:
        return 1.96 + 2.4 / df                      # close enough past 50 degrees of freedom
    lo = max(k for k in keys if k < df)
    hi = min(k for k in keys if k > df)
    return T975[lo] + (T975[hi] - T975[lo]) * (df - lo) / (hi - lo)


def batch_means(xs: list[float], batches: int = BATCHES) -> tuple[float, float, int]:
    """Mean, standard error from `batches` consecutive batch means, degrees of freedom."""
    n = len(xs)
    if n < 2 * batches:
        return (sum(xs) / n if n else float("nan")), float("nan"), 0
    size = n // batches
    xs = xs[n - size * batches:]                   # drop the oldest few so the batches are equal
    means = [sum(xs[i * size:(i + 1) * size]) / size for i in range(batches)]
    m = sum(means) / batches
    var = sum((x - m) ** 2 for x in means) / (batches - 1)
    return m, math.sqrt(var / batches), batches - 1


def autocorr_time(xs: list[float]) -> float:
    """Integrated autocorrelation time, Geyer's initial positive sequence (a cross-check on the batch means)."""
    n = len(xs)
    if n < 20:
        return float("nan")
    m = sum(xs) / n
    d = [x - m for x in xs]
    c0 = sum(v * v for v in d) / n
    if c0 == 0:
        return 1.0
    def rho(k):
        return sum(d[i] * d[i + k] for i in range(n - k)) / n / c0
    tau, k = 1.0, 1
    while k + 1 < n // 2:
        pair = rho(k) + rho(k + 1)
        if pair <= 0:
            break
        tau += 2 * pair
        k += 2
    return tau


class Series:
    """Per member, (cr, mu) after each of its decided games, and where its last change was."""
    def __init__(self):
        self.points: dict[str, list] = {}
        self.change_at: dict[str, int] = {}          # index into points where the current version starts

    def __call__(self, pool, ev):
        if ev["ev"] == "enter":
            mid = ev["member"]["mid"]
            self.points[mid], self.change_at[mid] = [], 0
        elif ev["ev"] == "update":
            self.change_at[ev["member"]] = len(self.points[ev["member"]])
        elif ev["ev"] == "game" and ev["decided"]:
            mu = pool.mu
            for mid in ev["members"]:
                if pool.members[mid].active:
                    self.points[mid].append((pool.members[mid].cr, mu))


def load(pool_dir) -> tuple[P.Pool, Series]:
    s = Series()
    return P.Pool(pool_dir, on_event=s), s


def tau_se(xs: list[float]) -> tuple[float, float, float, int]:
    """Mean, standard error sd * sqrt(tau / n), tau, degrees of freedom n / tau - 1."""
    n = len(xs)
    if n < 20:
        return (sum(xs) / n if n else float("nan")), float("nan"), float("nan"), 0
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1)
    tau = max(1.0, autocorr_time(xs))
    return mean, math.sqrt(var * tau / n), tau, max(1, int(n / tau) - 1)


def estimate(points: list, window: int = WINDOW_GAMES) -> dict:
    pts = points[-window:]
    rel = [c - m for c, m in pts]
    mean, se, tau, df = tau_se(rel)
    half = t975(df) * se if df else float("nan")
    _, se_batch, _ = batch_means(rel)
    return {"n": len(pts), "rel_cr": mean, "se": se, "lo": mean - half, "hi": mean + half, "tau": tau,
            "se_batch": se_batch,
            "mean_cr": sum(c for c, _ in pts) / len(pts) if pts else float("nan"),
            "mean_mu": sum(m for _, m in pts) / len(pts) if pts else float("nan")}


def rank_intervals(rows: list[dict]) -> None:
    """Fills best/worst rank within each class, among the rows marked ranked."""
    by_craft = {}
    for r in rows:
        if r["ranked"]:
            by_craft.setdefault(r["craft"], []).append(r)
    for rs in by_craft.values():
        n = len(rs)
        for r in rs:
            above = sum(1 for o in rs if o is not r and o["lo"] > r["hi"])
            below = sum(1 for o in rs if o is not r and o["hi"] < r["lo"])
            r["best"], r["worst"] = 1 + above, n - below


def board(pool: P.Pool, series: Series, window: int = WINDOW_GAMES) -> list[dict]:
    """The private board (§4.4 as written)."""
    rows = []
    for m in pool.active():
        pts = series.points[m.mid][series.change_at[m.mid]:]
        e = estimate(pts, window) if pts else {k: float("nan") for k in ("rel_cr", "se", "lo", "hi", "tau",
                                                                         "se_batch")} | {"n": 0}
        ranked = e["n"] >= window
        rows.append({"mid": m.mid, "anon": m.anon, "craft": P.CRAFT_ZH[m.craft], "owner": m.owner,
                     "version": m.version, "games": m.games, "ranked": ranked, "unstable": not ranked,
                     "over_line": ranked and e["rel_cr"] >= LINE, "surely_over_line": ranked and e["lo"] >= LINE,
                     **{k: e[k] for k in ("n", "rel_cr", "se", "lo", "hi", "tau", "se_batch")}})
    rank_intervals(rows)
    return sorted(rows, key=lambda r: (r["craft"], -(r["rel_cr"] if r["ranked"] else -1e9)))


def short_interval(points: list, e: dict) -> dict:
    """A38: fewer than 2000 games. The autocorrelation time estimated from a short series runs low (made-up games:
    a 95% interval covered 63-83% at 100-400 games), so use tau >= SHORT_TAU_FLOOR and the normal 1.96 (covered
    96-99% on made-up games; the baselines' tau in real games was 54-271, median 157)."""
    rel = [c - m for c, m in points]
    n = len(rel)
    mean = sum(rel) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in rel) / (n - 1))
    tau = max(SHORT_TAU_FLOOR, e["tau"] if e["tau"] == e["tau"] else 0.0)
    se = sd * math.sqrt(tau / n)
    return e | {"se": se, "lo": mean - 1.96 * se, "hi": mean + 1.96 * se, "tau": tau}


def public_board(pool: P.Pool, series: Series, window: int = WINDOW_GAMES) -> list[dict]:
    """A21 with Salem's S7: every member with at least 100 games since entry, over its last 2000 (whatever version
    played them); under 2000 games the interval is A38's."""
    rows = []
    for m in pool.active():
        pts = series.points[m.mid]
        if len(pts) < PUBLIC_MIN_GAMES:
            continue
        e = estimate(pts, window)
        if e["n"] < window:
            e = short_interval(pts[-window:], e)
        rows.append({"anon": m.anon, "craft": P.CRAFT_ZH[m.craft], "baseline": m.owner == "baseline",
                     "ranked": True, **{k: round(e[k], 1) for k in ("rel_cr", "lo", "hi")}})
    rank_intervals(rows)
    for r in rows:
        r.pop("ranked")
    return sorted(rows, key=lambda r: (r["craft"], -r["rel_cr"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pool")
    ap.add_argument("--public", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    pool, s = load(a.pool)
    rows = public_board(pool, s) if a.public else board(pool, s)
    text = json.dumps({"period": pool.period, "mu": round(pool.mu, 2), "rows": rows}, ensure_ascii=False,
                      indent=1, default=lambda x: None)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
