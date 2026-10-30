# 候选 A100：100 级自对弈数据重拟合，对照组（2026-10-08，没装）

`python -m svsim.learn.phased --games ramp-t_ramp-t-s100.jsonl --matchup ramp-t-ramp-t --hold-out-every 11`，默认参数（`--q-weight 0`）。

- 数据：local/data-pairings-20261008 @ d35a1b7 的 data/selfplay-s100/，跳费龙（比赛版）镜像 4400 局，双方 v2（`mcts:100+plan+learned+phased`），explore 0.03，在 02e58f0 上生成。局数和划分都和 A200 相同，用来区分"数据量"和"数据质量"（analysis/refit-200/README.md）。
- 划分：行号 % 11 == 0 的 400 局留出，用剩下的 4000 局拟合。版本 2 特征，线性；STOCK 照现装模型一样置零。
- 留出（100 级留出集，只按终局胜负）：ENDED 0.5966，ACT 0.6012；B（ramp-ramp）在同一留出集上是 0.6099 / 0.6184。按分析线的读法，只和同一数据集上的 B 比。
- 门：A = `mcts:200+plan+learned+phased=cand-refit100-ramp`，B = `level-strong`，ramp-t 镜像，定长 300 对，不用 `--versus`。条件：对手卡表已知（牌序、手牌未知）。
