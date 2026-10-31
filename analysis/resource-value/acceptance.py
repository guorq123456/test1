"""Acceptance positions for a resource-aware evaluation: Salem's verdicts on the bot's games with DFM's
增幅证据三轴土 (2026-10-31 22:45Z-23:03Z, architecture thread; file shadowverse/watch-sanzhoutu-2026-10-31.md).

Each item rebuilds the position by replaying the league deal (league.py seeds, both sides mcts:100+plan) up to the
deck's turn, plays Salem's line and the bot's line to the end of the turn, and scores both with the evaluation
under test (the mean over 40 reseeded copies, for random effects). An item passes when Salem's line scores higher.

These are checks, not fitting targets: the evaluation under test must get its card values from the cards
themselves (shadowverse/resource-value-design-2026-10-31.md), with no parameter set from these items. The external
deck enters no search, self-play or training.

    python analysis/resource-value/acceptance.py            # the current hand-set evaluation
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from svsim.cards.pool import POOL  # noqa: E402
from svsim.core.engine import apply, legal_actions, new_game  # noqa: E402
from svsim.search import evaluate as EV  # noqa: E402
from svsim.tools import deckbuild as DB  # noqa: E402
from svsim.tools.arena import make_agent  # noqa: E402
from svsim.ui.text import describe  # noqa: E402

REF = ROOT / "analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt"
ROSTER = ROOT / "analysis/deckbuild/blind-test/league5/roster.txt"
DECK = "dfm/RUNE-ユーリ"

# (name, opponent, seed, deck goes first, turn, Salem's line, the bot's line, kind)
ITEMS = [
    ("第一局第3回合：零嘴做4土 > 空过", "bot/T1-SWORD-1", 85981131, True, 3,
     ["使用「暴食的零嘴」，模式 1"], [], "资源"),
    ("第二局第3回合：先锅后光 > 先光后锅", "bot/T1-ABYSS-1", 85981161, True, 3,
     ["使用「魔女的炼金炉」", "使用「智慧光辉」"], ["使用「智慧光辉」", "使用「魔女的炼金炉」"], "资源"),
    ("第三局第4回合：先打物证再启动 > 先打解谜旋律再启动", "g3/g3-P1-ABYSS-nocturne", 85981441, False, 4,
     ["使用「神域的物证」", "启动「神域的物证」"], ["使用「解谜旋律」", "启动「神域的物证」"], "资源"),
    ("第一局第7回合：琪可打骑士+魔弹 > 怪兽打骑士+魔弹+琪可打脸", "bot/T1-SWORD-1", 85981131, True, 7,
     ["「玛纳利亚文书官·琪可」攻击敌方场上的「骑士」", "使用「玛纳利亚魔弹」", "使用「迷人怪兽」"],
     ["使用「迷人怪兽」", "「迷人怪兽」攻击敌方场上的「骑士」", "使用「玛纳利亚魔弹」", "「玛纳利亚文书官·琪可」攻击敌方主战者"],
     "打脸还是解场"),
]


def position(opp_label, seed, first, turn):
    ref, ros = dict(DB.read_seeds(str(REF))), dict(DB.read_seeds(str(ROSTER)))
    for seat in (0, 1):
        cards = [None, None]
        cards[seat], cards[1 - seat] = [POOL[i] for i in ref[DECK]], [POOL[i] for i in ros[opp_label]]
        state = new_game(cards[0], cards[1], seed=seed)
        if (state.first == seat) != first:
            continue
        agents = [None, None]
        agents[seat] = make_agent("mcts:100+plan", 2 * seed + seat)
        agents[1 - seat] = make_agent("mcts:100+plan", 2 * seed + 1 - seat + 7919)
        while not (state.turn == turn and state.active == seat and state.phase.name == "MAIN"):
            apply(state, agents[state.active].act(state, legal_actions(state)))
        return state, seat
    raise ValueError("no such seat")


def score(state, seat, line, k=40, evaluate=None):
    evaluate = evaluate or (lambda s, p: EV.evaluate(EV.after_end_of_turn(s), p, EV.DEFAULT))
    total = 0.0
    for j in range(k):
        t = state.clone()
        t.rng = random.Random(j)
        for step in line:
            action = next(a for a in legal_actions(t) if step in describe(t, a))
            apply(t, action)
        total += evaluate(t, seat)
    return total / k


def run(evaluate=None):
    passed = 0
    for name, opp, seed, first, turn, salem, bot, kind in ITEMS:
        state, seat = position(opp, seed, first, turn)
        a, b = score(state, seat, salem, evaluate=evaluate), score(state, seat, bot, evaluate=evaluate)
        ok = a > b
        passed += ok
        print(f"{'过' if ok else '没过'}  {name}（{kind}）：Salem 的打法 {a:.2f}，bot 的打法 {b:.2f}")
    print(f"{passed}/{len(ITEMS)} 过")
    return passed


if __name__ == "__main__":
    run()
