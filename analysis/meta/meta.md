# Shadowverse: Worlds Beyond, Rotation meta research (as of 2026-10-07)
Current pack: 第9弾 アズヴォルト・レヴナント / Revenants of Azvaldt (released 2026-08-27).
Collected with WebFetch/WebSearch. The WebFetch summarizer sometimes mistranslates class names (it calls Royal "Sword" or "Portal", and so on). Trust the Japanese names over its English translations.
Confidence: [V] = confirmed in two or more sources or quoted verbatim; [S] = single source; [U] = unverified or conflicting.

## 1. Tier lists

### Game8 Rotation Tier表: https://game8.jp/shadowverse-beyond/694512 (最終更新 2026.10.07 05:39) [V]
Post-patch (the page notes the 9/29 adjustment). The JP names below are verbatim.
- Tier1: 海賊ロイヤル ("海賊旗を貯めてバルバロスで解放・コンボによるダメージと盤面からのダメージを両立"), ラストワードナイトメア ("序盤から隙が無く攻めれる" midrange), ランプドラゴン ("PP加速で大型フォロワーを展開"), コンボエルフ ("ダストデイズでデッキフォロワーを強化")
- Tier2: 実験体ウィッチ, ハイランダーネメシス, フェイスドラゴン, AFネメシス, アミュレットビショップ, 連携ロイヤル
- Tier3: 魔手ウィッチ, OTK人形ネメシス, 進化ビショップ, スペルウィッチ
- The page gives no change log or numbers. Per Game8, the ranking is "deck power + adoption".
- Game8 Pirate Royal guide https://game8.jp/shadowverse-beyond/811814 (updated 2026-09-30 19:06): rates it Tier1 and says the 9/29 buffs to 渦潮の砲手, 海域の斥候 and 真王の刃・黄金の騎士 strengthen the deck. Its mulligan keeps include 海域の斥候 and 渦潮の砲手. Barbaros burst is up to 15 damage.

### beyond-dexel: https://beyond-dexel.com/dexel-decktier/ (最新更新日 2026.09.27, before the patch, "強豪プレイヤー3名監修") [S]
- Tier1: ダストデイズエルフ, 魔手ウィッチ, ランプドラゴン
- Tier1.5: ミッドレンジナイトメア, 進化ネメシス, アミュレットビショップ
- Tier2: クキシロビショップ, セフィーウィッチ, アグロナイトメア, AFネメシス
- Tier3: 連携ロイヤル, バルバロスロイヤル, 進化ビショップ
- This list is the pre-patch baseline. 魔手ウィッチ was T1 before the 魔恋の天晶 nerf and is T3 on Game8 after it. Pirate (バルバロス) Royal went from T3 to T1 after the buffs.

### appmatch (games.appmatch.jp/?p=223945, dated 2026-09-26, before the patch) [S, low-quality aggregator]
- Tier1: ミッドレンジナイトメア, ランプドラゴン, 魔手ウィッチ, コンボエルフ

### Stale or unusable sources (checked, but not current)
- GameWith 497197: still shows 第8弾 クロニクル・オブ・デスティニー content with no date (T1: テンポエルフ, 魔手ウィッチ, ランプドラゴン, AFダッシュネメシス, 破壊ネメシス). Other GameWith pages (top page, 573927) returned 403. gamewith.net English tier (68388) was last updated 2026-05-03 (Set 6).
- AppMedia (appmedia.jp/?p=78972524): last updated 2026-04-26 (第5弾 era). Altema (altema.jp/shadowversewb/saikyodeck): page says updated 2026-09-01 but the content is old (Legends Rise era). Gamerch 922937: 2026-05-27, stale.
- shadowverse.gg/tier-list/: its title says "(October 2026)", but every fetch returns 403, so the content is unverified.
- Reddit: no relevant threads found by search.
- YouTube (JP ladder titles from the new environment, dates not checked): "【シャドバWB】ランプドラ←海賊ロイヤル←コンボエルフ 新環境有限ランクマッチ【アズヴォルト・レヴナント】" https://www.youtube.com/watch?v=G3mC6aUselQ ; "ロイヤルはアッパーでどうなるんだい アプデきたぁ…" https://www.youtube.com/watch?v=zP8ymFc6I-I ; "海賊ロイ←みんな大好きカットスロート←ドラゴン アプデきたぁ…" https://www.youtube.com/watch?v=UQOYkMbcAXU (post-patch: Pirate Royal, Cutthroat Nemesis and Dragon on ladder).
- note by もとやしき (BEYOND rank, peak CR2235), 2026-09-01, pre-patch Pirate Royal guide: https://note.com/motoyqsiki/n/nf5fb40f65b00. Matchups it covers: コンボエルフ, 海賊ミラー, 実験体ウィッチ, ランプドラゴン, ミッドレンジナイトメア, アミュレットビショップ, AFネメシス.

