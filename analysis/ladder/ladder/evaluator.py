"""The frozen-pool evaluator (phase 1, item 1.5; task spec §4.4 final evaluation, steps 1 and 3).

    python -m ladder.evaluator freeze  POOLDIR --out FROZEN.json [--cr last1000 | current]
    python -m ladder.evaluator run     FROZEN.json --candidate MID | --deck CODE --strategy SPEC
                                       --out DIR --seeds LO HI [--games 1200 --tail 600 --repeats 5]
                                       [--workers 11 --mask 0x3FC3FC] [--rng-seed N]

Freeze: every member's CR is fixed, by default at the mean of its CR over its last 1000 decided games (§4.4 step 1;
A22: the last 1000 whatever version played them). The frozen pool is a file: members, decks, strategies, versions,
fixed CRs.

Run: the candidate (a member taken out of the frozen pool, or any deck + strategy) is the only member whose CR moves.
mu is the mean of the other members' fixed CRs and stays put; the candidate starts at mu (rounded: CRs are integers).
Every game is the candidate against an opponent drawn by the pool's own matching (pool.pick_opponent: class
uniformly, drawn again while it has nobody within 200 (Salem's S2), then by matching weight). One repeat is `games`
decided games (draws don't count, A3); its value is the mean CR over the last `tail` of them minus mu. A candidate
whose CR gets more than 200 past every frozen member has nobody within reach, and frozen members never move back:
by Salem's ruling S3 (11-22, 「严格停住，不打」) it plays nobody, so the repeat stops there and its remaining games
count at that CR (A30). The value is then a bound and the result says so ("stuck": which repeats, after how many
games, at the top or the bottom). Made-up repeats read a candidate 50-100 above the strongest frozen member 70-100
too high this way (LD-22); FAR = "closest" (the closest member instead, A28, not adopted) is kept for comparison. Repeats are independent (fresh seeds,
fresh start), so the interval is Student's t over the repeat values: the strong game-to-game correlation inside a
repeat never enters it. The phase-1 fluctuation check (20 evaluations of one strategy) tests that.

Seeds: each game's seed is drawn at random, without repetition, from the range given (the final self-test range for
the final evaluation, §4.4 step 5). A game the machine stopped is played again first on resume, with the same seed
and the same opponent (§7), and the log says so.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import secrets
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for p in (str(ROOT), str(HERE.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

from ladder import rules  # noqa: E402
from ladder.leaderboard import load as load_series, t975  # noqa: E402
from ladder.pool import CRAFT_ZH, NoOpponent, PoolError, near_by_craft, pick_opponent  # noqa: E402

FREEZE_GAMES = 1000
FAR = "wait"        # S3 (Salem 11-22): nobody within 200 in a frozen pool -> stop; "closest" = A28, not adopted


@dataclass
class Frozen:
    mid: str
    anon: str
    craft: int
    cr: int
    deck: list
    strategy: str
    version: int = 1
    base_version: str = ""
    protected: bool = False          # kept as it was when frozen (the matching weight uses it)
    games: int = 0
    cr_from: int = 0                 # how many games the fixed CR averages


@dataclass
class Candidate:
    mid: str
    craft: int
    deck: list
    strategy: str
    cr: float = 0.0
    protected: bool = True


def freeze(pool_dir, cr: str = "last1000") -> dict:
    pool, series = load_series(pool_dir)
    members = []
    for m in pool.active():
        pts = series.points[m.mid]
        if cr == "last1000" and pts:
            tail = pts[-FREEZE_GAMES:]
            fixed, n = round(sum(c for c, _ in tail) / len(tail)), len(tail)
        else:
            fixed, n = m.cr, 0
        members.append(Frozen(mid=m.mid, anon=m.anon, craft=m.craft, cr=int(fixed), deck=list(m.deck),
                              strategy=m.strategy, version=m.version, base_version=m.base_version,
                              protected=m.protected, games=m.games, cr_from=n))
    body = {"pool": str(pool_dir), "period": pool.period, "events": pool.n_events, "cr": cr,
            "members": [asdict(x) for x in members]}
    body["hash"] = hashlib.sha256(json.dumps(body["members"], sort_keys=True).encode()).hexdigest()[:16]
    return body


def load_frozen(path) -> tuple[list[Frozen], dict]:
    body = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Frozen(**m) for m in body["members"]], body


def opponents_for(frozen: list[Frozen], candidate_mid: str | None) -> tuple[list[Frozen], float]:
    others = [f for f in frozen if f.mid != candidate_mid]
    if not others:
        raise PoolError("nobody left to play")
    return others, sum(f.cr for f in others) / len(others)


def summarize(values: list[float]) -> dict:
    r = len(values)
    mean = sum(values) / r
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (r - 1)) if r > 1 else float("nan")
    se = sd / math.sqrt(r) if r > 1 else float("nan")
    half = t975(r - 1) * se if r > 1 else float("nan")
    return {"rel_cr": mean, "se": se, "lo": mean - half, "hi": mean + half, "repeats": r, "values": values}


def repeat_sync(play, others: list[Frozen], mu: float, games: int, tail: int, rng: random.Random,
                cand: Candidate | None = None) -> float:
    """One repeat with a made-up game: `play(opponent, rng)` -> True (won), False (lost) or None (draw).
    The statistical checks use this; real games go through `run`."""
    cand = cand or Candidate("cand", 0, [], "")
    cr, crs = round(mu), []
    while len(crs) < games:
        try:
            opp, _ = pick_opponent(cand, others, mu, rng, cr=cr, far=FAR)
        except NoOpponent:                       # FAR "wait": nobody within 200 ever again; the CR stays put
            crs += [cr] * (games - len(crs))
            break
        won = play(opp, rng)
        if won is None:
            continue
        cr += rules.delta(cr, opp.cr, won)
        crs.append(cr)
    return sum(crs[-tail:]) / tail - mu


class Evaluation:
    """One candidate, `repeats` repeats of `games` decided real games each, against a frozen pool."""

    def __init__(self, frozen_path, out_dir, candidate: Candidate, seeds, games=1200, tail=600, repeats=5,
                 rng_seed=None):
        self.frozen, self.body = load_frozen(frozen_path)
        self.others, self.mu = opponents_for(self.frozen, candidate.mid)
        self.by_mid = {f.mid: f for f in self.others}
        self.cand = candidate
        self.dir = Path(out_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.starts_path, self.games_path = self.dir / "starts.jsonl", self.dir / "games.jsonl"
        self.meta_path = self.dir / "meta.json"
        meta = {"frozen": str(frozen_path), "frozen_hash": self.body["hash"], "candidate": asdict(candidate),
                "seeds": list(seeds), "games": games, "tail": tail, "repeats": repeats,
                "mu": self.mu, "rng_seed": rng_seed if rng_seed is not None else secrets.randbits(48)}
        if self.meta_path.exists():
            old = json.loads(self.meta_path.read_text(encoding="utf-8"))
            for k in ("frozen_hash", "candidate", "seeds", "games", "tail", "repeats"):
                if old[k] != meta[k]:
                    raise PoolError(f"{out_dir} holds another evaluation ({k} differs)")
            meta = old
        else:
            self.meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        self.meta = meta
        self.games, self.tail, self.repeats = games, tail, repeats
        self.lo, self.hi = seeds
        self.cr = [round(self.mu)] * repeats
        self.crs = [[] for _ in range(repeats)]
        self.counts: dict[str, int] = {}
        self.starts, self.used, self.inflight = {}, set(), {}
        self.n_started = [0] * repeats
        if self.starts_path.exists():
            for line in self.starts_path.read_text(encoding="utf-8").splitlines():
                st = json.loads(line)
                self.starts[st["id"]] = st
                self.used.add(st["seed"])
                self.n_started[st["rep"]] += 1
        finished = set()
        if self.games_path.exists():
            for line in self.games_path.read_text(encoding="utf-8").splitlines():
                log = json.loads(line)
                finished.add(log["id"])
                self._fold(log)
        self.redo = [st for gid, st in self.starts.items() if gid not in finished]   # stopped by the machine

    def _fold(self, log):
        st = self.starts[log["id"]]
        self.counts[log["result"]] = self.counts.get(log["result"], 0) + 1
        decided = log["result"] in ("normal", "crash", "illegal", "timeout") and log.get("winner") in (0, 1)
        if decided:
            rep = st["rep"]
            won = log["winner"] == st["cand_seat"]
            self.cr[rep] += rules.delta(self.cr[rep], st["opp_cr"], won)
            self.crs[rep].append(self.cr[rep])

    def _job(self, st):
        opp = self.by_mid[st["opp"]]
        sides = [(self.cand.deck, self.cand.strategy), (opp.deck, opp.strategy)]
        if st["cand_seat"] == 1:
            sides.reverse()
        return {"id": st["id"], "seed": st["seed"], "first": None, "decks": [d for d, _ in sides],
                "strategies": [s for _, s in sides], "strategy_seeds": None,
                "labels": {"eval": self.meta["frozen_hash"], "rep": st["rep"], "candidate": self.cand.mid,
                           "opponent": opp.mid, "cand_seat": st["cand_seat"], "rerun": st.get("rerun", False)}}

    def _start(self, rep):
        k = self.n_started[rep]
        rng = random.Random(f"{self.meta['rng_seed']}:{rep}:{k}")
        opp, how = pick_opponent(self.cand, self.others, self.mu, rng, cr=self.cr[rep], far=FAR)
        if len(self.used) >= self.hi - self.lo:
            raise PoolError("the seed range is used up")
        while True:
            seed = rng.randrange(self.lo, self.hi)
            if seed not in self.used:
                break
        st = {"id": f"E{rep}-{k + 1:05d}", "rep": rep, "seed": seed, "opp": opp.mid, "opp_cr": opp.cr,
              "cand_cr": self.cr[rep], "cand_seat": rng.randrange(2), "how": how}
        self.n_started[rep] += 1
        self.used.add(seed)
        self.starts[st["id"]] = st
        with self.starts_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(st) + "\n")
        return st

    def _out_of_reach(self, rep) -> bool:
        """FAR "wait" only: nobody within 200 of this repeat's CR now (decided by the CR alone, so a resume finds
        it again)."""
        return FAR == "wait" and not near_by_craft(self.cand, self.others, self.cr[rep])

    def _stuck(self, rep) -> bool:
        """Short of its games, out of reach, and nothing in flight that could bring it back."""
        return (len(self.crs[rep]) < self.games and self._out_of_reach(rep)
                and not any(x == rep for x in self.inflight.values()) and not any(st["rep"] == rep for st in self.redo))

    def jobs(self):
        while self.redo:
            st = dict(self.redo.pop(0), rerun=True)
            self.inflight[st["id"]] = st["rep"]
            yield self._job(st)
        while True:
            prog = {r: len(self.crs[r]) + sum(1 for x in self.inflight.values() if x == r)
                    for r in range(self.repeats)}
            need = [r for r in range(self.repeats) if prog[r] < self.games and not self._out_of_reach(r)]
            if not need:
                return                   # done, stuck, or out of reach until the games in flight come back
            rep = min(need, key=lambda r: prog[r])
            st = self._start(rep)
            self.inflight[st["id"]] = rep
            yield self._job(st)

    def on_result(self, log):
        self.inflight.pop(log["id"], None)
        self._fold(log)

    def done(self) -> bool:
        return all(len(c) >= self.games or self._stuck(r) for r, c in enumerate(self.crs))

    def run(self, workers=4, step_limit=30.0, mask=None, quiet=True) -> dict:
        from ladder import runner
        idle = 0
        while not self.done():
            before = sum(len(c) for c in self.crs)
            runner.run(self.jobs(), str(self.games_path), workers=workers, step_limit=step_limit, mask=mask,
                       quiet=quiet, on_result=self.on_result)
            self.inflight.clear()
            idle = idle + 1 if sum(len(c) for c in self.crs) == before else 0
            if idle > 50:
                raise PoolError("too many rounds without a decided game: games keep ending void or drawn")
        return self.result()

    def result(self) -> dict:
        top, bottom = max(f.cr for f in self.others), min(f.cr for f in self.others)
        stuck, values = [], []
        for r, c in enumerate(self.crs):
            if len(c) < self.games:                                    # FAR "wait": stopped out of reach
                stuck.append({"rep": r, "after": len(c), "cr": self.cr[r],
                              "side": "top" if self.cr[r] > top else "bottom" if self.cr[r] < bottom else "?"})
                c = c + [self.cr[r]] * (self.games - len(c))
            values.append(sum(c[self.games - self.tail:self.games]) / self.tail - self.mu)
        out = {"candidate": self.cand.mid, "craft": CRAFT_ZH.get(self.cand.craft), "mu": self.mu,
               "frozen_hash": self.meta["frozen_hash"], "games": self.games, "tail": self.tail,
               "results": self.counts, "far_rule": FAR, "stuck": stuck,
               "far_games": sum(1 for st in self.starts.values() if st.get("how") == "far"), **summarize(values)}
        (self.dir / "result.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        return out


def candidate_from(frozen: list[Frozen], mid=None, deck=None, strategy=None) -> Candidate:
    if mid:
        f = next(x for x in frozen if x.mid == mid)
        return Candidate(f.mid, f.craft, f.deck, f.strategy)
    from ladder import base
    from ladder.runner import load_deck
    cards = load_deck(deck)
    return Candidate("outside", base.craft_of(cards), [c.card_id for c in cards], strategy)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freeze"); f.add_argument("pool"); f.add_argument("--out", required=True)
    f.add_argument("--cr", default="last1000", choices=["last1000", "current"])
    r = sub.add_parser("run"); r.add_argument("frozen"); r.add_argument("--candidate"); r.add_argument("--deck")
    r.add_argument("--strategy"); r.add_argument("--out", required=True)
    r.add_argument("--seeds", type=int, nargs=2, required=True)
    r.add_argument("--games", type=int, default=1200); r.add_argument("--tail", type=int, default=600)
    r.add_argument("--repeats", type=int, default=5); r.add_argument("--workers", type=int, default=4)
    r.add_argument("--mask"); r.add_argument("--step-limit", type=float, default=30.0)
    r.add_argument("--rng-seed", type=int)
    a = ap.parse_args()
    if a.cmd == "freeze":
        body = freeze(a.pool, a.cr)
        Path(a.out).write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps({"members": len(body["members"]), "hash": body["hash"]}))
        return
    frozen, _ = load_frozen(a.frozen)
    cand = candidate_from(frozen, a.candidate, a.deck, a.strategy)
    ev = Evaluation(a.frozen, a.out, cand, tuple(a.seeds), a.games, a.tail, a.repeats, a.rng_seed)
    print(json.dumps(ev.run(a.workers, a.step_limit, int(a.mask, 16) if a.mask else None, quiet=False),
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
