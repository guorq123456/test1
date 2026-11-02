# 分析线迁移清单（MANIFEST-analyst）

- 线程：分析线，session_01LfGPwGP5hardfTTjWqiw99
- 仓库：/home/user/test1；只推分支 `ccr-da4857cc-rkpgwr`
- 写于 2026-11-02 13:4xZ，应架构线 13:29Z 的迁移请求

## 0. 先说放在哪

- 本容器原来**没有** `/mnt/project-files`。这个目录是我建的，只在本容器里，别的容器和 Salem 的电脑都看不到。
- 所以能进 git 的小件，同时提交到分支 `ccr-da4857cc-rkpgwr` 的 `migration-inbox/architecture/analyst/`（和这里同名同内容）：
  - 本清单
  - `scratch-files.tsv`
  - `scratch-text.tar.gz`
  - `wt_fix-lethal_agent.diff`
  - `s10-local-branches.bundle`
- 下面两件**只在本容器**，没进 git：
  - `scratch-data.tar.gz`（104 MB）：太大，没问过不往共用仓库里塞。要的话我可以分成两段（每段 < 100 MB）推到本分支。
  - `official-card-data.LOCAL-ONLY.tar.gz`：官方卡牌数据。仓库 `.gitignore` 规定这类 Cygames 内容「本地取、不提交」。
- 本容器是临时的，回收后只在本地的东西就没了。

## 1. 本目录的文件

| 文件 | 大小 | sha256 | 是什么 |
|---|---|---|---|
| `MANIFEST-analyst.md` | — | — | 本清单 |
| `scratch-files.tsv` | 0.3 MB | `c9be83852ea3624ee9a6bf7cbdcc59f71aa6be300a6f0aef4e18e93e3bcf6161` | scratchpad 里工作区以外的 2337 个文件，一行一个：状态（IN = 和仓库里某个 git blob 完全相同；OUT = 不在仓库）、字节数、sha256（只算 OUT 的）、git blob、路径、放在哪个包里 |
| `scratch-text.tar.gz` | 0.5 MB | `eabe6d4393dcd014fbcd98c266dea72634cf843279fe96fc25f9ac79d28a7131` | OUT 里的脚本、日志、文本，共 513 个：.py .sh .md .txt .log .svg .png 等。已去掉含官方卡牌文字的文件 |
| `scratch-data.tar.gz` | 104 MB | `1307815292b88c429005735b40d89e1bd7432b3547a0c76aecffa953d2f7ea5e` | OUT 里的数据，共 373 个：.jsonl .json .npz .pkl .gz。**只在本容器** |
| `official-card-data.LOCAL-ONLY.tar.gz` | 1.2 MB | `5441c1dd452ab1435bb0f2920efbac69519e9bc6f5b394b6dc44aaa4c37ea0ef` | OUT 里的官方卡牌数据，共 32 个：`cardtext/`（各弹 en/chs 卡表 json）、`raw10/`（第 10 弹卡表和抽出的卡面文字）、`web/` 和 `web_dl/`（官方 glossary）、`audit_b_cards.txt`（逐张卡面文字）、`qa_grep.txt`（官方 Q&A 摘录）。**不能进仓库，只在本容器** |
| `wt_fix-lethal_agent.diff` | 1.7 KB | `7887cd442e78b398870d6b80a6b29dd7126602fe2f558277a5445dec8fdc3511` | 工作区 wt_fix（HEAD b355c44）里 `svsim/agents/lethal_agent.py` 未提交的 25 行改动，内容是让斩杀线服从被包住的搜索的 veto。**已被 842654e 取代**：同一功能已提交，00cc100 验证过 15 项 480 局逐局相同。只作存档 |
| `s10-local-branches.bundle` | 34 KB | `81443d6fb21a1556972221ac26bdeb6ff4cab36698aacc8fad871142fbdd6366` | 5 个只在本地的分支（见第 2 节）。`git bundle verify` 通过 |


## 2. 分支

**本线自己的分支**

| 分支 | 状态 |
|---|---|
| `ccr-da4857cc-rkpgwr` | 全部已推。迁移前最后一个提交是 9a13de3（种子账本：85980000～85983919，下一个 85990000），之后是本清单的提交 b20734f，和种子账本补登 pilot / 6b 的那个提交 |
| `main` | 等于 origin/main（ef62abe），本线没动过 |

**只在本地、没推的 5 个分支**（全在 `s10-local-branches.bundle` 里）

都是第 10 弹加卡的工作分支，内容已经以补丁形式进了本分支：

