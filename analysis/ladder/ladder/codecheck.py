"""Reading a submission's code (item 2.3; fifth pass LD-40, sixth LD-41, seventh LD-42). Nothing in the submitted
code runs.
The simulator's and ladder's own modules are imported here (they are the host's code) to tell a module from a class
from a function; svsim.learn, svsim.tools, svsim.ui, svsim.build, svsim.search.parallel and ladder's other modules
never are.

Two kinds of rules.

Names. Imports only from the allowed modules, and no private names from them; none of the names and attributes
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
          and a real property's .setter / .getter / .deleter (checked by what the name is, not how it's spelled).
A method's parameters start CLEAN, the module's own code being the only caller; HOLDS when someone else may call
it: a dunder, the __init__ of a class with a base that isn't the module's own (PlayerStrategy alone is fine), a
method named like any attribute the simulator's or ladder's code uses or a member of a non-own base class (the
host may call it with its objects: rename a helper that collides, the refusal says so); every method HOLDS when a
class's base can't be told; SHARED when the method is taken as a value. `cls(...)` in a classmethod is every
__init__ of the module.
A SHARED object may not be changed: no assignment or `del` into it (x.a = ..., x[k] = ...), no augmented assignment
on it (x += ...: write x = x + ...; adding a number literal is allowed), no method that changes a container
(append, add, update, pop, clear, sort, ...: called or taken as a value), no shuffle / heappush / insort on it, no
setattr / delattr on it. Assigning into anything reached from an imported name is refused whatever its level.
Levels follow assignments, for / with / comprehension targets, :=, unpacking, arguments into the module's own
functions and methods (a function or method taken as a value: its parameters are SHARED), return values,
attributes (by name: x.a = shared makes every .a SHARED), containers (d[k] = shared, l.append(shared)).
Also refused, because the reading would lose track: a module used as a value (only `m.x`); a class of the module
used other than to make an instance, read an attribute, isinstance / issubclass, a base, raise / except, a
comparison (an own class's name in an annotation only with `from __future__ import annotations`, which leaves
annotations unread; a match-class pattern; iterating or indexing an own Enum); a method called through its class
(K.method(x), cls.method(x), type(x).method(x)); type(x) used other than for an attribute, a comparison or
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
import textwrap
import time
import types
from pathlib import Path

ALLOWED_TOP = {"__future__", "typing", "math", "random", "collections", "itertools", "functools", "dataclasses",
               "heapq", "bisect", "statistics", "copy", "enum", "numpy", "svsim"}
ALLOWED_LADDER = {"ladder.interface", "ladder.base"}
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
    "memmap", "loadtxt", "savetxt", "genfromtxt", "savez", "savez_compressed", "DataSource",
    # processes, environment
    "system", "popen", "environ", "getenv", "putenv",
    # (LD-41) root-parallel search (its own processes); a class with chosen dunders; a property's raw functions
    "parallel", "par_spec", "make_dataclass", "fget", "fset", "fdel",
    # (LD-42) setattr / getattr by a name in a string (update_wrapper's assigned=, cached_property's attrname); a
    # class handed back as a value (a defaultdict's factory, the evaluated annotations)
    "update_wrapper", "wraps", "attrname", "default_factory", "get_type_hints",
}
BANNED_KEYWORDS = {"parallel", "par_spec"}

CLEAN, HOLDS, SHARED = 0, 1, 2
MUTATORS = frozenset({
    "append", "extend", "insert", "remove", "pop", "popitem", "clear", "update", "setdefault", "add", "discard",
    "sort", "reverse", "difference_update", "intersection_update", "symmetric_difference_update", "appendleft",
    "extendleft", "popleft", "rotate", "subtract", "move_to_end", "fill", "put", "itemset", "resize", "setflags",
    "setfield", "partition", "byteswap", "cache_clear"})
ADDERS = frozenset({"append", "add", "extend", "insert", "update", "appendleft", "extendleft"})
ARG_MUTATORS = frozenset({"shuffle", "heappush", "heappop", "heapify", "heapreplace", "heappushpop", "insort",
                          "insort_left", "insort_right"})
BUILTIN_TYPES = frozenset({"set", "dict", "list", "bytearray", "frozenset", "object", "type", "tuple"})
SCALAR_BUILTINS = frozenset({
    "len", "id", "hash", "isinstance", "issubclass", "callable", "hasattr", "bool", "int", "float", "str", "repr",
    "abs", "round", "ord", "chr", "any", "all", "divmod", "pow", "format", "ascii", "bin", "hex", "oct", "complex",
    "print", "setattr", "delattr"})
FRESH_BUILTINS = frozenset({"list", "dict", "set", "frozenset", "tuple", "sorted", "reversed", "enumerate", "zip",
                            "map", "filter", "iter", "range", "sum", "bytearray", "bytes", "slice"})
ELEMENT_BUILTINS = frozenset({"min", "max", "next"})
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
    if top == "ladder":
        return None if name in ALLOWED_LADDER else "ladder 里只能用 ladder.interface、ladder.base"
    if top in ALLOWED_TOP:
        return None
    return "不在允许的模块里"


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
    """Every attribute an instance of `cls` may have from its classes: dir(cls), and for svsim / ladder classes the
    `self.x = ...` (and setattr(self, "x", ...)) in their source."""
    if cls in _CLASS_ATTRS:
        return _CLASS_ATTRS[cls]
    names = set(dir(cls))
    for k in getattr(cls, "__mro__", ()):
        if (getattr(k, "__module__", "") or "").split(".")[0] not in ("svsim", "ladder"):
            continue
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


def duck_names() -> frozenset:
    """Every attribute name the simulator's and the ladder's code reads (x.name) or writes out as a string: a
    method of the strategy's own classes with one of these names may be called by host code with host objects
    (duck typing, a hook found by name), so its parameters start as HOLDS (LD-42). Read once per process."""
    global _DUCK
    if _DUCK is None:
        names = set()
        for pkg in ("svsim", "ladder"):
            m = _import(pkg)
            for root in (list(getattr(m, "__path__", [])) if m is not _MISSING else []):
                for path in sorted(Path(root).rglob("*.py")):
                    try:
                        tree = ast.parse(path.read_text(encoding="utf-8"))
                    except (OSError, SyntaxError, ValueError, UnicodeDecodeError):
                        continue
                    for n in ast.walk(tree):
                        if isinstance(n, ast.Attribute) and not (isinstance(n.value, ast.Name) and
                                                                 n.value.id in ("self", "cls")):
                            names.add(n.attr)       # (self.x: a subclass's, and class_attrs has those)
                        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.isidentifier():
                            names.add(n.value)
        _DUCK = frozenset(names)
    return _DUCK


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
    __slots__ = ("attrs", "builtin_bases", "dataclass", "deco_unknown", "fields", "fresh_ok", "node", "objs", "tainted",
                 "unknown", "user_bases")


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
        self.where, self.parent, self.inner = {}, {}, {}
        self.module = Scope(tree, "module", None)
        self.nodes = []
        self._build(tree, self.module)
        self._collect()
        self.lv: dict = {}
        self.attrs: dict = {}
        self.changed = False
        self._memo: dict = {}
        self.incomplete = False
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
        self.mods: dict = {}              # key -> module name
        self.objs: dict = {}              # key -> [(module, name, object)]
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

            if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load):
                self.stores[self.key(node)] = self.stores.get(self.key(node), 0) + 1
            elif isinstance(node, ast.Import):
                for a in node.names:
                    k = count(a.asname or a.name.split(".")[0])
                    self.mods[k] = a.name if a.asname else a.name.split(".")[0]
            elif isinstance(node, ast.ImportFrom):
                for a in node.names:
                    if a.name == "*":
                        continue
                    k = count(a.asname or a.name)
                    obj = member(node.module, a.name) if node.module and not node.level else _MISSING
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
        c.deco_unknown = any(k not in ("dataclass", "total_ordering") for k in kinds)   # LD-42
        c.fields = [s.target.id for s in node.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)]
        for b in node.bases:
            users = self.user_class(b)
            if users:
                c.user_bases += users
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
        c.tainted = c.unknown or bool(c.objs)
        ps = _player_strategy()
        c.fresh_ok = bool(c.objs) and not c.unknown and all(o is ps for o in c.objs)
        return c

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

    def external_names(self) -> frozenset | None:
        """Method names host code may call on the module's own objects: the names the simulator's and the ladder's
        code uses (duck_names), and every attribute of a base class that isn't the module's own (PlayerStrategy's
        hooks, a dict's get, an svsim class's methods). None: any name (a base the reading can't place)."""
        names = set(duck_names())
        for c in self.cls.values():
            if c.unknown:
                return None
            for o in c.objs + c.builtin_bases:
                names |= class_attrs(o)
        return frozenset(names)

    def _param_base(self, f, ext) -> int:
        """Where a function's parameters start (the calls in the module then raise them): SHARED for a function
        taken as a value; for a method, HOLDS when host code may call it (a name in `ext`, a dunder, __init__ of a
        class with a base that isn't the module's own but PlayerStrategy), else CLEAN like a plain function (LD-42:
        the module's own trees and tables were refused)."""
        if f.value_used:
            return SHARED
        if f.cls is None:
            return CLEAN
        name, info = f.node.name, self.cls[f.cls]
        if name == "__init__":
            return HOLDS if info.unknown or (info.objs and not info.fresh_ok) else CLEAN
        if dunder(name) or ext is None or name in ext:
            return HOLDS
        return CLEAN

    def _init_levels(self):
        ext = self.ext = self.external_names()
        for node, f in self.fn.items():
            if f.deco_unknown:
                self._raise_ret(node, SHARED)           # the name holds what the decorator returned (LD-42)
            base = self._param_base(f, ext)
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
        if info.unknown or info.deco_unknown or (a in info.attrs and not (info.fresh_ok and a in OWN_FRESH)):
            v = SHARED
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
                    if not mine and (info.unknown or a in info.attrs):
                        v = SHARED                     # inherited from an svsim / ladder class
                return v
            r = self.level(base)
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
        """What calling a defaultdict's factory gives: a standard-library class (not the simulator's) or a builtin
        type makes a new, clean object (LD-42: defaultdict(Counter) was refused)."""
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
            for c in self.cdefs.get(k, ()):
                out += [(d, 1) for d in self.class_methods(c, "__init__")]
            if k in self.own and self.own[k][1]:          # cls(...): this class or any subclass (LD-42)
                out += [(d, 1) for d in self.methods.get("__init__", ())]
        else:
            a = f.attr if isinstance(f, ast.Attribute) else self._getattr_name(f)
            for d in self.methods.get(a, ()) if a else ():
                out.append((d, 0 if self.fn[d].static else 1))
        return out

    def _flow_call(self, call):
        for d, off in self.targets(call):
            f = self.fn[d]
            pos = f.pos
            named = {x.arg: x for x in pos[off:] + f.kwonly}
            everything = pos[off:] + f.kwonly + [x for x in (f.vararg, f.kwarg) if x is not None]
            i = off
            for a in call.args:
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
            for kw in call.keywords:
                v = self.level(kw.value)
                if kw.arg is None:
                    for x in everything:
                        self._raise(self.key(x), elem(v))
                elif kw.arg in named:
                    self._raise(self.key(named[kw.arg]), v)
                elif f.kwarg is not None:
                    self._raise(self.key(f.kwarg), holds(v))
        fn = call.func
        if isinstance(fn, ast.Name):                           # a dataclass of the module: fields from arguments
            for c in self.cdefs.get(self.key(fn), ()):
                info = self.cls[c]
                if info.dataclass:
                    for name, a in zip(info.fields, call.args):
                        self._raise_attr(name, self.level(a))
                    for kw in call.keywords:
                        if kw.arg is None:
                            for name in info.fields:
                                self._raise_attr(name, elem(self.level(kw.value)))
                        else:
                            self._raise_attr(kw.arg, self.level(kw.value))
        name = fn.attr if isinstance(fn, ast.Attribute) else fn.id if isinstance(fn, ast.Name) else None
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
        if name in ARG_MUTATORS and len(call.args) >= 2:
            self._raise_container(call.args[0], holds(max(self.level(a) for a in call.args[1:])))
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

    def class_use_ok(node) -> bool:
        p = parent(node)
        if (isinstance(p, ast.Call) and p.func is node) or receiver(node) or isinstance(p, (ast.Compare, ast.Raise)):
            return True
        if isinstance(p, ast.MatchClass) and p.cls is node:
            return True                                 # case K(...): an isinstance (LD-42)
        if any(issubclass(o, enum.Enum) for c in flow.user_class(node) for o in flow.cls[c].objs if isinstance(o, type)):
            if isinstance(p, (ast.For, ast.comprehension)) and p.iter is node:
                return True                             # an enum of its own: its members (LD-42)
            if isinstance(p, ast.Subscript) and p.value is node and isinstance(p.ctx, ast.Load):
                return True
        if isinstance(p, ast.ClassDef) and node in p.bases:
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

    def hint(at) -> str:
        """Why a parameter may be shared, when that comes only from the name of the method the code is in."""
        m = flow.method_of(at)
        if m is None or m.name == "__init__" or dunder(m.name) or flow.fn[m].value_used or flow.ext is None:
            return ""
        info = flow.cls[flow.fn[m].cls]
        if m.name in duck_names() and not any(m.name in class_attrs(o) for o in info.objs + info.builtin_bases):
            return (f"（方法名 {m.name} 在模拟器 / 天梯的代码里也有，可能被它们拿主机的对象来调，所以它的参数按可能共用算："
                    "只给自己用的方法换个名字，比如加个前缀）")
        return ""

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
            elif isinstance(obj, types.ModuleType):
                why = module_problem(obj.__name__)
            elif m == "ladder":
                why = module_problem(f"ladder.{a}")
            else:
                origin = getattr(obj, "__module__", None)
                if isinstance(origin, str) and any(origin == p or origin.startswith(p + ".") for p in DENIED_PREFIXES):
                    why = f"它来自 {origin}"
            if why:
                bad(at, f"{m}.{a}（{why}）")
            if id(obj) in registrars:
                bad(at, f"{m}.{a}（注册卡牌脚本会改模拟器）")
        if ctx != "load":
            root = flow.import_root(base)
            if root is not None:
                bad(at, f"给 {root} 里的东西赋值或删除（不许改模块、引擎、卡牌里的东西）")
            elif flow.level(base) >= SHARED:
                bad(at, f"{how}：不许改可能共用的对象（从 svsim / ladder 拿来或读出来的东西；"
                        "要改就自己做一份：list(x)、dict(x)、dataclasses.replace(x, ...)）" + hint(at))
        if ctx == "load" and a in MUTATORS:
            kn = flow.known(base)
            unbound = (isinstance(base, ast.Name) and flow.key(base) is None and base.id in BUILTIN_TYPES) or \
                class_like(base) or (kn is not None and isinstance(kn[2], type))
            if flow.level(base) >= SHARED:
                bad(at, f"{how}：不许改可能共用的容器（要改就自己做一份：list(x)、dict(x)、dataclasses.replace(x, ...)）"
                    + hint(at))
            elif unbound and not (call is not None and call.args and not isinstance(call.args[0], ast.Starred)
                                  and flow.level(call.args[0]) < SHARED):
                bad(at, f"{how}：不许改可能共用的容器")
        if a in flow.regular and class_like(base):
            bad(at, f"{how}：普通方法不许经类调（K.method(x) 能把任何对象当 self）")

    for node in flow.nodes:
        p = parent(node)
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
                if mod == "random" and a.name != "Random":
                    bad(node, f"from random import {a.name}（要随机数用 self.random，不用全局的 random）")
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
            if ctx == "load" and flow.modpath(node) is not None and not receiver(node):
                bad(node, f"模块 {flow.modpath(node)} 不许当值用（只能写 模块.属性）")
        elif isinstance(node, ast.Subscript):
            if not isinstance(node.ctx, ast.Load):
                root = flow.import_root(node.value)
                if root is not None:
                    bad(node, f"给 {root} 里的东西赋值或删除（不许改模块、引擎、卡牌里的东西）")
                elif flow.level(node.value) >= SHARED:
                    bad(node, "x[...] = / del：不许改可能共用的对象（从 svsim / ladder 拿来或读出来的东西；"
                              "要改就自己做一份：list(x)、dict(x)、dataclasses.replace(x, ...)）" + hint(node))
        elif isinstance(node, ast.AugAssign):
            if flow.level(node.target) >= SHARED and not (_numeric(node.value) and
                                                          (not isinstance(node.op, ast.Mult) or _floaty(node.value))):
                bad(node, "x += ...：x 可能是共用的对象，原地运算会改它（写成 x = x + ...；"
                          "加减一个数字可以，乘一个整数不行：列表 *= 0 会原地清空）")
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
                if fn.id in ("setattr", "delattr") and flow.modpath(node.args[0]) is not None:
                    bad(node, f"{fn.id}({ast.unparse(node.args[0])}, ...)（不许改模块里的东西）")
            elif builtin and fn.id == "type":
                if len(node.args) != 1 or node.keywords:
                    bad(node, "type(名字, 基类, 字典)：不许这样造类")
                elif not (receiver(node) or isinstance(p, ast.Compare) or isinstance_arg(node)):
                    bad(node, "type(x) 只能用来读属性（如 .__name__）、比较、isinstance")
            name = fn.attr if isinstance(fn, ast.Attribute) else fn.id if isinstance(fn, ast.Name) else None
            if name in ARG_MUTATORS and node.args and \
                    (isinstance(node.args[0], ast.Starred) or flow.level(node.args[0]) >= SHARED):
                bad(node, f"{name}(...)：不许改可能共用的容器（要改就自己做一份：list(x)、dict(x)、dataclasses.replace(x, ...)）"
                    + hint(node))
        elif isinstance(node, ast.ClassDef) and isinstance(p, ast.Module):
            classes.append(node.name)
    if cls not in classes:
        problems.append(f"模块顶层没有类 {cls}")
    return problems
