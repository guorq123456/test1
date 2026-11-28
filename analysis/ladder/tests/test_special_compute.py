"""tools/special_compute.py (plan 4.5): period 4's compute check on the round robin's games. A made-up host as in
tests/test_special_rr.py. Games only on seeds 96540000-96549999 (the host's third probe range, this check's tests):
the round robin 96540000-96540017 (special_rr's SEEDS patched, 2 a pair), the calibration 96540100-96540104
(CAL_SEEDS patched); the formal 96600000-96609999 is only checked as constants, never played."""
import json
import random
import secrets
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "tools"))
sys.path.insert(0, str(HERE))
import special_compute as SC
import special_rr as R
import test_special_rr as TR

from ladder import compute_audit as CA
from ladder import deal
from ladder.pool import Pool
from ladder.submit import (
    COMPUTE_CAP,
    COMPUTE_REFUSE,
    DEFAULT,
    TURN_K,
    TURN_REFUSE,
    turn_budget,
)

TWO = ("pa-alpha", "pb-bravo")
HEAVY = '''from ladder.interface import PlayerStrategy


class Mine(PlayerStrategy):
    ITERATIONS = 500
'''
PLANNER = '''from ladder.interface import PlayerStrategy, sample_states
from svsim.search.mcts import ISMCTS


class Mine(PlayerStrategy):
    def __init__(self, seed=0):
        super().__init__(seed)
        self.planner = ISMCTS(iterations=100, seed=self.random.getrandbits(31))

    def turn_start(self, pos):
        for s in sample_states(pos, self.guess(pos), self.random, 6):
            self.planner.choose(s)
'''
PLAIN = '''from ladder.interface import PlayerStrategy


class Mine(PlayerStrategy):
    pass
'''
CODE = {("pa-alpha", 1): HEAVY, ("pa-alpha", 4): PLANNER, ("pa-alpha", 6): PLAIN, ("pb-bravo", 1): TR.STRATEGY}


@pytest.fixture(autouse=True)
def _own_path(monkeypatch):
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.delenv("LADDER_EXTRA_PATH", raising=False)
    monkeypatch.delenv(deal.KEY_ENV, raising=False)


def _host(tmp_path, code=CODE):
    """Two players: alpha's three blueprints (heavy, a planner, the default's own), bravo's 快攻妖精 (random moves);
    bravo's 跳费龙 and 兔子教 missing. The pool past period 4, never played."""
    host = tmp_path / "host"
    pool = Pool.create(host / "pool", seeds=(96549990, 96550000), rng_seed=1)
    for _ in range(5):
        pool.advance(force="test")
    subs = host / "subs"
    (subs / "code").mkdir(parents=True)
    lines = []
    for n, ((player, craft), src) in enumerate(code.items(), 1):
        rid = f"S-{n:04d}"
        (subs / rid).mkdir()
        (subs / rid / "submission.json").write_text(json.dumps({"type": "新卡组", "deck": TR._code(craft)}),
                                                    encoding="utf-8")
        (subs / "code" / f"sub_S{n:04d}.py").write_text(src, encoding="utf-8")
        lines.append({"ev": "receipt", "id": rid, "player": player, "period": 4, "kind": "deck", "verdict": "收下",
                      "member": f"{player.split('-')[1]}-{craft}", "craft": craft, "spec": f"py:sub_S{n:04d}:Mine",
                      "version": "submit-4", "blueprint": TR._record(craft, 0), "compute_ratio": 1.02,
                      "compute": {"K": TURN_K, "rule": "old", "in_turn": 1.01, "turn_start_q": 0.31}})
    TR._ledger(host, lines)
    return host, lines


def _env(monkeypatch):
    import environments
    monkeypatch.setattr(environments, "check", lambda period, root=None: {"name": "test-env"})


def _round_robin(tmp_path, monkeypatch, key):
    """The made-up host's formal round robin, 2 seeds a pair on 96540000-96540017: 3 pairs played, 12 games."""
    monkeypatch.setattr(R, "SEEDS", {4: (96540000, 96540100)})
    monkeypatch.setattr(R, "PER_PAIR", 2)
    _env(monkeypatch)
    host, lines = _host(tmp_path)
    body = R.evaluate(host, 4, workers=2, key=key, players=TWO, log=lambda *_: None)
    assert body["games"]["played"] == 12 and len(body["missing"]) == 2
    return host, lines


# --- no games ---------------------------------------------------------------------------------------------------------

