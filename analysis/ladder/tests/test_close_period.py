"""tools/close_period.py (RUNBOOK 每期 §4-§6 in one go). The commands it runs are stood in for here (`run` is replaced:
the ladder's games are made-up results settled in this process, the audits and evaluations write their files), so
what is tested is the order, what is kept on a second run, what holds the advance and what stops it before anything
runs. No game is played and no seed is used; a real run on a small pool is the rehearsal recorded in LD-64."""
import json
import random
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))

import close_period as C  # noqa: E402
from ladder import arena, collect  # noqa: E402
from ladder import anchors as A  # noqa: E402
from ladder.pool import Pool, period_kind, takes_updates  # noqa: E402
from test_pool import BASE_DECKS, finish  # noqa: E402

SEEDS = (99001700, 99011700)       # made-up results only: these seeds only count starts, no game is played


@pytest.fixture(autouse=True)
def any_simulator(monkeypatch):
    """The tree under test may be either environment's; tests/test_environments.py checks the real fingerprints."""
    import environments
    monkeypatch.setattr(environments, "check", lambda period, root=None: environments.env_of(period))


def setup(tmp_path, seconds=-60.0, listing=True, puzzle=True, period=1, gates=True):
    """A host whose pool is in `period` (1: a deck period; 4 on: merged, which with `gates` gets its delta and frozen
    pool as open_period leaves them)."""
    host, ar, players = tmp_path / "host", tmp_path / "arena", tmp_path / "players"
    pool = Pool.create(host / "pool", SEEDS, rng_seed=3)
    for i, d in enumerate(BASE_DECKS):
        pool.enter(d, "bot:greedy", "baseline", rng=random.Random(i))
    while pool.period < period:
        pool.advance(force="test")
    if gates and takes_updates(period):
        (host / "gates").mkdir(parents=True)
        (host / "gates" / f"delta-P{period}.json").write_text(json.dumps({"period": period, "delta": 5.0}),
                                                              encoding="utf-8")
        (host / "frozen").mkdir(parents=True)
        (host / "frozen" / f"P{period}.json").write_text("{}", encoding="utf-8")
    arena.snapshot(host / "pool", ar, cr="current")
    w = arena.open_window(ar, hours=seconds / 3600, games=10, workers=2)
    (players / "public").mkdir(parents=True)
    (host / "subs" / "code").mkdir(parents=True)
    if listing:
        collect._note(host / "subs", {"ev": "deadline", "period": period, "field": w["field"],
                                      "deadline": w["deadline"], "dirs": []})
    if puzzle:
        (host / "subs" / "puzzles.json").write_text(json.dumps({"START": {"deck": BASE_DECKS[5], "title": "t"}}),
                                                    encoding="utf-8")
    return host, ar, players


class Fake:
    """Stands in for the commands: records them, does what each leaves behind."""

    def __init__(self, host, failed=0, over=0, deliver_fails=False):
        """failed: how many games don't replay (g0, g1, ...), or which; over: how many members are over (m0, ...)."""
        self.failed = [f"g{i}" for i in range(failed)] if isinstance(failed, int) else list(failed)
        self.host, self.calls, self.over = host, [], over
        self.deliver_fails = deliver_fails

    def __call__(self, args, log, extra_env=None, check=True):
        args = [str(x) for x in args]
        what = " ".join(args[1:3])
        self.calls.append(what)
        out = "{}"
        if what == "ladder.pool ladder":
            assert extra_env == {"LADDER_EXTRA_PATH": str(self.host / "subs" / "code")}
            pool, rng, n = Pool(args[3]), random.Random(1), 0
            while pool.period_done():
                finish(pool, pool.next_job(), rng.randrange(2))
                n += 1
            out = json.dumps({"played": n, "short": 0, "isolated": [], "stuck": None})
        elif what == "ladder.anchors induct":
            Path(args[args.index("--hof") + 1]).write_text("[]", encoding="utf-8")
            out = "[]"
        elif what == "ladder.anchors table":
            hof = args[args.index("--hof") + 1]
            Path(args[args.index("--out") + 1]).write_text(json.dumps(A.table(hof)), encoding="utf-8")
        elif what == "ladder.anchors run":
            out_dir = Path(args[args.index("--out") + 1])
            (out_dir / "plan-P1.json").write_text(json.dumps({"period": 1, "jobs": 49, "first_seed": 1, "done": "b"}),
                                                  encoding="utf-8")
            out = json.dumps({"period": 1, "jobs": 49, "played": 49, "voids": {}})
        elif what == "ladder.anchors report":
            out = "[]"
        elif what == "ladder.puzzles run":
            o = Path(args[args.index("--out") + 1])
            (o / "result-host.json").write_text(json.dumps({"seeds": [int(x) for x in args[args.index("--seeds") + 1:
                                                                                         args.index("--seeds") + 3]],
                                                            "entries": []}), encoding="utf-8")
            (o / "result-public.json").write_text("{}", encoding="utf-8")
        elif what.startswith("ladder.audit"):
            self.audit_args = args
            o = Path(args[args.index("--out") + 1])
            o.write_text(json.dumps({"checked": 5, "skipped": 0, "failed": [{"id": g} for g in self.failed],
                                     "unlogged": [], "unreadable": [], "voids": {}, "ok": not self.failed}),
                         encoding="utf-8")
            return (1 if self.failed else 0), ""
        elif what.startswith("ladder.compute_audit"):
            o = Path(args[args.index("--out") + 1])
            o.write_text(json.dumps({"members": [{"member": f"m{i}", "version": 1, "over": True}
                                                 for i in range(self.over)],
                                     "calibration": {"games": 20}}), encoding="utf-8")
            return (1 if self.over else 0), ""
        elif what == "ladder.leaderboard " + args[3] or what.startswith("ladder.leaderboard"):
            Path(args[args.index("--out") + 1]).write_text("{}", encoding="utf-8")
        elif what == "ladder.submit deliver" and self.deliver_fails:
            raise RuntimeError("deliver exit 1")
        elif what == "ladder.pool advance":
            pool = Pool(args[3])
            out = json.dumps({"period": pool.advance(), "kind": period_kind(pool.period)})
        return 0, out


