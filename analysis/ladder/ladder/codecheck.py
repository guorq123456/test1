"""Reading a submission's code (item 2.3; fifth pass LD-40, sixth LD-41, seventh LD-42, eighth LD-43, ninth LD-44,
tenth LD-45, eleventh LD-46, twelfth LD-47, thirteenth LD-48, fourteenth LD-49, fifteenth LD-50,
sixteenth LD-51).
Nothing in the submitted code runs.
The simulator's and ladder's own modules are imported here (they are the host's code) to tell a module from a class
from a function; svsim.learn, svsim.tools, svsim.ui, svsim.build, svsim.search.parallel and ladder's other modules
never are.

Two kinds of rules.

Names. Imports only from the allowed modules, and no private names from them (of numpy only numpy, numpy.random,
linalg, fft, polynomial, exceptions, dtypes, typing, and none of its file, settings, test or global-random
names: LD-46; no writing into a possibly shared array through numpy's out=, by keyword or by position, a ufunc's
outputs or numpy's first-argument writers: LD-47, LD-48, and the arguments numpy changes in place: LD-49; one
dataclass decorator a class, its arguments written out by name and its init= True or False: LD-48, LD-49); a name an
import binds never bound again (rebound, it would no longer be what the reading takes it for), nor two imports
binding one name to different things (LD-46); none of the names and attributes
that reach files, the network, other processes, frames or the interpreter; no dunder names but __init__, __name__,
__post_init__ (and those three never assigned); other objects' private attributes no (the strategy's own `self._x`
yes: `self` = the first parameter of a method of the module's own class, never rebound); `getattr` & co. only
called directly, with a written-out name; no dunder methods defined, no class built by type(name, bases, dict) or
make_dataclass; `super().__init__` only inside __init__ / __post_init__; no functools.wraps / update_wrapper, no
`attrname`, `default_factory` or typing.get_type_hints (each hands out what a check would have to follow by hand).

Where shared objects go. Every value gets one of three levels, by a scope-aware reading of the whole module,
repeated until nothing changes:
  CLEAN   made by the strategy: a literal, an instance of its own class or of a standard-library class made from
          clean values, a number from math (not prod / sumprod: they start from what they're given; statistics
          neither: median_low, mode, ... return one of their arguments), what its own clean objects hold;
  HOLDS   fresh, but may hold shared objects: a list of imported objects, list(x) / dict(x) / sorted(x) of a shared
          x, an instance of an svsim / ladder class, dataclasses.replace(x, ...), a container something shared was
          put into, what the hooks are called with, dataclasses.fields / asdict / astuple of anything;
  SHARED  maybe an object the simulator or another strategy in the same process uses: an imported name, a module's
          attribute, what an svsim / ladder function returns (unless its annotation says a number, a bool, a str),
          anything read out of a HOLDS or SHARED object, what the strategy inherits from an svsim / ladder class
          (self.tree, self.agent, ...; self.random, self.rng, self.spec, self.defaults are its own); copy.copy and
          copy.deepcopy keep their argument's level (a copy of a class, a function or an enum member is itself);
          a def or class under a decorator other than lru_cache, cache, cached_property, total_ordering, dataclass
          and a real property's .setter / .getter / .deleter (checked by what the name is, not how it's spelled);
          anything read from an object of a class built on a storage type (typing.NamedTuple, namedtuple(...),
          TypedDict, dict, list, tuple, an exception...: what its constructor is given is kept where this reading
          doesn't follow it, LD-44), self's attributes and items inside such a class too, and what the methods it
          inherits give (self.get(...), super().get(...), self._asdict(): LD-45); the attributes a standard-library
          base sets on self (UserDict.data, ChainMap.maps: read from its source, LD-45).
A method's parameters start CLEAN, the module's own code being the only caller; SHARED for __post_init__ (its
InitVars come from any construction, a default or replace) and for an own Enum's __init__ and the hooks its base
names (_missing_...: the member values, what C(x) is given; LD-45); HOLDS when someone else may call it: a dunder, the __init__ of a class with a base that isn't the module's own (PlayerStrategy alone is fine), a
method named like an attribute the simulator's or ladder's code uses on objects it is handed (duck_names), or like
a member of a non-own base class or a name that base's code uses on self (the host may call it with its objects);
every method of a class whose base can't be told (typing.NamedTuple / TypedDict, Generic[...] and namedtuple(...)
can: LD-43); SHARED when the method is taken as a value. A refusal ends with a note naming the methods HOLDS only
for their name, each with a name host code doesn't use either, those named like a container's methods (rename
them), the classes built on a storage type (use a dataclass), and the lines of replace(x, **d) with a d not written
out. `cls(...)` in a classmethod is the construction of that class or of one of the module's classes built on it;
constructing a class runs its own __init__ if it has one, else, on each branch of its own bases, the first class's
that has one or is a dataclass (generated: init_sources; a superset of C3's choice, LD-44 / LD-45). A dataclass's
fields get the levels of the arguments that set them, at its construction (an undecorated subclass's, cls(...),
super().__init__(...) too) and in dataclasses.replace / copy.replace: by name; by position when the field order is
plain (dc_positional: read as dataclasses reads it, ClassVar / InitVar / KW_ONLY / field(init=, kw_only=) and the
string annotations included, LD-46), else every field the highest positional level (the receipt names the line);
`**{'k': v}` written out sets k, any other `**d` every field of every dataclass of the module (LD-45).
A SHARED object may not be changed: no assignment or `del` into it (x.a = ..., x[k] = ...), no augmented assignment
on it (x += ...: write x = x + ...; adding a number literal is allowed), no method that changes a container
(append, add, update, pop, clear, sort, ...: called or taken as a value), no shuffle / heappush / insort on it, no
setattr / delattr on it. Assigning into anything reached from an imported name is refused whatever its level.
Levels follow assignments, for / with / comprehension targets, :=, unpacking, arguments into the module's own
functions and methods (a function or method taken as a value: its parameters are SHARED), return values,
attributes (by name: x.a = shared makes every .a SHARED), containers (d[k] = shared, l.append(shared)).
Also refused, because the reading would lose track: a module used as a value (only `m.x`); a class of the module
used other than to make an instance, read an attribute, isinstance / issubclass, a base (Own[...] too), raise /
except, a comparison (an own class's name in an annotation only with `from __future__ import annotations`, which leaves
annotations unread; a match-class pattern; iterating or indexing an own Enum); a method called through its class
(K.method(x), cls.method(x), type(x).method(x)); a class defined inside a class (Outer.Inner(...) isn't followed to
its __init__: LD-44); an if / for / while / try / with / match in a class body (a def or a field under it isn't
seen as the class's: LD-45); a classmethod's cls used other than to construct, read an attribute, compare or
isinstance (f = cls; f(x) isn't followed: LD-45; an own Enum's cls may also be iterated, indexed and given to
list / sorted / max...: LD-46); dataclasses.dataclass, typing.final / no_type_check / override /
runtime_checkable / dataclass_transform / overload / abstractmethod, enum.global_enum and functools.total_ordering
other than as a decorator, getattr(m, 'name') spellings too (called on an imported class they change it: LD-45,
LD-46); `.register` on anything but the module's own functools.singledispatch function (ABCMeta.register changes
isinstance for the whole process: LD-46); a class attribute (or a dataclass field default) at the SHARED level that
isn't a name written straight from a module whose object is no dataclasses.Field and has no __set_name__ (the class
statement calls __set_name__; @dataclass rewrites a Field it finds in place: one from dataclasses.fields(PlayCard)
dropped `targets` from every later game, LD-46), an import or := in a class body; type(x) used other than for an attribute, a comparison or
isinstance; svsim.core.script.register; keyword arguments parallel / par_spec (ISMCTS's root-parallel processes:
their CPU is not the strategy's process's); `x *= n` with an int on a SHARED x (a list repeats in place); a yield
or await inside a try's body, except or else (when the generator is freed, there, off every clock, its except /
finally run: LD-42; the runner's idle watchdog is the backstop). The reading repeats until nothing changes, for up
to FLOW_SECONDS; a module that takes longer, or nests deeper than Python can read, is refused, not passed.
What it can't see: objects reached through what the hooks are given (a card's definition through a sampled state)
and the keys of a dictionary. Those are the tripwire's (watch.py: a change that lasts past a game) and the replay
audit's (audit.py: a rule changed and put back within a game).
"""
from __future__ import annotations

import ast
import builtins
import collections
import copy as _copy
import dataclasses
import enum
import importlib
import inspect
import re
import textwrap
import time
import types
import typing
from pathlib import Path

ALLOWED_TOP = {"__future__", "typing", "math", "random", "collections", "itertools", "functools", "dataclasses",
               "heapq", "bisect", "statistics", "copy", "enum", "numpy", "svsim"}
ALLOWED_LADDER = {"ladder.interface", "ladder.base"}
NUMPY_MODULES = frozenset({"numpy", "numpy.random", "numpy.linalg", "numpy.fft", "numpy.polynomial",
                           "numpy.exceptions", "numpy.dtypes", "numpy.typing"})    # and numpy.polynomial.*: LD-46,
#                         not numpy.testing (builds and imports C code), numpy.lib / ma / rec / f2py (files), numpy.emath
#                         (it is numpy.lib.scimath, no module of that name: LD-47), ...
NUMPY_DENIED = frozenset({                         # numpy's own names that aren't for strategies (LD-46)
    "load", "save", "savez", "savez_compressed", "savetxt", "loadtxt", "genfromtxt", "fromfile", "fromregex", "memmap",
    "open_memmap", "DataSource", "dump", "tofile",                                                  # files
    "seterr", "seterrcall", "setbufsize", "set_printoptions", "set_string_function", "set_numeric_ops", "add_newdoc",
    "add_docstring", "add_newdoc_ufunc", "set_default_printstyle", "printoptions", "seterrobj", "geterrobj",   # the
    #                                    process's numpy settings (LD-51: numpy 1.x's geterrobj gives the live list):
    #                                                                     every later game in the worker
    "test", "info", "source", "lookfor", "show_config", "show_runtime", "who", "get_include"})   # running, showing
NUMPY_OLD = {"product": "prod", "cumproduct": "cumprod", "sometrue": "any", "alltrue": "all"}   # numpy 1.x's
#   (*args, **kwargs) aliases: where their out sits can't be read (LD-49); numpy 2 has only the new names
NUMPY_RANDOM_OK = frozenset({"Generator", "default_rng", "RandomState", "SeedSequence", "BitGenerator", "MT19937",
                             "PCG64", "PCG64DXSM", "Philox", "SFC64"})   # not the process's global RandomState
DENIED_PREFIXES = ("svsim.learn", "svsim.tools",       # they load trained models (A12)
                   "svsim.ui",                          # the levels' rating table, records of games (red lines)
                   "svsim.build",                       # runs git
                   "svsim.search.parallel")             # a process pool: compute outside the strategy's process
BANNED_NAMES = {"open", "eval", "exec", "compile", "__import__", "globals", "locals", "vars", "breakpoint",
                "input", "memoryview", "help", "exit", "quit", "__builtins__", "__loader__", "__spec__", "__file__"}
ATTR_FUNCS = {"getattr", "setattr", "delattr", "hasattr"}   # allowed only with a written-out, allowed name
ALLOWED_DUNDERS = {"__init__", "__name__", "__post_init__"}
BANNED_ATTRS = {
    # frames, code, the interpreter
    "f_back", "f_locals", "f_globals", "f_builtins", "f_code", "tb_frame", "tb_next", "gi_frame", "gi_code",
    "cr_frame", "cr_code", "ag_frame", "ag_code", "co_code", "mro", "modules",
    # modules reachable as attributes of allowed modules
    "sys", "os", "gc", "inspect", "ctypes", "ctypeslib", "subprocess", "socket", "importlib", "builtins", "io",
    "pathlib", "shutil", "threading", "multiprocessing", "marshal", "pickle",
    # files
    "Path", "read_text", "read_bytes", "write_text", "write_bytes", "open", "unlink", "fromfile", "tofile",
    "memmap", "loadtxt", "savetxt", "genfromtxt", "savez", "savez_compressed", "DataSource", "dump",  # ndarray.dump
    # processes, environment
    "system", "popen", "environ", "getenv", "putenv",
    # (LD-41) root-parallel search (its own processes); a class with chosen dunders; a property's raw functions
    "parallel", "par_spec", "make_dataclass", "fget", "fset", "fdel",
    # (LD-42) setattr / getattr by a name in a string (update_wrapper's assigned=, cached_property's attrname); a
    # class handed back as a value (a defaultdict's factory, the evaluated annotations)
    "update_wrapper", "wraps", "attrname", "default_factory", "get_type_hints",
    # (LD-52) numpy 2's Cython functions name their insides without underscores: func_globals is a private
    # module's namespace (numpy.random._generator: a rebound PCG64 changed every later default_rng in the worker)
    "func_globals", "func_code", "func_closure", "func_dict", "func_defaults", "func_name", "func_doc",
}
DANGER_MODULES = frozenset({   # (LD-52) an object, class or function of these is refused where the reader can see it
    "os", "posix", "nt", "pathlib", "io", "_io", "shutil", "tempfile", "glob", "fnmatch", "zipfile", "tarfile",
    "subprocess", "socket", "ssl", "select", "selectors", "signal", "threading", "_thread", "multiprocessing",
    "concurrent", "asyncio", "logging", "sqlite3", "ctypes", "_ctypes", "mmap", "pickle", "marshal", "shelve",
    "importlib", "pkgutil", "runpy", "zipimport", "sys", "gc", "inspect", "traceback", "linecache", "tokenize",
    "atexit", "webbrowser", "urllib", "http", "winreg", "_winapi", "msvcrt", "pty", "fcntl", "resource",
    "code", "codeop", "pdb", "bdb", "faulthandler", "tracemalloc", "weakref", "_weakref"})
BANNED_KEYWORDS = {"parallel", "par_spec"}

CLEAN, HOLDS, SHARED = 0, 1, 2
MUTATORS = frozenset({
    "append", "extend", "insert", "remove", "pop", "popitem", "clear", "update", "setdefault", "add", "discard",
    "sort", "reverse", "difference_update", "intersection_update", "symmetric_difference_update", "appendleft",
    "extendleft", "popleft", "rotate", "subtract", "move_to_end", "fill", "put", "itemset", "resize", "setflags",
    "setfield", "partition", "byteswap", "cache_clear"})
ADDERS = frozenset({"append", "add", "extend", "insert", "update", "appendleft", "extendleft"})
REPLACERS = tuple(f for f in (dataclasses.replace, getattr(_copy, "replace", None)) if f is not None)  # 3.13's too
DC_PLAIN_KEYWORDS = frozenset({"frozen", "eq", "order", "repr", "unsafe_hash", "slots", "match_args", "weakref_slot"})
ARG_MUTATORS = frozenset({"shuffle", "heappush", "heappop", "heapify", "heapreplace", "heappushpop", "insort",
                          "insort_left", "insort_right"})
NUMPY_WRITERS = frozenset({"copyto", "place", "putmask", "fill_diagonal", "put_along_axis", "put", "frombuffer",
                           "nditer"})   # numpy functions that write into their first argument or alias it (LD-47,
#                                       LD-48: known as numpy's only, an own `place` is the player's)
UFUNC_OUT_AT = {"at": 0, "reduce": 3, "accumulate": 3, "reduceat": 4}   # the argument a ufunc method writes (LD-47)
METHOD_OUT_FIX = {"any": {2}, "all": {2}, "conj": {0}, "conjugate": {0}, "choose": set()}   # LD-49: where these
#   ndarray methods really take out (a.any(axis, dtype, out) goes through numpy's _any; a.conj(out) documents no
#   parameter; a.choose(c1, c2) takes every positional as a choice), which their documented signatures don't say
NUMPY_FLAGS = {"overwrite_input": (0, True), "copy": (0, False)}   # LD-49: a parameter that makes numpy change
#   argument 0 in place when it is true (median / percentile / quantile and their nan versions) or, for
#   nan_to_num only, false
NUMPY_INPLACE_PARAMS = {"array_repr": ("max_line_width",), "array2string": ("max_line_width",), "rot90": ("k",)}
#   LD-49: parameters numpy updates with an augmented assignment (options['linewidth'] -= ..., numpy 1.26's k %= 4):
#   an array given there is changed in place
BUILTIN_TYPES = frozenset({"set", "dict", "list", "bytearray", "frozenset", "object", "type", "tuple"})
SCALAR_BUILTINS = frozenset({
    "len", "id", "hash", "isinstance", "issubclass", "callable", "hasattr", "bool", "int", "float", "str", "repr",
    "abs", "round", "ord", "chr", "any", "all", "divmod", "pow", "format", "ascii", "bin", "hex", "oct", "complex",
    "print", "setattr", "delattr"})
FRESH_BUILTINS = frozenset({"list", "dict", "set", "frozenset", "tuple", "sorted", "reversed", "enumerate", "zip",
                            "map", "filter", "iter", "range", "sum", "bytearray", "bytes", "slice"})
ELEMENT_BUILTINS = frozenset({"min", "max", "next"})
ENUM_READERS = frozenset({"list", "tuple", "set", "frozenset", "sorted", "reversed", "min", "max", "len", "iter",
                          "enumerate", "any", "all"})      # builtins that only go through an Enum class's members
KEY_METHODS = frozenset({"get", "setdefault", "pop"})         # d.get(k, default): the key doesn't come back
SCALAR_METHODS = frozenset({"index", "count", "startswith", "endswith", "find", "rfind", "isdigit", "isalpha",
                            "total", "bit_length", "is_integer", "lower", "upper", "strip", "split", "join",
                            "format", "replace", "random", "randint", "randrange", "uniform", "gauss", "getrandbits", "bisect", "bisect_left", "bisect_right"})
SCALAR_MODULES = frozenset({"math", "cmath"})                   # numbers in, numbers out (LD-42: not statistics,
NOT_SCALAR = frozenset({"prod", "sumprod"})                       # whose median_low / mode / mean([x]) can be x)
FRESH_FUNCS = {("heapq", "nlargest"), ("heapq", "nsmallest"), ("heapq", "merge"), ("functools", "partial"),
               ("functools", "reduce")}
