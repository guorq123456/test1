"""The simulator's state in a worker process, before and after a game (fifth pass LD-40, sixth pass LD-41).

A runner worker plays one game after another, often of different players. Strategy code runs in that process, so it
could change things every later game there inherits: the shared card definitions (LD-40's finding: `pos.state` hands
out the pool's own CardDef objects), the card scripts and the engine's registries, the default bot's weights and
caches, a function's code, a class's name. The submission check's code reader (ladder/codecheck.py) refuses the ways it
can see; this is the second line: the worker warms up (one unlogged game that loads what games load,
runner._warm_up), empties the caches, takes a snapshot, and before every game empties the caches again and after it
compares. A change voids that game and ends the worker (the runner starts a new one).

What is followed, from every loaded module of svsim and ladder (and builtins): each global; the members of every
class defined there, and its name, qualified name and bases; for functions, their code, defaults, closure cells and
names; the items of dicts, lists and tuples; the attributes (and slots) of instances of svsim and ladder classes,
such as the CardDefs, the scripts and the bots' weights; set contents. Breadth first, each object once, a few levels
deep. Objects are compared by identity (the snapshot holds them, so an id can't be reused), sets by value, and a
dict, list or set that gained or lost an item has changed: the registries (scripts, listener sets, the card pool)
are filled when the modules load, before the snapshot.

The caches are the exception: CACHES (memo dicts the search fills and some clear at a size limit) and every
functools.lru_cache found are held by identity only and emptied before every game (reset_caches). They are pure
memos (phase 1's decision replays in fresh processes matched games played in long-lived workers), so emptying them
changes nothing but speed, and nothing one game leaves in them reaches the next. A dict found to grow in play that
isn't listed here would show up as a void "added" — a false alarm to fix by listing it, after reading its code.

What it doesn't see: a change made and undone inside one game (ladder/audit.py replays every game of a period before
it advances: it sees a change to the rules, not one to a bot's search), the inside of objects it doesn't follow
(numpy arrays, enum members), and other processes. It is a tripwire, not a sandbox (PHASE2-DESIGN: rules, prompt,
spot checks).
"""
from __future__ import annotations

import enum
import functools
import sys
import types
from itertools import repeat
from operator import attrgetter, is_

ROOTS = ("svsim", "ladder")
DEPTH = 6                                          # POOL -> CardDef -> its faith CardDef -> ... is 4
CACHES = (                                         # module, global: pure memo dicts, emptied before every game
    ("svsim.search.evaluate", "_REPLAY"), ("svsim.search.evaluate", "_BOUNCES"), ("svsim.search.evaluate", "_BURN"),
    ("svsim.search.evaluate", "_SCALED"), ("svsim.search.mcts", "_PAYOFF"), ("svsim.search.race", "_RAMPS"),
    ("svsim.search.moves", "_FINISHERS"), ("svsim.search.moves", "_ENHANCE"), ("svsim.search.formula", "_NEXT"),
    ("svsim.search.combo", "_DISCARD_CLASSES"), ("svsim.search.combo", "_EOT_CLASSES"),
    ("svsim.search.combo", "_NEXT_TURN"), ("svsim.search.xprune", "_DISCARDS"), ("svsim.agents.mulligan", "_DECK_KEYS"),
    ("svsim.core.state", "_SHARED"),
)
_ENUM_CACHES = ("_value2member_map_", "_unhashable_values_")    # Flag keeps its composite members here


def _watched(name) -> bool:
    return isinstance(name, str) and (name in ROOTS or name.startswith(tuple(r + "." for r in ROOTS)))


def _ours(obj) -> bool:
    return _watched((getattr(type(obj), "__module__", None) or "").split(".")[0])


def _cell(c):
    try:
        return c.cell_contents
    except ValueError:                             # an empty cell
        return GONE


GONE = object()


