# 打法接口说明（给选手）

版本：接口 interface-2，底座 base-1。写于 2026-11-22（主持方）；11-23 选手进场以前加了 `LETHAL_NODES`、`LETHAL_SCREEN` 两个设置（不设就和以前一样）。11-27 改正了 veto 那一行对斩杀的说法，补了「用 veto 写规则要注意」，接口和底座都没变。11-28 升到 interface-2，第 4 期起用：加了回合开始钩子 `turn_start` 和三个辅助函数（第三节「回合开始钩子」），算力改成按回合给（第四节第 1 条）；不写钩子的打法，下法和以前一步都不差。这份说明会随底座和接口的版本更新；你的成员记录着它用的是哪个版本。

## 一、你交的「打法」是什么

一个 Python 类，继承 `ladder.interface.PlayerStrategy`，放在你自己的模块里。它坐在默认打法的位置上：每到你做决定，底座先按你自己的猜测抽出一个完整局面，再让搜索在这个局面上选一步。如果你写了回合开始钩子 `turn_start`，每个自己回合的第一个决定之前，底座先调一次它，让你先规划这一回合（第三节「回合开始钩子」）。你能改的是下面第三节列的几个点，其余照默认打法。

**什么都不改，就是默认打法**（通用 bot `mcts:100+plan`：每步 100 次搜索的 ISMCTS，前面挡着斩杀搜索和它的规划器；斩杀搜索有预算，会漏一部分斩杀，见第三节最后两行和第五节）。主持方在 interface-1 上验收过：不改任何点的子类和默认打法逐个决策完全一样（电脑上 40 局）。interface-2 加了钩子以后，不写钩子、写一个空钩子、钩子里只用 `self.random` 推演完就扔掉，在主持方的测试里都和默认打法逐个决策一样；电脑上 40 局的复核做完再补在这里。

## 二、你看得到什么（信息条件）

- 开局前：只知道对手的职业。不知道对手的卡表、牌序、手牌。
- 对局中：和真人玩家看到的一样。对手职业；对手打出或亮出过的牌；双方场面；对手手牌和牌库的张数；你自己的手牌和卡表。
- 你的代码**拿不到真实局面**。每个钩子拿到的要么是公开局面 `pos`（`ladder.base.PublicPosition`），要么是底座按你的猜测抽出来的一个局面 `state`。抽出来的局面里，对手的未知牌来自你自己的猜测，牌序重新洗过，以后的随机结果重新定过。

## 三、能改的点

| 钩子 | 拿到什么 | 返回什么 | 默认 |
|---|---|---|---|
| `turn_start(pos)` | 公开局面（这回合你第一个决定时的） | 不用返回。每个自己回合调一次，在这回合第一个决定的抽样、搜索之前。用来规划这一回合：算出来的计划存在 `self` 上，这回合的决定（包括这第一个）再用 `veto`、`prior`、`search` 去执行。见下面「回合开始钩子」 | 不写就不调 |
| `guess(pos)` | 公开局面 | 对手卡表的猜测：`[(40 张牌的列表, 权重), ...]`。底座会按对手亮过的牌更新权重 | 对手打的是它那个职业的基线卡表 |
| `mulligan(state)` | 抽出来的局面（换牌阶段） | 一个换牌动作 | 通用 bot 的换牌 |
| `weights(pos)` | 公开局面 | `svsim.search.evaluate.Weights`：手写估值的各项数值。每步都会问，所以可以按对手职业、按回合不同 | `DEFAULT` |
| `evaluate(state, me, me_next)` | 抽出来的局面；`me` 是你；`me_next` 为真表示轮到你走 | 一个数，越大对你越好。整个替换估值。和 `weights` 只能改一个 | 不改：用 `weights` 的估值 |
| `veto(state, action)` | 抽出来的局面、一个合法动作 | 真 = 这一步不考虑。搜索里每一层都用。斩杀搜索和规划器找线时不看它，但线上每一步打出去之前都要过它：哪一步被排除，这条斩杀线就从那一步断掉（前面几步已经打出去了），剩下的交给搜索。全都被排除时，搜索里全部保留。见下面「用 veto 写规则要注意」 | 不改：什么都不排除 |
| `prior(state, actions)` | 抽出来的局面、合法动作 | 对这些动作的概率（加起来是 1），或 None。只在根节点加一个偏好：c_prior × P × √(根访问数) / (1 + 访问数) | 不改：没有偏好 |
| `search(pos)` | 公开局面 | 这一步的搜索设置，可以有：`iterations`（默认 100）、`c`（探索系数，0.5）、`scale`（估值折算成胜率的尺度，8.0）、`max_depth`（30）、`c_prior`（0.3）。别的键会被拒绝 | `{}` |
| 类属性 `LETHAL` | — | `"planner"`（斩杀搜索 + 规划器，默认）、`"exact"`（只有斩杀搜索）、`"off"`（不做斩杀搜索） | `"planner"` |
| 类属性 `LETHAL_NODES` | — | 斩杀搜索最多搜多少个局面（整数，1～100000）。只找「怎么抽、怎么随机都赢」的斩杀 | `2000` |
| 类属性 `LETHAL_SCREEN` | — | `(n, n2, k)`：搜之前先粗估这回合最多能打多少伤害，估出来不够斩杀就只搜 `n` 个局面，差 `k` 点以内搜 `n2` 个（`n`、`n2` 不超过 `LETHAL_NODES`）；`None`：不粗估，每次都按 `LETHAL_NODES` 搜 | `(200, 1000, 4)` |

