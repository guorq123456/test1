"""What each player can see, and sampling the hidden rest.

Search on hidden information works on determinized states: copies where the
unknown cards (opponent's hand and deck, own deck order) are reshuffled into
one possible arrangement. This assumes the observer knows the opponent's
decklist, as when training against fixed decks.
"""
import random

from .state import CardInstance, GameState


def _card(c: CardInstance) -> dict:
    info = {"uid": c.uid, "name": c.defn.name, "cost": c.cost}
    if c.defn.is_follower:
        info.update(atk=c.atk, life=c.life, evolved=c.evolved, super_evolved=c.super_evolved,
                    keywords=str(c.keywords))
    if c.countdown is not None:
        info["countdown"] = c.countdown
    if c.counters:
        info["counters"] = dict(c.counters)
    return info


def observe(state: GameState, player: int) -> dict:
    me, opp = state.players[player], state.players[1 - player]
    side = lambda p: {"leader_hp": p.leader_hp, "leader_max_hp": p.leader_max_hp,
                      "damage_cap": p.damage_cap, "pp": p.pp, "max_pp": p.max_pp, "ep": p.ep,
                      "sep": p.sep, "deck": len(p.deck), "shadows": p.shadows,
                      "field": [_card(c) for c in p.field],
                      "leader_area": [_card(c) for c in p.leader_area]}
    return {"turn": state.turn, "active": state.active, "you": player,
            "me": {**side(me), "hand": [_card(c) for c in me.hand]},
            "opponent": {**side(opp), "hand": len(opp.hand)}}


def _inline_shuffle(rng: random.Random, x: list) -> None:
    """random.Random.shuffle written out around getrandbits (the same draws, the same permutation), without its
    two method calls per swap; determinize shuffles two decks every search iteration."""
    getrandbits = rng.getrandbits
    for i in range(len(x) - 1, 0, -1):
        n = i + 1
        k = n.bit_length()
        r = getrandbits(k)
        while r >= n:
            r = getrandbits(k)
        x[i], x[r] = x[r], x[i]


def _inline_agrees() -> bool:
    """Whether _inline_shuffle is this Python's shuffle (checked once at import; else the library's is used)."""
    for seed in range(40):
        a, b = random.Random(seed), random.Random(seed)
        xs, ys = list(range(seed % 37)), list(range(seed % 37))
        a.shuffle(xs)
        _inline_shuffle(b, ys)
        if xs != ys or a.getstate() != b.getstate():
            return False
    return True


_INLINE = _inline_agrees()


def shuffle(rng: random.Random, x: list) -> None:
    """rng.shuffle(x), faster for a plain random.Random."""
    if _INLINE and type(rng) is random.Random:
        _inline_shuffle(rng, x)
    else:
        rng.shuffle(x)


def determinize(state: GameState, player: int, rng: random.Random, weights: dict | None = None,
                oracle: bool = False) -> GameState:
    """One guess at what `player` can't see. With `weights` ({uid: weight}, 1 if absent; search.infer), the
    opponent's hand is drawn by weight without replacement (Efraimidis-Spirakis keys) instead of uniformly. With
    `oracle` (an experiment: what knowing it is worth) the opponent's hand is their real one and only their deck's
    order is guessed."""
    s = state.clone(copy_rng=False)     # seeded below: nothing of the real generator is kept
    me, opp = s.players[player], s.players[1 - player]
    shuffle(rng, me.deck)
    if oracle:
        shuffle(rng, opp.deck)
        s.rng.seed(rng.getrandbits(64))
        return s
    pool = opp.hand + opp.deck
    if weights:
        keys = [rng.random() ** (1.0 / weights.get(c.uid, 1.0)) for c in pool]
        pool = [c for _, c in sorted(zip(keys, pool), key=lambda kc: -kc[0])]
    else:
        shuffle(rng, pool)
    opp.hand, opp.deck = pool[:len(opp.hand)], pool[len(opp.hand):]
    s.rng.seed(rng.getrandbits(64))   # future random effects are unknown too
    return s