def _members(obj):
    """The (name, value) pairs of `obj` to follow, or None for an object whose inside isn't followed. Dicts are read
    through dict's own methods, so a subclass's overrides never run here."""
    if isinstance(obj, types.FunctionType):
        out = [("__code__", obj.__code__), ("__defaults__", obj.__defaults__),
               ("__kwdefaults__", obj.__kwdefaults__), ("__dict__", obj.__dict__), ("__name__", obj.__name__),
               ("__qualname__", obj.__qualname__)]
        if obj.__closure__:
            out += [(("cell", i), _cell(c)) for i, c in enumerate(obj.__closure__)]
        return out
    if isinstance(obj, (staticmethod, classmethod)):
        return [("__func__", obj.__func__)]
    if isinstance(obj, property):
        return [("fget", obj.fget), ("fset", obj.fset), ("fdel", obj.fdel)]
    if isinstance(obj, type):
        if not _watched(obj.__module__):
            return None
        own = [(k, v) for k, v in vars(obj).items() if not (isinstance(obj, enum.EnumType) and k in _ENUM_CACHES)]
        return own + [(("type", "__name__"), obj.__name__), (("type", "__qualname__"), obj.__qualname__),
                      (("type", "__bases__"), obj.__bases__)]
    if isinstance(obj, dict):
        return list(dict.items(obj))
    if isinstance(obj, (list, tuple)):
        return list(enumerate(list.__iter__(obj) if isinstance(obj, list) else tuple.__iter__(obj)))
    if isinstance(obj, (types.ModuleType, enum.Enum, functools._lru_cache_wrapper)):
        return None                                # modules are entered from the top; an enum member's value is
        #                                            itself (members cache attributes as they're used)
    if _ours(obj):
        out = [("__class__", type(obj))]
        d = getattr(obj, "__dict__", None)
        if isinstance(d, dict):
            out += [(("attr", k), v) for k, v in dict.items(d)]
        for cls in type(obj).__mro__:
            slots = cls.__dict__.get("__slots__", ())
            for s in (slots,) if isinstance(slots, str) else slots:
                if s not in ("__dict__", "__weakref__"):
                    out.append((("slot", s), getattr(obj, s, GONE)))
        return out
    return None


class Snapshot:
    """`records`: one per followed object: [object, how, keys, values, path, read, size] (values compared by
    identity; size: how many members it had, where one more or fewer is a change); `sets`: [set, frozenset copy,
    path]; `modules`: name -> module, for every watched module loaded; `lru`: the lru caches found."""

    def __init__(self):
        self.records, self.sets, self.modules, self.held, self.lru = [], [], {}, [], []
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
    n = len(keys)
    if how in ("dict", "moddict"):
        return lambda o: tuple(map(dict.get, repeat(o, n), keys, repeat(GONE, n)))
    if how == "class":
        def read_class(o):
            v = vars(o)
            return tuple(getattr(o, k[1], GONE) if isinstance(k, tuple) and k[0] == "type" else v.get(k, GONE)
                         for k in keys)
        return read_class
    if how in ("list", "tuple"):
        def read_seq(o):
            items = list(list.__iter__(o) if how == "list" else tuple.__iter__(o))[:n]
            return tuple(items) + (GONE,) * (n - len(items))
        return read_seq
    getters = []
    for k in keys:
        if k == "__class__":
            getters.append(type)
        elif isinstance(k, tuple) and k[0] == "cell":
            getters.append(lambda o, i=k[1]: _cell(o.__closure__[i]))
        elif isinstance(k, tuple) and k[0] == "attr":
            getters.append(lambda o, a=k[1]: dict.get(o.__dict__, a, GONE))
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
    """How many members the object has now (None: a function, whose members are fixed)."""
    if how == "class":
        return len(vars(obj))
    if how in ("moddict", "dict"):
        return dict.__len__(obj)
    if how == "list":
        return list.__len__(obj)
    if how == "inst":
        d = getattr(obj, "__dict__", None)
        return dict.__len__(d) if isinstance(d, dict) else 0
    return None


def _caches() -> set:
    out = set()
    for mod, name in CACHES:
        d = getattr(sys.modules.get(mod), name, None)
        if isinstance(d, dict):
            out.add(id(d))
    return out


