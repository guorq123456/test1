"""The simulator's state in a worker process, before and after a game (fifth pass LD-40, sixth LD-41, seventh LD-42;
LD-43, LD-44, LD-45, LD-46, LD-47, LD-49, LD-50).

A runner worker plays one game after another, often of different players. Strategy code runs in that process, so it
could change things every later game there inherits: the shared card definitions (LD-40's finding: `pos.state` hands
out the pool's own CardDef objects), the card scripts and the engine's registries, the default bot's weights and
caches, a function's code, a class's name. The submission check's code reader (ladder/codecheck.py) refuses the ways it
can see; this is the second line: the worker loads every module a game or a strategy may load (preload), warms up
(one unlogged game that sets the lazy globals, runner._warm_up), empties the caches, takes a snapshot, and before
every game empties the caches again and after it compares. A change voids that game and ends the worker (the runner
starts a new one).

What is followed, from every loaded module of svsim and ladder (and builtins), and of the standard modules a
strategy may import (STDLIB: random.Random's methods are what the deal and the search shuffle with) and of the ones
statistics works with (FOLLOWED: fractions, numbers, decimal; LD-45) and copyreg (LD-49): each global, and of the
standard ones their own classes and functions and (LD-49) their dicts, lists and sets but typing's caches
(copy.dispatch_table: a key added there made every later copy of a position in the worker fail);
the members of every class defined there, and its name, qualified name and bases; for functions, their code,
defaults, closure cells and names, and the function an lru_cache wraps; the items of dicts, lists and tuples; the
attributes (and slots) of instances of svsim and ladder classes, such as the CardDefs, the scripts and the bots'
weights, and of the dataclasses module's (a dataclass's Field objects: LD-46, @dataclass rewrote one taken from
dataclasses.fields(PlayCard)); set contents. And what no module global holds (_process_state, LD-46): the ABC
registry's counter (ABCMeta.register changes isinstance for the whole process) and, numpy being loaded first
(NUMPY_MODULES: it registers ABCs as it loads), its error, buffer and print settings and its global RandomState,
and (LD-47) the arrays and plain values numpy's modules and their classes hold (Polynomial.window, polyx, ...: an
array is compared by its bytes; np.copyto into one changed every later polynomial in the worker) and (LD-50) their
dicts, lists and sets by their items (np.sctypeDict), numpy's memo caches emptied before every game instead.
Breadth first, each object once, a few levels
deep. Objects are compared by identity (the snapshot holds them, so an id can't be reused), sets by value, and a
dict, list or set that gained or lost an item has changed: the registries (scripts, listener sets, the card pool)
are filled when the modules load, before the snapshot.

The caches are the exception: CACHES (memo dicts the search fills and some clear at a size limit) and every
functools.lru_cache found are held by identity only and emptied before every game (reset_caches). They are pure
memos (phase 1's decision replays in fresh processes matched games played in long-lived workers), so emptying them
changes nothing but speed, and nothing one game leaves in them reaches the next. Two more, for the host's trained
pilots only (svsim.learn is closed to strategies): CACHE_ATTRS, a net's memo and counter attributes, not compared;
GROWS, svsim.learn's module dicts and sets (models loaded once per process), which may gain items but not lose or
replace one, and are then snapshotted again. And one CPython cache: copy.copy / deepcopy store `__slotnames__` in a
class the first time one of its objects is copied; the snapshot fills it in every class it follows first (LD-43:
a strategy that copied its position voided every game). And `__annotations__`: the first read of it on a class that has none stores an empty dict in the class (a
runtime-checkable Protocol's isinstance and functools.cache(K) read it); the snapshot reads it first (LD-45). And
another: a module's `__warningregistry__`, which CPython
makes the first time a warning is charged to that module, even one the filters ignore (copying an itertools object
warns from copy.py); the snapshot makes an empty one in every module it follows (not builtins) and holds it by
identity only (LD-44: a strategy copying an itertools.cycle voided every game). A dict found to grow in play that
isn't listed here would show up as a void "added" — a false alarm to fix by listing it, after reading its code.

What it doesn't see: a change made and undone inside one game (ladder/audit.py replays every game of a period before
it advances: it sees a change to the rules, not one to a bot's search), the inside of objects it doesn't follow
(numpy arrays other than numpy's own, enum members), and other processes. It is a tripwire, not a sandbox (PHASE2-DESIGN: rules, prompt,
spot checks).
"""
from __future__ import annotations

