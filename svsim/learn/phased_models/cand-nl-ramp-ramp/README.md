# 候选 cand-nl-ramp-ramp：非线性回合末模型（线性部分加一个 16 单元的 tanh 隐层；没装）

**条件：**对手卡表已知（牌序、手牌未知）。

架构线程 2026-10-10 13:21Z 布置。做法、留出读数、329/455 和算力都写在 analysis/nonlinear/README.md。

- **拟合：**用 cand-kc-ramp-ramp 的数据、特征和对比目标，从 cand-kc 出发；脚本是 analysis/nonlinear/nl_fit.py。
- **ACT：**ramp-ramp-act.json 就是现装那份。
- **智能体串：**`mcts:N+plan+learned+phased=cand-nl-ramp-ramp`。
- **装机：**要 Salem 本人的话。
