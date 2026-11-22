"""Every game of a period replayed move by move, before it advances (LD-40, RUNBOOK 每期 §4).

    python -m ladder.audit LOG [LOG ...] [--events POOLDIR/events.jsonl] [--workers 23] [--out audit.json]
        [--allow-empty PATTERN ...]

A LOG may be a pattern (cmd.exe doesn't expand them): "C:\\claude\\ladder-host\\gates\\*\\games.jsonl". A pattern that
matches nothing is an error, so a typo can't pass as "nothing to check"; a pattern given with --allow-empty may match
nothing (the gates' logs before the first gate of the pool: LD-41).

Strategy code shares a worker process with the simulator, so it could change something a game depends on and put
it back before the game ends: ladder/watch.py only sees changes that outlast a game. This replays each logged game
in clean processes from its own seed, decks and deal, applying the logged moves (replay.replay_moves): every move
must be legal when it comes and the game must end the same way. No strategy code runs here, only the log's moves.
Games that didn't reach an end by the rules (timeout, void) are skipped, as replay_moves does.

A failure means the game was played on a simulator that wasn't the one in the repository at that moment (or the log
was changed afterwards): it is listed, with why, for Salem (red line: 发现了就记录并报告), and nothing is changed
here. A line that isn't JSON (the half-written last line of a power cut: the runner starts its next line on a fresh
one, LD-41) is skipped and listed under "unreadable". "voids" counts the void games of each strategy, and of those
the ones it was losing when the tripwire voided them (a side that voids its own losses: report it). With --events
(the pool's events.jsonl), "unlogged" lists the games the pool counted (a "game" event) that have no readable line in
the logs: after a power cut the event can reach the disk and the game's line not, and the pool never plays a game id
again, so such a game moved CR without a replay (LD-43: report it). Exit code 1 if any game fails, 2 if a log is
missing or can't be read at all.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def _init():
    for p in (str(HERE.parent), str(ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import svsim.cards.library  # noqa: F401


def _one(item):
    where, g = item
    from ladder.replay import replay_moves
    try:
        ok, why = replay_moves(g)
    except Exception as e:                            # noqa: BLE001 a log the engine can't even start from
        ok, why = False, f"replay raised {type(e).__name__}: {str(e)[:300]}"
    return where, g.get("id"), ok, why


def read(path: Path, unreadable: list | None = None) -> list[dict]:
    """The games of a log. A line that isn't a JSON object is skipped and noted in `unreadable` as "path:line"."""
    out = []
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"{path}: can't be read ({e})", file=sys.stderr)
        sys.exit(2)
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip(" \t\r\n\x00")
        if not line:
            if raw.strip(" \t\r\n") and unreadable is not None:
                unreadable.append(f"{path}:{n}")       # only NULs: what a power cut can leave (LD-42)
            continue
        try:
            g = json.loads(line)
        except ValueError:
            g = None
        if isinstance(g, dict):
            out.append(g)
        elif unreadable is not None:
            unreadable.append(f"{path}:{n}")
    return out


def expand(args, allow_empty=()) -> list[Path]:
    import glob
    out = []
    for a in list(args) + list(allow_empty):
        if any(ch in str(a) for ch in "*?["):
            hits = sorted(glob.glob(str(a), recursive=True))
            if not hits and a not in allow_empty:
                print(f"nothing matches {a}", file=sys.stderr)
                sys.exit(2)
            out += [Path(h) for h in hits]
        elif a in allow_empty and not Path(a).exists():
            continue
        elif not Path(a).is_file():
            print(f"no such log: {a}", file=sys.stderr)
            sys.exit(2)
        else:
            out.append(Path(a))
    seen, unique = set(), []
    for p in out:                                       # a log named twice is read once (LD-42)
        k = str(p.resolve()).lower() if sys.platform == "win32" else str(p.resolve())
        if k not in seen:
            seen.add(k)
            unique.append(p)
    return unique


def counted(events) -> list[str]:
    """The ids of the games a pool counted: its "game" events, in order."""
    out = []
    for path in events:
        for e in read(Path(path)):
            if e.get("ev") == "game" and isinstance(e.get("id"), str):
                out.append(e["id"])
    return out


def audit(logs, workers: int = 4, mask=None, events=()) -> dict:
    from ladder.runner import MAX_WORKERS, _limit
    if workers > MAX_WORKERS:
        raise SystemExit(f"at most {MAX_WORKERS} workers")
    items, skipped, unreadable, voids, ids = [], 0, [], {}, set()
    for path in logs:
        for g in read(Path(path), unreadable):
            ids.add(g.get("id"))
            if g.get("result") == "void":               # who voids games, and how often while losing (LD-41)
                for seat, spec in enumerate(g.get("strategies") or []):
                    v = voids.setdefault(str(spec), {"void": 0, "was_losing": 0})
                    v["void"] += 1
                    v["was_losing"] += g.get("voided_winner") == 1 - seat
            if g.get("result") in ("timeout", "void") or "actions" not in g:
                skipped += 1
            else:
                items.append((str(path), g))
    failed = []
    if items:
        _limit(mask)
        with ProcessPoolExecutor(max_workers=min(workers, len(items)), initializer=_init,
                                 mp_context=mp.get_context("spawn")) as ex:   # as on Windows
            for where, gid, ok, why in ex.map(_one, items, chunksize=16):
                if not ok:
                    failed.append({"log": where, "id": gid, "why": why})
    unlogged = [gid for gid in counted(events) if gid not in ids]
    return {"logs": [str(p) for p in logs], "checked": len(items), "skipped": skipped, "failed": failed,
            "unreadable": unreadable, "voids": voids, "unlogged": unlogged, "ok": not failed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--mask", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--events", action="append", default=[], metavar="EVENTS",
                    help="the pool's events.jsonl: games it counted that have no line in the logs are listed")
    ap.add_argument("--allow-empty", nargs="+", default=[], metavar="PATTERN",
                    help="logs or patterns that may match nothing yet (the gates' before the pool's first gate)")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    for e in a.events:
        if not Path(e).is_file():
            print(f"no such events file: {e}", file=sys.stderr)
            sys.exit(2)
    res = audit(expand(a.logs, a.allow_empty), a.workers, int(a.mask, 16) if a.mask else None, a.events)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("checked", "skipped", "ok")} | {"failed": len(res["failed"]),
                                                                          "unreadable": len(res["unreadable"]),
                                                                          "unlogged": len(res["unlogged"])},
                     ensure_ascii=False))
    for spec, v in sorted(res["voids"].items(), key=lambda kv: -kv[1]["void"])[:10]:
        print(f"void {v['void']} (losing when voided {v['was_losing']}): {spec}")
    for u in res["unreadable"][:20]:
        print(f"{u}: not a JSON line, skipped (a half-written line from a power cut? check it)")
    for gid in res["unlogged"][:20]:
        print(f"{gid}: counted by the pool but no line in the logs (a power cut?): not replayed, report it")
    for f in res["failed"][:50]:
        print(f"{f['log']} {f['id']}: {f['why']}")
    sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
