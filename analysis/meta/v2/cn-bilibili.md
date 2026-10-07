# CN / Bilibili pass: tournament lists and high-CR creators (pack 9 复苏的阿兹弗特), 2026-10-07

Method:
- I could fetch Bilibili video pages (title, date, uploader, bio, description, tags, related list). The Bilibili search API, the search page, the view API and space pages are all blocked by robots.txt.
- I found new videos by walking the "related videos" lists from page to page.
- Every deck code was decoded locally against `/home/claude/sv/svsim/cards/data/rotation.json` (`zh` names) with `scratchpad/tools/dec.py`.
  - A code that decodes to 40 valid, legal card IDs counts as a check that the summarizer copied it correctly. A garbled token would not land on a real card ID.
  - One code did come back garbled once (the 娅娘 Dragon list had a 3-character token). A second verbatim fetch fixed it.
- Tags: [V2] two fetches or sources agree; [V1] one verbatim fetch; [D] deck code decoded cleanly (40 legal cards); [UNVERIFIED] summarizer-only or my inference.
- Card costs in the decodes come from local data, which already has the post-9/29 values (for example 魔恋的天晶 shows as 4 even in pre-patch lists).

## 0. Key takeaways
1. **The CN official championship happened in pack 9.** SNC 2026 Grand Finals ("Shadowverse NetEase Championship 2026"), 2026-09-19, NetEase HQ in Guangzhou. China's top 8, **2-deck BO3**. Pre-patch, so 魔恋の天晶 was still 3 cost and Pirate was unbuffed.
   - Results: 1st b站美少女莉莉猪, 2nd 我是小小离场王, 3rd 骇鳞, 4th 子衿. The top 4 go to WGP 2026 (December). Prize ¥80,000.
   - Sources: beyond-dexel.com/shadowverse-snc-grand-finals-result/ (2026-09-30, fetched 3x); shadowverse-magazine WGP2026 page; shadowverse-magazine news/svwb/74649 (2026-09-20). [V2]
   - **Champion's lineup: 魔手ウィッチ + ランプドラゴン.** Both lists are official deck-builder hashes on beyond-dexel [V1+D]; full lists are in section 1.
   - The other finalists' decks and the top-8 deck distribution are on svlabo.jp (blog-entry-1928 "結果＆デッキ分布", 1927 "デッキリスト比較", dated 2026/09/20). **That data is rendered by JavaScript and WebFetch could not read it.** Open it in a browser: it is the single best CN tournament source.
2. **The champion's Ramp Dragon is the user's example in action.** It runs **1× 日珥咆哮 and 0× 隔断的龙斗士 (the 6-cost 6/9)**. The ladder/creator Ramp lists below do the opposite or something else:
   - 娅娘 runs 2× 隔断的龙斗士 and 0 日珥咆哮.
   - 星野饼美's 扎针龙 runs 0 of both.
   - Section 4 compares them card by card.
3. **Almost every CN "deck guide" is an imported JP list from a ~1850–2120 职业分 player.** 星野饼美 credits the author and rating every time:
   - Arusu 1891, CQCQ 1879, ふじのん 1850, an unnamed 1857, 1856, みみっちハンター 2082, 冷夏喵皇 2102, 女神 2117.
   - The one exception is そろばん, credited as "6000人比赛8强", a tournament result.
   - 英梨梨的男友 also posts 搬运 (reuploads) of the JP YouTuber あっくちゃんねる.
   - This is the "国际服 ~2000cr" tier the user warned about. [V1 each]
4. **The CN creators with real competitive credentials are a small set** (section 3):
   - 云墨染s: bio says "2025 snc无限进化大师赛冠军".
   - 暮遥Kuharu: bio says "影之诗SNC终轮8强，狼宴杯冠军".
   - 蕾米莉亚__Scarlet: bio says "影之诗SNC2022季军".
   - Post-patch, 云墨染s calls 宇宙鱼, 连击妖 and 财宝海盗皇 all **T1**, and 暮遥Kuharu made a 旗皇 video. None of their descriptions contain lists.