import abc
import copyreg
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
CACHE_ATTRS = {                                    # (module, class): instance attributes not compared (LD-42): memos,
    ("svsim.learn.setnet", "SetNet"): frozenset({  # counters, and the rows a net adds for cards it meets in play.
        "_table", "_idx", "_pool", "_zone_sums", "_live_sums", "_live_hits", "_live_misses", "card_ids", "static"}),
}                                                  # Host-only (svsim.learn is closed to strategies): the pilots
GROWS = ("svsim.learn.",)                         # their module globals that are dicts or sets may gain items (the
#                                                    models loaded once per process, warnings given once), never lose
#                                                    or replace one; the snapshot is then taken again
STDLIB = ("random", "collections", "functools", "dataclasses", "heapq", "bisect", "statistics", "copy", "enum",
          "typing", "math", "cmath", "itertools")   # what strategies may import: its globals, and the members of the
#                                                    classes and functions defined there (LD-42: random.Random's)
FOLLOWED = ("fractions", "numbers", "decimal", "copyreg")   # not importable by strategies, but statistics works
#   with their classes (LD-45: changing fractions.Fraction broke later games); copy.dispatch_table is copyreg's (LD-49)
STD_CACHES = (("typing", "_caches"), ("typing", "_cleanups"), ("typing", "_overload_registry"))   # LD-49: typing's
#   own lru caches and the registry typing.overload fills: of the standard modules' dict, list and set globals the
#   only ones not compared


def _watched(name) -> bool:
    return isinstance(name, str) and (name in ROOTS or name.startswith(tuple(r + "." for r in ROOTS)))


def _ours(obj) -> bool:
    return _watched((getattr(type(obj), "__module__", None) or "").split(".")[0])


def _cache_attrs(cls) -> frozenset:
    return CACHE_ATTRS.get((getattr(cls, "__module__", None), getattr(cls, "__qualname__", None)), frozenset())


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
        if not (_watched(obj.__module__) or obj.__module__ in STDLIB + FOLLOWED):
            return None
        own = [(k, v) for k, v in vars(obj).items() if not (isinstance(obj, enum.EnumType) and k in _ENUM_CACHES)]
        return own + [(("type", "__name__"), obj.__name__), (("type", "__qualname__"), obj.__qualname__),
                      (("type", "__bases__"), obj.__bases__)]
    if isinstance(obj, dict):
        return list(dict.items(obj))
    if isinstance(obj, (list, tuple)):
        return list(enumerate(list.__iter__(obj) if isinstance(obj, list) else tuple.__iter__(obj)))
    if isinstance(obj, functools._lru_cache_wrapper):
        return [("__wrapped__", getattr(obj, "__wrapped__", GONE))]    # LD-42: the function under the cache
    if isinstance(obj, (types.ModuleType, enum.Enum)):
        return None                                # modules are entered from the top; an enum member's value is
        #                                            itself (members cache attributes as they're used)
    if _ours(obj) or getattr(type(obj), "__module__", None) == "dataclasses":   # LD-46: a dataclass's Field objects
        out = [("__class__", type(obj))]
        d = getattr(obj, "__dict__", None)
        skip = _cache_attrs(type(obj))
        if isinstance(d, dict):
            out += [(("attr", k), v) for k, v in dict.items(d) if k not in skip]
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
        self.records, self.sets, self.modules, self.held, self.lru, self.grows = [], [], {}, [], [], []
        self.relaxed = False                       # a lazy global was let through (see changes)
        self.process: dict = {}                    # the process-wide state no module global holds (LD-46)
        self.numpy_held, self.numpy_arrays = [], []   # numpy's own arrays and plain values (LD-47)


