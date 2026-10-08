# 候选：连击妖对跳费龙、连击妖一方的按组合 MLP（E2，2026-10-08，没装）

- 装机态全部模型的拷贝（截至 7136f17，22 个文件），只把 `elf-t-ramp-t-{ended,act}.json` 换成 E2。按名字挑文件的方式和装机态一样，所以 `+phased=cand-mlp-e2-20261008` 下任何组合都不会掉到回退。
- E2：`python -m svsim.learn.mlp --games elf-t_ramp-t.jsonl --matchup elf-t-ramp-t --epochs 300 --lr 3e-3`。
  - 版本 2 特征，一层 64 个 tanh 隐元，从线性解起步。
  - 数据是云端 elf-t_ramp-t 2000 局（data/pairings-20261008），只用连击妖一方的局面。
  - 留出行号 % 10 == 0 的局，早停看留出 loss。
- 同一划分的留出（log loss / 判对率）：
  - ENDED：E2 0.5737 / 68.9%，现装线性 0.5743 / 69.0%（现装线性的训练数据包含这些留出局）。
  - ACT：E2 0.5613 / 70.6%，现装线性 0.5686 / 69.8%。
- 开销（空机器，183 个局面）：
  - 200 次迭代：v2s 80.4 ms 对 85.4 ms（+6%），等算力 188 次。
  - 100 次迭代：+3%～+8%（有负载时测的）。
- 门：A = `mcts:188+plan+learned+phased=cand-mlp-e2-20261008`，B = `v2s`，C = `v2s` 打 ramp-t（`--versus v2s`），`--deck elf-t --opponent ramp-t`。
  - 100 级 SPRT（92 对 100，种子 45500000）：150 对 57.0% ± 5.2%，判 H1，只作信息。
