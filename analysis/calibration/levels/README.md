# 各档 CR：实际用的 agent 串（本机，2026-10-08）

B = C = `ruler20261008`，`--deck ramp-t`，`--fixed --max 200`（50 对/格），代码 local/pairings-20261008 的 2653d69（含 08a02d0）。

| 档 | 文件前缀 | 实际 `--a` 串 | 种子库（对 ramp-t / elf-t / nemesis-t / pirate-t） | 状态 |
|---|---|---|---|---|
| 原始版 | `orig_` | `mcts:100+plan+learned+phased=orig-f631e14+noalias+screen=200+mull=default` | 49800000 / 49900000 / 50000000 / 50100000 | 有效 |
| 普通 | `normal_` | `v2r`（arena.py 展开为 `mcts:115+plan+learned+phased+reuse`，和 LEVELS["normal"] 相同） | 50200000 / 50300000 / 50400000 / 50500000 | 有效 |
| 快速（写错的串） | `fast-phased_` | `greedy+plan+learned+phased` | 50600000 / 50700000 / 50800000 / 50900000 | 仅供参考：陪练台的快速档是 `greedy+plan+learned` |

快速档按 LEVELS 的 `greedy+plan+learned` 重跑，写进 `fast_…`，种子库 54000000 / 54100000 / 54200000 / 54300000；50600000～50900000 不再用。以后各档的串以 LEVELS 为准。
