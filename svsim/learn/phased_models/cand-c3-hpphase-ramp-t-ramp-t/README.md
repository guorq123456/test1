# 候选 C3 修订版「HP × 回合段」（hpphase）：ramp-t-ramp-t（没装）

组合 ramp-t-ramp-t（我方-对方），只用我方一侧的局面。`--features hand,hpphase`：在已装的 C2（hand）之上加 hpphase。hpphase 4 维（双方领袖 HP × 被评分方第 1～4 / 5～7 回合）的定义见 learn.features 和 analysis/c3-threat/README.md 第六节（3e6b4f2），代码 729630a。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：s200.jsonl，解压后 sha256 `c7fd49577934bd9f38d9818336ccac04f8733724d7fbe4d379511da1d7bff123`；同 cand-c2-hand-ramp 的那份。
- 拟合：`python -m svsim.learn.phased --games s200.jsonl --matchup ramp-t-ramp-t --hold-out-every 11 --features hand,hpphase --out <本目录>`。
- 对照：cand-c2-hand-ramp（同数据、同留出，只有 hand）。

留出局（400 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型就是 C2（同一份留出拟合）：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 6735 | 0.5809 | 0.5827 | -0.0018（-0.0040～+0.0003） | 0.5827 |
| act | 23645 | 0.5810 | 0.5818 | -0.0008（-0.0021～+0.0005） | 0.5818 |

文件 sha256：

    d6067af776b82fb41de63f5c4d859ea1512642eaca706113fabdf77d6d427d81  ramp-t-ramp-t-act.json
    dfca8b1c34cc65f6fd9309721f351a7f3eb4b990bd3dcfaafdc963d2705267b4  ramp-t-ramp-t-ended.json
