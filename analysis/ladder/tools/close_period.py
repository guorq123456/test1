"""Closing a period on Salem's computer in one go (RUNBOOK 每期 §4-§6): after the deadline, once the collection loop
has said 「这一期收完」 and stopped.

    python analysis/ladder/tools/close_period.py [--host DIR] [--arena DIR] [--players DIR] [--out DIR]
                                                 [--workers 23] [--e-workers 15] [--mask 0x3FC3FC]
                                                 [--check] [--advance-anyway REASON --held DIGEST]

Every step can be run again: a step that is done is kept (the ladder plays only what the period still needs, the
hall of fame is inducted once a period, the anchors are played once a period, a puzzle is evaluated once), so after
a stop (a power cut, Ctrl+C, an error fixed in between) the same double-click goes on from where it was.

1. lock: the locked files are as locked (tools/check_lock.py); key: the formal pool's deal key is there (its id only).
2. state: the simulator is P's environment (tools/environments.py, S25); the pool's period P; the arena's window is P's, on the field it was snapshot with, and its deadline is past.
   A pool already in P+1 with the window still P's: P was closed (and advanced) earlier; nothing is done.
3. collected: no collection loop is running (this holds SUBS/collect.lock to the end, so none can start), the loop
   took the listing at the deadline (SUBS/collect.jsonl) and every directory in it was taken, given up or found
   changed after the deadline, and every accepted deck of P is admitted and every accepted update gated (or its
   failure written down). Then the arena's lock is taken and held to the end: a practice run still going finishes
   first, none starts.
4. ladder: `ladder.pool ladder --until-period-done` on all cores with the received strategies on the path
   (LADDER_EXTRA_PATH = HOST/subs/code), again while the last run played games and members are still short (games
   still in flight can bring a member back within 200). Members short and with nobody within 200 don't hold the
   period (S8); a member short and not isolated stops here.
5. hall of fame (S9, A41): `ladder.anchors induct` once for P (HOST/anchors/hof.json), then `ladder.anchors table`
   (HOST/anchors/anchors.json: the baseline snapshot and the hall of fame).
6. anchors (S11, A48): `ladder.anchors run` once for P (HOST/anchors; a run cut off picks up its own games); the
   per-member rows for Salem in HOST/reports/anchors-P<P>.json.
7. puzzles due at the end of P (S21: START at the end of period 1): `ladder.puzzles run` on the E-cores (the pilot
   reference's compute is compared, LD-61), the field "others", the reference 参照 = the Haven pilot as 2.5 measured
   it (svsim.ui.session.pilot_native_spec, S19; the name "参照" goes into the public copy as it is). Seeds: the next
   1200 of the public-puzzle segment 91900000-91999999 after every puzzle plan already in HOST/puzzles, written in
   HOST/puzzles/<id>/plan.json before the first game (a run cut off goes on with the same seeds). The public result
   goes into the next period's report by tools/open_period.py.
8. audit (LD-40): `ladder.audit` replays every game of the pool, of P's anchors, of every gate and every puzzle
   (HOST/audit/P<P>.json); after a change of simulator (S25, A60) only what was written since the seal
   (tools/environments.py), the sealed part checked byte for byte (a change holds the period). A game that doesn't replay, a game the pool counted with no line, or a line that isn't
   JSON holds the period (no formal games, no advance), unless an earlier period's audit (HOST/audit/P<k>.json)
   listed it already (reported and decided then; the audit reads every log every period): written in the summary
   for the host to take to Salem.
9. compute (A52, LD-57): `ladder.compute_audit --period P` on the E-cores (HOST/audit/compute-P<P>.json; measured
   once a period: a second measure could flip a member near the line). A member whose 90% interval is above 1.15
   (S15) holds the advance: Salem decides (RUNBOOK §4).
10. formal (A53): `ladder.arena formal` gives each player their own members' formal games of P, if the audit held
   nothing new, or when Salem decided to advance all the same.
11. boards (RUNBOOK §6): the private and the public leaderboard of P in HOST/reports (board-P<P>-private.json,
   board-P<P>.json).
12. advance: `ladder.pool advance` if nothing held it; then the public board is copied to PLAYERS/public and the
   receipts' status files are written again for the new period (`submit deliver`; a stop there is redone by the next
   double-click). Held: nothing is advanced; the summary says why (the first games / members by name) and gives the
   held set's held_digest; HOST/audit/held-P<P>.json keeps every held set by its digest (games and members, not the
   text). `--advance-anyway REASON --held DIGEST` (only after Salem decided on the summary with that held_digest)
   advances all the same and gives the formal games, the reason kept in the summary, but only if every problem held
   now is in that set: one that wasn't is refused (and its own set saved, widening none), to be taken to Salem.

Things to report that don't hold the period (the collection's errors and late directories: changed after the
deadline in report.collect.late, put in after it in steps.collected.late_new; void games, members short
and isolated, the anchors' voids, calibration missing in the compute check) are listed under "report" in the summary.

`--check`: steps 1-3 only (nothing is run, no lock is kept; an advanced period's publish left undone is left to the
run after the pull): exit 0 if the close could start now, 3 if it can't yet (the deadline hasn't come, the
collection isn't finished: the PC's wrapper doesn't pull then), 1 if the check itself failed (the wrapper pulls).
Exit codes: 0 closed and advanced (or closed earlier), 1 an error stopped it, 2 held for the host (see "held").
Results: OUT/summary.json, every command and its output in OUT/commands.log.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = LADDER.parents[1]
sys.path[:0] = [str(LADDER), str(ROOT), str(HERE)]

E_CORES = "0x3FC3FC"
DUE_PUZZLES = {1: ["START"]}          # S21 (11-23): the starting puzzle is evaluated at the end of period 1
PUZZLE_SEEDS = (91900000, 92000000)   # 公共题、起点测量 (SEEDS.md 正式分段)
PUZZLE_FIELD = "others"
REF_NAME = "参照"                      # 11-23 prompt evaluation item 10: not 「驾驶员」 (it would tell the players)


class Held(Exception):
    """Something the host must look at before the period may advance."""


def start_ref() -> str:
    """S19, LD-61: the Haven pilot as 2.5 measured it (pilot_native_spec), not bot:pilot-T1-HAVEN-1 (N=30)."""
    from svsim.ui.session import pilot_native_spec
    return "bot:" + pilot_native_spec("T1-HAVEN-1")


def env_for(extra: dict | None = None) -> dict:
    from open_period import child_env
    return dict(child_env(), **(extra or {}))


def run(args: list, log: Path, extra_env: dict | None = None, check: bool = True) -> tuple[int, str]:
    """One RUNBOOK command (`py -m ...`) from analysis/ladder; its output goes to the console and the log as it
    comes (a ladder runs for a while). A non-zero exit raises unless check is False."""
    from ladder.collect import python_cmd
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n$ {' '.join(map(str, args))}\n")
        f.flush()
        p = subprocess.Popen([*python_cmd()[0], *map(str, args)], cwd=str(LADDER), env=env_for(extra_env),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                             errors="replace")
        lines = []
        try:
            for line in p.stdout:
                lines.append(line)
                f.write(line)
                f.flush()
                try:
                    print(line, end="", flush=True)
                except Exception:                 # noqa: BLE001 - a console that can't show it mustn't stop it
                    pass
        except BaseException:                     # Ctrl+C: the child goes with this window
            p.terminate()
            raise
        rc = p.wait()
        f.write(f"exit {rc}\n")
    text = "".join(lines)
    if check and rc != 0:
        raise RuntimeError(f"{' '.join(map(str, args[:3]))} exit {rc}: {text[-1500:]}")
    return rc, text


def last_json(text: str):
    """The JSON a command printed last: the whole output, or from the last line that opens an object."""
    try:
        return json.loads(text)
    except ValueError:
        pass
    lines = text.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("{"):
            try:
                return json.loads("\n".join(lines[i:]))
            except ValueError:
                continue
    return None


def _read(path: Path, default=None):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else default


def _jsonl(path: Path) -> list[dict]:
    from ladder.arena import _jsonl as read
    return read(Path(path)) if Path(path).exists() else []


def window_of(arena: Path) -> dict:
    w = _read(Path(arena) / "public" / "window.json")
    if w is None:
        raise SystemExit(f"练习场没开过（{Path(arena) / 'public' / 'window.json'} 不在）")
    return w


def deadline_passed(window: dict, now: float | None = None) -> bool:
    return (time.time() if now is None else now) > datetime.fromisoformat(window["deadline"]).timestamp()


class NotYet(SystemExit):
    """The close can't start yet (the deadline hasn't come, or the collection loop hasn't finished the period): under
    --check exit 3, which the PC's wrapper reads as "don't
    pull" (any other failure of the check doesn't stop the pull: 11-24 review 3, a fix must be able to reach the PC)."""


