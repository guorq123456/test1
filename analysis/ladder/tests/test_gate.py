"""The gate (phase 1, item 1.7): the SPRT on made-up pairs (false passes ~ alpha, misses ~ beta), the plan's
expected game counts, and real gates through the runner: identical versions, a clearly stronger and a clearly weaker
update, a fixed run, the ledger and its refusals. Gate seeds 99001800-99001899 (host probe bank, SEEDS.md)."""
import json
import os
import random
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE), str(HERE.parents[2])]
os.environ["LADDER_EXTRA_PATH"] = str(HERE)
from ladder import evaluator as E  # noqa: E402
from ladder import gate as G  # noqa: E402
from ladder import pool as P  # noqa: E402
from test_pool import BASE_DECKS, SEEDS  # noqa: E402

GATE_SEEDS = (99001800, 99001900)


def test_expected_games_match_the_plan():
    """Plan 检验口径: with a 40% discordant share, H1 +5 pp is about 1,700 games, +2 pp about 11,000."""
    for gap, games in ((5, 1700), (3, 5000), (2, 11000), (1.5, 19000), (1, 40000)):
        p0, p1 = G.p_of_gap(0, 0.4), G.p_of_gap(gap, 0.4)
        assert 2 * G.expected_pairs(p0, p1, 0.4) == pytest.approx(games, rel=0.12)


def test_sprt_error_rates_on_made_up_pairs():
    at0 = G.simulate(0.0, 0.0, 5.0, 0.4, 600, 1)
    at1 = G.simulate(5.0, 0.0, 5.0, 0.4, 600, 2)
    assert at0["accept_h1"] <= 0.09                     # alpha = 0.05
    assert at1["accept_h1"] >= 0.88                     # 1 - beta = 0.95, minus the undecided at 3x
    assert at1["mean_pairs"] == pytest.approx(at1["expected_pairs_h1"], rel=0.15)


@pytest.fixture()
def frozen(tmp_path):
    pool = P.Pool.create(tmp_path / "pool", SEEDS, rng_seed=11)
    for craft in (2, 5, 7):
        pool.enter(BASE_DECKS[craft - 1], "py:helpers:Random", "baseline", rng=random.Random(craft))
    fz = tmp_path / "frozen.json"
    fz.write_text(json.dumps(E.freeze(tmp_path / "pool", cr="current")), encoding="utf-8")
    return fz, E.load_frozen(fz)[0][0].mid


def gate(tmp_path, fz, mid, new, old, kind, **kw):
    # greedy vs random is thousands of times the compute, and random's microseconds per step are pure timing noise:
    # the compute rule is checked on its own below
    kw.setdefault("compute_is_the_point", True)
    return G.Gate(fz, mid, new, old, kind, change=kw.pop("change", "test"), prediction=kw.pop("prediction", "test"),
                  seeds=GATE_SEEDS, out_dir=tmp_path / "gates", ledger_root=tmp_path, rng_seed=kw.pop("rng", 1),
                  **kw)


def test_identical_versions_pass_without_statistics(tmp_path, frozen):
    fz, mid = frozen
    rec = gate(tmp_path, fz, mid, "py:helpers:Random", "py:helpers:Random", "same", pairs=12).run(workers=2)
    assert rec["verdict"].startswith("passed")
    rec = gate(tmp_path, fz, mid, "bot:greedy", "py:helpers:Random", "same", pairs=6, rng=2).run(workers=2)
    assert rec["verdict"].startswith("not passed")


def test_a_clearly_stronger_update_passes_and_a_weaker_one_doesnt(tmp_path, frozen):
    fz, mid = frozen
    good = gate(tmp_path, fz, mid, "bot:greedy", "py:helpers:Random", "better", delta=10, share=0.5).run(workers=3)
    assert good["verdict"] == "passed" and good["discordant"]["new"] > good["discordant"]["old"]
    assert good["pairs"] < good["cap_pairs"]
    # opponents are tallied over every pair the test used; the discordant ones are exactly what the test counted
    assert sum(good["opponents_discordant"].values()) == sum(good["discordant"].values())
    assert sum(good["opponents"].values()) >= sum(good["discordant"].values())
    bad = gate(tmp_path, fz, mid, "py:helpers:Random", "bot:greedy", "better", delta=10, share=0.5,
               rng=3).run(workers=3)
    assert bad["verdict"] == "not passed"
    lines = G.read_ledger(tmp_path)
    assert [r["gate"] for r in lines] == ["G-0001", "G-0002"]
    seeds = [set(r["seeds_used"]) for r in lines]
    assert not seeds[0] & seeds[1]                       # a gate never reuses a seed any earlier gate used
    assert all(GATE_SEEDS[0] <= s < GATE_SEEDS[1] for s in seeds[0] | seeds[1])
    md = (tmp_path / "GATES.md").read_text(encoding="utf-8")
    assert md.count("| G-000") == 2


