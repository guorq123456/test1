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
    return info


def observe(state: GameState, player: int) -> dict:
    me, opp = state.players[player], state.players[1 - player]
    side = lambda p: {"leader_hp": p.leader_hp, "pp": p.pp, "max_pp": p.max_pp, "ep": p.ep,
                      "sep": p.sep, "deck": len(p.deck), "shadows": p.shadows,
                      "field": [_card(c) for c in p.field]}
    return {"turn": state.turn, "active": state.active, "you": player,
            "me": {**side(me), "hand": [_card(c) for c in me.hand]},
            "opponent": {**side(opp), "hand": len(opp.hand)}}


def determinize(state: GameState, player: int, rng: random.Random) -> GameState:
    s = state.clone()
    me, opp = s.players[player], s.players[1 - player]
    rng.shuffle(me.deck)
    pool = opp.hand + opp.deck
    rng.shuffle(pool)
    opp.hand, opp.deck = pool[:len(opp.hand)], pool[len(opp.hand):]
    s.rng.seed(rng.getrandbits(64))   # future random effects are unknown too
    return s
