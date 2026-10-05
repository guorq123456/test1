"""Play against the AI in the terminal (Chinese interface).

    python -m svsim.tools.play                         # you: Pirate Sword, AI: Ramp Dragon
    python -m svsim.tools.play --you ramp --ai mcts:1000
    python -m svsim.tools.play --you "<deck hash>" --opponent pirate
    python -m svsim.tools.play --you rhino --ai mcts:400+plan   # Rhinoceroach Forest (Unlimited) vs Ramp

On your turn, type the number of an action, or:
    e   end the turn          h   ask the AI what it would do
    l   look for lethal       q   quit
    # <text>   a note on this position, saved with the game (why you play as you do)
Decks: pirate, ramp, rhino, or an official deck hash. AI: any agent from
tools.arena (default mcts:400, ISMCTS plus lethal search). "l" asks the
resource-flow planner first (with the quick count for combo finishers), then
exact search.

Every game is saved to replays/ (decks, seed and every action) and ends with a
replay code ("回放码") that can be pasted anywhere; tools.review replays it
and compares your choices with the AI's.
"""
import argparse
import random

from svsim.cards import decks, library
from svsim.core.actions import EndTurn, Mulligan
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Phase
from svsim.search.combo import solve
from svsim.search.lethal import find_lethal
from svsim.search.mcts import ISMCTS
from svsim.tools import records
from svsim.tools.arena import make_agent
from svsim.ui.text import card_line, describe, describe_line, render_state

assert library.__all__


def load_deck(name: str) -> list:
    if name == "pirate":
        return decks.build(decks.PIRATE_SWORD)
    if name == "ramp":
        return decks.build(decks.RAMP_DRAGON)
    if name == "rhino":
        return decks.build(decks.RHINO_FOREST)
    return decks.from_hash(name)


def run(you_deck, ai_deck, ai_spec: str = "mcts:400", seed: int | None = None,
        you_first: bool | None = None, ask=input, say=print, record_to: str | None = "replays") -> int | None:
    """Play one game; `ask` and `say` are the input and output (replaceable for tests).
    Returns the winner (0 = you, 1 = the AI) or None if you quit. The game is saved
    to the `record_to` folder (None: not saved) and its replay code is shown."""
    seed = random.randrange(10 ** 9) if seed is None else seed
    first = None if you_first is None else (0 if you_first else 1)
    state = new_game(you_deck, ai_deck, seed=seed, first=first)
    record = records.new_record(you_deck, ai_deck, seed, state.first, ai_spec)
    ai = make_agent(ai_spec, seed)
    say(f"对局种子 {seed}；你{'先手' if state.first == 0 else '后手'}。")

    def play(action):
        records.add(record, action)
        apply(state, action)

    def finish(winner):
        record["winner"] = winner
        if record_to is not None:
            path = records.save(record, record_to)
            say(f"对局记录已保存：{path}")
        say("回放码（复制整段发给别人就能复盘）：\n" + records.encode(record))
        return winner

    while not state.over:
        if state.active == 1:
            action = ai.act(state, legal_actions(state))
            if state.phase == Phase.MAIN:
                say(f"  AI：{describe(state, action)}")
            play(action)
            continue
        if state.phase == Phase.MULLIGAN:
            hand = state.players[0].hand
            say("起手：" + "；".join(f"{i}. {card_line(state, c, in_hand=True)}" for i, c in enumerate(hand)))
            reply = ask("要换掉哪些牌？输入编号，用空格分开，直接回车不换：").split()
            picks = tuple(sorted({int(x) for x in reply if x.isdigit() and int(x) < len(hand)}))
            play(Mulligan(picks))
            continue
        actions = legal_actions(state)
        say("\n" + render_state(state, viewer=0))
        for i, a in enumerate(actions):
            say(f"  {i}. {describe(state, a)}")
        reply = ask("你的选择（编号 / e 结束回合 / h 提示 / l 查斩杀 / # 备注 / q 退出）：").strip()
        if reply.startswith("#"):
            record.setdefault("notes", []).append({"at": len(record["actions"]), "text": reply[1:].strip()})
            say("  备注已记下。")
            continue
        reply = reply.lower()
        if reply == "q":
            return finish(None)
        if reply == "h":
            say("  AI 会这样走：" + describe(state, ISMCTS(iterations=800).choose(state)))
            continue
        if reply == "l":
            quick = solve(state, search_nodes=0)
            if not quick.estimate.pattern.startswith("没有"):     # a combo finisher in hand: count first
                hp = state.players[1 - state.active].leader_hp
                say("  速算：" + quick.estimate.text(hp).replace("\n", "\n  "))
            if quick.sure:
                say("  有必杀：" + " → ".join(describe_line(state, quick.line)))
                continue
            r = find_lethal(state)
            if r.sure:
                say("  有必杀：" + " → ".join(describe_line(state, r.line)))
            elif r.probability > 0:
                say(f"  没有必杀；靠运气的斩杀成功率约 {r.probability:.0%}：{describe(state, r.line[0])}")
            else:
                say("  这回合杀不了。" + ("" if r.complete else "（没搜完）"))
            continue
        if reply == "e":
            play(EndTurn())
            continue
        if reply.isdigit() and int(reply) < len(actions):
            play(actions[int(reply)])
            continue
        say("  没看懂，再输一次。")
    say("\n" + render_state(state, viewer=0))
    say("你赢了！" if state.winner == 0 else "AI 赢了。" if state.winner == 1 else "平局。")
    return finish(state.winner)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--you", default="pirate", help="your deck: pirate, ramp, rhino or a deck hash")
    parser.add_argument("--opponent", default=None, help="the AI's deck (default: the other one)")
    parser.add_argument("--ai", default="mcts:400")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--first", choices=("you", "ai"), help="who goes first (default: random)")
    parser.add_argument("--no-record", action="store_true", help="don't save the game to replays/")
    args = parser.parse_args()
    opponent = args.opponent or ("pirate" if args.you == "ramp" else "ramp")
    run(load_deck(args.you), load_deck(opponent), args.ai, args.seed,
        None if args.first is None else args.first == "you", record_to=None if args.no_record else "replays")


if __name__ == "__main__":
    main()
