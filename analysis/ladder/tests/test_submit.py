"""Submissions (phase 2, item 2.3): the entry point and its checks. Seeds 99001410-99001469 (host probe bank,
SEEDS.md): 99001410-99001419 the peek-check games, 99001420-99001449 the smoke and load-check games of `receive`."""
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
LINES = [l.strip().split("|") for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(encoding="utf-8")
         .splitlines() if l.strip() and not l.startswith("#")]
CODES = [c for _, c in LINES]
SMOKE = (99001420, 99001450)

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
from ladder.interface import PlayerStrategy
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

    def guess(self, pos):
        return base.default_guess(pos.opp_craft)

    def mulligan(self, state):
        return bot_mulligan(state)

    def evaluate(self, state, me, me_next):
        x = getattr(state, "turn", 0)
        return evaluate(state, me, DEFAULT, player_moves_next=me_next) + 0.0 * math.sqrt(x) + float(np.zeros(1)[0])

    def veto(self, state, action):
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
