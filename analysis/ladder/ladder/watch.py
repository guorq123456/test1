"""The simulator's state in a worker process, before and after a game (fifth pass, LD-40).

A runner worker plays one game after another, often of different players. Strategy code runs in that process, so it
could change things every later game there inherits: the shared card definitions (LD-40's finding: `pos.state` hands
out the pool's own CardDef objects), the card scripts, the default bot's weights, a function's code. submit.check_code
refuses the plain ways to do that; this is the second line: a snapshot of what later games read, taken when the worker
starts and compared after every game. A change voids that game and ends the worker (the runner starts a new one).

What is followed, from every loaded module of svsim and ladder (and builtins): each global; the members of every
class defined there; for functions, their code, defaults and closure cells; the items of dicts, lists and tuples;
the attributes (and slots) of instances of svsim and ladder classes, such as the CardDefs, the scripts and the bots'
weights; set contents. Breadth first, each object once, a few levels deep. Objects are compared by identity (the
snapshot holds them, so an id can't be reused), sets by value.

What it doesn't see: a change made and undone inside one game (that game's moves won't replay in a clean process:
ladder/audit.py replays every game of a period before it advances), the inside of objects it doesn't follow (numpy
arrays, caches), and other processes. It is a tripwire, not a sandbox (PHASE2-DESIGN: rules, prompt, spot checks).
"""
from __future__ import annotations

import enum
import sys
import types
from itertools import repeat
from operator import attrgetter, is_

ROOTS = ("svsim", "ladder")
DEPTH = 6                                          # POOL -> CardDef -> its faith CardDef -> ... is 4


def _watched(name) -> bool:
    return isinstance(name, str) and (name in ROOTS or name.startswith(tuple(r + "." for r in ROOTS)))


def _ours(obj) -> bool:
    return _watched((getattr(type(obj), "__module__", None) or "").split(".")[0])


def _cell(c):
    try:
        return c.cell_contents
    except ValueError:                             # an empty cell
        return _EMPTY_CELL


_EMPTY_CELL = object()


def _members(obj):
    """The (name, value) pairs of `obj` to follow, or None for an object whose inside isn't followed."""
    if isinstance(obj, types.FunctionType):
        out = [("__code__", obj.__code__), ("__defaults__", obj.__defaults__),
               ("__kwdefaults__", obj.__kwdefaults__), ("__dict__", obj.__dict__)]
        if obj.__closure__:
            out += [(("cell", i), _cell(c)) for i, c in enumerate(obj.__closure__)]
        return out
    if isinstance(obj, (staticmethod, classmethod)):
        return [("__func__", obj.__func__)]
    if isinstance(obj, property):
        return [("fget", obj.fget), ("fset", obj.fset), ("fdel", obj.fdel)]
    if isinstance(obj, type):
        return list(vars(obj).items()) if _watched(obj.__module__) else None
    if isinstance(obj, dict):
        return list(obj.items())
    if isinstance(obj, (list, tuple)):
        return list(enumerate(obj))
    if isinstance(obj, types.ModuleType):
        return None                                # modules are entered from the top only
    if isinstance(obj, enum.Enum):
        return None                                # a member caches attributes as it is used (Flag's _KW pseudo-
        #                                            members): its value is its identity
    if _ours(obj):
        out = [("__class__", type(obj))]
        d = getattr(obj, "__dict__", None)
        if isinstance(d, dict):
            out += [(("attr", k), v) for k, v in d.items()]
        for cls in type(obj).__mro__:
            slots = cls.__dict__.get("__slots__", ())
            for s in (slots,) if isinstance(slots, str) else slots:
                if s not in ("__dict__", "__weakref__"):
                    out.append((("slot", s), getattr(obj, s, _EMPTY_CELL)))
        return out
    return None


class Snapshot:
    """`records`: one per followed object: [object, how, keys, values, path, read, size] (values compared by
    identity; size: how many members it had, where a new one counts as a change);
    `sets`: [set, frozenset copy, path]; `modules`: name -> module, for every watched module loaded."""

    def __init__(self):
        self.records, self.sets, self.modules, self.held = [], [], {}, []
        self.relaxed = False                       # a lazy global was let through (see changes)


def _how(obj) -> str:
    if isinstance(obj, types.FunctionType):
        return "func"
    if isinstance(obj, type):
        return "class"
    if isinstance(obj, dict):
        return "dict"
    if isinstance(obj, list):
        return "list"
    if isinstance(obj, tuple):
        return "tuple"
    return "inst"


def _reader(obj, how, keys):
    """A function giving the values of `keys` in `obj` now, as one tuple (GONE for a missing one)."""
    if how in ("dict", "moddict"):
        return lambda o: tuple(map(o.get, keys, repeat(GONE, len(keys))))
    if how == "class":
        return lambda o: tuple(map(vars(o).get, keys, repeat(GONE, len(keys))))
    if how in ("list", "tuple"):
        n = len(keys)
        return lambda o: tuple(o[:n]) + (GONE,) * (n - len(o)) if len(o) < n else tuple(o[:n])
    getters = []
    for k in keys:
        if k == "__class__":
            getters.append(type)
        elif isinstance(k, tuple) and k[0] == "cell":
            getters.append(lambda o, i=k[1]: _cell(o.__closure__[i]))
        elif isinstance(k, tuple) and k[0] == "attr":
            getters.append(lambda o, a=k[1]: o.__dict__.get(a, GONE))
        elif isinstance(k, tuple) and k[0] == "slot":
            getters.append(lambda o, a=k[1]: getattr(o, a, GONE))
        else:
            getters.append(lambda o, a=k: getattr(o, a, GONE))
    plain = [k for k in keys if isinstance(k, tuple) and k[0] == "slot"]
    if plain and len(plain) == len(keys) - 1 and keys[0] == "__class__":     # the common case: a slotted object
        ag = attrgetter(*(k[1] for k in plain))
        one = len(plain) == 1

        def fast(o):
            try:
                v = ag(o)
            except AttributeError:
                return (type(o),) + tuple(g(o) for g in getters[1:])
            return (type(o), v) if one else (type(o),) + v
        return fast
    return lambda o: tuple(g(o) for g in getters)


