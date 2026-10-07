# Salem 的陪练台对局（从页面的共享存档拉出，2026-10-07 15:45Z）

每个文件是陪练台存档里的一条记录（`record` 下是回放记录，`bot` 是对局时的 bot 档位 / 版本 / spec / 构建号，座位 0 是 Salem）。
`analysis/mirror-regression/build_positions.py` 直接读得了这些文件。

- `2026-10-07-vs-v2s/`：今天对新 strong 档（v2s，构建 5175def）的 7 局。Salem 的话：bot 仍然没有全局的资源规划，会打成长盘的对局里过早交完进化点。
- `2026-10-06-evening-vs-old-bot/`：10-06 晚上对旧网页 bot（`mcts:200+plan+learned`）的 10 局，2 号的 `positions.json` 里没有这批（它只有 10-06 下午那 10 局）。

| 批次 | 对局 | 时间（UTC） | bot spec | 版本 | 先手 | 胜者 | 总回合 | 步数 |
|---|---|---|---|---|---|---|---|---|
| old | 1791315717152 | 2026-10-06 19:41Z | `mcts:200+plan+learned` | 旧 | bot | Salem | 23 | 72 |
| old | 1791316090276 | 2026-10-06 19:48Z | `mcts:200+plan+learned` | 旧 | bot | bot | 15 | 41 |
| old | 1791316350693 | 2026-10-06 19:52Z | `mcts:200+plan+learned` | 旧 | Salem | 未记录 | 11 | 28 |
| old | 1791316411815 | 2026-10-06 19:53Z | `mcts:200+plan+learned` | 旧 | bot | Salem | 16 | 48 |
| old | 1791316540438 | 2026-10-06 19:55Z | `mcts:200+plan+learned` | 旧 | bot | Salem | 16 | 51 |
| old | 1791316841837 | 2026-10-06 20:00Z | `mcts:200+plan+learned` | 旧 | Salem | Salem | 15 | 48 |
| old | 1791316974098 | 2026-10-06 20:02Z | `mcts:200+plan+learned` | 旧 | bot | Salem | 25 | 82 |
| old | 1791317238047 | 2026-10-06 20:07Z | `mcts:200+plan+learned` | 旧 | bot | bot | 19 | 62 |
| old | 1791317476826 | 2026-10-06 20:11Z | `mcts:200+plan+learned` | 旧 | bot | Salem | 20 | 69 |
| old | 1791317687161 | 2026-10-06 20:14Z | `mcts:200+plan+learned` | 旧 | Salem | Salem | 16 | 50 |
| v2s | 1791384258804 | 2026-10-07 14:44Z | `mcts:200+plan+learned+phased` | v2s | Salem | Salem | 24 | 79 |
| v2s | 1791385092476 | 2026-10-07 14:58Z | `mcts:200+plan+learned+phased` | v2s | bot | 未记录 | 16 | 53 |
| v2s | 1791385225044 | 2026-10-07 15:00Z | `mcts:200+plan+learned+phased` | v2s | Salem | Salem | 26 | 84 |
| v2s | 1791385824342 | 2026-10-07 15:10Z | `mcts:200+plan+learned+phased` | v2s | Salem | Salem | 24 | 84 |
| v2s | 1791387075633 | 2026-10-07 15:31Z | `mcts:200+plan+learned+phased` | v2s | Salem | Salem | 15 | 47 |
| v2s | 1791387160337 | 2026-10-07 15:32Z | `mcts:200+plan+learned+phased` | v2s | bot | Salem | 32 | 113 |
| v2s | 1791387437959 | 2026-10-07 15:37Z | `mcts:200+plan+learned+phased` | v2s | Salem | Salem | 19 | 70 |

胜者"未记录"的对局是认输或中途结束，存档里 `winner` 为空。

## 今天 7 局的进化点节奏（每人 2 个进化点 + 2 个超进化点，列的是用点的"自己的第几回合"）

| 对局 | 先手 | Salem | bot |
|---|---|---|---|
| 1791384258804 | Salem | 5 7超 9超 11 | 4 5 6超 7超 |
| 1791385092476 | bot | 4 6超 7超 | 5 7超 8超 |
| 1791385225044 | Salem | 5 6 7超 9超 | 4 5 6超 7超 |
| 1791385824342 | Salem | 6 7超 10超 | 4 5 7超 8超 |
| 1791387075633 | Salem | 5 6 7超 | 4 |
| 1791387160337 | bot | 4 6超 7超 8 | 5 7超 8超 11 |
| 1791387437959 | Salem | 5 7超 9 10超 | 4 5 6超 7超 |

读法：bot 几乎每次都在点刚可用的那个回合就用掉（后手 4、5、6、7），用完 4 个点平均在自己的第 8.0 回合，第 1 到第 4 个点相隔 3.8 回合；Salem 用完 4 个点平均在第 9.5 回合，相隔 4.8 回合。10-06 对旧 bot 的 20 局里同一组数字是 bot 8.2 / 3.3，Salem 9.2 / 4.3，所以 v2s 在这件事上没有变化。
2 号此前"进化时机配对比较几乎为 0"看的是单回合配对，看不见整局的节奏；要看整局。
