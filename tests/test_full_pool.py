"""The whole Rotation pool: every card with abilities has a script, and random
decks of every craft play against each other without breaking invariants."""
import random

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks, library
from svsim.cards.pool import POOL, ROTATION_IDS, collectible
from svsim.core.engine import new_game
from svsim.core.enums import Craft

from test_fuzz import check_invariants

CRAFTS = [c for c in Craft if c != Craft.NEUTRAL]
assert library.__all__


def test_every_card_with_abilities_has_a_script():
    missing = decks.unimplemented(POOL[i] for i in ROTATION_IDS)
    assert missing == [], [f"{c.card_id} {c.name}" for c in missing[:20]]


def test_rotation_pool_size():
    assert len(collectible()) == 516
    assert all(len([c for c in collectible(k) if c.craft == k]) in (67, 68) for k in CRAFTS)


def test_random_decks_of_every_craft_play_each_other():
    rng = random.Random(0)
    for g in range(14 * 10):
        a, b = CRAFTS[g % 7], CRAFTS[(g // 7) % 7]
        d0, d1 = decks.random_deck(a, rng), decks.random_deck(b, rng)
        assert decks.validate(d0) == [] and decks.validate(d1) == []
        state = new_game(d0, d1, seed=g)
        agents = [RandomAgent(2 * g, end_turn_weight=0.2), RandomAgent(2 * g + 1, end_turn_weight=0.2)]
        assert play_game(state, agents, on_action=check_invariants) in (0, 1, -1)
