"""The practice arena (phase 2, item 2.4): a frozen copy of this period's pool plus the anchors, tuning seeds only,
resuming from a position of one's own game, a game count per player and period.

Host:
    python -m ladder.arena snapshot POOLDIR --arena ARENA [--anchors ANCHORS.json] --code SUBS\\code
    python -m ladder.arena open     ARENA --hours 4 --games 20000 [--workers 23]
    python -m ladder.arena formal   ARENA --pool POOLDIR --subs SUBS --period P      # end of period P (A53)
Players (each command is one run; what a player may read is under ARENA/players/<code>/, nothing else):
    python -m ladder.arena field    ARENA --player fable
    python -m ladder.arena ladder   ARENA --player fable --version DIR [--replacing ANON] [--games 600 --tail 300 --repeats 3]
    python -m ladder.arena vs       ARENA --player fable --version DIR (--opponent ID | --class 精灵) --games N [--same-as RUN]
    python -m ladder.arena resume   ARENA --player fable --run RUN --game GAME --decision K --version DIR [--version DIR2]
                                    --continuations N
    python -m ladder.arena replay   ARENA --player fable --run RUN --game GAME

A version is a directory with strategy.py and submission.json ({"class": ..., "deck": deck code}; the other fields of
a submission are not needed here). Its code is read by the submission check's code reader first (submit.check_code).

What a player gets (PHASE2-DESIGN.md 2.4, player prompt 练习场):
- the opponents as the public leaderboard shows them: an anonymous id, the class, the CR relative to the pool's
  mean; anchors by their public name. Never a list, a strategy, an owner or a version;
- per game: which seat, first or second, the result, and the moves: their own in full, the opponent's as a human
  sees them (an opponent's mulligan only as "Mulligan"); the opponent's cards appear as they are shown. `replay`
  adds the player's own public view (base.public_position) at each of their decisions. No seed, no deck order;
- `ladder`: the pool's own matching against the frozen copy (the frozen-pool evaluator: S2, S3), a relative-CR
  estimate with its interval;
- `vs`: N games against one opponent or one class (members of it in turn), a win rate with its 95% interval;
  `--same-as RUN` plays exactly the games of an earlier run (same deals, opponents, seats and strategy seeds) with
  another version and reports the paired difference;
- `resume`: from the player's K-th decision of one of their games, the game is replayed to that point and played on
  with the given version(s): continuation 0 keeps everything as it was; continuations 1..N reshuffle the unseen part
  of both decks and the future random results (each continuation the same for every version). The hidden
  information stays with the tool. Both sides' strategies start afresh at that point.

Seeds: each player's own part of the tuning range (A34, SEEDS.md). Count: every game played (a continuation is one
game) counts against the player's cap for the period; a run that would go past the cap or start after the deadline is
refused. One run at a time on the machine (a lock file): the workers are shared (D2).

The field's received strategies (members' and hall-of-fame anchors' "py:" modules) are copied at the snapshot from the
host's received code into ARENA/host/code, where the workers import them (prompt review 11-23: from period 2 on the
arena couldn't load them). `--same-as` and `resume` take only a run of this period's field: across periods a member's
strategy may have been updated, and the same games played again would show which (red line: no versions). The formal
games of a period (`formal`, host side, A53) are the run F<period>: they can be replayed, not resumed or re-played.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import secrets
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = HERE.parents[2]
for p in (str(ROOT), str(LADDER)):
    if p not in sys.path:
        sys.path.insert(0, p)

ARENA_VERSION = "arena-1"
# The players by name (Salem S20, 11-23 18:57Z: no codenames). The name is also the player's folder name
# (C:\\claude\\ladder-players\\<name>, the arena's players\\<name>); in a module name "-" becomes "_" (module_slug).
PLAYERS = ("fable-ultracode", "fable", "astra", "opus", "sol")
PLAYER_SEEDS = dict(zip(PLAYERS, [(87400000, 87580000), (87580000, 87760000), (87760000, 87940000),
                                  (87940000, 88120000), (88120000, 88300000)]))   # A34 (the ranges 甲…戊 had, in order)
FOLDER = {p: p for p in PLAYERS}


def module_slug(player: str) -> str:
    """The player's name as it can stand in a Python module name."""
    return re.sub(r"[^0-9A-Za-z_]", "_", FOLDER[player])
CRAFT_BY_ZH = {"精灵": 1, "皇家护卫": 2, "巫师": 3, "龙族": 4, "梦魇": 5, "主教": 6, "超越者": 7}
RUN_GAMES_MAX = 2000         # games in one run (11-23 review: a run holds the arena's lock; host default, Salem told)
VOID_STOP = 30               # a ladder run stops once this many games are void and they are most of those back
LOAD_CHECK_SECONDS = 120.0
RUN_ID = re.compile(r"(R\d{4,}|F\d+)")              # a practice run, or a period's formal games


class ArenaError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(t: datetime) -> str:
    return t.isoformat(timespec="seconds")


