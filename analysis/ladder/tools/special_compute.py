"""Period 4's compute check (plan 4.5; Salem 11-27 22:51Z, compute by turns): the round robin's games
(tools/special_rr.py) measured as the receipt and the pool's period-end check measure, the default strategy asked and
timed on each member's own positions. For the host and Salem only: nothing is decided here, no player gets a receipt.

    python analysis/ladder/tools/special_compute.py [--period 4] [--host C:\\claude\\ladder-host]
        [--arena C:\\claude\\ladder-arena] [--workers 23] [--mask 0x...] [--per-member 30] [--calibration 60] [--dry]

The period's decks never enter the pool, so ladder.compute_audit never sees them: the receipt measured each once, on
smoke games, and a turn-start budget makes spending less there (LD-57) worth more. This looks at the real games.

1. members: the formal round robin's (HOST/special/P<P>/rr-plan.json), checked against the ledger as special_rr
   --report checks them, and the round robin complete (its formal rr-result.json). Measured once: with
   HOST/special/P<P>/compute.json there it stops (a second measure could flip a member near the line; close_period
   keeps compute-P<P>.json the same way).
2. the draw: of each member's round-robin games that ended (normal or a draw) with a decision of its seat, at most
   `per_member` (PER_MEMBER), a fixed draw (the period, the member and its receipt: no choice of the host's). A game
   drawn for both of its members is replayed for each.
3. calibration: the round robin has no game of the default's, so `calibration` (CAL_GAMES) games of the default
   against itself are played in the same batch, on the three blueprints (ladder.special) paired as in the round robin
   (the 9 ordered pairs of classes, seed i on pair i % 9: a mirror a third of the time), each seed twice with the
   decks swapped; seeds CAL_SEEDS[P] + i (period 4: 96600000 + i of the registered 96600000-96609999), dealt with the
   host's key (required, as for special_rr's formal run: deal.py's FORMAL list doesn't hold the range). Their game
   over replay is the batch's machine factor c (the receipt's twin over its shadow).
4. two runs of runner.guarded_map, both under the arena's lock as the host (D2), both on the round robin's own
   settings, its workers (23) and its cores (all of them, S10; not the E-cores alone as compute_audit's replays):
   a. the calibration games played, games only as in the round robin (after one warm-up game per worker that is
      dropped: a worker's first game is the slow one, and the round robin's workers played thousands): they stand for
      the round robin's conditions, which no replay can see (the logs' "limits" are compared and a difference is
      written);
   b. the replays, the members' and the calibration games' shuffled together after one warm-up calibration replay per
      worker (compute_audit.run_order; LD-68 ⑤), each its own task as compute_audit's and the receipt's shadows are
      (the worker resets the caches before each). A calibration game replayed in its own task right after it was
      played (11-28 review: the run before this) found the caches warm from the game: its replay came out ~10%
      cheaper than a member's, c that much too high and every member's numbers that much too low.
   Only host code runs, never a member's.
5. numbers: each replay split by turns with submit.shadow_parts (a game paired with itself: a member's replay keeps
   its seat's side, a calibration game the twin side of both seats) and pooled with submit.turn_budget, as the
   receipt does: all (the old rule's), in_turn, turn_start_q (K = submit.TURN_K), extra_turns, per_turn,
   u_twin_ratio (against the calibration games' turns), turn_start_wall_max_s (the round robin's own wall clock).
   90% intervals as compute_audit.interval (the member's games and the calibration games resampled); over:
   compute_audit.over_both (clearly over both rules); old_over: the old line alone; rule_point: the rule the point
   numbers pass on (submit.compute_verdict). The receipt's own numbers next to them.
6. HOST/special/P<P>/compute.json and compute.md (with the players' names), the calibration games' logs in
   HOST/special/P<P>/compute/calibration.jsonl. --dry: the plan only, nothing played or written.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = LADDER.parents[1]
sys.path[:0] = [str(HERE), str(LADDER), str(ROOT)]

import special_rr as R

CAL_SEEDS = {4: (96600000, 96610000)}   # SEEDS.md (the host's third probe range, 11-27): the formal check's
                                        # calibration games only, never a test's
PER_MEMBER = 30                         # games replayed a member, at most (compute_audit's)
CAL_GAMES = 60                          # calibration games (compute_audit's count), two a seed
MIN_CAL = 10                            # fewer calibration games back: no ratios (compute_audit's)
OK = ("normal", "draw")
NAME = "compute"
COMBOS = [(a, b) for a, _, _ in R.ARCH for b, _, _ in R.ARCH]     # the round robin's pairs of classes, in order
RULE_ZH = {"old": "老规矩", "turn": "按回合", None: "两条都没过"}


def _rd(x, n=3):
    return None if x is None else round(x, n)


# --- the members and their games ------------------------------------------------------------------------------------

def members_of(host: Path, period: int, players) -> tuple[dict, dict, list]:
    """({member name: member} of the formal round robin, its plan, the slots it had no deck for). The plan must be
    what the ledger says now (special_rr --report's check) and the round robin complete (its formal result)."""
    out = R._out_dir(host, period, None)
    pf = out / "rr-plan.json"
    if not pf.exists():
        raise R.EvalError(f"没有 {pf}：第 {period} 期的循环赛还没正式跑过")
    plan = json.loads(pf.read_text(encoding="utf-8"))
    if plan.get("trial") is not None or plan.get("period") != period:
        raise R.EvalError(f"{pf} 不是第 {period} 期正式循环赛的计划")
    try:
        R.saved(host, period)
    except R.EvalError:
        raise R.EvalError(f"第 {period} 期的循环赛还没打完（没有正式的 {out / (R.NAME + '.json')}）：先把 special_rr "
                          "跑完") from None
    cands, _, doubts = R.candidates(host, period, players)
    if doubts:
        raise R.EvalError("台账和卡组对不上，先查清：" + "；".join(doubts))
    now = R.plan_record(period, players, R.layout(players, period), cands, plan.get("key"), plan.get("env"))
    diff = [k for k in now if plan.get(k) != now[k]]
    if diff:
        raise R.EvalError(f"{pf} 和现在的台账、选手名单对不上（{'、'.join(diff)} 不一样）：先查清，不量另一批成员")
    members = {R.slot_name(s): cands[s] for s in R.slots(players) if s in cands}
    return members, plan, [R.slot_name(s) for s in R.slots(players) if s not in cands]


def scan(out: Path, period: int, members: dict) -> tuple[dict, list]:
    """({member: [(game id, seat, file, offset)]}, the "limits" the round robin's logs carry): each member's games on
    its receipt that ended (normal or a draw) with at least one decision of its seat. Only where each line is kept,
    not the line (the round robin's 90000 games)."""
    by = {m: {} for m in members}
    want = {(m, v["receipt"]): m for m, v in members.items()}
    limits = set()
    for f in sorted((out / "games").glob("*.jsonl")):
        with f.open("rb") as fh:
            while True:
                at = fh.tell()
                line = fh.readline()
                if not line:
                    break
                try:
                    g = json.loads(line)
                except ValueError:                   # a torn line: special_rr's count skips it too
                    continue
                if not isinstance(g, dict) or (g.get("labels") or {}).get("rr") != period:
                    continue
                if g.get("limits") is not None:
                    limits.add(json.dumps(g["limits"], sort_keys=True))
                if g.get("result") not in OK or not g.get("steps"):
                    continue
                lab, seats = g["labels"], {s for s, *_ in g["steps"]}
                for seat, key in enumerate(zip(lab.get("members") or (), lab.get("receipts") or ())):
                    m = want.get(key)
                    if m is not None and seat in seats:
                        by[m].setdefault((g["id"], seat), (g["id"], seat, f, at))    # an id's first line, as outcomes
    return {m: sorted(xs.values(), key=lambda x: (x[0], x[1])) for m, xs in by.items()}, \
        [json.loads(x) for x in sorted(limits)]


def draw(by: dict, members: dict, period: int, per_member: int) -> dict:
    """{member: the games replayed}: at most per_member of its games, a fixed draw (the period, the member, its
    receipt)."""
    out = {}
    for m, xs in by.items():
        rng = random.Random(f"special-compute:{period}:{m}:{members[m]['receipt']}")
        out[m] = rng.sample(xs, per_member) if len(xs) > per_member else list(xs)
    return out


def load(picks: dict) -> dict:
    """{(game id, seat): the game's log line} of the games drawn."""
    got = {}
    for xs in picks.values():
        for gid, seat, f, at in xs:
            with Path(f).open("rb") as fh:
                fh.seek(at)
                got[(gid, seat)] = json.loads(fh.readline())
    return got


# --- the calibration games ------------------------------------------------------------------------------------------

def cal_layout(period: int, games: int) -> dict:
    """The calibration's seeds: CAL_SEEDS[P][0] + i for i < ceil(games / 2), each played twice (the decks swapped)."""
    if period not in CAL_SEEDS:
        raise R.EvalError(f"第 {period} 期没有算力抽查校准局的种子（CAL_SEEDS）")
    lo, hi = CAL_SEEDS[period]
    n = math.ceil(games / 2)
    if n < 1 or lo + n > hi:
        raise R.EvalError(f"校准局 {games} 局要 {n} 个种子，{lo}～{hi - 1} 不够（或者局数不对）")
    return {"lo": lo, "hi": hi, "n": n, "used": [lo, lo + n - 1]}


def cal_jobs(period: int, lay: dict) -> list:
    """The default against itself on the period's blueprints: seed i on COMBOS[i % 9], in both seat orders."""
    from ladder import special
    from ladder.submit import DEFAULT
    decks = {}
    for c, _, _ in R.ARCH:
        b = special.blueprint_for(period, c)
        if b is None:
            raise R.EvalError(f"第 {period} 期没有{R.arch_name(c)}的蓝本")
        decks[c] = b["ids"]
    out = []
    for i in range(lay["n"]):
        a, b = COMBOS[i % len(COMBOS)]
        for x, (s0, s1) in enumerate(((a, b), (b, a))):
            out.append({"id": f"C{period}-{i:03d}{'ab'[x]}", "seed": lay["lo"] + i, "first": None,
                        "decks": [decks[s0], decks[s1]], "strategies": [DEFAULT, DEFAULT], "strategy_seeds": None,
                        "labels": {"compute_cal": period, "i": i, "a_seat": x,
                                   "arch": [R.arch_name(s0), R.arch_name(s1)]}})
    return out


def _task(task: dict, beat=None) -> dict:
    """The one task function (runner.guarded_map): a game, a member's or a calibration one, replayed with the default
    on every decision (submit._shadow); or a calibration game played (runner.play_job), only that: its replay is a
    task of its own in the replay run (module step 4)."""
    if task["kind"] == "replay":
        from ladder.submit import _shadow
        return _shadow(task["shadow"], beat)
    from ladder.runner import play_job
    return {"game": play_job(task["job"], beat)}


# --- the numbers ------------------------------------------------------------------------------------------------------

def member_part(g: dict, got: dict, seat: int) -> tuple[dict | None, list]:
    """A member's side of one replay: submit.shadow_parts on the game paired with itself, its seat's numbers kept and
    the twin side emptied (the calibration games give c). The opponent seat is another player's member here, not the
    default: emptied too."""
    parts, bad = _shadow_parts([(g, g, seat)], [got, got])
    if not parts:
        return None, bad
    p = parts[0]
    p.update(row=(p["row"][0], p["row"][1], 0, 0), opp=[0, 0], twin_F=[0, 0], twin_R=[0, 0], U_twin=0, T_twin=0)
    return p, []


def cal_part(g: dict, got: dict) -> tuple[dict | None, list]:
    """A calibration game's twin side, both seats: its game and replay CPU over all decisions (c), their two halves
    (c_parts), the default's CPU and turns over its MAIN decisions (U_twin, T_twin); the member side emptied."""
    two = []
    for seat in (0, 1):
        parts, bad = _shadow_parts([(g, g, seat)], [got, got])
        if not parts:
            return None, bad
        two.append(parts[0])
    p = two[0]
    p.update(row=(0, 0, p["row"][2], p["row"][3]), F=0, R=0, Fd=0, Rd=0, U=0, T=0, turns=[], opp=[0, 0],
             U_twin=two[0]["U_twin"] + two[1]["U_twin"], T_twin=two[0]["T_twin"] + two[1]["T_twin"])
    return p, []


def _shadow_parts(pairs, got):
    from ladder.submit import shadow_parts
    return shadow_parts(pairs, got)


def _c_part(c: float) -> dict:
    """The calibration as one part with game over replay c (for the resampled intervals: turn_budget takes c from
    its parts' twin side)."""
    return {"id": "calibration", "row": (0, 0, c, 1.0), "F": 0, "R": 0, "Fd": 0, "Rd": 0, "U": 0, "T": 0, "turns": [],
            "opp": [0, 0], "twin_F": [0, 0], "twin_R": [0, 0], "U_twin": 0, "T_twin": 0}


def measure(mparts: list, cparts: list, k: int | None = None, draws: int = 4000) -> dict:
    """A member's numbers: submit.turn_budget over its replays and the calibration games (the point), the 90% intervals
    of all, in_turn and turn_start_q as compute_audit.interval draws them, compute_audit.over_both."""
    from ladder import compute_audit as CA
    from ladder.submit import COMPUTE_REFUSE, TURN_K, compute_verdict, turn_budget
    k = TURN_K if k is None else k
    b = turn_budget(mparts + cparts, k)
    cal = [(p["row"][2], p["row"][3]) for p in cparts]
    light = [{**p, "turns": []} for p in mparts]        # the intervals need the sums only

    def stat(name):
        return lambda rows, c: turn_budget(rows + [_c_part(c)], k)[name]
    a90 = CA.interval(light, cal, draws=draws, stat=stat("all"))
    i90 = CA.interval(light, cal, draws=draws, stat=stat("in_turn"))
    q90 = CA.interval(light, cal, draws=draws, stat=stat("turn_start_q"))
    pt = b["per_turn"]
    return {"games": len(mparts), "ratio": _rd(b["all"]), "interval90": list(a90), "in_turn": _rd(b["in_turn"]),
            "interval90_in": list(i90), "turn_start_q": _rd(b["turn_start_q"]), "interval90_q": list(q90),
            "extra_turns": _rd(b["extra_turns"], 2), "turns": b["turns"],
            "per_turn": None if pt is None else {x: (v if x == "turns" else _rd(v, 2)) for x, v in pt.items()},
            "u_twin_ratio": _rd(b["u_twin_ratio"]), "turn_start_wall_max_s": _rd(b["turn_start_wall_max_s"], 2),
            "rule_point": compute_verdict(_rd(b["all"]), b, len(mparts), k)[2],
            "old_over": a90[0] is not None and a90[0] > COMPUTE_REFUSE,
            "over": CA.over_both(a90, i90, q90, k)}


def receipt_numbers(lines: list, rid: str) -> dict | None:
    """What the receipt measured on its smoke games (its line in the ledger, `lines`)."""
    line = next((l for l in reversed(lines) if l.get("ev") == "receipt" and l.get("id") == rid), None)
    if line is None:
        return None
    c = line.get("compute") or {}
    return {"version": line.get("version"), "ratio": line.get("compute_ratio"),
            **{x: c.get(x) for x in ("K", "rule", "in_turn", "turn_start_q", "extra_turns")}}


# --- running ----------------------------------------------------------------------------------------------------------

def dry(host: Path, period: int = 4, per_member: int = PER_MEMBER, calibration: int = CAL_GAMES, players=None,
        key="auto") -> dict:
    """What a run would do: nothing played or written."""
    players = tuple(players or R._players())
    out = R._out_dir(host, period, None)
    members, plan, missing = members_of(host, period, players)
    chk = R._checks(host, period, False, key)
    by, limits = scan(out, period, members)
    picks = draw(by, members, period, per_member)
    lay = cal_layout(period, calibration)
    measured = (out / f"{NAME}.json").exists()
    return {"period": period, "out": str(out / f"{NAME}.json"), "measured": measured,
            "members": {m: {"receipt": members[m]["receipt"], "games": len(by[m]), "drawn": len(picks[m])}
                        for m in members},
            "missing": missing, "replays": sum(len(x) for x in picks.values()),
            "calibration": {"games": 2 * lay["n"], "seeds": lay["used"]}, "rr_limits": limits,
            "key": chk["key"], "rr_key": plan.get("key"), "env": chk["env"], "warnings": chk["warnings"],
            "formal_ready": not chk["warnings"] and not measured}


def check(host: Path, period: int = 4, workers: int = 23, mask=None, per_member: int = PER_MEMBER,
          calibration: int = CAL_GAMES, key="auto", arena: Path | None = None, players=None, log=print,
          step_limit: float = 30.0, draws: int = 4000) -> dict:
    """Measure once and write the report (see the module's steps)."""
    from ladder import compute_audit as CA
    from ladder import deal
    from ladder.runner import _limit, guarded_map, jsonl, provenance
    from ladder.submit import (
        COMPUTE_CAP,
        COMPUTE_REFUSE,
        TURN_K,
        TURN_REFUSE,
        shadow_task,
        turn_budget,
    )
    players = tuple(players or R._players())
    if not 1 <= workers <= 23:
        raise R.EvalError("--workers 要 1～23")
    if per_member < 1:
        raise R.EvalError("--per-member 至少 1")
    out = R._out_dir(host, period, None)
    if (out / f"{NAME}.json").exists():
        raise R.EvalError(f"第 {period} 期的算力抽查已经量过了（{out / (NAME + '.json')}）：量一次就定，不重量（再量一次可能把"
                          "线边上的成员翻过来）；真要重量，先把它挪走")
    members, plan, missing = members_of(host, period, players)
    lay = cal_layout(period, calibration)
    chk = R._checks(host, period, True, key)        # the period closed, its simulator, the host's key (required)
    notes = []
    if plan.get("key") and chk["key"] != plan.get("key"):
        notes.append(f"校准局的发牌密钥（{chk['key']}）和循环赛的（{plan['key']}）不是同一把：校准不受影响，记一笔")
    if arena is not None:
        w = R._window_open(arena, period)
        if w:
            log(f"注意：{w}")
    by, rr_limits = scan(out, period, members)
    picks = draw(by, members, period, per_member)
    games = load(picks)
    items = [(("member", m), games[(gid, seat)], seat) for m in members for gid, seat, _, _ in picks[m]]
    jobs = []
    for j in cal_jobs(period, lay):
        deal.require(j, chk["key_bytes"])
        jobs.append(deal.seal(j, chk["key_bytes"]))
    play_workers = max(1, min(workers, len(jobs)))
    warm_play = jobs[:play_workers]                  # one warm-up game per worker (runner hands out one task each)
    play_tasks = [{"kind": "play", "job": j, "strategies": j["strategies"]} for j in warm_play + jobs]
    workers = max(1, min(workers, len(items) + len(jobs)))
    log(f"{len(members)} 副，重放 {len(items)} 局；校准局 {len(jobs)} 局（种子 {lay['used'][0]}～{lay['used'][1]}），"
        f"先打校准局（另热身 {len(warm_play)} 局），再把重放和校准局的重放混在一起跑（另热身 "
        f"{min(workers, len(jobs))} 次重放）；{workers} 个进程")
    limits = _limit(mask)
    prov = provenance()
    lock = unlock = let_others_in = None
    if arena is not None:                    # one run at a time (D2): the arena's lock as the host
        from special_eval import let_others_in

        from ladder.arena import _lock, _unlock
        lock, unlock = _lock(arena, "host"), _unlock
    mparts, cparts, problems, cal_logs = {m: [] for m in members}, [], [], []
    t0 = time.time()
    try:
        played = guarded_map("special_compute:_task", play_tasks, workers=play_workers, step_limit=step_limit,
                             mask=mask, paths=[str(HERE)])[len(warm_play):]    # the warm-up games are not counted
        play_seconds = round(time.time() - t0, 1)
        cal = []
        for j, r in zip(jobs, played):
            r = r or {"died": None}
            game = (r.get("value") or {}).get("game")
            if game is None:
                problems.append(f"{j['id']}（校准局）: {str({x: y for x, y in r.items() if x != 'value'})[:200]}")
                continue
            game.update(provenance=prov, limits=limits)
            cal_logs.append(game)
            if game.get("result") not in OK or not game.get("steps"):
                problems.append(f"{j['id']}（校准局）: {game.get('result')}: {R.why_void(game)}")
                continue
            cal.append((("calibration", j["id"]), game, 0))
        order, warm = CA.run_order(items, cal, period, workers)
        tasks = [{"kind": "replay", "shadow": shadow_task(g, seat)} for _, g, seat in order]
        got = guarded_map("special_compute:_task", tasks, workers=workers, step_limit=step_limit, mask=mask,
                          paths=[str(HERE)]) if tasks else []
    finally:
        if lock is not None:
            unlock(lock)
            let_others_in(arena)
    seconds = round(time.time() - t0, 1)
    every, got = order[warm:], got[warm:]            # the warm-up replays are not counted

    half = len(every) // 2
    for at, ((kind, g, seat), r) in enumerate(zip(every, got)):
        r = r or {"died": None}
        if kind[0] == "member":
            p, bad = member_part(g, r, seat)
            if p is None:
                problems += bad
            else:
                mparts[kind[1]].append(p)
            continue
        p, bad = cal_part(g, r)
        if p is None:
            problems += bad
        else:
            p["at"] = at
            cparts.append(p)
    (out / NAME).mkdir(parents=True, exist_ok=True)
    (out / NAME / "calibration.jsonl").write_text("".join(jsonl(g) for g in cal_logs), encoding="utf-8")

    def c_of(ps):
        a, b = sum(p["row"][2] for p in ps), sum(p["row"][3] for p in ps)
        return round(a / b, 4) if a and b else None
    cb = turn_budget(cparts, TURN_K)
    calib = {"games": len(cparts), "planned": len(jobs), "warm_up": len(warm_play), "warm_up_replays": warm,
             "seeds": lay["used"],
             "game_over_replay": c_of(cparts),
             "halves": [c_of([p for p in cparts if p["at"] < half]), c_of([p for p in cparts if p["at"] >= half])],
             "parts": None if cb["c_parts"] is None else {h: _rd(x, 4) for h, x in cb["c_parts"].items()}}
    if len(cparts) < MIN_CAL:
        calib["note"] = f"校准局回来能用的只有 {len(cparts)} 局（要 {MIN_CAL} 局）：不出比"
    batch_limits = json.loads(json.dumps(limits, sort_keys=True))
    if rr_limits and any(x != batch_limits for x in rr_limits):
        notes.append(f"这一批的进程限制（{_js(batch_limits)}）和循环赛日志里记的（{'、'.join(_js(x) for x in rr_limits)}）"
                     "不一样：核不一样，校准就对不上循环赛当时的机器快慢")
    from ladder.submit import ledger
    lines, rows = ledger(Path(host) / "subs"), []
    for m in members:
        info = members[m]
        row = {"member": m, "player": info["player"], "arch": info["arch"], "name": info["member"],
               "receipt": info["receipt"], "spec": info["spec"], "available": len(by[m]), "drawn": len(picks[m]),
               "ids": [f"{gid}@{seat}" for gid, seat, _, _ in picks[m]], "games": len(mparts[m]),
               "receipt_compute": receipt_numbers(lines, info["receipt"])}
        if mparts[m] and "note" not in calib:
            row.update(measure(mparts[m], [{x: y for x, y in p.items() if x != "at"} for p in cparts], TURN_K,
                               draws))
        else:
            row["over"] = row["old_over"] = False
        rows.append(row)
    body = {"period": period, "turn_k": TURN_K, "turn_refuse": TURN_REFUSE, "refuse": COMPUTE_REFUSE,
            "cap": COMPUTE_CAP, "per_member": per_member, "key": chk["key"], "env": chk["env"],
            "rr_key": plan.get("key"), "calibration": calib,
            "batch": {"workers": workers, "mask": None if mask is None else hex(mask), "limits": batch_limits,
                      "rr_limits": rr_limits, "replays": len(items), "seconds": seconds,
                      "play_seconds": play_seconds},
            "members": rows, "over": [r["member"] for r in rows if r.get("over")],
            "old_over": [r["member"] for r in rows if r.get("old_over")], "missing": missing,
            "problems": problems[:40], "problem_count": len(problems), "notes": notes}
    (out / f"{NAME}.json").write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / f"{NAME}.md").write_text(host_text(body), encoding="utf-8")
    return body


