# 跳费龙主基准

**条件**：对手卡表已知（牌序、手牌未知）。

**基准的含义**（架构线程 03:48Z 改口）：
- Salem 03:46Z 原话：「我能做的判断只有跳费龙是这个游戏当下环境里最简单的卡组，跳费龙 bot 当尺子量别人，我不知道这里初级具体指什么」。
- 所以这里的基准是：跳费龙是最简单的牌，bot 打它最接近正确。用**冻结的装机态跳费龙 bot**（9a6ea1c，v2s）当尺子，去量其他三套牌的 bot。
- 03:44Z 那版的说法（「跳费龙是主基准，所有提升报对它的 CR」）作废。

## 尺子表（2026-10-08）

- **bot 得分**：联赛重跑，全装机态（`local/pairings-20261008` @ 8a3b0c0 的 part1、part2；双方 v2s；种子库 25000000，每格 150 对、300 局）。报的是非跳费龙那一方对跳费龙的得分，95% 区间按对算。
- **CR**：Salem 刻度是 236 × logit(得分)，括号里是稳态式 800 ×（得分 − 0.5）。
- **人类对位**：从 meta 文档里找（`claude/bot-architecture-design` @ f81c821 的 `analysis/meta/`；/mnt/project-files 在这台机器上没有）。有数的就引，标出处；没有的写「无」。
- **差距** = bot 得分 − 人类对位。

| 对跳费龙 | bot 得分（95%） | CR（稳态式） | 先手 / 后手（按局） | 人类对位 | 差距 |
|---|---|---|---|---|---|
| 连击妖 | 50.7% ± 5.3% | +6（+5） | 59.3% / 42.0% | **20%**：yokidou BO10 表演赛 2:8（09-23，**调整前**，10 局），见 `v2/cn-bilibili.md`。第一版对局矩阵（`meta-decks-2026-10-07-v1.md` §7）反而写连击精灵对跳费龙「+（小优）」，是推断。 | **+31** |
| 机锋 | 51.3% ± 5.6% | +13（+11） | 54.0% / 48.7% | 无。第一版矩阵写「=（存疑）」，是推断，没有数。 | 无 |
| 旗皇 | 60.0% ± 5.4% | +96（+80） | 64.7% / 55.3% | **80%**：yokidou BO10 表演赛 8:2（10-07，调整后，10 局），见 `v2/cn-bilibili.md`、`v2/cn-en.md`。第二版 §3.6 引了这场，但把「海盗压制跳费龙」（M4、P6）收回，标〔存疑〕。 | **−20** |

- **Salem 评过的编号**：上面引的两条都不在第二版 §9 里 Salem 评过的编号中。M4、P6 已经收回；D8（狐火打宇宙鱼）Salem 写「不确定」，它不是胜率，不引。
- **人类对位的不确定性很大**：两条都只有 10 局，是创作者表演赛，不是比赛。Wilson 95% 区间：2/10 是 6%～51%，8/10 是 49%～94%。
  - 用区间相减粗算，差距的范围是：连击妖 −6～+50，旗皇 −40～+16。两个都跨 0。
  - 连击妖那场还是 09-29 平衡调整之前打的。
- **预登记读法**（架构线程 03:48Z）：差距最负的那套牌，就是 bot 打得最差的牌，提升资源先给它。
  - 时间说明：bot 得分在这条读法定下之前已经报过（deck-league 050cab6）；人类对位是现在才查的。
  - **按字面：旗皇**（−20，唯一的负值）。
  - 但旗皇的差距区间跨 0，人类数只有 10 局；机锋没有人类数，排不进来。所以这个排序的把握很低。
  - 要让这一列能用，需要更多人类对位数据（例如 Salem 自己的对局记录，或比赛的对局统计）。

## 数据指引（给 Salem：自己上手看数据）

Salem 03:52Z：「具体水平问题你到时候指引我去对应的分支，我去分析数据」。这一节随数据更新，每次报「水平」都会引用它。

