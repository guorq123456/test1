"""The code reader's flow rules (LD-41, the sixth review; LD-42, the seventh; LD-43, LD-44, LD-45): shared objects from svsim / ladder may
not be changed, through any alias, argument, return value, attribute, container or decorator; and the plain strategy
code (its own trees, tables, counters, enums, annotations) stays accepted."""
import sys
import textwrap
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
from ladder.codecheck import check_code

TAIL = "\nfrom ladder.interface import PlayerStrategy\n\nclass S(PlayerStrategy):\n    pass\n"

BAD = {
 "rename": "from svsim.core.actions import PlayCard\np = PlayCard\np.__name__ = 'x'",
 "self-param": "from svsim.core import script\ndef poison(self):\n    self._SCRIPTS.clear()\npoison(script)",
 "self-param2": "from svsim.search.evaluate import DEFAULT\ndef poison(self):\n    self._x = 1\npoison(DEFAULT)",
 "listen-update": "from svsim.core.script import LISTEN_IN_HAND\nLISTEN_IN_HAND.update({1,2})",
 "listen-alias": "from svsim.core.script import LISTEN_IN_HAND as L\ns = L\ns.add(5)",
 "listen-func": "from svsim.core.script import LISTEN_IN_HAND\ndef f(s):\n    s.add(1)\nf(LISTEN_IN_HAND)",
 "listen-ior": "from svsim.core.script import LISTEN_IN_HAND\nx = LISTEN_IN_HAND\nx |= {1}",
 "list-wrap": "from svsim.cards import pool\n[pool][0].POOL[1] = None",
 "list-wrap2": "from svsim.cards.pool import POOL\nholder = [POOL]\nholder[0][1] = None",
 "call-root": "from ladder import base\nbase.baseline_lists()[0] = []",
 "call-root2": "from ladder import base\nd = base.baseline_lists()\nd.clear()",
 "register": "from svsim.core.script import register\nregister(99999)(object)",
 "register2": "from svsim.core import script\nr = script.register",
 "unbound-set": "from svsim.core.script import INVOKERS\nset.add(INVOKERS, 3)",
 "map-add": "from svsim.core.script import INVOKERS\nlist(map(INVOKERS.add, [1]))",
 "getattr-add": "from svsim.core.script import INVOKERS\ngetattr(INVOKERS, 'add')(3)",
 "module-value": "from svsim.core import script\nm = script\nm.INVOKERS.add(1)",
 "module-arg": "from svsim.core import script\ndef f(m):\n    m.INVOKERS.add(1)\nf(script)",
 "submodule-value": "import svsim.core.script\nm = svsim.core\n",
 "private-import": "from svsim.core.script import _SCRIPTS",
 "random-reexport": "from ladder import interface\ninterface.random.seed(1)",
 "random-from": "from svsim.core.state import random as r\nr.seed(1)",
 "time-reexport": "from svsim.search import mcts\nmcts.time.sleep(1)",
 "ui": "import svsim.ui.session",
 "parallel": "from svsim.search.mcts import ISMCTS\nx = ISMCTS(parallel=4)",
 "parallel-attr": "def f(t):\n    t.parallel = 4",
 "unbound-method": "from svsim.core.script import INVOKERS\nclass K:\n    def m(self):\n        self.add(1)\nK.m(INVOKERS)",
 "type-method": "from svsim.core.script import INVOKERS\nclass K:\n    def m(self):\n        self.add(1)\n    def go(self):\n        type(self).m(INVOKERS)",
 "cls-method": "from svsim.core.script import INVOKERS\nclass K:\n    def m(self):\n        self.add(1)\n    @classmethod\n    def go(cls):\n        cls.m(INVOKERS)",
 "classbody-method": "from svsim.core.script import INVOKERS\nclass K:\n    def m(self):\n        self.add(1)\n    m(INVOKERS)",
 "class-value": "class K:\n    pass\nx = K",
 "type3": "X = type('X', (), {'__eq__': lambda s, o: True})",
 "tree-weights": "class T(PlayerStrategy):\n    def search(self, pos):\n        self.tree.c = 9\n        return {}",
 "tree-weights2": "class T(PlayerStrategy):\n    def search(self, pos):\n        w = self.tree\n        w.weights = None\n        return {}",
 "inherited-method-ret": "class T(PlayerStrategy):\n    def search(self, pos):\n        g = self.guess(pos)\n        g.append(1)\n        return {}",
 "deepcopy-class": "import copy\nfrom svsim.search.mcts import ISMCTS\nC = copy.deepcopy(ISMCTS)\nC.x = 1",
 "copy-shared": "import copy\nfrom svsim.search.evaluate import DEFAULT\nw = copy.copy(DEFAULT)\nw.board = 1",
 "return-shared": "from svsim.core.script import INVOKERS\ndef get():\n    return INVOKERS\nget().add(1)",
 "attr-flow": "from svsim.core.script import INVOKERS\nclass H:\n    pass\nh = H()\nh.s = INVOKERS\nh.s.add(1)",
 "dict-flow": "from svsim.core.script import INVOKERS\nd = {}\nd['k'] = INVOKERS\nd['k'].add(1)",
 "append-flow": "from svsim.core.script import INVOKERS\nl = []\nl.append(INVOKERS)\nl[0].add(1)",
 "for-flow": "from svsim.core.script import INVOKERS\nfor s in [INVOKERS]:\n    s.add(1)",
 "comp-flow": "from svsim.core.script import INVOKERS\n[s.add(1) for s in [INVOKERS]]",
 "walrus": "from svsim.core.script import INVOKERS\nif (s := INVOKERS):\n    s.add(1)",
 "global": "from svsim.core.script import INVOKERS\nG = None\ndef f():\n    global G\n    G = INVOKERS\ndef g():\n    G.add(1)",
 "nonlocal": "from svsim.core.script import INVOKERS\ndef f():\n    x = None\n    def g():\n        nonlocal x\n        x = INVOKERS\n    g()\n    x.add(1)",
 "lambda": "from svsim.core.script import INVOKERS\nf = lambda s: s.add(1)\nf(INVOKERS)",
 "key-func": "from svsim.core.script import INVOKERS\ndef f(s):\n    s.add(1)\nsorted([INVOKERS], key=f)",
 "partial": "import functools\nfrom svsim.core.script import INVOKERS\ndef f(s):\n    s.add(1)\nfunctools.partial(f, INVOKERS)()",
 "default-arg": "from svsim.core.script import INVOKERS\ndef f(s=INVOKERS):\n    s.add(1)",
 "kwargs": "from svsim.core.script import INVOKERS\ndef f(**k):\n    k['s'].add(1)\nf(s=INVOKERS)",
 "starargs": "from svsim.core.script import INVOKERS\ndef f(*a):\n    a[0].add(1)\nf(INVOKERS)",
 "unpack": "from svsim.core.script import INVOKERS\na, b = INVOKERS, 1\na.add(1)",
 "unpack2": "from svsim.core.script import INVOKERS\nt = (INVOKERS, 1)\na, b = t\na.add(1)",
 "with": "from svsim.core.script import INVOKERS\nwith INVOKERS as s:\n    s.add(1)",
 "heappush": "import heapq\nfrom ladder import base\nheapq.heappush(base.baseline_lists()[0], 1)",
 "shuffle": "from ladder import base\nclass T(PlayerStrategy):\n    def search(self, pos):\n        self.random.shuffle(base.baseline_lists()[0])\n        return {}",
 "setattr-shared": "from svsim.search.evaluate import DEFAULT\nx = DEFAULT\nsetattr(x, 'board', 1)",
 "setattr-name": "from svsim.core.actions import PlayCard\nsetattr(PlayCard, '__name__', 'x')",
 "super-init-outside": "class T(PlayerStrategy):\n    def search(self, pos):\n        super().__init__(5)\n        return {}",
 "nested-self": "from svsim.core.script import INVOKERS\nclass K:\n    def m(self):\n        def inner(self):\n            self._x = 1\n        inner(INVOKERS)",
 "rebound-self": "from svsim.core import script\nclass K:\n    def m(self):\n        self = script\n        self._SCRIPTS.clear()",
 "cache-clear": "from svsim.search import evaluate\nf = evaluate.follower_value\nf.cache_clear()",
 "via-hook-param-sort": "class T(PlayerStrategy):\n    def veto(self, state, action):\n        state.players[0].hand.sort()\n        return False",
 "aug-attr": "from svsim.search.evaluate import DEFAULT\nclass T(PlayerStrategy):\n    def search(self, pos):\n        self.tree.iterations += 1\n        return {}",
 "match": "from svsim.core.script import INVOKERS\nmatch INVOKERS:\n    case s:\n        s.add(1)",
 "except": "from svsim.core.script import INVOKERS\ntry:\n    pass\nexcept Exception as e:\n    e.args[0].add(1)",
 "classattr": "from svsim.core.script import INVOKERS\nclass H:\n    S = INVOKERS\nH.S.add(1)",
 "classattr2": "from svsim.core.script import INVOKERS\nclass H:\n    S = INVOKERS\n    def m(self):\n        self.S.add(1)",
 "dataclass": "from dataclasses import dataclass\nfrom svsim.core.script import INVOKERS\n@dataclass\nclass H:\n    s: set\nH(INVOKERS).s.add(1)",
 "yield": "from svsim.core.script import INVOKERS\ndef g():\n    yield INVOKERS\nfor s in g():\n    s.add(1)",
 "deco-unbound": "from svsim.core.script import INVOKERS\ndef deco(f):\n    f(INVOKERS)\n    return f\nclass K:\n    @deco\n    def m(self):\n        self.add(1)",
 "send": "from svsim.core.script import INVOKERS\ndef g():\n    x = yield\n    x.add(1)\nit = g()\nnext(it)\nit.send(INVOKERS)",
 "user-set-unbound": "from svsim.core.script import INVOKERS\nclass E(set):\n    pass\nE.add(INVOKERS, 1)",
 "deque-unbound": "import collections\nfrom svsim.core.script import INVOKERS\ncollections.deque.append(INVOKERS, 1)",
 "exc-args": "from svsim.core.script import INVOKERS\ntry:\n    raise ValueError(INVOKERS)\nexcept ValueError as e:\n    e.args[0].add(1)",
 "init-param": "from svsim.core.script import INVOKERS\nclass H:\n    def __init__(self, s):\n        self.s = s\nH(INVOKERS).s.add(1)",
 "reduce": "import functools\nfrom svsim.core.script import INVOKERS\nfunctools.reduce(lambda a, b: a.add(b) or a, [1], INVOKERS)",
 "dictstar": "from svsim.core.script import INVOKERS\nx = {**{'a': INVOKERS}}['a']\nx.add(1)",
 "next-iter": "from svsim.core.script import INVOKERS\nx = next(iter([INVOKERS]))\nx.add(1)",
 "setattr-flow": "from svsim.core.script import INVOKERS\nclass H:\n    pass\nh = H()\nsetattr(h, 's', INVOKERS)\nh.s.add(1)",
 "ident-vararg": "from svsim.core.script import INVOKERS\ndef ident(*a):\n    return a[0]\nident(INVOKERS).add(1)",
 "closure": "from svsim.core.script import INVOKERS\ndef outer():\n    s = INVOKERS\n    def inner():\n        s.add(1)\n    inner()",
 "fn-dict": "from svsim.core.script import INVOKERS\ndef f(s):\n    s.add(1)\nfs = {'f': f}\nfs['f'](INVOKERS)",
 "class-body-alias": "from svsim.core.script import INVOKERS\nclass K:\n    def m(self):\n        self.add(1)\n    n = m\nK().n.__call__",
 "aug-attr-holds": "from svsim.core.script import INVOKERS\nclass H:\n    pass\nh = H()\nh.s = INVOKERS\nh.s |= {1}",
 "slice": "from svsim.core.script import INVOKERS\nL = list(INVOKERS)\nx = [L]\nx[0][:] = []",
 # LD-42 (the seventh review)
 "statistics": "import statistics\nfrom random import Random\nR = statistics.median_low([Random])\nR.shuffle = None",
 "statistics-mode": "import statistics\nfrom svsim.core.script import INVOKERS\nstatistics.mode([INVOKERS]).add(1)",
 "statistics-mean": "import statistics\nfrom svsim.core.script import INVOKERS\nx = statistics.mean([INVOKERS])\nx.add(1)",
 "prod-start": "import math\nfrom random import Random\nr = math.prod([], start=Random)\nr.shuffle = None",
 "deco": "from random import Random\ndef steal(fn):\n    return Random\n@steal\ndef grabbed():\n    return 1\ngrabbed.shuffle = None",
 "deco-call": "from svsim.core.script import INVOKERS\ndef steal(fn):\n    return INVOKERS\n@steal\ndef f():\n    return 1\nf.add(1)",
 "deco-class": "from svsim.search.mcts import ISMCTS\ndef deco(k):\n    return ISMCTS\n@deco\nclass K:\n    pass\nK.c = 9",
 "fake-wrapper": "from random import Random\nclass W:\n    @staticmethod\n    def lru_cache(f):\n        return Random\n@W.lru_cache\ndef g():\n    pass\ng.shuffle = None",
 "fake-dataclass": "from random import Random\nclass W:\n    @staticmethod\n    def dataclass(k):\n        return Random\n@W.dataclass\nclass K:\n    pass\nK.shuffle = None",
 "fake-setter": "from random import Random\nclass W:\n    def setter(self, f):\n        return Random\nw = W()\nclass K:\n    @w.setter\n    def g(self):\n        pass\nK.g.shuffle = None",
 "setter-param": "from svsim.core.script import INVOKERS\nclass K:\n    @property\n    def p(self):\n        return 1\n    @p.setter\n    def p(self, v):\n        v.add(1)\nk = K()\nk.p = INVOKERS",
 "cls-init": "from svsim.core.script import INVOKERS\nclass N:\n    def __init__(self, p):\n        p.add(1)\n    @classmethod\n    def make(cls, x):\n        return cls(x)\nN.make(INVOKERS)",
 "init-super": "from svsim.core.script import INVOKERS\nclass A:\n    def __init__(self, p):\n        p.add(1)\nclass B(A):\n    def __init__(self, q):\n        super().__init__(q)\nB(INVOKERS)",
 "method-by-name": "from svsim.core.script import INVOKERS\nclass N:\n    def zork(self, p):\n        p.add(1)\nn = [N()][0]\nn.zork(INVOKERS)",
 "hook-param": "class T(PlayerStrategy):\n    def search(self, pos):\n        pos.state.players[0].hand.clear()\n        return {}",
 "fields-type": "import dataclasses\nfrom random import Random\n@dataclasses.dataclass\nclass D:\n    x: Random = None\ndataclasses.fields(D)[0].type.shuffle = None",
 "asdict": "import dataclasses\nfrom random import Random\n@dataclasses.dataclass\nclass D:\n    x: object = None\nd = D(x=Random)\ndataclasses.asdict(d)['x'].shuffle = None",
 "type-hints": "import typing\nclass K:\n    def m(self, x):\n        x.add(1)\ndef g(x: 'K'):\n    pass\ntyping.get_type_hints(g)['x'].m(set())",
 "annotation-unquoted": "class K:\n    pass\ndef g(x: K) -> K:\n    return x",
 "update-wrapper": "import functools\nfrom svsim.search import combo\ndef other(defn, fused=False):\n    return ()\nfunctools.update_wrapper(combo.profile, other, assigned=('__code__',), updated=())",
 "attrname": "import functools\ndef other(x):\n    return x\nclass Box:\n    x = functools.cached_property(other)\nBox.x.attrname = '__wrapped__'",
 "default-factory": "import collections\nd = collections.defaultdict(collections.Counter)\nd.default_factory.most_common = None",
 "imul-list": "from ladder import base\nx = base.baseline_lists()\ny = x['a']\ny *= 0",
 "yield-finally": "def tail(n):\n    try:\n        yield n\n    finally:\n        while True:\n            pass",
 "yield-except": "def tail(n):\n    try:\n        yield n\n    except BaseException:\n        pass",
 # LD-43: what the narrower rules must still refuse
 "cls-subclass-init": "from svsim.core.script import INVOKERS\nclass A:\n    @classmethod\n    def make(cls, x):\n        return cls(x)\nclass B(A):\n    def __init__(self, x):\n        x.append(1)\nB.make(INVOKERS)",
 "cls-inherited-init": "from svsim.core.script import INVOKERS\nclass A:\n    def __init__(self, x):\n        self.x = x\n    @classmethod\n    def make(cls, x):\n        return cls(x)\nclass B(A):\n    pass\nB.make(INVOKERS).x.append(1)",
 "field-default": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    x: object = dataclasses.field(default=INVOKERS)\nM().x.append(1)",
 "field-lambda": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    x: object = dataclasses.field(default_factory=lambda: INVOKERS)\nM().x.append(1)",
 "field-svsim-class": "import dataclasses\nfrom svsim.core.state import GameState\n@dataclasses.dataclass\nclass M:\n    x: object = dataclasses.field(default_factory=GameState)\nM().x.players.append(1)",
 "unknown-base-own": "def mk():\n    return object\nclass W(mk()):\n    def my_f(self, x):\n        x.items.append(1)",
 "namedtuple-method": "from typing import NamedTuple\nfrom svsim.core.script import INVOKERS\nclass P(NamedTuple):\n    a: int\n    def my_f(self, x):\n        x.append(1)\nP(1).my_f(INVOKERS)",
 # LD-44 (the ninth review): what a storage-type class keeps, construction through subclasses and cls(...), dataclass
 # fields set by cls(...) or replace, InitVars, nested classes
 "nested-class": "from svsim.core.script import INVOKERS\nclass Outer:\n    class Inner:\n        def __init__(self, x):\n            x.add(1)\nOuter.Inner(INVOKERS)",
 "exc-sub-args": "from svsim.core.script import INVOKERS\nclass E(Exception):\n    pass\nE(INVOKERS).args[0].add(1)",
 "dict-sub-self": "from svsim.core.script import INVOKERS\nclass D(dict):\n    def my_go(self):\n        self['k'].add(1)\nD(k=INVOKERS).my_go()",
 "dict-sub-out": "from svsim.core.script import INVOKERS\nclass D(dict):\n    pass\nD(k=INVOKERS)['k'].add(1)",
 "list-sub": "from svsim.core.script import INVOKERS\nclass L(list):\n    pass\nL([INVOKERS])[0].add(1)",
 "nt": "from svsim.core.script import INVOKERS\nfrom typing import NamedTuple\nclass P(NamedTuple):\n    s: object\nP(INVOKERS).s.add(1)",
 "nt-idx": "from svsim.core.script import INVOKERS\nfrom typing import NamedTuple\nclass P(NamedTuple):\n    s: object\nP(INVOKERS)[0].add(1)",
 "nt-default": "from svsim.core.script import INVOKERS\nfrom typing import NamedTuple\nclass P(NamedTuple):\n    s: object = INVOKERS\nP().s.add(1)",
 "nt-method-self": "from svsim.core.script import INVOKERS\nfrom typing import NamedTuple\nclass Box(NamedTuple):\n    s: object\n    def my_go(self):\n        self.s.add(1)\nBox(INVOKERS).my_go()",
 "cnt": "from svsim.core.script import INVOKERS\nimport collections\nclass P(collections.namedtuple('P', 's')):\n    pass\nP(INVOKERS).s.add(1)",
 "cnt-list": "from svsim.core.script import INVOKERS\nimport collections\nclass P(collections.namedtuple('P', ['s'])):\n    pass\nP(INVOKERS).s.add(1)",
 "tnt-func": "from svsim.core.script import INVOKERS\nimport typing\nclass P(typing.NamedTuple('P', [('s', object)])):\n    pass\nP(INVOKERS).s.add(1)",
 "td": "from svsim.core.script import INVOKERS\nfrom typing import TypedDict\nclass TD(TypedDict):\n    s: object\nTD(s=INVOKERS)['s'].add(1)",
 "dc-cls": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    x: object = None\n    @classmethod\n    def mk(cls, v):\n        return cls(x=v)\nM.mk(INVOKERS).x.add(1)",
 "dc-cls-pos": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    x: object = None\n    @classmethod\n    def mk(cls, v):\n        return cls(v)\nM.mk(INVOKERS).x.add(1)",
 "dc-replace": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    x: object = None\ndataclasses.replace(M(), x=INVOKERS).x.add(1)",
 "dc-replace-alias": "from svsim.core.script import INVOKERS\nfrom dataclasses import dataclass, replace as r\n@dataclass\nclass M:\n    x: object = None\nr(M(), x=INVOKERS).x.add(1)",
 "dc-replace-star": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    x: object = None\ndataclasses.replace(M(), **{'x': INVOKERS}).x.add(1)",
 "dc-initvar": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    y: dataclasses.InitVar[object] = None\n    def __post_init__(self, y):\n        y.add(1)\nM(INVOKERS)",
 "dc-initvar-attr": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    y: dataclasses.InitVar[object] = None\n    x: object = None\n    def __post_init__(self, y):\n        self.x = y\nM(y=INVOKERS).x.add(1)",
 "dc-initvar-replace": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    y: dataclasses.InitVar[object] = None\n    x: object = None\n    def __post_init__(self, y):\n        self.x = y\ndataclasses.replace(M(), y=INVOKERS).x.add(1)",
 "diamond-cm": "from svsim.core.script import INVOKERS\nclass A:\n    @classmethod\n    def mk(cls, x):\n        return cls(x)\nclass B(A):\n    def __init__(self, x):\n        x.add(1)\nclass C(A):\n    pass\nclass D(C, B):\n    pass\nD.mk(INVOKERS)",
 "diamond-direct": "from svsim.core.script import INVOKERS\nclass A:\n    pass\nclass B(A):\n    def __init__(self, x):\n        x.add(1)\nclass C(A):\n    pass\nclass D(C, B):\n    pass\nD(INVOKERS)",
 "generic-own-sub": "from svsim.core.script import INVOKERS\nfrom typing import Generic, TypeVar\nT_ = TypeVar('T_')\nclass Stack(Generic[T_]):\n    def __init__(self, x):\n        x.add(1)\nclass S2(Stack[int]):\n    pass\nS2(INVOKERS)",
 "generic-own-sub-attr": "from svsim.core.script import INVOKERS\nfrom typing import Generic, TypeVar\nT_ = TypeVar('T_')\nclass Stack(Generic[T_]):\n    def __init__(self, x):\n        self.x = x\nclass S2(Stack[int]):\n    pass\nS2(INVOKERS).x.add(1)",
 # LD-45 (the tenth review): a storage base's methods on self, the standard library's storage classes, class bodies
 # with if / try, cls as a value, dataclass subclasses and positions, enums, class-changing standard calls
 "45-dict-self-get": "from svsim.core.script import INVOKERS\nclass D(dict):\n    def my_go(self):\n        self.get('k').add(1)\nD(k=INVOKERS).my_go()",
 "45-dict-super-get": "from svsim.core.script import INVOKERS\nclass D(dict):\n    def my_go(self):\n        super().get('k').add(1)\nD(k=INVOKERS).my_go()",
 "45-dict-values": "from svsim.core.script import INVOKERS\nclass D(dict):\n    def my_go(self):\n        for v in self.values():\n            v.add(1)\nD(k=INVOKERS).my_go()",
 "45-dict-pop": "from svsim.core.script import INVOKERS\nclass D(dict):\n    def my_go(self):\n        self.pop('k').add(1)\nD(k=INVOKERS).my_go()",
 "45-dict-chain": "from svsim.core.script import INVOKERS\nclass D(dict):\n    def my_get(self):\n        return self.get('k')\n    def my_go(self):\n        self.my_get().add(1)\nD(k=INVOKERS).my_go()",
 "45-list-copy": "from svsim.core.script import INVOKERS\nclass L(list):\n    def my_go(self):\n        self.copy()[0].add(1)\nL([INVOKERS]).my_go()",
 "45-nt-asdict": "from svsim.core.script import INVOKERS\nfrom typing import NamedTuple\nclass P(NamedTuple):\n    s: object\n    def my_go(self):\n        self._asdict()['s'].add(1)\nP(INVOKERS).my_go()",
 "45-nt-replace": "from svsim.core.script import INVOKERS\nfrom typing import NamedTuple\nclass P(NamedTuple):\n    s: object\n    def my_go(self):\n        self._replace()[0].add(1)\nP(INVOKERS).my_go()",
 "45-nt-sub-asdict": "from svsim.core.script import INVOKERS\nfrom typing import NamedTuple\nclass P(NamedTuple):\n    s: object\nclass Q(P):\n    def my_go(self):\n        self._asdict()['s'].add(1)\nQ(INVOKERS).my_go()",
 "45-exc-tb": "from svsim.core.script import INVOKERS\nclass E(Exception):\n    def my_go(self):\n        self.with_traceback(None).args[0].add(1)\nE(INVOKERS).my_go()",
 "45-userdict-data": "from svsim.core.script import INVOKERS\nimport collections\nclass U(collections.UserDict):\n    def my_go(self):\n        self.data['k'].add(1)\nU(k=INVOKERS).my_go()",
 "45-userlist-data": "from svsim.core.script import INVOKERS\nimport collections\nclass U(collections.UserList):\n    def my_go(self):\n        self.data[0].add(1)\nU([INVOKERS]).my_go()",
 "45-chainmap-maps": "from svsim.core.script import INVOKERS\nimport collections\nclass C(collections.ChainMap):\n    def my_go(self):\n        self.maps[0].add(1)\nC(INVOKERS).my_go()",
 "45-if-nested-class": "from svsim.core.script import INVOKERS\nclass Outer:\n    if True:\n        class Inner:\n            def __init__(self, x):\n                x.add(1)\nOuter.Inner(INVOKERS)",
 "45-if-init": "from svsim.core.script import INVOKERS\nclass K:\n    if True:\n        def __init__(self, x):\n            x.add(1)\nK(INVOKERS)",
 "45-try-method": "from svsim.core.script import INVOKERS\nclass K:\n    try:\n        def my_m(self, x):\n            x.add(1)\n    except Exception:\n        pass\nK().my_m(INVOKERS)",
 "45-cls-alias": "from svsim.core.script import INVOKERS\nclass K:\n    def __init__(self, x=None):\n        if x is not None:\n            x.add(1)\n    @classmethod\n    def mk(cls, v):\n        f = cls\n        return f(v)\nK.mk(INVOKERS)",
 "45-cls-list": "from svsim.core.script import INVOKERS\nclass K:\n    def __init__(self, x=None):\n        if x is not None:\n            x.add(1)\n    @classmethod\n    def mk(cls, v):\n        return [cls][0](v)\nK.mk(INVOKERS)",
 "45-cls-return": "from svsim.core.script import INVOKERS\nclass K:\n    def __init__(self, x=None):\n        if x is not None:\n            x.add(1)\n    @classmethod\n    def kind(cls):\n        return cls\nK.kind()(INVOKERS)",
 "45-cls-arg": "from svsim.core.script import INVOKERS\ndef build(c, v):\n    return c(v)\nclass K:\n    def __init__(self, x=None):\n        if x is not None:\n            x.add(1)\n    @classmethod\n    def mk(cls, v):\n        return build(cls, v)\nK.mk(INVOKERS)",
 "45-dc-sub-field": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    x: object = None\nclass N(M):\n    pass\nN(INVOKERS).x.add(1)",
 "45-dc-sub-field-kw": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    x: object = None\nclass N(M):\n    pass\nN(x=INVOKERS).x.add(1)",
 "45-dc-sub2": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    x: object = None\nclass N(M):\n    pass\nclass E(N):\n    pass\nE(x=INVOKERS).x.add(1)",
 "45-dc-sub-initvar": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    y: dataclasses.InitVar[object] = None\n    def __post_init__(self, y):\n        y.add(1)\nclass N(M):\n    pass\nN(INVOKERS)",
 "45-dc-initvar-default": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    y: dataclasses.InitVar[object] = INVOKERS\n    def __post_init__(self, y):\n        y.add(1)\nM()",
 "45-dc-init-false": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    a: object = None\n    b: object = dataclasses.field(default=None, init=False)\n    c: object = None\nM(1, INVOKERS).c.add(1)",
 "45-dc-kw-only": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    a: object = None\n    b: object = dataclasses.field(default=None, kw_only=True)\n    c: object = None\nM(1, INVOKERS).c.add(1)",
 "45-dc-classvar": "from svsim.core.script import INVOKERS\nimport dataclasses\nimport typing\n@dataclasses.dataclass\nclass M:\n    a: object = None\n    b: typing.ClassVar[int] = 0\n    c: object = None\nM(1, INVOKERS).c.add(1)",
 "45-dc-plain-base": "from svsim.core.script import INVOKERS\nimport dataclasses\nclass Base:\n    a: object = None\n@dataclasses.dataclass\nclass M(Base):\n    b: object = None\n    c: object = None\nM(1, INVOKERS).c.add(1)",
 "45-dc-if-field": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    if True:\n        x: object = None\nM(INVOKERS).x.add(1)",
 "45-dc-super-init": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    x: object = None\nclass N(M):\n    def __init__(self, v):\n        super().__init__(v)\nN(INVOKERS).x.add(1)",
 "45-dc-super-init-kw": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    x: object = None\nclass N(M):\n    def __init__(self, v):\n        super().__init__(x=v)\nN(INVOKERS).x.add(1)",
 "45-enum-init": "from svsim.core.script import INVOKERS\nimport enum\nclass C(enum.Enum):\n    A = INVOKERS\n    def __init__(self, s):\n        s.add(1)",
 "45-enum-tuple": "from svsim.core.script import INVOKERS\nimport enum\nclass C(enum.Enum):\n    A = (1, INVOKERS)\n    def __init__(self, n, s):\n        self.s = s\n    def my_go(self):\n        self.s.add(1)\nC.A.my_go()",
 "45-enum-missing": "from svsim.core.script import INVOKERS\nimport enum\nclass C(enum.Enum):\n    A = 1\n    @classmethod\n    def _missing_(cls, v):\n        v.add(1)\n        return None\ntry:\n    C(INVOKERS)\nexcept ValueError:\n    pass",
 "45-final-craft": "import typing\nfrom svsim.cards.abyss import Craft\ntyping.final(Craft)",
 "45-dc-fraction": "import dataclasses\nimport statistics\ndataclasses.dataclass(statistics.Fraction)",
 "45-dc-alias": "import dataclasses\nimport statistics\ndc = dataclasses.dataclass\ndc(statistics.Fraction)",
 "45-dc-from": "from dataclasses import dataclass as dd\nimport statistics\ndd(statistics.Fraction)",
 "45-global-enum": "import enum\nfrom svsim.core.enums import CardType\nenum.global_enum(CardType)",
 "45-total-ordering": "import functools\nfrom svsim.cards.abyss import Craft\nfunctools.total_ordering(Craft)",
 "45-no-type-check": "import typing\nfrom svsim.cards.abyss import Craft\ntyping.no_type_check(Craft)",
 "45-dt-call": "import typing\nfrom svsim.cards.abyss import Craft\ntyping.dataclass_transform()(Craft)",
 "45-dict-unbound": "from svsim.core.script import INVOKERS\ndict.get({'k': INVOKERS}, 'k').add(1)",
 # LD-46 (the eleventh review, and what fixing it turned up): getattr forms of the decorator-only calls, ABC register,
 # class attributes that hand a shared object to the class statement (a host dataclass's Field), names bound by import
 # rebound, numpy's files, settings and global random numbers, dataclass orders that can't be read
 "46-getattr-dc": "import dataclasses\nimport statistics\ngetattr(dataclasses, 'dataclass')(statistics.Fraction)",
 "46-getattr-abcmeta": "import dataclasses\nimport typing\ngetattr(dataclasses, 'dataclass')(typing.ABCMeta)",
 "46-getattr-final": "import typing\nfrom svsim.cards.abyss import Craft\ngetattr(typing, 'final')(Craft)",
 "46-getattr-total-ordering": "import functools\nfrom svsim.cards.abyss import Craft\ngetattr(functools, 'total_ordering')(Craft)",
 "46-getattr-global-enum": "import enum\nfrom svsim.core.enums import CardType\ngetattr(enum, 'global_enum')(CardType)",
 "46-abstractmethod-call": "import typing\nfrom svsim.core import actions as moves\ntyping.abstractmethod(moves.to_dict)",
 "46-register-typing": "import typing\ntyping.Hashable.register(list)",
 "46-register-cabc": "import collections.abc\ncollections.abc.Hashable.register(list)",
 "46-register-getattr": "import typing\ngetattr(typing.Hashable, 'register')(list)",
 "46-register-alias": "import typing\nr = typing.Iterable.register\nr(int)",
 "46-register-own-abc": "import collections.abc\nclass H(collections.abc.Hashable):\n    def my_h(self):\n        return 1\nH.register(list)",
 "46-field-dataclass": "import dataclasses\nimport typing\nfrom svsim.core import actions as moves\nspec = dataclasses.fields(moves.PlayCard)\n@dataclasses.dataclass\nclass Note:\n    targets: typing.ClassVar[tuple] = spec[1]",
 "46-field-plain-class": "import dataclasses\nimport typing\nfrom svsim.core import actions as moves\nspec = dataclasses.fields(moves.PlayCard)\nclass Note:\n    t = spec[1]",
 "46-field-unpack": "import dataclasses\nimport typing\nfrom svsim.core import actions as moves\nspec = dataclasses.fields(moves.PlayCard)\nclass Note:\n    a, b = spec[0], spec[1]",
 "46-field-unpack-name": "import dataclasses\nimport typing\nfrom svsim.core import actions as moves\nspec = dataclasses.fields(moves.PlayCard)\nclass Note:\n    a, b, c = spec",
 "46-field-in-field": "import dataclasses\nimport typing\nfrom svsim.core import actions as moves\nspec = dataclasses.fields(moves.PlayCard)\n@dataclasses.dataclass\nclass Note:\n    x: object = dataclasses.field(default=spec[1])",
 "46-field-walrus": "import dataclasses\nimport typing\nfrom svsim.core import actions as moves\nspec = dataclasses.fields(moves.PlayCard)\nclass Note:\n    (t := spec[1])",
 "46-field-module-name": "import dataclasses\nimport typing\nfrom svsim.core import actions as moves\nspec = dataclasses.fields(moves.PlayCard)\nF = spec[1]\nclass Note:\n    t = F",
 "46-field-in-method": "import dataclasses\nimport typing\nfrom svsim.core import actions as moves\nspec = dataclasses.fields(moves.PlayCard)\nclass T:\n    def my_f(self):\n        @dataclasses.dataclass\n        class Note:\n            targets: typing.ClassVar[tuple] = spec[1]\n        return Note",
 "46-import-in-class": "class Note:\n    from svsim.core.actions import PlayCard",
 "46-rebind-cache": "import svsim.core.engine as E\nfrom functools import cache\ncache = lambda f: E.INVOKERS\n@cache\ndef f():\n    pass\nf.clear()",
 "46-rebind-def": "import svsim.core.engine as E\nfrom functools import cache\ndef cache(f):\n    return E.INVOKERS\n@cache\ndef f():\n    pass\nf.clear()",
 "46-rebind-module": "import svsim.core.engine as E\nimport functools\nfunctools = E",
 "46-two-imports": "import typing\nfrom typing import cast as d\nfrom dataclasses import dataclass as d\nd(typing.ABCMeta)",
 "46-np-seterr": "import numpy\nnumpy.seterr(all='raise')",
 "46-np-printoptions": "import numpy as np\nnp.set_printoptions(precision=1)",
 "46-np-random-seed": "import numpy\nnumpy.random.seed(3)",
 "46-np-random-rand": "import numpy\nx = numpy.random.rand(3)",
 "46-np-from-random": "from numpy.random import shuffle",
 "46-np-random-alias": "import numpy.random as npr\nnpr.seed(1)",
 "46-np-getattr-random": "import numpy\nr = getattr(numpy, 'random')\nr.seed(1)",
 "46-np-load": "import numpy\nx = numpy.load('x.npy')",
 "46-np-save": "import numpy\nnumpy.save('x.npy', numpy.zeros(3))",
 "46-np-fromregex": "import numpy\nx = numpy.fromregex('k.key', '(.*)', [('k', 'U200')])",
 "46-np-from-load": "from numpy import load",
 "46-np-dump": "import numpy\nnumpy.zeros(3).dump('d.pkl')",
 "46-np-testing": "import numpy.testing",
 "46-np-lib": "import numpy\nx = numpy.lib.format",
 "46-np-test": "import numpy\nnumpy.test()",
 "46-np-ma": "from numpy import ma",
 "46-dc-alias-classvar": "from svsim.core.script import INVOKERS\nimport dataclasses\nimport typing\nCV = typing.ClassVar\n@dataclasses.dataclass\nclass M:\n    a: object = None\n    b: CV[int] = 0\n    c: object = None\nM(1, INVOKERS).c.add(1)",
 "46-dc-lazy-alias": "from __future__ import annotations\nfrom svsim.core.script import INVOKERS\nimport dataclasses\nimport typing\nCV = typing.ClassVar\n@dataclasses.dataclass\nclass M:\n    a: object = None\n    b: CV[int] = 0\n    c: object = None\nM(1, INVOKERS).c.add(1)",
 "46-dc-field-from-func": "from svsim.core.script import INVOKERS\nimport dataclasses\ndef nf():\n    return dataclasses.field(default=None, init=False)\n@dataclasses.dataclass\nclass M:\n    a: object = None\n    b: object = nf()\n    c: object = None\nM(1, INVOKERS).c.add(1)",
 "46-dc-lazy-plain-name": "from __future__ import annotations\nfrom svsim.core.script import INVOKERS\nimport dataclasses\nfrom typing import ClassVar\n@dataclasses.dataclass\nclass M:\n    a: object = None\n    b: ClassVar[int] = 0\n    c: object = None\nM(1, INVOKERS).c.add(1)",
 "46-dc-kw-only-marker": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    a: object = None\n    _: dataclasses.KW_ONLY\n    b: object = None\nM(INVOKERS).a.add(1)",
 "46-dc-initvar-pos": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass M:\n    a: object = None\n    y: dataclasses.InitVar[object] = None\n    c: object = None\n    def __post_init__(self, y):\n        pass\nM(1, 2, INVOKERS).c.add(1)",
 "46-dc-redefined": "from svsim.core.script import INVOKERS\nimport dataclasses\n@dataclasses.dataclass\nclass A:\n    a: object = None\n    b: object = None\n@dataclasses.dataclass\nclass B(A):\n    c: object = None\n    a: object = None\nB(1, INVOKERS).b.add(1)",
 "47-dc-late-classvar": "from __future__ import annotations\nimport dataclasses\nfrom svsim.core.script import INVOKERS\n@dataclasses.dataclass\nclass Box:\n    tag: ClassVar[int] = 0\n    bag: object = None\nfrom typing import ClassVar\ndef f():\n    b = Box(0, INVOKERS)\n    b.bag.add(-7)",
 "47-dc-late-typing": "from __future__ import annotations\nimport dataclasses\nfrom svsim.core.script import INVOKERS\n@dataclasses.dataclass\nclass Box:\n    tag: typing.ClassVar[int] = 0\n    bag: object = None\nimport typing\ndef f():\n    Box(0, INVOKERS).bag.add(-7)",
 "47-dc-late-kwonly": "from __future__ import annotations\nimport dataclasses\nfrom svsim.core.script import INVOKERS\n@dataclasses.dataclass\nclass Box:\n    _: KW_ONLY\n    bag: object = None\nfrom dataclasses import KW_ONLY\ndef f():\n    Box(0, INVOKERS).bag.add(-7)",
 "47-dc-late-quoted": "import dataclasses\nfrom svsim.core.script import INVOKERS\n@dataclasses.dataclass\nclass Box:\n    tag: 'ClassVar[int]' = 0\n    bag: object = None\nfrom typing import ClassVar\ndef f():\n    Box(0, INVOKERS).bag.add(-7)",
 "47-dc-late-in-function": "from __future__ import annotations\nimport dataclasses\nfrom svsim.core.script import INVOKERS\ndef make(x):\n    @dataclasses.dataclass\n    class Box:\n        tag: ClassVar[int] = 0\n        bag: object = None\n    return Box(0, x)\nb = make(INVOKERS)\nfrom typing import ClassVar\nb.bag.add(-7)",
 "47-dc-lazy-quoted-classvar": "from __future__ import annotations\nfrom dataclasses import dataclass, field\nfrom typing import ClassVar\nfrom svsim.core.script import INVOKERS\n@dataclass\nclass Box:\n    tag: 'ClassVar[int]' = 0\n    items: set = field(default_factory=set)\n    src: object = None\ndef f():\n    b = Box(0, INVOKERS)\n    b.items.clear()",
 "47-dc-lazy-quoted-kwonly": "from __future__ import annotations\nfrom dataclasses import dataclass, KW_ONLY\nfrom svsim.core.script import INVOKERS\n@dataclass\nclass Box:\n    tag: int = 0\n    _: 'KW_ONLY' = 0\n    items: object = None\ndef f():\n    Box(0, 0, INVOKERS).items.clear()",
 "47-dc-dup-annotation": "from dataclasses import dataclass, field, KW_ONLY\nfrom svsim.core.script import INVOKERS\n@dataclass\nclass Box:\n    items: set = field(default_factory=set)\n    _: KW_ONLY\n    items: set = field(default_factory=set)\n    src: object = None\ndef f():\n    Box(INVOKERS).items.clear()",
 "47-dc-rebound-in-body": "from dataclasses import dataclass, field\nfrom svsim.core.script import INVOKERS\n@dataclass\nclass Box:\n    tag: int = 0\n    items: object = None\n    tag = field(default=0, init=False)\ndef f():\n    Box(INVOKERS).items.clear()",
 "47-dc-not-simple": "from dataclasses import dataclass\nfrom svsim.core.script import INVOKERS\n@dataclass\nclass Box:\n    (tag): int = 0\n    items: object = None\ndef f():\n    Box(INVOKERS).items.clear()",
 "47-dc-bytes-annotation": "from __future__ import annotations\nfrom dataclasses import dataclass\nfrom typing import ClassVar as b\nfrom svsim.core.script import INVOKERS\n@dataclass\nclass Box:\n    tag: b'x' = 0\n    items: object = None\ndef f():\n    Box(INVOKERS).items.clear()",
 "47-dc-extra-args": "from dataclasses import dataclass\nfrom svsim.core.script import INVOKERS\n@dataclass\nclass Box:\n    items: object = None\nclass Sub(Box):\n    def __init__(self, *a):\n        pass\ndef f():\n    b = Box(0, INVOKERS)\n    b.items.clear()",
 "47-np-copyto-window": "import numpy as np\nnp.copyto(np.polynomial.Polynomial.window, [0, 3], casting='unsafe')",
 "47-np-out-window": "import numpy as np\nnp.multiply(np.polynomial.Polynomial.window, 2, out=np.polynomial.Polynomial.window)",
 "47-np-out-tuple": "import numpy as np\nw = np.polynomial.Chebyshev.domain\nnp.negative(w, out=(w,))",
 "47-np-positional-out": "import numpy as np\nnp.negative(np.polynomial.Polynomial.window, np.polynomial.Polynomial.window)",
 "47-np-place": "import numpy as np\nnp.place(np.polynomial.Polynomial.window, [True, False], [9])",
 "47-np-putmask": "import numpy as np\nnp.putmask(np.polynomial.Polynomial.window, [True, False], 9)",
 "47-np-fill-diagonal": "import numpy as np\nnp.fill_diagonal(np.polynomial.Chebyshev.domain.reshape(1, 2), 9)",
 "47-np-put-along": "import numpy as np\nnp.put_along_axis(np.polynomial.Polynomial.window, np.array([0]), 9, 0)",
 "47-np-put": "import numpy as np\nnp.put(np.polynomial.Polynomial.window, [0], [5])",
 "47-np-copyto-alias": "import numpy as np\nfrom numpy import copyto as cp\ncp(np.polynomial.polynomial.polyx, [1, 2])",
 "47-np-at": "import numpy as np\nnp.add.at(np.polynomial.Polynomial.window, [0], 1)",
 "47-np-reduce-out": "import numpy as np\nnp.add.reduce(np.ones((2, 2)), 0, None, np.polynomial.Polynomial.window)",
 "47-np-clip-out": "import numpy as np\nnp.clip(np.ones(2), 0, 1, out=np.polynomial.Polynomial.window)",
 "47-np-generator-out": "import numpy as np\nnp.random.default_rng(1).random(out=np.polynomial.Chebyshev.window)",
 "47-np-printstyle": "import numpy as np\nnp.polynomial.set_default_printstyle('ascii')",
 "47-np-out-literal-star": "import numpy as np\nnp.add(np.ones(2), 1, **{'out': np.polynomial.Polynomial.window})",
 "48-dc-init-truthy": "import collections\nimport copy\nimport dataclasses\n@dataclasses.dataclass(init=1)\nclass Bag:\n    bag: object = None\nb = Bag(bag=copy.dispatch_table)\nb.bag[collections.ChainMap] = None",
 "48-dc-stacked": "import dataclasses\nfrom svsim.core.script import INVOKERS\n@dataclasses.dataclass(eq=True)\n@dataclasses.dataclass(init=False)\nclass M:\n    c: object = None\nM(c=INVOKERS).c.add(1)",
 "48-np-clip-pos": "import numpy as np\nnp.clip(np.polynomial.Polynomial.window, 0, 0, np.polynomial.Polynomial.window)",
 "48-np-cumsum-pos": "import numpy as np\nnp.cumsum(np.polynomial.Polynomial.window, 0, None, np.polynomial.Polynomial.window)",
 "48-np-dot-pos": "import numpy as np\nnp.dot(np.eye(2), np.array([5.0, 6.0]), np.polynomial.Polynomial.window)",
 "48-np-take-pos": "import numpy as np\nnp.take(np.array([5, 6]), [0, 1], None, np.polynomial.Polynomial.window)",
 "48-np-rng-pos": "import numpy as np\ng = np.random.default_rng(1)\ng.random(2, np.float64, np.polynomial.Polynomial.domain)",
 "48-np-method-pos": "import numpy as np\na = np.ones(2)\na.clip(0, 0, np.polynomial.Polynomial.window)",
 "48-np-star-pos": "import numpy as np\nnp.clip(*(np.polynomial.Polynomial.window, 0, 0, np.polynomial.Polynomial.window))",
 "48-np-ndarray-buffer": "import numpy as np\nb = np.ndarray((2,), float, np.polynomial.Polynomial.window)\nb[0] = 5.0",
 "48-np-frombuffer": "import numpy as np\nb = np.frombuffer(np.polynomial.Polynomial.window)",
 "48-np-nditer": "import numpy as np\nit = np.nditer(np.polynomial.Polynomial.window, op_flags=['readwrite'])",
 "48-np-nan-to-num": "import numpy as np\nnp.nan_to_num(np.polynomial.Polynomial.window, copy=False)",
 "48-np-out-own-method-name": "import numpy as np\nclass Vec:\n    def multiply(self, k):\n        return k\nnp.multiply(np.ones(2), 7.0, out=np.polynomial.Chebyshev.domain)",
 "49-dc-splat-init": "import copy\nimport dataclasses\nfrom ladder.base import PublicPosition\nclass Holder:\n    def __init__(self, first=None, second=None):\n        self.kept = second\n@dataclasses.dataclass(**{'init': False})\nclass Box(Holder):\n    bag: object = None\ndef boom(p):\n    raise RuntimeError('x')\nb = Box(None, copy.dispatch_table)\nb.kept[PublicPosition] = boom",
 "49-dc-splat-other": "import dataclasses\n@dataclasses.dataclass(**{'eq': True})\nclass Node:\n    a: int = 0",
 "49-dc-positional": "import dataclasses\n@dataclasses.dataclass(None)\nclass Node:\n    a: int = 0",
 "49-np-any-pos": "import numpy as np\nnp.zeros((3, 2)).any(0, None, np.polynomial.Polynomial.window)",
 "49-np-conj-pos": "import numpy as np\nnp.full(2, 4.0).conj(np.polynomial.Polynomial.window)",
 "49-np-product": "import numpy as np\nnp.product(np.ones((3, 2)), 0, None, np.polynomial.Polynomial.window)",
 "49-np-sometrue-import": "from numpy import sometrue",
 "49-np-partial-out": "import functools\nimport numpy as np\nfunctools.partial(np.negative, out=np.polynomial.Polynomial.window)(np.polynomial.Polynomial.window)",
 "49-np-partial-pos": "from functools import partial\nimport numpy as np\npartial(np.negative, np.ones(2), np.polynomial.Polynomial.window)()",
 "49-np-median-ow": "import numpy as np\nnp.median(np.polynomial.laguerre.lagx, overwrite_input=True)",
 "49-np-percentile-ow-pos": "import numpy as np\nnp.percentile(np.polynomial.laguerre.lagx, 50, None, None, True)",
 "49-np-nanquantile-ow": "import numpy as np\nnp.nanquantile(np.polynomial.laguerre.lagx, 0.5, overwrite_input=1)",
 "49-np-nan-to-num-pos": "import numpy as np\nnp.nan_to_num(np.polynomial.laguerre.lagx, False)",
 "49-np-array-repr-width": "import numpy as np\ntry:\n    np.array_repr(np.zeros(1), np.polynomial.Polynomial.window)\nexcept ValueError:\n    pass",
 "49-np-array2string-width": "import numpy as np\ntry:\n    np.array2string(np.zeros(1), max_line_width=np.polynomial.Polynomial.window, suffix='ab')\nexcept ValueError:\n    pass",
 "49-np-rot90-k": "import numpy as np\nnp.rot90(np.ones((2, 2)), np.polynomial.Polynomial.window)",
 "49-np-cls-sum": "import numpy as np\nnp.ndarray.sum(np.ones((3, 2)), 0, None, np.polynomial.Polynomial.window)",
 "49-np-cls-clip-from": "from numpy import ndarray, ones\nfrom numpy.polynomial import Polynomial\nndarray.clip(ones(2), 0, 0, Polynomial.window)",
 "49-np-cls-gen-random": "import numpy as np\nnp.random.Generator.random(np.random.default_rng(1), 2, 'float64', np.polynomial.Polynomial.domain)",
 "49-np-cls-shuffle": "import numpy as np\nnp.random.Generator.shuffle(np.random.default_rng(1), np.polynomial.laguerre.lagx)",
 "49-np-printoptions": "import numpy as np\nwith np.printoptions(precision=1):\n    pass",
 "50-replace-own-init": "import copy\nimport dataclasses\nfrom ladder.base import PublicPosition\n@dataclasses.dataclass\nclass Box:\n    bag: object = None\n    def __init__(self, bag=None):\n        self.kept = bag\n    def poison(self):\n        self.kept[PublicPosition] = None\ndataclasses.replace(Box(), bag=copy.dispatch_table).poison()",
 "50-replace-base-init": "import copy\nimport dataclasses\nfrom ladder.base import PublicPosition\nclass Holder:\n    def __init__(self, bag=None):\n        self.kept = bag\n    def poison(self):\n        self.kept[PublicPosition] = None\n@dataclasses.dataclass(init=False)\nclass Box(Holder):\n    bag: object = None\ndataclasses.replace(Box(), bag=copy.dispatch_table).poison()",
 "50-replace-registry": "import copy\nimport dataclasses\nREG = []\n@dataclasses.dataclass\nclass Box:\n    bag: object = None\n    def __init__(self, bag=None):\n        REG.append(bag)\ndataclasses.replace(Box(), bag=copy.dispatch_table)\nREG[-1][int] = None",
 "50-replace-numpy-table": "import dataclasses\nimport numpy as np\n@dataclasses.dataclass\nclass Box:\n    bag: object = None\n    def __init__(self, bag=None):\n        self.kept = bag\n    def put_in(self, k, v):\n        self.kept[k] = v\nb = dataclasses.replace(Box(), bag=np.sctypeDict)\nb.put_in('float32', np.int8)",
 "50-replace-attr-of-obj": "import copy\nimport dataclasses\n@dataclasses.dataclass\nclass Box:\n    bag: object = None\n    def __init__(self, bag=None):\n        self.kept = bag\nb = Box()\nb.bag = copy.dispatch_table\nc = dataclasses.replace(b)\nc.kept[int] = None",
 "50-type-shuffle": "import random\nfrom svsim.cards import forest\nr = random.Random(1)\ntype(r).shuffle(r, forest.CARDS)",
 "50-alias-shuffle": "import random\nfrom svsim.cards import forest\nR = random.Random\nR.shuffle(random.Random(1), forest.CARDS)",
 "50-getattr-shuffle": "import random\nfrom svsim.cards import forest\ngetattr(random.Random(1), 'shuffle')(forest.CARDS)",
 "50-getattr-heappush": "import heapq\nfrom svsim.cards import forest\ngetattr(heapq, 'heappush')(forest.CARDS, 1)",
 "50-star-cls-shuffle": "import random\nfrom svsim.cards import forest\nrandom.Random.shuffle(*(random.Random(1), forest.CARDS))",
 "50-np-type-sum": "import numpy as np\nx = np.ones((3, 2))\ntype(x).sum(x, 0, None, np.polynomial.Polynomial.window)",
 "50-np-alias-sum": "import numpy as np\nA = np.ndarray\nA.sum(np.ones((3, 2)), 0, None, np.polynomial.Polynomial.window)",
 "50-np-getattr-sum": "import numpy as np\ngetattr(np.ndarray, 'sum')(np.ones((3, 2)), 0, None, np.polynomial.Polynomial.window)",
 "50-np-type-shuffle": "import numpy as np\nrng = np.random.default_rng(1)\ntype(rng).shuffle(rng, np.polynomial.laguerre.lagx)",
 "47-np-emath": "import numpy as np\nx = np.emath.sqrt(-1.0)",
 "47-np-emath-import": "import numpy.emath as em\nx = em.sqrt(-1.0)",
}
GOOD_LD42 = {
 "tree": "class Node:\n    def __init__(self, parent, move):\n        self.parent = parent\n        self.move = move\n        self.children = []\n        self.visits = 0\n        if parent is not None:\n            parent.children.append(self)\nclass T(PlayerStrategy):\n    def search(self, pos):\n        root = Node(None, None)\n        n = Node(Node(root, 1), 2)\n        while n is not None:\n            n.visits += 1\n            n = n.parent\n        return {}",
 "grid": "class Grid:\n    def __init__(self, rows, cols):\n        self.cells = [[0.0] * cols for _ in range(rows)]\n    def place(self, r, c, v):\n        self.cells[r][c] = v\nclass T(PlayerStrategy):\n    def search(self, pos):\n        g = Grid(3, 4)\n        g.place(1, 2, 5.0)\n        return {}",
 "helper-param": "from collections import defaultdict\nclass T(PlayerStrategy):\n    def __init__(self, seed=0):\n        super().__init__(seed)\n        self.stats = defaultdict(list)\n    def _bump(self, stats, key, v):\n        stats[key].append(v)\n    def search(self, pos):\n        self._bump(self.stats, pos.state.turn, 1.0)\n        return {}",
 "defaultdict-counter": "from collections import defaultdict, Counter, deque\nclass T(PlayerStrategy):\n    def guess(self, pos):\n        d = defaultdict(Counter)\n        d['a']['b'] += 1\n        q = defaultdict(deque)\n        q['a'].append(1)\n        q['a'].popleft()\n        return super().guess(pos)",
 "enum": "import enum\nclass Mode(enum.Enum):\n    AGGRO = 1\n    CONTROL = 2\nclass T(PlayerStrategy):\n    def __init__(self, seed=0):\n        super().__init__(seed)\n        self.counts = {m: 0 for m in Mode}\n        self.mode = Mode['AGGRO']\n    def search(self, pos):\n        self.counts[self.mode] += 1\n        return {}",
 "match-class": "class Plan:\n    def __init__(self, level):\n        self.level = level\nclass T(PlayerStrategy):\n    def search(self, pos):\n        match Plan(3):\n            case Plan(level=l) if l > 2:\n                return {'iterations': 150}\n        return {}",
 "real-setter": "class K:\n    def __init__(self):\n        self._p = 0\n    @property\n    def p(self):\n        return self._p\n    @p.setter\n    def p(self, v):\n        self._p = v\nk = K()\nk.p = 3",
 "lru-method": "import functools\nclass T(PlayerStrategy):\n    @functools.lru_cache(maxsize=None)\n    def cost(self, n):\n        return n * 2\n    def search(self, pos):\n        return {'iterations': 100 + self.cost(1)}",
 "mul-float": "from svsim.search.evaluate import evaluate, DEFAULT\nclass T(PlayerStrategy):\n    def evaluate(self, state, me, me_next):\n        v = evaluate(state, me, DEFAULT, player_moves_next=me_next)\n        v *= 0.5\n        return v",
 "yield-plain": "def pairs(xs):\n    for i, x in enumerate(xs):\n        try:\n            v = x * 2\n        except TypeError:\n            v = 0\n        yield i, v",
}
GOOD_LD43 = {
 "typing-bases": "from typing import NamedTuple, Generic, TypeVar, TypedDict\nimport collections\nT_ = TypeVar('T_')\nclass E(NamedTuple):\n    u: int\n    v: int\nclass Box(Generic[T_]):\n    pass\nclass TD(TypedDict):\n    a: int\nclass E2(collections.namedtuple('E2', 'a b')):\n    pass\nclass G:\n    def __init__(self):\n        self.cells = [[0] * 3 for _ in range(3)]\n    def place(self, r, c, v):\n        self.cells[r][c] = v\nG().place(1, 1, 3)\nn = E(1, 2).u + 1",
 "unknown-base-elsewhere": "def mk():\n    return object\nclass W(mk()):\n    pass\nclass G:\n    def __init__(self):\n        self.items = []\n    def my_g(self, y):\n        y.items.append(1)\nG().my_g(G())",
 "cls-factory": "class Node:\n    def __init__(self, parent=None):\n        self.children = []\n        if parent is not None:\n            parent.children.append(self)\nclass Feat:\n    def __init__(self, life, hand):\n        self.life, self.hand = life, hand\n    @classmethod\n    def of(cls, pos):\n        p = pos.state.players[0]\n        return cls(p.life, len(p.hand))\nclass T(PlayerStrategy):\n    def search(self, pos):\n        f = Feat.of(pos)\n        Node(Node())\n        return {}",
 "field-factory": "import collections\nimport dataclasses\n@dataclasses.dataclass\nclass Memory:\n    counts: collections.Counter = dataclasses.field(default_factory=collections.Counter)\n    q: collections.deque = dataclasses.field(default_factory=collections.deque)\nclass T(PlayerStrategy):\n    def __init__(self, seed=0):\n        super().__init__(seed)\n        self.mem = Memory()\n    def search(self, pos):\n        self.mem.counts[pos.turn] += 1\n        self.mem.q.append(1)\n        return {}",
 "select-store": "class Tree:\n    def __init__(self):\n        self.rows = {}\n    def select(self, node):\n        node.hits.append(1)\n        return node\n    def store(self, k, entry):\n        entry.seen.append(k)\n        self.rows[k] = entry\nclass Entry:\n    def __init__(self):\n        self.hits, self.seen = [], []\nt = Tree()\nt.store(1, t.select(Entry()))",
}
GOOD_LD44 = {
 "generic-own-sub": "from typing import Generic, TypeVar\nT_ = TypeVar('T_')\nclass Stack(Generic[T_]):\n    def __init__(self):\n        self.items = []\n    def my_push(self, x):\n        self.items.append(x)\nclass IntStack(Stack[int]):\n    pass\ns = IntStack()\ns.my_push(1)\ns.items.append(2)",
 "cls-factory-mutate": "class Feat:\n    def __init__(self):\n        self.rows = []\n    @classmethod\n    def make(cls):\n        return cls()\nf = Feat.make()\nf.rows.append(1)",
 "nt-forms": "import collections, typing\nclass P(collections.namedtuple('P', ['a', 'b'])):\n    pass\nclass Q(typing.NamedTuple('Q', [('a', int)])):\n    pass\nclass E(typing.NamedTuple):\n    u: int\n    v: int\n    def my_len(self):\n        return self.u + self.v\nrows = [E(1, 2)]\nrows.append(E(3, 4))\nx = P(1, 2).a + Q(1).a + sum(e.my_len() for e in rows)",
 "dict-sub-plain": "class Tally(dict):\n    def my_bump(self, k):\n        self[k] = self.get(k, 0) + 1\nt = Tally()\nt.my_bump('a')",
 "initvar": "import dataclasses\n@dataclasses.dataclass\nclass M:\n    n: dataclasses.InitVar[int] = 3\n    rows: list = dataclasses.field(default_factory=list)\n    def __post_init__(self, n):\n        self.rows = [0] * n\nm = M(4)\nm.rows.append(1)\nm.rows[0] += 1",
}
GOOD_LD45 = {
 "45-root-sub": "class Node:\n    def __init__(self, parent=None, move=None):\n        self.parent, self.move = parent, move\n        self.children = []\n        self.n, self.w = 0, 0.0\n        if parent is not None:\n            parent.children.append(self)\nclass Root(Node):\n    def __init__(self, pos):\n        super().__init__()\n        self.turn = pos.turn\nclass T(PlayerStrategy):\n    def search(self, pos):\n        root = Root(pos)\n        n = Node(root, 1)\n        while n is not None:\n            n.n = n.n + 1\n            n.w = n.w + 0.5\n            n = n.parent\n        return {}",
 "45-model-hier": "class Model:\n    def __init__(self, table=None):\n        self.table = {} if table is None else table\n    def my_see(self, k):\n        self.table.setdefault(k, 0)\n        self.table[k] = self.table[k] + 1\nclass CraftModel(Model):\n    def __init__(self, craft):\n        super().__init__()\n        self.craft = craft\nclass T(PlayerStrategy):\n    def search(self, pos):\n        m = CraftModel(pos.turn)\n        m.my_see(1)\n        return {}",
 "45-generic-own-arg": "from typing import Generic, TypeVar\nimport dataclasses\nT_ = TypeVar('T_')\n@dataclasses.dataclass\nclass Arm:\n    n: int = 0\nclass Pool(Generic[T_]):\n    def __init__(self):\n        self.items = []\n    def my_add(self, x):\n        self.items.append(x)\nclass ArmPool(Pool[Arm]):\n    pass\np = ArmPool()\np.my_add(Arm())",
 "45-planet": "import enum\nclass Planet(enum.Enum):\n    MERCURY = (3.303e+23, 2.4397e6)\n    VENUS = (4.869e+24, 6.0518e6)\n    def __init__(self, mass, radius):\n        self.mass = mass\n        self.radius = radius\n    def my_g(self):\n        return self.mass / (self.radius * self.radius)\nx = Planet.VENUS.my_g()",
 "45-dc-decorators": "import dataclasses, functools, typing\n@dataclasses.dataclass(frozen=True)\nclass K:\n    a: int = 0\n@typing.final\nclass F:\n    pass\nk = K(1)",
 "45-dc-node-state": "import dataclasses\n@dataclasses.dataclass\nclass Node:\n    state: object\n    children: list = dataclasses.field(default_factory=list)\nclass T(PlayerStrategy):\n    def search(self, pos):\n        root = Node(pos.state)\n        root.children.append(Node(pos.state))\n        return {}",
 "45-dc-sub-node": "import dataclasses\n@dataclasses.dataclass\nclass Node:\n    state: object\n    children: list = dataclasses.field(default_factory=list)\nclass Root(Node):\n    pass\nclass T(PlayerStrategy):\n    def search(self, pos):\n        root = Root(pos.state)\n        root.children.append(Node(pos.state))\n        return {}",
 "45-cls-factory": "class Feat:\n    def __init__(self, life=0):\n        self.life = life\n        self.rows = []\n    @classmethod\n    def of(cls, pos):\n        return cls(pos.turn)\n    @classmethod\n    def is_me(cls, x):\n        return isinstance(x, cls) and cls is Feat\nclass T(PlayerStrategy):\n    def search(self, pos):\n        f = Feat.of(pos)\n        f.rows.append(1)\n        return {}",
 "45-cache-own": "import functools\ndef slow(n):\n    return n * 2\nfast = functools.cache(slow)\n@functools.lru_cache(maxsize=None)\ndef g(n):\n    return n",
 "45-replace-star-fixed": "import dataclasses\n@dataclasses.dataclass\nclass Node:\n    v: int = 0\n    children: list = dataclasses.field(default_factory=list)\n@dataclasses.dataclass(frozen=True)\nclass Knobs:\n    iterations: int = 80\nclass T(PlayerStrategy):\n    def search(self, pos):\n        k = dataclasses.replace(Knobs(), **({'iterations': 80 + pos.turn} if pos.turn > 10 else {}))\n        root = Node(-1)\n        root.children.append(Node(0))\n        return {'iterations': k.iterations}",
 "45-tally": "class Tally(dict):\n    def my_bump(self, k):\n        self[k] = self.get(k, 0) + 1\nt = Tally()\nt.my_bump('a')",
}
GOOD_LD46 = {
 "46-mcts-classvar": "import dataclasses\nimport math\nimport typing\n@dataclasses.dataclass\nclass Node:\n    state: object\n    parent: object = None\n    children: list = dataclasses.field(default_factory=list)\n    visits: int = 0\n    total: float = 0.0\n    C: typing.ClassVar[float] = math.sqrt(2)\n    @classmethod\n    def root(cls, state):\n        return cls(state)\n    def child(self, state):\n        c = Node(state, self)\n        self.children.append(c)\n        return c\nclass T(PlayerStrategy):\n    def search(self, pos):\n        root = Node.root(pos.state)\n        node = root.child(pos.state)\n        while node is not None:\n            node.visits += 1\n            node.total += 0.5\n            node = node.parent\n        return {}",
 "46-dc-init-false": "import dataclasses\n@dataclasses.dataclass\nclass Node:\n    state: object\n    children: list = dataclasses.field(default_factory=list)\n    best: object = dataclasses.field(default=None, init=False)\nclass T(PlayerStrategy):\n    def search(self, pos):\n        root = Node(pos.state)\n        root.children.append(Node(pos.state))\n        return {}",
 "46-dc-kw-only": "import dataclasses\n@dataclasses.dataclass\nclass Node:\n    state: object\n    children: list = dataclasses.field(default_factory=list)\n    _: dataclasses.KW_ONLY\n    depth: int = 0\nclass T(PlayerStrategy):\n    def search(self, pos):\n        root = Node(pos.state, depth=1)\n        root.children.append(Node(pos.state))\n        return {}",
 "46-dc-initvar-last": "import dataclasses\n@dataclasses.dataclass\nclass Node:\n    state: object\n    children: list = dataclasses.field(default_factory=list)\n    n: dataclasses.InitVar[int] = 0\n    def __post_init__(self, n):\n        self.visits = n\nclass T(PlayerStrategy):\n    def search(self, pos):\n        root = Node(pos.state)\n        root.children.append(Node(pos.state))\n        return {}",
 "46-dc-sub-classvar": "import dataclasses\nimport typing\n@dataclasses.dataclass\nclass Node:\n    move: object = None\n    parent: object = None\n    children: list = dataclasses.field(default_factory=list)\n    @classmethod\n    def make(cls, move, parent):\n        return cls(move, parent)\n@dataclasses.dataclass\nclass Root(Node):\n    BUDGET: typing.ClassVar[int] = 100\nclass T(PlayerStrategy):\n    def search(self, pos):\n        r = Root.make(pos.turn, None)\n        r.children.append(Node.make(1, r))\n        return {}",
 "46-dc-lazy-classvar": "from __future__ import annotations\nimport dataclasses\nimport typing\n@dataclasses.dataclass\nclass Node:\n    state: object\n    children: list = dataclasses.field(default_factory=list)\n    C: typing.ClassVar[float] = 1.4\nclass T(PlayerStrategy):\n    def search(self, pos):\n        root = Node(pos.state)\n        root.children.append(Node(pos.state))\n        return {}",
 "46-enum-missing": "import enum\nclass Mode(enum.Enum):\n    AGGRO = 'aggro'\n    CONTROL = 'control'\n    @classmethod\n    def _missing_(cls, value):\n        value = value.lower()\n        for member in cls:\n            if member.value == value:\n                return member\n        return None\nm = Mode('AGGRO')",
 "46-enum-base": "import enum\nclass Parsable(enum.Enum):\n    @classmethod\n    def parse(cls, s):\n        return cls[s.upper()]\n    @classmethod\n    def best(cls, t):\n        return max(cls, key=lambda m: len(m.name) * t)\nclass Mode(Parsable):\n    AGGRO = 1\n    CONTROL = 2\nm = Mode.parse('aggro')\nb = Mode.best(2)\nn = list(Mode)",
 "46-class-constants": "import math\nfrom svsim.core import actions as moves\nfrom svsim.core.enums import Craft\nclass T(PlayerStrategy):\n    FOREST = Craft.FOREST\n    PLAY = moves.PlayCard\n    PI = math.pi\n    ORDER = tuple(Craft)\n    def veto(self, state, action):\n        return isinstance(action, T.PLAY) and False",
 "46-dc-static-defaults": "import dataclasses\nimport math\nfrom svsim.core.enums import Craft\n@dataclasses.dataclass\nclass Plan:\n    craft: object = Craft.FOREST\n    c: float = math.pi\n    other: object = dataclasses.field(default=Craft.FOREST)\np = Plan()",
 "46-singledispatch": "import functools\n@functools.singledispatch\ndef score(x):\n    return 0\n@score.register\ndef _(x: int):\n    return x\nscore.register(float, lambda x: int(x))\nv = score(3)",
 "46-np-allowed": "import numpy as np\nfrom numpy.random import default_rng\nclass T(PlayerStrategy):\n    def __init__(self, seed=0):\n        super().__init__(seed)\n        self.rng = np.random.default_rng(seed)\n        self.g = default_rng(seed + 1)\n    def prior(self, state, actions):\n        p = self.rng.random(len(actions)) + 1.0\n        p = p / np.linalg.norm(p, 1)\n        return list(p)",
 "46-same-import-twice": "import svsim\nimport svsim.core\nfrom dataclasses import dataclass\nfrom dataclasses import dataclass\n@dataclass\nclass K:\n    a: int = 0",
}
GOOD_LD47 = {
 "47-dc-lazy-quoted-node": "from __future__ import annotations\nimport dataclasses\nimport typing\n@dataclasses.dataclass\nclass Node:\n    state: object\n    parent: 'Node' = None\n    children: list = dataclasses.field(default_factory=list)\n    C: typing.ClassVar[float] = 1.4\nclass T(PlayerStrategy):\n    def search(self, pos):\n        root = Node(pos.state)\n        root.children.append(Node(pos.state, root))\n        return {}",
 "47-np-functions": "import numpy as np\nclass T(PlayerStrategy):\n    def prior(self, state, actions):\n        p = np.add(np.ones(len(actions)), 1.0)\n        p = np.sort(np.subtract(p, 0.5))\n        q = np.zeros(len(actions))\n        np.multiply(p, 2.0, out=q)\n        np.copyto(q, p)\n        np.negative(q, q)\n        np.add.at(q, [0], 1.0)\n        np.put(q, [0], [1.0])\n        self.rng = np.random.default_rng(1)\n        self.rng.random(out=q)\n        np.negative(*[q, q])\n        np.add(q, 1.0, **{'out': q})\n        d = dict(out=pos.state)\n        return list(q / q.sum())",
 "48-own-place": "class Board:\n    def __init__(self):\n        self.cells = {}\n    def place(self, card, slot):\n        self.cells[slot] = card.defn.card_id\ndef put_along_axis(card, lane):\n    return lane\nclass T(PlayerStrategy):\n    def search(self, pos):\n        b = Board()\n        for i, card in enumerate(pos.state.players[0].hand):\n            b.place(card, i)\n            put_along_axis(card, i)\n        return {}",
 "48-out-field": "import dataclasses\nimport typing\n@dataclasses.dataclass\nclass Step:\n    action: object = None\n    out: object = None\nclass Edge(typing.NamedTuple):\n    a: object\n    out: object\nclass T(PlayerStrategy):\n    def __init__(self, seed=0):\n        super().__init__(seed)\n        self.log = []\n    def veto(self, state, action):\n        self.log.append(Step(action=action, out=state))\n        self.log.append(Edge(a=action, out=state))\n        s = '{out}'.format(out=state.turn)\n        return False",
 "48-np-mlp": "import numpy as np\nclass T(PlayerStrategy):\n    def __init__(self, seed=0):\n        super().__init__(seed)\n        g = np.random.default_rng(seed)\n        self.W1, self.b1, self.W2 = g.normal(size=(8, 3)), np.zeros(8), g.normal(size=8)\n    def evaluate(self, state, me, me_next):\n        p, q = state.players[me], state.players[1 - me]\n        x = np.array([p.leader_hp - q.leader_hp, len(p.hand), len(p.board)], dtype=float)\n        h = self.W1 @ x + self.b1\n        np.maximum(h, 0, out=h)\n        np.tanh(h, out=h)\n        span = (0, p.leader_hp)\n        xs = np.linspace(*span, 5)\n        s = np.sum(h, 0)\n        c = np.clip(h, 0, 1)\n        return float(self.W2 @ h) + float(xs[0]) + float(s) + float(c[0])",
 "49-np-stats": "import functools\nimport numpy as np\ndef own(a, out=None):\n    return a\nclass T(PlayerStrategy):\n    def evaluate(self, state, me, me_next):\n        p, q = state.players[me], state.players[1 - me]\n        xs = np.array([float(c.atk) for c in p.board] + [0.0])\n        ys = np.zeros(4)\n        buf = np.zeros(())\n        rng = np.random.default_rng(state.turn)\n        order = list(range(4))\n        np.random.Generator.shuffle(rng, order)\n        m = np.median(xs) + np.percentile(xs, 90) + np.median(ys, overwrite_input=True) + np.nanmedian(xs, None, None, False)\n        z = np.nan_to_num(xs) + np.nan_to_num(xs, True)\n        s = np.array2string(xs, max_line_width=120) + np.array_repr(xs, 80)\n        r = np.rot90(np.zeros((2, 2)), int(state.turn))\n        f = bool(xs.any()) + bool(xs.all(0)) + float(xs.conj()[0]) + float(np.ndarray.sum(xs, 0, None, buf))\n        g = functools.partial(np.clip, a_min=0, a_max=1)(xs)\n        h = functools.partial(own, out=state)(xs)\n        return float(m) + float(z[0]) + len(s) + float(r[0, 0]) + f + float(g[0]) + float(h[0]) + order[0]",
 "49-dc-keywords": "import dataclasses\nfrom dataclasses import dataclass, field\n@dataclass(frozen=True, order=True)\nclass Key:\n    score: float = 0.0\n    tag: str = ''\n@dataclasses.dataclass(init=True, eq=False)\nclass Node:\n    visits: int = 0\n    kids: list = field(default_factory=list)\n@dataclass()\nclass Leaf:\n    v: float = 0.0\nclass T(PlayerStrategy):\n    def search(self, pos):\n        n = Node()\n        n.kids.append(Leaf(1.0))\n        n.visits += 1\n        return {'iterations': 100 + len(n.kids) + int(Key(1.0) < Key(2.0))}",
 "50-replace-and-shuffle": "import dataclasses\nimport random\nimport numpy as np\nfrom svsim.search.evaluate import DEFAULT\n@dataclasses.dataclass(frozen=True)\nclass Node:\n    score: float = 0.0\n    kids: tuple = ()\nclass T(PlayerStrategy):\n    def weights(self, pos):\n        return dataclasses.replace(DEFAULT, hp=1.0)\n    def search(self, pos):\n        n = dataclasses.replace(Node(), score=1.0, kids=(Node(),))\n        xs = list(pos.state.players[0].hand)\n        type(self.random).shuffle(self.random, xs)\n        rng = np.random.default_rng(1)\n        a = np.zeros((3, 3))\n        type(rng).shuffle(rng, a)\n        getattr(self.random, 'shuffle')(xs)\n        b = np.zeros(())\n        type(a).sum(a, 0, None)\n        a.sum(None, None, b)\n        return {'iterations': 100 + len(n.kids) + len(xs)}",
 "48-type-checking-import": "from __future__ import annotations\nimport dataclasses\nimport typing\nif typing.TYPE_CHECKING:\n    from svsim.core.state import GameState\n@dataclasses.dataclass\nclass Node:\n    state: GameState\n    visits: int = 0\n    children: list = dataclasses.field(default_factory=list)\nclass T(PlayerStrategy):\n    def search(self, pos):\n        n = Node(pos.state)\n        n.visits += 1\n        n.children.append(Node(pos.state))\n        return {}",
}
GOOD = {
 "field-shadow": "from dataclasses import field\ndef f():\n    field = {}\n    field['a'] = 1\n    return field",
 "memo": "from ladder import base\nclass T(PlayerStrategy):\n    def __init__(self, seed=0):\n        super().__init__(seed)\n        self._memo = {}\n    def search(self, pos):\n        k = base.fingerprint(pos)\n        self._memo.setdefault(k, []).append(1)\n        self._memo[k] = [2]\n        return {}",
 "counter": "from collections import Counter\nclass T(PlayerStrategy):\n    def guess(self, pos):\n        c = Counter()\n        for card in pos.state.players[0].hand:\n            c[card.defn.card_id] += 1\n        return super().guess(pos)",
 "counter2": "from collections import Counter\nclass T(PlayerStrategy):\n    def guess(self, pos):\n        c = Counter(card.defn.card_id for card in pos.state.players[0].hand)\n        c[1] += 1\n        return super().guess(pos)",
 "score-aug": "from svsim.search.evaluate import evaluate, DEFAULT\nclass T(PlayerStrategy):\n    def evaluate(self, state, me, me_next):\n        v = evaluate(state, me, DEFAULT, player_moves_next=me_next)\n        v += 0.1 * state.turn\n        v -= self.random.random()\n        return v",
 "replace-weights": "import dataclasses\nfrom svsim.search.evaluate import DEFAULT\nclass T(PlayerStrategy):\n    def weights(self, pos):\n        return dataclasses.replace(DEFAULT, hp=1.0)",
 "sort-actions": "class T(PlayerStrategy):\n    def prior(self, state, actions):\n        acts = list(actions)\n        acts.sort(key=lambda a: repr(a))\n        n = len(acts)\n        return [1.0 / n] * n",
 "history": "class T(PlayerStrategy):\n    def __init__(self, seed=0):\n        super().__init__(seed)\n        self.seen = set()\n        self.hist = []\n    def search(self, pos):\n        self.seen.add(pos.turn)\n        self.hist.append(pos.turn)\n        if len(self.hist) > 10:\n            self.hist.pop(0)\n            self.seen.clear()\n        return {}",
 "helper-func": "def score(cards):\n    cards = sorted(cards)\n    cards.reverse()\n    return cards\nclass T(PlayerStrategy):\n    def search(self, pos):\n        x = score([1, 2])\n        x.append(3)\n        return {}",
 "isinstance": "from svsim.core.actions import Evolve\nclass T(PlayerStrategy):\n    def veto(self, state, action):\n        return isinstance(action, Evolve) and type(action).__name__ == 'Evolve'",
 "own-private": "class T(PlayerStrategy):\n    def __init__(self, seed=0):\n        super().__init__(seed)\n        self._n = 0\n    def search(self, pos):\n        self._n += 1\n        return {'iterations': 100 + self._n % 2}",
 "helper-class": "class Book:\n    def __init__(self):\n        self.rows = {}\n    def add(self, k, v):\n        self.rows[k] = v\nclass T(PlayerStrategy):\n    def __init__(self, seed=0):\n        super().__init__(seed)\n        self.book = Book()\n    def search(self, pos):\n        self.book.add(pos.turn, 1)\n        return {}",
 "nested-func": "class T(PlayerStrategy):\n    def prior(self, state, actions):\n        def val(a):\n            return len(repr(a))\n        vals = [val(a) for a in actions]\n        s = sum(vals)\n        return [v / s for v in vals]",
 "np": "import numpy as np\nclass T(PlayerStrategy):\n    def prior(self, state, actions):\n        p = np.ones(len(actions))\n        p[0] += 1\n        p /= p.sum()\n        return list(p)",
 "classmethod": "class T(PlayerStrategy):\n    TABLE = {}\n    @classmethod\n    def make(cls, seed):\n        return cls(seed)\n    @staticmethod\n    def norm(xs):\n        s = sum(xs)\n        return [x / s for x in xs]\n    def prior(self, state, actions):\n        return T.norm([1.0] * len(actions))",
 "except-class": "class Oops(Exception):\n    pass\nclass T(PlayerStrategy):\n    def search(self, pos):\n        try:\n            raise Oops('x')\n        except Oops:\n            pass\n        return {}",
}


