# 候选 C3「对手场面威胁」：ramp-t-pirate-t（没装）

组合 ramp-t-pirate-t（我方-对方），只用我方一侧的局面。`--features board`：在装机向量之上只加 board（这格没装 C2）。board 6 维的定义见 learn.features 和 analysis/c3-threat/README.md 第四节（09f7ca2），代码 36d0b78。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：pirate-t_ramp-t.jsonl，解压后 sha256 `f8f72e89d4b70fb1e71ed34c8d3dff5e3bcebcb1f18822e99bb828f78c11c992`；同 cand-bprime-ramp-t-pirate-t 的那份。
- 拟合：`python -m svsim.learn.phased --games pirate-t_ramp-t.jsonl --matchup ramp-t-pirate-t --hold-out-every 11 --features board --out <本目录>`。
- 对照：cand-bprime-ramp-t-pirate-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1477 | 0.5940 | 0.5943 | -0.0003（-0.0074～+0.0062） | 0.5888 |
| act | 5093 | 0.5832 | 0.5852 | -0.0021（-0.0059～+0.0019） | 0.5803 |

文件 sha256：

    72ca117d3913a8ab22db1c9ac9480d0df9155d5ab653cc8078d49ebedbc6ce82  ramp-t-pirate-t-act.json
    b5e7e6ca0e020e89bb98ddda4d20a1956f345d4ed5889d4aa9a67d702f3d1a47  ramp-t-pirate-t-ended.json
