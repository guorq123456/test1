"""tools/first_setup.py (RUNBOOK 第一次 4-5): the official pool copied from p1b and advanced, the p1b pool untouched,
the players' folders and the public copy; run twice, nothing changes. No games are played here."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
sys.path.insert(0, str(HERE))

import first_setup as F  # noqa: E402
from ladder import pool as P  # noqa: E402
from test_pool import baseline_pool  # noqa: E402


def test_the_pool_is_copied_advanced_and_never_copied_over(tmp_path, monkeypatch):
    src = baseline_pool(tmp_path, "p1b").dir
    before = F.digest(src)
    monkeypatch.setattr(P.Pool, "period_done", lambda self: [])      # as if period 0 were played out
    r = F.pool_step(src, tmp_path / "host" / "pool")
    assert r["ok"] and r["copied"] and r["period"] == 1 and r["kind"] == "deck" and r["members"] == 7
    assert F.digest(src) == before                                    # the original is not touched
    assert P.Pool(tmp_path / "host" / "pool").period == 1
    again = F.pool_step(src, tmp_path / "host" / "pool")
    assert again["ok"] and "already there" in again["note"]
    o = baseline_pool(tmp_path, "other")                              # a period-0 pool that is not p1b's
    o.enter(o.members["m0001"].deck, "bot:greedy", "baseline")
    other = o.dir
    try:
        F.pool_step(src, other)
    except SystemExit as e:
        assert "not the p1b pool" in str(e)
    else:
        raise AssertionError("copied over another pool")


def test_players_folders_and_the_public_copy(tmp_path):
    pub = tmp_path / "public-src"
    pub.mkdir()
    (pub / "rules.md").write_text("规则", encoding="utf-8")
    r = F.players_step(tmp_path / "players", pub)
    assert r["ok"] and len(r["made"]) == 10 and r["public_copied"] == ["rules.md"]
    for py in ("fable-ultracode", "fable", "astra", "opus", "sol"):
        assert (tmp_path / "players" / py / "submit").is_dir() and (tmp_path / "players" / py / "receipts").is_dir()
    (tmp_path / "players" / "public" / "reports").mkdir()                   # the period reports stay
    (pub / "rules.md").write_text("规则 v2", encoding="utf-8")
    r = F.players_step(tmp_path / "players", pub)
    assert r["ok"] and r["made"] == [] and r["public_copied"] == ["rules.md"]
    assert (tmp_path / "players" / "public" / "rules.md").read_text(encoding="utf-8") == "规则 v2"
    assert (tmp_path / "players" / "public" / "reports").is_dir()
    assert F.players_step(tmp_path / "players", pub)["public_same"] == ["rules.md"]


def test_a_failing_step_still_writes_the_summary(tmp_path, monkeypatch):
    import json
    import check_lock
    monkeypatch.setattr(check_lock, "differs", lambda: [])
    src = baseline_pool(tmp_path, "p1b").dir
    dest = tmp_path / "out" / "host" / "pool"
    dest.mkdir(parents=True)
    (dest / "events.jsonl").write_text("{torn", encoding="utf-8")      # a copy cut short
    code = F.main(["--dry", "--p1b", str(src), "--out", str(tmp_path / "out")])
    res = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert code == 1 and not res["ok"] and not res["steps"]["pool"]["ok"]
    assert "look before going on" in res["steps"]["pool"]["error"]



def test_the_starting_puzzle_is_added_once(tmp_path):
    import json
    subs, pub = tmp_path / "host" / "subs", tmp_path / "players" / "public"
    r = F.puzzle_step(subs, pub)
    assert r["ok"] and r["added"] and r["id"] == "START" and r["list"] == "bot/T1-HAVEN-1"
    reg = json.loads((subs / "puzzles.json").read_text(encoding="utf-8"))
    assert reg["START"]["deck_code"].startswith("1.6.") and len(reg["START"]["deck"]) == 40
    md = (pub / "puzzles.md").read_text(encoding="utf-8")
    assert "START" in md and reg["START"]["deck_code"] in md and "HAVEN" not in md   # no bot name, no pilot
    again = F.puzzle_step(subs, pub)
    assert again["ok"] and again["note"] == "already there"
    reg["START"]["deck_code"] = "1.6.other"
    (subs / "puzzles.json").write_text(json.dumps(reg), encoding="utf-8")
    try:
        F.puzzle_step(subs, pub)
    except SystemExit as e:
        assert "another list" in str(e)
    else:
        raise AssertionError("a START on another list was taken")


def test_the_codenames_empty_folders_go_and_names_come(tmp_path):
    pub = tmp_path / "public-src"
    pub.mkdir()
    players = tmp_path / "players"
    for old in ("jia", "yi", "bing", "ding", "wu"):                          # as made on 11-23 17:48Z
        for sub in ("submit", "receipts"):
            (players / old / sub).mkdir(parents=True)
    (players / "wu" / "submit" / "x.txt").write_text("something", encoding="utf-8")
    r = F.players_step(players, pub)
    assert r["ok"] and r["players"] == ["fable-ultracode", "fable", "astra", "opus", "sol"]
    assert sorted(r["old_removed"]) == sorted(str(players / o) for o in ("jia", "yi", "bing", "ding"))
    assert r["old_kept"] == [str(players / "wu")] and (players / "wu" / "submit" / "x.txt").exists()
    assert all((players / n / "submit").is_dir() for n in r["players"])
