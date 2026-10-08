# 候选 C3「对手场面威胁」：nemesis-t-ramp-t（没装）

组合 nemesis-t-ramp-t（我方-对方），只用我方一侧的局面。`--features board`：在装机向量之上只加 board（这格没装 C2）。board 6 维的定义见 learn.features 和 analysis/c3-threat/README.md 第四节（09f7ca2），代码 36d0b78。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：nemesis-t_ramp-t.jsonl，解压后 sha256 `f0c0d3be77bb3e2409a807dc4f0e998cf94db3e8b784c644aecf924b6c90f1e0`；同 cand-bprime-nemesis-t-ramp-t 的那份。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_ramp-t.jsonl --matchup nemesis-t-ramp-t --hold-out-every 11 --features board --out <本目录>`。
- 对照：cand-bprime-nemesis-t-ramp-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1476 | 0.5714 | 0.5684 | +0.0029（-0.0006～+0.0067） | 0.5599 |
| act | 6593 | 0.5640 | 0.5636 | +0.0004（-0.0027～+0.0035） | 0.5539 |

文件 sha256：

    c6da2ec7dc5a7eac22e46f7852f33b527e32382ea9347e52ef053105d2cfe939  nemesis-t-ramp-t-act.json
    ce264d2020316c32a6dbc8ec89a519f0bd5f1ca54ee6730f52b79bb539cafb3a  nemesis-t-ramp-t-ended.json
