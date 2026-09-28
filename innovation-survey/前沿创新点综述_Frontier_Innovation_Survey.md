# 前沿创新点综述：共性模式、创新方法与低成本方向
# Frontier Innovation Survey: Shared Patterns, Reusable Methods, Low-Cost Directions

*2026-09-28 · 为 Salem 准备 / prepared for Salem*

---

## 0. 一页结论 / TL;DR

**中文**
- 过去 3–5 年，几乎所有领域的突破都落在同一组"重合点"上：**预训练基础模型 + 小数据微调**、**生成→验证→学习的闭环**、**传感成本断崖式下降带来的高密度数据**、**旧资产新用途（老药、废料、存量数据）**、**以生物/天然材料为工厂**、以及**测量与验证（MRV）本身成为瓶颈**。
- 由此抽象出 7 个可复用创新方法（第 3 节）。其中最省钱的三招是：**"便宜传感器 × 开源预训练模型 × 细分场景"**、**"旧数据问新问题"**、**"做别人热点的验证者"**。
- 我最推荐的高潜力方向（成本低、竞争仍少、与你的环境/林业背景契合）：
  1. **环境/林业领域的 AI 科研代理（AI co-scientist）**：生物医学已有 Nature 论文，生态林业几乎空白，每轮成本约 10 美元级别。
  2. **多模态低成本森林"体检"**：手机 LiDAR + 声学 + eDNA + 免费卫星 + 地理基础模型，做样地级数字孪生。
  3. **自然碳汇/生物多样性的 MRV 验证科学**：市场急需"可信测量"，而最新大型实验显示很多宣称效果被高估。

**English**
- Across fields, recent breakthroughs converge on the same few overlaps: **pretrained foundation models + small-data fine-tuning**, **closed generate→test→learn loops**, **dense data from collapsing sensor costs**, **new uses for old assets (old drugs, waste streams, existing datasets)**, **biology/natural materials as factories**, and **measurement & verification (MRV) as the new bottleneck**.
- I abstract these into 7 reusable innovation methods (Section 3). The three cheapest: **"cheap sensor × open pretrained model × niche problem"**, **"ask old data a new question"**, and **"be the validator of someone else's hype."**
- My top high-potential picks (low cost, still uncrowded, fits an environmental-science/forestry background):
  1. **An AI co-scientist for environmental/forest science**: biomedicine already has a Nature paper; ecology/forestry is nearly empty; ~US$10 per discovery cycle.
  2. **Multimodal low-cost forest "check-ups"**: phone LiDAR + acoustics + eDNA + free satellite imagery + geospatial foundation models, building plot-scale digital twins.
  3. **Verification science (MRV) for nature-based carbon and biodiversity**: markets need trustworthy measurement, and recent large trials show many claimed effects are overstated.

---

## 1. 检索范围与可信度说明 / Scope and Confidence

**中文**：本次用约 20 组网络检索覆盖了 AI for Science、自主实验室、生物设计、材料（木材/纤维素/菌丝体）、地球观测、生物多样性监测（eDNA、声学）、碳移除、药物重定位、开源/节俭硬件，以及 WEF 2026 十大新兴技术。标 ✅ 的结论我读过原文摘要或权威页面核实；标 💭 的是基于我已有知识的推断，请在用之前再核对。这不是系统综述，而是一次"广而浅"的扫描，目的是找模式而非穷尽文献。

**English**: About 20 web searches covered AI for Science, self-driving labs, generative biology, materials (wood/cellulose/mycelium), Earth observation, biodiversity monitoring (eDNA, acoustics), carbon removal, drug repurposing, frugal/open hardware, and the WEF 2026 Top-10 list. ✅ = checked against the source page or abstract; 💭 = inferred from my prior knowledge, verify before relying on it. This is a broad, shallow scan for patterns, not a systematic review.

---

## 2. 各领域快照 / Field Snapshots

