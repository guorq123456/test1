# Windows 上要核对的东西（只准备，不装）

**条件：**对手卡表已知（牌序、手牌未知）。

架构线程 2026-10-10 15:27Z 布置。

**装什么、哪一档用什么，都等 Salem 本人决定。**这份清单只列在 Salem 的机器（Windows，Python 3.12.10）上要跑的命令和预期结果。

**怎么跑：**
- 所有命令都经 `python -m svsim.tools.host <module> ...` 启动：低于正常优先级，不用 CPU0，进程数 ≤ 12。
- 分析脚本按模块从 PYTHONPATH 运行，和 8bb28a8 那次一样。
- `STEP1` 是第 1 步数据目录（RC 6f11111）。

## 0. 版本和环境

- 分支 `ccr-165ad1e7-t2zmqu`，至少到 **0e038cb**（提速第 6 轮：根节点动作每步只算一次）。
- `python -c "import svsim.core.view as v; print(v._INLINE)"` 应打印 **True**，和 8bb28a8 那次一样。

## 1. 行为没变（三项都要过）

| 检查 | 命令 | 预期 |
|---|---|---|
| cmp_roots（116 个根节点，level-strong 整个智能体） | `analysis/speed/cmp_roots.py STEP1` | **`116 755a0bba6cfb1119729e19b4af0484d6a583854d678b1697cd91fb39f63596a6`** |
| 黄金对局哈希（本机打的五局，每一步） | `analysis/install/golden_hash.py` | 和下面 8bb28a8 记的 Windows 值逐行一样 |
| 全量测试 | `pytest -q` | 只有 `test_golden_search` 那 4 局在最后几位不一致，其余全过（见下） |

**cmp_roots 的说明：**
- 755a0bba…96a6 是 8bb28a8 在这台机器上对 c5413b3 的读数。
- 之后的改动都是精确的，或者默认关闭：
  - 提速第 3、4、6 轮：没有把任何浮点 `sum()` 换成别的写法；角色值求和按构造是 1/8 的倍数，与顺序无关；
  - 「最强」档：只是加了一档；
  - +lethal3 等：都是默认关闭的开关。
- 所以哈希应该不变。**要是变了，先停下，别装任何东西**，把读数发给建造线。

**黄金对局哈希（Windows，8bb28a8 记录）：**

```
ramp|ramp|101 60 a7931afcd4a73429fe64635130c6c4fa18ede47c35667c7343458d4b069742e9
ramp-t|ramp-t|102 50 a36de586a1707d1a854d6866213d30cc51458c1618787f32b39a38be5d5e40b8
elf-t|elf-t|103 50 57ff48df94e64a69b36878c091623b5060c5d514566e861e739e6be3a47b4800
elf-t|ramp-t|104 50 81cd3e3bae72d0c5c4d3ac8366351515720104b1b6dd9976710785ac6086f8c5
nemesis-t|pirate-t|105 40 c95bc23d4d17a38ca068ea2299cf7674ca0e851755dbb34d93bae72494f7785a
```

对照：这边 Linux（Python 3.11）的值，前 4 局在最后几位不同，第 5 局一样：

```
ramp|ramp|101 60 e018e8947ddc2fc08749123a741b24fb864ad8c92893c6d8a5683b210f960844
ramp-t|ramp-t|102 50 17d5b29369041fd6749723b734e681b65faa2a87ac4f621f494f30203b6b114b
elf-t|elf-t|103 50 21fda117ae0cb2de254eea5ab6e83d9e659dc4741630b9d3881c6e80f3aafcc9
elf-t|ramp-t|104 50 b8e34cdfeb7163ac74f3304b228ebb6c8edb9923501d8007a98f3d23cb8b86e9
nemesis-t|pirate-t|105 40 c95bc23d4d17a38ca068ea2299cf7674ca0e851755dbb34d93bae72494f7785a
```

**全量测试的已知情况：**
- `tests/test_golden_search.py` 的记录是在 Linux 上冻结的。8bb28a8 在 Windows 上 5 局里有 4 局只在最后几位不同（旧代码新代码都一样），这是机器差异。
- `tests/test_lethal3.py::test_ramps_missed_lethals_replayed` 要设 `SVSIM_STEP1_DIR` 才跑，否则跳过。
- 其余都应该通过，这边是 1163 通过、1 跳过。

