"""Compare ways of playing each of your turns by what they do to winning (Chinese output).

    python -m svsim.tools.impact replays/20261005-201500-123.json
    python -m svsim.tools.impact "<回放码>" --turn 13 --samples 8

For each of your turns: your turn as played, the AI's way of playing it from
the same start, and ending the turn at once, side by side on the dimensions of
search.impact (this turn; the opponent's answer, played by their AI on
reshuffled hands; both race clocks at your next turn; the evaluation's win
probability). The AI plays its turn with the cards drawn as they really came,
like you did; the futures are sampled the same way for all three.
"""
from __future__ import annotations

import argparse

from svsim.cards import library
from svsim.core.actions import EndTurn, PlayCard
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Phase
from svsim.search import impact
from svsim.tools import records
from svsim.tools.arena import make_agent
from svsim.ui.text import render_state

assert library.__all__


def turns(record: dict, human: int = 0) -> list:
    """[(start of the turn, position before ending it, cards played)] for `human`'s turns."""
    out, start, played = [], None, 0
    for state, action in records.steps(record):
        if state.phase != Phase.MAIN or state.active != human:
            continue
        if start is None or start.turn != state.turn:
            start, played = state.clone(), 0
        if isinstance(action, PlayCard):
            played += 1
        if isinstance(action, EndTurn):
            out.append((start, state.clone(), played))
    return out


def ai_turn(start, spec: str, seed: int) -> tuple:
    """The position before `spec` would end the turn from `start`, and the cards it played."""
    agent = make_agent(spec, seed)
    s, played, me = start.clone(), 0, start.active
    for _ in range(100):
        if s.over or s.active != me:
            break
        action = agent.act(s, legal_actions(s))
        if isinstance(action, EndTurn):
            break
        played += isinstance(action, PlayCard)
        apply(s, action)
    return s, played


def compare(start, end, played: int, ai: str = "mcts:200+plan", opponent: str = "mcts:50+plan+learned",
            samples: int = 6, seed: int = 0) -> list:
    ai_end, ai_played = ai_turn(start, ai, seed)
    if ai_end.over:
        return []
    return impact.assess(start, [end, ai_end, start], ["你的打法", "AI的打法", "直接结束"],
                         [played, ai_played, 0], samples=samples, seed=seed, opponent=opponent)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("record", help="replay code or path of a saved game")
    parser.add_argument("--turn", type=int, help="only this turn (the game's turn number)")
    parser.add_argument("--ai", default="mcts:200+plan", help="the AI whose turn to compare (see tools.arena)")
    parser.add_argument("--opponent", default="mcts:50+plan+learned", help="the AI that plays the answers")
    parser.add_argument("--samples", type=int, default=6)
    args = parser.parse_args()
    record = records.decode(args.record)
    for k, (start, end, played) in enumerate(turns(record)):
        if args.turn is not None and start.turn != args.turn:
            continue
        print(f"\n===== 第 {start.turn} 回合 =====")
        print(render_state(start, viewer=0))
        if end.over:
            print("（这回合你赢了）")
            continue
        out = compare(start, end, played, args.ai, args.opponent, args.samples, seed=k)
        print(impact.table(out) if out else "（AI 这回合能直接斩杀）")


if __name__ == "__main__":
    main()
