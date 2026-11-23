"""Collecting submissions during the window (ladder/collect.py, A50, PLAN 8b). The receive runs use test_submit's
smoke bank 99001420-99001449 and its pool's ladder range 99001460-99001469 (not played) (SEEDS.md)."""
import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE))
from ladder import arena, collect, submit  # noqa: E402
from ladder.pool import Pool  # noqa: E402
from test_submit import CODES, make_sub  # noqa: E402

TEST_RECEIVE = ["--smoke-games", "2", "--smoke-seeds", "99001420", "99001450", "--rng-seed", "7"]


def _period(tmp_path, n: int, seconds: float):
    """A pool at period n and its arena, whose window closes `seconds` from now (negative: closed)."""
    pool = Pool.create(tmp_path / "pool", seeds=(99001460, 99001470), rng_seed=1)
    for _ in range(n):
        pool.advance()
    a = tmp_path / "arena"
    arena.snapshot(tmp_path / "pool", a, cr="current")
    w = arena.open_window(a, hours=seconds / 3600, games=10, workers=2)
    return pool, a, datetime.fromisoformat(w["deadline"]).timestamp()


def _log(subs):
    return [json.loads(l) for l in (subs / "collect.jsonl").read_text(encoding="utf-8").splitlines()]


def test_collect_takes_what_is_there_by_the_deadline_once(tmp_path):
    # the real path: each receive in its own process; the deadline taken by the timer while a receive runs
    pool, a, deadline = _period(tmp_path, 1, 3)
    players, subs = tmp_path / "players", tmp_path / "subs"
    make_sub(players / "jia" / "submit" / "梦魇1", "新卡组", deck=CODES[4], member="四号")
    bad = make_sub(players / "jia" / "submit" / "坏的", "新卡组", deck=CODES[6], member="六号")
    (bad / "notes.md").unlink()                                      # a file missing: refused on format

    def late():                                                       # 乙 hands in after the deadline
        time.sleep(max(0.0, deadline - time.time()) + 0.7)
        make_sub(players / "yi" / "submit" / "晚了", "新卡组", deck=CODES[1], member="一号")
    t = threading.Thread(target=late)
    t.start()
    lines = []
    c = collect.Collector(players, tmp_path / "pool", subs, a, workers=2, settle=0, receive_args=TEST_RECEIVE,
                          out=lines.append)
    out = c.run(every=0.2)
    t.join()
    assert out == {"received": 2, "gated": 0, "gate_errors": 0, "late": ["晚了"]}, lines
    assert lines[-1].startswith("这一期收完") and lines[-1].endswith("可以开天梯了")
    recs = [l for l in submit.ledger(subs) if l.get("ev") == "receipt"]
    assert sorted((r["player"], Path(r["dir"]).name, r["verdict"]) for r in recs) == [
        ("甲", "坏的", "拒收"), ("甲", "梦魇1", "收下")]
    assert all(r["collect_stamp"] for r in recs)
    admitted = [l for l in submit.ledger(subs) if l.get("ev") == "admit"]
    assert len(admitted) == 1 and Pool(tmp_path / "pool").members[admitted[0]["mid"]].owner == "甲"
    box = players / "jia" / "receipts"
    assert sorted(p.name for p in box.iterdir()) == ["坏的.md", "梦魇1.md", "状态.md"]
    assert not (players / "yi" / "receipts").exists()
    log = _log(subs)
    dl = [l for l in log if l["ev"] == "deadline"]
    assert len(dl) == 1 and sorted(Path(d).name for _, d, _ in dl[0]["dirs"]) == ["坏的", "梦魇1"]
    # again (a restart): the deadline listing is read back; nothing is taken twice, the late one still isn't
    again = collect.Collector(players, tmp_path / "pool", subs, a, workers=2, settle=0, out=lines.append)
    assert again.final is not None
    assert again.run(every=0.2) == {"received": 0, "gated": 0, "gate_errors": 0, "late": ["晚了"]}


def test_turns_settle_and_links(tmp_path):
    pool, a, _ = _period(tmp_path, 1, 3600)
    players, subs = tmp_path / "players", tmp_path / "subs"
    for who, name in (("jia", "a"), ("jia", "b"), ("yi", "a")):
        d = players / who / "submit" / name
        d.mkdir(parents=True)
        (d / "f").write_text(name, encoding="utf-8")
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "f").write_text("x", encoding="utf-8")
    link = players / "yi" / "submit" / "link"
    link.symlink_to(outside, target_is_directory=True)               # a link out of the submit folder: never taken
    taken = []

    def fake(player, d, st):
        taken.append((player, Path(d).name))
        return {"id": f"S-{len(taken):04d}", "verdict": "拒收", "kind": "deck"}
    c = collect.Collector(players, tmp_path / "pool", subs, a, workers=2, settle=60, receive=fake, out=lambda s: None)
    assert c.next_item() is None                                      # nothing has settled for 60 s
    c.settle = 0
    while (item := c.next_item()) is not None:
        c.take(*item)
    assert taken == [("甲", "a"), ("乙", "a"), ("甲", "b")]          # in turn, not 甲's three first
    (players / "jia" / "submit" / "a" / "f").write_text("changed", encoding="utf-8")
    assert c.next_item()[:2] == ("甲", str((players / "jia" / "submit" / "a").resolve()))   # changed: a new one
    s1 = collect.stamp(players / "yi" / "submit" / "a")
    (players / "yi" / "submit" / "a" / "g").write_text("1", encoding="utf-8")
    assert collect.stamp(players / "yi" / "submit" / "a") != s1


