"""tools/special_check.py: the round, the room in the pool as it is, and a claim end to end on a copy."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "tools"))
sys.path.insert(0, str(HERE.parents[2]))
import special_check  # noqa: E402
from ladder import special  # noqa: E402
from ladder.pool import Pool  # noqa: E402


def host_in_period_1(tmp_path, monkeypatch):
    monkeypatch.setattr(special, "SPECIAL", {1: special.SPECIAL[3]})
    special.teams.cache_clear()
    pool = Pool.create(tmp_path / "host" / "pool", seeds=(99001460, 99001470), rng_seed=1)
    pool.advance()
    return tmp_path / "host", pool


def test_room_and_a_claim(tmp_path, monkeypatch):
    host, pool = host_in_period_1(tmp_path, monkeypatch)
    out = tmp_path / "out"
    out.mkdir()
    res = special_check.check(host, 1, out)
    assert res["ok"], res["problems"]
    assert res["round"]["codes_sha256"] == "e5a6b19e898b2ad0" and res["round"]["illegal"] == {}
    assert res["held"] == {}
    assert res["room_alone"] == {"Crazy Raccoon": 2, "MURASH GAMING": 2, "REJECT": 2, "レバンガ北海道": 2}
    assert res["room_together"] == 5 and res["enough"]       # five players, and six places (LVH and RC: 2 between them)
    assert res["claim"]["first"] == "收下" and res["claim"]["again"] == "拒收"
    assert list(out.iterdir()) == []                          # the scratch copy is gone
    assert len(pool.active()) == 0 and Pool(host / "pool").period == 1
    special.teams.cache_clear()


def test_a_held_list_takes_a_place(tmp_path, monkeypatch):
    host, pool = host_in_period_1(tmp_path, monkeypatch)
    pool.enter(special.teams(1)["MURASH GAMING"][5]["ids"], "bot:mcts:100+plan", "fable-ultracode")
    res = special_check.check(host, 1, tmp_path)
    assert res["held"] == {"MURASH GAMING 梦魇": ["m0001"]}
    assert res["room_alone"]["MURASH GAMING"] == 1 and res["room_together"] == 5 and res["enough"]
    sword = special.teams(1)["Crazy Raccoon"][2]["ids"]
    pool.enter(sword, "bot:mcts:100+plan", "fable")
    pool.enter(sword, "bot:mcts:100+plan", "opus")
    res = special_check.check(host, 1, tmp_path)
    assert res["room_alone"]["Crazy Raccoon"] == 0 and res["room_together"] == 3 and not res["enough"]
    assert not res["ok"] and "only 3" in res["problems"][0]
    special.teams.cache_clear()


def test_not_yet_in_the_period(tmp_path, monkeypatch):
    host, pool = host_in_period_1(tmp_path, monkeypatch)
    monkeypatch.setattr(special, "SPECIAL", {2: special.SPECIAL[1]})
    special.teams.cache_clear()
    res = special_check.check(host, 2, tmp_path)
    assert not res["ok"] and "close period 1 first" in res["problems"][0]
    assert special_check.main(["--period", "2", "--host", str(host), "--out", str(tmp_path / "o")]) == 1
    assert json.loads((tmp_path / "o" / "summary.json").read_text(encoding="utf-8"))["pool_period"] == 1
    special.teams.cache_clear()