NUMPY_MODULES = ("numpy", "numpy.random", "numpy.linalg", "numpy.fft", "numpy.polynomial", "numpy.exceptions",
                 "numpy.dtypes", "numpy.typing")   # what strategies may import of numpy (LD-46; numpy.polynomial.* too)


NUMPY_CACHES = (("numpy", "finfo", "_finfo_cache"), ("numpy", "iinfo", "_min_vals"), ("numpy", "iinfo", "_max_vals"))
#   LD-50: numpy's memo dicts (np.finfo / np.iinfo fill them on first use): emptied before every game, not compared


def _plain(v) -> bool:
    return v is None or type(v) in (bool, int, float, complex, str, bytes)


def _table(v) -> bool:
    """A dict, list or set numpy holds that is compared by its items (LD-50: np.sctypeDict, np.typecodes...)."""
    return isinstance(v, (dict, list, set))


def _numpy_caches() -> list:
    out = []
    for mod, cls, name in NUMPY_CACHES:
        d = getattr(getattr(sys.modules.get(mod), cls, None), "__dict__", {}).get(name)
        if isinstance(d, dict):
            out.append(d)
    return out


def _numpy_held() -> list:
    """numpy's own arrays and plain values that its modules (those strategies may use) and the classes they hold keep,
    as [(name, holder, attribute)] (LD-47): a strategy could write into such an array through a numpy function's
    destination argument (np.copyto(np.polynomial.Polynomial.window, ...) changed every later polynomial in the
    worker), or a numpy function could set such a value (set_default_printstyle). LD-50: and their dicts, lists and
    sets (np.sctypeDict: a key replaced there made every later np.array(..., dtype='float32') an int8 array), but
    numpy's memo caches (NUMPY_CACHES, emptied before every game) and an enum class's tables."""
    np = sys.modules.get("numpy")
    if np is None:
        return []
    caches = {id(d) for d in _numpy_caches()}
    out, seen = [], set()
    for m in sorted(n for n in list(sys.modules) if n in NUMPY_MODULES or n.startswith("numpy.polynomial.")):
        mod = sys.modules.get(m)
        if mod is None:
            continue
        for k, v in list(vars(mod).items()):
            if isinstance(v, np.ndarray) or _plain(v) or (_table(v) and k != "__builtins__"):
                out.append((f"{m}.{k}", mod, k))
            elif isinstance(v, type) and str(getattr(v, "__module__", "")).startswith("numpy") and id(v) not in seen \
                    and not isinstance(v, enum.EnumType):
                seen.add(id(v))
                for a, w in list(vars(v).items()):
                    if isinstance(w, np.ndarray) or _plain(w) or (_table(w) and id(w) not in caches):
                        out.append((f"{v.__module__}.{v.__qualname__}.{a}", v, a))
    return out


def _items(v):
    """A dict's, list's or set's items as something == compares: keys and values by identity, and one level down
    for the dicts, lists and tuples it holds (np.sctypes' lists)."""
    def inner(x):
        if isinstance(x, dict):
            return ("dict", id(x), tuple((id(a), id(b)) for a, b in dict.items(x)))
        if isinstance(x, (list, tuple)):
            return (type(x).__name__, id(x), tuple(map(id, x)))
        return id(x)
    if isinstance(v, dict):
        return ("dict", id(v), tuple((id(a), inner(b)) for a, b in dict.items(v)))
    if isinstance(v, set):
        return ("set", id(v), frozenset(map(id, v)))
    return ("list", id(v), tuple(inner(x) for x in list.__iter__(v)))


def _value(v):
    """A held numpy value as something == compares: an array by identity, type, shape and bytes."""
    np = sys.modules.get("numpy")
    if np is not None and isinstance(v, np.ndarray):
        return ("array", id(v), v.dtype.str, v.shape, v.tobytes(), v.flags.writeable)
    if _table(v):
        return _items(v)
    return (type(v), v)


