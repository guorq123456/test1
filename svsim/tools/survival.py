"""Learn how long followers stay on the field against an opponent (Chinese output).

    python -m svsim.tools.survival <games folder or files> --deck rhino --opponent ramp
    python -m svsim.tools.survival --play 40 --deck rhino --opponent ramp

Counts, from the games, how often each side's followers survive the other
side's turns, by the turn and the follower's defense (svsim.learn.survival),
prints the tables and saves them to svsim/learn/survival/<deck>-<opponent>.json
and <opponent>-<deck>.json, where the race clock finds them. `--play N` adds N
games of the AI against itself (the deck played by `--spec`, the opponent by
`--opponent-spec`), so no player games are needed.
"""
from __future__ import annotations

import argparse
from multiprocessing import Pool

from svsim.learn.survival import LIVES, TURNS, collect
from svsim.ui.session import DECKS


def play(job) -> dict:
    """One game of the AI against itself, as a record."""
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools import records as R
    from svsim.tools.arena import make_agent
    g, seed, deck, opponent, spec, opponent_spec = job
    seat = g % 2
    cards, specs = [None, None], [None, None]
    cards[seat], cards[1 - seat] = decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1])
    specs[seat], specs[1 - seat] = spec, opponent_spec
    agents = [make_agent(s, seed * 1000 + g * 2 + i) for i, s in enumerate(specs)]
    state = new_game(cards[0], cards[1], seed=seed * 100003 + g)
    record = R.new_record(cards[0], cards[1], seed * 100003 + g, state.first, f"{specs[0]} / {specs[1]}")
    while not state.over:
        action = agents[state.active].act(state, legal_actions(state))
        R.add(record, action)
        apply(state, action)
    record["winner"] = state.winner
    return record


def report(s, say=print) -> None:
    say(f"{DECKS[s.deck][0]} 的随从，对 {DECKS[s.opponent][0]}（{s.games} 局）："
        f"对手第几回合过后还活着（活下来 / 场上有），以及时钟用的存活率")
    say("  对手回合  " + "  ".join(f"{l}{'+' if l == LIVES else ' '}血".rjust(13) for l in range(1, LIVES + 1)))
    for t in range(1, TURNS + 1):
        cells = [f"{s.kept[t][l]:>2}/{s.seen[t][l]:<2} {s.chance(t, l):4.0%}" for l in range(1, LIVES + 1)]
        say(f"  第{t:>2}回合" + ("+" if t == TURNS else " ") + "  ".join(c.rjust(14) for c in cells))


def main() -> None:
    from svsim.tools.timing import load_games
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("games", nargs="*", help="game records (folders or files)")
    parser.add_argument("--deck", default="rhino")
    parser.add_argument("--opponent", default="ramp")
    parser.add_argument("--play", type=int, default=0, help="AI games to add")
    parser.add_argument("--spec", default="mcts:100+plan+reserve")
    parser.add_argument("--opponent-spec", default="mcts:200+plan+learned")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()
    records = load_games(args.games) if args.games else []
    if args.play:
        jobs = [(g, args.seed, args.deck, args.opponent, args.spec, args.opponent_spec) for g in range(args.play)]
        with Pool(args.workers) as pool:
            records += pool.map(play, jobs)
    for deck, opponent in ((args.deck, args.opponent), (args.opponent, args.deck)):
        s = collect(records, deck, opponent)
        report(s)
        if not args.no_save and s.games:
            print("已保存到", s.save())


if __name__ == "__main__":
    main()
