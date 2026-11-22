"""The practice arena (phase 2, item 2.4): a frozen copy of this period's pool plus the anchors, tuning seeds only,
resuming from a position of one's own game, a game count per player and period.

Host:
    python -m ladder.arena snapshot POOLDIR --arena ARENA [--anchors ANCHORS.json]
    python -m ladder.arena open     ARENA --hours 4 --games 20000 [--workers 23]
Players (each command is one run; what a player may read is under ARENA/players/<code>/, nothing else):
    python -m ladder.arena field    ARENA --player 甲
    python -m ladder.arena ladder   ARENA --player 甲 --version DIR [--replacing ANON] [--games 600 --tail 300 --repeats 3]
    python -m ladder.arena vs       ARENA --player 甲 --version DIR (--opponent ID | --class 精灵) --games N [--same-as RUN]
    python -m ladder.arena resume   ARENA --player 甲 --run RUN --game GAME --decision K --version DIR [--version DIR2]
                                    --continuations N
    python -m ladder.arena replay   ARENA --player 甲 --run RUN --game GAME

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
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
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
PLAYER_SEEDS = {"甲": (87400000, 87580000), "乙": (87580000, 87760000), "丙": (87760000, 87940000),
                "丁": (87940000, 88120000), "戊": (88120000, 88300000)}           # A34
PINYIN = {"甲": "jia", "乙": "yi", "丙": "bing", "丁": "ding", "戊": "wu"}
CRAFT_BY_ZH = {"精灵": 1, "皇家护卫": 2, "巫师": 3, "龙族": 4, "梦魇": 5, "主教": 6, "超越者": 7}


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
    p = Path(p)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _append(p: Path, rec: dict):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# --- the host's side: the frozen copy and the window -----------------------------------------------------------

def snapshot(pool_dir: Path, arena: Path, anchors: Path | None = None, cr: str = "last1000") -> dict:
    """This period's frozen copy of the pool (the evaluator's freeze, plus each member's owner, kept host side) and
    the anchors. Writes ARENA/host/field.json, ARENA/host/frozen.json (the evaluator's format) and the public
    ARENA/public/field.json."""
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
    host = {"version": ARENA_VERSION, "time": _iso(_now()), "pool": str(pool_dir), "period": body["period"],
            "hash": body["hash"], "mu": mu,
            # in anon order: the pool's own order (mid) is the order members were admitted, by player (red line)
            "members": sorted((dict(m, owner=owners.get(m["mid"])) for m in body["members"]), key=lambda m: m["anon"]),
            "anchors": anchor_rows}
    arena = Path(arena)
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
            raise ArenaError(f"没有代号 {player}（{'、'.join(PLAYER_SEEDS)}）")
        self.arena, self.player = Path(arena), player
        self.host = _read(self.arena / "host" / "field.json")
        win = self.arena / "public" / "window.json"
        self.window = _read(win) if win.exists() else None
        self.pub = self.arena / "players" / player
        self.priv = self.arena / "host" / "players" / PINYIN[player]
        self.count_path = self.pub / "count.jsonl"
        self.seeds = PLAYER_SEEDS[player]
        self.by_id = {m["anon"]: ("member", m) for m in self.host["members"]}
        self.by_id.update({a["id"]: ("anchor", a) for a in self.host["anchors"]})
        self.by_mid = {m["mid"]: m for m in self.host["members"]}

    # what the player may see of an opponent
    def opp_public(self, kind: str, row: dict) -> dict:
        from ladder.pool import CRAFT_ZH
        if kind == "member":
            return {"id": row["anon"], "class": CRAFT_ZH[row["craft"]], "rel_cr": round(row["cr"] - self.host["mu"])}
        return {"id": row["id"], "name": row["name"], "class": CRAFT_ZH[row["craft"]]}

    def used(self) -> int:
        return sum(r["games"] for r in _jsonl(self.count_path) if r.get("period") == self.host["period"])

    def check_window(self, games: int):
        if self.window is None or self.window["field"] != self.host["hash"]:
            raise ArenaError("这一期的练习场还没开")
        if _now() > datetime.fromisoformat(self.window["deadline"]):
            raise ArenaError(f"这一期的练习时间到了（{self.window['deadline']}）")
        left = self.window["games"] - self.used()
        if games > left:
            raise ArenaError(f"这一期还剩 {left} 局，这次要打 {games} 局")

    def new_run(self, kind: str) -> tuple[str, Path, Path]:
        runs = sorted(p.name for p in (self.pub / "runs").glob("R*")) if (self.pub / "runs").exists() else []
        rid = f"R{len(runs) + 1:04d}"
        pub, priv = self.pub / "runs" / rid, self.priv / rid
        pub.mkdir(parents=True)
        priv.mkdir(parents=True)
        return rid, pub, priv

    def count(self, rid: str, kind: str, games: int):
        _append(self.count_path, {"run": rid, "kind": kind, "period": self.host["period"], "games": games,
                                  "time": _iso(_now())})

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
        name = f"arena_{PINYIN[self.player]}_{h}"
        code = self.priv / "code"
        code.mkdir(parents=True, exist_ok=True)
        (code / f"{name}.py").write_text(src, encoding="utf-8")
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


def _unlock(f):
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
        f.close()


# --- the player's view of a game --------------------------------------------------------------------------------

def own_view(log: dict, seat: int, opp: dict) -> dict:
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
            "error": log.get("error") if log.get("loser") == seat else None, "moves": acts}


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
    k = seat.arena / "host" / "arena.key"
    return {"workers": w.get("workers", 4), "mask": w.get("mask"), "key": str(k) if k.exists() else None}


def run_vs(arena: Path, player: str, version_dir: Path, games: int, opponent: str | None = None,
           craft_zh: str | None = None, same_as: str | None = None, rng_seed: int | None = None) -> dict:
    from ladder.runner import run
    seat = Seat(arena, player)
    v = seat.version(version_dir)
    rng = random.Random(rng_seed if rng_seed is not None else secrets.randbits(64))
    if same_as:
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
                         "sseeds": [rng.randrange(1, 2 ** 31), rng.randrange(1, 2 ** 31)]})
    seat.check_window(games)
    rid, pub, priv = seat.new_run("vs")
    jobs = []
    for p in plan:
        row = seat.by_mid[p["opp"]] if p["kind"] == "member" else seat.by_id[p["opp"]][1]
        sides = [(v["deck"], v["spec"]), (row["deck"], row["strategy"])]
        if p["seat"] == 1:
            sides.reverse()
        jobs.append({"id": f"{rid}-{p['i']:05d}", "seed": p["seed"], "first": None, "decks": [d for d, _ in sides],
                     "strategies": [s for _, s in sides], "strategy_seeds": p["sseeds"],
                     "labels": {"run": rid, "seat": p["seat"]}})
    _write(priv / "jobs.json", {"plan": plan, "version": v, "same_as": same_as})
    lock = _lock(arena)
    try:
        cfg = _cfg(seat)
        run(jobs, str(priv / "games.jsonl"), workers=cfg["workers"], mask=cfg["mask"], quiet=True, key=cfg["key"])
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
    seat.count(rid, "vs", n)
    decided = [v_ for v_ in views if v_["won"] is not None]
    w = sum(1 for v_ in decided if v_["won"])
    p_, lo, hi = _wilson(w, len(decided))
    out = {"run": rid, "kind": "vs", "version": v["sha"], "games": n, "decided": len(decided), "wins": w,
           "win_rate": round(p_, 4), "lo": round(lo, 4), "hi": round(hi, 4), "same_as": same_as,
           "errors": sum(1 for v_ in views if v_["error"])}
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
    from ladder.evaluator import Candidate, Evaluation
    seat = Seat(arena, player)
    v = seat.version(version_dir)
    seat.check_window(games * repeats)
    mid = "outside"
    if replacing:
        kind, row = seat.by_id.get(replacing, (None, None))
        if kind != "member" or row.get("owner") != player:
            raise ArenaError(f"{replacing} 不是你的成员")
        mid = row["mid"]
    from ladder import base
    from ladder.runner import load_deck
    cand = Candidate(mid, int(base.craft_of(load_deck(v["deck"]))), v["deck"], v["spec"])
    rid, pub, priv = seat.new_run("ladder")
    ev = Evaluation(seat.arena / "host" / "frozen.json", priv, cand, seat.seeds, games=games, tail=tail,
                    repeats=repeats, rng_seed=rng_seed if rng_seed is not None else secrets.randbits(48))
    lock = _lock(arena)
    try:
        cfg = _cfg(seat)
        res = ev.run(workers=cfg["workers"], mask=cfg["mask"], key=cfg["key"])
    finally:
        _unlock(lock)
    starts = {s["id"]: s for s in _jsonl(priv / "starts.jsonl")}
    n = 0
    for g in _jsonl(priv / "games.jsonl"):
        st = starts.get(g["id"])
        if st is None:
            continue
        n += 1
        _append(pub / "games.jsonl", own_view(g, st["cand_seat"],
                                              seat.opp_public("member", seat.by_mid[st["opp"]])))
    seat.count(rid, "ladder", n)
    out = {"run": rid, "kind": "ladder", "version": v["sha"], "replacing": replacing, "games": n,
           "rel_cr": round(res["rel_cr"], 1), "lo": round(res["lo"], 1), "hi": round(res["hi"], 1),
           "repeats": res["repeats"], "values": [round(x, 1) for x in res["values"]],
           "stuck": [{k: s[k] for k in ("rep", "after", "side")} for s in res["stuck"]],
           "note": "停住的重复（stuck）读数是界限：在顶上的至少这么高，在底下的至多这么高（S3）" if res["stuck"] else ""}
    _write(pub / "summary.json", out)
    return out


def _from_position(job: dict) -> dict:
    """A worker: the logged game up to its `upto` move, then played on (continuation `cont`: None keeps the deal and
    the generator as they were; an int reshuffles the unseen deck order of both sides and reseeds the generator)."""
    import traceback
    from ladder import base
    from ladder.runner import _make_counter, load_deck, make_strategy
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
        strategies = [make_strategy(s, x) for s, x in zip(job["strategies"], job["strategy_seeds"])]
    except Exception:
        out.update(result="void", error="strategy failed to load:\n" + traceback.format_exc(limit=5))
        return out
    while not state.over:
        seat = state.active
        actions = legal_actions(state)
        pos = base.public_position(state, seat, tracker)
        c0 = counter()
        try:
            action = strategies[seat].act(pos, actions)
        except Exception:
            out.update(result="crash", loser=seat, winner=1 - seat, error=traceback.format_exc(limit=8))
            break
        out["steps"].append([seat, counter() - c0, 0])
        if action not in actions:
            out.update(result="illegal", loser=seat, winner=1 - seat, error=repr(action))
            break
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


def _init_worker(mask, paths):
    for p in paths:
        if p not in sys.path:
            sys.path.insert(0, p)
    from ladder.runner import _limit
    _limit(mask)


def run_resume(arena: Path, player: str, run_id: str, game: str, decision: int, version_dirs: list,
               continuations: int, rng_seed: int | None = None) -> dict:
    import concurrent.futures as cf
    import multiprocessing as mp
    seat = Seat(arena, player)
    versions = [seat.version(d) for d in version_dirs]
    if not 1 <= len(versions) <= 2:
        raise ArenaError("给一个或两个版本")
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
    total = (continuations + 1) * len(versions)
    seat.check_window(total)
    rid, pub, priv = seat.new_run("resume")
    rng = random.Random(rng_seed if rng_seed is not None else secrets.randbits(64))
    conts = [None] + [rng.randrange(2 ** 62) for _ in range(continuations)]
    sseeds = [[rng.randrange(1, 2 ** 31), rng.randrange(1, 2 ** 31)] for _ in conts]
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
    lock = _lock(arena)
    try:
        cfg = _cfg(seat)
        paths = [str(ROOT), str(LADDER), str(seat.priv / "code")]
        with cf.ProcessPoolExecutor(max_workers=min(cfg["workers"], len(jobs)), mp_context=mp.get_context("spawn"),
                                    initializer=_init_worker, initargs=(cfg["mask"], paths)) as ex:
            logs = list(ex.map(_from_position, jobs))
    finally:
        _unlock(lock)
    seat.count(rid, "resume", len(logs))
    if game in starts:
        opp_pub = seat.opp_public("member", seat.by_mid[starts[game]["opp"]])
    else:
        p = next(p for p in jobs_meta["plan"] if f"{run_id}-{p['i']:05d}" == game)
        opp_pub = seat.opp_public("member", seat.by_mid[p["opp"]]) if p["kind"] == "member" \
            else seat.opp_public(*seat.by_id[p["opp"]])
    results = {}
    for log in logs:
        _append(priv / "games.jsonl", log)
        _append(pub / "games.jsonl", own_view(log, me, opp_pub))
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


def replay(arena: Path, player: str, run_id: str, game: str) -> Path:
    """The player's own public view at each of their decisions in one of their games, with every move."""
    from ladder import base
    from ladder.runner import load_deck
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply
    seat = Seat(arena, player)
    g = next((x for x in _jsonl(seat.priv / run_id / "games.jsonl") if x["id"] == game), None)
    view = next((x for x in _jsonl(seat.pub / "runs" / run_id / "games.jsonl") if x["game"] == game), None)
    if g is None or view is None:
        raise ArenaError(f"{run_id} 里没有你的 {game}")
    me = view["seat"]
    if "decks" not in g:
        raise ArenaError("续打出来的局不能回放（续打点之后重新洗了牌）；回放原来那一局")
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


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ladder.arena")
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("snapshot")
    a.add_argument("pool")
    a.add_argument("--arena", required=True)
    a.add_argument("--anchors")
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
            out = public_field(snapshot(Path(args.pool), Path(args.arena), Path(args.anchors) if args.anchors else None))
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
