# 候选 C3 修订版「HP × 回合段」（hpphase）：elf-t-nemesis-t（没装）

组合 elf-t-nemesis-t（我方-对方），只用我方一侧的局面。`--features hand,hpphase`：在已装的 C2（hand）之上加 hpphase。hpphase 4 维（双方领袖 HP × 被评分方第 1～4 / 5～7 回合）的定义见 learn.features 和 analysis/c3-threat/README.md 第六节（3e6b4f2），代码 729630a。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：nemesis-t_elf-t.jsonl，解压后 sha256 `475d43f4a9b46241c59004f9a59c1cc86daea3ef113d1d94883f55d715b5e9e6`；同 cand-c2-hand-elf-t-nemesis-t 的那份。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_elf-t.jsonl --matchup elf-t-nemesis-t --hold-out-every 11 --features hand,hpphase --out <本目录>`。
- 对照：cand-c2-hand-elf-t-nemesis-t（同数据、同留出，只有 hand）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型就是 C2（同一份留出拟合）：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1333 | 0.5522 | 0.5538 | -0.0017（-0.0100～+0.0063） | 0.5538 |
| act | 6324 | 0.5497 | 0.5492 | +0.0004（-0.0055～+0.0064） | 0.5492 |

文件 sha256：

    07a4fc034c97aec6564e2558f62cfb30dd7fa9e8dbf556633cf61fd392d37316  elf-t-nemesis-t-act.json
    fbcd4cf18df2d8ea7008b6e7e45f07f73429e9421bbdef8c1eb1f76a116e9563  elf-t-nemesis-t-ended.json