5. **The 英梨梨的男友 【每周环境考察】 descriptions have no tier data.** 第41期 (09-15) and 第42期 (10-04) both carry only the same boilerplate. **I found no 第40期 BV.** Related-video lists show episodes 30, 31, 34, 36, 41 and 42 but no 37–40, and search found nothing. The rankings exist only inside the videos.

## 1. Tournaments in the pack-9 era (CN)
### SNC 2026 Grand Finals, 2026-09-19 (pre-patch) [V2 results; V1+D decks]
- Format: top 8 of China, 2デッキBO3 (svlabo and beyond-dexel agree). Beyond-dexel quote: "中国の上位8名のプレイヤーが年間チャンピオンのタイトルをかけて競い合い、上位4名は12月開催のShadowverse世界選手権（WGP）に中国代表として出場します。"
- Champion b站美少女莉莉猪. Interview quote: "試合が終わった後は手が震えていました". The summarizer paraphrased her as saying "Abyss random effects came up poorly... drew the final copy of Kalgidensura (卡卢基典瑟拉)" [UNVERIFIED paraphrase].

**Champion deck 1: 魔手法 (魔手ウィッチ)** [D]. Hash: `1.3.cH3E.cH3E.cH3E.e4Gg.e4Gg.e4Gg.eB7k.eBpe.eBpe.eZV6.eZV6.eZV6.eZYE.eZYE.eZYE.eZns.eZns.ea1U.ea1U.ea1U.eaD-.eaD-.eaD-.eaE8.eaE8.eaE8.fDXk.fDXk.fDXk.cfTu.cfTu.cfTu.fKZk.fKZk.fKZk.fKpM.fKpM.fKsU.fKsU.fKsU`
- 3 智慧光辉 / 3 暴风破 / 3 大游戏世界 / 3 天晶魔手 / 2 正常的侵蚀
- 1 明越花的转变 / 3 天晶授予 / 3 传承的意志
- 3 魔恋的爱慕·希姆 / 2 玛纳利亚文书官·琪可 / 3 钢铁的小憩
- 3 魔恋的天晶 (3 cost at the time) / 3 快乐绽花·萨米&玛莉
- 2 明越花·阿罗 / 3 古旧天晶·卡卢基典瑟拉

**Champion deck 2: 跳费龙 (ランプドラゴン)** [D]. Hash: `1.4.cJl6.cJl6.cJl6.drrE.drrE.drrE.drrO.drrO.drrO.e4IE.e4IE.eDpc.eE3E.eE3E.eE3E.eEFk.eEFk.eEFk.ecgE.ecgE.ecgE.ecgO.ecgO.ecgO.e-Ls.e-Ls.e-Ls.e_4k.e_4k.e_4k.fN08.fN08.fNIk.fNIk.fNVO.fNVO.fNVO.flvu.flvu.flvu`
- 2 狐火蜃景
- 3 懒惰的波摇花 / 3 古旧天刀·波菈莱 / 3 宣扬的龙人 / 2 满面笑容的烹饪·琪米卡
- 3 龙之启示 / **1 日珥咆哮**
- 3 世界的伙伴·佐伊 / 2 《世界》的呈现
- 3 炎之法则·威尔纳斯 / 3 断头的斩姬·相枛津 / 3 禁牙的变貌·诺玛格达拉
- 3 金银绚烂·璐米欧儿&雅尔贞特 / 3 焦灰的安纳提玛·班德奈特 / 3 约束的《正义》·伊兰翠

