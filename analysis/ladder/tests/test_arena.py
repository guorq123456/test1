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
    from ladder.runner import IDLE, LOAD
    j = {"id": "r-v0-c0001"}
    ok = {"id": "r-v0-c0001", "result": "normal", "winner": 1, "loser": None}
    assert arena._resumed(j, {"value": ok}) == ok
    t = arena._resumed(j, {"timeout": 1, "error": "ran past 30.0s of wall time"})
    assert (t["result"], t["loser"], t["winner"]) == ("timeout", 1, 0)
    assert arena._resumed(j, {"timeout": LOAD, "error": "x"})["result"] == "void"
    idle = arena._resumed(j, {"timeout": IDLE, "error": "nothing ran on any clock for 300s"})   # LD-42
    assert idle["result"] == "void" and "no clock" in idle["error"]
    assert arena._resumed(j, {"died": 9})["result"] == "void"
    c = arena._resumed(j, {"value": ok, "changed": "svsim.cards.pool.POOL: x"})
    assert c["result"] == "void" and c["voided_result"] == "normal" and c["winner"] is None
    assert arena.own_view(c, 0, {})["error"] is None              # the tripwire's text isn't the player's to see


# --- prompt review 11-23: received strategies in the field, runs of this field only, the formal games (A53) ----------

def test_the_snapshot_copies_the_fields_received_strategies(tmp_path, monkeypatch):
    # from period 2 the field holds players' members (and hall-of-fame anchors) on received code: the arena must
    # carry its own copy, and a snapshot without it is refused before anything is written
    monkeypatch.setitem(arena.PLAYER_SEEDS, "甲", (93400000, 93400200))
    from ladder.runner import load_deck
    pool = Pool.create(tmp_path / "pool", seeds=(93400190, 93400200), rng_seed=5, check=True)
    other = pool.enter([c.card_id for c in load_deck(CODES[1])], "py:sub_S0009:Quick", "乙", cr=1500)
    code = tmp_path / "subs" / "code"
    code.mkdir(parents=True)
    (code / "sub_S0009.py").write_text(QUICK, encoding="utf-8")
    a = tmp_path / "arena"
    with pytest.raises(arena.ArenaError, match="sub_S0009"):
        arena.snapshot(tmp_path / "pool", a, cr="current")
    assert not (a / "host" / "field.json").exists()
    host = arena.snapshot(tmp_path / "pool", a, cr="current", code=code)
    assert (a / "host" / "code" / "sub_S0009.py").read_text(encoding="utf-8") == QUICK
    assert list(host["code"]) == ["sub_S0009"]
    assert "sub_S0009" not in (a / "public" / "field.json").read_text(encoding="utf-8")
    arena.open_window(a, hours=1, games=10, workers=2)
    v = version(tmp_path / "v", QUICKER, CODES[6])
    out = arena.run_vs(a, "甲", v, 2, opponent=pool.members[other].anon, rng_seed=6)
    assert out["games"] == 2 and out["errors"] == 0
    logs = [json.loads(l) for l in (a / "host" / "players" / "jia" / out["run"] / "games.jsonl").read_text(
        encoding="utf-8").splitlines()]
    assert all(g["result"] != "void" for g in logs), [g.get("error") for g in logs]


def test_same_as_and_resume_only_on_this_periods_field(field, tmp_path):
    a, host, _ = field
    v = version(tmp_path / "v", QUICK, CODES[6])
    out = arena.run_vs(a, "甲", v, 2, opponent=host["members"][0]["anon"], rng_seed=7)
    game = json.loads((a / "players" / "甲" / "runs" / out["run"] / "games.jsonl").read_text(
        encoding="utf-8").splitlines()[0])["game"]
    lad = arena.run_ladder(a, "甲", v, games=4, tail=2, repeats=2, rng_seed=8)
    with pytest.raises(arena.ArenaError, match="不是 vs"):
        arena.run_vs(a, "甲", v, 0, same_as=lad["run"])
    for bad in ("../jia", "R1", "S-0001"):
        with pytest.raises(arena.ArenaError, match="没有这个编号"):
            arena.run_vs(a, "甲", v, 0, same_as=bad)
    # the next period: a new field (here one more member), a new window
    from ladder.runner import load_deck
    pool = Pool(tmp_path / "pool")
    pool.enter([c.card_id for c in load_deck(CODES[0])], FAST, "baseline", cr=1500)
    arena.snapshot(tmp_path / "pool", a, cr="current")
    arena.open_window(a, hours=1, games=60, workers=2)
    with pytest.raises(arena.ArenaError, match="不是这一期"):
        arena.run_vs(a, "甲", v, 0, same_as=out["run"])
    with pytest.raises(arena.ArenaError, match="不是这一期"):
        arena.run_resume(a, "甲", out["run"], game, 0, [v], continuations=1)
    arena.replay(a, "甲", out["run"], game)                          # looking at an old game is fine