def _read(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _write(p: Path, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def _jsonl(p: Path) -> list[dict]:
    """The records of a JSON-lines file; a line a power cut left half-written is skipped (LD-42)."""
    p = Path(p)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip(" \t\r\n\x00")
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def _append(p: Path, rec: dict):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        from ladder.runner import jsonl  # noqa: PLC0415 - no import cycle at load
        f.write(jsonl(rec))


def _on_path(d: Path):
    """Where this process and the workers it starts import strategies from (the runner's workers also read
    LADDER_EXTRA_PATH)."""
    d = str(Path(d))
    if d not in sys.path:
        sys.path.insert(0, d)
    extra = [x for x in os.environ.get("LADDER_EXTRA_PATH", "").split(os.pathsep) if x]
    if d not in extra:
        os.environ["LADDER_EXTRA_PATH"] = os.pathsep.join([d] + extra)


def _copy_code(specs, code, dest: Path) -> dict:
    """The field's received strategies ("py:module:Class" with a plain module name: a received submission), copied
    from the host's received code (`code`, subs\\code) into `dest` (ARENA/host/code). A module of the repository
    (a dotted name, e.g. ladder.interface) must be importable as it is. Anything missing: refused before a file is
    written. Returns module -> sha256 (first 16) of what was copied."""
    import importlib.util
    found, missing = {}, []
    for mod in sorted({s.split(":", 2)[1] for s in specs if s.startswith("py:")}):
        if "." in mod:
            if importlib.util.find_spec(mod) is None:
                missing.append(mod)
            continue
        f = Path(code) / f"{mod}.py" if code else None
        if f is None or not f.is_file():
            missing.append(mod)
        else:
            found[mod] = f
    if missing:
        raise ArenaError(f"找不到这些打法的模块：{'、'.join(missing)}（收下的打法要加 --code "
                         "C:\\claude\\ladder-host\\subs\\code）")
    out = {}
    if found:
        dest.mkdir(parents=True, exist_ok=True)
    for mod, f in found.items():
        b = f.read_bytes()
        (dest / f"{mod}.py").write_bytes(b)
        out[mod] = hashlib.sha256(b).hexdigest()[:16]
    return out


# --- the host's side: the frozen copy and the window -----------------------------------------------------------

def snapshot(pool_dir: Path, arena: Path, anchors: Path | None = None, cr: str = "last1000",
             code: Path | None = None) -> dict:
    """This period's frozen copy of the pool (the evaluator's freeze, plus each member's owner, kept host side) and
    the anchors. Writes ARENA/host/field.json, ARENA/host/frozen.json (the evaluator's format) and the public
    ARENA/public/field.json; copies the received strategies of the field from `code` (subs\\code) into
    ARENA/host/code."""
    from ladder.evaluator import freeze
    from ladder.pool import CRAFT_ZH, Pool
    pool = Pool(pool_dir)
    body = freeze(pool_dir, cr=cr)
    owners = {m.mid: m.owner for m in pool.members.values()}
    mu = sum(m["cr"] for m in body["members"]) / len(body["members"]) if body["members"] else 0.0
    anchor_rows = []
    for i, a in enumerate(_read(anchors) if anchors else []):
        from ladder.runner import load_deck
        from ladder import base
        cards = load_deck(a["deck"])
        anchor_rows.append({"id": a.get("id") or f"锚点{i + 1:02d}", "name": a["name"],
                            "craft": int(base.craft_of(cards)), "deck": [c.card_id for c in cards],
                            "strategy": a["strategy"]})
    arena = Path(arena)
    modules = _copy_code([m["strategy"] for m in body["members"]] + [a["strategy"] for a in anchor_rows], code,
                         arena / "host" / "code")
    host = {"version": ARENA_VERSION, "time": _iso(_now()), "pool": str(pool_dir), "period": body["period"],
            "hash": body["hash"], "mu": mu, "code": modules,
            # in anon order: the pool's own order (mid) is the order members were admitted, by player (red line)
            "members": sorted((dict(m, owner=owners.get(m["mid"])) for m in body["members"]), key=lambda m: m["anon"]),
            "anchors": anchor_rows}
    _write(arena / "host" / "frozen.json", body)
    _write(arena / "host" / "field.json", host)
    _write(arena / "public" / "field.json", public_field(host))
    return host


def public_field(host: dict) -> dict:
    from ladder.pool import CRAFT_ZH
    rows = [{"id": m["anon"], "kind": "成员", "class": CRAFT_ZH[m["craft"]], "rel_cr": round(m["cr"] - host["mu"])}
            for m in sorted(host["members"], key=lambda m: -m["cr"])]
    rows += [{"id": a["id"], "kind": "锚点", "name": a["name"], "class": CRAFT_ZH[a["craft"]]}
             for a in host["anchors"]]
    return {"period": host["period"], "field": host["hash"], "opponents": rows}


def open_window(arena: Path, hours: float, games: int, workers: int = 11, mask: int | None = None) -> dict:
    """The players' window for this period: the deadline and the game cap (both Salem's numbers: the temporary 4 h
    and the plan's 20 000)."""
    from ladder import deal
    host = _read(Path(arena) / "host" / "field.json")
    kf = Path(arena) / "host" / "arena.key"
    if not kf.exists():
        deal.new_key_file(kf)                     # the arena's own deal key (base-2), apart from the formal pool's
    cfg = {"period": host["period"], "field": host["hash"], "opened": _iso(_now()),
           "deadline": _iso(_now() + timedelta(hours=hours)), "hours": hours, "games": games,
           "workers": workers, "mask": mask}
    _write(Path(arena) / "public" / "window.json", cfg)
    return cfg


# --- per player --------------------------------------------------------------------------------------------------

class Seat:
    """One player's view of the arena."""

    def __init__(self, arena: Path, player: str):
        if player not in PLAYER_SEEDS:
            raise ArenaError(f"没有选手 {player}（{'、'.join(PLAYER_SEEDS)}）")
        self.arena, self.player = Path(arena), player
        if not (self.arena / "host" / "field.json").exists():
            raise ArenaError("这一期的练习场还没开")
        self.host = _read(self.arena / "host" / "field.json")
        win = self.arena / "public" / "window.json"
        self.window = _read(win) if win.exists() else None
        self.pub = self.arena / "players" / player
        self.priv = self.arena / "host" / "players" / FOLDER[player]
        self.count_path = self.pub / "count.jsonl"
        self.seeds = PLAYER_SEEDS[player]
        self.by_id = {m["anon"]: ("member", m) for m in self.host["members"]}
        self.by_id.update({a["id"]: ("anchor", a) for a in self.host["anchors"]})
        self.by_mid = {m["mid"]: m for m in self.host["members"]}
        self.code = self.arena / "host" / "code"      # the field's received strategies (snapshot)
        _on_path(self.code)

    # what the player may see of an opponent
    def opp_public(self, kind: str, row: dict) -> dict:
        from ladder.pool import CRAFT_ZH
        if kind == "member":
            return {"id": row["anon"], "class": CRAFT_ZH[row["craft"]], "rel_cr": round(row["cr"] - self.host["mu"])}
        return {"id": row["id"], "name": row["name"], "class": CRAFT_ZH[row["craft"]]}

    def used(self) -> int:
        """From the host's own copy of the count (the player's copy sits where the player could edit it)."""
        path = self.priv / "count.jsonl" if (self.priv / "count.jsonl").exists() else self.count_path
        return sum(r["games"] for r in _jsonl(path) if r.get("period") == self.host["period"])

    def check_window(self, games: int):
        if self.window is None or self.window["field"] != self.host["hash"]:
            raise ArenaError("这一期的练习场还没开")
        if games > RUN_GAMES_MAX:                      # one run holds the machine (D2): others wait behind it
            raise ArenaError(f"一次最多 {RUN_GAMES_MAX} 局，这次要打 {games} 局：分几次打")
        if _now() > datetime.fromisoformat(self.window["deadline"]):
            raise ArenaError(f"这一期的练习时间到了（{self.window['deadline']}）")
        left = self.window["games"] - self.used()
        if games > left:
            raise ArenaError(f"这一期还剩 {left} 局，这次要打 {games} 局")

    def field_id(self) -> dict:
        """What a run was played against: the frozen members (the evaluator's hash) and the anchor panel (not in that
        hash; 11-23 review: a re-snapshot with another panel kept the hash)."""
        panel = json.dumps([[a["id"], a["deck"], a["strategy"]] for a in self.host["anchors"]], sort_keys=True)
        return {"field": self.host["hash"], "anchors": hashlib.sha256(panel.encode("utf-8")).hexdigest()[:16]}

    def new_run(self, kind: str) -> tuple[str, Path, Path]:
        runs = sorted(p.name for p in (self.pub / "runs").glob("R*")) if (self.pub / "runs").exists() else []
        rid = f"R{len(runs) + 1:04d}"
        pub, priv = self.pub / "runs" / rid, self.priv / rid
        pub.mkdir(parents=True)
        priv.mkdir(parents=True)
        _write(priv / "run.json", {"run": rid, "kind": kind, "period": self.host["period"], **self.field_id(),
                                    "time": _iso(_now())})
        return rid, pub, priv

    def this_field(self, rid: str, what: str, kind: str | None = None) -> dict:
        """A run whose games are played again (`--same-as`) or played on (`resume`) must be one of this period's
        field: across periods a member's strategy may have been updated, and the same games played again would show
        which (red line: no versions). The formal games (F<period>) are only for replaying."""
        if not RUN_ID.fullmatch(str(rid)):
            raise ArenaError(f"没有这个编号：{rid}")
        if rid.startswith("F"):
            raise ArenaError(f"{rid} 是正式对局：只能回放（replay），不能{what}")
        mp = self.priv / rid / "run.json"
        if not (self.priv / rid).is_dir():
            raise ArenaError(f"没有 {rid}")
        meta = _read(mp) if mp.exists() else {}
        if not meta:
            raise ArenaError(f"{rid} 没有记下它是对哪个练习场打的，不能{what}")
        if {k: meta.get(k) for k in ("field", "anchors")} != self.field_id():
            raise ArenaError(f"{rid} 不是这一期的练习场里打的，不能{what}：跨期对手的打法可能换过。用这一期打的局")
        if kind and meta.get("kind") != kind:
            raise ArenaError(f"{rid} 不是 {kind} 打出来的，不能{what}")
        return meta

    def count(self, rid: str, kind: str, games: int):
        row = {"run": rid, "kind": kind, "period": self.host["period"], "games": games, "time": _iso(_now())}
        _append(self.priv / "count.jsonl", row)
        _append(self.count_path, row)

    def version(self, d: Path) -> dict:
        """A practice version: strategy.py + submission.json (class, deck). Staged where the workers import it."""
        from ladder.submit import check_code, check_deck
        d = Path(d)
        meta = _read(d / "submission.json")
        src = (d / "strategy.py").read_text(encoding="utf-8")
        problems = check_code(src, meta.get("class", ""))
        ids, deck_problems = check_deck(meta["deck"]) if meta.get("deck") else ([], ["submission.json 里要有 deck"])
        if problems or deck_problems:
            raise ArenaError("这个版本过不了提交校验的前几条：\n" + "\n".join(problems + deck_problems))
        h = hashlib.sha256(src.encode("utf-8")).hexdigest()[:10]
        name = f"arena_{module_slug(self.player)}_{h}"
        code = self.priv / "code"
        code.mkdir(parents=True, exist_ok=True)
        (code / f"{name}.py").write_text(src, encoding="utf-8")
        from ladder.submit import load_check
        lc = load_check(code / f"{name}.py", meta["class"], ids, 1, seed=1, game_seed=0,
                        work=self.priv / "loadcheck" / f"{h}-{os.getpid()}", timeout=LOAD_CHECK_SECONDS,
                        construct_only=True, seeds=[1, 2 ** 62 - 1])   # games give seeds up to 2**62 (deal.seal)
        if not lc.get("ok"):                           # 11-23 review: otherwise every game is void, unexplained
            why = ("碰了不许碰的：" + "；".join(lc["blocked"])) if lc.get("blocked") else lc.get("error", "")
            raise ArenaError("这个版本建不出你的打法类（在单独的进程里试过，没打对局、不算局数）：\n" + why)
        if str(code) not in sys.path:
            sys.path.insert(0, str(code))
        return {"spec": f"py:{name}:{meta['class']}", "deck": ids, "sha": h, "dir": str(d.resolve())}


def _lock(arena: Path):
    """One run at a time on the machine (the workers are shared, D2)."""
    path = Path(arena) / "host" / "run.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    f = open(path, "a+")
    told = False
    while True:
        try:
            if os.name == "nt":
                import msvcrt
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return f
        except OSError:
            if not told:
                print("练习场正在跑别人的对局，排队等……", file=sys.stderr, flush=True)
                told = True
            time.sleep(5)


def _locked(seat: "Seat", games: int):
    """The arena's lock, then the window checked again (11-23 review: a command queued behind others had been
    checked against a count without the runs ahead of it, and could start after the deadline). A run is opened only
    once this passes, so a refused command leaves nothing behind."""
    lock = _lock(seat.arena)
    try:
        seat.check_window(games)
    except BaseException:
        _unlock(lock)
        raise
    return lock


def _logged(path: Path, ids: set) -> int:
    """Games of this run in its log (each id once)."""
    return len({g.get("id") for g in _jsonl(path)} & set(ids)) if Path(path).exists() else 0


def _unlock(f):
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
        f.close()


# --- the player's view of a game --------------------------------------------------------------------------------

def _host_side(log: dict, seat: int) -> bool:
    """The other side of this game was a host strategy (bot:, mix:): the baseline members and the baseline anchors."""
    specs = log.get("strategies") or []
    return len(specs) == 2 and not str(specs[1 - seat]).startswith("py:")


def void_reason(log: dict, seat: int, host_opp: bool | None = None) -> str:
    """Why a game was void, as far as the player may see it (11-23 review: the reason never reached them). Against a
    host strategy only the player's own code was a player's, so the host's text is theirs to see. Against another
    player's member it is not: the cause may be on that side (red line), so only that it was void."""
    host_opp = _host_side(log, seat) if host_opp is None else host_opp
    if not host_opp:
        return "这一局作废（对手是别的选手的成员：原因可能在任何一方，不给细节）"
    return "这一局作废：" + (log.get("error") or "没有记下原因")


def own_view(log: dict, seat: int, opp: dict, host_opp: bool | None = None) -> dict:
    acts = []
    for step, a in zip(log.get("steps", []), log.get("actions", [])):
        if step[0] == seat:
            acts.append(["我", a])
        else:
            acts.append(["对手", {"type": "Mulligan"} if a.get("type") == "Mulligan" else a])
    won = log.get("winner") == seat if log.get("winner") in (0, 1) else None
    return {"game": log["id"], "seat": seat, "first": (log.get("first") == seat) if "first" in log else None,
            "opponent": opp, "result": log["result"], "won": won, "turns": log.get("turns"),
            "my_steps": sum(1 for s in log.get("steps", []) if s[0] == seat),
            "error": (log.get("error") if log.get("loser") == seat else
                      void_reason(log, seat, host_opp) if log.get("result") == "void" else None), "moves": acts}


def _wilson(w: int, n: int) -> tuple[float, float, float]:
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    z, p = 1.96, w / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return p, c - h, c + h


def _paired(a: list[int], b: list[int]) -> dict:
    """a, b: 1 won / 0 not, game by game on the same games. The difference in percentage points, 95% interval."""
    n = len(a)
    d = [x - y for x, y in zip(a, b)]
    mean = sum(d) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in d) / (n - 1)) if n > 1 else float("nan")
    half = 1.96 * sd / math.sqrt(n) if n > 1 else float("nan")
    return {"games": n, "both_won": sum(1 for x, y in zip(a, b) if x and y),
            "both_lost": sum(1 for x, y in zip(a, b) if not x and not y),
            "only_new": sum(1 for x in d if x > 0), "only_old": sum(1 for x in d if x < 0),
            "gap_pp": round(100 * mean, 2), "lo_pp": round(100 * (mean - half), 2), "hi_pp": round(100 * (mean + half), 2)}