## 2. Quantitative data (usage and win rates)
- I found no public usage or win-rate dataset for the 9th-pack environment. Cygames does not publish rates.
- The best-known community dataset is the "Shadowverse Tracker" note by こじま (https://note.com/dcg_ik/n/na5349dbba48b): 22,415 ranked games from 1,100+ players, collected 2026-01-09 to 01-22. It is from the 第5弾 era and is now stale. No newer edition was found.
- shadowverse-wins.com (e.g. https://shadowverse-wins.com/?format=rotation&group=topaz&leader=R&mp=A&seasonId=69): crowd-submitted win streaks (5–14 wins) for the current season (seasonId=69 = アズヴォルト・レヴナント). It has no aggregate rates. It could be scraped per class to get rough deck frequency. One sample row was a 連携ロイヤル streak.
- Tracker tools that exist but publish no aggregates: shadowverse-wb-tracker.netlify.app, dev.hy-clear.com/webapp/svwb_memo, GameWith 戦績管理ツール (507487).
- The best quantitative proxy is the tournament deck distribution in section 3.

## 3. Tournaments since 2026-08-27
### Shadowverse International Championship 2026 Singapore, 2026-09-26/27 (offline, WGP 2026 Day 1 slot + US$30,000) [V]
- Played before the 9/29 patch, so it reflects the old meta: 魔恋の天晶 still at 3 cost, Pirate Royal unbuffed.
- About 400 players. Day 1 was 9 Swiss rounds, Day 2 a top-32 single-elimination bracket. Each player brought 2 decks. (onemoregame.ph)
- Champion: Chappy (RIDDLE ORDER). Runner-up: Kraken (Singapore). The final went to game 3, with Forest in G1 for both players and Chappy on Dragon vs Kraken on Haven in G3. https://onemoregame.ph/2026/10/shadowverse-international-2026-sg-chappy/
- Top-32 deck distribution (64 decks), from https://www.shufflephase.com/news/combo-forestcraft-leads-day-2-at-shadowverses-singapore-international :
  - Combo Forestcraft (コンボ/ダストデイズエルフ) 18
  - Ramp Dragon 15
  - Crystal Rune (魔手ウィッチ / 天晶) 11
  - Midrange Abyss (ミッドレンジナイトメア) 9
  - Other 11
  - By class: Forest in 19 of 32 lineups, Dragon in 15 of 32, Haven 2, Sword (Royal) 1.
  - Article quote: "Combo Forest is the deck to beat."
- Official pages: https://ics.shadowverse-wb.com/en/news/detail/?id=75 (results), id=74 (Day 2 bracket and decks). WebFetch could not render the content of either.
### Shadowverse NetEase Championship 2026 (China WGP qualifier), around September 2026 [S]
- shadowverse-magazine's WGP page lists September qualifier winners b站美少女莉莉猪, 我是小小离场王, 骇鳞 and 子衿. I could not tell which of these belong to ICS and which to the NetEase event, and I found no decklists. https://shadowverse-magazine.com/svwb/event/wgp2026/
### Others
- WGP 2026: December 2026, 34 slots, ¥100M first prize. RAGE Japan Championship 2026 Season 3 is scheduled for October; Season 2 Grand Finals were 2026-08-23, before the 9th pack. SOC runs in November.
- I found no JCG or RAGE results in the 9th-pack format. shadowverse-magazine's event hub lists no post-8/27 results.

## 4. 2026-09-29 balance patch (maintenance 14:00–17:00 JST) [mostly V]
- Official JP X post (1/2): "9/29のメンテナンス時に『魔恋の天晶』『真王の刃・黄金の騎士』『渦潮の砲手』『海域の斥候』のカード能力を変更いたします" https://x.com/shadowverse_jp/status/2104162640595669022 (X blocks fetching). EN: https://x.com/shadowversegame/status/2104163874710999537. The changes were revealed on 熱血シャドバTVエクストラ (https://x.com/shadowverse_jp/status/2104043360151367849).
- shadowverse-magazine: "上方修正6枚、下方修正1枚の計7枚". https://shadowverse-magazine.com/news/svwb/74675/ , https://shadowverse-magazine.com/svwb/ability-change/ (previous change: 2026-08-27).
- Blog with class labels: https://silvervine0822.hatenablog.com/entry/2026/09/30/003000
- Game8's change page (https://game8.jp/shadowverse-beyond/712358) has the changes only as images.

| Card | Class | Change | Confidence |
|---|---|---|---|
| 魔恋の天晶 | Witch | NERF: cost 3→4, Enhance 5→6. Hits 天晶の魔手ウィッチ and スペルウィッチ | V (2 sources) |
| 真王の刃・黄金の騎士 | Royal | cost 7→6, Enhance 9→8 (base card: 7-cost 6/6 with 3 Modes; at Enhance all 3 fire). From 第4弾 蒼空の六竜 | V |
| 渦潮の砲手 | Royal (pirate) | 3/1 → 4/2 | V |
| 海域の斥候 | Royal (pirate, 2-cost; Fanfare: 震える海賊旗 into play) | 2/1 → 2/2 | V |
| ハクガ燐斂 | Nemesis (highlander) | cost 4→3 | V on the cost; the class is "Nemesis" per the blog, other sources garble it |
| 屈辱なる放逐 | Nemesis (highlander) | reworked: discard 1, draw a Nemesis follower with 必殺 (one source says 潜伏/Ambush); with no duplicates in deck, draw 2 more | U on exact text |
| 束刃の咎人・カットスロート | Nemesis | rework: now searches/draws a Nemesis follower with 必殺 (blog also says cost 2→1; magazine says its evolve effect changed instead of the old deck-destroy) | U on exact text |

- Net effect: three Pirate Royal buffs (it moved to T1 on Game8), three Nemesis buffs (Highlander/ハイランダーネメシス is now T2, and カットスロートネメシス appears in ladder video titles), and one Crystal/魔手 Witch nerf (魔手 fell from T1 to T3).
- Blog author's take: "海賊旗ロイヤル・カットスロートネメシスは安定感が増したが結局はダストデイズエルフにわからせられる".
- Balance-patch cadence: roughly the end of odd months plus emergency fixes. The next scheduled window would be around late November 2026 [S, GameWith EN].

## 5. Next pack (第10弾) and rotation
- I found no announcement of 第10弾's name or date as of 2026-10-07. Searches returned nothing.
- Expected date: about late October 2026, inferred from the cadence of packs 4–9 (10/29/25, 12/29/25, 2/26/26, 4/28/26, 6/29/26, 8/27/26). Packs are usually announced on a "しゃどばすチャンネルビヨンド" stream about 5 days before release; pack 9 was revealed 8/22 and released 8/27 (4Gamer, https://www.4gamer.net/games/760/G076037/20260823001/).
- Pack list (shadowverse-magazine all-cards; dates from the おんJ wiki):
  1. 伝説の幕開け (2025-06-17)
  2. インフィニティ・エボルヴ (2025-07-17)
  3. 絶傑の継承者 (2025-08-28)
  4. 蒼空の六竜 / Skybound Dragons (2025-10-29)
  5. 花酔遊戯 (2025-12-29)
  6. アポカリプス・パクト (2026-02-26)
  7. 神殺し・アナテマ (2026-04-28)
  8. クロニクル・オブ・デスティニー (2026-06-29)
  9. アズヴォルト・レヴナント (2026-08-27)
- Rotation rule (Game8 https://game8.jp/shadowverse-beyond/776155, updated 2026-09-30): "ローテーションは最新の6パックで戦われる"; rotation-outs started with the late-April 2026 pack, oldest first from 伝説の幕開け.
  - So the legal pool now is packs 4–9.
  - [Inference] 第10弾 should rotate out 第4弾 蒼空の六竜. That pack contains the just-buffed 真王の刃・黄金の騎士, so the Royal buff has a short shelf life.
  - Check this inference against an official rotation list when 第10弾 is announced. GameWith's 573327 "第9弾実装時にローテ落ち" page describes the previous rotation.

## 6. China (国服)
- Mainland China: NetEase (网易) operates 影之诗. 超凡世界 (Worlds Beyond) launched on 2025-06-17, the same day as the global release. It runs as a separate "超凡世界服" inside the existing 影之诗 mobile client, with a 怀旧服 (legacy) option.
  - The 国服 producer is 李雷鸣. Quote: "我们肯定是优先保证核心打牌玩法和后续版本更新跟日服同步" (GamerSky interview, 2025-05: https://www.gamersky.com/news/202505/1931751.shtml).
  - 国服-exclusive cosmetics include a free バルバロス leader skin (ali213 https://m.ali213.net/news/250314/218809.html ; iyingdi FAQ https://www.iyingdi.com/tz/post/5606982).
- The global client is also available in Simplified Chinese via Steam and shadowverse-wb.com/chs. Chinese players use "超凡" for WB in general. The 国服 has separate accounts and its own ladder.
- No evidence of a lag: card pool and patches are stated to be synced with JP. The NetEase Championship 2026 is an official WGP qualifier.
- Original Shadowverse ended global service on 2026-06-30 PT (GamerSky https://www.gamersky.com/news/202603/2111711.shtml). The status of the 国服 怀旧服 was not checked.
- 国服 meta since 2026-09: NOT FOUND.
  - Searches of NGA, bilibili, 旅法师营地 (iyingdi), 小黑盒 and 贴吧 returned nothing for the 9th-pack environment.
  - The latest Chinese weekly ladder series found is bilibili "【每周环境考察】天梯环境介绍与最强卡组推荐 第35期【影之诗 超凡世界】" by 英梨梨的男友, uploaded 2026-07-05 in the 第8弾 era. Its #1 deck was a 7-cost Dragon. https://www.bilibili.com/video/BV1oqMT6zE2G/
  - iyingdi 环境小报 posts are for the 怀旧服, not WB.
  - With identical card pools, the 国服 meta is presumably close to JP, but this is unconfirmed.
