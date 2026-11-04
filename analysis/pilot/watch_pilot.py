"""Games of the trained DFM 三轴土 pilot (round 2: value net g5 + prior 2, N 30) written out turn by turn in Chinese,
for Salem to point at the misplays (his replay review, 2026-10-31). The pilot plays dfm/RUNE-ユーリ; the opponent is
one of the bot's decks at mcts:100+plan. Only lost games are written. Measurement only; the external deck and these
games never enter search, self-play or training. Condition: 对手卡表已知（牌序、手牌未知）.

    python analysis/pilot/watch_pilot.py --opp bot/T1-SWORD-1 bot/T1-ABYSS-1 --losses 2 --out /tmp/watch.md
"""
import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import svsim.tools.arena  # noqa: E402,F401
from svsim.cards import deckcode  # noqa: E402
from svsim.cards.pool import POOL  # noqa: E402
from svsim.core.actions import EndTurn  # noqa: E402
from svsim.core.engine import apply, legal_actions, new_game  # noqa: E402
from svsim.tools.arena import make_agent  # noqa: E402
from svsim.ui.text import describe, render_state  # noqa: E402

FIELD = ROOT / "analysis/pilot/fields/dfm-yuri-vs-bot6.txt"
HERO = "dfm/RUNE-ユーリ"
M = "analysis/scaling/models"
SPEC = (f"mcts:30+plan+setnet={M}/net-pilot-rune-dfm-g5.npz+netmid+netany"
        f"+puct={M}/prior2-pilot-rune-dfm-ft-t05.npz:2:1")
NAMES = {"FOREST": "精灵", "SWORD": "皇家护卫", "RUNE": "巫师", "DRAGON": "龙族", "ABYSS": "梦魇", "HAVEN": "主教",
         "PORTAL": "超越者"}


def decks() -> dict:
    out = {}
    for line in FIELD.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            label, _, code = line.rpartition("|")
            out[label.strip()] = deckcode.decode_deck(code.strip())[2]
    return out


def play(job):
    opp, seed, seat = job
    d = decks()
    cards = [None, None]
    cards[seat], cards[1 - seat] = [POOL[i] for i in d[HERO]], [POOL[i] for i in d[opp]]
    state = new_game(cards[0], cards[1], seed=seed)
    agents = [None, None]
    agents[seat] = make_agent(SPEC, 2 * seed + seat)
    agents[1 - seat] = make_agent("mcts:100+plan", 2 * seed + 1 - seat + 7919)
    out, turn = [], None
    while not state.over:
        if state.turn != turn and state.phase.name == "MAIN":
            turn = state.turn
            if state.active == seat:
                out += ["", f"### 第 {state.turn} 回合（三轴土）", "```", render_state(state, seat), "```"]
            else:
                out += ["", f"### 第 {state.turn} 回合（对手）"]
        action = agents[state.active].act(state, legal_actions(state))
        if state.phase.name == "MAIN":
            who = "三轴土" if state.active == seat else "对手"
            out.append(f"- {who}：{describe(state, action)}" +
                       (f"（剩 {state.players[seat].pp} PP）" if isinstance(action, EndTurn) and state.active == seat else ""))
        apply(state, action)
    return opp, seed, seat, state.winner == seat, ("先手" if state.first == seat else "后手"), out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--opp", nargs="+", required=True)
    ap.add_argument("--losses", type=int, default=2)
    ap.add_argument("--games", type=int, default=10, help="games tried per opponent")
    ap.add_argument("--base", type=int, default=86047000)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    jobs = [(o, args.base + 100 * j + g, g % 2) for j, o in enumerate(args.opp) for g in range(args.games)]
    with Pool(args.workers) as pool:
        res = pool.map(play, jobs)
    lines = ["# 三轴土（练过两轮的 bot 在打）输掉的对局", "",
             "对局条件：对手卡表已知（牌序、手牌未知）。三轴土一方：评估网络第五代 + 「先试哪一步」第二版，每步搜索 30 次；"
             "对手：bot 自己的卡组，没训练的 bot（每步 100 次）。每个三轴土回合开头是那一刻的局面（三轴土的手牌可见）。"]
    for o in args.opp:
        mine = [r for r in res if r[0] == o]
        won = sum(r[3] for r in mine)
        cls = NAMES.get(o.split("-")[1], o)
        lines += ["", f"## 对 {cls}（{o}）：试了 {len(mine)} 局，赢 {won} 局；下面是输的前 {args.losses} 局"]
        for opp, seed, seat, win, order, log in [r for r in mine if not r[3]][:args.losses]:
            lines += ["", f"### 一局（种子 {seed}，三轴土{order}）：输"] + log
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.out, [(o, sum(r[3] for r in res if r[0] == o)) for o in args.opp])


if __name__ == "__main__":
    main()
