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

## 6. 强档 + 弃牌剪枝（只准备，不装；架构线程 21:09Z）——**已被第 7 节取代，不要再装这一节**

**内容**
- 强档配置从 `mcts:200+plan+learned+phased` 改成 `mcts:200+plan+learned+phased+xprune=3:3:cost`。
- 次数不改，评估器文件不动，「最强」档不加。
- 依据：+xprune 的门和确认门合并 52.4%（50.3～54.5），见 analysis/xprune/README.md 和分析线 4d24188。

**要改的文件和配置行**：由 `analysis/install/strong_xprune.py apply` 做精确文本替换，每处原文必须正好出现一次，否则一个字都不写。
| 文件 | 改前 | 改后 |
|---|---|---|
| svsim/ui/session.py | `"strong": "mcts:200+plan+learned+phased",` | `"strong": "mcts:200+plan+learned+phased+xprune=3:3:cost",`（上方加一行注释） |
| svsim/tools/arena.py | （无） | VERSIONS 加 `"v2sx": "mcts:200+plan+learned+phased+xprune=3:3:cost"`，让对局记录里写得出版本名 |
| tests/test_web.py | 两处断言写死旧的强档配置 | 改成新配置 / `v2sx` |
| tests/test_learn.py | 一处同上 | 同上 |

**改前改后的哈希**
- 档位哈希 = `sha256(json.dumps(LEVELS, sort_keys=True))`，`strong_xprune.py check` 会打印。这个值不受换行符影响，各机器一样：
  - 改前：`d1eb81d0896bb431dedba8ac511b157a5aff9f1b1f116c31174d20b381eaea10`
  - 改后：`d0801b946b6a927f9b2d32310556b51d894f7095948ac2091e22ac195ecd8bc5`
- cmp_roots 装前装后都应该是 **755a0bba…96a6**（Windows）：它写死 `mcts:200+plan+learned+phased`，不读档位。装后它不变，说明搜索代码没动；变了就停下。
- 这边（Linux）在独立 worktree 里核过：apply 之后 test_web、test_learn、test_xprune、test_golden_search 共 70 项全过；冒烟测试 OK；revert 之后 git 工作区干净。

**装之前要知道的两件事**
- **`level-strong` 的意思会变。** arena 的 `level-strong` 就是 `LEVELS["strong"]`。装后，所有拿 `level-strong` 当对照的门、标定都是对新强档。
  - 架构线程 21:14Z 定：装后要和旧强档比的门和标定，一律写明 `v2s`；新强档写 `v2sx`。
- **强档的 CR 是旧 bot 测的。** ratings.json 里强档各卡组的 CR（跳费龙 1331、连击妖 1340 等）是装前的值。装后在重新标定之前，开局界面显示的仍是旧值。要不要把它标成「待标定」，由 Salem 定；这个包不动 ratings.json。

**装（Salem 点头、电脑连上以后）**：在仓库根目录、cmd 里一行（低于正常优先级，掩码 0xFFFFE 不用 CPU0，最多 3 个进程）：

```
start "" /WAIT /BELOWNORMAL /AFFINITY FFFFE cmd /c "python analysis\install\strong_xprune.py check && python analysis\install\strong_xprune.py apply && python -m svsim.tools.host analysis.install.strong_xprune_smoke --workers 3 && python -m pytest -q tests\test_web.py tests\test_learn.py tests\test_xprune.py && python -m svsim.tools.host svsim.tools.gate --help >NUL && echo INSTALLED"
```

- 预期：
  - check 打印 `"state": "not installed"` 和改前哈希；
  - apply 打印 before / after 两个哈希，和上面一致；
  - 冒烟测试打印 6 局（跳费龙镜像 2 对、机锋打旗皇 1 对），都分出胜负，跳费龙那几局的 `cut` > 0，最后一行 `OK`；
  - pytest 全过；
  - 最后打印 `INSTALLED`。
- 任何一步失败，`&&` 会停在那里，不往下做。如果失败发生在 apply 之后，就照下面回退。

**装后冒烟测试单独跑**：`python -m svsim.tools.host analysis.install.strong_xprune_smoke --workers 3`（同上，看最后一行 `OK`）。

