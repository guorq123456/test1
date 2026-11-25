"""tools/special_eval.py (S27, S28): the special period's members against their class's baseline, on the pool frozen
after the period. Tiny settings; seeds 93409050-93409089 (host probe bank, SEEDS.md)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "tools"))
import special_eval as E  # noqa: E402
from ladder.pool import Pool  # noqa: E402
from ladder.submit import check_deck  # noqa: E402

ROOT = HERE.parents[2]
CODES = [l.strip().split("|")[1] for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(
    encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def _host(tmp_path):
    host = tmp_path / "host"
    pool = Pool.create(host / "pool", seeds=(99001460, 99001470), rng_seed=1)
    for code in CODES:                                          # the seven baseline members (period 0)
        pool.enter(check_deck(code)[0], E.DEFAULT, "baseline")
    pool.advance(force="test: period 1")
    ids, _ = check_deck(CODES[1])
    mid = pool.enter(ids, "bot:greedy+plan", "astra")
    subs = host / "subs"
    subs.mkdir(parents=True)
    lines = [{"ev": "receipt", "id": "S-0001", "player": "astra", "period": 1, "kind": "deck", "verdict": "收下",
              "member": "CR 皇家", "team": "Crazy Raccoon"},
             {"ev": "receipt", "id": "S-0002", "player": "sol", "period": 1, "kind": "deck", "verdict": "拒收"},
             {"ev": "admit", "receipt": "S-0001", "player": "astra", "member": "CR 皇家", "mid": mid}]
    (subs / "submissions.jsonl").write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lines),
                                            encoding="utf-8")
    return host, pool, mid


def test_not_before_the_close(tmp_path):
    host, pool, mid = _host(tmp_path)
    with pytest.raises(E.EvalError):
        E.candidates(host, 1)


def test_one_member_against_its_baseline(tmp_path, monkeypatch):
    host, pool, mid = _host(tmp_path)
    pool.advance(force="test: the period closed")
    base, mine = E.candidates(host, 1)
    assert len(base) == 7 and [c["mid"] for c in mine] == [mid] and mine[0]["team"] == "Crazy Raccoon"
    monkeypatch.setattr(E, "SEEDS", {1: (93409050, 93409090)})
    monkeypatch.setattr(E, "SPAN", 5)
    with pytest.raises(E.EvalError):                            # 8 candidates need 40 seeds: the range holds 40
        monkeypatch.setattr(E, "SEEDS", {1: (93409050, 93409085)})
        E.evaluate(host, 1, workers=2, only=[mid], games=2, tail=1, repeats=2, log=lambda *_: None)
    monkeypatch.setattr(E, "SEEDS", {1: (93409050, 93409090)})
    body = E.evaluate(host, 1, workers=2, only=[mid], games=2, tail=1, repeats=2, log=lambda *_: None,
                      arena=tmp_path / "arena")                       # under the arena's lock, released after
    assert list((tmp_path / "arena" / "host" / "queue").glob("*.t")) == []
    assert "host" in json.loads((tmp_path / "arena" / "host" / "served.json").read_text(encoding="utf-8"))
    (row,) = body["members"]
    sword = next(b for b in base if b["craft"] == 2)["mid"]
    assert row["mid"] == mid and row["base_mid"] == sword and row["owner"] == "astra"
    assert set(body["baselines"]) == {b["mid"] for b in base} and body["baselines"][sword] is not None
    assert sum(v is not None for v in body["baselines"].values()) == 1      # only the class needed was run
    assert row["pass"] == (row["diff_lo"] > 0) and row["good"] == (row["diff"] >= 200)
    seeds = json.loads((host / "special" / "P1" / mid / "meta.json").read_text(encoding="utf-8"))["seeds"]
    k = [c["mid"] for c in base + mine].index(mid)
    assert seeds == [93409050 + 5 * k, 93409050 + 5 * (k + 1)]
    again = E.evaluate(host, 1, workers=2, only=[mid], games=2, tail=1, repeats=2, log=lambda *_: None)
    assert again["members"] == body["members"]                  # read back, not run again
    got = E.deliver(body, tmp_path / "players")
    assert got == {"astra": 1}
    text = (tmp_path / "players" / "astra" / "receipts" / "特殊期评测-P1.md").read_text(encoding="utf-8")
    assert "Crazy Raccoon" in text and "astra" not in text.split("\n", 3)[3]   # their own rows, no names column
    assert "astra" in (host / "special" / "P1" / "result-only.md").read_text(encoding="utf-8")
    assert not (host / "special" / "P1" / "result.md").exists()             # --only leaves the full report alone
    with pytest.raises(E.EvalError, match="另一次评测"):                       # a kept result of other settings
        E.evaluate(host, 1, workers=2, only=[mid], games=2, tail=2, repeats=2, log=lambda *_: None)


def test_frozen_only_at_the_periods_end(tmp_path):
    host, pool, mid = _host(tmp_path)
    pool.advance(force="test: the period closed")
    E.at_end(host / "pool", 1)                                          # just advanced: fine
    with pytest.raises(E.EvalError, match="池子在第 2 期"):
        E.at_end(host / "pool", 0)
    pool.advance(force="test: one more")
    with pytest.raises(E.EvalError):
        E.at_end(host / "pool", 1)


def test_the_lab_gets_a_turn_between_candidates(tmp_path, monkeypatch):
    import time as T
    slept = []
    monkeypatch.setattr(T, "sleep", slept.append)
    q = tmp_path / "arena" / "host" / "queue"
    q.mkdir(parents=True)
    (q / "00000000000000000001-7-host.t").touch()
    E.let_others_in(tmp_path / "arena")
    assert slept == []                                                  # only the host waits: straight on
    (q / "00000000000000000002-8-salem.t").touch()
    E.let_others_in(tmp_path / "arena")
    assert slept and slept[0] > 2


def test_welch():
    a = {"rel_cr": 100.0, "se": 10.0, "repeats": 5}
    b = {"rel_cr": 0.0, "se": 10.0, "repeats": 5}
    w = E.welch(a, b)
    assert w["diff"] == 100 and abs(w["df"] - 8) < 1e-9 and w["lo"] > 60 and w["hi"] < 140


def test_references_one_per_list():
    ids, _ = check_deck(CODES[1])
    rune, _ = check_deck(CODES[2])
    mine = [{"mid": "a", "craft": 2, "team": "Crazy Raccoon"}, {"mid": "b", "craft": 2, "team": "REJECT"},
            {"mid": "c", "craft": 3, "team": "Crazy Raccoon"}]
    refs = E.references(mine, {"a": ids, "b": list(reversed(ids)), "c": rune})   # a and b: one list, two orders
    assert [r["craft"] for r in refs] == [2, 3] and refs[0]["of"] == ["a", "b"] and refs[1]["of"] == ["c"]
    assert refs[0]["deck"] == sorted(ids) and refs[0]["team"] == "Crazy Raccoon、REJECT"
    assert refs[0]["mid"] == E.ref_mid(2, ids) == E.ref_mid(2, list(reversed(ids))) != refs[1]["mid"]
    assert all(r["owner"] == "reference" for r in refs)


def test_a_member_against_its_lists_default_strategy(tmp_path, monkeypatch):
    """(11-25, Salem's decision card) Beside the baseline, the member's list with the default strategy, from outside
    the pool, on seeds of its own; 过关 and 良好 stay against the baseline."""
    host, pool, mid = _host(tmp_path)
    ids, _ = check_deck(CODES[1])
    pool.advance(force="test: the period closed")
    base, mine = E.candidates(host, 1)
    monkeypatch.setattr(E, "SEEDS", {1: (93409050, 93409090)})
    monkeypatch.setattr(E, "SPAN", 4)
    monkeypatch.setattr(E, "REF_SEEDS", {1: (93403300, 93403303)})          # 1 reference needs 4: too few
    with pytest.raises(E.EvalError, match="对照"):
        E.evaluate(host, 1, workers=2, only=[mid], games=2, tail=1, repeats=2, log=lambda *_: None)
    monkeypatch.setattr(E, "REF_SEEDS", {1: (93403300, 93403340)})
    body = E.evaluate(host, 1, workers=2, only=[mid], games=2, tail=1, repeats=2, log=lambda *_: None)
    (row,) = body["members"]
    rid = E.ref_mid(2, ids)
    assert row["mid"] == mid and row["ref_mid"] == rid and set(body["references"]) == {rid}
    q = body["references"][rid]["result"]
    assert q is not None and row["ref_rel_cr"] == q["rel_cr"]
    assert row["play_diff"] == row["rel_cr"] - q["rel_cr"] and row["play_better"] == (row["play_lo"] > 0)
    assert row["pass"] == (row["diff_lo"] > 0) and row["good"] == (row["diff"] >= 200)   # still the baseline's
    meta = json.loads((host / "special" / "P1" / rid / "meta.json").read_text(encoding="utf-8"))
    assert meta["seeds"] == [93403300, 93403304]                         # its own range, from its start
    assert meta["candidate"]["strategy"] == E.DEFAULT and meta["candidate"]["deck"] == sorted(ids)
    k = [c["mid"] for c in base + mine].index(mid)                       # the members' seeds as before
    mseeds = json.loads((host / "special" / "P1" / mid / "meta.json").read_text(encoding="utf-8"))["seeds"]
    assert mseeds == [93409050 + 4 * k, 93409050 + 4 * (k + 1)]
    md = (host / "special" / "P1" / "result-only.md").read_text(encoding="utf-8")
    assert "同卡表默认打法" in md and "比默认打法" in md
    got = E.deliver(body, tmp_path / "players")
    text = (tmp_path / "players" / "astra" / "receipts" / "特殊期评测-P1.md").read_text(encoding="utf-8")
    assert got == {"astra": 1} and "比默认打法" in text
    again = E.evaluate(host, 1, workers=2, only=[mid], games=2, tail=1, repeats=2, log=lambda *_: None)
    assert again["members"] == body["members"]                          # read back, not run again

def test_no_references_without_their_seeds(tmp_path, monkeypatch):
    host, pool, mid = _host(tmp_path)
    pool.advance(force="test: the period closed")
    monkeypatch.setattr(E, "SEEDS", {1: (93409050, 93409090)})
    monkeypatch.setattr(E, "SPAN", 5)
    monkeypatch.setattr(E, "REF_SEEDS", {})
    body = E.evaluate(host, 1, workers=2, only=[mid], games=2, tail=1, repeats=2, log=lambda *_: None)
    assert "references" not in body and "ref_mid" not in body["members"][0]
    assert "比默认打法" not in (host / "special" / "P1" / "result-only.md").read_text(encoding="utf-8")