WRAPPERS = frozenset({"staticmethod", "classmethod", "property", "cached_property", "lru_cache", "cache"})
REAL_WRAPPERS = (("functools", "lru_cache"), ("functools", "cache"), ("functools", "cached_property"),
                 ("functools", "total_ordering"), ("dataclasses", "dataclass"))
ACCESSORS = frozenset({"setter", "getter", "deleter"})
CLASS_MUTATORS = (("dataclasses", "dataclass"), ("typing", "final"), ("typing", "no_type_check"),  # change the class
                  ("typing", "override"), ("typing", "runtime_checkable"), ("typing", "dataclass_transform"),  # or the
                  ("typing", "overload"), ("typing", "no_type_check_decorator"), ("enum", "global_enum"),  # function
                  ("functools", "total_ordering"),  # they're given: decorators of the module's own only (LD-45)
                  ("typing", "abstractmethod"))     # LD-46: sets __isabstractmethod__ on what it's given
FLOW_SECONDS = 60                                 # a module whose reading takes longer is refused (LD-42)
OWN_FRESH = frozenset({"random", "rng", "spec", "defaults", "LETHAL", "ITERATIONS"})   # PlayerStrategy's own
SCALAR_ANNOTATIONS = {"float", "int", "bool", "str", "None", float, int, bool, str, None, type(None)}
_MISSING = object()


def holds(v: int) -> int:
    return HOLDS if v >= HOLDS else CLEAN


def elem(v: int) -> int:
    return SHARED if v >= HOLDS else CLEAN


def dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def banned_dunder(name: str) -> bool:
    return dunder(name) and name not in ALLOWED_DUNDERS


def module_problem(name: str) -> str | None:
    if any(p.startswith("_") for p in name.split(".")) and name != "__future__":
        return "私有模块不许用"
    if any(name == p or name.startswith(p + ".") for p in DENIED_PREFIXES):
        return "它们能载入训练好的模型、读强度表或对局记录、开进程（A12、红线）"
    top = name.split(".")[0]
    if top == "numpy" and name not in NUMPY_MODULES and not name.startswith("numpy.polynomial."):
        return ("numpy 只许用 numpy、numpy.random、numpy.linalg、numpy.fft、numpy.polynomial、"
                "numpy.exceptions、numpy.dtypes、numpy.typing：别的子模块能读写文件、编译载入 C 代码（LD-46）")
    if top == "ladder":
        return None if name in ALLOWED_LADDER else "ladder 里只能用 ladder.interface、ladder.base"
    if top in ALLOWED_TOP:
        return None
    return "不在允许的模块里"


def danger_problem(obj) -> str | None:
    """LD-52: why an object a module hands out (from m import x, m.x) is refused: a file path, a file, a lock, a
    logger, a function of the os / io / sys family... anything whose class or own module is one of DANGER_MODULES
    (ladder.base.ROOT was a pathlib.Path: its methods renamed, deleted, made and listed folders)."""
    if isinstance(obj, types.ModuleType) or obj is _MISSING:
        return None
    mods = {getattr(obj, "__module__", None) if isinstance(obj, (type, types.BuiltinFunctionType, types.FunctionType))
            else getattr(type(obj), "__module__", None)}
    self_ = getattr(obj, "__self__", None)
    if isinstance(self_, types.ModuleType):
        mods.add(self_.__name__)
    for m in mods:
        if isinstance(m, str) and m.split(".")[0] in DANGER_MODULES:
            return f"它是 {m} 的东西（文件、进程、线程、解释器一类，LD-52）"
    return None


def numpy_problem(mod: str, attr: str) -> str | None:
    """Why `mod.attr` of numpy isn't for strategies (LD-46), or None."""
    if mod.split(".")[0] != "numpy":
        return None
    if attr in NUMPY_DENIED:
        return "numpy 的这个不许用：读写文件、改整个进程的 numpy 设置（同一进程里后面别人的对局也受影响）或运行别的东西（LD-46）"
    if attr in NUMPY_OLD:
        return (f"numpy.{attr} 是 numpy 1.x 的旧别名（numpy 2 没有了），改用 numpy.{NUMPY_OLD[attr]}，参数一样（读代码看不清"
                "旧别名的参数，LD-49）")
    if mod == "numpy.random" and attr not in NUMPY_RANDOM_OK:
        return ("numpy 的全局随机数不许用（整个进程共用一个）：要随机数用 self.random，或 numpy.random.default_rng(种子) "
                "自己建一个（LD-46）")
    return None


_MODULES: dict = {}
_ATTRS: dict = {}


def _import(name: str):
    """The module `name`, imported only when it is allowed (the packages svsim and ladder themselves too)."""
    if name not in _MODULES:
        m = _MISSING
        if (module_problem(name) is None or name in ("svsim", "ladder")) and name != "__future__":
            try:
                m = importlib.import_module(name)
            except Exception:  # noqa: BLE001 - a name that isn't there is the submission's problem
                m = _MISSING
        _MODULES[name] = m
    return _MODULES[name]


def member(mod: str, attr: str):
    """What `mod.attr` is: a module, an object, or _MISSING. A submodule is imported only when it is allowed."""
    key = (mod, attr)
    if key not in _ATTRS:
        parent = _import(mod)
        obj = _MISSING
        if parent is not _MISSING:
            try:
                obj = getattr(parent, attr, _MISSING)
            except Exception:  # noqa: BLE001 - a module __getattr__ that raises
                obj = _MISSING
            if obj is _MISSING and hasattr(parent, "__path__"):
                obj = _import(f"{mod}.{attr}")
        _ATTRS[key] = obj
    return _ATTRS[key]


def _registrars() -> set:
    out = set()
    reg = member("svsim.core.script", "register")
    if reg is not _MISSING:
        out.add(id(reg))
    return out


def _player_strategy():
    return member("ladder.interface", "PlayerStrategy")


_CLASS_ATTRS: dict = {}


def class_attrs(cls) -> set:
    """Every attribute an instance of `cls` may have from its classes: dir(cls), and for every class in its MRO
    written in Python (svsim, ladder, the standard library's: LD-45) the `self.x = ...` (and setattr(self, "x", ...))
    in their source."""
    if cls in _CLASS_ATTRS:
        return _CLASS_ATTRS[cls]
    names = set(dir(cls))
    for k in getattr(cls, "__mro__", ()):
        names |= set(getattr(k, "__dict__", {}))   # LD-45: an enum's dir() leaves out _missing_ and the like
        if (getattr(k, "__module__", "") or "builtins") == "builtins":
            continue                               # LD-45: the standard library's Python classes too (UserDict.data)
        try:
            tree = ast.parse(textwrap.dedent(inspect.getsource(k)))
        except (OSError, TypeError, SyntaxError):
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self" and \
                    isinstance(n.ctx, ast.Store):
                names.add(n.attr)
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "setattr" and \
                    len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str):
                names.add(n.args[1].value)
    _CLASS_ATTRS[cls] = names
    return names


def fresh_class(cls) -> bool:
    """Calling `cls` makes a new instance: no enum, no metaclass __call__, no __new__ written in Python."""
    try:
        if issubclass(cls, enum.Enum) or type(cls).__call__ is not type.__call__:
            return False
        for k in cls.__mro__:
            if "__new__" in vars(k):
                return isinstance(vars(k)["__new__"], (types.BuiltinFunctionType, types.BuiltinMethodType))
    except Exception:  # noqa: BLE001
        return False
    return True


def scalar_return(fn) -> bool:
    try:
        ann = getattr(fn, "__annotations__", None) or {}
        return ann.get("return", _MISSING) in SCALAR_ANNOTATIONS
    except Exception:  # noqa: BLE001
        return False


_DUCK: frozenset | None = None


DUCK_SKIP = ("svsim/tools/", "svsim/ui/", "svsim/build/", "ladder/codecheck.py")   # never run with a strategy's
#                                                    objects (closed to strategies, or this reader's own word lists)
COMPUTED_ACCESS = frozenset({"getattr", "hasattr", "setattr", "delattr", "attrgetter", "methodcaller", "vars"})


def _computed_access(tree) -> bool:
    """The module reads attributes by a name it works out (getattr(x, name), vars(x)[k], x.__dict__): any string
    in it may be an attribute name."""
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
            if name in COMPUTED_ACCESS and any(not isinstance(a, ast.Constant) for a in n.args[1:2] or n.args[:1]):
                return True
        elif isinstance(n, ast.Attribute) and n.attr in ("__dict__", "__getattribute__"):
            return True
    return False


def duck_names() -> frozenset:
    """Every method name host code may call on an object it was handed (duck typing): the attribute names the
    simulator's and the ladder's code reads or writes (x.name, not self.x / cls.x: those are its own classes',
    see base_self_names), the written-out names of getattr / hasattr / attrgetter / methodcaller, and every
    identifier-shaped string of a module that reads attributes by a computed name. A method of the strategy's own
    classes with one of these names may be called by host code with host objects, so its parameters start as HOLDS
    (LD-42; LD-43 left out other strings, the modules closed to strategies and this reader). Read once."""
    global _DUCK
    if _DUCK is None:
        names = set()
        for pkg in ("svsim", "ladder"):
            m = _import(pkg)
            for root in (list(getattr(m, "__path__", [])) if m is not _MISSING else []):
                for path in sorted(Path(root).rglob("*.py")):
                    rel = path.relative_to(Path(root).parent).as_posix()
                    if rel.startswith(DUCK_SKIP):
                        continue
                    try:
                        tree = ast.parse(path.read_text(encoding="utf-8"))
                    except (OSError, SyntaxError, ValueError, UnicodeDecodeError):
                        continue
                    every_string = _computed_access(tree)
                    for n in ast.walk(tree):
                        if isinstance(n, ast.Attribute) and not (isinstance(n.value, ast.Name) and
                                                                 n.value.id in ("self", "cls")):
                            names.add(n.attr)
                        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.isidentifier():
                            if every_string:
                                names.add(n.value)
                        elif isinstance(n, ast.Call):
                            f = n.func
                            fname = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) \
                                else None
                            if fname in COMPUTED_ACCESS:
                                names.update(a.value for a in n.args if isinstance(a, ast.Constant) and
                                             isinstance(a.value, str) and a.value.isidentifier())
        _DUCK = frozenset(names)
    return _DUCK


_BASE_SELF: dict = {}


def base_self_names(cls) -> frozenset | None:
    """The names an svsim / ladder class's own code uses on self / cls (`self.hook(x)`, possibly a method only a
    subclass defines): a strategy's class built on it may have them called with host objects. None: its code reads
    self's attributes by a computed name (any name)."""
    if cls in _BASE_SELF:
        return _BASE_SELF[cls]
    names = set()
    for k in getattr(cls, "__mro__", ()):
        if (getattr(k, "__module__", "") or "").split(".")[0] not in ("svsim", "ladder"):
            continue
        try:
            tree = ast.parse(textwrap.dedent(inspect.getsource(k)))
        except (OSError, TypeError, SyntaxError):
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in ("self", "cls"):
                names.add(n.attr)
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in COMPUTED_ACCESS and \
                    n.args and isinstance(n.args[0], ast.Name) and n.args[0].id in ("self", "cls"):
                if len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str):
                    names.add(n.args[1].value)
                else:
                    _BASE_SELF[cls] = None
                    return None
    _BASE_SELF[cls] = frozenset(names)
    return _BASE_SELF[cls]


# --- the module's scopes and what flows where ------------------------------------------------------------------

class Scope:
    __slots__ = ("bound", "globals", "kind", "node", "nonlocals", "parent")

    def __init__(self, node, kind, parent):
        self.node, self.kind, self.parent = node, kind, parent
        self.bound, self.globals, self.nonlocals = set(), set(), set()


class Fn:
    __slots__ = (
        "classm",
        "cls",
        "deco_unknown",
        "decos",
        "kwarg",
        "kwonly",
        "node",
        "own",
        "pos",
        "ret",
        "scope",
        "static",
        "value_used",
        "vararg",
    )

    def __init__(self, node, scope):
        self.node, self.scope = node, scope
        a = node.args
        self.pos, self.kwonly = a.posonlyargs + a.args, a.kwonlyargs
        self.vararg, self.kwarg = a.vararg, a.kwarg
        self.cls, self.static, self.classm, self.decos, self.deco_unknown = None, False, False, [], False
        self.value_used, self.own, self.ret = isinstance(node, ast.Lambda), False, CLEAN


class Cls:
    __slots__ = ("attrs", "builtin_bases", "dataclass", "dc_init", "dc_odd", "dc_plain", "deco_unknown", "enum", "fields",
                 "fresh_ok", "node", "objs", "storage", "tainted", "unknown", "user_bases")


def _deco_name(d) -> str | None:
    if isinstance(d, ast.Call):
        d = d.func
    if isinstance(d, ast.Name):
        return d.id
    if isinstance(d, ast.Attribute):
        return d.attr
    return None


