# 候选 C2 推广：可用手牌价值（没装）：elf-t-elf-t

组合 elf-t-elf-t（我方-对方），只用我方一侧的局面（`--matchup elf-t-elf-t`）。加 `--features hand`（6 维，见 learn.features.EXTRAS）；版本 2 线性，2500 次迭代，STOCK（me_hand_*、me_pool_*）置零，`--hold-out-every 11`（行号 % 11 == 0 的局留出、不参与拟合）。做法同 cand-c2-hand-ramp（analysis/refit-200/README.md 的预注册）。C2 推广由架构线 2026-10-08 08:10Z 布置，只作 J6 旁证；门等跳费龙镜像装机后由分析线排（预留库 59500000）。

- 数据：data/pairings-20261008 分支的 data/pairings-20261008/elf-t_elf-t.jsonl.gz（2000 局），解压后 sha256 `d1f461ffe310d44c0dc0183cf2202e088f8c722ce2a9cdccde54670c06afe4b8`，即现装 `elf-t-elf-t-{ended,act}.json` 的 info 里记录的那份。
- 核对：全量重拟（不留出、不加特征）与现装系数逐位相同。
- 拟合：`python -m svsim.learn.phased --games elf-t_elf-t.jsonl --matchup elf-t-elf-t --hold-out-every 11 --features hand --out <本目录>`（代码 c87d51b）。

留出局上的 log loss（只看胜负，和局不计）。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 局面 | 现装* | B′ | C2 | C2 − B′ |
|---|---|---|---|---|---|
| ended | 2734 | 0.6022 | 0.6050 | 0.5933 | -0.0117 |
| act | 13010 | 0.5941 | 0.5968 | 0.5825 | -0.0143 |

文件 sha256：

    d895d212e537dd0d2a822740cdc1b1f177f223909cf041171eb21bf68a6da906  elf-t-elf-t-act.json
    e8509021f50b024aac3bbbf88b889250967f6f713ba126aa32c8324abcb064dc  elf-t-elf-t-ended.json
