# 候选 B′：同数据同留出、不加特征的干净基线（没装，只作对照）：ramp-t-pirate-t

组合 ramp-t-pirate-t（我方-对方），只用我方一侧的局面（`--matchup ramp-t-pirate-t`）。不加特征；版本 2 线性，2500 次迭代，STOCK（me_hand_*、me_pool_*）置零，`--hold-out-every 11`（行号 % 11 == 0 的局留出、不参与拟合）。做法同 cand-c2-hand-ramp（analysis/refit-200/README.md 的预注册）。C2 推广由架构线 2026-10-08 08:10Z 布置，只作 J6 旁证；门等跳费龙镜像装机后由分析线排（预留库 60400000）。

- 数据：local/data-pairings-20261008 分支的 data/pairings-20261008/pirate-t_ramp-t.jsonl.gz（2000 局），解压后 sha256 `f8f72e89d4b70fb1e71ed34c8d3dff5e3bcebcb1f18822e99bb828f78c11c992`，即现装 `ramp-t-pirate-t-{ended,act}.json` 的 info 里记录的那份。
- 核对：全量重拟（不留出、不加特征）的局面数和均值与现装逐位相同；系数在当初拟合的本机（Windows）与云端（Linux）之间有浮点差（系数最大差 7.2e-04（act）），数据相同。
- 拟合：`python -m svsim.learn.phased --games pirate-t_ramp-t.jsonl --matchup ramp-t-pirate-t --hold-out-every 11 --out <本目录>`（代码 c87d51b）。

留出局上的 log loss（只看胜负，和局不计）。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 局面 | 现装* | B′ | C2 | C2 − B′ |
|---|---|---|---|---|---|
| ended | 1477 | 0.5888 | 0.5943 | 0.5956 | +0.0013 |
| act | 5093 | 0.5803 | 0.5852 | 0.5855 | +0.0003 |

文件 sha256：

    4fc0d0059c0998742e7ad98d87cb4418fed7757761ca139159e34fae5d2e4316  ramp-t-pirate-t-act.json
    3bbb1d69710fc4f55d42f2f2221add8b0e8450098061f58eea6f240d9767198f  ramp-t-pirate-t-ended.json
