"""tools/special_rr.py (Salem 11-27): period 4's players against each other only. A made-up host: three players with
two or three decks each (two of them missing one), strategies from HOST/subs/code. Seeds 92648000-92648999 only (the
host's dry-run range): the formal layout is checked without games, and the games are played with SEEDS patched into
that range (formal: 92648100-92648153; the void games: 92648500-92648517) or with TRIAL_SEEDS patched to
92648200-92648299 (--trial), apart from tests/test_special.py's 92648000-92648049."""
import json
import math
import random
import secrets
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "tools"))
import special_rr as R

from ladder import deal
from ladder.pool import Pool

BLUEPRINT = {
    1: {10501110: 3, 10711120: 3, 11012110: 3, 10814120: 3, 10514120: 3, 11013310: 3, 11014110: 2, 10503210: 3,
        10811130: 3, 10514110: 2, 11012310: 3, 10914110: 3, 11013110: 3, 10814110: 3},
    4: {10542120: 2, 10842120: 3, 10544120: 3, 10603210: 3, 10644110: 3, 10844120: 3, 10544110: 3, 10644120: 3,
        10543310: 3, 10042310: 3, 10503310: 3, 10944120: 3, 10744110: 3, 11044110: 2},
    6: {10062210: 3, 10861110: 3, 10863210: 1, 10863110: 3, 11062110: 2, 10061210: 2, 11062310: 3, 10861120: 2,
        11001110: 1, 11061110: 2, 11002110: 3, 10962120: 3, 11063310: 3, 10864120: 3, 11064110: 3, 11063110: 3},
}
PLAYERS = ("pa-alpha", "pb-bravo", "pc-charlie")
HAVE = {"pa-alpha": (1, 4, 6), "pb-bravo": (1, 4), "pc-charlie": (1, 6)}     # bravo: no 兔子教, charlie: no 跳费龙
STRATEGY = '''import random

from ladder import base


class Mine:
    def __init__(self, seed=0):
        self.rng = random.Random(seed)

    def act(self, pos, actions):
        return actions[self.rng.randrange(len(actions))]

    def guess(self, pos):
        return base.default_guess(pos.opp_craft)
'''

BAD = STRATEGY.replace("        self.rng = random.Random(seed)", "        raise RuntimeError('never builds')")   # void

ROOT = HERE.parents[2]
SWORD = [l.strip().split("|")[1] for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(
    encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")][1]      # the baseline Swordcraft list


def _ids(craft, k=0):
    """The blueprint of `craft` with k cards changed (one copy each of its first k kinds out, k cards of the class
    from period 3's lists in, as tests/test_special.py does it)."""
    from ladder import special
    ids = sorted(c for c, n in BLUEPRINT[craft].items() for _ in range(n))
    if k:
        for c in sorted(set(ids))[:k]:
            ids.remove(c)
        others = sorted({c for by in special.teams(3).values() for c in by[craft]["ids"]} - set(BLUEPRINT[craft]))
        ids += [c for c in others for _ in range(3)][:k]
    return ids


def _code(craft, k=0):
    from svsim.cards.decks import to_hash

    from ladder.runner import load_deck
    if craft == 2:
        return SWORD
    return to_hash(load_deck(_ids(craft, k)))


def _record(craft, changes):
    """The receipt's blueprint record, as submit.py (submit-3) writes it."""
    name = next(n for c, n, _ in R.ARCH if c == craft)
    return {"name": name, "craft": craft, "max_changes": 6 if craft == 6 else 7, "changes": changes, "out": [],
            "in": []}


def _host(tmp_path, players=PLAYERS, period=5, have=HAVE, bad=()):
    """bad: (player, class) whose strategy raises when it is built (every game of it void)."""
    host = tmp_path / "host"
    pool = Pool.create(host / "pool", seeds=(92648990, 92649000), rng_seed=1)       # never played
    for _ in range(period):
        pool.advance(force="test")
    subs = host / "subs"
    (subs / "code").mkdir(parents=True)
    lines, n = [], 0

    def receipt(player, craft, changes=0, **kw):
        nonlocal n
        n += 1
        rid = f"S-{n:04d}"
        (subs / rid).mkdir()
        (subs / rid / "submission.json").write_text(json.dumps({"type": "新卡组", "deck": _code(craft, changes)}),
                                                    encoding="utf-8")
        spec = f"py:sub_S{n:04d}:Mine"
        (subs / "code" / f"sub_S{n:04d}.py").write_text(BAD if (player, craft) in bad else STRATEGY, encoding="utf-8")
        line = {"ev": "receipt", "id": rid, "player": player, "period": 4, "kind": "deck", "verdict": "收下",
                "member": f"{player.split('-')[1]}-{craft}", "craft": craft, "spec": spec, "version": "submit-3",
                **({"blueprint": _record(craft, changes)} if craft in BLUEPRINT else {}), **kw}
        lines.append(line)
        return line
    for p in players:
        for c in have[p]:
            receipt(p, c, changes=3 if (p, c) == ("pb-bravo", 1) else 0)   # bravo's 快攻妖精: 3 cards changed
    receipt(players[0], 2)                                   # another class: not evaluated, in the notes
    receipt(players[1], 6, verdict="拒收")                    # refused: not a member
    receipt(players[1], 6, period=3)                         # another period
    if "pb-bravo" in players and 1 in have["pb-bravo"]:      # a non-py strategy
        next(l for l in lines if l["player"] == "pb-bravo" and l["craft"] == 1).update(spec="bot:greedy")
    _ledger(host, lines)
    return host, lines


def _ledger(host, lines):
    (host / "subs" / "submissions.jsonl").write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lines),
                                                     encoding="utf-8")


