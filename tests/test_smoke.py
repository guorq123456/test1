"""tools.smoke: a pair of games, its report, and the recheck of the turns the probe didn't finish."""


def test_a_smoke_pair_reports_and_rechecks_unfinished_probes():
    from svsim.tools import records as R
    from svsim.tools.smoke import play_pair, recheck, report
    results = play_pair((0, 5, "ramp-t", "ramp-t", "greedy", 300))     # a tiny probe: some turns unfinished
    assert len(results) == 2 and not any(r["error"] for r in results)
    for r in results:
        starts = [t["i"] for t in r["turns"]]
        assert starts == sorted(starts) and len(list(R.steps(r["record"]))) == len(r["record"]["actions"])
        todo = sum(1 for t in r["turns"] if not t["probe_complete"] and not t["lethal"])
        assert recheck(r, 2000) == todo
    text = report(results)
    assert "对手卡表已知" in text and "ramp-t" in text