Other events:
- **SNC monthly cups:** svlabo lists "NetEase Championship 2026 8月 TOP8 結果＆デッキ分布/デッキリスト比較" (blog-entry-1877/1876, dated 2026/08/25). That is before pack 9 (pack 8 era), so it is not relevant here. It does show that svlabo tracks every SNC monthly. Svlabo's 海外大型大会 category shows no SNC entry after 09/20.
- **No pack-9 CN community, college or streamer cups found** (searched 狼宴杯, 高校赛, 主播赛, 邀请赛). The old sv.163.com SNC and match pages are 2020–2023 archives.
- **yokidou 【影之诗·BO10杯】:** creator showmatches of 10 games, not tournaments. Treat them as anecdotes (n=10) [V1 titles/desc]:
  - 09-17 中速梦 1:9 护符教 ("打出了9月以来的最大分差")
  - 09-23 连击妖 2:8 跳费龙 ("看来跳费龙是真的优开连击妖，上次的bo10没错")
  - 10-07 海贼皇 8:2 跳费龙 ("上次打还是55的，加强后效果拔群啊")
  - Other titles, dates unverified: 连撃妖 2:8 中速梦; 跳費龍 5:5 造物鱼; 跳費龍 6:4 中速梦 (餅佬 vs 吾影); 連撃妖 6:4 奧義教.
- 星野饼美 ("饼佬") and "jk兔娘周神" were casters at SNC (BV1Jrhh6eEiu title: "snc最佳解说争夺战") [V1 title]. 周神 = yokidou per the tags of BV1oraW65EZC ("周神轻松5连胜", tags yokidou/周报君) [V1].

## 2. Decklists from Bilibili descriptions (国服长码, decoded)
### 2a. Post-patch (after 9/29)
**海盗旗皇 (Pirate Royal).** 星野饼美 BV16ypP6MEsP, 2026-10-07. Description: "海盗皇预计T1。卡组作者：そろばん（6000人比赛8强）" [V1+D]
- 2 须臾剑士
- 3 古旧天剑·伊德梅塔 / 3 听略谍报兵 / 3 海域斥候
- 3 荣耀的丽金花 / 3 漩涡炮手 / 3 燃尽之缘
- 3 真红与群青·塞达&贝阿朵丽丝 / 3 黄金时代
- 3 丽金花·云庆 / 3 波涛副船长
- **3 真王之刃·黄金骑士** (6 cost post-patch)
- 3 逆行的罪人·巴巴洛丝
- 2 武皇的变貌·贝尔铁佐

Compare the pre-patch version: 星野饼美 BV1jrtM6sEGf, 2026-09-01, "预计T2… 卡组作者：CQCQ（职业分1879）" [V1+D]:
- 3 须臾剑士 / 1 惨烈的天剑 / 2 无音的包围
- 3 伊德梅塔 / 2 相伴相随的日常 / 3 海域斥候
- 3 荣耀的丽金花 / 3 漩涡炮手 / 2 燃尽之缘
- 3 塞达&贝阿朵丽丝 / 3 黄金时代
- 3 云庆 / 3 波涛副船长
- 3 巴巴洛丝 / 2 焦灼炎将·玛尔斯
- 1 贝尔铁佐

Post-patch changes (そろばん vs CQCQ):
- Added: +3 黄金骑士, +3 听略谍报兵, +1 燃尽之缘, +1 贝尔铁佐
- Cut: −2 玛尔斯, −2 无音的包围, −2 日常, −1 惨烈的天剑, −1 须臾剑士
- The buffed 6-cost 黄金骑士 replaced the 8-cost 玛尔斯 top end.

