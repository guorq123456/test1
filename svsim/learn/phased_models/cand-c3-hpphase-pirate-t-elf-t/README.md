# 候选 C3 修订版「HP × 回合段」（hpphase）：pirate-t-elf-t（没装）

组合 pirate-t-elf-t（我方-对方），只用我方一侧的局面。`--features hpphase`：在装机向量之上只加 hpphase（这格没装 C2）。hpphase 4 维（双方领袖 HP × 被评分方第 1～4 / 5～7 回合）的定义见 learn.features 和 analysis/c3-threat/README.md 第六节（3e6b4f2），代码 729630a。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：pirate-t_elf-t.jsonl，解压后 sha256 `8c08df56011c24543c9c0f2bd2a21046d8849f15699c8581091e3eb687aa42f8`；同 cand-bprime-pirate-t-elf-t 的那份。
- 拟合：`python -m svsim.learn.phased --games pirate-t_elf-t.jsonl --matchup pirate-t-elf-t --hold-out-every 11 --features hpphase --out <本目录>`。
- 对照：cand-bprime-pirate-t-elf-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1400 | 0.5738 | 0.5685 | +0.0053（-0.0007～+0.0113） | 0.5601 |
| act | 6260 | 0.5665 | 0.5529 | +0.0136（+0.0034～+0.0233） | 0.5455 |

文件 sha256：

    bda572e94cf547ae06e0f27e9996b12cf651d3350a77b28c9850b1618ba46b25  pirate-t-elf-t-act.json
    798566b8f6bb72197aea7d67a4a773fa4c00e023041e342aeb80aff935821028  pirate-t-elf-t-ended.json
