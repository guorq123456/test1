# 运营局面题（从 M4 自动挑，复测过的；README-puzzles.md）

**条件**：对手卡表已知（牌序、手牌未知）。

## 题 1：k = 320

- **对局**：Salem 第 1 批，对局号 1791305215412，动作序号 39；Salem 坐 0 号位。
- **回合**：全局第 13 回合，Salem 自己的第 7 回合；M3 归类 mixed。
- **复测**（default 方向，各 48 局，种子 67003500 派生）：Salem 的线 0.771，bot 的线 0.000，配对差 **+0.771**（+0.646～+0.875）。M4 里 K = 12 时的差 +0.917。

**当时的局面**（Salem 视角）

```
第 13 回合（你的回合）
对手：主战者 20/20  PP 0/9  进化点 0  超进化点 1  牌组 30  墓场 7  手牌 3
  战场：「约束的《正义》·伊兰翠（Erntz, Governing Justice）」 11/11 威慑 超进化
你：主战者 9/20  PP 10/10  进化点 2  超进化点 2  牌组 27  墓场 8
  战场：（空）
  手牌：「焦灰的安纳提玛·班德奈特（Burnite, Anathema of Ash）」 9费 9/9；「日珥咆哮（Roar of Prominence）」 4费；「约束的《正义》·伊兰翠（Erntz, Governing Justice）」 10费 8/8 守护；「古旧天刀·波菈莱（Vorlalai, Eld Blades）」 2费 0/2 毁灭；「焦灰的安纳提玛·班德奈特（Burnite, Anathema of Ash）」 9费 9/9；「金银绚烂·璐米欧儿&雅尔贞特（Lumiore & Argente, Shining Wings）」 8费 6/6；「满面笑容的烹饪·琪米卡（Kimika, Cook of Happiness）」 2费 2/1
  对手手牌（Salem 当时看不到）：「古旧天刀·波菈莱（Vorlalai, Eld Blades）」 2费 0/2 毁灭；「日珥咆哮（Roar of Prominence）」 4费；「天刀深渊（Depths of the Eld Blades）」 2费
```

**Salem 这回合的打法**

1. 使用「满面笑容的烹饪·琪米卡（Kimika, Cook of Happiness）」，选择 己方手牌中的「古旧天刀·波菈莱（Vorlalai, Eld Blades）」
2. 超进化「古旧天刀·波菈莱（Vorlalai, Eld Blades）」
3. 使用「断头的斩姬·相枛津（Sagatsumatsu, Fair Beheader）」，选择 己方手牌中的「天刀深渊（Depths of the Eld Blades）」
4. 使用「赤流（Spilling Red）」，选择 己方手牌中的「天刀深渊（Depths of the Eld Blades）」、敌方场上的「约束的《正义》·伊兰翠（Erntz, Governing Justice）」
5. 「断头的斩姬·相枛津（Sagatsumatsu, Fair Beheader）」攻击敌方主战者
6. 结束回合

**bot（`mcts:100+plan+learned+phased`，第 0 步的计划）这回合的打法**

1. 使用「约束的《正义》·伊兰翠（Erntz, Governing Justice）」
2. 结束回合

**Salem 的线打完以后**（ended；Salem 视角，对手要行动）

```
第 14 回合（对手的回合）
对手：主战者 13/20  PP 10/10  进化点 0  超进化点 1  牌组 29  墓场 8  手牌 4
  战场：（空）
你：主战者 12/20  PP 0/10  进化点 2  超进化点 1  牌组 26  墓场 12
  战场：「满面笑容的烹饪·琪米卡（Kimika, Cook of Happiness）」 2/1；「古旧天刀·波菈莱（Vorlalai, Eld Blades）」 3/5 毁灭 超进化；「断头的斩姬·相枛津（Sagatsumatsu, Fair Beheader）」 5/4 疾驰、毁灭、灵气
  手牌：「焦灰的安纳提玛·班德奈特（Burnite, Anathema of Ash）」 9费 9/9；「日珥咆哮（Roar of Prominence）」 4费；「约束的《正义》·伊兰翠（Erntz, Governing Justice）」 10费 8/8 守护；「焦灰的安纳提玛·班德奈特（Burnite, Anathema of Ash）」 9费 9/9；「金银绚烂·璐米欧儿&雅尔贞特（Lumiore & Argente, Shining Wings）」 8费 6/6；「天刀深渊（Depths of the Eld Blades）」 2费；「赤流（Spilling Red）」 1费
```