def _process_state(held=()) -> dict:
    """What a strategy could change for the whole process without touching a followed object (LD-46): the ABC
    registry's counter (every ABCMeta.register moves it: typing.Hashable.register(list) changes isinstance for
    every later game), and when numpy is loaded its error, buffer and print settings and its global RandomState, and
    (LD-47) the arrays and plain values its modules and classes hold (`held`, from _numpy_held)."""
    out = {"abc.register": abc.get_cache_token()}
    for name, holder, attr in held:
        try:
            out[name] = _value(vars(holder).get(attr, GONE))
        except Exception:                          # noqa: BLE001
            out[name] = GONE
    np = sys.modules.get("numpy")
    if np is not None:
        for name in ("geterr", "geterrcall", "getbufsize", "get_printoptions"):
            f = getattr(np, name, None)
            if f is not None:
                try:
                    out[f"numpy.{name}"] = f()
                except Exception:                  # noqa: BLE001
                    out[f"numpy.{name}"] = GONE
        rnd = sys.modules.get("numpy.random")
        if rnd is not None and hasattr(rnd, "get_state"):
            try:
                st = rnd.get_state(legacy=True)
                out["numpy.random (global)"] = (st[0], st[1].tobytes(), *st[2:])
            except Exception:                      # noqa: BLE001
                out["numpy.random (global)"] = GONE
    return out


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
    if how in ("dict", "moddict", "grows"):
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
        if not isinstance(d, dict):
            return 0
        skip = _cache_attrs(type(obj))
        return dict.__len__(d) if not skip else sum(1 for k in dict.keys(d) if k not in skip)
    return None                                    # a function, a tuple; a GROWS dict may gain items


def _caches(which=CACHES) -> set:
    out = set()
    for mod, name in which:
        d = getattr(sys.modules.get(mod), name, None)
        if isinstance(d, dict):
            out.add(id(d))
    return out


def snapshot() -> Snapshot:
    import builtins
    s = Snapshot()
    queue, seen = [], set(_caches())               # the caches: held by identity (their global), never followed
    grows = set()
    mods = sorted((n, m) for n, m in list(sys.modules.items()) if _watched(n) and m is not None)
    std = [(n, sys.modules[n]) for n in STDLIB + FOLLOWED if sys.modules.get(n) is not None]
    for name, m in mods + [("builtins", builtins)] + std:
        s.modules[name] = m
        d = getattr(m, "__dict__", None)
        if not isinstance(d, dict) or id(d) in seen:
            continue
        seen.add(id(d))
        if name != "builtins":                     # LD-44: CPython makes it on a module's first warning, even an
            seen.add(id(dict.setdefault(d, "__warningregistry__", {})))   # ignored one: made here, held by identity
        keys = list(dict.keys(d))
        if name.startswith(GROWS):
            grows.update(id(v) for v in dict.values(d) if type(v) in (dict, set))
        _record(s, d, "moddict", keys, name)
        if name in STDLIB + FOLLOWED:              # its own classes and functions only (not its caches), and its
            queue += [(v, f"{name}.{k}", 1) for k in keys    # dicts, lists and sets (LD-49: copy.dispatch_table)
                      if (isinstance(v := dict.get(d, k), (type, types.FunctionType)) and
                          getattr(v, "__module__", None) == name) or
                      (isinstance(v, (dict, list, set)) and (name, k) not in STD_CACHES)]
        elif name != "builtins":
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
            s.sets.append([obj, frozenset(obj), path, id(obj) in grows])
            continue
        if isinstance(obj, type) and (_watched(getattr(obj, "__module__", None)) or
                                      getattr(obj, "__module__", None) in STDLIB + FOLLOWED):
            if "__slotnames__" not in obj.__dict__:
                copyreg._slotnames(obj)            # LD-43: copy.copy / deepcopy store it on first use (a pure cache)
            if "__annotations__" not in obj.__dict__:
                try:                               # LD-45: the first read stores an empty one (a runtime-checkable
                    getattr(obj, "__annotations__", None)   # Protocol's isinstance, functools.cache(K) read it)
                except Exception:                  # noqa: BLE001, S110
                    pass
        try:
            members = _members(obj)
        except Exception:                          # an object that won't show its inside is held by identity only
            members = None
        if members is None:
            continue
        how = _how(obj)
        if id(obj) in grows:
            how = "grows"
            s.grows.append((obj, dict.__len__(obj)))
        keys = [k for k, _ in members]
        if how != "tuple":                         # a tuple can't change; what it holds is followed below
            _record(s, obj, how, keys, path)
        sep = "[{}]" if how in ("dict", "list", "tuple", "grows") else ".{}"
        queue += [(v, path + sep.format(_short(k, 40)), depth + 1) for k, v in members]
    s.numpy_held = _numpy_held()
    s.numpy_arrays = [vars(h).get(a) for _, h, a in s.numpy_held]   # held: an array's id isn't reused
    s.process = _process_state(s.numpy_held)
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
    for d in _numpy_caches():                      # LD-50
        dict.clear(d)


