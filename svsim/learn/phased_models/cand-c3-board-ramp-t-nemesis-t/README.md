# 候选 C3「对手场面威胁」：ramp-t-nemesis-t（没装）

> **已被取代，仅供参考（2026-10-08）**：分析线 3e6b4f2（analysis/c3-threat/README.md 第六节）撤回了两维 pressure，C3 改为 4 维 `hpphase`，见 cand-c3-hpphase-*。这个目录不开门。

组合 ramp-t-nemesis-t（我方-对方），只用我方一侧的局面。`--features board`：在装机向量之上只加 board（这格没装 C2）。board 6 维的定义见 learn.features 和 analysis/c3-threat/README.md 第四节（09f7ca2），代码 36d0b78。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：nemesis-t_ramp-t.jsonl，解压后 sha256 `f0c0d3be77bb3e2409a807dc4f0e998cf94db3e8b784c644aecf924b6c90f1e0`；同 cand-bprime-ramp-t-nemesis-t 的那份。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_ramp-t.jsonl --matchup ramp-t-nemesis-t --hold-out-every 11 --features board --out <本目录>`。
- 对照：cand-bprime-ramp-t-nemesis-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1481 | 0.5575 | 0.5573 | +0.0001（-0.0024～+0.0026） | 0.5513 |
| act | 5393 | 0.5584 | 0.5558 | +0.0026（-0.0007～+0.0059） | 0.5498 |

文件 sha256：

    c2161ff62619d6eeb2c43439e9b6ac087668675759253ecade5a3b174ecfcc8d  ramp-t-nemesis-t-act.json
    783841389ccb0bb4d032fcd63f9acf8bc86c2c149f3cacea973ba4d59e4e1667  ramp-t-nemesis-t-ended.json
