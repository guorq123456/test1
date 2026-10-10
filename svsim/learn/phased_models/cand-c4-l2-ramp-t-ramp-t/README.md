# 候选 C4「L2 1e-4」：ramp-t-ramp-t（没装）

组合 ramp-t-ramp-t（我方-对方），只用我方一侧的局面。底 = cand-c3-hpphase-ramp-t-ramp-t，即现装（a6fdf0a，C3）：同数据、同切分、同特征集 `--features hand,hpphase`，只把拟合的 L2 从 1e-3 改成 1e-4。单调约束、2500 次迭代、STOCK 置零、版本 2 线性、`--hold-out-every 11` 照旧。架构线 2026-10-08 17:36Z 布置。留出只作参考，门才算数。

- 数据（同底）：s200.jsonl，解压后 sha256 `c7fd49577934bd9f38d9818336ccac04f8733724d7fbe4d379511da1d7bff123`；同 cand-c2-hand-ramp 的那份。
- 拟合：`python -m svsim.learn.phased --games s200.jsonl --matchup ramp-t-ramp-t --hold-out-every 11 --features hand,hpphase --l2 1e-4 --out <本目录>`（代码 3feae70）。

留出局（400 局，行号 % 11 == 0）上的 log loss，候选 − 底的 95% 区间来自按局重抽 2000 次：

| 时刻 | 点数 | C4 | 底 | C4 − 底（95%） |
|---|---|---|---|---|
| ended | 6735 | 0.5786 | 0.5809 | -0.0023（-0.0048～+0.0000） |
| act | 23645 | 0.5789 | 0.5810 | -0.0021（-0.0041～-0.0002） |

文件 sha256：

    49b044fc3e8b33b67df30b8082d4a717cdc571b8241b4b4e81f48ccb641cc1a6  ramp-t-ramp-t-act.json
    e1d86f072532eaa54bd2f129d4fa1f7cb3ef43ebff12fa00bb6e500e5d88f67f  ramp-t-ramp-t-ended.json
