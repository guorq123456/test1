"""Pins of the task spec's numeric rules (§3, §4.2). Run: python -m pytest analysis/ladder/tests -q"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ladder import rules as R  # noqa: E402

# §3 by bin, from the higher (or equal) side: (lowest d, highest d, win, loss)
TABLE = [(0, 24, 16, -16), (25, 49, 15, -17), (50, 74, 14, -18), (75, 99, 13, -19), (100, 124, 12, -20),
         (125, 149, 11, -21), (150, 174, 10, -22), (175, 175, 9, -23), (176, 400, 8, -24)]


@pytest.mark.parametrize("lo,hi,win,loss", TABLE)
def test_each_bin_from_the_higher_side(lo, hi, win, loss):
    for d in range(lo, hi + 1):
        assert R.delta(1500 + d, 1500, True) == win, d
        assert R.delta(1500 + d, 1500, False) == loss, d


@pytest.mark.parametrize("lo,hi,win,loss", TABLE)
def test_the_lower_side_mirrors(lo, hi, win, loss):
    for d in range(lo, hi + 1):
        if d == 0:
            continue
        # the lower side gets what the higher side loses, and loses what it wins
        assert R.delta(1500, 1500 + d, True) == -loss, d
        assert R.delta(1500, 1500 + d, False) == -win, d


def test_zero_sum_and_integer_everywhere():
    for d in range(-500, 501):
        for a_won in (True, False):
            a, b = R.settle(1500 + d, 1500, a_won)
            assert isinstance(a, int) and isinstance(b, int)
            assert a + b == 3000 + d


def test_non_integer_cr_is_refused():
    with pytest.raises(TypeError):
        R.delta(1500.0, 1500, True)


def test_gap_beyond_the_window_still_settles():   # §4.2 nearest-member fallback; rating.py raised here
    assert R.delta(1800, 1500, True) == 8 and R.delta(1500, 1800, True) == 24
    assert not R.within_window(1800, 1500) and R.within_window(1700, 1500)


def test_steady_rates():
    assert R.steady_rate(0) == 0.5
    assert R.steady_rate(24) == 0.5
    assert R.steady_rate(25) == 17 / 32
    assert R.steady_rate(175) == 23 / 32
    assert R.steady_rate(176) == 0.75
    assert R.steady_rate(-25) == 15 / 32
    for d in range(0, 176):                         # expected change is zero at the steady rate
        p = R.steady_rate(d)
        assert abs(p * R.delta(1500 + d, 1500, True) + (1 - p) * R.delta(1500 + d, 1500, False)) < 1e-12


def test_pp_to_cr_is_8():
    assert R.pp_to_cr(1) == 8 and R.pp_to_cr(3.125) == 25


def test_match_weight_and_removal():
    mu = 1500
    assert R.match_weight(1300, mu) == 1.0          # exactly mu - 200
    assert R.match_weight(1250, mu) == pytest.approx(0.6)
    assert R.match_weight(1200, mu) == pytest.approx(0.2)
    assert R.match_weight(1100, mu) == pytest.approx(0.2)
    assert R.to_remove(1200, mu, protected=False) and not R.to_remove(1201, mu, protected=False)
    assert not R.to_remove(1100, mu, protected=True)
    assert R.effective_weight(1200, mu, protected=True) == 1.0
