# 候选 C1：节奏差（没装）

同 A200，另加 `--features tempo`（learn.features.EXTRAS）：`me_tempo` = min(对手下回合最大 PP, 10) − 我这回合最大 PP，`me_tempo_x_mid` = 它 × [自己第 5～7 回合]，`me_tempo_x_late` = 它 × [第 8 回合以后]。来源：analysis/evaluator-gaps/README.md 第四节（后手方被高估）。增量门的 B = A200（`mcts:200+plan+learned+phased=cand-refit200-ramp`）。

- 数据：local/data-pairings-20261008 @ bfb4aaa 的 data/selfplay-s200/ramp-t_ramp-t-s200.jsonl.gz，跳费龙（比赛版）镜像 4400 局，双方 `mcts:200+plan+learned+phased`，explore 0.03，种子 54800000，在 02e58f0 上生成。
- 划分：`--hold-out-every 11`，行号 % 11 == 0 的 400 局留出、不参与拟合（analysis/refit-200/README.md 的预注册），用剩下的 4000 局拟合。版本 2 特征，线性，2500 次迭代；我方手牌、牌库的库存特征（STOCK：me_hand_*、me_pool_*）照现装模型一样置零。
- 门：A = `mcts:N+plan+learned+phased=<本目录>` 对 B，ramp-t 镜像，定长 300 对（`--fixed --max 600`），不用 `--versus`。条件：对手卡表已知（牌序、手牌未知）。
