# 候选 C3 修订版「HP × 回合段」（hpphase）：原版跳费龙镜像 ramp-ramp（没装）

组合 ramp-ramp（原版跳费龙 `ramp` 镜像）。`--features hpphase`：在装机向量之上只加 hpphase（原版组合没装 C2）。hpphase 4 维（双方领袖 HP × 被评分方第 1～4 / 5～7 回合）的定义见 learn.features 和 analysis/c3-threat/README.md 第六节。版本 2 线性，2500 次迭代，STOCK 置零，`--hold-out-every 11`。门由分析线排（架构线：留出只作参考，门才算数）。

- 数据：同 ../cand-bprime-ramp-ramp（拟现装原版模型的那 2000 局，sha256 `87c8a60d0887a0f5c5fdd1ddd0723e262023433f7253de7b989b6ee00b3045b8`）。
- 拟合：`python -m svsim.learn.phased --games games.jsonl --matchup ramp-ramp --hold-out-every 11 --features hpphase --out <本目录>`（代码 877dda1）。
- 对照：cand-bprime-ramp-ramp（同数据、同留出，不加特征）。

留出局（182 局，行号 % 11 == 0）上的 log loss，候选 − 对照的 95% 区间来自按局重抽 2000 次。现装模型是全量拟合的，见过留出局，只作参考：

| 时刻 | 点数 | C3 | B′ | C3 − B′（95%） | 现装* |
|---|---|---|---|---|---|
| ended | 3175 | 0.6004 | 0.6009 | -0.0006（-0.0013～+0.0003） | 0.5978 |
| act | 10615 | 0.6001 | 0.5992 | +0.0009（+0.0004～+0.0014） | 0.5965 |

读法：ended 小幅改善但区间跨 0；act 变差且区间不跨 0。对照比赛版跳费龙镜像（400 局留出，C3 − C2：ended -0.0018（-0.0040～+0.0003）），方向相同、幅度约三分之一。v2s 只用 ended 模型。

文件 sha256：

    9e75307f27ada15f26f817db48b0e1a90cef090852798a45dfc1b0ccfe76b7fa  ramp-ramp-act.json
    090c5198fd712af0387a0a4b41d0caa2614ccdc11e7d022da17ebccde73691a7  ramp-ramp-ended.json
