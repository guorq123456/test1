"""The validation games (learn.setnet.in_valid; the architecture thread 2026-10-19 16:53Z). "key", the default, is
every earlier net's split; "hash" picks the same share of games with no tie to g's parity, so to the seat."""
import numpy as np
import pytest

from svsim.learn.setnet import in_valid


def _keys(seeds, games=1000):
    s = np.repeat(np.asarray(seeds, np.int64), games)
    g = np.tile(np.arange(games, dtype=np.int64), len(seeds))
    return s, g, s * 100003 + g


def test_key_is_the_old_split_and_picks_one_parity_of_g():
    s, g, k = _keys([79100000 + 2 * i for i in range(10)])
    assert np.array_equal(in_valid(k), k % 20 == 0) and np.array_equal(in_valid(k, 20, "key"), k % 20 == 0)
    assert len(set((g[in_valid(k)] % 2).tolist())) == 1           # even seeds: one seat only


def test_hash_picks_about_one_in_twenty_with_both_seats():
    s, g, k = _keys([79100000 + 2 * i for i in range(10)])
    v = in_valid(k, 20, "hash")
    assert 400 <= v.sum() <= 600                                    # 10 000 games, 500 expected
    share = (g[v] % 2 == 0).mean()
    assert 0.4 < share < 0.6
    assert np.array_equal(v, in_valid(k.copy(), 20, "hash"))        # a function of the key only
    for i in range(10):                                             # every shard has some
        assert v[s == 79100000 + 2 * i].sum() > 20


def test_an_unknown_split_is_refused():
    with pytest.raises(ValueError):
        in_valid(np.arange(5), 20, "seat")
