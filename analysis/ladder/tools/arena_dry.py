"""A dry run of one player period on Salem's computer, before the players come in (PLAN 8a/8b; A50, A52-A55): the
host's commands of RUNBOOK 每期 §1-§4 for a deck period, as the RUNBOOK gives them (`python -m ladder....`), on a
throwaway pool, ledger, arena and player folders under RUNS/<commit>. What only the real machine can show: the file
locks (msvcrt), the cycle counter and the E-core mask, Chinese folder names, the console's encoding (step 9), the
workers importing a player's code (spawn), the collection loop's own processes. Child commands start the real
interpreter, not the venv's launcher (D5).

    python analysis/ladder/tools/arena_dry.py --runs C:\\claude\\ladder-runs\\arena-dry [--workers 23]

 1. lock: tools/check_lock.py (the locked files as locked).
 2. pool: create (seeds 93409200-93409399), the seven baseline lists with the default strategy, 40 games, advance
    with --force (they are short of 2000) to period 1 (a deck period); freeze P1.
 3. arena: snapshot --code subs\\code, open for 8 minutes (20000 games, all cores).
 4. collect: the collection loop in its own process (--every 10; 15 workers on the E-cores; smoke seeds
    93409700-93409999). Before the deadline fable-ultracode hands in a deck (精灵1: the default strategy's own code through the
    interface) and a broken one (坏的: notes.md missing); fable a deck (龙族1: 95 search iterations, so its games go
    their own way); 15 s before the deadline fable-ultracode hands in 超越者1 (taken after the deadline), 3 s after it fable hands
    in 晚了 (while 超越者1 is being taken: the loop lists what is late when it ends). Meanwhile fable-ultracode practises in
    this process (vs, 200 games against the Forest members; then arena ladder, 100 games, 1 repeat), sharing the
    arena's lock with the loop; fable-ultracode's practice seeds are patched to 93409400-93409699 here (never fable-ultracode's real practice
    segment). Expected: 4 received (3 accepted, 1 refused), 晚了 late, receipts in each one's own folder only, 3
    admitted members, the final line 「这一期收完」; on the PC the compute ratio of 精灵1 and 超越者1 (the default's
    own code: the shadow replay, LD-56, recomputes exactly what they did) within 0.97-1.03. Then `submit deliver`
    again: nothing changes.
 5. ladder: 150 pool games on all cores (LADDER_EXTRA_PATH = subs\\code; the host's key).
 6. audit: every pool game replayed in clean processes; none may fail.
 7. formal: `arena formal --period 1`: members.json and runs\\F1 for fable-ultracode and fable, each holding only games of their own
    members; one formal game replays; resume and --same-as on F1 are refused.
 8. compute noise (A52, LD-55, LD-56, LD-57): tools/compute_noise.py on the E-cores, 40 sets of 10 pairs with the
    default on another seed, then 20 sets with tools/standins.py Adaptive (a cost that changes with the game), then
    20 sets with tools/standins.py Planner (A68: the turn-start budget used through turn_start, about submit.TURN_K
    default turns a turn), seeds drawn from 92796000-92799999 minus every cloud run's
    (probe/compute-noise-used-seeds-*.txt) and the earlier runs': the spread of both ways of comparing (the twin
    games, and the shadow replay receive uses now, with and without the twin's calibration), what a step costs in a
    game against in a shadow on the E-cores, and for the planner the turn rule's two numbers (in_turn, turn_start_q)
    and which rule a receipt passes it on. A dry run, not the PC's step-0 measurement of the two pools' noise
    (tools/compute_noise.py run on its own, with its own registered seeds).
 9. console: the players' commands (`arena field`, `arena replay`, `submit precheck`) as a player's agent runs them,
    output piped, without PYTHONUTF8 / PYTHONIOENCODING (cp1252 on Windows): UTF-8 JSON, exit 0 (precheck on 坏的:
    exit 1, ok false, notes.md named in Chinese).
10. pool compute: ladder.compute_audit on period 1's pool games (LD-57): the three admitted members each measured
    on their own pool games, calibrated by baseline-against-baseline games; on the PC 精灵1 and 超越者1 (the
    default's own code) within 0.9-1.1.

Seeds: host probe second segment 93409200-93409999 (SEEDS.md) and the host measurement 92796000-92799999; --cloud
(a small rehearsal in the container) 93404000-93404999 instead. The games say nothing about strength. Writes
RUNS/<commit>/ (all the folders, commands.log, collect.log, summary.json) and a copy of the summary at
RUNS/summary.json. A folder that is there already is refused: every run starts clean.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(LADDER))
sys.path.insert(0, str(ROOT))

DEFAULT = "bot:mcts:100+plan"
SEEDS = {"pc": {"pool": (93409200, 93409400), "practice": (93409400, 93409700), "smoke": (93409700, 93410000),
                "noise": (92796000, 92800000)},
         # --cloud: a rehearsal in the cloud container on its own seeds (host probe second segment, SEEDS.md)
         "cloud": {"pool": (93404000, 93404200), "practice": (93404200, 93404500), "smoke": (93404500, 93404800),
                   "noise": (93404800, 93405000)}}
WINDOW_MIN = 8
E_CORES = "0x3FC3FC"

SAME = '''
from ladder.interface import PlayerStrategy


class Mine(PlayerStrategy):
    """The default strategy through the interface, nothing changed."""
'''

CRAFT_NAMES = {1: "精灵", 2: "皇家护卫", 3: "巫师", 4: "龙族", 5: "梦魇", 6: "主教", 7: "超越者"}

FEWER = '''
from ladder.interface import PlayerStrategy


class Mine(PlayerStrategy):
    """{n} search iterations a decision instead of 100."""

    def search(self, pos):
        return {{"iterations": {n}}}
'''


def lists():
    out = []
    for line in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            name, code = line.strip().split("|")
            out.append((name, code))
    return out


def commit() -> str:
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True,
                               text=True).stdout.strip()
        return h.strip() + ("-dirty" if dirty else "")
    except OSError:
        return "nogit"


def env(extra: dict | None = None) -> dict:
    from ladder.collect import python_cmd
    return dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT), str(LADDER)]), PYTHONUTF8="1",
                PYTHONIOENCODING="utf-8", **python_cmd()[1], **(extra or {}))


def exe() -> list:
    from ladder.collect import python_cmd
    return python_cmd()[0]                      # the real interpreter in a Windows venv: no launcher process (D5)


def py(args: list, log: Path, extra_env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """One RUNBOOK command, from analysis/ladder, as `py -m ...` (or a tool script)."""
    cmd = [*exe(), *args]
    r = subprocess.run(cmd, cwd=str(LADDER), env=env(extra_env), capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n$ {' '.join(map(str, args))}\nexit {r.returncode}\n{r.stdout}{r.stderr}")
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, args[:3]))} exit {r.returncode}: {(r.stderr or r.stdout)[-1500:]}")
    return r


def last_json(text: str):
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return None


def make_sub(d: Path, deck: str, member: str, src: str, notes: bool = True):
    d.mkdir(parents=True)
    (d / "submission.json").write_text(json.dumps({"type": "新卡组", "member": member, "class": "Mine", "deck": deck},
                                                  ensure_ascii=False), encoding="utf-8")
    (d / "strategy.py").write_text(src, encoding="utf-8")
    if notes:
        (d / "notes.md").write_text("1. 空跑。\n2. ...\n3. ...\n4. ...\n5. ...\n6. 预测：中游。\n", encoding="utf-8")
    (d / "evidence.md").write_text("空跑，没有证据。\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--workers", type=int, default=23)
    ap.add_argument("--window-min", type=float, default=WINDOW_MIN)
    ap.add_argument("--mask", default=E_CORES, help="the E-cores, for what compares compute (A44); 'none' off Windows")
    ap.add_argument("--noise-sets", type=int, help="default: 40 on the PC, 2 with --cloud (its seed range holds 20)")
    ap.add_argument("--cloud", action="store_true",
                    help="a rehearsal in the cloud: its own seeds, no mask, small sizes (set LADDER_KEY_FILE to a "
                         "throwaway key)")
    args = ap.parse_args()
    seeds = SEEDS["cloud" if args.cloud else "pc"]
    # sizes: the PC's, or a small rehearsal in the container (4 cores)
    # (fable's deck searches less than the default: 95 of 100 on the PC; 50 in the container, whose 3 smoke games on
    # busy vCPUs can read a 0.95 strategy as 1.3, LD-55)
    n = (dict(base=10, vs=20, lad=10, tail=5, pool=30, smoke=["--smoke-games", "3"], fewer=50, noise=2,
              noise_workers=3) if args.cloud
         else dict(base=40, vs=200, lad=100, tail=50, pool=150, smoke=[], fewer=95, noise=40, noise_workers=15))
    if args.noise_sets is not None:
        n["noise"] = args.noise_sets
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:                                            # noqa: BLE001
            pass
    runs = Path(args.runs)
    out = runs / commit()
    if out.exists():
        raise SystemExit(f"{out} is there already: every dry run starts clean (move it away first)")
    out.mkdir(parents=True)
    log = out / "commands.log"
    mask = [] if args.mask == "none" or args.cloud else ["--mask", args.mask]
    host, arena, players = out / "host", out / "arena", out / "players"
    pool, subs = host / "pool", host / "subs"
    summary = {"commit": out.name, "started": datetime.now().isoformat(timespec="seconds"), "steps": {}}

    def step(name, fn):
        t = time.time()
        try:
            res = fn()
            summary["steps"][name] = {"ok": bool(res.pop("ok", True)) if isinstance(res, dict) else True,
                                      "seconds": round(time.time() - t), **(res if isinstance(res, dict) else {})}
        except Exception as e:                                       # noqa: BLE001
            summary["steps"][name] = {"ok": False, "seconds": round(time.time() - t), "error": repr(e)[-2000:],
                                      "trace": traceback.format_exc()[-3000:]}
        print(name, json.dumps(summary["steps"][name], ensure_ascii=False)[:600], flush=True)
        _write(out, runs, summary)
        return summary["steps"][name]["ok"]

    L = lists()

    # 1. lock
    def lock():
        r = py([str(HERE / "check_lock.py")], log, check=False)
        return {"ok": r.returncode == 0, "said": r.stdout.strip()[-300:]}
    step("1 lock", lock)

    # 2. pool
    def make_pool():
        py(["-m", "ladder.pool", "create", str(pool), "--seeds", *map(str, seeds["pool"]), "--rng-seed", "1",
            "--note", "arena dry run (tools/arena_dry.py)"], log)
        for name, code in L:
            py(["-m", "ladder.pool", "enter", str(pool), "--deck", code, "--strategy", DEFAULT, "--owner", "baseline",
                "--note", name], log)
        py(["-m", "ladder.pool", "ladder", str(pool), "--games", str(n["base"]), "--workers", str(args.workers)], log)
        py(["-m", "ladder.pool", "advance", str(pool), "--force", "dry run: baselines short of 2000"], log)
        (host / "frozen").mkdir(parents=True, exist_ok=True)
        py(["-m", "ladder.evaluator", "freeze", str(pool), "--out", str(host / "frozen" / "P1.json")], log)
        from ladder.pool import Pool
        p = Pool(pool)
        return {"ok": p.period == 1 and len(p.active()) == 7, "period": p.period, "members": len(p.active())}
    if not step("2 pool", make_pool):
        return finish(out, runs, summary)

    # 3. arena
    def open_arena():
        py(["-m", "ladder.arena", "snapshot", str(pool), "--arena", str(arena), "--code", str(subs / "code")], log)
        r = py(["-m", "ladder.arena", "open", str(arena), "--hours", str(args.window_min / 60), "--games", "20000",
                "--workers", str(args.workers)], log)
        w = last_json(r.stdout) or json.loads((arena / "public" / "window.json").read_text(encoding="utf-8"))
        return {"deadline": w["deadline"], "key_made": (arena / "host" / "arena.key").exists()}
    if not step("3 arena", open_arena):
        return finish(out, runs, summary)
    window = json.loads((arena / "public" / "window.json").read_text(encoding="utf-8"))
    deadline = datetime.fromisoformat(window["deadline"]).timestamp()

    # 4. collect, with practice alongside
    def collect():
        for who in ("fable-ultracode", "fable"):
            (players / who / "submit").mkdir(parents=True)
        clog = open(out / "collect.log", "w", encoding="utf-8")
        loop = subprocess.Popen([*exe(), "-m", "ladder.collect", "--players", str(players), "--pool", str(pool),
                                 "--subs", str(subs), "--arena", str(arena), "--workers", "15", *mask, "--every", "10",
                                 "--smoke-seeds", *map(str, seeds["smoke"]), *n["smoke"]],
                                cwd=str(LADDER), env=env(), stdout=clog, stderr=subprocess.STDOUT)
        make_sub(players / "fable-ultracode" / "submit" / "精灵1", L[0][1], "精灵一号", SAME)
        make_sub(players / "fable-ultracode" / "submit" / "坏的", L[6][1], "超越者一号", SAME, notes=False)
        make_sub(players / "fable" / "submit" / "龙族1", L[3][1], "龙族一号", FEWER.format(n=n["fewer"]))
        practice = {}

        def late():
            # one 15 s before the deadline (in the deadline listing, not settled: taken after the deadline), then
            # 晚了 3 s after it, while that one is being taken (the loop lists the late ones when it ends)
            time.sleep(max(0.0, deadline - 15 - time.time()))
            make_sub(players / "fable-ultracode" / "submit" / "超越者1", L[6][1], "超越者一号", SAME)
            time.sleep(max(0.0, deadline + 3 - time.time()))
            make_sub(players / "fable" / "submit" / "晚了", L[1][1], "皇家一号", SAME)
        t = threading.Thread(target=late)
        t.start()
        from ladder import arena as A
        A.PLAYER_SEEDS["fable-ultracode"] = seeds["practice"]                         # never fable-ultracode's real practice segment
        mine = players / "fable-ultracode" / "work" / "v1"
        make_sub(mine, L[0][1], "精灵一号", SAME)
        try:
            t0 = time.time()
            practice["vs"] = A.run_vs(arena, "fable-ultracode", mine, n["vs"], craft_zh="精灵", rng_seed=1)
            practice["vs_seconds"] = round(time.time() - t0)
            t0 = time.time()
            practice["ladder"] = A.run_ladder(arena, "fable-ultracode", mine, games=n["lad"], tail=n["tail"], repeats=1,
                                              rng_seed=2)
            practice["ladder_seconds"] = round(time.time() - t0)
        except Exception as e:                                       # noqa: BLE001
            practice["error"] = repr(e)[-1500:]
        t.join()
        try:
            code = loop.wait(timeout=45 * 60)
        except subprocess.TimeoutExpired:
            loop.kill()
            code = "killed after 45 min"
        clog.close()
        text = (out / "collect.log").read_text(encoding="utf-8", errors="replace")
        res = last_json(text)
        from ladder import submit
        recs = [l for l in submit.ledger(subs) if l.get("ev") == "receipt"]
        got = sorted((r["player"], Path(r["dir"]).name, r["verdict"]) for r in recs)
        admitted = [l for l in submit.ledger(subs) if l.get("ev") == "admit"]
        boxes = {who: sorted(p.name for p in (players / who / "receipts").iterdir())
                 if (players / who / "receipts").exists() else [] for who in ("fable-ultracode", "fable")}
        before = {who: {p.name: p.read_bytes() for p in (players / who / "receipts").iterdir()}
                  for who in ("fable-ultracode", "fable") if (players / who / "receipts").exists()}
        py(["-m", "ladder.submit", "deliver", str(subs), "--pool", str(pool), "--players", str(players)], log)
        after = {who: {p.name: p.read_bytes() for p in (players / who / "receipts").iterdir()}
                 for who in ("fable-ultracode", "fable") if (players / who / "receipts").exists()}
        want = [("fable", "龙族1", "收下"), ("fable-ultracode", "坏的", "拒收"), ("fable-ultracode", "精灵1", "收下"), ("fable-ultracode", "超越者1", "收下")]
        noise = []
        if args.cloud:      # 3 smoke games on the container's jittery vCPUs: a refusal on compute alone is its noise
            for r in recs:
                if r["verdict"] == "拒收" and Path(r["dir"]).name in ("精灵1", "超越者1", "龙族1") and r.get("reasons") \
                        and all(x.startswith("[算力]") for x in r["reasons"]):
                    noise.append(Path(r["dir"]).name)
            got = [(a, b, "收下" if b in noise else c) for a, b, c in got]
        ok = (code == 0 and res == {"received": 4, "gated": 0, "gate_errors": 0, "late": ["晚了"]} and got == want
              and len(admitted) == 3 - len(noise)
              and boxes == {"fable-ultracode": ["坏的.md", "状态.md", "精灵1.md", "超越者1.md"],
                                                   "fable": ["状态.md", "龙族1.md"]}
              and "这一期收完" in text and before == after and "error" not in practice
              and practice.get("vs", {}).get("games") == n["vs"] and practice.get("vs", {}).get("errors") == 0)
        # 精灵1 and 超越者1 are the default's own code on the default's seeds: the shadow (LD-56) recomputes exactly
        # what they computed, so on the PC their ratio is 1 up to the counter (the container's vCPUs jitter more)
        same = [r.get("compute_ratio") for r in recs if Path(r["dir"]).name in ("精灵1", "超越者1")]
        if not args.cloud:
            ok = ok and len(same) == 2 and all(x is not None and 0.97 <= x <= 1.03 for x in same)
        seconds = [(l.get("dir"), l.get("seconds")) for l in _jsonl(subs / "collect.jsonl") if "seconds" in l]
        return {"ok": ok, "exit": code, "result": res, "receipts": got, "admitted": len(admitted), "boxes": boxes,
                "deliver_again_same": before == after, "cloud_compute_noise": noise,
                "compute_ratio": {Path(r["dir"]).name: r.get("compute_ratio") for r in recs},
                "compute": {Path(r["dir"]).name: r.get("compute") for r in recs},
                "receive_seconds": seconds, "practice": practice}
    if not step("4 collect", collect):
        return finish(out, runs, summary)

    # 5. ladder
    def ladder():
        t0 = time.time()
        py(["-m", "ladder.pool", "ladder", str(pool), "--games", str(n["pool"]), "--workers", str(args.workers)], log,
           extra_env={"LADDER_EXTRA_PATH": str(subs / "code")})
        games = [json.loads(l) for l in (pool / "games.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        p1 = [g for g in games if (g.get("labels") or {}).get("period") == 1]
        bad = [g["id"] for g in p1 if g.get("result") not in ("normal", "draw")]
        return {"ok": len(p1) == n["pool"] and not bad, "games": len(p1), "not_normal": bad[:20],
                "games_per_hour": round(n["pool"] / max(1e-9, time.time() - t0) * 3600)}
    step("5 ladder", ladder)

    # 6. audit
    def audit():
        r = py(["-m", "ladder.audit", str(pool / "games.jsonl"), "--events", str(pool / "events.jsonl"),
                "--workers", str(args.workers), "--out", str(out / "audit.json")], log, check=False)
        return {"ok": r.returncode == 0, "said": last_json(r.stdout)}
    step("6 audit", audit)

    # 7. formal
    def formal():
        py(["-m", "ladder.arena", "formal", str(arena), "--pool", str(pool), "--subs", str(subs), "--period", "1"], log)
        from ladder import arena as A
        from ladder.pool import Pool
        p = Pool(pool)
        games = [json.loads(l) for l in (pool / "games.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        res, ok = {}, True
        mids = {}
        for l in _jsonl(subs / "submissions.jsonl"):
            if l.get("ev") == "admit":
                mids.setdefault(l["player"], []).append(l["mid"])
        for who, n in (("fable-ultracode", 2), ("fable", 1)):
            me = arena / "players" / who
            members = json.loads((me / "members.json").read_text(encoding="utf-8"))["members"]
            views = _jsonl(me / "runs" / "F1" / "games.jsonl")
            mine = mids.get(who, [])
            want = sum(g["labels"]["members"].count(m) for g in games for m in mine
                       if (g.get("labels") or {}).get("period") == 1)            # every game of the period, as formal
            anon = {p.members[m].anon for m in mine}
            leak = [v["game"] for v in views if v.get("member") not in anon]
            res[who] = {"members": [(m["member"], m["in_pool"]) for m in members], "views": len(views),
                        "expected": want, "leaks": leak[:10]}
            ok &= (len(mine) == n and len(members) == n and {m["id"] for m in members} == anon
                   and len(views) == want and not leak)
        jia = _jsonl(arena / "players" / "fable-ultracode" / "runs" / "F1" / "games.jsonl")
        if jia:
            A.replay(arena, "fable-ultracode", "F1", jia[0]["game"])
            res["replay"] = True
            refused = []
            for fn in (lambda: A.run_resume(arena, "fable-ultracode", "F1", jia[0]["game"], 0,
                                            [players / "fable-ultracode" / "work" / "v1"], 1),
                       lambda: A.run_vs(arena, "fable-ultracode", players / "fable-ultracode" / "work" / "v1", 1, same_as="F1")):
                try:
                    fn()
                    refused.append(False)
                except A.ArenaError as e:
                    refused.append(str(e)[:80])
            res["refused"] = refused
            ok &= all(refused)
        else:
            ok = False
        return {"ok": ok, **res}
    step("7 formal", formal)

    # 8. compute noise on the E-cores: the default with another seed (40 sets), then a stand-in whose cost changes
    # with the game (tools/standins.py Adaptive, half as many sets; LD-57), then a planner through turn_start
    # (tools/standins.py Planner, half as many; A68: the turn rule's two numbers), each on seeds the others never drew
    def noise():
        res = {}
        for standin, sets, rs in (("seed", n["noise"], "2"), ("adaptive", max(1, n["noise"] // 2), "5"),
                                  ("plan", max(1, n["noise"] // 2), "7")):
            name = "compute-noise" if standin == "seed" else f"compute-noise-{standin}"
            done = sorted((LADDER / "probe").glob("compute-noise-used-seeds*.txt")) + \
                sorted(out.glob("compute-noise*.games.jsonl"))
            r = py([str(HERE / "compute_noise.py"), "--sets", str(sets), "--seeds", *map(str, seeds["noise"]),
                    "--workers", str(n["noise_workers"]), *mask, "--standin", standin,
                    *[x for f in done for x in ("--exclude", str(f))],
                    "--rng-seed", rs, "--out", str(out / f"{name}.json")], log, check=False)
            body = json.loads((out / f"{name}.json").read_text(encoding="utf-8")) if r.returncode == 0 else None
            if body is None:
                return {"ok": False, "standin": standin, "said": (r.stderr or r.stdout)[-1500:]}
            res[standin] = {k: body[k] for k in ("pairs", "identical_games", "default_step", "shadow", "shadow_raw",
                                                 "game_over_shadow", "twins", "twins_diverged", "turn",
                                                 "calibration_parts")}
        return {"ok": True, **res}
    step("8 compute noise", noise)

    # 9. the players' commands on a console that isn't UTF-8 (a player's agent pipes the output: cp1252 on Windows)
    def console():
        plain = {k: v for k, v in env().items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
        if args.cloud:
            plain["PYTHONIOENCODING"] = "cp1252"                      # what the PC's console does, in the container
        jia = _jsonl(arena / "players" / "fable-ultracode" / "runs" / "F1" / "games.jsonl")
        cmds = {"field": ["-m", "ladder.arena", "field", str(arena), "--player", "fable-ultracode"],
                "precheck": ["-m", "ladder.submit", "precheck", str(players / "fable-ultracode" / "submit" / "坏的")]}
        if jia:
            cmds["replay"] = ["-m", "ladder.arena", "replay", str(arena), "--player", "fable-ultracode", "--run", "F1",
                              "--game", jia[-1]["game"]]
        res, ok = {}, bool(jia)
        for name, c in cmds.items():
            r = subprocess.run([*exe(), *c], cwd=str(LADDER), env=plain, capture_output=True)
            text = r.stdout.decode("utf-8", errors="replace")
            with open(log, "a", encoding="utf-8") as f:
                f.write(f"\n$ (plain console) {' '.join(c)}\nexit {r.returncode}\n{text}"
                        f"{r.stderr.decode('utf-8', errors='replace')}")
            try:
                body = json.loads(text)
                parsed = True
            except ValueError:
                body, parsed = None, False
            # 坏的 is broken on purpose (notes.md missing): precheck says so in Chinese and exits 1
            want = 1 if name == "precheck" else 0
            said = name != "precheck" or (isinstance(body, dict) and body.get("ok") is False
                                          and any("notes.md" in x for x in body.get("problems", [])))
            res[name] = {"exit": r.returncode, "utf8_json": parsed, "expected_exit": want}
            ok &= r.returncode == want and parsed and said
        return {"ok": ok, **res}
    step("9 console", console)

    # 10. the compute cap on the pool's own games (ladder.compute_audit, LD-57)
    def pool_compute():
        r = py(["-m", "ladder.compute_audit", str(pool), "--period", "1", "--workers", str(n["noise_workers"]), *mask,
                "--out", str(out / "compute-audit.json")], log, check=False)
        body = json.loads((out / "compute-audit.json").read_text(encoding="utf-8")) \
            if (out / "compute-audit.json").exists() else None
        if body is None:
            return {"ok": False, "said": (r.stderr or r.stdout)[-1500:]}
        got = {m["craft"]: m for m in body["members"]}
        ok = r.returncode == 0 and not body["problems"]
        if not args.cloud:     # 精灵1 and 超越者1 are the default's own code: about 1 (30 games on mixed cores)
            ok = ok and set(got) == {1, 4, 7} and body["calibration"].get("game_over_replay") is not None \
                and all(got[c]["ratio"] is not None and 0.9 <= got[c]["ratio"] <= 1.1 for c in (1, 7))
        return {"ok": ok, "calibration": body["calibration"], "replayed": body["replayed"],
                "members": {CRAFT_NAMES.get(c, c): {k: m[k] for k in ("games", "ratio", "interval90", "over")}
                            for c, m in sorted(got.items())}}
    step("10 pool compute", pool_compute)
    return finish(out, runs, summary)


def _jsonl(p: Path) -> list:
    if not Path(p).exists():
        return []
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def _write(out: Path, runs: Path, summary: dict):
    text = json.dumps(summary, ensure_ascii=False, indent=1)
    (out / "summary.json").write_text(text, encoding="utf-8")
    shutil.copyfile(out / "summary.json", runs / "summary.json")


def finish(out: Path, runs: Path, summary: dict):
    summary["finished"] = datetime.now().isoformat(timespec="seconds")
    summary["all_ok"] = all(s["ok"] for s in summary["steps"].values()) and len(summary["steps"]) == 10
    _write(out, runs, summary)
    print("ALL OK" if summary["all_ok"] else "NOT ALL OK", flush=True)
    return 0 if summary["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