| 本地分支 | 头 | 没推的提交 | 对应仓库里的哪一版 |
|---|---|---|---|
| `s10-final-nopend` | 70ea3a1 | 4 | **交付版**。4 个提交和仓库 `analysis/cards-s10/patches/0001～0004` 的 patch-id 逐个相同（92408f3：基于 d27dc30，不含 pending.py） |
| `s10-final-d27` | af6f058 | 4 | 61a1d4d 那一版（基于 d27dc30，含 pending.py 改动） |
| `s10-final` | cb66e2e | 4 | 3abfbba 那一版（基于 463b898） |
| `s10-deliver` | 7ce3eb9 | 4 | 和 s10-final 同一棵树，提交说明不同 |
| `s10-work` | 62b8ec6 | 5 | 更早的工作版。第 1 个提交是只在本地用的 SHIM（not for delivery），后来被建造线 463b898 的引擎钩子取代 |

- 这个包需要的前置提交 4d3d4b5、463b898、d27dc30 都在远端。
- 取出：`git fetch <bundle> 'refs/heads/*:refs/heads/s10/*'`

## 3. 工作区（git worktree）

- scratchpad 下有 92 个工作区（91 个不同的 HEAD）。
- 除 wt_s10、wt_s10b（就是上面两个本地分支）外，所有 HEAD 都已在远端。
- 有未提交内容的 5 个：

| 工作区 | 未提交的内容 | 处理 |
|---|---|---|
| wt_deckA（37f8451，搜索 A） | `runs/deckbuild-A/`（57 MB）和 `runs_A_*.log` | 全部已在仓库 `analysis/deckbuild/runs/A/`：deals.jsonl 和各轮 deals.jsonl.gz 合起来排序后 md5 相同，aborted 文件同样核过，其余文件 git blob 相同。没拷 |
| wt_eot（69e3ad2） | 8 个未跟踪的 .npz | 都和仓库里同名文件的 git blob 完全相同，例如 net-100000 在 e8be9bc、net-gen4-59000 在 1ca29ab。没拷 |
| wt_nm2（eec27ea） | net-nm3-elf-nem.npz（6826dc7）、net-nm3f-elf-nem.npz（113bba0） | 同上，没拷 |
| wt_puct（72a5148） | net-elft-gen4-38500（10dca1d）、net-gen5-68500（7802b8b）、prior-elft-gen4-ft-t05（f8ed72d）、prior-ramp-gen5-ft-t05（a540737） | 同上，没拷 |
| wt_fix（b355c44） | lethal_agent.py 改了 25 行 | → `wt_fix-lethal_agent.diff`，已被 842654e 取代 |

- 主工作区 `/home/user/test1` 没有未提交改动。
- 主工作区被 `.git/info/exclude` 挡掉的只有 `analysis/lethal-setup/runs/` 里两个文件，git blob 已在仓库。

## 4. scratchpad 里不在仓库的东西

- 工作区以外共 2337 个文件：1418 个和仓库里的 git blob 完全相同；919 个不在仓库，共 374.5 MB。
- 919 个里，单个最大的是 43.7 MB（`exp/positions.pkl`），没有超过 200 MB 的。
- 大多是已经写成仓库报告的那些测量的中间表或缓存。有些是仓库里 .gz 版本的未压缩原件，例如 `d8/scan-*.json`、`d9/*.json`、`cn/*.records.jsonl`、`kcrt/*.jsonl`。
- 逐个文件见 `scratch-files.tsv`。按目录汇总（只算不在仓库的）：

| 目录 | 文件数 | MB | 按文件名看是什么 |
|---|---|---|---|
| `o1/` | 21 | 57.5 | 先验概率表 probs-*.npz 和 meta |
| `exp/` | 15 | 44.1 | 早期回合规划实验（plan2 / turnplan / sat 脚本、positions.pkl） |
| `o1n/` | 8 | 34.8 | 同 o1，第二批 |
| `cn/` | 57 | 34.0 | crossn 评测台的 SPRT / 固定局记录和日志 |
| `c3/` | 5 | 26.9 | C3 的点数表 |
| `d8/` | 8 | 26.1 | D8 扫描 json |
| `d9/` | 4 | 24.1 | D9 json |
| `kcrt/` | 18 | 16.5 | cand-kc-ramp-t 的自对弈、计划、终局记录 |
| `gaps/` | 5 | 13.1 | 联赛差距 / 后悔的中间表 |
| `c2pair/` | 22 | 12.5 | C2 推广配对的行数据 |
| `rb/` | 20 | 12.3 | 回放 / top10 题的点数和脚本 |
| `sharp/` | 6 | 11.1 | 尖锐度样本和自对弈 |
| `refit/` | 8 | 9.3 | 留出集重拟合的行数据 |
| `scale_read/` | 8 | 8.2 | 缩放测试读数（logits） |
| `weak/` | 4 | 6.0 | 弱参考审计 |
| `rp/` | 10 | 5.5 | 分歧测量记录 |
| `cardtext/` | 22 | 4.7 | 官方卡表（只在 LOCAL-ONLY 包里） |
| `cross/` | 7 | 4.6 | 跨回合资源行数据、回归局面读数 |
| `d10/` | 6 | 3.8 | D10 |
| `infer/` | 11 | 3.7 | +infer 复核的行数据 |
| 其余约 100 个目录，加顶层 89 个散文件 | 约 330 | 约 17 | 小测量的脚本、日志、冒烟输出 |

