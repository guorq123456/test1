# 交给 Salem 本机跑的三个起手闸门（R 对 D，混池）

架构线程 23:24Z 定的：连击妖那个闸门在云端跑；下面三个转给本机（20 核 Windows）。顺序随意，互相独立。

**条件**：对手卡表已知（牌序、手牌未知）。

## 这三个闸门在测什么

- **R** 是草案的起手规则（`+mull=rules`，等于草案 R-B，每套 2000 手逐手核对一致），**D** 是现在的默认起手。
- **混池**：一个闸门固定被测卡组，对手是几套卡组轮换，同一个种子库里第 k 个种子对 `对手[k % 对手数]`。报告按对手拆行。
- **为什么不用 gate.py**：gate.py 一次只有一个 `--opponent`，而且比的是 A 对 B 的胜负。非镜像组合这样比，得分本来就不在 50%。
- 这里用的是 `analysis/tournament-audit/mulligan_gate.py`，比的是同一套卡组两种起手的差：
  - 每个种子，被测卡组先坐 0 号位、再坐 1 号位，先后手由种子决定；
  - 每个座位打两局：一局被测方按 R 换牌，一局按 D 换牌；
  - 对手一律按 D，双方 agent 种子按座位给（2s、2s+1），四局都一样；
  - 一对的得分是 d = R 的得分 − D 的得分，两个座位平均；
  - R 和 D 换的牌一样时，两局是同一局（agent 在同一副发牌下几乎是确定的），d 正好是 0。
- **SPRT**：对 0.5 + d 做，H0 0.50，H1 0.55，α = β = 0.05，用 tools.gate 的正态近似。H1 的意思是 R 让这套卡组的得分高 5 个点。每 25 对判一次，最多 600 对（R 局 1200 局）。
- **规矩**：SPRT 判 H1，才在新种子上接固定 300 对（R 局 600 局）。判 H0，就不跑固定局数。

## 准备（一次）

需要同一个仓库（guorq123456/test1）的两个检出目录，放在同一个父目录下：

- `svsim-c962055`：1 号分支的提交 **c962055**，里面是 svsim 代码。云端的连击妖闸门用的也是这个提交，三个闸门和它保持一致。
- `test1-analysis`：test1 会话的分支 `ccr-da4857cc-rkpgwr`，里面是脚本。

```
git clone https://github.com/guorq123456/test1.git svsim-c962055
cd svsim-c962055
git checkout c962055
git worktree add ..\test1-analysis origin/ccr-da4857cc-rkpgwr
mkdir ..\test1-analysis\analysis\tournament-audit\local
```

- Python 3.10 以上，不需要额外的包。
- 下面的命令都在 `svsim-c962055` 目录里执行。
- 每个窗口先设环境变量。

PowerShell：

```
$env:PYTHONPATH = "."
$env:PYTHONIOENCODING = "utf-8"
```

cmd：

```
set PYTHONPATH=.
set PYTHONIOENCODING=utf-8
```

`--workers` 按机器给。20 核可以用 16。结果只和种子有关，和进程数无关；只是 SPRT 判停时，已经跑完的是哪些对，会随完成顺序略有不同。

## 1. 旗皇 对 四套（R 和 D 换法不同的手约 63%）

```
python ..\test1-analysis\analysis\tournament-audit\mulligan_gate.py --deck pirate-t --way rules --opponents elf-t nemesis-t ramp-t pirate-t --phase sprt --pairs 600 --seed 39000000 --workers 16 --out ..\test1-analysis\analysis\tournament-audit\local\mull_pirate_sprt.jsonl
```

终端输出的最后一行是 `SPRT 停：H1` 时，才跑固定局数：

```
python ..\test1-analysis\analysis\tournament-audit\mulligan_gate.py --deck pirate-t --way rules --opponents elf-t nemesis-t ramp-t pirate-t --phase fixed --pairs 300 --seed 39500000 --workers 16 --out ..\test1-analysis\analysis\tournament-audit\local\mull_pirate_fixed600.jsonl
```

## 2. 跳费龙 对 连击妖、机锋（不含镜像和对旗皇；不同的手 40% / 36%）

```
python ..\test1-analysis\analysis\tournament-audit\mulligan_gate.py --deck ramp-t --way rules --opponents elf-t nemesis-t --phase sprt --pairs 600 --seed 40000000 --workers 16 --out ..\test1-analysis\analysis\tournament-audit\local\mull_ramp_sprt.jsonl
```

判 H1 时：

```
python ..\test1-analysis\analysis\tournament-audit\mulligan_gate.py --deck ramp-t --way rules --opponents elf-t nemesis-t --phase fixed --pairs 300 --seed 40500000 --workers 16 --out ..\test1-analysis\analysis\tournament-audit\local\mull_ramp_fixed600.jsonl
```

## 3. 机锋 对 四套，用条件变体 `rules:nem4`

不开变体时 R 和 D 完全一样，所以这里一定要带 nem4。

```
python ..\test1-analysis\analysis\tournament-audit\mulligan_gate.py --deck nemesis-t --way rules:nem4 --opponents elf-t nemesis-t ramp-t pirate-t --phase sprt --pairs 600 --seed 41000000 --workers 16 --out ..\test1-analysis\analysis\tournament-audit\local\mull_nemesis_sprt.jsonl
```

判 H1 时：

```
python ..\test1-analysis\analysis\tournament-audit\mulligan_gate.py --deck nemesis-t --way rules:nem4 --opponents elf-t nemesis-t ramp-t pirate-t --phase fixed --pairs 300 --seed 41500000 --workers 16 --out ..\test1-analysis\analysis\tournament-audit\local\mull_nemesis_fixed600.jsonl
```

## 中断和续跑

- 输出文件是一对一行（JSON lines）。
- 同样的命令再跑一次会从文件接着跑，已经有的对跳过。
- SPRT 已经判定时，重跑只打印判定，不再加局。

## 报告

每个闸门一条命令。有固定局数就把两个文件都列上，各出一节：

```
python ..\test1-analysis\analysis\tournament-audit\mulligan_gate.py --report ..\test1-analysis\analysis\tournament-audit\local\mull_pirate_sprt.jsonl ..\test1-analysis\analysis\tournament-audit\local\mull_pirate_fixed600.jsonl
```

报告里有：

- **按对手拆行**，最后一行是合计。每行两列，区间都按对算：
  - (a) 全部对的 R − D，也就是部署效果；
  - (b) 只算至少一个座位 R ≠ D 的对，也就是规则真发动时的效果。功效高，但这是条件效果，不能直接当部署效果用。
- **CR**：Salem 刻度（每 logit 236，以 D 自己的得分为基准），括号里是稳态式 800 × d。
- R ≠ D 的对占多少。
- **按真实先后手拆**：被测卡组先手的局和后手的局分开报 R − D，这一项按座位算。
- 一个自检数：「R=D 却胜负不同的座位」，应该接近 0。

## 预计用时

- 每对 4 局，v2s 一局约 6 秒（这边 4 核时的数）。
- SPRT 最多 600 对，就是 2400 局，16 个进程约 15 分钟。固定 300 对约 8 分钟。

## 跑完以后

把 `local\` 里的 `.jsonl` 和报告输出交回来，交给架构线程转，或者直接发给 test1 会话都行。test1 会话负责写进 README，和云端的连击妖闸门并排。
