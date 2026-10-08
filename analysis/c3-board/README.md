# C3「对手场面威胁」特征集 `board`：管线（2026-10-08，维度待分析线给）

## 现状

管线已经接好，`board` 本身还没有定义。在 `svsim/learn/features.py` 里加上它，只需要两处：
- `EXTRAS["board"] = [...]`：最多 6 个名字；
- `EXTRA_FNS["board"] = fn`：`fn(state, player)` 返回同样长度的数值，只用我方 / 对方场面和双方 HP 这类量，不含卡组 id。

其余部分都不用改：
- `learn.phased --features board`，或 `hand,board`（按给出的顺序排在版本特征之后）；
- 模型的 `extras` 会随模型记录，读取时按名字解析；
- 留出用 `--hold-out-every 11`，同 C2。

单测 `test_a_new_named_feature_set_needs_only_its_function_and_names` 用一个临时注册的特征集走完了全程：拟合行、存取、读输入。没定义时，`board` 会报 `unknown feature set`。

## 定义到了以后的拟合（用现有 netdata 重新编码，不采新数据）

- **跳费龙镜像（已装 C2，所以是 hand 之上加 board）：**
  ```
  python -m svsim.learn.phased --games <selfplay-s200/ramp-t_ramp-t-s200.jsonl> --matchup ramp-t-ramp-t \
      --features hand,board --hold-out-every 11 --out svsim/learn/phased_models/cand-c3-board-ramp-t-ramp-t
  ```
  对照：cand-c2-hand-ramp（同数据、同留出、只有 hand）。
- **跳费龙对旗皇（装机向量之上加 board）：**
  ```
  python -m svsim.learn.phased --games <pairings-20261008/pirate-t_ramp-t.jsonl> --matchup ramp-t-pirate-t \
      --features board --hold-out-every 11 --out svsim/learn/phased_models/cand-c3-board-ramp-t-pirate-t
  ```
  对照：cand-bprime-ramp-t-pirate-t（同数据、同留出、不加特征）。
- **其余组合：**
  - 连击妖镜像、连击妖对机锋：已装 C2，用 `hand,board`；
  - 其他组合用 `board`，数据同 C2 推广时各组合用的那份（见各 cand-c2-hand-<组合>/README.md）。
