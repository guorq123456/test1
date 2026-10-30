# 候选 A200′：同 A200，标签一半用 200 级搜索的 q 值（没装）

同 A200，另加 `--q-weight 0.5`。回合结束的局面没有搜索值，所以回合结束模型和 A200 的一样；只有回合中模型不同。B = `level-strong`。

- 数据：local/data-pairings-20261008 @ bfb4aaa 的 data/selfplay-s200/ramp-t_ramp-t-s200.jsonl.gz，跳费龙（比赛版）镜像 4400 局，双方 `mcts:200+plan+learned+phased`，explore 0.03，种子 54800000，在 02e58f0 上生成。
- 划分：`--hold-out-every 11`，行号 % 11 == 0 的 400 局留出、不参与拟合（analysis/refit-200/README.md 的预注册），用剩下的 4000 局拟合。版本 2 特征，线性，2500 次迭代；我方手牌、牌库的库存特征（STOCK：me_hand_*、me_pool_*）照现装模型一样置零。
- 门：A = `mcts:N+plan+learned+phased=<本目录>` 对 B，ramp-t 镜像，定长 300 对（`--fixed --max 600`），不用 `--versus`。条件：对手卡表已知（牌序、手牌未知）。

**在 v2s 下与 A200 对局逐步相同，q 标签未被检验。**
- **原因：** 回合中（ACT）模型只在 bot 推演了对手回合、又回到自己回合开始时才会被调用。具体有三处：
  - `search.mcts` 的 `mcts-reply`：叶子上推演对手回合后 `me_next=True`；
  - `agents.crossturn_agent`（`+cross`）；
  - `agents.sim_mulligan`（`mull=sim`）。
- **其他局面都用回合结束（ENDED）模型：** 包括 `mcts` 回合中途的叶子在内，一律传 `player_moves_next=False`。
- **门里的设置：** v2s（`mcts:200+plan+learned+phased`）没有 reply、没有 `+cross`，跳费龙换牌也不是 `sim`，所以只换 act 模型对局面不起作用。
- **门的结果：** 分析线 b4dc74a 里，A′ 门和 A200 门的 300 对逐对相同。
- **以后：** 要检验 q 标签，得在会调用 act 模型的配置下测。
