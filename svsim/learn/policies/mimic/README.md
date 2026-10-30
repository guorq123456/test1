# learn.mimic 的两个头（B，v0）

`+mimic=W`：搜索根节点的先验 = W × `player.npz` + (1 − W) × `selfplay.npz`，只在跳费龙镜像（Game8 版）里生效。编码没有卡号、没有卡组 id（`svsim/learn/mimic.py`）。

- `player.npz`（v0）：Salem 的 27 局跳费龙镜像（测试会话 d06b5b7 的 `analysis/mirror-regression/salem_games.json`，0 号位是他）里他那一方的全部 667 个决策，**未过滤失误**——这 27 局没有标过失误。测试会话会出每个决策的遗憾和标记（`salem_mistakes.jsonl`），到了以后用 `--decisions … --drop-flags F1 F2`（v1）或再加 `--soft 0.10`（v2）重拟，几版并排比。
- `selfplay.npz`：v2 自对弈 600 局（第三轮分叉的对照局，纯 v2 对 v2）的搜索访问分布，25974 个决策。

按局留出（三折，每折 9 局）时，"首选 = Salem 走的那步"：自对弈头 40.0%，Salem 头 45.3%，混合 0.3 / 0.7 是 43.9% / 45.6%。

重拟：

    python -m svsim.learn.mimic player --games salem_games.json --player 0 --out svsim/learn/policies/mimic
    python -m svsim.learn.mimic selfplay --games <v2 自对弈 JSON lines> --limit 600 --out svsim/learn/policies/mimic
