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
    body = E.evaluate(host, 1, workers=2, only=[mid], games=2, tail=1, repeats=2, log=lambda *_: None)
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
    assert "astra" in (host / "special" / "P1" / "result.md").read_text(encoding="utf-8")


def test_welch():
    a = {"rel_cr": 100.0, "se": 10.0, "repeats": 5}
    b = {"rel_cr": 0.0, "se": 10.0, "repeats": 5}
    w = E.welch(a, b)
    assert w["diff"] == 100 and abs(w["df"] - 8) < 1e-9 and w["lo"] > 60 and w["hi"] < 140