**宇宙鱼 (Highlander Nemesis), list A.** 星野饼美 BV1cJH66MEjH, 2026-10-04. "宇宙超预计T1。卡组作者：Arusu（职业分1891）" [V2 desc + D]
- 3× 束刃的罪人·卡特斯罗特 (Cutthroat), 1 of everything else:
  - 1 cost: 大游戏世界, 诚心的尽小花, 跑酷, 器械操纵者·吉尔克, 青锈小卒, 屈辱流放
  - 2 cost: 人偶长矛手, 人偶剧场, 露莉亚, 报恩工匠·艾萨克, 尽小花·伊鞠, 古旧天斧·尤泽塔, 悠然的滑手, 遗忘的纯真·爱卡, 你的前辈·欧丝
  - 3 cost: 夜王再起·翔, 斯洛士, 被侵略的世界, 神话记者, 狂野播报员, 门扉接续者·拉姿莉, 白牙燐敛
  - 4 cost: 古兰&姬塔, 奋厉追赶·米乌, 双子无人机少女, 锻磨保镖
  - 5 cost: 卡塔莉娜, 光之法则·龙敖, 亚修雷&莉缇雅, 铸铁亲信
  - 6 cost: 圣德芬, 混沌军势
  - 7 cost: 卡密希拉, 弹哭的变貌·艾兹伊甸
  - 8 cost: 愚劣的兵器, 斯卡雷特
  - 9 cost: 唯一王者·别西卜

**宇宙鱼, list B.** 娅娘征服世界 BV1esHL6oESC (2026-10-04) and BV1XTHq6UEhY (10-03), same code, author not credited [V1+D].
- The same as list A except:
  - Added: 苏生调律, 舞台缔造者, 人造的馈赠·蕾拉, 知恩图报·米莉亚姆
  - Cut: 大游戏世界, 遗忘的纯真·爱卡, 双子无人机少女, 光之法则·龙敖
- Both lists share a ~36-card core with the JP hashes already in `research2/hashes.txt` (shoya, lind, massu, uzumaki, …). Those variants swap in 舞台缔造者, 新时代地理学者, 低劣的玩具 and 聪明的创造者, and often cut 别西卜 and 爱卡. **The flex slots are 爱卡, 别西卜, 双子无人机少女, 龙敖, 舞台缔造者, 地理学者 and 低劣的玩具.**

### 2b. Pre-patch pack-9 lists (8/30–9/26), for reference
- **扎针龙 (Ramp variant).** 星野饼美 BV1R9tW6hEh2, 2026-08-31, "预计T1", author 职业分1857 (name not captured) [V1+D]
  - 3 露莉亚 / 3 懒惰的波摇花 / 3 波菈莱 / 3 宣扬的龙人 / 3 琪米卡
  - 3 龙之启示 / 2 焦龙的午睡
  - 3 佐伊
  - 3 相枛津 / 3 诺玛格达拉
  - 3 璐米欧儿&雅尔贞特
  - 3 班德奈特 / **2 阿尔比昂巴哈姆特**
  - 3 伊兰翠
  - No 威尔纳斯, no 日珥咆哮.
- **跳费龙.** 娅娘征服世界 BV1kHYq6bEuq, 2026-09-13, "优开全部t1！四费跳是对的！" [V2 code + D]
  - 2 露莉亚 / 3 水母舞姬 / 3 懒惰的波摇花 / 3 波菈莱
  - 3 龙之启示
  - 3 百无聊赖的睥睨
  - 3 佐伊
  - **2 隔断的龙斗士 (6/9)**
  - 3 威尔纳斯 / 3 相枛津 / 3 诺玛格达拉
  - 3 璐米欧儿&雅尔贞特
  - 3 班德奈特
  - 3 伊兰翠
- **快攻龙 (Face Dragon).** 星野饼美 BV1aQhS6zENW, 2026-09-26: "快龙T2，慎合。卡组作者：冷夏喵皇（职业分2102）" (verbatim, fetched 2x) [V2+D]
  - 3 碎裂的盗匪 / 3 幼龙闹脾气
  - 3 烈焰火蜥蜴 / 1 懒惰的波摇花 / 3 波菈莱 / 3 琪米卡 / 3 绝倒的袭击者 / 3 利牙
  - 3 决断的龙人
  - 3 天刀授予 / 1 载运飞龙 / 2 阿尔菲德
  - 3 尘土的不法者
  - 3 相枛津 / 3 穿孔的罪人·安缇马丽亚
  - Title claims "能打上2100分".
