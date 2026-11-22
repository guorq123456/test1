# 每期主持方流程（RUNBOOK）

写于 2026-11-22（主持方）。正式对局、检验、练习场都在 Salem 的电脑上跑（cyberpower），低优先级。Salem S10（11-22 08:49Z）允许全核：最多 23 个工作进程 + 1 = 24 个逻辑核，不加掩码；**要比每步算力的（收提交、策略期把关、驾驶员两种条件）只用能效核**：`--workers 15 --mask 0x3FC3FC`，不给掩码工具不跑（A44）。命令都在 `C:\claude\ladder\analysis\ladder` 下用虚拟环境的 Python 跑（`C:\claude\ladder\.venv\Scripts\python.exe`，下面写成 `py`）。

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
2. 练习场：`py -m ladder.arena snapshot C:\claude\ladder-host\pool --arena C:\claude\ladder-arena --anchors <锚点表>`；`py -m ladder.arena open C:\claude\ladder-arena --hours 4 --games 20000 --workers 23`（时限 4 小时是临时限时；2 万局是规划的数）。第一次开期会生成 `arena.key`。
3. 策略期：定这一期把关检验的 delta（规划：前几期 3～5 个百分点，后面 1.5），写进台账，再开期。
4. 环境报告：`py -m ladder.report C:\claude\ladder-host\pool --out C:\claude\ladder-players\public\reports --anchors-dir C:\claude\ladder-host\anchors [--puzzle <题>\result-public.json ...] --note "这一期的时限、规则变化"`。写 report-P<期>.md 和 .json：公开排行榜、每个职业几个成员、上一期的胜率表（成员对职业、成员对成员）、锚点成绩（上一期全员在新种子上重打的结果，按职业 × 基线快照 / 名人堂，外加全池；不标编号、不给局数，S11、A48）、公共题结果（不标是谁）。发以前主持方自己从头看一遍，只有匿名编号和数。

### 2. 选手工作（时限内）

- 选手在练习场里打、预检（`py -m ladder.submit precheck`），然后把提交目录交给主持方。
- 主持方不看谁在调什么，不回答怎么打的问题。

### 3. 收提交

- 每份：`py -m ladder.submit receive <提交目录> --player <代号> --pool C:\claude\ladder-host\pool --out C:\claude\ladder-host\subs --workers 15 --mask 0x3FC3FC`。回执原样给本人。
- 卡组期：收下的新卡组 `py -m ladder.submit admit C:\claude\ladder-host\subs --receipt S-xxxx --pool C:\claude\ladder-host\pool`。
- 策略期：收下的打法更新 `py -m ladder.submit gate C:\claude\ladder-host\subs --receipt S-xxxx --pool C:\claude\ladder-host\pool --frozen C:\claude\ladder-host\frozen\P<期>.json --seeds 88500000 89000000 --out C:\claude\ladder-host\gates --delta <这一期定的> --workers 15 --mask 0x3FC3FC`。过了自动换上；没过、中间一步都只记一笔。每次跑完把 `C:\claude\ladder-host\subs\S-xxxx\gate-note.md`（检验结果，只有本人的回执编号）原样给本人。
- `py -m ladder.submit status C:\claude\ladder-host\subs --pool C:\claude\ladder-host\pool --player <代号>` 看谁还缺哪个职业。

### 4. 天梯

- `set LADDER_EXTRA_PATH=C:\claude\ladder-host\subs\code`，然后 `py -m ladder.pool ladder C:\claude\ladder-host\pool --until-period-done --workers 23`。没有密钥它不开打（第 1 期起）。
- 打完 `py -m ladder.pool show C:\claude\ladder-host\pool` 看还差谁；够不着的不挡（S8）。**先做第 5 节的名人堂和锚点对战，再** `py -m ladder.pool advance C:\claude\ladder-host\pool`（锚点对战记在当前这一期）。

### 5. 锚点、公共题

- 名人堂（S9、A41）：天梯打完、进下一期以前 `py -m ladder.anchors induct C:\claude\ladder-host\pool --hof C:\claude\ladder-host\anchors\hof.json`，再 `py -m ladder.anchors table --out C:\claude\ladder-host\anchors\anchors.json --hof C:\claude\ladder-host\anchors\hof.json`（锚点 = 基线快照 + 名人堂；下一期练习场的 snapshot 也用这份）。
- 锚点对战（S11、A48）：名人堂进完、advance 以前，`py -m ladder.anchors run C:\claude\ladder-host\anchors\anchors.json --pool C:\claude\ladder-host\pool --out C:\claude\ladder-host\anchors --code C:\claude\ladder-host\subs\code --workers 23`（先加 `--plan` 看局数和种子）。池子里每个成员现在这一版对每个锚点 10 局，连自己的冻结副本也打；种子从锚点段 93510000～94509999 里接着上一期用过的往后取，一局一个，经密钥发牌（没密钥拒打）。开打以前先把每个打法、每副卡组载入一遍，有载不进来的（多半是忘了 `--code`）一局不打、直接报错。一期只打一次：中途停了再跑同一条命令，只补没打的局；因为设置或机器作废的局（打法没载入、工作进程死了、runner 出错）不进台账，同一条命令再跑会在它们原来的种子上重打；中间池子或锚点表变了、或者这一期已经打完，它都拒打，先查清楚，不换一批局重打。返回里的 voids 是记进台账的作废局（模拟器出错），有就记 LEDGER、报 Salem。`py -m ladder.anchors classes C:\claude\ladder-host\anchors` 是公开的数（按职业），`py -m ladder.anchors report C:\claude\ladder-host\anchors --anchors ...anchors.json` 是每个成员的行，只给 Salem。锚点段用完（`--plan` 会说）先在项目登记表上登记新的一段。
- 公共题：出题 `py -m ladder.puzzles add C:\claude\ladder-host\subs --id P01 --deck <卡组码> --title "..." --public C:\claude\ladder-players\public`；选手用 `submit` 交（种类「公共题」）。评测 `py -m ladder.puzzles run C:\claude\ladder-host\subs --id P01 --seeds <公共题段里没用过的一段> --out C:\claude\ladder-host\puzzles\P01 --workers 23`；种子段 91900000～91999999，每次用哪一截记进 SEEDS.md。result-public.json 进环境报告，result-host.json 只给 Salem。

### 6. 汇报

- 公开排行榜：`py -m ladder.leaderboard C:\claude\ladder-host\pool --public --out <公共目录>\board-P<期>.json`。
- 给 Salem 的：私有排行榜（同一条命令不加 `--public`）、这一期的检验台账、锚点成绩、同源度、算力和耗时、所有偏离规划的地方。每个数都能追到台账。

## 不做的事

- 不替任何选手改卡组或打法，不往池子里放成员（基线除外）。
- 不把一个选手的东西给另一个选手；谁是谁、第几期、第几版都不说。
- 把关、累计确认、正式天梯、最终自测、锚点的种子不给选手，主持方也不在上面调参。
- 跑着的时候不在电脑上 git pull。
