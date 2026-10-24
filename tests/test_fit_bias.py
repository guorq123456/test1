"""learn.fit.fit's intercept column (2026-10-09): with feature sets appended after "bias", the fit must be told where
the bias is, or the last appended feature takes its place and the intercept is lost."""
import numpy as np


def _data(seed=0, n=3000):
    rng = np.random.default_rng(seed)
    a, b = rng.normal(size=n), rng.normal(2.0, 3.0, size=n)
    p = 1 / (1 + np.exp(-(1.2 + 0.8 * a + 0.3 * b)))           # an intercept well away from 0
    y = (rng.uniform(size=n) < p).astype(float)
    return np.column_stack([a, np.ones(n)]), b, y                # [feature, bias] + an extra to append


def test_without_extras_the_fit_is_as_before():
    from svsim.learn.fit import fit
    X, _, y = _data()
    w0, m0, s0, _ = fit(X, y, None, iters=300)
    w1, m1, s1, _ = fit(X, y, None, iters=300, bias=X.shape[1] - 1)
    assert np.array_equal(w0, w1) and np.array_equal(m0, m1) and np.array_equal(s0, s1)


def test_an_extra_after_bias_keeps_the_intercept_when_bias_is_given():
    from svsim.learn.fit import fit
    X, b, y = _data()
    Xe = np.column_stack([X, b])                                 # the extra after bias, as learn.phased lays it out
    lost, ml, sl, rl = fit(Xe, y, None, iters=2000)              # the old way: the last column taken for the bias
    kept, mk, sk, rk = fit(Xe, y, None, iters=2000, bias=1)
    assert lost[1] == 0.0 and ml[1] == 1.0 and sl[2] == 1.0      # the intercept gone, the extra not standardized
    assert kept[1] > 0.5 and mk[1] == 0.0 and sk[1] == 1.0 and abs(sk[2] - b.std()) < 1e-9
    base = fit(X, y, None, iters=2000)[3]
    assert rk["loss"] <= base["loss"] + 1e-9                     # nested: the extra can't make the fit worse