**条件**：所有对局都是对手卡表已知（牌序、手牌未知）。

### 拉数据

```
git fetch origin ccr-da4857cc-rkpgwr local/pairings-20261008 local/mull-20261008 local/data-pairings-20261008 data/pairings-20261008
git checkout ccr-da4857cc-rkpgwr
```

- 第二行检出的是 test1 的分支，脚本和云端跑的数据都在里面。
- 其他分支的文件不用检出，用 `git show 分支:路径 > 本地文件名` 取出来就行，例如：
  `git show origin/local/pairings-20261008:analysis/local-runs/league-after-20261008-part1.jsonl.gz > part1.jsonl.gz`

### 每份数据

| 用途 | 分支 | 提交 | 路径 |
|---|---|---|---|
| 联赛基线：f631e14 的 bot，10 格 × 300 局 | ccr-da4857cc-rkpgwr | f1ab6d3，镜像第二局 17d294d | `analysis/deck-league/league_v2s_f631e14.jsonl.gz`、`league_v2s_f631e14_mirror2.jsonl.gz` |
| **联赛重跑，装机态（尺子表用的）** | local/pairings-20261008 | 8a3b0c0 | `analysis/local-runs/league-after-20261008-part1.jsonl.gz`（8 格）、`-part2.jsonl.gz`（跳费龙对旗皇） |
| 用时基线：本机 f631e14，每格 20 对 | local/pairings-20261008 | 352dd60 | `analysis/local-runs/league-base-timing-20261008.jsonl.gz` |
| 2×2：旗皇对连击妖，模型 × 起手 | local/pairings-20261008 | 233f391 | `analysis/local-runs/league-after-20261008-x-nomodel-R.jsonl.gz`、`-x-model-D.jsonl.gz` |
| 云端单格重跑：连击妖镜像、旗皇镜像、连击妖对跳费龙 | ccr-da4857cc-rkpgwr | 1497eb0、b1f7241、c150726 | `analysis/deck-league/league_v2s_3effa47_*.jsonl.gz`、`league_v2s_81c4660_*`、`league_v2s_d9b26e7_*` |
| 起手门（R 对 D），云端 | ccr-da4857cc-rkpgwr | ade248f | `analysis/tournament-audit/mull_gate_elf_sprt_c962055.jsonl` |
| 起手门，本机 | local/mull-20261008 | cd65fed | `analysis/tournament-audit/local/mull_*.jsonl`（同目录有各自的 report） |
| 配对模型门，本机 | local/pairings-20261008 | 8a3b0c0 | `analysis/local-runs/<卡组>_<对手>[.0/.1].sprt`、`.fixed`（结果表在同目录的 README.md） |
| 早期评测台（v1、v2 的门） | ccr-da4857cc-rkpgwr | — | `analysis/gate-runs/*.jsonl`（README.md 里有每个文件的 A、B、种子和结果） |
| 自对弈，云端：4 个配对 × 2000 局，v2 | data/pairings-20261008 | b0a37df | `data/pairings-20261008/*.jsonl.gz`（同目录 README.md） |
| 自对弈，本机：7 份 × 2000 局，v2 | local/data-pairings-20261008 | d58a27c | `data/pairings-20261008/*.jsonl.gz`（README.md 写了每份的种子、当时的构建提交、拟合出的模型） |
| 本节的审计：抽的点和结果 | ccr-da4857cc-rkpgwr | — | `analysis/ramp-benchmark/` |
| 种子库登记 | ccr-da4857cc-rkpgwr | — | `analysis/seed-banks.md` |

### 记录格式

