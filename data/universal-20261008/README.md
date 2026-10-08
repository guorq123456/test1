# 留一套牌测试的自对弈：后半（本机，2026-10-08）

`analysis/universal-bot/selfplay/run.sh`（e8d2153）的后半：crystal-t、synergy-t 各对 ramp-t / elf-t / pirate-t，每份 1000 局。前半（bishop-t、nm-t）由云端会话跑。

- 代码：`claude/universal-bot` @ e8d2153，本机单独的 worktree。
- 命令（每份）：`python -m svsim.learn.netdata --games 1000 --deck <d> --opponent <o> --agent v2 --explore 0.03 --workers 16 --seed <s> --out <d>_<o>.jsonl`，再 gzip。和 run.sh 的区别只有 `--workers 16`（脚本是 4）；结果只和种子有关。
- 种子按 run.sh 的循环顺序算（s 从 20261201 起，每份 +1，顺序 bishop-t、nm-t、crystal-t、synergy-t × ramp-t、elf-t、pirate-t），本机倒序跑，种子不变：

| 文件 | 种子 | 局数 |
|---|---|---|
| crystal-t_ramp-t.jsonl.gz | 20261208 | 1000 |
| crystal-t_elf-t.jsonl.gz | 20261209 | 1000 |
| crystal-t_pirate-t.jsonl.gz | 20261210 | 1000 |
| synergy-t_ramp-t.jsonl.gz | 20261211 | 1000 |
| synergy-t_elf-t.jsonl.gz | 20261212 | 1000 |
| synergy-t_pirate-t.jsonl.gz | 20261213 | 1000 |
