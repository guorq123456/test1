"""The simulator environments of the formal pool (S25, 11-24): which simulator plays which periods.

A balance patch changes cards, so a game replays (RUNBOOK 每期 §4, ladder.audit) only on the simulator it was played
on. An environment is the fingerprint of the whole simulator (the tracked files of svsim/ ending .py, .json, .npz,
.txt; text read with CRLF as LF, as tools/check_lock.py reads the locked files), from the first period it plays.

- tools/open_period.py refuses to open a period on a simulator that isn't that period's, and at the first period of a
  new environment seals the logs (HOST/audit/sealed.json: each log's length and sha256 at that moment). Every line
  in them was replayed by the close before, on the simulator it was played on.
- tools/close_period.py refuses to close a period on a simulator that isn't its own, checks every sealed log is still
  byte for byte what was sealed (a change holds the period), and gives ladder.audit only what was written after the
  latest seal.

    python analysis/ladder/tools/environments.py [PERIOD]      the fingerprint here, and the environment of PERIOD
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SUFFIXES = (".py", ".json", ".npz", ".txt")

ENVS = [
    {"from": 0, "name": "base-2026-11-21", "fingerprint": "6318e5f2cf1c5063",
     "what": "the simulator of phases 0-1 and period 1 (branch claude/forest2-pilot 75b7bc3)"},
    {"from": 2, "name": "patch-2026-11-26", "fingerprint": "84dcce58294e6e85", "notes": "docs/patch-2026-11-26.md",
     "what": "the balance patch announced 11-24 for the 11-26 maintenance: six cards (S25: from period 2)"},
]


def _files(root: Path) -> list[str]:
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "svsim"], capture_output=True, text=True,
                             check=True).stdout.split("\n")
        files = [f for f in out if f.strip()]
    except (OSError, subprocess.CalledProcessError):
        files = [p.relative_to(root).as_posix() for p in (root / "svsim").rglob("*")
                 if p.is_file() and "__pycache__" not in p.parts]
    return sorted(f for f in files if f.endswith(SUFFIXES))


def fingerprint(root: Path = REPO) -> str:
    h = hashlib.sha256()
    for f in _files(root):
        b = (root / f).read_bytes() if (root / f).exists() else b"missing"
        if not f.endswith(".npz"):
            b = b.replace(b"\r\n", b"\n")
        h.update(f.encode() + b"\0" + hashlib.sha256(b).digest())
    return h.hexdigest()[:16]


def env_of(period: int) -> dict:
    return [e for e in ENVS if e["from"] <= period][-1]


def check(period: int, root: Path = REPO) -> dict:
    """The environment of `period`, if the simulator here is it; stops otherwise."""
    env, got = env_of(period), fingerprint(root)
    if got != env["fingerprint"]:
        known = {e["fingerprint"]: e["name"] for e in ENVS}
        raise SystemExit(f"模拟器不是第 {period} 期的环境：要 {env['name']}（{env['fingerprint']}），这里是 "
                         f"{known.get(got, '没登记过的')}（{got}）：先查清楚这台电脑上的代码是哪一版")
    return env


def host_logs(host: Path) -> list[Path]:
    """Every game log the close's audit reads, as it is now."""
    return sorted(p for p in [host / "pool" / "games.jsonl", host / "pool" / "events.jsonl",
                              *(host / "anchors").glob("games-P*.jsonl"),
                              *(host / "gates").glob("*/games.jsonl"),
                              *(host / "puzzles").glob("*/games.jsonl")] if p.is_file())


def _sha(path: Path, n: int) -> str:
    h, left = hashlib.sha256(), n
    with open(path, "rb") as f:
        while left > 0:
            b = f.read(min(left, 1 << 20))
            if not b:
                break
            h.update(b)
            left -= len(b)
    return h.hexdigest()


def seals(host: Path) -> list[dict]:
    p = host / "audit" / "sealed.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def seal(host: Path, period: int) -> dict | None:
    """At the first period of a new environment (once): every log's length and sha256 now. Between periods only
    (the opener, before the window opens): nothing writes them then."""
    env = env_of(period)
    have = seals(host)
    if env["from"] != period or any(s["env"] == env["name"] for s in have):
        return None
    files = {p.relative_to(host).as_posix(): {"bytes": p.stat().st_size, "sha256": _sha(p, p.stat().st_size)}
             for p in host_logs(host)}
    s = {"env": env["name"], "period": period, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "files": files}
    (host / "audit").mkdir(parents=True, exist_ok=True)
    (host / "audit" / "sealed.json").write_text(json.dumps(have + [s], ensure_ascii=False, indent=1),
                                                encoding="utf-8")
    return s


def audit_inputs(host: Path, logs: list[Path], events: Path, work: Path) -> dict:
    """What ladder.audit reads after the latest seal: each sealed log is checked (its sealed part unchanged), and
    only what was written after it is copied into `work` to be replayed; a log not sealed is read whole.
    Returns {"logs": [...], "events": path or None, "changed": [sealed logs that changed], "sealed": env or None}."""
    have = seals(host)
    if not have:
        return {"logs": logs, "events": events if events.exists() else None, "changed": [], "sealed": None}
    last = have[-1]
    work.mkdir(parents=True, exist_ok=True)
    changed, out = [], []

    def cut(p: Path):
        rel = p.relative_to(host).as_posix()
        s = last["files"].get(rel)
        if s is None:
            return p
        size = p.stat().st_size if p.exists() else -1
        if size < s["bytes"] or _sha(p, s["bytes"]) != s["sha256"]:
            changed.append(rel)
            return None
        if size == s["bytes"]:
            return None
        t = work / rel.replace("/", "__")
        with open(p, "rb") as f:
            f.seek(s["bytes"])
            t.write_bytes(f.read())
        return t
    for rel in last["files"]:                     # a sealed log gone or shortened
        p = host / rel
        if not p.exists():
            changed.append(rel)
    for p in logs:
        if p.exists():
            got = cut(p)
            if got is not None:
                out.append(got)
    ev = cut(events) if events.exists() else None
    return {"logs": out, "events": ev, "changed": sorted(set(changed)), "sealed": last["env"]}


if __name__ == "__main__":
    fp = fingerprint()
    print(json.dumps({"fingerprint": fp, "known": [e["name"] for e in ENVS if e["fingerprint"] == fp],
                      **({"period": int(sys.argv[1]), "env": env_of(int(sys.argv[1]))["name"]}
                         if len(sys.argv) > 1 else {})}, ensure_ascii=False))