def test_the_formal_calibration_seeds_and_pairs():
    assert SC.CAL_SEEDS[4] == (96600000, 96610000) and SC.PER_MEMBER == 30 and SC.CAL_GAMES == 60
    assert deal.formal(96600000) is None                       # not a FORMAL segment: the tool itself needs the key
    lay = SC.cal_layout(4, 60)
    assert lay["n"] == 30 and lay["used"] == [96600000, 96600029]
    jobs = SC.cal_jobs(4, lay)
    from ladder import special
    bp = {c: special.blueprint_for(4, c)["ids"] for c, _, _ in R.ARCH}
    assert len(jobs) == 60 and len({j["id"] for j in jobs}) == 60
    assert all(j["strategies"] == [DEFAULT, DEFAULT] and j["strategy_seeds"] is None for j in jobs)
    for i in range(30):
        a, b = jobs[2 * i], jobs[2 * i + 1]
        assert a["seed"] == b["seed"] == 96600000 + i and a["decks"] == b["decks"][::-1]
        assert a["decks"] == [bp[SC.COMBOS[i % 9][0]], bp[SC.COMBOS[i % 9][1]]]
    from collections import Counter
    mix = Counter(frozenset((j["labels"]["arch"][0], j["labels"]["arch"][1])) for j in jobs[:18])
    assert all(n == (2 if len(k) == 1 else 4) for k, n in mix.items()) and len(mix) == 6   # as the round robin's
    assert SC.cal_layout(4, 61)["n"] == 31
    for bad in ((5, 60), (4, 0), (4, 20001)):
        with pytest.raises(R.EvalError):
            SC.cal_layout(*bad)


def _log(gid, members, receipts, result="normal", steps=((0, 5, 1), (1, 5, 1), (0, 9, 1)), period=4):
    return {"id": gid, "result": result, "steps": [list(s) for s in steps],
            "labels": {"rr": period, "members": list(members), "receipts": list(receipts)}}


def test_the_draw_is_fixed_and_takes_only_the_members_own_ended_games(tmp_path):
    members = {"a/快攻妖精": {"receipt": "S-0001"}, "b/快攻妖精": {"receipt": "S-0002"}}
    games = [_log(f"R4-00-{i:03d}a", ["a/快攻妖精", "b/快攻妖精"], ["S-0001", "S-0002"]) for i in range(40)]
    games += [_log("R4-00-900a", ["a/快攻妖精", "b/快攻妖精"], ["S-0001", "S-0002"], result="void"),     # void
              _log("R4-00-901a", ["a/快攻妖精", "b/快攻妖精"], ["S-0001", "S-0002"], result="draw"),
              _log("R4-00-902a", ["a/快攻妖精", "b/快攻妖精"], ["S-0009", "S-0002"]),                   # another receipt
              _log("R4-00-903a", ["a/快攻妖精", "b/快攻妖精"], ["S-0001", "S-0002"], steps=((1, 4, 1),)),  # a never decided
              _log("R4-00-904a", ["a/快攻妖精", "b/快攻妖精"], ["S-0001", "S-0002"], period=3),
              _log("R4-00-905a", ["a/快攻妖精", "b/快攻妖精"], ["S-0001", "S-0002"], result="timeout")]
    out = tmp_path / "P4"
    (out / "games").mkdir(parents=True)

    def write(order):
        (out / "games" / "x--y.jsonl").write_text("".join(json.dumps(games[i]) + "\n" for i in order[:30]) + "{torn\n",
                                                  encoding="utf-8")
        (out / "games" / "y--z.jsonl").write_text("".join(json.dumps(games[i]) + "\n" for i in order[30:]),
                                                  encoding="utf-8")
    write(list(range(len(games))))
    by, limits = SC.scan(out, 4, members)
    assert limits == []                                        # these made-up lines carry none
    ids = {m: [x[0] for x in xs] for m, xs in by.items()}
    assert len(ids["a/快攻妖精"]) == 41 and "R4-00-901a" in ids["a/快攻妖精"]                  # the draw counts
    assert not {"R4-00-900a", "R4-00-902a", "R4-00-903a", "R4-00-904a", "R4-00-905a"} & set(ids["a/快攻妖精"])
    assert "R4-00-903a" in ids["b/快攻妖精"] and "R4-00-902a" in ids["b/快攻妖精"] and len(ids["b/快攻妖精"]) == 43
    assert all(seat == 0 for _, seat, _, _ in by["a/快攻妖精"]) and all(s == 1 for _, s, _, _ in by["b/快攻妖精"])
    picks = SC.draw(by, members, 4, 30)
    assert len(picks["a/快攻妖精"]) == 30 and len(set(picks["a/快攻妖精"])) == 30
    got = SC.load(picks)
    assert all(got[(gid, seat)]["id"] == gid for gid, seat, _, _ in picks["a/快攻妖精"])
    shuffled = list(range(len(games)))
    random.Random(1).shuffle(shuffled)
    write(shuffled)                                            # the same games in another order: the same draw
    again = SC.draw(SC.scan(out, 4, members)[0], members, 4, 30)
    assert [x[:2] for x in again["a/快攻妖精"]] == [x[:2] for x in picks["a/快攻妖精"]]
    assert SC.draw(by, members, 4, 50)["a/快攻妖精"] == by["a/快攻妖精"]                     # fewer: all of them
    other = SC.draw(by, {**members, "a/快攻妖精": {"receipt": "S-0003"}}, 4, 30)        # another receipt: another draw
    assert [x[:2] for x in other["a/快攻妖精"]] != [x[:2] for x in picks["a/快攻妖精"]]


