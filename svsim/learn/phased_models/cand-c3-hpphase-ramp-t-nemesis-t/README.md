# 候选 C3 修订版「HP × 回合段」（hpphase）：ramp-t-nemesis-t（没装）

组合 ramp-t-nemesis-t（我方-对方），只用我方一侧的局面。`--features hpphase`：在装机向量之上只加 hpphase（这格没装 C2）。hpphase 4 维（双方领袖 HP × 被评分方第 1～4 / 5～7 回合）的定义见 learn.features 和 analysis/c3-threat/README.md 第六节（3e6b4f2），代码 729630a。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：nemesis-t_ramp-t.jsonl，解压后 sha256 `f0c0d3be77bb3e2409a807dc4f0e998cf94db3e8b784c644aecf924b6c90f1e0`；同 cand-bprime-ramp-t-nemesis-t 的那份。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_ramp-t.jsonl --matchup ramp-t-nemesis-t --hold-out-every 11 --features hpphase --out <本目录>`。
- 对照：cand-bprime-ramp-t-nemesis-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1481 | 0.5575 | 0.5573 | +0.0002（-0.0023～+0.0026） | 0.5513 |
| act | 5393 | 0.5553 | 0.5558 | -0.0005（-0.0021～+0.0011） | 0.5498 |

文件 sha256：

    28beec8dd1c6a0a5881d79ff9142592074f17249709890f89dfbe5e0bde6fe75  ramp-t-nemesis-t-act.json
    13ca64f5d3b3e0847c068afeee4636df9936c3239b59e9089f8c14a441aeca71  ramp-t-nemesis-t-ended.json