class Flow:
    def __init__(self, tree: ast.Module):
        self.tree = tree
        self.lazy = any(isinstance(n, ast.ImportFrom) and n.module == "__future__" and     # annotations are strings
                        any(a.name == "annotations" for a in n.names) for n in tree.body)
        self.where, self.parent, self.inner = {}, {}, {}
        self.module = Scope(tree, "module", None)
        self.nodes = []
        self._build(tree, self.module)
        self._collect()
        self.lv: dict = {}
        self.attrs: dict = {}
        self._ext: dict = {}
        self.changed = False
        self._memo: dict = {}
        self.incomplete = False
        self.star_fields: set = set()  # lines of replace(x, **d) / K(**d) that raised every dataclass field (LD-45)
        self.dc_rough: set = set()     # lines building a dataclass by position where the order isn't plain (LD-46)
        self.replace_lines: dict = {}  # LD-51: line of a replace whose object may be an own class -> those classes
        self._init_levels()
        deadline = time.monotonic() + FLOW_SECONDS
        while True:                    # levels only go up, over three values: this ends (no round cap: LD-42)
            self._memo = {}            # a level read before a raise in the same round is read again next round
            self.changed = False
            for n in self.nodes:
                self._flow(n)
            if not self.changed:
                break
            if time.monotonic() > deadline:
                self.incomplete = True
                break

    # scopes

    def _build(self, node, scope):
        self.where[node] = scope
        self.nodes.append(node)
        for child in ast.iter_child_nodes(node):
            self.parent[child] = node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = node.args
            outer = list(a.defaults) + [d for d in a.kw_defaults if d is not None]
            args = a.posonlyargs + a.args + a.kwonlyargs + [x for x in (a.vararg, a.kwarg) if x is not None]
            if not isinstance(node, ast.Lambda):
                outer += node.decorator_list + [x.annotation for x in args if x.annotation is not None]
                if node.returns is not None:
                    outer.append(node.returns)
            for x in outer:
                self._build(x, scope)
            inner = self.inner[node] = Scope(node, "function", scope)
            for x in args:
                self.where[x] = inner
                self.parent[x] = node
                self.nodes.append(x)
            for x in ([node.body] if isinstance(node, ast.Lambda) else node.body):
                self._build(x, inner)
            return
        if isinstance(node, ast.ClassDef):
            for x in node.bases + [k.value for k in node.keywords] + node.decorator_list:
                self._build(x, scope)
            inner = self.inner[node] = Scope(node, "class", scope)
            for x in node.body:
                self._build(x, inner)
            return
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            gens = node.generators
            self._build(gens[0].iter, scope)
            inner = self.inner[node] = Scope(node, "comp", scope)
            for i, g in enumerate(gens):
                self.where[g] = inner
                self.nodes.append(g)
                for child in ast.iter_child_nodes(g):
                    self.parent[child] = g
                self._build(g.target, inner)
                if i:
                    self._build(g.iter, inner)
                for c in g.ifs:
                    self._build(c, inner)
            for x in ([node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]):
                self._build(x, inner)
            return
        if isinstance(node, ast.Global):
            scope.globals.update(node.names)
        elif isinstance(node, ast.Nonlocal):
            scope.nonlocals.update(node.names)
        for child in ast.iter_child_nodes(node):
            self._build(child, scope)

    def _bind_in(self, scope, name):
        if name in scope.globals:
            self.module.bound.add(name)
        elif name not in scope.nonlocals:
            scope.bound.add(name)

    def resolve(self, scope, name):
        """The scope a name used in `scope` is bound in, or None (a builtin)."""
        s, first = scope, True
        if name in scope.nonlocals:
            s, first = scope.parent, False
        while s is not None:
            if s.kind == "class" and not first:
                s = s.parent
                continue
            if name in s.globals:
                return self.module if name in self.module.bound else None
            if name in s.bound and name not in s.nonlocals:
                return s
            first = False
            s = s.parent
        return None

    def key(self, node):
        """(scope, name) of a Name or an arg, or None for a builtin."""
        name = node.arg if isinstance(node, ast.arg) else node.id
        s = self.resolve(self.where[node], name)
        return (s, name) if s is not None else None

    def _collect(self):
        self.stores: dict = {}            # key -> how many bindings other than a parameter
        self.assigned: dict = {}          # key -> [values of its plain `name = value` bindings] (LD-51)
        self.arg_keys: set = set()        # the keys parameters bind (LD-51)
        self.attr_assigned: dict = {}     # attribute name -> [values of its plain `x.name = value` stores, a class
        #                                   body's `name = value`, setattr(x, "name", value)] (LD-52)
        self.uses: dict = {}              # key -> [its Name nodes] (LD-52)
        self.loop_extra: dict = {}        # key -> values in `assigned` beyond one per binding (loops, LD-52)
        self.attr_stored: set = set()     # attr_other but a class body's defs (LD-52)
        self.attr_other: set = set()      # attribute names set any other way: x.name += .., unpacking, loops, with,
        #                                   a class body's def or annotation (fields), del (LD-52)
        self.mods: dict = {}              # key -> module name
        self.objs: dict = {}              # key -> [(module, name, object)]
        self.imports: dict = {}           # key -> how many import statements bind it (LD-46)
        self.import_binds: dict = {}      # key -> {what each of them binds: a module's name, or id(the object)}
        self.import_nodes: dict = {}      # key -> [the import statements that bind it] (LD-47)
        self.fdefs: dict = {}             # key -> [def nodes]
        self.cdefs: dict = {}             # key -> [class nodes]
        self.fn: dict = {}                # def / lambda node -> Fn
        self.cls: dict = {}               # class node -> Cls
        self.methods: dict = {}           # name -> [method nodes]
        self.revoked = set()              # methods whose first parameter may be any object (taken unbound)
        for node in self.nodes:            # bindings first: resolve() needs them all
            scope = self.where[node]
            if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load):
                s = scope
                p = self.parent.get(node)
                if isinstance(p, ast.NamedExpr) and p.target is node:
                    while s.kind == "comp":
                        s = s.parent
                self._bind_in(s, node.id)
            elif isinstance(node, ast.arg):
                scope.bound.add(node.arg)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self._bind_in(scope, node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for a in node.names:
                    if a.name != "*":
                        self._bind_in(scope, a.asname or a.name.split(".")[0])
            elif isinstance(node, ast.ExceptHandler) and node.name or isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
                self._bind_in(scope, node.name)
            elif isinstance(node, ast.MatchMapping) and node.rest:
                self._bind_in(scope, node.rest)
        for node in self.nodes:
            scope = self.where[node]

            def count(name, s=scope):
                k = (self.resolve(s, name), name)
                if k[0] is not None:
                    self.stores[k] = self.stores.get(k, 0) + 1
                return k

            if isinstance(node, ast.Assign) and all(isinstance(t, (ast.Name, ast.Attribute)) for t in node.targets):
                for t in node.targets:
                    if isinstance(t, ast.Attribute):
                        self.attr_assigned.setdefault(t.attr, []).append(node.value)
                    else:
                        self.assigned.setdefault(self.key(t), []).append(node.value)
                        if scope.kind == "class":
                            self.attr_assigned.setdefault(t.id, []).append(node.value)
            elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and isinstance(node.target, ast.Name) and \
                    node.value is not None:
                self.assigned.setdefault(self.key(node.target), []).append(node.value)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Attribute) and \
                    node.value is not None:
                self.attr_assigned.setdefault(node.target.attr, []).append(node.value)
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)) and isinstance(node.target, ast.Name) \
                    and isinstance(node.iter, (ast.Tuple, ast.List, ast.Set)) and \
                    not any(isinstance(e, ast.Starred) for e in node.iter.elts):
                self.assigned.setdefault(self.key(node.target), []).extend(node.iter.elts)   # LD-52: a loop over
                self.loop_extra[self.key(node.target)] = \
                    self.loop_extra.get(self.key(node.target), 0) + len(node.iter.elts) - 1   # written-out values
                #                                                     binds one of them each time
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "setattr" and \
                    len(node.args) == 3 and isinstance(node.args[1], ast.Constant) and \
                    isinstance(node.args[1].value, str):
                self.attr_assigned.setdefault(node.args[1].value, []).append(node.args[2])
            if isinstance(node, ast.Attribute) and not isinstance(node.ctx, ast.Load):
                p = self.parent.get(node)
                if not ((isinstance(p, ast.Assign) and node in p.targets) or
                        (isinstance(p, ast.AnnAssign) and p.target is node and p.value is not None)):
                    self.attr_other.add(node.attr)
                    self.attr_stored.add(node.attr)
            elif scope.kind == "class" and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.attr_other.add(node.name)
            elif scope.kind == "class" and isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                self.attr_other.add(node.target.id)          # a field: what builds the object gives it
                self.attr_stored.add(node.target.id)
            elif scope.kind == "class" and isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load) and \
                    not (isinstance(self.parent.get(node), ast.Assign) and node in self.parent[node].targets):
                self.attr_other.add(node.id)
                self.attr_stored.add(node.id)
            if isinstance(node, ast.Name):
                self.uses.setdefault(self.key(node), []).append(node)
            if isinstance(node, ast.arg):
                self.arg_keys.add(self.key(node))
            elif isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load):
                self.stores[self.key(node)] = self.stores.get(self.key(node), 0) + 1
            elif isinstance(node, ast.Import):
                for a in node.names:
                    k = count(a.asname or a.name.split(".")[0])
                    self.imports[k] = self.imports.get(k, 0) + 1
                    self.import_nodes.setdefault(k, []).append(node)
                    self.mods[k] = a.name if a.asname else a.name.split(".")[0]
                    self.import_binds.setdefault(k, set()).add(self.mods[k])
            elif isinstance(node, ast.ImportFrom):
                for a in node.names:
                    if a.name == "*":
                        continue
                    k = count(a.asname or a.name)
                    self.imports[k] = self.imports.get(k, 0) + 1
                    self.import_nodes.setdefault(k, []).append(node)
                    obj = member(node.module, a.name) if node.module and not node.level else _MISSING
                    self.import_binds.setdefault(k, set()).add(obj.__name__ if isinstance(obj, types.ModuleType)
                                                               else (node.module, a.name) if obj is _MISSING else id(obj))
                    if isinstance(obj, types.ModuleType):
                        self.mods[k] = obj.__name__
                    else:
                        self.objs.setdefault(k, []).append((node.module or "", a.name, obj))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.fdefs.setdefault(count(node.name), []).append(node)
            elif isinstance(node, ast.ClassDef):
                self.cdefs.setdefault(count(node.name), []).append(node)
            elif isinstance(node, ast.ExceptHandler) and node.name or isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
                count(node.name)
            elif isinstance(node, ast.MatchMapping) and node.rest:
                count(node.rest)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                f = self.fn[node] = Fn(node, self.inner[node])
                p = self.parent.get(node)
                if isinstance(p, ast.ClassDef) and node in p.body:
                    f.cls = p
                    self.methods.setdefault(node.name, []).append(node)
        for node, f in self.fn.items():        # decorators, now that every import is known (LD-42: by what they are)
            if isinstance(node, ast.Lambda):
                continue
            f.decos = [self.wrapper(d) for d in node.decorator_list]
            f.static, f.classm = "staticmethod" in f.decos, "classmethod" in f.decos
        for node, f in self.fn.items():
            if isinstance(node, ast.Lambda):
                continue
            for d, real in zip(node.decorator_list, f.decos):
                if real is not None:
                    continue
                f.value_used = True                     # the decorator gets the function itself
                if self._accessor(d, f):
                    continue                            # @p.setter: called on an instance, by an assignment
                f.deco_unknown = True                   # the name is whatever the decorator returned
                if f.cls is not None:
                    self.revoked.add(node)              # ... and it got the method unbound
        # functions taken as values: their parameters can be anything
        for node in self.nodes:
            p = self.parent.get(node)
            called = isinstance(p, ast.Call) and p.func is node
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                defs = self.fdefs.get(self.key(node), ())
                prop = isinstance(p, ast.Attribute) and p.attr in ("setter", "getter", "deleter")
                for d in defs:
                    if self.fn[d].cls is not None and not prop:
                        self.revoked.add(d)          # a method named bare in its class body: unbound
                    if not called and not prop:
                        self.fn[d].value_used = True
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load) and not called:
                for d in self.methods.get(node.attr, ()):
                    self.fn[d].value_used = True
            elif isinstance(node, ast.Call) and self._getattr_name(node) is not None:
                pp = self.parent.get(node)
                if not (isinstance(pp, ast.Call) and pp.func is node):
                    for d in self.methods.get(self._getattr_name(node), ()):
                        self.fn[d].value_used = True
        self.regular = {name for name, ds in self.methods.items()
                        if any(not self.fn[d].static and not self.fn[d].classm for d in ds)}
        # `self`: the first parameter of a method, never rebound, the method never taken unbound
        self.own: dict = {}
        for node, f in self.fn.items():
            if f.cls is None or f.static or not f.pos or node in self.revoked:
                continue
            k = (f.scope, f.pos[0].arg)
            if self.stores.get(k, 0) == 0 and f.pos[0].arg not in f.scope.globals | f.scope.nonlocals:
                f.own = True
                self.own[k] = (f.cls, f.classm)
        for node in self.nodes:
            if isinstance(node, ast.ClassDef):
                self._class(node)

    def wrapper(self, d) -> str | None:
        """The name of a decorator that returns the function (or class) wrapped the usual way: the builtins
        staticmethod / classmethod / property, functools' lru_cache / cache / cached_property / total_ordering,
        dataclasses.dataclass, checked by what they are (LD-42: a decorator of the module's own could return
        anything, e.g. an imported class, under the function's name). None for any other."""
        target = d.func if isinstance(d, ast.Call) else d
        if isinstance(target, ast.Name) and self.key(target) is None and \
                target.id in ("staticmethod", "classmethod", "property"):
            return target.id
        kn = self.known(target)
        if kn is not None:
            for m, n in REAL_WRAPPERS:
                real = member(m, n)
                if real is not _MISSING and kn[2] is real:
                    return n
        return None

    def _accessor(self, d, f) -> bool:
        """`@p.setter` (getter, deleter) on a method, p a property of the same class body (every def of p there a
        property or one of its accessors)."""
        if f.cls is None or not (isinstance(d, ast.Attribute) and d.attr in ACCESSORS and isinstance(d.value, ast.Name)):
            return False
        k = self.key(d.value)
        defs = self.fdefs.get(k, ())
        if k is None or k[0] is not self.inner[f.cls] or not defs or self.stores.get(k, 0) != len(defs):
            return False
        prop = False
        for g in defs:
            gd = self.fn[g].decos
            prop |= "property" in gd
            for dd, real in zip(g.decorator_list, gd):
                if real is None and not (isinstance(dd, ast.Attribute) and dd.attr in ACCESSORS and
                                         isinstance(dd.value, ast.Name) and dd.value.id == d.value.id):
                    return False
        return prop

    def _getattr_name(self, call) -> str | None:
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "getattr" and \
                self.key(call.func) is None and len(call.args) >= 2 and isinstance(call.args[1], ast.Constant) \
                and isinstance(call.args[1].value, str):
            return call.args[1].value
        return None

    def _class(self, node) -> Cls:
        if node in self.cls:
            return self.cls[node]
        c = self.cls[node] = Cls()
        c.node, c.user_bases, c.objs, c.unknown, c.tainted, c.attrs = node, [], [], False, False, set()
        c.builtin_bases = []
        kinds = [self.wrapper(d) for d in node.decorator_list]
        c.dataclass = "dataclass" in kinds
        dc_kw = [k for d, kind in zip(node.decorator_list, kinds) if kind == "dataclass" and isinstance(d, ast.Call)
                 for k in d.keywords]
        c.dc_init = not any(k.arg == "init" and not (isinstance(k.value, ast.Constant) and k.value.value is True)
                            for k in dc_kw)    # LD-45: dataclass(init=False) runs a base's __init__
        c.dc_odd = kinds.count("dataclass") > 1 or any(   # LD-48: read only as one decorator, init a bool literal;
            d.args for d, kind in zip(node.decorator_list, kinds)   # LD-49: no **{'init': False}, nothing by position
            if kind == "dataclass" and isinstance(d, ast.Call)) or any(
            k.arg is None or k.arg == "init" and not (isinstance(k.value, ast.Constant) and type(k.value.value) is bool)
            for k in dc_kw)
        c.dc_plain = all(k.arg in DC_PLAIN_KEYWORDS for k in dc_kw)
        c.deco_unknown = any(k not in ("dataclass", "total_ordering") for k in kinds)   # LD-42
        c.fields = [s.target.id for s in node.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)]
        for b in node.bases:
            users = self.base_class(b)
            if users:
                c.user_bases += users
                continue
            plain = self._typing_base(b)
            if plain is not None:                  # NamedTuple, TypedDict, Generic[T], namedtuple(...) (LD-43)
                c.builtin_bases.append(plain)
                continue
            kn = self.known(b)
            if kn is not None and isinstance(kn[2], type):
                c.objs.append(kn[2])
                continue
            if isinstance(b, ast.Name) and self.key(b) is None and isinstance(getattr(builtins, b.id, None), type):
                c.builtin_bases.append(getattr(builtins, b.id))
                continue                       # object, dict, Exception...
            c.unknown = True
        if node.keywords:
            c.unknown = True
        for u in c.user_bases:
            if u is node:
                continue
            ui = self._class(u)
            c.objs += ui.objs
            c.builtin_bases += ui.builtin_bases
            c.unknown |= ui.unknown
            c.attrs |= ui.attrs
            c.fields = ui.fields + c.fields if c.dataclass else c.fields
        for o in c.objs:
            c.attrs |= class_attrs(o)
        c.storage = any(b is not object and b is not typing.Generic and b is not typing.Protocol
                        for b in c.builtin_bases)     # LD-44: a tuple / dict / list / Exception base keeps what the
        #                                               constructor is given (NamedTuple fields, e.args) unread here
        c.tainted = c.unknown or bool(c.objs) or c.storage
        c.enum = any(isinstance(o, type) and issubclass(o, enum.Enum) for o in c.objs)
        for b in c.builtin_bases:                  # LD-45: a dict / list / tuple base's methods (self.get(...))
            if b is not object and b is not typing.Generic and b is not typing.Protocol:
                c.attrs |= class_attrs(b)
        ps = _player_strategy()
        c.fresh_ok = bool(c.objs) and not c.unknown and all(o is ps for o in c.objs)
        return c

    def _typing_base(self, b):
        """A base that only shapes the class (typing.NamedTuple / TypedDict, Generic[...] / Protocol[...],
        collections.namedtuple(...)): the plain type it amounts to, else None."""
        if isinstance(b, ast.Subscript):
            kn = self.known(b.value)
            if kn is not None and any(kn[2] is t for t in (typing.Generic, typing.Protocol)):
                return kn[2]
            return None
        if isinstance(b, ast.Call):
            kn = self.known(b.func)

            def literal(x) -> bool:
                try:
                    ast.literal_eval(x)
                except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                    return False
                return True
            if kn is not None and kn[2] is collections.namedtuple and \
                    all(literal(a) for a in b.args) and all(k.arg is not None and literal(k.value) for k in b.keywords):
                return tuple                    # namedtuple('P', 'x y'), ['x', 'y'], defaults=(0, 0) (LD-44)
            if kn is not None and kn[2] is typing.NamedTuple and len(b.args) == 2 and not b.keywords and \
                    isinstance(b.args[0], ast.Constant) and isinstance(b.args[1], (ast.List, ast.Tuple)) and \
                    all(isinstance(e, ast.Tuple) and len(e.elts) == 2 and isinstance(e.elts[0], ast.Constant) and
                        isinstance(e.elts[1], (ast.Name, ast.Attribute, ast.Subscript, ast.Constant))
                        for e in b.args[1].elts):
                return tuple                    # NamedTuple('P', [('x', int)])
            return None
        kn = self.known(b)
        if kn is not None:
            if kn[2] is typing.NamedTuple:
                return tuple
            if kn[2] is typing.TypedDict:
                return dict
        return None

    # what a name or an expression is

    def modpath(self, node) -> str | None:
        """The module an expression names (`m`, `m.sub`, getattr(m, "sub")), or None."""
        if isinstance(node, ast.Name):
            return self.mods.get(self.key(node))
        a = None
        if isinstance(node, ast.Attribute):
            base, a = node.value, node.attr
        elif self._getattr_name(node) is not None:
            base, a = node.args[0], self._getattr_name(node)
        if a is None:
            return None
        m = self.modpath(base)
        if m is None:
            return None
        obj = member(m, a)
        return obj.__name__ if isinstance(obj, types.ModuleType) else None

    def known(self, node):
        """(module, name, object) for an object named straight from a module, else None."""
        if isinstance(node, ast.Name):
            got = self.objs.get(self.key(node))
            return got[0] if got else None
        a = None
        if isinstance(node, ast.Attribute):
            base, a = node.value, node.attr
        elif self._getattr_name(node) is not None:
            base, a = node.args[0], self._getattr_name(node)
        if a is None:
            return None
        m = self.modpath(base)
        if m is None:
            return None
        obj = member(m, a)
        return None if isinstance(obj, types.ModuleType) else (m, a, obj)

    def static_object(self, node):
        """The object a `name` or `name.attr.attr` bound only by one import names (`moves.PlayCard`, `Craft.FOREST`),
        or _MISSING: for what may be trusted to be that object (LD-46)."""
        attrs = []
        while isinstance(node, ast.Attribute):
            attrs.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return _MISSING
        k = self.key(node)
        if k is None or self.stores.get(k, 0) != 1 or self.imports.get(k, 0) != 1:
            return _MISSING
        if k in self.mods:
            obj = _import(self.mods[k])
        elif len(self.objs.get(k, ())) == 1:
            obj = self.objs[k][0][2]
        else:
            return _MISSING
        for a in reversed(attrs):
            if obj is _MISSING or a.startswith("_"):
                return _MISSING
            if isinstance(obj, types.ModuleType):
                obj = member(obj.__name__, a)
                continue
            try:
                obj = getattr(obj, a)
            except Exception:  # noqa: BLE001
                return _MISSING
        return obj

    def import_root(self, node) -> str | None:
        """The import-bound name an attribute / subscript chain starts from, or None."""
        while isinstance(node, (ast.Attribute, ast.Subscript)):
            node = node.value
        if isinstance(node, ast.Name):
            k = self.key(node)
            if k in self.mods or k in self.objs:
                return node.id
        return None

    def user_class(self, node) -> list:
        if isinstance(node, ast.Name):
            return self.cdefs.get(self.key(node), [])
        return []

    def base_class(self, node) -> list:
        """The module's own classes a base names: `K`, or `K[...]` of an own Generic class (LD-44)."""
        if isinstance(node, ast.Subscript):
            return self.user_class(node.value)
        return self.user_class(node)

    def own_of(self, node):
        """(class node, is the class itself, through super()) when `node` is the strategy's own object."""
        if isinstance(node, ast.Name):
            got = self.own.get(self.key(node))
            return (got[0], got[1], False) if got else None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "super" and \
                self.key(node.func) is None:
            if not node.args and not node.keywords:
                f = self.method_of(node)
                if f is not None and self.fn[f].own:
                    return (self.fn[f].cls, self.fn[f].classm, True)
            elif len(node.args) == 2 and not node.keywords:
                got = self.own_of(node.args[1])
                if got and not got[2]:
                    return (got[0], got[1], True)
        return None

    def method_of(self, node):
        """The method (def directly in a class) whose body `node` is in, through nested functions, or None."""
        s = self.where.get(node)
        while s is not None:
            if s.kind == "function" and isinstance(s.node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                    self.fn[s.node].cls is not None:
                return s.node
            s = s.parent
        return None

    def subclasses(self, c) -> list:
        """Class `c` and the module's classes built on it, directly or not (classes come only from class bodies:
        three-argument type and make_dataclass are refused)."""
        out = [c]
        for d in self.cls:
            if d is not c and c in self.ancestors(d):
                out.append(d)
        return out

    def ancestors(self, c, seen=None) -> set:
        seen = set() if seen is None else seen
        for u in self.cls[c].user_bases:
            if u not in seen:
                seen.add(u)
                self.ancestors(u, seen)
        return seen

    def init_sources(self, c, seen=None) -> list:
        """What constructing class `c` runs with the call's arguments: its own __init__ if it has one (a def node);
        else, a dataclass's generated one (the class node); else, for each of its own bases, the same, down to the
        first class on that branch that has either (LD-45: not every ancestor's __init__, which refused a subclass
        whose __init__ calls super().__init__() with other arguments). A superset of C3's single choice: a diamond's
        order isn't worked out (LD-44)."""
        seen = set() if seen is None else seen
        if c in seen:
            return []
        seen.add(c)
        d = next((s for s in c.body if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)) and s.name == "__init__"),
                 None)
        if d is not None:
            return [d]
        info = self.cls[c]
        if info.dataclass and info.dc_init:
            return [c]
        out = []
        for u in info.user_bases:
            if u is not c:
                out += [x for x in self.init_sources(u, seen) if x not in out]
        return out

    def inits(self, c) -> list:
        """The __init__ defs constructing class `c` may run with the call's arguments (init_sources)."""
        return [x for x in self.init_sources(c) if not isinstance(x, ast.ClassDef)]

    def all_fields(self, c) -> list:
        """Every annotated name of class `c` and of its own ancestors (a dataclass's fields, and more)."""
        out = []
        for k in [c] + sorted(self.ancestors(c), key=lambda n: n.lineno):
            out += [s.target.id for s in k.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)
                    and s.target.id not in out]
        return out

    def dc_positional(self, c) -> list | None:
        """The parameters a dataclass's generated __init__ takes by position, in order (LD-46: exactly, as dataclasses
        does it: a ClassVar or a field(init=False) isn't one, an InitVar is, the fields after a KW_ONLY or with
        kw_only=True come after `*`, a field a subclass annotates again keeps its first place), over a chain of
        single own bases, each a dataclass or a class with no annotations; None when that isn't plain to see (an
        annotation or a default whose kind can't be told: a string under the wrong name, a name not bound by one
        import, a call that could hand back a Field; a dataclass base that isn't the module's own; LD-47: a special
        form's name whose one import doesn't come first at the module's top level, a name annotated twice or bound
        again in the class body, `(x): int`): every field then gets the highest positional argument's level (LD-45),
        and the receipt says so (_name_note). LD-47: a quoted annotation under lazy annotations is kept with its
        quotes, so dataclasses reads it as a plain field."""
        chain, k = [], c
        while k is not None:
            info = self.cls[k]
            if any(isinstance(o, type) and dataclasses.is_dataclass(o) for o in info.objs):
                return None
            if not info.dataclass:
                if any(isinstance(st, ast.AnnAssign) for st in k.body) or k is c:
                    return None
            elif self._dc_kw_only(k) is None:
                return None
            chain.append(k)
            ub = [u for u in info.user_bases if u is not k]
            if len(ub) > 1:
                return None
            k = ub[0] if ub else None
        fields: dict = {}                              # name -> takes it by position (first place kept)
        for k in reversed(chain):
            if not self.cls[k].dataclass:
                continue
            kw_class, marker = self._dc_kw_only(k), False
            for st in k.body:
                if not isinstance(st, ast.AnnAssign):
                    continue
                if not isinstance(st.target, ast.Name) or not st.simple:
                    return None                # `(x): int` isn't in __annotations__: no field (LD-47)
                if self.stores.get(self.key(st.target), 0) != 1:
                    return None                # annotated twice, or bound again in the body (LD-47)
                kind = self._ann_kind(st.annotation, k)
                if kind is None:
                    return None
                if kind == "kw_only":
                    marker = True
                    continue
                positional = kind != "classvar"
                kw = kw_class or marker
                if st.value is not None and kind != "classvar":
                    got = self._default_kind(st.value)
                    if got is None:
                        return None
                    positional = got.get("init", True)
                    kw = got.get("kw_only", kw)
                fields[st.target.id] = positional and not kw
        return [n for n, pos in fields.items() if pos]

    def _dc_kw_only(self, k) -> bool | None:
        """A dataclass's kw_only= (False when not given), or None for a decorator keyword that isn't a plain one."""
        kw_only = False
        for d in k.decorator_list:
            if self.wrapper(d) != "dataclass" or not isinstance(d, ast.Call):
                continue
            if d.args:
                return None
            for kw in d.keywords:
                if kw.arg == "kw_only" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, bool):
                    kw_only = kw.value.value
                elif kw.arg not in DC_PLAIN_KEYWORDS and kw.arg != "init":
                    return None
        return kw_only

    def _named(self, node):
        """What a name or name.attr in an annotation or a default surely is: ("obj", object), ("builtin",),
        ("own",) for a class of the module's own, or None."""
        if isinstance(node, ast.Name) and self.key(node) is None and hasattr(builtins, node.id):
            return ("builtin",)
        if isinstance(node, ast.Name) and (cs := self.cdefs.get(self.key(node))) and \
                self.stores.get(self.key(node), 0) == len(cs):
            return ("own",)
        obj = self.static_object(node)
        return None if obj is _MISSING else ("obj", obj)

    def _ann_kind(self, ann, c) -> str | None:
        """"classvar", "initvar", "kw_only" (the KW_ONLY marker) or "field", as dataclasses reads the annotation of a
        field of class `c`; None when that can't be told."""
        if self.lazy or isinstance(ann, ast.Constant):
            if isinstance(ann, ast.Constant) and isinstance(ann.value, str):
                if self.lazy:                  # kept with its quotes ("'ClassVar[int]'"): dataclasses' reading
                    return "field"             # matches no name (LD-47)
                text = ann.value
            elif isinstance(ann, ast.Constant) and not self.lazy:
                return "field"                 # an object that isn't a string: not a special form
            else:
                text = ast.unparse(ann)        # what the compiler keeps for a lazy annotation (b'..' too)
            m = re.match(r"^(?:\s*(\w+)\s*\.)?\s*(\w+)", text)   # dataclasses' own reading of a string
            if m is None:                                          # annotation (dataclasses._is_type)
                return "field"
            first = self._module_binding(m.group(1) or m.group(2), c)
            if first is None:
                return None
            if first is _MISSING:                      # not a name of the module: dataclasses finds nothing
                return "field"
            if m.group(1) is None:
                return _special_kind(first) or "field"
            for mod, obj, kind in ((typing, typing.ClassVar, "classvar"), (dataclasses, dataclasses.InitVar, "initvar"),
                                   (dataclasses, dataclasses.KW_ONLY, "kw_only")):
                if first is mod and getattr(mod, m.group(2), None) is obj:
                    return kind
            return "field"
        head = ann.value if isinstance(ann, ast.Subscript) else ann
        if isinstance(head, ast.BinOp) or isinstance(ann, ast.BinOp):
            return "field"
        if not isinstance(head, (ast.Name, ast.Attribute)):
            return None
        got = self._named(head)
        if got is None:
            return None
        if got[0] != "obj":
            return "field"
        kind = _special_kind(got[1]) or "field"
        if kind == "kw_only" and isinstance(ann, ast.Subscript):
            return None
        return kind

    def _module_binding(self, name, c):
        """What the module-level `name` surely is (a module or an object) when class statement `c` runs: one import
        binds it; when that is a special form (or typing / dataclasses), at the module's top level, before the
        top-level statement that holds `c` (LD-47: dataclasses looks the name up when the decorator runs; an import
        further down isn't there yet; LD-48: anything else reads as a plain field either way, so an import under
        `if TYPE_CHECKING:` is fine). _MISSING when the module doesn't bind it or only class statements do
        (dataclasses' lookup then finds no special form), None when it can't be told."""
        if name not in self.module.bound:
            return _MISSING
        k = (self.module, name)
        if self.cdefs.get(k) and self.stores.get(k, 0) == len(self.cdefs[k]):
            return _MISSING
        if self.stores.get(k, 0) != 1 or self.imports.get(k, 0) != 1:
            return None
        if k in self.mods:
            obj = _import(self.mods[k])
        elif len(self.objs.get(k, ())) == 1:
            obj = self.objs[k][0][2]
        else:
            return None
        if obj is _MISSING:
            return None
        if (obj is typing or obj is dataclasses or _special_kind(obj)) and \
                not self._runs_before(self.import_nodes[k][0], c):
            return None
        return obj

    def _runs_before(self, stmt, c) -> bool:
        """`stmt` is a statement of the module's top level that has run whenever class statement `c` runs (LD-47)."""
        top = c
        while top is not None and self.parent.get(top) is not self.tree:
            top = self.parent.get(top)
        if top is None or self.parent.get(stmt) is not self.tree:
            return False
        body = [id(x) for x in self.tree.body]
        return body.index(id(stmt)) < body.index(id(top))

    def _default_kind(self, v) -> dict | None:
        """{} for a field default that surely isn't a dataclasses.Field, {"init": .., "kw_only": ..} for a
        dataclasses.field(...) call with written-out keywords, None for anything else (LD-46)."""
        if isinstance(v, ast.Call):
            got = self._named(v.func)
            if got is not None and got[0] == "obj" and got[1] is dataclasses.field:
                if v.args or any(k.arg is None for k in v.keywords):
                    return None
                out = {}
                for k in v.keywords:
                    if k.arg in ("init", "kw_only"):
                        if not (isinstance(k.value, ast.Constant) and isinstance(k.value.value, bool)):
                            return None
                        out[k.arg] = k.value.value
                return out
            if isinstance(v.func, ast.Name) and self.key(v.func) is None and \
                    v.func.id in ("int", "float", "str", "bool", "tuple", "frozenset", "complex"):
                return {}
            if got is not None and got[0] == "obj" and getattr(got[1], "__module__", None) in SCALAR_MODULES:
                return {}
            return None
        if isinstance(v, (ast.Constant, ast.JoinedStr, ast.Lambda, ast.Tuple, ast.List, ast.Set, ast.Dict,
                          ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            return {}
        if isinstance(v, (ast.UnaryOp, ast.BinOp)):
            return {} if _numeric(v) else None
        if isinstance(v, (ast.Name, ast.Attribute)):
            got = self._named(v)
            if got is None:
                return None
            return None if got[0] == "obj" and isinstance(got[1], dataclasses.Field) else {}
        return None

    def built_by(self, call) -> list:
        """The module's own classes a call may construct: `K(...)` (a name only class statements bind) or `cls(...)` in
        a classmethod (the class or one built on it)."""
        f = call.func
        if not isinstance(f, ast.Name):
            return []
        k = self.key(f)
        if k in self.own and self.own[k][1]:
            return self.subclasses(self.own[k][0])
        return list(self.cdefs.get(k, ()))

    def class_methods(self, c, name, seen=None) -> list:
        """The defs of `name` in class `c` or, failing that, in its first user base that has one."""
        seen = set() if seen is None else seen
        if c in seen:
            return []
        seen.add(c)
        found = [s for s in c.body if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)) and s.name == name]
        if found:
            return found
        for u in self.cls[c].user_bases:
            found = self.class_methods(u, name, seen)
            if found:
                return found
        return []

    # levels

    def ext_for(self, info) -> frozenset | None:
        """Method names host code may call on objects of one of the module's own classes: the names the simulator's
        and the ladder's code uses on objects it is handed (duck_names), and for a class built on a class that isn't
        the module's own, every attribute of it and every name its code uses on self (PlayerStrategy's hooks, a
        dict's get, an svsim class's methods and the hooks it expects). None: any name (a base the reading can't
        place, or one that reads self's attributes by a computed name). Per class (LD-43: one NamedTuple made every
        class's methods HOLDS)."""
        if info.unknown:
            return None
        key = id(info)
        if key not in self._ext:
            names = set(duck_names())
            for o in info.objs + info.builtin_bases:
                names |= class_attrs(o)
                more = base_self_names(o)
                if more is None:
                    self._ext[key] = None
                    return None
                names |= more
            self._ext[key] = frozenset(names)
        return self._ext[key]

    def name_rule(self, f) -> bool:
        """`f`'s parameters start as HOLDS only because of its name (renaming it would make them CLEAN)."""
        if f.value_used or f.cls is None or f.node.name == "__init__" or dunder(f.node.name):
            return False
        ext = self.ext_for(self.cls[f.cls])
        return ext is not None and f.node.name in ext

    def _param_base(self, f) -> int:
        """Where a function's parameters start (the calls in the module then raise them): SHARED for a function
        taken as a value; for a method, HOLDS when host code may call it (a name in its class's ext_for, a dunder,
        __init__ of a class with a base that isn't the module's own but PlayerStrategy), else CLEAN like a plain
        function (LD-42: the module's own trees and tables were refused)."""
        if f.value_used:
            return SHARED
        if f.cls is None:
            return CLEAN
        name, info = f.node.name, self.cls[f.cls]
        if name == "__post_init__":
            return SHARED                          # LD-45: InitVars come from any construction, default or replace
        ext = self.ext_for(info)
        if info.enum and (name == "__init__" or dunder(name) or ext is None or name in ext):
            return SHARED                          # LD-45: an Enum's __init__ gets the member values, _missing_ ...
        if name == "__init__":
            return HOLDS if info.unknown or (info.objs and not info.fresh_ok) else CLEAN
        if dunder(name) or ext is None or name in ext:
            return HOLDS
        return CLEAN

    def _init_levels(self):
        for node, f in self.fn.items():
            if f.deco_unknown:
                self._raise_ret(node, SHARED)           # the name holds what the decorator returned (LD-42)
            base = self._param_base(f)
            params = f.pos + f.kwonly + [x for x in (f.vararg, f.kwarg) if x is not None]
            for i, x in enumerate(params):
                if i == 0 and f.own:
                    continue
                if i == 0 and f.cls is not None and not f.static:
                    self._raise(self.key(x), SHARED)    # a `self` that isn't one
                else:
                    self._raise(self.key(x), base)

    def _raise(self, k, v):
        if k is not None and v > self.lv.get(k, CLEAN):
            self.lv[k] = v
            self.changed = True

    def _raise_attr(self, a, v):
        if v > self.attrs.get(a, CLEAN):
            self.attrs[a] = v
            self.changed = True

    def _raise_ret(self, f, v):
        if f is not None and v > self.fn[f].ret:
            self.fn[f].ret = v
            self.changed = True

    def _raise_container(self, node, v):
        if v < HOLDS:
            return
        if isinstance(node, ast.Name):
            self._raise(self.key(node), HOLDS)
            if self.key(node) is not None and self.key(node)[0].kind == "class":
                self._raise_attr(node.id, HOLDS)
        elif isinstance(node, ast.Attribute):
            self._raise_attr(node.attr, HOLDS)
        elif isinstance(node, ast.Subscript):
            self._raise_container(node.value, HOLDS)

    def name_level(self, node) -> int:
        k = self.key(node)
        if k is None:
            return CLEAN
        v = self.lv.get(k, CLEAN)
        if k in self.mods or k in self.objs:
            v = SHARED
        if k in self.own:
            v = max(v, HOLDS if self.cls[self.own[k][0]].tainted else CLEAN)
        for d in self.fdefs.get(k, ()):
            v = max(v, self.fn[d].ret)
        for c in self.cdefs.get(k, ()):
            v = max(v, SHARED if self.cls[c].deco_unknown else HOLDS if self.cls[c].tainted else CLEAN)
        return v

    def self_attr(self, c, a, via_super=False) -> int:
        info = self.cls[c]
        v = CLEAN
        if info.unknown or info.deco_unknown or info.storage or \
                (a in info.attrs and not (info.fresh_ok and a in OWN_FRESH)):
            v = SHARED                                  # storage: what it holds came in by construction (LD-44)
        if not via_super:
            v = max(v, self.attrs.get(a, CLEAN))
        for d in self.methods.get(a, ()):
            v = max(v, self.fn[d].ret)
        return v

    def attr_level(self, base, a) -> int:
        if self.modpath(base) is not None:
            return SHARED
        own = self.own_of(base)
        if own is not None:
            return self.self_attr(own[0], a, own[2])
        users = self.user_class(base)
        if users:
            return max(self.self_attr(c, a) for c in users)
        v = self.attrs.get(a, CLEAN)
        if self.level(base) >= HOLDS:
            v = SHARED
        for d in self.methods.get(a, ()):
            v = max(v, self.fn[d].ret)
        return v

    def level(self, n) -> int:
        if n is None:
            return CLEAN
        v = self._memo.get(n)
        if v is None:
            v = self._memo[n] = self._level(n)
        return v

    def _level(self, n) -> int:
        t = type(n)
        if t is ast.Name:
            return self.name_level(n)
        if t is ast.Attribute:
            return self.attr_level(n.value, n.attr)
        if t is ast.Subscript:
            return elem(self.level(n.value))
        if t is ast.Call:
            return self.call_level(n)
        if t in (ast.List, ast.Tuple, ast.Set):
            return holds(max((self.level(e) for e in n.elts), default=CLEAN))
        if t is ast.Dict:
            return holds(max((self.level(e) for e in n.keys + n.values if e is not None), default=CLEAN))
        if t in (ast.ListComp, ast.SetComp, ast.GeneratorExp):
            return holds(self.level(n.elt))
        if t is ast.DictComp:
            return holds(max(self.level(n.key), self.level(n.value)))
        if t is ast.BinOp:
            return holds(max(self.level(n.left), self.level(n.right)))
        if t is ast.UnaryOp:
            return holds(self.level(n.operand))
        if t is ast.BoolOp:
            return max(self.level(v) for v in n.values)
        if t is ast.IfExp:
            return max(self.level(n.body), self.level(n.orelse))
        if t in (ast.NamedExpr, ast.Starred, ast.Await):
            return self.level(n.value)
        if t is ast.Lambda:
            return self.fn[n].ret
        if t in (ast.Compare, ast.Constant, ast.JoinedStr, ast.FormattedValue, ast.Slice):
            return CLEAN
        return SHARED                       # yield (what is sent in), anything not listed

    def _args_level(self, call, skip_first=False) -> int:
        args = call.args[1:] if skip_first else call.args
        vals = [self.level(a) for a in args] + [self.level(k.value) for k in call.keywords if k.arg != "key"]
        return max(vals, default=CLEAN)

    def call_level(self, call) -> int:
        f = call.func
        args = self._args_level(call)
        if isinstance(f, ast.Name) and self.key(f) is None:                     # a builtin
            n = f.id
            if n in SCALAR_BUILTINS:
                return CLEAN
            if n in FRESH_BUILTINS:
                return holds(args)
            if n in ELEMENT_BUILTINS:
                return elem(args)
            if n == "getattr" and self._getattr_name(call) is not None:
                default = self.level(call.args[2]) if len(call.args) > 2 else CLEAN
                return max(self.attr_level(call.args[0], call.args[1].value), default)
            if n in ("staticmethod", "classmethod", "property"):
                return args
            return SHARED if args >= HOLDS else CLEAN
        if isinstance(f, ast.Name):
            k = self.key(f)
            if k in self.own and self.own[k][1]:          # cls(...) builds the class or one built on it (LD-44)
                return max((SHARED if self.cls[c].deco_unknown else HOLDS if self.cls[c].tainted else CLEAN
                            for c in self.built_by(call)), default=CLEAN)
            defs = len(self.fdefs.get(k, ())) + len(self.cdefs.get(k, ()))
            if defs and self.stores.get(k, 0) == defs:     # only def / class statements bind it
                v = max((self.fn[d].ret for d in self.fdefs.get(k, ())), default=CLEAN)
                for c in self.cdefs.get(k, ()):
                    v = max(v, SHARED if self.cls[c].deco_unknown else HOLDS if self.cls[c].tainted else CLEAN)
                return v
        kn = self.known(f)
        if kn is not None:
            return self._known_call(kn, args, call)
        if isinstance(f, ast.Attribute) or self._getattr_name(f) is not None:
            base, a = (f.value, f.attr) if isinstance(f, ast.Attribute) else (f.args[0], self._getattr_name(f))
            own = self.own_of(base)
            users = [own[0]] if own is not None else self.user_class(base)
            if users:                                   # self.m(...), super().m(...), K.m(...)
                via_super = own is not None and own[2]
                v = max((self.fn[d].ret for d in self.methods.get(a, ())), default=CLEAN)
                for c in users:
                    info = self.cls[c]
                    mine = [] if via_super else self.class_methods(c, a)
                    if via_super:
                        mine = [d for u in info.user_bases if u is not c for d in self.class_methods(u, a)]
                    if not mine and (info.unknown or info.storage or info.deco_unknown or a in info.attrs):
                        v = SHARED                     # inherited from an svsim / ladder class, a dict... (LD-45)
                return v
            r = self.level(base)
            if isinstance(base, ast.Name) and self.key(base) is None and base.id in BUILTIN_TYPES and call.args:
                return max([SHARED if self.level(call.args[0]) >= HOLDS else CLEAN, args])   # dict.get(d, k) (LD-45)
            if r >= SHARED:
                return SHARED
            if a in self.methods:                       # one of the module's own methods (or a namesake)
                v = max(self.fn[d].ret for d in self.methods[a])
                return v if r == CLEAN else SHARED
            if a in SCALAR_METHODS and r == CLEAN:
                return CLEAN
            if a in KEY_METHODS:
                return max(elem(r), self._args_level(call, skip_first=True))
            if a in ("copy", "keys", "values", "items"):
                return r
            return max(elem(r), SHARED if args >= HOLDS else CLEAN)
        fv = self.level(f)
        if fv >= HOLDS:
            return SHARED
        return SHARED if args >= HOLDS else CLEAN

    def _factory(self, node) -> int:
        """What calling a factory (a defaultdict's, a dataclass field's) gives: a standard-library class (not the
        simulator's) or a builtin type makes a new, clean object (LD-42: defaultdict(Counter) was refused)."""
        if isinstance(node, ast.Name) and self.key(node) is None and isinstance(getattr(builtins, node.id, None), type):
            return CLEAN
        kn = self.known(node)
        if kn is not None and isinstance(kn[2], type) and kn[0].split(".")[0] not in ("svsim", "ladder") and \
                fresh_class(kn[2]):
            return CLEAN
        return self.level(node)

    def _known_call(self, kn, args, call=None) -> int:
        mod, name, obj = kn
        top = mod.split(".")[0]
        shared_origin = top in ("svsim", "ladder")
        if obj is _copy.deepcopy or obj is _copy.copy:
            return args             # a copy of a class, a function or an enum member is the thing itself
        if any(obj is x for x in (dataclasses.replace, dataclasses.fields, dataclasses.asdict, dataclasses.astuple)):
            return max(holds(args), HOLDS if obj is not dataclasses.replace else CLEAN)   # fields' .type: a class
        if obj is dataclasses.field and call is not None:  # what an instance gets: the default, or a new one
            v = CLEAN                                     # from the factory (LD-43: default_factory=Counter)
            for kw in call.keywords:
                v = max(v, self._factory(kw.value) if kw.arg == "default_factory" else
                        self.level(kw.value) if kw.arg in ("default", None) else CLEAN)
            return max(v, args if any(isinstance(a, ast.Starred) for a in call.args) else CLEAN)
        if obj is collections.defaultdict and call is not None and call.args and \
                not isinstance(call.args[0], ast.Starred):
            rest = [self.level(a) for a in call.args[1:]] + [self.level(k.value) for k in call.keywords]
            return holds(max([self._factory(call.args[0])] + rest))
        if isinstance(obj, type):
            if fresh_class(obj):
                return HOLDS if shared_origin else holds(args)
            return SHARED
        if shared_origin:
            return CLEAN if scalar_return(obj) else SHARED
        origin = (getattr(obj, "__module__", None) or mod).split(".")[0]
        if ((top in SCALAR_MODULES or origin in SCALAR_MODULES) and name not in NOT_SCALAR) or \
                (top == "bisect" and name.startswith("bisect")):
            return CLEAN
        if top == "itertools" or (top, name) in FRESH_FUNCS:
            return holds(args) if name != "reduce" else elem(args)
        return SHARED if args >= HOLDS else CLEAN

    # one pass of the flow

    def _flow(self, n):
        t = type(n)
        if t is ast.Assign:
            for tg in n.targets:
                self._assign(tg, n.value)
        elif t is ast.AnnAssign:
            if n.value is not None:
                self._assign(n.target, n.value)
        elif t is ast.AugAssign:
            h = holds(self.level(n.value))
            tg = n.target
            if isinstance(tg, ast.Name):
                self._raise(self.key(tg), h)
            elif isinstance(tg, ast.Attribute):
                self._raise_attr(tg.attr, h)
            elif isinstance(tg, ast.Subscript):
                self._raise_container(tg.value, h)
        elif t in (ast.For, ast.AsyncFor, ast.comprehension):
            self._bind(n.target, elem(self.level(n.iter)))
        elif t is ast.withitem:
            if n.optional_vars is not None:
                self._bind(n.optional_vars, self.level(n.context_expr))
        elif t is ast.NamedExpr:
            self._bind(n.target, self.level(n.value))
        elif t is ast.Return:
            if n.value is not None:
                self._raise_ret(self._fn_of(n), self.level(n.value))
        elif t in (ast.Yield, ast.YieldFrom):
            if n.value is not None:
                self._raise_ret(self._fn_of(n), holds(self.level(n.value)))
        elif t is ast.ExceptHandler:
            if n.name:
                self._raise((self.resolve(self.where[n], n.name), n.name), HOLDS)
        elif t is ast.Match:
            v = self.level(n.subject)
            v = max(v, elem(v))
            for case in n.cases:
                for p in ast.walk(case.pattern):
                    name = getattr(p, "name", None) if isinstance(p, (ast.MatchAs, ast.MatchStar)) else \
                        p.rest if isinstance(p, ast.MatchMapping) else None
                    if name:
                        self._raise((self.resolve(self.where[n], name), name), v)
        elif t is ast.Call:
            self._flow_call(n)
        if t is ast.Lambda:
            self._raise_ret(n, self.level(n.body))
        if t in (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda):
            a = n.args
            pos = a.posonlyargs + a.args
            for x, d in zip(pos[len(pos) - len(a.defaults):], a.defaults):
                self._raise(self.key(x), self.level(d))
            for x, d in zip(a.kwonlyargs, a.kw_defaults):
                if d is not None:
                    self._raise(self.key(x), self.level(d))

    def _fn_of(self, node):
        s = self.where.get(node)
        while s is not None and s.kind == "comp":
            s = s.parent
        return s.node if s is not None and s.kind == "function" else None

    def _assign(self, target, value):
        if isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, (ast.Tuple, ast.List)) and \
                len(target.elts) == len(value.elts) and \
                not any(isinstance(e, ast.Starred) for e in target.elts + value.elts):
            for tg, v in zip(target.elts, value.elts):
                self._assign(tg, v)
        else:
            self._bind(target, self.level(value))

    def _bind(self, target, v):
        if isinstance(target, ast.Name):
            k = self.key(target)
            self._raise(k, v)
            if k is not None and k[0].kind == "class":
                self._raise_attr(target.id, v)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for e in target.elts:
                if isinstance(e, ast.Starred):
                    self._bind(e.value, holds(v))
                else:
                    self._bind(e, elem(v))
        elif isinstance(target, ast.Starred):
            self._bind(target.value, holds(v))
        elif isinstance(target, ast.Attribute):
            self._raise_attr(target.attr, v)
        elif isinstance(target, ast.Subscript):
            self._raise_container(target.value, holds(v))

    def targets(self, call) -> list:
        """The module's own functions a call may run, with the offset of the first argument among the parameters."""
        f, out = call.func, []
        if isinstance(f, ast.Name):
            k = self.key(f)
            out += [(d, 0) for d in self.fdefs.get(k, ())]
            seen = set()
            for c in self.built_by(call):                  # K(...), cls(...) (LD-42, LD-43, LD-44)
                for d in self.inits(c):
                    if d not in seen:
                        seen.add(d)
                        out.append((d, 1))
        else:
            a = f.attr if isinstance(f, ast.Attribute) else self._getattr_name(f)
            for d in self.methods.get(a, ()) if a else ():
                out.append((d, 0 if self.fn[d].static else 1))
        return out

    def _literal_keys(self, node):
        """{'k': v, ...} written out (or `a if c else b` of such), as [(key, value node)]; None otherwise."""
        if isinstance(node, ast.IfExp):
            a, b = self._literal_keys(node.body), self._literal_keys(node.orelse)
            return None if a is None or b is None else a + b
        if isinstance(node, ast.Dict) and all(isinstance(k, ast.Constant) and isinstance(k.value, str)
                                              for k in node.keys):
            return [(k.value, v) for k, v in zip(node.keys, node.values)]
        return None

    def _raise_fields(self, fields, positional, args, keywords):
        """Dataclass fields get the levels of the arguments that set them: by name, by position when `positional`
        (dc_positional) says which, else every field the highest positional level (LD-45). `**{'k': v}` written out
        sets k only; any other ** every field (and is noted, see _name_note)."""
        if positional is None or any(isinstance(a, ast.Starred) for a in args):
            v = max((elem(self.level(a.value)) if isinstance(a, ast.Starred) else self.level(a) for a in args),
                    default=CLEAN)
            if v > CLEAN:
                self.dc_rough.add(args[0].lineno)
            for name in fields:
                self._raise_attr(name, v)
        else:
            for name, a in zip(positional, args):
                self._raise_attr(name, self.level(a))
            extra = max((self.level(a) for a in args[len(positional):]), default=CLEAN)
            if extra > CLEAN:                  # more than the reading says it takes: never lose one (LD-47)
                self.dc_rough.add(args[0].lineno)
                for name in fields:
                    self._raise_attr(name, extra)
        for kw in keywords:
            if kw.arg is None:
                pairs = self._literal_keys(kw.value)
                if pairs is not None:
                    for name, v in pairs:
                        self._raise_attr(name, self.level(v))
                else:
                    self.star_fields.add(kw.value.lineno)
                    for name in fields:
                        self._raise_attr(name, elem(self.level(kw.value)))
            else:
                self._raise_attr(kw.arg, self.level(kw.value))

    def _raise_dataclass(self, c, args, keywords):
        """Constructing class `c` (or calling super().__init__ into it): the fields of each dataclass whose generated
        __init__ runs (init_sources) get the arguments' levels (LD-45: an undecorated subclass of a dataclass too)."""
        for x in self.init_sources(c):
            if isinstance(x, ast.ClassDef):
                self._raise_fields(self.all_fields(x), self.dc_positional(x), args, keywords)

    def _raise_params(self, d, off, args, keywords):
        """Raise the parameters of own def `d` (the first `off` of them taken) by the arguments a call gives it."""
        f = self.fn[d]
        pos = f.pos
        named = {x.arg: x for x in pos[off:] + f.kwonly}
        everything = pos[off:] + f.kwonly + [x for x in (f.vararg, f.kwarg) if x is not None]
        i = off
        for a in args:
            if isinstance(a, ast.Starred):
                for x in everything:
                    self._raise(self.key(x), elem(self.level(a.value)))
                continue
            v = self.level(a)
            if i < len(pos):
                self._raise(self.key(pos[i]), v)
            elif f.vararg is not None:
                self._raise(self.key(f.vararg), holds(v))
            i += 1
        for kw in keywords:
            v = self.level(kw.value)
            if kw.arg is None:
                for x in everything:
                    self._raise(self.key(x), elem(v))
            elif kw.arg in named:
                self._raise(self.key(named[kw.arg]), v)
            elif f.kwarg is not None:
                self._raise(self.key(f.kwarg), holds(v))

    def may_be_dataclass(self, c, seen=None) -> bool:
        """Whether class `c`'s objects may be dataclasses when the game runs (LD-51): decorated, or built on one (an
        own class, a host class that is one, or a base the reading can't name), however far up."""
        seen = set() if seen is None else seen
        if c in seen:
            return False
        seen.add(c)
        i = self.cls[c]
        return i.dataclass or i.unknown or any(dataclasses.is_dataclass(o) for o in i.objs) or \
            any(self.may_be_dataclass(u, seen) for u in i.user_bases)

    def surely_host(self, node, visiting=None) -> bool:
        """`node` surely isn't an object of the module's own classes (LD-51, LD-52): what an import names (svsim's
        DEFAULT, ev.THREAT), what a host class builds (Weights(...)), a replace / copy of one, either branch of
        `a if c else b` being one, TABLE[k] / TABLE.get(k, one) of a module dict written out with only these as
        values and only read, a local name every binding of which is one of these (`name = ...`, a loop over a
        written-out tuple of them; not a parameter), an attribute self.x every store of which in the module is one
        of these (`self.x = ...`, a class body's `x = ...`; not a field, a method, x += ..., unpacking).
        A greatest fixed point: a name or attribute met again while it is being decided counts as one (LD-52:
        `w = DEFAULT; w = replace(w, hp=0.8)` binds only replaces of DEFAULT)."""
        visiting = set() if visiting is None else visiting
        if node is None:
            return False
        if self.import_root(node) is not None:
            root = node
            while isinstance(root, (ast.Attribute, ast.Subscript)):
                root = root.value
            k = self.key(root)             # only bound by imports (`DEFAULT = Box()` after the import isn't)
            return self.stores.get(k, 0) == self.imports.get(k, 0)
        if isinstance(node, ast.IfExp):
            return self.surely_host(node.body, visiting) and self.surely_host(node.orelse, visiting)
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load):
            return self._host_table(node.value, visiting)
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr == "get" and 1 <= len(node.args) <= 2 and \
                    not node.keywords and not any(isinstance(a, ast.Starred) for a in node.args):
                return self._host_table(fn.value, visiting) and \
                    (len(node.args) == 2 and self.surely_host(node.args[1], visiting))
            if isinstance(fn, ast.Attribute) and fn.attr == "weights":
                sup = self.own_of(fn.value)        # super().weights(pos): PlayerStrategy's, DEFAULT, when no other
                if sup is not None and sup[2]:     # class of the module has a weights a mixin could put in between
                    return all(self._plain_class(c) for c in self.subclasses(sup[0]) + [sup[0]]) and \
                        all(self.fn[d].cls is sup[0] for d in self.methods.get("weights", ())) and \
                        "weights" not in self.attr_assigned and "weights" not in self.attr_stored
            callee = self._own_callee(fn)
            if callee is not None:                 # an own function or self.method whose every return is one
                return self._returns_host(callee, visiting)
            if self.user_class(fn):
                return False
            kn = self.known(fn)
            if kn is None:
                return False
            if isinstance(kn[2], type):
                return True
            same = _is_replacer(kn[2]) or (kn[0] == "copy" and kn[1] in ("copy", "deepcopy"))
            return same and bool(node.args) and self.surely_host(node.args[0], visiting)
        if isinstance(node, ast.Name):
            k = self.key(node)
            if k is None or self.imports.get(k):
                return False
            if k in visiting:
                return True
            vals = self.assigned.get(k, [])
            if len(vals) - self.loop_extra.get(k, 0) != self.stores.get(k, 0):
                return False
            visiting.add(k)
            if k in self.arg_keys:                 # a module function's parameter: what every call gives it
                if not self._host_param(k, visiting):
                    return False
            elif not vals:
                return False
            return all(self.surely_host(v, visiting) for v in vals)
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            own = self.own_of(node.value)          # self.x / cls.x in a method of a plain class of the module
            a = node.attr
            if own is None or own[2] or not all(self._plain_class(c) for c in self.subclasses(own[0])) or \
                    a in self.attr_other or a in self._own_fields() or a in OWN_FRESH or dunder(a):
                return False
            if ("attr", a) in visiting:
                return True
            visiting.add(("attr", a))         # never stored in the module: only the host sets it
            return all(self.surely_host(v, visiting) for v in self.attr_assigned.get(a, []))
        return False

    def _own_callee(self, fn):
        """The one def a call `f(...)` (a module-level function) or `self.m(...)` (a method of a plain class of the
        module, defined once in the module, never stored over) runs, or None (LD-52)."""
        ok_decos = {None, "lru_cache", "cache", "staticmethod", "classmethod"}
        if isinstance(fn, ast.Name):
            k = self.key(fn)
            defs = self.fdefs.get(k, ())
            if len(defs) != 1 or self.stores.get(k, 0) != 1 or k[0] is not self.module:
                return None
            d = defs[0]
        elif isinstance(fn, ast.Attribute):
            own = self.own_of(fn.value)
            if own is None or own[2] or dunder(fn.attr) or fn.attr in self.attr_assigned or \
                    fn.attr in self.attr_stored or not all(self._plain_class(c) for c in self.subclasses(own[0])):
                return None
            defs = self.methods.get(fn.attr, ())
            if len(defs) != 1 or self.fn[defs[0]].cls not in self.ancestors(own[0]) | {own[0]}:
                return None
            d = defs[0]
        else:
            return None
        f = self.fn[d]
        if f.deco_unknown or any(x not in ok_decos for x in f.decos) or d in self.revoked:
            return None
        return d

    def _returns_host(self, d, visiting) -> bool:
        if isinstance(d, ast.AsyncFunctionDef):
            return False
        if ("ret", d) in visiting:
            return True
        visiting.add(("ret", d))
        rets, gen = [], False
        for n in ast.walk(d):
            if self.where.get(n) is None or self.where[n].node is not d:
                continue                           # nested functions and classes are theirs
            if isinstance(n, (ast.Yield, ast.YieldFrom, ast.Await)):
                gen = True
            elif isinstance(n, ast.Return):
                rets.append(n.value)
        return bool(rets) and not gen and all(v is not None and self.surely_host(v, visiting) for v in rets)

    def _host_param(self, k, visiting) -> bool:
        """Parameter `k` of a module-level function (not a method: the host calls methods by name) that is only
        called directly, each call giving it (or its default) something surely the host's (LD-52)."""
        d = k[0].node
        f = self.fn.get(d)
        if f is None or isinstance(d, ast.Lambda) or f.cls is not None or self.where.get(d) is not self.module or \
                f.value_used or f.deco_unknown or f.decos or d in self.revoked:
            return False
        for use in self.uses.get(self.key_of_def(d), ()):    # only ever called directly: not handed to partial,
            p = self.parent.get(use)                        # map, a default... (the reading can't see those calls)
            if isinstance(use.ctx, ast.Load) and not (isinstance(p, ast.Call) and p.func is use):
                return False
        pos = [x.arg for x in f.pos]
        if k[1] in pos:
            i = pos.index(k[1])
            dflt = d.args.defaults
            default = dflt[i - (len(pos) - len(dflt))] if i >= len(pos) - len(dflt) else None
        elif k[1] in [x.arg for x in f.kwonly]:
            i = None
            default = d.args.kw_defaults[[x.arg for x in f.kwonly].index(k[1])]
        else:
            return False                           # *args, **kw
        if not hasattr(self, "_calls_of"):
            self._calls_of = {}
            for n in self.nodes:
                if isinstance(n, ast.Call):
                    for t, off in self.targets(n):
                        self._calls_of.setdefault(t, []).append((n, off))
        calls = self._calls_of.get(d, [])
        if not calls:
            return False
        for call, off in calls:
            if off or any(isinstance(a, ast.Starred) for a in call.args) or any(kw.arg is None for kw in call.keywords):
                return False
            given = [kw.value for kw in call.keywords if kw.arg == k[1]]
            if i is not None and i < len(call.args):
                given.append(call.args[i])
            if not given:
                given = [default]
            if not all(self.surely_host(g, visiting) for g in given):
                return False
        return True

    def key_of_def(self, d):
        return (self.resolve(self.where[d], d.name), d.name)

    def _plain_class(self, c) -> bool:
        """An own class whose objects get attributes only from the module's code (or PlayerStrategy's): no Enum,
        NamedTuple, tuple / dict / list / exception base, nothing unknown (LD-52)."""
        i = self.cls.get(c) or self._class(c)
        ps = _player_strategy()
        return not (i.unknown or i.storage or i.enum) and all(o is ps for o in i.objs)

    def _own_fields(self) -> set:
        if not hasattr(self, "_fields_cache"):
            self._fields_cache = {f for c in self.cls for f in self.all_fields(c)} | set(self.methods)
        return self._fields_cache

    def _host_table(self, node, visiting) -> bool:
        """`node` names a module-level dict written out once with only host objects as values (surely_host) and
        only read: TABLE[k], TABLE.get(k, ...), nothing else (LD-52)."""
        if not isinstance(node, ast.Name):
            return False
        k = self.key(node)
        if k is None or k[0] is not self.module or k in self.arg_keys or self.imports.get(k):
            return False
        vals = self.assigned.get(k, [])
        if len(vals) != 1 or self.stores.get(k, 0) != 1 or self.loop_extra.get(k) or not isinstance(vals[0], ast.Dict) or \
                any(key is None for key in vals[0].keys):
            return False
        for use in self.uses.get(k, ()):
            p = self.parent.get(use)
            if isinstance(p, ast.Subscript) and p.value is use and isinstance(p.ctx, ast.Load):
                continue
            if isinstance(p, ast.Attribute) and p.value is use and p.attr == "get" and \
                    isinstance(self.parent.get(p), ast.Call) and self.parent[p].func is p:
                continue
            if isinstance(p, ast.Assign) or (isinstance(p, (ast.AnnAssign, ast.NamedExpr)) and p.target is use):
                continue                                        # its own binding
            return False
        if ("table", k) in visiting:
            return True
        visiting.add(("table", k))
        return all(self.surely_host(v, visiting) for v in vals[0].values)

    def _replaced_classes(self, obj) -> list:
        """The module's classes whose __init__ replace(obj, ...) may run (LD-51): those that may be dataclasses
        (an undecorated subclass or a mixin's too), but none when obj surely isn't one of them (surely_host), and
        only K's when obj is K(...)."""
        memo = self.__dict__.setdefault("_host_memo", {})
        if obj not in memo:
            memo[obj] = self.surely_host(obj)
        if memo[obj]:
            return []
        if isinstance(obj, ast.Call):
            own = self.user_class(obj.func)
            if own:
                return [c for c in own if self.may_be_dataclass(c)]
        return [c for c in self.cls if self.may_be_dataclass(c)]

    def _flow_call(self, call):
        for d, off in self.targets(call):
            self._raise_params(d, off, call.args, call.keywords)
        fn = call.func
        for c in self.built_by(call):          # a dataclass of the module: fields from arguments (cls(...) too, LD-44)
            self._raise_dataclass(c, call.args, call.keywords)
        if isinstance(fn, ast.Attribute) and fn.attr == "__init__":
            own = self.own_of(fn.value)        # super().__init__(...) into a dataclass base (LD-45)
            if own is not None and own[2]:
                for u in self.cls[own[0]].user_bases:
                    if u is not own[0]:
                        self._raise_dataclass(u, call.args, call.keywords)
        kn = self.known(fn)
        if kn is not None and _is_replacer(kn[2]):  # replace(obj, field=x): every dataclass's field x
            self._raise_fields(sorted({f for c, i in self.cls.items() if i.dataclass for f in self.all_fields(c)}),
                               None, call.args[1:], call.keywords)
            # LD-50: replace builds the copy with obj's class, so the __init__ a class of the module runs (its
            # own, or a base's under init=False) gets the changes, and every other field obj's attribute of that
            # name. LD-51: any class of the module (an undecorated subclass or a mixin of a dataclass is one too,
            # so is a class built on a host dataclass), but the ones obj can't be: what an import names (svsim's
            # DEFAULT) or a host class builds; K(...) is a K. A **kw parameter gets every field's attribute.
            obj = call.args[0] if call.args and not isinstance(call.args[0], ast.Starred) else None
            given = {k.arg for k in call.keywords if k.arg is not None}
            fields = sorted({f for c in self.cls for f in self.all_fields(c)})
            for c in self._replaced_classes(obj):
                ds = self.inits(c)
                if ds:
                    self.replace_lines.setdefault(call.lineno, set()).add(c.name)
                for d in ds:
                    f = self.fn[d]
                    names = [x.arg for x in f.pos[1:] + f.kwonly]
                    if f.kwarg is not None:
                        names += [a for a in fields if a not in names]
                    rest = [a for a in names if a not in given]
                    kws = list(call.keywords)
                    if obj is not None:
                        kws += [ast.copy_location(ast.keyword(arg=a, value=ast.copy_location(
                            ast.Attribute(value=obj, attr=a, ctx=ast.Load()), obj)), obj) for a in rest]
                    else:                      # replace(*xs): what xs gives, into every parameter
                        kws += [ast.keyword(arg=None, value=call.args[0].value)] if call.args else []
                    self._raise_params(d, 1, call.args[1:], kws)
        if isinstance(fn, ast.Attribute) and fn.attr in ADDERS:
            v = max([self.level(a) for a in call.args] + [self.level(k.value) for k in call.keywords], default=0)
            if isinstance(fn.value, ast.Name) and self.key(fn.value) is None and fn.value.id in BUILTIN_TYPES:
                if call.args:                                   # set.add(s, x)
                    self._raise_container(call.args[0], holds(max([self.level(a) for a in call.args[1:]],
                                                                  default=CLEAN)))
            else:
                self._raise_container(fn.value, holds(v))
        elif isinstance(fn, ast.Attribute) and fn.attr == "setdefault" and len(call.args) >= 2:
            self._raise_container(fn.value, holds(self.level(call.args[1])))
        mut = _mutator_name(self, fn)            # LD-51: an import alias, a= / x= keywords too
        if mut is not None:
            cont, items = _mutator_parts(call, mut)
            if cont is not None and items:
                self._raise_container(cont, holds(max(self.level(a) for a in items)))
        if isinstance(fn, ast.Name) and fn.id == "setattr" and self.key(fn) is None and len(call.args) >= 3 and \
                isinstance(call.args[1], ast.Constant) and isinstance(call.args[1].value, str):
            self._raise_attr(call.args[1].value, self.level(call.args[2]))


