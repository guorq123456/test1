# 卡池、数据源与已有项目

> 整理日期 2026-10-05。数量统计来自官方卡牌接口的数据（`is_include_rotation` 等字段），梯度榜和卡表来自 Game8 / GameWith，均注明日期。

## 1. 卡包一览

| # | 中文名 | 英文名 | 发售（日本时间） | 卡数 |
|---|---|---|---|---|
| — | 基础卡 | Basic Cards | 2025-06-17 | 56 |
| 1 | 传说揭幕 | Legends Rise | 2025-06-17 | 142 |
| 2 | 无限进化 | Infinity Evolved | 2025-07-17 | 77 |
| 3 | 灾杰的继承者 | Heirs of the Omen | 2025-08-28 | 77 |
| 4 | 苍穹六龙 | Skybound Dragons | 2025-10-29 | 76 |
| 5 | 花醉游戏 | Blossoming Fate | 2025-12-29 | 76 |
| 6 | 天启契约 | Apocalypse Pact | 2026-02-26 | 76 |
| 7 | 弑神之安纳提玛 | Anathema's Gambit | 2026-04-28 | 77 |
| 8 | 命运编年史 | Chronicle of Destiny | 2026-06-29 | 78 |
| 9 | 复苏的阿兹弗特 | Revenants of Azvaldt | 2026-08-27 | 76 |
| 衍生物 | — | Tokens（set 90000） | — | 93 |

官方接口里的卡包编号：10000 是基础卡，10001–10009 对应第 1–9 弹，90000 是衍生物。

## 2. 指定系列：规则与当前范围
- **规则**：最新 6 个卡包 + 基础卡；每出一个新卡包，最老的卡包退出。从 2026-04-28 第 7 弹开始实行。
- **当前范围**：基础卡 + 第 4–9 弹。第 1 弹的「暴风破 / Stormy Blast」在第 8 弹重印过，所以也合法。
- **下一次轮换**：第 10 弹。截至 2026-10-05 官方还没公布，按两个月左右一弹的节奏推测在 10 月底；届时第 4 弹《苍穹六龙》退出。**模拟器的卡牌数据要按卡包版本管理**，轮换和平衡调整都会改变卡牌。
- 最近一次平衡调整是 2026-09-29：加强了海盗皇家和单卡超越者（Highlander Portal）的若干卡牌，削弱了魔手巫师的「魔恋の天晶」（3 费 → 4 费）。

## 3. 卡池规模与封闭性分析

| | 中立 | 每个职业 | 合计 |
|---|---|---|---|
| 指定系列可用卡 | 46 | 67 | 515 |
| 一个职业能用的牌 | | | 67 + 46 = 113 |
| 能产生的衍生物 | | | 56 |

按卡牌类型：随从 369、法术 118、护符 15、吟唱护符 13。

**结论：卡池是封闭的。** 研究助手对全部 571 条记录（515 张卡 + 56 个衍生物）检索了英文和日文卡面，**没有找到任何从全卡池随机生成卡牌的效果**。卡池之外的牌只可能通过下面几类效果进入对局，而这些牌全都在"双方卡组 + 衍生物"的范围之内：

| 类别 | 例子 | 对模拟器的影响 |
|---|---|---|
| 复制对手的牌 | 脚踩天穹的《倒吊人》·罗弗拉德（复制对手牌组里的 5 张）、被侵略的世界、救世的英姿、温泉度假猴、星晶兽吸收之力、“最强”的诱惑 | 手里可能出现对手职业的牌，所以**两套卡组的脚本要同时实现** |
| 复制自己的牌 | 从自己牌组、手牌、战场、本局被破坏的随从中复制或召唤 | 封闭 |
| 变身成固定的牌 | 变成骷髅、指定衍生物、神器融合链 | 封闭 |
| 在固定选项里随机 | 随机发动几个固定效果之一 | 封闭，只是需要随机数 |

所以，实现一组对局，只需要实现两套卡组里的牌加上它们的衍生物。神经网络的卡牌词表也是固定的。

## 4. 当前环境与建议的起步卡组

**梯度榜**（两家都在 2026-10-05 更新）
- **Game8 T1**：海盗皇家、谢幕曲梦魇、斜坡龙、连击精灵
- **GameWith T1**：斜坡龙、连击精灵、单卡超越者（Highlander Portal）、海盗皇家

**建议的第一组对局：海盗皇家 vs 斜坡龙。**
- 两者在两个榜上都是 T1，机制有代表性（衍生物、模式、爆能强化、涨 PP、纹章、计数）。
- 没有魔力增幅、土之秘术、融合这类需要额外系统的机制。
- 一共约 29 种牌 + 约 10 个衍生物。

卡表来自 Game8（2026-09-30 / 2026-10-05），已经用官方卡组接口解码核对；中文卡名取自官方简体中文数据。

### 海盗皇家（Pirate Sword）：40 张，14 种

