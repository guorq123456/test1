"""Submissions (phase 2, item 2.3): the entry point and its checks. Seeds 99001410-99001469 (host probe bank,
SEEDS.md): 99001410-99001419 the peek-check games, 99001420-99001449 the smoke and load-check games of `receive`.
The turn-start budget's tests (A68, 11-28): 96520000-96539999 (host probe third segment, SEEDS.md): 96520100-96520129
the planner's smoke and load-check games, 96520200-96520229 the remembering stand-in's, 96520300-96520309 the extended
peek check's games."""
import json
import random
import sys
import textwrap
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
from ladder import submit  # noqa: E402
from ladder.pool import Pool  # noqa: E402
from ladder.runner import play_job  # noqa: E402

ROOT = HERE.parents[2]
TOOLS = HERE.parent / "tools"
LINES = [l.strip().split("|") for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(encoding="utf-8")
         .splitlines() if l.strip() and not l.startswith("#")]
CODES = [c for _, c in LINES]
SMOKE = (99001420, 99001450)
PLAN_SMOKE = (96520100, 96520130)               # the turn-start budget's (A68): the planner's receipts
MEMORY_SMOKE = (96520200, 96520230)             # the remembering stand-in's receipt
TURN_PEEK = (96520300, 96520310)                # the extended peek check's games

PLANS = '''
from ladder.interface import PlayerStrategy, action_key, sample_states
from svsim.search.mcts import ISMCTS


class Plans(PlayerStrategy):
    """Cheap within the turn (8 iterations, the exact lethal search); at each own turn's start 16 searches of the
    default's size on states sampled with self.random, the picks kept on self (a planner's cost, its plan unused)."""
    LETHAL = "exact"

    def __init__(self, seed=0):
        super().__init__(seed)
        self.planner = ISMCTS(iterations=100, seed=self.random.getrandbits(31))
        self.picked = (None, [])

    def search(self, pos):
        return {"iterations": 8}

    def turn_start(self, pos):
        picks = []
        for s in sample_states(pos, self.guess(pos), self.random, 16):
            picks.append(action_key(s, self.planner.choose(s)))
        self.picked = (pos.state.turn, picks)
'''

REMEMBERS = '''
from ladder.interface import PlayerStrategy

_BOOK = {}


class Remembers(PlayerStrategy):
    """Counts in a module-level book how often it started its n-th own turn in this process; its search follows the
    count (tools/standins.py Memory): a worker's later games choose otherwise than a fresh process replaying them."""
    LETHAL = "exact"

    def __init__(self, seed=0):
        super().__init__(seed)
        self.extra = 0

    def turn_start(self, pos):
        n = pos.state.players[pos.me].turns_taken
        _BOOK[n] = _BOOK.get(n, 0) + 1
        self.extra = _BOOK[n] % 3

    def search(self, pos):
        return {"iterations": 4 + self.extra}
'''

QUICK = '''
from ladder import base
from ladder.interface import PlayerStrategy


class Quick(PlayerStrategy):
    """Cheap for the tests: 8 iterations a decision, the exact lethal search only."""
    LETHAL = "exact"

    def search(self, pos):
        return {"iterations": 8}

    def guess(self, pos):
        return base.default_guess(pos.opp_craft)
'''

PEEKY = '''
import sys
from ladder.interface import PlayerStrategy
from svsim.core.state import GameState


class Peeky(PlayerStrategy):
    """Reads the referee's real state off the call stack (what the peek check must catch)."""
    LETHAL = "exact"

    def search(self, pos):
        return {"iterations": 4}

    def act(self, pos, actions):
        f = sys._getframe(1)
        while f is not None:
            s = f.f_locals.get("state")
            if isinstance(s, GameState) and s is not pos.state:
                opp = s.players[1 - pos.me]
                h = sum(c.defn.card_id for c in opp.hand) + sum(c.defn.card_id for c in opp.deck_view()[-3:])
                return actions[h % len(actions)]
            f = f.f_back
        return super().act(pos, actions)
'''


def make_sub(d: Path, kind: str, src: str = QUICK, cls: str = "Quick", **meta) -> Path:
    d.mkdir(parents=True)
    (d / "submission.json").write_text(json.dumps({"type": kind, "member": meta.pop("member", "一号"),
                                                   "class": cls, **meta}, ensure_ascii=False), encoding="utf-8")
    (d / "strategy.py").write_text(textwrap.dedent(src), encoding="utf-8")
    (d / "notes.md").write_text("1. 靠场面赢。\n2. ...\n3. ...\n4. ...\n5. ...\n6. 预测：中游。\n", encoding="utf-8")
    (d / "evidence.md").write_text("练习场：对 7 个基线各 100 局。\n", encoding="utf-8")
    return d


# --- reading the code -----------------------------------------------------------------------------------------

def test_the_interface_skeleton_reads_clean():
    skeleton = '''
from ladder import base
from ladder.interface import PlayerStrategy, action_key, sample_states, to_next_turn
from svsim.agents.greedy_agent import mulligan as bot_mulligan
from svsim.search.evaluate import DEFAULT, evaluate
import math, random, collections
import numpy as np


class MyStrategy(PlayerStrategy):
    LETHAL = "planner"

    def __init__(self, seed=0):
        super().__init__(seed)
        self.table = collections.Counter()
        self.gen = random.Random(seed)
        self.kept = (None, [])

    def guess(self, pos):
        return base.default_guess(pos.opp_craft)

    def turn_start(self, pos):
        states = sample_states(pos, self.guess(pos), self.random, 2)
        end, info = to_next_turn(pos, self.guess(pos), random.Random(self.random.getrandbits(31)))
        if info["stopped"] == "over" or not states:
            self.table[pos.state.turn] += 1
        self.kept = (pos.state.turn, [])

    def mulligan(self, state):
        return bot_mulligan(state)

    def evaluate(self, state, me, me_next):
        x = getattr(state, "turn", 0)
        return evaluate(state, me, DEFAULT, player_moves_next=me_next) + 0.0 * math.sqrt(x) + float(np.zeros(1)[0])

    def veto(self, state, action):
        if self.kept[0] == state.turn and action_key(state, action) in self.kept[1]:
            return False
        return type(action).__name__ == "Evolve" and self.random.random() < 0.0

    def search(self, pos):
        return {"iterations": 100, "c": 0.5, "scale": 8.0}
'''
    assert submit.check_code(skeleton, "MyStrategy") == []


@pytest.mark.parametrize("line,what", [
    ("import os", "import os"),
    ("import sys", "import sys"),
    ("from ladder import runner", "只能用"),
    ("from ladder.runner import make_strategy", "ladder.runner"),
    ("import svsim.tools.arena", "svsim.tools"),
    ("from svsim import learn", "A12"),
    ("from svsim.tools.arena import make_agent", "svsim.tools"),
    ("from . import helpers", "相对 import"),
    ("x = open('a.txt').read()", "open"),
    ("x = eval('1')", "eval"),
    ("x = ().__class__", "__class__"),
    ("from ladder import base\nx = base.Path('a').read_text()", ".Path"),
    ("import random\nx = random.random()", "self.random"),
    ("from random import shuffle", "self.random"),
    ("try:\n    1/0\nexcept Exception as e:\n    f = e.__traceback__.tb_frame.f_back", "__traceback__"),
    ("x = getattr(object, name)", "写死"),
    ("x = getattr(object, '__subclasses__')", "__subclasses__"),
    ("g = getattr", "直接调用"),
    ("import importlib", "importlib"),
    ("import numpy as np\nnp.load('x.npy')", "numpy.load"),    # LD-46: numpy's file functions read any file
    # fifth pass (LD-40): rewriting shared objects in place, other objects' private parts, the ladder package's other
    # modules, assigning into imported modules, defining dunder methods
    ("def f(pos):\n    for c in pos.state.players[0].hand:\n        c.defn.__init__(1, 'x', 0, 0, 0)", "super().__init__"),
    ("def f(a):\n    a.__init__(10 ** 6, 0)", "super().__init__"),
    ("x = getattr(object, '__init__')", "__init__"),
    ("import collections\nx = collections._sys", "._sys"),
    ("import ladder.base\nx = ladder.runner", "ladder.runner"),
    ("from svsim.cards import pool\npool.POOL[10001] = None", "pool"),
    ("from svsim.core.actions import Attack\nAttack.__eq__ = None", "__eq__"),
    ("from svsim.search import evaluate\nevaluate.DEFAULT = None", "evaluate"),
    ("from svsim.search import evaluate\nsetattr(evaluate, 'DEFAULT', None)", "evaluate"),
    ("class H:\n    def __eq__(self, other):\n        return True", "def __eq__"),
    ("class H:\n    def __init__(self):\n        super().__init__()\n        self._n = 0\n    def __post_init__(self):\n        self._n += 1", None),
])
def test_the_code_check_refuses(line, what):
    src = line + "\nfrom ladder.interface import PlayerStrategy\n\nclass S(PlayerStrategy):\n    pass\n"
    problems = submit.check_code(src, "S")
    if what is None:
        assert problems == []
    else:
        assert problems and any(what in p for p in problems), problems