**回退**

```
start "" /WAIT /BELOWNORMAL /AFFINITY FFFFE cmd /c "python analysis\install\strong_xprune.py revert && python analysis\install\strong_xprune.py check && python -m pytest -q tests\test_web.py tests\test_learn.py"
```

- 预期：check 打印 `"state": "not installed"` 和改前哈希 d1eb81d0…ea10；pytest 全过。
- 也可以直接 `git checkout -- svsim/ui/session.py svsim/tools/arena.py tests/test_web.py tests/test_learn.py`。
- 已经打出的对局记录里写着 `v2sx`，回退后照样能读。
- **强档的 CR**（架构线程 21:14Z 定）：ratings.json 不动。
  - 强档的 CR 是加剪枝之前测的。
  - 门里跳费龙镜像约 +23 CR，其他对位约 0。
  - 要不要重新标定，等 Salem 定。

## 7. 「最强」档 + 强档合并包（加时钟评估器 + 弃牌剪枝）（只准备，不装；架构线程 2026-10-11 18:47Z）

**先后顺序**：第一步装「最强」档（b215e3d），第二步装强档合并包。两步各自可以单独回退。

**内容**
- 「最强」：`LEVELS["max"] = mcts:1043+plan+learned+phased`，是新增的一档，不替换任何档。b215e3d 起已经在代码里。
- 强档：`mcts:200+plan+learned+phased` 改成 `mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost`，次数 200 不改，和叠加门 J81 的写法一样。版本名 `v2skx`。
- 只装合并包，不要再装第 6 节。如果第 6 节已经装了，先用第 6 节的回退命令退掉；合并包的 apply 要求强档是旧配置，否则一个字都不写。

**加时钟包只影响强档，已经核实**（这边，2026-10-11）
- `phased=pkg-kc-ramp-ramp` 只给点名它的那个智能体单独加载这个目录（arena.make_agent → learn.phased.load(folder_of(name))），共用的 `svsim/learn/phased_models/ramp-ramp-ended.json` 不改。
  - 这份文件的 sha256 是 97b0a8f2…100e，从 491c6aa 起没变过。
- 「最强」档读的仍是这份原文件；强档读包里的那份（95acaf1e…a125，cand-kc 的）。
- 两边比过全部配对：只有 (ramp, ramp, ended) 不同，其他配对的评估器完全一样。
- 训练器网页的构建（tools.web）会因为有一档点名了 `pkg-kc-ramp-ramp`，自动把这个目录打进包里；合并包同时改了 test_web 里列出已打包目录的那条断言。

**pkg-kc-ramp-ramp 目录要随仓库到 Windows**
- 26 个文件，由 3eab414 生成，用 `PACKAGE.json` 记来源。
- 目录摘要 = 对按文件名排序的「文件名 sha256」逐行算 sha256，CRLF 当 LF 算，所以 Windows 换行转换不影响：
  - `1e7bc6f82c2515a2d06dfb4803e25997c3324374e4c9ba312d0dc3bf23bc5675`
- `strong_kc_xprune.py check / apply` 都会核这个摘要；不对，apply 就一个字都不写。
- 其中被替换的 `ramp-ramp-ended.json`：95acaf1e5c27a6d83eb342be32564cc1e9bec61ad512028b922694fae300a125。

**哈希**
- 档位哈希（`sha256(json.dumps(LEVELS, sort_keys=True))`，各机器一样）：
  - 改前：`d1eb81d0896bb431dedba8ac511b157a5aff9f1b1f116c31174d20b381eaea10`（已含「最强」档）
  - 合并包装后：`c0125dc5a06aaf7fa3f885ed6708c43df4e2f6a338c839834de00805376d9ea9`
- cmp_roots 两步前后都应该是 **755a0bba…96a6**（Windows）：它写死旧强档配置，不读档位。变了就停下。
- 这边（Linux）在独立 worktree 里走过一遍：
  - apply → test_web、test_learn、test_xprune、test_golden_search、test_install_packages 共 77 项全过；
  - 冒烟 OK：强档读 pkg-kc、「最强」读原文件；6 局都打完；跳费龙那几局剪枝起作用上千次；
  - revert → git 工作区干净；
  - 全量 `pytest -q`（apply 之后）：1171 通过、7 跳过；
  - 第一步的「最强」冒烟命令在这边跑了 14 秒，2 局都打完。

