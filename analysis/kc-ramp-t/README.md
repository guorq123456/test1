# cand-kc-ramp-t 的 G_end：分析线跑的 k 奇数那半（建造线 ecad6f8 的输入）

**条件**：对手卡表已知（牌序、手牌未知）。

- **输入**：建造线 ecad6f8 的 `analysis/kc-ramp-t/`。sha256 核过：selfplay 2957cfb1 / 解压 b3248e79，starts 047fee86 / f456eb33，plans ec271f63 / fcfa0415，step1_rampt.py 863f46b6。脚本原样收在 `analysis/turn-level/step1_rampt.py`（c630874）。
- **命令**：`python -m svsim.tools.host step1_rampt gend selfplay.jsonl starts.jsonl plans.jsonl --out … --ends … --shard 1/2 --bank 69900000 --workers 3`。svsim 建造线 32eb2db（和 ecad6f8 只差 cand-sp2 模型目录）。
- **中途停过一次，补跑过**：
  - 第一次跑了 2 小时，撞上本容器后台任务的时限被停，写完 696 个开头的结果行。
  - 回合末的 .gz 被杀时没刷完缓冲。按 det_seed = 69940000 + 20k + j 反推开头号核对：612 个开头的结果行和回合末都完整，84 个回合末缺了或不全，304 个没开始。
  - 这 612 个以外的 388 个开头单独再跑（筛过的 starts 文件，同样的参数），4394 秒。
  - **确定性核对**：那 84 个开头两次都有结果行，逐行比（除 cpu 计时）**0 处不同**。
  - 合并时只取 612 个完整开头的回合末，加上补跑的 388 个。
- **输出**（本目录）：
  - `gend_odd.jsonl`：1000 行，正好是 starts.jsonl 里的全部 k 奇数开头，不重不漏。训练 916 个（K = 4），留出 84 个（K = 16）。sha256 047ff8bb…10be。
  - `gend_odd_ends.jsonl.gz`：22372 行回合末，每个开头的条数都和它结果行里的局数相等。sha256 902574f4…9162。
- k 偶数那半在建造线跑，两半由建造线合并、核对 2000 个开头不重不漏。

## k 偶数那半的后 9 批（建造线容器重启后分给分析线；2026-10-14 05:3xZ）

- **输入**：建造线 da18c2b 的 `analysis/kc-ramp-t/data/even_rest/starts_09.jsonl`～`starts_17.jsonl`，sha256 前缀逐个核过（合起来那份 0a2243f8 也对）。共 335 个开头，k 1330～1998，全是偶数，不重，和 k 奇数那半没有交集。
- **命令**（每批）：`step1_rampt gend selfplay.jsonl starts_XX.jsonl plans.jsonl --out gend_XX.jsonl --ends gend_XX_ends.jsonl.gz --shard 0/2 --bank 69900000 --workers 3`，svsim 32eb2db，按批顺序，共 3757 秒，没有中断。
- **输出**：`even_09_17/` 下每批两个文件，sha256 在 `even_09_17/SHA256SUMS`。逐批核过：开头和该批 starts 一一对上，每个开头的回合末条数等于它结果行里的局数。
- 前 9 批（00～08，360 个开头）在建造线跑，合并由建造线做。