- **连击妖 (Combo Elf).** 星野饼美 BV16WYW6SE5K, 2026-09-09, "连击妖T1。卡组作者：みみっちハンター（职业分2082）" [V1+D]
  - 3 大游戏世界 / 3 古旧天枪·萨莎妮德 / 3 忧郁少女·莫埃尔 / 3 发芽组员
  - 2 露莉亚 / 2 风之法则·艾云尼亚 / 3 绿风细剑师 / 3 根延潜伏者 / 3 枝叶大姐大
  - 1 优雅的虫风花 / 3 虫风花·魅禄 / 3 烟管的罪人·曲千代
  - 3 达斯特迪兹
  - 2 冰界鹿王
  - 3 赛德斯&梅希亚
- **中速梦 (Midrange Nightmare).** 星野饼美 BV1hv4U6oErs, 2026-08-30, "中速梦预计T1。卡组作者：ふじのん（职业分1850，原构筑1魅惑的魅魔·莉莉姆2伊斯坦戴德）" [V1+D]
  - 3 可爱恶魔·莉莉姆
  - 3 恶魔鼓手·拉兹 / 3 幽冥中尉
  - 3 巴尔 / 3 制造麻烦的唤灵师 / 3 夜之歌的演唱会
  - 2 古旧天眼·比芭提
  - 3 猫咪走绳师
  - 3 徒姬 / 3 渊底上校
  - 3 伊斯坦戴德对玛尔奇盖特
  - 2 苇剑&武津御 / 3 伽罗塔德对泽特
  - 3 马克米朗
  - Note: the uploader changed the author's original 1 莉莉姆 + 2 伊斯坦戴德.
- **快攻梦 (Aggro Nightmare).** 星野饼美 BV1iCh76REoJ, 2026-09-22, "快梦T2。卡组作者：女神（职业分2117）" (title: "登顶世一") [V1 verbatim + D]
  - 3 魅惑的魅魔·莉莉姆 / 2 挥毫的怪物 / 3 可爱恶魔·莉莉姆
  - 2 恶毒的小木乃伊 / 3 残虐的炸裂 / 3 渴望的恶魔 / 2 兔耳恶魔·莉蜜儿 / 3 强袭的特攻队长
  - 3 巴尔 / 2 逃避幽灵者 / 3 夜之歌的演唱会
  - 2 通透的信念·安瑟珠 / 3 诚实的诅咒师·丝姬
  - 3 激烈的副总长
  - 3 伽罗塔德对泽特
- **实验体法 (Experiment Witch).** 星野饼美 BV18btj6vEJ2, 2026-09-02, T2, author 职业分1856 [V1+D]
  - 3 智慧光辉 / 3 暴风破
  - 2 露莉亚 / 3 炼金炎爆 / 3 传承的意志 / 3 沉溺的实验体
  - 3 琪可 / 3 钢铁的小憩 / 3 人性的爱
  - 3 心醉的研究者
  - 3 陶醉的才女 / 3 乌涅
  - 2 坦忒拉&拉缇卡
  - 3 万术的罪人·赛菲

