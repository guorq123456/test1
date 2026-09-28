# forest_eval：林业 ML 的"评估器优先"原型
# forest_eval: an evaluator-first prototype for forestry ML

*方向 A 的第一版 / First cut of Direction A (2026-09-28)*

---

## 1. 这是什么 / What this is

**中文**：一个小而完整的工具包，把"怎么给答案打分"先钉死，再让任何搜索者（人、随机搜索、演化循环、LLM 代理）去找答案。它实现了 Fable 报告里 F1/N1 的主张：**评估器才是护城河**。第一版跑在 UCI Covertype（科罗拉多 Roosevelt 国家森林，58 万个 30 m 像元，54 个地形/土壤特征，7 种森林覆盖类型）上，因为它是这个容器里唯一能下载到的开放林业数据。

**English**: A small but complete toolkit that pins down *how answers are scored* before any searcher (human, random search, evolutionary loop, LLM agent) looks for answers. It implements claim F1/N1 of the Fable report: **the evaluator is the moat**. Version 1 runs on UCI Covertype (Roosevelt National Forest, Colorado; 581k 30 m cells; 54 terrain/soil features; 7 cover types) because it is the only open forestry dataset reachable from this container.

## 2. 评估器的四个设计决定 / Four design decisions in the evaluator

每一条都对应 AI 科学家系统已被记录的失败模式（arXiv 2509.08713）。
Each answers a documented failure mode of AI-scientist systems (arXiv 2509.08713).

| 决定 Decision | 防的是什么 What it prevents |
|---|---|
| 固定指标（macro-F1）、固定数据、固定切分 / Fixed metric, data, splits | 挑指标、挑基准 / metric & benchmark shopping |
| **迁移分数**：留一荒野区（leave-one-wilderness-area-out），训练 3 个区、测试第 4 个区；排序只看它 / **Transfer score** ranks candidates | 靠记住空间结构刷分 / winning by memorising spatial structure (the classic ecological pitfall) |
| **封存测试集**：20% 行由加盐哈希选出，预算只有 3 次调用，每次记录 / **Sealed test set** with a 3-call budget, every call logged | 在测试集上事后挑选 / post-hoc selection on test |
| **只追加的审计日志**（JSONL）：每次评估的配置指纹、分区分数、耗时 / **Append-only audit log** | 只看论文看不出的问题；论文 51%，日志 74% / what papers hide (51% detectable from paper vs 74% from logs) |

## 3. 文件 / Files

```
evaluator-A/
├── forest_eval/
│   ├── data.py        # 读取镜像 CSV、修复列名、哈希封存切分 / load, fix header, sealed split
│   ├── evaluator.py   # ForestEvaluator: evaluate() / evaluate_sealed() / leaderboard()
│   ├── candidates.py  # 候选空间：生态特征工程开关 + 3 类模型 / candidate space
│   └── search.py      # 演化循环（AlphaEvolve 的极简版）/ minimal evolutionary loop
├── run_demo.py        # 基线 → 搜索 → 一次封存评估 / baselines → search → one sealed eval
├── results/           # audit_log.jsonl, leaderboard.csv, summary.json
├── RESULTS.md         # 本次运行的数字与解读 / numbers and reading of this run
└── README.md
```

## 4. 怎么跑 / How to run

```bash
pip install scikit-learn pandas numpy
# 数据：UCI Covertype 的 GitHub 镜像（约 75 MB）/ data: GitHub mirror of UCI Covertype
curl -L -o covtype.csv https://raw.githubusercontent.com/alpinedatalabs/demos/master/forest_cover/data/covtype.csv
python run_demo.py --csv covtype.csv --dev-rows 30000 --evals 14
```

`--dev-rows` 只对开发集下采样，封存集从不下采样。4 核 CPU 上 30k 行、14 轮约 40 分钟。
`--dev-rows` subsamples the dev set only; the sealed set is never subsampled. ~40 min for 30k rows, 14 rounds on 4 CPUs.

## 5. 怎么接入 LLM 代理 / Plugging in an LLM agent

搜索器只需要实现一个函数：`proposer(elite, rng) -> config_dict`。把它换成一个调用 LLM、读入精英榜和审计日志、输出 JSON 配置的函数，评估器与封存预算完全不变。
The searcher is one function: `proposer(elite, rng) -> config_dict`. Replace it with an LLM call that reads the elite list and the audit log and returns a JSON config; the evaluator and sealed budget stay identical.

```python
from forest_eval.search import evolve
def llm_proposer(elite, rng):
    prompt = render(elite)          # 展示精英配置与分区分数 / show elite configs + per-area scores
    return json.loads(call_llm(prompt))   # 必须只返回 config JSON / must return config JSON only
evolve(ev, n_evals=30, proposer=llm_proposer)
```

## 6. 已知局限与下一步 / Known limits and next steps

**中文**
- Covertype 没有坐标，"留一荒野区"是空间阻断的代理，不是真正的空间交叉验证。下一步换成有坐标的数据（FIA 样地 + Sentinel-2 / 冠层高度图），用地理分块（spatial blocking）替代。
- 候选空间是手写的 6 个特征开关 + 3 类模型；LLM 代理可以直接写新的特征函数（AlphaEvolve 式的"代码即候选"），那才是这个框架的完整形态。
- 封存预算为 3，这次用了 2 次（最佳候选 + 参考基线）。剩下 1 次留给下一版。

**English**
- Covertype has no coordinates; leave-one-area-out is a proxy for spatial blocking, not true spatial CV. Next: a dataset with coordinates (FIA plots + Sentinel-2 / canopy-height maps) with real spatial blocks.
- The candidate space is 6 hand-written feature flags + 3 model families; an LLM agent could write new feature *functions* (AlphaEvolve-style "code as candidate"), which is the full form of this framework.
- Sealed budget is 3; this run spent 2 (best candidate + reference baseline). One is left for the next version.

## 7. 数据来源 / Data source
Blackard, J. A. & Dean, D. J. (1999). Comparative accuracies of artificial neural networks and discriminant analysis in predicting forest cover types from cartographic variables. *Computers and Electronics in Agriculture* 24, 131–151. UCI Machine Learning Repository: Covertype. Mirror used: `alpinedatalabs/demos` on GitHub (header mislabeled; corrected in `data.py`, verified by one-hot row sums).
