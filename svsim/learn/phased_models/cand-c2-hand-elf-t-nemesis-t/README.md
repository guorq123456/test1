# 候选 C2 推广：可用手牌价值（没装）：elf-t-nemesis-t

组合 elf-t-nemesis-t（我方-对方），只用我方一侧的局面（`--matchup elf-t-nemesis-t`）。加 `--features hand`（6 维，见 learn.features.EXTRAS）；版本 2 线性，2500 次迭代，STOCK（me_hand_*、me_pool_*）置零，`--hold-out-every 11`（行号 % 11 == 0 的局留出、不参与拟合）。做法同 cand-c2-hand-ramp（analysis/refit-200/README.md 的预注册）。C2 推广由架构线 2026-10-08 08:10Z 布置，只作 J6 旁证；门等跳费龙镜像装机后由分析线排（预留库 59600000）。

- 数据：data/pairings-20261008 分支的 data/pairings-20261008/nemesis-t_elf-t.jsonl.gz（2000 局），解压后 sha256 `475d43f4a9b46241c59004f9a59c1cc86daea3ef113d1d94883f55d715b5e9e6`，即现装 `elf-t-nemesis-t-{ended,act}.json` 的 info 里记录的那份。
- 核对：全量重拟（不留出、不加特征）与现装系数逐位相同。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_elf-t.jsonl --matchup elf-t-nemesis-t --hold-out-every 11 --features hand --out <本目录>`（代码 c87d51b）。

留出局上的 log loss（只看胜负，和局不计）。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 局面 | 现装* | B′ | C2 | C2 − B′ |
|---|---|---|---|---|---|
| ended | 1333 | 0.5599 | 0.5656 | 0.5538 | -0.0118 |
| act | 6324 | 0.5596 | 0.5652 | 0.5492 | -0.0160 |

文件 sha256：

    ca6a4f2faa82ea504f194db699411af38d44b40cf4e315b15e32846de977ee86  elf-t-nemesis-t-act.json
    e9a27705f12c7c521d47421e79d42243c99be039ac34b55edabcc8d95097c329  elf-t-nemesis-t-ended.json
