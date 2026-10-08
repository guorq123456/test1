# 原始版的模型（f631e14，2026-10-08 各项改进之前的 bot）

`backup/bot-original-20261008` → f631e14 时 `svsim/learn/phased_models/` 顶层只有这两个文件（Game8 跳费龙镜像的 ramp-ramp 回合结束 / 回合中模型），原样复制。和现在顶层的同名文件逐字节相同。

原始版 = `mcts:100+plan+learned+phased=orig-f631e14+noalias+screen=200+mull=default`（陪练台的「原始版」档，`ui.session.LEVELS["original"]`）：
- 只用这里的模型，其他组合按原来的回退链走；
- `+noalias`：f631e14 还没有镜像别名；
- `+screen=200`：当时的斩杀筛（200 次，不带近斩杀加深）；
- `+mull=default`：当时还没有连击妖的规则换牌。

核对：同种子 717171，用当前代码跑这个串，和 f631e14 检出里的 `mcts:100+plan+learned+phased` 逐步相同（ramp-t 镜像 71 步、elf-t 对 ramp-t 77 步、nemesis-t 对 elf-t 77 步）。同种子 515151，和 5175def（上一版陪练台的普通档）在 Game8 卡组上也逐步相同（跳费龙镜像 43 步、破魔虫对跳费龙 80 步）。所以它可以在 1300 刻度上测出一个 CR。

sha256：
```
f6638159fa561712c03f29f3e0c51a9519e3a543227112887731fcca831cd0c2  ramp-ramp-act.json
97b0a8f2e747fe2509906c70595ecd702d9805ba2111e08eb52d3c8314bb100e  ramp-ramp-ended.json
```
