"""Public puzzles (公共题; player prompt: 「主持方有时会出公共题：指定一副卡组……请每个玩家各写一套打法……分清一件事：一副牌成绩差，
是牌不行，还是还没人会打」), and the starting measurement 2.6, which is a puzzle on a list with a trained pilot.

    python -m ladder.puzzles add SUBDIR --id P01 --deck CODE --title "..." [--note "..."] [--public PUBDIR]
    python -m ladder.puzzles run SUBDIR --id P01 --seeds LO HI --out DIR [--games-per-opponent 10]
                                 [--field others|frozen7|wgpq] [--ref NAME=SPEC ...] [--agreement 60]
                                 [--workers 23]

- add: the puzzle goes into SUBDIR/puzzles.json (the submission check reads it: a 公共题 submission must name a
  puzzle there and bring exactly its list) and, without the list's owner or anything else, into PUBDIR/puzzles.md.
- run: every player's latest accepted 公共题 strategy for the puzzle, and the references (always the default
  strategy; e.g. the pilot behind the base for 2.6, `--ref 驾驶员=bot:<pilot spec>`), play the puzzle's list against
  the same field on the same games: game i against field list j has seed LO + 100 * j + i, the puzzle side in seat
  i % 2; the field plays the default strategy. Win rates, and each entry's paired difference from the default.
- Agreement (同源度, plan 「公共题上选同一步的比例」): `--agreement K` decision points drawn from the default's own games
  on the puzzle list (seeded, the same for every entry); at each one every entry is built fresh and asked once on
  the same public position (like a resume: no state carried from earlier in the game). For each pair of entries, the
  share of points where they chose the same move. Players are shown as 甲、乙… only in the host's copy; the public
  copy says "选手 1、2…" in a shuffled order.
"""
from __future__ import annotations