## 5. 没拷的东西

- **会话记录** `/root/.claude/projects/-home-user-test1/cf6df9ad-….jsonl`（约 154 MB）：没在请求范围里，没拷。要的话说一声。
- **/tmp 下 scratchpad 以外的文件**：只有 harness 自己的诊断日志、编译缓存、浏览器文件，不是本线的东西。
- **92 个工作区里检出的代码**：都在已推的提交上，从 git 能重建。

## 6. 种子账本

- `analysis/seed-banks.md` 没有未推的改动；最新版在本分支 9a13de3。
- 最近三次登记：
  - 85970000～85979999：体检 C 步（量时间小样、正式互打、后续检查）。
  - 85980000～85983919：盲测和外部卡表互打。85983920～85989999 不分。
- **下一个可用：86400000**（11-02 架构线更正：85990000～86049999 已被 pilot 实验用掉，86300000～86304205 被借鉴流程 6b 用掉，都已补登）。
- 规矩：种子只由分析线分配。

## 7. 现在的状态

条件：对手卡表已知（牌序、手牌未知）

**在做什么**

- 没有在跑的任务。

**最近做完的**

- 卡组搜索 A 跑满 10 轮（3546557）：11 次接受，没有一次换上第 10 弹卡。
  - 参照分对第 0 轮的配对差：龙族 +25.0、精灵 +7.9、主教 +7.9、巫师 +6.4、梦魇 +5.0、皇家护卫 −2.1、超越者 0。
  - J184c 对：5 个职业上升。
- 第 10 弹探索分析，第 1～10 轮（a7aa49c、a33823f、3a460cb、3546557；脚本 `analysis/deckbuild/runs/A/set10/exploration.py`）：
  - 试新卡的比例 25.9%，期望 27.9%；
  - 分层差 −1.2 ± 0.6；
  - 复核 0/12。

**下一步、等谁**

- NM3 第 4 代：等 Salem 或用户拍板。
- 搜索 A 的工作区（scratchpad/wt_deckA）和存档按架构线的要求留着。以后可能要在 A 的现任上做冻结名单以外的比较，由架构线来找。
- 维护种子账本。

**约束**（用户和架构线定的）

- 不动陪练台和 main。
- 不改 `search/mcts.py`、`learn/net.py`、`tools/gate.py`。
- 不可逆的事（发布陪练台、合 main）等 Salem。
- 只推 `ccr-da4857cc-rkpgwr`，不开 PR，不碰 1 号的分支。

**已知坑**

1. **暴风雨般的爆破有两个卡号**（10131320 / 10831310）。`deckbuild.py` 的 legalize / _pick / variant 按卡号数张数，所以 A 的巫师现任第 0～5 轮有 4 张，第 6 轮起才合法。架构线在 9a551e7d、3c4d2c3e 修了，A 没换到修过的代码。巫师的数字只作相对读。
2. **搜索记录里的对手要读 `opp` 字段**。70 局一批不能被 6 整除，无镜像规则下不能用 (seed − s0) % 6 推对手。
3. **BLAS 线程超订**只抬高大矩阵（先验网）那一侧的 CPU 计时，小价值网不受影响。
4. **本容器里干净基线上有 4 个 golden-search 测试失败**，和任何改动无关。换到本机后要重新看。
5. **搜索用 fork 的进程池**，开跑时建好。跑的途中改文件不影响正在跑的进程，换代码只在职业边界（state.json 存档后）做。本容器重启过 3 次，A 每次从 state.json 续跑，没有丢东西。
6. **规则**：
   - 在 Salem 比对前，不上网查第 10 弹的环境（卡组、梯队、天梯统计、比赛结果）。规则和官方卡牌数据可以查。
   - DFM 那七副外部卡表（`external/dfm-2026-10-31.txt`）不能进任何搜索、自对弈卡池或训练数据。
     - 例外 1：dfm/RUNE-ユーリ（三轴土），Salem 10-31 23:18Z 在决定卡上选了「隔离训练」，只为测量做自对弈训练。模型名带 -dfm-，永远不进组卡搜索、不进陪练台和网页模型、不装。
     - 例外 2：dfm/PORTAL-MingiGod（人灭鱼），架构线按同一条规矩延伸做的，Salem 没有单独批。
     - 其余五副照旧不能碰。
   - CLUE_ZERO_DESTROYS = True 是对的。
   - 职业名用官方简中：精灵、皇家护卫、巫师、龙族、梦魇、主教、超越者。
7. **官方卡牌数据不能进仓库**（`.gitignore`：data/raw/ 等）。本包里的那部分单独放在 LOCAL-ONLY 包里。
