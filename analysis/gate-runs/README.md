# 评测台结果（test1 会话跑的）

代码：隔壁分支 `ccr-165ad1e7-t2zmqu` 的提交 3e58415（分阶段线性模型在 `svsim/learn/phased_models/`）。跳费龙内战。每行是一对：同一个种子打两局，A 先后手各一次，`points` 是 A 在两局的得分。

| 文件 | A | B | 种子库起点 | 停止方式 | 结果 |
|---|---|---|---|---|---|
| `sprt_reply_phased_vs_installed_seed1000000.jsonl` | `mcts-reply:100+plan+learned+phased+lazy+focus` | `mcts:100+plan+learned` | 1000000 | SPRT（H0 50% / H1 55%，α=β=0.05） | 250 局判 H1：58.0% ± 5.5% |
| `fixed600_reply_phased_vs_installed_seed2000000.jsonl` | 同上 | 同上 | 2000000 | 固定 600 局 | 57.7% ± 3.3%（54.3%～61.0%），CR 约 +61；先手 57.0%，后手 58.3% |
| `fixed200_reply_phased_vs_greedy_seed4000000.jsonl` | 同上 | `greedy+plan+learned` | 4000000 | 固定 200 局 | 92.5% ± 3.5%；先手 91.0%，后手 94.0% |

`fixed_run.py` 用评测台自己的 `play_pair`，只是不按 SPRT 提前停，所以给的区间没有提前停带来的偏差。

## 第一张联赛表（`python -m svsim.tools.league`，现装记作 0，斜率 200 CR/logit，1000 次重抽）

| 版本 | 局数 | 强度 logit | 95% 区间 | 相对 CR | CR 区间 |
|---|---|---|---|---|---|
| 候选 `mcts-reply+phased` | 1050 | +0.313 | +0.198～+0.425 | +63 | +40～+85 |
| 现装 `mcts:100+plan+learned` | 850 | 0 | — | 0 | — |
| `greedy+plan+learned` | 200 | −2.199 | −2.789～−1.752 | −440 | −558～−350 |

只有两条边，三个版本连成一条链，没有环，所以表里只是把两两的胜率换成同一把尺子，还没法检查一致性。加一条"现装对 greedy"就有环了。greedy 的 −440 远超天梯的 175 分匹配窗口，只是斜率的读数，天梯本身分辨不出这么大的差距。绝对 CR 等 Salem 给锚点。
