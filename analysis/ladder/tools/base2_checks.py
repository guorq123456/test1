"""base-2 on Salem's computer, before phase 1's lock (RUNBOOK 第一次 step 2-3; LEDGER LD-27, LD-29; PHASE1-REPORT
第一节): make the host's deal key if it isn't there yet, then check the lock version with it.

    python analysis/ladder/tools/base2_checks.py --runs C:\\claude\\ladder-runs\\base2 --p1b C:\\claude\\ladder-runs\\p1b
        [--make-key] [--workers 23]

1. key: --make-key writes the host's key (deal.DEFAULT_KEY) only if there is none (a key is made once; it never goes
   into the repository or the project folder). The key must load; its id is printed, never the key.
2. keyed games: 20 games of the seven baseline lists, the default strategy (every ordered pair of classes in turn),
   dealt with the key by the runner. Each line carries the deal (this deal version, this key's id) and strategy
   seeds that are not the game seed x2+1 / x2+2; each replays move by move and decision by decision here, without
   the key.
3. list order (LD-29): for the same 20 games, the cards sorted by uid at the start are not the list order on either
   side; the same seeds without the key still are (so the check would catch the old deal).
4. phase-1 logs: the 20 p1b baseline games the phase-1 replay check sampled (random.Random(1)), replayed with this
   code, moves and decisions: logs without a deal still replay.
5. base: tests/test_base.py (the public position holds no secret, samples agree with the real position, the default
   strategy doesn't move when only secrets change), run here without pytest (it isn't installed on this computer).
6. interface: tools/check_interface.py's 40 games (the default strategy through ladder.interface, decision for
   decision, plain and with every hook written out).
7. speed: 2300 keyed games of the baseline lists on all cores (the runner alone, no pool): games per hour, for the
   practice arena's time limit. With the tripwire on (LD-40): a false alarm would void games and fail this step.
8. tripwire (LD-40, LD-41): 6 keyed games in one worker: a test strategy that rewrites shared card definitions, one
   that adds a member to the scripts' base class, one that adds a card id to the scripts' listener registry, each
   followed by a plain game. The three are void with the reason and the original result kept; the plain ones after
   them are normal and replay (the worker was replaced).
9. guarded tasks (LD-40): runner.guarded_map, as puzzles and the arena's resume use it, on Windows: a task that
   changes the simulator is marked and its worker replaced, a hang is stopped by the clock, a worker that exits is
   that task's alone.
10. audit (LD-40): ladder/audit.py replays every game of steps 2, 7 and 8 move by move in clean processes; the only
   ones allowed to fail are none (the void ones are skipped).

Seeds: 93150000-93150019 (2, 3), 93150020-93150025 (8) and 93150100-93152399 (7), host measurement second segment
(SEEDS.md); 4 replays p1b's own; 5 and 6 reuse the probe bank seeds the tests use (99001000+, 99001520-99001559), on
purpose. A dry run elsewhere (--dry, with --key a throwaway file and --speed-games small) uses 93403000-93403025 and
93403100 onward instead (host probe second segment).
Writes RUNS/<commit>/keyed.jsonl, speed.jsonl, tripwire.jsonl, summary.json (one folder per commit, "-dirty" if the
working tree differs: a second run on the same code skips the games already played, a run on new code plays its
own) and a copy of the summary at RUNS/summary.json.
"""
from __future__ import annotations

import argparse
import itertools
import json
import random
import sys
import time
import traceback
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(LADDER), str(ROOT), str(LADDER / "tests"), str(HERE)]

from ladder import deal, runner  # noqa: E402
from ladder.replay import replay_decisions, replay_moves  # noqa: E402

KEYED = (93150000, 93150020)
TRIP = 93150020
SPEED = (93150100, 93152400)
DRY_KEYED = (93403000, 93403020)
DRY_TRIP = 93403020
DRY_SPEED = 93403100
DEFAULT = "bot:mcts:100+plan"
TRIP_STRATEGIES = ["py:helpers:ChangesCards", "py:helpers:Random", "py:helpers:PatchesScripts", "py:helpers:Random",
                   "py:helpers:GrowsRegistry", "py:helpers:Random"]