@pytest.mark.parametrize("name", sorted(BAD))
def test_refused(name):
    assert check_code(textwrap.dedent(BAD[name]) + TAIL, "S"), name


@pytest.mark.parametrize("name", sorted(GOOD) + sorted(GOOD_LD42) + sorted(GOOD_LD43) + [f"44:{k}" for k in GOOD_LD44]
                         + sorted(GOOD_LD45) + sorted(GOOD_LD46) + sorted(GOOD_LD47))
def test_accepted(name):
    src = textwrap.dedent(GOOD_LD44[name[3:]] if name.startswith("44:") else GOOD_LD45.get(name) or
                          GOOD_LD46.get(name) or GOOD_LD47.get(name) or GOOD.get(name) or GOOD_LD42.get(name) or
                          GOOD_LD43[name])
    if "class T(" in src:
        future, _, rest = src.partition("\n") if src.startswith("from __future__") else ("", "", src)
        src = (future + "\n" if future else "") + "from ladder.interface import PlayerStrategy\n" + rest
    assert check_code(src + TAIL, "S") == []


def test_a_method_named_like_host_code_says_so():
    # LD-42, LD-43: a method whose name the simulator or the ladder also uses on objects it is handed may be called by
    # them with their objects, so its parameters start as possibly shared; a refusal ends with a note naming every
    # such method (only those with parameters), and renaming them as it says gets the module accepted
    src = textwrap.dedent(GOOD_LD42["grid"]).replace("place", "put")
    got = check_code("from ladder.interface import PlayerStrategy\n" + src + TAIL, "S")
    notes = [g for g in got if g.startswith("提示：")]
    assert notes and "Grid.put → my_put" in notes[0]
    assert check_code("from ladder.interface import PlayerStrategy\n" + src.replace("put(", "my_put(") + TAIL, "S") == []
    bag = ("class Item:\n    def __init__(self, w):\n        self.w = w\n"
           "class Bag:\n    def __init__(self):\n        self.items = []\n    def add(self, it):\n        self.items.append(it)\n"
           "    def normalize(self):\n        total = sum(i.w for i in self.items)\n        for i in self.items:\n"
           "            i.w = i.w / total\n            i.w += 1\n"
           "b = Bag()\nb.add(Item(1.0))\nb.normalize()\n")
    got = check_code(bag + TAIL, "S")
    notes = [g for g in got if g.startswith("提示：")]
    assert any("Bag.add" in n and "Bag.normalize" not in n.split(" ")[0] for n in notes), got
    assert len([g for g in got if not g.startswith("提示：")]) == 2          # the attribute and the += refusal
    assert check_code(bag.replace("add(", "my_add(") + TAIL, "S") == []


