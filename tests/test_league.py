"""Bradley–Terry strengths for bot versions (learn.league, tools.league), on synthetic gate results."""
import json
import math
import random

from svsim.learn import league as L
from svsim.tools import league as tool


def synthetic(true: dict, schedule: list, pairs: int, seed: int = 1, draw: float = 0.0) -> list:
    """Matches played as the gate plays them (pairs of games), A winning with the BT probability."""
    rng = random.Random(seed)
    out = []
    for a, b in schedule:
        p = 1 / (1 + math.exp(-(true[a] - true[b])))
        games = []
        for _ in range(pairs):
            pair = []
            for _ in range(2):
                u = rng.random()
                pair.append(0.5 if u < draw else 1.0 if u < draw + (1 - draw) * p else 0.0)
            games.append(tuple(pair))
        out.append(L.Match(a, b, games))
    return out


TRUE = {"v1": 0.0, "v2": 0.4, "v3": -0.3, "v4": 0.9}
SCHEDULE = [("v2", "v1"), ("v3", "v1"), ("v4", "v2"), ("v3", "v2"), ("v4", "v1")]


def test_the_fit_recovers_the_strengths_behind_the_results():
    est = L.fit(synthetic(TRUE, SCHEDULE, 3000), ref="v1")
    assert est["v1"] == 0.0
    for n, r in TRUE.items():
        assert abs(est[n] - r) < 0.08, (n, est[n], r)


def test_one_match_gives_the_logit_of_the_score():
    m = L.Match("a", "b", [(1.0, 1.0)] * 30 + [(1.0, 0.0)] * 40 + [(0.0, 0.0)] * 30)   # 50%
    assert abs(L.fit([m])["b"]) < 1e-6
    m = L.Match("a", "b", [(1.0, 1.0)] * 60 + [(0.0, 0.0)] * 40)                       # a scores 60%
    est = L.fit([m], ref="b")
    assert abs(est["a"] - math.log(0.6 / 0.4)) < 1e-3


def test_a_version_that_won_everything_stays_finite():
    est = L.fit([L.Match("a", "b", [(1.0, 1.0)] * 10)], ref="b")
    assert 3 < est["a"] < 20


def test_intervals_cover_the_truth_and_narrow_with_more_games():
    few = L.bootstrap(synthetic(TRUE, SCHEDULE, 60, seed=3), ref="v1", samples=200)
    many = L.bootstrap(synthetic(TRUE, SCHEDULE, 1500, seed=3), ref="v1", samples=200)
    for n in TRUE:
        if n == "v1":
            continue
        assert many[n][0] <= TRUE[n] <= many[n][1], (n, many[n])
        assert many[n][1] - many[n][0] < few[n][1] - few[n][0]


def test_cr_without_anchors_is_relative_with_the_ladder_slope():
    crs, slope, offset = L.to_cr({"a": 0.0, "b": 0.5})
    assert slope == L.CR_PER_LOGIT and offset == 0.0
    assert crs == {"a": 0.0, "b": 100.0}


def test_one_anchor_sets_the_offset_and_two_fit_the_slope():
    r = {"a": 0.0, "b": 0.5, "c": 1.0}
    crs, slope, _ = L.to_cr(r, {"a": 1700})
    assert crs["a"] == 1700 and crs["c"] == 1700 + L.CR_PER_LOGIT and slope == L.CR_PER_LOGIT
    crs, slope, offset = L.to_cr(r, {"a": 1700, "c": 2000})
    assert abs(slope - 300) < 1e-9 and abs(crs["b"] - 1850) < 1e-9
    crs, _, _ = L.to_cr(r, {"unknown": 1500})          # anchors for versions not played are ignored
    assert crs["a"] == 0.0


def test_disconnected_versions_are_detected():
    assert L.connected(synthetic(TRUE, SCHEDULE, 2))
    assert not L.connected([L.Match("a", "b", [(1, 0)]), L.Match("c", "d", [(1, 0)])])


def test_the_tool_reads_gate_files_and_prints_the_table(tmp_path, capsys):
    files = []
    for m in synthetic(TRUE, SCHEDULE[:3], 200, seed=5):
        path = tmp_path / f"gate-{m.a}-{m.b}.jsonl"
        path.write_text("".join(json.dumps({"k": k, "seed": 1000 + k, "points": list(p)}) + "\n"
                                for k, p in enumerate(m.pairs)), encoding="utf-8")
        files += ["--match", m.a, m.b, str(path)]
    tool.main(files + ["--anchor", "v1=1700", "--bootstrap", "50"])
    out = capsys.readouterr().out
    assert "v4" in out and "1700" in out and "v2 对 v1" in out
    lines = [line for line in out.splitlines() if line.startswith("v")]
    assert [line.split()[0] for line in lines][0] == "v4"      # strongest first