一个照抄默认打法的骨架（每个点都写出来，结果和默认打法一样）：

```python
from ladder import base
from ladder.interface import PlayerStrategy
from svsim.agents.greedy_agent import mulligan as bot_mulligan
from svsim.search.evaluate import DEFAULT, evaluate


class MyStrategy(PlayerStrategy):
    LETHAL = "planner"
    LETHAL_NODES = 2000
    LETHAL_SCREEN = (200, 1000, 4)

    def guess(self, pos):
        return base.default_guess(pos.opp_craft)

    def mulligan(self, state):
        return bot_mulligan(state)

    def evaluate(self, state, me, me_next):
        return evaluate(state, me, DEFAULT, player_moves_next=me_next)

    def veto(self, state, action):
        return False

    def search(self, pos):
        return {"iterations": 100, "c": 0.5, "scale": 8.0}

    def turn_start(self, pos):
        return None
```

### 用 veto 写规则要注意

1. **规则会挡斩杀。** 不管是「这种时候必须出 X」这种强制规则，还是「不许出 Y」这种限制规则，只要否掉了斩杀线上的某一步，这条线就断了，这回合可能就斩不成。默认的斩杀层先跑规划器、再跑斩杀搜索，两种找出来的线都会被挡。不想漏斩杀，规则里要自己先判断这回合有没有斩杀。
2. **`search()` 返回的 `iterations` 或 `max_depth` 小于等于 0 时，搜索树是空的**，直接走第一个合法动作，veto 不起作用。
3. **同名同费的牌在搜索里算同一步**（打哪一张结果都一样），所以规则按卡牌 id 和张数写，不要按 uid 指定「留这一张」：手里有两张一样的牌时，只排除其中一张的 uid 可能落空。

### 回合开始钩子 `turn_start`（interface-2）

**什么时候调**
- 每个自己回合调一次：在这回合你的第一个决定里，底座抽局面、搜索之前。所以这回合的第一个决定就已经能用上你刚存的计划。
- 换牌不调；对手回合里不调（那时根本不问你）。额外 PP（UseBonusPP）不算新回合。
- 回合一开始对局就结束了（比如抽空牌库），这回合不调；回合中途对局结束，计划就作废了。
- 练习场从中途续打、练习题、斩杀题库：打法对象是在对局中途新建的，钩子在它第一次被问到的那个决定里调，可能落在回合中间。
- 只认类里写的 `def turn_start`；在 `__init__` 里给 `self.turn_start` 赋值不算，不会被调。底座是在 `act` 里调钩子的：你要是自己重写 `act`、不调 `super().act`，钩子就不会被调。