def test_failures_retry_give_up_and_stop(tmp_path):
    pool, a, _ = _period(tmp_path, 1, 3600)
    players, subs = tmp_path / "players", tmp_path / "subs"
    for who, name in (("jia", "a"), ("jia", "b"), ("yi", "c")):
        d = players / who / "submit" / name
        d.mkdir(parents=True)
        (d / "f").write_text(name, encoding="utf-8")

    def broken(player, d, st):
        raise RuntimeError("the host's side")
    c = collect.Collector(players, tmp_path / "pool", subs, a, workers=2, settle=0, receive=broken, out=lambda s: None)
    c.take(*c.next_item())
    c.take(*c.next_item())
    with pytest.raises(SystemExit, match="连着 3 份"):                 # three in a row: the loop stops
        c.take(*c.next_item())
    assert not (players / "jia" / "receipts").exists()               # nothing given up yet: tried once each
    again = collect.Collector(players, tmp_path / "pool", subs, a, workers=2, settle=0, receive=broken,
                              out=lambda s: None)
    item = again.next_item()
    again.take(*item)                                                 # the second failure on it: given up
    box = players / ("jia" if item[0] == "甲" else "yi") / "receipts"
    assert [p.name for p in box.iterdir()] == [f"{Path(item[1]).name}-没收成.md"]
    assert again.next_item() != item                                  # not tried a third time
    assert [l for l in _log(subs) if l.get("gave_up")][0]["dir"] == item[1]


def test_changed_after_the_deadline_is_not_taken(tmp_path):
    pool, a, _ = _period(tmp_path, 1, -1)
    players, subs = tmp_path / "players", tmp_path / "subs"
    d = players / "jia" / "submit" / "x"
    d.mkdir(parents=True)
    (d / "f").write_text("1", encoding="utf-8")
    taken = []
    c = collect.Collector(players, tmp_path / "pool", subs, a, workers=2, settle=0, out=lambda s: None,
                          receive=lambda *k: taken.append(k) or {"id": "S-0001", "verdict": "拒收", "kind": "deck"})
    c.final = collect.listing(players)                                # what was there at the deadline
    (d / "f").write_text("2", encoding="utf-8")                       # ... and changed afterwards
    assert c.run(every=0.1)["late"] == ["x"] and taken == []
    with pytest.raises(SystemExit, match="after-deadline"):           # nobody was looking at the deadline
        collect.Collector(tmp_path / "p2", tmp_path / "pool", tmp_path / "s2", a, workers=2, settle=0,
                          out=lambda s: None).run(every=0.1)


def test_after_the_deadline_gates_and_admits_what_was_left(tmp_path):
    pool, a, _ = _period(tmp_path, 2, -1)                             # period 2: a strategy period
    subs = tmp_path / "subs"
    r = lambda i, kind, verdict, period=2: {"ev": "receipt", "id": f"S-{i:04d}", "player": "甲", "period": period,
                                            "kind": kind, "verdict": verdict, "dir": f"/x/{i}", "time": "t",
                                            "version": "v", "reasons": [], "warnings": [], "checks": []}
    for line in (r(1, "update", "收下", period=1), r(2, "update", "收下"), r(3, "update", "拒收"),
                 r(4, "update", "收下"), r(5, "update", "收下"), {"ev": "gated", "receipt": "S-0004"}):
        submit._append(subs, line)
    calls = []

    def gate(rid):
        calls.append(rid)
        if rid == "S-0005":
            raise SystemExit("S-0005 不在池子里了")
        submit._append(subs, {"ev": "gated", "receipt": rid, "verdict": "passed"})
        return {"verdict": "passed"}
    frozen = tmp_path / "f.json"
    frozen.write_text("{}", encoding="utf-8")
    c = collect.Collector(tmp_path / "players", tmp_path / "pool", subs, a, workers=2, settle=0, frozen=frozen,
                          delta=3, gates_out=tmp_path / "gates", gate=gate, out=lambda s: None, after_deadline=True)
    assert c.run(every=0.1) == {"received": 0, "gated": 1, "gate_errors": 1, "late": []} and calls == ["S-0002",
                                                                                                       "S-0005"]
    assert [l["receipt"] for l in _log(subs) if l["ev"] == "gate-failed"] == ["S-0005"]
    assert c.pending_gates() == []                                   # a failed gate is reported, not retried
    with pytest.raises(SystemExit, match="策略期要给"):
        collect.Collector(tmp_path / "players", tmp_path / "pool", subs, a, workers=2, delta=3,
                          gates_out=tmp_path / "gates")


def test_an_accepted_deck_cut_off_before_its_admit_is_admitted(tmp_path):
    pool, a, _ = _period(tmp_path, 1, -1)
    subs = tmp_path / "subs"
    ids, _ = submit.check_deck(CODES[3])
    submit._append(subs, {"ev": "receipt", "id": "S-0001", "player": "甲", "period": 1, "kind": "deck",
                          "verdict": "收下", "dir": "/x/1", "member": "三号", "spec": "bot:mcts:8", "time": "t",
                          "version": "v", "reasons": [], "warnings": [], "checks": []})
    (subs / "S-0001").mkdir()
    (subs / "S-0001" / "submission.json").write_text(json.dumps({"deck": CODES[3]}), encoding="utf-8")
    c = collect.Collector(tmp_path / "players", tmp_path / "pool", subs, a, workers=2, settle=0, out=lambda s: None,
                          after_deadline=True)
    assert c.pending_admits() == ["S-0001"]
    c.run(every=0.1)
    adm = [l for l in submit.ledger(subs) if l.get("ev") == "admit"]
    assert [l["receipt"] for l in adm] == ["S-0001"] and Pool(tmp_path / "pool").members[adm[0]["mid"]].deck == ids
    assert c.pending_admits() == []
