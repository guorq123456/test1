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
    """A runner.guarded_map task for the tests: t is "ok", "hang", "linger", "change", "die" or "raise"."""
    import os
    if t == "hang":
        beat[0], beat[1] = 1, time.monotonic_ns()
        time.sleep(600)
    if t == "linger":                                   # stuck with no clock on (LD-42)
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


class GrowsRegistry(Random):
    """Adds a card id to the engine's hand-listener registry on its first decision (a set the card scripts fill when
    they load; a module global, never rebound): void, worker replaced (LD-41)."""
    def act(self, pos, actions):
        from svsim.core import script
        script.LISTEN_IN_HAND.add(987654321)
        return super().act(pos, actions)


class RenamesAMove(Random):
    """Renames a move class (type(a).__name__ is how some code tells moves apart): void, worker replaced (LD-41)."""
    def act(self, pos, actions):
        from svsim.core.actions import Evolve
        Evolve.__name__ = "Evolved"
        return super().act(pos, actions)



class PatchesRandom(Random):
    """Wraps random.Random.shuffle on its first decision: the same shuffle in a different function (the deal and the
    search shuffle with it), so the game plays as it would; it outlasts the game: void, worker replaced (LD-42)."""
    def act(self, pos, actions):
        import random
        if not getattr(random.Random.shuffle, "wrapped_by_a_strategy", False):
            inner = random.Random.shuffle

            def shuffle(rng, x):
                return inner(rng, x)
            shuffle.wrapped_by_a_strategy = True
            random.Random.shuffle = shuffle
        return super().act(pos, actions)


class CopiesPosition(Random):
    """Copies what it is given every decision (copy.copy / deepcopy of the position, a ChainMap, a UserDict): allowed,
    and changes nothing shared; CPython caches __slotnames__ in each class copied for the first time (LD-43: the
    tripwire took that for a change and voided every game)."""
    def act(self, pos, actions):
        import collections
        import copy
        copy.deepcopy(pos)
        copy.copy(pos)
        copy.deepcopy(collections.ChainMap({"n": len(actions)}, {}))
        copy.deepcopy(collections.UserDict({"n": 1}))
        return super().act(pos, actions)

class CopiesIterators(Random):
    """Copies itertools objects every decision (copy.copy, a deepcopy holding one, dataclasses.asdict over one): allowed;
    Python 3.12+ warns from copy.py while doing it (ignored by the filters), and CPython keeps a __warningregistry__ in
    the copy module from then on (LD-44: the tripwire took that for a change and voided every game)."""
    def act(self, pos, actions):
        import copy
        import dataclasses
        import itertools

        @dataclasses.dataclass
        class Book:
            ids: object = dataclasses.field(default_factory=itertools.count)
        copy.copy(itertools.cycle(range(3)))
        copy.deepcopy({"ids": itertools.count(), "seen": []})
        dataclasses.asdict(Book())
        return super().act(pos, actions)


class ChecksProtocols(Random):
    """isinstance against a runtime-checkable Protocol and typing.SupportsInt, functools.cache over a host class, and
    statistics: allowed; CPython stores an empty __annotations__ in each host class the first time it is read (LD-45:
    the tripwire took that for a change and voided every game)."""
    def act(self, pos, actions):
        import functools
        import statistics
        import typing

        @typing.runtime_checkable
        class Targeted(typing.Protocol):
            target: int
        n = sum(1 for a in actions if isinstance(a, Targeted)) + sum(1 for a in actions if isinstance(a, typing.SupportsInt))
        isinstance(self, Targeted)
        functools.cache(type(actions[0]))
        statistics.mean([n, 1.5])
        return super().act(pos, actions)


class RegistersAbc(Random):
    """Registers a class of its own as a virtual subclass of collections.abc.Sequence: the code reader refuses .register
    on anything but an own singledispatch function (LD-46: typing.Hashable.register(list) changed isinstance for every
    later game in the worker); the tripwire sees the ABC registry's counter move and voids the game."""
    def act(self, pos, actions):
        import collections.abc

        class Mine:
            pass
        collections.abc.Sequence.register(Mine)
        return super().act(pos, actions)


class UsesNumpy(Random):
    """numpy the allowed way: arrays, its own Generator, linalg, errstate. Nothing process-wide changes (LD-46: the
    tripwire follows numpy's error, buffer and print settings and its global RandomState, and the ABC counter)."""
    def __init__(self, seed=0):
        super().__init__(seed)
        import numpy
        self.g = numpy.random.default_rng(seed)

    def act(self, pos, actions):
        import numpy
        p = self.g.random(len(actions)) + numpy.linalg.norm(numpy.ones(2))
        with numpy.errstate(all="ignore"):
            p = p + numpy.float64(1.0) / numpy.float64(0.0) * 0
        return actions[int(numpy.argmax(numpy.nan_to_num(p)))]


def _lingering(n):
    try:
        yield n
    finally:                                            # runs when the generator is freed: after the game
        time.sleep(600)


class Lingers(Random):
    """Keeps a started generator whose finally never ends; it runs when the strategy is freed after the game, off
    every clock (the code reader refuses a yield inside a try, LD-42): the idle watchdog voids the game, replaces the
    worker, and the next game plays."""
    def __init__(self, seed=0):
        super().__init__(seed)
        self.left = _lingering(1)
        next(self.left)
