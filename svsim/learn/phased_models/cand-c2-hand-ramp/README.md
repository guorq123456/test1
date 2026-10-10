# 候选 C2：可用手牌价值（没装）

同 A200，另加 `--features hand`：`me_handplay_{face,removal,heal,draw,ramp,body}` = 我方手牌的六个角色值，每张乘 min(1, (最大 PP + 1) / 当前费用)，最大 PP + 1 封顶 10，0 费不打折。对手不加。原来的 6 个 `me_hand_*` 仍被 STOCK 屏蔽，所以打折版是唯一的手牌信息（撤屏蔽是另一个变量，不在这里）。来源：analysis/evaluator-gaps/README.md 第四节（下回合付不起的手牌）。增量门的 B = A200。

- 数据：local/data-pairings-20261008 @ bfb4aaa 的 data/selfplay-s200/ramp-t_ramp-t-s200.jsonl.gz，跳费龙（比赛版）镜像 4400 局，双方 `mcts:200+plan+learned+phased`，explore 0.03，种子 54800000，在 02e58f0 上生成。
- 划分：`--hold-out-every 11`，行号 % 11 == 0 的 400 局留出、不参与拟合（analysis/refit-200/README.md 的预注册），用剩下的 4000 局拟合。版本 2 特征，线性，2500 次迭代；我方手牌、牌库的库存特征（STOCK：me_hand_*、me_pool_*）照现装模型一样置零。
- 门：A = `mcts:N+plan+learned+phased=<本目录>` 对 B，ramp-t 镜像，定长 300 对（`--fixed --max 600`），不用 `--versus`。条件：对手卡表已知（牌序、手牌未知）。
