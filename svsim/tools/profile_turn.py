"""Where v2's time goes in a self-play game (default: the tournament Ramp mirror): own time (tottime) under cProfile
summed by component (module path), per decision."""
import cProfile, pstats, sys, collections, time
sys.path.insert(0, "/home/user/test1")
from svsim.learn.netdata import play
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
pr = cProfile.Profile()
t0 = time.perf_counter()
decisions = 0
pr.enable()
for g in range(N):
    rec = play((g, 424242, "ramp-t", "ramp-t", "v2", 0.0))
    decisions += sum(1 for x in rec["search"] if x is not None) + 0
pr.disable()
wall = time.perf_counter() - t0
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
print(f"{N} 局，{decisions} 个搜索决定，墙钟 {wall:.1f} s（剖析开着，约慢 1.5～2 倍）；剖析内合计 {total:.1f} s")
print("| 组件 | 占比 | 每个决定（ms） |\n|---|---|---|")
for name, t in by.most_common():
    print(f"| {name} | {t / total:.0%} | {1000 * t / max(decisions, 1):.1f} |")