def test_the_note_names_free_names_and_storage_classes():
    # LD-44: the suggested name is one host code doesn't use either (my_hp, my_hand are svsim.learn's), and a class built
    # on a storage type is named with the way out (a dataclass)
    src = ("from typing import NamedTuple\nclass E(NamedTuple):\n    u: int\nclass G:\n    def __init__(self):\n"
           "        self.cells = [[0] * 3 for _ in range(3)]\n    def hp(self, r, v):\n        self.cells[r][0] = v\n"
           "G().hp(1, E(1).u)\n")
    got = check_code(src + TAIL, "S")
    notes = [g for g in got if g.startswith("提示：")]
    assert any("G.hp → mine_hp" in n for n in notes) and any(n.startswith("提示：E 建在") for n in notes), got
    fixed = src.replace("hp(", "mine_hp(").replace("class E(NamedTuple):\n    u: int",
                                                    "@dataclasses.dataclass\nclass E:\n    u: int")
    assert check_code("import dataclasses\n" + fixed + TAIL, "S") == []


def test_replace_with_a_dict_built_elsewhere_is_noted():
    # LD-45: replace(x, **d) with d not written out raises every dataclass field of the module; the note says which
    # line and how to write it, and written out it is accepted
    src = ("import dataclasses\n@dataclasses.dataclass\nclass Node:\n    v: int = 0\n"
           "    children: list = dataclasses.field(default_factory=list)\n@dataclasses.dataclass(frozen=True)\n"
           "class Knobs:\n    iterations: int = 80\nclass T(PlayerStrategy):\n    def search(self, pos):\n"
           "        late = {'iterations': 80 + pos.turn} if pos.turn > 10 else {}\n"
           "        k = dataclasses.replace(Knobs(), **late)\n        root = Node(-1)\n"
           "        root.children.append(Node(0))\n        return {'iterations': k.iterations}\n")
    head = "from ladder.interface import PlayerStrategy\n"
    got = check_code(head + src + TAIL, "S")
    assert any(g.startswith("提示：第 13 行的 **字典") for g in got), got
    fixed = src.replace("**late", "**({'iterations': 80 + pos.turn} if pos.turn > 10 else {})")
    assert check_code(head + fixed + TAIL, "S") == []


