"""Submissions (phase 2, item 2.3): the entry point, and the checks a submission passes before it goes anywhere.

    python -m ladder.submit precheck DIR [--deck-of-member CODE]      # format, deck, code; no games, counts nothing
    python -m ladder.submit receive  DIR --player 甲 --pool POOLDIR --out SUBDIR [--workers 15] --mask 0x3FC3FC
    python -m ladder.submit admit    SUBDIR --receipt S-0001 --pool POOLDIR   # an accepted new deck enters the pool
    python -m ladder.submit status   SUBDIR --pool POOLDIR --player 甲         # classes done / missing this period

A submission is one directory (public/submit.md is the players' description):
    submission.json  {"type": "新卡组" | "打法更新" | "公共题", "member": the player's name for the member,
                      "class": the strategy class, "deck": deck code (新卡组, 公共题),
                      "change": what changed, "prediction": expected gap and why (打法更新),
                      "route": {"steps": N, "step": k, "stop_if": "...", "route_of": "S-xxxx"} (multi-step, A33),
                      "resubmit_of": "S-xxxx", "since": "..." (an update after a failed gate on the same version, A46),
                      "puzzle": puzzle id (公共题)}
    strategy.py      the strategy: one module, the class named by "class", a subclass of ladder.interface
                     .PlayerStrategy
    notes.md         the strategy notes (the six items of the player prompt)
    evidence.md      the practice-arena evidence (against whom, how many games, what came out)

`receive` runs every check, writes a receipt (accepted / refused, with every reason) and appends one line to
SUBDIR/submissions.jsonl, accepted or not. The ledger is append-only. Slots follow Salem's S5 (11-22): every deck
period each player submits one new deck for every class (an accepted one fills its class; a refused one leaves it
open, A35); strategy updates are not limited; a 公共题 uses no slot. A declared multi-step route is gated once, at
its end, against the version before its first step (A33).

The checks (PHASE2-DESIGN.md 2.3):
- format: the four files, the fields the type needs;
- deck (新卡组): legal by the simulator's own rules (svsim.cards.decks.validate: 40 cards, 3 of a name, one class
  plus Neutral, Rotation as the simulator has it: A7), every card scripted (runner.unscripted), one class;
- slots: no cap on a player's members (S6), at most 2 members per list, one new deck per class per deck
  period (S5), updates not limited; new decks only in a deck period, updates only in a strategy period;
- code, read (no running): imports only from the allowed modules, none of the names and attributes that reach
  files, the network, other processes, frames or the interpreter (static, by the syntax tree);
- code, loaded in a separate process with an audit hook (PEP 578) that refuses files, sockets, processes, ctypes
  and the garbage collector's object lists, and one short game against the default strategy there;
- smoke: SMOKE_GAMES games against the default strategy, with the baseline lists; no crash, illegal move or timeout;
- determinism: two of those games replayed decision by decision;
- compute: per-step compute of the submission against the default strategy in the same seat, same seeds; above
  1.08 a warning here (the gate refuses it: A25);
- peek: at a few decisions of two smoke games, the real state is replaced by another one the strategy can't tell
  from it (the opponent's unknown cards, both decks' order, the generator: base.vary_secrets); a strategy that only
  reads what the hooks give makes the same choice. A different choice is refused.
What these can't stop: code that is determined to reach the real state in the same Python process can (the audit
hook is not a security boundary), and under S4 the players run in Salem's own account. Spot reading of the code
covers the rest (plan 2.3).
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import random
import secrets
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent             # analysis/ladder/ladder
LADDER = HERE.parent                                # analysis/ladder
ROOT = HERE.parents[2]                              # the repository root (svsim)
for p in (str(ROOT), str(LADDER)):
    if p not in sys.path:
        sys.path.insert(0, p)

SUBMIT_VERSION = "submit-1"
TYPES = {"新卡组": "deck", "打法更新": "update", "公共题": "puzzle"}
FILES = ("submission.json", "strategy.py", "notes.md", "evidence.md")
UPDATES_PER_PERIOD = None           # Salem S5 (11-22): no limit on strategy updates (the plan's 3 is gone)
SMOKE_SEEDS = (88300000, 88400000)  # the host's part of the tuning range (SEEDS.md)
SMOKE_GAMES = 10
PEEK_GAMES, PEEK_POINTS = 2, 3
REPLAY_GAMES = 2
COMPUTE_WARN = 1.08
YOUR_VOIDS = ("the simulator changed in this worker during the game",   # what the strategy's own code voids
              "nothing ran on any clock", "the check after the game ran past", "worker died",  # (LD-45)
              "the strategies took more than", "strategy failed to load")    # LD-46: loading it, the twin loads fine
DEFAULT = "bot:mcts:100+plan"

from ladder.codecheck import (  # noqa: F401 - the code reader (LD-41); the names stay importable from here
    ALLOWED_LADDER,
    ALLOWED_TOP,
    BANNED_ATTRS,
    BANNED_NAMES,
    DENIED_PREFIXES,
    check_code,
    module_problem,
)


class Refused(Exception):
    pass


# --- the submission directory ----------------------------------------------------------------------------------

def read_dir(d: Path) -> dict:
    """The submission as a dict, or Refused with every format problem."""
    d = Path(d)
    problems = [f"缺文件 {f}" for f in FILES if not (d / f).is_file()]
    if problems:
        raise Refused(problems)
    try:
        meta = json.loads((d / "submission.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise Refused([f"submission.json 读不了：{e}"])
    if not isinstance(meta, dict):
        raise Refused(["submission.json 要是一个对象"])
    kind = TYPES.get(meta.get("type"))
    if kind is None:
        problems.append(f"类型要是 {'、'.join(TYPES)} 之一，不是 {meta.get('type')!r}")
    for k in ("member", "class"):
        if not isinstance(meta.get(k), str) or not meta[k].strip():
            problems.append(f"submission.json 缺 {k}")
    if kind in ("deck", "puzzle") and not isinstance(meta.get("deck"), str):
        problems.append("新卡组、公共题要有 deck（卡组代码）")
    if kind == "update":
        for k in ("change", "prediction"):
            if not isinstance(meta.get(k), str) or not meta[k].strip():
                problems.append(f"打法更新要写 {k}（改了什么 / 预期差多少、为什么）")
        r = meta.get("route")
        if r is not None:
            if not (isinstance(r, dict) and isinstance(r.get("steps"), int) and isinstance(r.get("step"), int)
                    and 1 <= r["step"] <= r["steps"] and r["steps"] >= 2):
                problems.append("route 要有 steps（总步数，至少 2）和 step（这是第几步）")
            elif r["step"] == 1 and not str(r.get("stop_if", "")).strip():
                problems.append("多步改法的第 1 步要写 stop_if（什么情况下中途停）")
            elif r["step"] > 1 and not str(r.get("route_of", "")).startswith("S-"):
                problems.append("多步改法第 2 步起要写 route_of（第 1 步的回执编号）")
            elif "stop" in r and not (r["stop"] is True and 1 < r["step"] < r["steps"]):
                problems.append("stop 只能写 true，而且只在第 2 步到倒数第 2 步之间（按 stop_if 中途停）")
    if kind == "update" and ("resubmit_of" in meta or "since" in meta):
        if not str(meta.get("resubmit_of", "")).startswith("S-") or not str(meta.get("since", "")).strip():
            problems.append("重交要同时写 resubmit_of（指回的那一次的回执编号）和 since（实质改了什么）")
    if kind == "puzzle" and not isinstance(meta.get("puzzle"), str):
        problems.append("公共题要写 puzzle（题号）")
    for f in ("notes.md", "evidence.md"):
        if not (d / f).read_text(encoding="utf-8", errors="replace").strip():
            problems.append(f"{f} 是空的")
    src = (d / "strategy.py").read_text(encoding="utf-8", errors="replace")
    if problems:
        raise Refused(problems)
    return {"meta": meta, "kind": kind, "src": src, "dir": d}


def check_deck(code: str) -> tuple[list, list[str]]:
    """(card ids, problems) for a deck code, by the simulator's own rules (A7)."""
    from ladder.runner import load_deck, unscripted
    from svsim.cards.decks import craft_of, validate
    from svsim.core.enums import Craft
    try:
        deck = load_deck(code)
    except Exception as e:                                  # an unknown card id or a malformed code
        return [], [f"卡组代码读不了（{type(e).__name__}: {e}）：有模拟器里没有的牌，或者代码写错了"]
    problems = list(validate(deck))
    if craft_of(deck) == Craft.NEUTRAL:
        problems.append("要有一个职业（全中立或混了两个职业都不行）")
    missing = unscripted(deck)
    if missing:
        from svsim.cards.pool import card
        problems.append("这些牌有效果却没有脚本，会按白板打：" + "、".join(sorted({card(i).name for i in missing})))
    return [c.card_id for c in deck], problems


