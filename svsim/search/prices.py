"""Shadow prices: resources valued by what they buy, not by fixed weights.

The player's way with evolution points and resources against Ramp Dragon
(2026-10-06, docs/architecture.md): every point is turned into play points or
a dead big follower (Mylo and Baby Carbuncle super-evolved: play points back,
and a super-evolved follower takes no damage on its own turn, so it kills the
big follower Ramp just played), the second super-evolution point waits for
the kill turn (Baby Carbuncle: 3 more play points, 3 more cards, +3 Combo for
every Rhinoceroach), and nothing is evolved just for its stats. The AI spent a
third of its points on stats alone (Fairies, Bayle), because the evaluation
prices an unused point at a fixed 1 (1.5 for super-evolution) while +2/+2 on
the field looks like more.

`Priced` is an evaluation that prices two things by what they buy instead:

- the player's followers on the field, at what is expected to be left of them
  after the opponent's turn: each follower's value times its chance to survive
  that turn (learn.survival, from the games of the matchup; no games, no
  discount). Stats the opponent will answer anyway are worth little;
- unused evolution points, at the damage they add to the player's next turn by
  the resource-flow planner (search.combo.next_turn_damage with and without
  the points), `per_damage` each, on top of the base weights. The next turn
  can use one evolution, so with two points left the first costs nothing
  extra and the last one costs what it adds to the burst: keep one for the
  kill turn, spend the other where it pays now.
"""
from __future__ import annotations

from svsim.search.evaluate import DEFAULT, Weights, evaluate, follower_value


class Priced:
    def __init__(self, base=None, survival: bool = True, points: bool = True, per_damage: float = 0.5,
                 nodes: int = 300, profiles: dict | None = None):
        self.base = base if base is not None else DEFAULT
        self.weights = self.base if isinstance(self.base, Weights) else DEFAULT
        self.survival = survival
        self.points = points
        self.per_damage = per_damage
        self.nodes = nodes
        if profiles is None and survival:
            from svsim.learn.survival import by_crafts
            profiles = by_crafts()
        self.profiles = profiles or {}
        self._profile: dict = {}

    def _survival(self, state, side: int):
        key = (id(state.players[side].deck), side)
        if key not in self._profile:
            from svsim.learn.model import deck_craft
            self._profile[key] = self.profiles.get((deck_craft(state, side), deck_craft(state, 1 - side)))
        return self._profile[key]

    def board_discount(self, state, side: int) -> float:
        """What `side`'s followers are expected to lose on the opponent's coming turn."""
        from svsim.learn.survival import own_turn
        profile = self._survival(state, side)
        if profile is None:
            return 0.0
        turn = own_turn(state, 1 - side, state.turn + 1 if state.active == side else state.turn)
        return sum((1.0 - profile.chance(turn, f.life)) * follower_value(f, self.weights)
                   for f in state.players[side].followers)

    def points_price(self, state, side: int) -> float:
        """Damage `side`'s unused evolution points add to its next turn (planner)."""
        from svsim.search.combo import next_turn_damage
        p = state.players[side]
        if not (p.ep or p.sep):
            return 0.0
        with_points = next_turn_damage(state, side, self.nodes)
        ep, sep = p.ep, p.sep
        p.ep = p.sep = 0
        try:
            without = next_turn_damage(state, side, self.nodes)
        finally:
            p.ep, p.sep = ep, sep
        return max(with_points - without, 0)

    def score(self, state, player: int, player_moves_next: bool = False) -> float:
        value = evaluate(state, player, self.base, player_moves_next)
        if state.winner is not None:
            return value
        if self.survival and not player_moves_next:
            value -= self.board_discount(state, player)
        if self.points:
            value += self.per_damage * self.points_price(state, player)
        return value
