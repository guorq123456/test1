# 候选 C3 修订版「HP × 回合段」（hpphase）：elf-t-elf-t（没装）

组合 elf-t-elf-t（我方-对方），只用我方一侧的局面。`--features hand,hpphase`：在已装的 C2（hand）之上加 hpphase。hpphase 4 维（双方领袖 HP × 被评分方第 1～4 / 5～7 回合）的定义见 learn.features 和 analysis/c3-threat/README.md 第六节（3e6b4f2），代码 729630a。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：elf-t_elf-t.jsonl，解压后 sha256 `d1f461ffe310d44c0dc0183cf2202e088f8c722ce2a9cdccde54670c06afe4b8`；同 cand-c2-hand-elf-t-elf-t 的那份。
- 拟合：`python -m svsim.learn.phased --games elf-t_elf-t.jsonl --matchup elf-t-elf-t --hold-out-every 11 --features hand,hpphase --out <本目录>`。
- 对照：cand-c2-hand-elf-t-elf-t（同数据、同留出，只有 hand）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型就是 C2（同一份留出拟合）：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 2734 | 0.5894 | 0.5933 | -0.0038（-0.0090～+0.0011） | 0.5933 |
| act | 13010 | 0.5825 | 0.5825 | +0.0001（-0.0022～+0.0024） | 0.5825 |

文件 sha256：

    706cf1368b776280980902d1744e4ca385b0e1338671899fb7194051b61987f7  elf-t-elf-t-act.json
    f0bc7e4e42dd9c81533d5284f2be8f1f28d1f747170f5b7e0d52744158af9386  elf-t-elf-t-ended.json
