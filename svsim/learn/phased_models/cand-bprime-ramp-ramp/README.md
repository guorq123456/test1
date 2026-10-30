# 候选 B′：原版跳费龙镜像，同数据同留出、不加特征的干净基线（没装，只作对照）：ramp-ramp

组合 ramp-ramp（原版跳费龙 `ramp` 镜像），不加特征；版本 2 线性，2500 次迭代，STOCK（me_hand_*、me_pool_*）置零，`--hold-out-every 11`（行号 % 11 == 0 的 182 局留出、不参与拟合）。做法同 cand-bprime-*（比赛版各组合）。架构线 2026-10-08 布置：原版组合补拟 B′ 与 C3 hpphase。

- 数据：拟现装 `ramp-ramp-{ended,act}.json`（3e58415，当时叫 dragon-dragon）的那份 netdata：2000 局自对弈，双方 `mcts:100+plan+learned`，explore 0.03，Phase 1 生成（本会话 scratchpad 的 net/games.jsonl，未入库）。sha256 `87c8a60d0887a0f5c5fdd1ddd0723e262023433f7253de7b989b6ee00b3045b8`，7,753,646 字节，2000 行；记录不带 names，镜像两边的局面都用。
- 核对：当初 3e58415 的拟合输出（scratchpad 的 net/phased/）与现装两个文件 sha256 逐字节相同；用今天的代码全量重拟（不留出、不加特征），局面数（ended 35601、act 118719）、均值、系数与现装逐位相同（最大差 0.0），只有 info 元数据不同（deck 名 ramp 对 dragon，多记了 games 等字段）。
- 拟合：`python -m svsim.learn.phased --games games.jsonl --matchup ramp-ramp --hold-out-every 11 --out <本目录>`（代码 877dda1）。

留出表见 ../cand-c3-hpphase-ramp-ramp/README.md。

文件 sha256：

    3fd57970c7142656e3713c054a2666a219e9e6a904d705594baf549affc09628  ramp-ramp-act.json
    ec33013ff2059b7542917f16d659ef84bc47a4643bff3043025b0502263d03a9  ramp-ramp-ended.json
