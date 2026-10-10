# 斩杀修正（`+lethal2`）的等算力门：预注册（架构线程 2026-10-10 05:13Z 布置；写在任何门的对局之前）

**条件**：对手卡表已知（牌序、手牌未知）。

**改动**（建造线 23b317d，说明在它的 `analysis/speed/LETHAL.md`「+lethal2」一节）：`+lethal2` = `+tick` 加更深的斩杀筛。
- `+tick`：资源流规划器把我方会打对手主战者的倒计时护符（ticker，在沙盒里量，不用按卡的表）算进去；只在我方场上有 ticker 时起作用。
- 更深的筛：`LethalAgent` 的 `near=(2000, 4)`、`max_nodes=3000`（`level-strong` 是 `near=(1000, 4)`、2000）。
- 建造线的离线评估（海盗镜像 80 局）：
  - 开头的检查漏掉的 13 个斩杀，`+lethal2` 找回 12 个，一个没丢；
  - 没兑现的 4 个全部找回；
  - 每个回合开头平均多花 5.3 ms（p90 13.3；`level-strong` 的检查本身平均 78 ms）。
- 谜题库的 pirate-flags-lethal：`+lethal2` 在种子 1～3 上都解出，`level-strong` 解不出。

## A 和 B

- **A** = `level-strong+lethal2`。
- **B** = `mcts:N_B+plan+learned+phased`：`level-strong` 只调迭代次数，让每回合的毫秒数相同。
- svsim 用建造线 23b317d 或之后。

**等算力**
- **起点 N_B = 203**。建造线量的是每个回合开头多 5.3 ms；`level-strong` 一回合约 380 ms（RC 上跳费龙镜像 377 ms，海盗镜像按同量级算），约多 1.4%，所以 round(200 × 1.014) = 203。
- **照惯例复核一次**：
  - 门命令 `--fixed --max 40`，20 对，种子 66699000～66699019；
  - A ÷ B 的每搜索决策毫秒比（`analysis/oracle-hand/pooled.py`）落在 0.97～1.03 之外，就修一次 N_B = round(203 × 毫秒比)。
- **门的毫秒数这次能用**（和 turnpick 不同）：
  - `+lethal2` 多出的时间花在每回合第一个决策的检查上，之后基础搜索照跑，所以记得上；
  - 只有「找到斩杀、照斩杀线走、不跑搜索」的回合记不上，两边都有，而且少（约 5% 的开头）。
  - 另外附带脚本会在 A 的真实回合开头上直接计时，报 A 每个回合开头多花的毫秒。

## 门

- 海盗镜像（`--deck pirate-t --opponent pirate-t`）直接对打，`--fixed --max 600`，**定长 300 对**，种子 **66600000～66600299**（库 66600000）。
- **两个门槛，都写在跑之前**。哪个决定装机，架构线程在问 Salem；候选档位是 strong 和 max。
  - **(S) 标准门**：下沿 > 50%。
  - **(NI) 不伤**：下沿 ≥ 46%（约 −28 CR），而且谜题库的 pirate-flags-lethal 在 RC 上由 A 在种子 1～3 都解出。
- 理由（架构线程）：建造线 80 局的海盗样本里，`+lethal2` 找回全部 4 个没兑现的斩杀，约占 A 的 2.5% 局。其中一半改变胜负的话，约 +1 个百分点（推断）。300 对的门看不出这么小的差。

**两个门槛各自过的概率**（正态近似；300 对的对分标准误按以往镜像门的区间 ±2.8～±3.4 取 1.4～1.75 个百分点）

| 真实效果 | (S) 下沿 > 50% | (NI) 下沿 ≥ 46% |
|---|---|---|
| 0 | 2.5% | 63%～82% |
| +1 个百分点 | 8%～11% | 82%～95% |
| +3 个百分点 | 40%～57% | 98%～99.9% |

- (S) 要点估计约 52.7%～53.4% 才过；(NI) 要点估计约 48.7%～49.4%。
- (NI) 另要谜题那一条。建造线本机解出了；RC 上搜索可能和本机走得不完全一样，按约 95% 算。
- 照记：真实效果是 0 时，(NI) 也有六到八成会过。所以 (NI) 量的是「没有明显变差」，不是「变好了」。

