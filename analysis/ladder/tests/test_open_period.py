"""tools/open_period.py (RUNBOOK 每期 §1 and §3 in one go): a dry run on a period-1 pool opens the arena, writes the
report and runs the collection loop to the end of a short window; started again it never opens a second window. No
games are played here and no seed is used."""
import json
import random
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
sys.path.insert(0, str(HERE))

import open_period as O  # noqa: E402
from test_pool import baseline_pool, finish  # noqa: E402


@pytest.fixture(autouse=True)
def any_simulator(monkeypatch):
    """The tree under test may be either environment's; tests/test_environments.py checks the real fingerprints."""
    import environments
    monkeypatch.setattr(environments, "check", lambda period, root=None: environments.env_of(period))


def period_one(tmp_path):
    pool = baseline_pool(tmp_path / "host", "pool")
    rng = random.Random(5)
    for _ in range(40):
        finish(pool, pool.next_job(), rng.randrange(2))
    pool.advance(force="test")
    return pool


def test_a_dry_opening_runs_to_the_end_of_its_window(tmp_path):
    period_one(tmp_path)
    out = tmp_path / "out"
    code = O.main(["--dry", "--host", str(tmp_path / "host"), "--out", str(out), "--hours", "0.004", "--every", "1",
                   "--mask", "none", "--workers", "2"])
    s = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert code == 0 and s["ok"], s
    assert s["steps"]["state"] == {"ok": True, "period": 1, "kind": "deck", "already_open": False}
    assert s["steps"]["anchors"]["anchors"] == 7 and not s["steps"]["anchors"]["hof"]
    assert s["steps"]["arena"]["opponents"] == 14 and s["steps"]["arena"]["games"] == 60000
    report = (out / "players" / "public" / "reports" / "report-P1.md").read_text(encoding="utf-8")
    assert "起点题 START" in report and s["steps"]["arena"]["deadline"] in report
    assert "这一期收完" in (out / "collect.log").read_text(encoding="utf-8")
    assert (out / "host" / "frozen" / "P1.json").exists()
    assert not (tmp_path / "host" / "frozen").exists() or not any((tmp_path / "host" / "frozen").iterdir())
    for name in ("fable-ultracode", "fable", "astra", "opus", "sol"):
        assert (out / "players" / name / "submit").is_dir()
    # the real layout opened by hand is found open: no second snapshot, no second window
    window = json.loads((out / "arena" / "public" / "window.json").read_text(encoding="utf-8"))
    assert O.is_open(out / "arena", 1) == window
    assert O.is_open(out / "arena", 2) is None


def test_an_open_window_is_never_opened_again(tmp_path, monkeypatch):
    period_one(tmp_path)
    host, arena, players = tmp_path / "host", tmp_path / "arena", tmp_path / "players"
    for name in ("public",):
        (players / name).mkdir(parents=True)
    (players / "public" / "arena.md").write_text("old", encoding="utf-8")       # an old guide is replaced
    (players / "public" / "reports").mkdir()
    (players / "public" / "puzzles.md").write_text("kept", encoding="utf-8")    # files not from the repo: left
    calls = []
    real_py = O.py
    monkeypatch.setattr(O, "py", lambda args, log: calls.append(args[1]) or real_py(args, log))
    monkeypatch.setattr(O, "collect", lambda args, log: 0)
    argv = ["--host", str(host), "--arena", str(arena), "--players", str(players), "--out", str(tmp_path / "o"),
            "--hours", "1", "--mask", "none", "--workers", "2"]
    monkeypatch.setattr("ladder.deal.resolve", lambda key: b"k" * 32)
    monkeypatch.setattr("ladder.deal.key_id", lambda key: "test")
    assert O.main(argv) == 0
    assert calls == ["ladder.evaluator", "ladder.anchors", "ladder.arena", "ladder.arena", "ladder.report"]
    s = json.loads((tmp_path / "o" / "summary.json").read_text(encoding="utf-8"))
    assert "arena.md" in s["steps"]["public"]["updated"]
    assert (players / "public" / "arena.md").read_bytes() == (O.LADDER / "public" / "arena.md").read_bytes()
    assert "按选手轮流" in (players / "public" / "arena.md").read_text(encoding="utf-8")
    assert (players / "public" / "puzzles.md").read_text(encoding="utf-8") == "kept"
    first = (arena / "public" / "window.json").read_text(encoding="utf-8")
    calls.clear()
    assert O.main(argv) == 0
    s = json.loads((tmp_path / "o" / "summary.json").read_text(encoding="utf-8"))
    assert calls == [] and s["steps"]["state"]["already_open"] and "kept" in s["steps"]["report"]
    assert "public" not in s["steps"]                                   # mid-period: the guides are not touched
    assert (arena / "public" / "window.json").read_text(encoding="utf-8") == first


