# 第 10 弹加卡：分析线写的四个职业

条件：对手卡表已知（牌序、手牌未知）

这是 Salem 10-28 17:59Z 要的「先在模拟器更新一下游戏的新卡」的分析线那一半。架构线 18:09Z 分工：分析线写巫师、夜魔、主教、复仇者，建造线写中立、皇家、龙、妖精，写完互审。加卡属于开发工作，不装档、不发布。

## 交付

- 补丁在 `patches/`，一个职业一个提交，共 4 个。
- 基线是建造线的 `463b898`（set 10 的引擎钩子）。在它上面 `git am analysis/cards-s10/patches/*.patch` 就能接上。
- 只改了 `svsim/cards/{rune,abyss,haven,portal}.py`、对应的 `tests/test_cards_*.py`，以及 `svsim/cards/pending.py`（把写好的卡移出 PENDING）。公共文件一行没动。

| 补丁 | 职业 | 脚本 | 新测试 |
|---|---|---|---|
| 0001 | 巫师（Runecraft） | 10 张卡 + 2 个纹章 | 10 个 |
| 0002 | 夜魔（Abysscraft） | 10 张卡 + 1 个纹章 | 12 个 |
| 0003 | 主教（Havencraft） | 10 张卡 + 2 个纹章 + 地害之兔 | 11 个 |
| 0004 | 复仇者（Portalcraft） | 9 张卡 + 1 个纹章；异界来访者只有关键词，不用脚本 | 12 个 |

合计 47 个卡号移出 PENDING：巫师 12、夜魔 11、主教 13、复仇者 11。架构线说的 13 / 13 / 12 / 17 是另一种数法，其余衍生卡要么早有脚本，要么是白板。

## 用到的建造线接口（463b898 / 931775d）

- `E.CLUE`、`E.clues`、`E.consume_clues`：Nocturne's Interrogation、Calamity in Custody。
- 监听 `on_card_banished`：Solemn Gravekeeper、Attending Amanuensis、Nocturne、Parareligious Idol。证据合并也会触发。
- 监听 `on_ally_fuse`：Extinctionist Socialite、Extinctionist Dandy、Dimensional Wanderer 和它的纹章。
- `E.engaged_amulet_this_turn`：Discerning Melody。
- 倒计时到 0 的那个回合，「回合开始时」仍然发动：Fruitless Testimony 和 Lapinette 的纹章。

接口到之前，我在本地 worktree 里垫了一层临时实现，接口名照我提的写。建造线的版本只有一处名字不同（`engaged_amulet_this_turn`），已改成正式的。垫层没交出去。

## 核查（标准照 10-07）

1. **EN / CHS 对照**：47 张卡逐张对过英文和简中原文。两种语言不一致、或原文没写清楚的地方，按下表处理。
2. **每张卡都有测试**：45 个新测试；纹章和地害之兔各有专门的断言，异界来访者测关键词和「没有脚本」。
3. **突变检查**：在 set 10 的代码里逐个造突变体，每次只改一处：
   - 把钩子的函数体换成 `return`；
   - 整数加 1；
   - 模式号互换；
   - `==` 和 `!=` 互换。

   每个突变体都要让该职业的测试文件失败。最终 172 个突变体全部被抓，见下面「结果」一节。
   - 第一轮里有两类假结果，都已经排除：
     - 文档字符串里的数字被当成了代码；
     - 同样大小的突变文件在同一秒内写回时，Python 会继续用旧的 .pyc，可能把上一个突变体带进下一次测试。现在每次都删掉 `__pycache__`，并且用 `-B` 运行。
   - 期间补了 6 个测试：
     - 巫师 2 处：Noeinhowell 纹章恰好回 1 点 PP；Wily Witch 只提供两个单选模式；
     - Solemn Gravekeeper 只强化 1 个亡者；
     - Fruitless Testimony 只提供两个单选模式；
     - Hand of Extinction 融合后恰好 8 点伤害；
     - Extinctionist Dandy 和 Calamity in Custody 在有多个候选时只破坏 1 个。
4. **随机对局**：每个职业 300 局，`qa/games.py`。
   - 卡组是本职业 10 张新卡各 3 张，再加 10 张随机的其他已有脚本的卡；对手是随机职业的随机卡组。
   - 每一步都检查 `test_fuzz.check_invariants`。
   - 另用 `qa/hookcov.py` 统计钩子：新卡的每个钩子都至少发动过 43 次。

### 结果

| 职业 | 突变体 | 被抓 | 300 局随机对局 |
|---|---|---|---|
| 巫师 | 53 | 53 | 不崩；先手方 146 胜、后手方 154 胜，平均 19.9 回合 |
| 夜魔 | 33 | 33 | 不崩；154 / 146，18.9 回合 |
| 主教 | 49 | 49 | 不崩；145 / 155，18.2 回合 |
| 复仇者 | 37 | 37 | 不崩；154 / 146，20.4 回合 |

- 4 个补丁在 463b898 上用 `git am` 接得上，结果和我这边的树逐字节相同。
- 全套测试在 463b898 + 这 4 个补丁上：1317 passed，7 skipped，4 failed。
- 失败的 4 个都是 `test_golden_search`。它们在干净的 4d3d4b5 上、在我的容器里就失败（决策 6 对不上），和加卡无关。建造线那边的说法是 golden search 没变。

## 解读和假设（请审的人重点看）

| 卡 | 处理 | 依据 |
|---|---|---|
| Calamity in Custody | 「证据 -2」当成代价：不够 2 就不破坏，回复 2 照常 | EN "Consume 2 clues to destroy …" 是代价句式；CHS「使…证据-2，破坏…」两种读法都行 |
| Lineage | 主战者生命上限减半，向上取整 | 原文没写取整；向上取整不会因为减半直接判负 |
| Nocturne's Interrogation、Infernal Chimera | X = 0 时不造成伤害（屏障留着） | 和 Missionary of Recruitment 的写法一致 |
| Infernal Chimera | 用引擎的 `split_damage`：从最早的随从开始分，剩下的打主战者 | 和现有「分配伤害」卡一致 |
| Extinctionist Socialite、Dandy | 「融合护符时」：一次融合里只要有护符，就发动 1 次，不按护符张数算 | 「自己【融合】护符时」 |
| Hand of Extinction、Calamity in Custody、Lineage | 「与本卡牌融合时召唤证据」：每次融合 1 张，不按融进去的张数算 | 同上 |
| 地害之兔 | 按当前费用找最便宜的牌，并列时随机；手牌是空的也照样进化；这次进化不算用进化点 | 「本随从进化」 |
| Parareligious Idol | 每张消失的敌方随从复制 1 个，完全复制（带伤害和增益） | EN "an exact copy of it"；CHS「召唤对应数量的复制随从」 |
| 夜魔三张「自己的卡牌在战场上消失时」 | 护符也算；怨灵在自己回合结束时消失，仍算「自己的回合」 | 原文「卡牌」；回合结束时还是自己的回合 |
| Lapinette | 超进化时先拿纹章（倒计时 1），再推迟 1，所以纹章会召唤 2 次兔子 | 引擎先发「进化时」再发「超进化时」 |

## 文件

- `patches/`：4 个补丁。
- `qa/mutate.py`、`qa/games.py`、`qa/hookcov.py`：上面的核查脚本，在仓库根目录运行。
