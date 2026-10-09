# cand-hv-ramp-ramp 的 B′：同数据、同切分、同 L2，不加特征（没装，门前检查用）

命令同 ../cand-hv-ramp-ramp 去掉 `--features hand_value --hand-value`：`python -m svsim.learn.phased --games selfplay.jsonl --matchup ramp-ramp --hold-out-every 11 --out <本目录>`。版本 2 线性，2500 次迭代，L2 1e-3，STOCK 置零。不带 extras，截距照常（截距修复不影响它）。用途：分析线门前检查（候选翻号而 B′ 不翻才做并排重放），只报数，不挡门。条件：对手卡表已知（牌序、手牌未知）。

- 数据：local/pairings-20261008 分支 b355c44 的 analysis/card-value/student/（种子 65800000；分析线 5eca2d4 的 student_data.py）。原版跳费龙镜像 level-strong 自对弈 1000 局，第 n 行即 g = n。sha256：
  - selfplay.jsonl：`bf16460354c84770a70eb4c1c8218e450ab04c34f5ff15f5eef8be954958f3a8`
  - positions.jsonl：`5c11e1b23ef6d91ce39f05054b365648ffb6bdf2b55b801f48be90bede7ee174`
  - teacher.jsonl：`917ffeb3d3cb228f0ee2ef5cd5278fce092d9415b7b39240b05ad133825af73e`
  - labels.jsonl：`19978274090f0cbdaf159f706e92decf271957f01ac4c6603360c4a86b877d3a`

文件 sha256：

    53f0e6c0cceccdee5e37857dc0ba3122bfb69052b38e4070daef3fe9eed2dccb  ramp-ramp-act.json
    b3c6d0795575241ae04da93bfc1ce2ca16705df6253e0ff39eb388c1c3cab86c  ramp-ramp-ended.json
