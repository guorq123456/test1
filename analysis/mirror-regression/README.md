# 跳费龙内战回归局面（来自 Salem 的 10 局）

这套局面用来检查新 bot 能不能在同样的局面做出高手的选择。它是测试，不是写进 bot 的规则。来源是 Salem 在超凡陪练台上和网页 bot（`mcts:200+plan+learned`）打的 10 局跳费龙内战，Salem 10-0。

每个局面是 Salem 某个回合开始时的局面（座位 0）。被测的 agent 从这里替 Salem 打完整个回合，检查的是这一整回合有没有做到某件事。

## 文件

- `positions.json`：对局记录只存一份（`records`），局面（`positions`）按 `game` + `at` 引用。`at` 是动作下标：重放前 `at` 个动作，就到这个回合开始。每个局面带当时的局面摘要（`context`）、Salem 这一回合实际怎么打（`salem_turn`）、检查条件（`check`）和理由（`why`）。
- `build_positions.py`：从对局 JSON 生成 `positions.json`。
- `check.py`：跑一个 agent，报告每个局面和每一类的通过率。agent 写成 `salem` 时，重放 Salem 自己的回合，用来验证检查本身写得对：现在 52/52 全过。

```
cd <svsim 仓库> && PYTHONPATH=. python3 check.py positions.json "mcts:200+plan+learned" 3
SVSIM_WEIGHTS=<只放 dragon.json 的目录> PYTHONPATH=. python3 check.py positions.json "mcts:200+plan+learned" 3
```

## 八类检查

| 类别 | 数量 | 通过条件（整回合） |
|---|---|---|
| `lethal` | 10 | 这一回合就赢（攻击、效果、回合结束伤害都算） |
| `super_evolve` | 11 | 超进化 Salem 超进化的那张（伊兰翠 5、班德 6） |
| `discard` | 9 | 弃牌时不弃伊兰翠或班德（Salem 弃的是波菈莱、深渊、咆哮） |
| `red_target` | 8 | 打出赤流，而且打的是对面场上最大的随从 |
| `red_hold` | 1 | 对面只有小随从时，不把赤流打在小随从上 |
| `erntz_unevolved` | 3 | 10 血以下，白板下伊兰翠（不进化），拿那 8 点回血 |
| `bonus_keep` | 6 | 后手自己第 1 回合，不用额外 PP |
| `bonus_ramp` | 4 | 后手自己第 2 回合，用额外 PP 打 3 费跳费 |

## 注意

- 这些是 Salem 在那一个局面的选择，不保证是唯一正确答案。Salem 说过超进化伊兰翠还是班德"要看双方资源，没有固定答案"。所以这套局面适合看趋势（新 bot 的通过率有没有上升），不适合单个局面判对错。
- `discard`、`red_hold` 这类检查，不弃牌、不打赤流也算通过，只拦"做错的那一步"。
- 52 个局面太少，不能用来比较两个 bot 谁更强，那是评测台（`svsim/tools/gate.py`）的事。这里只回答"像不像高手"。

## Salem 的战绩（人类基准）

按 bot 版本分开记录，用 Beta 后验（均匀先验）给出 95% 区间。

| 日期 | 对局 | bot | 战绩 | 95% 区间 |
|---|---|---|---|---|
| 2026-10-06 | 破魔虫 对 跳费龙 | 强档（`mcts:200+plan+learned`，旧评估） | 9-1 | 59%～98% |
| 2026-10-06 | 跳费龙内战 | 同上（纹章 bug 未修、无内战模型） | 10-0 | 72%～100% |
| 2026-10-06 起 | 跳费龙内战 | 第 12 版网页（内战模型 + 纹章修正） | 待打 | |

现在的对局记录里没有 bot 的代码版本，只能按发布时间对应。建议以后在记录里存 bot 的提交号。