# two mulligans, seat 0's turn (a first decision, then its EndTurn), seat 1's turn: kinds M M F R F
MOVES = [{"type": "Mulligan"}, {"type": "Mulligan"}, {"type": "PlayCard"}, {"type": "EndTurn"}, {"type": "EndTurn"}]
KINDS = ["M", "M", "F", "R", "F"]


def _g(cpu):
    return {"id": "g", "steps": [[s, c, 7] for s, c in zip((0, 1, 0, 0, 1), cpu)], "actions": MOVES}


def _sh(cpu):
    return {"value": {"steps": [[s, c] for s, c in zip((0, 1, 0, 0, 1), cpu)], "kinds": KINDS}}


def test_the_numbers_are_the_receipts_and_over_is_compute_audits():
    """A member's replay keeps its seat's side and a calibration game the twin side (both seats); turn_budget over
    them is the receipt's arithmetic with c the calibration's game over replay."""
    m, bad = SC.member_part(_g([1, 1, 40, 18, 30]), _sh([1, 1, 5, 4, 15]), 0)
    assert bad == [] and m["row"] == (59, 10, 0, 0) and (m["F"], m["Fd"], m["R"], m["Rd"]) == (40, 5, 19, 5)
    assert m["U"] == 9 and m["T"] == 1 and m["opp"] == [0, 0] and m["twin_F"] == m["twin_R"] == [0, 0]
    c, bad = SC.cal_part(_g([1, 1, 10, 8, 20]), _sh([1, 1, 5, 4, 10]))
    assert c["row"] == (0, 0, 40, 21) and c["twin_F"] == [30, 15] and c["twin_R"] == [10, 6]
    assert (c["U_twin"], c["T_twin"]) == (9 + 10, 2) and c["F"] == c["U"] == c["T"] == 0 and c["turns"] == []
    assert SC.member_part(_g([1, 1, 40, 18, 30]), {"timeout": 0}, 0)[0] is None
    cal = [c] * 4
    res = SC.measure([m] * 3, cal, k=2, draws=200)
    f = 40 / 21
    assert res["ratio"] == round((59 / 10) / f, 3) and res["in_turn"] == round((19 / 5) / f, 3)
    assert res["turn_start_q"] == round((40 / f) / (COMPUTE_CAP * 5 + 2 * 9), 3)
    assert res["extra_turns"] == round((40 / f - COMPUTE_CAP * 5) / 9, 2)
    b = turn_budget([m] * 3 + cal, 2)
    assert res["u_twin_ratio"] == round(b["u_twin_ratio"], 3) and res["turn_start_wall_max_s"] == 0.0
    for key, x in (("interval90", "ratio"), ("interval90_in", "in_turn"), ("interval90_q", "turn_start_q")):
        assert res[key] == [res[x], res[x]]                    # every game the same: no spread
    assert res["over"] == CA.over_both(res["interval90"], res["interval90_in"], res["interval90_q"], 2)
    assert res["old_over"] and res["over"] and res["rule_point"] is None     # 3.1 x all, 2 x in turn: over both
    light, _ = SC.member_part(_g([1, 1, 40, 4, 30]), _sh([1, 1, 5, 4, 15]), 0)   # the same turn starts, the rest cheap
    lr = SC.measure([light] * 3, cal, k=2, draws=200)
    assert lr["old_over"] and lr["in_turn"] < COMPUTE_REFUSE and lr["turn_start_q"] < TURN_REFUSE
    assert not lr["over"] and lr["rule_point"] == "turn"       # the turn rule holds: not over
    k0 = SC.measure([light] * 3, cal, k=0, draws=200)
    assert k0["over"] == k0["old_over"] is True and k0["rule_point"] is None   # K = 0: the old line alone
    rng = random.Random(4)
    for _ in range(30):                                        # the draws: compute_audit.interval's, per number
        ms = [SC.member_part(_g([1, 1, rng.randint(5, 60), rng.randint(2, 30), 9]), _sh([1, 1, 5, 4, 15]), 0)[0]
              for _ in range(5)]
        r = SC.measure(ms, cal, k=2, draws=100)
        assert r["interval90"][0] <= r["interval90"][1] and r["interval90_q"][0] <= r["interval90_q"][1]
        assert r["over"] == CA.over_both(r["interval90"], r["interval90_in"], r["interval90_q"], 2)
        assert r["over"] <= r["old_over"]


