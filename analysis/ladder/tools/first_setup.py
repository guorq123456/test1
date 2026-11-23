"""RUNBOOK 第一次 4-5, once, before the players come in: the official pool and the players' folders.

    python analysis/ladder/tools/first_setup.py [--p1b DIR] [--host DIR] [--players DIR] [--out DIR] [--dry]

1. The locked files are as locked (tools/check_lock.py); the deal key is there (only its id is written).
2. The official pool: the p1b baseline pool (`--p1b`, C:\\claude\\ladder-runs\\p1b\\baseline\\pool) copied whole to
   HOST\\pool (the original is not touched: its files are hashed before and after), then advanced into period 1
   (S8: the baseline nobody can reach does not hold it back; the event logs how short it is). A pool already there
   is never copied over: already past period 0, the step is reported done; still at period 0 and the same as the
   p1b pool, it is advanced; anything else stops the tool.
3. The host's folders (HOST\\subs, gates, frozen, anchors, reports, audit, puzzles).
4. The players' folders (A50): PLAYERS\\<拼音>\\submit and receipts for 甲 乙 丙 丁 戊 (ladder.arena.PINYIN), and
   PLAYERS\\public: every file of analysis/ladder/public copied in (a file of the same name is replaced: the repo is
   the source; other files there, such as the period reports, are left).
Nothing here plays a game or uses a seed. Run again, it changes nothing that is already right. Results in
OUT\\summary.json. `--dry` works under OUT on a copy of the p1b pool's events only, with no key.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
sys.path[:0] = [str(LADDER), str(LADDER.parents[1]), str(HERE)]

HOST_DIRS = ("subs", "gates", "frozen", "anchors", "reports", "audit", "puzzles")


def digest(d: Path) -> dict:
    out = {}
    for p in sorted(d.iterdir()):
        if p.is_file():
            h = hashlib.sha256()
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            out[p.name] = h.hexdigest()
    return out


def pool_step(src: Path, dest: Path) -> dict:
    from ladder.pool import Pool, period_kind
    if not (src / "events.jsonl").exists():
        raise SystemExit(f"no p1b pool at {src}")
    before = digest(src)
    if dest.exists() and any(dest.iterdir()):
        pool = Pool(dest)
        if pool.period >= 1:
            return {"ok": True, "note": f"already there, period {pool.period} ({period_kind(pool.period)})",
                    "period": pool.period}
        if digest(dest) != before:
            raise SystemExit(f"{dest} holds a period-0 pool that is not the p1b pool: look before going on")
        copied = False
    else:
        dest.mkdir(parents=True, exist_ok=True)
        for p in sorted(src.iterdir()):
            if p.is_file():
                shutil.copy2(p, dest / p.name)
        copied = True
        if digest(dest) != before:
            raise SystemExit("the copy differs from the p1b pool")
    pool = Pool(dest)
    if pool.period != 0 or len(pool.active()) != 7 or any(m.owner != "baseline" for m in pool.active()):
        raise SystemExit(f"not the baseline pool: period {pool.period}, {len(pool.active())} members")
    isolated = pool.isolated()
    period = pool.advance()
    pool = Pool(dest)
    if digest(src) != before:
        raise SystemExit("the p1b pool changed while copying: look before going on")
    return {"ok": pool.period == 1, "copied": copied, "period": pool.period, "kind": period_kind(pool.period),
            "isolated_at_advance": isolated, "members": len(pool.active()), "advance_returned": period,
            "p1b_unchanged": True, "files": sorted(before)}


def players_step(players: Path, public_src: Path) -> dict:
    from ladder.arena import PINYIN
    made = []
    for code, py in PINYIN.items():
        for sub in ("submit", "receipts"):
            d = players / py / sub
            if not d.exists():
                d.mkdir(parents=True)
                made.append(str(d))
    pub = players / "public"
    pub.mkdir(parents=True, exist_ok=True)
    copied, same = [], []
    for p in sorted(public_src.iterdir()):
        if not p.is_file():
            continue
        t = pub / p.name
        if t.exists() and t.read_bytes() == p.read_bytes():
            same.append(p.name)
            continue
        shutil.copy2(p, t)
        copied.append(p.name)
    ok = all((players / py / s).is_dir() for py in PINYIN.values() for s in ("submit", "receipts")) and \
        all((pub / p.name).read_bytes() == p.read_bytes() for p in public_src.iterdir() if p.is_file())
    return {"ok": ok, "players": dict(PINYIN), "made": made, "public_copied": copied, "public_same": same}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--p1b", type=Path, default=Path(r"C:\claude\ladder-runs\p1b\baseline\pool"))
    ap.add_argument("--host", type=Path, default=Path(r"C:\claude\ladder-host"))
    ap.add_argument("--players", type=Path, default=Path(r"C:\claude\ladder-players"))
    ap.add_argument("--out", type=Path, default=Path(r"C:\claude\ladder-runs\first-setup"))
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    if a.dry:
        a.host, a.players = a.out / "host", a.out / "players"
    res = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "dry": a.dry, "steps": {}}

    def finish(code: int):
        res["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
        res["ok"] = code == 0 and all(s.get("ok") for s in res["steps"].values()) and len(res["steps"]) == 4
        (a.out / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0 if res["ok"] else 1

    from check_lock import differs, recorded
    bad = differs()
    res["steps"]["lock"] = {"ok": not bad, "files": len(recorded()), "differs": bad}
    if bad:
        return finish(1)
    if a.dry:
        res["steps"]["key"] = {"ok": True, "note": "dry run: no key"}
    else:
        from ladder import deal
        key = deal.resolve("auto")
        res["steps"]["key"] = {"ok": key is not None, "id": deal.key_id(key) if key else None}
        if key is None:
            return finish(1)
    from ladder.pool import PoolError
    try:
        res["steps"]["pool"] = pool_step(a.p1b, a.host / "pool")
    except (SystemExit, PoolError) as e:
        res["steps"]["pool"] = {"ok": False, "error": str(e)}
        return finish(1)
    for d in HOST_DIRS:
        (a.host / d).mkdir(parents=True, exist_ok=True)
    res["steps"]["pool"]["host_dirs"] = list(HOST_DIRS)
    res["steps"]["players"] = players_step(a.players, LADDER / "public")
    return finish(0)


if __name__ == "__main__":
    sys.exit(main())