| 领域 Field | 近期代表进展 Recent highlights | 体现的模式 Pattern |
|---|---|---|
| AI 科研代理 AI scientists | ✅ Nature 2026 "Robin" 多代理系统：文献代理+数据分析代理闭环，为干性黄斑变性提出已上市药 ripasudil 的新用途；551 篇文献 30 分钟读完（约 200 倍提速），**每轮约 $10.76**。局限：多步生信流程准确率仅 15%。Google "Co-Scientist" 亦登 Nature 2026。 / Robin multi-agent loop repurposed ripasudil for dry AMD; 551 papers in 30 min; ~$10.76 per cycle; weak on multi-step bioinformatics (15%). | 闭环、旧药新用 / closed loop, repurposing |
| 自主实验室 Self-driving labs | ✅ 2026 年 C&EN 与 RSC "SDL 2.0" 综述：化学/材料已从"自动化"走向"自主"，但多篇评论强调硬件昂贵、通用性差，"hype vs reality"。 / SDLs moving from automation to autonomy; hardware cost and generality remain the gap. | 闭环 / closed loop |
| 蛋白与酶设计 Protein design | ✅ RFdiffusion2（Nature Methods）原子级活性位点搭建；Nature 2025 通过催化基序搭建进行计算酶设计；Nature 2026 de novo 设计回顾。工具开源。 / Atom-level enzyme scaffolding, open tools. | 基础模型、生成→验证 / FM, generate→test |
| 地球观测 Earth observation | ✅ NASA/IBM Prithvi 成为首个在轨运行的地理基础模型；IBM 发布 TerraMind/Prithvi "tiny" 小模型；参数高效微调（PEFT）论文；天气基础模型被微调做气候模式参数化。✅ OpenForest 森林机器学习数据目录。 / Prithvi in orbit; tiny EO models; PEFT; weather FMs fine-tuned for parameterization; OpenForest catalog. | 基础模型+小数据 / FM + small data |
| 生物多样性监测 Biodiversity | ✅ eDNA + 纳米孔测序提升欠发达地区可及性；有论文专门提出资源受限条件下的 eDNA 流程权衡框架。✅ BirdNET 被微调用于阿尔卑斯森林；2026 年论文指出 BirdNET/VicFrogNET **性能随物种差异很大**。 / Nanopore eDNA for access; trade-off frameworks; BirdNET fine-tuning; variable performance. | 传感降本、验证 / sensor cost collapse, validation |
| 碳移除 Carbon removal | ✅ 增强岩石风化（ERW）三年田间试验：信号持续但 CO₂ 移除有限；美国中西部试验显示**钢渣有效、玄武岩不明显**。 / ERW 3-yr trials: limited CO₂ removal; steel slag worked, basalt did not. | MRV 瓶颈、废料利用 / MRV bottleneck, waste reuse |
| 木材与纤维素材料 Wood & cellulose | ✅ Nature Reviews Materials 2025 高性能工程木；Advanced Materials 2025 "木材与纤维素是最可持续的先进材料"；透明木材多篇综述。💭 去木质素"降温木材"被动辐射制冷（Science 2019）。 / High-performance engineered wood, transparent wood, 💭 radiative-cooling wood. | 天然材料为平台 / nature as platform |
| 菌丝体/生物炭 Mycelium & biochar | ✅ 2026 年 3D 打印生物炭-菌丝体复合建材；污泥生物炭+菌丝体用于混凝土；菌丝体衍生生物炭平台。 / 3D-printed biochar-mycelium components; biosolids biochar in concrete. | 废料→材料 / waste→material |
| 药物重定位 Drug repurposing | ✅ 2020–2025 AI 重定位综述（COVID、肿瘤）；多篇系统综述。 / AI repurposing reviews. | 旧资产新用途 / old assets |
| 公民科学 Citizen science | ✅ 公民科学记录推动新植物物种发现（2025）；"你的自然照片可能是科学突破"（ScienceDaily 2025）。 / Citizen records → new plant species. | 存量数据再挖掘 / mining existing data |
| 节俭科学 Frugal science | ✅ Nature Communications 2025 "节俭显微镜普及路线图"。 / Roadmap for frugal microscopes. | 传感降本 / cost collapse |
| WEF 2026 十大 Top-10 | ✅ 分布式储能并网、直接提锂、**被动辐射制冷材料**、**PFAS 分解**、**精准发酵**、外泌体递送、个性化 mRNA 癌症疫苗、量子模拟制药、**世界模型**、格密码。WEF 概括："竞争从 AI 转向工厂、医院和电网"。 / Everything-to-grid, DLE, radiative cooling, PFAS destruction, precision fermentation, exosomes, mRNA cancer vaccines, quantum simulation, world models, lattice crypto. | 聚合分布式、破坏而非移除、生物制造 / aggregation, destroy-not-remove, biomanufacturing |

---

## 3. 共性创新模式 / Shared Innovation Patterns

