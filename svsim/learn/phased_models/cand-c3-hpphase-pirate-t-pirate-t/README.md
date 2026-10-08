# 候选 C3 修订版「HP × 回合段」（hpphase）：pirate-t-pirate-t（没装）

组合 pirate-t-pirate-t（我方-对方），只用我方一侧的局面。`--features hpphase`：在装机向量之上只加 hpphase（这格没装 C2）。hpphase 4 维（双方领袖 HP × 被评分方第 1～4 / 5～7 回合）的定义见 learn.features 和 analysis/c3-threat/README.md 第六节（3e6b4f2），代码 729630a。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：pirate-t_pirate-t.jsonl，解压后 sha256 `54bba6c4368c19b445cdc49e97ac5e973646dd9706f9acb52c4d31dfbabbfce5`；同 cand-bprime-pirate-t-pirate-t 的那份。
- 拟合：`python -m svsim.learn.phased --games pirate-t_pirate-t.jsonl --matchup pirate-t-pirate-t --hold-out-every 11 --features hpphase --out <本目录>`。
- 对照：cand-bprime-pirate-t-pirate-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 2884 | 0.5962 | 0.5972 | -0.0010（-0.0016～-0.0003） | 0.5990 |
| act | 12295 | 0.6039 | 0.6034 | +0.0005（-0.0002～+0.0012） | 0.6008 |

文件 sha256：

    3798a304f508db12ccd45274f7b095740202f3412f4df6f34376c21d213da257  pirate-t-pirate-t-act.json
    902ae3273f4c61134ba7fa64fced76df0ecc67e2d889a39796eaaa3b36b8db2b  pirate-t-pirate-t-ended.json
