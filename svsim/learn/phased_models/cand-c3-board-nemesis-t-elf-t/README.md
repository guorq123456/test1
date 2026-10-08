# 候选 C3「对手场面威胁」：nemesis-t-elf-t（没装）

> **已被取代，仅供参考（2026-10-08）**：分析线 3e6b4f2（analysis/c3-threat/README.md 第六节）撤回了两维 pressure，C3 改为 4 维 `hpphase`，见 cand-c3-hpphase-*。这个目录不开门。

组合 nemesis-t-elf-t（我方-对方），只用我方一侧的局面。`--features board`：在装机向量之上只加 board（这格没装 C2）。board 6 维的定义见 learn.features 和 analysis/c3-threat/README.md 第四节（09f7ca2），代码 36d0b78。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：nemesis-t_elf-t.jsonl，解压后 sha256 `475d43f4a9b46241c59004f9a59c1cc86daea3ef113d1d94883f55d715b5e9e6`；同 cand-bprime-nemesis-t-elf-t 的那份。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_elf-t.jsonl --matchup nemesis-t-elf-t --hold-out-every 11 --features board --out <本目录>`。
- 对照：cand-bprime-nemesis-t-elf-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1327 | 0.5665 | 0.5667 | -0.0002（-0.0014～+0.0009） | 0.5592 |
| act | 6217 | 0.5622 | 0.5584 | +0.0038（+0.0007～+0.0067） | 0.5515 |

文件 sha256：

    33d03691cf290699bdb69b61ad723e4daefce1df1665eda5f8f6ce382df5af4d  nemesis-t-elf-t-act.json
    27db7b2bfeafa4ee3e5a961494137283278a8723e8259b7c2a373cda25272fb5  nemesis-t-elf-t-ended.json
