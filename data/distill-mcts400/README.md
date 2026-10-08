# mcts:400 自对弈记录和用它拟合的两个模型（2026-10-07）

条件：对手卡表已知（牌序、手牌未知）。

## `games_s400.jsonl.gz`：500 局

- 卡组：两边都是 Game8 跳费龙（`ramp`，`cards.decks.RAMP_DRAGON`），是镜像。记录里没有 `names` 字段，当时还没记卡组名。
- bot：两边都是 `mcts:400+plan+learned+phased`，即 v2 的搜索加到 400 次迭代。
  - 用的模型是当时装着的 `ramp-ramp-{ended,act}.json`（v2 的模型）。
  - 3% 随机走子（`explore` 0.03，第一回合不随机）。
- 命令：`python -m svsim.learn.netdata --games 500 --agent "mcts:400+plan+learned+phased" --workers 4 --seed 18000000 --out games_s400.jsonl`。
  - 4 个 worker 共 1767 秒。
  - 生成开始于 2026-10-07 10:47Z 前后，当时的分支头是 976d106。
- 种子：`--seed 18000000`。第 g 局（g = 0…499）：
  - 发牌种子 `seed` = 18000000 × 100003 + g = 1800054000000 + g，就是记录里的 `seed` 字段，所以也可以说是"种子 18000540"开头的那批；
  - 随机走子的种子 = 18000000 × 7919 + g；
  - 两边 agent 的种子 = 18000000 × 1000 + 2g + {0, 1}。
- 每局一行，字段：`decks`、`seed`、`first`、`first_arg`、`actions`、`winner`、`ai`、`version`（记录格式 1）、`explore`、`g`、`date`、`search`。这批生成早于 `turn_starts` / `rng_seed` / `agent_seeds` / `deck_keys` 那些字段，所以记录里没有它们。
- 解压后 sha256 = `6cd44e3c7711e80c7eea1381536575c58e699cc65c85328d878ce8719d2997e2`（3830675 字节）。

### `search` 字段怎么读

- `record["search"][i]` 和 `record["actions"][i]` 一一对应。
- 值为 `null`：这一步没有搜索树可记，比如斩杀检查或规划器直接选的走法、换牌。
- 否则是 `{"visits": [...], "value": v, "center": c}`（`svsim/learn/netdata.py` 的 `_thought`）：
  - `visits`：这一步每个合法走法在根节点的访问次数，顺序是 `engine.legal_actions(state)` 的顺序。重放到这一步、取合法走法列表，就能一一对上。这是策略头的训练目标 π（`learn.policy.decisions` 读它）。
  - `value`：搜索给访问最多那个走法的估值（`search.estimate(best)`），是 0～1 之间压缩过的胜率估计。
  - `center`：根局面的评分，`value` 就是相对它压缩的。
  - 换回 logit 的公式见 `netdata.py` 里读它的那段：`z = log(v/(1−v))/gain + center/(8·gain)`。`learn.phased` 的 q 标签（`--q-weight`）用的就是它。
- 重放：`svsim.tools.records` 按 `decks` + `seed` + `first` 发牌，按 `actions` 逐步走。

### 和本机 d58a27c 那份的比对

本机分支 `local/data-pairings-20261008` 的 d58a27c 里有 `analysis/selfplay/v2-mcts400-500games.jsonl.gz`，解压后和本文件逐字节相同：sha256 一样（`6cd44e3c…97e2`），500 局里每局的 `seed`、`actions`、`search` 都一样。所以是同一批数据，不是另跑的一批。两个 .gz 文件本身的哈希不同，只是压缩时的文件头不同。

## `phased400/`：用这批数据重拟合的分阶段模型（候选，没装）

- `ramp-ramp-ended.json`、`ramp-ramp-act.json`，版本 2 特征。
- 用 `python -m svsim.learn.phased --games games400.jsonl --q-weight 0.5` 在这 500 局上拟合：胜负标签和搜索 q 值各占一半。
- 局面数：回合结束 8877，回合中 31373。
- 训练集上的数（没有留出）：loss 0.6034 / 0.6132，value_accuracy 66.0% / 65.5%。

## `pol400/`：用这批数据蒸馏的策略头（候选，没装）

- `ramp-ramp.npz`，是 `learn.policy.PolicyNet`：一层 tanh 64，局面用汇总特征，走法按类别、来源牌、目标编码。
- 对 500 局里 22411 个搜索决定的访问分布 π 做交叉熵，拟合记录的交叉熵是 1.376。
- 在搜索里用 `+prior` 接入，见 `docs/architecture.md` 的策略先验一节。