**计划怎么存**
- 存在 `self` 上，同时记下是哪个回合的：`self.plan_turn = pos.state.turn`（全局回合数：先手是 1、3、5……，后手是 2、4、6……）。用的时候先看 `state.turn` 对不对得上，对不上就当没有计划。
- 按卡牌 id 写，不按 uid：对手没亮过的牌、你以后才抽到的牌，在每份抽样里的 uid 都不一样。`action_key` 能把一个动作换成按卡牌 id 和位置的键，在每份抽样里都一样。
- 执行：在 `veto` 里排除不合计划的动作，或者用 `prior` 给计划里的动作加偏好，或者用 `search` 按计划改这一步的搜索设置。用 `veto` 会挡斩杀线（上面「用 veto 写规则要注意」第 1 条）。

**辅助函数**（都在 `ladder.interface` 里：`from ladder.interface import sample_states, to_next_turn, action_key`）
- `sample_states(pos, guess, rng, n)`：抽 n 份互相独立的完整局面（每份就是一次 `base.sample`）。`guess` 传 `self.guess(pos)`，`rng` 传 `self.random`。
- `to_next_turn(pos, guess, rng, line=(), mine=None, opponent=None, max_actions=200)`：推演到你下个回合开头，返回 `(局面, info)`。只能在你自己回合的决定里调（`turn_start`，或者 `search`、`weights` 这些拿公开局面的钩子在你回合里被问的时候）：换牌那一步、对局已经结束时调会报错（ValueError），报错就是这一方崩溃、判负。`guess(pos)` 在换牌那一步也会被问，别在 `guess` 里调它。
  1. 它自己抽一份局面来推，不改 `pos`。别直接拿 `pos.state` 去推：公开局面里对手的牌库只有亮过的牌，对手一抽牌就判输，推出来全是假的「赢」。
  2. 先按顺序走 `line`（你打算这回合走的动作）；哪一步在这份抽样里不合法（比如抽到的牌不一样），就从那一步起不走了。
  3. 再让 `mine` 打完你这回合（任何有 `act(state, actions)` 的智能体，比如 `GreedyAgent`）；不给就马上结束回合。
  4. 然后对手打一整个回合：默认是 `GreedyAgent(seed=rng.getrandbits(31), samples=1)`（便宜，不查斩杀），也可以传你自己的 `opponent`。
  5. 停在你下个回合的第一个决定之前（这时你已经抽了牌、PP 回满了、倒数也走过了，和真对局一样），或者对局结束，或者一共走满 `max_actions` 步。
  6. 智能体给出不合法的动作，就当它结束回合；对局结束以后什么都不再走。
  7. `info` 里有：`stopped`（`"next_turn"` 到了你下回合，`"over"` 对局结束，`"max_actions"` 走满了）、`line`（`line` 走了几步）、`line_ok`（是不是全走了）、`actions`（一共走了几步）、`winner`（对局结束时的胜方，平局是 -1，没结束是 None）。
  8. 要在同样的未来上比几个候选：每份抽样先从 `self.random` 取一个种子，每个候选都传一个用这个种子新建的 `random.Random`。同一个种子抽出同一份局面、对手也一样，比出来的差别就只来自候选本身。
  9. 返回的局面可以读、可以估值，也可以再 `apply` 往下走；不能直接改它的字段（读代码会拒）。
- `action_key(state, action)`：把动作换成按卡牌 id 和位置的键（就是 `svsim.search.mcts.action_key`）。比如出一张手牌是 `("P", ("H", True, 卡牌 id, 费用, ...), 目标, 模式)`。

