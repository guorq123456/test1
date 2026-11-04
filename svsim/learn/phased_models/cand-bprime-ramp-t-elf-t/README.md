# 候选 B′：同数据同留出、不加特征的干净基线（没装，只作对照）：ramp-t-elf-t

组合 ramp-t-elf-t（我方-对方），只用我方一侧的局面（`--matchup ramp-t-elf-t`）。不加特征；版本 2 线性，2500 次迭代，STOCK（me_hand_*、me_pool_*）置零，`--hold-out-every 11`（行号 % 11 == 0 的局留出、不参与拟合）。做法同 cand-c2-hand-ramp（analysis/refit-200/README.md 的预注册）。C2 推广由架构线 2026-10-08 08:10Z 布置，只作 J6 旁证；门等跳费龙镜像装机后由分析线排（预留库 60200000）。

- 数据：data/pairings-20261008 分支的 data/pairings-20261008/elf-t_ramp-t.jsonl.gz（2000 局），解压后 sha256 `4cccb6a46e885bc2bc45d3187f380e4a3a95c86418df7d2aec7df4698dc8d27b`，即现装 `ramp-t-elf-t-{ended,act}.json` 的 info 里记录的那份。
- 核对：全量重拟（不留出、不加特征）与现装系数逐位相同。
- 拟合：`python -m svsim.learn.phased --games elf-t_ramp-t.jsonl --matchup ramp-t-elf-t --hold-out-every 11 --out <本目录>`（代码 c87d51b）。

留出局上的 log loss（只看胜负，和局不计）。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 局面 | 现装* | B′ | C2 | C2 − B′ |
|---|---|---|---|---|---|
| ended | 1369 | 0.5983 | 0.6053 | 0.6018 | -0.0035 |
| act | 4845 | 0.5859 | 0.5931 | 0.5921 | -0.0010 |

文件 sha256：

    67285eb4818824b22ffad86aa264bd18139fa9d719c3df44bf19c46234df01d6  ramp-t-elf-t-act.json
    7a9722b0e0195aaf2c689199a973887a931abd5093c10b2ca1ce7ba3353045c0  ramp-t-elf-t-ended.json
