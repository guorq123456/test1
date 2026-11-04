# 候选 C2 推广：可用手牌价值（没装）：pirate-t-pirate-t

组合 pirate-t-pirate-t（我方-对方），只用我方一侧的局面（`--matchup pirate-t-pirate-t`）。加 `--features hand`（6 维，见 learn.features.EXTRAS）；版本 2 线性，2500 次迭代，STOCK（me_hand_*、me_pool_*）置零，`--hold-out-every 11`（行号 % 11 == 0 的局留出、不参与拟合）。做法同 cand-c2-hand-ramp（analysis/refit-200/README.md 的预注册）。C2 推广由架构线 2026-10-08 08:10Z 布置，只作 J6 旁证；门等跳费龙镜像装机后由分析线排（预留库 60100000）。

- 数据：local/data-pairings-20261008 分支的 data/pairings-20261008/pirate-t_pirate-t.jsonl.gz（2000 局），解压后 sha256 `54bba6c4368c19b445cdc49e97ac5e973646dd9706f9acb52c4d31dfbabbfce5`，即现装 `pirate-t-pirate-t-{ended,act}.json` 的 info 里记录的那份。
- 核对：全量重拟（不留出、不加特征）的局面数和均值与现装逐位相同；系数在当初拟合的本机（Windows）与云端（Linux）之间有浮点差（系数最大差 2.5e-02（ended）/ 6.6e-04（act）），数据相同。
- 拟合：`python -m svsim.learn.phased --games pirate-t_pirate-t.jsonl --matchup pirate-t-pirate-t --hold-out-every 11 --features hand --out <本目录>`（代码 c87d51b）。

留出局上的 log loss（只看胜负，和局不计）。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 局面 | 现装* | B′ | C2 | C2 − B′ |
|---|---|---|---|---|---|
| ended | 2884 | 0.5990 | 0.5972 | 0.5974 | +0.0002 |
| act | 12295 | 0.6008 | 0.6034 | 0.6038 | +0.0004 |

文件 sha256：

    9cb37f3d7dd8ab25a2595b95a48ff2e3b5fb8d99e011f19255f693058f3ee36a  pirate-t-pirate-t-act.json
    e4a091d542f7c79ab2261571d504f580b49e419b57e44f9fa39b2268e53b18f4  pirate-t-pirate-t-ended.json
