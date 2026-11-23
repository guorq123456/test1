# 每期主持方流程（RUNBOOK）

写于 2026-11-22（主持方）。正式对局、检验、练习场都在 Salem 的电脑上跑（cyberpower），低优先级。Salem S10（11-22 08:49Z）允许全核：最多 23 个工作进程 + 1 = 24 个逻辑核，不加掩码；**要比每步算力的（收提交、策略期把关、驾驶员两种条件）只用能效核**：`--workers 15 --mask 0x3FC3FC`，不给掩码工具不跑（A44）。命令都在 `C:\claude\ladder\analysis\ladder` 下用虚拟环境的 Python 跑（`C:\claude\ladder\.venv\Scripts\python.exe`，下面写成 `py`）。

## 目录（都在 Salem 的账户里，S4）

| 目录 | 放什么 | 谁看 |
|---|---|---|
| `C:\claude\ladder` | 仓库（只拉 claude/ladder 分支；跑着的时候不拉） | 主持方 |
| `C:\claude\ladder-host\` | `ladder.key`（发牌密钥，base-2，A39）、`pool\`（正式池）、`subs\`（提交台账；`subs\code\` 是收下的打法）、`gates\`（检验台账）、`frozen\`（每期的冻结池）、`anchors\`、`reports\` | 只有主持方。选手不许读（规则 + 提示词，S4） |
| `C:\claude\ladder-arena\` | 练习场：`host\`（冻结副本、谁是谁、`arena.key`、完整日志）、`public\`、`players\<名字>\`（选手名，arena.py） | `host\` 只有主持方；选手只读自己那份 |
| `C:\claude\ladder-players\<名字>\` | 每个选手自己的工作目录：笔记本、`submit\`（交提交，一个提交一个子目录）、`receipts\`（主持方放回执）、`summary-P<期>.md`、`to-host.md`（A50） | 本人；主持方收提交、放回执、读小结 |
| `C:\claude\ladder-players\public\` | 公共目录副本：`analysis/ladder/public/` 全部 + 每期的环境报告 | 全部选手，只读 |

选手（S20，Salem 11-23 18:57Z：不用代号，用选手名；名字就是目录名）：fable-ultracode、fable、astra、opus、sol（顺序就是 ladder.arena.PLAYERS，练习种子段按这个顺序分，A34）。

## 第一次（第 1 期以前，只做一次）

1. ~~阶段 1 验收、锁定（1.9）~~：11-23 锁在 dc2cbeb（LOCK.md）。base-2 的代码在锁定的版本里。锁定的文件不经 Salem 同意不改；每次开跑前 `python analysis/ladder/tools/check_lock.py` 应该打出「all 14 locked files as locked」。
2～3. ~~建密钥、重跑 base-2 的检查~~（11-23 dc2cbeb 十一项全过，LD-53）：Salem 双击 `tools\pc\base2-checks.cmd`（拉代码 → 没有密钥才建 `C:\claude\ladder-host\ladder.key`，只建一次，文件不进仓库、不进项目共享目录 → `tools/base2_checks.py`：密钥发牌的新局逐步、逐个决策重放，卡表顺序不从编号漏出，p1b 旧局用新代码重放，底座检查，接口复现 40 局，全核测速，绊线、公共题式任务、对局里的审计钩子（打法写文件、读外面的文件、起进程被拦下，正常打法不被拦），全部新局重放审计；一共十一项）。结果在 `C:\claude\ladder-runs\base2\summary.json`，只记密钥编号。全过才往下走（1.9 锁定）。之后 `py -m ladder.deal id` 应该打出同一个编号。
4. 正式池：把 p1b 的基线池（`C:\claude\ladder-runs\p1b\baseline\pool\`）整个复制到 `C:\claude\ladder-host\pool\`，原件不动。`py -m ladder.pool advance C:\claude\ladder-host\pool` 进第 1 期（S8：巫师基线够不着，不挡；日志里记它差几局）。
   **11-23 起用 `tools\pc\prep-players.cmd` 一次做完第 4、5 步**（`tools/first_setup.py`：先核锁定文件和密钥；池子复制前后都核 p1b 原件的哈希；目标位置已经有池子时绝不覆盖：已过第 0 期就只报「已经建好」，还在第 0 期且和 p1b 一样才 advance，别的都停下；重跑什么都不改）。同一个启动文件接着跑 2.5（驾驶员两种条件，能效核）和 2.2（斩杀题库，全核）。结果在 `C:\claude\ladder-runs\prep\<提交>\`。驾驶员的对局走主持方的裁判外跑（`ladder/outside.py`，S17：锁定的绊线不改；驾驶员的先验模型给没见过的牌补表，绊线会当成改了模拟器而作废，LD-59）：和 runner 是同一局（同样发牌、同样的公开局面和合法性检查、同样计算力），只是没有绊线、拦截钩子和看门狗，只收主持方自己的打法（bot:、mix:），日志每行带 `"referee": "outside"`。窗口里按 Ctrl+C 会马上停（已写的局保留，重跑同一条命令接着跑）。
5. 建选手目录（上表），把 `analysis/ladder/public/` 复制到 `C:\claude\ladder-players\public\`。
5b. 选手进场前，电脑上空跑一期：Salem 双击 `tools\pc\arena-dry.cmd`（`tools/arena_dry.py`）。在 `C:\claude\ladder-runs\arena-dry\<提交>\` 里另建一个小池子、台账、练习场和两个假选手的目录，按本文件第 1～4 节的命令走一遍卡组期：开练习场 8 分钟、收提交的循环收四份（三份收下、一份拒收）、截止后放进来的一份不收、同时一个假选手在练习场打、天梯 150 局、重放审计、交正式对局；再在能效核上量收提交算力比的误差（LD-55、LD-56），再用不是 UTF-8 的控制台跑一遍选手的命令，最后在天梯那 150 局上试正式对局的算力抽查（LD-57）。真的池子、台账、练习场、选手目录都不碰。结果 `C:\claude\ladder-runs\arena-dry\summary.json`，十项全过再让选手进场。
6. 选手先做 2.6 起点测量（计划第二节），再进第 1 期。题目（S19）：主教 bot/T1-HAVEN-1，题号 START；`tools\pc\first-setup.cmd`（Salem 双击 `C:\claude\ladder-runs\first-setup.cmd`）把它加进 `C:\claude\ladder-host\subs\puzzles.json` 和 `C:\claude\ladder-players\public\puzzles.md`，同时把仓库的 public\ 再抄一遍。选手按公共题交（类型「公共题」，puzzle 写 START）。评测：`py -m ladder.puzzles run C:\claude\ladder-host\subs --id START --seeds <公共题段里没用过的一截> --out C:\claude\ladder-host\puzzles\START --field others --ref 驾驶员=bot:mcts:35+plan+setnet=analysis/scaling/models/net-pilot-haven-bot-g3.npz+netmid+netany+puct=analysis/scaling/models/prior-pilot-haven-bot-ft-t05.npz:2:1 --workers 15 --mask 0x3FC3FC`（驾驶员用 2.5 量过的规格，LD-61：算力 1.09 倍；能效核，因为要比算力）。`ladder.puzzles run` 的 `--ref` 里载入训练模型的驾驶员（`bot:pilot-<卡组>`，或写出 `setnet=`、`puct=`）自动走裁判外跑（S17），结果里 `outside_tripwire` 列出哪几个（只在主持方那份）；选手的成员照旧走带绊线的 runner。

## 每期

### 1. 开期

1. 冻结池：`py -m ladder.evaluator freeze C:\claude\ladder-host\pool --out C:\claude\ladder-host\frozen\P<期>.json`（每个成员最近 1000 局平均，A22）。
2. 练习场：`py -m ladder.arena snapshot C:\claude\ladder-host\pool --arena C:\claude\ladder-arena --anchors <锚点表> --code C:\claude\ladder-host\subs\code`（把池子成员和名人堂收下的打法复制进 `C:\claude\ladder-arena\host\code\`；找不到就拒绝、什么都不写）；`py -m ladder.arena open C:\claude\ladder-arena --hours 4 --games 20000 --workers 23`（时限 4 小时是临时限时；2 万局是规划的数）。第一次开期会生成 `arena.key`。
3. 策略期：定这一期把关检验的 delta（规划：前几期 3～5 个百分点，后面 1.5），写进台账，再开期。
4. 环境报告：`py -m ladder.report C:\claude\ladder-host\pool --out C:\claude\ladder-players\public\reports --anchors-dir C:\claude\ladder-host\anchors [--puzzle <题>\result-public.json ...] --note "这一期的时限、规则变化"`。写 report-P<期>.md 和 .json：公开排行榜、每个职业几个成员、上一期的胜率表（成员对职业、成员对成员）、锚点成绩（上一期全员在新种子上重打的结果，按职业 × 基线快照 / 名人堂，外加全池；不标编号、不给局数，S11、A48）、公共题结果（不标是谁）。发以前主持方自己从头看一遍，只有匿名编号和数。

### 2. 选手工作（时限内）

- 选手在练习场里打、预检（`py -m ladder.submit precheck`），然后把提交目录交给主持方。
- 主持方不看谁在调什么，不回答怎么打的问题。

### 3. 收提交

- 练习场一开，就在电脑上开着收提交的循环（PLAN 8b，A55）：`py -m ladder.collect --players C:\claude\ladder-players --pool C:\claude\ladder-host\pool --subs C:\claude\ladder-host\subs --arena C:\claude\ladder-arena --workers 15 --mask 0x3FC3FC`（策略期再加 `--gates <after 或 now> --frozen C:\claude\ladder-host\frozen\P<期>.json --delta <这一期定的> --gates-out C:\claude\ladder-host\gates`）。它做的事：每两分钟看一遍五个人的 `submit\`；新目录（文件 30 秒没动过、真在本人的 `submit\` 里，链接出去的不认）一份一份收，五个人轮流；每份在单独的进程里收（偷看检查要在主持方进程里跑选手的代码，不能让它影响后面别人的回执）；收的时候拿练习场的锁（电脑上同一时间只跑一样）；每收一份写一次 `receipts\`；卡组期收下的直接入池。截止那一刻记下当时 `submit\` 里有哪些目录（写进 `C:\claude\ladder-host\subs\collect.jsonl`，重启也认），那些截止后照收，截止后才放进来或又改过的不收、列在最后。**截止以后它不会马上停**：先收完截止时在的，再把这一期收下了却还没入池的卡组入池、收下了却还没检验的打法更新逐个检验（`--gates now` 也一样补），最后打一行「这一期收完……可以开天梯了」才退出。收一份出错（台账里没有它的回执）隔两分钟再试，第二次还错就放弃、给本人放一张「目录名-没收成.md」；连着三份出错它自己停下（多半是主持方这边的问题）。入池、检验出错只记一笔、不重试。这些都在 `collect.jsonl`，要报。截止那一刻它没在跑（停电、关了），重启会拒绝，查过文件时间确定现在看到的都算截止前的，再加 `--after-deadline`。下面几条是它做的事；要手动补救，先停掉它（手动命令和它共用一把提交台账的锁，同时跑会排队，但别指望排队替你理顺顺序）。
- 提交目录在 `C:\claude\ladder-players\<名字>\submit\<目录名>\`（A50）。每份：`py -m ladder.submit receive <提交目录> --player <名字> --pool C:\claude\ladder-host\pool --out C:\claude\ladder-host\subs --workers 15 --mask 0x3FC3FC`。
- 每收一份、每检验完一份，都跑一次 `py -m ladder.submit deliver C:\claude\ladder-host\subs --pool C:\claude\ladder-host\pool --players C:\claude\ladder-players`：把每个人自己的回执（`目录名.md`）、检验结果（`目录名-检验.md`）、这一期的状态（`状态.md`：卡组期收下了哪些职业、还缺哪些，打法更新收了几份、检验完几份、换上几份）写进 `C:\claude\ladder-players\<名字>\receipts\`。只写本人的，重跑写出来一样。
- 卡组期：收下的新卡组 `py -m ladder.submit admit C:\claude\ladder-host\subs --receipt S-xxxx --pool C:\claude\ladder-host\pool`。
- 策略期：收下的打法更新 `py -m ladder.submit gate C:\claude\ladder-host\subs --receipt S-xxxx --pool C:\claude\ladder-host\pool --frozen C:\claude\ladder-host\frozen\P<期>.json --seeds 88500000 89000000 --out C:\claude\ladder-host\gates --delta <这一期定的> --workers 15 --mask 0x3FC3FC`。过了自动换上；没过、中间一步都只记一笔。检验结果 `C:\claude\ladder-host\subs\S-xxxx\gate-note.md`（只有本人的回执编号）由上面的 deliver 交给本人。
- `py -m ladder.submit status C:\claude\ladder-host\subs --pool C:\claude\ladder-host\pool --player <名字>` 看谁还缺哪个职业（主持方自己看；选手看 `receipts\状态.md`）。

### 4. 天梯

- **先等收提交的循环打出「这一期收完……可以开天梯了」、自己退出**，再开天梯：它截止以后还在入池、检验、换打法，和天梯同时动池子会乱（池子的事件日志没有锁）。
- `set LADDER_EXTRA_PATH=C:\claude\ladder-host\subs\code`，然后 `py -m ladder.pool ladder C:\claude\ladder-host\pool --until-period-done --workers 23`。没有密钥它不开打（第 1 期起）。
- 打完 `py -m ladder.pool show C:\claude\ladder-host\pool` 看还差谁；够不着的不挡（S8）。**先做第 5 节的名人堂和锚点对战，再做下面的重放审计，再把正式对局交给选手（下面最后一条），再** `py -m ladder.pool advance C:\claude\ladder-host\pool`（锚点对战记在当前这一期）。
- 重放审计（LD-40，advance 以前）：`py -m ladder.audit C:\claude\ladder-host\pool\games.jsonl "C:\claude\ladder-host\anchors\games-P<期>*.jsonl" --events C:\claude\ladder-host\pool\events.jsonl --workers 23 --out C:\claude\ladder-host\audit\P<期>.json --allow-empty "C:\claude\ladder-host\gates\*\games.jsonl"`（日志写在前面，`--allow-empty` 放最后：第一次把关以前把关日志一个都没有，不算错；别的通配匹配不到就退出码 2）。断行（停电写了一半的一行，或一行 NUL）跳过并列在结果的 unreadable 里。把关、锚点的日志续跑时会把没写完的那局重打；池子的不会（池子的局号不重用）：池子已经算过分、日志里却没有完整一行的局列在 unlogged 里（`--events` 拿池子的事件对照），这些局改了 CR 却没法重放，记 LEDGER、报 Salem（LD-43）。没停过电却有断行，也报 Salem。同一个日志被两个参数同时匹配到只读一次。结果里的 voids 按打法数作废局和其中「作废时它正输着」的局（LD-41）：某个成员的作废局明显多、尤其多是输着作废的，记 LEDGER、报 Salem。每一局在干净的进程里从种子、卡组、发牌按记下的走法重放（不跑任何打法代码）；走法不合法或结局对不上的局列出来。有一局对不上就先不 advance：记 LEDGER、报 Salem（可能是打法在进程里改了模拟器又改回去，也可能是记录被动过）。工作进程里的绊线（ladder/watch.py）已经把「改了没改回去」的局作废、换了进程，作废局的原因写在局里（"the simulator changed"），这类也要报；原因是 "nothing ran on any clock" 的，是空转看门狗（LD-42）作废的：工作进程拿着这局、没有任何时钟在走太久（多半是打法留下了局后还在跑的代码），也要报。
- 正式对局上的算力抽查（A52、LD-57，advance 以前）：`py -m ladder.compute_audit C:\claude\ladder-host\pool --period <期> --workers 15 --mask 0x3FC3FC --out C:\claude\ladder-host\audit\compute-P<期>.json`。每个选手成员的每一版抽这一期最多 30 局，在它的局面上重放默认打法，用同一期基线对基线的局在同一批里校准（只跑主持方代码，不打新局）。`over` 为真（90% 区间整个在 1.08 以上）的：先不下结论，记 LEDGER、报 Salem，怎么处理由 Salem 定；退出码 1 就是有这种成员。比率只给主持方和 Salem，不给选手。
- 交正式对局（A53，审计全过以后、advance 以前）：`py -m ladder.arena formal C:\claude\ladder-arena --pool C:\claude\ladder-host\pool --subs C:\claude\ladder-host\subs --period <期>`。给每个有成员的选手写 `C:\claude\ladder-arena\players\<名字>\members.json`（成员名 → 匿名编号、职业、在不在池子里）和 `runs\F<期>\`（这一期正式天梯里他的成员打的每一局，他那一侧；局号重编，自己对自己的局两份）。选手用 `arena replay` 看；不能续打、不能 `--same-as`。只写本人的，重跑写出来一样。

### 5. 锚点、公共题

- 名人堂（S9、A41）：天梯打完、进下一期以前 `py -m ladder.anchors induct C:\claude\ladder-host\pool --hof C:\claude\ladder-host\anchors\hof.json`，再 `py -m ladder.anchors table --out C:\claude\ladder-host\anchors\anchors.json --hof C:\claude\ladder-host\anchors\hof.json`（锚点 = 基线快照 + 名人堂；下一期练习场的 snapshot 也用这份）。
- 锚点对战（S11、A48）：名人堂进完、advance 以前，`py -m ladder.anchors run C:\claude\ladder-host\anchors\anchors.json --pool C:\claude\ladder-host\pool --out C:\claude\ladder-host\anchors --code C:\claude\ladder-host\subs\code --workers 23`（先加 `--plan` 看局数和种子）。池子里每个成员现在这一版对每个锚点 10 局，连自己的冻结副本也打；种子从锚点段 93510000～94509999 里接着上一期用过的往后取，一局一个，经密钥发牌（没密钥拒打）。开打以前先查：收下的打法模块都找得到（只找、不运行；找不到多半是忘了 `--code`）、主持方的打法都建得起来、每副卡组的卡都有脚本；有一样不行就一局不打、直接报错。一期只打一次：中途停了再跑同一条命令，只补没打的局；可能是设置或机器造成的作废局（打法没载入、工作进程死了、runner 出错）用原来的种子再打一次（每局最多一次，不管跑了几回），再作废就照实记成作废；中间池子或锚点表变了、或者这一期已经打完，它都拒打，先查清楚，不换一批局重打。返回里的 voids 是记进台账的作废局和原因（模拟器出错、重打一次还作废的），有就记 LEDGER、报 Salem。`py -m ladder.anchors classes C:\claude\ladder-host\anchors` 是公开的数（按职业），`py -m ladder.anchors report C:\claude\ladder-host\anchors --anchors ...anchors.json` 是每个成员的行，只给 Salem。锚点段用完（`--plan` 会说）先在项目登记表上登记新的一段。
- 公共题：出题 `py -m ladder.puzzles add C:\claude\ladder-host\subs --id P01 --deck <卡组码> --title "..." --public C:\claude\ladder-players\public`；选手用 `submit` 交（种类「公共题」）。评测 `py -m ladder.puzzles run C:\claude\ladder-host\subs --id P01 --seeds <公共题段里没用过的一段> --out C:\claude\ladder-host\puzzles\P01 --workers 23`；种子段 91900000～91999999，每次用哪一截记进 SEEDS.md。result-public.json 进环境报告，result-host.json 只给 Salem。

### 6. 汇报

- 公开排行榜：`py -m ladder.leaderboard C:\claude\ladder-host\pool --public --out <公共目录>\board-P<期>.json`。
- 给 Salem 的：私有排行榜（同一条命令不加 `--public`）、这一期的检验台账、锚点成绩、同源度、算力和耗时、所有偏离规划的地方。每个数都能追到台账。

## 不做的事

- 不替任何选手改卡组或打法，不往池子里放成员（基线除外）。
- 不把一个选手的东西给另一个选手；谁是谁、第几期、第几版都不说。
- 把关、累计确认、正式天梯、最终自测、锚点的种子不给选手，主持方也不在上面调参。
- 跑着的时候不在电脑上 git pull。
