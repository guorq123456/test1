"""Collecting the players' submissions during the period's window (A50, player prompt v2 交法): the host's loop on
Salem's PC (PLAN 8b).

    python -m ladder.collect --players C:\\claude\\ladder-players --pool C:\\claude\\ladder-host\\pool
        --subs C:\\claude\\ladder-host\\subs --arena C:\\claude\\ladder-arena --workers 15 --mask 0x3FC3FC
        [--every 120] [--gates after|now --frozen FROZEN.json --delta D --gates-out C:\\claude\\ladder-host\\gates]
        [--after-deadline]

Until the window's deadline (ARENA/public/window.json): each player's submit\\ folder is looked at; a sub-directory
not collected yet (by player, path and a stamp of its files: names, sizes, times), whose files haven't changed for
`settle` seconds and which really is inside that player's own submit\\ folder, is received. One at a time, the
players in turn (the one after the last served goes first), a player's own in the order they were first seen. Each
is received in a fresh process (`python -m ladder.submit receive`: the peek check runs the strategy in the host's
process, and a strategy must not be able to change the checks for the receipts after it), while holding the arena's
lock: the machine runs one thing at a time (D2), and the compute check wants the E-cores to itself (A44). The player's
receipts folder is written again after each (`submit.deliver`); an accepted new deck enters the pool at once
(`submit.admit`, deck period).

The deadline: at that moment (checked before every step, and by a timer while a step is running) the listing of the
submit folders is taken and written down (SUBS/collect.jsonl), keyed by the window's field and deadline, so a restarted
collector keeps it. What was there then is still collected afterwards, unless its files changed after the deadline;
anything that comes or changes later is not (prompt: 到点以后放进去的不算), and is listed at the end. A collector
started after the deadline without that listing refuses, unless told `--after-deadline` (then what is there now
counts as there by the deadline). A collected directory whose files change before the deadline is another submission
(it gets its own receipt).

Updates (strategy period) go to the gate (`python -m ladder.submit gate`, the period's delta and frozen field):
`--gates now` right after their receipt, also under the lock (the arena waits); `--gates after` (default) all of
them after the deadline, in receipt order. After the deadline every accepted update of the period not gated yet is
gated in either mode, and every accepted deck of the period not admitted yet is admitted (a collector cut off between
the two steps). The loop ends after that, with one line "这一期收完…": the pool's ladder starts only then (RUNBOOK §4).

Failures: a directory whose receive fails (no receipt in the ledger) is tried again `retry` seconds later; after the
second failure it is given up, written down, and the player gets "<name>-没收成.md" in their receipts folder. Three
failures in a row stop the loop (most likely the host's side). A failed admit or gate is written down and not tried
again. Everything is in SUBS/collect.jsonl (host side); the host reports it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = HERE.parents[2]
for _p in (str(LADDER), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SETTLE = 30.0          # seconds a directory's files must stay unchanged before it is taken (one being copied in)
TRIES = 2              # receive attempts on one directory before it is given up
STOP_AFTER = 3         # failures in a row that stop the loop


class CollectError(Exception):
    pass


def stamp(d: Path) -> str:
    """The directory's files: relative name, size and modification time; another stamp is another submission."""
    rows = []
    for p in sorted(Path(d).rglob("*")):
        if p.is_file():
            st = p.stat()
            rows.append(f"{p.relative_to(d).as_posix()}|{st.st_size}|{st.st_mtime_ns}")
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()[:16]


def python_cmd() -> tuple[list, dict]:
    """The interpreter for a child command and what its environment needs. In a Windows venv sys.executable is the
    venv's python.exe, a launcher that starts the real interpreter as a second process (D5, 11-23 review): start the
    real one, telling it the venv through __PYVENV_LAUNCHER__, as multiprocessing does (popen_spawn_win32)."""
    base = getattr(sys, "_base_executable", None) or sys.executable
    if os.name == "nt" and os.path.normcase(base) != os.path.normcase(sys.executable):
        return [base], {"__PYVENV_LAUNCHER__": sys.executable}
    return [sys.executable], {}


def _log_path(subs: Path) -> Path:
    return Path(subs) / "collect.jsonl"


def _note(subs: Path, rec: dict):
    from ladder.arena import _append
    _append(_log_path(subs), dict(rec, time=datetime.now(timezone.utc).isoformat(timespec="seconds")))