# --- runs ----------------------------------------------------------------------------------------------------------

def _cfg(seat: Seat) -> dict:
    """Workers and mask from the window; the arena's own deal key (base-2; made by open_window, never the formal
    pool's key). No key file (an arena opened before base-2, or a test arena): the old deal."""
    w = seat.window or {}
    _on_path(seat.code)
    k = seat.arena / "host" / "arena.key"
    return {"workers": w.get("workers", 4), "mask": w.get("mask"), "key": str(k) if k.exists() else None}


def run_vs(arena: Path, player: str, version_dir: Path, games: int, opponent: str | None = None,
           craft_zh: str | None = None, same_as: str | None = None, rng_seed: int | None = None) -> dict:
    from ladder.runner import run
    seat = Seat(arena, player)
    v = seat.version(version_dir)
    rng = random.Random(rng_seed if rng_seed is not None else secrets.randbits(64))
    if same_as:
        seat.this_field(same_as, "拿来 --same-as", kind="vs")
        old = _read(seat.priv / same_as / "jobs.json")
        plan = [dict(p) for p in old["plan"]]
        games = len(plan)
    else:
        if opponent:
            if opponent not in seat.by_id:
                raise ArenaError(f"练习场里没有 {opponent}")
            pool = [seat.by_id[opponent]]
        elif craft_zh:
            craft = CRAFT_BY_ZH.get(craft_zh)
            pool = sorted((("member", m) for m in seat.host["members"] if m["craft"] == craft),
                          key=lambda x: x[1]["anon"])           # never the admission (mid) order: it groups owners
            if not pool:
                raise ArenaError(f"练习场里没有{craft_zh}的成员")
        else:
            raise ArenaError("要指定 --opponent 或 --class")
        plan = []
        for i in range(games):
            kind, row = pool[i % len(pool)]
            plan.append({"i": i, "seed": rng.randrange(*seat.seeds), "seat": i % 2, "kind": kind,
                         "opp": row["mid"] if kind == "member" else row["id"],
                         "sseeds": [rng.randrange(1, 2 ** 62), rng.randrange(1, 2 ** 62)]})  # as wide as a ladder
    gone = sorted({p["opp"] for p in plan if (p["opp"] not in seat.by_mid if p["kind"] == "member"
                                              else p["opp"] not in seat.by_id)})
    if gone:
        raise ArenaError(f"{same_as} 里的对手现在的练习场里没有了，不能重打")
    seat.check_window(games)
    lock = _locked(seat, games)
    try:
        rid, pub, priv = seat.new_run("vs")
        jobs = []
        for p in plan:
            row = seat.by_mid[p["opp"]] if p["kind"] == "member" else seat.by_id[p["opp"]][1]
            sides = [(v["deck"], v["spec"]), (row["deck"], row["strategy"])]
            if p["seat"] == 1:
                sides.reverse()
            jobs.append({"id": f"{rid}-{p['i']:05d}", "seed": p["seed"], "first": None,
                         "decks": [d for d, _ in sides], "strategies": [s for _, s in sides],
                         "strategy_seeds": p["sseeds"], "labels": {"run": rid, "seat": p["seat"]}})
        _write(priv / "jobs.json", {"plan": plan, "version": v, "same_as": same_as})
        try:
            cfg = _cfg(seat)
            run(jobs, str(priv / "games.jsonl"), workers=cfg["workers"], mask=cfg["mask"], quiet=True,
                key=cfg["key"])
        finally:
            seat.count(rid, "vs", _logged(priv / "games.jsonl", {j["id"] for j in jobs}))
    finally:
        _unlock(lock)
    logs = {g["id"]: g for g in _jsonl(priv / "games.jsonl")}
    views, wins, n = [], [], 0
    for p, j in zip(plan, jobs):
        g = logs.get(j["id"])
        if g is None:
            continue
        kind, row = ("member", seat.by_mid[p["opp"]]) if p["kind"] == "member" else seat.by_id[p["opp"]]
        view = own_view(g, p["seat"], seat.opp_public(kind, row))
        views.append(view)
        n += 1
        wins.append(1 if view["won"] else 0)
    decided = [v_ for v_ in views if v_["won"] is not None]
    w = sum(1 for v_ in decided if v_["won"])
    p_, lo, hi = _wilson(w, len(decided))
    out = {"run": rid, "kind": "vs", "version": v["sha"], "games": n, "decided": len(decided), "wins": w,
           "win_rate": round(p_, 4), "lo": round(lo, 4), "hi": round(hi, 4), "same_as": same_as,
           "errors": sum(1 for v_ in views if v_["error"] and v_["result"] != "void"),
           "void": sum(1 for v_ in views if v_["result"] == "void")}
    if same_as:
        old_views = {x["game"].split("-")[1]: x for x in _jsonl(seat.pub / "runs" / same_as / "games.jsonl")}
        a, b = [], []
        for x in views:
            y = old_views.get(x["game"].split("-")[1])
            if y is not None and x["won"] is not None and y["won"] is not None:
                a.append(1 if x["won"] else 0)
                b.append(1 if y["won"] else 0)
        out["paired"] = _paired(a, b) if a else None
    for x in views:
        _append(pub / "games.jsonl", x)
    _write(pub / "summary.json", out)
    return out


