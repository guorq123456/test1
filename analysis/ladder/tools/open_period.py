"""Opening a period on Salem's computer in one go (RUNBOOK 每期 §1 and §3; 11-23 prompt evaluation: without it the
players' first arena command says the arena is not open and nobody collects what they hand in).

    python analysis/ladder/tools/open_period.py [--host DIR] [--arena DIR] [--players DIR] [--out DIR]
                                                [--hours 12] [--games 60000] [--workers 23] [--delta PP] [--dry]

1. lock: the locked files are as locked (tools/check_lock.py); key: the formal pool's deal key is there (its id only).
2. state: the pool's period and kind (deck or strategy in periods 1-3; from period 4 every period is merged: new decks
   and strategy updates in one window, Salem S35/S36). A period that takes updates (strategy, merged) needs its gate
   margin (RUNBOOK §1.3): kept in HOST/gates/delta-P<period>.json, written the first time it is given (`--delta`);
   given again it must be the same. A merged period with none given and none kept carries over the most recent kept
   delta-P<k>.json (k < period; S34's 5 pp stands until Salem changes it) and keeps it for this period, saying so; with
   none at all (or a strategy period with none) the tool stops. So the double-click needs no input.
   **If the arena's window is already open for this period's field, steps 3-5 are skipped**: never a second snapshot
   or window (the deadline and the field the players practise on stay as they were). A window of this period on
   another field (someone snapshot by hand after it opened) stops the tool: it never opens a second window.
   Opening (not when the window is open already): the players' guides (analysis/ladder/public) copied into
   PLAYERS/public, each file that differs (11-24: arena.md on the queue's turns).
3. freeze: HOST/frozen/P<period>.json (ladder.evaluator freeze; kept if it is there already).
4. anchors: HOST/anchors/anchors.json (ladder.anchors table: the baseline snapshot, then the hall of fame from
   HOST/anchors/hof.json if there is one).
5. arena: ladder.arena snapshot POOL --arena ARENA --anchors anchors.json --code HOST/subs/code, then ladder.arena open
   --hours --games --workers (12 hours, 60 000 games a player: Salem's numbers, S29 from period 3; periods 1-2 had 4 hours, 20 000).
6. report: ladder.report POOL --out PLAYERS/public/reports --anchors-dir HOST/anchors, with a note naming the period, the
   deadline (UTC) and the practice limits, and --puzzle for every HOST/puzzles/<id>/result-public.json not in an
   earlier report (HOST/puzzles/reported.json lists those that were). Kept if this period's report is there. A
   report that fails is written in the summary and the loop still starts (the window is open already).
7. collect: ladder.collect until the deadline and after it until everything of the period is in (A55): 15 workers on
   the E-cores (--mask 0x3FC3FC: receiving compares compute, A44); a period that takes updates (strategy, merged)
   adds --gates after --frozen --delta --gates-out. Its last line says the period is collected and the ladder can start. Started again after the
   deadline it refuses (it does not know what was there at the deadline); see RUNBOOK §3.

`--dry` works under OUT only: the formal pool copied to OUT/host/pool (the original is not touched), an empty ledger
whose code is the real HOST/subs/code (only read), the real hall of fame, kept delta and public puzzle results copied,
OUT/arena, OUT/players with the five players' folders and the public folder; the window is short (`--hours`, default
0.05 = 3 minutes) and the loop looks every 10 seconds. It plays no game and uses no seed. Results: OUT/summary.json,
the loop's lines in OUT/collect.log.

`--is-open` (for the launcher's wrapper, which pulls the repository only when no window is open): exit 10 if the
arena has a window for the pool's period, 11 if not; nothing else is done.
`--set-delta PP` (before the first double-click of a period that takes updates, RUNBOOK §1.3): only records the pool's
period's gate margin in HOST/gates/delta-P<period>.json (refused if another one is kept, or if the period takes no
updates: a deck period); opens nothing.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = LADDER.parents[1]
sys.path[:0] = [str(LADDER), str(ROOT), str(HERE)]

E_CORES = "0x3FC3FC"


def child_env() -> dict:
    from ladder.collect import python_cmd
    return dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT), str(LADDER)]), PYTHONUTF8="1",
                PYTHONIOENCODING="utf-8", PYTHONHASHSEED="0", **python_cmd()[1])


def py(args: list, log: Path) -> str:
    """One RUNBOOK command (`py -m ...`) from analysis/ladder; its output goes to the log; a non-zero exit stops."""
    from ladder.collect import python_cmd
    r = subprocess.run([*python_cmd()[0], *map(str, args)], cwd=str(LADDER), env=child_env(), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n$ {' '.join(map(str, args))}\nexit {r.returncode}\n{r.stdout}{r.stderr}")
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, args[:3]))} exit {r.returncode}: {(r.stderr or r.stdout)[-1500:]}")
    return r.stdout


def dry_layout(out: Path, host: Path) -> tuple[Path, Path, Path]:
    """OUT/host (a copy of the formal pool, an empty ledger, the hall of fame, kept deltas and puzzle results), OUT/arena,
    OUT/players (the five folders, public)."""
    from ladder.arena import FOLDER
    from first_setup import HOST_DIRS
    for d in ("host", "arena", "players"):
        if (out / d).exists():
            raise SystemExit(f"{out / d} is there already: a dry run starts clean (use another --out)")
    if not (host / "pool" / "events.jsonl").exists():
        raise SystemExit(f"no pool at {host / 'pool'}")
    shutil.copytree(host / "pool", out / "host" / "pool")
    for d in HOST_DIRS:
        (out / "host" / d).mkdir(parents=True, exist_ok=True)
    (out / "host" / "subs" / "code").mkdir(parents=True, exist_ok=True)
    for rel in ("anchors/hof.json", *[str(p.relative_to(host)) for p in sorted((host / "gates").glob("delta-P*.json"))],
                "puzzles/reported.json", "audit/sealed.json",
                *[str(p.relative_to(host)) for p in sorted((host / "puzzles").glob("*/result-public.json"))]):
        if (host / rel).is_file():
            (out / "host" / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(host / rel, out / "host" / rel)
    for name in FOLDER.values():
        for sub in ("submit", "receipts"):
            (out / "players" / name / sub).mkdir(parents=True, exist_ok=True)
    pub = out / "players" / "public"
    pub.mkdir(parents=True)
    for f in (LADDER / "public").iterdir():
        if f.is_file():
            shutil.copy2(f, pub / f.name)
    return out / "host", out / "arena", out / "players"


def is_open(arena: Path, period: int) -> dict | None:
    """The window, if the arena is open for this period on the field it was snapshot with. A window of this period
    on another field (a snapshot by hand after the window opened) stops: never a second window (11-23 review)."""
    f, w = arena / "host" / "field.json", arena / "public" / "window.json"
    if not w.exists():
        return None
    window = json.loads(w.read_text(encoding="utf-8"))
    field = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    if window.get("period") != period:
        return None
    if field.get("period") == period and window.get("field") == field.get("hash"):
        return window
    raise SystemExit(f"第 {period} 期的窗口已经开过（截止 {window.get('deadline')}），可是练习场的冻结副本换过了："
                     "不再开一次窗口、不挪截止时刻。先查清楚是谁、为什么又做了 snapshot（RUNBOOK 每期第 1 节）")


def kept_delta_before(host: Path, period: int) -> tuple[int, float] | None:
    """The most recent kept gate margin of an earlier period: (k, delta) from HOST/gates/delta-P<k>.json, k < period."""
    kept = []
    for f in (host / "gates").glob("delta-P*.json"):
        k = f.stem[len("delta-P"):]
        if k.isdigit() and int(k) < period:
            kept.append((int(k), float(json.loads(f.read_text(encoding="utf-8"))["delta"])))
    return max(kept) if kept else None


def period_delta(host: Path, period: int, given: float | None, carry: bool = False) -> float:
    """The gate margin of a period that takes updates: kept in HOST/gates/delta-P<period>.json once given. `carry` (a
    merged period, S35/S36): with none given and none kept, the most recent earlier kept one is carried over and kept
    for this period (S34's 5 pp stands until Salem changes it)."""
    f = host / "gates" / f"delta-P{period}.json"
    if f.exists():
        kept = json.loads(f.read_text(encoding="utf-8"))["delta"]
        if given is not None and float(given) != float(kept):
            raise SystemExit(f"第 {period} 期的 delta 已经定成 {kept:g}（{f}），这次给的是 {given:g}：不改")
        return float(kept)
    row = {"period": period}
    if given is None:
        before = kept_delta_before(host, period) if carry else None
        if before is None:
            raise SystemExit(f"第 {period} 期收打法更新：要先定这一期把关的 delta（RUNBOOK 每期 1.3），"
                             f"第一次用 --delta 给，会记进 {f}")
        row["carried_from"], given = before
        print(f"第 {period} 期没给 delta：沿用第 {before[0]} 期的 {before[1]:g}（gates\\delta-P{before[0]}.json），"
              f"记进 {f}", flush=True)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({**row, "delta": float(given), "time": time.strftime("%Y-%m-%d %H:%M:%S")}),
                 encoding="utf-8")
    return float(given)