# --- the rules ---------------------------------------------------------------------------------------------------

def _numeric(node) -> bool:
    """An expression that is surely a number (so `x += it` can't change a container in place)."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float)) and not isinstance(node.value, bool) or \
            isinstance(node.value, bool)
    if isinstance(node, ast.UnaryOp):
        return _numeric(node.operand)
    if isinstance(node, ast.BinOp):
        return _numeric(node.left) and _numeric(node.right)
    return False


def _floaty(node) -> bool:
    """A number expression that is surely a float (`a_list *= 2` changes the list in place; `*= 0.5` raises)."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, float)
    if isinstance(node, ast.UnaryOp):
        return _floaty(node.operand)
    if isinstance(node, ast.BinOp):
        return isinstance(node.op, ast.Div) or _floaty(node.left) or _floaty(node.right)
    return False


def check_code(src: str, cls: str) -> list[str]:
    """Problems found by reading the code (empty list: none). Nothing is run."""
    try:
        tree = ast.parse(src)
        compile(tree, "<strategy>", "exec", dont_inherit=True)          # scope errors (global after use, ...)
    except SyntaxError as e:
        return [f"语法错误：第 {e.lineno} 行，{e.msg}"]
    except (ValueError, RecursionError, MemoryError) as e:
        return [f"读不了：{type(e).__name__}"]
    try:
        flow = Flow(tree)
    except (RecursionError, MemoryError):
        return ["读不了：嵌套太深"]
    if flow.incomplete:
        return [f"读不了：读了 {FLOW_SECONDS} 秒还没读完（代码太大或太绕）"]
    try:
        return _rules(tree, flow, cls)
    except (RecursionError, MemoryError):          # LD-42: a long chain of attributes
        return ["读不了：嵌套太深"]


