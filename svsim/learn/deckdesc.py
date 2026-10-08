"""A deck described by what its cards do: a fixed-length vector pooled over its 40 cards, no card or deck ids.

For an evaluation shared by every pairing (learn.mlp --shared): the same network sees both decks' lists
through this vector, so it can tell a combo deck from a ramp deck by what the cards measure, not by
their names. Static: computed once from the list (cards.decks.NAMED through PlayerState.deck_name),
never from what has been drawn.

Parts, each a mean over the 40 cards unless said otherwise:
- the cost curve (share of cards at cost <= 1, 2, ..., 7, >= 8) and the mean cost;
- the card types (followers, spells, amulets) and the followers' mean attack and defense;
- keyword shares (ward, storm, rush, bane, drain, barrier) among the cards printed with them;
- learn.roles: each role's mean (face, removal, heal, draw, ramp, body) and the share of cards with it;
- learn.roles.recurring: what the cards do each round on the field (face, heal, clear);
- learn.payoff: the mean payoff of evolving and super-evolving, and the shares of payoff tier 1 and 2.
"""
from __future__ import annotations

COSTS = (1, 2, 3, 4, 5, 6, 7)
KEYWORDS = ("WARD", "STORM", "RUSH", "BANE", "DRAIN", "BARRIER")


def names() -> list[str]:
    from svsim.learn.roles import RECURRING, ROLES
    out = [f"cost_le{c}" for c in COSTS] + ["cost_ge8", "cost_mean", "followers", "spells", "amulets",
                                              "follower_atk", "follower_def"]
    out += [f"kw_{k.lower()}" for k in KEYWORDS]
    out += [f"role_{r}" for r in ROLES] + [f"has_{r}" for r in ROLES]
    out += [f"each_round_{r}" for r in RECURRING]
    out += ["evolve_payoff", "super_payoff", "payoff_tier1", "payoff_tier2"]
    return out


_CACHE: dict = {}


def describe(listing: dict) -> list[float]:
    """The vector for a deck list {CardDef: copies}."""
    key = tuple(sorted((d.card_id, n) for d, n in listing.items()))
    if key in _CACHE:
        return _CACHE[key]
    from svsim.core.enums import Keyword
    from svsim.learn import payoff as P
    from svsim.learn.roles import ROLES, card_roles, recurring
    cards = [d for d, n in listing.items() for _ in range(n)]
    total = float(len(cards)) or 1.0
    mean = lambda f: sum(f(d) for d in cards) / total            # noqa: E731
    followers = [d for d in cards if d.is_follower]
    out = [mean(lambda d, c=c: d.cost <= c) for c in COSTS] + [mean(lambda d: d.cost >= 8), mean(lambda d: d.cost)]
    out += [len(followers) / total, mean(lambda d: d.is_spell), mean(lambda d: d.is_amulet)]
    out += [sum(d.atk for d in followers) / (len(followers) or 1), sum(d.life for d in followers) / (len(followers) or 1)]
    out += [mean(lambda d, k=getattr(Keyword, k): bool(d.keywords & k)) for k in KEYWORDS]
    roles = {d.card_id: card_roles(d) for d in set(cards)}
    out += [mean(lambda d, i=i: roles[d.card_id][i]) for i in range(len(ROLES))]
    out += [mean(lambda d, i=i: roles[d.card_id][i] > 0) for i in range(len(ROLES))]
    each = {d.card_id: recurring(d) for d in set(cards)}
    out += [mean(lambda d, i=i: each[d.card_id][i]) for i in range(len(each[cards[0].card_id]))] if cards else [0.0] * 3
    tiers = {d.card_id: P.tier(d) if d.is_follower else 0 for d in set(cards)}
    out += [mean(lambda d: P.evolve_payoff(d) if d.is_follower else 0.0),
            mean(lambda d: P.evolve_payoff(d, True) if d.is_follower else 0.0),
            mean(lambda d: tiers[d.card_id] >= 1), mean(lambda d: tiers[d.card_id] >= 2)]
    out = [float(x) for x in out]
    assert len(out) == len(names())
    _CACHE[key] = out
    return out


def of_player(state, player: int) -> list[float]:
    """The vector of the deck `player` started with (zeros for a deck that isn't registered)."""
    from svsim.cards.decks import NAMED
    name = state.players[player].deck_name
    if name in NAMED:
        return describe(NAMED[name])
    return [0.0] * len(names())


def pair(state, me: int) -> list[float]:
    """Both decks' vectors, `me`'s first."""
    return of_player(state, me) + of_player(state, 1 - me)