**第一步：「最强」档（b215e3d）**，在仓库根目录、cmd 里：
- check：
  ```
  start "" /WAIT /BELOWNORMAL /AFFINITY FFFFE cmd /c "git merge-base --is-ancestor b215e3d HEAD && python analysis\install\strong_kc_xprune.py check"
  ```
  预期 `"max": "mcts:1043+plan+learned+phased"`、`"strong": "mcts:200+plan+learned+phased"`。如果 git 那一步失败，说明检出的代码早于 b215e3d，要先更新分支。
- apply：不用改文件，检出的代码在 b215e3d 之后就已经包含它；训练器里会多出「最强」一档。
- 冒烟（1 对，「最强」对强档，跳费龙镜像，大约几分钟）：
  ```
  start "" /WAIT /BELOWNORMAL /AFFINITY FFFFE cmd /c "python -m svsim.tools.host svsim.tools.gate --a level-max --b level-strong --deck ramp --opponent ramp --fixed --max 2 --seed 69900010 --workers 2 --out max_smoke.jsonl"
  ```
  预期 2 局都打完，打印 2 局的得分行。胜负不作判定，只看能不能跑完。
- 回退：「最强」是新增的一档，不选它就等于没装。要从代码里拿掉，要 revert b215e3d（它改了 session.py、ratings.json、test_web.py、index.html，之后的提交也改过这几个文件），请先问建造线。

**第二步：强档合并包**
- check：
  ```
  start "" /WAIT /BELOWNORMAL /AFFINITY FFFFE cmd /c "python analysis\install\strong_kc_xprune.py check"
  ```
  预期：`"state": "not installed"`，改前哈希 d1eb81d0…ea10，`"package": {... "ok": true}`。
- apply + 冒烟 + 测试（一行；任何一步失败都会停下）：
  ```
  start "" /WAIT /BELOWNORMAL /AFFINITY FFFFE cmd /c "python analysis\install\strong_kc_xprune.py apply && python -m svsim.tools.host analysis.install.strong_kc_xprune_smoke --workers 3 && python -m pytest -q tests\test_web.py tests\test_learn.py tests\test_xprune.py tests\test_install_packages.py && echo INSTALLED"
  ```
  - 预期：apply 打印 before d1eb81d0…ea10 / after c0125dc5…9ea9，`package.ok` 为 true；
  - 冒烟第一行是 `"ramp_ramp_ended_read_by": {"strong": "pkg-kc-ramp-ramp", "max": "installed"}`，接着 6 局都分出胜负，跳费龙那几局 `cut` > 0，最后一行 `OK`；
  - pytest 全过；最后打印 `INSTALLED`。
- 冒烟单独跑：`python -m svsim.tools.host analysis.install.strong_kc_xprune_smoke --workers 3`。
- 回退：
  ```
  start "" /WAIT /BELOWNORMAL /AFFINITY FFFFE cmd /c "python analysis\install\strong_kc_xprune.py revert && python analysis\install\strong_kc_xprune.py check && python -m pytest -q tests\test_web.py tests\test_learn.py"
  ```
  - 预期：check 回到 `"state": "not installed"`、改前哈希 d1eb81d0…ea10；pytest 全过。
  - 也可以直接 `git checkout -- svsim/ui/session.py svsim/tools/arena.py tests/test_web.py tests/test_learn.py`。
  - pkg-kc-ramp-ramp 目录留着无害：没有档位点名它，就没有任何东西读它，网页构建也不会打包它。
  - 对局记录里写着 `v2skx` 的照样能读。

**装后的名字和段位**
- 装后 `level-strong` 指新强档。要和旧强档比的门和标定，一律写明 `v2s`；新强档写 `v2skx`（同第 6 节的约定）。
- 强档的 CR（ratings.json，跳费龙 1331 等）是改前测的。这个包不动 ratings.json，要不要重新标定，等 Salem 定。