def _same(k, a, b) -> bool:
    """Unchanged: the same object; for a class's name, an equal str (a builtin type makes it anew at each reading)."""
    return a is b or (type(a) is str and type(b) is str and isinstance(k, tuple) and k[0] == "type" and a == b)


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
                if _same(k, a, b):
                    continue
                if how == "moddict" and b is None and a is not GONE:
                    lazy.append(k)                 # a lazy global set for the first time
                    continue
                if say(f"{path}: {_short(k)} {'removed' if a is GONE else 'changed'}"):
                    return out
            if lazy and len(lazy) == sum(not _same(k, a, b) for k, a, b in zip(keys, now, before)):
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
    for obj, fs, path, grow in snap.sets:
        if not (fs <= obj if grow else fs == obj):
            if say(f"{path}: set changed"):
                return out
    now = _process_state(snap.numpy_held)
    for k, v in snap.process.items():
        try:
            same = now.get(k, GONE) == v
        except Exception:                          # noqa: BLE001
            same = False
        if not same and say(f"{k} changed"):
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


def preload(extra=()):
    """What games load, loaded before the warm-up and the first snapshot (so the snapshot follows it from the start):
    PRELOAD, STDLIB, every module of svsim a strategy may import (LD-42: one first loaded during a game was taken into
    the next snapshot with whatever that game did to it), and `extra` (a guarded task's own module). runner._warm_up
    then plays one game, which sets the lazy globals."""
    import importlib
    import pkgutil

    from ladder.codecheck import DENIED_PREFIXES
    for m in PRELOAD + STDLIB + FOLLOWED + tuple(extra):
        importlib.import_module(m)
    for m in NUMPY_MODULES:                        # LD-46: numpy registers ABCs (numbers.Integral...) when it loads
        try:
            importlib.import_module(m)
        except Exception:                          # noqa: BLE001, S110 - not installed: strategies can't use it either
            pass
    typing = sys.modules["typing"]
    for n in ("Pattern", "Match", "ContextManager", "AsyncContextManager"):
        getattr(typing, n, None)                   # Python 3.13 makes these on first use, in typing's globals
    import svsim
    for info in pkgutil.walk_packages(svsim.__path__, "svsim."):
        name = info.name
        if any(name == d or name.startswith(d + ".") for d in DENIED_PREFIXES) or \
                any(part.startswith("_") for part in name.split(".")):
            continue
        try:
            importlib.import_module(name)
        except Exception:                          # noqa: BLE001, S110 - a module that can't load can't be later either
            pass


def stale(snap: Snapshot) -> bool:
    """True if the snapshot should be taken again after a clean task: a watched module was loaded since, or a lazy
    global got its value (so what it holds is followed from now on)."""
    return snap.relaxed or any(_watched(n) and m is not None and n not in snap.modules
                               for n, m in list(sys.modules.items())) or \
        any(dict.__len__(d) > n for d, n in snap.grows) or \
        any(grow and len(obj) > len(fs) for obj, fs, _, grow in snap.sets)
