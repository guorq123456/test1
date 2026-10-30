# 候选 C3 修订版「HP × 回合段」（hpphase）：ramp-t-pirate-t（没装）

组合 ramp-t-pirate-t（我方-对方），只用我方一侧的局面。`--features hpphase`：在装机向量之上只加 hpphase（这格没装 C2）。hpphase 4 维（双方领袖 HP × 被评分方第 1～4 / 5～7 回合）的定义见 learn.features 和 analysis/c3-threat/README.md 第六节（3e6b4f2），代码 729630a。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：pirate-t_ramp-t.jsonl，解压后 sha256 `f8f72e89d4b70fb1e71ed34c8d3dff5e3bcebcb1f18822e99bb828f78c11c992`；同 cand-bprime-ramp-t-pirate-t 的那份。
- 拟合：`python -m svsim.learn.phased --games pirate-t_ramp-t.jsonl --matchup ramp-t-pirate-t --hold-out-every 11 --features hpphase --out <本目录>`。
- 对照：cand-bprime-ramp-t-pirate-t（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | 对照 | C3 − 对照（95%） | 现装 |
|---|---|---|---|---|---|
| ended | 1477 | 0.5943 | 0.5943 | +0.0001（-0.0072～+0.0068） | 0.5888 |
| act | 5093 | 0.5835 | 0.5852 | -0.0017（-0.0054～+0.0021） | 0.5803 |

文件 sha256：

    2c03c9173b53ab80c1b451024146e1546a81381c68424a54f69b63b353d2fa55  ramp-t-pirate-t-act.json
    e534530c6430ac07e85efbae1f0c24494a77399a4598654830584a0a7d8f1ba3  ramp-t-pirate-t-ended.json