def collected(host: Path, arena: Path, players: Path, period: int, kind: str, mask: int | None) -> dict:
    """Whether the collection loop finished period `period` (it stopped after its line 「这一期收完」): the listing at
    the deadline is in SUBS/collect.jsonl, every directory of it is done, nothing accepted is left to admit or gate.
    Read only: nothing is written here. `mask`: the E-cores, as the loop had them (the Collector refuses none on
    Windows, 11-24 review; it only reads here)."""
    from ladder.collect import Collector, listing
    subs = host / "subs"
    delta = _read(host / "gates" / f"delta-P{period}.json", {}).get("delta") if kind == "strategy" else None
    c = Collector(players, host / "pool", subs, arena, gates="after", frozen=host / "frozen" / f"P{period}.json",
                  delta=delta, gates_out=host / "gates", mask=mask, out=lambda s: None)
    if c.final is None:
        raise NotYet("收提交的循环截止那一刻没在跑（collect.jsonl 里没有这一期截止时的目录清单）：先照 RUNBOOK 第 3 节"
                         "查过文件时间，再用 open-period.cmd 重起收提交的循环（它会要 --after-deadline），等它打出「这一期收完」")
    done = c.done()
    left = sorted(f"{p}:{Path(d).name}" for (p, d), (st, _) in c.final.items() if (p, d, st) not in done)
    admits, gates = c.pending_admits(), c.pending_gates()
    if left or admits or gates:
        raise NotYet("收提交的循环还没收完：" + "；".join(x for x in (
            f"截止时在的目录还没收 {left}" if left else "", f"收下了还没入池 {admits}" if admits else "",
            f"收下了还没检验 {gates}" if gates else "") if x) + "。双击 open-period.cmd 让它收完（窗口要等到「这一期收完」）")
    # put into a submit\ after the deadline: the loop only printed them (collect.log); the report lists them (review 3)
    late_new = sorted(f"{p}:{Path(d).name}" for (p, d), (st, _) in listing(players).items()
                      if (p, d, st) not in done and (p, d) not in c.final)
    return {"deadline_dirs": len(c.final), "late_new": late_new}