**P1 基础模型 + 小数据微调 / Foundation model + small-data fine-tuning**
中文：大机构花巨资预训练（Prithvi、天气模型、蛋白模型、BirdNET），个人只需少量标注就能迁移到细分问题。价值从"训练模型"转移到"拥有细分数据和问题"。
English: Big institutions pay for pretraining; individuals adapt with little labeled data. Value shifts from *training models* to *owning niche data and questions*.

**P2 生成→验证→学习闭环 / Generate→test→learn loops**
中文：Robin、自主实验室、蛋白设计都把"提出假设—实验—更新"自动化。瓶颈从"想法"变成"验证速度"。
English: Robin, SDLs, and protein design automate hypothesis→experiment→update. The bottleneck moves from ideas to validation throughput.

**P3 传感成本断崖 → 数据密度爆炸 / Sensor cost collapse → data density**
中文：纳米孔 eDNA、AudioMoth 类录音器、手机 LiDAR、节俭显微镜，让以前需要团队和昂贵设备的数据一个人就能采。
English: Nanopore eDNA, cheap acoustic recorders, phone LiDAR, frugal microscopes let one person collect what used to need a team.

**P4 旧资产新用途 / New uses for old assets**
中文：老药新适应症（ripasudil）、钢渣做碳移除、污泥做生物炭、公民科学照片发现新种。风险低，因为资产的其他属性已被验证。
English: Old drugs, steel slag, biosolids, citizen photos. Low risk because the asset's other properties are already validated.

**P5 生物/天然材料作为工厂和平台 / Biology and natural materials as factories**
中文：精准发酵、菌丝体、工程木、透明木、纤维素功能材料。原料便宜、可再生，创新在"结构调控与加工"。
English: Precision fermentation, mycelium, engineered/transparent wood, cellulose. Cheap renewable feedstock; the innovation is in structuring and processing.

**P6 测量与验证成为新瓶颈 / Measurement & verification is the new bottleneck**
中文：ERW 三年试验移除量有限、BirdNET 性能因物种而异、SDL 被批"炒作"。谁能可靠地"证明它有效/无效"，谁就掌握话语权。
English: ERW's limited removal, BirdNET's variable accuracy, SDL hype critiques. Whoever can reliably prove *does it work?* holds leverage.

**P7 聚合分布式资源 / Aggregating the distributed**
中文：电动车并网、公民科学网络、多站点传感网。单点很小，聚合后很大。
English: EVs to grid, citizen-science networks, multi-site sensor meshes. Tiny units, large aggregate.

**P8 "破坏/转化"取代"移除/储存" / Destroy or convert instead of remove or store**
中文：PFAS 分解而非吸附、废料转化为材料。把负债变资产。
English: Break PFAS bonds rather than filter; convert waste into material. Turn liabilities into assets.

---

## 4. 抽象出的可复用创新方法 / Abstracted Reusable Methods

| # | 方法 Method | 公式 Formula | 成本 Cost | 例子 Example |
|---|---|---|---|---|
| M1 | 三件套组合 Triple stack | 便宜传感器 × 开源预训练模型 × 细分场景 / cheap sensor × open pretrained model × niche | 很低 very low | BirdNET 微调到本地森林 / BirdNET fine-tuned for a local forest |
| M2 | 旧数据问新问题 Old data, new question | 公开数据集 + 新假设 + 新方法 / public dataset + new hypothesis + new method | 几乎为零 ~zero | GBIF/iNaturalist → 物候或分布变化 / phenology, range shifts |
| M3 | 闭环化 Close the loop | 把手工迭代变成自动流程（LLM 代理 + 脚本） / automate manual iteration with agents + scripts | 低 low | Robin 每轮 ~$10 / ~$10 per cycle |
| M4 | 负债变资产 Liability → asset | 找本地废料流 → 功能化 / local waste stream → functionalize | 低-中 low-mid | 林业剩余物 → 生物炭-菌丝体 / forest residue → biochar-mycelium |
| M5 | 跨域移植 Cross-domain transplant | 在 A 领域成熟的方法 → 搬到 B 领域的空白 / mature method in A → gap in B | 低 low | 生物医学 AI 代理 → 生态学 / biomedical AI agents → ecology |
| M6 | 做验证者 Be the validator | 挑选热门宣称 → 独立基准/田间对照 / pick a hyped claim → independent benchmark or field control | 低 low | ERW、BirdNET 的误差评估 / error audits of ERW, BirdNET |
| M7 | 做基础设施 Build the commons | 整理数据集/基准/目录供他人用 / curate datasets, benchmarks, catalogs | 低，但回报长期 low, long payoff | OpenForest 数据目录 / catalog |

