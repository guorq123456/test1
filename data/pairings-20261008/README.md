# 本机 v2 自对弈原始记录（2026-10-08，Salem 的电脑）

条件：对手卡表已知（牌序、手牌未知）。

`svsim.learn.netdata` 的输出，一行一局（含 names、search、plans、turn_starts 等），gzip 压缩。用 `python -m svsim.learn.phased --games <解压后的 .jsonl>` 可以直接再拟合。每个文件都远小于 100 MB，没有分块。

## 每份数据

所有文件：`--games 2000 --agent v2 --explore 0.03`，v2 = `mcts:100+plan+learned+phased`（用当时 `svsim/learn/phased_models/` 顶层装着的模型；ramp-t 镜像没有自己的模型时走别名）。局数都是 2000。

| 文件 | 组合（--deck / --opponent） | 种子 | 构建提交（当时检出） | 拟合出的模型 |
|---|---|---|---|---|
| nemesis-t_nemesis-t.jsonl.gz | nemesis-t / nemesis-t | 20261111 | 034260e | local-nemesis-t-nemesis-t（判 H0，没装） |
| pirate-t_pirate-t.jsonl.gz | pirate-t / pirate-t | 20261112 | 034260e | pirate-t-pirate-t（过门，已装） |
| ramp-t_ramp-t.jsonl.gz | ramp-t / ramp-t | 20261113 | c47449d（含 6c1a03c） | local-ramp-t-ramp-t（H0，没装） |
| pirate-t_elf-t.jsonl.gz | pirate-t / elf-t | 20261114 | 5fd130e | pirate-t-elf-t（过门，已装）；elf-t-pirate-t（H0） |
| pirate-t_nemesis-t.jsonl.gz | pirate-t / nemesis-t | 20261115 | a6aaf2b | 两边都没装（H0 / 合并 900 对 51.5%） |
| pirate-t_ramp-t.jsonl.gz | pirate-t / ramp-t | 20261116 | dacb126（pirate-t 镜像和 pirate-t-elf-t 已装） | ramp-t-pirate-t（过门，已装）；pirate-t-ramp-t（没装） |
| pirate-t_pirate-t-r2.jsonl.gz | pirate-t / pirate-t，第二圈 | 20261122 | 85febf5（已装第一圈 pirate-t-pirate-t） | local-pirate-t-pirate-t-r2（H0，没装） |

构建提交都在分支 `local/pairings-20261008` 上（034260e、6c1a03c 来自构建分支 ccr-165ad1e7-t2zmqu）。

## 拟合时的训练 / 留出划分

没有留出。`python -m svsim.learn.phased --games <文件> --matchup <deck>-<opponent> --workers 12/16`，默认参数（`--version 2`，`--q-weight 0`，`--moments ended act`）：

- 用文件里**全部 2000 局**的局面；交叉组合按 `--matchup` 只取那一边玩家的局面；
- 去掉平局（标签 0.5）；回合结束（ended）和回合中（act）各拟一份；
- `svsim.learn.fit.fit` 2500 次迭代，无验证集。日志里的 `value_accuracy` 是训练集上的数，不是留出精度。

要做留出评估，建议按局（行）划分，例如按种子或行号奇偶，不要按局面划分（同一局的局面高度相关）。
