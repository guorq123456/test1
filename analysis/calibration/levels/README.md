# 各档 CR：实际用的 agent 串（本机，2026-10-08）

B = C = `ruler20261008`，`--deck ramp-t`，`--fixed --max 200`（50 对/格），代码 local/pairings-20261008 的 2653d69（含 08a02d0）。

| 档 | 文件前缀 | 实际 `--a` 串 | 种子库（对 ramp-t / elf-t / nemesis-t / pirate-t） |
|---|---|---|---|
| 原始版 | `orig_` | `mcts:100+plan+learned+phased=orig-f631e14+noalias+screen=200+mull=default` | 49800000 / 49900000 / 50000000 / 50100000 |
| 普通 | `normal_` | `v2r` | 50200000 / 50300000 / 50400000 / 50500000 |
| 快速 | `fast_` | `greedy+plan+learned+phased`（按转来的命令；注意 08a02d0 的 `ui.session.LEVELS["fast"]` 是 `greedy+plan+learned`，不带 `phased`） | 50600000 / 50700000 / 50800000 / 50900000 |
