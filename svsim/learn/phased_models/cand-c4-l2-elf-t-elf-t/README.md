# 候选 C4「L2 1e-4」：elf-t-elf-t（没装）

组合 elf-t-elf-t（我方-对方），只用我方一侧的局面。底 = cand-c3-hpphase-elf-t-elf-t，即C3（门已过，装机等 Salem）：同数据、同切分、同特征集 `--features hand,hpphase`，只把拟合的 L2 从 1e-3 改成 1e-4。单调约束、2500 次迭代、STOCK 置零、版本 2 线性、`--hold-out-every 11` 照旧。架构线 2026-10-08 17:36Z 布置。留出只作参考，门才算数。

- 数据（同底）：elf-t_elf-t.jsonl，解压后 sha256 `d1f461ffe310d44c0dc0183cf2202e088f8c722ce2a9cdccde54670c06afe4b8`；同 cand-c2-hand-elf-t-elf-t 的那份。
- 拟合：`python -m svsim.learn.phased --games elf-t_elf-t.jsonl --matchup elf-t-elf-t --hold-out-every 11 --features hand,hpphase --l2 1e-4 --out <本目录>`（代码 3feae70）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 底的 95% 区间来自按局重抽 2000 次：

| 时刻 | 点数 | C4 | 底 | C4 − 底（95%） |
|---|---|---|---|---|
| ended | 2734 | 0.5896 | 0.5894 | +0.0002（-0.0015～+0.0019） |
| act | 13010 | 0.5824 | 0.5825 | -0.0001（-0.0019～+0.0017） |

文件 sha256：

    3d671b5e5131343893490bee03bf3b5b5ea5e6ab8f02d76e0afeed7f9e536a13  elf-t-elf-t-act.json
    7845414f8c8aea27cdfa8c164e03511448113e94836152eec7892ba586362b58  elf-t-elf-t-ended.json
