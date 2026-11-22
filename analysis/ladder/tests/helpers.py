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


class AppendsIllegal(_Base):
    """Adds a move of its own to the list it was handed and plays it: still illegal (LD-37)."""
    def act(self, pos, actions):
        from svsim.core.actions import Attack
        bogus = Attack(9999, 9998)
        actions.append(bogus)
        return bogus


class ReturnsArray(_Base):
    """Returns an object whose comparison raises: illegal, not a void (LD-37)."""
    def act(self, pos, actions):
        import numpy as np
        return np.array([0, 1])


class OddMessage(Crash):
    """Crashes with a message holding the characters str.splitlines() breaks at (LD-37)."""
    def act(self, pos, actions):
        self.n += 1
        if self.n == 2:
            raise ValueError("x\u2028y\u2029z\x85w")
        return actions[0]


class Rewrites(_Base):
    """Rewrites a move it was handed in place through its __init__ (frozen dataclasses allow that) and plays it: it
    holds only a copy, so this is an illegal move, not the referee's own object changed (11-22 fourth pass)."""
    def act(self, pos, actions):
        import dataclasses
        for a in actions:
            fs = dataclasses.fields(a)
            if fs and isinstance(getattr(a, fs[0].name), int):
                vals = [getattr(a, f.name) for f in fs]
                vals[0] = 10 ** 6
                a.__init__(*vals)
                return a
        return actions[0]


class HostCtrlC(_Base):
    """Stands in for the host pressing Ctrl+C while this side thinks: a real SIGINT to its own process (ignored in
    the runner's workers)."""
    def act(self, pos, actions):
        import signal
        signal.raise_signal(signal.SIGINT)
        return actions[0]


class _Hang:
    def __eq__(self, other):
        while True:
            time.sleep(0.05)

    __hash__ = object.__hash__


class HangsWhenJudged(_Base):
    """Returns a move of the right type whose field never finishes comparing: a timeout (fourth pass)."""
    def act(self, pos, actions):
        import dataclasses
        for a in actions:
            fs = dataclasses.fields(a)
            if fs:
                vals = [getattr(a, f.name) for f in fs]
                vals[0] = _Hang()
                return type(a)(*vals)
        return actions[0]


class Surrogate(Crash):
    """Crashes with a lone surrogate in its message (no UTF-8 file can hold one): the log still gets written."""
    def act(self, pos, actions):
        self.n += 1
        if self.n == 2:
            raise ValueError("lost anyway \ud800")
        return actions[0]