**规矩**
1. 钩子里要随机数只用 `self.random`。别碰 `self.rng`（底座给每一步抽样用的）、`self.agent`、`self.tree`（每一步的搜索）：钩子里用了它们，你后面的决定就会跟着变（主持方试过）。
2. 钩子的预算只能按次数或局面数定（比如「4 份抽样 × 3 个候选」「最多 500 个局面」），不能按时间：按时间停没法重放（机器一忙，搜到哪儿停就变了）。读代码不许 import time，也不许用 svsim 搜索的 `seconds` 参数（`ISMCTS`、`MCTSAgent`、`full_game_agent` 的第二个位置参数就是它，所以这几个第一个以后的参数要写成关键字），不许读搜索结果里的耗时 `.seconds`（比如 `LethalSearch.solve(...).seconds`）；自己的参数、属性也别叫 `seconds`。读代码拦不到的写法，主持方的重放抽查会抓。
3. 钩子算在这回合第一个决定里：它的 CPU 算回合开头那一笔（第四节第 1 条），墙钟也在这一步的 30 秒里，超了这一局判负；钩子报错就是这一方崩溃、判负。
4. 不许跨局留会改选择的东西（比如在模块级、类级的字典、列表里存上一局算的结果）：一个工作进程会连着打好几局，同一个种子、同样的局面必须做出同样的选择（第四节第 4 条）。
5. 用的时候才载入训练过的模型的 svsim 帮手不能用（第四节第 2 条），读代码按名字拒收：比如 `foresight.next_lethal_prob`、`foresight.direction_rollout`、`impact.assess`、`candidates.generate`、`CrossTurnAgent`、`TurnsAgent`、`TurnPickAgent`、`FuelAgent`、`ImpactAgent`。只用你给的智能体的照样能用：`impact.reply`、`GreedyAgent`、`LethalAgent`、你自己建的 `ISMCTS`。

**K 大约够做多少推演**

回合开头那一笔是「默认打法在这一步上花的 1.08 倍」再加上「默认打法打你这一整个回合花的 K 倍」，后一半就是给规划的（第四节第 1 条）。现在 K = 2（Salem 还在定）。下面按主持方在电脑上量的数换算（Salem 的电脑，能效核、单进程，第 4 期三副蓝本默认打法互打 48 局，LD-95；单次推演的 3.7 毫秒和下面的 90 分位是同一次测量的明细）：默认打法每个自己回合平均 79.8 毫秒。

| K | 每回合平均多给（电脑上约） | 「3 个候选 × 4 份抽样，贪心打完这回合和对手回合」一整套 12 次推演（中位 48.6 毫秒） | 单次两回合推演（中位 3.7 毫秒） | 只让贪心对手打完一个回合（中位 1.3 毫秒） |
|---|---|---|---|---|
| 1 | 80 毫秒 | 约 1.6 套 | 约 22 次 | 约 61 次 |
| 2（现在） | 160 毫秒 | 约 3.3 套 | 约 43 次 | 约 123 次 |
| 4 | 320 毫秒 | 约 6.6 套 | 约 86 次 | 约 246 次 |

读这张表要注意：
- 表里都是中位数。90 分位大约是中位的 2 倍（一整套 86.3 毫秒、单次 7.7 毫秒、贪心对手 3.5 毫秒），局面复杂时更贵；再算上量的误差，按表里的一半来定比较稳。
- 预算不是一个固定的毫秒数：它是「默认打法在你自己的冒烟局面上打这些回合花了多少」的 K 倍，局面越复杂给得越多。表里只是平均。
- 对手换成看得出斩杀的 `LethalAgent(GreedyAgent(...), planner=True)` 要贵得多：云端一回合中位约 42 毫秒（贪心约 1.8 毫秒）。
- 「1.08 × 默认打法这一步」那一半也在这一笔里：关掉或调小斩杀搜索（`LETHAL`、`LETHAL_NODES`），省下来的也能拿去规划。
- 按 50 局合起来算：有的回合多花、有的回合少花都行，但单步 30 秒的墙钟照样管着每一步。

一个例子：每回合开头比一比「整回合交给贪心」和「先出某一张牌、剩下交给贪心」（最多 3 种先出的牌，每种在同样的 4 份抽样上推到你下回合开头再估值，一共 16 次推演，电脑上大约 60 毫秒）；挑出来的那一步存在 `self` 上，这回合用 `prior` 给它加偏好，最后走哪步还是搜索定。只是演示写法，不一定打得更好；主持方的测试会实际跑它（重放、偷看检查都过）。

