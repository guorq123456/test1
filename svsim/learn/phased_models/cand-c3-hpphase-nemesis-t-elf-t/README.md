# 候选 C3 修订版「HP × 回合段」（hpphase）：nemesis-t-elf-t（没装）

组合 nemesis-t-elf-t（我方-对方），只用我方一侧的局面。`--features hpphase`：在装机向量之上只加 hpphase（这格没装 C2）。hpphase 4 维（双方领袖 HP × 被评分方第 1～4 / 5～7 回合）的定义见 learn.features 和 analysis/c3-threat/README.md 第六节（3e6b4f2），代码 729630a。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：nemesis-t_elf-t.jsonl，解压后 sha256 `475d43f4a9b46241c59004f9a59c1cc86daea3ef113d1d94883f55d715b5e9e6`；同 cand-bprime-nemesis-t-elf-t 的那份。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_elf-t.jsonl --matchup nemesis-t-elf-t --hold-out-every 11 --features hpphase --out <本目录>`。
- 对照：cand-bprime-nemesis-t-elf-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1327 | 0.5671 | 0.5667 | +0.0004（-0.0005～+0.0013） | 0.5592 |
| act | 6217 | 0.5622 | 0.5584 | +0.0038（+0.0008～+0.0066） | 0.5515 |

文件 sha256：

    12cb017fdd8e164fb883aa687ea8b249f5096ea3872beec3936af44f6a8356e4  nemesis-t-elf-t-act.json
    f457d40a31d7b6ae165da59e3e5637cf3021b3459f5a15bff6635a54fc41d053  nemesis-t-elf-t-ended.json