def _formal_pool(tmp_path):
    """A pool with 甲's two members and two baseline ones, and five logged formal games of its period (seeds
    93400180-93400184, the arena tests' bank): 甲 v baseline both ways, 甲 v 甲, baseline v baseline, and one of
    another period."""
    from ladder.runner import load_deck, run
    pool = Pool.create(tmp_path / "pool", seeds=(93400190, 93400200), rng_seed=9, check=True)
    ids = [[c.card_id for c in load_deck(CODES[i])] for i in range(4)]
    a1 = pool.enter(ids[0], FAST, "甲", cr=1500)
    a2 = pool.enter(ids[1], FAST, "甲", cr=1500)
    b1 = pool.enter(ids[2], FAST, "baseline", cr=1500)
    b2 = pool.enter(ids[3], FAST, "baseline", cr=1500)
    ms = pool.members
    pairs = [(a1, b1, pool.period), (b2, a1, pool.period), (a1, a2, pool.period), (b1, b2, pool.period),
             (a2, b1, pool.period + 1)]
    jobs = [{"id": f"L{p}-{i + 1:07d}", "seed": 93400180 + i, "first": None, "decks": [ms[x].deck, ms[y].deck],
             "strategies": [FAST, FAST], "strategy_seeds": [11 + i, 21 + i],
             "labels": {"members": [x, y], "anon": [ms[x].anon, ms[y].anon], "versions": [1, 1], "period": p}}
            for i, (x, y, p) in enumerate(pairs)]
    run(jobs, str(tmp_path / "pool" / "games.jsonl"), workers=2, quiet=True, key=None)
    subs = tmp_path / "subs"
    subs.mkdir()
    (subs / "submissions.jsonl").write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in (
        {"ev": "admit", "receipt": "S-0001", "player": "甲", "member": "快攻", "mid": a1},
        {"ev": "admit", "receipt": "S-0002", "player": "甲", "member": "控制", "mid": a2})), encoding="utf-8")
    return pool, subs, (a1, a2, b1, b2)


def test_formal_games_go_to_their_owner_only(field, tmp_path):
    a, _, _ = field
    pool, subs, (a1, a2, b1, b2) = _formal_pool(tmp_path / "f")
    ms, p = pool.members, pool.period
    got = arena.formal(a, tmp_path / "f" / "pool", subs, p)
    assert got == {"甲": {"members": 2, "games": 4}}                   # nothing for a player without members
    me = a / "players" / "甲"
    members = json.loads((me / "members.json").read_text(encoding="utf-8"))
    assert {(r["member"], r["id"], r["in_pool"]) for r in members["members"]} == {("快攻", ms[a1].anon, True),
                                                                                ("控制", ms[a2].anon, True)}
    rid = f"F{p}"
    text = (me / "runs" / rid / "games.jsonl").read_text(encoding="utf-8")
    views = [json.loads(l) for l in text.splitlines()]
    assert [v["game"] for v in views] == [f"{rid}-{k:05d}" for k in range(1, 5)]
    # 甲 v baseline, baseline v 甲, then 甲 v 甲 seen from both seats (in the order the games ended); never the
    # baseline pair or another period
    assert sorted((v["member"], v["opponent"]["id"], v["seat"]) for v in views) == sorted([
        (ms[a1].anon, ms[b1].anon, 0), (ms[a1].anon, ms[b2].anon, 1), (ms[a1].anon, ms[a2].anon, 0),
        (ms[a2].anon, ms[a1].anon, 1)])
    second = next(v["game"] for v in views if v["seat"] == 1 and v["opponent"]["id"] == ms[b2].anon)
    for secret in [m.mid for m in ms.values()] + ["seed", FAST, f"L{p}-", "baseline"]:
        assert secret not in text, secret
    # the run can be replayed, not resumed or played again
    rep = json.loads(arena.replay(a, "甲", rid, second).read_text(encoding="utf-8"))
    assert rep["seat"] == 1 and rep["steps"]
    v = version(tmp_path / "v", QUICK, CODES[0])
    with pytest.raises(arena.ArenaError, match="正式对局"):
        arena.run_resume(a, "甲", rid, f"{rid}-00001", 0, [v], continuations=1)
    with pytest.raises(arena.ArenaError, match="正式对局"):
        arena.run_vs(a, "甲", v, 0, same_as=rid)
    summary = json.loads((me / "runs" / rid / "summary.json").read_text(encoding="utf-8"))
    assert summary["games"] == 4 and summary["members"][ms[a1].anon]["games"] == 3
    assert not (a / "players" / "乙").exists()
    # again: the same files, not twice the games
    arena.formal(a, tmp_path / "f" / "pool", subs, p)
    assert (me / "runs" / rid / "games.jsonl").read_text(encoding="utf-8") == text


def test_the_field_includes_the_anchors_and_replay_takes_the_seat_from_the_host(field, tmp_path):
    # 11-23 review: a re-snapshot with another anchor panel kept the members' hash; and replay read the seat from the
    # player's own (writable) view file, which could show the opponent's hand
    a, host, _ = field
    v = version(tmp_path / "v", QUICK, CODES[6])
    out = arena.run_vs(a, "甲", v, 2, opponent=host["anchors"][0]["id"], rng_seed=11)
    vf = a / "players" / "甲" / "runs" / out["run"] / "games.jsonl"
    views = [json.loads(l) for l in vf.read_text(encoding="utf-8").splitlines()]
    flipped = [dict(x, seat=1 - x["seat"]) for x in views]
    vf.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in flipped), encoding="utf-8")
    rep = json.loads(arena.replay(a, "甲", out["run"], views[0]["game"]).read_text(encoding="utf-8"))
    assert rep["seat"] == views[0]["seat"]                           # the host's record, not the edited file
    arena.snapshot(tmp_path / "pool", a, cr="current")                # the same members, no anchors
    arena.open_window(a, hours=1, games=60, workers=2)
    assert arena.Seat(a, "甲").host["hash"] == host["hash"]
    with pytest.raises(arena.ArenaError, match="不是这一期"):
        arena.run_vs(a, "甲", v, 0, same_as=out["run"])
    runs = sorted(p.name for p in (a / "players" / "甲" / "runs").iterdir())
    (a / "host" / "players" / "jia" / out["run"] / "run.json").unlink()
    with pytest.raises(arena.ArenaError, match="没有记下"):
        arena.run_vs(a, "甲", v, 0, same_as=out["run"])
    assert sorted(p.name for p in (a / "players" / "甲" / "runs").iterdir()) == runs   # no run opened for nothing
