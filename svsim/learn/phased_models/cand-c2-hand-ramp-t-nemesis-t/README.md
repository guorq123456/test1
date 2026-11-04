# 候选 C2 推广：可用手牌价值（没装）：ramp-t-nemesis-t

组合 ramp-t-nemesis-t（我方-对方），只用我方一侧的局面（`--matchup ramp-t-nemesis-t`）。加 `--features hand`（6 维，见 learn.features.EXTRAS）；版本 2 线性，2500 次迭代，STOCK（me_hand_*、me_pool_*）置零，`--hold-out-every 11`（行号 % 11 == 0 的局留出、不参与拟合）。做法同 cand-c2-hand-ramp（analysis/refit-200/README.md 的预注册）。C2 推广由架构线 2026-10-08 08:10Z 布置，只作 J6 旁证；门等跳费龙镜像装机后由分析线排（预留库 60300000）。

- 数据：data/pairings-20261008 分支的 data/pairings-20261008/nemesis-t_ramp-t.jsonl.gz（2000 局），解压后 sha256 `f0c0d3be77bb3e2409a807dc4f0e998cf94db3e8b784c644aecf924b6c90f1e0`，即现装 `ramp-t-nemesis-t-{ended,act}.json` 的 info 里记录的那份。
- 核对：全量重拟（不留出、不加特征）与现装系数逐位相同。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_ramp-t.jsonl --matchup ramp-t-nemesis-t --hold-out-every 11 --features hand --out <本目录>`（代码 c87d51b）。

留出局上的 log loss（只看胜负，和局不计）。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 局面 | 现装* | B′ | C2 | C2 − B′ |
|---|---|---|---|---|---|
| ended | 1481 | 0.5513 | 0.5573 | 0.5571 | -0.0002 |
| act | 5393 | 0.5498 | 0.5558 | 0.5554 | -0.0004 |

文件 sha256：

    e031038b4d03429a8d2ff7f87f513373969b3fa23f2c4fc968406c294070ed2e  ramp-t-nemesis-t-act.json
    5d0554eeba221ad593f4b79d6a44eb0f234f665c02c69054aeb9805da528cbd3  ramp-t-nemesis-t-ended.json