def new_puzzles(host: Path) -> list[Path]:
    """Public puzzle results not in an earlier report."""
    rec = host / "puzzles" / "reported.json"
    done = set(json.loads(rec.read_text(encoding="utf-8"))) if rec.exists() else set()
    return [p for p in sorted((host / "puzzles").glob("*/result-public.json")) if p.parent.name not in done]


def mark_reported(host: Path, files: list[Path]):
    rec = host / "puzzles" / "reported.json"
    done = json.loads(rec.read_text(encoding="utf-8")) if rec.exists() else []
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_text(json.dumps(done + [p.parent.name for p in files if p.parent.name not in done], ensure_ascii=False),
                   encoding="utf-8")


def note_for(period: int, kind: str, window: dict, delta: float | None = None) -> str:
    from ladder.arena import RUN_GAMES_MAX
    from environments import env_of
    from ladder.pool import MERGED_FROM
    zh = {"deck": "卡组期", "strategy": "策略期", "merged": "合并期"}[kind]
    text = (f"第 {period} 期（{zh}）。工作时间 {window['hours']:g} 小时，五人共用一个截止时刻：{window['deadline']}（UTC）。"
            f"练习每人这一期最多 {window['games']} 局，一次最多 {RUN_GAMES_MAX} 局。")
    if period == 1:
        text += "起点题 START 和这一期共用工作时间和练习局数。"
    if kind == "merged":                          # Salem S35/S36: decks and updates in one period from period 4
        if period == MERGED_FROM:
            text += "从这一期起卡组期和策略期合并（Salem 定的），规则见公共目录里的 rules.md 和 submit.md（这一期换了版本）。"
        text += ("这一期新卡组和打法更新都收：新卡组可交可不交，每个职业最多一副，收下就入池；"
                 "打法更新只给这一期开始时已经在池子里的成员，这一期才入池的成员这一期不能改打法，下一期起可以。"
                 "保护期：这一期入池的成员到下一期结束都受保护。")
    if kind in ("strategy", "merged") and delta is not None:  # the prompt: 要强多少，主持方每期开始前定好
        text += (f"这一期把关检验要新版本比池子里那一版强 {delta:g} 个百分点（检验的备择假设）；"
                 "检验在截止以后统一跑" + ("，对手是这一期开始时冻结的池子。" if kind == "merged" else "。"))
    env = env_of(period)
    if env["from"] == period and period > 1:     # S25: a new simulator from this period
        text += (f"这一期起模拟器换成新环境（{env['name']}"
                 + (f"，改了什么见公共目录里的 {Path(env['notes']).name}" if env.get("notes") else "") +
                 "）：这一期的练习和正式对局都在新环境里打；下面上一期的成绩、胜率、锚点和公共题结果都是旧环境里打的，"
                 "上一期发给你的正式对局（runs 里上一期那份）也是，用现在的代码重放会对不上。")
    return text


