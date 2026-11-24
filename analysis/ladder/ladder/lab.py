"""Salem's lab (S30, 11-24 20:07Z: 「给我一个单独的训练接口，全核」): his own practice interface on the PC, apart from
the players' arena. All cores (23 workers, no mask), no game cap, no window; everything visible (the field's decks,
owners and strategies; both sides of every game).

    python -m ladder.lab field   [--lab C:\\claude\\ladder-lab] [--arena C:\\claude\\ladder-arena]
    python -m ladder.lab decks   [--find TEXT]
    python -m ladder.lab vs      (--version DIR | --deck X [--strategy SPEC])
                                 (--opponent ID [--opponent ID ...] | --class 精灵 | --vs-deck X [--vs-deck X ...]
                                  [--vs-strategy SPEC]) --games N [--same-as L0001] [--workers 23]
    python -m ladder.lab ladder  (--version DIR | --deck X [--strategy SPEC]) [--replacing ID]
                                 [--games 600 --tail 300 --repeats 3] [--workers 23]
    python -m ladder.lab replay  --run L0001 --game L0001-00003 [--seat 0|1]

Your side: a version directory as a player's (strategy.py + submission.json {"class": the strategy's class name,
"deck": X}); the submission check's code reader runs on it for warnings only (nothing is refused for it: a game in
which the strategy touches what the game guard stops is void, and the log says why). Or a deck and a host strategy
(`--strategy`, default bot:mcts:100+plan; any bot:/mix: spec).
A deck X: a deck code, or a label of the archive (public/decklists.md: the baseline seven bot/..., the bot's own 19,
the WGP qualifier, the pro league lists); `decks` lists the labels.
Opponents: members and anchors of the arena's frozen field as it is now (the snapshot of the period, ARENA/host/
field.json), by anonymous id, member id (m0010) or anchor id, each with its own strategy; `--class` (精灵 or forest, ...): every member
of that class in turn; `--vs-deck` (repeatable): decks driven by `--vs-strategy` (default bot:mcts:100+plan). Games go
round the opponents in turn, seats alternating. `--same-as L0001`: the games of an earlier vs run again (same deals,
opponents, seats and strategy seeds) with your new side, and the paired difference.
A strategy that loads a trained model (outside.trained: setnet=, puct=, a pilot) is played by the referee without the
tripwire (S17: ladder/outside.py), and only against host strategies; `ladder` doesn't take one (the evaluator plays
through the runner, whose tripwire voids those games, LD-59).

The machine (D2: one run at a time): every run takes the arena's lock as "salem", in the players' queue (the host's
own work first, then whoever was served longest ago). A `vs` run is played in turns of at most arena.RUN_GAMES_MAX
(2000) games and queues again between them, so nobody waits behind you more than one turn. A `ladder` run is one
evaluator run and holds the lock to its end: while a period's window is open at most LADDER_OPEN_MAX games (5 x 1200,
the evaluator's acceptance setting, fits), outside a window no cap. With nobody else queued, all cores are yours.
Seeds: the lab's own range LAB_SEEDS (SEEDS.md), drawn at random as the arena's are; the deals are sealed with the
lab's own key (LAB/lab.key, made on first use), never the formal pool's or the arena's.

Everything stays under LAB (C:\\claude\\ladder-lab): runs/L0001/ (run.json, jobs.json, games.jsonl the full logs,
summary.json, replays) and code/ (your versions' strategy.py as played). These are Salem's own games: the host never
uses them for anything (red line: his game records are not used for search or training) and the players' prompt
names this folder among those not to read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import secrets
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = HERE.parents[2]
for _p in (str(ROOT), str(LADDER), str(LADDER / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ladder import arena as A  # noqa: E402

LAB = Path(r"C:\claude\ladder-lab")
ARENA = Path(r"C:\claude\ladder-arena")
LAB_SEEDS = (94910000, 95910000)      # SEEDS.md (S30)
WORKERS = 23                          # all cores (S10): 23 workers and this process
DEFAULT = "bot:mcts:100+plan"
LADDER_OPEN_MAX = 6300                # games of one ladder run while a period's window is open (5 x 1200 + 5%)
RUN_ID = re.compile(r"L\d{4,}")
CLASS_EN = {"forest": "精灵", "sword": "皇家护卫", "rune": "巫师", "dragon": "龙族", "abyss": "梦魇", "haven": "主教",
            "portal": "超越者"}                 # a terminal's code page can mangle 精灵 on its way through a .cmd


class LabError(Exception):
    pass


def archive() -> dict:
    """label -> deck code, from the decklists public/decklists.md is made of (tools/make_public.SOURCES)."""
    from make_public import SOURCES, rows
    out = {}
    for _title, path, _note in SOURCES:
        if Path(path).exists():
            for label, code in rows(Path(path)):
                out.setdefault(label, code)
    return out


def deck_of(x: str, arch: dict | None = None) -> tuple[list, str]:
    """(card ids, label or the code) for a label of the archive or a deck code; refused if the simulator's own rules
    refuse it (submit.check_deck: 40 cards, every effect scripted, the card pool)."""
    from ladder.submit import check_deck
    arch = archive() if arch is None else arch
    code = arch.get(x, x)
    try:
        ids, problems = check_deck(code)
    except Exception as e:                                # noqa: BLE001 - not a code at all
        raise LabError(f"不认识这副卡组：{x}（{type(e).__name__}: {e}）；卡组代码或 decks 里的名字") from None
    if problems:
        raise LabError(f"{x} 模拟器不收：" + "；".join(problems))
    return ids, (x if x in arch else code)


class Lab:
    def __init__(self, lab: Path = LAB, arena: Path = ARENA, workers: int = WORKERS):
        self.dir, self.arena, self.workers = Path(lab), Path(arena), workers
        fj = self.arena / "host" / "field.json"
        self.field = A._read(fj) if fj.exists() else {"members": [], "anchors": [], "hash": None, "period": None,
                                                        "mu": 0.0}
        self.by_id = {}
        for m in self.field["members"]:
            self.by_id[m["anon"]] = self.by_id[m["mid"]] = ("member", m)
        for a in self.field["anchors"]:
            self.by_id[a["id"]] = ("anchor", a)
        A._on_path(self.arena / "host" / "code")          # the field's received strategies
        self.code = self.dir / "code"
        self.code.mkdir(parents=True, exist_ok=True)
        A._on_path(self.code)
        self.key = self.dir / "lab.key"
        if not self.key.exists():
            from ladder import deal
            deal.new_key_file(self.key)

    # --- what there is -------------------------------------------------------------------------------------------
    def window_open(self) -> bool:
        w = self.arena / "public" / "window.json"
        if not w.exists():
            return False
        win = A._read(w)
        return win.get("field") == self.field.get("hash") and A._now() < datetime.fromisoformat(win["deadline"])

    def show(self, kind: str, row: dict) -> dict:
        from ladder.pool import CRAFT_ZH
        if kind == "member":
            return {"id": row["anon"], "mid": row["mid"], "owner": row.get("owner"), "class": CRAFT_ZH[row["craft"]],
                    "rel_cr": round(row["cr"] - self.field["mu"]), "strategy": row["strategy"]}
        if kind == "anchor":
            return {"id": row["id"], "name": row["name"], "class": CRAFT_ZH[row["craft"]], "strategy": row["strategy"]}
        return {"deck": row["label"], "class": CRAFT_ZH[row["craft"]], "strategy": row["strategy"]}

    def field_rows(self) -> dict:
        from ladder.pool import list_key
        arch = archive()
        named = {}
        for label, code in arch.items():
            try:
                named.setdefault(list_key(deck_of(code, {})[0]), label)
            except LabError:
                pass
        rows = [dict(self.show("member", m), deck=named.get(list_key(m["deck"]), "（不在存档里）"))
                for m in sorted(self.field["members"], key=lambda m: -m["cr"])]
        rows += [dict(self.show("anchor", a), deck=named.get(list_key(a["deck"]), "（不在存档里）"))
                 for a in self.field["anchors"]]
        return {"period": self.field["period"], "field": self.field["hash"], "window_open": self.window_open(),
                "workers": self.workers, "opponents": rows}

    # --- the sides -----------------------------------------------------------------------------------------------
    def mine(self, version: str | None, deck: str | None, strategy: str | None) -> dict:
        from ladder import base
        from ladder.runner import load_deck
        if bool(version) == bool(deck):
            raise LabError("你这边要么 --version 目录，要么 --deck 卡组（加 --strategy）")
        if version:
            from ladder.submit import check_code
            d = Path(version)
            meta = A._read(d / "submission.json")
            src = (d / "strategy.py").read_text(encoding="utf-8")
            if not meta.get("class") or not meta.get("deck"):
                raise LabError("submission.json 要有 class（打法类的名字）和 deck")
            ids, label = deck_of(meta["deck"])
            h = hashlib.sha256(src.encode("utf-8")).hexdigest()[:10]
            name = f"lab_{h}"
            (self.code / f"{name}.py").write_text(src, encoding="utf-8")
            spec = f"py:{name}:{meta['class']}"
            warnings = check_code(src, meta["class"])
            out = {"spec": spec, "deck": ids, "label": label, "version": str(d.resolve()), "sha": h,
                   "warnings": warnings}
        else:
            ids, label = deck_of(deck)
            spec = strategy or DEFAULT
            if spec.startswith("py:"):
                raise LabError("py: 打法用 --version 目录给")
            out = {"spec": spec, "deck": ids, "label": label, "warnings": []}
        out["craft"] = int(base.craft_of(load_deck(ids)))
        return out

    def opponents(self, ids, craft_zh, vs_decks, vs_strategy) -> list[dict]:
        from ladder import base
        from ladder.runner import load_deck
        given = sum(bool(x) for x in (ids, craft_zh, vs_decks))
        if given != 1:
            raise LabError("对手给一种：--opponent、--class 或 --vs-deck")
        out = []
        if ids:
            for i in ids:
                if i not in self.by_id:
                    raise LabError(f"练习场的冻结池里没有 {i}（field 看有哪些）")
                kind, row = self.by_id[i]
                out.append({"kind": kind, "key": row["mid"] if kind == "member" else row["id"], "deck": row["deck"],
                            "strategy": row["strategy"]})
        elif craft_zh:
            craft_zh = CLASS_EN.get(craft_zh.lower(), craft_zh)
            craft = A.CRAFT_BY_ZH.get(craft_zh)
            if craft is None:
                raise LabError(f"没有这个职业：{craft_zh}（{'、'.join(A.CRAFT_BY_ZH)}，或 {'/'.join(CLASS_EN)}）")
            ms = sorted((m for m in self.field["members"] if m["craft"] == craft), key=lambda m: m["mid"])
            if not ms:
                raise LabError(f"冻结池里没有{craft_zh}的成员")
            out = [{"kind": "member", "key": m["mid"], "deck": m["deck"], "strategy": m["strategy"]} for m in ms]
        else:
            spec = vs_strategy or DEFAULT
            if spec.startswith("py:"):
                raise LabError("--vs-strategy 用 bot: 或 mix:；py: 打法的对手用 --opponent 指池子里的成员")
            arch = archive()
            for x in vs_decks:
                d, label = deck_of(x, arch)
                out.append({"kind": "deck", "key": label, "deck": d, "strategy": spec, "label": label,
                            "craft": int(base.craft_of(load_deck(d)))})
        return out

    def row_of(self, o: dict) -> dict:
        if o["kind"] == "deck":
            return o
        return self.by_id[o["key"]][1]

    # --- running -------------------------------------------------------------------------------------------------
    def new_run(self, kind: str) -> tuple[str, Path]:
        runs = self.dir / "runs"
        runs.mkdir(parents=True, exist_ok=True)
        n = len([p for p in runs.iterdir() if RUN_ID.fullmatch(p.name)])
        while (runs / f"L{n + 1:04d}").exists():
            n += 1
        rid = f"L{n + 1:04d}"
        d = runs / rid
        d.mkdir()
        A._write(d / "run.json", {"run": rid, "kind": kind, "period": self.field["period"],
                                  "field": self.field["hash"], "time": A._iso(A._now()), "workers": self.workers})
        return rid, d

    def play(self, jobs: list, out: Path, log=print) -> None:
        """In turns of at most RUN_GAMES_MAX games, each under the arena's lock as "salem"."""
        from ladder import outside
        from ladder.runner import run
        self.check_trained([j["strategies"] for j in jobs])
        step = A.RUN_GAMES_MAX
        for k in range(0, len(jobs), step):
            chunk = jobs[k:k + step]
            lock = A._lock(self.arena, "salem")
            try:
                plain = [j for j in chunk if not any(outside.trained(s) for s in j["strategies"])]
                trained = [j for j in chunk if j not in plain]
                if plain:
                    run(plain, str(out), workers=min(self.workers, len(plain)), mask=None, quiet=True,
                        key=str(self.key))
                if trained:
                    outside.run(trained, out, workers=min(self.workers, len(trained)), mask=None, key=str(self.key))
            finally:
                A._unlock(lock)
            if len(jobs) > step:
                log(f"打完 {min(k + step, len(jobs))}/{len(jobs)} 局", file=sys.stderr)

    @staticmethod
    def check_trained(pairs) -> None:
        """A strategy that loads a trained model plays only host strategies, outside the tripwire (S17)."""
        from ladder import outside
        for specs in pairs:
            if any(outside.trained(s) for s in specs):
                try:
                    outside.host_only(specs)
                except outside.OutsideError:
                    raise LabError("载入训练模型的打法（setnet=、puct=、驾驶员）只能和 bot:、mix: 的打法打（S17：它们走没有"
                                   "绊线的裁判，选手的和你的 py: 打法不进那里）") from None

    def vs(self, me: dict, opps: list | None, games: int, same_as: str | None = None, rng_seed=None) -> dict:
        import random
        rng = random.Random(rng_seed if rng_seed is not None else secrets.randbits(64))
        notes = []
        if same_as:
            old = self.jobs_of(same_as)
            plan, opps = [dict(p) for p in old["plan"]], old["opps"]
            for o in opps:
                if o["kind"] != "deck":
                    if o["key"] not in self.by_id:
                        raise LabError(f"{same_as} 的对手 {o['key']} 现在的冻结池里没有了，不能重打")
                    now = self.by_id[o["key"]][1]
                    if now["deck"] != o["deck"] or now["strategy"] != o["strategy"]:
                        notes.append(f"{o['key']} 的卡组或打法和 {same_as} 那时不一样了，这次用现在的")
            games = len(plan)
        else:
            if games < 1:
                raise LabError("--games 至少 1")
            plan = [{"i": i, "seed": rng.randrange(*LAB_SEEDS), "seat": i % 2, "opp": i % len(opps),
                     "sseeds": [rng.randrange(1, 2 ** 62), rng.randrange(1, 2 ** 62)]} for i in range(games)]
        self.check_trained([[me["spec"], self.row_of(o)["strategy"]] for o in opps])
        rid, d = self.new_run("vs")
        jobs = []
        for p in plan:
            o = opps[p["opp"]]
            row = self.row_of(o)
            sides = [(me["deck"], me["spec"]), (row["deck"], row["strategy"])]
            if p["seat"] == 1:
                sides.reverse()
            jobs.append({"id": f"{rid}-{p['i']:05d}", "seed": p["seed"], "first": None,
                         "decks": [x for x, _ in sides], "strategies": [s for _, s in sides],
                         "strategy_seeds": p["sseeds"], "labels": {"run": rid, "seat": p["seat"], "opp": p["opp"]}})
        A._write(d / "jobs.json", {"plan": plan, "opps": opps, "me": me, "same_as": same_as})
        self.play(jobs, d / "games.jsonl")
        out = self.summary(rid, d, plan, opps, jobs)
        out.update(me={k: me.get(k) for k in ("label", "spec", "version", "warnings")}, same_as=same_as)
        if notes:
            out["notes"] = notes
        if same_as:
            old = {g["id"].split("-")[1]: g for g in A._jsonl(self.dir / "runs" / same_as / "games.jsonl")}
            new = {g["id"].split("-")[1]: g for g in A._jsonl(d / "games.jsonl")}
            a, b = [], []
            for p in plan:
                k = f"{p['i']:05d}"
                x, y = new.get(k), old.get(k)
                if x and y and x.get("winner") in (0, 1) and y.get("winner") in (0, 1):
                    a.append(int(x["winner"] == p["seat"]))
                    b.append(int(y["winner"] == p["seat"]))
            out["paired"] = A._paired(a, b) if a else None
        A._write(d / "summary.json", out)
        return out

    def summary(self, rid: str, d: Path, plan: list, opps: list, jobs: list) -> dict:
        logs = {g["id"]: g for g in A._jsonl(d / "games.jsonl")}
        per, seats, voids, errors = {}, {True: [0, 0], False: [0, 0]}, Counter(), Counter()
        w = n = played = 0
        for p, j in zip(plan, jobs):
            g = logs.get(j["id"])
            if g is None:
                continue
            played += 1
            o = opps[p["opp"]]
            name = o["key"] if o["kind"] != "member" else self.by_id.get(o["key"], (None, {"anon": o["key"]}))[1]["anon"]
            c = per.setdefault(name, {"games": 0, "decided": 0, "wins": 0})
            c["games"] += 1
            if g.get("result") == "void":
                voids[(g.get("error") or "")[:200]] += 1
                continue
            if g.get("loser") == p["seat"] and g.get("error"):
                errors[g["error"][:200]] += 1
            if g.get("winner") not in (0, 1):
                continue
            won = g["winner"] == p["seat"]
            first = g.get("first") == p["seat"]
            n += 1
            w += won
            c["decided"] += 1
            c["wins"] += won
            seats[first][0] += won
            seats[first][1] += 1
        rate, lo, hi = A._wilson(w, n)
        for c in per.values():
            c["win_rate"] = round(c["wins"] / c["decided"], 4) if c["decided"] else None
        return {"run": rid, "kind": "vs", "games": played, "decided": n, "wins": w, "win_rate": round(rate, 4),
                "lo": round(lo, 4), "hi": round(hi, 4),
                "first": {"games": seats[True][1], "wins": seats[True][0]},
                "second": {"games": seats[False][1], "wins": seats[False][0]},
                "by_opponent": per, "void": sum(voids.values()), "void_reasons": dict(voids.most_common(5)),
                "my_errors": dict(errors.most_common(5))}

    def ladder(self, me: dict, replacing: str | None, games: int, tail: int, repeats: int, rng_seed=None) -> dict:
        from ladder import outside
        from ladder.evaluator import Candidate
        if self.field["hash"] is None:
            raise LabError("练习场还没有冻结池（ARENA/host/frozen.json）")
        if outside.trained(me["spec"]):
            raise LabError("载入训练模型的打法用 vs（冻结池评测走带绊线的 runner，这种局会被作废，LD-59）")
        budget = games * repeats + max(A.VOID_STOP, games * repeats // 20)
        if self.window_open() and budget > LADDER_OPEN_MAX:
            raise LabError(f"期中一次冻结池评测最多 {LADDER_OPEN_MAX} 局（选手在排队），这次要 {budget}")
        mid = "outside"
        if replacing:
            kind, row = self.by_id.get(replacing, (None, None))
            if kind != "member":
                raise LabError(f"{replacing} 不是冻结池里的成员")
            mid = row["mid"]
        cand = Candidate(mid, me["craft"], me["deck"], me["spec"])
        lock = A._lock(self.arena, "salem")
        stopped = None
        try:
            rid, d = self.new_run("ladder")
            A._write(d / "jobs.json", {"me": me, "replacing": replacing, "games": games, "tail": tail,
                                       "repeats": repeats})
            ev = A._StoppingEvaluation(self.arena / "host" / "frozen.json", d, cand, LAB_SEEDS, games=games,
                                       tail=tail, repeats=repeats,
                                       rng_seed=rng_seed if rng_seed is not None else secrets.randbits(48))
            ev.budget, ev.approved = budget, games * repeats
            try:
                res = ev.run(workers=self.workers, mask=None, key=str(self.key))
            except A._TooManyVoid as e:
                stopped = str(e)
        finally:
            A._unlock(lock)
        out = {"run": rid, "kind": "ladder", "me": {k: me.get(k) for k in ("label", "spec", "version", "warnings")},
               "replacing": replacing, "games": len({g["id"] for g in A._jsonl(d / "games.jsonl")})}
        if stopped:
            out["stopped"] = stopped
        else:
            out.update(rel_cr=round(res["rel_cr"], 1), lo=round(res["lo"], 1), hi=round(res["hi"], 1),
                       repeats=res["repeats"], values=[round(x, 1) for x in res["values"]],
                       stuck=[{k: s[k] for k in ("rep", "after", "side")} for s in res["stuck"]])
        A._write(d / "summary.json", out)
        return out

    def jobs_of(self, rid: str) -> dict:
        if not RUN_ID.fullmatch(str(rid)) or not (self.dir / "runs" / rid / "jobs.json").exists():
            raise LabError(f"没有这个编号：{rid}")
        j = A._read(self.dir / "runs" / rid / "jobs.json")
        if "plan" not in j:
            raise LabError(f"{rid} 不是 vs 打出来的")
        return j

    def replay(self, rid: str, game: str, seat: int | None = None) -> Path:
        """Every move of both sides; with `seat`, that side's public view at each of its decisions too."""
        if not RUN_ID.fullmatch(str(rid)):
            raise LabError(f"没有这个编号：{rid}")
        g = next((x for x in A._jsonl(self.dir / "runs" / rid / "games.jsonl") if x["id"] == game), None)
        if g is None:
            raise LabError(f"{rid} 里没有 {game}")
        moves = [{"seat": s[0], "move": a} for s, a in zip(g.get("steps", []), g.get("actions", []))]
        body = {k: g.get(k) for k in ("id", "result", "winner", "loser", "first", "turns", "error", "strategies",
                                      "referee")}
        body["moves"] = moves
        if seat is not None:
            from ladder import base, deal
            from svsim.core.actions import from_dict
            from svsim.core.engine import apply
            _, state = deal.start(g)            # the log line has the deal as it was opened
            tracker = base.Tracker(state)
            views = []
            for step, data in zip(g.get("steps", []), g.get("actions", [])):
                if step[0] == seat:
                    views.append({"move": len(views), "view": base.public_position(state, seat, tracker).observation(),
                                  "chosen": data})
                tracker.before(state)
                apply(state, from_dict(data))
                tracker.after(state)
            body["views"], body["view_seat"] = views, seat
        out = self.dir / "runs" / rid / f"replay-{game}{'' if seat is None else f'-seat{seat}'}.json"
        A._write(out, body)
        return out


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:                                 # noqa: BLE001
            pass
    ap = argparse.ArgumentParser(prog="python -m ladder.lab")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("field", "decks", "vs", "ladder", "replay"):
        a = sp.add_parser(name)
        a.add_argument("--lab", type=Path, default=LAB)
        a.add_argument("--arena", type=Path, default=ARENA)
        a.add_argument("--workers", type=int, default=WORKERS)
        if name == "decks":
            a.add_argument("--find")
        if name in ("vs", "ladder"):
            a.add_argument("--version")
            a.add_argument("--deck")
            a.add_argument("--strategy")
        if name == "vs":
            a.add_argument("--opponent", action="append")
            a.add_argument("--class", dest="craft")
            a.add_argument("--vs-deck", action="append")
            a.add_argument("--vs-strategy")
            a.add_argument("--games", type=int, default=200)
            a.add_argument("--same-as")
        if name == "ladder":
            a.add_argument("--replacing")
            a.add_argument("--games", type=int, default=600)
            a.add_argument("--tail", type=int, default=300)
            a.add_argument("--repeats", type=int, default=3)
        if name == "replay":
            a.add_argument("--run", required=True)
            a.add_argument("--game", required=True)
            a.add_argument("--seat", type=int, choices=(0, 1))
    args = ap.parse_args(argv)
    try:
        if args.cmd == "decks":
            from ladder.pool import CRAFT_ZH
            rows = [{"label": k, "code": v, "class": CRAFT_ZH.get(int(v.split(".")[1]), "?")}
                    for k, v in archive().items() if not args.find or args.find.lower() in k.lower()]
            out = {"decks": rows}
        else:
            lab = Lab(args.lab, args.arena, args.workers)
            if args.cmd == "field":
                out = lab.field_rows()
            elif args.cmd == "vs":
                me = lab.mine(args.version, args.deck, args.strategy)
                opps = None if args.same_as else lab.opponents(args.opponent, args.craft, args.vs_deck,
                                                               args.vs_strategy)
                out = lab.vs(me, opps, args.games, args.same_as)
            elif args.cmd == "ladder":
                out = lab.ladder(lab.mine(args.version, args.deck, args.strategy), args.replacing, args.games,
                                 args.tail, args.repeats)
            else:
                out = {"replay": str(lab.replay(args.run, args.game, args.seat))}
    except (LabError, A.ArenaError) as e:
        print(f"没跑：{e}", file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=1))
    if isinstance(out, dict) and out.get("stopped"):
        print(f"停下了：{out['stopped']}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
