# 候选 C3「对手场面威胁」：ramp-t-ramp-t（没装）

> **已被取代，仅供参考（2026-10-08）**：分析线 3e6b4f2（analysis/c3-threat/README.md 第六节）撤回了两维 pressure，C3 改为 4 维 `hpphase`，见 cand-c3-hpphase-*。这个目录不开门。

组合 ramp-t-ramp-t（我方-对方），只用我方一侧的局面。`--features hand,board`：在已装的 C2（hand）之上加 board。board 6 维的定义见 learn.features 和 analysis/c3-threat/README.md 第四节（09f7ca2），代码 36d0b78。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：s200.jsonl，解压后 sha256 `c7fd49577934bd9f38d9818336ccac04f8733724d7fbe4d379511da1d7bff123`；同 cand-c2-hand-ramp 的那份。
- 拟合：`python -m svsim.learn.phased --games s200.jsonl --matchup ramp-t-ramp-t --hold-out-every 11 --features hand,board --out <本目录>`。
- 对照：cand-c2-hand-ramp（同数据、同留出，只有 hand）。

留出局（400 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型就是 C2（同一份留出拟合）：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 6735 | 0.5807 | 0.5827 | -0.0020（-0.0042～+0.0003） | 0.5827 |
| act | 23645 | 0.5808 | 0.5818 | -0.0010（-0.0024～+0.0003） | 0.5818 |

文件 sha256：

    70ff1982e9a6512d764bfb3927b6adce0887a8cb5f1209c2be9f70df5ecf81a7  ramp-t-ramp-t-act.json
    c66590db8f95dd37ff1da2428130d44fd70eca98a719d05e692a55b5d61d7ef4  ramp-t-ramp-t-ended.json