**中文快速判断法**：一个点子若同时满足"数据或材料免费/便宜 + 模型或方法已开源 + 该细分领域还没人做 + 结果能在 4 周内出第一版"，就值得立刻试。

**English quick test**: an idea is worth trying now if data or materials are free/cheap, the model or method is open, nobody has applied it to that niche yet, and a first result is possible within 4 weeks.

---

## 5. 低成本可尝试方向（10 个）/ Ten Low-Cost Directions to Try

预算按个人研究者估算（💭 推断）/ Budgets estimated for an individual researcher (💭 inferred).

| # | 方向 Direction | 方法 | 预算 Budget | 第一步 First step |
|---|---|---|---|---|
| 1 | 用 Prithvi/TerraMind tiny 小模型检测纽约州森林病虫害（如山毛榉叶病、铁杉球蚜、白蜡窄吉丁）/ Fine-tune tiny geospatial FMs on NY forest pests & diseases | M1, M5 | $0–100（Sentinel-2 免费，Colab GPU）| 下载 Prithvi 权重与 PEFT 代码，找一个已有样地标注 / get weights + PEFT code, find labeled plots |
| 2 | 校园/林场被动声学监测，并做 **分物种 BirdNET 误差审计** / Campus acoustic monitoring with per-species BirdNET error audit | M1, M6 | ~$100–500（2–5 台录音器）| 部署 2 台，录 2 周，人工核对 200 段 / deploy 2 units, 2 weeks, hand-check 200 clips |
| 3 | iPhone LiDAR 测胸径/材积 vs 卷尺与 TLS 的精度评估 / Phone LiDAR vs tape & TLS for DBH/volume | M1, M6 | 已有手机即可 / free with a Pro phone | 选 30 棵树做对照 / 30-tree comparison |
| 4 | GBIF/iNaturalist/eBird 数据挖掘物候或分布北移 / Mine GBIF/iNat/eBird for phenology & range shifts | M2 | $0 | 选一个类群 + 一个气候变量 / one taxon + one climate variable |
| 5 | 用 LLM 代理从文献中抽取"菌丝体复合材料性能数据库"或"木材改性工艺数据库"并开源 / LLM-extracted open property database (mycelium composites or wood modification) | M3, M7 | ~$20–100 API | 先抓 50 篇，人工校验 10 篇 / 50 papers, validate 10 by hand |
| 6 | 本地林业剩余物 → 生物炭-菌丝体砖，测抗压/保温 / Forest residue → biochar-mycelium blocks, test compression/insulation | M4 | ~$200–1000 | 蘑菇菌种 + 模具 + 实验室万能试验机 / spawn, molds, lab testing machine |
| 7 | 去木质素木材做被动辐射制冷的本地化/低成本工艺 💭 / Low-cost delignified wood for passive radiative cooling | M4, P5 | ~$300–1500 | 复现一篇工艺，测表面温差 / replicate one recipe, measure surface ΔT |
| 8 | 溪流 eDNA 纳米孔流程在本地的成本-精度权衡 / Stream eDNA with nanopore: cost-accuracy trade-off locally | M1, M6 | ~$1000–3000 | 借用学校测序平台 / use core facility |
| 9 | 森林碳储量估计的不确定性审计（对比多个免费生物量产品）/ Uncertainty audit of forest carbon maps (compare free biomass products) | M2, M6 | $0 | 选一个县，对比 3 个数据产品 / one county, 3 products |
| 10 | 为某个细分任务做开源基准数据集（如东北阔叶林树种声学/影像）/ Open benchmark for a niche task | M7 | 时间成本为主 / mostly time | 参考 OpenForest 的格式 / follow OpenForest's format |

---

## 6. 我推荐的高潜力方向 / My Recommended High-Potential Directions

### ⭐ 1. 环境与林业的 AI 科研代理 / AI co-scientist for environmental & forest science
**中文**：Robin 与 Co-Scientist 证明了"文献代理+数据代理+实验反馈"的闭环能产生真实发现，且单轮成本约 10 美元。但它们集中在生物医学。生态林业文献分散、数据公开（GBIF、FIA 森林清查、Sentinel），非常适合移植。可做的产品：给定一个生态问题 → 自动汇总机制假设 → 自动在公开数据上做初步检验 → 排序给人类。**为何高潜力**：成本极低、竞争少、可以同时产出论文和工具。**风险**：Robin 显示复杂分析流程准确率低，需要人类把关，这本身也是研究点（M6）。

