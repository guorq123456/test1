# 搜索 A：变体试没试第 10 弹的卡（第 1～10 轮，不打新对局）

条件：对手卡表已知（牌序、手牌未知）

重放核对：{'winner found': 70, 'deck code match': 488}

## (a) 换上至少一张第 10 弹卡的变体占比

| 轮 | 变体 | 含第 10 弹 | 占比 | 同样的 variant() 随机抽的期望占比 |
|---|---|---|---|---|
| 1 | 56 | 11 | 19.6% | 29.0% |
| 2 | 56 | 16 | 28.6% | 27.6% |
| 3 | 56 | 17 | 30.4% | 28.8% |
| 4 | 56 | 15 | 26.8% | 28.8% |
| 5 | 56 | 12 | 21.4% | 27.3% |
| 6 | 56 | 13 | 23.2% | 27.5% |
| 7 | 56 | 10 | 17.9% | 26.5% |
| 8 | 56 | 14 | 25.0% | 27.6% |
| 9 | 56 | 20 | 35.7% | 27.7% |
| 10 | 56 | 17 | 30.4% | 28.0% |
| 合计 | 560 | 145 | 25.9% | 27.9% |

各职业可选卡池里第 10 弹卡的占比（本职业 + 中立、有脚本、非衍生）：
- FOREST: 14.2%
- SWORD: 14.2%
- RUNE: 14.0%
- DRAGON: 14.2%
- ABYSS: 14.2%
- HAVEN: 14.2%
- PORTAL: 14.2%

## (b) 减半第 0 段（所有变体同一批 28 个发牌）对现任的配对差

每个变体先求 28 个发牌的平均差，再按变体平均；标准误按变体之间的差异算。

| 分组 | 变体数 | 平均配对差 | 标准误 |
|---|---|---|---|
| 含第 10 弹 | 145 | -3.7% | 0.5% |
| 不含 | 415 | -2.0% | 0.3% |
| 换 1 张，含第 10 弹 | 38 | -0.8% | 0.7% |
| 换 1 张，不含 | 189 | -1.0% | 0.3% |
| 换 2 张，含第 10 弹 | 49 | -4.2% | 0.8% |
| 换 2 张，不含 | 130 | -2.6% | 0.5% |
| 换 3 张，含第 10 弹 | 58 | -5.1% | 0.9% |
| 换 3 张，不含 | 96 | -3.2% | 0.6% |

按换卡张数分层后的差（含 − 不含）：-1.2% ± 0.6%

## (c) 含第 10 弹卡的变体走到哪一步

- 含第 10 弹卡的变体 145 个：进第 1 段 60 个，进第 2 段 30 个，成为减半胜者 16 个。
- 对照：不含的 415 个：进第 1 段 220 个，进第 2 段 110 个，成为减半胜者 54 个。
- 含第 10 弹卡的减半胜者：
  - 第 1 轮 FOREST：换上 脚踩天穹的《倒吊人》·罗弗拉德、慈颜的拥趸、优雅看护者；undecided，复核 +1.1% ± 1.3%
  - 第 1 轮 SWORD：换上 表里侦探·诺·莱芙；no change (halving)
  - 第 2 轮 FOREST：换上 煌响使者·亨莉雅妲、水镜的信赖、群狼侍者；rejected，复核 -1.4% ± 1.3%
  - 第 3 轮 PORTAL：换上 人造的馈赠·蕾拉、知恩图报·米莉亚姆、人灭执事；rejected，复核 -3.7% ± 1.6%
  - 第 4 轮 RUNE：换上 信仰天使·迪纳梅斯；rejected，复核 -0.8% ± 0.9%
  - 第 5 轮 SWORD：换上 织田信长、宝石淑女；no change (halving)
  - 第 6 轮 FOREST：换上 不屈的剑斗士、理想国·涅格尔赫亚；no change (halving)
  - 第 6 轮 ABYSS：换上 爱意天使·艾克夏丝；rejected，复核 -2.4% ± 1.3%
  - 第 7 轮 FOREST：换上 被侵略的世界、金刚伙伴、自然的再生；undecided，复核 +0.4% ± 1.1%
  - 第 7 轮 SWORD：换上 千金大参谋·阿尔梅莉洁；undecided，复核 +0.5% ± 0.8%
  - 第 8 轮 SWORD：换上 信仰天使·迪纳梅斯；no change (halving)
  - 第 8 轮 RUNE：换上 最古老的狱卒、弑神现场；rejected，复核 -3.0% ± 1.4%
  - 第 9 轮 SWORD：换上 《世界》的呈现、《世界》的呈现、变心卫士；rejected，复核 -2.1% ± 1.5%
  - 第 9 轮 HAVEN：换上 阿尔比昂巴哈姆特、亚教偶像；undecided，复核 -0.1% ± 1.1%
  - 第 10 轮 FOREST：换上 巴别隆城、兽语侦探·诺榭；rejected，复核 -5.5% ± 1.7%
  - 第 10 轮 DRAGON：换上 烈焰火蜥蜴、神话记者、天噬三恶·莱特欧芙；undecided，复核 +1.2% ± 1.3%
- 进了复核的减半胜者（含第 10 弹）：12 个，接受 0 个；第 1 轮 FOREST undecided、第 2 轮 FOREST rejected、第 3 轮 PORTAL rejected、第 4 轮 RUNE rejected、第 6 轮 ABYSS rejected、第 7 轮 FOREST undecided、第 7 轮 SWORD undecided、第 8 轮 RUNE rejected、第 9 轮 SWORD rejected、第 9 轮 HAVEN undecided、第 10 轮 FOREST rejected、第 10 轮 DRAGON undecided
- 进了复核的减半胜者（不含）：35 个，接受 11 个；第 1 轮 RUNE rejected、第 1 轮 DRAGON accepted、第 1 轮 ABYSS undecided、第 1 轮 HAVEN accepted、第 2 轮 SWORD undecided、第 2 轮 DRAGON accepted、第 2 轮 ABYSS rejected、第 3 轮 FOREST accepted、第 3 轮 SWORD undecided、第 3 轮 DRAGON accepted、第 3 轮 ABYSS rejected、第 3 轮 HAVEN undecided、第 4 轮 FOREST undecided、第 4 轮 DRAGON rejected、第 4 轮 HAVEN accepted、第 4 轮 PORTAL undecided、第 5 轮 FOREST undecided、第 5 轮 RUNE undecided、第 5 轮 DRAGON undecided、第 5 轮 HAVEN accepted at the cap、第 6 轮 SWORD rejected、第 6 轮 RUNE accepted、第 6 轮 DRAGON rejected、第 6 轮 HAVEN undecided、第 7 轮 RUNE undecided、第 7 轮 DRAGON undecided、第 8 轮 FOREST undecided、第 8 轮 DRAGON undecided、第 8 轮 HAVEN undecided、第 9 轮 FOREST accepted at the cap、第 9 轮 PORTAL rejected、第 10 轮 SWORD accepted、第 10 轮 ABYSS accepted、第 10 轮 HAVEN undecided、第 10 轮 PORTAL undecided