## 3. Creators: claims and credibility
| Creator | Credential (where stated) | Pack-9 content | Credibility note |
|---|---|---|---|
| **云墨染s** | bio: "2025 snc无限进化大师赛冠军" [V2, 4 pages] | 09-30 "t1宇宙鱼卡组介绍＋对局解说，获得加强的高上限卡组" (BV17uaX6fEgC); 10-02 "t1玩不腻连击妖…一张没削的全面卡组" (BV1GKay6fEPh); 10-04 "t1财宝海盗皇卡组解析…云庆的币是关键" (BV1GDHq6JEx7); 07-30 "t1国一跳费威慑龙…对法皇特化构筑" (BV12h3p66EZb, pack 8) | **Highest.** He is an SNC champion. "无限进化" is probably the pack-2 (インフィニティ・エボルヴ) era SNC [UNVERIFIED]. His descriptions have no lists, so the content is only in the videos. Post-patch he rates 宇宙鱼, 连击妖 and 财宝海盗皇 all T1. |
| **暮遥Kuharu** | bio: "围棋业余6段，影之诗SNC终轮8强，狼宴杯冠军" [V1] | 10-02 "【影之诗】旗皇焚决！学会随手上超凡！" (BV1ptay6yENc) | High: SNC final-round top 8 plus a community-cup win. No list in the description. "超凡" here is the ladder's top rank (BEYOND). |
| **蕾米莉亚__Scarlet** | bio: "影之诗SNC2022季军" [V2] | 08-29 "17连胜中速梦…预计T1，操作简单，强度够高" (BV1tb4k6qEbL); 09-05 "大优跳费龙，不惧中速梦！…操作稍难，强度很高" (BV1VtbL63EcL) | High for an SV1-era result. Pre-patch content only. |
| 困倦keeexing | bio: "Nikke开服场8冠 影之诗十年鱼丸主播" | 09-05 "手法被削还能T1！9月最新梯度排行"; 09-11 "连击妖改变环境！T1占比80%！…全世1卡组分享"; 08-30 "T1禁牙跳费龙…超强756无脑上分"; 09-30 "宇宙鱼质变加强！…新版本最高分构筑" | Medium. He is a veteran streamer with no tournament credential stated. He is a Nemesis main ("鱼丸"), so expect a bias toward Nemesis. "全世1" = a world-#1 list [UNVERIFIED]. |
| 星野饼美 (饼佬) | SNC caster; streams daily | Daily deck videos, each crediting the JP author and 职业分 | Medium as a *conduit*: transparent sourcing, but the lists are mostly from ~1850–2120 JP ladder players. The "预计T1/T2" labels are his own predictions. |
| 英梨梨的男友 | none stated | 【每周环境考察】 41/42 (claims "收集大量数据"); 搬运 of あっくちゃんねる (YouTube iDRsADKbD5Y): 宇宙鱼 10-02, 海盗旗皇 08-28 | Data series of unknown method. The reuploads are JP ladder content. |
| yokidou (周神/周报君) | translates JP 连胜 data; SNC caster | BO10杯 series; 10-07 海贼皇 8:2 跳费龙 | Medium; n=10 showmatches. |
| 诗月樱 | bio: "影之诗卡组构筑UP" | 08-30 "【第9弹强度榜】环境大変！造物鱼泡沫，跳费龙崛起" (method claim: international win-streak sites + rating leaderboards across servers + "1000+场" in a test group); 08-28 中速梦 "92%胜率" | Low–medium; the win rates are self-reported. |
| 娅娘征服世界 | none | 跳费龙 (09-13), 宇宙鱼 (10-03/04) lists | Low (no credential). Her lists are useful as a "ladder-flavor" comparison. |
| AKNO_ | none | 10-02 "环境里找不到劣势对局的强力卡组！海盗旗皇" ("个人观点，仅供参考") | Low. |

**The "职业分" figures that 星野饼美 cites:** Arusu 1891, CQCQ 1879, ふじのん 1850, an unnamed 1857, an unnamed 1856, みみっちハンター 2082, 冷夏喵皇 2102, 女神 2117. I could not confirm whether 职业分 equals the user's "CR" (the WB master-tier rating) [UNVERIFIED]. Either way, these are ~1850–2120 ladder players, not tournament players. The exception is そろばん ("6000人比赛8强").

## 4. Card-choice comparison: Ramp Dragon
Four Ramp lists, 3-ofs unless noted. The shared core: 懒惰的波摇花, 波菈莱, 龙之启示, 佐伊, 相枛津, 诺玛格达拉, 璐米欧儿&雅尔贞特, 班德奈特, 伊兰翠.

