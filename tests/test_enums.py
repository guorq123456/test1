"""Keyword's table-driven & and | return exactly what IntFlag's own operators return."""
from enum import IntFlag

from svsim.core.enums import Keyword


def test_keyword_and_or_are_intflags_own_for_every_pair_and_plain_ints():
    flags = list(range(1 << 9))
    for a in flags:
        A = Keyword(a)
        for b in flags:
            B = Keyword(b)
            assert (A & B) is IntFlag.__and__(A, B)
            assert (A | B) is IntFlag.__or__(A, B)
        assert (A & 3) is IntFlag.__and__(A, 3) and (3 & A) is IntFlag.__rand__(A, 3)
        assert (A & -2) is IntFlag.__and__(A, -2)
        assert (A | 1024) == IntFlag.__or__(A, 1024)
    assert (Keyword.WARD & ~Keyword.WARD) is Keyword.NONE
    assert bool(Keyword.WARD | Keyword.RUSH) and not (Keyword.STORM & Keyword.RUSH)


def test_determinizes_shuffle_is_the_librarys():
    import random
    from svsim.core import view
    assert view._INLINE                                   # on this Python the written-out shuffle is used
    for seed in range(300):
        a, b = random.Random(seed), random.Random(seed)
        xs, ys = list(range(seed % 61)), list(range(seed % 61))
        a.shuffle(xs)
        view.shuffle(b, ys)
        assert xs == ys and a.getstate() == b.getstate()