def test_fixed_run_reports_a_gap_by_class(tmp_path, frozen):
    fz, mid = frozen
    rec = gate(tmp_path, fz, mid, "bot:greedy", "py:helpers:Random", "fixed", pairs=24).run(workers=3)
    assert rec["gap_pp"] > 0 and rec["ci_pp"][0] < rec["gap_pp"] < rec["ci_pp"][1]
    assert sum(v["pairs"] for v in rec["by_class"].values()) <= 24
    assert rec["compute_ratio"] > 1                      # greedy thinks far longer than random


def test_unequal_compute_makes_a_gate_invalid(tmp_path, frozen):
    fz, mid = frozen
    rec = gate(tmp_path, fz, mid, "bot:greedy", "py:helpers:Random", "fixed", pairs=4,
               compute_is_the_point=False).run(workers=2)
    assert rec["verdict"].startswith("invalid: compute ratio")


def test_refusals(tmp_path, frozen):
    fz, mid = frozen
    with pytest.raises(P.PoolError):
        gate(tmp_path, fz, mid, "bot:greedy", "py:helpers:Random", "better", prediction=" ")
    gate(tmp_path, fz, mid, "bot:greedy", "py:helpers:Random", "same", pairs=2).run(workers=1)
    with pytest.raises(P.PoolError):                     # the same change a second time
        gate(tmp_path, fz, mid, "bot:greedy", "py:helpers:Random", "same", pairs=2)
    g = gate(tmp_path, fz, mid, "bot:greedy", "py:helpers:Random", "same", pairs=2,
             resubmit_of="G-0001", since="search order changed")
    assert g.gid == "G-0002"


def test_a_member_nobody_can_reach(tmp_path, frozen, monkeypatch):
    fz, mid = frozen
    body = json.loads(fz.read_text(encoding="utf-8"))
    body["members"][0]["cr"] = 1800                      # the others are at 1500: 300 away
    far = tmp_path / "far.json"
    far.write_text(json.dumps(body), encoding="utf-8")
    m0 = body["members"][0]["mid"]
    monkeypatch.setattr(E, "FAR", "wait")                # S2 strictly: nothing to test it against
    with pytest.raises(P.PoolError, match="nobody within 200"):
        gate(tmp_path, far, m0, "bot:greedy", "py:helpers:Random", "same", pairs=2)
    monkeypatch.setattr(E, "FAR", "closest")             # A28: the closest (here all of them are)
    g = gate(tmp_path, far, m0, "bot:greedy", "py:helpers:Random", "same", pairs=2)
    jobs = g._pair(0, "x")
    assert g.pairs[-1]["how"] == "far" and len(jobs) == 2


def test_identical_versions_in_the_sequential_test_stop_with_no_difference(tmp_path, frozen, monkeypatch):
    fz, mid = frozen
    monkeypatch.setattr(G, "SAME_AFTER", 15)
    rec = gate(tmp_path, fz, mid, "py:helpers:Random", "py:helpers:Random", "better", share=0.4).run(workers=2)
    assert rec["verdict"].startswith("no difference") and rec["pairs"] < rec["cap_pairs"]


def test_an_interrupted_gate_is_recorded_and_the_rerun_starts_fresh(tmp_path, frozen, monkeypatch):
    # review 11-22: a re-run used to reuse the stopped attempt's folder, skip its games and end undecided
    fz, mid = frozen
    from ladder import runner
    real = runner.run
    calls = {"n": 0}

    def stop_after_four(jobs, out, **kw):
        cut = []
        for j in jobs:
            cut.append(j)
            if len(cut) == 4:
                break
        real(cut, out, **kw)
        raise KeyboardInterrupt
    monkeypatch.setattr(runner, "run", stop_after_four)
    with pytest.raises(KeyboardInterrupt):
        gate(tmp_path, fz, mid, "bot:greedy", "py:helpers:Random", "better", delta=10, share=0.5).run(workers=2)
    monkeypatch.setattr(runner, "run", real)
    assert G.read_ledger(tmp_path) == []
    g = gate(tmp_path, fz, mid, "bot:greedy", "py:helpers:Random", "better", delta=10, share=0.5, rng=5)
    lines = G.read_ledger(tmp_path)
    assert g.gid == "G-0002" and [r["gate"] for r in lines] == ["G-0001"] and lines[0]["interrupted"]
    assert lines[0]["new"] == "bot:greedy" and len(lines[0]["seeds_used"]) == 2
    rec = g.run(workers=3)
    assert rec["verdict"] == "passed"                            # the interrupted attempt is not "gated already"
    assert not set(rec["seeds_used"]) & set(lines[0]["seeds_used"])


def test_a_used_up_seed_range_is_refused(tmp_path, frozen):
    fz, mid = frozen
    G.append_ledger({"gate": "G-0001", "date": "11-22", "member": mid, "kind": "fixed", "new": "x", "old": "y",
                     "change": "t", "prediction": "t", "seed_note": "", "opponents_note": "", "verdict": "t",
                     "seeds_used": list(range(*GATE_SEEDS))}, tmp_path)
    with pytest.raises(P.PoolError, match="used up"):
        gate(tmp_path, fz, mid, "bot:greedy", "py:helpers:Random", "better", delta=10, share=0.5)
