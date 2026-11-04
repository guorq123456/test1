"""A pure speed-up changes no behaviour: the fixed-seed games of tests/golden_search.py replay to the same actions,
iterations and root children (visits and values, bit for bit) as the frozen record."""
import json

import pytest

from golden_search import GAMES, GOLDEN, play


@pytest.mark.parametrize("deck,opponent,seed,limit", GAMES)
def test_the_search_plays_and_counts_as_frozen(deck, opponent, seed, limit):
    want = json.loads(GOLDEN.read_text())[f"{deck}|{opponent}|{seed}"]
    got = play(deck, opponent, seed, limit)
    for i, (g, w) in enumerate(zip(got, want)):
        assert g == w, f"decision {i} of {deck} vs {opponent} (seed {seed}) differs"
    assert len(got) == len(want)
