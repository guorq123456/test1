# 候选 C3「对手场面威胁」：elf-t-nemesis-t（没装）

组合 elf-t-nemesis-t（我方-对方），只用我方一侧的局面。`--features hand,board`：在已装的 C2（hand）之上加 board。board 6 维的定义见 learn.features 和 analysis/c3-threat/README.md 第四节（09f7ca2），代码 36d0b78。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：nemesis-t_elf-t.jsonl，解压后 sha256 `475d43f4a9b46241c59004f9a59c1cc86daea3ef113d1d94883f55d715b5e9e6`；同 cand-c2-hand-elf-t-nemesis-t 的那份。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_elf-t.jsonl --matchup elf-t-nemesis-t --hold-out-every 11 --features hand,board --out <本目录>`。
- 对照：cand-c2-hand-elf-t-nemesis-t（同数据、同留出，只有 hand）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型就是 C2（同一份留出拟合）：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1333 | 0.5516 | 0.5538 | -0.0023（-0.0110～+0.0066） | 0.5538 |
| act | 6324 | 0.5493 | 0.5492 | +0.0000（-0.0050～+0.0048） | 0.5492 |

文件 sha256：

    aca6243ded68b1538aa3434fb4b23cb44c8cc067228239d689fddb2e2a89c075  elf-t-nemesis-t-act.json
    781bb941531c25b79e9edba105a9e33046f2da295fe149e5a346c00c34e4b2d3  elf-t-nemesis-t-ended.json
