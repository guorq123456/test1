# 候选：X1 留一法，去掉连击妖对跳费龙（2026-10-08，没装）

- 和 cand-mlp-x1-20261008 一样（装机态模型的拷贝，只换 `elf-t-ramp-t-{ended,act}.json`），但 X1 训练时拿掉了 elf-t_ramp-t 那一份数据：剩 10 份、20000 局，这个组合 X1 从没见过。
- 训练：`python -m svsim.learn.mlp --shared --act-stride 2 --games <10 个文件> --matchup elf-t-ramp-t --epochs 300 --lr 3e-3`，日志 train.log。
- 门（架构线程 05:45Z 的建议）：A = `mcts:188+plan+learned+phased=cand-mlp-x1-loo-elframp-20261008`，B = `v2s`（专用线性），C = `v2s` 打 ramp-t，`--deck elf-t --opponent ramp-t`，定长 300 对，种子 37000000 起。结果 analysis/universal-bot/gates/x1loo_elframp.jsonl。