**联赛**（`league_*.jsonl.gz` 和 `league-after-*.jsonl.gz`，gzip，一行一局）：
- `pair`：「前一个卡组/后一个卡组」，例如 `elf-t/ramp-t`。
- `k`：第几对，0～149。种子 `seed` = 25000000 + k。
- `seat_a`：前一个卡组坐的座位（0 或 1）。一对就是同一个种子打两局，换座位；镜像的第二局还交换双方 agent 的种子。
- `first`：先手的座位。
- `winner`：赢家的座位；null 是平局。前一个卡组的得分：`winner == seat_a` 记 1，平局记 0.5。
- `turns`：总回合数，双方合计。`seconds`：这局的墙钟秒数。`agent_seeds`：两个座位 agent 的种子。
- `record`：完整对局：
  - `names`：两个座位的卡组名；`decks`：两个座位的 40 张卡号；
  - `ai`：「座位 0 的 agent 串 / 座位 1 的」，v2s = `mcts:200+plan+learned+phased`；
  - `actions`：每一步动作，按顺序。`Mulligan` 的 `indices` 是换掉的手牌位置；`PlayCard` 的 `uid` 是出的牌，`targets` 是目标；`Attack` 是 `attacker` 打 `target`；`Evolve` 的 `super_` 为真表示超进化；还有 `EndTurn`、`UseBonusPP` 等。目标是负数时指主战者：−1 是座位 0，−2 是座位 1。
  - 用 `svsim.tools.records.start(record)` 可以得到开局局面，再按 `actions` 一步步走，就能复盘任何一步。

**起手门**（`mull_*.jsonl`，一行一对）：
- `k`、`seed`、`opp`（对手）、`opp_way`（对手的起手方式）、`deck`（被测卡组）；
- `seat0`、`seat1`：被测卡组坐这个座位时的两局，R 和 D 各一局，各有 `points`（得分）、`first`（是否先手）、`turns`、`seconds`、`redraw`（[R 换的位置, D 换的位置]）；
- `differ`：这个座位上 R 和 D 换的牌是否不同。

**配对模型门和评测台**（`*.sprt`、`*.fixed`、`gate-runs/*.jsonl`，一行一对）：
- `k`、`seed`；
- `points`：A 在两局里的得分；
- `b_points`：用 `--versus` 时 B 在同样两局里的得分（A、B 都打同一个 C）；
- `same`：A、B 在同一副发牌、同一座位上着法是否完全一样。

**自对弈**（`data/pairings-20261008/*.jsonl.gz`，`learn.netdata` 的输出，一行一局）：
- 和联赛的 `record` 字段一样：`seed`、`first`、`decks`、`actions`、`winner`、`ai`。另外还有：
- `names`：两个座位的卡组名。`deck_keys`：查对局模型用的卡组键。
- `search`：和 `actions` 一一对应。
  - null：这一步没有搜索，比如换牌、只有一个合法动作，或者由必杀检查、规划器直接给出；
  - 否则是这一步搜索的根：`visits` 是各候选动作的访问次数，`value` 是根的胜率估计，`center` 是评估的中心值。
- `turn_starts`：每个回合开始时的快照。`i` 是这回合第一步在 `actions` 里的位置，`player` 是谁的回合，`hand` 是手牌 uid，`deck` 是牌库 uid（最后一个是牌库顶）。
- `g`：第几局。`explore`：随机探索比例，0.03 表示 3% 的步随机走。`agent_seeds`、`rng_seed`、`deck_hashes`（卡组哈希）、`date`。

### 复现命令

下面三个脚本只用标准库，不需要 svsim。在 test1 分支的根目录执行：

```
# 尺子表的一行，以连击妖为例
python3 analysis/deck-league/compare_cell.py --pair elf-t/ramp-t 重跑=part1.jsonl.gz
# 旗皇那格写作 ramp-t/pirate-t，报的是跳费龙的得分：旗皇的得分 = 100% − 它，先手、后手也要对调
python3 analysis/deck-league/compare_cell.py --pair ramp-t/pirate-t 重跑=part2.jsonl.gz

# 格级对照表：重跑对基线，连击妖几格注明起手 D→R，用时对本机的用时基线
python3 analysis/deck-league/compare_league.py 基线=analysis/deck-league/league_v2s_f631e14.jsonl.gz+analysis/deck-league/league_v2s_f631e14_mirror2.jsonl.gz 重跑=part1.jsonl.gz+part2.jsonl.gz --note "elf-t=起手 D→R" --timing-base timing.jsonl.gz

# 起手门：几份合成一个样本
python3 analysis/tournament-audit/mulligan_gate.py --report 第一份.jsonl 第二份.jsonl --pool
```