def listing(players: Path) -> dict:
    """Every player's submit\\ sub-directory now: {(player, resolved dir): (stamp, newest file time)}. A link out of the
    player's own submit\\ folder is not followed (11-23 review)."""
    from ladder.arena import FOLDER
    out = {}
    for player, py in FOLDER.items():
        box = Path(players) / py / "submit"
        try:
            if not box.is_dir():
                continue
            root = box.resolve()
            entries = sorted(box.iterdir())
        except OSError:
            continue
        for d in entries:
            try:
                if not d.is_dir():
                    continue
                r = d.resolve()
                if r.parent != root:
                    continue
                times = [p.stat().st_mtime for p in d.rglob("*") if p.is_file()]
                out[(player, str(r))] = (stamp(d), max(times, default=d.stat().st_mtime))
            except OSError:                       # moved or changed while looked at: the next round sees it
                continue
    return out


class Collector:
    def __init__(self, players, pool, subs, arena, workers=15, mask=None, gates="after", frozen=None, delta=None,
                 gates_out=None, gate_seeds=(88500000, 89000000), settle=SETTLE, receive=None, gate=None,
                 receive_args=(), out=print, after_deadline=False, retry=120.0):
        from ladder.arena import _jsonl, _read
        from ladder.pool import Pool, period_kind
        from ladder.runner import one_core_type
        from ladder.submit import ledger
        self.players, self.pool, self.subs, self.arena = Path(players), Path(pool), Path(subs), Path(arena)
        self.workers, self.mask, self.gates, self.settle = workers, mask, gates, settle
        self.frozen, self.delta, self.gates_out, self.gate_seeds = frozen, delta, gates_out, tuple(gate_seeds)
        self.receive_args, self._out, self.after_deadline = list(receive_args), out, after_deadline
        self.receive_fn = receive or self._receive_process
        self.gate_fn = gate or self._gate_process
        # the host's own settings, checked once here (11-23 review: a missing --mask failed every directory)
        one_core_type(mask)
        self.subs.mkdir(parents=True, exist_ok=True)
        ledger(self.subs)
        self.window = _read(self.arena / "public" / "window.json")
        self.period = Pool(self.pool).period
        self.kind = period_kind(self.period)
        if self.window["period"] != self.period:
            raise SystemExit(f"练习场开的是第 {self.window['period']} 期，池子在第 {self.period} 期：先开这一期的练习场")
        if gates not in ("after", "now"):
            raise SystemExit("--gates 只能是 after 或 now")
        if self.kind == "strategy" and (frozen is None or delta is None or gates_out is None
                                        or not Path(frozen).is_file()):
            raise SystemExit("策略期要给 --frozen（这一期的冻结池文件）、--delta、--gates-out")
        self.deadline = datetime.fromisoformat(self.window["deadline"]).timestamp()
        self.final = None                         # the listing taken at the deadline (kept from an earlier run)
        for l in _jsonl(_log_path(self.subs)):
            if l.get("ev") == "deadline" and l.get("field") == self.window["field"] \
                    and l.get("deadline") == self.window["deadline"]:
                self.final = {(p_, d): (st, 0.0) for p_, d, st in l["dirs"]}
        self._final_lock = threading.Lock()
        self.first_seen, self.last_player, self.in_row = {}, None, 0
        self.retry, self.failed_at, self.waiting = retry, {}, False

    def out(self, text: str):
        try:
            self._out(text)
        except Exception:                         # noqa: BLE001 - a console that can't show it mustn't stop the loop
            pass

    # --- the ledgers -------------------------------------------------------------------------------------------
    def _log(self) -> list[dict]:
        from ladder.arena import _jsonl
        return _jsonl(_log_path(self.subs))

    def _receipt_for(self, d: str, st: str):
        from ladder.submit import ledger
        return next((l for l in reversed(ledger(self.subs)) if l.get("ev") == "receipt" and l.get("dir") == d
                     and l.get("collect_stamp") == st), None)

    def done(self) -> set:
        """(player, dir, stamp) collected, given up or changed after the deadline; also a receipt the ledger has but
        the collect log doesn't (cut off between the two)."""
        from ladder.submit import ledger
        out = {(l["player"], l["dir"], l["stamp"]) for l in self._log() if l.get("ev") == "dir"}
        out |= {(l["player"], l["dir"], l["collect_stamp"]) for l in ledger(self.subs)
                if l.get("ev") == "receipt" and l.get("collect_stamp")}
        return out

    def tries(self, key) -> int:
        return sum(1 for l in self._log() if l.get("ev") == "error" and (l["player"], l["dir"], l["stamp"]) == key)

    # --- the steps (each run in a fresh process by default) ------------------------------------------------------
    def _env(self):
        return dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT), str(LADDER)]), PYTHONUTF8="1",
                    PYTHONIOENCODING="utf-8", **python_cmd()[1])

    def _run(self, cmd: list) -> subprocess.CompletedProcess:
        return subprocess.run([*python_cmd()[0], "-m", "ladder.submit", *cmd], cwd=str(LADDER), env=self._env(),
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def _common(self) -> list:
        return ["--workers", str(self.workers)] + (["--mask", hex(self.mask)] if self.mask is not None else [])

    def _receive_process(self, player: str, d: str, st: str) -> dict:
        r = self._run(["receive", d, "--player", player, "--pool", str(self.pool), "--out", str(self.subs),
                       "--stamp", st, *self._common(), *self.receive_args])
        rec = self._receipt_for(d, st)
        if rec is None:
            raise CollectError(f"exit {r.returncode}: " + ((r.stderr or "") + (r.stdout or ""))[-3000:])
        return rec

    def _gate_process(self, rid: str) -> dict:
        from ladder.submit import ledger
        r = self._run(["gate", str(self.subs), "--receipt", rid, "--pool", str(self.pool), "--frozen",
                       str(self.frozen), "--seeds", *map(str, self.gate_seeds), "--out", str(self.gates_out),
                       "--delta", str(self.delta), *self._common()])
        line = next((l for l in reversed(ledger(self.subs)) if l.get("ev") == "gated" and l.get("receipt") == rid),
                    None)
        if line is None:
            raise CollectError(f"exit {r.returncode}: " + ((r.stderr or "") + (r.stdout or ""))[-3000:])
        return line

    def _deliver(self):
        from ladder.submit import deliver
        try:
            got = deliver(self.subs, self.pool, self.players)
        except Exception as e:                    # noqa: BLE001 - written down; the loop goes on
            got = {"*": f"{type(e).__name__}: {e}"}
        bad = {k: v for k, v in got.items() if isinstance(v, str)}
        if bad:
            _note(self.subs, {"ev": "deliver-failed", "players": bad})
            self.out(f"  回执写不进去：{bad}（记在 collect.jsonl）")

    def _admit(self, rid: str):
        from ladder import submit
        try:
            mid = submit.admit(self.subs, rid, self.pool)
            self.out(f"  {rid} 入池 {mid}")
        except BaseException as e:                # noqa: BLE001
            if isinstance(e, KeyboardInterrupt):
                raise
            _note(self.subs, {"ev": "admit-failed", "receipt": rid, "error": f"{type(e).__name__}: {e}"})
            self.out(f"  {rid} 入池出错，记在 collect.jsonl，主持方要看")

    def _gate(self, rid: str) -> bool:
        try:
            res = self.gate_fn(rid)
            self.out(f"  {rid} 检验：{res.get('verdict')}")
            return True
        except BaseException as e:                # noqa: BLE001
            if isinstance(e, KeyboardInterrupt):
                raise
            _note(self.subs, {"ev": "gate-failed", "receipt": rid, "error": f"{type(e).__name__}: {e}"[-3000:]})
            self.out(f"  {rid} 检验出错，记在 collect.jsonl，主持方要看")
            return False

    def _gave_up(self, player: str, d: str, st: str, why: str):
        from ladder.arena import FOLDER
        from ladder.submit import box_name
        _note(self.subs, {"ev": "dir", "player": player, "dir": d, "stamp": st, "gave_up": why[-3000:]})
        try:
            box = self.players / FOLDER[player] / "receipts"
            box.mkdir(parents=True, exist_ok=True)
            name = box_name(Path(d).name, "没收成", set())
            (box / f"{name}-没收成.md").write_text(
                f"# {Path(d).name}：没收成\n\n收这一份的时候主持方这边出错了，不是查出来的问题，也没有回执编号。主持方会看。"
                "这一份不算交过；工作时间没到的话，可以把它换个目录名再放进 submit\\ 一次。\n", encoding="utf-8")
        except OSError:
            pass

    def take(self, player: str, d: str, st: str):
        from ladder.arena import _lock, _unlock
        key = (player, d, st)
        self.last_player = player
        lock = _lock(self.arena)
        t0 = time.time()
        try:
            try:
                rec = self.receive_fn(player, d, st)
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException as e:            # noqa: BLE001
                why = f"{type(e).__name__}: {e}"
                _note(self.subs, {"ev": "error", "player": player, "dir": d, "stamp": st, "error": why[-3000:]})
                self.in_row += 1
                self.failed_at[key] = time.time()
                if self.tries(key) >= TRIES:
                    self._gave_up(player, d, st, why)
                    self.out(f"{player} {Path(d).name}：收了 {TRIES} 次都出错，放弃，记在 collect.jsonl，主持方要看")
                else:
                    self.out(f"{player} {Path(d).name}：收的时候出错，下一轮再试（collect.jsonl）")
                if self.in_row >= STOP_AFTER:
                    raise SystemExit(f"连着 {self.in_row} 份都出错，多半是主持方这边的问题：停下来，看 collect.jsonl")
                return None
            self.in_row = 0
            _note(self.subs, {"ev": "dir", "player": player, "dir": d, "stamp": st, "receipt": rec["id"],
                              "verdict": rec["verdict"], "seconds": round(time.time() - t0)})
            self.out(f"{player} {Path(d).name} → {rec['id']} {rec['verdict']}")
            self._deliver()                       # the receipt first, before an admit or a gate
            if rec["verdict"] == "收下" and rec.get("kind") == "deck":
                self._admit(rec["id"])
            if rec["verdict"] == "收下" and rec.get("kind") == "update" and self.gates == "now":
                self._gate(rec["id"])
        finally:
            _unlock(lock)
        self._deliver()
        return rec

    # --- after a cut-off: what the earlier run left half done ----------------------------------------------------
    def pending_admits(self) -> list:
        from ladder.submit import ledger
        lines = ledger(self.subs)
        admitted = {l["receipt"] for l in lines if l.get("ev") == "admit"}
        failed = {l["receipt"] for l in self._log() if l.get("ev") == "admit-failed"}
        return [l["id"] for l in lines if l.get("ev") == "receipt" and l.get("period") == self.period
                and l.get("kind") == "deck" and l.get("verdict") == "收下" and l["id"] not in admitted | failed]

    def pending_gates(self) -> list:
        from ladder.submit import ledger
        lines = ledger(self.subs)
        gated = {l["receipt"] for l in lines if l.get("ev") == "gated"}
        failed = {l["receipt"] for l in self._log() if l.get("ev") == "gate-failed"}
        return [l["id"] for l in lines if l.get("ev") == "receipt" and l.get("period") == self.period
                and l.get("kind") == "update" and l.get("verdict") == "收下" and l["id"] not in gated | failed]

    def recover(self):
        from ladder.arena import _lock, _unlock
        for rid in self.pending_admits():
            lock = _lock(self.arena)
            try:
                self._admit(rid)
            finally:
                _unlock(lock)

    # --- the loop -----------------------------------------------------------------------------------------
    def _at_deadline(self):
        with self._final_lock:
            if self.final is not None:
                return
            final = listing(self.players)
            for _ in range(3):
                try:
                    _note(self.subs, {"ev": "deadline", "period": self.period, "field": self.window["field"],
                                      "deadline": self.window["deadline"],
                                      "dirs": [[p_, d, st] for (p_, d), (st, _) in sorted(final.items())]})
                    break
                except OSError:
                    time.sleep(1)
            self.final = final

    def next_item(self):
        """The next directory to take, or None. Before the deadline: settled, not done. After it: in the deadline
        listing, not done, its files unchanged since (a changed one is written down as late, once). One that failed
        waits `retry` seconds (self.waiting says there is one waiting)."""
        done, now, final = self.done(), time.time(), self.final
        cur = listing(self.players)
        if final is not None:
            cands = []
            for (p_, d), (st, _) in final.items():
                if (p_, d, st) in done:
                    continue
                if cur.get((p_, d), (None,))[0] != st:
                    _note(self.subs, {"ev": "dir", "player": p_, "dir": d, "stamp": st,
                                      "late": "its files changed (or it went) after the deadline"})
                    self.out(f"{p_} {Path(d).name}：截止以后又改过（或拿走了），不收")
                    continue
                cands.append((p_, d, st))
        else:
            cands = [(p_, d, st) for (p_, d), (st, newest) in cur.items()
                     if (p_, d, st) not in done and now - newest >= self.settle]
        for k in cands:
            self.first_seen.setdefault(k, now)
        ready = [k for k in cands if now - self.failed_at.get(k, float("-inf")) >= self.retry]
        self.waiting = len(ready) < len(cands)
        cands = ready
        if not cands:
            return None
        from ladder.arena import FOLDER
        order = list(FOLDER)
        if self.last_player in order:
            i = order.index(self.last_player) + 1
            order = order[i:] + order[:i]
        for player in order:
            mine = sorted((k for k in cands if k[0] == player), key=lambda k: (self.first_seen[k], Path(k[1]).name))
            if mine:
                return mine[0]
        return None

    def run(self, every: float = 120.0) -> dict:
        if self.final is None and time.time() > self.deadline and not self.after_deadline:
            raise SystemExit("工作时间已经截止，截止那一刻收提交的循环没在跑，不知道哪些目录是截止前放的。"
                             "查过文件时间、确定现在看到的都算，再加 --after-deadline")
        self.recover()
        timer = threading.Timer(max(0.0, self.deadline - time.time()), self._at_deadline)
        timer.daemon = True
        timer.start()
        n = 0
        try:
            while True:
                if time.time() >= self.deadline:
                    self._at_deadline()
                item = self.next_item()
                if item is None:
                    if self.final is not None and not self.waiting:
                        break
                    left = self.deadline - time.time()
                    time.sleep(max(0.2, min(every, left if left > 0 else every, self.retry)))
                    continue
                if self.take(*item):
                    n += 1
        finally:
            timer.cancel()
        self.recover()
        g = bad = 0
        for rid in self.pending_gates():
            from ladder.arena import _lock, _unlock
            lock = _lock(self.arena)
            try:
                ok = self._gate(rid)
            finally:
                _unlock(lock)
            self._deliver()
            g, bad = g + ok, bad + (not ok)
        late = sorted(Path(d).name for (p_, d), (st, _) in listing(self.players).items()
                      if (p_, d, st) not in self.done() and (p_, d) not in self.final)
        late += sorted(Path(l["dir"]).name for l in self._log() if l.get("ev") == "dir" and l.get("late")
                       and (l["player"], l["dir"]) in self.final)
        self.out(f"这一期收完：收 {n} 份" + (f"，检验 {g} 份" if g else "") + (f"，检验出错 {bad} 份" if bad else "") +
                 (f"；到点以后才放进来或又改过、没收的：{'、'.join(late)}" if late else "") + "。可以开天梯了")
        return {"received": n, "gated": g, "gate_errors": bad, "late": late}


def main(argv=None):
    for s in (sys.stdout, sys.stderr):           # a redirected console is cp1252 on Windows (ENVIRONMENT pitfall 1)
        try:
            s.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:                         # noqa: BLE001
            pass
    ap = argparse.ArgumentParser(prog="python -m ladder.collect")
    ap.add_argument("--players", required=True)
    ap.add_argument("--pool", required=True)
    ap.add_argument("--subs", required=True)
    ap.add_argument("--arena", required=True)
    ap.add_argument("--workers", type=int, default=15)
    ap.add_argument("--mask", type=lambda x: int(x, 0))
    ap.add_argument("--every", type=float, default=120.0)
    ap.add_argument("--gates", default="after", choices=("after", "now"))
    ap.add_argument("--frozen")
    ap.add_argument("--delta", type=float)
    ap.add_argument("--gates-out")
    ap.add_argument("--after-deadline", action="store_true")
    ap.add_argument("--smoke-games", type=int, help="dry runs and tests only: passed to every receive")
    ap.add_argument("--smoke-seeds", type=int, nargs=2, metavar=("LO", "HI"),
                    help="dry runs and tests only: the smoke games' seed range for every receive")
    ap.add_argument("--gate-seeds", type=int, nargs=2, metavar=("LO", "HI"), default=(88500000, 89000000),
                    help="dry runs only: the gates' seed range (default: the formal gate segment)")
    a = ap.parse_args(argv)
    extra = (["--smoke-games", str(a.smoke_games)] if a.smoke_games else []) + \
        (["--smoke-seeds", *map(str, a.smoke_seeds)] if a.smoke_seeds else [])
    c = Collector(a.players, a.pool, a.subs, a.arena, workers=a.workers, mask=a.mask, gates=a.gates,
                  frozen=a.frozen, delta=a.delta, gates_out=a.gates_out, after_deadline=a.after_deadline,
                  gate_seeds=tuple(a.gate_seeds), receive_args=extra,
                  out=lambda s: print(f"{time.strftime('%H:%M:%S')} {s}", flush=True))
    print(json.dumps(c.run(a.every), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