@pytest.fixture(autouse=True)
def _own_path(monkeypatch):
    """evaluate puts HOST/subs/code on sys.path and LADDER_EXTRA_PATH: each test's own, given back after it."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.delenv("LADDER_EXTRA_PATH", raising=False)


def _logs(out):
    return [json.loads(l) for f in sorted((out / "games").glob("*.jsonl"))
            for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_the_formal_layout():
    five = ("fable-ultracode", "fable", "astra", "opus", "sol")
    lay = R.layout(five, 4)
    ps = lay["pairs"]
    assert len(ps) == 90 and lay["n"] == 500 and lay["used"] == [96310000, 96354999]
    assert all(p["a"][0] != p["b"][0] for p in ps)                      # a player's own three never meet
    assert len({(p["a"], p["b"]) for p in ps}) == 90
    from collections import Counter
    assert set(Counter(s for p in ps for s in (p["a"], p["b"])).values()) == {12}    # each member: 4 players x 3
    assert set(Counter((p["a"][0], p["b"][0]) for p in ps).values()) == {9}          # each two players: 3 x 3
    seen = set()
    for p in ps:
        s = R.pair_seeds(lay, p["k"])
        assert s == list(range(96310000 + 500 * p["k"], 96310000 + 500 * (p["k"] + 1)))
        assert not seen & set(s)
        seen |= set(s)
    assert min(seen) >= R.SEEDS[4][0] and max(seen) < R.SEEDS[4][1]
    assert R.layout(five, 4)["pairs"] == ps                             # the same every time
    assert R.layout(five, trial=11)["used"] == [92648000, 92648989]
    with pytest.raises(R.EvalError):
        R.layout(five, trial=12)                                         # 90 x 12 > the trial range
    with pytest.raises(R.EvalError):
        R.layout(five, trial=1)
    with pytest.raises(R.EvalError):
        R.layout(five, 5)                                                # no seeds for period 5
    from ladder import special  # what the submission side has for period 4
    spec = special.SPECIAL[4]
    assert tuple(spec["eval_seeds"]) == R.SEEDS[4]
    assert [(b["craft"], n) for n, b in spec["blueprints"].items()] == [(c, n) for c, n, _ in R.ARCH]
    assert {c: b["cards"] for b in spec["blueprints"].values() for c in [b["craft"]]} == BLUEPRINT


def test_counting_draws_voids_errors_and_missing():
    lay = R.layout(("x", "y"), trial=50)
    cands = {s: {} for s in R.slots(("x", "y")) if s != ("y", 6)}      # y has no 兔子教
    pair = lay["pairs"][0]
    assert pair["a"] == ("x", 1) and pair["b"] == ("y", 1)
    got = {}
    for i in range(50):
        got[R.job_id(4, 0, i, 0)] = {"result": "normal", "winner": 0 if i < 30 else 1}    # a in seat 0
        if i < 2:
            got[R.job_id(4, 0, i, 1)] = {"result": "void", "winner": None}
        elif i < 5:
            got[R.job_id(4, 0, i, 1)] = {"result": "draw", "winner": None}
        elif i < 7:
            got[R.job_id(4, 0, i, 1)] = {"result": "crash", "winner": 1}                 # b (seat 0) crashed
        else:
            got[R.job_id(4, 0, i, 1)] = {"result": "normal", "winner": 0}                # a in seat 1 lost
    row, units = R.tally(pair, lay, cands, got, 4)
    assert row["status"] == "played" and row["voids"] == 2 and row["draws"] == 3 and row["games"] == 98
    assert row["score_a"] == 30 + 1.5 + 2 and row["score_b"] == 98 - row["score_a"]
    assert row["wins_a"] == 32 and row["wins_b"] == 20 + 43 and row["errors"] == {"b:crash": 2}
    assert row["void_share"] == 0.02                                     # not above 2%: not flagged
    r = R.rate([R.view(row, units, "a")])
    p = row["score_a"] / 98
    es = [s - p * n for s, n in units if n]
    se = math.sqrt(len(es) / (len(es) - 1) * sum(e * e for e in es)) / 98
    assert abs(r["rate"] - p) < 1e-12 and abs(r["se"] - se) < 1e-12 and abs(r["lo"] - (p - R.Z95 * se)) < 1e-12
    b = R.rate([R.view(row, units, "b")])
    assert abs(b["rate"] + r["rate"] - 1) < 1e-12 and abs(b["se"] - r["se"]) < 1e-12
    with pytest.raises(R.EvalError, match="没有记录"):                    # a game not played yet
        R.tally(pair, lay, cands, {k: v for k, v in got.items() if k != R.job_id(4, 0, 7, 1)}, 4)
    gone = next(p for p in lay["pairs"] if p["b"] == ("y", 6))           # x's member against y's missing one
    row2, u2 = R.tally(gone, lay, cands, {}, 4)
    assert u2 is None and row2["missing"] == ["b"] and row2["score_a"] == 100 and row2["score_b"] == 0
    both = R.rate([R.view(row, units, "a"), R.view(row2, u2, "a")])
    pb = (row["score_a"] + 100) / 198
    assert both["games"] == 198 and both["missing_games"] == 100 and abs(both["rate"] - pb) < 1e-12
    es = [s - pb * n for s, n in units if n]                             # the missing games are fixed: only the
    mean = sum(es) / len(es)                                             # played pair's units vary
    se2 = math.sqrt(len(es) / (len(es) - 1) * sum((e - mean) ** 2 for e in es)) / 198
    assert abs(both["se"] - se2) < 1e-12


def test_dry_plays_and_writes_nothing(tmp_path):
    host, _ = _host(tmp_path, period=4)                                  # period 4 not closed: dry says so
    d = R.dry(host, 4, players=PLAYERS, key=None)
    assert d["pairs"] == 27 and d["playable"] == 16 and d["games"] == 16 * 1000
    assert d["members"]["pb-bravo/兔子教"] == "缺交" and d["members"]["pc-charlie/跳费龙"] == "缺交"
    assert d["members"]["pb-bravo/快攻妖精"]["changes"] == 3 and not d["formal_ready"]
    assert any("第 4 期" in w for w in d["warnings"]) and any("密钥" in w for w in d["warnings"])
    assert len(d["notes"]) == 1 and "皇家护卫" in d["notes"][0] and d["doubts"] == []
    t = R.dry(host, 4, trial=2, players=PLAYERS, key=None)
    assert t["games"] == 64 and t["seeds"]["used"] == [92648000, 92648053]
    assert not (host / "special").exists()


def test_the_formal_run(tmp_path, monkeypatch):
    """Patched to 2 seeds a pair on 92648100-92648159: 16 pairs played (64 games), 11 with a missing member."""
    import environments
    monkeypatch.setattr(R, "SEEDS", {4: (92648100, 92648160)})
    monkeypatch.setattr(R, "PER_PAIR", 2)
    monkeypatch.setattr(environments, "check", lambda period, root=None: {"name": "test-env"})
    host, lines = _host(tmp_path, period=4)
    key = secrets.token_bytes(32)
    with pytest.raises(R.EvalError, match="第 4 期收尾"):                 # the period isn't closed
        R.evaluate(host, 4, workers=2, key=key, players=PLAYERS, log=lambda *_: None)
    Pool(host / "pool").advance(force="test: the period closed")
    with pytest.raises(R.EvalError, match="密钥"):                        # no key: refused, though deal.py wouldn't
        R.evaluate(host, 4, workers=2, key=None, players=PLAYERS, log=lambda *_: None)
    assert deal.formal(92648100) is None and deal.formal(96310000) is None
    out = host / "special" / "P4"
    assert not (out / "games").exists()
    body = R.evaluate(host, 4, workers=2, key=key, arena=tmp_path / "arena", players=PLAYERS, log=lambda *_: None)
    assert list((tmp_path / "arena" / "host" / "queue").glob("*.t")) == []                  # the lock let go
    assert "host" in json.loads((tmp_path / "arena" / "host" / "served.json").read_text(encoding="utf-8"))

    rows = body["pairs"]
    played = [r for r in rows if r["status"] == "played"]
    assert len(rows) == 27 and len(played) == 16 and body["games"]["played"] == 64
    assert sorted(body["missing"]) == ["pb-bravo/兔子教", "pc-charlie/跳费龙"]
    logs = _logs(out)
    assert len(logs) == 64 and len({g["id"] for g in logs}) == 64
    kid = deal.key_id(key)
    assert all(g["deal"] and g["deal"]["key"] == kid for g in logs)                         # every game keyed
    ranges = [tuple(r["seeds"]) for r in rows]
    assert ranges == [(92648100 + 2 * k, 92648101 + 2 * k) for k in range(27)]             # disjoint, in order
    by_pair = {}
    for g in logs:
        k = g["labels"]["pair"]
        assert ranges[k][0] <= g["seed"] <= ranges[k][1]
        by_pair.setdefault((k, g["seed"]), []).append(g)
    assert len(by_pair) == 32 and all(len(v) == 2 for v in by_pair.values())
    for (k, seed), (g, h) in by_pair.items():                           # one seed, both seats
        assert {g["labels"]["a_seat"], h["labels"]["a_seat"]} == {0, 1}
        assert g["decks"] == h["decks"][::-1] and g["strategies"] == h["strategies"][::-1]
        assert g["deal"]["engine"] == h["deal"]["engine"] and g["first"] == h["first"]
    assert all(r["score_a"] + r["score_b"] == r["games"] for r in played)
    assert body["hold"] == [] or body["games"]["void"]                   # held only for void games

    # 缺交: every game it was due is lost, the other side wins it; both missing: both lose
    m = body["members"]["pb-bravo/兔子教"]
    assert m["total"]["games"] == 6 * 4 and m["total"]["rate"] == 0 and m["total"]["losses"] == 24
    vs = next(r for r in rows if r["a"] == "pa-alpha/快攻妖精" and r["b"] == "pb-bravo/兔子教")
    assert vs["status"] == "missing" and vs["score_a"] == 4 and vs["score_b"] == 0
    nobody = next(r for r in rows if r["a"] == "pb-bravo/兔子教" and r["b"] == "pc-charlie/跳费龙")
    assert nobody["missing"] == ["a", "b"] and nobody["score_a"] == nobody["score_b"] == 0
    assert body["same_arch"]["兔子教"]["pa-alpha"]["pb-bravo"]["rate"] == 1.0
    assert body["members_in"]["pb-bravo/快攻妖精"]["changes"] == 3 and len(body["notes"]) == 1
    for p in PLAYERS:
        t = body["totals"][p]
        assert t["games"] == 18 * 4 - t["voids"]                         # 3 members x 6 others x 4 games
        assert t["lo"] <= t["rate"] <= t["hi"]
        assert sum(body["matrix"][p][q]["games"] for q in PLAYERS if q != p) == t["games"]
    assert min(body["ranks"].values()) == 1
    md = (out / "rr-result.md").read_text(encoding="utf-8")
    assert all(p in md for p in PLAYERS) and "妖对妖" in md and "兔对兔" in md and "缺交" in md

    got = R.deliver(body, tmp_path / "players")
    assert sorted(got) == sorted(PLAYERS)
    for p in PLAYERS:                                                    # their own numbers, nobody else's
        text = (tmp_path / "players" / p / "receipts" / "特殊期评测-P4.md").read_text(encoding="utf-8")
        assert f"第 {body['ranks'][p]}" in text and "3 个选手" in text and R.pct(body["totals"][p], long=True) in text
        assert "少交了哪一副，那一副该打的局算你赢" in text and R.PLAYER_INTERVAL in text and R.INTERVAL not in text
        for l in lines:
            if l["player"] != p:
                for leak in (l["player"], l["player"].split("-")[1], l["member"], l["id"], l["spec"]):
                    assert leak not in text, (p, leak)
        for q, info in body["members_in"].items():
            if not q.startswith(p + "/"):
                assert info["code"] not in text
        assert p not in text                                             # not even their own name
    assert "缺交" in (tmp_path / "players" / "pb-bravo" / "receipts" / "特殊期评测-P4.md").read_text(encoding="utf-8")

    again = R.evaluate(host, 4, workers=2, key=key, players=PLAYERS, log=lambda *_: None)   # read back, no games
    assert len(_logs(out)) == 64 and again["totals"] == body["totals"]
    with pytest.raises(R.EvalError, match="另一次评测"):                   # another key: never mixed
        R.evaluate(host, 4, workers=2, key=secrets.token_bytes(32), players=PLAYERS, log=lambda *_: None)


def test_a_trial_run(tmp_path, monkeypatch):
    """--trial: its own range and folder, no key needed, the period need not be closed, never delivered."""
    monkeypatch.setattr(R, "TRIAL_SEEDS", (92648200, 92648300))
    two = PLAYERS[:2]
    host, _ = _host(tmp_path, players=two, period=4)
    said = []
    body = R.evaluate(host, 4, workers=2, trial=2, key=None, players=two, log=said.append)
    out = host / "special" / "P4" / "trial-2"
    logs = _logs(out)
    assert body["trial"] == 2 and len(body["pairs"]) == 9 and len(logs) == 6 * 4 == body["games"]["played"]
    assert all(92648200 <= g["seed"] < 92648218 and g["deal"] is None for g in logs)
    assert any("密钥" in s for s in said) and not (host / "special" / "P4" / "rr-plan.json").exists()
    with pytest.raises(R.EvalError, match="试跑"):
        R.deliver(body, tmp_path / "players")


def _formal_ready(monkeypatch, host, env="test-env"):
    """The period closed and the simulator the period's (environments.check patched); returns the key (made up)."""
    import environments

    def check(period, root=None):
        if env is None:
            raise SystemExit("这台电脑的模拟器不是第 4 期的环境（测试）")
        return {"name": env}
    monkeypatch.setattr(environments, "check", check)
    if Pool(host / "pool").period <= 4:
        Pool(host / "pool").advance(force="test: the period closed")
    return secrets.token_bytes(32)


