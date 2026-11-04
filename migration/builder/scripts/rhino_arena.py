"""按卡组拆分的对战：谁操作破魔虫、谁赢、找到几次斩杀、斩杀时是第几回合。"""
import sys, pickle, time
sys.path.insert(0, "/home/user/test1")
from multiprocessing import Pool
from collections import defaultdict
from svsim.tools.arena import play_one

def run(job):
    a, b, g, kind, seed = job
    t = time.perf_counter()
    a_, b_, winner, clock = play_one(job)
    specs = (a, b) if (g // 2) % 2 == 0 else (b, a)
    rhino_spec = specs[0] if g % 2 == 0 else specs[1]
    return rhino_spec, winner, clock, time.perf_counter() - t

if __name__ == "__main__":
    a, b, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    jobs = [(a, b, g, "rhino", 1) for g in range(n)]
    with Pool(4) as pool:
        res = pool.map(run, jobs)
    pickle.dump(res, open(f"rhino_arena_{a}_{b}.pkl".replace(":", "-"), "wb"))
    for spec in (a, b):
        games = [r for r in res if r[0] == spec]
        wins = sum(1 for r in games if r[1] == spec)
        p = wins / len(games); m = 1.96 * (p * (1 - p) / len(games)) ** .5
        print(f"{spec} 操作破魔虫：{wins}/{len(games)} 胜，胜率 {p:.0%} ± {m:.0%}")
    for spec in (a, b):
        secs = sum(r[2][spec][0] for r in res); dec = sum(r[2][spec][1] for r in res); leth = sum(r[2][spec][2] for r in res)
        print(f"{spec}：每步 {secs / dec * 1000:.0f} 毫秒，共找到 {leth} 次必杀")