## 2. 「最强」档（b215e3d）

- `python -c "from svsim.ui.session import LEVELS; print(LEVELS['max'], LEVELS['strong'])"` 应打印 `mcts:1043+plan+learned+phased mcts:200+plan+learned+phased`。
- 换算表在 analysis/speed/WALLCLOCK.md。这边 0e038cb 上的墙钟是旧代码的 0.71 倍（最强）和 0.76 倍（强）。
- Salem 的机器快慢不同。要不要把 N 加回到原来的墙钟（大约强 300、最强 1460），得先在这台机器上重测：
  - 命令：`analysis/speed/wallclock.py STEP1 out.json 2 "mcts:200+plan+learned+phased" "mcts:1043+plan+learned+phased" ...`
  - 在 3e9a331 和 0e038cb 两个检出上各跑一次。

## 3. +lethal3（默认关闭的开关）

- 提交：开关在 13b0b7a，修正 realize 在 9c1bb01，离线读数在 518b12f（Ramp 找到 905，没有丢的）。
  - 架构线程写的 850237d 是 cand-th 的提交，不是 +lethal3 的。
- 核对：
  - `tests/test_lethal3.py` 全过（设了 `SVSIM_STEP1_DIR` 时 8 项）；
  - `python -c "from svsim.tools.arena import make_agent; make_agent('level-strong+lethal3', 0)"` 不报错。
- 它不在任何一档里，装不装由 Salem 定。

## 4. 提速（0e038cb）

- 行为核对就是第 1 节，三项都要过。
- 速度：`analysis/speed/bench.py STEP1 30 3`，在 3e9a331 和 0e038cb 上交替跑。
  - 这边的读数是每秒迭代 2154 → 2979（只算第 6 轮），从第 3 轮之前算起约 +60%。
- 根节点缓存的核对模式（可选，十几分钟）：`analysis/speed/root_check.py STEP1 --named-games 1 --random-games 100`，预期 `"differences": 0`。

## 5. 装档包（只覆盖跳费龙镜像 ENDED 的那份）

- `svsim/learn/phased_models/pkg-kc-ramp-ramp/`、`pkg-nl-ramp-ramp/`，由 `analysis/install/make_pkg.py` 生成。
- 内容：现装全部 24 个模型文件逐字节拷贝，只有 `ramp-ramp-ended.json` 换成候选的。
  - 单用候选目录（`cand-kc-ramp-ramp`）的话，其他配对会退回别的模型：海盗局面的 ACT 读数从 +14.5 变成 −14.3。
- 每个包的 `PACKAGE.json` 记了每个文件的来源和 sha256。
- 替换进去的文件：

| 包 | ramp-ramp-ended.json 的 sha256 |
|---|---|
| pkg-kc-ramp-ramp | 95acaf1e5c27a6d83eb342be32564cc1e9bec61ad512028b922694fae300a125 |
| pkg-nl-ramp-ramp | 2e151816768efea6463e5591a5e04e9fe1033c2833be2534f73fef26c951f655 |

- 核对：`pytest -q tests/test_install_packages.py` 7 项全过。它逐字节比对文件，并断言加载后除 ramp-ramp ENDED 以外每个配对的模型都和现装一样，海盗和精灵局面的打分也和现装完全一样。
- **用法：**`mcts:N+plan+learned+phased=pkg-kc-ramp-ramp`。只有写进档位才会生效，写不写由 Salem 定。
- **一个差别要知道：**跳费龙 ramp-t 镜像用的是现装的 ramp-t-ramp-t 模型。直接用候选目录时，会经别名用到候选的 ramp-ramp 模型。
- **门的情况：**
  - cand-kc：门前检查 (1) 没过，见 cand-kc README。
  - cand-nl：对 level-strong 的门已由分析线预注册，在跑。
  - 两者在题 3 那类局面都偏向打脸（analysis/puzzles3/README.md 末节）。