def test_doubts_about_the_ledger_stop_a_formal_run(tmp_path, monkeypatch):
    """The changes are counted again: a receipt with no blueprint record, another count, or a deck over the cap. No
    game is played."""
    host, lines = _host(tmp_path, period=5)
    key = _formal_ready(monkeypatch, host)
    assert R.candidates(host, 4, PLAYERS)[2] == []
    alpha = {l["craft"]: l for l in lines if l["player"] == "pa-alpha" and l.get("verdict") == "收下"
             and l.get("period") == 4}
    del alpha[1]["blueprint"]                                           # no record
    alpha[4]["blueprint"]["changes"] = 2                                # the record says 2, the deck has 0
    over = next(l for l in lines if l["player"] == "pc-charlie" and l["craft"] == 6)
    (host / "subs" / over["id"] / "submission.json").write_text(
        json.dumps({"type": "新卡组", "deck": _code(6, 7)}), encoding="utf-8")     # 7 > 兔子教's 6
    over["blueprint"]["changes"] = 7
    _ledger(host, lines)
    _, _, doubts = R.candidates(host, 4, PLAYERS)
    assert len(doubts) == 3
    assert alpha[1]["id"] in doubts[0] and "没有蓝本" in doubts[0]
    assert alpha[4]["id"] in doubts[1] and "改了 2 张" in doubts[1] and "0 张" in doubts[1]
    assert over["id"] in doubts[2] and "改了 7 张，超过上限 6 张" in doubts[2]
    d = R.dry(host, 4, players=PLAYERS, key=key)
    assert d["doubts"] == doubts and not d["formal_ready"] and d["members"]["pc-charlie/兔子教"]["changes"] == 7
    with pytest.raises(R.EvalError, match="台账和卡组对不上"):
        R.evaluate(host, 4, workers=2, key=key, players=PLAYERS, log=lambda *_: None)
    assert not (host / "special").exists()                             # stopped before anything is written