# --- the ledger -----------------------------------------------------------------------------------------------

def ledger(subdir: Path) -> list[dict]:
    p = Path(subdir) / "submissions.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _append(subdir: Path, rec: dict):
    p = Path(subdir) / "submissions.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        from ladder.runner import jsonl  # noqa: PLC0415 - no import cycle at load
        f.write(jsonl(rec))
        f.flush()


def _members_of(lines: list[dict], player: str) -> dict:
    """The player's member names -> pool member ids, from the admit lines."""
    return {l["member"]: l["mid"] for l in lines if l.get("ev") == "admit" and l.get("player") == player}


def _craft(ids) -> int:
    from ladder import base
    from ladder.runner import load_deck
    return int(base.craft_of(load_deck(list(ids))))


def check_slots(sub: dict, player: str, pool, lines: list[dict]) -> tuple[list[str], dict]:
    """Slot and period problems, and what the receipt records about slots. Salem's S5 (11-22): every deck period
    each player submits one deck for every class; strategy updates are not limited. A refused deck leaves its
    class open for this period (A35)."""
    from ladder.pool import CRAFT_ZH, MAX_PER_LIST, MAX_PER_PLAYER, NEW_DECKS_PER_CLASS, list_key, period_kind
    kind, meta = sub["kind"], sub["meta"]
    pkind = period_kind(pool.period)
    problems, info = [], {"period": pool.period, "period_kind": pkind, "uses_slot": False}
    names = _members_of(lines, player)
    if kind == "deck":
        info["uses_slot"] = True                       # if accepted, it fills its class for this period
        if pkind != "deck":
            problems.append(f"第 {pool.period} 期是{ {'strategy': '策略期', 'baseline': '基线期'}.get(pkind, pkind)}，只有卡组期收新卡组")
        if sub.get("deck_ids"):
            craft = _craft(sub["deck_ids"])
            info["craft"] = craft
            taken = [l for l in lines if l.get("ev") == "receipt" and l.get("player") == player
                     and l.get("period") == pool.period and l.get("kind") == "deck" and l.get("verdict") == "收下"
                     and l.get("craft") == craft]
            if len(taken) >= NEW_DECKS_PER_CLASS:
                problems.append(f"这一期你的{CRAFT_ZH[craft]}已经交过一副、收下了（{taken[0]['id']}）；每个卡组期每个职业一副")
            key = list_key(sub["deck_ids"])
            same = [m for m in pool.active() if list_key(m.deck) == key]
            if len(same) >= MAX_PER_LIST:
                problems.append(f"同一张卡表池子里已经有 {len(same)} 个成员（最多 {MAX_PER_LIST} 个）")
        active = [m for m in pool.active() if m.owner == player]
        if MAX_PER_PLAYER is not None and len(active) >= MAX_PER_PLAYER:
            problems.append(f"池子里已经有你的 {len(active)} 个成员（最多 {MAX_PER_PLAYER} 个）")
        if meta["member"] in names:
            problems.append(f"成员名 {meta['member']!r} 你已经用过了")
    elif kind == "update":
        route = meta.get("route")
        if pkind != "strategy":
            problems.append(f"第 {pool.period} 期不是策略期，只有策略期收打法更新")
        if route is not None and route["step"] > 1:
            first = [l for l in lines if l.get("ev") == "receipt" and l.get("id") == route["route_of"]]
            if not first or first[0].get("player") != player or first[0].get("member") != meta["member"] \
                    or (first[0].get("route") or {}).get("step") != 1:
                problems.append(f"route_of {route['route_of']} 不是你这个成员一条多步改法的第 1 步")
            elif first[0]["route"]["steps"] != route["steps"]:
                problems.append("总步数和第 1 步说的不一样")
        mid = names.get(meta["member"])
        if mid is None or mid not in pool.members or not pool.members[mid].active:
            problems.append(f"你在池子里没有叫 {meta['member']!r} 的成员")
        else:
            info["mid"] = mid
            info["was"] = {"strategy": pool.members[mid].strategy, "version": pool.members[mid].version}
            sub["deck_ids"] = list(pool.members[mid].deck)
    return problems, info


