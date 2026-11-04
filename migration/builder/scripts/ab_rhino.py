import sys
sys.argv = sys.argv[:1] + ["100"]
import importlib.util
spec = importlib.util.spec_from_file_location("ab", "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/ab_center.py")
ab = importlib.util.module_from_spec(spec); spec.loader.exec_module(ab)
ab.MATCHES.clear()
ab.MATCHES["破魔虫(新) vs 手写跳费龙 mcts:200+plan(旧)"] = (("rhino", "new", 200, False), ("ramp", "old", 200, False))
ab.MATCHES["破魔虫(旧) vs 手写跳费龙 mcts:200+plan(旧)"] = (("rhino", "old", 200, False), ("ramp", "old", 200, False))
from collections import defaultdict
from multiprocessing import Pool
if __name__ == "__main__":
    jobs = [(name, a, b, g) for name, (a, b) in ab.MATCHES.items() for g in range(100)]
    score = defaultdict(lambda: [0.0, 0])
    with Pool(4) as pool:
        for name, x in pool.imap_unordered(ab.play, jobs):
            score[name][0] += x; score[name][1] += 1
    for name, (w, k) in score.items():
        p = w / k
        print(f"{name}: {w:g}/{k} = {p:.0%} ± {1.96 * (p * (1 - p) / k) ** 0.5:.0%}", flush=True)
