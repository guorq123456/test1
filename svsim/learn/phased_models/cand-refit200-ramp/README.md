# 候选 A200：200 级自对弈数据重拟合（2026-10-08，没装）

`python -m svsim.learn.phased --games ramp-t_ramp-t-s200.jsonl --matchup ramp-t-ramp-t --hold-out-every 11`，默认参数（`--q-weight 0`）。B = `level-strong`（ramp-t 镜像借原版 ramp-ramp 模型）。

- 数据：local/data-pairings-20261008 @ bfb4aaa 的 data/selfplay-s200/ramp-t_ramp-t-s200.jsonl.gz，跳费龙（比赛版）镜像 4400 局，双方 `mcts:200+plan+learned+phased`，explore 0.03，种子 54800000，在 02e58f0 上生成。
- 划分：`--hold-out-every 11`，行号 % 11 == 0 的 400 局留出、不参与拟合（analysis/refit-200/README.md 的预注册），用剩下的 4000 局拟合。版本 2 特征，线性，2500 次迭代；我方手牌、牌库的库存特征（STOCK：me_hand_*、me_pool_*）照现装模型一样置零。
- 门：A = `mcts:N+plan+learned+phased=<本目录>` 对 B，ramp-t 镜像，定长 300 对（`--fixed --max 600`），不用 `--versus`。条件：对手卡表已知（牌序、手牌未知）。
