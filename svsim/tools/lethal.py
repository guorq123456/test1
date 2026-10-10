"""Lethal search on real games: benchmark it, pit the lethal agent against
random play, or collect lethal puzzles to practise on.

    python -m svsim.tools.lethal bench   --games 30                # how often, how fast
    python -m svsim.tools.lethal bench   --games 30 --screen 200   # ... with damage screening
    python -m svsim.tools.lethal match   --games 400               # LethalAgent vs RandomAgent
    python -m svsim.tools.lethal puzzles --count 5 --out puzzles.jsonl

Positions come from random self-play (Pirate Sword vs Ramp Dragon by default,
--decks random for random decks of every craft), taken at the start of each
turn after the draw. A puzzle is a sure lethal that needs more than attacking
the leader with everything: at least --min-len actions, found by random play at
most --max-random of the time, one per game. Each saved puzzle has
the decks, seed and actions to rebuild the position (see `replay`).
"""
import argparse
from collections import Counter
import json
import random
import time

from svsim.agents.lethal_agent import LethalAgent
from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks, library
from svsim.cards.pool import card
from svsim.core.actions import Attack, from_dict, to_dict
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Craft, Phase
from svsim.search.lethal import LethalSearch
from svsim.ui.text import describe_line, render_state

assert library.__all__        # every craft module registers its scripts
CRAFTS = [c for c in Craft if c != Craft.NEUTRAL]


def deck_pair(kind: str, g: int, rng: random.Random) -> tuple[list, list]:
    if kind == "starter":
        pirate, ramp = decks.build(decks.PIRATE_SWORD), decks.build(decks.RAMP_DRAGON)
        return (pirate, ramp) if g % 2 == 0 else (ramp, pirate)
    return decks.random_deck(rng.choice(CRAFTS), rng), decks.random_deck(rng.choice(CRAFTS), rng)


def turn_starts(kind: str, games: int, seed: int = 0):
    """Random games; yields (state, record) at each turn's first decision, where
    `record` rebuilds the position. The caller must not change `state`."""
    rng = random.Random(seed)
    for g in range(games):
        d0, d1 = deck_pair(kind, g, rng)
        state = new_game(d0, d1, seed=seed + g)
        agents = [RandomAgent(2 * g, 0.2), RandomAgent(2 * g + 1, 0.2)]
        history, last = [], None
        while not state.over:
            if state.phase == Phase.MAIN and state.turn != last:
                last = state.turn
                yield state, {"decks": [[c.card_id for c in d0], [c.card_id for c in d1]],
                              "seed": seed + g, "history": [to_dict(a) for a in history]}
            action = agents[state.active].act(state, legal_actions(state))
            apply(state, action)
            history.append(action)


def replay(record: dict):
    """Rebuild a saved position."""
    d0, d1 = ([card(i) for i in ids] for ids in record["decks"])
    state = new_game(d0, d1, seed=record["seed"])
    for a in record["history"]:
        apply(state, from_dict(a))
    return state


def face_only_wins(state) -> bool:
    """Does attacking the leader with every follower that can (strongest first) win?"""
    s, me = state.clone(), state.active
    while not s.over:
        face = [a for a in legal_actions(s) if isinstance(a, Attack) and a.target < 0]
        if not face:
            break
        apply(s, max(face, key=lambda a: s.on_field(a.attacker).atk))
    return s.winner == me


def random_conversion(state, rollouts: int = 20, seed: int = 0) -> float:
    """How often random play (RandomAgent, end_turn_weight 0.2) wins this turn from
    here: a rough difficulty for a lethal (low = easy to miss)."""
    me, wins = state.active, 0
    for i in range(rollouts):
        s, agent = state.clone(), RandomAgent(seed + i, 0.2)
        while not s.over and s.active == me:
            apply(s, agent.act(s, legal_actions(s)))
        wins += s.winner == me
    return wins / rollouts