| 张数 | 费用 | 中文名 | 英文名 |
|---|---|---|---|
| 3 | 1 | 须臾剑士 | Flashstep Quickblader |
| 3 | 1 | 无音的包围 | Orchestrated Silence |
| 3 | 2 | 古旧天剑·伊德梅塔 | Yidmetra, Eld Sword |
| 3 | 2 | 海域斥候 | Open-Sea Scout |
| 3 | 3 | 漩涡炮手 | Whirlpool Gunner |
| 3 | 3 | 荣耀的丽金花 | Splendor of the Goldbloom |
| 3 | 3 | 燃尽之缘 | Severed Ties |
| 3 | 4 | 真红与群青·塞达&贝阿朵丽丝 | Zeta & Bea, Crimson and Blue |
| 3 | 4 | 黄金时代 | L'Age d'Or |
| 3 | 5 | 丽金花·云庆 | Unkei, Goldbloom |
| 3 | 5 | 波涛副船长 | Roughwater First Mate |
| 3 | 6 | 真王之刃·黄金骑士 | Golden Knight, True King's Blade |
| 3 | 7 | 逆行的罪人·巴巴洛丝 | Barbaros, Rebellious Convict |
| 1 | 10 | 武皇的变貌·贝尔铁佐 | Beltezore, Valorous Revenant |

**衍生物**：令人战栗的海盗旗、黄金短剑、黄金之杯、黄金之靴、黄金项链、闪耀的金币、铁甲骑士、天剑深渊。

### 斜坡龙（Ramp Dragon）：40 张，15 种

| 张数 | 费用 | 中文名 | 英文名 |
|---|---|---|---|
| 3 | 2 | 掌握天空命运的少女·露莉亚（中立） | Lyria, Skydestined |
| 3 | 2 | 古旧天刀·波菈莱 | Vorlalai, Eld Blades |
| 3 | 2 | 宣扬的龙人 | Dragonewt Promoter |
| 2 | 2 | 满面笑容的烹饪·琪米卡 | Kimika, Cook of Happiness |
| 3 | 2 | 懒惰的波摇花 | Sloth of the Crestpetal |
| 3 | 3 | 龙之启示 | Dragonsign |
| 1 | 3 | 焦龙的午睡 | Lazing Flame |
| 2 | 4 | 日珥咆哮 | Roar of Prominence |
| 2 | 5 | 《世界》的呈现（中立） | Fate of the World |
| 3 | 5 | 世界的伙伴·佐伊 | Zooey, Ally of the World |
| 3 | 7 | 断头的斩姬·相枛津 | Sagatsumatsu, Fair Beheader |
| 3 | 7 | 禁牙的变貌·诺玛格达拉 | Normagdala, Ravening Revenant |
| 3 | 8 | 金银绚烂·璐米欧儿&雅尔贞特 | Lumiore & Argente, Shining Wings |
| 3 | 9 | 焦灰的安纳提玛·班德奈特 | Burnite, Anathema of Ash |
| 3 | 10 | 约束的《正义》·伊兰翠 | Erntz, Governing Justice |

**衍生物**：赤流、天刀深渊；另有班德奈特给对手的纹章。

其他职业的主流卡组（连击精灵、谢幕曲梦魇、单卡超越者等），以及各卡组的替换版本，见 Game8 / GameWith 的卡组页面。

## 5. 已有开源项目

