# 按卡组取模型的核对（svsim 491c6aa）

491c6aa 把学到的评估从"按职业对"改成"先按卡组对、再按职业对、再退回 Learned"。`engine.new_game` 记下每一方的卡组名，装着的 `dragon-dragon*` 改名为 `ramp-ramp*`。核对的标准是：跳费龙内战和不同职业的对局，改动前后逐步完全相同；快攻龙按设计改走回退。

改动前用 e8d190a（491c6aa 的上一个提交），改动后用 491c6aa。比较的是每一步的走法，不是胜率。

## 结果：全部符合

**1. 1 号会话自己的 12 局**（`analysis/deckkey/replay_check.py`，在两个提交上各跑一次）
- 跳费龙内战（v2 对 v2；装着的对装着的），以及跳费龙对破魔虫，共 6 局：逐步相同。
- 快攻龙相关的 6 局：按设计变了。
- 我这边跑出来的 12 局，和 1 号提交的 `before.json`、`after.json` 逐步一致，说明对局可以复现。
- 文件：`replay_before_e8d190a.json`、`replay_after_491c6aa.json`。

**2. 补的 20 局**（`extra_cases.py`，换了种子，每种 2 局）
- 改动前后逐步相同（12 局）：
  - v1：推演对手回合时用 ACT 模型，检查它也按新键取到；
  - `+net`：价值网络；
  - `+prior`：没装策略头文件，只说明没文件时一致；
  - 跳费龙内战 strong 档：v2s 对 `mcts:200+plan+learned`；
  - 跳费龙对破魔虫 strong 档，两边各坐一次。
- 快攻龙（8 局）：改动后 v2 和装着的 `mcts:100+plan+learned` 逐步相同，无论 v2 执跳费龙打快攻龙，还是执快攻龙打快攻龙。两边都退回到 Learned 的 `dragon.json`。
- 文件：`extra_before_e8d190a.json`、`extra_after_491c6aa.json`。

**3. Salem 的 94 个回合**
- 用 `../cross-turn/play_turns.py`，v2、v2s 各 5 个种子，共 940 个 bot 回合，改动前后逐步完全相同。
- Salem 对局记录里的卡组，在 491c6aa 上认出来是 `ramp` / `ramp`。`clone` 后卡组名还在。
- 文件：`turns_v2_v2s_491c6aa.jsonl`。对照的是 `../cross-turn/turns_v2_v2s_e8d190a.jsonl`。

**夜里"跳费龙对快攻龙"那组的结论。** 那组 v2 对装着的 bot 打出 55.8% ± 5.3%，是因为两边同为龙族，硬套了跳费龙内战模型。现在这类对局里，v2 和装着的 bot 都退回到 `dragon.json`，两边逐步相同，差距按定义为 0，不用重测。

## 用法

```
cd <改动前的 svsim> && PYTHONPATH=. python3 extra_cases.py before.json
cd <改动后的 svsim> && PYTHONPATH=. python3 extra_cases.py after.json
python3 compare.py before.json after.json --same 6=7,8=9
```