def _size(obj, how):
    """How many members the object has now (for a new one: a class, an instance's __dict__, a module's globals)."""
    if how == "class":
        return len(vars(obj))
    if how == "moddict":
        return len(obj)
    if how == "inst":
        d = getattr(obj, "__dict__", None)
        return len(d) if isinstance(d, dict) else 0
    return None


def snapshot() -> Snapshot:
    import builtins
    s = Snapshot()
    queue, seen = [], set()
    mods = sorted((n, m) for n, m in list(sys.modules.items()) if _watched(n) and m is not None)
    for name, m in mods + [("builtins", builtins)]:
        s.modules[name] = m
        d = getattr(m, "__dict__", None)
        if not isinstance(d, dict) or id(d) in seen:
            continue
        seen.add(id(d))
        keys = list(d)
        _record(s, d, "moddict", keys, name)
        if name != "builtins":
            queue += [(d[k], f"{name}.{k}", 1) for k in keys]
    i = 0
    while i < len(queue):
        obj, path, depth = queue[i]
        i += 1
        if id(obj) in seen or depth > DEPTH:
            continue
        seen.add(id(obj))
        s.held.append(obj)                         # keeps every followed object alive, so ids stay unique
        if isinstance(obj, (set, frozenset)):
            s.sets.append([obj, frozenset(obj), path])
            continue
        try:
            members = _members(obj)
        except Exception:                          # an object that won't show its inside is held by identity only
            members = None
        if members is None:
            continue
        how = _how(obj)
        keys = [k for k, _ in members]
        if how != "tuple":                         # a tuple can't change; what it holds is followed below
            _record(s, obj, how, keys, path)
        sep = "[{!r}]" if how in ("dict", "list", "tuple") else ".{}"
        queue += [(v, path + sep.format(k), depth + 1) for k, v in members]
    return s


def _record(s: Snapshot, obj, how, keys, path):
    read = _reader(obj, how, keys)
    s.records.append([obj, how, keys, read(obj), path, read, _size(obj, how)])


def changes(snap: Snapshot, limit: int = 5) -> list[str]:
    """What changed since `snap` was taken (at most `limit` lines), or []. Allowed: new items in a dict, list or
    set (the simulator's caches, scripts registered by a module loaded during the game), a module global that
    was None getting its value (a lazy one), a package getting a submodule. Anything else is a change: a global, a
    class member, an instance attribute or slot, a function's code, defaults or closure, an item of a dict or list
    replaced or removed, a member added to a class or an instance, an item gone from a set."""
    out = []

    def say(line):
        out.append(line)
        return len(out) >= limit

    for name, m in snap.modules.items():
        if sys.modules.get(name, m) is not m:
            if say(f"module {name} replaced"):
                return out
    for rec in snap.records:
        obj, how, keys, before, path, read, size = rec
        try:
            now = read(obj)
        except Exception as e:                     # noqa: BLE001
            if say(f"{path}: unreadable now ({type(e).__name__})"):
                return out
            continue
        if not all(map(is_, now, before)):
            lazy = []
            for k, a, b in zip(keys, now, before):
                if a is b:
                    continue
                if how == "moddict" and b is None and a is not GONE:
                    lazy.append(k)                 # a lazy global set for the first time
                    continue
                if say(f"{path}: {_short(k)} {'removed' if a is GONE else 'changed'}"):
                    return out
            if lazy and len(lazy) == sum(a is not b for a, b in zip(now, before)):
                rec[3] = now                       # from now on its value is the one to keep
                snap.relaxed = True
        if size is not None and _size(obj, how) != size:
            if how == "moddict":
                for k in [k for k in obj if k not in set(keys)]:
                    v = obj[k]
                    if isinstance(v, types.ModuleType) and v.__name__ == f"{path}.{k}" and \
                            sys.modules.get(v.__name__) is v:
                        continue                   # a package's submodule, imported during the game
                    if say(f"{path}: {_short(k)} added"):
                        return out
            elif say(f"{path}: {_size(obj, how) - size:+d} members"):
                return out
    for _, (obj, fs, path) in enumerate(snap.sets):
        if not fs <= obj:
            if say(f"{path}: items gone from the set"):
                return out
    return out


def _short(k, limit=80) -> str:
    try:
        r = repr(k)
    except Exception:                              # noqa: BLE001
        r = f"<{type(k).__name__}>"
    return r if len(r) <= limit else r[:limit] + "…"


GONE = _EMPTY_CELL


# --- for a worker that plays one task after another ---------------------------------------------------------------

PRELOAD = ("svsim.cards.library", "svsim.core.engine", "svsim.core.actions", "ladder.base", "ladder.deal",
           "ladder.runner")


def preload():
    """What every game loads, loaded before the first snapshot (so the snapshot follows it from the start)."""
    import importlib
    for m in PRELOAD:
        importlib.import_module(m)


def stale(snap: Snapshot) -> bool:
    """True if the snapshot should be taken again after a clean task: a watched module was loaded since, or a lazy
    global got its value (so what it holds is followed from now on)."""
    return snap.relaxed or any(_watched(n) and m is not None and n not in snap.modules
                               for n, m in list(sys.modules.items()))
