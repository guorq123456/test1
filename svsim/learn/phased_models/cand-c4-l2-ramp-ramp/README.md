# 候选 C4「L2 1e-4」：原版跳费龙镜像 ramp-ramp（没装）

组合 ramp-ramp（原版 `ramp` 镜像），不加特征（同现装原版 ramp-ramp，无 extras），只把拟合的 L2 从 1e-3 改成 1e-4。单调约束、2500 次迭代、STOCK 置零、版本 2 线性、`--hold-out-every 11` 照旧。架构线 2026-10-08 18:00Z 布置（C4 第 1 格跳费龙镜像门不过后，只再测这一格）。留出只作参考，门才算数。

- 数据：同 ../cand-bprime-ramp-ramp：拟现装原版模型的那 2000 局（3e58415），data/pairings-20261008 分支 9cd97b6 的 `ramp-t_ramp-t_original-3e58415.jsonl.gz`，解压后 sha256 `87c8a60d0887a0f5c5fdd1ddd0723e262023433f7253de7b989b6ee00b3045b8`。
- 拟合：`python -m svsim.learn.phased --games games.jsonl --matchup ramp-ramp --hold-out-every 11 --l2 1e-4 --out <本目录>`（代码 3feae70）。
- 对照：cand-bprime-ramp-ramp（同数据、同留出、同特征，L2 1e-3）。现装是全量拟合的，见过留出局，只作参考。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次：

| 时刻 | 点数 | C4 | 对照（B′） | C4 − B′（95%） | 现装* |
|---|---|---|---|---|---|
| ended | 3175 | 0.5985 | 0.6009 | -0.0024（-0.0057～+0.0009） | 0.5978 |
| act | 10615 | 0.5977 | 0.5992 | -0.0015（-0.0042～+0.0015） | 0.5965 |

文件 sha256：

    30e02ec9715ca94c6c0aa385863f989c34f376c4be9ccc5115b317beab8bc064  ramp-ramp-act.json
    48adf8b6dab5aa7c178010e1dddca03ddccfe46875ea8a58a6e0c8c2298eb8c7  ramp-ramp-ended.json