**English**: Robin and Co-Scientist show that literature agents + data agents + experimental feedback can yield real discoveries at ~$10 per cycle, but they target biomedicine. Ecology and forestry have scattered literature and rich open data (GBIF, FIA, Sentinel), ideal for transplanting. Product: ecological question → auto-synthesized mechanistic hypotheses → quick tests on open data → ranked shortlist for humans. **Why high potential**: very cheap, uncrowded, yields both papers and a tool. **Risk**: Robin's weak multi-step analysis accuracy means human oversight is required, which is itself a research angle (M6).

### ⭐ 2. 多模态低成本森林"体检"与样地数字孪生 / Multimodal low-cost forest check-ups and plot-scale digital twins
**中文**：把手机 LiDAR（结构）、声学（鸟类/蛙类）、eDNA（隐性物种）、Sentinel-2（冠层时间序列）融合，用地理基础模型做对齐。单一模态都有人做，**融合且低成本**的很少。适合做"一个人一周测一块样地"的标准流程。**为何高潜力**：契合 P1+P3+P7，未来可扩展成公民科学网络。

**English**: Fuse phone LiDAR (structure), acoustics (birds/frogs), eDNA (cryptic species), and Sentinel-2 (canopy time series), aligned with geospatial FMs. Each modality is studied alone; **cheap fusion** is rare. Aim for a standard "one person, one week, one plot" protocol. **Why**: combines P1+P3+P7 and can scale into a citizen-science network.

### ⭐ 3. 自然碳汇与生物多样性的 MRV 验证科学 / MRV verification science for nature-based carbon & biodiversity
**中文**：ERW 大型试验显示宣称效果被高估，BirdNET 性能因物种而异，碳信用市场信任危机持续。**"独立、便宜、可重复的测量方法"**需求会越来越大，而且几乎只用公开数据和少量田间对照就能做。**为何高潜力**：政策与市场双驱动，学术和产业都需要。

**English**: ERW trials show overstated benefits, BirdNET varies by species, and carbon markets face ongoing trust issues. Demand for **independent, cheap, reproducible measurement** will grow, and much of it can be done with open data plus small field controls. **Why**: driven by both policy and markets, needed in academia and industry.

### 备选 4. 木材/纤维素/菌丝体功能材料 / Wood, cellulose & mycelium functional materials
**中文**：WEF 2026 把被动辐射制冷列入十大，Advanced Materials 2025 称木材纤维素是最可持续的先进材料。成本中等，需要实验室，但与 ESF 的学科优势高度吻合。
**English**: WEF 2026 lists passive radiative cooling as a top-10 technology; Advanced Materials 2025 calls wood and cellulose the most sustainable advanced materials. Medium cost, needs a lab, but strongly aligned with ESF's strengths.

### 优先级矩阵 / Priority matrix

| 方向 Direction | 成本 Cost | 首个结果 Time to first result | 新颖度 Novelty | 拥挤度 Crowdedness |
|---|---|---|---|---|
| ⭐1 AI 科研代理 | 很低 very low | 1–2 周 weeks | 高 high | 低 low |
| ⭐2 多模态森林体检 | 低 low | 3–6 周 weeks | 中高 mid-high | 低-中 low-mid |
| ⭐3 MRV 验证 | 很低 very low | 2–4 周 weeks | 中 mid | 中 mid |
| 4 功能材料 | 中 mid | 1–3 月 months | 中高 mid-high | 中高 mid-high |

---

## 7. 建议的一周启动计划 / Suggested One-Week Starter Plan

**中文**
- 第 1–2 天：从第 5 节挑 1 个零成本方向（推荐 #4 或 #9），跑出第一张图。
- 第 3–4 天：用 LLM 代理搭一个最小"文献→假设"流程，针对同一问题（对应 ⭐1）。
- 第 5 天：比较代理提出的假设与你的数据结果，记录它对/错在哪。
- 第 6–7 天：写一页纸的研究提案，决定是否投入 ⭐2 或 ⭐3。

