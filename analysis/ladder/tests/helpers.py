"""Test-only strategies for the runner's checks (never used in a real pool)."""
import random
import time

from ladder import base


class _Base:
    def __init__(self, seed=0):
        self.rng = random.Random(seed)

    def guess(self, pos):
        return base.default_guess(pos.opp_craft)


class Random(_Base):
    def act(self, pos, actions):
        return actions[self.rng.randrange(len(actions))]


class Crash(_Base):
    """Raises on its third decision."""
    def __init__(self, seed=0):
        super().__init__(seed)
        self.n = 0

    def act(self, pos, actions):
        self.n += 1
        if self.n == 3:
            raise ValueError("boom")
        return actions[0]


class Illegal(_Base):
    def act(self, pos, actions):
        from svsim.core.actions import Attack
        return Attack(9999, 9998)


class Slow(_Base):
    """Sleeps far past any step limit on its second decision."""
    def __init__(self, seed=0):
        super().__init__(seed)
        self.n = 0

    def act(self, pos, actions):
        self.n += 1
        if self.n == 2:
            time.sleep(600)
        return actions[0]


class Quits(_Base):
    """Ends its process the polite way (SystemExit) on its third decision: a crash, not a dead worker (LD-36)."""
    def __init__(self, seed=0):
        super().__init__(seed)
        self.n = 0

    def act(self, pos, actions):
        self.n += 1
        if self.n == 3:
            raise SystemExit(3)
        return actions[0]


class Interrupts(Quits):
    def act(self, pos, actions):
        if self.n == 1:
            raise KeyboardInterrupt
        return super().act(pos, actions)


class QuitsInGuess(Random):
    """Plays on, then raises SystemExit when asked for its guess at the end: the game's result stands."""
    def guess(self, pos):
        raise SystemExit(4)