| 项目 | 内容 | 协议 / 更新 | 怎么用 |
|---|---|---|---|
| [jacklee12312/SWB-RL](https://github.com/jacklee12312/SWB-RL) | Python 确定性引擎 + PettingZoo/Gym 环境 + PPO 联盟训练 + 人机对战网页。用 JSON DSL 描述卡牌规则，声称 735 张卡和 91 个衍生物全部实现。数据快照是 2026-07-08，**不含第 9 弹**。作者自述"尚未形成强战术" | MIT（游戏内容除外）/ 2026-08-06 | 可以参考规则细节，或者做差分测试；核心结算文件有 1.8 万行，不适合直接改 |
| [jakaline-dev/svwb](https://github.com/jakaline-dev/svwb) | 209 个卡牌类，覆盖约 10 套卡组，数据是 2026-09-22 的（含第 9 弹）。有回合规划器，以及"行为克隆 → DAgger → PPO"的训练流程，还没有训练结果 | **无协议**（只能看，不能拷代码）/ 2026-10-02 | 参考设计思路 |
| [SomostVE/beyond_decks](https://github.com/SomostVE/beyond_decks) | 浏览器里的对战模拟（JS），文本和正则驱动，加上逐卡修正，有全卡覆盖审计 | 无协议 / 2026-08-25 | 参考 |
| [Riemann460/SVsim](https://github.com/Riemann460/SVsim) | 事件驱动引擎，把卡面文字解析成效果 JSON（声称成功率 96.89%），有模糊测试，没有 AI | 无协议 / 2026-06-10 | 反面教材：自动解析有错误（比如把"移除目标的守护"解析成移除自己的） |
| [SomostVE/beyond_codex](https://github.com/SomostVE/beyond_codex) | 每周同步官方数据的规范化 JSON（904 张），有变更日志 | 无协议 / 2026-09-28 | 可以当数据镜像，减少直接请求官方接口 |
| [AutumnCrocus/shadow_sim](https://github.com/AutumnCrocus/shadow_sim) | 初代影之诗的模拟器，有规则型、贪心、MCTS 和神经网络 AI | MIT / 2021-12 | 参考 AI 部分 |

**值得借鉴的做法**（研究助手总结）：
- 卡牌定义和行为分离；数据里有卡没实现时，启动就报错。
- 官方 Q&A 当回归测试。
- 统计哪些卡在运行中从没触发过（运行时覆盖率）。
- 动作空间按"行动类型 → 来源 → 目标"分解，同名手牌去重。
- 搜索时对隐藏信息做确定化，把自己的牌组当作多重集合。
- 用种子保证确定性，支持快照和回放。

Cygames 自己的 AI 设计（[技术博客 2016](https://tech.cygames.co.jp/archives/2853/)、[CEDEC 2016](https://cedec.cesa.or.jp/2016/session/ENG/15387.html)）：有限理性的规划，剪掉"攻击后什么也没击杀"的组合，可调的局面评估函数。

**注意**：GitHub 上有不少"外挂 / 修改器"仓库，疑似垃圾或恶意软件；也有在真实客户端上自动对战的脚本（违反用户协议）。都不要用。

## 6. 法律与使用边界
以下是阅读[用户协议](https://shadowverse-wb.com/en/terms/)（2026-03-30 版）的摘要，不构成法律意见：

- **第 11 条禁止**：外部工具和机器人、反编译和逆向工程、未经授权获取内容或访问服务器。
  → 本项目**只做离线模拟器**，不接入客户端，不解包客户端数据。
- **第 5 条限制**：修改、复制、分发游戏内容。
  → 卡牌数据库只用 `fetch_cards.py` **低频拉取到本地**（`data/raw/` 已在 `.gitignore` 里），**不提交到仓库**，也不分发卡图。
  → 例外：**已经实现的卡**（目前是两套起步卡组）在代码里写死了对战用的数值（卡号、费用、身材、关键词），不包含卡面文字和卡图，和卡牌脚本放在一起。SWB-RL 等开源模拟器也在仓库里附带了卡牌数据。这样测试不依赖下载的数据。
- **粉丝创作指引**（[guideline](https://shadowverse-wb.com/en/guideline/)）：要求注明"与 Cygames 无关"，不得收费。项目 README 里已经注明。

## 7. 数据接口速查
所有接口都不需要登录，语言用请求头 `Lang: en | ja | chs | cht | ko` 指定。响应格式是 `{"data_headers": {"result_code": 1}, "data": {...}}`。

| 用途 | 接口 |
|---|---|
| 按卡包获取全部卡牌 | `GET /web/CardSet/cardList?card_set_id=10009` |
| 卡牌检索（每页 30 张） | `GET /web/CardList/cardList?offset=N&battle_format=1`（1 = 指定系列） |
| 单卡详情和衍生物 | `GET /web/CardList/card?card_id=N` |
| 某职业的全部可用卡 | `GET /web/DeckBuilder/cards?class=0,{职业}&battle_format=1` |
| 官方词汇表 | `GET /web/System/glossaryList` · `GET /web/System/abilityKeywordList` |
| 解码卡组 | `GET /web/DeckBuilder/deckHashDetail?hash=…` |

**卡牌记录的关键字段**：
- `common`：`card_id`、`name`、`cost`、`atk`、`life`、`type`（1 随从 / 2 护符 / 3 吟唱护符 / 4 法术）、`class`（0 中立 … 7 超越者）、`rarity`、`card_set_id`、`skill_text`、`questions`（官方 Q&A）、`is_token`、`is_include_rotation`。
- `evo`：只有文字和卡图，没有身材字段。
- 关联关系：`cards[id].related_card_ids` 是衍生物；`specific_effect_card_ids` 是激奏 / 结晶 / 纹章形态，对应另一张"特殊效果卡"。

**卡面标记**：
- `<hr>` 分隔不同能力；
- `<ev>…</ev>` 是进化时能力，`<sev>…</sev>` 是超进化时能力；
- `<ridx=N>` 是模式选项；
- `<b><color=Keyword>…</color></b>` 是关键词。

**卡组哈希**：格式是 `{赛制}.{职业}.{40 个 4 字符的卡牌编码}`。每个编码是 card_id 的 64 进制写法，字母表为 `0-9A-Za-z-_`，高位在前。分享链接是 `https://shadowverse-wb.com/{lang}/deck/detail/?hash=…`。卡组代码是 4 位数字，**只是临时的**；导入卡组请用哈希。