**bot 的线打完以后**（ended；Salem 视角，对手要行动）

```
第 14 回合（对手的回合）
对手：主战者 20/20  PP 10/10  进化点 0  超进化点 1  牌组 29  墓场 7  手牌 4
  战场：「约束的《正义》·伊兰翠（Erntz, Governing Justice）」 11/3（上限 11） 威慑 超进化 可攻击
你：主战者 17/20  PP 0/10  进化点 2  超进化点 2  牌组 27  墓场 8
  战场：「约束的《正义》·伊兰翠（Erntz, Governing Justice）」 8/8 守护
  手牌：「焦灰的安纳提玛·班德奈特（Burnite, Anathema of Ash）」 9费 9/9；「日珥咆哮（Roar of Prominence）」 4费；「古旧天刀·波菈莱（Vorlalai, Eld Blades）」 2费 0/2 毁灭；「焦灰的安纳提玛·班德奈特（Burnite, Anathema of Ash）」 9费 9/9；「金银绚烂·璐米欧儿&雅尔贞特（Lumiore & Argente, Shining Wings）」 8费 6/6；「满面笑容的烹饪·琪米卡（Kimika, Cook of Happiness）」 2费 2/1
```

## 题 2：k = 518

- **对局**：Salem 第 2 批，对局号 1791387160337，动作序号 56；Salem 坐 0 号位。
- **回合**：全局第 16 回合，Salem 自己的第 8 回合；M3 归类 mixed。
- **复测**（default 方向，各 48 局，种子 67039500 派生）：Salem 的线 0.542，bot 的线 0.000，配对差 **+0.542**（+0.396～+0.667）。M4 里 K = 12 时的差 +0.333。

**当时的局面**（Salem 视角）

```
第 16 回合（你的回合）
对手：主战者 11/20  PP 0/10  进化点 1  超进化点 0  牌组 21  墓场 15  手牌 4
  战场：「掌握天空命运的少女·露莉亚（Lyria, Skydestined）」 1/1 屏障；「禁牙的变貌·诺玛格达拉（Normagdala, Ravening Revenant）」 8/9 守护 超进化；「满面笑容的烹饪·琪米卡（Kimika, Cook of Happiness）」 2/1；「古旧天刀·波菈莱（Vorlalai, Eld Blades）」 0/2 毁灭
你：主战者 3/20  PP 10/10  进化点 1  超进化点 0  牌组 25  墓场 16
  战场：（空）
  手牌：「日珥咆哮（Roar of Prominence）」 4费；「龙之启示（Dragonsign）」 3费；「懒惰的波摇花（Sloth of the Crestpetal）」 2费；「赤流（Spilling Red）」 1费；「古旧天刀·波菈莱（Vorlalai, Eld Blades）」 2费 0/2 毁灭；「约束的《正义》·伊兰翠（Erntz, Governing Justice）」 10费 8/8 守护；「掌握天空命运的少女·露莉亚（Lyria, Skydestined）」 2费 1/1 屏障；「断头的斩姬·相枛津（Sagatsumatsu, Fair Beheader）」 7费 5/4 疾驰、毁灭、灵气；「满面笑容的烹饪·琪米卡（Kimika, Cook of Happiness）」 2费 2/1
  对手手牌（Salem 当时看不到）：「宣扬的龙人（Dragonewt Promoter）」 2费 2/1 突进；「宣扬的龙人（Dragonewt Promoter）」 2费 2/1 突进；「约束的《正义》·伊兰翠（Erntz, Governing Justice）」 10费 8/8 守护；「世界的伙伴·佐伊（Zooey, Ally of the World）」 5费 5/5
```

**Salem 这回合的打法**