def run_ladder(arena: Path, player: str, version_dir: Path, replacing: str | None = None, games: int = 600,
               tail: int = 300, repeats: int = 3, rng_seed: int | None = None) -> dict:
    from ladder.evaluator import Candidate
    seat = Seat(arena, player)
    v = seat.version(version_dir)
    budget = games * repeats + max(VOID_STOP, games * repeats // 20)   # void and drawn games are played again
    seat.check_window(budget)
    mid = "outside"
    if replacing:
        kind, row = seat.by_id.get(replacing, (None, None))
        if kind != "member" or row.get("owner") != player:
            raise ArenaError(f"{replacing} 不是你的成员")
        mid = row["mid"]
    from ladder import base
    from ladder.runner import load_deck
    cand = Candidate(mid, int(base.craft_of(load_deck(v["deck"]))), v["deck"], v["spec"])
    lock = _locked(seat, budget)
    stopped = None
    try:
        rid, pub, priv = seat.new_run("ladder")
        ev = _StoppingEvaluation(seat.arena / "host" / "frozen.json", priv, cand, seat.seeds, games=games, tail=tail,
                                 repeats=repeats, rng_seed=rng_seed if rng_seed is not None else secrets.randbits(48))
        ev.budget, ev.approved = budget, games * repeats
        try:
            cfg = _cfg(seat)
            res = ev.run(workers=cfg["workers"], mask=cfg["mask"], key=cfg["key"])
        except _TooManyVoid as e:
            stopped = str(e)
        finally:
            seat.count(rid, "ladder", _logged(priv / "games.jsonl", set(ev.starts)))
    finally:
        _unlock(lock)
    starts = {s["id"]: s for s in _jsonl(priv / "starts.jsonl")}
    n, seen = 0, set()
    for g in _jsonl(priv / "games.jsonl"):
        st = starts.get(g["id"])
        if st is None or g["id"] in seen:
            continue
        seen.add(g["id"])
        n += 1
        _append(pub / "games.jsonl", own_view(g, st["cand_seat"],
                                              seat.opp_public("member", seat.by_mid[st["opp"]])))
    if stopped:                                        # no reading: the games played count all the same
        out = {"run": rid, "kind": "ladder", "version": v["sha"], "replacing": replacing, "games": n,
               "stopped": stopped + f"（这次打了 {n} 局，都算进局数）"}
        _write(pub / "summary.json", out)
        return out
    out = {"run": rid, "kind": "ladder", "version": v["sha"], "replacing": replacing, "games": n,
           "rel_cr": round(res["rel_cr"], 1), "lo": round(res["lo"], 1), "hi": round(res["hi"], 1),
           "repeats": res["repeats"], "values": [round(x, 1) for x in res["values"]],
           "stuck": [{k: s[k] for k in ("rep", "after", "side")} for s in res["stuck"]],
           "note": "停住的重复（stuck）读数是界限：在顶上的至少这么高，在底下的至多这么高（S3）" if res["stuck"] else ""}
    _write(pub / "summary.json", out)
    return out


class _TooManyVoid(Exception):
    pass


def _stopping_evaluation():
    from ladder.evaluator import Evaluation

    class Stopping(Evaluation):
        """The locked evaluator plays void games again until a decided one comes (up to 50 rounds): with a version
        whose every game is void that holds the arena for hours (11-23 review). Stop once VOID_STOP games are void
        and they are most of those back."""
        budget = approved = None

        def on_result(self, log):
            super().on_result(log)
            void, total = self.counts.get("void", 0), sum(self.counts.values())
            if void >= VOID_STOP and void * 2 > total:
                raise _TooManyVoid(f"练习停下了：{void} 局作废，比打完的一半还多（多半是你的打法在对局里碰了不许碰的东西，"
                                   "或者对局里出错）。用 vs 对基线成员打几局，games.jsonl 里作废的局写着原因")
            if self.budget and total >= self.budget and not self.done():
                raise _TooManyVoid(f"练习停下了：作废和平局的局要补打，打到 {total} 局（批的 {self.approved} 局加补打余量）"
                                   f"还没打完（其中作废 {void} 局）。用 vs 对基线成员打几局，games.jsonl 里作废的局写着原因")
    return Stopping


def _StoppingEvaluation(*a, **k):
    return _stopping_evaluation()(*a, **k)


def _from_position(job: dict, beat=None) -> dict:
    """A runner.guarded_map task: the logged game up to its `upto` move, then played on (continuation `cont`: None
    keeps the deal and the generator as they were; an int reshuffles the unseen deck order of both sides and
    reseeds the generator)."""
    from ladder.runner import host_ctrl_c
    with host_ctrl_c():                               # only a real Ctrl+C stops the resume run (fourth pass)
        return _play_on(job, beat)


def _play_on(job: dict, beat=None) -> dict:
    from ladder import base
    from ladder.runner import _make_counter, host_interrupt, legal_choice, load_strategies, offer, safe_repr, tb
    from svsim.core.actions import from_dict, to_dict
    from svsim.core.engine import apply, legal_actions
    from ladder import deal
    counter, unit = _make_counter()
    _, state = deal.start(job)
    tracker = base.Tracker(state)
    for data in job["prefix"]:
        tracker.before(state)
        apply(state, from_dict(data))
        tracker.after(state)
    if job["cont"] is not None:
        r = random.Random(job["cont"])
        for p in state.players:
            d = [c.copy() for c in p.deck_view()]
            r.shuffle(d)
            p.deck = d
        state.rng.seed(r.getrandbits(64))
    out = {"id": job["id"], "result": None, "winner": None, "loser": None, "cpu_unit": unit,
           "steps": [list(s) for s in job["prefix_steps"]], "actions": list(job["prefix"])}
    try:
        strategies = load_strategies(job["strategies"], job["strategy_seeds"], beat)   # on the load clock (LD-40)
    except BaseException as e:                        # as the runner (LD-36)
        if host_interrupt(e):
            raise
        out.update(result="void", error="strategy failed to load:\n" + tb(5))
        return out
    while not state.over:
        seat = state.active
        actions = legal_actions(state)
        pos = base.public_position(state, seat, tracker)
        c0 = counter()
        if beat is not None:                          # the step clock, as in the runner (LD-40)
            beat[0], beat[1] = seat, time.monotonic_ns()
        try:
            try:
                action = strategies[seat].act(pos, offer(actions))   # fresh copies, as in the runner (fourth pass)
            except BaseException as e:                # SystemExit too: the strategy's crash, as in the runner (LD-36)
                if host_interrupt(e):
                    raise
                out.update(result="crash", loser=seat, winner=1 - seat, error=tb())
                break
            out["steps"].append([seat, counter() - c0, 0])
            chosen = legal_choice(action, actions)    # as in the runner (LD-37), still on the clock
            shown = safe_repr(action) if chosen is None else None     # its repr is the strategy's code (LD-41)
        finally:
            if beat is not None:
                beat[1] = 0
        if chosen is None:
            out.update(result="illegal", loser=seat, winner=1 - seat, error=shown)
            break
        action = chosen
        out["actions"].append(to_dict(action))
        tracker.before(state)
        apply(state, action)
        tracker.after(state)
    if out["result"] is None:
        out["winner"] = state.winner if state.winner in (0, 1) else None
        out["result"] = "normal" if out["winner"] is not None else "draw"
    out["turns"] = state.turn
    out["first"] = state.first
    return out


def _resumed(job: dict, g: dict | None) -> dict:
    """guarded_map's result for one continuation, as a game log: a hang loses by timeout (on loading it is void, as
    in the runner), a dead worker is void, and so is a game during which the simulator changed (LD-40) or a strategy's
    code tried what a game may not do (LD-52)."""
    from ladder.runner import IDLE, LOAD, clean
    g = g or {"died": None}
    if "value" in g:
        log = g["value"]
    elif "timeout" in g and g["timeout"] in (0, 1):
        s = g["timeout"]
        log = {"id": job["id"], "result": "timeout", "loser": s, "winner": 1 - s, "error": g.get("error")}
    elif "timeout" in g:
        what = {LOAD: "loading the strategies", IDLE: "the worker, with no clock on:"}.get(g["timeout"],
                                                                                         "the check after the game")
        log = {"id": job["id"], "result": "void", "winner": None, "loser": None, "error": f"{what} {g.get('error')}"}
    elif "died" in g:
        log = {"id": job["id"], "result": "void", "winner": None, "loser": None,
               "error": f"worker died (exit code {g['died']})"}
    else:
        log = {"id": job["id"], "result": "void", "winner": None, "loser": None, "error": g.get("error")}
    if g.get("changed") or g.get("blocked"):
        from ladder.runner import BLOCKED, CHANGED
        why = ([BLOCKED + g["blocked"]] if g.get("blocked") else []) + ([CHANGED + g["changed"]] if g.get("changed")
                                                                       else [])
        log = dict(log, voided_result=log.get("result"), voided_winner=log.get("winner"), result="void", winner=None,
                   loser=None, error=clean(" | ".join(why)))
    return log


def run_resume(arena: Path, player: str, run_id: str, game: str, decision: int, version_dirs: list,
               continuations: int, rng_seed: int | None = None) -> dict:
    from ladder.runner import guarded_map
    seat = Seat(arena, player)
    versions = [seat.version(d) for d in version_dirs]
    if not 1 <= len(versions) <= 2:
        raise ArenaError("给一个或两个版本")
    seat.this_field(run_id, "续打")
    src = next((g for g in _jsonl(seat.priv / run_id / "games.jsonl") if g["id"] == game), None)
    if src is None or "actions" not in src:
        raise ArenaError(f"{run_id} 里没有 {game}（或那一局没有完整的走法）")
    if "decks" not in src:
        raise ArenaError("续打出来的局不能再续打；从原来那一局开始续打")
    starts = {s["id"]: s for s in _jsonl(seat.priv / run_id / "starts.jsonl")}
    jobs_meta = _read(seat.priv / run_id / "jobs.json") if (seat.priv / run_id / "jobs.json").exists() else None
    if game in starts:
        me = starts[game]["cand_seat"]
    elif jobs_meta:
        me = next(p["seat"] for p in jobs_meta["plan"] if f"{run_id}-{p['i']:05d}" == game)
    else:
        raise ArenaError("找不到你在那一局坐哪边")
    mine = [i for i, s in enumerate(src["steps"]) if s[0] == me]
    if not 0 <= decision < len(mine):
        raise ArenaError(f"那一局你一共做了 {len(mine)} 个决定（从 0 数）")
    upto = mine[decision]
    if any(sorted(v["deck"]) != sorted(src["decks"][me]) for v in versions):
        raise ArenaError("续打的版本要用原来那副卡组")
    if continuations < 0:
        raise ArenaError("--continuations 不能是负数（0 = 只重打原来那一局）")
    total = (continuations + 1) * len(versions)
    seat.check_window(total)
    rng = random.Random(rng_seed if rng_seed is not None else secrets.randbits(64))
    conts = [None] + [rng.randrange(2 ** 62) for _ in range(continuations)]
    sseeds = [[rng.randrange(1, 2 ** 62), rng.randrange(1, 2 ** 62)] for _ in conts]   # as wide as a ladder's
    lock = _locked(seat, total)
    try:
        rid, pub, priv = seat.new_run("resume")
        jobs = []
        for vi, v in enumerate(versions):
            for ci, (c, ss) in enumerate(zip(conts, sseeds)):
                strategies = list(src["strategies"])
                strategies[me] = v["spec"]
                jobs.append({"id": f"{rid}-v{vi}-c{ci:04d}", "decks": src["decks"], "seed": src["seed"],
                             "deal": src.get("deal"),
                             "first_arg": src.get("first_arg"), "prefix": src["actions"][:upto],
                             "prefix_steps": src["steps"][:upto], "cont": c, "strategies": strategies,
                             "strategy_seeds": ss})
        _write(priv / "jobs.json", {"from": [run_id, game, decision, upto], "versions": versions, "conts": conts})
        cfg = _cfg(seat)
        paths = [str(ROOT), str(LADDER), str(seat.priv / "code"), str(seat.code)]
        got = guarded_map("ladder.arena:_from_position", jobs, workers=min(cfg["workers"], len(jobs)),
                          mask=cfg["mask"], paths=paths)
        logs = [_resumed(j, g) for j, g in zip(jobs, got)]
        seat.count(rid, "resume", len(logs))
    finally:
        _unlock(lock)
    host_opp = not str(src["strategies"][1 - me]).startswith("py:")
    if game in starts:
        opp_pub = seat.opp_public("member", seat.by_mid[starts[game]["opp"]])
    else:
        p = next(p for p in jobs_meta["plan"] if f"{run_id}-{p['i']:05d}" == game)
        opp_pub = seat.opp_public("member", seat.by_mid[p["opp"]]) if p["kind"] == "member" \
            else seat.opp_public(*seat.by_id[p["opp"]])
    results = {}
    for log in logs:
        _append(priv / "games.jsonl", log)
        _append(pub / "games.jsonl", own_view(log, me, opp_pub, host_opp))
        vi = int(log["id"].split("-v")[1].split("-")[0])
        results.setdefault(vi, []).append(1 if log.get("winner") == me else 0)
    out = {"run": rid, "kind": "resume", "from": {"run": run_id, "game": game, "decision": decision},
           "continuations": continuations, "versions": [v["sha"] for v in versions],
           "wins": {str(k): sum(x) for k, x in results.items()}, "games_each": continuations + 1,
           "original_continuation": {str(k): x[0] for k, x in results.items()}}
    if len(versions) == 2:
        out["paired"] = _paired(results[1], results[0])        # the second version against the first
    _write(pub / "summary.json", out)
    return out


def _my_seat(seat: Seat, run_id: str, g: dict) -> int:
    """Which side of game `g` (the host's log line) was the player's: from the host's own records of the run."""
    if "view_seat" in g:                                   # formal games (formal() writes it)
        return g["view_seat"]
    starts = {s["id"]: s for s in _jsonl(seat.priv / run_id / "starts.jsonl")}
    if g["id"] in starts:                                  # ladder runs
        return starts[g["id"]]["cand_seat"]
    jp = seat.priv / run_id / "jobs.json"
    if jp.exists():                                        # vs runs
        for p in _read(jp).get("plan", []):
            if f"{run_id}-{p['i']:05d}" == g["id"]:
                return p["seat"]
    if (g.get("labels") or {}).get("seat") in (0, 1):
        return g["labels"]["seat"]
    raise ArenaError("找不到你在那一局坐哪边")


def replay(arena: Path, player: str, run_id: str, game: str) -> Path:
    """The player's own public view at each of their decisions in one of their games, with every move."""
    from ladder import base
    from ladder.runner import load_deck
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply
    seat = Seat(arena, player)
    if not RUN_ID.fullmatch(str(run_id)):
        raise ArenaError(f"没有这个编号：{run_id}")
    g = next((x for x in _jsonl(seat.priv / run_id / "games.jsonl") if x["id"] == game), None)
    view = next((x for x in _jsonl(seat.pub / "runs" / run_id / "games.jsonl") if x["game"] == game), None)
    if g is None or view is None:
        raise ArenaError(f"{run_id} 里没有你的 {game}")
    if "decks" not in g:
        raise ArenaError("续打出来的局不能回放（续打点之后重新洗了牌）；回放原来那一局")
    me = _my_seat(seat, run_id, g)             # from the host's records, never the player's view file (11-23 review)
    from ladder import deal
    _, state = deal.start(g)
    tracker = base.Tracker(state)
    steps, k = [], 0
    for step, data in zip(g.get("steps", []), g.get("actions", [])):
        if step[0] == me:
            steps.append({"decision": k, "view": base.public_position(state, me, tracker).observation(),
                          "move": data})
            k += 1
        else:
            steps.append({"opponent_move": {"type": "Mulligan"} if data.get("type") == "Mulligan" else data})
        tracker.before(state)
        apply(state, from_dict(data))
        tracker.after(state)
    end = base.public_position(state, me, tracker).observation()
    out = seat.pub / "runs" / run_id / f"replay-{game}.json"
    _write(out, {"game": game, "seat": me, "opponent": view["opponent"], "result": view["result"],
                 "won": view["won"], "steps": steps, "end": end})
    return out


# --- the host's side, end of a period: each player's own formal games (A53) -------------------------------------

def formal(arena: Path, pool_dir: Path, subs_dir: Path, period: int) -> dict:
    """End of period `period`, host side (A53). For each player: their own members (the member name they gave ->
    the anonymous id, the class, still in the pool or not) in ARENA/players/<name>/members.json, and every formal
    ladder game of the period one of those members played, the player's side only (`own_view`: the opponent's
    anonymous id and class, its moves as a human sees them), as the run F<period>. `replay` works on it; it can't
    be resumed or played again with --same-as (`Seat.this_field`). A game between two of the player's own members
    gives two views. The games are renumbered F<period>-00001...: the pool's ids count every game of the pool.
    Written again (the same) if called again; never another player's members or games."""
    from ladder.pool import CRAFT_ZH, Pool
    from ladder.submit import ledger
    pool = Pool(pool_dir)
    lines = ledger(subs_dir)
    games = [g for g in _jsonl(Path(pool_dir) / "games.jsonl") if (g.get("labels") or {}).get("period") == period]
    arena, rid, out = Path(arena), f"F{period}", {}
    for player, py in FOLDER.items():
        names = {l["mid"]: l["member"] for l in lines if l.get("ev") == "admit" and l.get("player") == player}
        mine = {mid: m for mid, m in pool.members.items() if m.owner == player}
        if not mine:
            continue
        pub_dir, priv_dir = arena / "players" / player, arena / "host" / "players" / py
        rows = [{"member": names.get(mid), "id": m.anon, "class": CRAFT_ZH[m.craft], "in_pool": m.active}
                for mid, m in sorted(mine.items(), key=lambda x: (x[1].craft, names.get(x[0]) or "", x[1].anon))]
        _write(pub_dir / "members.json", {"after_period": period, "members": rows})
        pub, priv = pub_dir / "runs" / rid, priv_dir / rid
        for f in (pub / "games.jsonl", priv / "games.jsonl"):
            if f.exists():
                f.unlink()
        k, per = 0, {}
        for g in games:
            lab = g["labels"]
            for s in (0, 1):
                if lab["members"][s] not in mine:
                    continue
                k += 1
                vid = f"{rid}-{k:05d}"
                o = lab["members"][1 - s]
                opp = {"id": lab["anon"][1 - s], "class": CRAFT_ZH[pool.members[o].craft]}
                line = dict(g, id=vid, pool_game=g["id"], view_seat=s)
                view = dict(own_view(line, s, opp), member=lab["anon"][s])
                _append(priv / "games.jsonl", line)
                _append(pub / "games.jsonl", view)
                c = per.setdefault(lab["anon"][s], {"games": 0, "decided": 0, "wins": 0})
                c["games"] += 1
                c["decided"] += view["won"] is not None
                c["wins"] += bool(view["won"])
        _write(priv / "run.json", {"run": rid, "kind": "formal", "period": period, "field": None,
                                    "time": _iso(_now())})
        summary = {"run": rid, "kind": "formal", "period": period, "games": k, "members": per}
        _write(pub / "summary.json", summary)
        out[player] = {"members": len(rows), "games": k}
    return out


def main(argv=None):
    for s in (sys.stdout, sys.stderr):           # a redirected or piped console is cp1252 on Windows (ENVIRONMENT
        try:                                      # pitfall 1; 11-23 review: a player's agent pipes the output)
            s.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:                         # noqa: BLE001
            pass
    ap = argparse.ArgumentParser(prog="python -m ladder.arena")
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("snapshot")
    a.add_argument("pool")
    a.add_argument("--arena", required=True)
    a.add_argument("--anchors")
    a.add_argument("--code", help="the received strategies (C:\\claude\\ladder-host\\subs\\code)")
    a = sp.add_parser("formal")
    a.add_argument("arena")
    a.add_argument("--pool", required=True)
    a.add_argument("--subs", required=True)
    a.add_argument("--period", type=int, required=True)
    a = sp.add_parser("open")
    a.add_argument("arena")
    a.add_argument("--hours", type=float, required=True)
    a.add_argument("--games", type=int, required=True)
    a.add_argument("--workers", type=int, default=11)
    a.add_argument("--mask", type=lambda x: int(x, 0))
    for name in ("field", "ladder", "vs", "resume", "replay"):
        a = sp.add_parser(name)
        a.add_argument("arena")
        a.add_argument("--player", required=True)
        if name in ("ladder", "vs"):
            a.add_argument("--version", required=True)
        if name == "ladder":
            a.add_argument("--replacing")
            a.add_argument("--games", type=int, default=600)
            a.add_argument("--tail", type=int, default=300)
            a.add_argument("--repeats", type=int, default=3)
        if name == "vs":
            a.add_argument("--opponent")
            a.add_argument("--class", dest="craft")
            a.add_argument("--games", type=int, default=200)
            a.add_argument("--same-as")
        if name in ("resume", "replay"):
            a.add_argument("--run", required=True)
            a.add_argument("--game", required=True)
        if name == "resume":
            a.add_argument("--decision", type=int, required=True)
            a.add_argument("--version", action="append", required=True)
            a.add_argument("--continuations", type=int, default=50)
    args = ap.parse_args(argv)
    try:
        if args.cmd == "snapshot":
            out = public_field(snapshot(Path(args.pool), Path(args.arena), Path(args.anchors) if args.anchors else None,
                                        code=Path(args.code) if args.code else None))
        elif args.cmd == "formal":
            out = formal(Path(args.arena), Path(args.pool), Path(args.subs), args.period)
        elif args.cmd == "open":
            out = open_window(Path(args.arena), args.hours, args.games, args.workers, args.mask)
        elif args.cmd == "field":
            s = Seat(Path(args.arena), args.player)
            out = {**public_field(s.host), "window": s.window, "used": s.used()}
        elif args.cmd == "ladder":
            out = run_ladder(Path(args.arena), args.player, Path(args.version), args.replacing, args.games,
                             args.tail, args.repeats)
        elif args.cmd == "vs":
            out = run_vs(Path(args.arena), args.player, Path(args.version), args.games, args.opponent, args.craft,
                         args.same_as)
        elif args.cmd == "resume":
            out = run_resume(Path(args.arena), args.player, args.run, args.game, args.decision,
                             [Path(x) for x in args.version], args.continuations)
        else:
            out = {"replay": str(replay(Path(args.arena), args.player, args.run, args.game))}
    except ArenaError as e:
        print(f"没跑：{e}", file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=1))
    if isinstance(out, dict) and out.get("stopped"):
        print(f"停下了：{out['stopped']}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