import argparse
import json
import math
import hashlib
import random
import secrets
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for _p in (str(HERE.parent), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

DEFAULT = "bot:mcts:100+plan"


class PuzzleError(Exception):
    pass


def field_of(kind):
    """The opponents' lists: \"others\" (the bot's 12 outside the frozen seven), \"frozen7\", \"wgpq\" (pro lists, deduplicated)."""
    frozen = [l.strip().split("|") for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(
        encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    if kind == "frozen7":
        return frozen
    if kind == "others":
        codes = {c for _, c in frozen}
        rows = [l.strip().split("|")[:2] for l in (ROOT / "svsim/ui/bot_decks.txt").read_text(encoding="utf-8")
                .splitlines() if l.strip() and not l.startswith("#")]
        return [(f"bot/{n}", c) for n, c in rows if c not in codes]
    if kind == "wgpq":
        rows = [l.strip().split("|")[:2] for l in (HERE.parent / "decklists/wgpq-2026-11-14.txt").read_text(
            encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
        seen, out = set(), []
        for n, c in rows:
            if c not in seen:
                seen.add(c)
                out.append((n, c))
        return out
    raise SystemExit(f"unknown field {kind}")


def _registry(subdir: Path) -> dict:
    f = Path(subdir) / "puzzles.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def add(subdir: Path, pid: str, code: str, title: str, note: str = "", public: Path | None = None) -> dict:
    from ladder.submit import check_deck
    ids, problems = check_deck(code)
    if problems:
        raise PuzzleError(f"the list doesn't pass the deck check: {problems}")
    reg = _registry(subdir)
    if pid in reg:
        raise PuzzleError(f"{pid} exists already")
    reg[pid] = {"deck": ids, "deck_code": code, "title": title, "note": note,
                "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
    Path(subdir).mkdir(parents=True, exist_ok=True)
    (Path(subdir) / "puzzles.json").write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    if public:
        lines = ["# 公共题（给选手）", "", "交法见 submit.md：类型写「公共题」，`puzzle` 写题号，`deck` 照抄题目的卡组代码。公共题不占名额。", ""]
        for k, v in reg.items():
            lines += [f"## {k}　{v['title']}", "", f"- 卡组代码：`{v['deck_code']}`"] + ([f"- {v['note']}"] if v["note"] else []) + [""]
        Path(public).mkdir(parents=True, exist_ok=True)
        (Path(public) / "puzzles.md").write_text("\n".join(lines), encoding="utf-8")
    return reg[pid]


def entries(subdir: Path, pid: str) -> list[dict]:
    """Each player's latest accepted 公共题 submission for `pid`."""
    from ladder.submit import ledger
    last = {}
    for l in ledger(subdir):
        if l.get("ev") == "receipt" and l.get("kind") == "puzzle" and l.get("puzzle") == pid and l["verdict"] == "收下":
            last[l["player"]] = {"name": l["player"], "spec": l["spec"], "receipt": l["id"]}
    return list(last.values())


def _wilson(w, n):
    if n == 0:
        return None, None, None
    z, p = 1.96, w / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return round(p, 4), round(c - h, 4), round(c + h, 4)


def _diff(a, b):
    n = len(a)
    d = [x - y for x, y in zip(a, b)]
    m = sum(d) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1)) if n > 1 else float("nan")
    h = 1.96 * sd / math.sqrt(n)
    return round(100 * m, 2), round(100 * (m - h), 2), round(100 * (m + h), 2)


def _ask(job, beat=None):
    """One entry asked once at one decision point (a runner.guarded_map task, so a hang, a crash or a change to the
    simulator stays in this answer): replay the logged game to it, build the entry fresh, ask."""
    from ladder.runner import host_ctrl_c
    with host_ctrl_c():                               # only a real Ctrl+C stops the run (fifth pass, as the runner)
        return _ask_one(job, beat)


def _ask_one(job, beat=None):
    from ladder import base, deal
    from ladder.runner import host_interrupt, legal_choice, load_strategies, offer, safe_repr
    from svsim.core.actions import from_dict, to_dict
    from svsim.core.engine import apply, legal_actions
    log, seat, k = job["log"], job["seat"], job["k"]
    _, state = deal.start(log)
    tracker = base.Tracker(state)
    n = 0
    for data in log["actions"]:
        if state.active == seat:
            if n == k:
                legal = legal_actions(state)
                try:                                  # the entry's own raise (SystemExit too) is its answer: none
                    strat = load_strategies([job["spec"]], [job["seed"]], beat)[0]
                    pos = base.public_position(state, seat, tracker)
                    if beat is not None:              # on the step clock, as in a game (judging included)
                        beat[0], beat[1] = seat, time.monotonic_ns()
                    try:
                        a = strat.act(pos, offer(legal))
                        chosen = legal_choice(a, legal)   # judged as the runner judges it; illegal is no answer
                        shown = None if chosen is not None else safe_repr(a, 200)
                    finally:
                        if beat is not None:
                            beat[1] = 0
                    return {"point": job["point"], "entry": job["entry"],
                            "move": to_dict(chosen) if chosen is not None else None,
                            **({} if chosen is not None else {"error": "illegal: " + shown})}
                except BaseException as e:            # noqa: BLE001
                    if host_interrupt(e):
                        raise
                    return {"point": job["point"], "entry": job["entry"], "move": None, "error": safe_repr(e, 200)}
            n += 1
        tracker.before(state)
        apply(state, from_dict(data))
        tracker.after(state)
    return {"point": job["point"], "entry": job["entry"], "move": None, "error": "point past the game's end"}


def _answers(ask: list, got: list, ents: list) -> tuple[list, list]:
    """guarded_map's results as answers (a hang, a dead worker or a runner error is no answer), and the entries
    during whose answer the simulator changed (LD-40) or the code tried what a game may not do (LD-52): their answer
    is none, and the host's copy names them."""
    answers, tripped = [], []
    for j, g in zip(ask, got):
        g = g or {"error": "no result"}
        a = g.get("value")
        if a is None:
            why = ("timeout" if "timeout" in g else f"worker died ({g['died']})" if "died" in g
                   else str(g.get("error", ""))[:200])
            a = {"point": j["point"], "entry": j["entry"], "move": None, "error": why}
        if g.get("changed") or g.get("blocked"):
            a = dict(a, move=None, error="the simulator changed during this answer" if g.get("changed") else
                     "the answer's code tried what a game may not do (LD-52)")
            tripped.append({"entry": ents[j["entry"]]["name"], "point": j["point"],
                            "what": " | ".join(x for x in (g.get("blocked"), g.get("changed")) if x)[:500]})
        answers.append(a)
    return answers, tripped


def public_copy(host: dict, refs: list) -> dict:
    """The players' copy of a puzzle result: players as 「选手 N」, no seeds, no deal, no alias map, and of the
    answers voided because the simulator changed only how many (the host's copy names the entries: LD-41)."""
    alias = host["aliases"]
    refs_order = {name: i for i, name in enumerate(refs)}

    def rank(name):                                       # refs in their own order, then 选手 1, 2, ... 10
        return (0, refs_order[name]) if name in refs_order else (1, int(name.split()[-1]))
    pub = json.loads(json.dumps(host))
    for r in pub["entries"]:
        r["entry"] = alias.get(r["entry"], r["entry"])
    pub["entries"].sort(key=lambda r: rank(r["entry"]))
    for r in pub["agreement"]:
        a, b = alias.get(r["a"], r["a"]), alias.get(r["b"], r["b"])
        r["a"], r["b"] = sorted((a, b), key=rank)        # neither the row order nor a/b tells the intake order
    pub["agreement"].sort(key=lambda r: (rank(r["a"]), rank(r["b"])))
    for k in ("seeds", "deal", "aliases"):
        pub.pop(k)
    pub["simulator_changed"] = len(host.get("simulator_changed") or ())
    return pub


def run(subdir: Path, pid: str, seeds, out: Path, games: int = 10, field: str = "others", refs=None,
        agreement: int = 60, workers: int = 4, mask=None, key="auto", rng_seed: int = 0) -> dict:
    from ladder import deal, runner
    reg = _registry(subdir)
    if pid not in reg:
        raise PuzzleError(f"no puzzle {pid}")
    code_dir = Path(subdir).resolve() / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    import os
    os.environ["LADDER_EXTRA_PATH"] = os.pathsep.join(x for x in (str(code_dir), os.environ.get("LADDER_EXTRA_PATH", "")) if x)
    ents = [{"name": "默认打法", "spec": DEFAULT, "ref": True}]
    for r in refs or []:
        name, spec = r.split("=", 1)
        ents.append({"name": name, "spec": spec, "ref": True})
    ents += [dict(e, ref=False) for e in entries(subdir, pid)]
    fl = field_of(field)
    lo, hi = seeds
    if lo + 100 * len(fl) > hi or games > 100:
        raise PuzzleError("seed range too small, or more than 100 games per field list")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    jobs, which = [], {}
    for e_i, e in enumerate(ents):
        # the id says what the game is: this run's seeds and this entry's version (its receipt, or the ref's spec),
        # so a re-run into the same folder plays what is new and never scores an old version's games as this one's
        tag = e.get("receipt") or "ref-" + hashlib.sha1(e["spec"].encode("utf-8")).hexdigest()[:10]
        for j, (oname, ocode) in enumerate(fl):
            for i in range(games):
                seat = i % 2
                sides = [(reg[pid]["deck"], e["spec"]), (ocode, DEFAULT)]
                if seat == 1:
                    sides.reverse()
                gid = f"{pid}-{lo}-{tag}-{j:02d}-{i:03d}"
                which[gid] = e_i
                jobs.append({"id": gid, "seed": lo + 100 * j + i, "first": None,
                             "decks": [d for d, _ in sides], "strategies": [s for _, s in sides],
                             "labels": {"entry": e_i, "field": oname, "game": i, "seat": seat}})
    key = deal.resolve(key)
    runner.run(jobs, str(out / "games.jsonl"), workers=workers, mask=mask, quiet=True, key=key)
    logs = []
    for x in (out / "games.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            g = json.loads(x.strip(" \t\r\n\x00") or "null")
        except ValueError:                                 # a line a power cut left half-written (the runner starts
            continue                                       # the next on a fresh line and plays that game again)
        if isinstance(g, dict) and g.get("id") in which:   # this run's games only
            g["labels"] = dict(g["labels"], entry=which[g["id"]])
            logs.append(g)
    deals = {g.get("deal", {}).get("key") if isinstance(g.get("deal"), dict) else g.get("deal") for g in logs}
    won = {}
    for g in logs:
        lab = g["labels"]
        if g.get("winner") in (0, 1) and g.get("result") != "void":   # decided games only (as the pool, A3)
            won.setdefault(lab["entry"], {})[(lab["field"], lab["game"])] = 1 if g["winner"] == lab["seat"] else 0
    base_games = won.get(0, {})
    table = []
    for e_i, e in enumerate(ents):
        w = won.get(e_i, {})
        keys = sorted(set(w) & set(base_games))            # pairs where both games were decided
        p, lo_, hi_ = _wilson(sum(w.values()), len(w))
        row = {"entry": e["name"], "ref": e["ref"], "games": sum(1 for g in logs if g["labels"]["entry"] == e_i),
               "decided": len(w), "rate": p, "lo": lo_, "hi": hi_}
        if e_i and keys:
            row["vs_default_pp"] = _diff([w[k] for k in keys], [base_games[k] for k in keys])
        table.append(row)
    # agreement: decision points from the default's own games on the puzzle list
    rng = random.Random(rng_seed)
    default_logs = sorted((g for g in logs if g["labels"]["entry"] == 0 and g["result"] in ("normal", "draw")),
                          key=lambda g: g["id"])
    points = []
    for _ in range(agreement if len(ents) > 1 and default_logs else 0):
        g = rng.choice(default_logs)
        seat = g["labels"]["seat"]
        mine = sum(1 for s in g.get("steps", []) if s[0] == seat)
        if mine:
            points.append((g, seat, rng.randrange(mine), rng.randrange(1, 2 ** 31)))
    ask = [{"log": g, "seat": seat, "k": k, "point": n, "entry": e_i, "spec": e["spec"], "seed": s}
           for n, (g, seat, k, s) in enumerate(points) for e_i, e in enumerate(ents)]
    answers, tripped = _answers(ask, runner.guarded_map("ladder.puzzles:_ask", ask, workers=workers, mask=mask),
                                ents) if ask else ([], [])
    moves = {}
    for a in answers:
        moves.setdefault(a["entry"], {})[a["point"]] = json.dumps(a["move"], sort_keys=True) if a["move"] else None
    agree = []
    for x in range(len(ents)):
        for y in range(x + 1, len(ents)):
            both = [p for p in range(len(points)) if moves.get(x, {}).get(p) and moves.get(y, {}).get(p)]
            same = sum(moves[x][p] == moves[y][p] for p in both)
            agree.append({"a": ents[x]["name"], "b": ents[y]["name"], "points": len(both),
                          "same": round(same / len(both), 3) if both else None})
    # the public names: a fresh secret order for every run, so 「选手 N」 says nothing about who or in what order
    # anyone submitted, and nothing links one puzzle's 选手 N to another's (the map stays in the host's copy)
    players = [e["name"] for e in ents if not e["ref"]]
    order = players[:]
    random.Random(secrets.randbits(64)).shuffle(order)
    alias = {n: f"选手 {i + 1}" for i, n in enumerate(order)}
    host = {"puzzle": pid, "title": reg[pid]["title"], "field": field, "games_per_list": games, "seeds": [lo, hi],
            "deal": sorted(d for d in deals if d) or None, "entries": table, "agreement": agree,
            "points": len(points), "aliases": alias, "simulator_changed": tripped}
    (out / "result-host.json").write_text(json.dumps(host, ensure_ascii=False, indent=1), encoding="utf-8")
    pub = public_copy(host, [e["name"] for e in ents if e["ref"]])
    (out / "result-public.json").write_text(json.dumps(pub, ensure_ascii=False, indent=1), encoding="utf-8")
    return host


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ladder.puzzles")
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("add")
    a.add_argument("subdir")
    a.add_argument("--id", required=True)
    a.add_argument("--deck", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--note", default="")
    a.add_argument("--public")
    a = sp.add_parser("run")
    a.add_argument("subdir")
    a.add_argument("--id", required=True)
    a.add_argument("--seeds", type=int, nargs=2, required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--games-per-opponent", type=int, default=10)
    a.add_argument("--field", default="others", choices=["others", "frozen7", "wgpq"])
    a.add_argument("--ref", action="append", default=[])
    a.add_argument("--agreement", type=int, default=60)
    a.add_argument("--workers", type=int, default=4)
    a.add_argument("--mask", type=lambda x: int(x, 0))
    args = ap.parse_args(argv)
    if args.cmd == "add":
        print(json.dumps(add(Path(args.subdir), args.id, args.deck, args.title, args.note,
                             Path(args.public) if args.public else None), ensure_ascii=False, indent=1))
    else:
        print(json.dumps(run(Path(args.subdir), args.id, tuple(args.seeds), Path(args.out), args.games_per_opponent,
                             args.field, args.ref, args.agreement, args.workers, args.mask), ensure_ascii=False,
                         indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