| Slot | SNC 2026 champion (09-19) | 娅娘 (09-13, ladder) | 扎针龙 (职业分1857, 08-31) |
|---|---|---|---|
| 1–2 cost extra | 2 狐火蜃景, 3 宣扬的龙人, 2 琪米卡 | 2 露莉亚, 3 水母舞姬 | 3 露莉亚, 3 宣扬的龙人, 3 琪米卡 |
| 3–4 cost | **1 日珥咆哮** | 3 百无聊赖的睥睨 | 2 焦龙的午睡 |
| 5 cost | 2 《世界》的呈现 | — | — |
| 6 cost | — | **2 隔断的龙斗士 (6/9)** | — |
| 7 cost | 3 威尔纳斯 | 3 威尔纳斯 | — |
| 9 cost | — | — | 2 阿尔比昂巴哈姆特 |

- The tournament list runs a single 日珥咆哮 (4-cost spell), no 6/9 body, and 2 《世界》的呈现.
- The ladder list runs the 6/9 and no 日珥.
- I did NOT read the card texts here; the "why" needs the card text and matchup analysis (likely the 日珥 slot targets the field-wide or Nemesis/Royal threats in a BO3 lineup) [UNVERIFIED].

## 5. Not found / blocked
- svlabo SNC 2026 top-8 distribution and all 16 lists (JS-rendered; blog-entry-1928/1927) need a browser.
- No 英梨梨 第40期. No tier text in the 41 or 42 descriptions.
- No other CN pack-9 tournaments with lists. No 国服-ladder-specific leaderboard data.
- No SNC finals VOD found on Bilibili via search.
- The ladder-names-to-JP mapping for "财宝海盗皇" vs "海盗旗皇": 云墨染s titles it "财宝海盗皇" with "云庆的币是关键"; the そろばん list has 3 云庆 + 3 丽金花. These are the same archetype (Goldbloom treasure package + pirates).

## Sources
- SNC: https://beyond-dexel.com/shadowverse-snc-grand-finals-result/ ; https://svlabo.jp/blog-entry-1928.html ; https://svlabo.jp/blog-entry-1927.html ; https://svlabo.jp/blog-category-60.html ; https://shadowverse-magazine.com/svwb/event/wgp2026/ ; https://shadowverse-magazine.com/news/svwb/74649/
- Bilibili:
  - https://www.bilibili.com/video/BV16ypP6MEsP/ ; BV1jrtM6sEGf ; BV1cJH66MEjH ; BV1esHL6oESC ; BV1XTHq6UEhY ; BV1kHYq6bEuq ; BV1R9tW6hEh2 ; BV1aQhS6zENW ; BV16WYW6SE5K ; BV1hv4U6oErs ; BV1iCh76REoJ ; BV18btj6vEJ2
  - BV17uaX6fEgC ; BV1GKay6fEPh ; BV1GDHq6JEx7 ; BV12h3p66EZb ; BV1ptay6yENc ; BV1tb4k6qEbL ; BV1VtbL63EcL
  - BV1Xra96dEBs ; BV1u1ah6REZm ; BV1DkY561EBA ; BV1kmtr6bEHL ; BV1wQtn6TEJn ; BV1mTaS6YEJr ; BV1UcaS6qEi3 ; BV16ktA6EE4p ; BV1Gs4d6mErp ; BV1494X6cEvE
  - BV1NdpN6SEov ; BV13Bhn6dE1u ; BV18ZeP6UE5D ; BV1oraW65EZC ; BV18AHk6oEYL ; BV1sTej6GEsy ; BV1JSNM6zEHd ; BV1L74d6pEK7
- Decoder: /tmp/claude-0/-home-claude/d1f8fa57-d8df-5aad-bcb6-b7aa526dbb19/scratchpad/tools/dec.py (uses /home/claude/sv/svsim/cards/data/rotation.json)
