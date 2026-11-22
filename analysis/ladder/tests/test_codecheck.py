"""The code reader's flow rules (LD-41, the sixth review; LD-42, the seventh): shared objects from svsim / ladder may
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


@pytest.mark.parametrize("name", sorted(GOOD) + sorted(GOOD_LD42))
def test_accepted(name):
    src = textwrap.dedent(GOOD.get(name) or GOOD_LD42[name])
    if "class T(" in src:
        src = "from ladder.interface import PlayerStrategy\n" + src
    assert check_code(src + TAIL, "S") == []


def test_a_method_named_like_host_code_says_so():
    # LD-42: a method whose name the simulator or the ladder also uses may be called by them with their objects, so
    # its parameters start as possibly shared; the refusal says to rename it
    src = textwrap.dedent(GOOD_LD42["grid"]).replace("place", "put")
    got = check_code("from ladder.interface import PlayerStrategy\n" + src + TAIL, "S")
    assert got and "方法名 put" in got[0]


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
