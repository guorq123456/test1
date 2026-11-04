# 候选 C3 修订版「HP × 回合段」（hpphase）：elf-t-ramp-t（没装）

组合 elf-t-ramp-t（我方-对方），只用我方一侧的局面。`--features hpphase`：在装机向量之上只加 hpphase（这格没装 C2）。hpphase 4 维（双方领袖 HP × 被评分方第 1～4 / 5～7 回合）的定义见 learn.features 和 analysis/c3-threat/README.md 第六节（3e6b4f2），代码 729630a。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：elf-t_ramp-t.jsonl，解压后 sha256 `4cccb6a46e885bc2bc45d3187f380e4a3a95c86418df7d2aec7df4698dc8d27b`；同 cand-bprime-elf-t-ramp-t 的那份。
- 拟合：`python -m svsim.learn.phased --games elf-t_ramp-t.jsonl --matchup elf-t-ramp-t --hold-out-every 11 --features hpphase --out <本目录>`。
- 对照：cand-bprime-elf-t-ramp-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1360 | 0.5945 | 0.5930 | +0.0014（-0.0033～+0.0057） | 0.5887 |
| act | 6463 | 0.5935 | 0.5937 | -0.0002（-0.0022～+0.0019） | 0.5894 |

文件 sha256：

    d8e19b7a3261581558fe8cd781b1173c4e939a17fe09963df65b331dc245d91f  elf-t-ramp-t-act.json
    e4af93a06b50447d3864d2d4e655eafb0a09004f8db5835e24943153fd2c5e03  elf-t-ramp-t-ended.json
