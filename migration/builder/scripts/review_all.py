"""在你的每个决策点让 AI（mcts:200+plan，假设它操作破魔虫）也选一次，按类型统计分歧。"""
import json, glob, sys
sys.path.insert(0, "/home/user/test1")
from multiprocessing import Pool
from collections import Counter
from svsim.tools import records
from svsim.tools.review import ai_view
from svsim.search.mcts import action_key
from svsim.core.actions import PlayCard, Attack, EndTurn, Evolve, Engage, Fuse, Mulligan, UseBonusPP
from svsim.core.enums import Phase
from svsim.ui.text import describe

def kind(state, a):
    if isinstance(a, EndTurn): return "结束回合"
    if isinstance(a, PlayCard):
        from svsim.cards import unlimited as U
        c = state.in_hand(state.active, a.uid)
        return "出破魔虫" if c.defn == U.KILLER_RHINOCEROACH else "出牌"
    if isinstance(a, Attack): return "攻击"
    if isinstance(a, Evolve): return "进化"
    if isinstance(a, Fuse): return "融合"
    return type(a).__name__

def run(path):
    body = json.load(open(path)); body = body.get("data", body); rec = body["record"]
    out = []
    for n, (state, a) in enumerate(records.steps(rec)):
        if state.active != 0 or state.phase != Phase.MAIN: continue
        s = state.clone()
        ai, values = ai_view(s, "mcts:200+plan", 1000 + n)
        km, ka = action_key(state, a), action_key(state, ai)
        out.append((path.split("/")[-1][:13], state.turn, state.players[0].turns_taken, kind(state, a), kind(state, ai), km == ka,
                    describe(state, a), describe(state, ai), values.get(km), values.get(ka)))
    return out

if __name__ == "__main__":
    files = []
    for f in sorted(glob.glob("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/dbgames2/games/*.json")):
        b = json.load(open(f)); b = b.get("data", b)
        if b.get("finished"): files.append(f)
    with Pool(4) as pool:
        rows = [r for part in pool.map(run, files) for r in part]
    json.dump(rows, open("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/review_rows.json", "w"), ensure_ascii=False)
    same = sum(r[5] for r in rows)
    print(f"你做了 {len(rows)} 次决定，AI 选得一样的 {same} 次（{same/len(rows):.0%}）")
    pairs = Counter((r[3], r[4]) for r in rows if not r[5])
    print("分歧类型（你 → AI）：")
    for (h, a), n in pairs.most_common(10): print(f"  你{h}，AI 想{a}：{n} 次")
    early = [r for r in rows if r[2] <= 6]; late = [r for r in rows if r[2] > 6]
    for name, part in (("前 6 回合", early), ("第 7 回合以后", late)):
        print(f"{name}：{len(part)} 次决定，一致 {sum(r[5] for r in part)/max(1,len(part)):.0%}")
    print("AI 想出破魔虫而你没出的回合（你的回合数）：", sorted(Counter(r[2] for r in rows if r[4] == '出破魔虫' and r[3] != '出破魔虫').items()))
    print("AI 想结束回合而你继续出牌的次数：", sum(1 for r in rows if r[4] == '结束回合' and r[3] != '结束回合'))