def _rules(tree, flow, cls) -> list[str]:
    problems, classes = [], []
    registrars = _registrars()
    lazy_annotations = any(isinstance(n, ast.ImportFrom) and n.module == "__future__" and
                           any(a.name == "annotations" for a in n.names) for n in tree.body)
    annotations = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = n.args
            annotations.update(x.annotation for x in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg]
                               if x is not None and x.annotation is not None)
            if n.returns is not None:
                annotations.add(n.returns)
        elif isinstance(n, ast.AnnAssign):
            annotations.add(n.annotation)

    def bad(node, what):
        msg = f"第 {getattr(node, 'lineno', '?')} 行：{what}"
        if msg not in problems:
            problems.append(msg)

    def parent(node):
        return flow.parent.get(node)

    def receiver(node) -> bool:
        """`node` is only the object of an attribute (`node.x`) or getattr / hasattr's first argument."""
        p = parent(node)
        return (isinstance(p, ast.Attribute) and p.value is node) or \
            (isinstance(p, ast.Call) and isinstance(p.func, ast.Name) and p.func.id in ("getattr", "hasattr")
             and flow.key(p.func) is None and p.args and p.args[0] is node)

    def isinstance_arg(node) -> bool:
        p = parent(node)
        if isinstance(p, ast.Tuple):
            node, p = p, parent(p)
        return isinstance(p, ast.Call) and isinstance(p.func, ast.Name) and p.func.id in ("isinstance", "issubclass") \
            and node in p.args[1:]

    def in_annotation(node) -> bool:
        while node is not None:
            if node in annotations:
                return True
            node = parent(node)
        return False

    def own_enum(c) -> bool:
        """Class `c` of the module's own is an Enum (through its own bases too)."""
        return any(issubclass(o, enum.Enum) for k in [c, *flow.ancestors(c)] for o in flow.cls[k].objs
                   if isinstance(o, type))

    def enum_use(node) -> bool:
        """`node`, an Enum class of the module's own, is only gone through for its members: for / a comprehension,
        K[name], or list(K), sorted(K), max(K, key=...)... (LD-46: through a classmethod's cls too)."""
        p = parent(node)
        if isinstance(p, (ast.For, ast.AsyncFor, ast.comprehension)) and p.iter is node:
            return True
        if isinstance(p, ast.Subscript) and p.value is node and isinstance(p.ctx, ast.Load):
            return True
        return isinstance(p, ast.Call) and p.args and p.args[0] is node and isinstance(p.func, ast.Name) and \
            flow.key(p.func) is None and p.func.id in ENUM_READERS

    def class_use_ok(node) -> bool:
        p = parent(node)
        if (isinstance(p, ast.Call) and p.func is node) or receiver(node) or isinstance(p, (ast.Compare, ast.Raise)):
            return True
        if isinstance(p, ast.MatchClass) and p.cls is node:
            return True                                 # case K(...): an isinstance (LD-42)
        if any(own_enum(c) for c in flow.user_class(node)) and enum_use(node):
            return True                                 # an enum of its own: its members (LD-42)
        if isinstance(p, ast.ClassDef) and node in p.bases:
            return True
        if isinstance(p, ast.Subscript) and p.value is node and isinstance(parent(p), ast.ClassDef) and \
                p in parent(p).bases:
            return True                                 # class B(Own[int]): a generic base of its own (LD-44)
        q = node                                        # class B(Own[Arm]), Own[Arm, int]: a type argument (LD-45)
        while isinstance(parent(q), ast.Tuple) or (isinstance(parent(q), ast.Subscript) and parent(q).slice is q):
            q = parent(q)
            if isinstance(q, ast.Subscript) and flow.base_class(q) and isinstance(parent(q), ast.ClassDef) and \
                    q in parent(q).bases:
                return True
        if isinstance(p, ast.ExceptHandler) or (isinstance(p, ast.Tuple) and isinstance(parent(p), ast.ExceptHandler)):
            return True
        return isinstance_arg(node)

    def type_call(node) -> bool:
        return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "type" and \
            flow.key(node.func) is None

    def class_like(node) -> bool:
        own = flow.own_of(node)
        return bool(flow.user_class(node)) or (own is not None and own[1] and not own[2]) or type_call(node)

    level_hit = []                                 # a refusal because something may be shared (LD-43's note)

    def shared(node, what):
        level_hit.append(node)
        bad(node, what)

    def yield_in_try(node) -> bool:
        """`node` (a yield / await) is inside a try of its own function, outside that try's finally."""
        child, p = node, parent(node)
        while p is not None and not isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef,
                                                   ast.Module)):
            if isinstance(p, (ast.Try, getattr(ast, "TryStar", ast.Try))) and child not in p.finalbody:
                return True
            child, p = p, parent(p)
        return False

    def in_init(node) -> bool:
        m = flow.method_of(node)
        return m is not None and m.name in ("__init__", "__post_init__") and flow._fn_of(node) is m

    def attr_rules(base, a, at, ctx, call, how):
        """The rules for `base.a` (or getattr(base, "a")): ctx "load" / "store" / "del"; `call`: the Call that
        calls it right away, or None; `how`: the text to show."""
        if a in BANNED_ATTRS or banned_dunder(a):
            bad(at, f"{how}（不许用：碰文件、别的进程、调用栈或解释器）")
            return
        if a == "__init__":
            sup = flow.own_of(base)
            if not (sup and sup[2]):
                bad(at, f"{how}：.__init__ 只能写成 super().__init__(...)（对别的对象调 __init__ 会原地改写它，"
                        "包括裁判的走法和卡牌定义）")
            elif not in_init(at):
                bad(at, f"{how}：super().__init__ 只能在 __init__、__post_init__ 里调")
        if ctx != "load" and dunder(a):
            bad(at, f"{how}：双下划线属性不许赋值或删除")
        if a.startswith("_") and not dunder(a) and flow.own_of(base) is None:
            bad(at, f"{how}（别的对象、模块的私有属性不许碰；自己的 self._x 可以）")
        m = flow.modpath(base)
        if m is not None:
            obj = member(m, a)
            why = None
            if m == "random" and a != "Random":
                why = "要随机数用 self.random，不用全局的 random"
            elif numpy_problem(m, a):
                why = numpy_problem(m, a)
            elif isinstance(obj, types.ModuleType):
                why = module_problem(obj.__name__)
            elif m == "ladder":
                why = module_problem(f"ladder.{a}")
            else:
                origin = getattr(obj, "__module__", None)
                if isinstance(origin, str) and any(origin == p or origin.startswith(p + ".") for p in DENIED_PREFIXES):
                    why = f"它来自 {origin}"
                else:
                    why = danger_problem(obj)
            if why:
                bad(at, f"{m}.{a}（{why}）")
            if id(obj) in registrars:
                bad(at, f"{m}.{a}（注册卡牌脚本会改模拟器）")
        if ctx != "load":
            root = flow.import_root(base)
            if root is not None:
                bad(at, f"给 {root} 里的东西赋值或删除（不许改模块、引擎、卡牌里的东西）")
            elif flow.level(base) >= SHARED:
                shared(at, f"{how}：不许改可能共用的对象（从 svsim / ladder 拿来或读出来的东西；"
                           "要改就自己做一份：list(x)、dict(x)、dataclasses.replace(x, ...)）")
        if ctx == "load" and a in MUTATORS and not (flow.modpath(base) or "").startswith("numpy"):
            kn = flow.known(base)               # np.add, np.sort, np.subtract: numpy's functions (LD-47; np.put and
                                                # the out= of a ufunc: _written_args)
            unbound = (isinstance(base, ast.Name) and flow.key(base) is None and base.id in BUILTIN_TYPES) or \
                class_like(base) or (kn is not None and isinstance(kn[2], type))
            if flow.level(base) >= SHARED:
                shared(at, f"{how}：不许改可能共用的容器（要改就自己做一份：list(x)、dict(x)、dataclasses.replace(x, ...)）")
            elif unbound and not (call is not None and call.args and not isinstance(call.args[0], ast.Starred)
                                  and flow.level(call.args[0]) < SHARED):
                bad(at, f"{how}：不许改可能共用的容器")
        if a in flow.regular and class_like(base):
            bad(at, f"{how}：普通方法不许经类调（K.method(x) 能把任何对象当 self）")
        if a == "register" and ctx == "load" and not own_function(base):
            bad(at, f"{how}：register 只许用在你自己的 functools.singledispatch 函数上（抽象基类的 register 改的是"
                    "整个进程的 isinstance，后面别人的对局也受影响，LD-46）")

    mutators = [o for m, n in CLASS_MUTATORS if (o := member(m, n)) is not _MISSING]
    defs = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

    def as_decorator(node) -> bool:
        """`node` is a decorator of a def or class: @x or @x(...)."""
        p = parent(node)
        if isinstance(p, ast.Call) and p.func is node:
            node, p = p, parent(p)
        return isinstance(p, defs) and node in p.decorator_list

    def class_value_ok(v) -> bool:
        """A possibly shared value may be a class attribute when it is a name straight from a module (static_object)
        whose object isn't a dataclasses.Field and has no __set_name__, or a dataclasses.field(...) whose default is
        one (LD-46: the class statement calls __set_name__, @dataclass rewrites a Field it finds in place)."""
        if isinstance(v, ast.Call) and (kn := flow.known(v.func)) is not None and kn[2] is dataclasses.field:
            return all(k.arg is not None and (k.arg != "default" or flow.level(k.value) < SHARED or class_value_ok(k.value))
                       for k in v.keywords) and not v.args
        obj = flow.static_object(v)
        return obj is not _MISSING and not isinstance(obj, dataclasses.Field) and \
            not hasattr(type(obj), "__set_name__")

    def in_class_body(node) -> bool:
        s = flow.where.get(node)
        while s is not None and s.kind == "comp":
            s = s.parent
        return s is not None and s.kind == "class"

    def own_function(node) -> bool:
        """`node` names a def of the module's own, bound only by def statements, each plain or a
        functools.singledispatch / singledispatchmethod (whose .register is its own, LD-46)."""
        if not isinstance(node, ast.Name):
            return False
        k = flow.key(node)
        defs = flow.fdefs.get(k, ())
        ok = (member("functools", "singledispatch"), member("functools", "singledispatchmethod"))
        return bool(defs) and flow.stores.get(k, 0) == len(defs) and \
            all(all((kn := flow.known(d)) is not None and any(kn[2] is o for o in ok) for d in x.decorator_list)
                for x in defs)

    compound = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, getattr(ast, "TryStar", ast.Try), ast.With,
                ast.AsyncWith, getattr(ast, "Match", ast.If))
    for node in flow.nodes:
        p = parent(node)
        if isinstance(node, compound) and isinstance(p, ast.ClassDef) and node in p.body:
            bad(node, f"类 {p.name} 的类体里不许写 if / for / while / try / with / match：方法、字段、类属性直接写在类里"
                      "（读代码只认直接写在类里的，LD-45）")
        if isinstance(node, (ast.Import, ast.ImportFrom)) and isinstance(p, ast.ClassDef):
            bad(node, f"类 {p.name} 的类体里不许 import：写在模块顶上（LD-46）")
        if isinstance(node, ast.ClassDef) and (ci := flow.cls.get(node)) is not None and ci.dc_odd:
            bad(node, f"类 {node.name}：只许一个 dataclass 装饰器，参数只许按名字写（不许 **字典、不许按位置），它的 init= "
                      "只许写 True 或 False（读代码要看清有没有生成的 __init__，LD-48、LD-49）")
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(p, ast.ClassDef) and node.value is not None:
            v = flow.level(node.value)
            if isinstance(node, ast.Assign) and any(not isinstance(t, ast.Name) for t in node.targets):
                v = max(v, elem(v))                     # a, b = x: each gets an item
            if v >= SHARED and not class_value_ok(node.value):
                shared(node, f"类 {p.name} 的类属性：可能共用的东西只许直接写模块里的名字（moves.PlayCard、Craft.FOREST 这样），"
                             "算出来、取出来的不行——建类时 Python 会调它的 __set_name__，@dataclass 会原地改写拿到的 "
                             "dataclasses.Field（LD-46）；放进 __init__（self.x = ...）或者用的地方再取")
        bound = None
        if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load):
            bound = flow.key(node), node.id
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound = (flow.resolve(flow.where[node], node.name), node.name), node.name
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
            bound = (flow.resolve(flow.where[node], node.name), node.name), node.name
        elif isinstance(node, ast.MatchMapping) and node.rest:
            bound = (flow.resolve(flow.where[node], node.rest), node.rest), node.rest
        if bound is not None and bound[0] in flow.imports:
            bad(node, f"{bound[1]} 是 import 进来的名字，不许再赋值、删除或拿来定义函数、类（读代码按 import 的东西认它，LD-46）")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                k = (flow.resolve(flow.where[node], a.asname or a.name.split(".")[0]), a.asname or a.name.split(".")[0])
                if len(flow.import_binds.get(k, ())) > 1:
                    bad(node, f"{k[1]} 被 import 了不止一次、指的不是同一个东西：换个名字（LD-46）")
        if isinstance(node, ast.NamedExpr) and in_class_body(node):
            bad(node, "类体里不许写 :=（它把值放成类属性，读代码跟不上，LD-46）")
        if (isinstance(node, (ast.Name, ast.Attribute)) and isinstance(node.ctx, ast.Load) or    # LD-46: getattr(m,
                flow._getattr_name(node) is not None) and \
                (kn := flow.known(node)) is not None and any(kn[2] is o for o in mutators) and not as_decorator(node):
            bad(node, f"{kn[1]} 只能当装饰器写在你自己的类或函数上（@{kn[1]}）：直接调用会改它拿到的类或函数"
                      "（LD-45；getattr 写法同样，LD-46）")
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and (o := flow.own.get(flow.key(node))) and \
                o[1] and not (receiver(node) or isinstance(p, ast.Compare) or isinstance_arg(node) or
                              (own_enum(o[0]) and enum_use(node)) or
                              (isinstance(p, ast.Call) and (p.func is node or (isinstance(p.func, ast.Name) and
                                                                                 p.func.id in ("super", "issubclass")
                                                                                 and flow.key(p.func) is None)))):
            bad(node, f"{node.id}（classmethod 的类）只能用来建实例（{node.id}(...)）、读类属性、比较、isinstance"
                      f"（枚举还可以 for m in {node.id}、{node.id}[名字]、list({node.id})），不许当值传（LD-45）")
        if isinstance(node, ast.ClassDef) and isinstance(p, ast.ClassDef):
            bad(node, f"类 {node.name} 定义在类 {p.name} 里面：写到模块顶层（{p.name}.{node.name}(...) 这样建对象，"
                      "读代码跟不上它的 __init__，LD-44）")
        if isinstance(node, ast.Import):
            for a in node.names:
                why = module_problem(a.name)
                if why:
                    bad(node, f"import {a.name}（{why}）")
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                bad(node, "相对 import（一个成员只交一个模块）")
                continue
            mod = node.module or ""
            why = None if mod == "ladder" else module_problem(mod)     # `from ladder import x`: checked per name
            if why:
                bad(node, f"from {mod} import ...（{why}）")
                continue
            for a in node.names:
                if a.name == "*":
                    bad(node, f"from {mod} import *")
                    continue
                full = f"{mod}.{a.name}"
                obj = member(mod, a.name)
                if a.name.startswith("_") and not dunder(a.name):
                    bad(node, f"from {mod} import {a.name}（私有名字不许拿）")
                if mod == "ladder" and full not in ALLOWED_LADDER:
                    bad(node, f"from {mod} import {a.name}（{module_problem(full)}）")
                elif isinstance(obj, types.ModuleType) and module_problem(obj.__name__):
                    bad(node, f"from {mod} import {a.name}（{module_problem(obj.__name__)}）")
                elif any(full == p_ or full.startswith(p_ + ".") for p_ in DENIED_PREFIXES):
                    bad(node, f"from {mod} import {a.name}（{module_problem(full)}）")
                else:
                    origin = getattr(obj, "__module__", None) if not isinstance(obj, types.ModuleType) else None
                    if isinstance(origin, str) and any(origin == q or origin.startswith(q + ".")
                                                       for q in DENIED_PREFIXES):
                        bad(node, f"from {mod} import {a.name}（它来自 {origin}）")
                    elif danger_problem(obj):
                        bad(node, f"from {mod} import {a.name}（{danger_problem(obj)}）")
                if mod == "random" and a.name != "Random":
                    bad(node, f"from random import {a.name}（要随机数用 self.random，不用全局的 random）")
                if numpy_problem(mod, a.name):
                    bad(node, f"from {mod} import {a.name}（{numpy_problem(mod, a.name)}）")
                if a.name in BANNED_NAMES or a.name in BANNED_ATTRS or banned_dunder(a.name):
                    bad(node, f"from {mod} import {a.name}（这个名字不许用）")
                if id(obj) in registrars:
                    bad(node, f"from {mod} import {a.name}（注册卡牌脚本会改模拟器）")
        elif isinstance(node, ast.Name):
            if node.id in BANNED_NAMES or banned_dunder(node.id):
                bad(node, f"{node.id}（不许用：碰文件、动态执行或解释器）")
                continue
            if not isinstance(node.ctx, ast.Load):
                if dunder(node.id):
                    bad(node, f"{node.id}：双下划线名字不许赋值")
                continue
            k = flow.key(node)
            if k is None and node.id in ATTR_FUNCS and not (isinstance(p, ast.Call) and p.func is node):
                bad(node, f"{node.id} 只能直接调用")
            if not (isinstance(p, ast.Call) and p.func is node) and _direct_only(flow, node):
                bad(node, f"{node.id}（{_direct_only(flow, node)}）只能直接调用：当值用（赋给别的名字、默认参数、"
                          "functools.partial、map）读代码就看不到它改了什么、放进了什么（LD-51）")
            if k in flow.mods and not receiver(node):
                bad(node, f"模块 {node.id} 不许当值用（只能写 {node.id}.属性）")
            if flow.cdefs.get(k) and not class_use_ok(node):
                if not in_annotation(node):
                    bad(node, f"类 {node.id} 只能用来建实例、读类属性、isinstance、继承、raise / except、比较、"
                              "match 的 case、类型标注")
                elif not lazy_annotations:              # LD-42: an evaluated annotation hands the class out
                    bad(node, f"类 {node.id} 写在类型标注里：模块开头要有 from __future__ import annotations"
                              f"（标注就不会被求值），或者写成字符串 '{node.id}'")
            if any(id(o) in registrars for _, _, o in flow.objs.get(k, ())):
                bad(node, f"{node.id}（注册卡牌脚本会改模拟器）")
        elif isinstance(node, ast.Attribute):
            ctx = "load" if isinstance(node.ctx, ast.Load) else "store" if isinstance(node.ctx, ast.Store) else "del"
            call = p if isinstance(p, ast.Call) and p.func is node else None
            attr_rules(node.value, node.attr, node, ctx, call, f".{node.attr}")
            if ctx == "load" and call is None and _direct_only(flow, node):
                bad(node, f"{ast.unparse(node)} 只能直接调用：当值用（赋给别的名字、默认参数、functools.partial、map）"
                          "读代码就看不到它改了什么、放进了什么（LD-51）")
            if ctx == "load" and flow.modpath(node) is not None and not receiver(node):
                bad(node, f"模块 {flow.modpath(node)} 不许当值用（只能写 模块.属性）")
        elif isinstance(node, ast.Subscript):
            if not isinstance(node.ctx, ast.Load):
                root = flow.import_root(node.value)
                if root is not None:
                    bad(node, f"给 {root} 里的东西赋值或删除（不许改模块、引擎、卡牌里的东西）")
                elif flow.level(node.value) >= SHARED:
                    shared(node, "x[...] = / del：不许改可能共用的对象（从 svsim / ladder 拿来或读出来的东西；"
                                 "要改就自己做一份：list(x)、dict(x)、dataclasses.replace(x, ...)）")
        elif isinstance(node, ast.AugAssign):
            if flow.level(node.target) >= SHARED and not (_numeric(node.value) and
                                                          (not isinstance(node.op, ast.Mult) or _floaty(node.value))):
                shared(node, "x += ...：x 可能是共用的对象，原地运算会改它（写成 x = x + ...；"
                             "加减一个数字可以，乘一个小数常量可以，乘整数不行：列表 *= 0 会原地清空）")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and banned_dunder(node.name):
            bad(node, f"def {node.name}（自己定义双下划线方法不许，__init__、__post_init__ 除外）")
        elif isinstance(node, (ast.Yield, ast.YieldFrom, ast.Await)) and yield_in_try(node):
            bad(node, "yield 写在 try 里（try 的正文、except、else）：生成器被丢掉时那里的 except / finally 会在"
                      "别的时候、不在任何时钟上跑（LD-42）。先算好再 yield，或者把 try 放到 yield 前面")
        elif isinstance(node, ast.Call):
            fn = node.func
            builtin = isinstance(fn, ast.Name) and flow.key(fn) is None
            for kw in node.keywords:
                if kw.arg in BANNED_KEYWORDS:
                    bad(node, f"参数 {kw.arg}=（并行搜索开别的进程，不许）")
            if builtin and fn.id in ATTR_FUNCS:
                name = node.args[1] if len(node.args) >= 2 else None
                if not (isinstance(name, ast.Constant) and isinstance(name.value, str)) or \
                        any(isinstance(a, ast.Starred) for a in node.args) or node.keywords:
                    bad(node, f"{fn.id} 的属性名要写死成字符串")
                    continue
                ctx = {"setattr": "store", "delattr": "del"}.get(fn.id, "load")
                if ctx != "load" and dunder(name.value):
                    bad(node, f"{fn.id}(..., {name.value!r})（双下划线属性不许改）")
                    continue
                if name.value in BANNED_ATTRS or banned_dunder(name.value) or name.value == "__init__":
                    bad(node, f"{fn.id}(..., {name.value!r})（这个属性不许碰）")
                    continue
                pp = parent(node)
                call = pp if isinstance(pp, ast.Call) and pp.func is node else None
                attr_rules(node.args[0], name.value, node, ctx, call, f"{fn.id}(..., {name.value!r})")
                if fn.id == "getattr" and call is None and _direct_only(flow, node):
                    bad(node, f"{ast.unparse(node)} 只能直接调用（LD-51）")
                if fn.id == "getattr" and flow.modpath(node) is not None and not receiver(node):
                    bad(node, f"模块 {flow.modpath(node)} 不许当值用（只能写 模块.属性，LD-46）")
                if fn.id in ("setattr", "delattr") and flow.modpath(node.args[0]) is not None:
                    bad(node, f"{fn.id}({ast.unparse(node.args[0])}, ...)（不许改模块里的东西）")
            elif builtin and fn.id == "type":
                if len(node.args) != 1 or node.keywords:
                    bad(node, "type(名字, 基类, 字典)：不许这样造类")
                elif not (receiver(node) or isinstance(p, ast.Compare) or isinstance_arg(node)):
                    bad(node, "type(x) 只能用来读属性（如 .__name__）、比较、isinstance")
            mc = _as_call(node, node.args[0], node.args[1:]) if _partial(flow, node) else node
            name = _mutator_name(flow, mc.func)    # LD-51: an import alias, functools.partial, a= / x= keywords
            at = _arg_at(flow, mc.func)            # LD-49: Generator.shuffle(rng, x) changes x; LD-50: type(r).shuffle
            if name is not None:
                ckw = _MUTATOR_KW.get(name)
                conts = [mc.args[i] for i in at if i < len(mc.args)] + [k.value for k in mc.keywords if k.arg == ckw]
                if any(isinstance(a, ast.Starred) for a in mc.args[:max(at) + 1]) or \
                        any(k.arg is None for k in mc.keywords) or any(flow.level(a) >= SHARED for a in conts):
                    shared(node, f"{name}(...)：不许改可能共用的容器（要改就自己做一份：list(x)、dict(x)、"
                                 "dataclasses.replace(x, ...)）")
            kr = flow.known(fn)
            if kr is not None and _is_replacer(kr[2]) and node.args and isinstance(node.args[0], ast.Starred):
                bad(node, f"{ast.unparse(fn)}(*...)：replace 的对象要直接写出来，不许用 *（LD-51）")
            for dest, how in _written_args(flow, node):          # numpy writing into an argument (LD-47, LD-48)
                if flow.import_root(dest) is not None or flow.level(dest) >= SHARED:
                    shared(node, f"{how}：不许让 numpy 写进可能共用的数组（numpy 自己模块和类里的数组整个进程共用，"
                                 "后面别人的对局也受影响；写进你自己建的数组" +
                           ("；不是 numpy 的函数，就把参数 out 换个名字" if how == "out=" else "") + "，LD-47）")
        elif isinstance(node, ast.ClassDef) and isinstance(p, ast.Module):
            classes.append(node.name)
    if cls not in classes:
        problems.append(f"模块顶层没有类 {cls}")
    if level_hit:
        problems += _name_note(flow)
    return problems


