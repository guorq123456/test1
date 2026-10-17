# 候选 cand-tl-ramp-ramp：回合级第 1 步，对比训练的回合末模型（原版跳费龙镜像；没装）

条件：对手卡表已知（牌序、手牌未知）。架构线程 2026-10-09 22:22Z 布置；预注册见分析线 8740d0f（analysis/turn-level/README.md「第 1 步」），J22 说的就是这个线性版。

- **模型**：`ramp-ramp-ended.json`，回合末（ENDED），版本 2 线性特征，特征和现装的原版跳费龙镜像一样，不加特征。`ramp-ramp-act.json` 是现装的回合中模型原样拷过来的（ACT 不动）。
- **训练器**：`learn.contrast.fit_contrast`。损失 = Σw(σ(E(a)) − σ(E(b)) − L)² / Σw + μ × 校准对数损失 + L2（截距不罚）。
- **设置**：在任何第 1 步数据和留出读数之前就定了（ddfef2f 的试验，analysis/contrast-trial）。
  - μ = 0.03，L2 = 1e-4，起点为零，3000 轮，学习率 0.05；
  - 版本 2 的符号约束；STOCK（me_hand_*、me_pool_*）置零；截距自由（训练出来 −0.3516）。
- **标签**：分析线 c661c8a 的 `analysis/turn-level/step1_labels/labels.jsonl`。
  - sha256 a67903d0241b691520be7d5e5884b02ab456bb121af342fd088f02fa106e81d3。
  - 校准 b = 0.888，τ² = 0.01784，end 的权重乘 0.375。
  - 我用分析线自己的 step1.py 在这边重算了一遍，逐行一致，浮点差在 1e-11 以内。
  - 只用 split == "train"。
- **例子**：每个标签的权重 W 平均分给它保留下来的确定化（每个 W ÷ 个数），每个确定化给一对回合末（候选的 / bot 的，或者限制线 / 老师主线）。
  - 回合末用 teacher_ends.turn_end(end_of_turn=True) 重建，再按行动方读成版本 2 的特征。
  - 两条线动作一样的确定化不要。
  - 任一端在回合中途就终局（多半是斩杀）的确定化排除并计数，W 分给剩下的。全被排除的标签就不进训练。
  - 训练例子：第 1 步 5,453 个标签、108,686 个例子（231 个标签没剩例子）；老师重跑 13,607 个标签、211,696 个例子（251 个标签没剩例子）。
  - 权重份额：第 1 步 31.1%，老师重跑 68.9%。权重的有效样本量 93.6%。
  - 确定化计数（训练加留出）：第 1 步共 133,038 对，终局排除 9,333，动作相同 2,085；老师重跑共 243,281 对，终局排除 7,177，动作相同 470。
- **校准行**：两份自对弈里分出胜负的局的 ENDED 回合末，只取训练局（g % 11 != 0），共 32,446 行。
  - 第 1 步自对弈：RC 6f11111 的 analysis/turn-level/step1/selfplay.jsonl；
  - 老师重跑的自对弈：b355c44 的 analysis/card-value/student/selfplay.jsonl。
- **训练集上的读数**（按权重算；只作记录，判定看门）：对比误差 0.00850，同号率 74.62%，校准对数损失 0.5957。

## 数据 sha256

| 文件 | 出处 | sha256 |
|---|---|---|
| teacher_ends.jsonl.gz（第 1 步 T） | RC 6f11111 analysis/turn-level/step1/ | b6ad66a55a701bc56f2205f5d4739f76b060526cc52e4abbfd34f98f62fbe689 |
| gend_ends.jsonl.gz（第 1 步 G_end） | 同上 | e9fbf9b5f465f8c018c3baf458685ac899da2edd3e8e0099592caf5c776cd7fb |
| selfplay.jsonl（第 1 步） | 同上 | e615e6e55197aa7ff072afaef30438fc83773727f2f4d2e13a256e3b2763fc75 |
| labels.jsonl | 分析线 c661c8a analysis/turn-level/step1_labels/ | a67903d0241b691520be7d5e5884b02ab456bb121af342fd088f02fa106e81d3 |
| teacher_ends.jsonl.gz（老师重跑） | 分析线 753d531 analysis/card-value/student_read/ | 1340e4f35eba940c2c1a9141a67a8bb6c37c224ec3c9fcc77218df0c64f3e5ca |
| selfplay.jsonl（学生数据） | b355c44 analysis/card-value/student/ | bf16460354c84770a70eb4c1c8218e450ab04c34f5ff15f5eef8be954958f3a8 |
| ramp-ramp-ended.json（本候选） | | 19d12e0c343174d9e284697cdbd644a980735663a316282c9098231f6c39f532 |
| ramp-ramp-act.json（= 现装） | | f6638159fa561712c03f29f3e0c51a9519e3a543227112887731fcca831cd0c2 |

脚本和日志在 analysis/step1-candidate/：s1_extract.py 抽例子，s1_fit.py 拟合本候选和 B′。

- **智能体串**：`mcts:N+plan+learned+phased=cand-tl-ramp-ramp`，N 按等算力复核。
- **门**：预注册写的 300 对，库 66000000，下沿 > 50%，由分析线经 RC 跑。装机要 Salem 本人的话。
