# 斩杀包（`+lethal3`）的等算力门：预注册（架构线程 2026-10-10 06:27Z 布置；写在任何门的对局之前）

**条件**：对手卡表已知（牌序、手牌未知）。

**改动**（建造线 715230d，说明在它的 `analysis/speed/LETHAL.md`「+lethal3」一节）：`+lethal3` = `+lethal2` + `+plannerfix` + `+eot`。
- `+lethal2`：计数器建模（ticker），加更深的筛（near 2000 节点、差 4 以内；3000 节点）。现在带有最大 PP 的修正（80d47ff），以及「计数器计划在引擎里打不出来时，退回不带计数器的规划器」的修正。所以 `+lethal2` 底下的代码和 23b317d 略有不同。
- `+plannerfix`：普通规划器按实际在场的 PP 量卡，优先打脸。
- `+eot`：规划器把我方随从的回合末伤害算进去。
- 建造线的离线结果（在每个开头上直接跑 LethalAgent 的检查）：
  - 原版跳费龙镜像（6f11111，18,892 个开头）：找到的斩杀 755 → 904；27 个当回合没打出来的找回 21 个；0 丢失；每个开头多 +5.1 ms（p90 +8.1）。
  - 海盗镜像（80 局）：60 → 76；4 个找回 4 个；0 丢失；+6.9 ms（p90 +21.8）。
- `+lethal2` 那道门（6e468ba）留作记录。装机候选现在是 `+lethal3`，仍要 Salem 本人的话。

## 改动（2026-10-10 07:45Z；在门的任何对局之前）

- **svsim 从 715230d 换成建造线 850237d**。中间带上了 9c1bb01：realize 修正。
  - 修了什么：规划器的计划落成真实动作时，同样的几张随从按「还剩几次攻击」和「能打到哪儿」配对，进化就落在还没攻击过的那张上（跳费龙镜像 g127）。
  - 只在 `face_first` 那条路上生效，也就是 `+plannerfix / +tick / +lethal2 / +lethal3`。普通的 realize 一行没动。
  - 715230d → 850237d 之间 svsim 里只改了 `svsim/search/combo.py`（这一处），另外新加了候选 A 的模型文件。所以 B（`mcts:N+plan+learned+phased`）和 `level-strong` 走的代码不变。
  - 建造线在 518b12f 用修过的版本重跑了离线检查：跳费龙镜像找到 905 个斩杀（原 904），27 个没打出来的找回 22 个（原 21），0 丢失；海盗镜像不变。
- **理由**：装机候选现在是修过的这一版。拿 715230d 过门，测的是一个已知有毛病、不会装的版本。
- **不变的**：两格、种子、N_B 起点 203、复核规矩、两个门槛、J35 / J36、另报各项。
  - 附带脚本的两种检查（`check3`）跟着用 850237d 的 `combo.planned_lethal`。
  - 下面「命令」里的 `<svsim 715230d>` 读作 `<svsim 850237d>`。

## A、B 和两格

- **A** = `level-strong+lethal3`。
- **B** = `mcts:N_B+plan+learned+phased`：`level-strong` 只调迭代次数，让每回合的毫秒数相同。每格各自复核。
- **两格**，各定长 300 对，直接对打，`--fixed --max 600`：
  - **原版跳费龙镜像**（`--deck ramp --opponent ramp`，陪练的那一格，斩杀包在这里作用最大），种子 **66700000～66700299**；
  - **海盗镜像**（`--deck pirate-t --opponent pirate-t`），种子 **66710000～66710299**。
- **等算力**（每格照惯例复核一次）：
  - 起点 N_B = 203：两格的每回合开头各多 5.1 / 6.9 ms，都约是一回合的 1.5%～2%。上一道门用同样的起点，复核比值是 1.000。
  - 复核：门命令 `--fixed --max 40`，20 对；跳费龙镜像的种子 66790000～66790019，海盗镜像 66791000～66791019。A ÷ B 的每搜索决策毫秒比在 0.97～1.03 之外，就修一次 N_B = round(203 × 毫秒比)。
  - 复核和门在同一个容器、同样的进程数下跑。
- **机器**：分析线的云容器（Linux，4 个 CPU），3 个 worker，经 `svsim.tools.host`；svsim 建造线 ~~715230d~~ **850237d**（见上面的改动）。排在 M2、M4 之后。

## 两个门槛（都写在跑之前）

- **(S) 标准门**：两格合并（逐对，按格分层重抽 4000 次，`analysis/oracle-hand/pooled.py`）的下沿 > 50%。
- **(NI) 不伤**，三条都要成立：
  - 每格的下沿 ≥ 46%（正态区间，同门的报法）；
  - 两格合并的下沿 ≥ 47.5%；
  - 谜题 pirate-flags-lethal 在本容器上由 A 在种子 1～3 都解出。
- 只报、不进判定：谜题 pirate-flags-setup 在种子 1～3 上，A 没有打出、也没有宣称斩杀（建造线的测试里有这一条；这题按 Salem 那条线的完整枚举没有斩杀）。