_OUT_AT: dict = {}
_METHOD_OUT: dict = {}


def _params(obj) -> list | None:
    """The names of the parameters a numpy function or method takes by position, without self: from its signature,
    else from the first line of its docstring (numpy 1.26's C functions and ndarray methods have no signature)."""
    try:
        names = [p.name for p in inspect.signature(obj).parameters.values()
                 if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)]
    except (TypeError, ValueError):
        lines = (getattr(obj, "__doc__", None) or "").strip().splitlines()
        m = re.match(r"^\s*[\w.]*\((.*)\)", lines[0]) if lines else None
        if m is None:
            return None
        names, depth, cur = [], 0, ""
        for ch in m.group(1) + ",":
            depth += (ch in "([{") - (ch in ")]}")
            if ch == "," and depth == 0:
                p, cur = cur.strip().split("=")[0].strip(), ""
                if p.startswith("*"):
                    break
                if p != "/":
                    names.append(p)
            else:
                cur += ch
    except Exception:  # noqa: BLE001 - a signature that can't be made
        return None
    return names[1:] if names and names[0] == "self" else names


def _out_at(obj) -> int | None:
    """Where a numpy function or method takes `out` by position (LD-48: np.clip(a, lo, hi, out)), or None."""
    k = id(obj)
    if k not in _OUT_AT:
        names = _params(obj) if callable(obj) else None
        _OUT_AT[k] = names.index("out") if names and "out" in names else None
    return _OUT_AT[k]


