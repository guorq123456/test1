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
    for py in ("jia", "yi", "bing", "ding", "wu"):
        assert (tmp_path / "players" / py / "submit").is_dir() and (tmp_path / "players" / py / "receipts").is_dir()
    (tmp_path / "players" / "public" / "reports").mkdir()                   # the period reports stay
    (pub / "rules.md").write_text("规则 v2", encoding="utf-8")
    r = F.players_step(tmp_path / "players", pub)
    assert r["ok"] and r["made"] == [] and r["public_copied"] == ["rules.md"]
    assert (tmp_path / "players" / "public" / "rules.md").read_text(encoding="utf-8") == "规则 v2"
    assert (tmp_path / "players" / "public" / "reports").is_dir()
    assert F.players_step(tmp_path / "players", pub)["public_same"] == ["rules.md"]