def snapshot() -> Snapshot:
    import builtins
    s = Snapshot()
    queue, seen = [], set(_caches())               # the caches: held by identity (their global), never followed
    mods = sorted((n, m) for n, m in list(sys.modules.items()) if _watched(n) and m is not None)
    for name, m in mods + [("builtins", builtins)]:
        s.modules[name] = m
        d = getattr(m, "__dict__", None)
        if not isinstance(d, dict) or id(d) in seen:
            continue
        seen.add(id(d))
        keys = list(dict.keys(d))
        _record(s, d, "moddict", keys, name)
        if name != "builtins":
            queue += [(dict.get(d, k), f"{name}.{k}", 1) for k in keys]
    i = 0
    while i < len(queue):
        obj, path, depth = queue[i]
        i += 1
        if id(obj) in seen or depth > DEPTH:
            continue
        seen.add(id(obj))
        s.held.append(obj)                         # keeps every followed object alive, so ids stay unique
        if isinstance(obj, functools._lru_cache_wrapper):
            s.lru.append(obj)
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
        sep = "[{}]" if how in ("dict", "list", "tuple") else ".{}"
        queue += [(v, path + sep.format(_short(k, 40)), depth + 1) for k, v in members]
    return s


def _record(s: Snapshot, obj, how, keys, path):
    read = _reader(obj, how, keys)
    s.records.append([obj, how, keys, read(obj), path, read, _size(obj, how)])


def reset_caches(snap: Snapshot | None = None) -> None:
    """Empty the memo caches (before every game, and before the snapshot): nothing one game leaves there reaches
    the next. `snap` adds the lru caches it found."""
    for mod, name in CACHES:
        d = getattr(sys.modules.get(mod), name, None)
        if isinstance(d, dict):
            dict.clear(d)
    for f in (snap.lru if snap is not None else ()):
        f.cache_clear()


def changes(snap: Snapshot, limit: int = 5) -> list[str]:
    """What changed since `snap` was taken (at most `limit` lines), or []. Allowed: a module global that was None
    getting its value (a lazy one; the snapshot is then taken again), a package getting a submodule, the caches.
    Anything else is a change: a global, a class member or name or base, an instance attribute or slot, a function's
    code, defaults, closure or name, an item of a dict, list or set replaced, removed or added, a member added to a
    class or an instance."""
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
                known = set(keys)
                for k in [k for k in dict.keys(obj) if k not in known]:
                    v = dict.get(obj, k)
                    if type(v) is types.ModuleType and v.__name__ == f"{path}.{k}" and \
                            sys.modules.get(v.__name__) is v:
                        continue                   # a package's submodule, imported during the game
                    if say(f"{path}: {_short(k)} added"):
                        return out
            elif say(f"{path}: {_size(obj, how) - size:+d} members"):
                return out
    for obj, fs, path in snap.sets:
        if fs != obj:
            if say(f"{path}: set changed"):
                return out
    return out


def _short(k, limit=80) -> str:
    """A key as text, without running a strategy's code: repr only for plain host values."""
    if type(k) in (str, int, float, bool, type(None)) or (type(k) is tuple and all(
            type(x) in (str, int, float, bool, type(None)) for x in k)):
        r = repr(k)
    else:
        r = f"<{type(k).__name__}>"
    return r if len(r) <= limit else r[:limit] + "…"


# --- for a worker that plays one task after another ---------------------------------------------------------------

PRELOAD = ("svsim.cards.library", "svsim.cards.demo", "svsim.cards.decks", "svsim.core.engine", "svsim.core.actions",
           "svsim.tools.arena", "ladder.base", "ladder.deal", "ladder.interface", "ladder.strategy", "ladder.runner")


def preload():
    """What games load, loaded before the warm-up and the first snapshot (so the snapshot follows it from the start);
    runner._warm_up then plays one game, which loads the rest and sets the lazy globals."""
    import importlib
    for m in PRELOAD:
        importlib.import_module(m)


def stale(snap: Snapshot) -> bool:
    """True if the snapshot should be taken again after a clean task: a watched module was loaded since, or a lazy
    global got its value (so what it holds is followed from now on)."""
    return snap.relaxed or any(_watched(n) and m is not None and n not in snap.modules
                               for n, m in list(sys.modules.items()))