def test_a_dataclass_built_by_position_in_an_unclear_order_is_noted():
    # LD-46: when the reader can't tell which field a positional argument sets (here a ClassVar written through a
    # module-level alias), every field takes the highest argument's level; the receipt names the lines and says to
    # pass by name, which is then accepted. A ClassVar written plainly is read exactly (GOOD_LD46)
    src = ("import dataclasses\nimport typing\nCV = typing.ClassVar\n@dataclasses.dataclass\nclass Node:\n"
           "    state: object\n    children: list = dataclasses.field(default_factory=list)\n    C: CV[float] = 1.4\n"
           "class T(PlayerStrategy):\n    def search(self, pos):\n        root = Node(pos.state)\n"
           "        root.children.append(Node(pos.state))\n        return {}\n")
    head = "from ladder.interface import PlayerStrategy\n"
    out = check_code(head + src + TAIL, "S")
    assert any(x.startswith("提示：第 12、13 行按位置") for x in out), out
    fixed = src.replace("Node(pos.state)", "Node(state=pos.state)")
    assert check_code(head + fixed + TAIL, "S") == []


def test_ordinary_names_from_strings_alone_are_not_method_names():
    # LD-43: only attribute names, getattr-style written-out names and the strings of modules that read attributes
    # by a computed name count; not argparse choices, dict keys or this reader's own word lists
    from ladder.codecheck import base_self_names, duck_names
    from ladder.interface import PlayerStrategy
    d = duck_names()
    assert {"select", "store", "normalize", "merge", "node"}.isdisjoint(d)
    assert {"update", "add", "put", "get", "act", "guess"} <= d
    assert {"prior", "veto", "evaluate", "guess"} <= base_self_names(PlayerStrategy)


