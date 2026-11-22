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


class HangsInGuess(Random):
    """Plays at random, then never finishes its end-of-game guess: a timeout for its side, not a stalled run (LD-40)."""
    def guess(self, pos):
        time.sleep(600)


class HangsOnLoad(Random):
    """Never finishes being built: the game is void after the load clock, not a stalled run (LD-40)."""
    def __init__(self, seed=0):
        time.sleep(600)


class ChangesCards(Random):
    """On its first decision rewrites the shared definitions of the cards in its hand (cost 0) and plays on: the
    runner voids the game and replaces the worker (LD-40)."""
    done = False

    def act(self, pos, actions):
        if not self.done:
            self.done = True
            for c in pos.state.players[pos.me].hand:
                object.__setattr__(c.defn, "cost", 0)
        return super().act(pos, actions)


class PatchesScripts(Random):
    """Adds a member to the scripts' base class on its first decision (harmless here, but every later game in the
    process would inherit it): void, worker replaced (LD-40)."""
    def act(self, pos, actions):
        from svsim.core.script import CardScript
        CardScript.patched_by_a_strategy = True
        return super().act(pos, actions)


def task(t, beat=None):
    """A runner.guarded_map task for the tests: t is "ok", "hang", "change", "die" or "raise"."""
    import os
    if t == "hang":
        beat[0], beat[1] = 1, time.monotonic_ns()
        time.sleep(600)
    if t == "change":
        from svsim.cards.pool import POOL
        d = next(iter(POOL.values()))
        object.__setattr__(d, "cost", d.cost + 1)
    if t == "die":
        os._exit(3)
    if t == "raise":
        raise ValueError("task failed")
    from svsim.cards.pool import POOL
    return {"t": t, "pid": os.getpid(), "costs": sum(d.cost for d in POOL.values())}


class ChangesUntilGuess(Random):
    """Lets both sides evolve from their first turn (the engine's own rule table, changed in place) and evolves
    whenever it can; puts the table back in its end-of-game guess: nothing outlasts the game, so the worker's
    tripwire can't see it; ladder/audit.py's replay does (LD-40)."""
    def __init__(self, seed=0):
        super().__init__(seed)
        self.kept = None

    def act(self, pos, actions):
        from svsim.core import engine
        if self.kept is None:
            self.kept = dict(engine.EVOLVE_TURN)
            for k in engine.EVOLVE_TURN:
                engine.EVOLVE_TURN[k] = 0
        evolve = [a for a in actions if type(a).__name__ == "Evolve"]
        return evolve[0] if evolve else super().act(pos, actions)

    def guess(self, pos):
        from svsim.core import engine
        if self.kept is not None:
            engine.EVOLVE_TURN.update(self.kept)
        return super().guess(pos)
