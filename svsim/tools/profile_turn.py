"""Where v2's time goes in a self-play game (default: the tournament Ramp mirror): own time (tottime) under cProfile
summed by component (module path), per decision.

    python svsim/tools/profile_turn.py [GAMES] [DECK OPPONENT [--side]]

With --side only DECK's moves are profiled and counted (elf-t's share of an elf-t vs ramp-t game)."""
import cProfile, pstats, sys, collections, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from svsim.learn.netdata import play
from svsim.tools import arena
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
DECK, OPP = (sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else ("ramp-t", "ramp-t")
SIDE = "--side" in sys.argv
pr = cProfile.Profile()
counts = {"decisions": 0, "seconds": 0.0}
make = arena.make_agent


def profiled(spec, seed):                          # profile the moves of DECK's player only (or every move)
    agent = make(spec, seed)
    act = agent.act

    def timed(state, legal):
        if SIDE and state.players[state.active].deck_name != DECK:
            return act(state, legal)
        t = time.perf_counter()
        pr.enable()
        try:
            return act(state, legal)
        finally:
            pr.disable()
            counts["decisions"] += 1
            counts["seconds"] += time.perf_counter() - t
    agent.act = timed
    return agent


arena.make_agent = profiled
for g in range(N):
    play((g, 424242, DECK, OPP, "v2", 0.0))
decisions, wall = counts["decisions"], counts["seconds"]
st = pstats.Stats(pr)
GROUPS = [("斩杀检查与规划器", ("search/lethal.py", "agents/lethal_agent.py", "search/combo.py", "search/planner", "search/plan", "search/race.py")),
          ("确定化（重发看不见的牌）", ("search/view.py", "core/view.py")),
          ("特征抽取", ("learn/features.py", "learn/payoff.py", "learn/roles.py", "learn/encode.py")),
          ("评分（线性模型、回退评估）", ("learn/model.py", "learn/phased.py", "search/evaluate.py", "learn/net.py")),
          ("树操作（选择、展开、回传）", ("search/mcts.py", "agents/mcts_agent.py")),
          ("规则推进（引擎、卡牌脚本）", ("svsim/core/", "svsim/cards/")),
          ]
by = collections.Counter()
total = 0.0
def group(path):
    for name, keys in GROUPS:
        if any(k in path for k in keys):
            return name
    return None

for (path, line, fn), (cc, nc, tt, ct, callers) in st.stats.items():
    total += tt
    g = group(path)
    if g is None and (path == "~" or path.startswith("<") or path.endswith("random.py") or path.endswith("copy.py")) and callers:   # a builtin: charge it to its callers
        share = sum(v[2] for v in callers.values()) or 1.0
        for (cpath, _, _), v in callers.items():
            by[group(cpath) or "其他（记录、其余）"] += tt * v[2] / share
    else:
        by[g or "其他（记录、其余）"] += tt
print(f"{N} 局 {DECK} 对 {OPP}，{'只算 ' + DECK + ' 一方' if SIDE else '两方'}的 {decisions} 步（act 调用），墙钟 {wall:.1f} s（剖析开着，约慢 1.5～2 倍）；剖析内合计 {total:.1f} s")
print("| 组件 | 占比 | 每个决定（ms） |\n|---|---|---|")
for name, t in by.most_common():
    print(f"| {name} | {t / total:.0%} | {1000 * t / max(decisions, 1):.1f} |")
