# 候选 C3 修订版「HP × 回合段」（hpphase）：nemesis-t-ramp-t（没装）

组合 nemesis-t-ramp-t（我方-对方），只用我方一侧的局面。`--features hpphase`：在装机向量之上只加 hpphase（这格没装 C2）。hpphase 4 维（双方领袖 HP × 被评分方第 1～4 / 5～7 回合）的定义见 learn.features 和 analysis/c3-threat/README.md 第六节（3e6b4f2），代码 729630a。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：nemesis-t_ramp-t.jsonl，解压后 sha256 `f0c0d3be77bb3e2409a807dc4f0e998cf94db3e8b784c644aecf924b6c90f1e0`；同 cand-bprime-nemesis-t-ramp-t 的那份。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_ramp-t.jsonl --matchup nemesis-t-ramp-t --hold-out-every 11 --features hpphase --out <本目录>`。
- 对照：cand-bprime-nemesis-t-ramp-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1476 | 0.5687 | 0.5684 | +0.0002（-0.0011～+0.0015） | 0.5599 |
| act | 6593 | 0.5639 | 0.5636 | +0.0002（-0.0027～+0.0032） | 0.5539 |

文件 sha256：

    104c7f6420e337f3553714484ea29eeb2d53ecceb1d83afa0f6bfc6e043e7eec  nemesis-t-ramp-t-act.json
    fff81da21623134057d8ede593a49c00cb6944a4dd71df5ede291bac81227a34  nemesis-t-ramp-t-ended.json