**English**
- Days 1–2: pick one zero-cost direction from Section 5 (I suggest #4 or #9) and produce a first figure.
- Days 3–4: build a minimal literature→hypothesis agent for the same question (toward ⭐1).
- Day 5: compare the agent's hypotheses with your data; log where it was right or wrong.
- Days 6–7: write a one-page proposal and decide whether to invest in ⭐2 or ⭐3.

---

## 8. 来源 / Sources

- WEF Top 10 Emerging Technologies 2026: https://www.weforum.org/stories/emerging-technologies/the-top-10-emerging-technologies-of-2026/
- Robin, multi-agent system for automating scientific discovery (Nature 2026): https://www.nature.com/articles/s41586-026-10652-y
- Accelerating scientific discovery with Co-Scientist (Nature 2026): https://www.nature.com/articles/s41586-026-10644-y
- Survey of LLMs in scientific discovery (EMNLP 2025): https://github.com/HKUST-KnowComp/Awesome-LLM-Scientific-Discovery
- Self-driving lab 2.0 (Materials Horizons 2026): https://pubs.rsc.org/mh/article/13/10/4712/1226991/Toward-self-driving-laboratory-2-0-for-chemistry
- Self-driving labs changing chemistry (C&EN 2026): https://cen.acs.org/physical-chemistry/computational-chemistry/Self-driving-labs-changing-chemists/104/web/2026/06
- RFdiffusion2 enzyme scaffolding (Nature Methods): https://www.nature.com/articles/s41592-025-02975-x
- Computational enzyme design by catalytic motif scaffolding (Nature 2025): https://www.nature.com/articles/s41586-025-09747-9
- Past, present and future of de novo protein design (Nature 2026): https://www.nature.com/articles/s41586-026-10328-7
- Prithvi first geospatial FM in orbit (NASA): https://science.nasa.gov/science-research/ai-foundation-model-in-orbit/
- TerraMind/Prithvi tiny models (IBM): https://research.ibm.com/blog/terramind-prithvi-tiny-small-models-geospatial
- PEFT for geospatial FMs: https://arxiv.org/html/2504.17397v1
- Fine-tuning weather FMs for parameterizations (JAMES 2025): https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025MS005075
- OpenForest data catalog: https://www.cambridge.org/core/journals/environmental-data-science/article/openforest-a-data-catalog-for-machine-learning-in-forest-monitoring/F62FBEADFF8E3A10C6EDA789D7D180C6
- eDNA advances (Ecology & Evolution 2026): https://onlinelibrary.wiley.com/doi/10.1002/ece3.72891
- Nanopore eDNA accessibility: https://pmc.ncbi.nlm.nih.gov/articles/PMC12530551/
- eDNA workflow trade-offs in resource-limited settings: https://pmc.ncbi.nlm.nih.gov/articles/PMC12760245/
- BirdNET fine-tuning, Italian Alps: https://doi.org/10.3390/info16080628
- BirdNET/VicFrogNET variable performance (2026): https://www.sciencedirect.com/science/article/pii/S1574954126000506
- ERW three-year field trials (ES&T): https://doi.org/10.1021/acs.est.5c09820
- ERW steel slag vs basalt (OSTI): https://www.osti.gov/pages/biblio/3024684-evidence-carbon-dioxide-removal-via-enhanced-rock-weathering-steel-slag-though-basalt-midwestern-field-trial
- Engineered wood products (Nature Reviews Materials 2025): https://www.nature.com/articles/s41578-025-00865-4
- Wood and cellulose as sustainable advanced materials (Adv. Mater. 2025): https://advanced.onlinelibrary.wiley.com/doi/10.1002/adma.202415787
- Transparent wood review: https://doi.org/10.3390/molecules30071506
- 3D-printed biochar-mycelium composites (2026): https://link.springer.com/article/10.1007/s44223-026-00125-7
- Biosolids biochar + mycelium concretes: https://ascelibrary.org/doi/10.1061/JMCEE7.MTENG-21251
- AI drug repurposing review 2020–2025: https://pmc.ncbi.nlm.nih.gov/articles/PMC13312802/
- Citizen science and new plant species: https://pubmed.ncbi.nlm.nih.gov/40375312/
- Frugal microscopes roadmap (Nat. Commun. 2025): https://www.nature.com/articles/s41467-025-63691-w
- Terrestrial LiDAR in forest research: https://pmc.ncbi.nlm.nih.gov/articles/PMC12501281/
- Forest digital twin via laser scanning (2025): https://phys.org/news/2025-10-digital-twin-forests-laser-scan.html