def argv(host, ar, players, out, *more):
    return ["--host", str(host), "--arena", str(ar), "--players", str(players), "--out", str(out), "--mask", "none",
            "--workers", "2", "--e-workers", "2", *more]


@pytest.fixture
def keyed(monkeypatch):
    monkeypatch.setattr("ladder.deal.resolve", lambda key: b"k" * 32)
    monkeypatch.setattr("ladder.deal.key_id", lambda key: "test")


def summary(out):
    return json.loads((out / "summary.json").read_text(encoding="utf-8"))


def test_a_closed_period_runs_every_step_once_and_advances(tmp_path, monkeypatch, keyed):
    host, ar, players = setup(tmp_path)
    fake = Fake(host)
    monkeypatch.setattr(C, "run", fake)
    assert C.main(argv(host, ar, players, tmp_path / "o")) == 0, summary(tmp_path / "o")
    assert fake.calls == ["ladder.pool ladder", "ladder.anchors induct", "ladder.anchors table", "ladder.anchors run",
                          "ladder.anchors report", "ladder.puzzles run", f"ladder.audit {host / 'pool' / 'games.jsonl'}",
                          f"ladder.compute_audit {host / 'pool'}", "ladder.arena formal",
                          f"ladder.leaderboard {host / 'pool'}", f"ladder.leaderboard {host / 'pool'}",
                          "ladder.pool advance", "ladder.submit deliver"]
    s = summary(tmp_path / "o")
    assert s["ok"] and s["held"] == [] and Pool(host / "pool").period == 2
    assert (players / "public" / "board-P1.json").exists()
    plan = json.loads((host / "puzzles" / "START" / "plan.json").read_text(encoding="utf-8"))
    assert plan["seeds"] == [91900000, 91901200] and plan["ref"] == {"参照": C.start_ref()}
    # again: the period was closed; nothing runs
    fake.calls.clear()
    assert C.main(argv(host, ar, players, tmp_path / "o2")) == 0
    assert fake.calls == [] and summary(tmp_path / "o2")["steps"]["state"]["already_closed"]


