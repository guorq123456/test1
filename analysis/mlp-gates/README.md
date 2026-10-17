# MLP 评估器各道门的逐对结果（100 次迭代那一级，2026-10-08）

`tools/gate.py` 写出的结果文件，每行一对：`k`、`seed`、`points`（A 的得分）、`b_points`（`--versus` 时 B 的得分）、`same`。拿同样的命令和 `--out` 指到这个文件，gate 就会接着读，重报这段的数。条件：对手卡表已知（牌序、手牌未知）。

| 文件 | 门 | 种子 | 结果 |
|---|---|---|---|
| `e2_100_sprt.jsonl` | E2：A = `mcts:92+plan+learned+phased=cand-mlp-e2-20261008`，B = v2，C = v2 打 ramp-t，`--deck elf-t --opponent ramp-t --versus v2` | 45500000 | 第 150 对判 H1，57.0% ± 5.2% |
| `e2_100_fixed300.jsonl` | 同上，`--fixed --max 1200` | 46000000 | 300 对 45.5% ± 3.7%（41.8%～49.2%）。前 16 对是停之前跑的，后面从断点续跑 |
| `x1_100_sprt.jsonl` | X1：A = `mcts:92+plan+learned+phased=cand-mlp-x1-20261008`，其余同 E2 | 47000000 | 第 75 对判 H0，41.3% ± 8.0% |
| `m3_ramp_mirror_100_sprt.jsonl` | M3：A = `mcts:98+plan+learned+phased=<M3>`（只有 ramp-t-ramp-t 两个文件），B = v2（别名），ramp-t 镜像 | 46500000 | 第 100 对判 H0，47.5% ± 5.6% |

- 跑门的时候，E2 / X1 的 A 用的是草稿目录里的全套模型，模型内容和这两个候选目录里的一样。两个候选目录各多一对 elf-t-nemesis-t，是之后装机加进去的，和这一格无关。
- 200 级的定长 300 对在本机线跑：E2 49.0%，X1 49.5%，都不装。
- 读法：同是 100 级，E2 的 SPRT 停在 57.0，定长却是 45.5，所以 57.0 是早停的乐观偏差。
