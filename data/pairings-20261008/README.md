# 云端的分组合自对弈记录（2026-10-07 / 08）

条件：对手卡表已知（牌序、手牌未知）。每个文件是 gzip 压缩的 JSON lines，一行一局，就是 `svsim.learn.netdata` 写出、`python -m svsim.learn.phased --games` 直接吃的那种记录。没有切块（每个都在 3 MB 以下），校验和在 `SHA256SUMS`（`sha256sum -c SHA256SUMS`）。解压：`gunzip -k <文件>.jsonl.gz`。

每局记录里有：`decks`、`seed`、`first`、`actions`、`winner`；`names`（按座位的卡组名）、`deck_keys`、`deck_hashes`（按卡号排序的卡表哈希）；`search`（每个决定的访问分布和搜索值，`learn.policy.decisions` 读它）；`turn_starts`（每回合开始时的手牌和牌组 uid，即搜索的 `_root_deck`）；`rng_seed`、`agent_seeds`；`explore`。

| 文件 | 两边卡组（按卡组名，座位轮换：第 g 局 A 方坐 g % 2 号位） | 局数 | 自对弈种子 | 生成时的代码 |
|---|---|---|---|---|
| `elf-t_elf-t.jsonl.gz` | elf-t / elf-t | 2000 | 20261101 | 0512567（代码同 af086ee + e59a9c0） |
| `elf-t_ramp-t.jsonl.gz` | elf-t / ramp-t | 2000 | 20261102 | 3effa47（代码同上，另装了 elf-t 镜像的模型，不影响这个组合） |
| `nemesis-t_ramp-t.jsonl.gz` | nemesis-t / ramp-t | 2000 | 20261103 | 2ff3aca |
| `nemesis-t_elf-t.jsonl.gz` | nemesis-t / elf-t | 2000 | 20261104 | 2e7aea8 |

- bot：两边都是 `v2` = `mcts:100+plan+learned+phased`，3% 随机走子（`netdata --explore 0.03`；第一回合不随机）。命令：`python -m svsim.learn.netdata --games 2000 --agent v2 --deck A --opponent B --explore 0.03 --seed S --workers 4 --out F`。
- 生成时这几个组合都还没有自己的模型：v2 在这些对局里走的是回退（elf-t、nemesis-t 手写评分；ramp-t 在非镜像里是 `learn/weights/dragon.json`），所以这批数据等于"回退评估器的 v2"的自对弈。
- 斩杀检查是当时的默认 `screen=200:1000:4`（af086ee 起）。起手：四份都用的是原来的默认换牌（D）；elf-t 改用规则换牌（R）是 7d219cc（02:46Z），晚于这四份数据。
- 卡表哈希（`deck_hashes`）：elf-t `1.1.dhqm…fea-`，ramp-t `1.4.cJl6…flvu`，nemesis-t `1.7.cQnG…ftEe`（完整串见每局记录）。

拟合（各组合的专用模型，`svsim/learn/phased_models/<卡组>-<对手>-{ended,act}.json`）：
- `python -m svsim.learn.phased --games <文件> --matchup <卡组>-<对手> --out <目录>`，版本 2 特征，回合结束和回合中模型在同一份数据上一起拟合；两边是不同命名卡组时，每个模型只用自己那一方的局面（`learn/phased.py` 的 `_rows`，`side` 过滤，e59a9c0）。
- 没有留出划分：`learn.fit.fit`（`svsim/learn/fit.py:22`，由 `svsim/learn/phased.py:162` 调用）用全部局面拟合，日志里的 loss / value_accuracy 是训练集上的数。模型好不好由等算力闸门判（SPRT 种子 27xxxxxx、定长 28xxxxxx，和自对弈种子 2026110x 不重叠），见 `docs/architecture.md` 的逐组合表。