def test_a_held_period_keeps_what_is_done_and_advances_only_when_told(tmp_path, monkeypatch, keyed):
    host, ar, players = setup(tmp_path)
    fake = Fake(host, failed=2, over=1)
    monkeypatch.setattr(C, "run", fake)
    assert C.main(argv(host, ar, players, tmp_path / "o")) == 2
    s = summary(tmp_path / "o")
    assert len(s["held"]) == 2 and "skipped" in s["steps"]["formal"] and not s["steps"]["advance"]["ok"]
    assert "ladder.arena formal" not in fake.calls and Pool(host / "pool").period == 1
    assert not (players / "public" / "board-P1.json").exists()
    assert "g0、g1" in s["held"][0] and "m0" in s["held"][1]          # which games and members, for Salem
    with pytest.raises(SystemExit):                                  # the decision names the summary Salem saw
        C.main(argv(host, ar, players, tmp_path / "ox", "--advance-anyway", "Salem 11-24"))
    # Salem decided: advance all the same. The ladder, the anchors and the puzzle are kept (nobody was inducted, so
    # the induction is asked again: the same pool gives the same nobody)
    fake.calls.clear()
    assert C.main(argv(host, ar, players, tmp_path / "o2", "--advance-anyway", "Salem 11-24",
                       "--held", s["held_digest"])) == 0
    assert "ladder.pool ladder" not in fake.calls
    assert "ladder.anchors run" not in fake.calls and "ladder.puzzles run" not in fake.calls
    assert fake.calls[-2:] == ["ladder.pool advance", "ladder.submit deliver"]
    assert "ladder.arena formal" in fake.calls                     # Salem's decision covers the formal games too
    assert f"ladder.compute_audit {host / 'pool'}" not in fake.calls   # measured once: kept
    assert summary(tmp_path / "o2")["steps"]["advance"]["anyway"] == "Salem 11-24"
    assert Pool(host / "pool").period == 2


def test_advance_anyway_covers_only_what_was_held_when_asked(tmp_path, monkeypatch, keyed):
    host, ar, players = setup(tmp_path)
    monkeypatch.setattr(C, "run", Fake(host, failed=["a"]))
    assert C.main(argv(host, ar, players, tmp_path / "o")) == 2
    shown = summary(tmp_path / "o")["held_digest"]
    for i, failed in enumerate((["a", "b"], ["a", "b"], ["c"])):  # new since Salem was asked; again; same count
        fake = Fake(host, failed=failed)
        monkeypatch.setattr(C, "run", fake)
        assert C.main(argv(host, ar, players, tmp_path / f"o{i + 2}", "--advance-anyway", "Salem",
                           "--held", shown)) == 2
        s = summary(tmp_path / f"o{i + 2}")
        assert s["steps"]["advance"]["anyway_refused"] and "ladder.pool advance" not in fake.calls
        assert "ladder.arena formal" not in fake.calls              # no formal games past what Salem saw (review 3)
        assert s["held_digest"] != shown and Pool(host / "pool").period == 1
    fake = Fake(host, failed=["a"])
    monkeypatch.setattr(C, "run", fake)
    assert C.main(argv(host, ar, players, tmp_path / "o9", "--advance-anyway", "Salem", "--held", "nope")) == 2
    assert C.main(argv(host, ar, players, tmp_path / "o10", "--advance-anyway", "Salem", "--held", shown)) == 0
    assert "ladder.arena formal" in fake.calls and Pool(host / "pool").period == 2


def test_what_an_earlier_audit_listed_holds_no_later_period(tmp_path, monkeypatch, keyed):
    host, ar, players = setup(tmp_path)
    (host / "audit").mkdir(parents=True)
    (host / "audit" / "P0.json").write_text(json.dumps({"failed": [{"id": "g0"}, {"id": "g1"}], "unlogged": [],
                                                        "unreadable": []}), encoding="utf-8")
    monkeypatch.setattr(C, "run", Fake(host, failed=2))           # the same games, listed (and decided) in period 0
    assert C.main(argv(host, ar, players, tmp_path / "o")) == 0
    s = summary(tmp_path / "o")
    assert s["held"] == [] and s["steps"]["audit"]["listed_earlier"]["failed"] == 2
    assert Pool(host / "pool").period == 2


def test_a_publish_cut_off_after_the_advance_is_done_by_the_next_run(tmp_path, monkeypatch, keyed):
    host, ar, players = setup(tmp_path)
    monkeypatch.setattr(C, "run", Fake(host, deliver_fails=True))
    assert C.main(argv(host, ar, players, tmp_path / "o")) == 1
    assert Pool(host / "pool").period == 2 and "deliver" in summary(tmp_path / "o")["steps"]["publish"]["error"]
    fake = Fake(host)
    monkeypatch.setattr(C, "run", fake)
    assert C.main(argv(host, ar, players, tmp_path / "oc", "--check")) == 0     # the check runs nothing (review 3)
    assert fake.calls == [] and summary(tmp_path / "oc")["steps"]["publish"]["pending"]
    assert C.main(argv(host, ar, players, tmp_path / "o2")) == 0
    assert fake.calls == ["ladder.submit deliver"] and (players / "public" / "board-P1.json").exists()


def test_the_check_reads_the_collection_with_the_e_cores_on_windows(tmp_path, monkeypatch, keyed):
    import types
    host, ar, players = setup(tmp_path)
    monkeypatch.setattr("ladder.runner.os", types.SimpleNamespace(name="nt"))   # Collector refuses no mask there
    more = ["--host", str(host), "--arena", str(ar), "--players", str(players), "--out", str(tmp_path / "o"), "--check"]
    assert C.main(more) == 0, summary(tmp_path / "o")


