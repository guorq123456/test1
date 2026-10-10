# 候选 hand_value：原版跳费龙镜像 ramp-ramp（没装；系数 ≤ 0，按规矩不开门）

手牌价值线（Salem 2026-10-09 02:01Z，架构线 07:10Z）。基础特征（版本 2，同现装 ramp-ramp，无其他 extras）加 `hand_value`：学生 H(手牌 | 局面) 的值（learn.handvalue；本目录的 ramp-ramp-hv.npz）。版本 2 线性，2500 次迭代，L2 1e-3，STOCK 置零，`--hold-out-every 11`。代码 4746b43（截距修复之后）。对照：../cand-hv-ramp-ramp-bprime。条件：对手卡表已知（牌序、手牌未知）。

- 数据：local/pairings-20261008 分支 b355c44 的 analysis/card-value/student/（种子 65800000；分析线 5eca2d4 的 student_data.py）。原版跳费龙镜像 level-strong 自对弈 1000 局，第 n 行即 g = n。sha256：
  - selfplay.jsonl：`bf16460354c84770a70eb4c1c8218e450ab04c34f5ff15f5eef8be954958f3a8`
  - positions.jsonl：`5c11e1b23ef6d91ce39f05054b365648ffb6bdf2b55b801f48be90bede7ee174`
  - teacher.jsonl：`917ffeb3d3cb228f0ee2ef5cd5278fce092d9415b7b39240b05ad133825af73e`
  - labels.jsonl：`19978274090f0cbdaf159f706e92decf271957f01ac4c6603360c4a86b877d3a`
- 学生：`python -m svsim.learn.handvalue --selfplay selfplay.jsonl --positions positions.jsonl --teacher teacher.jsonl --out ramp-ramp-hv.npz`（默认：嵌入 8、宽 16、隐层 16、3000 次、lr 0.01、L2 1e-4、批 256、种子 0）。
- 拟合：`python -m svsim.learn.phased --games selfplay.jsonl --matchup ramp-ramp --hold-out-every 11 --features hand_value --hand-value ramp-ramp-hv.npz --out <本目录>`。

## 学生

- 标签：train 10010、val 1025，与分析线 labels.jsonl 逐条相同（T 与 1/var 权重）。去掉：回合开头不在手里 455 + 44，限制没改变打法 456 + 34（train + val）。
- 1/var 权重的有效样本量 1686（占 16.8%），低于 30%，按规矩退回等权。
- 损失（加权 MSE）：训练 0.0223、留出 0.0202。Spearman(ΔH, T)：训练 0.294、留出 0.289（贴合度门槛 0.72，只报）。
- 容量扫描（在训练标签内部再按 g % 7 切一份做检查，不碰留出）：更大的网络把内部拟合提到 0.47，检查集仍在 0.33～0.36。上限来自输入（学生只看到场面的张数，看不到场上是什么），不是容量；所以用的是预定的默认尺寸。

## 回合末模型里的 hand_value

- 标准化系数 -0.0520（回合末）、-0.0378（回合中）；每单位 -0.2592。特征在训练局面上均值 -0.258、标准差 0.201。
- 按局重抽 30 次重拟回合末模型：标准化系数 -0.0601 ± 0.0490（标准误），为正的比例 17%。
- **系数 ≤ 0：按规矩不开门。** 共线性检查：和 me_hand（手牌张数）相关 -0.666；hand_value 对其余特征回归 R² 0.577（VIF 2.37，轻度）。去掉 me_hand 后系数 -0.2718，更负：不是共线把正效应盖住了，H 本身近似「负的手牌张数」。
- 读法（推断）：T = keep:c，是「这回合留着 c」减「bot 的主线」。主线通常是对的，所以 T 多为负，学生学成「手里每张牌都让分数变低」。回合末评估要的是「手里有这张牌值多少」，和这个标签的含义不一样。

## 留出（91 局，行号 % 11 == 0；候选 − B′，按局重抽 2000 次，只作参考）

| 时刻 | 点数 | 候选 | B′ | 候选 − B′（95%） |
|---|---|---|---|---|
| ended | 1583 | 0.5925 | 0.5927 | -0.0003（-0.0014～+0.0009） |
| act | 5558 | 0.5937 | 0.5937 | +0.0000（-0.0008～+0.0010） |

和 B′ 相比翻号、且较大一边 ≥ 0.015 的特征：回合末 0 个，回合中 0 个（只报，不挡门）。

文件 sha256：

    8822b3d32e9a9f9ea8d834af0e05cf30671036333a54cf330110b862daa84a28  ramp-ramp-act.json
    1edff8640d595f04e4357969f10ce940c8b8549f6fce868ec9cc88c1928884e6  ramp-ramp-ended.json
    125ce1653f136d538e0cee86fc945d66e320b4dc78fbe258a726f1148d487241  ramp-ramp-hv.npz