**判断**
- **J33**（架构线程）：(S) 过，置信 15%。
  - 照记：按上面的算法，真实效果取以 +0.7 为中心、标准差 1 的分布（+1 的推断，减去 B 多 1.4% 迭代的一点好处），(S) 过的概率约 9%～12%。
- **J34**（分析线，按上面的算法）：**(NI) 过，置信 75%**。
  - 依据：同样的分布下，下沿那一条过的概率约 74%～87%（看标准误取哪头）；乘上谜题那一条的约 95%，约 0.75。

## 另报（附带脚本 `lethal2_games.py`，在 RC 上门跑完后、同一台机器、同样的种子）

- 用门自己的 `_game` 和 `_agent`、同样的 agent 种子，把这 300 对重打一遍并留下记录（这次门本身不留记录）。逐局和门的得分比，应该全部相同。
- **每 100 局兑现的斩杀**，A 和 B 各一个数：赢家在自己回合里赢下的局；结束回合时的回合末效果、对手随后抽空牌库也算，同 M1。
- **A 的自己回合开头里，场上有 ticker 的比例**（`search.combo.tickers_of`）。
- **A 每个回合开头多花的毫秒**：在 A 的每个真实回合开头上，`level-strong` 的检查和 `+lethal2` 的检查各跑一次计时（同建造线的 `lethal2_eval.py`）。报平均和 p90，另报两种检查各找到几个斩杀。
- 门行照报：A 先手、后手的分数；两局走法完全相同的对数。

**冒烟**（本机，库外种子 99600500，2 对，svsim 23b317d，强制 spawn、经启动器）
- 附带脚本重打的 4 局和门本身的 4 局逐局相同，读数能跑。
- 冒烟的数不当结果。

## 种子

- 库 66600000～66699999：门 66600000～66600299，复核 66699000～66699019。附带脚本用门的种子。
- 下一个空位 **66700000**。

## RC 的命令（svsim 用建造线 23b317d 或之后；分析线分支 ccr-da4857cc-rkpgwr 在这份预注册的提交或之后；排在装机和 M2 / M4 之后）

```
cd <svsim checkout>
set PYTHONPATH=.;<分析线分支>/analysis/lethal-setup     (Linux: export，用冒号)
mkdir analysis\gates\lethal2                            (Linux: mkdir -p analysis/gates/lethal2)
python -m svsim.tools.host svsim.tools.gate --a "level-strong+lethal2" --b "mcts:203+plan+learned+phased" ^
    --deck pirate-t --opponent pirate-t --fixed --max 40 --seed 66699000 --workers 12 ^
    --out analysis/gates/lethal2/ncheck_pirate_pirate.jsonl
python <分析线分支>/analysis/oracle-hand/pooled.py analysis/gates/lethal2/ncheck_pirate_pirate.jsonl
```
- 看最后的「ms per searched decision A … / B … = 比值」：在 0.97～1.03 之内 N_B 就是 203；在外面 N_B = round(203 × 比值)。

```
python -m svsim.tools.host svsim.tools.gate --a "level-strong+lethal2" --b "mcts:<N_B>+plan+learned+phased" ^
    --deck pirate-t --opponent pirate-t --fixed --max 600 --seed 66600000 --workers 12 ^
    --out analysis/gates/lethal2/pirate_pirate.jsonl
python -m svsim.tools.puzzles --spec "level-strong+lethal2" level-strong --seeds 1,2,3 --only pirate-flags-lethal
python -m svsim.tools.host lethal2_games play --a "level-strong+lethal2" --b "mcts:<N_B>+plan+learned+phased" ^
    --deck pirate-t --opponent pirate-t --seed 66600000 --pairs 300 --workers 12 --out analysis/gates/lethal2/records.jsonl
python -m svsim.tools.host lethal2_games read analysis/gates/lethal2/records.jsonl ^
    analysis/gates/lethal2/pirate_pirate.jsonl --workers 12
```
- 推：`analysis/gates/lethal2/` 下的 ncheck_pirate_pirate.jsonl、pirate_pirate.jsonl、records.jsonl（约几 MB）。
- 谜题那一行和 `lethal2_games read` 打出的几行也一起发回来。
- 算力：门约 10 分钟，附带脚本重打约 10 分钟，计时约几分钟，合计约半小时。