def test_the_class_must_be_there():
    assert any("没有类" in p for p in submit.check_code("x = 1\n", "S"))
    assert any("语法错误" in p for p in submit.check_code("def (:\n", "S"))


# --- the directory, the deck, the slots ---------------------------------------------------------------------------

def test_format_problems_are_all_listed(tmp_path):
    d = tmp_path / "s"
    d.mkdir()
    with pytest.raises(submit.Refused) as e:
        submit.read_dir(d)
    assert len(e.value.args[0]) == 4
    make_sub(tmp_path / "u", "打法更新", route={"steps": 3, "step": 1})
    with pytest.raises(submit.Refused) as e:
        submit.read_dir(tmp_path / "u")
    msgs = " ".join(e.value.args[0])
    assert "change" in msgs and "prediction" in msgs and "stop_if" in msgs


def test_decks_by_the_simulators_rules():
    ids, problems = submit.check_deck(CODES[0])
    assert len(ids) == 40 and problems == []
    from svsim.cards.decks import to_hash
    from ladder.runner import load_deck
    deck = load_deck(CODES[0])
    _, problems = submit.check_deck(to_hash(deck + deck[:1]))
    assert any("41" in p for p in problems)
    _, problems = submit.check_deck("not a deck code")
    assert problems


def test_a_derived_form_is_not_a_deck_card():
    """LD-68 (astra, period 1): the Accelerate form of Jailor of Antiquity (10901112, 1 cost) passed the simulator's
    validate; it is not in the card pool (rotation.json: no rot flag), so the deck check refuses it."""
    from svsim.cards.decks import to_hash
    from svsim.cards.pool import card
    from ladder.runner import load_deck
    deck = load_deck(CODES[2])
    real = [card(10901110)] * 3 + deck[3:]
    derived = [card(10901112)] * 3 + deck[3:]
    assert not any("不是能放进卡组的牌" in p for p in submit.check_deck(to_hash(real))[1])
    _, problems = submit.check_deck(to_hash(derived))
    assert any("不是能放进卡组的牌" in p and "10901112" in p for p in problems)
    for code in CODES:                                   # the seven baseline lists: nothing new refused
        assert not any("不是能放进卡组的牌" in p for p in submit.check_deck(code)[1])


def _pool(tmp_path, period: int):
    pool = Pool.create(tmp_path / "pool", seeds=(99001460, 99001470), rng_seed=1)
    while pool.period < period:                            # 1: a deck period; 4: special; 5 on: merged (S35/S36)
        pool.advance(force="test")
    return pool


def test_slots_and_periods(tmp_path):
    """S5 (Salem 11-22): one new deck per class per deck period (a refused one leaves the class open, A35);
    updates not limited."""
    pool = _pool(tmp_path, 1)
    ids, _ = submit.check_deck(CODES[1])                                  # Sword
    sub = {"kind": "deck", "meta": {"member": "二号"}, "deck_ids": ids}
    r = lambda i, kind, **k: {"ev": "receipt", "id": f"S-{i:04d}", "player": "fable-ultracode", "period": pool.period,
                              "kind": kind, **k}
    problems, info = submit.check_slots(sub, "fable-ultracode", pool, [r(1, "deck", verdict="拒收", craft=2)])
    assert problems == [] and info["uses_slot"] and info["craft"] == 2   # the refused one left Sword open
    problems, _ = submit.check_slots(sub, "fable-ultracode", pool, [r(1, "deck", verdict="收下", craft=2)])
    assert any("已经交过一副" in p for p in problems)
    problems, _ = submit.check_slots(sub, "fable-ultracode", pool, [r(i, "deck", verdict="收下", craft=c)
                                                       for i, c in enumerate((1, 3, 4, 5, 6, 7))])
    assert problems == []                                                # six other classes don't block Sword
    problems, _ = submit.check_slots(sub, "fable", pool, [r(1, "deck", verdict="收下", craft=2)])
    assert problems == []                                                # another player's classes are theirs
    mid = pool.enter(ids, "bot:mcts:100+plan", "fable-ultracode")
    pool.advance(force="test: straight to a strategy period")
    admitted = [{"ev": "admit", "player": "fable-ultracode", "member": "二号", "mid": mid}]
    problems, _ = submit.check_slots(sub, "fable-ultracode", pool, admitted)
    assert any("卡组期" in p for p in problems)
    up = {"kind": "update", "meta": {"member": "二号"}}
    many = admitted + [r(i, "update", verdict="拒收", member="二号") for i in range(1, 21)]
    problems, info = submit.check_slots(up, "fable-ultracode", pool, many)
    assert problems == [] and info["mid"] == mid and up["deck_ids"] == ids   # updates are not limited
    routed = admitted + [r(1, "update", member="二号", route={"steps": 2, "step": 1})]
    later = {"kind": "update", "meta": {"member": "二号", "route": {"steps": 2, "step": 2, "route_of": "S-0001"}}}
    problems, _ = submit.check_slots(later, "fable-ultracode", pool, routed)
    assert problems == []
    wrong = {"kind": "update", "meta": {"member": "二号", "route": {"steps": 3, "step": 2, "route_of": "S-0001"}}}
    problems, _ = submit.check_slots(wrong, "fable-ultracode", pool, routed)
    assert any("总步数" in p for p in problems)
    problems, _ = submit.check_slots({"kind": "update", "meta": {"member": "三号"}}, "fable-ultracode", pool, admitted)
    assert any("没有叫" in p for p in problems)


def test_slots_in_a_merged_period(tmp_path):
    """S35/S36: in a merged period (from period 5; period 4 is special, Salem 11-27) new decks (optional, at most one
    per class) and updates in the same period; an update for a member entered in this period is refused at receipt
    (it isn't in the period-start frozen pool)."""
    pool = _pool(tmp_path, 1)
    sword, _ = submit.check_deck(CODES[1])
    forest, _ = submit.check_deck(CODES[0])
    old = pool.enter(sword, "bot:mcts:100+plan", "fable-ultracode")
    up = lambda name: {"kind": "update", "meta": {"member": name}}
    admitted = [{"ev": "admit", "player": "fable-ultracode", "member": "二号", "mid": old}]
    problems, _ = submit.check_slots(up("二号"), "fable-ultracode", pool, admitted)
    assert any("只有策略期、合并期收打法更新" in p for p in problems)          # period 1: decks only
    pool.advance(force="test"); pool.advance(force="test")                    # period 3 (special): decks only
    problems, _ = submit.check_slots(up("二号"), "fable-ultracode", pool, admitted)
    assert any("卡组期" in p for p in problems)
    pool.advance(force="test")                                                # period 4: special, no updates
    problems, info = submit.check_slots(up("二号"), "fable-ultracode", pool, admitted)
    assert problems == ["第 4 期是特殊期，不收老成员改打法，第 5 期起合并期，那时再交（special-P4.md）"]
    assert "mid" not in info
    pool.advance(force="test")                                                # period 5: merged
    r = lambda i, kind, **k: {"ev": "receipt", "id": f"S-{i:04d}", "player": "fable-ultracode", "period": pool.period,
                              "kind": kind, **k}
    deck = {"kind": "deck", "meta": {"member": "一号"}, "deck_ids": forest}
    problems, info = submit.check_slots(deck, "fable-ultracode", pool, admitted)
    assert problems == [] and info["uses_slot"] and info["craft"] == 1 and info["period_kind"] == "merged"
    problems, _ = submit.check_slots(deck, "fable-ultracode", pool, admitted + [r(1, "deck", verdict="收下", craft=1)])
    assert any("已经交过一副" in p and "每期每个职业最多一副" in p for p in problems)
    problems, info = submit.check_slots(up("二号"), "fable-ultracode", pool, admitted)
    assert problems == [] and info["mid"] == old                               # an update, the same period
    same = {"kind": "deck", "meta": {"member": "二号乙"}, "deck_ids": sword}  # a list the player already holds
    problems, info = submit.check_slots(same, "fable-ultracode", pool, admitted)
    assert problems == [] and any("新成员" in w for w in info["warnings"])
    same_taken = {"kind": "deck", "meta": {"member": "二号"}, "deck_ids": sword}   # refused (name used): no reminder
    problems, info = submit.check_slots(same_taken, "fable-ultracode", pool, admitted)
    assert any("你已经用过了" in p for p in problems) and info["warnings"] == []
    # the deck accepted, its admit still to come; then admitted: no update of it this period, either way
    pending = admitted + [r(2, "deck", verdict="收下", craft=1, member="一号")]
    problems, _ = submit.check_slots(up("一号"), "fable-ultracode", pool, pending)
    assert any("是这一期才交的新卡组，这一期不能改打法；它入池了的话，下一期起可以" in p for p in problems)
    new = pool.enter(forest, "bot:mcts:100+plan", "fable-ultracode")
    now = pending + [{"ev": "admit", "player": "fable-ultracode", "member": "一号", "mid": new}]
    problems, _ = submit.check_slots(up("一号"), "fable-ultracode", pool, now)
    assert any("这个成员是这一期才入池的，这一期不能改打法，下一期起可以" in p for p in problems)
    pool.advance(force="test")                                                # period 6: from now on it can
    problems, info = submit.check_slots(up("一号"), "fable-ultracode", pool, now)
    assert problems == [] and info["mid"] == new