**两个门槛各自过的概率**（正态近似；两格真实效果相同）
- 海盗镜像的对分标准误按上一道门实测的 0.92 个百分点（一对九成一胜一负）；跳费龙镜像按以往门的区间 ±2.8～±3.4 取 1.4～1.75。
- 合并后的标准误约 0.84～0.99。

| 真实效果 | (S) 合并下沿 > 50% | (NI) 统计那几条 |
|---|---|---|
| 0 | 2%～3% | 59%～77% |
| +1 个百分点 | 17%～22% | 81%～94% |
| +3 个百分点 | 86%～95% | 98%～99.9% |

- (S) 要合并的点估计约 51.7%～51.9%。
- (NI) 里最紧的一条通常是跳费龙镜像那格的「下沿 ≥ 46%」（那一格标准误最大）。
- 照记：真实效果是 0 时，(NI) 也有六到八成会过，所以它量的是「没有明显变差」，不是「变好了」。合并下沿取 47.5% 是架构线程提的数，这里照用，功效如上。

**判断**（分析线，按上面的算法）
- 真实效果取：跳费龙镜像以 +0.8 为中心、海盗镜像以 +0.5 为中心，各自标准差 1、相关 0.5。
  - 依据（推断）：跳费龙镜像每 1000 局找回 21 个没打出来的斩杀（约 2% 的局），其中约一半改变胜负，约 +1 个百分点，减去 B 多约 1.5% 迭代的一点好处；海盗镜像上一道门实测 +0.2 ± 1.8。
- 在这个分布下，(S) 过的概率约 16%～21%；(NI) 统计那几条约 72%～84%；谜题那一条上一道门在本容器上 3/3，按约 97% 算。
- **J35**：(S) 过，置信 **20%**。
- **J36**：(NI) 过，置信 **75%**。

## 另报（同上一道门，每格各一份）

- 用附带脚本 `lethal2_games.py play` 以门的种子重打 300 对、留记录（门本身不留），逐局和门的得分比，应该全部相同。
- 由这些记录，每格报（`lethal2_games.py read --package lethal3`，两种检查用建造线 `lethal3_eval.py` 的定义）：
  - **每 100 局在自己回合里赢下的局**，A 和 B 各一个数；
  - **A 的自己回合开头里，场上有 ticker 的比例**（跳费龙镜像预计近 0）；
  - **A 每个回合开头多花的毫秒**（平均、p90）；
  - 两种检查各找到几个斩杀、只有一方找到的各几个。
- 门行照报：A 先手 / 后手的分数；两局走法完全相同的对数；门自己的毫秒比。

## 种子

- 库 66700000～66799999：
  - 跳费龙镜像的门 66700000～66700299，复核 66790000～66790019；
  - 海盗镜像的门 66710000～66710299，复核 66791000～66791019。
- 附带脚本用门的种子。下一个空位 **66800000**。

## 命令（本容器；svsim 715230d；顺序：跳费龙镜像一格做完，再做海盗镜像）

```
export PYTHONPATH=<svsim 715230d>:<分析线>/analysis/lethal-setup
# 每格（以跳费龙镜像为例；海盗镜像把 ramp 换成 pirate-t、种子换成 66791000 / 66710000）
python -m svsim.tools.host svsim.tools.gate --a "level-strong+lethal3" --b "mcts:203+plan+learned+phased" \
    --deck ramp --opponent ramp --fixed --max 40 --seed 66790000 --workers 3 --out analysis/gates/lethal3/ncheck_ramp_ramp.jsonl
python analysis/oracle-hand/pooled.py analysis/gates/lethal3/ncheck_ramp_ramp.jsonl       # 毫秒比 → N_B
python -m svsim.tools.host svsim.tools.gate --a "level-strong+lethal3" --b "mcts:<N_B>+plan+learned+phased" \
    --deck ramp --opponent ramp --fixed --max 600 --seed 66700000 --workers 3 --out analysis/gates/lethal3/ramp_ramp.jsonl
python -m svsim.tools.host lethal2_games play --a "level-strong+lethal3" --b "mcts:<N_B>+plan+learned+phased" \
    --deck ramp --opponent ramp --seed 66700000 --pairs 300 --workers 3 --out analysis/gates/lethal3/records_ramp.jsonl
python -m svsim.tools.host lethal2_games read analysis/gates/lethal3/records_ramp.jsonl analysis/gates/lethal3/ramp_ramp.jsonl \
    --package lethal3 --workers 3
# 两格都完了以后
python analysis/oracle-hand/pooled.py analysis/gates/lethal3/ramp_ramp.jsonl analysis/gates/lethal3/pirate_pirate.jsonl
python -m svsim.tools.puzzles --spec "level-strong+lethal3" level-strong --seeds 1,2,3
```
- 算力估计：每格复核约 2 分钟、门约 15～20 分钟、附带重打约 15～20 分钟、计时约 4 分钟；两格合计约 1.3 小时。
