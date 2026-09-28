# 第一次运行结果与解读 / First run: numbers and what they mean

*2026-09-28 · Covertype · dev 30,000 行（按区分层抽样）· sealed 116,237 行 · 4 CPU · 总耗时约 20 分钟*
*dev 30,000 rows (area-stratified) · sealed 116,237 rows · 4 CPUs · ~20 min total*

## 1. 三个基线 / Three baselines (dev set)

| 模型 | iid macro-F1 | iid acc | **transfer macro-F1**（留一荒野区）| 各区 Rawah / Neota / Comanche / Cache |
|---|---|---|---|---|
| logreg_raw | 0.530 | 0.723 | **0.291** | 0.235 / 0.441 / 0.229 / 0.259 |
| rf_raw | 0.741 | 0.843 | **0.268** | 0.246 / 0.411 / 0.229 / 0.186 |
| hgb_raw | 0.691 | 0.799 | **0.252** | 0.249 / 0.342 / 0.209 / 0.207 |

## 2. 演化搜索（14 轮，只看 transfer F1）/ Evolutionary search (14 rounds, transfer F1 only)

- 最佳候选：HGB + `aspect_sincos` + `shade_stats`，400 轮、lr 0.03、63 叶、class_weight=balanced。
- transfer F1 从基线最好的 0.291 提到 **0.293**；iid F1 0.744。
- Best candidate: HGB + `aspect_sincos` + `shade_stats`, 400 iters, lr 0.03, 63 leaves, balanced class weights. Transfer F1 moved from the best baseline's 0.291 to **0.293**; iid F1 0.744.

## 3. 封存集（一次性，2/3 预算已用）/ Sealed set (2 of 3 budget spent)

| 候选 | sealed macro-F1 | sealed acc | Rawah / Neota / Comanche / Cache |
|---|---|---|---|
| 搜索最佳（按 transfer 选）best-by-transfer | 0.747 | 0.794 | 0.759 / 0.753 / 0.718 / 0.634 |
| 参考基线 hgb_raw | **0.792** | **0.857** | 0.814 / 0.883 / 0.777 / 0.775 |

## 4. 三条真正的发现 / Three real findings

**发现 1：随机切分把成绩夸大了约 2.5 倍。**
同一个模型，随机 3 折 F1 是 0.69–0.76，换成"训练 3 个荒野区、测第 4 个"就掉到 0.25–0.29。如果一篇论文只报随机切分，它报告的是"记住了这片森林"而不是"学会了森林"。这就是评估器优先要抓的东西。
**Finding 1: A random split inflates the score ~2.5x.** The same models score 0.69–0.76 macro-F1 under random 3-fold CV and 0.25–0.29 when trained on three wilderness areas and tested on the fourth. A paper reporting only the random split is reporting "memorised this forest," not "learned forests." This is exactly what an evaluator-first design is meant to expose.

**发现 2：在这个迁移目标上，14 轮搜索几乎没有进展（0.291 → 0.293），最简单的逻辑回归和最好的候选打平。**
这不是搜索器差，而是目标本身有"标签漂移"：Cache la Poudre 区 90% 以上是黄松/杨柳/花旗松（类型 3、4、6），而这三类在 Neota 完全不存在。任何只见过其他三区的模型都不可能学到它们。**评估器暴露了任务的天花板，这本身就是结果。**
**Finding 2: On this transfer target, 14 rounds of search barely moved (0.291 → 0.293) and plain logistic regression ties the best candidate.** The searcher is not weak; the target has label shift: Cache la Poudre is >90% ponderosa/cottonwood/Douglas-fir (types 3, 4, 6), and those classes do not exist in Neota at all. No model that has seen only the other three areas can learn them. **The evaluator exposed the ceiling of the task, which is itself a result.**

**发现 3：为迁移而选出的候选，在（随机分布的）封存集上反而比朴素基线低 4.5 个点（0.747 vs 0.792）。**
这是"评估器决定你得到什么"的直接证据：优化平衡类权重和跨区稳健性，就会牺牲同分布精度。没有封存集和审计日志，很容易只报有利的一个数字。
**Finding 3: The candidate selected for transfer scores 4.5 points *lower* than the naive baseline on the (randomly distributed) sealed set (0.747 vs 0.792).** Direct evidence that *the evaluator decides what you get*: optimising balanced class weights and cross-area robustness costs in-distribution accuracy. Without a sealed set and an audit log it would be easy to report only the favourable number.

## 5. 由此对评估器 v2 的修改 / Changes for evaluator v2

1. **迁移指标只在"目标区存在的类别"上算 macro-F1**，或改成"留一区 + 类别加权"，消除标签漂移带来的不可学部分。 / Compute transfer macro-F1 only over classes present in the held-out area, or use a class-weighted variant, so the unlearnable part of label shift stops dominating.
2. **复合分 = 迁移分与 iid 分的几何平均**，避免搜索器为迁移牺牲一切。 / Composite = geometric mean of transfer and iid, so the searcher cannot sacrifice everything for transfer.
3. **换成有坐标的数据**（FIA 样地 + Sentinel-2 / 冠层高度），用真正的空间分块。 / Move to a dataset with coordinates and real spatial blocking.
4. **让候选可以是代码**（LLM 写特征函数），而不只是开关。 / Let candidates be code (LLM-written feature functions), not only flags.

## 6. 审计线索 / Audit trail
- `results/audit_log.jsonl`：24 条记录（3 基线 + 14 搜索 + 2 封存 + 5 条搜索器去重重试），每条含配置指纹、分区分数、耗时。
- `results/leaderboard.csv`、`results/summary.json`。
- 24 records (3 baselines + 14 search + 2 sealed + 5 de-dup retries), each with config fingerprint, per-area scores and wall time.