def test_a_deck_on_the_players_own_list_refused_later_gets_no_same_list_note(tmp_path):
    # A66 ⑤: the note says what an accepted deck would be; a deck refused by a later check (here the code reader,
    # before any game) does not get it, and the receipt is written without it (period 5: merged)
    pool = _pool(tmp_path, 5)
    sword, _ = submit.check_deck(CODES[1])
    pool.enter(sword, "bot:mcts:100+plan", "fable-ultracode")
    bad = "import importlib\n" + QUICK
    d = make_sub(tmp_path / "in", "新卡组", src=bad, deck=CODES[1], member="二号乙")
    rec = submit.receive(d, "fable-ultracode", pool.dir, tmp_path / "subs", workers=2, rng_seed=7, smoke_games=2,
                         seeds=SMOKE)
    assert rec["verdict"] == "拒收" and any(r.startswith("[代码（读）]") for r in rec["reasons"]), rec["reasons"]
    assert submit.SAME_LIST_NOTE not in rec["warnings"]
    assert "同一张卡表" not in (tmp_path / "subs" / rec["id"] / "receipt.md").read_text(encoding="utf-8")
    assert not [c for c in rec["checks"] if c["check"] in ("载入（隔离进程）", "冒烟")]   # no game was played


def test_status_in_a_merged_period(tmp_path):
    # S36: new decks optional in a merged period (from period 5): the status shows what can still come, nothing
    # "missing"
    pool = _pool(tmp_path, 5)
    subs = tmp_path / "subs"
    for i, (craft, verdict) in enumerate(((1, "收下"), (2, "拒收"))):
        submit._append(subs, {"ev": "receipt", "id": f"S-{i + 1:04d}", "player": "fable", "period": 5, "kind": "deck",
                              "verdict": verdict, "craft": craft})
    submit._append(subs, {"ev": "receipt", "id": "S-0003", "player": "fable", "period": 5, "kind": "update",
                          "verdict": "收下"})
    st = submit.status(subs, pool.dir, "fable")
    assert st["kind"] == "merged" and st["classes_done"] == ["精灵"] and len(st["classes_open"]) == 6
    assert "classes_missing" not in st and st["updates_accepted"] == 1
    text = submit.status_text(st, submit.ledger(subs))
    assert text.startswith("# 第 5 期（合并期）你的提交")
    assert "已经收下的职业：精灵" in text and "还能交（可交可不交，每个职业最多一副）：皇家护卫" in text
    assert "还缺" not in text and "收下（进检验）1 份" in text


# --- the load check (its own process) ------------------------------------------------------------------------------

def test_the_load_check_plays_and_blocks(tmp_path):
    ids, _ = submit.check_deck(CODES[2])
    ok = tmp_path / "ok.py"
    ok.write_text(QUICK, encoding="utf-8")
    r = submit.load_check(ok, "Quick", ids, 1, seed=3, game_seed=99001449, work=tmp_path / "w1")
    assert r["ok"], r
    cpu = r["cpu"]                                        # A68: import and construction measured, reported only
    assert cpu["unit"] in ("ns", "cycles") and all(isinstance(cpu[k], int) and cpu[k] >= 0
                                                    for k in ("import", "construct", "default_construct")), cpu
    bad = tmp_path / "bad.py"
    bad.write_text(QUICK + "\nDATA = open(r'%s').read()\n" % str(ROOT / "analysis/ladder/SEEDS.md"),
                   encoding="utf-8")
    r = submit.load_check(bad, "Quick", ids, 1, seed=3, game_seed=99001449, work=tmp_path / "w2")
    assert not r["ok"] and any("SEEDS.md" in b for b in r["blocked"]), r
    sneaky = tmp_path / "sneaky.py"                       # swallows the refusal: still caught
    sneaky.write_text(QUICK + "\ntry:\n    import socket\n    socket.socket().connect(('127.0.0.1', 9))\n"
                      "except Exception:\n    pass\n", encoding="utf-8")
    r = submit.load_check(sneaky, "Quick", ids, 1, seed=3, game_seed=99001449, work=tmp_path / "w3")
    assert not r["ok"] and r["blocked"], r
    lazy = tmp_path / "lazy.py"                           # LD-47: a dataclass with string annotations loads
    lazy.write_text("from __future__ import annotations\nimport dataclasses\nimport typing\n" + QUICK +
                    "\n@dataclasses.dataclass\nclass Node:\n    parent: Node | None = None\n    mark: 'Node' = None\n"
                    "    C: typing.ClassVar[float] = 1.4\n\nROOT = Node()\n", encoding="utf-8")
    r = submit.load_check(lazy, "Quick", ids, 1, seed=3, game_seed=99001449, work=tmp_path / "w4")
    assert r["ok"], r
    missing = tmp_path / "missing.py"                     # LD-47: the error, not '<unknown>' (3.13's traceback)
    missing.write_text(QUICK + "\nimport numpy.emath\n", encoding="utf-8")
    r = submit.load_check(missing, "Quick", ids, 1, seed=3, game_seed=99001449, work=tmp_path / "w5")
    assert not r["ok"] and r["blocked"] == [] and "ModuleNotFoundError" in r.get("error", ""), r


# --- the peek check ---------------------------------------------------------------------------------------------

def _log(tmp_path, name, src, cls, seed):
    mod = tmp_path / "mods"
    mod.mkdir(exist_ok=True)
    (mod / f"{name}.py").write_text(src, encoding="utf-8")
    if str(mod) not in sys.path:
        sys.path.insert(0, str(mod))
    job = {"id": f"peek-{name}", "seed": seed, "first": None, "decks": [CODES[3], CODES[5]],
           "strategies": [f"py:{name}:{cls}", "bot:mcts:100+plan"], "strategy_seeds": [11, 12]}
    return json.loads(json.dumps(play_job(job)))


