# 候选 B′：同数据同留出、不加特征的干净基线（没装，只作对照）：nemesis-t-elf-t

组合 nemesis-t-elf-t（我方-对方），只用我方一侧的局面（`--matchup nemesis-t-elf-t`）。不加特征；版本 2 线性，2500 次迭代，STOCK（me_hand_*、me_pool_*）置零，`--hold-out-every 11`（行号 % 11 == 0 的局留出、不参与拟合）。做法同 cand-c2-hand-ramp（analysis/refit-200/README.md 的预注册）。C2 推广由架构线 2026-10-08 08:10Z 布置，只作 J6 旁证；门等跳费龙镜像装机后由分析线排（预留库 59800000）。

- 数据：data/pairings-20261008 分支的 data/pairings-20261008/nemesis-t_elf-t.jsonl.gz（2000 局），解压后 sha256 `475d43f4a9b46241c59004f9a59c1cc86daea3ef113d1d94883f55d715b5e9e6`，即现装 `nemesis-t-elf-t-{ended,act}.json` 的 info 里记录的那份。
- 核对：全量重拟（不留出、不加特征）与现装系数逐位相同。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_elf-t.jsonl --matchup nemesis-t-elf-t --hold-out-every 11 --out <本目录>`（代码 c87d51b）。

留出局上的 log loss（只看胜负，和局不计）。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 局面 | 现装* | B′ | C2 | C2 − B′ |
|---|---|---|---|---|---|
| ended | 1327 | 0.5592 | 0.5667 | 0.5647 | -0.0020 |
| act | 6217 | 0.5515 | 0.5584 | 0.5571 | -0.0013 |

文件 sha256：

    2ab94546521ba7641ef41e02a24598168f18d29bcc7c56edfbb020caa57df394  nemesis-t-elf-t-act.json
    d6e22c93e39e87fa72157e7a25a77073231d6f19d080863089c9d5e0408978ef  nemesis-t-elf-t-ended.json
