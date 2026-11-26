# 每期主持方流程（RUNBOOK）

写于 2026-11-22（主持方）。正式对局、检验、练习场都在 Salem 的电脑上跑（cyberpower），低优先级。Salem S10（11-22 08:49Z）允许全核：最多 23 个工作进程 + 1 = 24 个逻辑核，不加掩码；**要比每步算力的（收提交、把关检验（第 2 期策略期，第 4 期起每期）、驾驶员两种条件）只用能效核**：`--workers 15 --mask 0x3FC3FC`，不给掩码工具不跑（A44）。命令都在 `C:\claude\ladder\analysis\ladder` 下用虚拟环境的 Python 跑（`C:\claude\ladder\.venv\Scripts\python.exe`，下面写成 `py`）。

## 目录（都在 Salem 的账户里，S4）

| 目录 | 放什么 | 谁看 |
|---|---|---|
| `C:\claude\ladder` | 仓库（只拉 claude/ladder 分支；跑着的时候不拉） | 主持方 |
| `C:\claude\ladder-host\` | `ladder.key`（发牌密钥，base-2，A39）、`pool\`（正式池）、`subs\`（提交台账；`subs\code\` 是收下的打法）、`gates\`（检验台账）、`frozen\`（每期的冻结池）、`anchors\`、`reports\` | 只有主持方。选手不许读（规则 + 提示词，S4） |
| `C:\claude\ladder-arena\` | 练习场：`host\`（冻结副本、谁是谁、`arena.key`、完整日志）、`public\`、`players\<名字>\`（选手名，arena.py） | `host\` 只有主持方；选手只读自己那份 |
| `C:\claude\ladder-players\<名字>\` | 每个选手自己的工作目录：笔记本、`submit\`（交提交，一个提交一个子目录）、`receipts\`（主持方放回执）、`summary-P<期>.md`、`to-host.md`（A50） | 本人；主持方收提交、放回执、读小结 |
| `C:\claude\ladder-lab\` | Salem 的实验场（S30，LAB.md）：`lab.cmd`、`lab.key`（实验场自己的发牌密钥）、`runs\L<号>\`（他的对局，完整日志）、`code\` | 只有 Salem。主持方不拿来做任何事（他本人的对局记录），选手不许读（提示词） |
| `C:\claude\ladder-players\public\` | 公共目录副本：`analysis/ladder/public/` 全部 + 每期的环境报告 | 全部选手，只读 |

选手（S20，Salem 11-23 18:57Z：不用代号，用选手名；名字就是目录名）：fable-ultracode、fable、astra、opus、sol（顺序就是 ladder.arena.PLAYERS，练习种子段按这个顺序分，A34）。

## 第一次（第 1 期以前，只做一次）

1. ~~阶段 1 验收、锁定（1.9）~~：11-23 锁在 dc2cbeb（LOCK.md）。base-2 的代码在锁定的版本里。锁定的文件不经 Salem 同意不改；每次开跑前 `python analysis/ladder/tools/check_lock.py` 应该打出「all 14 locked files as locked」。
2～3. ~~建密钥、重跑 base-2 的检查~~（11-23 dc2cbeb 十一项全过，LD-53）：Salem 双击 `tools\pc\base2-checks.cmd`（拉代码 → 没有密钥才建 `C:\claude\ladder-host\ladder.key`，只建一次，文件不进仓库、不进项目共享目录 → `tools/base2_checks.py`：密钥发牌的新局逐步、逐个决策重放，卡表顺序不从编号漏出，p1b 旧局用新代码重放，底座检查，接口复现 40 局，全核测速，绊线、公共题式任务、对局里的审计钩子（打法写文件、读外面的文件、起进程被拦下，正常打法不被拦），全部新局重放审计；一共十一项）。结果在 `C:\claude\ladder-runs\base2\summary.json`，只记密钥编号。全过才往下走（1.9 锁定）。之后 `py -m ladder.deal id` 应该打出同一个编号。
4. 正式池：把 p1b 的基线池（`C:\claude\ladder-runs\p1b\baseline\pool\`）整个复制到 `C:\claude\ladder-host\pool\`，原件不动。`py -m ladder.pool advance C:\claude\ladder-host\pool` 进第 1 期（S8：巫师基线够不着，不挡；日志里记它差几局）。
   **11-23 起用 `tools\pc\prep-players.cmd` 一次做完第 4、5 步**（`tools/first_setup.py`：先核锁定文件和密钥；池子复制前后都核 p1b 原件的哈希；目标位置已经有池子时绝不覆盖：已过第 0 期就只报「已经建好」，还在第 0 期且和 p1b 一样才 advance，别的都停下；重跑什么都不改）。同一个启动文件接着跑 2.5（驾驶员两种条件，能效核）和 2.2（斩杀题库，全核）。结果在 `C:\claude\ladder-runs\prep\<提交>\`。驾驶员的对局走主持方的裁判外跑（`ladder/outside.py`，S17：锁定的绊线不改；驾驶员的先验模型给没见过的牌补表，绊线会当成改了模拟器而作废，LD-59）：和 runner 是同一局（同样发牌、同样的公开局面和合法性检查、同样计算力），只是没有绊线、拦截钩子和看门狗，只收主持方自己的打法（bot:、mix:），日志每行带 `"referee": "outside"`。窗口里按 Ctrl+C 会马上停（已写的局保留，重跑同一条命令接着跑）。
5. 建选手目录（上表），把 `analysis/ladder/public/` 复制到 `C:\claude\ladder-players\public\`。
5b. 选手进场前，电脑上空跑一期：Salem 双击 `tools\pc\arena-dry.cmd`（`tools/arena_dry.py`）。在 `C:\claude\ladder-runs\arena-dry\<提交>\` 里另建一个小池子、台账、练习场和两个假选手的目录，按本文件第 1～4 节的命令走一遍卡组期：开练习场 8 分钟、收提交的循环收四份（三份收下、一份拒收）、截止后放进来的一份不收、同时一个假选手在练习场打、天梯 150 局、重放审计、交正式对局；再在能效核上量收提交算力比的误差（LD-55、LD-56），再用不是 UTF-8 的控制台跑一遍选手的命令，最后在天梯那 150 局上试正式对局的算力抽查（LD-57）。真的池子、台账、练习场、选手目录都不碰。结果 `C:\claude\ladder-runs\arena-dry\summary.json`，十项全过再让选手进场。
6. 选手先做 2.6 起点测量（计划第二节），再做第 1 期的卡组（S21：起点题并进第 1 期，共用 4 小时和 2 万局，不另开窗口；评测在第 1 期截止、收提交的循环退出以后跑，下面这条命令）。题目（S19）：主教 bot/T1-HAVEN-1，题号 START；`tools\pc\first-setup.cmd`（Salem 双击 `C:\claude\ladder-runs\first-setup.cmd`）把它加进 `C:\claude\ladder-host\subs\puzzles.json` 和 `C:\claude\ladder-players\public\puzzles.md`，同时把仓库的 public\ 再抄一遍。选手按公共题交（类型「公共题」，puzzle 写 START）。评测：`py -m ladder.puzzles run C:\claude\ladder-host\subs --id START --seeds <公共题段里没用过的一截> --out C:\claude\ladder-host\puzzles\START --field others --ref 参照=bot:mcts:35+plan+setnet=analysis/scaling/models/net-pilot-haven-bot-g3.npz+netmid+netany+puct=analysis/scaling/models/prior-pilot-haven-bot-ft-t05.npz:2:1 --workers 15 --mask 0x3FC3FC`（驾驶员用 2.5 量过的规格，LD-61：算力 1.09 倍；能效核，因为要比算力。名字写「参照」：`--ref` 的名字原样进公开那份结果和环境报告，写「驾驶员」等于告诉选手这副牌有训练过的驾驶员，评估第 10 条；Salem 没另说就这样）。结果 `C:\claude\ladder-host\puzzles\START\result-public.json` 由第 2 期的开期启动文件自动放进 report-P2（`HOST\puzzles\reported.json` 记已经放过的）。`ladder.puzzles run` 的 `--ref` 里载入训练模型的驾驶员（`bot:pilot-<卡组>`，或写出 `setnet=`、`puct=`）自动走裁判外跑（S17），结果里 `outside_tripwire` 列出哪几个（只在主持方那份）；选手的成员照旧走带绊线的 runner。

7. 开期以前空跑一次开期启动文件：双击 `C:\claude\ladder-runs\open-period-dry.cmd`（`tools\pc\open-period.cmd dry` → `tools/open_period.py --dry`：池子复制一份到 `C:\claude\ladder-runs\open-dry\<时间>-<提交>\`，在那里冻结、锚点表、练习场快照、开 3 分钟的窗口、写环境报告、跑收提交的循环到它打出「这一期收完」；不打对局、不用种子，真的池子、练习场、选手目录都不碰）。`summary.json` 的 ok 为真再开期。
8. 启动选手（S23，A57）。每期都照做：
   1. 先开期（下面第 1 节，`open-period.cmd`），确认 `C:\claude\ladder-arena\public\window.json` 有这一期的截止时刻。
   2. 开之前查一遍，下面这些文件和 Claude Code、Codex 已有的记忆里，没有本项目、别的选手、主持方的内容（有就先挪开）：`%USERPROFILE%\.claude\CLAUDE.md`；会话目录的每一层上级里的 `CLAUDE.md`、`CLAUDE.local.md`（`C:\CLAUDE.md`、`C:\claude\CLAUDE.md`、`C:\claude\ladder-players\CLAUDE.md` 和同名 .local）；`%USERPROFILE%\.codex\AGENTS.md`、`AGENTS.override.md`；上级目录里的 `AGENTS.md`（`C:\claude\` 是 git 仓库根时 Codex 会读）。
   3. 每个选手在自己的目录 `C:\claude\ladder-players\<名字>\` 里开一个新会话（每期新开，不接着上一期的会话；不从仓库目录开）。模型和思考强度照 11-23 08:15Z 定的：fable-ultracode = Fable 5.2 xhigh + ultracode，fable = Fable 5.2 max，astra = GPT 6.2 A，opus = Opus 5.5，sol = GPT 6.2 sol。第一条消息是 `prompts\<名字>.md` 的全文（共享目录 ladder/prompts/，五份成品，`python analysis/ladder/tools/make_prompts.py <目录>` 生成；player-prompt-v2.md 每改一次就重新生成、核一遍打出来的哈希，同目录的 PROMPTS.md 记着哪一版提示词、五份的哈希）。
   4. 五个人上网的条件一样：都开网页搜索。开跑时让每人先搜一次（随便一个卡牌名），在主持方笔记里记一行：谁、几点、能不能搜。
   5. 选手的会话权限（S4：Salem 账户里直接跑，规则 + 提示词 + 抽查管着，不另设系统权限；五个人设成一样）：能读写自己目录；能读公共目录 `C:\claude\ladder-players\public\`、练习场里自己那份 `C:\claude\ladder-arena\players\<名字>\`、仓库里 `svsim\core\`、`svsim\cards\`、`svsim\search\`、`svsim\agents\` 和 `analysis\ladder\ladder\`（提示词「能读的」那一条）；在 `C:\claude\ladder\analysis\ladder` 下用 `.venv` 的 Python 跑 `-m ladder.arena` 和 `-m ladder.submit precheck`。练习场命令自己会写 `C:\claude\ladder-arena\`（`players\<名字>\`、`host\players\<名字>\`、`host\run.lock`），会话的沙箱要放行这些写（或者像 S4 说的不开沙箱，五个人一样）。
   6. 每个选手开工后，主持方看一眼它第一次 `arena field` 的输出（练习场开着、局数 0）；有人卡在权限或路径上，五个人都停下来先修，修好再一起开始（截止时刻不改，要改问 Salem）。

## 每期

### 1. 开期

**特殊期开期前（第 3 期，A62、A64）**：上一期关完以后双击 `C:\claude\ladder-runs\before-P3.cmd`：拉代码 → 核锁定文件 → `tools\special_check.py --period 3`（28 副合法、关期后的池子里每队还能放几个人、五个选手能不能都选到队、在副本上收一次「选队」；结果 `C:\claude\ladder-runs\before-P3\<提交>\summary.json`）→ 开期空跑。五个选手选不全（`enough` 是 false）就先报 Salem，不开期。

**实验场（S30）**：Salem 的命令和选手排同一个队，开期、关期、空跑的外层启动文件看到天梯的 Python 在跑（包括实验场）就不拉代码、不开始：先等它跑完。

**用启动文件一次做完（11-23）**：双击 `C:\claude\ladder-runs\open-period.cmd`（`tools\pc\open-period.cmd` → `tools/open_period.py`），要输入 OPEN 才开。它按顺序做下面第 1、2、4 步和第 3 节的收提交循环：核锁定文件和密钥 → 核模拟器是这一期的环境（`tools/environments.py`，S25、A60：不是就停）→ 新环境的第一期：封存所有对局日志（`audit\sealed.json`）、补丁说明抄进 `C:\claude\ladder-players\public\` → 上一期是特殊期（第 4 期开期时：第 3 期）：特殊期评测的冻结池 `special\P<上一期>\frozen.json`（和 `special_eval.py` 第一步一样：先核池子是上一期收尾时的样子，再 `ladder.evaluator freeze`；已有就留着；池子已经变过就停下不开，11-26 审查）→ 公共目录的说明更新 → 每人的 `状态.md` 按这一期重写（`ladder.submit deliver`；写不进去的记进 summary，照样开）→ 冻结池（`frozen\P<期>.json`，已有就留着）→ 锚点表（`anchors\anchors.json`，有 `hof.json` 就带上）→ 练习场 snapshot（`--anchors`、`--code`）和 open（12 小时、每人 6 万局、23 个工作进程；S29 第 3 期起，前两期 4 小时、2 万局）→ 环境报告（note 自动写期号、截止时刻、局数上限；还没进过报告的公共题结果 `HOST\puzzles\*\result-public.json` 自动带上，记在 `HOST\puzzles\reported.json`；报告写不成也照样开收提交的循环，summary 里记一笔）→ 收提交的循环（能效核 15 个；收打法更新的期（第 2 期策略期，第 4 期起每一期都是合并期，S35、S36）加 `--gates after`，delta 读 `C:\claude\ladder-host\gates\delta-P<期>.json`：第 3 步定了以后先在 `C:\claude\ladder\analysis\ladder` 下跑一次 `py tools\open_period.py --set-delta <数>`，只记下、什么都不开；以后双击就用它，再给不一样的它拒绝；合并期没记就双击，它沿用最近一期记下的 delta（第 4 期起 5 个百分点，S34；Salem 改了才变），记进这一期的文件、打一行「沿用第 k 期的…」、summary 的 state 里有 `delta_carried_from`；一个都没有就停下不开）。**窗口要一直开着**，到它打出「这一期收完……可以开天梯了」。练习场这一期已经开着时再双击，它不会再开一次窗口（截止时刻、冻结副本都不变），也不拉代码（选手在跑），只重新起收提交的循环；同一时间只能有一个收提交的循环（`subs\collect.lock`）；截止以后才重启，循环会拒绝（见第 3 节 `--after-deadline`）。这一期的窗口已经开过、冻结副本却换了（有人期中手动 snapshot），它停下不开。结果在 `C:\claude\ladder-runs\open\<时间>-<提交>\`（summary.json、commands.log、collect.log）。下面是它做的命令，手动补救时照着做：

1. 冻结池：`py -m ladder.evaluator freeze C:\claude\ladder-host\pool --out C:\claude\ladder-host\frozen\P<期>.json`（每个成员最近 1000 局平均，A22）。
2. 练习场：`py -m ladder.arena snapshot C:\claude\ladder-host\pool --arena C:\claude\ladder-arena --anchors <锚点表> --code C:\claude\ladder-host\subs\code`（把池子成员和名人堂收下的打法复制进 `C:\claude\ladder-arena\host\code\`；找不到就拒绝、什么都不写）；`py -m ladder.arena open C:\claude\ladder-arena --hours 12 --games 60000 --workers 23`（S29：第 3 期起 12 小时、每人 6 万局；前两期 4 小时、2 万局）。第一次开期会生成 `arena.key`。
3. 收打法更新的期（第 2 期策略期；第 4 期起每一期，合并期）：定这一期把关检验的 delta（规划：前几期 3～5 个百分点，后面 1.5），写进台账，再开期。第 4 期起 S34 的 5 个百分点一直沿用到 Salem 改（开期时没记就自动沿用上一个，见上）。环境报告的说明里会写上这个数（A60⑤），合并期还写上新卡组可交可不交、这一期入池的成员这一期不能改打法、保护期到下一期结束。
   第 4 期开期前（第一次合并期）：合并的代码（pool.py 新的锁定版本，LOCK.md 11-26 那一行）和 public 里的 rules-2、submit-2 要先拉到电脑上；第 3 期收尾时已经按旧代码给选手写了「第 4 期（策略期）」的 `状态.md`，开期启动文件开窗口以前会按合并期重写（`ladder.submit deliver`；手动开期时开期以前自己跑一次 `py -m ladder.submit deliver C:\claude\ladder-host\subs --pool C:\claude\ladder-host\pool --players C:\claude\ladder-players`）。选手提示词（make_prompts）也要按新的 player-prompt-v2.md 重新生成。池子事件日志里第 3→4 期那一行写的是 `"kind": "strategy"`（LD-88，合并以前写的，只增不改）；代码不读那一项，现在第 4 期按 `period_kind` 算是合并期。
   换模拟器（补丁）：在 `tools/environments.py` 的 ENVS 里登记新环境（名字、从第几期起、`python analysis/ladder/tools/environments.py` 打出的指纹、说明文件），合进天梯分支；只在两期之间换（上一期收完、这一期开期以前）。
4. 环境报告：`py -m ladder.report C:\claude\ladder-host\pool --out C:\claude\ladder-players\public\reports --anchors-dir C:\claude\ladder-host\anchors [--puzzle <题>\result-public.json ...] --note "这一期的时限、规则变化"`。写 report-P<期>.md 和 .json：公开排行榜、每个职业几个成员、上一期的胜率表（成员对职业、成员对成员）、锚点成绩（上一期全员在新种子上重打的结果，按职业 × 基线快照 / 名人堂，外加全池；不标编号、不给局数，S11、A48）、公共题结果（不标是谁）。发以前主持方自己从头看一遍，只有匿名编号和数。

### 2. 选手工作（时限内）

- 选手在练习场里打、预检（`py -m ladder.submit precheck`），然后把提交目录交给主持方。
- 主持方不看谁在调什么，不回答怎么打的问题。

### 3. 收提交

- 练习场一开，就在电脑上开着收提交的循环（PLAN 8b，A55）：`py -m ladder.collect --players C:\claude\ladder-players --pool C:\claude\ladder-host\pool --subs C:\claude\ladder-host\subs --arena C:\claude\ladder-arena --workers 15 --mask 0x3FC3FC`（收打法更新的期，即第 2 期和第 4 期起每一期，再加 `--gates <after 或 now> --frozen C:\claude\ladder-host\frozen\P<期>.json --delta <这一期定的> --gates-out C:\claude\ladder-host\gates`；不给它不起）。它做的事：每两分钟看一遍五个人的 `submit\`；新目录（文件 30 秒没动过、真在本人的 `submit\` 里，链接出去的不认）一份一份收，五个人轮流；每份在单独的进程里收（偷看检查要在主持方进程里跑选手的代码，不能让它影响后面别人的回执）；收的时候拿练习场的锁（电脑上同一时间只跑一样）；每收一份写一次 `receipts\`；收下的新卡组（卡组期、合并期）直接入池；合并期里打法更新也收，截止以后再检验（S14），检验的对手是开期时冻结的池子，这一期入池的成员不在里面，所以给它们的打法更新收的时候就拒收。截止那一刻记下当时 `submit\` 里有哪些目录（写进 `C:\claude\ladder-host\subs\collect.jsonl`，重启也认），那些截止后照收，截止后才放进来或又改过的不收、列在最后。**截止以后它不会马上停**：先收完截止时在的，再把这一期收下了却还没入池的卡组入池、收下了却还没检验的打法更新逐个检验（`--gates now` 也一样补），最后打一行「这一期收完……可以开天梯了」才退出（这一期有入池的，行里还有「入池 k 份」「入池出错 j 份」）。收一份出错（台账里没有它的回执）隔两分钟再试，第二次还错就放弃、给本人放一张「目录名-没收成.md」；连着三份出错它自己停下（多半是主持方这边的问题）。入池、检验出错只记一笔、不重试。这些都在 `collect.jsonl`，要报。截止那一刻它没在跑（停电、关了），重启会拒绝，查过文件时间确定现在看到的都算截止前的，再加 `--after-deadline`。下面几条是它做的事；要手动补救，先停掉它（手动命令和它共用一把提交台账的锁，同时跑会排队，但别指望排队替你理顺顺序）。
- 提交目录在 `C:\claude\ladder-players\<名字>\submit\<目录名>\`（A50）。每份：`py -m ladder.submit receive <提交目录> --player <名字> --pool C:\claude\ladder-host\pool --out C:\claude\ladder-host\subs --workers 15 --mask 0x3FC3FC`。
- 每收一份、每检验完一份，都跑一次 `py -m ladder.submit deliver C:\claude\ladder-host\subs --pool C:\claude\ladder-host\pool --players C:\claude\ladder-players`：把每个人自己的回执（`目录名.md`）、检验结果（`目录名-检验.md`）、这一期的状态（`状态.md`：新卡组收下了哪些职业、卡组期还缺哪些（合并期是「还能交」哪些，不算缺），打法更新收了几份、检验完几份、换上几份）写进 `C:\claude\ladder-players\<名字>\receipts\`。只写本人的，重跑写出来一样。
- 卡组期、合并期：收下的新卡组 `py -m ladder.submit admit C:\claude\ladder-host\subs --receipt S-xxxx --pool C:\claude\ladder-host\pool`。
- 策略期、合并期：收下的打法更新（只有这一期开始时已经在池子里的成员）`py -m ladder.submit gate C:\claude\ladder-host\subs --receipt S-xxxx --pool C:\claude\ladder-host\pool --frozen C:\claude\ladder-host\frozen\P<期>.json --seeds 88500000 89000000 --out C:\claude\ladder-host\gates --delta <这一期定的> --workers 15 --mask 0x3FC3FC`。过了自动换上；没过、中间一步都只记一笔。检验结果 `C:\claude\ladder-host\subs\S-xxxx\gate-note.md`（只有本人的回执编号）由上面的 deliver 交给本人。
- 检验出错（`collect.jsonl` 里的 gate-failed）不重试，先报 Salem。第 2 期 3 份是不同局占比太小、旧的检验工具抛错（LD-77）：S31 以后检验工具直接判没过；那 3 份用 `tools\gate_settle.py` 补记（电脑上 `C:\claude\ladder\analysis\ladder\tools\pc\settle-P2.cmd`，拉过代码以后才有：先空跑核对，打 WRITE 才写；不打局、不用种子；写检验台账、提交台账、本人回执）。别的错不能用它补记。
- `py -m ladder.submit status C:\claude\ladder-host\subs --pool C:\claude\ladder-host\pool --player <名字>` 看谁还缺（卡组期）或还能交（合并期）哪个职业（主持方自己看；选手看 `receipts\状态.md`）。

### 4. 天梯

**用启动文件一次做完第 4～6 节（11-24，A59）**：截止以后、开期那个窗口打出「这一期收完……可以开天梯了」并退出以后，先关掉五个选手的对话，再双击 `C:\claude\ladder-runs\close-period.cmd`（外层：练习场的截止时刻已过、电脑上没有任何和天梯有关的 Python 在跑（主持方的、选手的练习对局和脚本都算：它们都载入仓库的代码）、`close_period.py --check` 没说「还不能收尾」（退出码 3：截止没到、收提交没收完；第一次电脑上还没有这个文件时跳过；检查本身出错是退出码 1，照样拉，好让修好的代码到电脑上），才拉代码、删 `ladder\__pycache__`；然后 `tools\pc\close-period.cmd` → `tools/close_period.py`），要输入 CLOSE 才开始。它按顺序做：核锁定文件和密钥 → 核状态（池子在第 P 期、练习场的窗口是第 P 期的、截止已过；池子已经在 P+1 而窗口还是 P 的，说明收过尾了，什么都不做）→ 核收提交收完（拿住 `subs\collect.lock` 到最后，收提交的循环起不来；截止那一刻的目录清单在、里面每个目录都收了或放弃了或记成截止后改过，收下的卡组都入池、收下的打法更新都检验过）→ 拿练习场的锁到最后（选手还有对局在跑就等它跑完）→ 天梯（下面第一条，`LADDER_EXTRA_PATH` 指 `subs\code`；还有人不够 100 局、又不是够不着的，再跑；一次没打出局就停）→ 名人堂 induct（每期一次，这一期已经进过的就不再进）和锚点表 → 锚点对战（每期一次，打完的留着；每个成员那几行写进 `reports\anchors-P<期>.json`，只给 Salem）→ 这一期到期的公共题（第 1 期末：START，命令就是第一次第 6 条那条，能效核；种子是公共题段里接着用过的往后 1200 个，开打以前先写进 `puzzles\<题>\plan.json`，中断了接着用同一截）→ 重放审计（池子全部、这一期锚点、所有把关、所有公共题的日志）→ 算力抽查（能效核；每期只量一次，量过的留着）→ 交正式对局（重放审计没有新问题才交；Salem 定了照样进下一期时也交）→ 私有和公开排行榜（`reports\board-P<期>-private.json`、`board-P<期>.json`）→ advance。**有一项要主持方先看的就不 advance**（停在 advance 以前，退出码 2，`summary.json` 的 held 写着为什么、头几局 / 哪几个成员，`held_digest` 是这份清单的编号；`audit\held-P<期>.json` 按编号记着每份清单里具体是哪几局、哪几个成员）：有局重放不出来、池子算过分却没日志的局、日志里有不完整的行（前几期的审计已经列过的不算：那时报过、定过；审计每期都读全部日志）、有成员算力 90% 区间整个在 1.15 以上。看过、报过 Salem、Salem 定了要照样进下一期，在 `C:\claude\ladder\analysis\ladder` 下跑 `py tools\close_period.py --out C:\claude\ladder-runs\close\anyway-P<期> --advance-anyway "<Salem 怎么说的、几点>" --held <给 Salem 看的那份 summary 的 held_digest>`（做完的步骤都留着，只补没做的、给正式对局、再 advance；这次又冒出那份清单里没有的局或成员，它不给正式对局、不 advance，把新的清单另记一个编号，要拿新的去问 Salem；重跑同一条命令也一样拒绝）。advance 以后把公开排行榜抄进 `C:\claude\ladder-players\public\`，再 `submit deliver` 一次（回执里的状态换成新一期；这一步中断了，下次双击会补上）。不挡 advance、要报的（收提交出的错、截止后又改过的目录（report.collect.late）和截止后才放进来的目录（steps.collected.late_new）、作废局、够不着的成员、锚点作废局、算力抽查没有校准局）在 summary 的 report 里。每一步都能重跑：中途停了（Ctrl+C、停电、出错修好）再双击，做完的留着，接着做没做完的。外层文件万一一直不拉（比如检查说没收完、其实是检查本身的毛病），截止已过、没有天梯的 Python 在跑时，可以手动拉：`cd /d C:\claude\ladder && git pull --ff-only origin claude/ladder`。结果在 `C:\claude\ladder-runs\close\<时间>-<提交>\`（summary.json、commands.log）。下面是它做的命令，手动补救时照着做：

- **先等收提交的循环打出「这一期收完……可以开天梯了」、自己退出**，再开天梯：它截止以后还在入池、检验、换打法，和天梯同时动池子会乱（池子的事件日志没有锁）。
- `set LADDER_EXTRA_PATH=C:\claude\ladder-host\subs\code`，然后 `py -m ladder.pool ladder C:\claude\ladder-host\pool --until-period-done --workers 23`。没有密钥它不开打（第 1 期起）。
- 打完 `py -m ladder.pool show C:\claude\ladder-host\pool` 看还差谁；够不着的不挡（S8）。**先做第 5 节的名人堂和锚点对战，再做下面的重放审计，再把正式对局交给选手（下面最后一条），再** `py -m ladder.pool advance C:\claude\ladder-host\pool`（锚点对战记在当前这一期）。
- 重放审计（LD-40，advance 以前；换过环境以后，期末启动文件只核封存的日志没动、只重放封存以后写的部分，A60）：`py -m ladder.audit C:\claude\ladder-host\pool\games.jsonl "C:\claude\ladder-host\anchors\games-P<期>*.jsonl" --events C:\claude\ladder-host\pool\events.jsonl --workers 23 --out C:\claude\ladder-host\audit\P<期>.json --allow-empty "C:\claude\ladder-host\gates\*\games.jsonl"`（日志写在前面，`--allow-empty` 放最后：第一次把关以前把关日志一个都没有，不算错；别的通配匹配不到就退出码 2）。断行（停电写了一半的一行，或一行 NUL）跳过并列在结果的 unreadable 里。把关、锚点的日志续跑时会把没写完的那局重打；池子的不会（池子的局号不重用）：池子已经算过分、日志里却没有完整一行的局列在 unlogged 里（`--events` 拿池子的事件对照），这些局改了 CR 却没法重放，记 LEDGER、报 Salem（LD-43）。没停过电却有断行，也报 Salem。同一个日志被两个参数同时匹配到只读一次。结果里的 voids 按打法数作废局和其中「作废时它正输着」的局（LD-41）：某个成员的作废局明显多、尤其多是输着作废的，记 LEDGER、报 Salem。每一局在干净的进程里从种子、卡组、发牌按记下的走法重放（不跑任何打法代码）；走法不合法或结局对不上的局列出来。有一局对不上就先不 advance：记 LEDGER、报 Salem（可能是打法在进程里改了模拟器又改回去，也可能是记录被动过）。工作进程里的绊线（ladder/watch.py）已经把「改了没改回去」的局作废、换了进程，作废局的原因写在局里（"the simulator changed"），这类也要报；原因是 "nothing ran on any clock" 的，是空转看门狗（LD-42）作废的：工作进程拿着这局、没有任何时钟在走太久（多半是打法留下了局后还在跑的代码），也要报。
- 正式对局上的算力抽查（A52、LD-57，advance 以前）：`py -m ladder.compute_audit C:\claude\ladder-host\pool --period <期> --workers 15 --mask 0x3FC3FC --out C:\claude\ladder-host\audit\compute-P<期>.json`。每个选手成员的每一版抽这一期最多 30 局，在它的局面上重放默认打法，用同一期基线对基线的局在同一批里校准（只跑主持方代码，不打新局）。`over` 为真（90% 区间整个在 1.08 以上）的：先不下结论，记 LEDGER、报 Salem，怎么处理由 Salem 定；退出码 1 就是有这种成员。比率只给主持方和 Salem，不给选手。
- 交正式对局（A53，审计全过以后、advance 以前）：`py -m ladder.arena formal C:\claude\ladder-arena --pool C:\claude\ladder-host\pool --subs C:\claude\ladder-host\subs --period <期>`。给每个有成员的选手写 `C:\claude\ladder-arena\players\<名字>\members.json`（成员名 → 匿名编号、职业、在不在池子里）和 `runs\F<期>\`（这一期正式天梯里他的成员打的每一局，他那一侧；局号重编，自己对自己的局两份）。选手用 `arena replay` 看；不能续打、不能 `--same-as`。只写本人的，重跑写出来一样。

### 5. 锚点、公共题

- 名人堂（S9、A41）：天梯打完、进下一期以前 `py -m ladder.anchors induct C:\claude\ladder-host\pool --hof C:\claude\ladder-host\anchors\hof.json`，再 `py -m ladder.anchors table --out C:\claude\ladder-host\anchors\anchors.json --hof C:\claude\ladder-host\anchors\hof.json`（锚点 = 基线快照 + 名人堂；下一期练习场的 snapshot 也用这份）。
- 锚点对战（S11、A48）：名人堂进完、advance 以前，`py -m ladder.anchors run C:\claude\ladder-host\anchors\anchors.json --pool C:\claude\ladder-host\pool --out C:\claude\ladder-host\anchors --code C:\claude\ladder-host\subs\code --workers 23`（先加 `--plan` 看局数和种子）。池子里每个成员现在这一版对每个锚点 10 局，连自己的冻结副本也打；种子从锚点段 93510000～94509999 里接着上一期用过的往后取，一局一个，经密钥发牌（没密钥拒打）。开打以前先查：收下的打法模块都找得到（只找、不运行；找不到多半是忘了 `--code`）、主持方的打法都建得起来、每副卡组的卡都有脚本；有一样不行就一局不打、直接报错。一期只打一次：中途停了再跑同一条命令，只补没打的局；可能是设置或机器造成的作废局（打法没载入、工作进程死了、runner 出错）用原来的种子再打一次（每局最多一次，不管跑了几回），再作废就照实记成作废；中间池子或锚点表变了、或者这一期已经打完，它都拒打，先查清楚，不换一批局重打。返回里的 voids 是记进台账的作废局和原因（模拟器出错、重打一次还作废的），有就记 LEDGER、报 Salem。`py -m ladder.anchors classes C:\claude\ladder-host\anchors` 是公开的数（按职业），`py -m ladder.anchors report C:\claude\ladder-host\anchors --anchors ...anchors.json` 是每个成员的行，只给 Salem。锚点段用完（`--plan` 会说）先在项目登记表上登记新的一段。
- 公共题：出题 `py -m ladder.puzzles add C:\claude\ladder-host\subs --id P01 --deck <卡组码> --title "..." --public C:\claude\ladder-players\public`；选手用 `submit` 交（种类「公共题」）。评测 `py -m ladder.puzzles run C:\claude\ladder-host\subs --id P01 --seeds <公共题段里没用过的一段> --out C:\claude\ladder-host\puzzles\P01 --workers 23`；种子段 91900000～91999999，每次用哪一截记进 SEEDS.md。result-public.json 进环境报告，result-host.json 只给 Salem。

- 特殊期（S27、A62、A63）：期末收尾以后跑评测 `py tools\special_eval.py --period 3 --workers 23`（在 `C:\claude\ladder\analysis\ladder` 下；约 26 万局，加上 S33 的对照（每副卡表配默认打法）再多 13 万～16 万局，全核共 9～11 小时；Ctrl+C 停了再跑接着跑）。带选手名的结果在 `C:\claude\ladder-host\special\P3\result.md`，每人自己的几行放进各自的 `receipts\特殊期评测-P3.md`；两份都多两列「同卡表默认打法」「比默认打法」。第 4 期开期前跑完（第 4 期是合并期，开期以后一收下新卡组池子就变了，评测的冻结那一步就拒绝，至少它第一步的冻结要在开期以前做完）。开期启动文件会先做这一步冻结（`special\P3\frozen.json`，已有就留着；池子已经变过就停下不开），所以评测可以开期以后再跑，它读这份冻结池；手动开期时开期以前自己跑一次评测（至少到它打出「冻结池：…」）。

### 6. 汇报

- 公开排行榜：`py -m ladder.leaderboard C:\claude\ladder-host\pool --public --out <公共目录>\board-P<期>.json`。
- 给 Salem 的：私有排行榜（同一条命令不加 `--public`）、这一期的检验台账、锚点成绩、同源度、算力和耗时、所有偏离规划的地方。每个数都能追到台账。

## 不做的事

- 不替任何选手改卡组或打法，不往池子里放成员（基线除外）。
- 不把一个选手的东西给另一个选手；谁是谁、第几期、第几版都不说。
- 把关、累计确认、正式天梯、最终自测、锚点的种子不给选手，主持方也不在上面调参。
- 跑着的时候不在电脑上 git pull。
