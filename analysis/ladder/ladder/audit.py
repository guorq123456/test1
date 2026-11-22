"""Every game of a period replayed move by move, before it advances (LD-40, RUNBOOK 每期 §4).

    python -m ladder.audit LOG [LOG ...] [--workers 23] [--out audit.json]

A LOG may be a pattern (cmd.exe doesn't expand them): "C:\\claude\\ladder-host\\gates\\*\\games.jsonl". A pattern that
matches nothing is an error, so a typo can't pass as "nothing to check".

Strategy code shares a worker process with the simulator, so it could change something a game depends on and put
it back before the game ends: ladder/watch.py only sees changes that outlast a game. This replays each logged game
in clean processes from its own seed, decks and deal, applying the logged moves (replay.replay_moves): every move
must be legal when it comes and the game must end the same way. No strategy code runs here, only the log's moves.
Games that didn't reach an end by the rules (timeout, void) are skipped, as replay_moves does.

A failure means the game was played on a simulator that wasn't the one in the repository at that moment (or the log
was changed afterwards): it is listed, with why, for Salem (red line: 发现了就记录并报告), and nothing is changed
here. Exit code 1 if any game fails, 2 if a log can't be read.
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


def read(path: Path) -> list[dict]:
    out = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line = line.strip(" \t\r\n\x00")
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            raise SystemExit(f"{path}:{n}: not a JSON line (a half-written last line from a power cut? check it)")
    return out


def expand(args) -> list[Path]:
    import glob
    out = []
    for a in args:
        if any(ch in str(a) for ch in "*?["):
            hits = sorted(glob.glob(str(a), recursive=True))
            if not hits:
                raise SystemExit(f"nothing matches {a}")
            out += [Path(h) for h in hits]
        elif not Path(a).is_file():
            raise SystemExit(f"no such log: {a}")
        else:
            out.append(Path(a))
    return out


def audit(logs, workers: int = 4, mask=None) -> dict:
    from ladder.runner import MAX_WORKERS, _limit
    if workers > MAX_WORKERS:
        raise SystemExit(f"at most {MAX_WORKERS} workers")
    items, skipped = [], 0
    for path in logs:
        for g in read(Path(path)):
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
    return {"logs": [str(p) for p in logs], "checked": len(items), "skipped": skipped, "failed": failed,
            "ok": not failed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--mask", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    res = audit(expand(a.logs), a.workers, int(a.mask, 16) if a.mask else None)
    if a.out:
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("checked", "skipped", "ok")} | {"failed": len(res["failed"])},
                     ensure_ascii=False))
    for f in res["failed"][:50]:
        print(f"{f['log']} {f['id']}: {f['why']}")
    sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
