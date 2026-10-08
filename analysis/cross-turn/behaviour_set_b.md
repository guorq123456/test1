# 给构建会话的材料：Salem 的 27 局和行为验收局面集（(b) 的 B 方案）

**条件**：对手卡表已知（牌序、手牌未知）。牌名写常用名（费用身材）。

## 1. Salem 的 27 局

- **文件**：`analysis/mirror-regression/salem_games.json`。
  - `records` 是对局号到整局记录的映射（tools.records 格式：`decks`、`seed`、`first`、`actions`、`winner` 等）。
  - `meta` 是每局的批次、对手 bot 和胜负。
  - `source` 是来源说明。
- **哪一方是 Salem**：每一局都是 **0 号位**。1 号位是网页上的 bot。
- **组成**：全部是跳费龙镜像（Game8 版的 `ramp`）。
  - 10 局是 2026-10-06 下午的，来自 `positions.json`，对手是旧 bot `mcts:200+plan+learned`；
  - 17 局来自架构分支 d0117bf 的 `analysis/salem-games`：10 局是 10-06 晚上对旧 bot，7 局是 10-07 对 v2s（`mcts:200+plan+learned+phased`）。
- **筛选方式**：
  - **节奏统计**（`pacing.py --salem`）：27 局全用，不剔除，只取 0 号位。按"全部局"和"长局（双方合计 24 回合以上）"分组。
  - **进化表和探针**（`evolve_targets.salem_turns`、`turn_row`）：取 0 号位每个主阶段回合，只看能进化的回合（本回合有合法的进化动作，或者他进化了）。
  - 不算"出了正义、整回合没进化"的回合。Salem 裁定那是正义的另一种用法，和进化一样强，不是留点（`erntz_unevolved`，12 个）。
- 拿去做搜索先验时，局面特征不许用卡牌 id，这是构建会话那边的约束，这里只是提一句。

## 2. 行为验收局面集（`behaviour_set_b.json`，由 `behaviour_set.py` 生成）

一共 34 个局面：

| 组 | 个数 | 说明 |
|---|---|---|
| 留点 | 24 | 验收表里的 evolve_hold，全部计入 |
| 关键格的花点 | 9 | "A 档在手、够不着"（按实际出法）里他进化的回合，全在他自己的第 4～5 回合，7 次进化佐伊（5费 5/5） |
| 只在"按局面可能"下才进关键格的花点 | 1 | 1791316841837 第 6 回合，进化佐伊；单独标出，用来算第二种定义 |

**每个局面的字段**：
- `game`、`at`：局面怎么还原。`records.start(records[game])`，再依次执行 `records[game]["actions"][:at]`，这时轮到 0 号位（Salem）行动。
- `own_turn`、`first`、`global_turn`、`pp`、`ep_sep`。
- `salem`：他的选择，"留（不进化）"或"花：进化 X"。
- `a_cards_in_hand`：手里的 A 档牌。
- `cell_by_line_played`：**按实际出法**。他那条线上场上有没有 A 档可以进化，是验收表现在的口径。
- `cell_by_position`：**按局面可能**，本回合任何合法出法都够不着才算。算法和 1 号分叉一致（`hold_vs_spend.new_cell`）：场上还没进化的随从，或者手里费用 ≤ 本回合 PP 的随从（最大 PP，加上可用的额外 PP），算够得着。层级不变：A 档够得着 → 最好只够得着 B 档 → A 档在手、够不着。
- `payoff_in_hand_out_of_reach`、`normal_only`：验收表里另外两格。
- `probe_id`、`category`、`check`：对应 `evolve_probes.json` 里的探针。evolve_hold 要求不进化，evolve_use 要求进化。

分档（我的组）：A 档是班德（9费 9/9）、正义（10费 8/8）、金银（8费 6/6）；B 档是波菈莱（2费 0/2）、牢头（7费 5/6）、琪米卡（2费 2/1）、口人魔。

**两种定义下关键格的样本**：
- 按实际出法：留 12 个、花 9 个。
- 按局面可能：留 3 个、花 6 个。原来那 9 个花点里有 5 个，加上标出的那 1 个。
- 原来 12 个留点回合里，有 9 个在局面上其实下得起 A 档或 B 档的目标。
- 架构线程 21:41Z 定：整张验收表暂时不按新定义重标，两种定义并排报。

## 3. 分辨力怎么算

1. **跑探针**：候选 agent 从这一回合开头接手，打完这一回合，看有没有进化。每个局面 5 个种子。

   ```
   cd <svsim 检出目录> && PYTHONPATH=. python3 <test1>/analysis/mirror-regression/check.py \
       <test1>/analysis/mirror-regression/evolve_probes.json "<候选的 arena spec>" 5 > results_cand.txt
   ```

   跑全部 114 条探针约十几分钟。也可以用 `--ids` 只跑这 34 个的 `probe_id`。
2. **在这个集合上打分**，两种定义都给。第一个结果文件是基线，v2 的在仓库里：

   ```
   python3 analysis/cross-turn/behaviour_set_score.py analysis/cross-turn/behaviour_set_b.json \
       v2=analysis/mirror-regression/results_evolve_v2_2ab3a8d.txt cand=results_cand.txt
   ```

   - **分辨力** = Salem 留的回合的忍住率 − Salem 花的回合的忍住率 = evolve_hold − (100 − evolve_use)，在关键格里算。
   - 和基线的差：在格内重抽局面 4000 次，给 95% 区间。
3. **整张验收表**（各格的 evolve_hold、evolve_use 和分辨力，用全部 24 + 78 条探针，按实际出法）：

   ```
   python3 analysis/cross-turn/evolve_hold_review.py analysis/mirror-regression/salem_games.json \
       analysis/mirror-regression/evolve_probes.json --results v2=<v2 结果> --results cand=<候选结果> \
       [--selfplay v2 <v2 自对弈记录> --selfplay cand <候选自对弈记录>]
   ```

**现有基线**（关键格，按实际出法 / 按局面可能）：
- v2：+50 / +83
- v2s：+42 / +63
- b3：+52 / +97

**验收规矩**（架构线程 18:51Z）：
- 候选在关键格的分辨力必须明显高于 v2。只是这一格整体多忍，不算过。
- 硬规则：自对弈 bot 一侧，"A 档够得着"的忍住率不得高于 v2 的 16%。
- 另外看 erntz_unevolved 探针（12 条）不掉。