```python
import random

from ladder.interface import PlayerStrategy, action_key, to_next_turn
from svsim.agents.greedy_agent import GreedyAgent
from svsim.core.actions import PlayCard
from svsim.core.engine import legal_actions
from svsim.search.evaluate import DEFAULT, evaluate


class Planner(PlayerStrategy):
    SAMPLES = 4                         # 每个候选在几份抽样上比
    CANDIDATES = 3                      # 最多比几种先出的牌

    def __init__(self, seed=0):
        super().__init__(seed)
        self.plan_turn = None           # 计划是哪个回合的（全局回合数）
        self.first = None               # 这回合想先出的那一步（action_key 的键）；None：照搜索的

    def turn_start(self, pos):
        me, guess = pos.me, self.guess(pos)
        firsts, keys = [None], []       # 候选：None 是「整回合都交给贪心」，其余是「先出这张，剩下交给贪心」
        for a in legal_actions(pos.state):
            k = action_key(pos.state, a)
            if isinstance(a, PlayCard) and k not in keys and len(keys) < self.CANDIDATES:
                firsts.append(a)
                keys.append(k)
        score = [0.0] * len(firsts)
        for _ in range(self.SAMPLES):
            seed = self.random.getrandbits(31)
            for i, a in enumerate(firsts):
                rng = random.Random(seed)            # 同一个种子：每个候选在同一份抽样、同一个对手上比
                line = [] if a is None else [a]
                state, info = to_next_turn(pos, guess, rng, line=line, mine=GreedyAgent(seed=seed, samples=1))
                if info["stopped"] == "over":
                    value = 1000.0 if info["winner"] == me else -1000.0
                else:
                    value = evaluate(state, me, DEFAULT, player_moves_next=True)
                score[i] = score[i] + value
        best = max(range(len(firsts)), key=lambda i: (score[i], i == 0))
        self.plan_turn = pos.state.turn
        self.first = None if best == 0 else keys[best - 1]

    def prior(self, state, actions):
        if self.first is None or state.turn != self.plan_turn:
            return None
        hit = [1.0 if action_key(state, a) == self.first else 0.0 for a in actions]
        total = sum(hit)
        return None if total == 0 else [h / total for h in hit]
```

## 四、限制

1. **算力**（interface-2 起按回合给）：主持方从对局记录里认出你每个自己回合的第一个决定（叫「回合开头」，钩子就在这一步里跑），其余的决定（包括换牌）叫「回合里」。收提交时让默认打法在你的冒烟局面上也算一遍来比，下面两条过一条就收：
   - **老规矩**（和 interface-1 一样）：所有决定加起来，不超过默认打法的 1.08 倍；量出来超过 1.15 倍，这一条才不过。
   - **新规矩**：回合里的决定加起来，不超过默认打法在这些决定上的 1.08 倍（量出来超过 1.15 倍不过）；**并且**回合开头的决定加起来，不超过「默认打法在这些决定上的 1.08 倍，再加上 K 倍的默认打法打你这些回合的全部花费」（量出来超过这条线的 1.065 倍不过：1.065 = 1.15 ÷ 1.08，和老规矩一样的余量，量完误差可能再调）。K 现在是 2（Salem 还在定）。
   - 两条都不过才拒收。
   - 都是 50 对冒烟局合起来算，也就是按平均：这回合多花、那回合少花都可以。用不完的作废；走新规矩时，回合里和回合开头两笔各算各的，不能互相挪。
   - 花在哪一步就记在哪一步：回合开头那一步里花的（钩子、`search` 调大的 `iterations`、这一步的斩杀搜索）都算回合开头那一笔；斩杀搜索每一步都会跑，回合里那几步的算回合里（第五节）；在 `veto`、`prior` 里推演，花在哪一步就算哪一步。主持方只看对局记录，你的代码报什么都不算。
   - 不管走哪条，每一步（包括回合开头那一步里的钩子）都在 30 秒的墙钟上，超了这一局判负。
   - 量法有误差（老规矩那一个数，电脑上上下约 1%；回合里、回合开头两笔各自的误差都还在量，两笔都比合起来的那个数小，误差会更大）。细则见 submit.md 第三节第 7 项。加搜索次数、换更贵的估值都算在里面。
   - 打法更新（第 5 期起才有）的检验怎么算规划用的算力，主持方还在和 Salem 定，定了写在这里。
