"""tools/environments.py (S25): the simulator's fingerprint per environment, the seal of the logs at a new
environment's first period, and what the close's audit reads after it. No game is played and no seed is used."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

import environments as E  # noqa: E402


def test_this_tree_is_a_known_environment():
    got = E.fingerprint()
    assert got in {e["fingerprint"] for e in E.ENVS}, got
    assert E.env_of(0)["name"] == E.env_of(1)["name"] == "base-2026-11-21"
    assert E.env_of(2)["name"] == E.env_of(9)["name"] == "patch-2026-11-26"
    for e in E.ENVS:
        if e.get("notes"):
            assert (E.REPO / e["notes"]).is_file()


def test_another_simulator_is_refused(monkeypatch):
    monkeypatch.setattr(E, "fingerprint", lambda root=E.REPO: "0000000000000000")
    with pytest.raises(SystemExit, match="没登记过的"):
        E.check(2)


def test_crlf_text_reads_as_lf(tmp_path):
    for nl in ("\n", "\r\n"):
        root = tmp_path / ("lf" if nl == "\n" else "crlf")
        (root / "svsim").mkdir(parents=True)
        (root / "svsim" / "a.py").write_bytes(f"x = 1{nl}y = 2{nl}".encode())
        (root / "svsim" / "b.md").write_text("not counted", encoding="utf-8")
    assert E.fingerprint(tmp_path / "lf") == E.fingerprint(tmp_path / "crlf")


def logs(host: Path):
    (host / "pool").mkdir(parents=True)
    (host / "pool" / "games.jsonl").write_text('{"id": 1}\n{"id": 2}\n', encoding="utf-8")
    (host / "pool" / "events.jsonl").write_text('{"ev": "game", "id": 1}\n', encoding="utf-8")
    (host / "anchors").mkdir()
    (host / "anchors" / "games-P1.jsonl").write_text('{"id": "a"}\n', encoding="utf-8")
    (host / "puzzles" / "START").mkdir(parents=True)
    (host / "puzzles" / "START" / "games.jsonl").write_text('{"id": "s"}\n', encoding="utf-8")


def inputs(host, work):
    ls = [host / "pool" / "games.jsonl", *sorted((host / "anchors").glob("games-P2*.jsonl")),
          *sorted((host / "puzzles").glob("*/games.jsonl"))]
    return E.audit_inputs(host, ls, host / "pool" / "events.jsonl", work)


def test_the_seal_is_taken_once_at_the_first_period_of_an_environment(tmp_path):
    host = tmp_path / "host"
    logs(host)
    assert E.seal(host, 1) is None                       # period 1 starts no environment
    s = E.seal(host, 2)
    assert s["env"] == "patch-2026-11-26" and sorted(s["files"]) == [
        "anchors/games-P1.jsonl", "pool/events.jsonl", "pool/games.jsonl", "puzzles/START/games.jsonl"]
    assert E.seal(host, 2) is None and E.seal(host, 3) is None
    assert len(json.loads((host / "audit" / "sealed.json").read_text(encoding="utf-8"))) == 1


def test_only_what_was_written_after_the_seal_is_replayed(tmp_path):
    host = tmp_path / "host"
    logs(host)
    E.seal(host, 2)
    got = inputs(host, tmp_path / "w")
    assert got["logs"] == [] and got["events"] is None and got["changed"] == []
    with open(host / "pool" / "games.jsonl", "a", encoding="utf-8") as f:
        f.write('{"id": 3}\n')
    with open(host / "pool" / "events.jsonl", "a", encoding="utf-8") as f:
        f.write('{"ev": "game", "id": 3}\n')
    (host / "anchors" / "games-P2.jsonl").write_text('{"id": "b"}\n', encoding="utf-8")
    got = inputs(host, tmp_path / "w")
    assert [p.name for p in got["logs"]] == ["pool__games.jsonl", "games-P2.jsonl"]
    assert got["logs"][0].read_text(encoding="utf-8") == '{"id": 3}\n'
    assert got["events"].read_text(encoding="utf-8") == '{"ev": "game", "id": 3}\n'
    assert got["sealed"] == "patch-2026-11-26" and got["changed"] == []


def test_a_sealed_log_changed_or_gone_is_named(tmp_path):
    host = tmp_path / "host"
    logs(host)
    E.seal(host, 2)
    (host / "pool" / "games.jsonl").write_text('{"id": 1}\n{"id": 9}\n{"id": 3}\n', encoding="utf-8")
    (host / "puzzles" / "START" / "games.jsonl").unlink()
    got = inputs(host, tmp_path / "w")
    assert got["changed"] == ["pool/games.jsonl", "puzzles/START/games.jsonl"]
    assert got["logs"] == []
