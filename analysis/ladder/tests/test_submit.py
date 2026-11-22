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
    ("import numpy as np\nnp.load('x.npy')", None),            # np.load is allowed by name; files fail at load time
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


def _pool(tmp_path, period: int):
    pool = Pool.create(tmp_path / "pool", seeds=(99001460, 99001470), rng_seed=1)
    pool.advance()                                         # period 1: a deck period
    return pool


def test_slots_and_periods(tmp_path):
    """S5 (Salem 11-22): one new deck per class per deck period (a refused one leaves the class open, A35);
    updates not limited."""
    pool = _pool(tmp_path, 1)
    ids, _ = submit.check_deck(CODES[1])                                  # Sword
    sub = {"kind": "deck", "meta": {"member": "二号"}, "deck_ids": ids}
    r = lambda i, kind, **k: {"ev": "receipt", "id": f"S-{i:04d}", "player": "甲", "period": pool.period,
                              "kind": kind, **k}
    problems, info = submit.check_slots(sub, "甲", pool, [r(1, "deck", verdict="拒收", craft=2)])
    assert problems == [] and info["uses_slot"] and info["craft"] == 2   # the refused one left Sword open
    problems, _ = submit.check_slots(sub, "甲", pool, [r(1, "deck", verdict="收下", craft=2)])
    assert any("已经交过一副" in p for p in problems)
    problems, _ = submit.check_slots(sub, "甲", pool, [r(i, "deck", verdict="收下", craft=c)
                                                       for i, c in enumerate((1, 3, 4, 5, 6, 7))])
    assert problems == []                                                # six other classes don't block Sword
    problems, _ = submit.check_slots(sub, "乙", pool, [r(1, "deck", verdict="收下", craft=2)])
    assert problems == []                                                # another player's classes are theirs
    mid = pool.enter(ids, "bot:mcts:100+plan", "甲")
    pool.advance(force="test: straight to a strategy period")
    admitted = [{"ev": "admit", "player": "甲", "member": "二号", "mid": mid}]
    problems, _ = submit.check_slots(sub, "甲", pool, admitted)
    assert any("卡组期" in p for p in problems)
    up = {"kind": "update", "meta": {"member": "二号"}}
    many = admitted + [r(i, "update", verdict="拒收", member="二号") for i in range(1, 21)]
    problems, info = submit.check_slots(up, "甲", pool, many)
    assert problems == [] and info["mid"] == mid and up["deck_ids"] == ids   # updates are not limited
    routed = admitted + [r(1, "update", member="二号", route={"steps": 2, "step": 1})]
    later = {"kind": "update", "meta": {"member": "二号", "route": {"steps": 2, "step": 2, "route_of": "S-0001"}}}
    problems, _ = submit.check_slots(later, "甲", pool, routed)
    assert problems == []
    wrong = {"kind": "update", "meta": {"member": "二号", "route": {"steps": 3, "step": 2, "route_of": "S-0001"}}}
    problems, _ = submit.check_slots(wrong, "甲", pool, routed)
    assert any("总步数" in p for p in problems)
    problems, _ = submit.check_slots({"kind": "update", "meta": {"member": "三号"}}, "甲", pool, admitted)
    assert any("没有叫" in p for p in problems)


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


# --- receive, end to end ------------------------------------------------------------------------------------------

def test_receive_and_admit(tmp_path):
    pool = _pool(tmp_path, 1)
    subs = tmp_path / "subs"
    d = make_sub(tmp_path / "in1", "新卡组", deck=CODES[4], member="四号")              # Abyss
    rec = submit.receive(d, "甲", pool.dir, subs, workers=2, rng_seed=7, smoke_games=2, seeds=SMOKE)
    assert rec["verdict"] == "收下", rec["reasons"]
    assert [c["check"] for c in rec["checks"]] == ["格式", "卡组", "名额和期", "代码（读）", "载入（隔离进程）", "冒烟",
                                                   "算力", "确定性", "偷看"]
    assert rec["uses_slot"] and rec["craft"] == 5 and len(rec["smoke_seeds"]) == 2 and rec["compute_ratio"] is not None
    assert (subs / rec["id"] / "receipt.md").exists()
    mid = submit.admit(subs, rec["id"], pool.dir)
    m = Pool(pool.dir).members[mid]
    assert m.owner == "甲" and m.strategy == rec["spec"]
    # refused: reads a file; nothing is run; Portal stays open
    d2 = make_sub(tmp_path / "in2", "新卡组", deck=CODES[6], member="六号",
                  src=QUICK + "\nX = open('a').read()\n")
    rec2 = submit.receive(d2, "甲", pool.dir, subs, workers=2, rng_seed=8, smoke_games=2, seeds=SMOKE)
    assert rec2["verdict"] == "拒收" and not rec2["uses_slot"] and rec2["smoke_seeds"] == []
    # a second Abyss deck this period: refused before any game
    d3 = make_sub(tmp_path / "in3", "新卡组", deck=CODES[4], member="四号乙")
    rec3 = submit.receive(d3, "甲", pool.dir, subs, workers=2, rng_seed=9, smoke_games=2, seeds=SMOKE)
    assert rec3["verdict"] == "拒收" and any("已经交过一副" in r for r in rec3["reasons"])
    # Portal again, fixed: accepted
    d4 = make_sub(tmp_path / "in4", "新卡组", deck=CODES[6], member="六号")
    rec4 = submit.receive(d4, "甲", pool.dir, subs, workers=2, rng_seed=10, smoke_games=2, seeds=SMOKE)
    assert rec4["verdict"] == "收下", rec4["reasons"]
    assert [l["id"] for l in submit.ledger(subs) if l["ev"] == "receipt"] == ["S-0001", "S-0002", "S-0003", "S-0004"]
    st = submit.status(subs, pool.dir, "甲")
    assert st["classes_done"] == ["梦魇", "超越者"] and len(st["classes_missing"]) == 5
