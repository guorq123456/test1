# 候选 C3「对手场面威胁」：pirate-t-pirate-t（没装）

> **已被取代，仅供参考（2026-10-08）**：分析线 3e6b4f2（analysis/c3-threat/README.md 第六节）撤回了两维 pressure，C3 改为 4 维 `hpphase`，见 cand-c3-hpphase-*。这个目录不开门。

组合 pirate-t-pirate-t（我方-对方），只用我方一侧的局面。`--features board`：在装机向量之上只加 board（这格没装 C2）。board 6 维的定义见 learn.features 和 analysis/c3-threat/README.md 第四节（09f7ca2），代码 36d0b78。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：pirate-t_pirate-t.jsonl，解压后 sha256 `54bba6c4368c19b445cdc49e97ac5e973646dd9706f9acb52c4d31dfbabbfce5`；同 cand-bprime-pirate-t-pirate-t 的那份。
- 拟合：`python -m svsim.learn.phased --games pirate-t_pirate-t.jsonl --matchup pirate-t-pirate-t --hold-out-every 11 --features board --out <本目录>`。
- 对照：cand-bprime-pirate-t-pirate-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 2884 | 0.5958 | 0.5972 | -0.0013（-0.0022～-0.0004） | 0.5990 |
| act | 12295 | 0.6020 | 0.6034 | -0.0014（-0.0025～-0.0003） | 0.6008 |

文件 sha256：

    785ec49bd330a59c017bad086881a85977a2b3912ecb633e87614ad075516561  pirate-t-pirate-t-act.json
    3c08275123707e5dc6e883c5e17447fb71ac1a69734428e3d8627e3e7bc0dd3f  pirate-t-pirate-t-ended.json