def collect(args: list, log: Path) -> int:
    """The collection loop as its own process; its lines go to the console and to the log."""
    from ladder.collect import python_cmd
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n$ {' '.join(map(str, args))}\n")
        p = subprocess.Popen([*python_cmd()[0], *map(str, args)], cwd=str(LADDER), env=child_env(),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                             errors="replace")
        try:
            for line in p.stdout:
                f.write(line)
                f.flush()
                try:
                    print(line, end="", flush=True)
                except Exception:                 # noqa: BLE001 - a console that can't show it mustn't stop the loop
                    pass
        except BaseException:                     # Ctrl+C: the loop goes with this window
            p.terminate()
            raise
        return p.wait()


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
    ap.add_argument("--out", type=Path, default=Path(r"C:\claude\ladder-runs\open"))
    ap.add_argument("--hours", type=float, help="default 12 (S29); 0.05 with --dry")
    ap.add_argument("--games", type=int, default=60000)   # S29
    ap.add_argument("--workers", type=int, default=23, help="the arena's workers (all cores, S10)")
    ap.add_argument("--mask", default=E_CORES, help="the collection loop's E-cores (A44); 'none' off Windows")
    ap.add_argument("--delta", type=float, help="the gate margin of a period that takes updates (percentage points)")
    ap.add_argument("--every", type=float, help="the loop's pause between looks (default 120 s, 10 s with --dry)")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--is-open", action="store_true")
    ap.add_argument("--set-delta", type=float, help="only record this period's gate margin (a period that takes "
                                                     "updates: strategy, merged), open nothing")
    a = ap.parse_args(argv)
    if a.set_delta is not None:
        from ladder.pool import Pool, period_kind, takes_updates
        period = Pool(a.host / "pool").period
        if not takes_updates(period):
            zh = {"baseline": "基线期", "deck": "卡组期"}.get(period_kind(period), period_kind(period))
            raise SystemExit(f"第 {period} 期是{zh}，不收打法更新、没有把关，不用 delta")
        print(f"第 {period} 期的 delta：{period_delta(a.host, period, a.set_delta):g}（{a.host / 'gates'}）")
        return 0
    if a.is_open:
        from ladder.pool import Pool
        try:
            return 10 if is_open(a.arena, Pool(a.host / "pool").period) else 11
        except SystemExit:
            return 10                             # a window of this period on another field: open, all the same
    hours = a.hours if a.hours is not None else (0.05 if a.dry else 12.0)
    every = a.every if a.every is not None else (10.0 if a.dry else 120.0)
    a.out.mkdir(parents=True, exist_ok=True)
    log = a.out / "commands.log"
    res = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "dry": a.dry, "steps": {}}

    def finish(ok: bool) -> int:
        res["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
        res["ok"] = ok and all(s.get("ok", True) for s in res["steps"].values())
        (a.out / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(res, ensure_ascii=False, indent=1), flush=True)
        return 0 if res["ok"] else 1

    step = "lock"
    try:                                              # whatever stops a step, summary.json says which and why
        from check_lock import differs, recorded
        bad = differs()
        res["steps"]["lock"] = {"ok": not bad, "files": len(recorded()), "differs": bad}
        if bad:
            return finish(False)
        step = "key"
        from ladder import deal
        key = deal.resolve("auto")
        if a.dry and key is None:
            res["steps"]["key"] = {"ok": True, "note": "dry run: no key (no formal game is played)"}
        else:
            res["steps"]["key"] = {"ok": key is not None, "id": deal.key_id(key) if key else None}
            if key is None:
                return finish(False)
        host, arena, players = a.host, a.arena, a.players
        if a.dry:
            step = "dry layout"
            host, arena, players = dry_layout(a.out, a.host)
            res["steps"]["dry layout"] = {"ok": True, "host": str(host), "arena": str(arena), "players": str(players)}
        step = "state"
        from ladder.pool import Pool, period_kind, takes_updates
        pool_dir = host / "pool"
        period = Pool(pool_dir).period
        kind = period_kind(period)
        if period < 1:
            raise SystemExit(f"the pool is in period {period}: the players' periods start at 1 (RUNBOOK 第一次 4)")
        delta = period_delta(host, period, a.delta, carry=kind == "merged") if takes_updates(period) else None
        window = is_open(arena, period)
        carried = (json.loads((host / "gates" / f"delta-P{period}.json").read_text(encoding="utf-8"))
                   .get("carried_from") if delta is not None else None)
        res["steps"]["state"] = {"ok": True, "period": period, "kind": kind, "already_open": window is not None,
                                 **({"delta": delta} if delta is not None else {}),
                                 **({"delta_carried_from": carried} if carried is not None else {})}
        step = "environment"                      # S25: the simulator must be this period's (tools/environments.py)
        import environments
        env = environments.check(period)
        res["steps"]["environment"] = {"ok": True, "env": env["name"], "fingerprint": env["fingerprint"]}
        frozen = host / "frozen" / f"P{period}.json"
        if window is None:
            step = "seal"                         # a new environment's first period: the old logs, as replayed
            sealed = environments.seal(host, period)
            if sealed:
                res["steps"]["seal"] = {"ok": True, "env": sealed["env"], "files": len(sealed["files"])}
            if env.get("notes") and env["from"] == period:
                (players / "public").mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / env["notes"], players / "public" / Path(env["notes"]).name)
                res["steps"]["environment"]["notes"] = str(players / "public" / Path(env["notes"]).name)
            step = "public"                       # the players' guides as the repository has them now (11-24:
            pub = players / "public"              # arena.md on the turns); between periods only, like the seal
            pub.mkdir(parents=True, exist_ok=True)
            changed = []
            for f in sorted((LADDER / "public").iterdir()):
                if f.is_file() and (not (pub / f.name).exists() or (pub / f.name).read_bytes() != f.read_bytes()):
                    shutil.copy2(f, pub / f.name)
                    changed.append(f.name)
            res["steps"]["public"] = {"ok": True, "updated": changed}
            step = "freeze"
            if frozen.exists():
                res["steps"]["freeze"] = {"ok": True, "kept": str(frozen)}
            else:
                frozen.parent.mkdir(parents=True, exist_ok=True)
                py(["-m", "ladder.evaluator", "freeze", pool_dir, "--out", frozen], log)
                res["steps"]["freeze"] = {"ok": True, "wrote": str(frozen)}
            step = "anchors"
            anchors = host / "anchors" / "anchors.json"
            hof = host / "anchors" / "hof.json"
            anchors.parent.mkdir(parents=True, exist_ok=True)
            py(["-m", "ladder.anchors", "table", "--out", anchors, *(["--hof", hof] if hof.exists() else [])], log)
            res["steps"]["anchors"] = {"ok": True, "anchors": len(json.loads(anchors.read_text(encoding="utf-8"))),
                                       "hof": hof.exists()}
            step = "arena"
            code = (a.host if a.dry else host) / "subs" / "code"         # the dry run only reads the real one
            if not a.dry:
                code.mkdir(parents=True, exist_ok=True)
            py(["-m", "ladder.arena", "snapshot", pool_dir, "--arena", arena, "--anchors", anchors, "--code", code],
               log)
            py(["-m", "ladder.arena", "open", arena, "--hours", f"{hours:g}", "--games", a.games,
                "--workers", a.workers], log)
            window = is_open(arena, period)
            if window is None:
                raise RuntimeError("the arena did not open")
            field = json.loads((arena / "public" / "field.json").read_text(encoding="utf-8"))
            res["steps"]["arena"] = {"ok": True, "opened": window["opened"], "deadline": window["deadline"],
                                     "hours": window["hours"], "games": window["games"],
                                     "opponents": len(field["opponents"])}
        step = "report"
        reports = players / "public" / "reports"
        try:                                      # the window is open: a failed report must not keep the loop off
            if (reports / f"report-P{period}.md").exists():
                res["steps"]["report"] = {"ok": True, "kept": str(reports / f"report-P{period}.md")}
            else:
                puzzles = new_puzzles(host)
                py(["-m", "ladder.report", pool_dir, "--out", reports, "--anchors-dir", host / "anchors",
                    "--note", note_for(period, kind, window, delta), *[x for p in puzzles for x in ("--puzzle", p)]], log)
                mark_reported(host, puzzles)
                res["steps"]["report"] = {"ok": True, "wrote": str(reports / f"report-P{period}.md"),
                                          "puzzles": [p.parent.name for p in puzzles]}
        except Exception as e:                    # noqa: BLE001
            res["steps"]["report"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
            print(f"环境报告没写成（见 summary.json）：收提交的循环照样开。", flush=True)
        (a.out / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"第 {period} 期开了：截止 {window['deadline']}（UTC）。收提交的循环开始，"
              f"这个窗口要一直开着，到它打出「这一期收完」。", flush=True)
        step = "collect"
        mask = [] if a.mask == "none" else ["--mask", a.mask]
        gates = (["--gates", "after", "--frozen", frozen, "--delta", f"{delta:g}", "--gates-out", host / "gates"]
                 if takes_updates(period) else [])
        rc = collect(["-m", "ladder.collect", "--players", players, "--pool", pool_dir, "--subs", host / "subs",
                      "--arena", arena, "--workers", "15", *mask, "--every", f"{every:g}", *gates],
                     a.out / "collect.log")
        clog = a.out / "collect.log"
        tail = [l for l in clog.read_text(encoding="utf-8", errors="replace").splitlines() if l] if clog.exists() else []
        res["steps"]["collect"] = {"ok": rc == 0, "exit": rc, "last": tail[-2:] if tail else []}
        return finish(rc == 0 and res["steps"]["report"].get("ok", False))
    except KeyboardInterrupt:
        res["steps"][step] = {"ok": False, "error": "stopped by Ctrl+C"}
        return finish(False)
    except (Exception, SystemExit) as e:
        res["steps"][step] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        return finish(False)


if __name__ == "__main__":
    sys.exit(main())