def status(subdir: Path, pool_dir: Path, player: str) -> dict:
    """This period, for one player: the classes with an accepted new deck and the ones still missing (S5), the
    updates received."""
    from ladder.pool import CRAFT_ZH, Pool, period_kind
    pool = Pool(pool_dir)
    lines = [l for l in ledger(subdir) if l.get("ev") == "receipt" and l.get("player") == player
             and l.get("period") == pool.period]
    done = sorted({l["craft"] for l in lines if l.get("kind") == "deck" and l.get("verdict") == "收下"
                   and l.get("craft")})
    out = {"player": player, "period": pool.period, "kind": period_kind(pool.period),
           "updates": sum(1 for l in lines if l.get("kind") == "update"),
           "updates_accepted": sum(1 for l in lines if l.get("kind") == "update" and l.get("verdict") == "收下")}
    if out["kind"] == "deck":
        out["classes_done"] = [CRAFT_ZH[c] for c in done]
        out["classes_missing"] = [CRAFT_ZH[c] for c in sorted(CRAFT_ZH) if c not in done]
    return out


# --- the load check (a separate process) ------------------------------------------------------------------------

LOAD_BLOCK = {"subprocess.Popen", "os.system", "os.exec", "os.spawn", "os.posix_spawn", "os.startfile", "os.fork",
              "os.forkpty", "os.kill", "os.remove", "os.rename", "os.mkdir", "os.rmdir", "os.chmod", "os.putenv",
              "os.unsetenv", "gc.get_objects", "gc.get_referrers", "gc.get_referents", "sys._current_frames",
              "sys.settrace", "sys.setprofile", "builtins.input", "msvcrt.locking"}
LOAD_BLOCK_PREFIX = ("socket.", "ctypes.", "shutil.", "winreg.", "urllib.", "http.", "ftplib.", "smtplib.",
                     "webbrowser.", "_winapi.")


def _quote(why: str, n: int = 600) -> str:
    """An error for a receipt: whole when short; else a traceback's first line and its tail, where the player's frame
    and the exception are (LD-47: the head was the runner's own frames), any other text's head."""
    why = why.strip()
    if len(why) <= n:
        return why
    if "Traceback (most recent call last)" not in why:
        return why[:n] + "…"
    first = why.splitlines()[0][:100]
    return f"{first} … {why[-(n - len(first) - 3):]}"


