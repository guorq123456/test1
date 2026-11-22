"""The code reader's flow rules (LD-41, the sixth review): shared objects from svsim / ladder may not be changed,
through any alias, argument, return value, attribute or container; and the plain strategy code stays accepted."""
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


@pytest.mark.parametrize("name", sorted(GOOD))
def test_accepted(name):
    src = textwrap.dedent(GOOD[name])
    if "class T(" in src:
        src = "from ladder.interface import PlayerStrategy\n" + src
    assert check_code(src + TAIL, "S") == []


def test_the_documented_skeleton_is_accepted():
    doc = (HERE.parent / "public" / "base-interface.md").read_text(encoding="utf-8")
    src = doc.split("```python")[1].split("```")[0]
    assert check_code(src, "MyStrategy") == []
