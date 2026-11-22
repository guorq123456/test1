"""The practice arena (phase 2, item 2.4). 甲's tuning sub-range is the player's, so the tests move it to the host's
second probe bank: seeds 93400000-93400199 (SEEDS.md); the test pool's ladder range 93400190-93400199 plays nothing."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
from ladder import arena  # noqa: E402
from ladder.pool import Pool  # noqa: E402

ROOT = HERE.parents[2]
LINES = [l.strip().split("|") for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(encoding="utf-8")
         .splitlines() if l.strip() and not l.startswith("#")]
CODES = [c for _, c in LINES]
FAST = "bot:mcts:8"

QUICK = '''
from ladder.interface import PlayerStrategy


class Quick(PlayerStrategy):
    LETHAL = "exact"

    def search(self, pos):
        return {"iterations": 8}
'''
QUICKER = QUICK.replace('"iterations": 8', '"iterations": 4')


def version(d: Path, src: str, deck: str) -> Path:
    d.mkdir(parents=True)
    (d / "strategy.py").write_text(src, encoding="utf-8")
    (d / "submission.json").write_text(json.dumps({"class": "Quick", "deck": deck}), encoding="utf-8")
    return d


@pytest.fixture()
def field(tmp_path, monkeypatch):
    monkeypatch.setitem(arena.PLAYER_SEEDS, "甲", (93400000, 93400200))
    from ladder.runner import load_deck
    pool = Pool.create(tmp_path / "pool", seeds=(93400190, 93400200), rng_seed=3, check=True)
    for code, cr in ((CODES[1], 1450), (CODES[2], 1500), (CODES[3], 1550)):
        pool.enter([c.card_id for c in load_deck(code)], FAST, "baseline", cr=cr)
    mine = pool.enter([c.card_id for c in load_deck(CODES[4])], FAST, "甲", cr=1500)
    anchors = tmp_path / "anchors.json"
    anchors.write_text(json.dumps([{"name": "bot 贪心", "deck": CODES[5], "strategy": "bot:greedy"}],
                                  ensure_ascii=False), encoding="utf-8")
    a = tmp_path / "arena"
    host = arena.snapshot(tmp_path / "pool", a, anchors, cr="current")
    arena.open_window(a, hours=1, games=60, workers=2)
    return a, host, pool.members[mine].anon


def test_the_public_field_shows_only_public_things(field):
    a, host, _ = field
    # never in the pool's own (admission) order, which groups members by owner (review 11-22)
    assert [m["anon"] for m in host["members"]] == sorted(m["anon"] for m in host["members"])
    pub = json.loads((a / "public" / "field.json").read_text(encoding="utf-8"))
    text = json.dumps(pub, ensure_ascii=False)
    for m in host["members"]:
        assert m["mid"] not in text and m["strategy"] not in text and str(m["deck"][0]) not in text
    assert "bot:greedy" not in text and "baseline" not in text and "甲" not in text
    assert sorted(r["rel_cr"] for r in pub["opponents"] if r["kind"] == "成员") == [-50, 0, 0, 50]


def test_vs_same_as_resume_replay(field, tmp_path):
    a, host, mine = field
    v1 = version(tmp_path / "v1", QUICK, CODES[6])
    v2 = version(tmp_path / "v2", QUICKER, CODES[6])
    out = arena.run_vs(a, "甲", v1, 4, craft_zh=None, opponent=host["members"][0]["anon"], rng_seed=1)
    assert out["games"] == 4 and 0 <= out["wins"] <= 4
    views = [json.loads(l) for l in (a / "players" / "甲" / "runs" / out["run"] / "games.jsonl").read_text(
        encoding="utf-8").splitlines()]
    text = json.dumps(views, ensure_ascii=False)
    assert "seed" not in text and host["members"][0]["mid"] not in text and FAST not in text
    assert all(v["opponent"]["id"] == host["members"][0]["anon"] for v in views)
    # the opponent's mulligan shows as a bare Mulligan
    assert all(m == {"type": "Mulligan"} for v in views for who, m in v["moves"] if who == "对手" and
               m["type"] == "Mulligan")
    same = arena.run_vs(a, "甲", v2, 0, same_as=out["run"], rng_seed=2)
    assert same["games"] == 4 and same["paired"]["games"] == same["decided"]
    priv = arena.PINYIN["甲"]
    j1 = json.loads((a / "host" / "players" / priv / out["run"] / "jobs.json").read_text(encoding="utf-8"))
    j2 = json.loads((a / "host" / "players" / priv / same["run"] / "jobs.json").read_text(encoding="utf-8"))
    assert j1["plan"] == j2["plan"]                                   # same deals, opponents, seats, strategy seeds
    # resume from my 3rd decision of the first game: continuation 0 with the same version replays the original
    game = views[0]["game"]
    res = arena.run_resume(a, "甲", out["run"], game, 2, [v1, v2], continuations=2, rng_seed=3)
    assert res["games_each"] == 3 and set(res["wins"]) == {"0", "1"}
    conts = [json.loads(l) for l in (a / "players" / "甲" / "runs" / res["run"] / "games.jsonl").read_text(
        encoding="utf-8").splitlines()]
    upto = [i for i, (who, _) in enumerate(views[0]["moves"]) if who == "我"][2]
    assert len(conts) == 6 and all(c["moves"][:upto] == views[0]["moves"][:upto] for c in conts)
    # a continuation can't be replayed or resumed again (reshuffled after the resume point): a clear refusal
    with pytest.raises(arena.ArenaError, match="续打出来的局"):
        arena.replay(a, "甲", res["run"], conts[0]["game"])
    with pytest.raises(arena.ArenaError, match="续打出来的局"):
        arena.run_resume(a, "甲", res["run"], conts[0]["game"], 0, [v1], continuations=1)
    # the replay holds my view only
    path = arena.replay(a, "甲", out["run"], game)
    rep = json.loads(path.read_text(encoding="utf-8"))
    assert all(isinstance(s["view"]["opponent"]["hand"], int) for s in rep["steps"] if "view" in s)
    # the count
    seat = arena.Seat(a, "甲")
    assert seat.used() == 4 + 4 + 6
    with pytest.raises(arena.ArenaError, match="还剩"):
        arena.run_vs(a, "甲", v1, 100, opponent=host["members"][0]["anon"])


def test_ladder_mode_and_replacing(field, tmp_path):
    a, host, mine = field
    v = version(tmp_path / "v", QUICK, CODES[4])
    out = arena.run_ladder(a, "甲", v, replacing=mine, games=10, tail=5, repeats=2, rng_seed=4)
    assert out["games"] >= 1 and out["repeats"] == 2
    with pytest.raises(arena.ArenaError, match="不是你的成员"):
        arena.run_ladder(a, "甲", v, replacing=next(m["anon"] for m in host["members"] if m["anon"] != mine),
                         games=4, tail=2, repeats=2)


def test_refusals(field, tmp_path):
    a, host, _ = field
    bad = version(tmp_path / "bad", QUICK + "\nX = open('x')\n", CODES[6])
    with pytest.raises(arena.ArenaError, match="提交校验"):
        arena.run_vs(a, "甲", bad, 2, opponent=host["members"][0]["anon"])
    with pytest.raises(arena.ArenaError, match="没有代号"):
        arena.Seat(a, "己")


def test_resumed_outcomes_become_logs():
    # LD-40: the resume run asks through runner.guarded_map; a hang in a decision loses by timeout, a hang while
    # loading or a dead worker is void, and a continuation during which the simulator changed is void
    from ladder.runner import LOAD
    j = {"id": "r-v0-c0001"}
    ok = {"id": "r-v0-c0001", "result": "normal", "winner": 1, "loser": None}
    assert arena._resumed(j, {"value": ok}) == ok
    t = arena._resumed(j, {"timeout": 1, "error": "ran past 30.0s of wall time"})
    assert (t["result"], t["loser"], t["winner"]) == ("timeout", 1, 0)
    assert arena._resumed(j, {"timeout": LOAD, "error": "x"})["result"] == "void"
    assert arena._resumed(j, {"died": 9})["result"] == "void"
    c = arena._resumed(j, {"value": ok, "changed": "svsim.cards.pool.POOL: x"})
    assert c["result"] == "void" and c["voided_result"] == "normal" and c["winner"] is None
    assert arena.own_view(c, 0, {})["error"] is None              # the tripwire's text isn't the player's to see
