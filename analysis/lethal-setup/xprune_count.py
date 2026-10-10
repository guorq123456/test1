"""The +xprune gate's description (README-xprune.md): in the companion replay's games (lethal2_games.py play), the
share of decisions with a discard choice among the legal moves (search.xprune.discards) and with pruning active
(XPrune(3, 3, "cost") vetoes a legal move at the root), A and B apart; and among the decisions with pruning active,
how often the move the side chose is one the pruning leaves out (README-xprune-max.md: for B, how often its own
choice would have been cut; for A, a check, the search never picks a vetoed move at the root).
Condition: the opponent's deck list is known (order and hand not).

    python -m svsim.tools.host xprune_count records.jsonl --workers 3 --out count.txt
"""
import argparse
import json
from multiprocessing import Pool


def _game(g):
    from svsim.core.actions import Engage, Evolve, PlayCard, from_dict
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.core.enums import Phase
    from svsim.search.xprune import XPrune, discards
    import lethal2_games as L
    mine, theirs = L._cards(g["deck"], g["opponent"])
    a = g["a_seat"]
    cards = [None, None]
    cards[a], cards[1 - a] = mine, theirs
    st = new_game(cards[0], cards[1], seed=g["seed"])
    veto = XPrune(3, 3, "cost")
    out = {"A": [0, 0, 0, 0], "B": [0, 0, 0, 0]}    # decisions with 2+ moves, a discard choice, pruning active, chosen cut
    for data in g["actions"]:
        if st.over:
            break
        if st.phase == Phase.MAIN:
            legal = legal_actions(st)
            if len(legal) >= 2:
                side = "A" if st.active == a else "B"
                out[side][0] += 1
                hand = {c.uid for c in st.players[st.active].hand}
                disc = False
                for act in legal:
                    if isinstance(act, (PlayCard, Evolve, Engage)) and act.targets:
                        targeted = [t for t in act.targets if t in hand]
                        if targeted and discards(st, act, targeted):
                            disc = True
                            break
                if disc:
                    out[side][1] += 1
                    if any(veto(st, act) for act in legal):
                        out[side][2] += 1
                        if veto(st, from_dict(data)):
                            out[side][3] += 1
        apply(st, from_dict(data))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    games = [json.loads(x) for x in open(args.records, encoding="utf-8") if x.strip()]
    with Pool(args.workers) as pool:
        res = pool.map(_game, games)
    lines = ["条件：对手卡表已知（牌序、手牌未知）。+xprune 门里含弃牌选择的决策（README-xprune.md 的加报）\n",
             f"- 重打的 {len(games)} 局", "", "| 方 | 合法走法 ≥ 2 的决策 | 含弃牌选择 | 剪枝起作用 | 至少出现一次弃牌选择的局 |",
             "|---|---|---|---|---|"]
    cut = ["", "| 方 | 剪枝起作用的决策 | 所选那步正是被剪掉的 |", "|---|---|---|"]
    for side in ("A", "B"):
        n = sum(r[side][0] for r in res)
        d = sum(r[side][1] for r in res)
        c = sum(r[side][2] for r in res)
        g = sum(r[side][1] > 0 for r in res)
        lines.append(f"| {side} | {n} | {d}（{d / n:.2%}） | {c}（{c / n:.2%}） | {g} / {len(res)}（{g / len(res):.1%}） |")
        x = sum(r[side][3] for r in res)
        cut.append(f"| {side} | {c} | {x}（{x / c:.1%}） |")
    text = "\n".join(lines + cut)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
