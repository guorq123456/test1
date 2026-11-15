"""Watch the hand-set cheap bot (mcts:100+plan, the deck search's ruler) pilot a tournament combo elf list against the
bot's own decks: every action written in Chinese + per-turn counts (cards played, PP left). Evaluation only; the
external list never enters search/self-play/training. Condition: 对手卡表已知（牌序、手牌未知）.
usage: watch_elf.py REF.txt LABEL --opp bot/T1-SWORD-1 ... --base 87220000 --out X.md
"""
import argparse, sys, json
from multiprocessing import Pool
from pathlib import Path as _P
ROOT = str(_P(__file__).resolve().parents[5])
sys.path.insert(0, ROOT)
import svsim.tools.arena  # noqa
from svsim.cards.pool import POOL
from svsim.core.actions import EndTurn, PlayCard, Evolve, Attack
from svsim.core.engine import apply, legal_actions, new_game
from svsim.tools import deckbuild as DB
from svsim.tools.arena import make_agent
from svsim.ui.text import describe, render_state
BOT = ROOT + '/analysis/pilot/fields/bot-frozen7.txt'
def play(job):
    ids, opp, seed, seat, spec = job
    cards = [None, None]
    cards[seat], cards[1 - seat] = [POOL[i] for i in ids], [POOL[i] for i in opp]
    state = new_game(cards[0], cards[1], seed=seed)
    agents = [None, None]
    agents[seat] = make_agent(spec, 2 * seed + seat)
    agents[1 - seat] = make_agent(spec, 2 * seed + 1 - seat + 7919)
    out, turn, stats = [], None, []
    cur = None
    while not state.over:
        if state.turn != turn and state.phase.name == "MAIN":
            turn = state.turn
            if state.active == seat:
                out += ["", f"### 第 {state.turn} 回合（连击精灵）", "```", render_state(state, seat), "```"]
                cur = {"turn": state.turn, "played": 0, "evolved": 0, "attacks_face": 0, "pp_left": None, "cards": []}
                stats.append(cur)
            else:
                out += ["", f"### 第 {state.turn} 回合（对手）"]
        action = agents[state.active].act(state, legal_actions(state))
        who = "精灵" if state.active == seat else "对手"
        if state.phase.name == "MAIN":
            if state.active == seat and cur is not None:
                if isinstance(action, PlayCard):
                    cur["played"] += 1; cur["cards"].append(describe(state, action))
                elif isinstance(action, Evolve): cur["evolved"] += 1
                elif isinstance(action, EndTurn): cur["pp_left"] = state.players[seat].pp
            out.append(f"- {who}：{describe(state, action)}" +
                       (f"（剩 {state.players[seat].pp} PP）" if isinstance(action, EndTurn) and who == "精灵" else ""))
        apply(state, action)
    res = "赢" if state.winner == seat else ("平" if state.winner not in (0, 1) else "输")
    return opp, seed, seat, res, ("先手" if state.first == seat else "后手"), out, stats, state.turn
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('ref'); ap.add_argument('label')
    ap.add_argument('--opp', nargs='+', required=True); ap.add_argument('--base', type=int, default=87220000)
    ap.add_argument('--spec', default='mcts:100+plan'); ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--games', type=int, default=2, help='per opponent (seats alternate)'); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    ref = dict(DB.read_seeds(a.ref)); bot = dict(DB.read_seeds(BOT)); ids = ref[a.label]
    jobs = [(ids, bot[o], a.base + 100 * j + g, g % 2, a.spec) for j, o in enumerate(a.opp) for g in range(a.games)]
    with Pool(a.workers) as pool: res = pool.map(play, jobs)
    lines = [f"# 手写 bot（{a.spec}）打比赛连击精灵 {a.label} 的对局", "", "条件：对手卡表已知（牌序、手牌未知）；只用于观察，比赛卡表不进训练。", ""]
    allstats = []
    for opp, seed, seat, r, first, out, stats, nturn in res:
        lines += [f"## 对手 {opp}，种子 {seed}，{first}，结果：{r}，共 {nturn} 回合", ""]
        lines += ["| 回合 | 出牌数 | 进化 | 剩 PP | 出的牌 |", "|---|---|---|---|---|"]
        for s in stats:
            lines.append(f"| {s['turn']} | {s['played']} | {s['evolved']} | {s['pp_left']} | {'；'.join(s['cards'])[:160]} |")
        lines += [""] + out + [""]
        allstats.append({"opp": opp, "seed": seed, "seat": seat, "result": r, "first": first, "turns": nturn, "stats": stats})
    open(a.out, 'w', encoding='utf-8').write("\n".join(lines))
    json.dump(allstats, open(a.out + '.json', 'w', encoding='utf-8'), ensure_ascii=False)
    # summary
    for s in allstats:
        combo3 = sum(1 for t in s['stats'] if t['played'] >= 3)
        waste = sum((t['pp_left'] or 0) for t in s['stats'])
        print(s['opp'], s['seed'], s['first'], s['result'], f"回合 {s['turns']}", f"≥3张的回合 {combo3}/{len(s['stats'])}", f"剩PP合计 {waste}")
if __name__ == '__main__': main()
