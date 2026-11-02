import sys, json
sys.path.insert(0, "/home/user/test1")
from svsim.tools import records
exec(open("det_play2.py").read().split("trace = []")[0].split("from svsim.ui import session as S")[1])
rec = json.load(open("det_record.json")); orig = json.load(open("t_orig.json"))
for i, (st, a) in enumerate(records.steps(rec)):
    f = fp(st)
    if f != orig[i][1]:
        print("第", i, "步之前局面不同；上一步动作:", orig[i-1][0])
        A, B = json.loads(orig[i][1]), json.loads(f)
        for n, p, q in zip(["牌组末尾", "手牌", "场上", "血量", "PP"], A, B):
            if p != q: print(" ", n, "\n   原局:", p, "\n   重放:", q)
        break
else: print("全部相同")
