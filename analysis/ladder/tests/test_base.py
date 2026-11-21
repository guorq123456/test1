"""The non-peeking core (phase 1, item 1.2): a public position holds no secret, samples are consistent with it, and
a strategy's decisions don't move when only secrets change (the plan's 偷看检查, first form).
Seeds: 99001000-99001999 (phase-0/1 host probe bank, SEEDS.md)."""
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from ladder import base  # noqa: E402
from ladder.strategy import BotStrategy, play  # noqa: E402
from svsim.agents.greedy_agent import GreedyAgent  # noqa: E402
from svsim.cards.decks import from_hash  # noqa: E402
from svsim.cards.pool import collectible  # noqa: E402
from svsim.core.engine import legal_actions  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
LINES = [l.strip().split("|") for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(encoding="utf-8")
         .splitlines() if l.strip() and not l.startswith("#")]
DECKS = [from_hash(c) for _, c in LINES]


class Greedy:
    """A cheap strategy behind the base (to reach many positions fast)."""
    def __init__(self, seed):
        self.agent, self.rng = GreedyAgent(seed=seed), random.Random(seed)

    def guess(self, pos):
        return base.default_guess(pos.opp_craft)

    def act(self, pos, actions):
        s, _ = base.sample(pos, self.guess(pos), self.rng)
        return self.agent.act(s, legal_actions(s))


def positions(pairs=((1, 4), (0, 3), (2, 6), (5, 1)), seed=99001000, every=3):
    """Real positions along refereed greedy games: (state, seat, tracker) snapshots."""
    out = []
    for g, (a, b) in enumerate(pairs):
        seen = []

        def keep(state, seat, tracker, pos, action, seen=seen):
            if len(seen) % every == 0:
                import copy
                t = copy.deepcopy(tracker)
                seen.append((state.clone(), seat, t))
            else:
                seen.append(None)
        play(DECKS[a], DECKS[b], [Greedy(seed + 10 * g), Greedy(seed + 10 * g + 1)], seed=seed + g, on_decision=keep)
        out += [x for x in seen if x is not None]
    return out


POS = positions()


def test_enough_positions():
    assert len(POS) > 40


@pytest.mark.parametrize("i", range(0, 60, 3))
def test_public_position_holds_no_secret(i):
    state, seat, tracker = POS[i % len(POS)]
    rng = random.Random(i)
    want = base.fingerprint(base.public_position(state, seat, tracker))
    craft = tracker.crafts[1 - seat]
    others = [c.card_id for c in collectible(craft)] if hasattr(collectible(craft)[0], "card_id") else None
    for k in range(3):
        varied = base.vary_secrets(state, seat, tracker, rng, replacements=others if k else None)
        assert base.fingerprint(base.public_position(varied, seat, tracker)) == want


@pytest.mark.parametrize("i", range(1, 60, 4))
def test_samples_agree_with_the_real_position(i):
    state, seat, tracker = POS[i % len(POS)]
    pos = base.public_position(state, seat, tracker)
    opp = 1 - seat
    real_actions = legal_actions(state)
    for k in range(5):
        s, info = base.sample(pos, base.default_guess(pos.opp_craft), random.Random(k))
        assert len(s.players[opp].hand) == len(state.players[opp].hand)
        assert len(s.players[opp].deck_view()) == len(state.players[opp].deck_view())
        assert Counter(c.defn.card_id for c in s.players[seat].deck_view()) == \
            Counter(c.defn.card_id for c in state.players[seat].deck_view())
        assert [c.uid for c in s.players[seat].hand] == [c.uid for c in state.players[seat].hand]
        assert s.players[opp].deck_name == ""
        if state.active == seat:
            assert set(legal_actions(s)) == set(real_actions)


def test_tracker_counts_add_up():
    for state, seat, tracker in POS[::5]:
        opp = 1 - seat
        pos = base.public_position(state, seat, tracker)
        # every starting card is either seen (revealed) or still unknown in the hand / deck
        assert sum(pos.opp_revealed.values()) + pos.opp_unknown_hand + pos.opp_unknown_deck == 40


def test_posterior_and_out_of_guess():
    a, b = tuple([1] * 3 + [2] * 37), tuple([3] * 3 + [2] * 37)
    w = base.posterior([(a, 1.0), (b, 1.0)], Counter({1: 1}))
    assert w[0] > 0.9
    assert base.out_of_guess([(a, 1.0)], Counter({1: 4, 9: 1})) == 2


@pytest.mark.parametrize("i", range(2, 40, 6))
def test_the_default_strategy_doesnt_move_when_secrets_change(i):
    """Same internal seed, a real position vs. one with different secrets: the same decision."""
    state, seat, tracker = POS[i % len(POS)]
    if state.active != seat:
        pytest.skip("not this seat's move")
    rng = random.Random(1000 + i)
    varied = base.vary_secrets(state, seat, tracker, rng)
    acts = [BotStrategy(seed=4242).act(base.public_position(s, seat, tracker), legal_actions(s))
            for s in (state, varied)]
    assert acts[0] == acts[1]