def bench(args) -> None:
    search = LethalSearch(max_nodes=args.budget, screen=args.screen)
    stats, times, converted = Counter(), [], []
    screened = 0
    for state, _ in turn_starts(args.decks, args.games, args.seed):
        r = search.solve(state)
        times.append(r.seconds)
        stats["sure" if r.sure else "chance" if r.probability > 0 else "none"] += 1
        stats["incomplete"] += not r.complete
        screened += r.screened
        if r.sure:
            converted.append(random_conversion(state))
    times.sort()
    n = len(times)
    print(f"{n} positions: sure lethal {stats['sure']}, lethal only with luck {stats['chance']}, "
          f"none {stats['none']}; budget ran out {stats['incomplete']}")
    print(f"time per position: median {times[n // 2] * 1000:.0f} ms, "
          f"95% {times[int(n * 0.95)] * 1000:.0f} ms, max {times[-1]:.1f} s, total {sum(times):.0f} s"
          + (f"; {screened} screened to a quick search" if args.screen else ""))
    if converted:
        print(f"random play wins {sum(converted) / len(converted):.0%} of the sure lethals "
              f"(averaged over {len(converted)} positions, 20 tries each)")


def match(args) -> None:
    wins, start, lethal_agents = Counter(), time.perf_counter(), []
    rng = random.Random(args.seed)
    for g in range(args.games):
        d0, d1 = deck_pair(args.decks, g, rng)
        smart = g % 2                       # alternate seats
        agents = [RandomAgent(2 * g, 0.2), RandomAgent(2 * g + 1, 0.2)]
        agents[smart] = LethalAgent(agents[smart], max_nodes=args.budget, screen=args.screen, seed=g)
        lethal_agents.append(agents[smart])
        winner = play_game(new_game(d0, d1, seed=args.seed + g), agents)
        wins["lethal agent" if winner == smart else "random" if winner in (0, 1) else "draw"] += 1
    elapsed = time.perf_counter() - start
    print(f"{args.games} games in {elapsed:.0f}s: LethalAgent {wins['lethal agent']}, "
          f"RandomAgent {wins['random']}, draws {wins['draw']} "
          f"({wins['lethal agent'] / args.games:.1%} for the lethal agent)")
    print(f"sure lethals found and played: {sum(a.lethals for a in lethal_agents)}")


def puzzles(args) -> None:
    search = LethalSearch(max_nodes=args.budget)
    found, out, used = 0, open(args.out, "w", encoding="utf-8") if args.out else None, set()
    for state, record in turn_starts(args.decks, args.games, args.seed):
        if record["seed"] in used:            # one puzzle per game
            continue
        r = search.solve(state)
        if not r.sure or len(r.line) < args.min_len or face_only_wins(state):
            continue
        rate = random_conversion(state)
        if rate > args.max_random:
            continue
        found += 1
        used.add(record["seed"])
        steps = describe_line(state, r.line)
        text = (render_state(state) + f"\n（随机打法 20 次里打出 {round(rate * 20)} 次）\n答案：\n"
                + "\n".join(f"  {i}. {s}" for i, s in enumerate(steps, 1)))
        print(f"=== 斩杀题 {found} ===\n{text}\n")
        if out:
            record.update(line=[to_dict(a) for a in r.line], random_wins=rate, text=text)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
        if found >= args.count:
            break
    if out:
        out.close()
    print(f"{found} puzzles")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name, budget in (("bench", 2000), ("match", 2000), ("puzzles", 20000)):
        p = sub.add_parser(name)
        p.add_argument("--games", type=int, default={"bench": 30, "match": 400, "puzzles": 500}[name])
        p.add_argument("--decks", choices=("starter", "random"), default="starter")
        p.add_argument("--budget", type=int, default=budget, help="search nodes per position")
        p.add_argument("--seed", type=int, default=0)
        if name != "puzzles":
            p.add_argument("--screen", type=int, default=200 if name == "match" else None,
                           help="quick-search budget when the damage estimate falls short "
                                "(see search.lethal); 0 or less turns screening off")
        if name == "puzzles":
            p.add_argument("--count", type=int, default=5)
            p.add_argument("--min-len", type=int, default=3)
            p.add_argument("--max-random", type=float, default=0.25,
                           help="skip lethals random play finds more often than this")
            p.add_argument("--out", help="save puzzles as JSON lines")
    args = parser.parse_args()
    if getattr(args, "screen", None) is not None and args.screen <= 0:
        args.screen = None
    {"bench": bench, "match": match, "puzzles": puzzles}[args.command](args)


if __name__ == "__main__":
    main()
