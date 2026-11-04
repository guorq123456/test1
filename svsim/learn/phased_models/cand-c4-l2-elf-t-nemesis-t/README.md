# 候选 C4「L2 1e-4」：elf-t-nemesis-t（没装）

组合 elf-t-nemesis-t（我方-对方），只用我方一侧的局面。底 = cand-c2-hand-elf-t-nemesis-t，即现装（C2；C3 第 3 门不过）：同数据、同切分、同特征集 `--features hand`，只把拟合的 L2 从 1e-3 改成 1e-4。单调约束、2500 次迭代、STOCK 置零、版本 2 线性、`--hold-out-every 11` 照旧。架构线 2026-10-08 17:36Z 布置。留出只作参考，门才算数。

- 数据（同底）：data/pairings-20261008 分支的 data/pairings-20261008/nemesis-t_elf-t.jsonl.gz（2000 局），解压后 sha256 `475d43f4a9b46241c59004f9a59c1cc86daea3ef113d1d94883f55d715b5e9e6`，即现装 `elf-t-nemesis-t-{ended,act}.json` 的 info 里记录的那份。
- 拟合：`python -m svsim.learn.phased --games nemesis-t_elf-t.jsonl --matchup elf-t-nemesis-t --hold-out-every 11 --features hand --l2 1e-4 --out <本目录>`（代码 3feae70）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 底的 95% 区间来自按局重抽 2000 次：

| 时刻 | 点数 | C4 | 底 | C4 − 底（95%） |
|---|---|---|---|---|
| ended | 1333 | 0.5550 | 0.5538 | +0.0012（-0.0018～+0.0042） |
| act | 6324 | 0.5501 | 0.5492 | +0.0009（-0.0027～+0.0045） |

文件 sha256：

    215a5892894ebde3135a95eaee6be3099548efe0ff04b783d742468b280dcef7  elf-t-nemesis-t-act.json
    aa41a6f87097a70deef8428e606ee703ae32c2b601eb99b7be37a0c1c98f63b7  elf-t-nemesis-t-ended.json
