import sys, cProfile, pstats
sys.path.insert(0, "/home/user/test1")
exec(open("threat_cost.py").read().split("ref = {}")[0])
from svsim.search import combo as C
for s in states: C.next_turn_damage(s, 0, 300)    # warm caches
def run():
    for _ in range(3):
        C._NEXT_TURN.clear()
        for s in states: C.next_turn_damage(s, 0, 300)
cProfile.run("run()", "tp.out")
pstats.Stats("tp.out").sort_stats("cumulative").print_stats(18)