def _method_out() -> dict:
    """{method name: {where it takes out by position}} over numpy's ndarray, Generator and RandomState (LD-48)."""
    if not _METHOD_OUT:
        _METHOD_OUT["?"] = set()
        for mod, name in (("numpy", "ndarray"), ("numpy.random", "Generator"), ("numpy.random", "RandomState")):
            t = member(mod, name)
            if isinstance(t, type):
                for a in dir(t):
                    i = None if a.startswith("_") else _out_at(getattr(t, a, None))
                    if i is not None:
                        _METHOD_OUT.setdefault(a, set()).add(i)
                if name == "ndarray":
                    _METHOD_OUT.setdefault("dot", set()).add(1)   # a.dot(b, out): numpy 1.26 gives it no docstring
                    for a, at in METHOD_OUT_FIX.items():
                        _METHOD_OUT[a] = set(at)
                        if not at:
                            del _METHOD_OUT[a]
    return _METHOD_OUT


def _call_name(flow, fn) -> str | None:
    """The name a call calls: `f(...)`, `x.f(...)`, `getattr(x, 'f')(...)` (LD-50)."""
    if isinstance(fn, ast.Attribute):
        return fn.attr
    if isinstance(fn, ast.Name):
        return fn.id
    return flow._getattr_name(fn)


