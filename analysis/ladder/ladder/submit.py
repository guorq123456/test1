"""Submissions (phase 2, item 2.3): the entry point, and the checks a submission passes before it goes anywhere.

    python -m ladder.submit precheck DIR [--deck-of-member CODE]      # format, deck, code; no games, counts nothing
    python -m ladder.submit receive  DIR --player fable --pool POOLDIR --out SUBDIR [--workers 15] --mask 0x3FC3FC
    python -m ladder.submit admit    SUBDIR --receipt S-0001 --pool POOLDIR   # an accepted new deck enters the pool
    python -m ladder.submit status   SUBDIR --pool POOLDIR --player fable         # classes done / missing this period
    python -m ladder.submit deliver  SUBDIR --pool POOLDIR --players C:\\claude\\ladder-players   # receipts, gate results, status
                                                                             # into each player's receipts\\ (A50)

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
- compute: per-step compute of the submission over the default strategy's on the submission's own positions (the
  smoke games replayed with the default, calibrated by the twin game and its replay, LD-56); the cap is 1.08,
  measured above 1.15 refused (S15), in between a warning,
  every version (A52: new decks never go through the gate, and the gate compares new with old, A25);
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
TYPES = {"新卡组": "deck", "打法更新": "update", "公共题": "puzzle", "选队": "team"}   # 选队: a special period (S27, A62)
FILES = ("submission.json", "strategy.py", "notes.md", "evidence.md")
UPDATES_PER_PERIOD = None           # Salem S5 (11-22): no limit on strategy updates (the plan's 3 is gone)
SMOKE_SEEDS = (88300000, 88400000)  # the host's part of the tuning range (SEEDS.md)
SMOKE_GAMES = 50                    # LD-55..58: over 10 games the twins' compute ratio spread ~8% (an honest default-cost
                                    # strategy refused ~12% of the time); the shadow on the PC's E-cores over 50: 0.7-1.0%
                                    # (container: 1.6-2.0% over 100); each receipt holds the arena's lock, so not more
PEEK_GAMES, PEEK_POINTS = 2, 3
REPLAY_GAMES = 2
COMPUTE_CAP = 1.08                                 # per-step compute over the default's: the cap (A52)
COMPUTE_REFUSE = 1.15                              # refused above: the cap's public allowance for the measurement's
                                                   # error (S15, Salem 11-23 14:10Z); 1.08-1.15 accepted with a warning
YOUR_VOIDS = ("the simulator changed in this worker during the game",   # what the strategy's own code voids
              "a strategy's code tried what a game may not do",                # (LD-52)
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
    team = _team_dir(d)
    if team is not None:
        return team
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


def _team_dir(d: Path) -> dict | None:
    """A 选队 submission (special period, A62): submission.json {"type": "选队", "team": ...} and nothing else is
    needed (other files are ignored). None if the directory is not one."""
    try:
        meta = json.loads((d / "submission.json").read_text(encoding="utf-8"))
    except OSError:
        return None
    except ValueError as e:              # a BOM, UTF-16, a JSON error: said first, not as three missing files (review)
        raise Refused([f"submission.json 读不了：{e}（要 UTF-8、不带 BOM 的 JSON）"])
    if not isinstance(meta, dict) or str(meta.get("type", "")).strip() != "选队":
        return None
    if not isinstance(meta.get("team"), str) or not meta["team"].strip():
        raise Refused(["选队要写 team（队名，照抄 special-P3.md 里的写法）"])
    return {"meta": meta, "kind": "team", "src": "", "dir": d}


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
    odd = sorted({f"{c.name_zh or c.name}（{c.card_id}）" for c in deck if c.is_token or not c.rotation})
    if odd:                                  # LD-68: validate lets in a derived form (an Accelerate card, 10901112)
        problems.append("这些不是能放进卡组的牌（衍生物、激奏或结晶形态，模拟器卡牌数据里不在指定卡池）："
                        + "、".join(odd))
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


class _ledger_lock:
    """One receive, admit, gate or deliver at a time on a ledger (11-23 review: a receipt id is the ledger's count +
    1, taken at the start and written minutes later; a hand-run command next to the collector got the same id).
    Waits for the other one to finish."""

    def __init__(self, subdir: Path):
        self.path = Path(subdir) / "ledger.lock"

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(self.path, "a+")
        told = False
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    self.f.seek(0)
                    msvcrt.locking(self.f.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except OSError:
                if not told:
                    print("提交台账正被另一个命令用着（收提交的循环？），等它做完……", file=sys.stderr, flush=True)
                    told = True
                time.sleep(2)

    def __exit__(self, *exc):
        try:
            if os.name == "nt":
                import msvcrt
                self.f.seek(0)
                msvcrt.locking(self.f.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            self.f.close()


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
            from ladder import special
            if special.is_special(pool.period):
                why, info["team"] = special.check_deck(sub["deck_ids"], craft, player, pool.period, lines)
                problems += why
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
    from ladder import special
    if special.is_special(pool.period):
        out.update(special.status(ledger(subdir), pool.period, player))
    return out


def status_text(st: dict, lines: list[dict]) -> str:
    """The status a player finds in their receipts folder (A50): this period's accepted and missing classes (a deck
    period), the updates received and what their gates said."""
    kind = {"deck": "卡组期", "strategy": "策略期"}.get(st["kind"], st["kind"])
    out = [f"# 第 {st['period']} 期（{kind}）你的提交", ""]
    if st.get("special"):
        out += [f"- 这一期是特殊期：{st['special']}。你选的队：{st['team'] or '还没选（先交「选队」）'}"]
    if st["kind"] == "deck":
        out += [f"- 新卡组已经收下的职业：{'、'.join(st['classes_done']) or '还没有'}",
                f"- 还缺：{'、'.join(st['classes_missing']) or '不缺了'}"]
    mine = {l["id"] for l in lines if l.get("ev") == "receipt" and l.get("player") == st["player"]
            and l.get("period") == st["period"] and l.get("kind") == "update"}
    gated = [l for l in lines if l.get("ev") == "gated" and l.get("receipt") in mine]
    passed = sum(1 for l in gated if l.get("verdict") == "passed")
    out += [f"- 打法更新：收到 {st['updates']} 份，收下（进检验）{st['updates_accepted']} 份；检验完 {len(gated)} 份，"
            f"其中换上池子 {passed} 份。每份的结果在同名的「-检验」文件里"]
    return "\n".join(out) + "\n"


RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}


def box_name(name: str, rid: str, taken: set) -> str:
    """The file name (without .md) a receipt gets in the player's receipts folder: the directory's name if it is a
    plain one (letters of any script, digits, - _ . and spaces inside, at most 60), else the receipt id; never 状态,
    never ending in -检验 or -没收成 (those are the host's), never one already taken (then the receipt id is added)."""
    import re
    ok = (bool(re.fullmatch(r"[\w][\w\-. ]{0,59}", name)) and not name.endswith((".", " "))
          and name.split(".")[0].lower() not in RESERVED and name != "状态"
          and not name.endswith(("-检验", "-没收成")))
    base_ = name if ok else rid
    out = base_ if base_ not in taken else f"{base_}-{rid}"
    taken.add(out)
    return out


def deliver(subdir: Path, pool_dir: Path, players: Path) -> dict:
    """What goes back to each player (A50), into PLAYERS/<name>/receipts/: each of their receipts under the name of the
    directory they handed in (box_name: <name>.md), the gate result of each update (<name>-检验.md, gate_note) and
    this period's status (状态.md). Written again on every call (the same text, so it can run after every receive and
    gate); never another player's. A player whose folder can't be written is skipped and reported ({player: the
    error}); the others still get theirs."""
    from ladder.arena import FOLDER
    subdir, players = Path(subdir), Path(players)
    with _ledger_lock(subdir.resolve()):
        lines = ledger(subdir)
    out = {}
    for player, py in FOLDER.items():
        recs = [l for l in lines if l.get("ev") == "receipt" and l.get("player") == player]
        if not recs:
            continue
        try:
            box = players / py / "receipts"
            box.mkdir(parents=True, exist_ok=True)
            taken, n = set(), 0
            for rec in recs:
                name = box_name(Path(str(rec.get("dir") or rec["id"])).name, rec["id"], taken)
                src = subdir / rec["id"] / "receipt.md"
                text = src.read_text(encoding="utf-8") if src.exists() else receipt_text(rec)
                (box / f"{name}.md").write_text(text, encoding="utf-8")
                note = subdir / rec["id"] / "gate-note.md"
                if note.exists():
                    (box / f"{name}-检验.md").write_text(note.read_text(encoding="utf-8"), encoding="utf-8")
                n += 1
            (box / "状态.md").write_text(status_text(status(subdir, pool_dir, player), lines), encoding="utf-8")
            out[player] = n
        except OSError as e:
            out[player] = f"写不进去：{type(e).__name__}: {e}"
    return out


# --- the load check (a separate process) ------------------------------------------------------------------------

from ladder.guard import BLOCK as LOAD_BLOCK, BLOCK_PREFIX as LOAD_BLOCK_PREFIX  # noqa: E402 - the games' list
#   (LD-52: the load step's own list lacked os.symlink, os.link, os.truncate, os.utime, os.chown, os.chdir, threads)


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
            if args.get("construct_only"):              # the arena's check of a practice version: built, no game
                for s in args.get("seeds") or []:       # with every seed a game may give it (11-23 review)
                    klass(seed=s)
                out.update(ok=True)
            else:
                seats = [strat, S.BotStrategy(seed=args["seed"] + 1)]
                winner, state, _ = S.play(deck, opp, seats, seed=args["game_seed"],
                                          max_turns=args.get("max_turns", 60))
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
               timeout: float = 600.0, construct_only: bool = False, seeds: list | None = None) -> dict:
    """In a process of its own, under the audit hook: import the strategy, build its class and (unless
    `construct_only`, the arena's check) play one game against the default."""
    work = Path(work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    argfile = work / "loadcheck-args.json"
    argfile.write_text(json.dumps({"path": str(Path(path).resolve()), "class": cls, "deck": deck, "opp_craft": opp_craft,
                                   "seed": seed, "game_seed": game_seed, "construct_only": construct_only,
                                   "seeds": seeds}),
                       encoding="utf-8")
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
    sys.modules.pop(name, None)                           # a cut-off earlier try at this id may have imported it
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


PUBLIC_LIST_FILES = ("analysis/pilot/fields/bot-frozen7.txt", "svsim/ui/bot_decks.txt",      # tools/make_public.py
                     "analysis/ladder/decklists/wgpq-2026-11-14.txt", "analysis/ladder/decklists/ps1011-2026-11-11.txt")
SMOKE_SWAPS = 6                       # a smoke opponent's list: a public one with 0..6 cards swapped (LD-57)
_PUBLIC = None


def public_lists() -> dict:
    """{craft: [card id lists]}: the lists of public/decklists.md (every player has them, S1) that the simulator plays
    as written (40 cards, legal, every card scripted). Never a pool member's list: a strategy sees what its opponent
    plays, and a receipt is back within minutes (LD-57)."""
    global _PUBLIC
    if _PUBLIC is None:
        from ladder import base
        from ladder.runner import load_deck, unscripted
        from svsim.cards.decks import validate
        out = {}
        for rel in PUBLIC_LIST_FILES:
            for line in (base._ROOT / rel).read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "|" not in line:
                    continue
                try:
                    deck = load_deck(line.split("|")[1].strip())
                except Exception:                            # a card the simulator doesn't have
                    continue
                if len(deck) == 40 and not validate(deck) and not unscripted(deck):
                    ids = sorted(c.card_id for c in deck)
                    lists = out.setdefault(int(base.craft_of(deck)), [])
                    if ids not in lists:
                        lists.append(ids)
        _PUBLIC = out
    return _PUBLIC


def smoke_list(craft: int, rng: random.Random, opponents: dict | None, swaps: int = SMOKE_SWAPS) -> list:
    """One of `opponents[craft]` (else the baseline list), with up to `swaps` cards swapped for others of the lists
    of that class (no card past its copy limit; a list the simulator wouldn't take is drawn again)."""
    from ladder import base
    choices = (opponents or {}).get(craft) or [sorted(base.baseline_lists()[craft])]
    start = list(choices[rng.randrange(len(choices))])
    k = rng.randrange(swaps + 1) if swaps else 0
    if not k:
        return start
    from ladder.runner import load_deck
    from svsim.cards.decks import validate
    cards = sorted({c for l in choices for c in l})
    for _ in range(20):
        deck = list(start)
        for _ in range(k):
            deck.pop(rng.randrange(len(deck)))
            deck.append(cards[rng.randrange(len(cards))])
        try:
            if not validate(load_deck(deck)):
                return deck
        except Exception:
            pass
    return start


def smoke_jobs(spec: str, deck_ids: list, rid: str, rng: random.Random, used: set, games: int = SMOKE_GAMES,
               seeds: tuple[int, int] = SMOKE_SEEDS, opponents: dict | None = None, swaps: int = SMOKE_SWAPS):
    """Pairs of jobs: the submission and the default strategy in the same seat, same seed, same strategy seeds,
    against the default strategy, classes in turn, each game's list from smoke_list (receive: the public lists).
    Strategy seeds from the same range as the pool's (deal.seal: 62 bits), so a strategy can't tell a smoke game by
    its seed, nor by its opponent's list being exactly a baseline one (LD-57)."""
    from ladder import base
    crafts = sorted(base.baseline_lists())
    jobs, played = [], []
    left = (seeds[1] - seeds[0]) - sum(1 for s in used if seeds[0] <= s < seeds[1])
    if left < games:                              # the host's to fix: never loop for a seed that isn't there
        raise SystemExit(f"冒烟种子段 {seeds[0]}～{seeds[1] - 1} 只剩 {left} 个没用过，这一份要 {games} 个：先在 SEEDS.md "
                         "和项目登记表上登记新的一段")
    for i in range(games):
        while True:
            seed = rng.randrange(*seeds)
            if seed not in used:
                break
        used.add(seed)
        played.append(seed)
        seat = i % 2
        opp = smoke_list(crafts[i % len(crafts)], rng, opponents, swaps)
        sseeds = [rng.randrange(1, 2 ** 62), rng.randrange(1, 2 ** 62)]
        for side, s in (("sub", spec), ("default", DEFAULT)):
            sides = [(list(deck_ids), s), (list(opp), DEFAULT)]
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


# --- the compute check on the submission's own positions (A52, LD-56) -----------------------------------------

def shadow_task(log: dict, seat: int, seeds=None) -> dict:
    """What `_shadow` needs of a logged smoke game: the deal, the moves, the strategy seeds (`seeds`: others than the
    log's, for tools/compute_noise.py only), the submission's seat."""
    return {"id": log["id"], "seed": log["seed"], "first_arg": log.get("first_arg"), "decks": log["decks"],
            "deal": log.get("deal"), "strategy_seeds": list(seeds or log["strategy_seeds"]),
            "actions": log["actions"], "seat": seat}


def _shadow(task: dict, beat=None) -> dict:
    """A runner.guarded_map task: the logged game again, move for move, with the default strategy on both seats.
    Every decision is asked and timed as the runner times a step (the same counter, the same calls around it), its
    answer thrown away, the logged move played. Only host code runs here: the submission is never run again, so it
    can't tell a measurement from a game (LD-56)."""
    from ladder.runner import host_ctrl_c
    with host_ctrl_c():
        return _shadow_play(task, beat)


def _shadow_play(task: dict, beat) -> dict:
    from ladder import base, deal
    from ladder.runner import _make_counter, load_strategies, offer
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply, legal_actions
    counter, unit = _make_counter()
    _, state = deal.start(task)
    tracker = base.Tracker(state)
    strategies = load_strategies([DEFAULT, DEFAULT], task["strategy_seeds"], beat)
    steps = []
    for data in task["actions"]:
        seat = state.active
        actions = legal_actions(state)
        offered = offer(actions)
        pos = base.public_position(state, seat, tracker)
        if beat is not None:
            beat[0], beat[1] = seat, time.monotonic_ns()
        c0 = counter()
        try:
            strategies[seat].act(pos, offered)
            steps.append([seat, counter() - c0])
        finally:
            if beat is not None:
                beat[1] = 0
        tracker.before(state)
        apply(state, from_dict(data))
        tracker.after(state)
    return {"id": task["id"], "steps": steps, "cpu_unit": unit}


def shadow_tasks(pairs) -> list:
    """Two shadows per pair (submission's game, its twin; `pairs` are (game, twin, seat)), one after the other, so
    both run in the same batch under the same conditions. Both on the seeds the pair was played with."""
    return [t for g, ref, seat in pairs for t in (shadow_task(g, seat), shadow_task(ref, seat))]


def shadow_rows(pairs, got) -> tuple[list, list]:
    """(rows, problems). One row per pair whose two shadows came back whole and match their games' decisions:
    (the submission's CPU on its decisions in its game, the default's on the same positions in the shadow, the twin
    game's CPU on all its decisions, its shadow's on the same). The twin and its shadow are the very same computation
    (the default on the same positions and seeds), so their ratio is how much a step costs in a game against in a
    shadow on this machine just then (it drifted ~9% between two runs in the container, LD-56); the submission's own
    ratio is divided by it."""
    rows, bad = [], []
    for i, (g, ref, seat) in enumerate(pairs):
        rs = [got[2 * i] or {"died": None}, got[2 * i + 1] or {"died": None}]
        broken = [r for r in rs if "value" not in r or r.get("changed") or r.get("blocked")]
        if broken:
            bad.append(f"{g['id']}: {_quote(str({k: v for k, v in broken[0].items() if k != 'value'}), 200)}")
            continue
        mine = [c for s, c, _ in g.get("steps", []) if s == seat]
        dflt = [c for s, c in rs[0]["value"]["steps"] if s == seat]
        twin = [c for _, c, _ in ref.get("steps", [])]
        tw_sh = [c for _, c in rs[1]["value"]["steps"]]
        if len(mine) != len(dflt) or len(twin) != len(tw_sh) or not mine or not twin:
            bad.append(f"{g['id']}: decisions {len(mine)} / {len(dflt)} (game / shadow), twin {len(twin)} / "
                       f"{len(tw_sh)}")
            continue
        rows.append((sum(mine), sum(dflt), sum(twin), sum(tw_sh)))
    return rows, bad


def pooled_ratio(rows) -> float | None:
    """The submission's per-step CPU over the default's on the same positions, over the rows, corrected by how
    much more a step cost in the games than in the shadows (the twins')."""
    t = [sum(r[i] for r in rows) for i in range(4)]
    return (t[0] / t[1]) / (t[2] / t[3]) if all(t) else None


# --- receive ---------------------------------------------------------------------------------------------------

def _sha(d: Path) -> dict:
    return {f: hashlib.sha256((d / f).read_bytes()).hexdigest() for f in FILES if (d / f).is_file()}


def precheck(d: Path, deck_of_member: str | None = None) -> dict:
    """What a player may run on their own: format, deck, the code read. No games, no ledger, no slots."""
    out = {"ok": True, "problems": [], "warnings": []}
    try:
        sub = read_dir(d)
    except Refused as e:
        return {"ok": False, "problems": list(e.args[0]), "warnings": []}
    if sub["kind"] == "team":                          # the name, here; whether the team has room only at receive
        from ladder import special
        names = special.all_team_names()
        if special.canonical(sub["meta"]["team"], names) not in names:
            out["problems"].append(f"没有叫 {sub['meta']['team']!r} 的队；能选的是：{'、'.join(sorted(names))}（照抄）")
        out["ok"] = not out["problems"]
        return out
    code = sub["meta"].get("deck") if sub["kind"] in ("deck", "puzzle") else deck_of_member
    if code:
        _, problems = check_deck(code)
        out["problems"] += problems
    out["problems"] += check_code(sub["src"], sub["meta"]["class"])
    out["ok"] = not out["problems"]
    return out


def receive(d: Path, player: str, pool_dir: Path, subdir: Path, workers: int = 4, mask=None,
            rng_seed: int | None = None, smoke_games: int = SMOKE_GAMES, step_limit: float = 30.0,
            seeds: tuple[int, int] = SMOKE_SEEDS, extra: dict | None = None) -> dict:
    """Every check; the receipt; one ledger line (accepted or refused). `extra`: host fields kept in the ledger line
    (the collector's stamp of the directory). Holds the ledger lock throughout."""
    from ladder.arena import PLAYERS
    if player not in PLAYERS:                             # a typo would open a ledger for nobody (S20: names)
        raise SystemExit(f"没有选手 {player!r}（{'、'.join(PLAYERS)}）")
    Path(subdir).mkdir(parents=True, exist_ok=True)
    with _ledger_lock(Path(subdir).resolve()):
        return _receive(d, player, pool_dir, subdir, workers, mask, rng_seed, smoke_games, step_limit, seeds, extra)


def _receive(d, player, pool_dir, subdir, workers, mask, rng_seed, smoke_games, step_limit, seeds, extra) -> dict:
    from ladder.runner import one_core_type
    one_core_type(mask)                                   # the compute check compares games (A44)
    from ladder import base
    from ladder.pool import Pool
    from ladder.replay import replay_decisions
    from ladder.runner import guarded_map, provenance, run
    subdir = Path(subdir).resolve()
    lines = ledger(subdir)
    n = sum(1 for l in lines if l.get("ev") == "receipt") + 1
    rid = f"S-{n:04d}"
    rng = random.Random(rng_seed if rng_seed is not None else secrets.randbits(64))
    rec = {"ev": "receipt", "id": rid, "player": player, "time": datetime.now(timezone.utc).isoformat(
        timespec="seconds"), "version": SUBMIT_VERSION, "interface": None, "base": base.BASE_VERSION,
           "dir": str(Path(d).resolve()), "kind": None, "member": None, "checks": [], "reasons": [],
           "warnings": [], "verdict": None, "uses_slot": False, "smoke_seeds": [], **(extra or {})}
    try:
        from ladder.interface import INTERFACE_VERSION
        rec["interface"] = INTERFACE_VERSION
    except Exception:
        pass
    store = subdir / rid
    if store.exists():                                    # an earlier try at this id was cut off before its ledger line
        aside = subdir / "_cut-off" / f"{rid}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}"
        aside.parent.mkdir(parents=True, exist_ok=True)   # (11-23 review: its smoke games were taken as this one's)
        shutil.move(str(store), str(aside))
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
    for f in (("submission.json",) if sub["kind"] == "team" else FILES):
        shutil.copy2(Path(d) / f, store / f)
    rec["sha256"] = _sha(store)
    meta = sub["meta"]
    if sub["kind"] == "team":                             # a special period's team claim (A62): no code, no games
        from ladder import special
        rec.update(kind="team", member=None)
        check("格式", [])
        pool = Pool(pool_dir)
        problems, info = special.check_claim(sub, player, pool, lines)
        rec.update(period=info["period"], team=info.get("team"))
        check("选队", problems)
        return finish()
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
        if info.get("team") is not None:
            rec["team"] = info["team"]
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
    jobs, played = smoke_jobs(spec, sub["deck_ids"], rid, rng, used, games=smoke_games, seeds=seeds,
                              opponents=public_lists())
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
    twins = (tot[0] / tot[1]) / (tot[2] / tot[3]) if tot[1] and tot[3] and tot[2] else None
    # LD-56: the default on the submission's own positions, calibrated by the twin (the twins alone go their own
    # way: ~8% noise over 10 pairs, LD-55); `twins` is kept in the receipt for comparison only
    items = [(g, ref, j["labels"]["seat"]) for j, g, ref in pairs
             if g.get("result") in ("normal", "draw") and ref and ref.get("result") in ("normal", "draw")]
    tasks = shadow_tasks(items)
    got = guarded_map("ladder.submit:_shadow", tasks, workers=max(1, min(workers, len(tasks))),
                      step_limit=step_limit, mask=mask) if tasks else []
    rows, bad = shadow_rows(items, got)
    if items and len(rows) < max(1, len(items) // 2):    # the host's side failed: no receipt, the collector retries
        raise SystemExit(f"算力重放只回来 {len(rows)} / {len(items)} 对：{'；'.join(bad)[:1500]}")
    ratio = pooled_ratio(rows)
    r3 = None if ratio is None else round(ratio, 3)       # one number for the decision, the receipt and the message
    rec["compute_ratio"] = r3
    rec["compute"] = {"method": "shadow", "games": len(rows), "skipped": bad[:20],
                      "twin_void": sum(1 for _, g, ref in pairs if g.get("result") in ("normal", "draw")
                                       and not (ref and ref.get("result") in ("normal", "draw"))),
                      "twins": None if twins is None else round(twins, 3)}
    need = max(1, smoke_games // 2)
    if len(rows) < need:      # too few to measure (games void on both sides, or the twins void): never let it pass
        over = [f"冒烟局里能量算力的只有 {len(rows)} 对（要 {need} 对；其余是作废局，或者同一对里默认打法那局作废了），"
                "量不准，不收（A52、LD-57）"]
    elif r3 is not None and r3 > COMPUTE_REFUSE:
        over = [f"每步算力是默认打法的 {r3:.3f} 倍，超过 {COMPUTE_REFUSE}：上限是 {COMPUTE_CAP} 倍，量法有误差，量出来超过 "
                f"{COMPUTE_REFUSE} 倍就拒收（所有成员一样，每一版都查，A52、S15）。这次量了 {len(rows)} 对；电脑上 50 对上下约 1%"
                "（LD-58）"]
    else:
        over = []
        if r3 is not None and r3 > COMPUTE_CAP:
            rec["warnings"].append(f"每步算力量出来是默认打法的 {r3:.3f} 倍，超过上限 {COMPUTE_CAP}，还在容差 {COMPUTE_REFUSE} "
                                   "以内，收下；再往上就会被拒收（S15）")
    check("算力", over, {"ratio": rec["compute_ratio"], "unit": pairs[0][1].get("cpu_unit") if pairs else None})
    if rec["reasons"]:
        return finish()

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
            try:
                r = peek_check(g, seat, k, random.Random(rng.randrange(2 ** 63)))
            except (Exception, SystemExit) as e:          # noqa: BLE001 - the strategy's own error (11-23 review)
                r = "crashed"
                problems.append(f"{g['id']} 第 {k} 个决策：重放时你的打法报错了：{_quote(f'{type(e).__name__}: {e}', 300)}")
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
             f"- 职业：{_craft_zh(rec.get('craft'))}" + ("（这一期这个职业的新卡组就是它了）" if rec.get("uses_slot") else "")]
    if rec.get("team") is not None:
        lines.append(f"- 队：{rec['team']}" + ("（这一期你就是这个队了）" if rec.get("kind") == "team"
                                               and rec.get("verdict") == "收下" else ""))
    lines.append("")
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
    with _ledger_lock(Path(subdir).resolve()):
        return _admit(subdir, rid, pool_dir)


def _admit(subdir: Path, rid: str, pool_dir: Path) -> str:
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
    with _ledger_lock(Path(subdir).resolve()):
        return _gate_update(subdir, rid, pool_dir, frozen, seeds, out_dir, delta, workers, mask, rng_seed)


def _gate_update(subdir: Path, rid: str, pool_dir: Path, frozen: Path, seeds: tuple[int, int], out_dir: Path,
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
        from ladder.gate import COMPUTE_RATIO                         # S16: 1.15 (the text said 1.08, 11-23 review)
        text = f"检验无效：新打法每步算力超过旧版的 {COMPUTE_RATIO} 倍。池子里还是原来那一版。"
    elif v.startswith("invalid"):
        text = "检验无效（作废的局太多）。池子里还是原来那一版。"
    else:
        text = "检验没过，池子里还是原来那一版。"
    if v != "passed":
        text += f"再交这个成员的更新，要写 resubmit_of（{rid}）和 since（实质改了什么），见 submit.md 第一节。"
    gate_note(subdir, rid, ("（收件以后这个成员换过版本，这次是和现在那一版比的。）" if line.get("note") else "") + text)
    return line


def main(argv=None):
    for s in (sys.stdout, sys.stderr):           # a redirected or piped console is cp1252 on Windows (ENVIRONMENT
        try:                                      # pitfall 1; 11-23 review: a player's agent pipes the output)
            s.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:                         # noqa: BLE001
            pass
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
    a.add_argument("--stamp", help="the collector's stamp of the directory (ladder.collect), kept in the ledger")
    a.add_argument("--smoke-games", type=int, default=SMOKE_GAMES, help="tests only")
    a.add_argument("--smoke-seeds", type=int, nargs=2, default=list(SMOKE_SEEDS), help="tests only")
    a.add_argument("--rng-seed", type=int, help="tests only")
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
    a = sp.add_parser("deliver")
    a.add_argument("subdir")
    a.add_argument("--pool", required=True)
    a.add_argument("--players", required=True)
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
                      mask=args.mask, rng_seed=args.rng_seed, smoke_games=args.smoke_games,
                      seeds=tuple(args.smoke_seeds), extra={"collect_stamp": args.stamp} if args.stamp else None)
        print(receipt_text(rec))
        print(f"({time.time() - t0:.0f} s)")
        return 0
    if args.cmd == "status":
        print(json.dumps(status(Path(args.subdir), Path(args.pool), args.player), ensure_ascii=False, indent=1))
        return 0
    if args.cmd == "deliver":
        print(json.dumps(deliver(Path(args.subdir), Path(args.pool), Path(args.players)), ensure_ascii=False))
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