- `part1.jsonl.gz`、`part2.jsonl.gz`、`timing.jsonl.gz` 是用上面的 `git show` 从本机分支取出来的文件。
- 要复盘某一局的某一步，需要 svsim：检出构建提交（例如 9a6ea1c），在那个目录里 `PYTHONPATH=.`，用 `svsim.tools.records`。

## 深搜 vs 浅搜分歧审计（2026-10-08）

### 第二版设计（架构线程 03:48Z，现行）

**目的**：看 bot 在哪套牌上「想得越深、走法越不一样、差得越多」，同时检验 Salem 的论断「跳费龙最简单」。

**局面**：全部取自联赛重跑（全装机态，part1、part2）里三套牌对跳费龙的对局，共 400 个决策点：
- **连击妖、机锋、旗皇各 100 个**：取那一方自己的决策点，来自它对跳费龙的那一格；
- **跳费龙 100 个作对照**：取跳费龙一方的决策点，来自同样三格，但只用三套牌的样本没用过的局，免得同一局两边都抽；
- 每套牌按自己的回合段分层：前期 1～4 取 34 个，中期 5～7、后期 8+ 各 33 个；
- 每局每段最多 1 个，所以每局最多 3 个；局按固定种子打乱后逐局取。

**方法**：和第一版一样。在同 8 个确定化上，v2 的走法对 mcts:800 的走法，余下这一回合由 v2s 打完，算配对遗憾；类型的分法和先后不变（见下面第一版）。

**噪声底**：从这 400 个点里用固定种子抽 50 个，两个不同种子的深搜各选一步。

**给 Salem 的 10 个局面**：连击妖、机锋、旗皇各取遗憾最大的 3 个，跳费龙取 1 个，写法和第一版一样，写在 `ramp_shallow_deep_top10.md`。

**预登记**（开跑前写下，结果出来后不改）：
1. 类型那两条照旧（见下面第一版的预登记）：分母是遗憾 ≥ 0.10 的全部点（四套牌合在一起），另外每套牌也分开报一次。
2. **新加一条**（架构线程 03:48Z）：分歧率和平均遗憾各按牌排序，两个指标分开判。
   - 跳费龙最低，而且它的 95% 区间上沿低于次低那套牌的 95% 区间下沿：报「支持 Salem：跳费龙最简单」；
   - 否则报「不支持或分不开」。
   - 分歧率的区间用 Wilson；平均遗憾的区间按点算（正态近似，没分歧的点遗憾记 0）。

### 第一版设计（架构线程 03:44Z，已被第二版替代）

第一版的 300 个跳费龙决策点（跳费龙镜像自对弈 75 个，加上跳费龙对三家各 75 个）在改口之前已经开跑。跑完的结果只放在本节末尾当附录，不用来判读。下面这些写法是第二版沿用的部分。


**目的**：把「初级」落到具体的走法类型上，并挑出给 Salem 看的局面。脚本是 `shallow_deep.py`。

### 局面

约 300 个决策点，都是跳费龙一方的决策点（合法动作多于一个）。四个来源各 75 个：

| 来源 | 文件 | 当时的代码 | 走子的 bot |
|---|---|---|---|
| 跳费龙镜像 | 本机自对弈：`local/data-pairings-20261008` @ d58a27c 的 `data/pairings-20261008/ramp-t_ramp-t.jsonl.gz`（2000 局，探索 0.03） | c47449d | v2 |
| 连击妖对跳费龙 | 联赛重跑 part1（`local/pairings-20261008` @ 8a3b0c0） | ≥ 7d219cc | v2s |
| 机锋对跳费龙 | 同上 | 同上 | v2s |
| 跳费龙对旗皇 | 联赛重跑 part2（同一提交） | 9a6ea1c | v2s |

