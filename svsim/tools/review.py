"""Review a recorded game: at every decision of the human player, what the AI
would have done there, and how it rates both choices (Chinese output).

    python -m svsim.tools.review replays/20261005-201500-123.json
    python -m svsim.tools.review "<回放码>" --ai mcts:400+plan --summary

For each of your turns: the position, then each of your actions; where the AI
would have chosen differently, its choice and the ISMCTS values (0..1, the
expected result from your side) of your move and of its own. Each turn also
says how much damage the resource-flow planner thought possible that turn and
how much you dealt. --summary prints only the overall agreement and the turns
with the biggest disagreements.
"""
from __future__ import annotations

import argparse

from svsim.agents.greedy_agent import mulligan
from svsim.cards import library
from svsim.core.actions import Mulligan
from svsim.core.engine import legal_actions
from svsim.core.enums import Phase
from svsim.search import combo
from svsim.search.mcts import action_key
from svsim.tools import records
from svsim.tools.arena import make_agent
from svsim.ui.text import card_line, describe, render_state

assert library.__all__


def ai_view(state, spec: str, seed: int):
    """(the AI's action, value of each root action by key) at this position."""
    agent = make_agent(spec, seed)
    action = agent.act(state, legal_actions(state))
    search = getattr(getattr(agent, "base", agent), "search", None)
    root = getattr(search, "last_root", None)
    values = {}
    if root is not None:
        values = {k: search.estimate(n) for k, n in root.children.items() if n.visits}
    return action, values


def review(record: dict, spec: str = "mcts:200+plan", human: int = 0, say=print, summary: bool = False) -> dict:
    """Replay `record` and compare `human`'s decisions with the AI's. Returns the
    statistics (decisions, agreements, the largest value gaps)."""
    out = (lambda *a: None) if summary else say
    stats = {"decisions": 0, "same": 0, "gaps": []}
    turn, hp_at_start, best_this_turn = None, None, None
    notes = records.notes_at(record)
    for index, (state, action) in enumerate(records.steps(record)):
        if state.active != human:
            if turn is not None and state.turn != turn:
                dealt = hp_at_start - state.players[1 - human].leader_hp
                out(f"  本回合打了对手 {dealt} 点；规划器认为最多 {best_this_turn} 点")
                turn = None
            continue
        if state.phase == Phase.MULLIGAN and isinstance(action, Mulligan):
            hand = state.players[human].hand
            names = lambda idx: "、".join(card_line(state, hand[i], in_hand=True) for i in idx) or "不换"
            ai = mulligan(state)
            out("起手：" + "；".join(card_line(state, c, in_hand=True) for c in hand))
            out(f"  你换掉：{names(action.indices)}")
            if set(action.indices) != set(ai.indices):
                out(f"  AI 会换：{names(ai.indices)}")
            continue
        if state.turn != turn:
            turn = state.turn
            hp_at_start = state.players[1 - human].leader_hp
            best_this_turn = combo.plan(state, 20000).damage
            out(f"\n===== 第 {state.turn} 回合（你的第 {state.players[human].turns_taken} 回合）=====")
            out(render_state(state, viewer=human))
        for text in notes.get(index, []):
            out(f"  【你的备注】{text}")
        mine = describe(state, action)
        ai_action, values = ai_view(state, spec, record["seed"] * 1000 + stats["decisions"])
        stats["decisions"] += 1
        key_mine, key_ai = action_key(state, action), action_key(state, ai_action)
        if key_mine == key_ai:
            stats["same"] += 1
            out(f"  你：{mine}（AI 也会这样）")
            continue
        v_mine, v_ai = values.get(key_mine), values.get(key_ai)
        rating = ""
        if v_mine is not None and v_ai is not None:
            rating = f"；AI 估值：你的 {v_mine:.2f}，它的 {v_ai:.2f}"
            stats["gaps"].append((v_ai - v_mine, state.turn, mine, describe(state, ai_action)))
        out(f"  你：{mine}\n      AI 会：{describe(state, ai_action)}{rating}")
    if turn is not None:
        out(f"  本回合打了对手 {hp_at_start - state.players[1 - human].leader_hp} 点；规划器认为最多 {best_this_turn} 点")
    n = max(stats["decisions"], 1)
    winner = record.get("winner")
    say(f"\n结果：{'你赢了' if winner == human else 'AI 赢了' if winner == 1 - human else '没下完或平局'}；"
        f"你做了 {stats['decisions']} 次决定，AI 选得一样的 {stats['same']} 次（{stats['same'] / n:.0%}）")
    gaps = sorted(stats["gaps"], reverse=True)[:5]
    if gaps:
        say("AI 认为差别最大的几处（它的估值减你的）：")
        for gap, t, mine, theirs in gaps:
            say(f"  第 {t} 回合：你 {mine} / AI {theirs}（{gap:+.2f}）")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("record", help="replay code or path of a saved game")
    parser.add_argument("--ai", default="mcts:200+plan", help="the AI to compare with (see tools.arena)")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    review(records.decode(args.record), args.ai, summary=args.summary)


if __name__ == "__main__":
    main()