def test_two_decks_of_one_blueprint_and_plans_that_differ(tmp_path):
    host, lines = _host(tmp_path, period=5)
    first = next(l for l in lines if l["player"] == "pa-alpha" and l["craft"] == 6)
    twin = dict(first, id="S-0099")
    (host / "subs" / "S-0099").mkdir()
    (host / "subs" / "S-0099" / "submission.json").write_text(
        (host / "subs" / first["id"] / "submission.json").read_text(encoding="utf-8"), encoding="utf-8")
    _ledger(host, lines + [twin])
    with pytest.raises(R.EvalError, match="收下了两副"):
        R.candidates(host, 4, PLAYERS)
    _ledger(host, lines)
    cands, _, _ = R.candidates(host, 4, PLAYERS)
    lay = R.layout(PLAYERS, trial=2)
    plan = R.plan_record(4, PLAYERS, lay, cands, "k1", "env-a")
    path = tmp_path / "plan" / "rr-plan.json"
    R._same_plan(path, plan)                                             # written
    R._same_plan(path, json.loads(json.dumps(plan)))                     # the same: fine
    other = {**plan, "members": {**plan["members"], "pa-alpha/兔子教": None}}
    for changed, what in ((other, "members"), (R.plan_record(4, PLAYERS[:2], R.layout(PLAYERS[:2], trial=2), cands,
                                                             "k1", "env-a"), "players"),
                          ({**plan, "env": "env-b"}, "env")):
        with pytest.raises(R.EvalError, match=what):
            R._same_plan(path, changed)


