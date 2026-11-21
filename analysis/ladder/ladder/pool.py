"""The pool manager (phase 1, item 1.4): members, matching, CR, mu, down-weighting, removal, protection, periods.

    python -m ladder.pool create  POOLDIR --seeds LO HI [--rng-seed N]
    python -m ladder.pool enter   POOLDIR --deck CODE --strategy SPEC --owner WHO [--note TEXT]
    python -m ladder.pool update  POOLDIR --member MID --strategy SPEC --gate REF
    python -m ladder.pool ladder  POOLDIR --workers 11 [--mask 0x3FC3FC] [--games N | --until-period-done]
    python -m ladder.pool advance POOLDIR [--force REASON]
    python -m ladder.pool show    POOLDIR [--private]

Everything follows the task spec §3-§4 (rules.py holds the numbers); the choices it leaves open are assumptions
A3, A4, A13-A19 in DEVIATIONS.md.

Storage: POOLDIR/events.jsonl is the pool. Every change is one appended line (create, enter, start, game, remove,
update, period, exit_reason) and the state is rebuilt by folding the lines in order, the same code path live and on
load, so a stopped ladder resumes where it was and every CR can be traced to the games that made it. The full game
logs (moves, per-step compute) go to POOLDIR/games.jsonl through the batch runner. A game that was started but
never finished (the machine stopped) has no game line: it changes nothing, its seed stays used.

Who owns a member, in which period its deck entered and which version its strategy is at are kept here for the host
and Salem only (`show --private`); outside, a member is its random anonymous id and its class (plan, 公开与私有).
"""
from __future__ import annotations

import argparse
import json
import random
import secrets
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from ladder import rules  # noqa: E402

CRAFTS = (1, 2, 3, 4, 5, 6, 7)    # Forest, Sword, Rune, Dragon, Abyss, Haven, Portal (svsim Craft values)
CRAFT_ZH = {1: "精灵", 2: "皇家护卫", 3: "巫师", 4: "龙族", 5: "梦魇", 6: "主教", 7: "超越者"}
PROTECT_GAMES = 1000              # §4.5 protection: the first 1000 games ...
FULL_PERIOD_GAMES = 2000          # §4.5 a period ends once every member has 2000 games since its last change
UNSTABLE_GAMES = 300              # §4.3 after a strategy update, "unstable" until 300 games
MAX_PER_PLAYER = 7                # plan 阶段 3 名额: at most 7 members per player in the pool
MAX_PER_LIST = 2                  # ... at most 2 members with the same list
NEW_DECKS_PER_PERIOD = 2          # ... at most 2 new decks per player per deck period
HOST_OWNERS = ("baseline", "salem")   # members that belong to no player (§4.1)
ANON_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class PoolError(Exception):
    pass


class ListFull(PoolError):
    """A third member with a list already held by two: the plan compares it with them outside the pool first."""
    def __init__(self, holders):
        super().__init__(f"this list already has {len(holders)} members: {holders}")
        self.holders = holders


def period_kind(n: int) -> str:
    """Period 0 is the phase-1 baseline run; then deck, strategy, deck, ... (§4.5: period 1 is a deck period)."""
    return "baseline" if n == 0 else ("deck" if n % 2 == 1 else "strategy")


def list_key(card_ids) -> str:
    return ".".join(str(c) for c in sorted(card_ids))


@dataclass
class Member:
    mid: str                      # internal id (host and Salem only)
    anon: str                     # random public id: says nothing about owner, age or version; kept on update
    craft: int
    deck: list                    # card ids, frozen at entry
    deck_code: str | None
    owner: str                    # player codename, or "baseline" / "salem"
    entry_period: int
    strategy: str                 # runner spec of the current version
    version: int = 1
    base_version: str = ""
    note: str = ""
    cr: int = rules.ENTRY_CR
    games: int = 0                # decided games (wins + losses) since entry; draws and void games don't count (A3)
    draws: int = 0
    since_change: int = 0         # decided games since the last change (entry or strategy update)
    period_games: int = 0         # decided games in this period since its last change in this period (A14)
    full_strategy_period: bool = False   # has been in the pool through one whole strategy period (§4.5)
    active: bool = True
    removed_at: int | None = None        # event number of the removal
    exit_reason: str | None = None       # 卡组弱 / 还不会打 (set by the host afterwards, plan 吃操作的卡组)
    history: list = field(default_factory=list)   # (version, strategy, base_version, event number, gate ref)

    @property
    def protected(self) -> bool:
        """§4.5: the first 1000 games, or until it has been through a whole strategy period, whichever is later."""
        return self.games < PROTECT_GAMES or not self.full_strategy_period

    @property
    def unstable(self) -> bool:
        return self.since_change < UNSTABLE_GAMES