# --- the report -------------------------------------------------------------------------------------------------------

def _iv(x, iv) -> str:
    if x is None:
        return "—"
    return f"{x:.3f}（{iv[0]:.3f}～{iv[1]:.3f}）" if iv and iv[0] is not None else f"{x:.3f}"


def _js(x) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def _num(x, n=3) -> str:
    return "—" if x is None else f"{x:.{n}f}"


def host_text(body: dict) -> str:
    k, cap, refuse, q = body["turn_k"], body["cap"], body["refuse"], body["turn_refuse"]
    c = body["calibration"]
    out = [f"# 第 {body['period']} 期算力抽查：循环赛的对局", "",
           "带选手名，只给主持方和 Salem。这个工具不判、不发选手回执：超线的怎么处理由 Salem 定。", "",
           (f"怎么量：每一副从循环赛里它打完的局（正常结束或平局）里固定抽至多 {body['per_member']} 局（按期号、成员、回执号定的"
            "抽法，主持方不挑），用主持方的代码一步一步重放，每到这一副的决定就问一次默认打法、计时；选手的代码不再跑（和收提交、"
            "期末抽查同一个办法）。循环赛里没有默认打法自己打的局，所以同一批里另打"
            f" {c['planned']} 局默认打法对默认打法（三副蓝本两两相打、同原型也打，比例和循环赛一样；每个种子两边各坐一次），"
            "它们的「对局 ÷ 重放」就是这一批的机器系数 c。分两段跑：先只打校准局，和循环赛一样全是对局"
            f"（开头每个进程先热身一局、不算，这次 {c['warm_up']} 局）；再把成员的重放和校准局的重放打乱混在一起跑，"
            "每一次重放都是单独的任务，和成员的重放同一个条件"
            f"（开头每个进程先热身一次重放、不算，这次 {c.get('warm_up_replays', 0)} 次）。"), "",
           "三个数（和收提交同一个算法，submit.turn_budget）：",
           f"- 所有步：这一副所有决定的 CPU ÷ 默认打法在同样局面上的 ÷ c（老规矩的数，上限 {cap}，超过 {refuse} 拒收）；",
           f"- 回合里：除了每个自己回合第一个决定以外的那些步（换牌算在这里），同样的比（上限 {cap}，超过 {refuse} 拒收）；",
           (f"- 回合开头：每个回合第一个决定的 CPU ÷ c，对「{cap} × 默认打法在这一步的 + {k} × 默认打法这一整回合的」的比"
            f"（K = {k}，超过 {q} 拒收）；「多花几个默认回合」是回合开头平均比 {cap} 倍多花了几个默认打法的整回合（给的是 {k} 个）。"),
           "",
           "90% 区间：这一副的局和校准局各自有放回地重抽 4000 次（和期末抽查 compute_audit 一样）。",
           (f"超线（和 compute_audit 的 over 一样，两条规矩都超）：所有步的区间整个在 {refuse} 以上，"
            + (f"而且回合里的区间整个在 {refuse} 以上，或者回合开头的区间整个在 {q} 以上。" if k else "（K = 0：只看这一条）。")
            + f"「只按老规矩超」：所有步的区间整个在 {refuse} 以上、按回合那条没超；收提交两条过一条就收，这种不算超线。"), ""]
    if c.get("note"):
        out += [f"**{c['note']}。**", ""]
    out += ["## 每一副", "",
            ("| 选手 | 原型 | 成员 | 重放（可抽） | 所有步（90%） | 回合里（90%） | 回合开头对预算（90%） | 多花几个默认回合 | "
             "点估计按哪条过 | 超线 | 收提交时：所有步 / 回合里 / 回合开头 / 按哪条收 |"), "|" + "---|" * 11]
    for r in body["members"]:
        rc = r.get("receipt_compute") or {}
        said = " / ".join([_num(rc.get("ratio")), _num(rc.get("in_turn")), _num(rc.get("turn_start_q")),
                           {"old": "老规矩", "turn": "按回合"}.get(rc.get("rule"), "—")]) if rc else "—"
        over = "**超线**" if r.get("over") else ("只按老规矩超" if r.get("old_over") else "没有")
        out.append(f"| {r['player']} | {r['arch']} | {r['name'] or '—'} | {r['games']}（{r['available']}） | "
                   f"{_iv(r.get('ratio'), r.get('interval90'))} | {_iv(r.get('in_turn'), r.get('interval90_in'))} | "
                   f"{_iv(r.get('turn_start_q'), r.get('interval90_q'))} | {_num(r.get('extra_turns'), 2)} | "
                   f"{RULE_ZH[r['rule_point']] if 'rule_point' in r else '—'} | {over} | {said} |")
    out += ["", "## 回合开头的分布（只报）", "",
            (f"每回合多花 = 回合开头这一步的 CPU ÷ c − {cap} × 默认打法在这一步的，以这一副局面上默认打法平均一回合为单位；"
             "预算按所有回合平均，这一回合不花、那一回合多花是允许的。默认打法每回合 ÷ 校准局的：这一副的局面上默认打法一回合"
             "要算多少，对默认打法自己打蓝本时的（预算跟着它走）。墙钟是循环赛对局日志里记的那一步的，一步超过 30 秒判负。"), "",
            "| 成员 | 回合数 | 每回合多花：中位 / 90 分位 / 最大 | 默认打法每回合 ÷ 校准局的 | 回合开头最长墙钟（秒） |",
            "|" + "---|" * 5]
    for r in body["members"]:
        pt = r.get("per_turn") or {}
        out.append(f"| {r['member']} | {r.get('turns', '—')} | {_num(pt.get('median'), 2)} / {_num(pt.get('p90'), 2)} / "
                   f"{_num(pt.get('max'), 2)} | {_num(r.get('u_twin_ratio'), 2)} | "
                   f"{_num(r.get('turn_start_wall_max_s'), 2)} |")
    b = body["batch"]
    out += ["", "## 校准和这一批", "",
            (f"- 校准局回来能用的 {c['games']} 局（打了 {c['planned']} 局，另热身 {c['warm_up']} 局），种子 {c['seeds'][0]}～"
             f"{c['seeds'][1]}（热身的局是前 {c['warm_up']} 个校准局又打了一遍），发牌密钥 {body['key'] or '没有'}"
             f"（循环赛的 {body['rr_key'] or '没有'}），模拟器环境 {body['env'] or '—'}。"),
            (f"- 机器系数 c（校准局的对局 ÷ 重放）= {_num(c.get('game_over_replay'), 4)}；这一批前一半 "
             f"{_num(c['halves'][0], 4)}、后一半 {_num(c['halves'][1], 4)}（看这一批跑的时候快慢有没有漂）；按两池分开看：回合开头 "
             f"{_num((c.get('parts') or {}).get('F'), 4)}、其余 {_num((c.get('parts') or {}).get('R'), 4)}（只作诊断，比照旧用合起来的 c）。"),
            (f"- 这一批：{b['workers']} 个进程，进程限制 {_js(b['limits'])}，用了 {b['seconds']:.0f} 秒（打校准局 "
             f"{b.get('play_seconds', 0):.0f} 秒）；循环赛日志里记的"
             f"进程限制：{'、'.join(_js(x) for x in b['rr_limits']) or '没有'}。"),
            ("- 局限：校准局是这次另打的，不是循环赛当时打的。循环赛当时机器的快慢（核的种类、负载、温度）只能靠同样的进程数、"
             "同样的核去对上；对上不了的那部分对所有成员是同一个偏差，没量过有多大。排名不受它影响，离线近的要留余量。"
             "另外循环赛里对手是别的选手的成员，不是默认打法：对手规划得重、留下一堆要回收的东西，回收可能落在这一副的步上，"
             "这一副就量得偏高（收提交时对手是默认打法，没有这一项）。"),
            "", "## 要留意的", "",
            "- 超线的：" + ("、".join(body["over"]) or "没有") + "（由主持方看过、报 Salem 定）",
            "- 只按老规矩超的（按回合那条没超，不算超线）：" + ("、".join(m for m in body["old_over"] if m not in body["over"])
                                                        or "没有"),
            "- 点估计两条都没过、但区间没整个越线的：" + ("、".join(r["member"] for r in body["members"]
                                                    if "rule_point" in r and r["rule_point"] is None
                                                    and not r.get("over")) or "没有"),
            "- 没交、没有可量的：" + ("、".join(body["missing"]) or "没有"),
            f"- 重放没回来、对不上的：{body['problem_count']} 局" + ("：" + "；".join(body["problems"][:10])
                                                             if body["problems"] else "")]
    out += [f"- {n}" for n in body["notes"]]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", type=int, default=4)
    ap.add_argument("--host", type=Path, default=Path(r"C:\claude\ladder-host"))
    ap.add_argument("--arena", type=Path, default=Path(r"C:\claude\ladder-arena"), help="whose lock it takes")
    ap.add_argument("--workers", type=int, default=23, help="the round robin's (the calibration stands for its runs)")
    ap.add_argument("--mask", type=lambda x: int(x, 0), default=None, help="the round robin's (none: all cores)")
    ap.add_argument("--per-member", type=int, default=PER_MEMBER)
    ap.add_argument("--calibration", type=int, default=CAL_GAMES)
    ap.add_argument("--dry", action="store_true", help="the plan only: nothing played or written")
    a = ap.parse_args(argv)
    try:
        if a.dry:
            print(json.dumps(dry(a.host, a.period, a.per_member, a.calibration), ensure_ascii=False, indent=1))
            return 0
        body = check(a.host, a.period, a.workers, a.mask, a.per_member, a.calibration, arena=a.arena)
    except R.EvalError as e:
        print(f"停下：{e}")
        return 1
    except KeyboardInterrupt:
        print("停了（Ctrl+C）：什么也没写。再跑同一条命令从头量。")
        return 130
    out = R._out_dir(a.host, a.period, None)
    print(f"完成：{len(body['members'])} 副，超线 {len(body['over'])} 副（{'、'.join(body['over']) or '没有'}）；"
          f"结果 {out / (NAME + '.md')}（只给主持方和 Salem，不发选手）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