def codes():
    lines = [l.strip().split("|") for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(
        encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    return [c for _, c in lines]


def jobs(lo, hi, tag):
    cs = codes()
    pairs = list(itertools.permutations(range(len(cs)), 2))
    return [{"id": f"{tag}-{s}", "seed": s, "first": None, "decks": [cs[pairs[k % len(pairs)][0]],
             cs[pairs[k % len(pairs)][1]]], "strategies": [DEFAULT, DEFAULT], "strategy_seeds": None,
             "labels": {"check": "base-2"}} for k, s in enumerate(range(lo, hi))]


def read(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip(" \t\r\n\x00")
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def uid_order(state, seat):
    cards = list(state.players[seat].deck) + list(state.players[seat].hand)
    return [c.defn.card_id for c in sorted(cards, key=lambda c: c.uid)]


class Skipped(Exception):
    pass


def pytest_shim():
    """Just enough of pytest for tests/test_base.py and tests/test_interface.py to import and run here."""
    m = types.ModuleType("pytest")

    def parametrize(names, values):
        def deco(f):
            f._params = ([n.strip() for n in names.split(",")], list(values))
            return f
        return deco

    def skip(msg=""):
        raise Skipped(msg)
    m.mark = types.SimpleNamespace(parametrize=parametrize)
    m.skip = skip
    return m


def run_module(mod) -> dict:
    """Every test_* function of `mod`, each parameter set in turn: passed / skipped / failed (with the reason)."""
    passed, skipped, failed = 0, 0, []
    for name in sorted(n for n in dir(mod) if n.startswith("test_")):
        f = getattr(mod, name)
        names, values = getattr(f, "_params", ([], [()]))
        for v in values:
            args = dict(zip(names, v if len(names) > 1 else (v,))) if names else {}
            try:
                f(**args)
                passed += 1
            except Skipped:
                skipped += 1
            except Exception:
                failed.append({"test": name, "args": args, "why": traceback.format_exc(limit=3)[-600:]})
    return {"passed": passed, "skipped": skipped, "failed": failed, "ok": not failed and passed > 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--p1b", required=True, help="the phase-1 re-run folder (its baseline log is replayed)")
    ap.add_argument("--make-key", action="store_true", help="write the host's key if there is none")
    ap.add_argument("--workers", type=int, default=23)
    ap.add_argument("--key", help="a key file other than the host's (a dry run elsewhere)")
    ap.add_argument("--dry", action="store_true", help="probe-bank seeds instead of the measurement ones")
    ap.add_argument("--speed-games", type=int, default=SPEED[1] - SPEED[0])
    a = ap.parse_args()
    keyed_range = DRY_KEYED if a.dry else KEYED
    speed_range = (DRY_SPEED, DRY_SPEED + a.speed_games) if a.dry else (SPEED[0], SPEED[0] + a.speed_games)
    if speed_range[1] > (DRY_SPEED + 800 if a.dry else SPEED[1]):      # 93403900 is the warm-up seed
        raise SystemExit("--speed-games past the seeds set aside for it")
    key_file = Path(a.key) if a.key else deal.DEFAULT_KEY
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    top = Path(a.runs)
    prov = runner.provenance()
    runs = top / ((prov["commit"] or "nocommit")[:7] + ("-dirty" if prov["dirty"] else ""))
    runs.mkdir(parents=True, exist_ok=True)
    out = {"machine": prov, "folder": str(runs)}
    import os
    os.environ["LADDER_EXTRA_PATH"] = os.pathsep.join(
        x for x in (str(LADDER / "tests"), os.environ.get("LADDER_EXTRA_PATH", "")) if x)   # the test strategies

    def say(step, value):
        out[step] = value
        print(json.dumps({step: value}, ensure_ascii=False, default=str), flush=True)

    # 1. the key
    made = None
    if a.make_key and not key_file.exists():
        made = deal.new_key_file(key_file)
    key = deal.load_key(key_file)
    kid = deal.key_id(key)
    say("key", {"file": str(key_file), "id": kid, "made_now": made is not None, "ok": made in (None, kid)})

    # 2. keyed games, replayed without the key
    path = runs / "keyed.jsonl"
    runner.run(jobs(*keyed_range, "k"), str(path), workers=min(a.workers, 20), quiet=True, key=key)
    logs = [g for g in read(path) if g["id"].startswith("k-")]
    bad = []
    for g in logs:
        d = g.get("deal") or {}
        if d.get("key") != kid or d.get("version") != deal.DEAL_VERSION:
            bad.append({"id": g["id"], "why": f"deal {d}"})
        elif g["strategy_seeds"] == [g["seed"] * 2 + 1, g["seed"] * 2 + 2]:
            bad.append({"id": g["id"], "why": "strategy seeds from the game seed"})
        elif g["result"] not in ("normal", "draw"):
            bad.append({"id": g["id"], "why": f"result {g['result']}: {g.get('error', '')[:300]}"})
        else:
            for check in (replay_moves, replay_decisions):
                ok, why = check(g)
                if not ok:
                    bad.append({"id": g["id"], "why": f"{check.__name__}: {why}"})
                    break
    say("keyed_games", {"games": len(logs), "failed": bad,
                        "ok": len(logs) == keyed_range[1] - keyed_range[0] and not bad})

    # 3. list order: keyed starts don't follow the list, unkeyed ones do
    keyed_follow, plain_follow, sides = 0, 0, 0
    for g in logs:
        listed = [[c.card_id for c in runner.load_deck(x)] for x in g["decks"]]
        _, st = deal.start(g)
        plain = dict(g, deal=None)
        _, st0 = deal.start(plain)
        for seat in (0, 1):
            sides += 1
            keyed_follow += uid_order(st, seat) == listed[seat]
            plain_follow += uid_order(st0, seat) == listed[seat]
    say("list_order", {"sides": sides, "keyed_in_list_order": keyed_follow, "unkeyed_in_list_order": plain_follow,
                       "ok": sides > 0 and keyed_follow == 0 and plain_follow == sides})

    # 4. the phase-1 logs still replay with this code
    base_log = Path(a.p1b) / "baseline" / "pool" / "games.jsonl"
    old = read(base_log)
    pick = random.Random(1).sample(old, min(20, len(old)))
    bad = []
    for g in pick:
        for check in (replay_moves, replay_decisions):
            ok, why = check(g)
            if not ok:
                bad.append({"id": g["id"], "why": f"{check.__name__}: {why}"})
                break
    say("phase1_logs", {"checked": len(pick), "failed": bad, "ok": len(pick) == 20 and not bad,
                        "logged_commit": (pick[0].get("provenance") or {}).get("commit") if pick else None})

    # 5 and 6: the base's tests and the interface check, without pytest
    real = sys.modules.get("pytest")
    sys.modules["pytest"] = pytest_shim()
    try:
        import test_base
        say("base", run_module(test_base))
        import check_interface as CI
        rows = []
        pairs = list(itertools.permutations(range(len(CI.DECKS)), 2))
        for g in range(40):
            da, db = pairs[g % len(pairs)]
            seed = CI.SEEDS[0] + g
            ref = CI.record(da, db, [CI.BotStrategy(seed=2 * seed), CI.BotStrategy(seed=2 * seed + 1)], seed)
            plain = CI.record(da, db, [CI.PlayerStrategy(seed=2 * seed), CI.PlayerStrategy(seed=2 * seed + 1)], seed)
            expl = CI.record(da, db, [CI.BotStrategy(seed=2 * seed), CI.Explicit(seed=2 * seed + 1)], seed)
            rows.append({"seed": seed, "decisions": len(ref[1]), "plain": plain == ref, "explicit": expl == ref})
        say("interface", {"games": len(rows), "decisions": sum(r["decisions"] for r in rows),
                          "plain_same": sum(r["plain"] for r in rows), "explicit_same": sum(r["explicit"] for r in rows),
                          "ok": len(rows) == 40 and all(r["plain"] and r["explicit"] for r in rows)})
    finally:
        if real is None:
            sys.modules.pop("pytest", None)
        else:
            sys.modules["pytest"] = real

    # 7. speed on all cores
    path = runs / "speed.jsonl"
    earlier = {}
    if (runs / "summary.json").exists():
        try:
            earlier = json.loads((runs / "summary.json").read_text(encoding="utf-8")).get("speed") or {}
        except ValueError:
            earlier = {}
    t = time.time()
    res = runner.run(jobs(*speed_range, "s"), str(path), workers=a.workers, quiet=True, key=key)
    speed = [g for g in read(path) if g["id"].startswith("s-")]
    results = {}
    for g in speed:
        results[g["result"]] = results.get(g["result"], 0) + 1
    fresh = res.get("played", 0)
    gph = round(fresh / res["seconds"] * 3600) if fresh and res.get("seconds") else None
    if gph is None and earlier.get("games_per_hour"):
        gph = earlier["games_per_hour"]                  # nothing new played: the figure from the run that played
    say("speed", {"games": len(speed), "results": results, "workers": a.workers, "played_now": fresh,
                  "seconds_now": round(time.time() - t, 1), "games_per_hour": gph,
                  "games_per_hour_from": "this run" if fresh else "the earlier run on this commit",
                  "ok": len(speed) == speed_range[1] - speed_range[0] and set(results) <= {"normal", "draw"}})

    # 8. the tripwire: changes that outlast a game void it and replace the worker
    path = runs / "tripwire.jsonl"
    t0 = DRY_TRIP if a.dry else TRIP
    cs = codes()
    tjobs = [{"id": f"w-{t0 + k}", "seed": t0 + k, "first": 0, "decks": [cs[1], cs[4]],
              "strategies": [spec, "py:helpers:Random"], "strategy_seeds": None, "labels": {"check": "base-2 LD-40"}}
             for k, spec in enumerate(TRIP_STRATEGIES)]
    runner.run(tjobs, str(path), workers=1, step_limit=30.0, quiet=True, key=key)
    rows = {g["id"]: g for g in read(path) if g["id"].startswith("w-")}
    bad = []
    for k, spec in enumerate(TRIP_STRATEGIES):
        g = rows.get(f"w-{t0 + k}")
        if g is None:
            bad.append({"id": f"w-{t0 + k}", "why": "missing"})
        elif "Random" in spec.split(":")[-1]:
            ok, why = replay_moves(g) if g["result"] in ("normal", "draw") else (False, f"result {g['result']}")
            if not ok:
                bad.append({"id": g["id"], "why": why})
        elif not (g["result"] == "void" and g.get("voided_result") in ("normal", "draw")
                  and "LD-40" in str(g.get("error", ""))):
            bad.append({"id": g["id"], "why": f"{g['result']}: {str(g.get('error', ''))[:200]}"})
    say("tripwire", {"games": len(rows), "failed": bad, "ok": len(rows) == len(TRIP_STRATEGIES) and not bad})

    # 9. guarded tasks (puzzles, the arena's resume)
    got = runner.guarded_map("helpers:task", ["ok", "change", "ok", "hang", "ok", "die", "ok"], workers=1,
                             step_limit=5.0)
    try:
        want = (got[0].get("value") and got[2].get("value") and "changed" in got[1] and "changed" not in got[2]
                and got[0]["value"]["costs"] == got[2]["value"]["costs"] == got[4]["value"]["costs"]
                and got[1]["value"]["pid"] != got[2]["value"]["pid"] and got[3].get("timeout") == 1
                and got[5] == {"died": 3} and "value" in got[6])
    except (AttributeError, KeyError, TypeError):
        want = False
    say("guarded", {"tasks": [sorted(g or {}) for g in got], "ok": bool(want)})

    # 10. every game above replayed move by move in clean processes
    from ladder import audit
    res = audit.audit([runs / "keyed.jsonl", runs / "speed.jsonl", runs / "tripwire.jsonl"], workers=a.workers)
    say("audit", {"checked": res["checked"], "skipped": res["skipped"], "failed": res["failed"][:20],
                  "ok": res["ok"] and res["checked"] >= (keyed_range[1] - keyed_range[0]) + len(speed)})

    out["ok"] = all(v.get("ok") for k, v in out.items() if isinstance(v, dict) and "ok" in v)
    text = json.dumps(out, ensure_ascii=False, indent=1, default=str)
    (runs / "summary.json").write_text(text, encoding="utf-8")
    (top / "summary.json").write_text(text, encoding="utf-8")
    print(json.dumps({"ok": out["ok"], "folder": str(runs)}), flush=True)


if __name__ == "__main__":
    main()