2. **不用训练过的模型**：不加载任何训练过的网络、驾驶员或它们的数据。svsim 里有些帮手用的时候才去载入它们，读代码按名字拒收（第三节「回合开始钩子」的规矩第 5 条）。
3. **只用钩子给你的东西**：不读文件、不联网、不碰别的进程，不去翻调用栈或内存找真实局面。提交时会检查（细则见 submit.md）。
4. **要能重放**：同一个种子、同样的局面，你的打法必须做出同样的选择。需要随机数时用 `self.random`（由这局的种子派生，和搜索、抽样用的随机数分开），不用时间、不用全局的 `random`。钩子里也一样只用 `self.random`。不许跨局留会改选择的东西（模块级、类级的容器里存上一局算的结果）：一个工作进程会连着打好几局。要自己写 `__init__` 的话，先调 `super().__init__(seed)`。主持方会抽查重放。
5. **一个成员一个打法类**。改打法就是交新版本，过检验才生效。

## 五、底座已知的局限（base-1）

- 对手靠效果拿到的牌一律当作公开的，虽然少数效果其实不亮牌。
- 对手手牌或牌库里被效果改过的牌（费用、攻防），在抽出来的局面里会变回原样。
- 每次决策从猜测里抽一份卡表；猜测里剩下的牌比对手未知的牌多时，这次决策随机取其中一部分。
- **斩杀搜索有预算，会漏斩杀**（斩杀题库验收的结论：默认打法不动，预算由你自己定）。粗估伤害是一张牌一张牌单独算的，几张牌配合才打得出的伤害（亡语、靠法术推进的倒数、要一起加攻才够的）它看不出来，这时只搜 200 个局面，多半找不到。局面复杂的时候，2000 个局面也可能搜不完。主持方量过：默认打法互打、公开卡表的天梯局面里（电脑上 300 局），确定能斩杀的 287 个，默认打法 3 遍都打出来 266 个（93%），3 遍都没打出来 17 个；随机卡组、随机打法的局面里（云端），239 个里 3 遍都打出来 229 个（96%）；一道靠海盗旗亡语的题，默认打法打不出来，`LETHAL_NODES = 20000`、`LETHAL_SCREEN = None` 打得出来。代价：不粗估、搜 2 万个，每个回合开头平均多约 2.5 秒（云端），差不多是默认打法打一整个回合（云端约 114 毫秒）的 22 倍，K = 4 也付不起。而且斩杀搜索**每个决定都会跑**，不只是回合开头：底座每一步都重新抽一份局面，牌序和以后的随机结果都换了，斩杀搜索认不出是同一个局面，就再搜一遍（主持方在 2 局里数过：回合开头的决定 34 个里搜了 32 次，回合里的 104 个里搜了 102 次，回合里搜的局面反而更多）。所以调大 `LETHAL_NODES`、去掉粗估，回合开头和回合里两笔一起涨，回合里那一笔多半先超过新规矩的 1.15 倍（第四节第 1 条），K 帮不上忙。要在预算里换，比如放宽粗估（`n` 调大）而不是全不粗估，或者少搜几次 `iterations`。想拿 K 换更深的斩杀，只能在 `turn_start` 里自己在抽样上跑斩杀搜索（`svsim.search.lethal.LethalSearch`），把找到的线存在 `self` 上，再用 `prior` 或 `veto` 去执行；类属性的斩杀预算留小。

## 六、别的说明

- 怎么提交、提交时查什么：见 submit.md。
- 练习场怎么用：见 arena.md。