def _load_main(argfile: str) -> int:
    """Runs in its own process: import the player's module behind an audit hook and play one short game."""
    args = json.loads(Path(argfile).read_text(encoding="utf-8"))
    import importlib.util
    import sysconfig
    import svsim.cards.library  # noqa: F401
    from svsim.tools.arena import make_agent  # noqa: F401   (the interface builds its agent with it)
    from ladder import base, interface, strategy as S
    from ladder.runner import load_deck
    try:
        import numpy  # noqa: F401
    except ImportError:
        pass
    base.baseline_lists()
    interface.PlayerStrategy(seed=1)                  # the default agent's own lazy imports, before the hook
    deck = load_deck(args["deck"])
    opp = load_deck(list(base.baseline_lists()[args["opp_craft"]]))
    path = Path(args["path"]).resolve()
    code_roots = [Path(p).resolve() for p in {sysconfig.get_paths()[k] for k in ("stdlib", "platstdlib", "purelib",
                                                                                  "platlib")}]
    code_roots += [(ROOT / "svsim").resolve(), (LADDER / "ladder").resolve()]
    seen = []

    path_dirs = {Path(x).resolve() for x in sys.path if x} | {path.parent}

    def _resolve(p):
        try:
            return Path(os.fsdecode(p)).resolve()
        except Exception:
            return None

    def allowed_read(p) -> bool:
        if isinstance(p, int):
            return True                                 # an already open descriptor
        q = _resolve(p)
        if q is None:
            return False
        if q == path or (q.parent == path.parent / "__pycache__" and q.name.startswith(path.stem + ".")):
            return True
        return q.suffix in (".py", ".pyc", ".pyd", ".so", ".dll") and any(r in q.parents for r in code_roots)

    def allowed_dir(p) -> bool:                         # the import machinery lists the directories it searches
        q = _resolve(p) if p is not None else Path.cwd()
        return q is not None and (q in path_dirs or any(q == r or r in q.parents for r in code_roots))

    def hook(event, a):
        why = None
        if event == "open":
            p, mode, flags = (list(a) + [None, None, None])[:3]
            if isinstance(p, str) and p.startswith("<") and p.endswith(">") and "/" not in p and "\\" not in p:
                raise FileNotFoundError(2, "no such file", p)   # 3.13 formatting a traceback opens '<unknown>':
                #                                                   no file there, and not the player's doing (LD-47)
            writing = (mode is not None and any(m in str(mode) for m in "wax+")) or \
                      (mode is None and isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
            if writing or not allowed_read(p):
                why = f"open {p!r} {mode or flags}"
        elif event in ("os.listdir", "os.scandir"):
            if not allowed_dir(a[0] if a else None):
                why = f"{event} {a[0] if a else ''!r}"
        elif event in LOAD_BLOCK or event.startswith(LOAD_BLOCK_PREFIX):
            why = event
        if why:
            seen.append(why)
            raise RuntimeError(f"提交校验：不许 {why}")

    from ladder.runner import jsonl                     # before the hook: it reads files
    sys.dont_write_bytecode = True
    sys.addaudithook(hook)
    out = {"ok": False, "blocked": seen}
    try:
        spec = importlib.util.spec_from_file_location("player_strategy", str(path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod                    # as an import does: dataclasses looks a class's module up
        spec.loader.exec_module(mod)                    # there for string annotations (LD-47)
        klass = getattr(mod, args["class"], None)
        if not (isinstance(klass, type) and issubclass(klass, interface.PlayerStrategy)
                and klass is not interface.PlayerStrategy):
            out["error"] = f"{args['class']} 不是 ladder.interface.PlayerStrategy 的子类"
        else:
            strat = klass(seed=args["seed"])
            seats = [strat, S.BotStrategy(seed=args["seed"] + 1)]
            winner, state, _ = S.play(deck, opp, seats, seed=args["game_seed"], max_turns=args.get("max_turns", 60))
            out.update(ok=True, winner=winner, turns=state.turn)
    except BaseException as e:                          # noqa: BLE001 (report anything, including SystemExit)
        import traceback
        out["error"] = "".join(traceback.format_exception(type(e), e, e.__traceback__, limit=6))[-3000:]
    out["blocked"] = list(seen)
    out["ok"] = out["ok"] and not seen
    sys.stdout.write("\nLOADCHECK " + jsonl(out))
    sys.stdout.flush()
    return 0


def load_check(path: Path, cls: str, deck, opp_craft: int, seed: int, game_seed: int, work: Path,
               timeout: float = 600.0) -> dict:
    work = Path(work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    argfile = work / "loadcheck-args.json"
    argfile.write_text(json.dumps({"path": str(Path(path).resolve()), "class": cls, "deck": deck, "opp_craft": opp_craft,
                                   "seed": seed, "game_seed": game_seed}), encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT), str(LADDER)]), PYTHONHASHSEED="0",
               PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run([sys.executable, "-m", "ladder.submit", "_load", str(argfile)], cwd=str(LADDER),
                           env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"载入检查超过 {timeout:.0f} 秒"}
    out, err = r.stdout or "", r.stderr or ""         # the player's code can write anything there (fifth pass)
    for line in reversed(out.splitlines()):
        if line.startswith("LOADCHECK "):
            try:
                return json.loads(line[len("LOADCHECK "):])
            except ValueError:
                break
    from ladder.runner import clean
    return {"ok": False, "error": clean("载入检查的进程没有交回结果：\n" + (err or out)[-3000:])}


# --- games ----------------------------------------------------------------------------------------------------

def _stage(sub: dict, rid: str, subdir: Path) -> str:
    """Copy the strategy where the workers import it; returns its runner spec."""
    code = Path(subdir) / "code"
    code.mkdir(parents=True, exist_ok=True)
    name = "sub_" + rid.replace("-", "")
    (code / f"{name}.py").write_text(sub["src"], encoding="utf-8")
    if str(code) not in sys.path:
        sys.path.insert(0, str(code))
    return f"py:{name}:{sub['meta']['class']}"


def gate_note(subdir: Path, rid: str, text: str) -> Path:
    """What the player is told about the gate of their receipt (RUNBOOK §3: handed back like the receipt). Only the
    player's own receipts: no gate ids, members' ids, opponents or seeds."""
    p = Path(subdir) / rid / "gate-note.md"
    p.write_text(f"# 检验结果 {rid}\n\n{text}\n", encoding="utf-8")
    return p


def code_fingerprint(src: str, cls: str) -> str:
    """The strategy's code without comments, layout or docstrings (its syntax tree), with the class it names: two
    submissions with the same fingerprint are the same change (red line: 同一个改动没有实质修改，不重新检验)."""
    import ast
    tree = ast.parse(src)
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
    return hashlib.sha256((cls + "\n" + ast.dump(tree, annotate_fields=False)).encode("utf-8")).hexdigest()


def _used_smoke_seeds(lines: list[dict]) -> set:
    return {s for l in lines if l.get("ev") == "receipt" for s in l.get("smoke_seeds", [])}


def smoke_jobs(spec: str, deck_ids: list, rid: str, rng: random.Random, used: set, games: int = SMOKE_GAMES,
               seeds: tuple[int, int] = SMOKE_SEEDS):
    """Pairs of jobs: the submission and the default strategy in the same seat, same seed, same strategy seeds,
    against the default strategy with the baseline lists (classes in turn)."""
    from ladder import base
    lists = base.baseline_lists()
    crafts = sorted(lists)
    jobs, played = [], []
    for i in range(games):
        while True:
            seed = rng.randrange(*seeds)
            if seed not in used:
                break
        used.add(seed)
        played.append(seed)
        seat = i % 2
        opp = list(lists[crafts[i % len(crafts)]])
        sseeds = [rng.randrange(1, 2 ** 31), rng.randrange(1, 2 ** 31)]
        for side, s in (("sub", spec), ("default", DEFAULT)):
            sides = [(list(deck_ids), s), (opp, DEFAULT)]
            if seat == 1:
                sides.reverse()
            jobs.append({"id": f"{rid}-smoke{i:03d}-{side}", "seed": seed, "first": None,
                         "decks": [d for d, _ in sides], "strategies": [x for _, x in sides],
                         "strategy_seeds": sseeds, "labels": {"side": side, "seat": seat}})
    return jobs, played


def peek_check(log: dict, seat: int, k: int, rng: random.Random) -> str:
    """Replay `log` with a fresh copy of the strategy at `seat`; at its k-th decision swap the real state for one it
    can't tell apart (base.vary_secrets) and ask again. 'same', 'differs', 'diverged' (an earlier decision
    differed: a determinism failure) or 'skipped'."""
    from ladder import base
    from ladder.runner import load_deck, make_strategy
    from svsim.cards.pool import collectible
    from svsim.core.actions import from_dict, to_dict
    from svsim.core.engine import apply, legal_actions
    from ladder import deal
    strat = make_strategy(log["strategies"][seat], log["strategy_seeds"][seat])
    _, state = deal.start(log)
    tracker = base.Tracker(state)
    others = [c.card_id for c in collectible(tracker.crafts[1 - seat])]
    n = 0
    for data in log["actions"]:
        if state.active == seat:
            if n == k:
                want = base.fingerprint(base.public_position(state, seat, tracker))
                state = base.vary_secrets(state, seat, tracker, rng, replacements=others)
                gc.collect()                                # the real state is gone; only the varied one is left
                pos = base.public_position(state, seat, tracker)
                if base.fingerprint(pos) != want:
                    return "skipped"
                got = json.loads(json.dumps(to_dict(strat.act(pos, legal_actions(state)))))
                return "same" if got == data else "differs"
            got = json.loads(json.dumps(to_dict(strat.act(base.public_position(state, seat, tracker),
                                                          legal_actions(state)))))
            if got != data:
                return "diverged"
            n += 1
        tracker.before(state)
        apply(state, from_dict(data))
        tracker.after(state)
    return "skipped"


def _mean_step(log: dict, seat: int) -> tuple[float, int]:
    xs = [c for s, c, _ in log.get("steps", []) if s == seat]
    return (sum(xs), len(xs))


# --- receive ---------------------------------------------------------------------------------------------------

def _sha(d: Path) -> dict:
    return {f: hashlib.sha256((d / f).read_bytes()).hexdigest() for f in FILES}


def precheck(d: Path, deck_of_member: str | None = None) -> dict:
    """What a player may run on their own: format, deck, the code read. No games, no ledger, no slots."""
    out = {"ok": True, "problems": [], "warnings": []}
    try:
        sub = read_dir(d)
    except Refused as e:
        return {"ok": False, "problems": list(e.args[0]), "warnings": []}
    code = sub["meta"].get("deck") if sub["kind"] in ("deck", "puzzle") else deck_of_member
    if code:
        _, problems = check_deck(code)
        out["problems"] += problems
    out["problems"] += check_code(sub["src"], sub["meta"]["class"])
    out["ok"] = not out["problems"]
    return out


def receive(d: Path, player: str, pool_dir: Path, subdir: Path, workers: int = 4, mask=None,
            rng_seed: int | None = None, smoke_games: int = SMOKE_GAMES, step_limit: float = 30.0,
            seeds: tuple[int, int] = SMOKE_SEEDS) -> dict:
    """Every check; the receipt; one ledger line (accepted or refused)."""
    from ladder.runner import one_core_type
    one_core_type(mask)                                   # the compute check compares games (A44)
    from ladder import base
    from ladder.pool import Pool
    from ladder.replay import replay_decisions
    from ladder.runner import provenance, run
    subdir = Path(subdir).resolve()
    lines = ledger(subdir)
    n = sum(1 for l in lines if l.get("ev") == "receipt") + 1
    rid = f"S-{n:04d}"
    rng = random.Random(rng_seed if rng_seed is not None else secrets.randbits(64))
    rec = {"ev": "receipt", "id": rid, "player": player, "time": datetime.now(timezone.utc).isoformat(
        timespec="seconds"), "version": SUBMIT_VERSION, "interface": None, "base": base.BASE_VERSION,
           "dir": str(Path(d).resolve()), "kind": None, "member": None, "checks": [], "reasons": [],
           "warnings": [], "verdict": None, "uses_slot": False, "smoke_seeds": []}
    try:
        from ladder.interface import INTERFACE_VERSION
        rec["interface"] = INTERFACE_VERSION
    except Exception:
        pass
    store = subdir / rid
    store.mkdir(parents=True, exist_ok=True)

    def check(name, problems, detail=None):
        rec["checks"].append({"check": name, "ok": not problems, "detail": detail})
        rec["reasons"].extend(f"[{name}] {p}" for p in problems)
        return not problems

    def finish():
        rec["verdict"] = "收下" if not rec["reasons"] else "拒收"
        rec["uses_slot"] = bool(rec.get("uses_slot")) and rec["verdict"] == "收下"   # a refused deck leaves its class open
        (store / "receipt.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        (store / "receipt.md").write_text(receipt_text(rec), encoding="utf-8")
        _append(subdir, rec)
        return rec

    try:
        sub = read_dir(Path(d))
    except Refused as e:
        check("格式", list(e.args[0]))
        try:                                            # what it was meant to be, for the ledger
            meta = json.loads((Path(d) / "submission.json").read_text(encoding="utf-8"))
            kind = TYPES.get(meta.get("type"))
            rec.update(kind=kind, member=meta.get("member"), period=Pool(pool_dir).period)
        except Exception:
            pass
        return finish()
    for f in FILES:
        shutil.copy2(Path(d) / f, store / f)
    rec["sha256"] = _sha(store)
    meta = sub["meta"]
    rec.update(kind=sub["kind"], member=meta["member"], route=meta.get("route"), puzzle=meta.get("puzzle"))
    check("格式", [])
    pool = Pool(pool_dir)
    if sub["kind"] in ("deck", "puzzle"):
        ids, problems = check_deck(meta["deck"])
        sub["deck_ids"] = ids
        check("卡组", problems)
    if sub["kind"] == "puzzle":
        puzzles = subdir / "puzzles.json"
        known = json.loads(puzzles.read_text(encoding="utf-8")) if puzzles.exists() else {}
        p = known.get(meta["puzzle"])
        problems = [] if p and sorted(p.get("deck", [])) == sorted(sub.get("deck_ids", [])) else \
            [f"没有题号 {meta['puzzle']!r}，或者卡组和题目指定的不一样"]
        check("公共题", problems)
    else:
        problems, info = check_slots(sub, player, pool, lines)
        rec.update(period=info["period"], period_kind=info["period_kind"], uses_slot=info["uses_slot"],
                   mid=info.get("mid"), craft=info.get("craft"), was=info.get("was"))
        check("名额和期", problems)
    rec.setdefault("period", pool.period)
    code_problems = check_code(sub["src"], meta["class"])
    check("代码（读）", code_problems)
    if rec["reasons"] or not sub.get("deck_ids"):
        return finish()                                   # nothing is run for a submission already refused

    from ladder.runner import load_deck
    craft = int(base.craft_of(load_deck(sub["deck_ids"])))
    lists = base.baseline_lists()
    opp_craft = next(c for c in sorted(lists) if c != craft)
    lc = load_check(store / "strategy.py", meta["class"], sub["deck_ids"], opp_craft, seed=rng.randrange(1, 2 ** 31),
                    game_seed=rng.randrange(*seeds), work=store)
    problems = [] if lc.get("ok") else ([f"载入后碰了不许碰的：{'；'.join(lc.get('blocked', []))}"] if lc.get("blocked")
                                       else [lc.get("error", "载入失败")])
    check("载入（隔离进程）", problems, {k: lc.get(k) for k in ("winner", "turns")})
    if rec["reasons"]:
        return finish()

    spec = _stage(sub, rid, subdir)
    rec["spec"] = spec
    used = _used_smoke_seeds(lines)
    jobs, played = smoke_jobs(spec, sub["deck_ids"], rid, rng, used, games=smoke_games, seeds=seeds)
    rec["smoke_seeds"] = played
    out = store / "smoke.jsonl"
    run(jobs, str(out), workers=workers, step_limit=step_limit, mask=mask, quiet=True)
    logs = {}
    for line in out.read_text(encoding="utf-8").splitlines():
        if line.strip():
            g = json.loads(line)
            logs[g["id"]] = g
    mine = [logs.get(j["id"]) for j in jobs if j["labels"]["side"] == "sub"]
    problems, voids, other = [], 0, []
    for j, g in zip([j for j in jobs if j["labels"]["side"] == "sub"], mine):
        seat = j["labels"]["seat"]
        if g is None:
            problems.append(f"{j['id']} 没打完")
        elif g["result"] in ("crash", "illegal", "timeout") and g.get("loser") == seat:
            problems.append(f"{j['id']}：{ {'crash': '崩了', 'illegal': '走了非法步', 'timeout': '超时'}[g['result']]}："
                            f"{str(g.get('error', ''))[-600:]}")
        elif g["result"] == "void":
            voids += 1
            twin = logs.get(j["id"].replace("-sub", "-default"))
            why = str(g.get("error", ""))
            if any(why.startswith(t) for t in YOUR_VOIDS) and twin is not None and twin.get("result") != "void":
                problems.append(f"{j['id']}：这局作废了，同一局换默认打法没作废——是你的代码（LD-45、LD-46）：{_quote(why)}")
            else:
                first = (why.strip().splitlines() or ["?"])[0][:160]
                both = twin is not None and twin.get("result") == "void"
                other.append(f"{j['id']}（{'换默认打法也作废' if both else '原因不在你的代码'}）：{first}")
    wins = sum(1 for j, g in zip([j for j in jobs if j["labels"]["side"] == "sub"], mine)
               if g and g.get("winner") == j["labels"]["seat"])
    if mine and voids == len(mine) and not problems:
        problems.append(f"冒烟局 {voids} 局全作废，后面的检查什么也查不到（LD-46）：" + "；".join(other)[:1200])
    check("冒烟", problems, {"games": len(mine), "wins": wins, "void": voids})
    if voids and not problems:
        rec["warnings"].append(f"冒烟局里有 {voids} 局作废，不算你的，只提醒：" + "；".join(other)[:1200])
    if rec["reasons"]:
        return finish()

    pairs = [(j, logs[j["id"]], logs.get(j["id"].replace("-sub", "-default"))) for j in jobs
             if j["labels"]["side"] == "sub" and j["id"] in logs]
    tot = [0, 0, 0, 0]
    for j, g, ref in pairs:
        seat = j["labels"]["seat"]
        s, k = _mean_step(g, seat)
        tot[0] += s
        tot[1] += k
        if ref:
            s, k = _mean_step(ref, seat)
            tot[2] += s
            tot[3] += k
    ratio = (tot[0] / tot[1]) / (tot[2] / tot[3]) if tot[1] and tot[3] and tot[2] else None
    rec["compute_ratio"] = None if ratio is None else round(ratio, 3)
    if ratio is not None and ratio > COMPUTE_WARN:
        rec["warnings"].append(f"每步算力是默认打法的 {ratio:.2f} 倍，超过 {COMPUTE_WARN}：把关检验会判无效（A25）")
    check("算力", [], {"ratio": rec["compute_ratio"], "unit": pairs[0][1].get("cpu_unit") if pairs else None})

    problems = []
    normal = [g for _, g, _ in pairs if g["result"] in ("normal", "draw")]
    for g in normal[:REPLAY_GAMES]:
        ok, why = replay_decisions(g)
        if not ok:
            problems.append(f"{g['id']} 重放对不上：{why}（同一种子、同一局面要做出同样的选择；随机数用 self.random）")
    check("确定性", problems, {"replayed": min(len(normal), REPLAY_GAMES)})
    if rec["reasons"]:
        return finish()

    problems, tried = [], []
    for j, g, _ in [p for p in pairs if p[1].get("result") in ("normal", "draw")][:PEEK_GAMES]:
        seat = j["labels"]["seat"]
        count = sum(1 for s, _, _ in g.get("steps", []) if s == seat)
        if count == 0:
            continue
        points = sorted(rng.sample(range(count), min(PEEK_POINTS, count)))
        for k in points:
            r = peek_check(g, seat, k, random.Random(rng.randrange(2 ** 63)))
            tried.append([g["id"], k, r])
            if r == "differs":
                problems.append(f"{g['id']} 第 {k} 个决策：真实局面里你看不到的东西换了，你的选择跟着变了")
            elif r == "diverged":
                problems.append(f"{g['id']}：重放到第 {k} 个决策以前就对不上了（不确定）")
    check("偷看", problems, {"points": tried})
    rec["provenance"] = provenance()
    return finish()


def _craft_zh(c) -> str:
    from ladder.pool import CRAFT_ZH
    return CRAFT_ZH.get(c, "—")


def receipt_text(rec: dict) -> str:
    kind = {v: k for k, v in TYPES.items()}.get(rec.get("kind"), "?")
    lines = [f"# 回执 {rec['id']}：{rec['verdict']}", "",
             f"- 选手：{rec['player']}　类型：{kind}　成员：{rec.get('member')}　第 {rec.get('period')} 期",
             f"- 收到：{rec['time']}　提交校验 {rec['version']}，接口 {rec.get('interface')}，底座 {rec.get('base')}",
             f"- 职业：{_craft_zh(rec.get('craft'))}" + ("（这一期这个职业的新卡组就是它了）" if rec.get("uses_slot") else ""), ""]
    if rec["reasons"]:
        lines += ["## 拒收理由", ""] + [f"- {r}" for r in rec["reasons"]] + [""]
    if rec["warnings"]:
        lines += ["## 提醒", ""] + [f"- {w}" for w in rec["warnings"]] + [""]
    lines += ["## 查了什么", ""]
    for c in rec["checks"]:
        d = c.get("detail")
        lines.append(f"- {c['check']}：{'过' if c['ok'] else '没过'}" + (f"（{json.dumps(d, ensure_ascii=False)}）"
                                                                      if d else ""))
    if rec.get("compute_ratio") is not None:
        lines.append(f"- 每步算力 / 默认打法：{rec['compute_ratio']}")
    return "\n".join(lines) + "\n"


def admit(subdir: Path, rid: str, pool_dir: Path) -> str:
    """An accepted new deck enters the pool (pool.enter); the player's member name is kept here, not in the pool."""
    from ladder.pool import Pool
    lines = ledger(subdir)
    rec = next((l for l in lines if l.get("ev") == "receipt" and l["id"] == rid), None)
    if rec is None or rec["verdict"] != "收下" or rec["kind"] != "deck":
        raise SystemExit(f"{rid} 不是收下的新卡组")
    if any(l.get("ev") == "admit" and l.get("receipt") == rid for l in lines):
        raise SystemExit(f"{rid} 已经入池了")
    meta = json.loads((Path(subdir) / rid / "submission.json").read_text(encoding="utf-8"))
    ids, problems = check_deck(meta["deck"])
    if problems:
        raise SystemExit(f"{rid} 的卡组现在不合法了：{problems}")
    pool = Pool(pool_dir)
    mid = pool.enter(ids, rec["spec"], rec["player"], deck_code=meta["deck"], note=f"submission {rid}")
    _append(subdir, {"ev": "admit", "receipt": rid, "player": rec["player"], "member": rec["member"], "mid": mid,
                     "time": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    return mid


def gate_update(subdir: Path, rid: str, pool_dir: Path, frozen: Path, seeds: tuple[int, int], out_dir: Path,
                delta: float, workers: int = 4, mask=None, rng_seed: int | None = None) -> dict:
    """An accepted 打法更新 goes to the gate (§4.3: kind better, the player's change and prediction as written) and,
    if it passes, replaces the member's version in the pool (same CR, unstable for 300 games). Multi-step routes
    (A33): an intermediate step is only recorded; the last step, or the step marked "stop", is gated against the
    version the member had before step 1. The gate ledger lives in `out_dir` (host side, never the repository:
    it holds members, versions and the players' own words)."""
    from ladder.gate import Gate
    from ladder.pool import Pool
    subdir = Path(subdir).resolve()
    lines = ledger(subdir)
    rec = next((l for l in lines if l.get("ev") == "receipt" and l["id"] == rid), None)
    if rec is None or rec["verdict"] != "收下" or rec["kind"] != "update":
        raise SystemExit(f"{rid} 不是收下的打法更新")
    if any(l.get("ev") == "gated" and l.get("receipt") == rid for l in lines):
        raise SystemExit(f"{rid} 已经检验过了")
    meta = json.loads((subdir / rid / "submission.json").read_text(encoding="utf-8"))
    pool = Pool(pool_dir)
    m = pool.members.get(rec["mid"])
    if m is None or not m.active:
        raise SystemExit(f"{rec['mid']} 不在池子里了")
    route = rec.get("route") or {}
    line = {"ev": "gated", "receipt": rid, "player": rec["player"], "member": rec["member"], "mid": m.mid,
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if route and route["step"] < route["steps"] and not route.get("stop"):
        line.update(verdict="中间一步，不检验（A33）", gate=None)
        _append(subdir, line)
        gate_note(subdir, rid, "多步改法的中间一步：照常查过了，不检验，也不换上池子。走完最后一步（或按 stop_if 停下的那一步）再检验。")
        return line
    # where this update starts in the ledger (a route: its first step): only what happened before it counts below
    start_id = route.get("route_of") or rid if route else rid
    pos = next(i for i, l in enumerate(lines) if l.get("ev") == "receipt" and l.get("id") == start_id)
    prior = lines[:pos]
    # the same change, gated before for this member (under any receipt): not gated again (red line)
    fp = code_fingerprint((subdir / "code" / f"{rec['spec'].split(':')[1]}.py").read_text(encoding="utf-8"),
                          rec["spec"].split(":")[2])
    for l in lines:
        if l.get("ev") == "gated" and l.get("mid") == m.mid and l.get("gate") and l.get("fingerprint") == fp:
            line.update(verdict=f"同一个改动，不重新检验（和 {l['receipt']} 一样，检验 {l['gate']}）", gate=None,
                        fingerprint=fp, same_as=l["receipt"])
            _append(subdir, line)
            gate_note(subdir, rid, f"和你的 {l['receipt']} 是同一份代码（去掉注释、排版以后一样），同一个改动不重新检验。")
            return line
    # against the member's version now: an update received before another one passed is compared with the one
    # that passed, never with the version it was written against (it would otherwise replace a version it never
    # met); for a route, the member's version now is the one before step 1 unless another update passed meanwhile
    old = m.strategy
    change, prediction = meta["change"], meta["prediction"]
    if route:
        first = next(l for l in lines if l.get("ev") == "receipt" and l.get("id") == (route.get("route_of") or rid))
        was = first.get("was") or {}
        change = f"多步改法（{route['steps']} 步，停在第 {route['step']} 步）：{change}"
    else:
        was = rec.get("was") or {}
    if was.get("version") is not None and was["version"] != m.version:
        line["note"] = f"收件时成员是第 {was['version']} 版，现在是第 {m.version} 版：和现在这一版比"
    # an earlier gate of this member against this same version that did not pass: a new try must not be the same
    # change in other words, must name that gate and say what changed in substance (A46; the gate's 指回 column)
    failed = [l for l in prior if l.get("ev") == "gated" and l.get("mid") == m.mid and l.get("gate")
              and l.get("verdict") != "passed" and l.get("old") == old]
    resubmit_gate, since = None, ""
    if failed:
        def said(r):
            p = subdir / r / "submission.json"
            x = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
            return str(x.get("change", "")).strip(), str(x.get("prediction", "")).strip()
        mine = (str(meta["change"]).strip(), str(meta["prediction"]).strip())
        twin = next((l for l in failed if said(l["receipt"]) == mine), None)
        if twin:
            line.update(verdict=f"同一个改动（改动说明和预测和 {twin['receipt']} 一样），不重新检验", gate=None,
                        fingerprint=fp, same_as=twin["receipt"])
            _append(subdir, line)
            gate_note(subdir, rid, f"改动说明和预测和你没过的 {twin['receipt']} 一字不差，算同一个改动，不重新检验。")
            return line
        names = {}                                    # a failed route can be named by its last or its first receipt
        for l in failed:
            names[l["receipt"]] = l["gate"]
            r0 = next((x for x in prior if x.get("ev") == "receipt" and x.get("id") == l["receipt"]), {})
            if (r0.get("route") or {}).get("route_of"):
                names[r0["route"]["route_of"]] = l["gate"]
        ro, since = meta.get("resubmit_of"), str(meta.get("since") or "").strip()
        if route and not (ro and since):             # a route may carry them on its first step
            m0 = subdir / start_id / "submission.json"
            m0 = json.loads(m0.read_text(encoding="utf-8")) if m0.exists() else {}
            ro, since = ro or m0.get("resubmit_of"), since or str(m0.get("since") or "").strip()
        if ro not in names or not since:
            shown = "、".join(sorted({l["receipt"] for l in failed}))
            line.update(verdict=f"重交：这一版上已经有没过的检验（{shown}），要在 submission.json 里写 "
                                "resubmit_of（指回哪一次）和 since（实质改了什么）；不检验", gate=None, fingerprint=fp)
            _append(subdir, line)
            gate_note(subdir, rid, f"这个成员现在这一版上已经有没过的检验（你的 {shown}）。再交要在 submission.json 里写 "
                                   "resubmit_of（指回没过的那一次的回执编号）和 since（这次实质改了什么），见 submit.md "
                                   "第一节。这次不检验。")
            return line
        resubmit_gate = names[ro]
    code = subdir / "code"
    if str(code) not in sys.path:
        sys.path.insert(0, str(code))                     # the workers import the staged submission from here
    os.environ["LADDER_EXTRA_PATH"] = os.pathsep.join(
        x for x in (str(code), os.environ.get("LADDER_EXTRA_PATH", "")) if x)
    g = Gate(frozen, m.mid, rec["spec"], old, "better", change, prediction, seeds, out_dir, delta=delta,
             ledger_root=Path(out_dir), rng_seed=rng_seed, resubmit_of=resubmit_gate, since=since)
    res = g.run(workers=workers, mask=mask)
    line.update(gate=res["gate"], verdict=res["verdict"], old=old, new=rec["spec"], fingerprint=fp)
    if res["verdict"] == "passed":
        line["version"] = pool.update(m.mid, rec["spec"], gate=res["gate"])         # the new version number
    _append(subdir, line)
    v = res["verdict"]
    if v == "passed":
        text = "检验过了，已经换上池子（CR 沿用，匿名编号不变）。"
    elif v.startswith("invalid: compute"):
        text = "检验无效：新打法每步算力超过旧版的 1.08 倍。池子里还是原来那一版。"
    elif v.startswith("invalid"):
        text = "检验无效（作废的局太多）。池子里还是原来那一版。"
    else:
        text = "检验没过，池子里还是原来那一版。"
    if v != "passed":
        text += f"再交这个成员的更新，要写 resubmit_of（{rid}）和 since（实质改了什么），见 submit.md 第一节。"
    gate_note(subdir, rid, ("（收件以后这个成员换过版本，这次是和现在那一版比的。）" if line.get("note") else "") + text)
    return line


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ladder.submit")
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("precheck")
    a.add_argument("dir")
    a.add_argument("--deck-of-member")
    a = sp.add_parser("receive")
    a.add_argument("dir")
    a.add_argument("--player", required=True)
    a.add_argument("--pool", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--workers", type=int, default=4)
    a.add_argument("--mask", type=lambda x: int(x, 0))
    a = sp.add_parser("admit")
    a.add_argument("subdir")
    a.add_argument("--receipt", required=True)
    a.add_argument("--pool", required=True)
    a = sp.add_parser("gate")
    a.add_argument("subdir")
    a.add_argument("--receipt", required=True)
    a.add_argument("--pool", required=True)
    a.add_argument("--frozen", required=True)
    a.add_argument("--seeds", type=int, nargs=2, required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--delta", type=float, required=True)
    a.add_argument("--workers", type=int, default=4)
    a.add_argument("--mask", type=lambda x: int(x, 0))
    a = sp.add_parser("status")
    a.add_argument("subdir")
    a.add_argument("--pool", required=True)
    a.add_argument("--player", required=True)
    a = sp.add_parser("_load")
    a.add_argument("argfile")
    args = ap.parse_args(argv)
    if args.cmd == "_load":
        return _load_main(args.argfile)
    if args.cmd == "precheck":
        out = precheck(Path(args.dir), args.deck_of_member)
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0 if out["ok"] else 1
    if args.cmd == "receive":
        t0 = time.time()
        rec = receive(Path(args.dir), args.player, Path(args.pool), Path(args.out), workers=args.workers,
                      mask=args.mask)
        print(receipt_text(rec))
        print(f"({time.time() - t0:.0f} s)")
        return 0
    if args.cmd == "status":
        print(json.dumps(status(Path(args.subdir), Path(args.pool), args.player), ensure_ascii=False, indent=1))
        return 0
    if args.cmd == "admit":
        print(admit(Path(args.subdir), args.receipt, Path(args.pool)))
        return 0
    if args.cmd == "gate":
        out = gate_update(Path(args.subdir), args.receipt, Path(args.pool), Path(args.frozen), tuple(args.seeds),
                          Path(args.out), delta=args.delta, workers=args.workers, mask=args.mask)
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0


if __name__ == "__main__":
    sys.exit(main())
