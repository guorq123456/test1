# 实验场（Salem 自己用的练习接口，S30）

和选手的练习场分开，给 Salem 自己试卡组和打法。全核（23 个工作进程），不限局数，不看开期窗口，什么都看得到（对手的卡表、是谁的、打法；每局两边的每一步）。代码在 `ladder/lab.py`，启动文件 `C:\claude\ladder-lab\lab.cmd`（转到仓库里的 `tools\pc\lab.cmd`）。

## 命令

在 Windows 终端里（哪个目录都行）：

```
C:\claude\ladder-lab\lab.cmd field                       现在冻结池里的成员和锚点：编号、成员号、主人、职业、相对 CR、打法、卡组在存档里的名字
C:\claude\ladder-lab\lab.cmd decks [--find RUNE]          存档里的卡组名字（public/decklists.md 那些：基线七副 bot/…、bot 自己的 19 副、WGP 资格赛、职业联赛）
C:\claude\ladder-lab\lab.cmd vs  你这边  对手  --games N   对战，胜率和 95% 区间、先后手分开、按对手分开、作废原因
C:\claude\ladder-lab\lab.cmd vs  你这边  --same-as L0003   把 L0003 那次的局原样再打一遍（同发牌、同对手、同座位、同打法种子），给配对差
C:\claude\ladder-lab\lab.cmd ladder  你这边  [--replacing 成员]  [--games 600 --tail 300 --repeats 3]   冻结池评测（相对 CR）
C:\claude\ladder-lab\lab.cmd replay --run L0003 --game L0003-00007 [--seat 0]   一局两边的每一步；加 --seat 还给那一边每次决策时看到的局面
```

**你这边**（二选一）：
- `--version 目录`：和选手一样的版本目录，`strategy.py` 加 `submission.json`（`{"class": "打法类的名字", "deck": 卡组代码或存档名字}`）。提交校验的读代码那一步只给警告，不拒；对局里碰了守卫拦的东西，那一局作废，日志里写原因。
- `--deck 卡组 [--strategy 打法]`：卡组代码或存档名字；打法默认 `bot:mcts:100+plan`，可以写任何 `bot:` / `mix:`，比如 `bot:mcts:400+plan`。

**对手**（三选一）：
- `--opponent 编号`（可以写几次）：冻结池里的成员（匿名编号或成员号 m0010）或锚点，用它自己的打法。
- `--class 职业`：这个职业的所有成员轮流。写中文（精灵、皇家护卫、巫师、龙族、梦魇、主教、超越者）或英文（forest、sword、rune、dragon、abyss、haven、portal；终端的编码有时会把中文弄坏）。
- `--vs-deck 卡组`（可以写几次）：任意卡组，用 `--vs-strategy` 的打法开（默认 `bot:mcts:100+plan`）。

局在对手之间轮流，先后手交替。冻结池是练习场这一期的那份（开期时冻结的）。

**载入训练模型的打法**（`setnet=`、`puct=`、驾驶员 `bot:pilot-…`）：只能和 `bot:` / `mix:` 的打法打，走没有绊线的裁判（S17）；`ladder` 不收（冻结池评测走带绊线的对局，这种局会被作废，LD-59）。

## 机器怎么分

电脑同一时间只跑一件事（D2）。实验场的每次运行都排进练习场的队，名字是 salem：主持方自己的活（收提交、把关、关期）先，其余轮流，谁上次轮到得最早谁先。
- `vs` 每轮最多打 2000 局，打完一轮重新排队，所以期中别人最多等你一轮（全核约 3 分钟）。
- `ladder` 是一次评估器运行，从头占到尾：**期中**一次最多 6300 局（验收口径 5×1200 放得下，全核约 10 分钟）；期外不限。
- 没人排队时全核都是你的。期中选手在用的时候，你的大命令会和他们轮流，慢一些。
- 关期、开期的启动文件看到有天梯的 Python 在跑（包括实验场）就不拉代码、不开始：要关期、开期前，先等实验场的命令跑完。

## 种子和记录

- 种子：实验场自己的一段 94910000～95909999（SEEDS.md、项目登记表），和练习场一样在段里随机抽；发牌用实验场自己的密钥（`C:\claude\ladder-lab\lab.key`，第一次用时生成），不碰正式池和练习场的密钥。
- 记录都在 `C:\claude\ladder-lab\`：`runs\L0001\`（run.json、jobs.json、games.jsonl 完整对局日志、summary.json、回放）、`code\`（跑过的 strategy.py）。这是你本人的对局记录：主持方不拿来做任何事（红线：本人对局记录不用于搜索和训练），选手提示词里把这个目录列进不许读的地方。
