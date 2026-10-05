"""Runtime coverage: which card-script hooks fire during random self-play.

    python -m svsim.tools.coverage --games 1000

A hook that never fires is either unreachable with these decks or wired wrong;
look at it either way. Rarely firing hooks deserve a dedicated test.
"""
import argparse
from collections import Counter

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks
from svsim.core.engine import new_game
from svsim.core.script import HOOKS, script_for


def instrument(card_defs) -> tuple[Counter, set]:
    """Wrap every hook of these cards' scripts with a counter."""
    fired, expected = Counter(), set()
    for defn in card_defs:
        script = script_for(defn.card_id)
        for hook in HOOKS:
            method = getattr(script, hook)
            key = (type(script).__name__, hook)
            if method is None or key in expected:
                continue
            expected.add(key)

            def counted(ctx, method=method, key=key):
                fired[key] += 1
                return method(ctx)
            setattr(script, hook, counted)
    return fired, expected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    fired, expected = instrument(decks.KNOWN.values())
    pirate, ramp = decks.build(decks.PIRATE_SWORD), decks.build(decks.RAMP_DRAGON)
    for g in range(args.games):
        d0, d1 = (pirate, ramp) if g % 2 == 0 else (ramp, pirate)
        play_game(new_game(d0, d1, seed=args.seed + g),
                  [RandomAgent(2 * g, end_turn_weight=0.15), RandomAgent(2 * g + 1, end_turn_weight=0.15)])
    never = sorted(expected - set(fired))
    print(f"{len(expected)} script hooks, {len(expected) - len(never)} fired in {args.games} games")
    for name, hook in never:
        print(f"  never fired: {name}.{hook}")
    print("least fired:", ", ".join(f"{name}.{hook} x{n}"
                                    for (name, hook), n in sorted(fired.items(), key=lambda kv: kv[1])[:5]))


if __name__ == "__main__":
    main()
