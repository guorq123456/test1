"""破魔虫模型只用玩家的对局学（单步 + 整回合，不用自对弈），留一局检验，存到 weights_v3。"""
import sys, shutil
from pathlib import Path
sys.path.insert(0, "/home/user/test1")
import numpy as np
from svsim.learn import data, fit as F
from svsim.learn.model import LinearValue
from svsim.learn.features import names
from svsim.tools.learn import load_records
D = Path("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad")
recs = load_records([str(D / "human_games")])
steps = [data.choices(r, 0, True) for r in recs]
turns = [data.turn_choices(r, 0, True, seed=i) for i, r in enumerate(recs)]
allc = np.vstack([np.asarray(c) for g in steps + turns for _, c in g])
mean, std = F.standardize(allc)
repeat, l2 = 3, float(sys.argv[1]) if len(sys.argv) > 1 else 1e-2
empty = (np.zeros((0, len(mean))), np.zeros(0))
hits = {"step": [0, 0], "turn": [0, 0]}
for k in range(len(recs)):
    train = [p for j, g in enumerate(steps) if j != k for p in g] + [p for j, g in enumerate(turns) if j != k for p in g] * repeat
    w, *_ = F.fit(*empty, train, l2=l2, iters=2000, mean=mean, std=std)
    for name, test in (("step", steps[k]), ("turn", turns[k])):
        if test:
            hits[name][0] += F.top1(w, F.choice_groups(test, mean, std)) * len(test); hits[name][1] += len(test)
print(f"只用玩家对局（l2={l2}）留一局检验：单步命中 {hits['step'][0]/hits['step'][1]:.0%}，整回合命中 {hits['turn'][0]/hits['turn'][1]:.0%}")
w, *_ , rep = F.fit(*empty, [p for g in steps for p in g] + [p for g in turns for p in g] * repeat, l2=l2, iters=3000, mean=mean, std=std)
out = D / "weights_v3"; out.mkdir(exist_ok=True)
model = LinearValue(w.tolist(), mean.tolist(), std.tolist(), True, {"deck": "rhino", "source": "player only", **rep})
model.save(out / "forest.json"); shutil.copy(D / "weights_v2" / "dragon.json", out / "dragon.json")
top = sorted(model.weights_by_name().items(), key=lambda kv: -abs(kv[1] * std[names(True).index(kv[0])]))[:12]
print("影响最大的特征：" + "，".join(f"{k} {v:+.3f}" for k, v in top))
