"""300 random games per class with decks built around the set 10 cards (each set 10 card of
the class x3, the rest random scripted class/Neutral cards), against a random Rotation deck of
a random class. Invariants checked after every action (tests/test_fuzz.check_invariants).
Run from the worktree root: python games.py <craft> <n>"""
import random, sys, time
sys.path[:0] = [".", "tests"]
from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks, library  # noqa: F401  (registers every script)
from svsim.cards.pool import POOL, collectible
from svsim.core.enums import Craft
from svsim.core.engine import new_game
from svsim.core.script import has_script
from test_fuzz import check_invariants

CRAFTS = {"rune": Craft.RUNE, "abyss": Craft.ABYSS, "haven": Craft.HAVEN, "portal": Craft.PORTAL}


def s10_deck(craft, rng):
    new = [c for c in collectible(craft) if c.card_set == 10010 and c.craft == craft]
    deck = [c for c in new for _ in range(3)]
    options = [c for c in collectible(craft) if c.card_set != 10010 and not (c.has_ability and not has_script(c.card_id))]
    while len(deck) < 40:
        c = rng.choice(options)
        if deck.count(c) < 3:
            deck.append(c)
    return deck, len(new)


def main(name, n):
    craft = CRAFTS[name]
    others = [c for c in Craft if c not in (Craft.NEUTRAL,) and c.name in ("FOREST", "SWORD", "RUNE", "DRAGON", "ABYSS", "HAVEN", "PORTAL")]
    rng = random.Random(10010)
    t0, results, lengths = time.time(), [], []
    for g in range(n):
        mine, k = s10_deck(craft, rng)
        foe = decks.random_deck(rng.choice(others), rng)
        d0, d1 = (mine, foe) if g % 2 == 0 else (foe, mine)
        state = new_game(d0, d1, seed=10010_000 + g)
        agents = [RandomAgent(2 * g, end_turn_weight=0.2), RandomAgent(2 * g + 1, end_turn_weight=0.2)]
        w = play_game(state, agents, on_action=check_invariants)
        assert w in (0, 1, -1) and state.over
        results.append(w)
        lengths.append(state.turn)
    print(f"{name}: {n} games, {k} set-10 cards x3 per deck, no crash; winners 0/1/draw = "
          f"{results.count(0)}/{results.count(1)}/{results.count(-1)}; mean length {sum(lengths)/n:.1f} turns; {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
