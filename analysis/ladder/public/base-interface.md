# 打法接口说明（给选手）

版本：接口 interface-1，底座 base-1。写于 2026-11-22（主持方）。这份说明会随底座和接口的版本更新；你的成员记录着它用的是哪个版本。

## 一、你交的「打法」是什么

一个 Python 类，继承 `ladder.interface.PlayerStrategy`，放在你自己的模块里。它坐在默认打法的位置上：每到你做决定，底座先按你自己的猜测抽出一个完整局面，再让搜索在这个局面上选一步。你能改的是下面第三节列的几个点，其余照默认打法。

**什么都不改，就是默认打法**（通用 bot `mcts:100+plan`：每步 100 次搜索的 ISMCTS，前面挡着精确斩杀搜索和它的规划器）。主持方验收过：不改任何点的子类和默认打法逐个决策完全一样。

## 二、你看得到什么（信息条件）

- 开局前：只知道对手的职业。不知道对手的卡表、牌序、手牌。
- 对局中：和真人玩家看到的一样。对手职业；对手打出或亮出过的牌；双方场面；对手手牌和牌库的张数；你自己的手牌和卡表。
- 你的代码**拿不到真实局面**。每个钩子拿到的要么是公开局面 `pos`（`ladder.base.PublicPosition`），要么是底座按你的猜测抽出来的一个局面 `state`。抽出来的局面里，对手的未知牌来自你自己的猜测，牌序重新洗过，以后的随机结果重新定过。

## 三、能改的点

| 钩子 | 拿到什么 | 返回什么 | 默认 |
|---|---|---|---|
| `guess(pos)` | 公开局面 | 对手卡表的猜测：`[(40 张牌的列表, 权重), ...]`。底座会按对手亮过的牌更新权重 | 对手打的是它那个职业的基线卡表 |
| `mulligan(state)` | 抽出来的局面（换牌阶段） | 一个换牌动作 | 通用 bot 的换牌 |
| `weights(pos)` | 公开局面 | `svsim.search.evaluate.Weights`：手写估值的各项数值。每步都会问，所以可以按对手职业、按回合不同 | `DEFAULT` |
| `evaluate(state, me, me_next)` | 抽出来的局面；`me` 是你；`me_next` 为真表示轮到你走 | 一个数，越大对你越好。整个替换估值。和 `weights` 只能改一个 | 不改：用 `weights` 的估值 |
| `veto(state, action)` | 抽出来的局面、一个合法动作 | 真 = 这一步不考虑。搜索里每一层都用，斩杀搜索的路线也遵守。全都被排除时全部保留 | 不改：什么都不排除 |
| `prior(state, actions)` | 抽出来的局面、合法动作 | 对这些动作的概率（加起来是 1），或 None。只在根节点加一个偏好：c_prior × P × √(根访问数) / (1 + 访问数) | 不改：没有偏好 |
| `search(pos)` | 公开局面 | 这一步的搜索设置，可以有：`iterations`（默认 100）、`c`（探索系数，0.5）、`scale`（估值折算成胜率的尺度，8.0）、`max_depth`（30）、`c_prior`（0.3）。别的键会被拒绝 | `{}` |
| 类属性 `LETHAL` | — | `"planner"`（精确斩杀搜索 + 规划器，默认）、`"exact"`（只有精确斩杀搜索）、`"off"`（不做斩杀搜索） | `"planner"` |

一个照抄默认打法的骨架（每个点都写出来，结果和默认打法一样）：

```python
from ladder import base
from ladder.interface import PlayerStrategy
from svsim.agents.greedy_agent import mulligan as bot_mulligan
from svsim.search.evaluate import DEFAULT, evaluate


class MyStrategy(PlayerStrategy):
    LETHAL = "planner"

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
```

## 四、限制

1. **算力**：每步平均 CPU 上限是默认打法的 1.08 倍（在你自己的冒烟局面上，让默认打法也算一遍来比）。量法有误差（电脑上上下约 1%），收提交时量出来超过 1.15 倍才拒收（submit.md 第三节第 7 项）。加搜索次数、换更贵的估值都算在里面。
2. **不用训练过的模型**：不加载任何训练过的网络、驾驶员或它们的数据。
3. **只用钩子给你的东西**：不读文件、不联网、不碰别的进程，不去翻调用栈或内存找真实局面。提交时会检查（细则见 submit.md）。
4. **要能重放**：同一个种子、同样的局面，你的打法必须做出同样的选择。需要随机数时用 `self.random`（由这局的种子派生，和搜索、抽样用的随机数分开），不用时间、不用全局的 `random`。要自己写 `__init__` 的话，先调 `super().__init__(seed)`。主持方会抽查重放。
5. **一个成员一个打法类**。改打法就是交新版本，过检验才生效。

## 五、底座已知的局限（base-1）

- 对手靠效果拿到的牌一律当作公开的，虽然少数效果其实不亮牌。
- 对手手牌或牌库里被效果改过的牌（费用、攻防），在抽出来的局面里会变回原样。
- 每次决策从猜测里抽一份卡表；猜测里剩下的牌比对手未知的牌多时，这次决策随机取其中一部分。

## 六、还没写的

- ~~怎么提交、提交时查什么~~：见 submit.md。
- 练习场怎么用：对冻结池的副本和锚点打、只发调参种子、能从某局某个局面续打、局数计数（阶段 2.4）。
