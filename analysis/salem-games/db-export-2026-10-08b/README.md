# 陪练台存档第二次导出（2026-10-08 07:05Z）

`db-export-2026-10-08/`（37 局，9bb5293）之后存档里新增的 10 局。每个 JSON 是存档里的原样记录，格式和上次一样：`finished`、`moves`、`updated`、`winner`、`record`。座位 0 是 Salem。
导出时又检查了一遍上次那 37 局：存档里的内容和上次导出逐字节一致，没有被改动或删除。

条件：对手卡表已知（牌序、手牌未知）。

**卡组名**：存档里只有双方 40 张卡的 id 列表，没有卡组名。下表的卡组名是把列表和 `svsim.cards.decks.NAMED` 逐张比对得出的，10 局全部唯一匹配。机读版本在 `index.json`。
Salem 说这两套（nemesis-t = 宇宙鱼，pirate-t = 旗皇）他不熟（约 1700 CR），只能作弱参考。上次导出的 37 局里，Salem 用的是 ramp（27 局）和 rhino（10 局），bot 都是 ramp。

| 对局 | 开始（UTC） | Salem 卡组 | bot 卡组 | bot 档位 | 先手 | 胜者 | 打完 | 总回合 | 步数 |
|---|---|---|---|---|---|---|---|---|---|
| 1791438391276 | 05:46Z | nemesis-t | elf-t | strong | Salem | Salem | 是 | 19 | 84 |
| 1791438595615 | 05:49Z | nemesis-t | elf-t | strong | bot | Salem | 是 | 20 | 88 |
| 1791438924857 | 05:55Z | nemesis-t | elf-t | strong | Salem | Salem | 是 | 19 | 95 |
| 1791439562701 | 06:06Z | nemesis-t | elf-t | original | Salem | Salem | 是 | 15 | 72 |
| 1791440630873 | 06:23Z | nemesis-t | elf-t | strong | bot | bot | 是 | 17 | 79 |
| 1791440874805 | 06:27Z | nemesis-t | elf-t | strong | bot | Salem | 是 | 18 | 88 |
| 1791441594328 | 06:39Z | pirate-t | elf-t | strong | Salem | Salem | 是 | 19 | 85 |
| 1791441785786 | 06:43Z | pirate-t | elf-t | strong | bot | bot | 是 | 17 | 65 |
| 1791441981815 | 06:46Z | pirate-t | elf-t | strong | bot | Salem | 是 | 18 | 74 |
| 1791442148174 | 06:49Z | pirate-t | elf-t | strong | bot | Salem | 是 | 14 | 59 |

总回合是双方回合数之和（`EndTurn` 次数 + 最后一回合）。步数是存档的 `moves`。

汇总：

- **Salem 8 胜 2 负。** nemesis-t 5–1（其中 original 档 1 局），pirate-t 3–1。
- **对 strong 档 9 局，Salem 7–2。**
  - Salem 先手 3–0；
  - Salem 后手 4–2。

这些局对应哪个 bot 构建：

- **记录里没有构建号。** `record.ai` 只有 spec：strong 是 `mcts:200+plan+learned+phased`；original 是 `mcts:100+plan+learned+phased=orig-f631e14+noalias+screen=200+mull=default`。`record.version` 是记录格式的版本号，不是构建号。
- **只能按发布时间推断。**
  - Version 14 是 9edd59d（04:17Z）。
  - Version 15 的最后一个提交是 5558960（05:50Z）。从 Version 15 起，页面里才有 elf-t 对 nemesis-t 的 elf-t 一侧模型（7136f17）。
  - Version 16 是 03519f0（06:05Z），Version 17 是 d9a3cb2（06:19Z）。这三版都包含 7136f17。
- **前两局（05:46Z、05:49Z）一定是 Version 14。** 那时 Version 15 还没发布，所以 bot 用的是没有这组配对模型的回退评估。
- **其后的局取决于 Salem 有没有刷新页面，存档里看不出来。**
