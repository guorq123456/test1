# 候选 C3 修订版「HP × 回合段」（hpphase）：ramp-t-elf-t（没装）

组合 ramp-t-elf-t（我方-对方），只用我方一侧的局面。`--features hpphase`：在装机向量之上只加 hpphase（这格没装 C2）。hpphase 4 维（双方领袖 HP × 被评分方第 1～4 / 5～7 回合）的定义见 learn.features 和 analysis/c3-threat/README.md 第六节（3e6b4f2），代码 729630a。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：elf-t_ramp-t.jsonl，解压后 sha256 `4cccb6a46e885bc2bc45d3187f380e4a3a95c86418df7d2aec7df4698dc8d27b`；同 cand-bprime-ramp-t-elf-t 的那份。
- 拟合：`python -m svsim.learn.phased --games elf-t_ramp-t.jsonl --matchup ramp-t-elf-t --hold-out-every 11 --features hpphase --out <本目录>`。
- 对照：cand-bprime-ramp-t-elf-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1369 | 0.6042 | 0.6053 | -0.0011（-0.0034～+0.0011） | 0.5983 |
| act | 4845 | 0.5937 | 0.5931 | +0.0005（-0.0034～+0.0043） | 0.5859 |

文件 sha256：

    335b82847be5ee048deac3eca60600e33cb4200fcd4552bf84afad6461d5ad20  ramp-t-elf-t-act.json
    67b9e4da6cc02f75f565257a01814a7c6a05a84ac83746f823a66e4e1c3d1850  ramp-t-elf-t-ended.json
