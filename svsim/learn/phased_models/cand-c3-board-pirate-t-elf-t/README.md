# 候选 C3「对手场面威胁」：pirate-t-elf-t（没装）

> **已被取代，仅供参考（2026-10-08）**：分析线 3e6b4f2（analysis/c3-threat/README.md 第六节）撤回了两维 pressure，C3 改为 4 维 `hpphase`，见 cand-c3-hpphase-*。这个目录不开门。

组合 pirate-t-elf-t（我方-对方），只用我方一侧的局面。`--features board`：在装机向量之上只加 board（这格没装 C2）。board 6 维的定义见 learn.features 和 analysis/c3-threat/README.md 第四节（09f7ca2），代码 36d0b78。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：pirate-t_elf-t.jsonl，解压后 sha256 `8c08df56011c24543c9c0f2bd2a21046d8849f15699c8581091e3eb687aa42f8`；同 cand-bprime-pirate-t-elf-t 的那份。
- 拟合：`python -m svsim.learn.phased --games pirate-t_elf-t.jsonl --matchup pirate-t-elf-t --hold-out-every 11 --features board --out <本目录>`。
- 对照：cand-bprime-pirate-t-elf-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1400 | 0.5743 | 0.5685 | +0.0058（-0.0004～+0.0119） | 0.5601 |
| act | 6260 | 0.5661 | 0.5529 | +0.0132（+0.0029～+0.0228） | 0.5455 |

文件 sha256：

    e16edbfe82df83eb02fb8baf91b4b0548fc060497dc5d6dd61eeabed151f9b5c  pirate-t-elf-t-act.json
    268fb689fc4e20eca8d291ec493453c379d89f8482b3bd518745064c5258939f  pirate-t-elf-t-ended.json
