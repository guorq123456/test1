"""The compute cap checked on the pool's own games (A52, LD-57): the host's per-period spot check.

    python -m ladder.compute_audit POOL --period P [--per-member 30] [--workers 15] [--mask 0x3FC3FC] [--out F]

The receipt measures a submission on smoke games (submit, LD-56). A strategy could try to tell those from the pool's
games and spend less there (LD-57 lists the tells closed and the ones left). This looks at the real thing: for each
players' member version, up to `per_member` of its games of period P (a fixed draw: the period and the member, no
choice of the host's), replayed move for move with the default strategy asked and timed at every decision of that
member's seat (submit._shadow: only host code runs, the member's code never), and the same for baseline-against-
baseline games of the same period, in the same batch: those two are the very same computation, so their ratio is
what a step cost in the pool's games against in this batch's replays (cores, load, time of day). A member's ratio is
(its CPU per decision / the default's on the same positions) over that. A 90% interval from resampling its games.

Nothing is decided here: a member clearly over 1.15, the refusal line (S15; the interval above it), is written in the report for the host to
look into and take to Salem. The report names members (host and Salem only; never to players). Replays only: no new
games, no seeds.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))

from ladder.submit import COMPUTE_REFUSE, DEFAULT, _shadow, shadow_task  # noqa: E402,F401

OK = ("normal", "draw")


def _jsonl(p: Path) -> list:
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:                       # a line cut short by a stop: the audit skips it too
            continue
    return out


def plan(games: list, members: dict, period: int, per_member: int = 30, calib: int = 60) -> tuple[list, list]:
    """(member items, calibration items): (key, log, seat) to replay. key = (mid, version) for a players' member's
    seat; ("baseline", None) for a baseline-against-baseline game (both seats counted)."""
    base = {mid for mid, m in members.items() if m.owner == "baseline" and m.strategy == DEFAULT}
    by, cal = {}, []
    for g in games:
        lab = g.get("labels") or {}
        if lab.get("period") != period or g.get("result") not in OK or not g.get("steps"):
            continue
        mids = lab.get("members") or []
        if len(mids) != 2:
            continue
        if all(x in base for x in mids):
            cal.append((("baseline", None), g, None))
            continue
        for seat, mid in enumerate(mids):
            m = members.get(mid)
            if m is None or m.owner in ("baseline", "salem"):
                continue
            by.setdefault((mid, (lab.get("versions") or [None, None])[seat]), []).append((g, seat))
    items = []
    for key in sorted(by, key=str):
        rng = random.Random(f"compute-audit:{period}:{key[0]}:{key[1]}")
        xs = by[key]
        for g, seat in (rng.sample(xs, per_member) if len(xs) > per_member else xs):
            items.append((key, g, seat))
    rng = random.Random(f"compute-audit:{period}:baseline")
    cal = rng.sample(cal, calib) if len(cal) > calib else cal
    return items, cal


def rows_of(items, got) -> tuple[dict, list]:
    """{key: [(game CPU, shadow CPU)]} over the decisions counted (the member's seat; both seats for calibration)."""
    out, bad = {}, []
    for (key, g, seat), r in zip(items, got):
        r = r or {}
        if "value" not in r or r.get("changed") or r.get("blocked"):
            bad.append(f"{g['id']}: {str({k: v for k, v in r.items() if k != 'value'})[:200]}")
            continue
        game = [c for s, c, _ in g["steps"] if seat is None or s == seat]
        sh = [c for s, c in r["value"]["steps"] if seat is None or s == seat]
        if len(game) != len(sh) or not game:
            bad.append(f"{g['id']}: decisions {len(game)} / {len(sh)}")
            continue
        out.setdefault(key, []).append((sum(game), sum(sh)))
    return out, bad


def ratio(rows, factor) -> float | None:
    a, b = sum(r[0] for r in rows), sum(r[1] for r in rows)
    return (a / b) / factor if a and b and factor else None


def interval(rows, cal, draws: int = 4000, seed: int = 7) -> tuple:
    """90% interval of the calibrated ratio, resampling the member's games and the calibration games."""
    rng = random.Random(seed)
    xs = []
    for _ in range(draws):
        r = [rows[rng.randrange(len(rows))] for _ in rows]
        c = [cal[rng.randrange(len(cal))] for _ in cal]
        f = sum(x[0] for x in c) / sum(x[1] for x in c)
        v = ratio(r, f)
        if v is not None:
            xs.append(v)
    xs.sort()
    return (round(xs[int(0.05 * len(xs))], 3), round(xs[int(0.95 * len(xs)) - 1], 3)) if xs else (None, None)


def audit(pool_dir, period: int, per_member: int = 30, calib: int = 60, workers: int = 4, mask=None,
          step_limit: float = 30.0) -> dict:
    from ladder.pool import Pool
    from ladder.runner import guarded_map
    pool = Pool(pool_dir)
    items, cal = plan(_jsonl(pool.games_path), pool.members, period, per_member, calib)
    every = []                                           # members and calibration interleaved: the same conditions
    for i in range(max(len(items), len(cal))):
        if i < len(items):
            every.append(items[i])
        if i < len(cal):
            every.append(cal[i])
    tasks = [shadow_task(g, 0 if seat is None else seat) for _, g, seat in every]
    got = guarded_map("ladder.submit:_shadow", tasks, workers=max(1, min(workers, len(tasks))),
                      step_limit=step_limit, mask=mask) if tasks else []
    rows, bad = rows_of(every, got)
    c = rows.pop(("baseline", None), [])
    out = {"period": period, "per_member": per_member, "replayed": len(tasks), "problems": bad[:20],
           "calibration": {"games": len(c)}, "members": []}
    if len(c) < 10:
        out["calibration"]["note"] = "fewer than 10 baseline-against-baseline games: no ratios"
        return out
    factor = sum(r[0] for r in c) / sum(r[1] for r in c)
    out["calibration"]["game_over_replay"] = round(factor, 4)
    for (mid, version), rs in sorted(rows.items(), key=lambda kv: str(kv[0])):
        m = pool.members[mid]
        r = ratio(rs, factor)
        lo, hi = interval(rs, c)
        out["members"].append({"member": mid, "anon": m.anon, "owner": m.owner, "craft": m.craft,
                               "version": version, "games": len(rs), "ratio": None if r is None else round(r, 3),
                               "interval90": [lo, hi], "over": lo is not None and lo > COMPUTE_REFUSE})
    return out


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    a = argparse.ArgumentParser()
    a.add_argument("pool", type=Path)
    a.add_argument("--period", type=int, required=True)
    a.add_argument("--per-member", type=int, default=30)
    a.add_argument("--calibration", type=int, default=60)
    a.add_argument("--workers", type=int, default=4)
    a.add_argument("--mask", type=lambda x: int(x, 0), default=None)
    a.add_argument("--out", type=Path)
    args = a.parse_args()
    out = audit(args.pool, args.period, args.per_member, args.calibration, args.workers, args.mask)
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 1 if any(m["over"] for m in out["members"]) else 0


if __name__ == "__main__":
    sys.exit(main())
