# 候选 C2 推广：可用手牌价值（没装）：elf-t-ramp-t

组合 elf-t-ramp-t（我方-对方），只用我方一侧的局面（`--matchup elf-t-ramp-t`）。加 `--features hand`（6 维，见 learn.features.EXTRAS）；版本 2 线性，2500 次迭代，STOCK（me_hand_*、me_pool_*）置零，`--hold-out-every 11`（行号 % 11 == 0 的局留出、不参与拟合）。做法同 cand-c2-hand-ramp（analysis/refit-200/README.md 的预注册）。C2 推广由架构线 2026-10-08 08:10Z 布置，只作 J6 旁证；门等跳费龙镜像装机后由分析线排（预留库 59700000）。

- 数据：data/pairings-20261008 分支的 data/pairings-20261008/elf-t_ramp-t.jsonl.gz（2000 局），解压后 sha256 `4cccb6a46e885bc2bc45d3187f380e4a3a95c86418df7d2aec7df4698dc8d27b`，即现装 `elf-t-ramp-t-{ended,act}.json` 的 info 里记录的那份。
- 核对：全量重拟（不留出、不加特征）与现装系数逐位相同。
- 拟合：`python -m svsim.learn.phased --games elf-t_ramp-t.jsonl --matchup elf-t-ramp-t --hold-out-every 11 --features hand --out <本目录>`（代码 c87d51b）。

留出局上的 log loss（只看胜负，和局不计）。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 局面 | 现装* | B′ | C2 | C2 − B′ |
|---|---|---|---|---|---|
| ended | 1360 | 0.5887 | 0.5930 | 0.5746 | -0.0184 |
| act | 6463 | 0.5894 | 0.5937 | 0.5714 | -0.0223 |

文件 sha256：

    63f9187c853c8e2c5d3cd52041038d7a6db1da254526b5fb43baa2786d1272dd  elf-t-ramp-t-act.json
    f256e88d7652e4109815d9deefa0aa5d7ce04e595b74cac35f243b2109d9d551  elf-t-ramp-t-ended.json