def _is_replacer(o) -> bool:
    """dataclasses.replace or copy.replace, by identity (an array's == wouldn't give one answer)."""
    return any(o is r for r in REPLACERS)


_MUTATOR_KW = {"shuffle": "x", "insort": "a", "insort_left": "a", "insort_right": "a"}   # LD-51: the container by
#   keyword (random.Random.shuffle(x=L), Generator.shuffle(x=W), bisect.insort(a=h, x=v)); heapq's take none


def _mutator_name(flow, fn) -> str | None:
    """The shuffle-like function (ARG_MUTATORS) a call calls: by the name written (an own method of that name too),
    or (LD-51) by what an imported name is (`from heapq import heappush as push`)."""
    name = _call_name(flow, fn)
    if name in ARG_MUTATORS:
        return name
    if isinstance(fn, ast.Name):
        for _, n, _o in flow.objs.get(flow.key(fn), ()):
            if n in ARG_MUTATORS:
                return n
    return None


def _mutator_parts(call, name):
    """(the container, the items put in) of a heappush / insort-like call (LD-51: by keyword too); (None, []) when
    the call can't be read that way (a *xs, a **d: the rule refuses those on what may be shared)."""
    ckw = _MUTATOR_KW.get(name)
    if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None for k in call.keywords):
        return None, []
    pos = list(call.args)
    if pos:
        return pos[0], pos[1:] + [k.value for k in call.keywords]
    return next((k.value for k in call.keywords if k.arg == ckw), None), [k.value for k in call.keywords if k.arg != ckw]


def _direct_only(flow, node) -> str | None:
    """LD-51: dataclasses.replace / copy.replace and heapq's and bisect's functions that change their first argument
    are only called directly, where the reading sees what they get: as a value (r = dataclasses.replace, a default,
    functools.partial, map) they'd take it unseen. Gives the name, or None."""
    if isinstance(node, ast.Name):
        got = list(flow.objs.get(flow.key(node), ()))
    else:
        kn = flow.known(node)
        got = [kn] if kn is not None else []
    for m, n, o in got:
        if _is_replacer(o) or (m in ("heapq", "bisect") and n in ARG_MUTATORS):
            return f"{m}.{n}"
    return None


def _receiver(flow, fn):
    """What a method call is called on: `x` of `x.f(...)` and of `getattr(x, 'f')(...)`, else None."""
    if isinstance(fn, ast.Attribute):
        return fn.value
    return fn.args[0] if flow._getattr_name(fn) is not None else None


def _arg_at(flow, fn) -> tuple:
    """Where the container a shuffle-like call changes sits: 0 for a function or a method of an instance, 1 for a
    method called through its class (LD-49: np.random.Generator.shuffle(rng, x)); both when the receiver may be a
    class the reading can't name (LD-50: type(r).shuffle(r, x), R = random.Random; R.shuffle(r, x), getattr)."""
    recv = _receiver(flow, fn)
    if recv is None or flow.modpath(recv) is not None:
        return (0,)
    o = flow.static_object(recv)
    if isinstance(o, type):
        return (1,)
    return (0,) if o is not _MISSING else (0, 1)


def _partial(flow, call) -> bool:
    """`functools.partial(f, ...)` / partialmethod: what it is given goes to `f` when the result is called (LD-49)."""
    kn = flow.known(call.func)
    return kn is not None and kn[0] == "functools" and kn[1] in ("partial", "partialmethod") and \
        bool(call.args) and not isinstance(call.args[0], ast.Starred)


def _as_call(call, f, args):
    """A call of `f` with `args` and `call`'s keywords, standing for what `call` hands on (LD-49)."""
    return ast.copy_location(ast.Call(func=f, args=list(args), keywords=list(call.keywords)), call)


def _may_be_numpy(flow, call) -> bool:
    """Whether a call may be numpy's, so its out= is read as numpy's (LD-48): not a class or function of the module's
    own, not a builtin, not a function of a module other than numpy (functools.partial: what it wraps, LD-49), not a
    method of a literal."""
    f = call.func
    if _partial(flow, call):
        return _may_be_numpy(flow, _as_call(call, call.args[0], call.args[1:]))
    if flow.built_by(call):
        return False
    if isinstance(f, ast.Name):
        k = flow.key(f)
        if k is None or k in flow.fdefs:
            return False
        if flow.imports.get(k):
            kn = flow.known(f)
            return kn is None or kn[0].split(".")[0] == "numpy"
        return True                                    # a variable: could hold a numpy function
    if isinstance(f, ast.Attribute):
        m = flow.modpath(f.value)
        if m is not None:
            return m.split(".")[0] == "numpy"
        return not isinstance(f.value, (ast.Constant, ast.JoinedStr, ast.List, ast.Tuple, ast.Dict, ast.Set,
                                        ast.ListComp, ast.SetComp, ast.DictComp))
    return True


def _special_kind(obj) -> str | None:
    """"classvar", "initvar" or "kw_only" when dataclasses takes `obj` for that special form (its own tests:
    ClassVar or ClassVar[...], InitVar or InitVar[...], KW_ONLY), else None (LD-48)."""
    if obj is typing.ClassVar or (type(obj) is getattr(typing, "_GenericAlias", None) and
                                  getattr(obj, "__origin__", None) is typing.ClassVar):
        return "classvar"
    if obj is dataclasses.InitVar or type(obj) is dataclasses.InitVar:
        return "initvar"
    if obj is dataclasses.KW_ONLY:
        return "kw_only"
    return None


def _written_args(flow, call) -> list:
    """The arguments a call writes into, or makes an array over, the way numpy does (LD-47, LD-48), as [(node, how)]:
    out= of a call that may be numpy's (_may_be_numpy; out=(a, b) writes a and b, **{'out': x} too); a known numpy
    function's or a numpy method's out given by position (np.clip(a, lo, hi, out), w.cumsum(0, None, out),
    rng.random(2, np.float64, out); a method name the module's own methods also use is left to the tripwire); a known
    ufunc's positional outputs after its inputs (np.negative(x, x)), what a *xs of a numpy call gives; the array of
    ufunc.at and the out of reduce / accumulate / reduceat; the first argument of copyto, place, putmask,
    fill_diagonal, put_along_axis, put, frombuffer, nditer and of nan_to_num(copy=False), the buffer of np.ndarray.
    LD-49: what functools.partial hands on, read as a call of what it wraps; a method called through its class
    (np.ndarray.sum(a, 0, None, out)) counts its positions after the object; argument 0 of median / percentile /
    quantile (and nan versions) with overwrite_input, and of nan_to_num with copy false, by keyword or position; the
    parameters numpy updates in place (NUMPY_INPLACE_PARAMS).
    The tripwire compares every array numpy's modules and classes hold, so what is written through a container or an
    alias the reading doesn't follow (a numpy.polynomial object's window is its class's) still voids the game."""
    if _partial(flow, call):
        return _written_args(flow, _as_call(call, call.args[0], call.args[1:]))
    out = []

    def given(v, how):
        if isinstance(v, (ast.Tuple, ast.List)):
            out.extend((x.value if isinstance(x, ast.Starred) else x, how) for x in v.elts)
        else:
            out.append((v, how))

    f = call.func
    if _may_be_numpy(flow, call):
        for kw in call.keywords:
            if kw.arg == "out":
                given(kw.value, "out=")
            elif kw.arg is None:
                for k, v in flow._literal_keys(kw.value) or ():
                    if k == "out":
                        given(v, "out=")
    ufunc = member("numpy", "ufunc")
    if not isinstance(ufunc, type):
        return out
    kn = flow.known(f)
    o = kn[2] if kn is not None else flow.static_object(f)
    name = ast.unparse(f)
    numpy_fn = kn is not None and kn[0].split(".")[0] == "numpy"

    def positional(i, how):
        for a in call.args[:i]:
            if isinstance(a, ast.Starred):              # where the out lands can't be told: what it gives
                given(a.value, how)
                return
        if i < len(call.args):
            given(call.args[i].value if isinstance(call.args[i], ast.Starred) else call.args[i], how)

    if isinstance(o, ufunc):
        for a in call.args:
            if isinstance(a, ast.Starred):
                given(a.value, f"{name}(*...)")
        out += [(a, f"{name} 的输出") for a in call.args[o.nin:] if not isinstance(a, ast.Starred)]
    elif numpy_fn and callable(o):
        i = _out_at(o)
        if i is not None:
            positional(i, f"{name} 的 out（按位置）")
        if kn[1] in NUMPY_WRITERS:
            out += [(a, name) for a in call.args[:1]]
        names = _params(o) or []

        def param(p):
            """(node given for parameter p, whether a *xs before it hides where it lands) or (None, False)."""
            for k in call.keywords:
                if k.arg == p:
                    return k.value, False
                if k.arg is None:
                    for kk, v in flow._literal_keys(k.value) or ():
                        if kk == p:
                            return v, False
            if p in names:
                j = names.index(p)
                for a in call.args[:j + 1]:
                    if isinstance(a, ast.Starred):
                        return a.value, True
                if j < len(call.args):
                    return call.args[j], False
            return None, False

        for p, (_, when) in NUMPY_FLAGS.items():
            if p == "copy" and kn[1] != "nan_to_num":
                continue
            v, hidden = param(p)
            if hidden or (v is not None and not (isinstance(v, ast.Constant) and bool(v.value) is not when)):
                positional(0, f"{name}({p}={when})")
        for p in NUMPY_INPLACE_PARAMS.get(kn[1], ()):
            v, _ = param(p)
            if v is not None:
                given(v, f"{name} 的 {p}（numpy 会原地改传给它的东西；传数字就写 int(...)）")
        if kn[1] == "ndarray":
            out += [(a, f"{name} 的 buffer") for a in call.args[2:3]]
            out += [(k.value, f"{name} 的 buffer") for k in call.keywords if k.arg == "buffer"]
    elif _receiver(flow, f) is not None and flow.modpath(_receiver(flow, f)) is None and \
            _call_name(flow, f) in _method_out() and not flow.targets(call):
        m = _call_name(flow, f)
        for shift in _arg_at(flow, f):              # LD-49: T.m(obj, ...) is obj.m(...); LD-50: type(x).m(x, ...)
            for i in sorted(_method_out()[m]):
                positional(i + shift, f".{m} 的 out（按位置）")
    if isinstance(f, ast.Attribute) and f.attr in UFUNC_OUT_AT:
        b = flow.known(f.value)
        if isinstance(b[2] if b is not None else flow.static_object(f.value), ufunc):
            i = UFUNC_OUT_AT[f.attr]
            out += [(a, name) for a in call.args[i:i + 1]]
    return out


def _free_name(n: str, taken=frozenset()) -> str:
    """A name for an own method that host code doesn't use (LD-44: my_hp, my_hand... are svsim.learn's)."""
    d = duck_names()
    for cand in (f"my_{n}", f"mine_{n}", *(f"my_{n}_{i}" for i in range(2, 100))):
        if cand not in d and cand not in taken:
            return cand
    return f"my_{n}_x"


def _name_note(flow) -> list[str]:
    """Why the module's own objects may count as shared when that comes from a method's name (LD-43): the methods
    whose parameters start as HOLDS only for their name (not a hook the base class has or calls), with a free name
    for each (LD-44); the module's methods named like a container's (x.update(...) is read as a dict's or a set's);
    and its classes built on a storage type (LD-44: what is read from their objects counts as shared)."""
    by_name, like = [], []
    for node, f in flow.fn.items():
        if f.cls is None:
            continue
        info = flow.cls[f.cls]
        base = set()
        for o in info.objs + info.builtin_bases:
            base |= class_attrs(o) | (base_self_names(o) or set())
        label = f"{f.cls.name}.{node.name}"
        params = f.pos[0 if f.static else 1:] + f.kwonly + [x for x in (f.vararg, f.kwarg) if x is not None]
        if params and flow.name_rule(f) and node.name not in base:
            by_name.append(f"{label} → {_free_name(node.name, base | set(flow.methods))}")
        if node.name in MUTATORS or node.name in ADDERS:
            like.append(label)
    out = []
    if by_name:
        out.append("提示：" + "、".join(sorted(set(by_name))) + "：左边方法的名字模拟器 / 天梯的代码里也用（它们可能拿主机的"
                   "对象来调这个名字的方法），所以参数按可能共用算，从参数读出来、传出去、存起来的东西也一样。只给自己用的"
                   "方法按箭头右边改名就行（它们不用的名字；别用下划线开头：x._y 只有 self._y 能碰）")
    if like:
        out.append("提示：" + "、".join(sorted(set(like))) + " 和容器的方法同名：x.update(...)、x.add(...) 这类调用会被"
                   "当成往容器里放东西或改容器，换个名字")
    if flow.star_fields:
        out.append("提示：第 " + "、".join(map(str, sorted(flow.star_fields))) + " 行的 **字典 不是写死键的字典，读代码只好把"
                   "模块里所有 dataclass 的字段都按它的档位算（LD-45）：写成 replace(x, 字段=值)、K(字段=值)，或者 **{'字段': 值}")
    if flow.dc_rough:
        out.append("提示：第 " + "、".join(map(str, sorted(flow.dc_rough))) + " 行按位置（或用 *）给 dataclass 传参，读代码对不上"
                   "是哪个字段（字段的写法读代码排不清顺序，或者父类不是你自己的 dataclass），只好把所有字段都按这些参数里"
                   "最高的档算（LD-46）：改成按名字传，K(字段=值)")
    if flow.replace_lines:
        names = sorted({n for v in flow.replace_lines.values() for n in v})
        out.append("提示：第 " + "、".join(map(str, sorted(flow.replace_lines))) + " 行的 replace(x, ...)：读代码看不出 x 是不是 "
                   + "、".join(names) + " 的对象；建这些类会跑自己写的 __init__（自己的或父类的），replace 也会调它，所以"
                   "它的参数按 replace 给的东西和 x 的同名属性算，存下来的东西跟着算（LD-50～LD-52）。读代码只认这些写法"
                   "「肯定是 svsim 的东西」：直接 import 的名字（DEFAULT、ev.THREAT）；svsim 的类建的（Weights(...)）；"
                   "这些东西的 replace / copy；a if c else b 两边都是；只这样赋过值的局部名字（w = replace(w, ...) "
                   "也算，for w in (DEFAULT, THREAT) 也算）；self.x（模块里每处给 .x 赋的值都是这些，类体里的 x = ... "
                   "也算）；模块顶层只写一次、值都是这些、只用 T[k] 或 T.get(k, 这些) 读的字典；模块顶层函数的参数"
                   "（每处调用都传这些）；自己的函数或 self.方法(...)（每个 return 都是这些）；super().weights(pos)。"
                   "别的（方法的参数、从局面或别的对象读出来的、循环普通列表……）都不算。总能过的改法：replace 那一行"
                   "直接写 DEFAULT / Weights(...) / 模块常量；或者有自己 __init__ 的类别加 @dataclass、也别继承 dataclass；"
                   "自己的对象要换字段，直接建新的：K(字段=值)")
    storage = sorted({c.name for c, i in flow.cls.items() if i.storage})
    if storage:
        out.append("提示：" + "、".join(storage) + " 建在 NamedTuple / namedtuple / TypedDict / dict / list / tuple / 异常"
                   "上：建它时放进去的东西读代码跟不上，所以从它的对象里读出来的都按可能共用算（LD-44）。只放自己东西的"
                   "小记录改用 @dataclasses.dataclass（按建它时传进去的东西算）")
    return out
