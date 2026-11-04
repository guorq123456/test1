# 候选 B′：同数据同留出、不加特征的干净基线（没装，只作对照）：nemesis-t-ramp-t

组合 nemesis-t-ramp-t（我方-对方），只用我方一侧的局面（`--matchup nemesis-t-ramp-t`）。不加特征；版本 2 线性，2500 次迭代，STOCK（me_hand_*、me_pool_*）置零，`--hold-out-every 11`（行号 % 11 == 0 的局留出、不参与拟合）。做法同 cand-c2-hand-ramp（analysis/refit-200/README.md 的预注册）。C2 推广由架构线 2026-10-08 08:10Z 布置，只作 J6 旁证；门等跳费龙镜像装机后由分析线排（预留库 59900000）。

- 数据：data/pairings-20261008 分支的 data/pairings-20261008/nemesis-t_ramp-t.jsonl.gz（2000 局），解压后 sha256 `f0c0d3be77bb3e2409a807dc4f0e998cf94db3e8b784c644aecf924b6c90f1e0`，即现装 `nemesis-t-ramp-t-{ended,act}.json` 的 info 里记录的那份。
- 核对：全量重拟（不留出、不加特征）与现装系数逐位相同。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_ramp-t.jsonl --matchup nemesis-t-ramp-t --hold-out-every 11 --out <本目录>`（代码 c87d51b）。

留出局上的 log loss（只看胜负，和局不计）。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 局面 | 现装* | B′ | C2 | C2 − B′ |
|---|---|---|---|---|---|
| ended | 1476 | 0.5599 | 0.5684 | 0.5684 | +0.0000 |
| act | 6593 | 0.5539 | 0.5636 | 0.5615 | -0.0021 |

文件 sha256：

    fb2b868311293867cc9207bcd5af58647b1c2ff3799d3337e89b2817dcdf1ae7  nemesis-t-ramp-t-act.json
    d616e1f00c70ac904f8c7ac1d8f86af65c57bf5188808ee86519f7b16bc7efea  nemesis-t-ramp-t-ended.json
