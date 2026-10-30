# 候选 C3「对手场面威胁」：elf-t-elf-t（没装）

> **已被取代，仅供参考（2026-10-08）**：分析线 3e6b4f2（analysis/c3-threat/README.md 第六节）撤回了两维 pressure，C3 改为 4 维 `hpphase`，见 cand-c3-hpphase-*。这个目录不开门。

组合 elf-t-elf-t（我方-对方），只用我方一侧的局面。`--features hand,board`：在已装的 C2（hand）之上加 board。board 6 维的定义见 learn.features 和 analysis/c3-threat/README.md 第四节（09f7ca2），代码 36d0b78。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：elf-t_elf-t.jsonl，解压后 sha256 `d1f461ffe310d44c0dc0183cf2202e088f8c722ce2a9cdccde54670c06afe4b8`；同 cand-c2-hand-elf-t-elf-t 的那份。
- 拟合：`python -m svsim.learn.phased --games elf-t_elf-t.jsonl --matchup elf-t-elf-t --hold-out-every 11 --features hand,board --out <本目录>`。
- 对照：cand-c2-hand-elf-t-elf-t（同数据、同留出，只有 hand）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型就是 C2（同一份留出拟合）：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 2734 | 0.5898 | 0.5933 | -0.0035（-0.0085～+0.0014） | 0.5933 |
| act | 13010 | 0.5824 | 0.5825 | -0.0001（-0.0024～+0.0022） | 0.5825 |

文件 sha256：

    a4d413f5d0885e8e088ee65d9e0e601c54e2f5f4e73f712e96161486c476a6bf  elf-t-elf-t-act.json
    d363abc36aa9331aae2c97ad2e807a127fcf7b26e206eeccf14b53215ff6d11d  elf-t-elf-t-ended.json
