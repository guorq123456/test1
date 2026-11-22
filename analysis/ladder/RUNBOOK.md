# 每期主持方流程（RUNBOOK）

写于 2026-11-22（主持方）。正式对局、检验、练习场都在 Salem 的电脑上跑（cyberpower），最多 11 个工作进程 + 1，能效核掩码 0x3FC3FC，低优先级。命令都在 `C:\claude\ladder\analysis\ladder` 下用虚拟环境的 Python 跑（`C:\claude\ladder\.venv\Scripts\python.exe`，下面写成 `py`）。

## 目录（都在 Salem 的账户里，S4）

| 目录 | 放什么 | 谁看 |
|---|---|---|
| `C:\claude\ladder` | 仓库（只拉 claude/ladder 分支；跑着的时候不拉） | 主持方 |
| `C:\claude\ladder-host\` | `ladder.key`（发牌密钥，base-2，A39）、`pool\`（正式池）、`subs\`（提交台账；`subs\code\` 是收下的打法）、`gates\`（检验台账）、`frozen\`（每期的冻结池）、`anchors\`、`reports\` | 只有主持方。选手不许读（规则 + 提示词，S4） |
| `C:\claude\ladder-arena\` | 练习场：`host\`（冻结副本、谁是谁、`arena.key`、完整日志）、`public\`、`players\<拼音>\` | `host\` 只有主持方；选手只读自己那份 |
| `C:\claude\ladder-players\<拼音>\` | 每个选手自己的工作目录 | 本人 |
| `C:\claude\ladder-players\public\` | 公共目录副本：`analysis/ladder/public/` 全部 + 每期的环境报告 | 全部选手，只读 |

拼音：甲 jia、乙 yi、丙 bing、丁 ding、戊 wu。

## 第一次（第 1 期以前，只做一次）

1. 阶段 1 验收、锁定（1.9）。base-2 的代码在锁定的版本里。
2. 建密钥：`py -m ladder.deal new C:\claude\ladder-host\ladder.key`（只建一次；文件不进仓库、不进项目共享目录）。`py -m ladder.deal id` 应该打出同一个编号。
3. 在电脑上重跑 base-2 的检查：重放（含密钥发牌的新局）、底座检查、接口复现（tools/check_interface.py，40 局逐个决策）。全过才往下走。
4. 正式池：把 p1b 的基线池（`C:\claude\ladder-runs\p1b\baseline\pool\`）整个复制到 `C:\claude\ladder-host\pool\`，原件不动。`py -m ladder.pool advance C:\claude\ladder-host\pool` 进第 1 期（S8：巫师基线够不着，不挡；日志里记它差几局）。
5. 建选手目录（上表），把 `analysis/ladder/public/` 复制到 `C:\claude\ladder-players\public\`。
6. 选手先做 2.6 起点测量（计划第二节），再进第 1 期。

## 每期

### 1. 开期

1. 冻结池：`py -m ladder.evaluator freeze C:\claude\ladder-host\pool --out C:\claude\ladder-host\frozen\P<期>.json`（每个成员最近 1000 局平均，A22）。
2. 练习场：`py -m ladder.arena snapshot C:\claude\ladder-host\pool --arena C:\claude\ladder-arena --anchors <锚点表>`；`py -m ladder.arena open C:\claude\ladder-arena --hours 4 --games 20000 --workers 11 --mask 0x3FC3FC`（时限 4 小时是临时限时；2 万局是规划的数）。第一次开期会生成 `arena.key`。
3. 策略期：定这一期把关检验的 delta（规划：前几期 3～5 个百分点，后面 1.5），写进台账，再开期。
4. 环境报告：这一期是卡组期还是策略期、时限、公开排行榜、池子里每个职业几个成员（只给匿名编号）、规则有什么变化。放进公共目录。

### 2. 选手工作（时限内）

- 选手在练习场里打、预检（`py -m ladder.submit precheck`），然后把提交目录交给主持方。
- 主持方不看谁在调什么，不回答怎么打的问题。

### 3. 收提交

- 每份：`py -m ladder.submit receive <提交目录> --player <代号> --pool C:\claude\ladder-host\pool --out C:\claude\ladder-host\subs --workers 11 --mask 0x3FC3FC`。回执原样给本人。
- 卡组期：收下的新卡组 `py -m ladder.submit admit C:\claude\ladder-host\subs --receipt S-xxxx --pool C:\claude\ladder-host\pool`。
- 策略期：收下的打法更新 `py -m ladder.submit gate C:\claude\ladder-host\subs --receipt S-xxxx --pool C:\claude\ladder-host\pool --frozen C:\claude\ladder-host\frozen\P<期>.json --seeds 88500000 89000000 --out C:\claude\ladder-host\gates --delta <这一期定的> --workers 11 --mask 0x3FC3FC`。过了自动换上；没过、中间一步都只记一笔。
- `py -m ladder.submit status C:\claude\ladder-host\subs --pool C:\claude\ladder-host\pool --player <代号>` 看谁还缺哪个职业。

### 4. 天梯

- `set LADDER_EXTRA_PATH=C:\claude\ladder-host\subs\code`，然后 `py -m ladder.pool ladder C:\claude\ladder-host\pool --until-period-done --workers 11 --mask 0x3FC3FC`。没有密钥它不开打（第 1 期起）。
- 打完 `py -m ladder.pool show C:\claude\ladder-host\pool` 看还差谁；够不着的不挡（S8）。`py -m ladder.pool advance C:\claude\ladder-host\pool`。

### 5. 锚点、公共题

- 锚点对战：第一次先 `py -m ladder.anchors table --out C:\claude\ladder-host\anchors\anchors.json`（驾驶员做完 2.5 再加 `--pilots`）。每期 `py -m ladder.anchors run C:\claude\ladder-host\anchors\anchors.json --pool C:\claude\ladder-host\pool --out C:\claude\ladder-host\anchors --workers 11 --mask 0x3FC3FC`（先加 `--plan` 看局数）；只打新版本（A40）。`py -m ladder.anchors report C:\claude\ladder-host\anchors --anchors ...anchors.json` 出成绩。
- 公共题（题库在做）：种子段 91900000～91999999。

### 6. 汇报

- 公开排行榜：`py -m ladder.leaderboard C:\claude\ladder-host\pool --public --out <公共目录>\board-P<期>.json`。
- 给 Salem 的：私有排行榜（同一条命令不加 `--public`）、这一期的检验台账、锚点成绩、同源度、算力和耗时、所有偏离规划的地方。每个数都能追到台账。

## 不做的事

- 不替任何选手改卡组或打法，不往池子里放成员（基线除外）。
- 不把一个选手的东西给另一个选手；谁是谁、第几期、第几版都不说。
- 把关、累计确认、正式天梯、最终自测、锚点的种子不给选手，主持方也不在上面调参。
- 跑着的时候不在电脑上 git pull。
