# 候选 C3「对手场面威胁」：elf-t-ramp-t（没装）

> **已被取代，仅供参考（2026-10-08）**：分析线 3e6b4f2（analysis/c3-threat/README.md 第六节）撤回了两维 pressure，C3 改为 4 维 `hpphase`，见 cand-c3-hpphase-*。这个目录不开门。

组合 elf-t-ramp-t（我方-对方），只用我方一侧的局面。`--features board`：在装机向量之上只加 board（这格没装 C2）。board 6 维的定义见 learn.features 和 analysis/c3-threat/README.md 第四节（09f7ca2），代码 36d0b78。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：elf-t_ramp-t.jsonl，解压后 sha256 `4cccb6a46e885bc2bc45d3187f380e4a3a95c86418df7d2aec7df4698dc8d27b`；同 cand-bprime-elf-t-ramp-t 的那份。
- 拟合：`python -m svsim.learn.phased --games elf-t_ramp-t.jsonl --matchup elf-t-ramp-t --hold-out-every 11 --features board --out <本目录>`。
- 对照：cand-bprime-elf-t-ramp-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1360 | 0.5941 | 0.5930 | +0.0010（-0.0038～+0.0054） | 0.5887 |
| act | 6463 | 0.5928 | 0.5937 | -0.0009（-0.0030～+0.0013） | 0.5894 |

文件 sha256：

    73d6868f3f80c5298e64fa38e0c7c8152be4f9e2424aad8f3cee39ee5eb7a4e2  elf-t-ramp-t-act.json
    57ccd023c2cf395852843ba403f7dffbb82fa36e2abd3aa5208209cc5b923863  elf-t-ramp-t-ended.json