def test_the_tables_are_symmetric():
    """Made-up results for five players, two seeds a pair: a player's rate against another and the other's against
    them add up to 1 (a missing deck: the other side wins it), and a total is the mean of the four (equal games)."""
    five = ("p1", "p2", "p3", "p4", "p5")
    lay = R.layout(five, trial=2)
    missing = {("p2", 6)}
    cands = {s: {} for s in R.slots(five) if s not in missing}
    rng = random.Random(5)
    got = {R.job_id(4, p["k"], i, x): {"result": "draw" if rng.random() < 0.1 else "normal",
                                       "winner": rng.randrange(2), "why": None}
           for p in lay["pairs"] for i in range(2) for x in (0, 1)}
    rows, units = [], {}
    for p in lay["pairs"]:
        row, u = R.tally(p, lay, cands, got, 4)
        rows.append(row)
        if u is not None:
            units[p["k"]] = u
    s = R.summarize(five, rows, units)
    for p in five:
        for q in five:
            if p != q:
                assert abs(s["matrix"][p][q]["rate"] + s["matrix"][q][p]["rate"] - 1) < 1e-12, (p, q)
                assert s["matrix"][p][q]["games"] == 9 * 4
        mean = sum(s["matrix"][p][q]["rate"] for q in five if q != p) / 4
        assert abs(s["totals"][p]["rate"] - mean) < 1e-12
    assert s["members"]["p2/兔子教"]["total"]["rate"] == 0 and s["same_arch"]["兔子教"]["p1"]["p2"]["rate"] == 1
    cands.pop(("p3", 6))                                                 # both missing: both lose that pair
    rows = [R.tally(p, lay, cands, got, 4)[0] for p in lay["pairs"]]
    both = next(r for r in rows if r["a"] == "p2/兔子教" and r["b"] == "p3/兔子教")
    assert both["score_a"] == both["score_b"] == 0 and both["games"] == 4


