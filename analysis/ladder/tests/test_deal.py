"""base-2's keyed deal (ladder/deal.py; LEDGER LD-27, LD-29): seeds a strategy can't work back, list order the uids
don't give away, logs that replay without the key, and the formal pool refusing to play without one.
Seeds 93400200-93400219 (host probe bank 2, SEEDS.md)."""
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE), str(HERE.parents[2])]
os.environ["LADDER_EXTRA_PATH"] = str(HERE)
from ladder import deal, runner  # noqa: E402
from ladder import pool as P  # noqa: E402
from ladder.replay import replay_decisions, replay_moves  # noqa: E402
from test_pool import BASE_DECKS, SEEDS  # noqa: E402

ROOT = HERE.parents[2]
CODES = [l.strip().split("|")[1] for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(
    encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
KEY = bytes(range(32))


def a_job(i, **kw):
    return {"id": f"d-{i}", "seed": 93400200 + i, "first": None, "decks": [CODES[1], CODES[4]],
            "strategies": ["bot:greedy", "bot:greedy"], "labels": {}, **kw}


def test_seal_derives_what_a_strategy_cant_work_back():
    j = a_job(0)
    assert deal.seal(j, None) is j                                     # no key: the old deal
    s = deal.seal(j, KEY)
    assert "deal" not in j and s["deal"]["key"] == deal.key_id(KEY)   # a copy; the log names the key, not gives it
    assert s["deal"]["engine"] != j["seed"]
    assert s["strategy_seeds"] != [j["seed"] * 2 + 1, j["seed"] * 2 + 2]
    assert deal.seal(j, KEY) == s and deal.seal(s, bytes(32)) is s     # the same every time; sealed once
    assert deal.seal(j, bytes(32))["deal"]["engine"] != s["deal"]["engine"]
    own = deal.seal(a_job(1, strategy_seeds=[5, 6]), KEY)
    assert own["strategy_seeds"] == [5, 6]                             # seeds a host tool drew itself are kept


def test_without_a_deal_the_game_is_the_old_one():
    from svsim.core.engine import new_game
    j = a_job(2)
    _, st = deal.start(j, first="first")
    decks = [runner.load_deck(d) for d in j["decks"]]
    old = new_game(decks[0], decks[1], seed=j["seed"], first=None)
    assert st.first == old.first
    assert [[c.uid for c in p.hand] for p in st.players] == [[c.uid for c in p.hand] for p in old.players]


def _uid_order(state, seat):
    cards = list(state.players[seat].deck) + list(state.players[seat].hand)
    return [c.defn.card_id for c in sorted(cards, key=lambda c: c.uid)]


def test_uids_no_longer_follow_the_list_order():
    # LD-29: without a deal the uids number the cards in list order; with one they don't
    j = a_job(3)
    listed = [c.card_id for c in runner.load_deck(j["decks"][1])]
    _, st = deal.start(j, first="first")
    assert _uid_order(st, 1) == listed
    _, st2 = deal.start(deal.seal(j, KEY), first="first")
    order = _uid_order(st2, 1)
    assert sorted(order) == sorted(listed) and order != listed


def test_keyed_games_log_the_deal_and_replay_without_the_key(tmp_path):
    kf = tmp_path / "k.key"
    kid = deal.new_key_file(kf)
    with pytest.raises(deal.DealError):
        deal.new_key_file(kf)                                          # made once
    out = tmp_path / "games.jsonl"
    res = runner.run([a_job(10), a_job(11)], str(out), workers=2, quiet=True, key=str(kf))
    assert res["deal"] == kid and res["played"] == 2
    logs = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    for log in logs:
        assert log["deal"]["key"] == kid and log["deal"]["version"] == deal.DEAL_VERSION
        assert log["strategy_seeds"] != [log["seed"] * 2 + 1, log["seed"] * 2 + 2]
        assert replay_moves(log) == (True, "ok")
        assert replay_decisions(log) == (True, "ok")
    plain = tmp_path / "plain.jsonl"
    runner.run([a_job(10)], str(plain), workers=1, quiet=True, key=None)
    p = json.loads(plain.read_text(encoding="utf-8"))
    assert p["deal"] is None and p["strategy_seeds"] == [p["seed"] * 2 + 1, p["seed"] * 2 + 2]


def test_load_key_errors_and_env(tmp_path, monkeypatch):
    monkeypatch.delenv(deal.KEY_ENV, raising=False)
    assert deal.load_key() is None or deal.DEFAULT_KEY.is_file()
    with pytest.raises(deal.DealError):
        deal.load_key(tmp_path / "missing.key")
    kf = tmp_path / "k.key"
    deal.new_key_file(kf)
    monkeypatch.setenv(deal.KEY_ENV, str(kf))
    assert deal.resolve("auto") == deal.load_key(kf)
    short = tmp_path / "short.key"
    short.write_text("abcd\n", encoding="ascii")
    with pytest.raises(deal.DealError):
        deal.load_key(short)


def test_the_players_pool_wont_play_without_a_key(tmp_path, monkeypatch):
    monkeypatch.delenv(deal.KEY_ENV, raising=False)
    if deal.DEFAULT_KEY.is_file():
        pytest.skip("the host's key file is on this machine")
    pool = P.Pool.create(tmp_path / "p", SEEDS, rng_seed=7)
    for i, d in enumerate(BASE_DECKS):
        pool.enter(d, "bot:greedy", "baseline")
    pool.advance(force="test")                                         # period 1: players' members may enter
    with pytest.raises(P.PoolError, match="deal key"):
        pool.ladder(games=1)
