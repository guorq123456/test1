# 阶段 1 锁定记录（1.9）

- **锁定时间**：2026-11-23 07:30Z（Salem 那边 02:30），主持方。
- **版本**：dc2cbeb9a42ee4872423395752371d1b1356b7f9（claude/ladder 分支上的这一提交；推标签被代理拒了，所以不打标签，以这里的哈希为准）。
- **凭什么**：Salem 11-22 12:58Z「y验收」阶段 1（PHASE1-REPORT.md，p1b 五项全过，LD-38）；锁前在 Salem 电脑上用这一版跑 base-2 检查十一项全过（11-23 07:08～07:17Z，C:\claude\ladder-runs\base2\dc2cbeb，LD-53）。
- **规矩**（任务说明红线）：通过验收并锁定的基础设施，不经 Salem 同意不改。下表的文件改任何一处（注释也算）都要先问 Salem，改了进 LEDGER、这里加一行新版本。

## 锁定的文件

哈希是文件内容（换行统一成 LF）的 sha256，`python analysis/ladder/tools/check_lock.py` 核对；tests/test_lock.py 每次跑测试都核。

| 文件 | 是什么 | sha256 |
|---|---|---|
| ladder/__init__.py | 包 | 761bed1334eee7aa95b45fed4df77dca0e66a6db12f45d49fbff1f22776bb5f1 |
| ladder/rules.py | 1.1 CR 结算 | c6cb401f2becd7cf4ef800a25c333c838901d874b3e9aa1386933197a3fbeafb |
| ladder/base.py | 1.2 不偷看的底座 | e1023a77503eceb8cfce2bee870194d50f31f0a30d59a24d200c1e230a4a1df6 |
| ladder/strategy.py | 1.2 默认打法、bot 包装 | 63fce890d5c7157613f56c4a598c8650228e37753c9896de77b85e38bfa5d125 |
| ladder/runner.py | 1.3 批量对战、判负、计时、工作进程 | 435d0312d4128331e38dbd3d3b1b55d40e6adc934c5f049da34d16727c101baf |
| ladder/replay.py | 1.3 重放 | 675c808ad7df4e15445242ae7248078e2b8cf4e61ead3818e8aa1082692e878e |
| ladder/deal.py | base-2 密钥发牌（LD-27、LD-29） | 475df573bdd4854a36d6c55ea39ec024f61df9ac682042d32f96f2df355a066c |
| ladder/watch.py | 绊线（LD-40～LD-52） | 15b42a00f33bc347e2dbf786d45f2e0aaf1b770e01e6bf747824d25002855e71 |
| ladder/guard.py | 对局里的审计钩子（LD-52） | a01c07ea904a420f122938f6fae7a8a993d63f1e63a586d45a16f0f1054bc548 |
| ladder/audit.py | 重放审计（LD-40） | b97e1392c5162bbf56e2bc1fd62d3e195145c5d6e1cc54bcd7e15d1dfaad6704 |
| ladder/pool.py | 1.4 池管理器 | 8dafca4e9e5bef6664b7e2894a52f35bfbaf46ec5391f5d997d2c3176a835df8 |
| ladder/evaluator.py | 1.5 冻结池评测器 | 164a1378bc2b91e1b80a99ed5cb9c3b7cb4207ba86d54b92cb93fc36479bec6f |
| ladder/leaderboard.py | 1.6 排行榜 | 439fcd4987db26a1575f74d31181a5bc9758f9bf474351f6b1097211dbaba92b |
| ladder/gate.py | 1.7 检验工具 | 2118aabb1769d88d8cd9072205d384e90498a26c61c3a229ed5d340e98cc7584 |

## 不锁的（A49）

- 阶段 2 还在做的：ladder/interface.py（2.1）、submit.py 和 codecheck.py（2.3 收提交、读代码）、arena.py（2.4）、puzzles.py、report.py、anchors.py。阶段 2 验收时再锁。
- tools/、tests/、文档、public/（给选手的说明跟着阶段 2 走）。
- 一处牵连：绊线（watch.py，锁定）预载 svsim 模块时跳过 codecheck.DENIED_PREFIXES 里的；改这个名单等于改绊线跟哪些模块，算改锁定的东西，要先问。

## 版本

| 日期 | 版本 | 为什么 |
|---|---|---|
| 11-23 | dc2cbeb | 1.9 锁定 |
| 11-23 | （本次提交，gate.py 一处） | S16：Salem 14:30Z 决定卡同意，把关里新旧版每步算力比的无效线 1.08 → 1.15（和收提交的 S15 一致）；只改 COMPUTE_RATIO 一行和文档串，别的锁定文件不动 |