def test_own_classes_in_annotations_need_lazy_annotations():
    # LD-42: an evaluated annotation hands the class out (dataclasses.fields(...).type); a lazy one is a string
    src = "class Node:\n    def __init__(self, parent: Node | None):\n        self.parent = parent\n    def up(self) -> Node:\n        return self.parent"
    assert any("from __future__ import annotations" in p for p in check_code(src + TAIL, "S"))
    assert check_code("from __future__ import annotations\n" + src + TAIL, "S") == []


def test_long_chains_and_deep_nesting_are_read_or_refused_quickly():
    # LD-42: the reading goes on until nothing changes (a 201-function chain written callers first was cut at 200
    # rounds), each expression's level is worked out once per round (nested .get defaults took 2^n), and a too-deep
    # expression is refused, not a crash
    import time
    n = 260
    lines = ["from svsim.core.script import INVOKERS"]
    lines += [f"def f{i}():\n    return f{i + 1}()" for i in range(1, n)] + [f"def f{n}():\n    return INVOKERS", "f1().add(7)"]
    assert check_code("\n".join(lines) + TAIL, "S")
    e = "0"
    for i in range(60):
        e = f"d.get({i}, {e})"
    t = time.perf_counter()
    assert check_code(f"d = {{}}\nx = {e}" + TAIL, "S") == []
    assert time.perf_counter() - t < 5
    assert check_code("x = 1\ny = x" + ".a" * 700 + TAIL, "S") == ["读不了：嵌套太深"]


def test_the_documented_skeleton_is_accepted():
    doc = (HERE.parent / "public" / "base-interface.md").read_text(encoding="utf-8")
    src = doc.split("```python")[1].split("```")[0]
    assert check_code(src, "MyStrategy") == []