1. 使用「约束的《正义》·伊兰翠（Erntz, Governing Justice）」
2. 使用额外能量点
3. 使用「赤流（Spilling Red）」，选择 己方手牌中的「古旧天刀·波菈莱（Vorlalai, Eld Blades）」、敌方场上的「禁牙的变貌·诺玛格达拉（Normagdala, Ravening Revenant）」
4. 进化「古旧天刀·波菈莱（Vorlalai, Eld Blades）」
5. 「古旧天刀·波菈莱（Vorlalai, Eld Blades）」攻击敌方场上的「掌握天空命运的少女·露莉亚（Lyria, Skydestined）」
6. 结束回合

**bot（`mcts:100+plan+learned+phased`，第 0 步的计划）这回合的打法**

1. 使用「约束的《正义》·伊兰翠（Erntz, Governing Justice）」
2. 进化「约束的《正义》·伊兰翠（Erntz, Governing Justice）」
3. 「约束的《正义》·伊兰翠（Erntz, Governing Justice）」攻击敌方场上的「禁牙的变貌·诺玛格达拉（Normagdala, Ravening Revenant）」
4. 结束回合

**Salem 的线打完以后**（ended；Salem 视角，对手要行动）

```
第 17 回合（对手的回合）
对手：主战者 11/20  PP 10/10  进化点 1  超进化点 0  牌组 20  墓场 19  手牌 5
  战场：（空）
你：主战者 11/20  PP 0/10  进化点 0  超进化点 0  牌组 25  墓场 18
  战场：「约束的《正义》·伊兰翠（Erntz, Governing Justice）」 8/8 守护；「古旧天刀·波菈莱（Vorlalai, Eld Blades）」 2/3（上限 4） 毁灭 已进化
  手牌：「日珥咆哮（Roar of Prominence）」 4费；「龙之启示（Dragonsign）」 3费；「懒惰的波摇花（Sloth of the Crestpetal）」 2费；「掌握天空命运的少女·露莉亚（Lyria, Skydestined）」 2费 1/1 屏障；「断头的斩姬·相枛津（Sagatsumatsu, Fair Beheader）」 7费 5/4 疾驰、毁灭、灵气；「满面笑容的烹饪·琪米卡（Kimika, Cook of Happiness）」 2费 2/1；「天刀深渊（Depths of the Eld Blades）」 2费
```

**bot 的线打完以后**（ended；Salem 视角，对手要行动）

```
第 17 回合（对手的回合）
对手：主战者 3/20  PP 10/10  进化点 1  超进化点 0  牌组 20  墓场 16  手牌 5
  战场：「掌握天空命运的少女·露莉亚（Lyria, Skydestined）」 1/1 屏障 可攻击；「满面笑容的烹饪·琪米卡（Kimika, Cook of Happiness）」 2/1 可攻击；「古旧天刀·波菈莱（Vorlalai, Eld Blades）」 0/2 毁灭 可攻击
你：主战者 3/20  PP 0/10  进化点 0  超进化点 0  牌组 25  墓场 16
  战场：「约束的《正义》·伊兰翠（Erntz, Governing Justice）」 10/2（上限 10） 威慑 已进化
  手牌：「日珥咆哮（Roar of Prominence）」 4费；「龙之启示（Dragonsign）」 3费；「懒惰的波摇花（Sloth of the Crestpetal）」 2费；「赤流（Spilling Red）」 1费；「古旧天刀·波菈莱（Vorlalai, Eld Blades）」 2费 0/2 毁灭；「掌握天空命运的少女·露莉亚（Lyria, Skydestined）」 2费 1/1 屏障；「断头的斩姬·相枛津（Sagatsumatsu, Fair Beheader）」 7费 5/4 疾驰、毁灭、灵气；「满面笑容的烹饪·琪米卡（Kimika, Cook of Happiness）」 2费 2/1
```

## 题 3：k = 445

- **对局**：Salem 第 2 批，对局号 1791317238047，动作序号 49；Salem 坐 0 号位。
- **回合**：全局第 16 回合，Salem 自己的第 8 回合；M3 归类 conserve。
- **复测**（default 方向，各 48 局，种子 67027500 派生）：Salem 的线 0.667，bot 的线 0.125，配对差 **+0.542**（+0.375～+0.708）。M4 里 K = 12 时的差 +0.417。

**当时的局面**（Salem 视角）

