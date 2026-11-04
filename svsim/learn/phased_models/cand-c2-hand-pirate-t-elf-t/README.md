# 候选 C2 推广：可用手牌价值（没装）：pirate-t-elf-t

组合 pirate-t-elf-t（我方-对方），只用我方一侧的局面（`--matchup pirate-t-elf-t`）。加 `--features hand`（6 维，见 learn.features.EXTRAS）；版本 2 线性，2500 次迭代，STOCK（me_hand_*、me_pool_*）置零，`--hold-out-every 11`（行号 % 11 == 0 的局留出、不参与拟合）。做法同 cand-c2-hand-ramp（analysis/refit-200/README.md 的预注册）。C2 推广由架构线 2026-10-08 08:10Z 布置，只作 J6 旁证；门等跳费龙镜像装机后由分析线排（预留库 60000000）。

- 数据：local/data-pairings-20261008 分支的 data/pairings-20261008/pirate-t_elf-t.jsonl.gz（2000 局），解压后 sha256 `8c08df56011c24543c9c0f2bd2a21046d8849f15699c8581091e3eb687aa42f8`，即现装 `pirate-t-elf-t-{ended,act}.json` 的 info 里记录的那份。
- 核对：全量重拟（不留出、不加特征）的局面数和均值与现装逐位相同；系数在当初拟合的本机（Windows）与云端（Linux）之间有浮点差（系数最大差 9.6e-07），数据相同。
- 拟合：`python -m svsim.learn.phased --games pirate-t_elf-t.jsonl --matchup pirate-t-elf-t --hold-out-every 11 --features hand --out <本目录>`（代码 c87d51b）。

留出局上的 log loss（只看胜负，和局不计）。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 局面 | 现装* | B′ | C2 | C2 − B′ |
|---|---|---|---|---|---|
| ended | 1400 | 0.5601 | 0.5685 | 0.5683 | -0.0002 |
| act | 6260 | 0.5455 | 0.5529 | 0.5537 | +0.0008 |

文件 sha256：

    98c0b64e5d45ac5a0bfd6a09f663e655766161cc36c1afb6bd31f03f8bce1032  pirate-t-elf-t-act.json
    2cc60397f65e5378523f7390eb73d53160542797a7e6eba62dfe7398c8dacdda  pirate-t-elf-t-ended.json