def pick_opponent(a, members, mu: float, rng: random.Random, cr: float | None = None):
    """§4.2 for one side `a` (its CR `cr`, default a.cr): the opponent's class uniformly over the 7, again while
    that class has nobody (other than `a`); within it, by matching weight among members within 200, else the one
    with the closest CR (ties uniformly, A17). Shared by the pool and the frozen-pool evaluator."""
    mine = a.cr if cr is None else cr
    by_craft = {}
    for m in members:
        if m is not a:
            by_craft.setdefault(m.craft, []).append(m)
    if not by_craft:
        raise PoolError("nobody to play")
    while True:
        cands = by_craft.get(rng.choice(CRAFTS))
        if not cands:
            continue                                           # nobody of that class: draw the class again
        near = [m for m in cands if rules.within_window(mine, m.cr)]
        if near:
            w = [rules.effective_weight(m.cr, mu, m.protected) for m in near]
            return rng.choices(near, weights=w)[0], "window"
        best = min(abs(m.cr - mine) for m in cands)
        return rng.choice([m for m in cands if abs(m.cr - mine) == best]), "closest"


class Pool:
    def __init__(self, path, on_event=None):
        """`path` None: an in-memory pool (statistical checks on made-up results; nothing written).
        `on_event(pool, ev)` is called after every event is folded in, on load and live (the leaderboard uses it)."""
        self.dir = Path(path) if path is not None else None
        self.events_path = self.dir / "events.jsonl" if self.dir else None
        self.games_path = self.dir / "games.jsonl" if self.dir else None
        self.on_event = on_event
        self.members: dict[str, Member] = {}
        self.period = 0
        self.params: dict = {}
        self.used_seeds: set[int] = set()
        self.started = 0                 # games started (each one used a seed)
        self.settled = 0
        self.n_events = 0
        self.inflight: dict[str, dict] = {}
        self.cr_sum_check = 0            # sum of CR changes from games (zero-sum check)
        self.lost_to_removal = 0         # CR changes that went to a member already removed (A4)
        if self.events_path is not None and self.events_path.exists():
            for line in self.events_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self._apply(json.loads(line))
            self.inflight.clear()        # started but never finished: changes nothing, the seed stays used

    # --- creation and the event log --------------------------------------------------------------------------

    @classmethod
    def create(cls, path, seeds: tuple[int, int], rng_seed: int | None = None, note: str = "",
               on_event=None) -> "Pool":
        if path is not None:
            d = Path(path)
            if (d / "events.jsonl").exists():
                raise PoolError(f"{d} already holds a pool")
            d.mkdir(parents=True, exist_ok=True)
        pool = cls(path, on_event=on_event)
        lo, hi = int(seeds[0]), int(seeds[1])
        if not lo < hi:
            raise PoolError("empty seed range")
        pool._log({"ev": "create", "seeds": [lo, hi], "rng_seed": rng_seed if rng_seed is not None
                   else secrets.randbits(48), "note": note,
                   "rules": {"entry": rules.ENTRY_CR, "window": rules.WINDOW, "floor": rules.WEIGHT_FLOOR,
                             "remove_at": rules.REMOVE_AT, "protect": PROTECT_GAMES, "period": FULL_PERIOD_GAMES,
                             "unstable": UNSTABLE_GAMES}})
        return pool

    def _log(self, ev: dict) -> dict:
        ev = {"n": self.n_events, **ev}
        if self.dir is not None:
            with self.events_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")
                f.flush()
        self._apply(ev)
        return ev

    def _apply(self, ev: dict):
        """Fold one event into the state. The only place the state changes."""
        kind = ev["ev"]
        self.n_events = ev["n"] + 1
        if kind == "create":
            self.params = ev
        elif kind == "enter":
            m = Member(**ev["member"])
            m.history = [[m.version, m.strategy, m.base_version, ev["n"], None]]
            self.members[m.mid] = m
        elif kind == "start":
            self.used_seeds.add(ev["seed"])
            self.started += 1
            self.inflight[ev["id"]] = ev
        elif kind == "game":
            self.inflight.pop(ev["id"], None)
            self.settled += 1
            for mid, d in zip(ev["members"], ev["deltas"]):
                m = self.members[mid]
                if ev["decided"]:
                    if m.active:
                        m.cr += d
                        m.games += 1
                        m.since_change += 1
                        m.period_games += 1
                        self.cr_sum_check += d
                    else:
                        self.lost_to_removal += d
                elif ev["result"] == "draw" and m.active:
                    m.draws += 1
        elif kind == "remove":
            m = self.members[ev["member"]]
            m.active, m.removed_at = False, ev["n"]
        elif kind == "update":
            m = self.members[ev["member"]]
            m.version, m.strategy, m.base_version = ev["version"], ev["strategy"], ev["base_version"]
            m.since_change = m.period_games = 0
            m.history.append([m.version, m.strategy, m.base_version, ev["n"], ev.get("gate")])
        elif kind == "period":
            if period_kind(self.period) == "strategy":      # the strategy period that just ended
                for mid in ev.get("through_strategy_period", []):
                    self.members[mid].full_strategy_period = True
            self.period = ev["period"]
            for m in self.members.values():
                m.period_games = 0
        elif kind == "exit_reason":
            self.members[ev["member"]].exit_reason = ev["reason"]
        else:
            raise PoolError(f"unknown event {kind}")
        if self.on_event is not None:
            self.on_event(self, ev)

    # --- state ---------------------------------------------------------------------------------------------

    def active(self, craft: int | None = None) -> list[Member]:
        return [m for m in self.members.values() if m.active and (craft is None or m.craft == craft)]

    @property
    def mu(self) -> float:
        """§4.1: the mean CR of every member now in the pool."""
        act = self.active()
        return sum(m.cr for m in act) / len(act) if act else float(rules.ENTRY_CR)

    def weight(self, m: Member, mu: float | None = None) -> float:
        return rules.effective_weight(m.cr, self.mu if mu is None else mu, m.protected)

    def total_cr(self) -> int:
        return sum(m.cr for m in self.active())

    # --- entering, updating, periods ---------------------------------------------------------------------------

    def enter(self, deck, strategy: str, owner: str, deck_code: str | None = None, note: str = "",
              base_version: str | None = None, rng=None) -> str:
        """A new member at 1500 (§4.1). Only in the baseline run or a deck period (§4.5)."""
        from ladder import base
        kind = period_kind(self.period)
        if kind == "strategy":
            raise PoolError("no new decks in a strategy period (§4.5)")
        if owner not in HOST_OWNERS and kind == "baseline":
            raise PoolError("players' decks enter from period 1")
        ids = [int(c) for c in deck]
        if len(ids) != 40:
            raise PoolError(f"a deck has 40 cards, not {len(ids)}")
        craft = base.craft_of(_cards(ids))
        key = list_key(ids)
        holders = [m.mid for m in self.active() if list_key(m.deck) == key]
        if len(holders) >= MAX_PER_LIST:
            raise ListFull(holders)
        if owner not in HOST_OWNERS:
            mine = [m for m in self.active() if m.owner == owner]
            if len(mine) >= MAX_PER_PLAYER:
                raise PoolError(f"{owner} already has {len(mine)} members in the pool (at most {MAX_PER_PLAYER})")
            new_here = [m for m in self.members.values() if m.owner == owner and m.entry_period == self.period]
            if len(new_here) >= NEW_DECKS_PER_PERIOD:
                raise PoolError(f"{owner} already entered {len(new_here)} decks this period")
        rng = rng or secrets.SystemRandom()
        taken = {m.anon for m in self.members.values()}
        while True:
            anon = "".join(rng.choice(ANON_ALPHABET) for _ in range(6))
            if anon not in taken:
                break
        mid = f"m{len(self.members) + 1:04d}"
        m = Member(mid=mid, anon=anon, craft=craft, deck=ids, deck_code=deck_code, owner=owner,
                   entry_period=self.period, strategy=strategy, base_version=base_version or base.BASE_VERSION,
                   note=note)
        d = asdict(m)
        d.pop("history")
        self._log({"ev": "enter", "member": d})
        return mid

    def update(self, mid: str, strategy: str, gate: str, base_version: str | None = None) -> int:
        """A strategy update that passed its gate (§4.3): new version, same CR, unstable for 300 games."""
        from ladder import base
        if period_kind(self.period) != "strategy":
            raise PoolError("strategy updates take effect only in a strategy period (§4.3)")
        m = self.members.get(mid)
        if m is None or not m.active:
            raise PoolError(f"{mid} is not in the pool")
        if not gate:
            raise PoolError("an update needs the gate record that passed it")
        self._log({"ev": "update", "member": mid, "version": m.version + 1, "strategy": strategy,
                   "base_version": base_version or base.BASE_VERSION, "gate": gate})
        return m.version

    def period_done(self) -> list[str]:
        """The members still short of 2000 games in this period since their last change (empty = may advance)."""
        return [m.mid for m in self.active() if m.period_games < FULL_PERIOD_GAMES]

    def advance(self, force: str | None = None) -> int:
        short = self.period_done()
        if short and not force:
            raise PoolError(f"{len(short)} members still short of {FULL_PERIOD_GAMES} games: {short[:10]}")
        through = []
        if period_kind(self.period) == "strategy":
            # nobody enters during a strategy period, so everyone in the pool now was there for all of it
            through = [m.mid for m in self.active()]
        self._log({"ev": "period", "period": self.period + 1, "kind": period_kind(self.period + 1),
                   "through_strategy_period": through, "forced": force, "short": short})
        return self.period

    def set_exit_reason(self, mid: str, reason: str):
        if reason not in ("卡组弱", "还不会打"):
            raise PoolError("reason is 卡组弱 or 还不会打")
        if self.members[mid].active:
            raise PoolError(f"{mid} is still in the pool")
        self._log({"ev": "exit_reason", "member": mid, "reason": reason})

    # --- matching (§4.2) -------------------------------------------------------------------------------------

    def draw_pair(self, rng: random.Random) -> tuple[Member, Member, str]:
        """The initiator by matching weight; the opponent's class uniformly over the 7; within it, by weight among
        members within 200, else the one with the closest CR; a class with nobody in it is drawn again."""
        act = self.active()
        if len(act) < 2:
            raise PoolError("fewer than two members in the pool")
        mu = self.mu
        a = rng.choices(act, weights=[self.weight(m, mu) for m in act])[0]
        b, how = pick_opponent(a, act, mu, rng)
        return a, b, how

    def next_job(self) -> dict:
        """Pair two members from the CRs of this moment, reserve a ladder seed, log the start."""
        lo, hi = self.params["seeds"]
        rng = random.Random(f"{self.params['rng_seed']}:{self.started}")
        a, b, how = self.draw_pair(rng)
        if len(self.used_seeds) >= hi - lo:
            raise PoolError("the ladder seed range is used up")
        while True:
            seed = rng.randrange(lo, hi)
            if seed not in self.used_seeds:
                break
        seats = [a, b] if rng.random() < 0.5 else [b, a]       # who sits in seat 0; who goes first is the seed's
        gid = f"L{self.period}-{self.started + 1:07d}"
        self._log({"ev": "start", "id": gid, "seed": seed, "members": [m.mid for m in seats],
                   "initiator": a.mid, "how": how, "cr": [m.cr for m in seats], "mu": round(self.mu, 3),
                   "period": self.period})
        return {"id": gid, "seed": seed, "first": None, "decks": [m.deck for m in seats],
                "strategies": [m.strategy for m in seats], "strategy_seeds": None,
                "labels": {"members": [m.mid for m in seats], "anon": [m.anon for m in seats],
                           "versions": [m.version for m in seats], "base": [m.base_version for m in seats],
                           "period": self.period}}

    # --- settling (§3, §4.2) ---------------------------------------------------------------------------------

    def settle(self, log: dict) -> dict:
        """One finished game, in the order games end (A4: the CRs of this moment). Then removals."""
        start = self.inflight.get(log["id"])
        if start is None:
            raise PoolError(f"{log['id']} was not started by this pool")
        mids = start["members"]
        ms = [self.members[x] for x in mids]
        decided = log["result"] in ("normal", "crash", "illegal", "timeout") and log.get("winner") in (0, 1)
        deltas = [0, 0]
        if decided:
            w = log["winner"]
            deltas[w] = rules.delta(ms[w].cr, ms[1 - w].cr, True)
            deltas[1 - w] = rules.delta(ms[1 - w].cr, ms[w].cr, False)
            if deltas[0] + deltas[1] != 0:
                raise AssertionError("not zero-sum")
        ev = self._log({"ev": "game", "id": log["id"], "members": mids, "result": log["result"],
                        "winner": log.get("winner"), "decided": decided, "cr_before": [m.cr for m in ms],
                        "deltas": deltas, "active": [m.active for m in ms]})
        removed = self._remove_below_line()
        ev["mu_after"] = round(self.mu, 3)
        ev["removed"] = removed
        return ev

    def _remove_below_line(self) -> list[str]:
        """§4.2: CR <= mu - 300 leaves at once (not in protection). mu rises with each removal, so check again
        until nobody else is below the line (A16)."""
        out = []
        while True:
            mu = self.mu
            below = [m for m in self.active() if rules.to_remove(m.cr, mu, m.protected)]
            if not below or len(self.active()) - len(below) < 1:
                return out
            for m in below:
                self._log({"ev": "remove", "member": m.mid, "cr": m.cr, "mu": round(mu, 3),
                           "games": m.games, "version": m.version})
                out.append(m.mid)

    # --- running the ladder ----------------------------------------------------------------------------------

    def jobs(self, games: int | None = None, until_period_done: bool = False):
        """Pairings on demand: stop after `games` more starts, or once every member has its 2000 games."""
        n = 0
        while True:
            if games is not None and n >= games:
                return
            if until_period_done and not self.period_done():
                return
            n += 1
            yield self.next_job()

    def ladder(self, workers: int = 4, games: int | None = None, until_period_done: bool = False,
               step_limit: float = 30.0, mask=None, quiet=True) -> dict:
        from ladder import runner
        self.inflight.clear()
        if games is None and not until_period_done:
            raise PoolError("say how many games, or until the period is done")
        return runner.run(self.jobs(games, until_period_done), str(self.games_path), workers=workers,
                          step_limit=step_limit, mask=mask, quiet=quiet, on_result=self.settle)

    # --- views ---------------------------------------------------------------------------------------------

    def public_rows(self) -> list[dict]:
        """What any player may see now (plan 公开与私有): anon id, class, relative CR. No game counts, no
        'unstable' mark, no owner, no age, no version."""
        mu = self.mu
        rows = [{"anon": m.anon, "craft": CRAFT_ZH[m.craft], "rel_cr": round(m.cr - mu, 1),
                 "baseline": m.owner == "baseline"} for m in self.active()]
        return sorted(rows, key=lambda r: -r["rel_cr"])

    def private_rows(self) -> list[dict]:
        mu = self.mu
        return [{"mid": m.mid, "anon": m.anon, "craft": CRAFT_ZH[m.craft], "owner": m.owner,
                 "entry_period": m.entry_period, "version": m.version, "base": m.base_version, "cr": m.cr,
                 "rel_cr": round(m.cr - mu, 1), "games": m.games, "draws": m.draws, "since_change": m.since_change,
                 "period_games": m.period_games, "protected": m.protected, "unstable": m.unstable,
                 "active": m.active, "exit_reason": m.exit_reason} for m in self.members.values()]