def test_void_games_stop_the_run_hold_the_result_and_wait_for_deliver(tmp_path, monkeypatch, capsys):
    """alpha's 兔子教 can't be built: every game of it void. Two seeds a pair on 92648500-92648517 (2 players, 9
    pairs; 2 of them playable: alpha's 快攻妖精 and 兔子教 against bravo's 快攻妖精): 4 games played and 4 void."""
    two = PLAYERS[:2]
    monkeypatch.setattr(R, "SEEDS", {4: (92648500, 92648518)})
    monkeypatch.setattr(R, "PER_PAIR", 2)
    monkeypatch.setattr(R, "_players", lambda: two)
    host, _ = _host(tmp_path, players=two, period=5, have={"pa-alpha": (1, 6), "pb-bravo": (1,)},
                    bad={("pa-alpha", 6)})
    key = _formal_ready(monkeypatch, host)
    kf = tmp_path / "deal-key.txt"                                       # main() reads the key as the host does
    kf.write_text(key.hex() + "\n", encoding="ascii")
    monkeypatch.setenv(deal.KEY_ENV, str(kf))
    out = host / "special" / "P4"
    with pytest.raises(R.EvalError, match="pa-alpha/兔子教 这一次作废了 3 局"):
        R.evaluate(host, 4, workers=2, key=key, arena=tmp_path / "arena", players=two, log=lambda *_: None,
                   void_stop=3)
    assert list((tmp_path / "arena" / "host" / "queue").glob("*.t")) == []                 # the lock let go
    assert 3 <= sum(g["result"] == "void" for g in _logs(out)) < 8
    body = R.evaluate(host, 4, workers=2, key=key, players=two, log=lambda *_: None, void_stop=False)
    v = body["member_voids"]["pa-alpha/兔子教"]
    assert v["voids"] == v["games"] == 4 and list(v["why"]) == ["strategy failed to load:"]
    assert body["member_voids"]["pb-bravo/快攻妖精"] == {"voids": 4, "games": 8, "why": v["why"], "share": 0.5}
    assert body["void_flagged"] == [6] and body["games"] == {"played": 8, "counted": 4, "void": 4,
                                                              "draws": body["games"]["draws"]}
    assert any("pa-alpha/兔子教 的局作废 4/4" in h for h in body["hold"])
    md = (out / "rr-result.md").read_text(encoding="utf-8")
    assert "先不发给选手" in md and "strategy failed to load: 4" in md and "由主持方和 Salem 定" in md
    box = tmp_path / "players" / "pa-alpha" / "receipts" / "特殊期评测-P4.md"
    argv = ["--host", str(host), "--players", str(tmp_path / "players"), "--arena", str(tmp_path / "arena"),
            "--workers", "2"]
    assert R.main(argv) == 0                                             # read back, no game: held, not delivered
    assert "先不发给选手" in capsys.readouterr().out and not box.exists()
    assert len(_logs(out)) == 8
    _formal_ready(monkeypatch, host, env=None)                           # the simulator moved on
    assert R.main(argv) == 1 and "不是第 4 期的环境" in capsys.readouterr().out
    assert R.main(argv + ["--report"]) == 0                              # the report again, from the logs
    assert "--report 从日志重出" in (out / "rr-result.md").read_text(encoding="utf-8") and not box.exists()
    assert R.main(argv + ["--deliver"]) == 0                             # the host has read it: delivered
    said = capsys.readouterr().out
    assert "照你说的发" in said and box.exists() and (tmp_path / "players" / "pb-bravo" / "receipts" /
                                                      "特殊期评测-P4.md").exists()
    assert "另有作废 4 局" in box.read_text(encoding="utf-8") and "pb-bravo" not in box.read_text(encoding="utf-8")
    assert len(_logs(out)) == 8


def test_a_later_periods_open_window_is_said(tmp_path):
    from datetime import datetime, timedelta, timezone
    pub = tmp_path / "arena" / "public"
    pub.mkdir(parents=True)
    later = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(timespec="seconds")
    for period, deadline, said in ((5, later, True), (4, later, False), (5, "2026-01-01T00:00:00+00:00", False)):
        (pub / "window.json").write_text(json.dumps({"period": period, "deadline": deadline}), encoding="utf-8")
        w = R._window_open(tmp_path / "arena", 4)
        assert bool(w) is said and (not said or "第 5 期的练习场窗口开着" in w)
    assert R._window_open(tmp_path / "none", 4) is None