def collect_notes(host: Path, window: dict, period: int) -> dict:
    """What the collection wrote down in this window that the host reports (no hold), and the receipts of P."""
    from ladder.submit import ledger
    opened = datetime.fromisoformat(window["opened"])
    lines = []
    for l in _jsonl(host / "subs" / "collect.jsonl"):
        try:
            t = datetime.fromisoformat(l.get("time", ""))
        except ValueError:
            continue
        if t >= opened:
            lines.append(l)
    notes = {
        "receive_errors": sum(1 for l in lines if l.get("ev") == "error"),
        "given_up": [Path(l["dir"]).name for l in lines if l.get("ev") == "dir" and l.get("gave_up")],
        "late": [Path(l["dir"]).name for l in lines if l.get("ev") == "dir" and l.get("late")],
        "admit_failed": [l.get("receipt") for l in lines if l.get("ev") == "admit-failed"],
        "gate_failed": [l.get("receipt") for l in lines if l.get("ev") == "gate-failed"],
        "deliver_failed": sum(1 for l in lines if l.get("ev") == "deliver-failed"),
    }
    per = {}
    for l in ledger(host / "subs"):
        if l.get("ev") == "receipt" and l.get("period") == period:
            d = per.setdefault(l["player"], {})
            k = f"{l.get('kind')}:{l.get('verdict')}"
            d[k] = d.get(k, 0) + 1
    notes["receipts"] = per
    return notes


def period_voids(games_path: Path, period: int) -> dict:
    """The void games of the pool in P, by the first line of their error (host side)."""
    out = {}
    for g in _jsonl(games_path):
        if (g.get("labels") or {}).get("period") == period and g.get("result") == "void":
            why = str(g.get("error") or "void").splitlines()[0][:160]
            out[why] = out.get(why, 0) + 1
    return out


def anchor_voids(anchors_dir: Path, period: int) -> dict:
    """The void games of P's anchor games as anchors.run counts them (games-P<P>.jsonl, then its redo files in order;
    the last line of an id wins), by the first line of their error. Read again on a re-run (11-24 review)."""
    files = [anchors_dir / f"games-P{period}.jsonl"] + sorted(
        anchors_dir.glob(f"games-P{period}-redo*.jsonl"), key=lambda f: int(f.stem.rsplit("redo", 1)[1]))
    last = {}
    for f in files:
        for g in _jsonl(f):
            if g.get("id"):
                last[g["id"]] = g
    out = {}
    for g in last.values():
        if g.get("result") == "void":
            why = str(g.get("error") or "void").splitlines()[0][:160]
            out[why] = out.get(why, 0) + 1
    return out


