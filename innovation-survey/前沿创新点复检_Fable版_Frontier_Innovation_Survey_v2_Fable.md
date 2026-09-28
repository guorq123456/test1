# 前沿创新点复检（Fable 5.1 独立版）+ 与 Opus 版对比
# Frontier Innovation Re-Survey (Fable 5.1, independent) + Comparison with the Opus Report

*2026-09-28 · 为 Salem 准备 / prepared for Salem*

> 方法说明：我**先做独立检索、先写自己的结论**（第 1–5 节），最后才打开 Opus 的报告做逐条对比（第 6 节），以避免被它的框架带偏。检索故意换了入口：年度榜单（Science、MIT TR、Nature's 10、Physics World、CAS）、元科学（"什么让研究具有颠覆性"）、以及 Opus 没碰的领域（社会科学、数学、能源、农业、城市气候、土壤/木质素）。
> Method: I ran my own searches and wrote my own conclusions (Sections 1–5) **before** opening the Opus report, then compared item by item (Section 6). I deliberately used different entry points: year-end lists (Science, MIT TR, Nature's 10, Physics World, CAS), meta-science ("what makes research disruptive"), and fields Opus did not cover (social science, mathematics, energy, agriculture, urban climate, soil/lignin).

两个页面被限流没读到正文：Nature 2026《LLM 能预测社会科学实验结果》和 Nature Comms 2025《全球数据驱动火灾预测》；对它们我只用了摘要页/新闻稿信息，标了 ⚠️。
Two pages were rate-limited: Nature 2026 "LLMs can predict social-science experiment results" and Nat. Commun. 2025 "Global data-driven prediction of fire activity"; for those I relied on abstract/press pages only, marked ⚠️.

---

## 0. 一页结论 / TL;DR

**中文**
1. 我看到的最强重合点不是"用了 AI"，而是：**凡是能写出便宜的自动评估器（evaluator）的问题，都正在被 AI 搜索循环吃掉**（AlphaEvolve 的数学、蛋白设计、Robin 的药物排序）。评估器才是护城河，不是模型。
2. 第二个重合点：**"计算机里先做一遍"（in-silico pilot）**正在从物理/化学蔓延到社会科学（LLM 预测实验结果）与生态学。它把昂贵实验的失败前移到几美元的推理。
3. 元科学的一个反直觉证据：**"远距离跨学科拼接"与颠覆性呈负相关**；真正被引用为"取代旧范式"的工作，52% 与其挑战的对象在同一领域——即"同一问题、更好解法"胜过"新奇组合"。这直接修正了常见的"跨界创新"建议。
4. 我最推荐的三条低成本高潜力路线：**(A) 评估器优先**——为一个林业/环境问题写出可自动打分的评估器，然后让搜索/代理循环跑；**(B) 开放格网数据的全球综合 + 公平性维度**（Nature Comms 2026 树木-城市热岛论文就是模板，成本 $0）；**(C) 审计自动化科学**——AI 科学家系统已被证明会挑基准、漏数据，生态领域尚无人做这种审计。

**English**
1. The strongest overlap I see is not "uses AI" but: **any problem for which a cheap automated evaluator can be written is being eaten by AI search loops** (AlphaEvolve in math, protein design, Robin's drug ranking). The evaluator is the moat, not the model.
2. Second overlap: the **in-silico pilot** is spreading from physics/chemistry into social science (LLMs predicting experiment outcomes) and ecology. It moves the failure of expensive experiments forward into a few dollars of inference.
3. A counter-intuitive meta-science result: **distant interdisciplinary recombination is *negatively* correlated with disruption**; papers that displace old paradigms share 52% field overlap with what they challenge. "Same problem, better solution" beats "novel combination." This directly amends the usual "innovate by crossing fields" advice.
4. My three low-cost, high-potential routes: **(A) evaluator-first**: write an auto-scoring evaluator for one forestry/environment question, then let search/agent loops run; **(B) global synthesis on open gridded data with an equity lens** (the Nat. Commun. 2026 trees-vs-urban-heat paper is the template, cost $0); **(C) audit automated science**: AI-scientist systems have been shown to cherry-pick benchmarks and leak data, and nobody has done this audit in ecology yet.

---

## 1. 我这次看到了什么 / What I found this pass

| 来源 Source | 要点 Highlight | 我读出的模式 Pattern I read |
|---|---|---|
| ✅ Science 2025 年度突破 | 年度第一是**可再生能源的不可阻挡崛起**（中国规模化让清洁能源全球廉价）；亚军含个性化 CRISPR 婴儿疗法、抗淋病新抗生素、神经细胞向肿瘤输送线粒体、Rubin 望远镜、丹尼索瓦人头骨、**LLM 加速科研**、缪子磁矩异常、猪器官异种移植约 9 个月、**耐热稻基因**。 | 规模化本身就是突破；挖掘天然变异 / scale as breakthrough; mining natural variation |
| ✅ MIT TR 2026 十大 | 钠离子电池、生成式编程、下一代核能、AI 伴侣、碱基编辑婴儿、**基因复活**（灭绝物种基因库）、**机制可解释性**、商业空间站、胚胎评分、超大规模 AI 数据中心。 | 丰度替代（钠代锂）、打开黑箱 / abundance substitution, opening black boxes |
| ✅ Nature's 10 (2025) | 含 Achal Agrawal（揭露印度高校高撤稿率）、Mengran Du（最深动物生态系统）、Luciano Moreira（在巴西量产抗病蚊）、梁文锋（DeepSeek）、KJ Muldoon（首个定制 CRISPR 疗法）。 | 元科学/诚信本身是创新点；开源低成本模型 / integrity as innovation; open low-cost models |
| ✅ Physics World 2025 十大 | 含 **基于安卓手机的全球地震预警网**、活细胞内的蛋白质量子比特、空芯光纤破 40 年损耗极限、单原子最高分辨成像。 | 消费设备即行星级传感器 / consumer devices as planetary sensors |
| ✅ CAS 2026 趋势 | 混合太阳能、钠通道非阿片镇痛、纺织回收、AI 生物标志物、替代电池、CRISPR 抗旱作物、**无细胞生物制造用于即时诊断**、IoT+自愈涂层基础设施。 | 无细胞/去中心化制造 / cell-free, decentralized manufacturing |
| ✅ AlphaEvolve (arXiv 2511.02864) | 67 个数学问题，多数复现最优解、若干问题**改进已知最优**，能把有限输入的结果推广成通式。机制：LLM 生成代码 + **自动评估** + 进化迭代。 | 评估器优先 / evaluator-first |
| ⚠️ Nature 2026 LLM 预测社会科学实验 | 斯坦福团队：LLM 对大量已发表实验的效应方向/大小预测与真实结果高度相关（正文被限流，数值未核）。 | 硅内先导实验 / in-silico pilot |
| ✅ 《自动化越多，看见越少》(arXiv 2509.08713) | 两个 AI 科学家系统被审计：82% 场合按列表顺序选基准；未披露的子采样/合成数据；按提示顺序选指标；被操纵时 49% 选最差候选。只看论文只能查出 51%，看日志能到 74%。 | 审计自动化 / audit the automation |
| ✅ 元科学 (arXiv 2506.15959) | 非典型组合与颠覆性**稳健负相关**（跨领域、跨时代、跨团队规模）；颠覆性论文与其挑战对象 52% 同领域（随机的 37 倍）；概念突破来得快，方法突破取代旧方法慢。 | 同一问题更好解法 / same problem, better solution |
| ✅ Nature Comms 2026 树木与城市热岛 | 8,919 个城市、36 亿人：树冠已抵消 41–49% 的最大潜在热岛，人口加权仅降 0.15 °C；高收入国家 0.23 °C，低收入 0.08 °C；即使极限扩绿也只抵消本世纪中叶变暖的约 20%。数据全部公开（ESA WorldCover、LandScan、CMIP6）。 | 开放格网数据全球综合 + 公平性 / open-data global synthesis + equity |
| ✅ 土壤真菌与森林碳 | 真菌群落组成可在大陆尺度预测森林碳储量（Nat. Commun.）；AMF + 生物炭增强土壤碳稳定（Sci. Rep. 2025）。 | 隐性变量成为预测器 / hidden variables as predictors |
| ✅ 木质素增值 | 2025–2026 多篇综述：从燃料转向芳烃、材料、碳材料；"工业转型"叙事增强。 | 负债变资产（与 Opus 重合）/ liability→asset |
| ✅ 农业 | CRISPR 改造有益菌/真菌；植物微生物组"从接种到基因编辑"；CRISPR 介导的水平基因转移造新作物。 | 生物即平台（与 Opus 重合）/ biology as platform |
| ✅ 机器人 | 世界-动作模型（World-Action Models）：先在视频上预训练"想象"，再微调"行动"。 | 基础模型 + 微调（与 Opus 重合）/ FM + fine-tune |

---

## 2. 我独立提炼的共性模式 / Patterns I extracted independently

**F1 评估器即护城河 / The evaluator is the moat**
中文：AlphaEvolve、蛋白设计、Robin 的 LLM 裁判，共同前提是"有一个便宜、可自动运行、够可信的打分函数"。有了它，搜索就能外包给机器；没有它，再强的模型也只能生成猜想。
English: AlphaEvolve, protein design and Robin's LLM judge all presuppose a cheap, automatic, trustworthy scoring function. With it, search can be outsourced to machines; without it, even the best model only produces conjectures.

**F2 硅内先导 / In-silico pilot**
中文：用模型先"预演"实验（社会科学的 LLM 预测、气候的 FM 参数化、材料的虚拟筛选），把昂贵实验的一部分失败提前到几美元的推理上。
English: Rehearse the experiment in a model first (LLM predictions in social science, FM parameterizations in climate, virtual screening in materials), moving part of the failure cost of expensive experiments into cents of inference.

**F3 同一问题、更好解法 / Same problem, better solution**
中文：元科学证据表明，颠覆来自正面挑战主导解法，而非把它拼到远处的领域。跨界拼接更多是"巩固"而不是"取代"。
English: Meta-science evidence says disruption comes from directly challenging the dominant solution, not from splicing it onto a distant field. Cross-field splicing mostly consolidates rather than displaces.

**F4 规模与丰度即突破 / Scale and abundance as the breakthrough**
中文：Science 把年度突破给了"部署"而不是"发明"；钠离子电池的意义是"用海量便宜元素替代稀缺元素"。
English: Science gave its top prize to deployment, not invention; sodium-ion matters because it swaps a scarce element for an abundant one.

**F5 消费设备即行星传感器 / Consumer devices as planetary sensors**
中文：安卓地震预警把数十亿部手机变成地震仪网络。同类逻辑：手机 LiDAR、手机麦克风、汽车摄像头。
English: Android earthquake alerts turn billions of phones into a seismometer network. Same logic: phone LiDAR, phone microphones, car cameras.

**F6 开放格网数据的全球综合 + 公平性维度 / Global synthesis on open gridded data, with an equity lens**
中文：树木-热岛论文全部基于公开数据，新意在"全球尺度 + 谁受益"。公平性维度是当前审稿人和资助方都在找的角度。
English: The trees-vs-heat paper used only open data; the novelty was "global scale + who benefits." The equity dimension is what reviewers and funders are currently looking for.

**F7 挖掘天然变异与古基因 / Mining natural variation and ancient genes**
中文：耐热稻基因来自自然变异；"基因复活"从灭绝物种找线索。成本低于从头设计。
English: The heat-resistant rice gene came from natural variation; "gene resurrection" mines extinct species. Cheaper than de novo design.

**F8 审计自动化 / Audit the automation**
中文：AI 科学家系统被证明会系统性地作弊（非故意），撤稿率曝光者入选 Nature's 10。谁能提供"可信度"，谁就有位置。
English: AI-scientist systems have been shown to systematically (if unintentionally) cheat; a retraction-rate whistleblower made Nature's 10. Whoever supplies trust has a seat.

---

## 3. 抽象出的创新方法（Fable 版）/ Abstracted methods (Fable version)

| # | 方法 Method | 一句话操作 How | 成本 Cost |
|---|---|---|---|
| N1 | 评估器优先 Evaluator-first | 先问"这个问题的答案能不能被脚本自动打分？"能，就让代理/进化搜索跑；不能，就先去造评估器（这本身可发表）。 / Ask "can a script score answers?" If yes, run agent/evolutionary search; if no, build the evaluator (publishable itself). | 很低 very low |
| N2 | 硅内先导 In-silico pilot | 做实验前，让模型预测结果并给出置信度；只把模型不确定或与直觉冲突的条件拿去实测。 / Have a model predict outcomes first; only run the conditions where it is uncertain or contradicts intuition. | 几美元 dollars |
| N3 | 正面替换 Head-on replacement | 找一个领域里"大家都在用但都在抱怨"的默认方法，给出更简单/更准的同功能替代。 / Find the default method everyone uses but complains about; offer a simpler or more accurate drop-in. | 低 low |
| N4 | 丰度替代 Abundance substitution | 列出你领域里的稀缺输入（稀有样本、昂贵仪器、专家时间），逐个问"能不能用海量便宜的东西替代？" / List scarce inputs and ask for each: can something abundant and cheap replace it? | 低 low |
| N5 | 口袋传感网 Pocket sensor network | 把已经在人们口袋/车上的传感器组织成数据集。 / Organize sensors already in pockets and cars into a dataset. | 低 low |
| N6 | 全球综合 + 谁受益 Global synthesis + who benefits | 拿公开格网数据做全球/大陆尺度回答，并且分收入/地区报告效益分配。 / Answer at global/continental scale with open gridded data, and report the distribution of benefits. | $0 |
| N7 | 挖存量变异 Mine standing variation | 在种质库、老样本、灭绝物种数据里找已经存在的解。 / Look for solutions already present in germplasm banks, archived samples, extinct-species data. | 低-中 low-mid |
| N8 | 审计自动化 Audit the automation | 挑一个正在被 AI 自动化的科研环节，用日志级证据量化它的系统性偏差。 / Pick a research step being automated by AI and quantify its systematic bias with log-level evidence. | 很低 very low |

---

## 4. 低成本可尝试方向 / Low-cost directions to try

| # | 方向 Direction | 方法 | 预算 Budget（💭 估计） | 第一步 First step |
|---|---|---|---|---|
| 1 | 为"树种识别/林分类型"写一个公开评估器（Sentinel-2 + FIA 样地），然后让 LLM 代理或进化搜索自动找特征与模型 / Public evaluator for tree-species/stand-type mapping, then let agents search | N1 | $0–50 | 选一个州，定义指标与留出集 / one state, metric + holdout |
| 2 | 用 LLM 预测已发表的森林/生态实验（如施肥、疏伐、火烧）的效应方向，与真实结果比对，复刻社会科学那篇的范式 / Replicate the "LLMs predict experiments" paradigm on forestry/ecology field experiments | N2, N8 | $20–200 API | 收集 100 篇有明确处理-对照的论文 / 100 papers with clear treatment-control |
| 3 | 全球/北美尺度：城市树冠降温效益的**收入分层**分析（复刻热岛论文到县级）/ County-level equity analysis of urban canopy cooling | N6 | $0 | 下载 WorldCover + LandScan + 地表温度 / download the three layers |
| 4 | 审计 AI 科学家系统在生态数据上的行为（基准选择、指标选择、是否泄漏）/ Audit AI-scientist systems on ecological datasets | N8 | $50–300 | 跑 Agent Laboratory/AI Scientist 一次并保留日志 / one run with logs |
| 5 | 手机麦克风众包的"城市鸟鸣/蛙鸣"数据集，参照安卓地震网逻辑 / Crowd-sourced phone-mic urban bird/frog dataset | N5 | 时间为主 mostly time | 先做一个校园试点 App 或用现成 App 数据 / campus pilot or existing app data |
| 6 | 用真菌群落数据预测森林碳，检验"隐性变量"是否优于遥感 / Test whether soil-fungal composition beats remote sensing for carbon prediction | N3 | $0（公开数据）| 用已发表的大陆数据集复现并加对照 / reproduce the continental dataset with a baseline |
| 7 | 木质素增值文献的自动"工艺-产率-成本"抽取与开放数据库 / Auto-extracted lignin valorization process database | N1, N8 | $20–100 | 50 篇起 / start with 50 papers |
| 8 | "丰度替代"清单：在你实验室里列出 5 个稀缺输入，各配一个廉价替代实验 / An abundance-substitution audit of your own lab | N4 | 视项目 varies | 一小时头脑风暴 / one-hour brainstorm |

---

## 5. 我推荐的高潜力方向 / My high-potential picks

### ⭐ A. 评估器优先的林业/环境 AI 搜索 / Evaluator-first AI search for forestry & environment
**中文**：AlphaEvolve 和蛋白设计说明，只要有可信的自动评估器，AI 就能在几天内跑过人类几年的试错。林业与环境科学里大量问题（生物量估计、物种分布、火险指数、材性预测）都有公开数据可以构造评估器，但几乎没人把"评估器 + 搜索循环"当成一个研究范式来做。**为何高潜力**：成本极低；评估器本身可发表；一旦跑通就是可复用基础设施。**风险**：评估器写歪了，搜索就会"高分低能"（Goodhart），这恰是与 ⭐C 的结合点。
**English**: AlphaEvolve and protein design show that with a trustworthy automatic evaluator, AI can run through years of human trial-and-error in days. Many forestry/environment problems (biomass, species distribution, fire indices, wood property prediction) have open data from which evaluators can be built, yet almost nobody treats "evaluator + search loop" as a research paradigm. **Why**: near-zero cost; the evaluator is publishable on its own; once working it is reusable infrastructure. **Risk**: a mis-specified evaluator yields Goodhart-style high-score/low-value results, which is exactly where ⭐C plugs in.

### ⭐ B. 开放格网数据的全球综合 + 公平性 / Open-data global synthesis with an equity lens
**中文**：树木-热岛论文证明了这条路能直接上 Nature Communications：全公开数据、全球尺度、加上"谁受益"。可直接迁移的题目：城市树冠的空气污染/洪涝/心理健康效益分配、森林碳汇收益的地区分配、野火烟雾暴露的人群不平等。**为何高潜力**：$0 成本、审稿人与资助方都在找这个维度、与 ESF 学科高度契合。
**English**: The trees-vs-heat paper shows this route reaches Nature Communications with fully open data, global scale and a "who benefits" angle. Directly transferable topics: distribution of canopy benefits for air pollution, flooding or mental health; regional distribution of forest-carbon benefits; population inequality in wildfire-smoke exposure. **Why**: $0 cost; reviewers and funders want this dimension; strong fit with ESF.

### ⭐ C. 审计自动化科学（生态/环境版）/ Auditing automated science, ecology edition
**中文**：AI 科学家系统已被证明存在系统性偏差，而生态学数据（空间自相关、类别极不平衡、时间泄漏）恰恰是这些系统最容易踩坑的地方。做一个"生态学 AI 科学家审计基准"，既是验证科学，也是方法论贡献。**为何高潜力**：几乎无人做、成本低、话语权高。
**English**: AI-scientist systems have documented systematic biases, and ecological data (spatial autocorrelation, extreme class imbalance, temporal leakage) is exactly where they fail most easily. An "ecology AI-scientist audit benchmark" is both validation science and a methods contribution. **Why**: nearly nobody is doing it, cheap, and high leverage.

### 优先级矩阵 / Priority matrix

| 方向 | 成本 Cost | 首个结果 | 新颖度 | 拥挤度 |
|---|---|---|---|---|
| ⭐A 评估器优先 | 很低 | 2–3 周 | 高 | 低 |
| ⭐B 全球综合+公平 | $0 | 3–5 周 | 中高 | 低-中 |
| ⭐C 审计 AI 科学家 | 很低 | 2–4 周 | 高 | 很低 |

---

## 6. 与 Opus 报告的逐条对比 / Item-by-item comparison with the Opus report

### 6.1 一致的地方 / Where we agree
- **基础模型 + 小数据微调**、**闭环**、**传感器降本**、**旧资产新用途**、**生物/天然材料为平台**、**验证成为瓶颈**：这六条我在不同来源里独立看到了同样的信号，可视为**稳健结论**。 / FM + fine-tune, closed loops, sensor cost collapse, repurposing, biology as platform, verification bottleneck: I saw the same signals independently from different sources, so treat these six as **robust**.
- 都认为 **MRV/验证科学** 是低成本高杠杆方向。 / Both rank MRV/verification science as low-cost, high-leverage.
- 都认为对个人研究者而言，**价值在于拥有细分数据和问题，而不是训练模型**。 / Both say the individual's edge is owning niche data and questions, not training models.

### 6.2 我看到而 Opus 没强调的 / What I saw that Opus did not emphasize
1. **评估器即护城河（F1/N1）**：Opus 把 AlphaEvolve 类工作归入"闭环"，我认为应单独拎出——闭环能否成立取决于评估器，而评估器是个人研究者最容易造、最容易发表的部件。 / Opus folds AlphaEvolve-style work into "closed loop"; I separate it: whether a loop works depends on the evaluator, and the evaluator is the part an individual can most easily build and publish.
2. **硅内先导（F2/N2）**：LLM 预测社会科学实验结果这条线 Opus 没有覆盖，它把"先导实验"成本压到几美元，对田间实验缓慢的生态学尤其重要。 / The "LLMs predict experiments" line was absent from Opus; it pushes pilot cost to dollars, which matters most where field experiments are slow, like ecology.
3. **元科学证据修正"跨界"建议（F3）**：Opus 的 M5"跨域移植"是它三大推荐之一的基础；元科学数据显示远距离拼接与颠覆性负相关。我不否定移植，但建议改写为"把 A 领域的方法带到 B 领域，**正面替换** B 领域现有的默认方法"，而不是做一个新奇组合。 / Opus's M5 "cross-domain transplant" underpins its #1 pick; meta-science shows distant recombination is negatively tied to disruption. I do not reject transplanting, but reframe it: bring A's method into B to **replace B's default head-on**, rather than to make a novel combination.
4. **规模/丰度即突破（F4）与消费设备传感网（F5）**：Opus 有"聚合分布式"，但没有把"用海量便宜元素替代稀缺输入"当作方法。 / Opus has "aggregate the distributed" but not "substitute scarce inputs with abundant ones" as a method.
5. **公平性维度（F6）**：Opus 完全没有提。对当前审稿与资助口味而言，这是几乎零成本的加分项。 / Opus never mentions equity. For current review and funding tastes it is a near-zero-cost differentiator.
6. **审计自动化科学（F8）**：Opus 的 M6"做验证者"针对的是 ERW、BirdNET 这类实证宣称；我把矛头指向 AI 科学家系统本身，证据（arXiv 2509.08713）显示它们有可量化的系统性偏差。 / Opus's "be the validator" targets empirical claims like ERW and BirdNET; I aim at the AI-scientist systems themselves, where documented biases exist.

### 6.3 Opus 看到而我这轮没覆盖的 / What Opus covered that I did not
- eDNA + 纳米孔、BirdNET 逐物种误差、ERW 田间试验细节、透明木材/辐射制冷木材、菌丝体-生物炭建材、节俭显微镜。这些是它检索更"贴近 ESF"的收获，我认为**仍然成立**，尤其 ERW 结果的负面证据很有价值。 / eDNA + nanopore, per-species BirdNET error, ERW trial details, transparent/radiative-cooling wood, mycelium-biochar building materials, frugal microscopes. These come from its more ESF-adjacent search and **still hold**, especially the negative ERW evidence.

### 6.4 推荐排序的差异 / Differences in ranking

| 主题 | Opus 排名 | Fable 排名 | 我的理由 / My reasoning |
|---|---|---|---|
| 生态/林业 AI 科研代理 | ⭐1 | 并入 ⭐A | Robin 的闭环依赖湿实验反馈，生态学田间反馈太慢；把它改造成"评估器 + 对公开数据的搜索"才能真正跑起来，否则只剩文献综述代理。 / Robin's loop needs wet-lab feedback; ecology's field feedback is too slow. Recast as evaluator + search over open data, or it degrades to a literature-review agent. |
| 多模态低成本森林体检 | ⭐2 | 未列入前三 | 我认同方向，但它需要多台设备、多人协调与野外时间，"低成本"更多指资金而非时间；作为第二阶段更合适。 / Sound, but needs hardware, coordination and field time; low in money, not in time. Better as a phase two. |
| MRV 验证科学 | ⭐3 | 与 ⭐C 合并 | 都赞成；我把范围从"验证碳汇宣称"扩到"验证 AI 生成的科学结论"，后者更空白。 / Agree; I widen from verifying carbon claims to verifying AI-generated science, which is emptier. |
| 开放数据全球综合 + 公平 | 未列 | ⭐B | 这是我认为 Opus 最大的遗漏：$0、已有 Nature Comms 级模板、与 ESF 高度匹配。 / Opus's biggest miss, in my view: $0, a Nat. Commun.-level template exists, strong ESF fit. |
| 木材/纤维素功能材料 | 备选 4 | 备选 | 一致：好方向但需要实验室与中等预算。 / Agree: good but needs a lab and medium budget. |

### 6.5 给 Salem 的一句话判断 / One-line verdict for Salem
**中文**：两份报告在"模式层"高度一致（说明这些模式是真的），在"方法层"互补（Opus 偏工具与传感，我偏评估器、硅内先导与审计），在"推荐层"的最大分歧是：我会先做 **$0 的开放数据综合（B）** 和 **评估器（A）**，把 Opus 的多模态野外方案放到第二阶段。
**English**: The two reports agree strongly at the *pattern* level (a sign the patterns are real), complement each other at the *method* level (Opus leans tools and sensing; I lean evaluators, in-silico pilots and audits), and diverge most at the *recommendation* level: I would start with the **$0 open-data synthesis (B)** and the **evaluator (A)**, and move Opus's multimodal field plan to phase two.

---

## 7. 来源 / Sources
- Science 2025 Breakthrough of the Year: https://www.science.org/content/article/breakthrough-2025 ；runners-up 摘要 via https://gigazine.net/gsc_news/en/20251225-science-2025-breakthrough/
- MIT Technology Review 10 Breakthrough Technologies 2026: https://www.technologyreview.com/2026/01/12/1130697/10-breakthrough-technologies-2026/
- Nature's 10 (2025): https://www.nature.com/immersive/d41586-025-03848-1/index.html
- Physics World Top 10 Breakthroughs 2025: https://physicsworld.com/a/top-10-breakthroughs-of-the-year-in-physics-for-2025-revealed/
- CAS 2026 emerging trends: https://www.cas.org/resources/cas-insights/scientific-breakthroughs-2026-emerging-trends-watch
- AlphaEvolve, mathematical exploration at scale: https://arxiv.org/abs/2511.02864
- ⚠️ LLMs can predict the results of social science experiments (Nature 2026): https://www.nature.com/articles/s41586-026-10742-x ; Stanford summary: https://ai4pb.stanford.edu/projects/predicting-results-of-social-science-experiments-using-large-language-models
- The More You Automate, the Less You See (AI scientist pitfalls): https://arxiv.org/html/2509.08713v1
- Can Recombination Displace Dominant Scientific Ideas?: https://arxiv.org/pdf/2506.15959
- Trees halve urban heat island effect globally but unequal benefits (Nat. Commun. 2026): https://www.nature.com/articles/s41467-026-71825-x
- ⚠️ Global data-driven prediction of fire activity (Nat. Commun. 2025): https://www.nature.com/articles/s41467-025-58097-7
- Fungal community composition predicts forest carbon storage at continental scale: https://www.nature.com/articles/s41467-024-46792-w
- AMF + biochar soil carbon stabilisation (Sci. Rep. 2025): https://www.nature.com/articles/s41598-025-23219-0
- Lignin valorization review (2025): https://link.springer.com/article/10.1186/s40643-025-00929-x
- Plant microbiome engineering, inoculation to genome editing: https://pmc.ncbi.nlm.nih.gov/articles/PMC13144036/
- World-Action Models (NVIDIA): https://developer.nvidia.com/blog/pretrained-to-imagine-fine-tuned-to-act-the-rise-of-world-action-models/
- Sodium-ion batteries (MIT TR 2026): https://www.technologyreview.com/2026/01/12/1129991/sodium-ion-batteries-2026-breakthrough-technology/
- Are GLP-1s the first longevity drugs? (Nat. Biotechnol.): https://www.nature.com/articles/s41587-025-02932-1
- Opus 版报告 / Opus report: `/mnt/project-files/innovation-survey/前沿创新点综述_Frontier_Innovation_Survey.md`