def _cards(ids):
    from ladder.runner import load_deck
    return load_deck(ids)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create"); c.add_argument("dir"); c.add_argument("--seeds", type=int, nargs=2, required=True)
    c.add_argument("--rng-seed", type=int); c.add_argument("--note", default="")
    e = sub.add_parser("enter"); e.add_argument("dir"); e.add_argument("--deck", required=True)
    e.add_argument("--strategy", required=True); e.add_argument("--owner", required=True)
    e.add_argument("--note", default="")
    u = sub.add_parser("update"); u.add_argument("dir"); u.add_argument("--member", required=True)
    u.add_argument("--strategy", required=True); u.add_argument("--gate", required=True)
    l_ = sub.add_parser("ladder"); l_.add_argument("dir"); l_.add_argument("--workers", type=int, default=4)
    l_.add_argument("--mask"); l_.add_argument("--games", type=int); l_.add_argument("--until-period-done",
                                                                                   action="store_true")
    l_.add_argument("--step-limit", type=float, default=30.0)
    a_ = sub.add_parser("advance"); a_.add_argument("dir"); a_.add_argument("--force")
    s = sub.add_parser("show"); s.add_argument("dir"); s.add_argument("--private", action="store_true")
    a = ap.parse_args()
    if a.cmd == "create":
        Pool.create(a.dir, tuple(a.seeds), a.rng_seed, a.note)
        print(json.dumps({"created": a.dir}))
        return
    pool = Pool(a.dir)
    if a.cmd == "enter":
        from ladder.runner import load_deck
        ids = [c.card_id for c in load_deck(a.deck)]
        print(json.dumps({"member": pool.enter(ids, a.strategy, a.owner, deck_code=a.deck, note=a.note)}))
    elif a.cmd == "update":
        print(json.dumps({"version": pool.update(a.member, a.strategy, a.gate)}))
    elif a.cmd == "ladder":
        res = pool.ladder(a.workers, a.games, a.until_period_done, a.step_limit,
                          int(a.mask, 16) if a.mask else None, quiet=False)
        print(json.dumps({**res, "mu": round(pool.mu, 2), "short": len(pool.period_done())}))
    elif a.cmd == "advance":
        print(json.dumps({"period": pool.advance(a.force), "kind": period_kind(pool.period)}))
    elif a.cmd == "show":
        rows = pool.private_rows() if a.private else pool.public_rows()
        print(json.dumps({"period": pool.period, "kind": period_kind(pool.period), "mu": round(pool.mu, 2),
                          "members": rows}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
