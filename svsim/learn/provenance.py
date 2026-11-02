"""Models bound to the simulator version (process item 2, analysis/process/PROCESS.md).

A trained model is only as good as the rules it learned on. At training time a model's info gets a "provenance"
record: the git commit, the RULES HASH (sha256 over the rules files, `rules_files()`), and a short digest per file.

At load, a model whose hash differs from the current rules warns once per process, with the number of rules files
that changed. A model without a record warns as 未登记 and is not refused. The gates (tools.herogate,
tools.deckgate) refuse a stale model unless --allow-stale is given (`guard`).

    python -m svsim.learn.provenance list [DIR]           # each model: commit, current / stale / 未登记
    python -m svsim.learn.provenance backfill MODEL ...   # stamp a legacy model when no rules file changed since
    python -m svsim.learn.provenance hash                 # the current rules hash
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# svsim/cards modules that are not game rules: deck codes, deck lists, the demo decks
NOT_RULES = {"deckcode.py", "decks.py", "demo.py"}


def rules_files(root: Path | None = None) -> list[Path]:
    """The files whose contents are the simulator's rules: the engine (svsim/core), the card scripts and the pool
    loader (svsim/cards/*.py less NOT_RULES), and the card tables the engine loads (svsim/cards/data/*.json).
    The one place to change what counts."""
    root = root or ROOT
    files = list((root / "svsim" / "core").glob("*.py"))
    files += [p for p in (root / "svsim" / "cards").glob("*.py") if p.name not in NOT_RULES]
    files += list((root / "svsim" / "cards" / "data").glob("*.json"))
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def file_digests(root: Path | None = None) -> dict:
    """{relative path: first 16 hex of the file's sha256} over rules_files()."""
    root = root or ROOT
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in rules_files(root)}


def rules_hash(root: Path | None = None) -> str:
    """sha256 over the rules files sorted by path, each fed in as its path, a NUL, its bytes and a NUL."""
    root = root or ROOT
    h = hashlib.sha256()
    for p in rules_files(root):
        h.update(p.relative_to(root).as_posix().encode() + b"\0")
        h.update(p.read_bytes() + b"\0")
    return h.hexdigest()


_CURRENT: dict = {}


def current() -> tuple:
    """(rules hash, file digests) of this checkout, computed once per process."""
    if not _CURRENT:
        _CURRENT["v"] = (rules_hash(), file_digests())
    return _CURRENT["v"]


def _git(*args, root: Path | None = None) -> str | None:
    root = root or ROOT
    try:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def _rel_rules(root: Path | None = None) -> list[str]:
    root = root or ROOT
    return [p.relative_to(root).as_posix() for p in rules_files(root)]


def stamp(root: Path | None = None) -> dict:
    """The provenance record for a model trained now."""
    root = root or ROOT
    h, files = rules_hash(root), file_digests(root)
    dirty = _git("status", "--porcelain", "--", *_rel_rules(root), root=root)
    return {"commit": _git("rev-parse", "HEAD", root=root), "rules_dirty": bool(dirty), "rules_hash": h,
            "rules_files": files, "stamped": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def ensure(info: dict) -> dict:
    """`info` with a provenance record (stamped now if it has none); the same dict."""
    if not isinstance(info.get("provenance"), dict):
        info["provenance"] = stamp()
    return info


def status(info: dict | None) -> tuple:
    """("current" | "stale" | "未登记", the rules files that differ: changed, added or removed)."""
    rec = (info or {}).get("provenance")
    if not isinstance(rec, dict) or "rules_hash" not in rec:
        return "未登记", []
    h, files = current()
    if rec["rules_hash"] == h:
        return "current", []
    old = rec.get("rules_files") or {}
    changed = sorted(k for k in set(old) | set(files) if old.get(k) != files.get(k))
    return "stale", changed


# what the plan calls them: a stale model is 「待复测」 (to be re-measured)
LABEL = {"current": "current", "stale": "待复测 (stale)", "未登记": "未登记"}

_WARNED: set = set()


def check_loaded(path, info: dict | None) -> str:
    """At load: a warning line on stderr once per model and process when it is stale or 未登记; never raises."""
    try:
        st, changed = status(info)
    except Exception as e:                    # a check must never break a load (the trainer's Pyodide build too)
        st, changed = "unknown", [repr(e)]
    key = str(path)
    if st != "current" and key not in _WARNED:
        _WARNED.add(key)
        name = Path(str(path)).name
        if st == "stale":
            print(f"警告：模型 {name} 与当前规则不符（{len(changed)} 个规则文件已改）", file=sys.stderr, flush=True)
        elif st == "未登记":
            print(f"警告：模型 {name} 未登记（训练时没有记录规则版本）", file=sys.stderr, flush=True)
        else:
            print(f"警告：模型 {name} 的规则版本无法检查（{changed[0]}）", file=sys.stderr, flush=True)
    return st


# --- the gates --------------------------------------------------------------------------------------------------

_MODEL_OPTIONS = re.compile(r"(?:^|\+)(setnet|puct)=([^+]+)")


def models_in_spec(spec: str) -> list[str]:
    """The model paths an arena spec loads: setnet=PATH and puct=PATH[:C[:T]]."""
    out = []
    for kind, val in _MODEL_OPTIONS.findall(spec or ""):
        out.append(val.split(":")[0] if kind == "puct" else val)
    return out


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.exists() or p.is_absolute() else ROOT / p


def model_info(path) -> dict | None:
    """The info dict of a model .npz (None when it has none)."""
    import numpy as np
    with np.load(_resolve(str(path)), allow_pickle=False) as z:
        return json.loads(str(z["info"])) if "info" in z.files else None


def guard(specs, allow_stale: bool = False, out=print) -> list:
    """For a gate: check every model the specs load. A stale model stops the run (SystemExit) unless allow_stale;
    未登记 only warns. Prints one line per model and, when allow_stale lets a stale model through, says so."""
    rows, stale = [], []
    for spec in specs:
        for m in models_in_spec(spec):
            if any(r[0] == m for r in rows):
                continue
            st, changed = status(model_info(m))
            rows.append((m, st, changed))
            if st == "stale":
                stale.append(m)
    for m, st, changed in rows:
        extra = f"，{len(changed)} 个规则文件已改" if st == "stale" else ""
        out(f"模型规则版本：{Path(m).name} {LABEL.get(st, st)}{extra}")
    if stale and not allow_stale:
        raise SystemExit(f"模型与当前规则不符：{', '.join(Path(m).name for m in stale)}"
                         "（--allow-stale 可放行，并记入输出）")
    if stale:
        out(f"--allow-stale：放行 {len(stale)} 个与当前规则不符的模型")
    return rows


# --- backfill and list ------------------------------------------------------------------------------------------

def training_commit(path: Path, info: dict | None) -> tuple:
    """(commit, how): the model's own record when it has one, else the commit that first added the file."""
    rec = (info or {}).get("provenance") or {}
    if rec.get("commit"):
        return rec["commit"], "the model's record"
    for key in ("commit", "git_commit"):
        if (info or {}).get(key):
            return info[key], f"the model's info '{key}'"
    added = _git("log", "--diff-filter=A", "--format=%H", "--", str(path.relative_to(ROOT)) if path.is_relative_to(ROOT)
                 else str(path))
    if added:
        return added.splitlines()[-1], "the commit that first added the file"
    return None, "unknown (the file is not in git)"


def rules_changed_since(commit: str) -> list[str]:
    """The rules files changed in commits after `commit` up to HEAD (git log commit..HEAD), or None if git fails."""
    out = _git("log", "--format=", "--name-only", f"{commit}..HEAD", "--", *_rel_rules())
    if out is None:
        return None
    return sorted(set(line for line in out.splitlines() if line.strip()))


def backfill(path, write: bool = True) -> tuple:
    """Stamp a legacy model with the current hash when no rules file changed since its training commit and the
    rules files are clean; (ok, message). The arrays are rewritten unchanged."""
    import numpy as np
    p = _resolve(str(path))
    info = model_info(p)
    if info is None:
        return False, f"{p.name}: no info to stamp"
    st, _ = status(info)
    if st != "未登记":
        return False, f"{p.name}: already {st}"
    commit, how = training_commit(p, info)
    if commit is None:
        return False, f"{p.name}: training commit {how}"
    changed = rules_changed_since(commit)
    if changed is None:
        return False, f"{p.name}: git log {commit[:9]}..HEAD failed"
    if changed:
        return False, f"{p.name}: {len(changed)} rules files changed since {commit[:9]} ({how}): {', '.join(changed[:5])}"
    if _git("status", "--porcelain", "--", *_rel_rules()):
        return False, f"{p.name}: the rules files have uncommitted changes"
    rec = stamp()
    rec.update(commit=commit, backfilled=True, backfill_from=how)
    info["provenance"] = rec
    if write:
        with np.load(p, allow_pickle=False) as z:
            arrays = {k: z[k] for k in z.files}
        arrays["info"] = np.array(json.dumps(info))
        tmp = p.with_name(p.name + ".tmp.npz")
        np.savez(tmp, **arrays)
        tmp.replace(p)
    return True, f"{p.name}: stamped from {commit[:9]} ({how})"


def list_models(folder) -> list:
    rows = []
    for p in sorted(Path(folder).glob("*.npz")):
        try:
            info = model_info(p)
        except Exception as e:
            rows.append((p.name, "?", f"unreadable: {e!r}", []))
            continue
        st, changed = status(info)
        commit = ((info or {}).get("provenance") or {}).get("commit") or "-"
        rows.append((p.name, commit[:9], st, changed))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("dir", nargs="?", default="analysis/scaling/models")
    bf = sub.add_parser("backfill")
    bf.add_argument("models", nargs="+")
    bf.add_argument("--dry-run", action="store_true")
    sub.add_parser("hash")
    args = ap.parse_args()
    if args.cmd == "hash":
        print(rules_hash(), len(rules_files()), "files")
    elif args.cmd == "list":
        rows = list_models(_resolve(args.dir))
        for name, commit, st, changed in rows:
            tail = f"  changed: {', '.join(changed)}" if changed else ""
            print(f"{name}\t{commit}\t{LABEL.get(st, st)}{tail}")
        counts = {s: sum(1 for r in rows if r[2] == s) for s in ("current", "stale", "未登记")}
        print(f"# {len(rows)} models: " + ", ".join(f"{k} {v}" for k, v in counts.items()) + f"; rules hash {current()[0][:16]}")
    else:
        for m in args.models:
            ok, msg = backfill(m, write=not args.dry_run)
            print(("OK " if ok else "-- ") + msg)


if __name__ == "__main__":
    main()