```
第 16 回合（你的回合）
对手：主战者 13/20  PP 0/10  进化点 1  超进化点 0  牌组 25  墓场 9  手牌 5
  战场：「约束的《正义》·伊兰翠（Erntz, Governing Justice）」 11/11 威慑 超进化
你：主战者 5/20  PP 10/10  进化点 0  超进化点 2  牌组 27  墓场 14
  战场：（空）
  手牌：「约束的《正义》·伊兰翠（Erntz, Governing Justice）」 10费 8/8 守护；「金银绚烂·璐米欧儿&雅尔贞特（Lumiore & Argente, Shining Wings）」 8费 6/6；「懒惰的波摇花（Sloth of the Crestpetal）」 2费；「赤流（Spilling Red）」 1费；「古旧天刀·波菈莱（Vorlalai, Eld Blades）」 2费 0/2 毁灭
  对手手牌（Salem 当时看不到）：「《世界》的呈现（Fate of the World）」 5费；「宣扬的龙人（Dragonewt Promoter）」 2费 2/1 突进；「焦灰的安纳提玛·班德奈特（Burnite, Anathema of Ash）」 9费 9/9；「宣扬的龙人（Dragonewt Promoter）」 2费 2/1 突进；「断头的斩姬·相枛津（Sagatsumatsu, Fair Beheader）」 7费 5/4 疾驰、毁灭、灵气
```

**Salem 这回合的打法**

1. 使用「赤流（Spilling Red）」，选择 己方手牌中的「古旧天刀·波菈莱（Vorlalai, Eld Blades）」、敌方场上的「约束的《正义》·伊兰翠（Erntz, Governing Justice）」
2. 使用额外能量点
3. 使用「约束的《正义》·伊兰翠（Erntz, Governing Justice）」
4. 结束回合

**bot（`mcts:100+plan+learned+phased`，第 0 步的计划）这回合的打法**

1. 使用「金银绚烂·璐米欧儿&雅尔贞特（Lumiore & Argente, Shining Wings）」，选择 己方手牌中的「约束的《正义》·伊兰翠（Erntz, Governing Justice）」、己方手牌中的「懒惰的波摇花（Sloth of the Crestpetal）」
2. 使用「赤流（Spilling Red）」，选择 己方手牌中的「古旧天刀·波菈莱（Vorlalai, Eld Blades）」、敌方场上的「约束的《正义》·伊兰翠（Erntz, Governing Justice）」
3. 超进化「古旧天刀·波菈莱（Vorlalai, Eld Blades）」
4. 使用额外能量点
5. 使用「天刀深渊（Depths of the Eld Blades）」
6. 结束回合

**Salem 的线打完以后**（ended；Salem 视角，对手要行动）

```
第 17 回合（对手的回合）
对手：主战者 13/20  PP 10/10  进化点 1  超进化点 0  牌组 24  墓场 10  手牌 6
  战场：（空）
你：主战者 13/20  PP 0/10  进化点 0  超进化点 2  牌组 27  墓场 16
  战场：「古旧天刀·波菈莱（Vorlalai, Eld Blades）」 0/2 毁灭；「约束的《正义》·伊兰翠（Erntz, Governing Justice）」 8/8 守护
  手牌：「金银绚烂·璐米欧儿&雅尔贞特（Lumiore & Argente, Shining Wings）」 8费 6/6；「懒惰的波摇花（Sloth of the Crestpetal）」 2费
```

**bot 的线打完以后**（ended；Salem 视角，对手要行动）

```
第 17 回合（对手的回合）
对手：主战者 8/20  PP 10/10  进化点 1  超进化点 0  牌组 24  墓场 10  手牌 6
  战场：（空）
你：主战者 6/20  PP 0/10  进化点 0  超进化点 1  牌组 27  墓场 19
  战场：「金银绚烂·璐米欧儿&雅尔贞特（Lumiore & Argente, Shining Wings）」 6/6；「古旧天刀·波菈莱（Vorlalai, Eld Blades）」 3/5 毁灭 超进化
  手牌：「天刀深渊（Depths of the Eld Blades）」 2费；「天刀深渊（Depths of the Eld Blades）」 2费
```

