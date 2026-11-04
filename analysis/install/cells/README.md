# D 格：现装 mcts:1460 对 mcts:1043（分析线 0b6832b 预注册，只作描述）

**条件：**对手卡表已知（牌序、手牌未知）。

- **命令：**`python -m svsim.tools.host svsim.tools.gate --a "mcts:1460+plan+learned+phased" --b "mcts:1043+plan+learned+phased" --deck ramp --opponent ramp --fixed --max 600 --seed 68030000 --workers 4 --out D.jsonl`
- **代码：**svsim 0e038cb（git worktree）。
- **机器：**建造线容器，4 核；host 去掉 CPU0 后剩 3 核，nice 10；workers 被限成 3。用时 4329 s。
- **结果：**gate 自己的读数是 A 得分 50.8%（48.8%～52.9%），A 先手 61.3%、后手 40.3%，着法完全一样的对 30 / 300。正式读数由分析线用 pooled.py 做。
- **文件：**D.jsonl（300 行）、D.log。