def test_anchor_voids_count_the_last_line_of_each_game(tmp_path):
    d = tmp_path
    (d / "games-P1.jsonl").write_text("\n".join(json.dumps(g) for g in [
        {"id": "a", "result": "void", "error": "worker died (exit code 1)"},
        {"id": "b", "result": "void", "error": "the simulator changed\nmore"},
        {"id": "c", "result": "normal"}]) + "\n", encoding="utf-8")
    (d / "games-P1-redo1.jsonl").write_text(json.dumps({"id": "a", "result": "normal"}) + "\n", encoding="utf-8")
    assert C.anchor_voids(d, 1) == {"the simulator changed": 1}


def test_nothing_runs_before_the_deadline(tmp_path, monkeypatch, keyed):
    host, ar, players = setup(tmp_path, seconds=600)
    fake = Fake(host)
    monkeypatch.setattr(C, "run", fake)
    assert C.main(argv(host, ar, players, tmp_path / "o")) == 1
    assert fake.calls == [] and "截止" in summary(tmp_path / "o")["steps"]["state"]["error"]
    assert C.main(argv(host, ar, players, tmp_path / "oc", "--check")) == 3      # the PC's wrapper doesn't pull


def test_nothing_runs_before_the_collection_is_done(tmp_path, monkeypatch, keyed):
    host, ar, players = setup(tmp_path, listing=False)
    fake = Fake(host)
    monkeypatch.setattr(C, "run", fake)
    assert C.main(argv(host, ar, players, tmp_path / "o")) == 1
    assert fake.calls == [] and "截止那一刻没在跑" in summary(tmp_path / "o")["steps"]["collected"]["error"]
    assert C.main(argv(host, ar, players, tmp_path / "oc", "--check")) == 3
    # the listing names a directory nobody took
    w = json.loads((ar / "public" / "window.json").read_text(encoding="utf-8"))
    d = players / "fable" / "submit" / "x"
    d.mkdir(parents=True)
    collect._note(host / "subs", {"ev": "deadline", "period": 1, "field": w["field"], "deadline": w["deadline"],
                                  "dirs": [["fable", str(d.resolve()), collect.stamp(d)]]})
    assert C.main(argv(host, ar, players, tmp_path / "o2")) == 1
    assert fake.calls == [] and "还没收" in summary(tmp_path / "o2")["steps"]["collected"]["error"]
    assert C.main(argv(host, ar, players, tmp_path / "o2c", "--check")) == 3
    # a collection loop still running
    collect._note(host / "subs", {"ev": "dir", "player": "fable", "dir": str(d.resolve()), "stamp": collect.stamp(d),
                                  "late": "test"})
    held = collect._only_one(host / "subs")
    try:
        assert C.main(argv(host, ar, players, tmp_path / "o3")) == 1
        assert "已经在别的窗口" in summary(tmp_path / "o3")["steps"]["collected"]["error"]
    finally:
        held.close()
    assert C.main(argv(host, ar, players, tmp_path / "o4", "--check")) == 0 and fake.calls == []
    assert summary(tmp_path / "o4")["report"]["collect"]["late"] == ["x"]
    # put in after the deadline: only in the listing now (the loop printed it, collect.jsonl doesn't have it)
    (players / "sol" / "submit" / "y").mkdir(parents=True)
    assert C.main(argv(host, ar, players, tmp_path / "o5", "--check")) == 0
    assert summary(tmp_path / "o5")["steps"]["collected"]["late_new"] == ["sol:y"]


def test_a_check_that_fails_for_another_reason_says_1(tmp_path, monkeypatch, keyed):
    host, ar, players = setup(tmp_path)
    import check_lock
    monkeypatch.setattr(check_lock, "differs", lambda: ["ladder/rules.py"])
    assert C.main(argv(host, ar, players, tmp_path / "o", "--check")) == 1     # the wrapper pulls then


def test_the_next_puzzle_takes_the_seeds_after_the_last(tmp_path):
    host = tmp_path / "host"
    assert C.next_puzzle_seed(host) == 91900000
    (host / "puzzles" / "START").mkdir(parents=True)
    (host / "puzzles" / "START" / "plan.json").write_text(json.dumps({"seeds": [91900000, 91901200]}))
    (host / "puzzles" / "P01").mkdir(parents=True)
    (host / "puzzles" / "P01" / "result-host.json").write_text(json.dumps({"seeds": [91901200, 91902400]}))
    assert C.next_puzzle_seed(host) == 91902400