def test_a_strategy_period_needs_its_delta(tmp_path, monkeypatch):
    pool = period_one(tmp_path)
    monkeypatch.setattr("ladder.pool.period_kind", lambda p: "strategy")
    code = O.main(["--dry", "--host", str(tmp_path / "host"), "--out", str(tmp_path / "o"), "--mask", "none"])
    s = json.loads((tmp_path / "o" / "summary.json").read_text(encoding="utf-8"))
    assert code == 1 and "delta" in s["steps"]["state"]["error"]
    assert pool.period == 1


def test_a_strategy_periods_delta_is_kept_once_given(tmp_path):
    host = tmp_path / "host"
    assert O.period_delta(host, 2, 3.0) == 3.0
    assert O.period_delta(host, 2, None) == 3.0                    # the double-click gives nothing: the kept one
    assert O.period_delta(host, 2, 3) == 3.0
    try:
        O.period_delta(host, 2, 1.5)
    except SystemExit as e:
        assert "已经定成 3" in str(e)
    else:
        raise AssertionError("changed a kept delta")
    try:
        O.period_delta(host, 4, None)
    except SystemExit as e:
        assert "delta" in str(e)
    else:
        raise AssertionError("opened a strategy period without its delta")


def test_public_puzzle_results_go_into_the_next_report_once(tmp_path):
    host = tmp_path / "host"
    for pid in ("START", "P01"):
        (host / "puzzles" / pid).mkdir(parents=True)
        (host / "puzzles" / pid / "result-public.json").write_text("{}", encoding="utf-8")
    (host / "puzzles" / "P01" / "result-host.json").write_text("{}", encoding="utf-8")
    got = O.new_puzzles(host)
    assert [p.parent.name for p in got] == ["P01", "START"]
    O.mark_reported(host, got[1:])
    assert [p.parent.name for p in O.new_puzzles(host)] == ["P01"]
    O.mark_reported(host, O.new_puzzles(host))
    assert O.new_puzzles(host) == []


def test_a_window_on_another_field_is_never_opened_again(tmp_path):
    arena = tmp_path / "arena"
    (arena / "host").mkdir(parents=True)
    (arena / "public").mkdir(parents=True)
    (arena / "public" / "window.json").write_text(json.dumps({"period": 3, "field": "aaa", "deadline": "x"}),
                                                   encoding="utf-8")
    (arena / "host" / "field.json").write_text(json.dumps({"period": 3, "hash": "bbb"}), encoding="utf-8")
    try:
        O.is_open(arena, 3)
    except SystemExit as e:
        assert "不再开一次窗口" in str(e)
    else:
        raise AssertionError("would open a second window")
    assert O.is_open(arena, 4) is None


def test_is_open_for_the_wrapper(tmp_path):
    period_one(tmp_path)
    argv = ["--is-open", "--host", str(tmp_path / "host"), "--arena", str(tmp_path / "arena")]
    assert O.main(argv) == 11
    (tmp_path / "arena" / "host").mkdir(parents=True)
    (tmp_path / "arena" / "public").mkdir(parents=True)
    (tmp_path / "arena" / "public" / "window.json").write_text(json.dumps({"period": 1, "field": "h"}),
                                                                encoding="utf-8")
    (tmp_path / "arena" / "host" / "field.json").write_text(json.dumps({"period": 1, "hash": "h"}), encoding="utf-8")
    assert O.main(argv) == 10


def test_set_delta_only_records(tmp_path, monkeypatch):
    period_one(tmp_path)
    host = tmp_path / "host"
    try:
        O.main(["--set-delta", "3", "--host", str(host)])
    except SystemExit as e:
        assert "卡组期" in str(e)                                 # period 1 has no gate
    else:
        raise AssertionError("recorded a delta for a deck period")
    monkeypatch.setattr("ladder.pool.period_kind", lambda p: "strategy")
    assert O.main(["--set-delta", "3", "--host", str(host)]) == 0
    assert json.loads((host / "gates" / "delta-P1.json").read_text(encoding="utf-8"))["delta"] == 3.0
    assert not (tmp_path / "arena").exists()                      # nothing opened
