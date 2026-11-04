import json, glob, statistics as st
from svsim.tools import records
from svsim.core.actions import EndTurn
from svsim.core.enums import Phase
D = "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad"
hand, waste, board = [], [], []
files = {}
for f in sorted(glob.glob(D + "/human_games/*.json")) + sorted(glob.glob(D + "/db_latest/games/*.json")):
    files[f.rsplit("/", 1)[-1]] = f
games = 0
for f in files.values():
    d = json.load(open(f)); d = d.get("data", d); rec = d["record"]
    if len(rec["actions"]) < 20: continue
    games += 1
    for s, a in records.steps(rec):
        if s.active == 0 and s.phase == Phase.MAIN and isinstance(a, EndTurn):
            p = s.players[0]
            if 4 <= p.turns_taken <= 10:
                hand.append(len(p.hand)); board.append(len(p.followers))
            if 3 <= p.turns_taken <= 10:
                waste.append(p.pp)
print(f"玩家（破魔虫）第4～10回合结束时：手牌 {st.mean(hand):.2f}，随从数 {st.mean(board):.2f}；第3～10回合浪费PP {st.mean(waste):.2f}（{games} 局，{len(hand)} 个回合）")