**怎么抽**：
- 「回合」指跳费龙自己的第几回合。按回合段分层：前期 1～4、中期 5～7、后期 8 以后，每个来源每段 25 个。
- 游戏按固定种子打乱后逐局看，每局每段最多取 1 个点，所以每局最多 3 个点。
- 抽样只依赖种子，可以重抽出同一批点。

### 方法

沿用 Salem 失误分析的配对遗憾，跑在 9a6ea1c 上，全装机态。在每个决策点：
- **浅**：v2（`mcts:100+plan+learned+phased`）整个 agent 选一步；
- **深**：`mcts:800+plan+learned+phased` 整个 agent 选一步；
- 两步用 `search.mcts.action_key` 比，相同就算没有分歧，遗憾记 0；
- 不同时，在同 8 个确定化上，两步各走一遍。确定化是从跳费龙一方看，对手没见过的牌按已知卡表发。这一回合剩下的部分由 v2s（整个 agent）打完，两条线用同一个随机种子；
- 回合结束时的局面，用 v2s 自己的评估（分对局模型，turn-end）估一次胜率；局在这回合结束的，用结果；
- **遗憾 = 深那步之后的胜率 − 浅那步之后的胜率**，8 次平均，以胜率计（0.10 = 10 个胜率点）。负数表示浅那步反而更好。

**噪声底**：从同样的 300 个点里，用固定种子随机抽 50 个，让两个不同种子的深搜（`mcts:800`）各选一步。用同样的办法算遗憾（种子 A − 种子 B），看分歧率和遗憾的分布。

**报告**：
- 分歧率，按回合段；
- 遗憾的分布（中位、p90、平均，≥ 0.05 和 ≥ 0.10 的占比）；
- 遗憾 ≥ 0.10 的点按类型归类，每类的数量和平均遗憾；
- 遗憾最大的 10 个局面，写给 Salem 看（`ramp_shallow_deep_top10.md`）：每个局面写清浅搜怎么走、深搜怎么走、差多少，不写哪个对。

### 类型怎么分（开跑前定下，按下面的先后，第一条符合的为准）

看的是两边各自的第一步（浅那步 a、深那步 b）：

1. **③ 进化 / 超进化时机**：a、b 有一个是进化或超进化。
2. **④ 留牌 / 不出牌**：一个是结束回合，另一个是出牌。
3. **① 跳费 vs 铺场 / 抢节奏**：一个出的是跳费牌，另一个不是跳费牌（出别的牌，或者攻击）。跳费牌按 `search.race.ramps` 判定：前期打出会提高 PP 上限的牌。
4. **② 换血 vs 打脸**：两个都是攻击，一个打对手主战者，一个打随从。
5. **⑤ 出哪张 / 先后**（我加的）：两个都是出牌（都不是跳费牌，或者都是跳费牌），或者一个出牌一个攻击，也就是出哪张、目标是谁、先出牌还是先攻击。
6. **⑥ 其他**（我加的）：上面都不符合，例如攻击与否（攻击对结束回合）、两个攻击打的是不同的随从、用额外 PP。

### 预登记（架构线程 03:44Z 定，开跑前写下，结果出来后不改）

- 占比的分母是遗憾 ≥ 0.10 的全部点，包括 ⑤⑥。
- ①～④ 里某一类占比 ≥ 40%：报「系统性弱点在该类」。
- ①～④ 四类都在 15%～35% 之间：报「无单一类型主导」。
- 两条都不满足时，照实报各类占比，不下这两种结论。
- ⑤ 或 ⑥ 占比 ≥ 40% 时也照实报出来：那说明四类的分法没抓住主要的分歧。
- 遗憾 ≥ 0.10 的点可能只有一二十个。占比的区间会很宽，所以报占比的同时报个数。