def test_it_needs_the_formal_round_robin_done_and_measures_once(tmp_path, monkeypatch):
    """No game: the plan, the result, the ledger, the key, a second measure."""
    _env(monkeypatch)
    host, lines = _host(tmp_path)
    out = host / "special" / "P4"
    with pytest.raises(R.EvalError, match="还没正式跑过"):
        SC.check(host, 4, workers=2, key=secrets.token_bytes(32), players=TWO, log=lambda *_: None)
    cands, _, _ = R.candidates(host, 4, TWO)
    out.mkdir(parents=True)
    plan = R.plan_record(4, TWO, R.layout(TWO, 4), cands, "k1", "test-env")
    (out / "rr-plan.json").write_text(json.dumps({**plan, "trial": 2}), encoding="utf-8")
    with pytest.raises(R.EvalError, match="不是第 4 期正式循环赛"):
        SC.members_of(host, 4, TWO)
    (out / "rr-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(R.EvalError, match="还没打完"):
        SC.members_of(host, 4, TWO)
    (out / "rr-result.json").write_text(json.dumps({"period": 4, "trial": None}), encoding="utf-8")
    members, _, missing = SC.members_of(host, 4, TWO)
    assert sorted(members) == ["pa-alpha/兔子教", "pa-alpha/快攻妖精", "pa-alpha/跳费龙", "pb-bravo/快攻妖精"]
    assert missing == ["pb-bravo/跳费龙", "pb-bravo/兔子教"]
    d = SC.dry(host, 4, players=TWO, key=None)
    assert d["replays"] == 0 and d["calibration"] == {"games": 60, "seeds": [96600000, 96600029]}
    assert not d["formal_ready"] and any("密钥" in w for w in d["warnings"]) and not (out / "compute").exists()
    with pytest.raises(R.EvalError, match="密钥"):            # formal: the host's key required
        SC.check(host, 4, workers=2, key=None, players=TWO, log=lambda *_: None)
    TR._ledger(host, lines[:-1])                               # bravo's deck gone from the ledger: not this plan
    with pytest.raises(R.EvalError, match="对不上"):
        SC.members_of(host, 4, TWO)
    TR._ledger(host, lines)
    (out / "compute.json").write_text("{}", encoding="utf-8")
    with pytest.raises(R.EvalError, match="已经量过"):
        SC.check(host, 4, workers=2, key=secrets.token_bytes(32), players=TWO, log=lambda *_: None)
    assert not (out / "compute").exists()


# --- games --------------------------------------------------------------------------------------------------------

def test_the_check_on_a_made_up_round_robin(tmp_path, monkeypatch):
    """12 round-robin games, then two runs on 2 workers: the 10 calibration games on 96540100-96540104 played (and 2
    warm-up ones, the first two again); then 16 replays (4 a member) and the calibration games' 10 shuffled together,
    each its own task (and 2 warm-up replays)."""
    key = secrets.token_bytes(32)
    host, _ = _round_robin(tmp_path, monkeypatch, key)
    out = host / "special" / "P4"
    rr = sorted(p.read_text(encoding="utf-8") for p in (out / "games").glob("*.jsonl"))
    monkeypatch.setattr(SC, "CAL_SEEDS", {4: (96540100, 96540110)})
    from ladder import runner
    runs, real_map = [], runner.guarded_map

    def watched(fn, tasks, *a, **kw):
        runs.append([t["kind"] for t in tasks])
        return real_map(fn, tasks, *a, **kw)
    monkeypatch.setattr(runner, "guarded_map", watched)
    said = []
    body = SC.check(host, 4, workers=2, per_member=4, calibration=10, key=key, arena=tmp_path / "arena",
                    players=TWO, log=said.append, draws=1000)
    assert list((tmp_path / "arena" / "host" / "queue").glob("*.t")) == []                 # the lock let go
    assert "host" in json.loads((tmp_path / "arena" / "host" / "served.json").read_text(encoding="utf-8"))
    assert any("重放 16 局" in x and "校准局 10 局" in x and "热身 2 局" in x and "热身 2 次重放" in x for x in said)
    # 11-28 review: a calibration game replayed in the task that played it found the caches warm (c ~10% high, every
    # member low); its replay is a task of its own, in the run with the members' replays
    assert runs == [["play"] * 12, ["replay"] * 28]
    rows = {r["member"]: r for r in body["members"]}
    assert sorted(rows) == ["pa-alpha/兔子教", "pa-alpha/快攻妖精", "pa-alpha/跳费龙", "pb-bravo/快攻妖精"]
    assert body["missing"] == ["pb-bravo/跳费龙", "pb-bravo/兔子教"] and body["problem_count"] == 0
    for m, r in rows.items():
        assert r["games"] == r["drawn"] == min(4, r["available"]) and len(r["ids"]) == r["drawn"]
        assert r["available"] == (12 if m.startswith("pb") else 4)
        assert r["receipt_compute"]["ratio"] == 1.02 and r["receipt_compute"]["rule"] == "old"
        for x in ("interval90", "interval90_in", "interval90_q"):
            assert r[x][0] <= r[x][1]
    c = body["calibration"]
    assert c["games"] == c["planned"] == 10 and c["warm_up"] == c["warm_up_replays"] == 2
    assert c["seeds"] == [96540100, 96540104]
    assert 0.5 < c["game_over_replay"] < 2 and all(h is not None for h in c["halves"])
    assert body["turn_k"] == TURN_K and body["turn_refuse"] == TURN_REFUSE and body["batch"]["replays"] == 16
    heavy, plain, rnd, plan = (rows[x] for x in ("pa-alpha/快攻妖精", "pa-alpha/兔子教", "pb-bravo/快攻妖精",
                                                 "pa-alpha/跳费龙"))
    print({m: {x: r.get(x) for x in ("ratio", "interval90", "in_turn", "interval90_in", "turn_start_q",
                                     "interval90_q", "extra_turns", "over")} for m, r in rows.items()})
    assert heavy["ratio"] > 1.4 and heavy["in_turn"] > 1.4 and heavy["over"]                # 5 x the search
    assert not plain["over"] and not plain["old_over"] and 0.85 < plain["ratio"] < 1.15    # the default's own: ~1
    #   (4 games against 10, ~5% a game: ~3 sd; the bias itself is held by `runs` above: the run before this
    #   measured 0.96 here, its c ~10% high, which 4 games can't tell from noise)
    assert not rnd["over"] and rnd["ratio"] < 0.5                                          # random moves cost little
    assert plan["extra_turns"] > 0.2 and plan["turn_start_q"] < TURN_REFUSE and plan["in_turn"] < COMPUTE_REFUSE
    assert plan["old_over"] and not plan["over"] and plan["rule_point"] == "turn"         # over the old line alone
    assert body["over"] == ["pa-alpha/快攻妖精"] and "pa-alpha/跳费龙" in body["old_over"]
    cal = [json.loads(l) for l in (out / "compute" / "calibration.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(cal) == 10 and sorted(g["id"] for g in cal) == sorted(j["id"] for j in SC.cal_jobs(4, SC.cal_layout(4, 10)))
    assert all(96540100 <= g["seed"] <= 96540104 and g["deal"]["key"] == deal.key_id(key) for g in cal)
    assert all(g["strategies"] == [DEFAULT, DEFAULT] and g["provenance"] and g["limits"] for g in cal)
    md = (out / "compute.md").read_text(encoding="utf-8")
    assert "只给主持方和 Salem" in md and "pa-alpha" in md and "pb-bravo" in md
    assert "超线的：pa-alpha/快攻妖精" in md and "只按老规矩超的（按回合那条没超，不算超线）：pa-alpha/跳费龙" in md
    assert "96540100～96540104" in md
    saved = json.loads((out / "compute.json").read_text(encoding="utf-8"))
    assert saved["over"] == body["over"] and saved["members"] == json.loads(json.dumps(body["members"]))
    assert sorted(p.read_text(encoding="utf-8") for p in (out / "games").glob("*.jsonl")) == rr   # the logs as they were
    assert not (tmp_path / "players").exists() and not list(host.rglob("特殊期评测*"))         # nothing to players
    with pytest.raises(R.EvalError, match="已经量过"):
        SC.check(host, 4, workers=2, per_member=4, calibration=10, key=key, players=TWO, log=lambda *_: None)