def audit_keys(au: dict) -> dict:
    """The audit's problems as comparable keys: failed (log, id), unlogged ids, unreadable "path:line"."""
    return {"failed": sorted(f"{f.get('log')}|{f.get('id')}" for f in au.get("failed", [])),
            "unlogged": sorted(str(x) for x in au.get("unlogged", [])),
            "unreadable": sorted(str(x) for x in au.get("unreadable", []))}


def held_digest(ids) -> str:
    """A short name for one set of held problems (what Salem is shown and decides on)."""
    return hashlib.sha256("\n".join(sorted(ids)).encode("utf-8")).hexdigest()[:10]


def earlier_audits(audit_dir: Path, period: int) -> dict:
    """Every problem an earlier period's audit (HOST/audit/P<k>.json, k < P) already listed: reported and decided
    then, so it doesn't hold P again (11-24 review: the audit reads every log of the pool, every period)."""
    seen = {"failed": set(), "unlogged": set(), "unreadable": set()}
    for f in audit_dir.glob("P*.json"):
        try:
            k = int(f.stem[1:])
        except ValueError:
            continue
        if k < period:
            for name, keys in audit_keys(_read(f, {})).items():
                seen[name].update(keys)
    return seen


def publish(host: Path, players: Path, subs: Path, pool_dir: Path, period: int, log: Path) -> dict:
    """After the advance: the public board of P into PLAYERS/public, then the receipts' status files written again for
    the new period. Both can be done again (a copy; deliver writes the same)."""
    pub = players / "public"
    pub.mkdir(parents=True, exist_ok=True)
    board = host / "reports" / f"board-P{period}.json"
    shutil.copy2(board, pub / board.name)
    _, text = run(["-m", "ladder.submit", "deliver", subs, "--pool", pool_dir, "--players", players], log)
    got = last_json(text) or {}
    bad = {k: v for k, v in got.items() if isinstance(v, str)} if isinstance(got, dict) else {}
    if bad:
        raise RuntimeError(f"回执写不进去：{bad}")
    out = {"ok": True, "board": str(pub / board.name), "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (host / "reports" / f"published-P{period}.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def next_puzzle_seed(host: Path) -> int:
    """After every seed range a puzzle plan or result of HOST/puzzles took (the segment is used up in order)."""
    his = [PUZZLE_SEEDS[0]]
    for f in sorted((host / "puzzles").glob("*/plan.json")) + sorted((host / "puzzles").glob("*/result-host.json")):
        try:
            his.append(int(json.loads(f.read_text(encoding="utf-8"))["seeds"][1]))
        except (ValueError, KeyError, TypeError, IndexError):
            continue
    return max(his)


def main(argv=None):
    for s in (sys.stdout, sys.stderr):           # a redirected console is cp1252 on Windows (ENVIRONMENT pitfall 1)
        try:
            s.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:                         # noqa: BLE001
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", type=Path, default=Path(r"C:\claude\ladder-host"))
    ap.add_argument("--arena", type=Path, default=Path(r"C:\claude\ladder-arena"))
    ap.add_argument("--players", type=Path, default=Path(r"C:\claude\ladder-players"))
    ap.add_argument("--out", type=Path, default=Path(r"C:\claude\ladder-runs\close"))
    ap.add_argument("--workers", type=int, default=23, help="all cores (S10): ladder, anchors, audit")
    ap.add_argument("--e-workers", type=int, default=15, help="the E-cores: what compares compute (A44)")
    ap.add_argument("--mask", default=E_CORES, help="the E-cores' mask; 'none' off Windows")
    ap.add_argument("--games-per-anchor", type=int, default=10, help="RUNBOOK §5 (tests only change it)")
    ap.add_argument("--check", action="store_true", help="only see whether the close could start now")
    ap.add_argument("--advance-anyway", metavar="REASON", help="advance although something held it (Salem decided)")
    ap.add_argument("--held", metavar="DIGEST", help="with --advance-anyway: the held_digest of the summary Salem was "
                                                     "shown; only those problems are let through")
    a = ap.parse_args(argv)
    if bool(a.advance_anyway) != bool(a.held):
        ap.error("--advance-anyway and --held go together (the held_digest of the summary Salem saw)")
    a.out.mkdir(parents=True, exist_ok=True)
    log = a.out / "commands.log"
    res = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "check": a.check, "steps": {}, "report": {}, "held": []}
    mask = [] if a.mask == "none" else ["--mask", a.mask]
    host, arena, players = a.host, a.arena, a.players
    pool_dir, subs, code = host / "pool", host / "subs", host / "subs" / "code"
    keep = []                                     # the locks held to the end

    def save():
        (a.out / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    def finish(code_: int) -> int:
        res["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
        res["exit"] = code_
        res["ok"] = code_ == 0
        save()
        print(json.dumps(res, ensure_ascii=False, indent=1), flush=True)
        return code_

    step = "lock"
    try:
        from check_lock import differs, recorded
        bad = differs()
        res["steps"]["lock"] = {"ok": not bad, "files": len(recorded()), "differs": bad}
        if bad:
            return finish(1)
        step = "key"
        from ladder import deal
        key = deal.resolve("auto")
        res["steps"]["key"] = {"ok": key is not None, "id": deal.key_id(key) if key else None}
        if key is None:
            return finish(1)
        step = "state"
        from ladder.pool import Pool, period_kind
        pool = Pool(pool_dir)
        period, window = pool.period, window_of(arena)
        if window["period"] == period - 1:
            res["steps"]["state"] = {"ok": True, "period": window["period"], "already_closed": True,
                                     "pool_period": period}
            done = window["period"]
            if (host / "reports" / f"board-P{done}.json").exists() and \
                    not (host / "reports" / f"published-P{done}.json").exists():
                step = "publish"                  # the advance went through, the publish didn't: do it now
                if a.check:                       # --check runs nothing: the run after the pull publishes (review 3)
                    res["steps"]["publish"] = {"ok": True, "pending": True}
                    return finish(0)
                res["steps"]["publish"] = publish(host, players, subs, pool_dir, done, log)
            print(f"第 {window['period']} 期已经收尾、进了第 {period} 期：什么都不做。", flush=True)
            return finish(0)
        if window["period"] != period:
            raise SystemExit(f"练习场最后开的是第 {window['period']} 期，池子在第 {period} 期：先查清楚")
        from open_period import is_open
        is_open(arena, period)                    # a window of P on another field stops here
        if not deadline_passed(window):
            raise NotYet(f"第 {period} 期还没到截止时间（{window['deadline']}，UTC）：什么都没做")
        kind = period_kind(period)
        import environments                       # S25: closed (played, replayed) on the period's own simulator
        env = environments.check(period)
        res["steps"]["state"] = {"ok": True, "period": period, "kind": kind, "deadline": window["deadline"],
                                 "env": env["name"]}
        step = "collected"
        if not a.check:
            from ladder.collect import _only_one
            keep.append(_only_one(subs))          # no collection loop now, and none while this runs
        mask_int = None if a.mask == "none" else int(a.mask, 0)
        res["steps"]["collected"] = {"ok": True, **collected(host, arena, players, period, kind, mask_int)}
        res["report"]["collect"] = collect_notes(host, window, period)
        if a.check:
            return finish(0)
        from ladder.arena import _lock
        print("拿练习场的锁（选手还有对局在跑就等它跑完）……", flush=True)
        keep.append(_lock(arena))
        save()

        step = "ladder"
        runs = []
        for _ in range(8):
            pool = Pool(pool_dir)
            if not pool.period_done() or pool.stuck(True):
                break
            _, text = run(["-m", "ladder.pool", "ladder", pool_dir, "--until-period-done", "--workers", a.workers],
                          log, {"LADDER_EXTRA_PATH": str(code)})
            got = last_json(text) or {}
            runs.append({k: got.get(k) for k in ("played", "seconds", "results", "short", "isolated", "stuck")})
            save()
            if not got.get("played"):
                break
        pool = Pool(pool_dir)
        short = pool.period_done()
        iso = set(pool.isolated())
        res["steps"]["ladder"] = {"ok": not short, "runs": runs, "short": short,
                                  "short_isolated": [{"member": m.mid, "games": m.period_games, "cr": m.cr}
                                                     for m in pool.short_members() if m.mid in iso],
                                  "active": len(pool.active()), "mu": round(pool.mu, 2)}
        res["report"]["ladder_voids"] = period_voids(pool.games_path, period)
        if short:
            raise SystemExit(f"天梯停了，还有 {len(short)} 个成员不够 100 局、又不是够不着：{short[:10]}")
        save()

        step = "hof"
        anchors_dir = host / "anchors"
        anchors_dir.mkdir(parents=True, exist_ok=True)
        hof, table = anchors_dir / "hof.json", anchors_dir / "anchors.json"
        had = [h for h in _read(hof, []) if h.get("period") == period]
        if had:
            new = had
            res["steps"]["hof"] = {"ok": True, "kept": [h["mid"] for h in had]}
        else:
            _, text = run(["-m", "ladder.anchors", "induct", pool_dir, "--hof", hof], log)
            new = last_json(text) or []
            res["steps"]["hof"] = {"ok": True, "new": [{"slot": h["slot"], "craft": h["craft"], "member": h["mid"],
                                                        "version": h["version"], "rel_cr": h["rel_cr"]} for h in new]}
        run(["-m", "ladder.anchors", "table", "--out", table, "--hof", hof], log)
        res["steps"]["hof"]["anchors"] = len(_read(table, []))
        save()

        step = "anchors"
        plan = _read(anchors_dir / f"plan-P{period}.json", {})
        if plan.get("done"):
            res["steps"]["anchors"] = {"ok": True, "kept": plan.get("done"), "games": plan.get("jobs")}
        else:
            _, text = run(["-m", "ladder.anchors", "run", table, "--pool", pool_dir, "--out", anchors_dir,
                           "--code", code, "--games-per-anchor", a.games_per_anchor, "--workers", a.workers], log)
            got = last_json(text) or {}
            res["steps"]["anchors"] = {"ok": True, **{k: got.get(k) for k in ("jobs", "played", "first_seed",
                                                                               "last_seed", "deal")}}
        av = anchor_voids(anchors_dir, period)
        if av:
            res["report"]["anchor_voids"] = av
        host_reports = host / "reports"
        host_reports.mkdir(parents=True, exist_ok=True)
        _, text = run(["-m", "ladder.anchors", "report", anchors_dir, "--anchors", table, "--period", period], log)
        (host_reports / f"anchors-P{period}.json").write_text(text, encoding="utf-8")
        save()

        step = "puzzles"
        from ladder.puzzles import _registry, field_of
        due = {}
        for pid in DUE_PUZZLES.get(period, []):
            if pid not in _registry(subs):
                raise SystemExit(f"题 {pid} 没在 {subs / 'puzzles.json'} 里登记（first_setup 第 5 步）")
            out = host / "puzzles" / pid
            if (out / "result-public.json").exists():
                due[pid] = {"kept": str(out / "result-public.json")}
                continue
            out.mkdir(parents=True, exist_ok=True)
            pf = out / "plan.json"
            if not pf.exists():
                lo = next_puzzle_seed(host)
                hi = lo + 100 * len(field_of(PUZZLE_FIELD))
                if hi > PUZZLE_SEEDS[1]:
                    raise SystemExit(f"公共题种子段 {PUZZLE_SEEDS[0]}～{PUZZLE_SEEDS[1] - 1} 不够了：先登记新的一段")
                pf.write_text(json.dumps({"puzzle": pid, "seeds": [lo, hi], "field": PUZZLE_FIELD,
                                          "ref": {REF_NAME: start_ref()}, "time": time.strftime("%Y-%m-%dT%H:%M:%S")},
                                         ensure_ascii=False), encoding="utf-8")
            p = _read(pf)
            run(["-m", "ladder.puzzles", "run", subs, "--id", pid, "--seeds", *p["seeds"], "--out", out,
                 "--field", p["field"], *[x for n, s in p["ref"].items() for x in ("--ref", f"{n}={s}")],
                 "--workers", a.e_workers, *mask], log)
            host_res = _read(out / "result-host.json", {})
            due[pid] = {"seeds": p["seeds"], "entries": [{k: e.get(k) for k in ("entry", "decided", "rate", "lo",
                                                                                   "hi", "vs_default_pp")}
                                                          for e in host_res.get("entries", [])],
                        "simulator_changed": host_res.get("simulator_changed")}
        res["steps"]["puzzles"] = {"ok": True, **due}
        save()

        step = "audit"
        audit_dir = host / "audit"
        audit_dir.mkdir(parents=True, exist_ok=True)
        audit_out = audit_dir / f"P{period}.json"
        if not environments.seals(host):          # one environment so far: every log, whole
            rc, _ = run(["-m", "ladder.audit", pool_dir / "games.jsonl", anchors_dir / f"games-P{period}*.jsonl",
                         "--events", pool_dir / "events.jsonl", "--workers", a.workers, "--out", audit_out,
                         "--allow-empty", host / "gates" / "*" / "games.jsonl", host / "puzzles" / "*" / "games.jsonl"],
                        log, check=False)
            sealed = None
        else:                                     # S25: what was sealed was replayed on its own simulator already
            logs = [pool_dir / "games.jsonl", *sorted(anchors_dir.glob(f"games-P{period}*.jsonl")),
                    *sorted((host / "gates").glob("*/games.jsonl")), *sorted((host / "puzzles").glob("*/games.jsonl"))]
            sealed = environments.audit_inputs(host, logs, pool_dir / "events.jsonl", audit_dir / f"since-seal-P{period}")
            if sealed["logs"] or sealed["events"]:
                if not sealed["logs"]:            # games counted since, none logged: all "unlogged"
                    none = audit_dir / f"since-seal-P{period}" / "no-games.jsonl"
                    none.write_text("", encoding="utf-8")
                    sealed["logs"] = [none]
                rc, _ = run(["-m", "ladder.audit", *sealed["logs"],
                             *(["--events", sealed["events"]] if sealed["events"] else []),
                             "--workers", a.workers, "--out", audit_out], log, check=False)
            else:
                rc = 0
                audit_out.write_text(json.dumps({"checked": 0, "skipped": 0, "failed": [], "unlogged": [],
                                                 "unreadable": [], "voids": {}, "ok": True}), encoding="utf-8")
        if rc not in (0, 1) or not audit_out.exists():
            raise RuntimeError(f"ladder.audit exit {rc}（日志找不到或读不了，见 commands.log）")
        au = _read(audit_out)
        seen = earlier_audits(audit_dir, period)
        new = {name: [k for k in keys if k not in seen[name]] for name, keys in audit_keys(au).items()}
        res["steps"]["audit"] = {"ok": True, "checked": au["checked"], "skipped": au["skipped"],
                                 **{name: len(keys) for name, keys in new.items()},
                                 "listed_earlier": {name: len(audit_keys(au)[name]) - len(new[name]) for name in new}}
        if sealed is not None:
            res["steps"]["audit"].update({"since_seal": sealed["sealed"], "logs": len(sealed["logs"])})
            for rel in sealed["changed"]:
                new.setdefault("sealed", []).append(rel)
        audit_clean = not any(new.values())
        held_ids = [f"{name}:{k}" for name, keys in new.items() for k in keys]

        def some(keys):
            return "、".join(k.rsplit("|", 1)[-1] for k in keys[:5]) + ("……" if len(keys) > 5 else "")
        if new["failed"]:
            res["held"].append(f"重放审计：{len(new['failed'])} 局重放不出来（{some(new['failed'])}；{audit_out}）")
        if new["unlogged"]:
            res["held"].append(f"重放审计：池子算过分、日志里没有的局 {len(new['unlogged'])} 局"
                               f"（{some(new['unlogged'])}；{audit_out}）")
        if new["unreadable"]:
            res["held"].append(f"重放审计：日志里有 {len(new['unreadable'])} 行不是完整的 JSON"
                               f"（{some(new['unreadable'])}；{audit_out}）")
        if new.get("sealed"):
            res["held"].append(f"换环境时封存的旧日志被动过：{'、'.join(new['sealed'])}（{host / 'audit' / 'sealed.json'}）")
        if any(res["steps"]["audit"]["listed_earlier"].values()):
            res["report"]["audit_listed_earlier"] = res["steps"]["audit"]["listed_earlier"]
        if au["voids"]:
            res["report"]["audit_voids"] = au["voids"]
        save()

        step = "compute"
        comp_out = audit_dir / f"compute-P{period}.json"
        kept_compute = comp_out.exists()          # measured once: a second measure could flip a member near the line
        if not kept_compute:
            tmp = comp_out.with_suffix(".partial.json")
            rc, _ = run(["-m", "ladder.compute_audit", pool_dir, "--period", period, "--workers", a.e_workers, *mask,
                         "--out", tmp], log, check=False)
            if rc not in (0, 1) or not tmp.exists():
                raise RuntimeError(f"ladder.compute_audit exit {rc}（见 commands.log）")
            os.replace(tmp, comp_out)
        co = _read(comp_out)
        over = [m for m in co["members"] if m.get("over")]
        res["steps"]["compute"] = {"ok": True, **({"kept": str(comp_out)} if kept_compute else {}),
                                   "members": len(co["members"]), "over": len(over),
                                   "calibration": co["calibration"], "problems": len(co.get("problems", []))}
        if over:
            held_ids += [f"compute:{m['member']}@{m['version']}" for m in over]
            res["held"].append(f"算力抽查：{len(over)} 个成员 90% 区间整个在 1.15 以上"
                               f"（{'、'.join(m['member'] for m in over)}；{comp_out}）：由 Salem 定")
        if co["calibration"].get("note") or co.get("problems"):
            res["report"]["compute"] = {"calibration": co["calibration"], "problems": co.get("problems", [])}
        save()

        # what held this run, by identity (games, members): Salem's --advance-anyway names the set he was shown by its
        # digest, and lets through only problems in that set; a run held again adds its own set, widening none (review 3)
        held_file = audit_dir / f"held-P{period}.json"
        sets = _read(held_file, {})
        if not isinstance(sets, dict):
            sets = {}
        digest = held_digest(held_ids) if res["held"] else None
        res["held_digest"] = digest
        shown = set((sets.get(a.held) or {}).get("ids", [])) if a.held else set()
        covered = bool(a.advance_anyway) and a.held in sets and set(held_ids) <= shown
        save()

        step = "formal"
        if audit_clean or covered:                # Salem's decision covers the period's games (11-24 review)
            _, text = run(["-m", "ladder.arena", "formal", arena, "--pool", pool_dir, "--subs", subs,
                           "--period", period], log)
            res["steps"]["formal"] = {"ok": True, "players": last_json(text)}
        else:
            res["steps"]["formal"] = {"ok": True, "skipped": "重放审计有新问题：正式对局先不给，Salem 定了照样进下一期"
                                                         "（--advance-anyway … --held <held_digest>）时一起给"}
        save()

        step = "boards"
        _, text = run(["-m", "ladder.leaderboard", pool_dir, "--out", host_reports / f"board-P{period}-private.json"],
                      log)
        run(["-m", "ladder.leaderboard", pool_dir, "--public", "--out", host_reports / f"board-P{period}.json"], log)
        res["steps"]["boards"] = {"ok": True, "private": str(host_reports / f"board-P{period}-private.json"),
                                  "public": str(host_reports / f"board-P{period}.json")}
        save()

        step = "advance"
        if res["held"] and not covered:
            sets.setdefault(digest, {"ids": sorted(held_ids), "held": res["held"], "out": str(a.out),
                                     "time": time.strftime("%Y-%m-%dT%H:%M:%S")})
            held_file.write_text(json.dumps(sets, ensure_ascii=False, indent=1), encoding="utf-8")
            refused = {}
            if a.advance_anyway:
                refused = {"anyway_refused": (f"--held {a.held} 不在 {held_file.name} 里" if a.held not in sets else
                                              "有 Salem 看过的那份清单里没有的问题：要再问 Salem")}
            res["steps"]["advance"] = {"ok": False, "held": True, **refused}
            print(f"没进下一期，要主持方先看（held_digest {digest}）：\n" + "\n".join(res["held"]), flush=True)
            return finish(2)
        _, text = run(["-m", "ladder.pool", "advance", pool_dir], log)
        res["steps"]["advance"] = {"ok": True, **(last_json(text) or {}),
                                   **({"anyway": a.advance_anyway, "held": a.held} if res["held"] else {})}
        save()
        step = "publish"                          # after the advance; a stop here is redone by the next double-click
        res["steps"]["publish"] = publish(host, players, subs, pool_dir, period, log)
        print(f"第 {period} 期收尾完了，池子进了第 {period + 1} 期。", flush=True)
        return finish(0)
    except KeyboardInterrupt:
        res["steps"][step] = {"ok": False, "error": "stopped by Ctrl+C"}
        return finish(1)
    except (Exception, SystemExit) as e:
        res["steps"][step] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        return finish(3 if a.check and isinstance(e, NotYet) else 1)
    finally:
        from ladder.arena import _unlock
        for f in reversed(keep):
            try:
                _unlock(f)
            except Exception:                     # noqa: BLE001
                pass


if __name__ == "__main__":
    sys.exit(main())