def test_the_peek_check(tmp_path):
    honest = _log(tmp_path, "honest_q", QUICK, "Quick", 99001410)
    assert honest["result"] == "normal"
    n = sum(1 for s, _, _ in honest["steps"] if s == 0)
    rng = random.Random(1)
    got = [submit.peek_check(honest, 0, k, random.Random(rng.randrange(2 ** 32))) for k in (0, 1, n // 2, n - 1)]
    assert all(g == "same" for g in got), got
    peeky = _log(tmp_path, "peeky_q", PEEKY, "Peeky", 99001411)
    n = sum(1 for s, _, _ in peeky["steps"] if s == 0)
    got = [submit.peek_check(peeky, 0, k, random.Random(rng.randrange(2 ** 32))) for k in range(0, n, max(1, n // 8))]
    assert "differs" in got, got


def test_shadow_rows_divide_by_the_twins_game_over_shadow():
    """LD-56: the submission's CPU over the default's on its own positions, over (twin game / twin shadow)."""
    g = {"id": "x-sub", "steps": [[0, 10, 0], [1, 5, 0], [0, 30, 0]]}
    ref = {"id": "x-default", "steps": [[0, 8, 0], [1, 4, 0]]}
    got = [{"value": {"steps": [[0, 20], [1, 1], [0, 20]]}}, {"value": {"steps": [[0, 6], [1, 2]]}}]
    rows, bad = submit.shadow_rows([(g, ref, 0)], got)
    assert rows == [(40, 40, 12, 8)] and bad == []
    assert abs(submit.pooled_ratio(rows) - 1 / 1.5) < 1e-9
    rows, bad = submit.shadow_rows([(g, ref, 0)], [got[0], None])                  # a shadow died
    assert rows == [] and len(bad) == 1
    rows, bad = submit.shadow_rows([(g, ref, 0)], [{"value": {"steps": [[0, 20]]}}, got[1]])   # not the same game
    assert rows == [] and "decisions 2 / 1" in bad[0]
    rows, bad = submit.shadow_rows([(g, ref, 0)], [got[0], {"value": {"steps": []}, "changed": ["x"]}])
    assert rows == [] and len(bad) == 1
    assert submit.pooled_ratio([]) is None
    assert [t["strategy_seeds"] for t in submit.shadow_tasks([({"id": "a", "seed": 1, "decks": [], "actions": [],
                                                                 "strategy_seeds": [3, 4]},
                                                                {"id": "b", "seed": 1, "decks": [], "actions": [],
                                                                 "strategy_seeds": [3, 4]}, 1)])] == [[3, 4], [3, 4]]


def test_a_shadow_asks_the_default_at_every_logged_decision(tmp_path):
    log = _log(tmp_path, "shadowed_q", QUICK, "Quick", 99001412)
    assert log["result"] == "normal"
    out = submit._shadow(submit.shadow_task(log, 0))
    assert [s for s, _ in out["steps"]] == [s for s, _, _ in log["steps"]]
    assert out["cpu_unit"] == log["cpu_unit"] and all(c >= 0 for _, c in out["steps"])
    rows, bad = submit.shadow_rows([(log, log, 0)], [{"value": out}, {"value": out}])
    assert len(rows) == 1 and not bad
    # A68: the engine's kinds (the shadow's) are the moves' (turn_kinds): two mulligans, then one turn start per turn
    kinds = submit.turn_kinds(log["actions"], len(log["steps"]))
    assert out["kinds"] == kinds and kinds[:2] == ["M", "M"] and kinds[2] == "F"
    firsts = [s for (s, _, _), k in zip(log["steps"], kinds) if k == "F"]
    assert firsts == [firsts[0], 1 - firsts[0]] * (len(firsts) // 2) + [firsts[0]] * (len(firsts) % 2)   # by turns
    assert submit.checked_kinds(log, out) == kinds
    with pytest.raises(SystemExit, match="两种认法对不上"):          # the host's rule wrong: no receipt
        submit.checked_kinds(log, {**out, "kinds": ["M", "M", "R"] + kinds[3:]})
    parts, bad = submit.shadow_parts([(log, log, 0)], [{"value": out}, {"value": out}])
    p = parts[0]
    assert not bad and p["row"] == rows[0] and p["F"] + p["R"] == rows[0][0] and p["Fd"] + p["Rd"] == rows[0][1]
    assert p["T"] == kinds.count("F") - sum(1 for (s, _, _), k in zip(log["steps"], kinds) if k == "F" and s == 1)
    assert p["U"] == sum(t[2] for t in p["turns"]) and len(p["turns"]) == p["T"]


# --- compute by turns (A68, Salem 11-27): the log rule, the two rules, the extended peek check ---------------------

def _moves(*names):
    return [{"type": n} for n in names]


def test_turn_kinds_from_the_moves():
    # two mulligans; the first turn; the opponent's; a bonus-PP move is no new turn; the game's first decision
    acts = _moves("Mulligan", "Mulligan", "PlayCard", "Attack", "EndTurn", "EndTurn", "UseBonusPP", "PlayCard",
                  "EndTurn", "Attack")
    assert submit.turn_kinds(acts) == ["M", "M", "F", "R", "R", "F", "F", "R", "R", "F"]
    assert submit.turn_kinds(acts, len(acts)) == submit.turn_kinds(acts)
    # a game ended on an illegal move logged one step more than moves (runner.py): that step by the move before it,
    # a mulligan among the first two decisions
    assert submit.turn_kinds(acts[:4], 5) == ["M", "M", "F", "R", "R"]
    assert submit.turn_kinds(acts[:5], 6) == ["M", "M", "F", "R", "R", "F"]
    assert submit.turn_kinds(acts[:2], 3) == ["M", "M", "F"]
    assert submit.turn_kinds([], 1) == ["M"] and submit.turn_kinds(acts[:1], 2) == ["M", "M"]
    # a timeout or a void game logs no step for its last move: the rule is the normal one on what is there
    assert submit.turn_kinds(acts[:7], 7) == ["M", "M", "F", "R", "R", "F", "F"]
    assert submit.turn_kinds([], 0) == []


def _part(F, R, Fd, Rd, U, T=9, twin=(100, 100), opp=(50, 50), wall=200_000):
    """A pair split by turns, as shadow_parts gives it (CPU in any unit; T turns of equal cost)."""
    turns = [[F / T, Fd / T, U / T, wall] for _ in range(T)]
    return {"id": "x", "row": (F + R, Fd + Rd, twin[0], twin[1]), "F": F, "R": R, "Fd": Fd, "Rd": Rd, "U": U, "T": T,
            "turns": turns, "opp": list(opp), "twin_F": [twin[0] / 2, twin[1] / 2], "twin_R": [twin[0] / 2, twin[1] / 2],
            "U_twin": U, "T_twin": T}


def _verdict(parts, k):
    b = submit.turn_budget(parts, k)
    r3 = round(submit.pooled_ratio([p["row"] for p in parts]), 3)
    return (r3, b) + submit.compute_verdict(r3, b, len(parts), k)


DEFAULT_PAIR = dict(Fd=54, Rd=46, U=99)       # the default's own: 54% at the turn starts, a mulligan of 1


def test_two_rules_one_of_which_must_hold():
    """Salem 11-27: the turn starts get 1.08 x the default's there + K default turns, every other decision 1.08 as
    before; the old rule (all steps) still passes what it passed."""
    k = submit.TURN_K
    assert k > 0 and submit.TURN_REFUSE == 1.065
    planner = [_part(F=54 + 0.9 * k * 99, R=46, **DEFAULT_PAIR)] * 50           # within K: the turn rule
    r3, b, over, warned, rule = _verdict(planner, k)
    assert r3 > submit.COMPUTE_REFUSE and over == [] and rule == "turn" and warned == [], (r3, b)
    assert abs(b["in_turn"] - 1) < 1e-9 and b["turn_start_q"] < 1 and abs(b["extra_turns"] - (0.9 * k - 0.08 * 54 / 99)) < 1e-9
    assert b["per_turn"]["median"] == b["per_turn"]["max"] and b["u_twin_ratio"] == 1 and b["opp_seat"] == 1
    extra = 0.9 * k * 99                                                      # the same total, over every decision
    spread = [_part(F=54 + extra / 3.9, R=46 + extra * 2.9 / 3.9, **DEFAULT_PAIR)] * 50
    r3, b, over, _, rule = _verdict(spread, k)
    assert rule is None and len(over) == 2 and b["in_turn"] > 2, b
    assert "A52" in over[0] and "按回合给算力的那条规矩也没过" in over[1] and "回合里的每一步" in over[1]
    greedy = [_part(F=54 + 1.3 * k * 99, R=46, **DEFAULT_PAIR)] * 50          # past K
    r3, b, over, _, rule = _verdict(greedy, k)
    assert rule is None and b["turn_start_q"] > submit.TURN_REFUSE and f"给的是 {k} 个" in over[1]
    # LETHAL "off", more search within the turn, all steps within 1.08: passed as before, on the old rule
    off = [_part(F=20, R=46 * 1.6, **DEFAULT_PAIR)] * 50
    r3, b, over, warned, rule = _verdict(off, k)
    assert r3 <= submit.COMPUTE_CAP and b["in_turn"] > submit.COMPUTE_REFUSE and over == [] and rule == "old"
    assert warned == []
    # past the caps, within the allowance: a warning on the rule it passed on
    near = [_part(F=54 + 0.9 * k * 99, R=46 * 1.1, **DEFAULT_PAIR)] * 50
    _, _, over, warned, rule = _verdict(near, k)
    assert over == [] and rule == "turn" and len(warned) == 1 and "按回合给算力的那条收下" in warned[0]
    # within both: the old rule's name, no warning
    _, _, over, warned, rule = _verdict([_part(F=54, R=46, **DEFAULT_PAIR)] * 50, k)
    assert over == [] and warned == [] and rule == "old"
    # K = 0, the switch: the planner refused, by the old text alone
    r3, b, over, warned, rule = _verdict(planner, 0)
    assert rule is None and len(over) == 1 and over[0].startswith(f"每步算力是默认打法的 {r3:.3f} 倍") and warned == []


def _old_verdict(r3, pairs):
    """The compute check's decision before the turn rule (submit-3), as the code had it."""
    if r3 is not None and r3 > submit.COMPUTE_REFUSE:
        return [f"每步算力是默认打法的 {r3:.3f} 倍，超过 {submit.COMPUTE_REFUSE}：上限是 {submit.COMPUTE_CAP} 倍，量法有误差，"
                f"量出来超过 {submit.COMPUTE_REFUSE} 倍就拒收（所有成员一样，每一版都查，A52、S15）。这次量了 {pairs} 对；"
                "电脑上 50 对上下约 1%（LD-58）"], []
    warned = []
    if r3 is not None and r3 > submit.COMPUTE_CAP:
        warned.append(f"每步算力量出来是默认打法的 {r3:.3f} 倍，超过上限 {submit.COMPUTE_CAP}，还在容差 "
                      f"{submit.COMPUTE_REFUSE} 以内，收下；再往上就会被拒收（S15）")
    return [], warned


def test_k_zero_decides_exactly_as_before():
    """TURN_K = 0 is the switch back: the same refusals, texts and warnings as the old check, whatever the split;
    and at any K the turn rule never refuses what the old rule passes."""
    rng = random.Random(11)
    for _ in range(3000):
        parts = [_part(F=rng.uniform(1, 400), R=rng.uniform(1, 200), Fd=rng.uniform(20, 80), Rd=rng.uniform(20, 80),
                       U=rng.uniform(60, 140), twin=(100, rng.uniform(80, 120))) for _ in range(rng.randrange(1, 6))]
        b = submit.turn_budget(parts, 0)
        r3 = round(submit.pooled_ratio([p["row"] for p in parts]), 3)
        if rng.random() < 0.02:
            r3 = None
        over, warned, rule = submit.compute_verdict(r3, b, len(parts), 0)
        assert (over, warned) == _old_verdict(r3, len(parts)) and rule in (None, "old")
        for k in (1, 2, 4):
            over_k, _, _ = submit.compute_verdict(r3, submit.turn_budget(parts, k), len(parts), k)
            assert not over_k or _old_verdict(r3, len(parts))[0]               # refused at K: refused before too


def test_compute_notes_warn_and_decide_nothing():
    # the player's: the wall clock alone; u_twin and the opponent seat are the host's flags until their lines are
    # measured (11-28 review: the default against itself came out 1.153 on the opponent seat in the container); K = 0
    # (the switch): neither, the receipt as it was
    c = {"K": 2, "turn_start_wall_max_s": 12.0, "u_twin_ratio": 1.4, "opp_seat": 1.2}
    notes = submit.compute_notes(c, 30.0)
    assert len(notes) == 1 and "12.0 秒" in notes[0] and "30 秒" in notes[0]
    assert submit.compute_flags(c) == ["u_twin 1.40 > 1.25", "opp_seat 1.20 > 1.1"]
    assert submit.compute_notes({**c, "K": 0}, 30.0) == [] and submit.compute_flags({**c, "K": 0}) == []
    calm = {"K": 2, "turn_start_wall_max_s": 1.0, "u_twin_ratio": 1.1, "opp_seat": 1.0}
    assert submit.compute_notes(calm) == [] and submit.compute_flags(calm) == []
    assert submit.compute_notes({}) == [] and submit.compute_flags({}) == []
    assert submit.extra_text(-0.04) == submit.extra_text(0) == "回合开头没用到另给的预算"
    assert submit.extra_text(1.234) == "回合开头平均多花了 1.23 个默认回合"


def test_the_receipt_at_k_zero_reads_as_before():
    # K = 0 (the switch): the compute line as submit-3 wrote it, nothing of the turn rule
    rec = {"id": "S-0001", "player": "p", "kind": "deck", "verdict": "收下", "reasons": [], "warnings": [],
           "time": "2026-11-28T00:00:00Z", "version": submit.SUBMIT_VERSION,
           "checks": [{"check": "算力", "ok": True, "detail": {"ratio": 1.01, "unit": "ns"}}], "compute_ratio": 1.01,
           "compute": {"K": 0, "rule": "old", "in_turn": 1.0, "turn_start_q": 0.3, "extra_turns": -0.1}}
    lines = [x for x in submit.receipt_text(rec).splitlines() if "算力" in x]
    assert lines == ["- 算力：过（{\"ratio\": 1.01, \"unit\": \"ns\"}）", "- 每步算力 / 默认打法：1.01"], lines
    rec["compute"]["K"] = 2
    text = submit.receipt_text(rec)
    assert "算力，老规矩（所有步合在一起）/ 默认打法：1.01" in text and "回合开头没用到另给的预算" in text
    assert "按老规矩收下的" in text and "每步算力 / 默认打法" not in text


def _tool_log(name, cls, seed):
    """A game of tools/standins.py `cls` at seat 0 against the default (played here, in this process)."""
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    job = {"id": f"turn-{name}", "seed": seed, "first": None, "decks": [CODES[3], CODES[5]],
           "strategies": [f"py:standins:{cls}", "bot:mcts:100+plan"], "strategy_seeds": [11, 12]}
    return json.loads(json.dumps(play_job(job)))


def test_the_peek_check_carried_through_a_turn():
    """A68: a strategy that peeks only in its turn-start hook and plays by it later in the turn passes the plain
    peek check (the turn's first decision is its plain search) and is caught by peek_turn; an honest planner that
    acts on its plan is not."""
    rng = random.Random(5)
    peeky = _tool_log("peeky", "PlanPeeky", TURN_PEEK[0])
    honest = _tool_log("honest", "PlanUses", TURN_PEEK[0] + 1)
    assert peeky["result"] in ("normal", "draw") and honest["result"] in ("normal", "draw")
    starts = submit.turn_points(peeky, 0)
    assert len(starts) >= 3, starts
    plain = [submit.peek_check(peeky, 0, k, random.Random(rng.randrange(2 ** 32))) for k in starts]
    assert set(plain) <= {"same", "skipped"}, plain                       # the plain check misses it
    carried = [submit.peek_turn(peeky, 0, k, random.Random(rng.randrange(2 ** 32))) for k in starts]
    assert any(r == "differs" for r, _ in carried), carried
    starts = submit.turn_points(honest, 0)
    assert len(starts) >= 3, starts
    carried = [submit.peek_turn(honest, 0, k, random.Random(rng.randrange(2 ** 32))) for k in starts]
    assert all(r in ("same", "skipped") for r, _ in carried) and sum(n for _, n in carried) >= 1, carried
    # from a decision within a turn: carried from there to the turn's end, the same for the honest one
    kinds = submit.turn_kinds(honest["actions"], len(honest["steps"]))
    mine = [k for (s, _, _), k in zip(honest["steps"], kinds) if s == 0]
    mid = next(i for i, k in enumerate(mine) if k == "R")
    assert mid not in starts and submit.peek_turn(honest, 0, mid, random.Random(1))[0] in ("skipped", "same")


# --- receive, end to end ------------------------------------------------------------------------------------------

def test_receive_and_admit(tmp_path):
    pool = _pool(tmp_path, 1)
    subs = tmp_path / "subs"
    d = make_sub(tmp_path / "in1", "新卡组", deck=CODES[4], member="四号")              # Abyss
    rec = submit.receive(d, "fable-ultracode", pool.dir, subs, workers=2, rng_seed=7, smoke_games=2, seeds=SMOKE)
    assert rec["verdict"] == "收下", rec["reasons"]
    assert [c["check"] for c in rec["checks"]] == ["格式", "卡组", "名额和期", "代码（读）", "载入（隔离进程）", "冒烟",
                                                   "算力", "确定性", "偷看"]
    assert rec["uses_slot"] and rec["craft"] == 5 and len(rec["smoke_seeds"]) == 2 and rec["compute_ratio"] is not None
    assert rec["compute"]["method"] == "shadow" and rec["compute"]["games"] >= 1, rec["compute"]
    assert rec["compute"]["rule"] == "old" and rec["compute"]["K"] == submit.TURN_K and rec["version"] == "submit-4"
    assert {"in_turn", "turn_start_q", "extra_turns", "per_turn", "u_twin_ratio", "opp_seat", "c_parts",
            "turn_start_wall_max_s"} <= set(rec["compute"]) and rec["compute"]["in_turn"] is not None
    points = next(c for c in rec["checks"] if c["check"] == "偷看")["detail"]["points"]
    assert any(len(x) == 5 and x[3] == "turn" for x in points)
    assert all(x[2] in ("same", "skipped") for x in points if len(x) == 5), points
    assert (subs / rec["id"] / "receipt.md").exists()
    mid = submit.admit(subs, rec["id"], pool.dir)
    m = Pool(pool.dir).members[mid]
    assert m.owner == "fable-ultracode" and m.strategy == rec["spec"]
    # refused: reads a file; nothing is run; Portal stays open
    d2 = make_sub(tmp_path / "in2", "新卡组", deck=CODES[6], member="六号",
                  src=QUICK + "\nX = open('a').read()\n")
    rec2 = submit.receive(d2, "fable-ultracode", pool.dir, subs, workers=2, rng_seed=8, smoke_games=2, seeds=SMOKE)
    assert rec2["verdict"] == "拒收" and not rec2["uses_slot"] and rec2["smoke_seeds"] == []
    # a second Abyss deck this period: refused before any game
    d3 = make_sub(tmp_path / "in3", "新卡组", deck=CODES[4], member="四号乙")
    rec3 = submit.receive(d3, "fable-ultracode", pool.dir, subs, workers=2, rng_seed=9, smoke_games=2, seeds=SMOKE)
    assert rec3["verdict"] == "拒收" and any("已经交过一副" in r for r in rec3["reasons"])
    # Portal again, fixed: accepted
    d4 = make_sub(tmp_path / "in4", "新卡组", deck=CODES[6], member="六号")
    rec4 = submit.receive(d4, "fable-ultracode", pool.dir, subs, workers=2, rng_seed=10, smoke_games=2, seeds=SMOKE)
    assert rec4["verdict"] == "收下", rec4["reasons"]
    assert [l["id"] for l in submit.ledger(subs) if l["ev"] == "receipt"] == ["S-0001", "S-0002", "S-0003", "S-0004"]
    st = submit.status(subs, pool.dir, "fable-ultracode")
    assert st["classes_done"] == ["梦魇", "超越者"] and len(st["classes_missing"]) == 5


def test_smoke_games_its_own_code_voided_refuse_a_submission(tmp_path, monkeypatch):
    # LD-45: a smoke game the tripwire (or the idle watchdog) voided while the same game with the default strategy
    # played normally is the submission's doing: refused, quoting what changed; other voids stay a warning
    import ladder.runner
    real = ladder.runner.run

    def fake(jobs, path, **kw):
        with open(path, "w", encoding="utf-8") as f:
            for j in jobs:
                sub = j["labels"]["side"] == "sub"
                f.write(json.dumps({"id": j["id"], "result": "void" if sub else "normal", "winner": None if sub else 0,
                                    "error": ("the simulator changed in this worker during the game (LD-40): "
                                              "svsim.cards.abyss.Craft: +1 members") if sub else None}) + "\n")
        return {}
    pool = _pool(tmp_path, 1)
    subs = tmp_path / "subs"
    monkeypatch.setattr(ladder.runner, "run", fake)
    d = make_sub(tmp_path / "in1", "新卡组", deck=CODES[4], member="四号")
    rec = submit.receive(d, "fable-ultracode", pool.dir, subs, workers=2, rng_seed=7, smoke_games=2, seeds=SMOKE)
    assert rec["verdict"] == "拒收" and any("是你的代码" in r and "Craft: +1 members" in r for r in rec["reasons"]), rec
    monkeypatch.setattr(ladder.runner, "run", real)


LONG_LOAD = ("strategy failed to load:\nTraceback (most recent call last):\n" +
             '  File "C:\\claude\\ladder\\ladder\\runner.py", line 255, in _play\n    strategies = load_strategies(job)\n' * 8
             + '  File "C:\\subs\\planpick.py", line 9, in __init__\n    self.iters = 8 + 24 // (seed % 3)\n'
             "ZeroDivisionError: integer division or modulo by zero")


@pytest.mark.parametrize("error", ["strategy failed to load:\nTraceback (most recent call last):\nIndexError: list index",
                                   "the strategies took more than 8.0s to load", "engine error outside a move: X",
                                   LONG_LOAD])
def test_smoke_games_its_own_load_voided_or_all_void_refuse_a_submission(tmp_path, monkeypatch, error):
    # LD-46: a smoke game voided while loading the submission (the default twin loaded fine) is its own doing, and
    # a smoke run where every game is void checks nothing after it: both refused, the reason quoted
    import ladder.runner
    real = ladder.runner.run
    engine = error.startswith("engine")

    def fake(jobs, path, **kw):
        with open(path, "w", encoding="utf-8") as f:
            for j in jobs:
                void = j["labels"]["side"] == "sub" or engine
                f.write(json.dumps({"id": j["id"], "result": "void" if void else "normal",
                                    "winner": None if void else 0, "error": error if void else None}) + "\n")
        return {}
    pool = _pool(tmp_path, 1)
    monkeypatch.setattr(ladder.runner, "run", fake)
    d = make_sub(tmp_path / "in1", "新卡组", deck=CODES[4], member="四号")
    rec = submit.receive(d, "fable-ultracode", pool.dir, tmp_path / "subs", workers=2, rng_seed=7, smoke_games=2, seeds=SMOKE)
    monkeypatch.setattr(ladder.runner, "run", real)
    want = "全作废" if engine else "是你的代码"
    assert rec["verdict"] == "拒收" and any(want in r and error.splitlines()[0][:20] in r for r in rec["reasons"]), rec
    assert any(error.splitlines()[-1] in r for r in rec["reasons"]), rec    # LD-47: the player's exception is quoted


def test_an_accepted_update_goes_to_the_gate(tmp_path, monkeypatch):
    """gate_update's wiring (the gate itself is tests/test_gate.py): old version, routes (A33), pool update."""
    from ladder.runner import load_deck
    pool = Pool.create(tmp_path / "pool", seeds=(99001460, 99001470), rng_seed=1)
    for c in CODES[:2]:
        pool.enter([x.card_id for x in load_deck(c)], "bot:greedy", "baseline")
    pool.advance(force="test")
    pool.advance(force="test")                                 # period 2: a strategy period
    mid = pool.active()[0].mid
    was = pool.members[mid].strategy
    subs = tmp_path / "subs"
    calls = []

    class FakeGate:
        def __init__(self, frozen, member, new, old, kind, change, prediction, seeds, out_dir, **kw):
            calls.append({"member": member, "new": new, "old": old, "kind": kind, "change": change,
                          "ledger_root": kw.get("ledger_root"), "resubmit_of": kw.get("resubmit_of"),
                          "since": kw.get("since")})

        def run(self, workers=4, mask=None):
            return {"gate": f"G-{len(calls):04d}", "verdict": "passed" if len(calls) == 1 else "not passed"}
    import ladder.gate
    monkeypatch.setattr(ladder.gate, "Gate", FakeGate)

    def receipt(rid, route=None, spec="py:sub_x:Quick", src=None, was_=None, change="改了换牌", **extra):
        (subs / rid).mkdir(parents=True, exist_ok=True)
        (subs / "code").mkdir(parents=True, exist_ok=True)
        (subs / "code" / f"{spec.split(':')[1]}.py").write_text(
            src or f"class Quick:\n    N = {rid[-1]}\n", encoding="utf-8")
        (subs / rid / "submission.json").write_text(json.dumps(
            {"type": "打法更新", "member": "一号", "class": "Quick", "change": change, "prediction": "+3，因为…",
             "route": route, **extra}, ensure_ascii=False), encoding="utf-8")
        submit._append(subs, {"ev": "receipt", "id": rid, "player": "fable-ultracode", "kind": "update", "verdict": "收下",
                              "member": "一号", "mid": mid, "spec": spec, "route": route,
                              "was": was_ or {"strategy": pool.members[mid].strategy, "version": 1}})
    receipt("S-0001", spec="py:sub_S0001:Quick")
    out = submit.gate_update(subs, "S-0001", pool.dir, tmp_path / "frozen.json", (1, 2), tmp_path / "gates", delta=3)
    assert out["verdict"] == "passed" and out["version"] == 2
    assert calls[0]["old"] == was and calls[0]["new"] == "py:sub_S0001:Quick" and calls[0]["kind"] == "better"
    assert calls[0]["ledger_root"] == tmp_path / "gates"           # host side, not the repository
    assert Pool(pool.dir).members[mid].strategy == "py:sub_S0001:Quick"
    with pytest.raises(SystemExit):
        submit.gate_update(subs, "S-0001", pool.dir, tmp_path / "frozen.json", (1, 2), tmp_path / "gates", delta=3)
    # a three-step route: step 1 is only recorded; step 3 is gated against the version before step 1
    pool = Pool(pool.dir)
    receipt("S-0002", route={"steps": 3, "step": 1, "stop_if": "x"}, spec="py:sub_S0002:Quick")
    before = pool.members[mid].strategy
    mid_step = submit.gate_update(subs, "S-0002", pool.dir, tmp_path / "f.json", (1, 2), tmp_path / "gates", delta=3)
    assert mid_step["gate"] is None and "中间一步" in mid_step["verdict"] and len(calls) == 1
    receipt("S-0003", route={"steps": 3, "step": 3, "route_of": "S-0002"}, spec="py:sub_S0003:Quick")
    last = submit.gate_update(subs, "S-0003", pool.dir, tmp_path / "f.json", (1, 2), tmp_path / "gates", delta=3)
    assert calls[1]["old"] == before and "停在第 3 步" in calls[1]["change"]
    assert last["verdict"] == "not passed" and "version" not in last
    assert Pool(pool.dir).members[mid].strategy == before         # not passed: the pool keeps the old version
    # the same code again under a new receipt (comments and layout aside): not gated again (red line)
    receipt("S-0004", spec="py:sub_S0004:Quick", src="# again\nclass Quick:\n    N   =   1   # same as S-0001\n")
    same = submit.gate_update(subs, "S-0004", pool.dir, tmp_path / "f.json", (1, 2), tmp_path / "gates", delta=3)
    assert same["gate"] is None and "同一个改动" in same["verdict"] and same["same_as"] == "S-0001"
    assert len(calls) == 2
    # after S-0003 failed on this version: the same change in other code is not gated; a new try must name it
    receipt("S-0005", spec="py:sub_S0005:Quick")
    twin = submit.gate_update(subs, "S-0005", pool.dir, tmp_path / "f.json", (1, 2), tmp_path / "gates", delta=3)
    assert twin["gate"] is None and "改动说明和预测和 S-0003 一样" in twin["verdict"] and len(calls) == 2
    receipt("S-0006", spec="py:sub_S0006:Quick", change="换牌改成看对手职业")
    bare = submit.gate_update(subs, "S-0006", pool.dir, tmp_path / "f.json", (1, 2), tmp_path / "gates", delta=3)
    assert bare["gate"] is None and "resubmit_of" in bare["verdict"] and len(calls) == 2
    # an update written against an older version is compared with the version the member has now
    receipt("S-0007", spec="py:sub_S0007:Quick", was_={"strategy": was, "version": 1}, change="换牌改成看对手职业",
            resubmit_of="S-0003", since="换牌看对手职业，不再固定换掉高费卡")
    now = Pool(pool.dir).members[mid]
    late = submit.gate_update(subs, "S-0007", pool.dir, tmp_path / "f.json", (1, 2), tmp_path / "gates", delta=3)
    assert calls[2]["old"] == now.strategy != was and "现在这一版" in late["note"]
    assert calls[2]["resubmit_of"] == "G-0002" and calls[2]["since"].startswith("换牌看对手职业")
    note = (subs / "S-0006" / "gate-note.md").read_text(encoding="utf-8")
    assert "resubmit_of" in note and "S-0003" in note and "G-0" not in note        # the player's own receipts only
    assert "检验" in (subs / "S-0007" / "gate-note.md").read_text(encoding="utf-8")
    # two updates received before either is gated: the first fails, the second is still gated (it could not have
    # named a failure that had not happened yet); a route may carry resubmit_of/since on its first step
    receipt("S-0008", spec="py:sub_S0008:Quick", change="甲方案", resubmit_of="S-0007", since="fable-ultracode")
    receipt("S-0009", spec="py:sub_S0009:Quick", change="乙方案", resubmit_of="S-0007", since="fable")
    calls_before = len(calls)
    submit.gate_update(subs, "S-0008", pool.dir, tmp_path / "f.json", (1, 2), tmp_path / "gates", delta=3)
    sib = submit.gate_update(subs, "S-0009", pool.dir, tmp_path / "f.json", (1, 2), tmp_path / "gates", delta=3)
    assert sib["gate"] is not None and len(calls) == calls_before + 2
    receipt("S-0010", route={"steps": 2, "step": 1, "stop_if": "x"}, spec="py:sub_S0010:Quick", change="丙方案",
            resubmit_of="S-0009", since="换了搜索的剪枝")
    submit.gate_update(subs, "S-0010", pool.dir, tmp_path / "f.json", (1, 2), tmp_path / "gates", delta=3)
    receipt("S-0011", route={"steps": 2, "step": 2, "route_of": "S-0010"}, spec="py:sub_S0011:Quick", change="丙方案二",
            src="class Quick:\n    N = 11\n")
    end = submit.gate_update(subs, "S-0011", pool.dir, tmp_path / "f.json", (1, 2), tmp_path / "gates", delta=3)
    assert end["gate"] is not None and calls[-1]["since"] == "换了搜索的剪枝"


def test_an_update_passed_in_a_merged_period_goes_into_the_pool(tmp_path, monkeypatch):
    from ladder.runner import load_deck
    pool = Pool.create(tmp_path / "pool", seeds=(99001460, 99001470), rng_seed=1)
    pool.enter([x.card_id for x in load_deck(CODES[0])], "bot:greedy", "baseline")
    while pool.period < 5:                     # 5: a deck period before S35, merged now
        pool.advance(force="test")
    mid = pool.active()[0].mid

    class FakeGate:
        def __init__(self, *a, **kw):
            pass

        def run(self, workers=4, mask=None):
            return {"gate": "G-0001", "verdict": "passed"}
    import ladder.gate
    monkeypatch.setattr(ladder.gate, "Gate", FakeGate)
    subs = tmp_path / "subs"
    (subs / "S-0001").mkdir(parents=True)
    (subs / "code").mkdir(parents=True)
    (subs / "code" / "sub_S0001.py").write_text("class Quick:\n    N = 1\n", encoding="utf-8")
    (subs / "S-0001" / "submission.json").write_text(json.dumps(
        {"type": "打法更新", "member": "一号", "class": "Quick", "change": "c", "prediction": "p"}, ensure_ascii=False),
        encoding="utf-8")
    submit._append(subs, {"ev": "receipt", "id": "S-0001", "player": "fable", "kind": "update", "verdict": "收下",
                          "period": 5, "member": "一号", "mid": mid, "spec": "py:sub_S0001:Quick", "route": None,
                          "was": {"strategy": "bot:greedy", "version": 1}})
    out = submit.gate_update(subs, "S-0001", pool.dir, tmp_path / "frozen.json", (1, 2), tmp_path / "gates", delta=5)
    assert out["verdict"] == "passed" and out["version"] == 2
    assert Pool(pool.dir).members[mid].strategy == "py:sub_S0001:Quick"


def test_a_route_stop_mark_is_checked(tmp_path):
    bad = make_sub(tmp_path / "s1", "打法更新", member="一号", change="c", prediction="p",
                   route={"steps": 3, "step": 3, "route_of": "S-0001", "stop": True})
    with pytest.raises(submit.Refused) as e:
        submit.read_dir(bad)
    assert any("stop" in p for p in e.value.args[0])
    ok = make_sub(tmp_path / "s2", "打法更新", member="一号", change="c", prediction="p",
                  route={"steps": 3, "step": 2, "route_of": "S-0001", "stop": True})
    assert submit.read_dir(ok)["meta"]["route"]["stop"] is True


def test_a_resubmission_names_the_failed_gate_and_what_changed(tmp_path):
    bad = make_sub(tmp_path / "s1", "打法更新", member="一号", change="c", prediction="p", resubmit_of="S-0001")
    with pytest.raises(submit.Refused) as e:
        submit.read_dir(bad)
    assert any("since" in p for p in e.value.args[0])
    ok = make_sub(tmp_path / "s2", "打法更新", member="一号", change="c", prediction="p", resubmit_of="S-0001",
                  since="搜索深度按剩余费用调")
    assert submit.read_dir(ok)["meta"]["resubmit_of"] == "S-0001"


def test_a_strategy_over_the_compute_cap_is_refused(tmp_path):
    """A52: every version is held to 1.08 x the default's per-step compute at receipt (new decks never meet the gate)."""
    pool = _pool(tmp_path, 1)
    heavy = QUICK.replace('"iterations": 8', '"iterations": 300').replace("class Quick", "class Heavy")
    d = make_sub(tmp_path / "in", "新卡组", src=heavy, cls="Heavy", deck=CODES[4], member="重")
    rec = submit.receive(d, "fable-ultracode", pool.dir, tmp_path / "subs", workers=2, rng_seed=7, smoke_games=2, seeds=SMOKE)
    assert rec["verdict"] == "拒收" and (rec.get("compute_ratio") or 0) > submit.COMPUTE_REFUSE, rec["reasons"]
    assert [r for r in rec["reasons"] if r.startswith("[算力]") and "A52" in r], rec["reasons"]
    assert [c["check"] for c in rec["checks"]][-1] == "算力"            # nothing after it runs
    assert len([r for r in rec["reasons"] if r.startswith("[算力]")]) == 2    # both rules say why (TURN_K > 0)
    assert rec["compute"]["rule"] is None and rec["compute"]["in_turn"] > submit.COMPUTE_REFUSE, rec["compute"]


def test_a_planner_within_its_turn_budget_passes_on_the_turn_rule(tmp_path, monkeypatch):
    """A68 (Salem 11-27): a strategy that spends its turn-start hook (16 searches of the default's size: about three
    default turns in the container) and little within the turn is over the old rule (all steps) and within the turn
    rule. TURN_K is set to 6 here only so that two smoke pairs of the container's noise can't carry it across a line;
    the real one is submit.TURN_K. Its peek points at turn starts, carried through the turn, all the same. K = 0
    (the switch) refuses the same code on the old rule alone, as before the turn rule."""
    monkeypatch.setattr(submit, "TURN_K", 6)
    pool = _pool(tmp_path, 1)
    subs = tmp_path / "subs"
    d = make_sub(tmp_path / "in1", "新卡组", src=PLANS, cls="Plans", deck=CODES[4], member="规划")
    rec = submit.receive(d, "fable-ultracode", pool.dir, subs, workers=2, rng_seed=7, smoke_games=2, seeds=PLAN_SMOKE)
    assert rec["verdict"] == "收下", rec["reasons"]
    c = rec["compute"]
    assert c["rule"] == "turn" and c["K"] == 6 and rec["compute_ratio"] > submit.COMPUTE_REFUSE, (rec["compute_ratio"], c)
    assert c["in_turn"] < 1 and c["turn_start_q"] < 1 and c["extra_turns"] > 0.5, c
    assert c["per_turn"]["turns"] == c["turns"] > 0 and set(c["c_parts"]) == {"F", "R"}
    assert c["turn_start_wall_max_s"] is not None and c["opp_seat"] is not None and c["u_twin_ratio"] is not None
    peek = next(x for x in rec["checks"] if x["check"] == "偷看")["detail"]["points"]
    carried = [x for x in peek if len(x) == 5 and x[3] == "turn"]
    assert carried and all(x[2] in ("same", "skipped") for x in carried) and len(peek) > len(carried), peek
    text = (subs / rec["id"] / "receipt.md").read_text(encoding="utf-8")
    assert "算力，按回合（回合开头另给 6 个默认回合）" in text and "「按回合给」那条规矩收下" in text
    assert "载入时的 CPU" in text and rec["load_cpu"]["construct"] is not None
    assert isinstance(c["flags"], list) and not any(x.startswith(("u_twin", "opp_seat")) for x in rec["warnings"])
    monkeypatch.setattr(submit, "TURN_K", 0)
    d = make_sub(tmp_path / "in2", "新卡组", src=PLANS, cls="Plans", deck=CODES[5], member="规划二")
    rec = submit.receive(d, "fable-ultracode", pool.dir, subs, workers=2, rng_seed=8, smoke_games=2, seeds=PLAN_SMOKE)
    assert rec["verdict"] == "拒收" and [x["check"] for x in rec["checks"]][-1] == "算力", rec["reasons"]
    comp = [r for r in rec["reasons"] if r.startswith("[算力]")]
    assert len(comp) == 1 and comp[0].startswith("[算力] 每步算力是默认打法的") and "A52" in comp[0], rec["reasons"]
    assert rec["compute"]["K"] == 0 and rec["compute"]["rule"] is None
    assert next(x for x in rec["checks"] if x["check"] == "算力")["detail"].keys() == {"ratio", "unit"}
    text = (subs / rec["id"] / "receipt.md").read_text(encoding="utf-8")
    assert "- 每步算力 / 默认打法：" in text and "按回合" not in text and "老规矩" not in text, text


def test_memory_kept_from_game_to_game_fails_the_replay_of_late_games(tmp_path):
    """A68: a module-level book carried from game to game (the tripwire follows svsim and ladder only) changes the
    choices of a worker's later games; the determinism check replays the last smoke games, played after others in
    one worker (workers=1 here), in this process that has played none: they differ. (The first two, as before, were
    the worker's first games: replayed in order here, they repeated the same memory and passed.)"""
    pool = _pool(tmp_path, 1)
    d = make_sub(tmp_path / "in", "新卡组", src=REMEMBERS, cls="Remembers", deck=CODES[4], member="记性")
    rec = submit.receive(d, "fable-ultracode", pool.dir, tmp_path / "subs", workers=1, rng_seed=7, smoke_games=3,
                         seeds=MEMORY_SMOKE)
    assert rec["verdict"] == "拒收" and any(r.startswith("[确定性]") for r in rec["reasons"]), rec["reasons"]
    assert [x["check"] for x in rec["checks"]][-1] == "确定性" and rec["compute"]["rule"] == "old"



def test_deliver_puts_each_players_own_receipts_and_status_in_their_box(tmp_path):
    # A50 (prompt review 11-23): the receipts, gate results and the period's status go into the player's own
    # receipts folder, under the name of the directory they handed in; nothing of another player's
    pool = _pool(tmp_path, 1)
    subs = tmp_path / "subs"
    recs = [{"ev": "receipt", "id": "S-0001", "player": "fable-ultracode", "period": pool.period, "kind": "deck", "verdict": "收下",
             "craft": 1, "dir": str(tmp_path / "fable-ultracode" / "submit" / "精灵1"), "member": "一号", "reasons": [],
             "warnings": [], "checks": [], "time": "t", "version": "v"},
            {"ev": "receipt", "id": "S-0002", "player": "fable", "period": pool.period, "kind": "deck", "verdict": "拒收",
             "craft": 2, "dir": str(tmp_path / "fable" / "submit" / "皇家1"), "member": "秘密的名字",
             "reasons": ["[卡组] x"], "warnings": [], "checks": [], "time": "t", "version": "v"},
            {"ev": "receipt", "id": "S-0003", "player": "fable-ultracode", "period": pool.period, "kind": "deck", "verdict": "拒收",
             "craft": 2, "dir": str(tmp_path / "fable-ultracode" / "submit" / "精灵1"), "member": "二号", "reasons": ["[卡组] y"],
             "warnings": [], "checks": [], "time": "t", "version": "v"}]
    for r in recs:
        submit._append(subs, r)
        (subs / r["id"]).mkdir(parents=True)
        (subs / r["id"] / "receipt.md").write_text(submit.receipt_text(r), encoding="utf-8")
    submit.gate_note(subs, "S-0001", "检验过了。")
    players = tmp_path / "players"
    assert submit.deliver(subs, pool.dir, players) == {"fable-ultracode": 2, "fable": 1}
    box = players / "fable-ultracode" / "receipts"
    assert sorted(p.name for p in box.iterdir()) == ["状态.md", "精灵1-S-0003.md", "精灵1-检验.md", "精灵1.md"]
    assert "S-0001" in (box / "精灵1.md").read_text(encoding="utf-8")
    assert (box / "精灵1-检验.md").read_text(encoding="utf-8").endswith("检验过了。\n")
    status = (box / "状态.md").read_text(encoding="utf-8")
    assert "已经收下的职业：精灵" in status and "皇家护卫" in status       # Sword refused: still missing
    mine = "".join(p.read_text(encoding="utf-8") for p in box.iterdir())
    assert "秘密的名字" not in mine and "S-0002" not in mine
    assert sorted(p.name for p in (players / "fable" / "receipts").iterdir()) == ["状态.md", "皇家1.md"]


def test_receipt_file_names_in_the_players_folder():
    taken = set()
    assert submit.box_name("梦魇1", "S-0001", taken) == "梦魇1"
    assert submit.box_name("梦魇1", "S-0002", taken) == "梦魇1-S-0002"          # used twice: the id added
    for bad in ("状态", "X-检验", "X-没收成", "aux", "CON.txt", "a/b", "x" * 61, "trailing.", " lead", ""):
        assert submit.box_name(bad, "S-0009", set()) == "S-0009", bad


def test_smoke_seeds_running_out_stop_the_receipt_before_any_game():
    ids, _ = submit.check_deck(CODES[0])
    used = set(range(99001420, 99001448))                             # 2 left in a 30-seed range
    with pytest.raises(SystemExit, match="只剩 2 个"):
        submit.smoke_jobs("bot:greedy", ids, "S-0001", random.Random(1), used, games=3, seeds=SMOKE)
    jobs, played = submit.smoke_jobs("bot:greedy", ids, "S-0001", random.Random(1), used, games=2, seeds=SMOKE)
    assert sorted(played) == [99001448, 99001449] and len(jobs) == 4


def test_smoke_games_look_like_pool_games_seeds_and_lists():
    """LD-57: strategy seeds from the pool's range (62 bits, as deal.seal); each opponent's list a public one with a
    few cards swapped, legal and playable, the twin on the very same list."""
    from collections import Counter
    from ladder import base
    from ladder.runner import load_deck, unscripted
    from svsim.cards.decks import validate
    ids, _ = submit.check_deck(CODES[0])
    crafts = sorted(base.baseline_lists())
    public = submit.public_lists()
    assert set(public) == set(crafts) and all(sorted(base.baseline_lists()[c]) in public[c] for c in crafts)
    jobs, _ = submit.smoke_jobs("bot:greedy", ids, "S-0001", random.Random(3), set(), games=28, seeds=SMOKE,
                                opponents=public)
    assert any(s >= 2 ** 31 for j in jobs for s in j["strategy_seeds"])
    assert all(1 <= s < 2 ** 62 for j in jobs for s in j["strategy_seeds"])
    swapped = []
    for i in range(28):
        sub, twin = jobs[2 * i], jobs[2 * i + 1]
        assert twin["decks"] == sub["decks"] and twin["strategy_seeds"] == sub["strategy_seeds"]
        opp = sub["decks"][1 - sub["labels"]["seat"]]
        deck = load_deck(opp)
        assert int(base.craft_of(deck)) == crafts[i % 7] and not validate(deck) and not unscripted(deck)
        swapped.append(min(sum((Counter(opp) - Counter(l)).values()) for l in public[crafts[i % 7]]))
    assert max(swapped) <= submit.SMOKE_SWAPS and sum(1 for x in swapped if x) >= 14, swapped
    jobs, _ = submit.smoke_jobs("bot:greedy", ids, "S-0002", random.Random(3), set(), games=7, seeds=SMOKE, swaps=0)
    assert [sorted(j["decks"][1 - j["labels"]["seat"]]) for j in jobs[::2]] == \
        [sorted(base.baseline_lists()[c]) for c in crafts]               # no lists given, no swaps: the baselines


def test_receive_refuses_a_name_that_is_no_player(tmp_path):
    # S20: players are named; a typo (or an old codename) must not open a ledger for nobody
    import pytest
    for who in ("甲", "opsu", "Fable"):
        with pytest.raises(SystemExit, match="没有选手"):
            submit.receive(tmp_path / "in", who, tmp_path / "pool", tmp_path / "subs")
    assert not (tmp_path / "subs").exists()
