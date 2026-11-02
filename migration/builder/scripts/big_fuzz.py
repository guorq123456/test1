"""Cross-craft random fuzz with extra invariants: clone safety, uid uniqueness."""
import random, sys, traceback
from collections import Counter
from multiprocessing import Pool

sys.path.insert(0, "/home/user/test1")
sys.path.insert(0, "/home/user/test1/tests")
from svsim.agents.random_agent import RandomAgent
from svsim.cards import decks, library  # noqa
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Craft, Phase
from svsim.core.view import observe
from test_fuzz import check_invariants

CRAFTS = [c for c in Craft if c != Craft.NEUTRAL]
IMMUTABLE = (int, str, bool, float, tuple, type(None), frozenset)


def extra_invariants(state):
    uids = Counter()
    for p in state.players:
        for zone in (p.deck, p.hand, p.field, p.leader_area):
            for c in zone:
                uids[c.uid] += 1
                for k, v in (c.counters or {}).items():
                    if isinstance(v, list):
                        assert all(isinstance(x, IMMUTABLE) for x in v), (c, k, v)
                    else:
                        assert isinstance(v, IMMUTABLE), (c, k, v)
    dup = [u for u, n in uids.items() if n > 1]
    assert not dup, dup


def fingerprint(state):
    def card(c):
        return (c.uid, c.defn.card_id, c.cost, c.atk, c.life, c.max_life, int(c.keywords), c.countdown,
                c.evolved, c.attacks_made, repr(sorted((c.counters or {}).items())), len(c.grants or ()))
    return (state.turn, state.active, state.winner, state.rng.getstate(),
            tuple((p.leader_hp, p.leader_max_hp, p.pp, p.max_pp, p.ep, p.sep, p.shadows, p.rally,
                   tuple(map(card, p.deck)), tuple(map(card, p.hand)), tuple(map(card, p.field)),
                   tuple(map(card, p.leader_area)), tuple(d.card_id for d in p.destroyed),
                   tuple(sorted(p.entered.items())), p.extra_damage) for p in state.players))


def run(seed_range):
    fails, wins, n_actions = [], Counter(), 0
    for g in seed_range:
        rng = random.Random(g)
        a, b = rng.choice(CRAFTS), rng.choice(CRAFTS)
        try:
            d0, d1 = decks.random_deck(a, rng), decks.random_deck(b, rng)
        except ValueError as e:
            fails.append((g, "deck", str(e)))
            continue
        state = new_game(d0, d1, seed=g)
        agents = [RandomAgent(2 * g, 0.15), RandomAgent(2 * g + 1, 0.15)]
        history, last = [], None
        try:
            while state.phase != Phase.OVER and state.winner is None:
                acts = legal_actions(state)
                act = agents[state.active].act(state, acts)
                last = act
                twin = state.clone() if len(history) % 23 == 5 else None
                apply(state, act)
                if twin is not None:                     # clone safety: same action, same result
                    apply(twin, act)
                    assert fingerprint(twin) == fingerprint(state), act
                history.append(act)
                n_actions += 1
                check_invariants(state, act)
                extra_invariants(state)
            wins[(a, b)[state.winner].name if state.winner in (0, 1) else "draw"] += 1
        except Exception:
            fails.append((g, a.name, b.name, repr(last), traceback.format_exc()[-1500:]))
    return fails, wins, n_actions


if __name__ == "__main__":
    total = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    chunks = [range(start + i, start + total, 4) for i in range(4)]
    import time
    t = time.time()
    with Pool(4) as pool:
        results = pool.map(run, chunks)
    fails = [f for r in results for f in r[0]]
    wins = sum((r[1] for r in results), Counter())
    acts = sum(r[2] for r in results)
    print(f"{total} games, {acts} actions, {time.time() - t:.1f}s, failures {len(fails)}")
    print(dict(wins.most_common()))
    seen = set()
    for f in fails:
        key = f[-1].strip().splitlines()[-1] if len(f) > 3 else f[2]
        if key in seen:
            continue
        seen.add(key)
        print("=" * 60)
        print(*f[:4])
        print(f[-1])
