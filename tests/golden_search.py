"""The search's behaviour, frozen: fixed-seed games whose every decision is recorded as the action played, the
iterations searched, and the root's children (key, visits, value) bit for bit. A speed-up that changes nothing
leaves the record identical (tests/test_golden_search.py).

    python tests/golden_search.py write      # regenerate tests/data/golden_search.json (only when behaviour
                                             # is meant to change)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOLDEN = HERE / "data" / "golden_search.json"
SPEC = "mcts:30+plan+learned+phased"
# (deck, opponent, seed, decisions recorded): the original Ramp mirror and four tournament pairings, so the
# installed per-pairing models (extras included) are all on the path
GAMES = [("ramp", "ramp", 101, 60), ("ramp-t", "ramp-t", 102, 50), ("elf-t", "elf-t", 103, 50),
         ("elf-t", "ramp-t", 104, 50), ("nemesis-t", "pirate-t", 105, 40)]


def _search(agent):
    from svsim.tools.gate import _search as find
    return find(agent)


def play(deck: str, opponent: str, seed: int, limit: int) -> list:
    """The first `limit` decisions of one game, both seats played by SPEC (seeds 2 x seed, 2 x seed + 1)."""
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools.arena import make_agent
    from svsim.ui.session import DECKS
    agents = [make_agent(SPEC, 2 * seed), make_agent(SPEC, 2 * seed + 1)]
    searches = [_search(a) for a in agents]
    state = new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1]), seed=seed)
    out = []
    while not state.over and len(out) < limit:
        search = searches[state.active]
        search.last_root, search.last_iterations = None, None
        action = agents[state.active].act(state, legal_actions(state))
        root = search.last_root
        children = None if root is None else sorted(
            [repr(k), c.visits, repr(c.value)] for k, c in root.children.items())
        out.append({"seat": state.active, "action": repr(action), "iterations": search.last_iterations,
                    "children": children})
        apply(state, action)
    return out


def record() -> dict:
    return {f"{d}|{o}|{s}": play(d, o, s, n) for d, o, s, n in GAMES}


if __name__ == "__main__":
    if sys.argv[1:] == ["write"]:
        sys.path.insert(0, str(HERE.parent))
        GOLDEN.parent.mkdir(exist_ok=True)
        GOLDEN.write_text(json.dumps(record(), indent=0) + "\n")
        print(f"wrote {GOLDEN}")