def test_the_reference_is_the_one_the_runbook_names():
    runbook = (HERE.parent / "RUNBOOK.md").read_text(encoding="utf-8")
    assert f"--ref 参照={C.start_ref()} " in runbook


def test_last_json_reads_what_a_command_printed_last():
    assert C.last_json('{"a": 1}') == {"a": 1}
    assert C.last_json('progress\n{"a": 1,\n "b": [2]\n}\n') == {"a": 1, "b": [2]}
    assert C.last_json("nothing") is None


def test_after_a_seal_only_what_was_written_since_is_replayed(tmp_path, monkeypatch, keyed):
    import environments as E
    host, ar, players = setup(tmp_path)
    games, events = host / "pool" / "games.jsonl", host / "pool" / "events.jsonl"
    games.write_text('{"id": "old"}\n', encoding="utf-8")
    monkeypatch.setattr(E, "env_of", lambda period: {"from": 1, "name": "new", "fingerprint": "x"})
    assert E.seal(host, 1)["files"]["pool/games.jsonl"]["bytes"] == len('{"id": "old"}\n')
    sealed_events = events.stat().st_size
    with open(games, "a", encoding="utf-8") as f:                # a game logged since the seal
        f.write('{"id": "new"}\n')
    fake = Fake(host)
    monkeypatch.setattr(C, "run", fake)
    assert C.main(argv(host, ar, players, tmp_path / "o")) == 0, summary(tmp_path / "o")
    logs = [Path(x) for x in fake.audit_args[2:fake.audit_args.index("--events")]]
    assert [x.name for x in logs] == ["pool__games.jsonl"] and logs[0].parent.name == "since-seal-P1"
    assert logs[0].read_text(encoding="utf-8") == '{"id": "new"}\n'
    ev = Path(fake.audit_args[fake.audit_args.index("--events") + 1])
    got = ev.read_bytes()                                          # the events since (the advance adds more later)
    assert got and got == events.read_bytes()[sealed_events:sealed_events + len(got)]
    assert summary(tmp_path / "o")["steps"]["audit"]["since_seal"] == "new"


def test_a_sealed_log_changed_holds_the_period(tmp_path, monkeypatch, keyed):
    import environments as E
    host, ar, players = setup(tmp_path)
    games = host / "pool" / "games.jsonl"
    games.write_text('{"id": "old"}\n', encoding="utf-8")
    monkeypatch.setattr(E, "env_of", lambda period: {"from": 1, "name": "new", "fingerprint": "x"})
    E.seal(host, 1)
    games.write_text('{"id": "odd"}\n', encoding="utf-8")          # same length, other bytes
    fake = Fake(host)
    monkeypatch.setattr(C, "run", fake)
    assert C.main(argv(host, ar, players, tmp_path / "o")) == 2
    s = summary(tmp_path / "o")
    assert any("封存" in h and "pool/games.jsonl" in h for h in s["held"])
    assert "ladder.arena formal" not in fake.calls and Pool(host / "pool").period == 1


def test_a_merged_period_is_collected_with_its_delta_and_frozen_pool(tmp_path, monkeypatch, keyed):
    # S35/S36: from period 4 the close reads the collection as a period that takes updates (delta, frozen pool), and
    # both a deck still to admit and an update still to gate hold it
    host, ar, players = setup(tmp_path, period=4)
    fake = Fake(host)
    monkeypatch.setattr(C, "run", fake)
    assert C.main(argv(host, ar, players, tmp_path / "o", "--check")) == 0, summary(tmp_path / "o")
    assert summary(tmp_path / "o")["steps"]["state"]["kind"] == "merged" and fake.calls == []
    from ladder import submit
    for i, kind in ((1, "deck"), (2, "update")):
        submit._append(host / "subs", {"ev": "receipt", "id": f"S-{i:04d}", "player": "fable", "period": 4,
                                       "kind": kind, "verdict": "收下"})
    assert C.main(argv(host, ar, players, tmp_path / "o2", "--check")) == 3
    err = summary(tmp_path / "o2")["steps"]["collected"]["error"]
    assert "收下了还没入池 ['S-0001']" in err and "收下了还没检验 ['S-0002']" in err


def test_a_merged_period_without_its_delta_stops_the_close(tmp_path, monkeypatch, keyed):
    host, ar, players = setup(tmp_path / "a", period=4, gates=False)
    monkeypatch.setattr(C, "run", Fake(host))
    assert C.main(argv(host, ar, players, tmp_path / "o", "--check")) == 1
    assert "要给 --frozen" in summary(tmp_path / "o")["steps"]["collected"]["error"]
