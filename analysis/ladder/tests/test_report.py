"""The players' environment report (ladder/report.py): only anonymous ids, classes and numbers; the win tables count
one period; the anchor results are per class without ids or counts (A42, A43, S11/A48). Made-up games, no engine."""
import json
import os
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE), str(HERE.parents[2])]
os.environ["LADDER_EXTRA_PATH"] = str(HERE)
from ladder import report as R  # noqa: E402
from ladder.pool import Pool  # noqa: E402
from test_pool import BASE_DECKS  # noqa: E402


def _play(pool, n, strengths, rng):
    for _ in range(n):
        job = pool.next_job()
        a, b = job["labels"]["members"]
        pool.settle({"id": job["id"], "result": "normal",
                     "winner": 0 if rng.random() < 0.5 + strengths[a] - strengths[b] else 1})


def test_report_says_nothing_about_owners_versions_or_age(tmp_path, monkeypatch):
    pool = Pool.create(tmp_path / "pool", (10 ** 12, 2 * 10 ** 12), rng_seed=5, check=True)
    strengths = {}
    for i, (d, owner, s) in enumerate([(BASE_DECKS[0], "baseline", 0.0), (BASE_DECKS[1], "baseline", 0.0),
                                       (BASE_DECKS[2], "baseline", 0.0), (BASE_DECKS[0], "甲", 0.06),
                                       (BASE_DECKS[1], "乙", -0.03)]):
        strengths[pool.enter(d, "bot:greedy", owner, rng=random.Random(i))] = s
    rng = random.Random(6)
    _play(pool, 600, strengths, rng)
    pool.advance(force="test")
    _play(Pool(pool.dir), 300, strengths, rng)
    pool = Pool(pool.dir)
    mids = {m.owner: m.mid for m in pool.active()}
    ver = {m.owner: m.version for m in pool.active()}
    craft = {m.owner: m.craft for m in pool.active()}
    # anchors (S11): the last period's run, per class; an older period's line must not show
    (tmp_path / "anchors").mkdir()
    lines = [(pool.period, "甲", 14, 6), (pool.period, "乙", 8, 12), (pool.period - 1, "乙", 1, 19)]
    (tmp_path / "anchors" / "anchors.jsonl").write_text("".join(
        json.dumps({"period": p, "member": mids[o], "version": ver[o], "craft": craft[o], "anchor": "A00",
                    "tier": "基线快照", "games": 20, "won": w, "lost": l, "draw": 0, "void": 0, "batch": f"b{p}"}) + "\n"
        for p, o, w, l in lines), encoding="utf-8")
    from ladder.anchors import _write_json
    for p in (pool.period - 1, pool.period):
        _write_json(tmp_path / "anchors" / f"plan-P{p}.json", {"period": p, "jobs": 40, "first_seed": 40 * p,
                                                                "done": f"b{p}"})
    puzzle = tmp_path / "result-public.json"
    puzzle.write_text(json.dumps({"puzzle": "P01", "title": "一题", "entries": [
        {"entry": "默认打法", "rate": .5, "lo": .4, "hi": .6},
        {"entry": "选手 1", "rate": .6, "lo": .5, "hi": .7, "vs_default_pp": [10.0, 2.0, 18.0]}],
        "agreement": [{"a": "选手 1", "b": "默认打法", "same": .8, "points": 40}]}, ensure_ascii=False),
        encoding="utf-8")
    r = R.build(pool.dir, tmp_path / "anchors", [puzzle], note="第一期")
    text = json.dumps(r, ensure_ascii=False) + R.markdown(r)
    for word in ("甲", "乙", "owner", "version", "mid") + tuple(mids.values()):
        assert word not in text, word
    # the win tables count the last period only (300 games: 600 decided appearances in all)
    assert r["games_period"] == pool.period
    assert sum(v[1] for t in r["wins_vs_class"].values() for v in t.values()) == 600
    assert sum(v[1] for t in r["wins_vs_member"].values() for v in t.values()) == 600
    before = R.build(pool.dir, games_period=pool.period - 1)
    assert sum(v[1] for t in before["wins_vs_class"].values() for v in t.values()) == 1200
    # anchors (S11, A48): per class and the whole pool, rounded, no id, no counts; the older period left out: 22 of 40
    from ladder.pool import CRAFT_ZH
    assert r["anchors_period"] == pool.period
    assert r["anchors"] == [{"craft": CRAFT_ZH[craft["甲"]], "tier": "基线快照", "rate": 70, "lo": 48, "hi": 85},
                            {"craft": CRAFT_ZH[craft["乙"]], "tier": "基线快照", "rate": 40, "lo": 22, "hi": 61},
                            {"craft": "全池", "tier": "基线快照", "rate": 55, "lo": 40, "hi": 69}]
    assert "| 全池 | 55%（40～69%） |" in R.markdown(r)
    md = R.markdown(r)
    assert "第一期" in md and "P01" in md and "选手 1" in md and "+10.0（+2.0～+18.0）" in md
    assert {b["anon"] for b in r["board"]} <= {m.anon for m in pool.active()}


def test_cli_writes_both_files(tmp_path):
    pool = Pool.create(tmp_path / "pool", (10 ** 12, 2 * 10 ** 12), rng_seed=7, check=True)
    for i, d in enumerate(BASE_DECKS[:3]):
        pool.enter(d, "bot:greedy", "baseline", rng=random.Random(i))
    _play(pool, 50, {m.mid: 0.0 for m in pool.active()}, random.Random(8))
    assert R.main([str(pool.dir), "--out", str(tmp_path / "pub")]) == 0
    assert (tmp_path / "pub" / f"report-P{pool.period}.md").exists()
    assert json.loads((tmp_path / "pub" / f"report-P{pool.period}.json").read_text(encoding="utf-8"))["board"] == []
