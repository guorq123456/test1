"""Watch the bot pilot an external deck: a few games written out turn by turn in Chinese (the position at the start
of each of the deck's turns, then every action of both sides), for a player to point at the misplays.

The games are deals of league.py (same seeds, both sides mcts:100+plan unless --spec), so each one is a game of
runs/external/dfm-cheap.jsonl. Evaluation only: the external decks never enter search, self-play or training.

    python analysis/deckbuild/blind-test/external/watch.py analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt \
        --deck RUNE --opp bot/T1-SWORD-1 --seat 0 --k 0 --out /tmp/watch.md

Condition: 对手卡表已知（牌序、手牌未知）.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from svsim.cards.pool import POOL  # noqa: E402
from svsim.core.actions import EndTurn  # noqa: E402
from svsim.core.engine import apply, legal_actions, new_game  # noqa: E402
from svsim.tools import deckbuild as DB  # noqa: E402
from svsim.tools.arena import make_agent  # noqa: E402
from svsim.ui.text import describe, render_state  # noqa: E402
import league  # noqa: E402


def play(ids, opp, seed, seat, spec):
    """The game of play_deal for this seat, with every action written down."""
    cards = [None, None]
    cards[seat], cards[1 - seat] = [POOL[i] for i in ids], [POOL[i] for i in opp]
    state = new_game(cards[0], cards[1], seed=seed)
    agents = [None, None]
    agents[seat] = make_agent(spec, 2 * seed + seat)
    agents[1 - seat] = make_agent(spec, 2 * seed + 1 - seat + 7919)
    out, turn, waste = [], None, []
    while not state.over:
        if state.turn != turn and state.phase.name == "MAIN":
            turn = state.turn
            if state.active == seat:
                out += ["", f"### 第 {state.turn} 回合（被测卡组）", "```", render_state(state, seat), "```"]
            else:
                out += ["", f"### 第 {state.turn} 回合（对手）"]
        action = agents[state.active].act(state, legal_actions(state))
        who = "我方" if state.active == seat else "对手"
        if isinstance(action, EndTurn) and state.active == seat:
            waste.append(state.players[seat].pp)
        if state.phase.name == "MAIN":
            out.append(f"- {who}：{describe(state, action)}" +
                       (f"（剩 {state.players[seat].pp} PP）" if isinstance(action, EndTurn) and who == "我方" else ""))
        apply(state, action)
    result = "赢" if state.winner == seat else ("平" if state.winner not in (0, 1) else "输")
    return out, result, waste, ("先手" if state.first == seat else "后手")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ref")
    ap.add_argument("--deck", required=True, help="class of the external deck, e.g. RUNE")
    ap.add_argument("--opp", nargs="+", required=True, help="roster labels")
    ap.add_argument("--seat", type=int, default=0)
    ap.add_argument("--k", type=int, default=0, help="deal number 0-9 of league.py")
    ap.add_argument("--spec", default="mcts:100+plan")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    ref = DB.read_seeds(args.ref)
    roster = DB.read_seeds(str(league.ROSTER))
    i = next(n for n, (l, _) in enumerate(ref) if args.deck in l)
    label, ids = ref[i]
    lines = [f"# bot 操作「{label}」的对局记录", "",
             f"对局条件：对手卡表已知（牌序、手牌未知）；两边都由 {args.spec} 操作；发牌和模拟器互打（league.py）相同。",
             "「我方」是被测卡组。每个我方回合开头是那一刻的局面（我方手牌可见）。"]
    for o in args.opp:
        j = next(n for n, (l, _) in enumerate(roster) if l == o)
        seed = league.SEED + (i * len(roster) + j) * 10 + args.k
        log, result, waste, order = play(ids, roster[j][1], seed, args.seat, args.spec)
        lines += ["", f"## 对 {o}（种子 {seed}，被测卡组{order}）：{result}",
                  f"每回合结束时剩下没用的 PP：{waste}"] + log
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
