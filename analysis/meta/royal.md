# Royal (Sword) research — 海賊ロイヤル / 連携ロイヤル
Collected 2026-10-07. Pack: 第9弾「アズヴォルト・レヴナント」(2026-08-27). Balance patch 2026-09-29.
Verification legend: [V2] = confirmed by 2 independent fetches/sources; [V1] = single fetch only; [UNVERIFIED] = suspect/inconsistent.

## 0. 2026-09-29 balance patch (7 cards: 上方修正6枚・下方修正1枚 — shadowverse-magazine news, 2026-09-29)
Royal buffs [V2: shadowverse-magazine ability-change page + silvervine0822 hatenablog 2026-09-30 + onj wiki change list]:
- 真王の刃・黄金の騎士 (Golden Knight, True King's Blade): コスト7→6; 【エンハンス_9】→【エンハンス_8】「1つを選ぶのではなくすべて。」
  Current text (Game8 card page https://game8.jp/shadowverse-beyond/733760, 最終更新 2026.09.30 12:35): 「【ファンファーレ】【モード】1つを選んでその能力が働く。（1）これは超進化する。（2）相手の場のフォロワーすべてに4ダメージ。（3）自分のリーダーを4回復。【エンハンス_8】1つを選ぶのではなくすべて。」
- 渦潮の砲手 (Whirlpool Gunner): 3コスト 3/1 → 3/4/2 (cost 3, now 4/2)
- 海域の斥候 (Open-Sea Scout): 2コスト 2/1 → 2/2
Other changes (not Royal): ウィッチ 魔恋の天晶 下方 (コスト3→4, エンハンス5→6) ; ネメシス 束刃の咎人・カットスロート (2/2/2→1/1/1 + text change), 屈辱なる放逐 (text), ハクガ燐斂 (コスト4→3).
Blogger comment (silvervine0822): 「結局はダストデイズエルフにわからせられるような気がします」 (feels like Dust Days Elf will still beat them).
NOTE: the decoder output below already shows post-patch values (Gunner 4/2, Scout 2/2, Golden Knight cost 6).
NOTE: one GameWith fetch of https://gamewith.jp/shadowverse-wb/516874 returned "9/29" changes for リュウフウ/リーアム/パペットキャット/シンフォニアハートツヴァイ — these are NOT in any other source and look like summarizer hallucination / stale content. DISCARD.

Sources: https://shadowverse-magazine.com/news/svwb/74675/ (2026-09-29); https://shadowverse-magazine.com/svwb/ability-change/ ; https://silvervine0822.hatenablog.com/entry/2026/09/30/003000 (2026-09-30); https://onjshadowverse-worlds-beyond.game-info.wiki/d/能力変更されたカード一覧 ; Game8 change page https://game8.jp/shadowverse-beyond/712358 (9/29 section is images only).

Card text verbatim (svlabo 第9弾 card list https://svlabo.jp/blog-entry-1867.html) [V2 with Game8 card pages for Barbaros/Beltezore]:
- 逆行の咎人・バルバロス 7コスト 4/3: 「【ファンファーレ】『戦慄の海賊旗』1枚を自分の場に出す。自分の場の『戦慄の海賊旗』すべてのカウントを-5する。【疾走】」 進化後: - (no evolve effect; Game8 https://game8.jp/shadowverse-beyond/811030, 最終更新 2026-08-26). "バルバロスに進化を切る" therefore = evolving it for +2/+2 extra Storm damage.
- 武皇の変貌・ベルテゾール 10コスト 2/12: 「【疾走】【必殺】【守護】【オーラ】1ターンに3回攻撃できる。」 (Game8 https://game8.jp/shadowverse-beyond/811748, 最終更新 2026.09.05; no cost-reduction text found on either page.)
- 戦慄の海賊旗 (token amulet): 「カウントダウン_7 自分がスペルをプレイしたとき、これのカウントを-1する。ラストワード 相手のリーダーに2ダメージ。」
- 渦潮の砲手: 「ファンファーレ『戦慄の海賊旗』1枚を自分の場に出す。『黄金の杯』1枚を自分の手札に加える。突進」
- 海域の斥候: 「ファンファーレ『戦慄の海賊旗』1枚を自分の場に出す。進化時『黄金の靴』1枚を自分の手札に加える。」
- 波濤の副船長: 「ファンファーレ 相手の場のフォロワー1枚を選ぶ。それに3ダメージ。『戦慄の海賊旗』1枚を自分の場に出す。」(+進化時/超進化時 — see decoder: evolve replicates FF; SE adds 黄金の短剣+黄金の首飾り at cost 0)
- アージュドール: 「『戦慄の海賊旗』1枚を自分の場に出す。相手の場のフォロワーすべてに2ダメージ。」 エンハンス_6: 2枚・4ダメージ
- 燃え落ちる縁: 「相手の場のフォロワー1枚を選ぶ。それに5ダメージ。これのコストが3なら、『燃え落ちる縁』1枚を自分の手札に加える。」 (copy cost 1)
- 刹那のクイックブレイダー 1コスト 1/1 「【疾走】」 (basic card, no evolve effect; Game8 https://game8.jp/shadowverse-beyond/698519) — this is the only "(no script)" card; it is a vanilla Storm 1/1.

Meta placement:
- Game8 Tier表 https://game8.jp/shadowverse-beyond/694512 最終更新 2026.10.07 05:39: Tier1 = 海賊ロイヤル, ラストワードナイトメア, ランプドラゴン, コンボエルフ; Tier2 includes 実験体ウィッチ, ハイランダーネメシス, フェイスドラゴン, 連携ロイヤル (「準環境トップのデッキ」). 海賊ロイヤル: 「・海賊旗を貯めてバルバロスで解放 ・コンボによるダメージと盤面からのダメージを両立」; 連携ロイヤル: 「・連携20の達成を目指すデッキ ・横並べから打点を出していく」. [V1 on full tier membership; deck blurbs V2]
- beyond-dexel Tier https://beyond-dexel.com/dexel-decktier/ last updated 2026-09-27 (PRE-PATCH): Tier3 = 連携ロイヤル, "バルバロスロイヤル", 進化ビショップ; Tier1 = ダストデイズエルフ, 魔手(?)ウィッチ, ランプドラゴン. Coordination Royal shown 不利 vs ランプドラゴン and 進化ビショップ. [V1, English-translated by summarizer; JP deck names not quoted]
- shadowverse-wins.com (rotation, Royal filter, season 69 = アズヴォルト・レヴナント) shows only win-streak tweets Oct 4–7 2026: kt 14連勝, ゑ 12連勝, Zaneric Logs 11連勝, 10連勝 Rihito/あきたネル/けいちやそ, 8連勝 竜城めり/ラスカル/ありしべる (archetype per streak not separated in summary). No aggregate win-rate/usage numbers found anywhere. [V1]
- Game8 Tier header links mention 「最新弾『クロニクル・オブ・デスティニー』の新デッキTier表」 — possibly an announced next pack; not investigated.

==========================================================================
# A. 海賊ロイヤル (Pirate Royal)
==========================================================================

## A1. Game8 list — https://game8.jp/shadowverse-beyond/811814 — 最終更新日：2026.09.30 19:06 (post-patch) [hash V2]
URL: https://shadowverse-wb.com/ja/deck/detail/?hash=1.2.cEZs.cEZs.cEZs.dmj6.dmj6.dmj6.dmyk.dmyk.dmyk.e9Ak.e9Ak.e9Ak.e9NO.e9NO.e9NO.eXnu.eXnu.eXnu.evm6.evm6.evm6.fgIM.fgIM.fgIM.fgX-.fgX-.fgX-.fgb6.fgb6.fgb6.fgnc.fgnc.fgnc.fgqk.fgqk.fgqk.fh1E.fh1E.fh1E.fh1O
必要エーテル：45,960. Page JP list: 刹那のクイックブレイダー×3、無音の包囲×3、旧き天剣・イドメタ×3、海域の斥候×3、渦潮の砲手×3、栄耀なる麗金花×3、燃え落ちる縁×3、真紅と群青・ゼタ＆ベアトリクス×3、アージュドール×3、麗金花・ウンケイ×3、波濤の副船長×3、真王の刃・黄金の騎士×3、逆行の咎人・バルバロス×3、武皇の変貌・ベルテゾール×1 (matches decode).
```
format 1 class 2
3x [1] 须臾剑士 / Flashstep Quickblader (1/1; Storm; set 10000) :: (no script)
3x [1] 无音的包围 / Orchestrated Silence (spell; ; set 10007) :: Add a Steelclad Knight to your hand and give it Rush. Rally (10): add 2 instead.
3x [2] 古旧天剑·伊德梅塔 / Yidmetra, Eld Sword (1/2; ; set 10006) :: Fanfare: add a Depths of the Eld Sword to your hand. Evolve: reduce your faith's value by 5 to give it the +1/+1 ability.
     -> 天剑深渊 / Depths of the Eld Sword :: Select an enemy follower and deal it 1 damage. Enhance (1): 3 instead.
3x [2] 海域斥候 / Open-Sea Scout (2/2; ; set 10009) :: Fanfare: summon a Dread Pirate's Flag. Evolve: add a Gilded Boots to your hand.
     -> 令人战栗的海盗旗 / Dread Pirate's Flag :: Countdown (7). Whenever you play a spell, advance the count by 1. Last Words: deal 2 damage to the enemy leader.
     -> 黄金之靴 / Gilded Boots :: Select an allied follower and give it +1/+0 and Rush.
3x [3] 荣耀的丽金花 / Splendor of the Goldbloom (spell; ; set 10005) :: Add 2 Glittering Gold to your hand. Enhance (5): add 4 instead.
     -> 闪耀的金币 / Glittering Gold :: Mode: 1. Draw a card. 2. Deal 2 damage to a random enemy follower.
3x [3] 漩涡炮手 / Whirlpool Gunner (4/2; Rush; set 10009) :: Fanfare: summon a Dread Pirate's Flag and add a Gilded Goblet to your hand. Rush.
     -> 令人战栗的海盗旗 / Dread Pirate's Flag :: Countdown (7). Whenever you play a spell, advance the count by 1. Last Words: deal 2 damage to the enemy leader.
     -> 黄金之杯 / Gilded Goblet :: Restore 2 defense to your leader.
3x [3] 燃尽之缘 / Severed Ties (spell; ; set 10009) :: Select an enemy follower and deal it 5 damage. If this card's cost is 3, add a Severed Ties to your hand and set its cost to 1.
     -> 燃尽之缘 / Severed Ties :: Select an enemy follower and deal it 5 damage. If this card's cost is 3, add a Severed Ties to your hand and set its cost to 1.
3x [4] 真红与群青·塞达&贝阿朵丽丝 / Zeta & Bea, Crimson and Blue (3/2; Rush; set 10004) :: Fanfare: summon a Zeta & Bea. Enhance (6): give it Bane and this follower Storm. Rush.
     -> 真红与群青·塞达&贝阿朵丽丝 / Zeta & Bea, Crimson and Blue :: Fanfare: summon a Zeta & Bea. Enhance (6): give it Bane and this follower Storm. Rush.
3x [4] 黄金时代 / L'Age d'Or (spell; ; set 10009) :: Summon a Dread Pirate's Flag and deal 2 damage to all enemy followers. Enhance (6): summon 2 and deal 4 instead.
     -> 令人战栗的海盗旗 / Dread Pirate's Flag :: Countdown (7). Whenever you play a spell, advance the count by 1. Last Words: deal 2 damage to the enemy leader.
3x [5] 丽金花·云庆 / Unkei, Goldbloom (2/4; ; set 10005) :: Fanfare: select an enemy follower and banish it; add a Glittering Gold to your hand. Super-Evolve: gain Crest: Unkei, Goldbloom.
     -> 闪耀的金币 / Glittering Gold :: Mode: 1. Draw a card. 2. Deal 2 damage to a random enemy follower.
3x [5] 波涛副船长 / Roughwater First Mate (3/3; ; set 10009) :: Fanfare: select an enemy follower and deal it 3 damage; summon a Dread Pirate's Flag. Evolve: replicate the Fanfare. Super-Evolve: add a Gilded Blade and a Gilded Necklace to your hand and set their costs to 0.
     -> 令人战栗的海盗旗 / Dread Pirate's Flag :: Countdown (7). Whenever you play a spell, advance the count by 1. Last Words: deal 2 damage to the enemy leader.
     -> 黄金短剑 / Gilded Blade :: Select an enemy follower or the enemy leader and deal it 1 damage.
     -> 黄金项链 / Gilded Necklace :: Select an allied follower and give it +0/+1 and Ward.
3x [6] 真王之刃·黄金骑士 / Golden Knight, True King's Blade (6/6; ; set 10004) :: Fanfare: Mode: 1. Super-evolve this follower. 2. Deal 4 damage to all enemy followers. 3. Restore 4 defense to your leader. Enhance (8): all of them.
3x [7] 逆行的罪人·巴巴洛丝 / Barbaros, Rebellious Convict (4/3; Storm; set 10009) :: Fanfare: summon a Dread Pirate's Flag, then advance the counts of all allied Dread Pirate's Flags by 5. Storm.
     -> 令人战栗的海盗旗 / Dread Pirate's Flag :: Countdown (7). Whenever you play a spell, advance the count by 1. Last Words: deal 2 damage to the enemy leader.
1x [10] 武皇的变貌·贝尔铁佐 / Beltezore, Valorous Revenant (2/12; Ward,Storm,Bane,Aura; set 10009) :: Storm, Bane, Ward, Aura. Can attack 3 times per turn.
total 40
```
Game8 text (the page is thin: headings are only デッキレシピ / 評価 / みんなの評価 / マリガン — no 回し方, 対面, キーカード, 弱点 sections exist) [V2, 3 fetches]:
- 評価見出し「海賊旗を盤面に貯めてバルバロスでバースト」: 「海賊ロイヤルはミッドレンジとコンボの中間にあるデッキです。海賊旗を盤面に貯めて、バルバロスに進化を切ることで最大15点のダメージが出せます。」 (Between midrange and combo; stack flags, evolve Barbaros for up to 15 dmg.)
- マリガン: 共通 = 旧き天剣・イドメタ、海域の斥候、渦潮の砲手、栄耀なる麗金花 / 低コストとセット = 逆行の咎人・バルバロス. 「マリガンはあくまで一例です」.

## A2. beyond-dexel — テンジンさん「CR瞬間2位」 — https://beyond-dexel.com/deck-royal-20261006/ — 公開 2026-10-06 (post-patch) [hash V1, content V2]
URL: https://shadowverse-wb.com/ja/deck/detail/?hash=1.2.cEZs.cEZs.cEZs.dmj6.dmj6.dmj6.dmyk.dmyk.dmyk.e9Ak.e9Ak.e9Ak.e9NO.e9NO.e9NO.eXnu.eXnu.eXnu.evi-.evm6.evm6.fIcu.fgIM.fgIM.fgIM.fgX-.fgX-.fgX-.fgb6.fgb6.fgnc.fgnc.fgnc.fgqk.fgqk.fgqk.fh1E.fh1E.fh1E.fh1O
```
format 1 class 2
3x [1] 须臾剑士 / Flashstep Quickblader (1/1; Storm; set 10000) :: (no script)
2x [1] 无音的包围 / Orchestrated Silence (spell; ; set 10007) :: Add a Steelclad Knight to your hand and give it Rush. Rally (10): add 2 instead.
3x [2] 古旧天剑·伊德梅塔 / Yidmetra, Eld Sword (1/2; ; set 10006) :: Fanfare: add a Depths of the Eld Sword to your hand. Evolve: reduce your faith's value by 5 to give it the +1/+1 ability.
     -> 天剑深渊 / Depths of the Eld Sword :: Select an enemy follower and deal it 1 damage. Enhance (1): 3 instead.
1x [2] 听略谍报兵 / Sharp-Eared Operative (2/1; ; set 10007) :: Last Words: summon a Knight. Evolve: select an enemy follower and deal it 3 damage.
3x [2] 海域斥候 / Open-Sea Scout (2/2; ; set 10009) :: Fanfare: summon a Dread Pirate's Flag. Evolve: add a Gilded Boots to your hand.
     -> 令人战栗的海盗旗 / Dread Pirate's Flag :: Countdown (7). Whenever you play a spell, advance the count by 1. Last Words: deal 2 damage to the enemy leader.
     -> 黄金之靴 / Gilded Boots :: Select an allied follower and give it +1/+0 and Rush.
3x [3] 荣耀的丽金花 / Splendor of the Goldbloom (spell; ; set 10005) :: Add 2 Glittering Gold to your hand. Enhance (5): add 4 instead.
     -> 闪耀的金币 / Glittering Gold :: Mode: 1. Draw a card. 2. Deal 2 damage to a random enemy follower.
3x [3] 漩涡炮手 / Whirlpool Gunner (4/2; Rush; set 10009) :: Fanfare: summon a Dread Pirate's Flag and add a Gilded Goblet to your hand. Rush.
     -> 令人战栗的海盗旗 / Dread Pirate's Flag :: Countdown (7). Whenever you play a spell, advance the count by 1. Last Words: deal 2 damage to the enemy leader.
     -> 黄金之杯 / Gilded Goblet :: Restore 2 defense to your leader.
2x [3] 燃尽之缘 / Severed Ties (spell; ; set 10009) :: Select an enemy follower and deal it 5 damage. If this card's cost is 3, add a Severed Ties to your hand and set its cost to 1.
     -> 燃尽之缘 / Severed Ties :: Select an enemy follower and deal it 5 damage. If this card's cost is 3, add a Severed Ties to your hand and set its cost to 1.
3x [4] 真红与群青·塞达&贝阿朵丽丝 / Zeta & Bea, Crimson and Blue (3/2; Rush; set 10004) :: Fanfare: summon a Zeta & Bea. Enhance (6): give it Bane and this follower Storm. Rush.
     -> 真红与群青·塞达&贝阿朵丽丝 / Zeta & Bea, Crimson and Blue :: Fanfare: summon a Zeta & Bea. Enhance (6): give it Bane and this follower Storm. Rush.
3x [4] 黄金时代 / L'Age d'Or (spell; ; set 10009) :: Summon a Dread Pirate's Flag and deal 2 damage to all enemy followers. Enhance (6): summon 2 and deal 4 instead.
     -> 令人战栗的海盗旗 / Dread Pirate's Flag :: Countdown (7). Whenever you play a spell, advance the count by 1. Last Words: deal 2 damage to the enemy leader.
3x [5] 丽金花·云庆 / Unkei, Goldbloom (2/4; ; set 10005) :: Fanfare: select an enemy follower and banish it; add a Glittering Gold to your hand. Super-Evolve: gain Crest: Unkei, Goldbloom.
     -> 闪耀的金币 / Glittering Gold :: Mode: 1. Draw a card. 2. Deal 2 damage to a random enemy follower.
3x [5] 波涛副船长 / Roughwater First Mate (3/3; ; set 10009) :: Fanfare: select an enemy follower and deal it 3 damage; summon a Dread Pirate's Flag. Evolve: replicate the Fanfare. Super-Evolve: add a Gilded Blade and a Gilded Necklace to your hand and set their costs to 0.
     -> 令人战栗的海盗旗 / Dread Pirate's Flag :: Countdown (7). Whenever you play a spell, advance the count by 1. Last Words: deal 2 damage to the enemy leader.
     -> 黄金短剑 / Gilded Blade :: Select an enemy follower or the enemy leader and deal it 1 damage.
     -> 黄金项链 / Gilded Necklace :: Select an allied follower and give it +0/+1 and Ward.
3x [6] 真王之刃·黄金骑士 / Golden Knight, True King's Blade (6/6; ; set 10004) :: Fanfare: Mode: 1. Super-evolve this follower. 2. Deal 4 damage to all enemy followers. 3. Restore 4 defense to your leader. Enhance (8): all of them.
3x [7] 逆行的罪人·巴巴洛丝 / Barbaros, Rebellious Convict (4/3; Storm; set 10009) :: Fanfare: summon a Dread Pirate's Flag, then advance the counts of all allied Dread Pirate's Flags by 5. Storm.
     -> 令人战栗的海盗旗 / Dread Pirate's Flag :: Countdown (7). Whenever you play a spell, advance the count by 1. Last Words: deal 2 damage to the enemy leader.
1x [8] 焦灼炎将·玛尔斯 / Mars, Conflagrant Commander (1/5; Storm,Bane; set 10008) :: Fanfare: 3 Knights. Entering Officer allies: +2/+0, Rush; this +1/+0. Super-Evolve: a Knight.
1x [10] 武皇的变貌·贝尔铁佐 / Beltezore, Valorous Revenant (2/12; Ward,Storm,Bane,Aura; set 10009) :: Storm, Bane, Ward, Aura. Can attack 3 times per turn.
total 40
```
Diff vs Game8 list (from decodes): 無音の包囲 3→2, 燃え落ちる縁 3→2, +1 聴略の諜報兵, +1 焦がれし炎将・マーズ; everything else identical (3 黄金の騎士, 1 ベルテゾール).
- コンセプト: 「序盤のアグロと10PP前後の強力なフィニッシュを両立した、盤面を取れるミッドレンジ」. 盤面を確保しながらライフを削り、「焦がれし炎将・マーズ」「武皇の変貌・ベルテゾール」「逆行の咎人・バルバロス」でリーサルを狙う.
- マリガン最優先: 「刹那のクイックブレイダー」「海域の斥候」「旧き天剣・イドメタ」「聴略の諜報兵」「無音の包囲」「渦潮の砲手」「波濤の副船長」; 手札全体のバランス確認後「栄耀なる麗金花」「アージュドール」を検討.
- キーカード: マーズとベルテゾールは各1枚 — 組み合わせで「守護対策」と「直接打点」の両立.
- 不採用: 「迷夢の獅子・モルドレッド」（以前3枚→現在0枚）: 「進化権の重要性が高まった。フィニッシャーへの進化か盤面フォロワーへの進化に枠を使うため、手札疾走に3PPを割くと動きが固くなる」.
- 対面別:
  - vs連携ロイヤル: 「後攻の場合は、相手の『寛厳の音帥・セザール』とどう向き合うかが重要になります。」 エクストラPPを使ってバルバロスを進化させライフを詰める.
  - vsミラー: 「相手の最大打点をしっかり確認し、リーサルがない場面では基本的に『黄金の首飾り』を温存します。」 (相手の後攻6ターン目バルバロスを防ぐ)
  - vsドラゴン: 「中盤の進化権の節約を特に意識する（リーサルが見えた場合は、進化権を出し惜しみしない）。」 ライフを詰めて相手にEPを使わせる.
  - vsコントロール: 「『波濤の副船長』の超進化と『武皇の変貌・ベルテゾール』の超進化を組み合わせることで、20点のOTK」.
  - 弱点 section: not found in fetch.

## A3. note — もとやしき「【BEYOND＆瞬間1位】アズヴォルト・レヴナント環境 海賊ロイヤル雑記」 — https://note.com/motoyqsiki/n/nf5fb40f65b00 — 公開 2026-09-01 19:16 (PRE-PATCH; partly paywalled ¥300) [V1–V2]
- 成績: 「最高CR2235（花酔遊戯前半最終4位）最終BEYOND×4」 (+ title claims 瞬間1位).
- No hash URL on page (image only) [V2].
- Concept: 「『戦慄の海賊旗』を並べて『逆行の咎人・バルバロス』の超打点での削り切りを狙うコンボアグロデッキ」; 先攻7ターン・後攻6ターンで最大15点、準備すれば20点OTK.
- Key line: 「リーサル意識とスペルの温存が重要」「8ppでの『波濤の副船長』後に『天剣の深淵』『輝く金貨』を使うことで最速での『逆行の咎人・バルバロス』効果発動時に『戦慄の海賊旗』が割れるようにする」.
- マリガン共通: 「『刹那のクイックブレイダー』+2コストフォロワー計3枚まで」「『渦潮の砲手』『波濤の副船長』『逆行の咎人・バルバロス』各1枚」.
- List [UNVERIFIED — summarizer gave 37 cards and mis-typed spells/followers]: クイックブレイダー3, 聴略の諜報兵3, 海域の斥候3, 迷夢の獅子・モルドレッド3, 渦潮の砲手3, アージュドール3, 麗金花・ウンケイ3, 波濤の副船長3, バルバロス3, 焦がれし炎将・マーズ2, 二等分の日常2, 燃え落ちる縁3, ゼタ＆ベアトリクス3 (+3 unknown).
- Matchup table [V1, summarizer paraphrase with quoted card names]:
  - コンボエルフ: keep 低コスト横で【アージュドール】; 波濤の副船長超進化で次のリーサル準備をすれば大体勝てる; 【香風の変貌・ヒエン】は【麗金花・ウンケイ】で対処.
  - ミラー: keep 2コスト横で【迷夢の獅子・モルドレッド】; 副船長超進化が優秀、【決意の輝竜・アーサー】がバルバロスケア; 「このリストはミラー有利」.
  - 実験体ウィッチ: keep 低コスト2枚横で【燃え落ちる縁】; 【万術の咎人・セフィー】盤面はウンケイ or 副船長超進化＋1コスト燃え落ちる縁で返す.
  - ランプドラゴン: 単キープ+モルドレッド、2コスト横でゼタ＆ベア; 【禁牙の変貌・ノマグダラ】回復モードを一回に抑える; マーズに【黄金の首飾り】付与で【律する《正義》・イランツァ】着地キャンセル.
  - ミッドレンジナイトメア: 2コスト横でアージュドール; 序盤は顔を詰めてアージュドールで取り返す; 【淵底の大佐】はウンケイ.
  - アミュレットビショップ: 単キープ+モルドレッド、2コスト横でゼタ＆ベア; 【アドアマネージャー・イニシア】への対処はゼタ＆ベアのみ; 相手手札がパンパンなら面を空にして【旧き天書・リアントース】着地キャンセル.
  - AFネメシス: 2コスト横で燃え落ちる縁; 【弾哭の変貌・アイズエデン】にはウンケイ超進化; 【尽小花・イマリ】展開はエンハンスアージュドール.

## A4. GameWith — https://gamewith.jp/shadowverse-wb/573927 (海賊ロイヤル), /573272 (バルバロス評価): HTTP 403 on every attempt. NOT RETRIEVED.
## A5. onj wiki 「海賊旗ロイヤル！海賊王に俺はなる！！！！」 (最終更新 2026-10-06 20:23) — EUC-JP page came back garbled; card names unreadable. NOT USABLE.

## A6. Variants summary (Pirate)
- Game8 (9/30): spell-heavy 3x Silence/Ties/Splendor/L'Age, 3x Golden Knight, 1 Beltezore, no Mars.
- テンジン (10/06): −1 Silence, −1 Ties, +1 聴略の諜報兵, +1 マーズ (1 Mars + 1 Beltezore as finishers); 3 Golden Knight.
- もとやしき (9/01, pre-patch): 3 モルドレッド, 3 諜報兵, 2 マーズ, 2 二等分の日常, no Golden Knight/Beltezore (unverified). Post-patch players dropped モルドレッド (dexel explicitly) and adopted 6-cost 黄金の騎士 x3 after the buff.

==========================================================================
# B. 連携ロイヤル (Synergy / Rally Royal)
==========================================================================

## B1. Game8 — https://game8.jp/shadowverse-beyond/781940 — 最終更新日：2026.09.30 12:35 — Tier 2 (ミッドレンジ) [hashes V2]
### 前寄せデッキリスト (必要エーテル 80,330)
URL: https://shadowverse-wb.com/ja/deck/detail/?hash=1.2.cEZs.cEZs.cEZs.dmyk.dmyk.dmyk.e8x6.e8x6.e8x6.eXnu.eXnu.evTW.evTW.evTW.evi-.evi-.evi-.evj8.evj8.evj8.evm6.evm6.evm6.evyc.evyc.evyc.ewCE.ewCE.ewCE.ewCO.ewCO.ewCO.fHts.fHts.fIck.fIck.fIck.fIcu.fIcu.fIcu
```
format 1 class 2
3x [1] 须臾剑士 / Flashstep Quickblader (1/1; Storm; set 10000) :: (no script)
3x [1] 无音的包围 / Orchestrated Silence (spell; ; set 10007) :: Add a Steelclad Knight to your hand and give it Rush. Rally (10): add 2 instead.
3x [2] 温柔援军 / Serenity's Shield (spell; ; set 10005) :: Summon 2 Knights. Enhance (4): summon 4 instead.
2x [2] 古旧天剑·伊德梅塔 / Yidmetra, Eld Sword (1/2; ; set 10006) :: Fanfare: add a Depths of the Eld Sword to your hand. Evolve: reduce your faith's value by 5 to give it the +1/+1 ability.
     -> 天剑深渊 / Depths of the Eld Sword :: Select an enemy follower and deal it 1 damage. Enhance (1): 3 instead.
3x [2] 听略谍报兵 / Sharp-Eared Operative (2/1; ; set 10007) :: Last Words: summon a Knight. Evolve: select an enemy follower and deal it 3 damage.
3x [3] 传调联络兵 / High-Strung Liaison (2/3; ; set 10007) :: Fanfare: summon a Knight and add a Steelclad Knight to your hand.
3x [4] 真红与群青·塞达&贝阿朵丽丝 / Zeta & Bea, Crimson and Blue (3/2; Rush; set 10004) :: Fanfare: summon a Zeta & Bea. Enhance (6): give it Bane and this follower Storm. Rush.
     -> 真红与群青·塞达&贝阿朵丽丝 / Zeta & Bea, Crimson and Blue :: Fanfare: summon a Zeta & Bea. Enhance (6): give it Bane and this follower Storm. Rush.
3x [4] 统音的安纳提玛·吉尔达利娅 / Gildaria, Anathema of Attunement (4/4; ; set 10007) :: Fanfare: Rally (20): crest, evolve. Your turn: entering allies get Rush. Evolves: 2 Steelclads.
3x [5] 斩奏医护兵 / Metronomic Medic (2/3; ; set 10007) :: Fanfare: draw 2 cards, summon 2 Knights. Evolve: 3 damage to an enemy follower.
3x [5] 响爪分队长 / Knellclaw Lieutenant (3/2; ; set 10007) :: Fanfare: summon 3 Knights, then Mode: other allies +1/+0 and Rush, or +0/+1 and Ward.
3x [5] 天命的子弹·巴妮&巴隆 / Bunny & Baron, Fate's Bullet (4/4; Rush; set 10008) :: Fanfare: summon a copy; Rally (20): 4 to the enemy leader. Rush. Evolve: add Desperados' Shot.
     -> 天命的子弹·巴妮&巴隆 / Bunny & Baron, Fate's Bullet :: Fanfare: summon a copy; Rally (20): 4 to the enemy leader. Rush. Evolve: add Desperados' Shot.
     -> 亡命者的枪击 / Desperados' Shot :: Twice: deal 4 damage to a random enemy follower.
3x [7] 宽严的音帅·塞扎尔 / Cesar, Accordant Major (5/7; Ward; set 10007) :: Fanfare: 2 Steelclads; other Swordcraft allies +1/+3, Ward. Super-Evolve: destroy an enemy.
2x [7] 武力与治安·娜哈特·娜哈特&宾森特 / Naht & Vince, Force and Order (5/4; ; set 10008) :: Fanfare: summon a Naht's Henchman, 3 damage to all enemy followers. Super-Evolve: do it again.
3x [8] 焦灼炎将·玛尔斯 / Mars, Conflagrant Commander (1/5; Storm,Bane; set 10008) :: Fanfare: 3 Knights. Entering Officer allies: +2/+0, Rush; this +1/+0. Super-Evolve: a Knight.
total 40
```
### 後ろ寄せデッキリスト
URL: https://shadowverse-wb.com/ja/deck/detail/?hash=1.2.dhqm.dmyk.dmyk.dmyk.dmyu.dmyu.dmyu.eXnk.eXnk.eXnu.eXnu.eXnu.evTW.evTW.evTW.evi-.evi-.evi-.evj8.evj8.evm6.evm6.evm6.evyc.evyc.evyc.ewCE.ewCE.ewCE.ewCO.ewCO.ewCO.fIck.fIck.fIck.fIcu.fIcu.fIcu.fh1O.fh1O
```
format 1 class 2
3x [1] 无音的包围 / Orchestrated Silence (spell; ; set 10007) :: Add a Steelclad Knight to your hand and give it Rush. Rally (10): add 2 instead.
1x [2] 掌握天空命运的少女·露莉亚 / Lyria, Skydestined (1/1; Barrier; set 10004) :: Enhance (8): draw a follower that costs 7 or more, then recover 7 play points. Barrier.
3x [2] 古旧天剑·伊德梅塔 / Yidmetra, Eld Sword (1/2; ; set 10006) :: Fanfare: add a Depths of the Eld Sword to your hand. Evolve: reduce your faith's value by 5 to give it the +1/+1 ability.
     -> 天剑深渊 / Depths of the Eld Sword :: Select an enemy follower and deal it 1 damage. Enhance (1): 3 instead.
3x [2] 听略谍报兵 / Sharp-Eared Operative (2/1; ; set 10007) :: Last Words: summon a Knight. Evolve: select an enemy follower and deal it 3 damage.
3x [3] 传调联络兵 / High-Strung Liaison (2/3; ; set 10007) :: Fanfare: summon a Knight and add a Steelclad Knight to your hand.
3x [4] 真红与群青·塞达&贝阿朵丽丝 / Zeta & Bea, Crimson and Blue (3/2; Rush; set 10004) :: Fanfare: summon a Zeta & Bea. Enhance (6): give it Bane and this follower Storm. Rush.
     -> 真红与群青·塞达&贝阿朵丽丝 / Zeta & Bea, Crimson and Blue :: Fanfare: summon a Zeta & Bea. Enhance (6): give it Bane and this follower Storm. Rush.
3x [4] 十天众统领·希耶提 / Seofon, Leader of the Eternals (4/3; ; set 10004) :: Fanfare: Skybound Art: evolve all unevolved allies (itself too); Super: super-evolve them.
3x [4] 统音的安纳提玛·吉尔达利娅 / Gildaria, Anathema of Attunement (4/4; ; set 10007) :: Fanfare: Rally (20): crest, evolve. Your turn: entering allies get Rush. Evolves: 2 Steelclads.
2x [5] 斩奏医护兵 / Metronomic Medic (2/3; ; set 10007) :: Fanfare: draw 2 cards, summon 2 Knights. Evolve: 3 damage to an enemy follower.
3x [5] 响爪分队长 / Knellclaw Lieutenant (3/2; ; set 10007) :: Fanfare: summon 3 Knights, then Mode: other allies +1/+0 and Rush, or +0/+1 and Ward.
3x [5] 天命的子弹·巴妮&巴隆 / Bunny & Baron, Fate's Bullet (4/4; Rush; set 10008) :: Fanfare: summon a copy; Rally (20): 4 to the enemy leader. Rush. Evolve: add Desperados' Shot.
     -> 天命的子弹·巴妮&巴隆 / Bunny & Baron, Fate's Bullet :: Fanfare: summon a copy; Rally (20): 4 to the enemy leader. Rush. Evolve: add Desperados' Shot.
     -> 亡命者的枪击 / Desperados' Shot :: Twice: deal 4 damage to a random enemy follower.
2x [6] 惨烈的剑王·罗德诺艾尔四世 / Noel IV, Ruthless Warlord (4/5; ; set 10006) :: Fanfare: Bane soldier; Enhance (7): +Drain one; (8): +Storm one. Super-Evolve: others +1/+1.
     -> 勇烈的士兵 / Fearless Soldier :: Enhance (3): give this follower +1/+1. Rush.
3x [7] 宽严的音帅·塞扎尔 / Cesar, Accordant Major (5/7; Ward; set 10007) :: Fanfare: 2 Steelclads; other Swordcraft allies +1/+3, Ward. Super-Evolve: destroy an enemy.
3x [8] 焦灼炎将·玛尔斯 / Mars, Conflagrant Commander (1/5; Storm,Bane; set 10008) :: Fanfare: 3 Knights. Entering Officer allies: +2/+0, Rush; this +1/+0. Super-Evolve: a Knight.
2x [10] 武皇的变貌·贝尔铁佐 / Beltezore, Valorous Revenant (2/12; Ward,Storm,Bane,Aura; set 10009) :: Storm, Bane, Ward, Aura. Can attack 3 times per turn.
total 40
```
(Game8 page text listed ロードノエル四世×3 for this list — sums to 41; the hash decodes to 2. Trust the hash.)
JP name map: 優しき援軍=Serenity's Shield, 聴略の諜報兵=Sharp-Eared Operative, 調伝の連絡兵=High-Strung Liaison, 統音のアナテマ・ギルダリア=Gildaria, 斬奏の衛生兵=Metronomic Medic, 響爪の分班長=Knellclaw Lieutenant, 天命の弾丸・バニー＆バロン=Bunny & Baron, 寛厳の音帥・セザール=Cesar, 焦がれし炎将・マーズ=Mars, 武力と治安・ナハト＆ヴィンセント=Naht & Vince, 空の命運を握る少女・ルリア=Lyria, 十天衆の頭目・シエテ=Seofon, 凄烈の剣王・ロードノエル四世=Noel IV.

Game8 text verbatim [V2]:
- 概要: 「連携ロイヤルは横並びの盤面で戦うデッキです。序盤からフォロワーの展開を続けて、連携20達成で発動するギルダリアのクレストとサンダルフォンを合わせて削り切りを狙います。」 (NB: mentions サンダルフォン which is in neither list — stale text.)
- 立ち回り 「序盤からフォロワーを押し付ける」: 「序盤から低コストフォロワーを押し付けて、相手に処理を強要し続けるデッキです。進化可能ターンまでの盤面を取り返す能力は低いため、序盤では常に盤面の有利を取り続ける意識でプレイしましょう。」
- 「中盤以降は場に残ったフォロワーで削る」: 「相手がフォロワーを処理しきれず場に残ったら、連携20を目指しながら体力を削りましょう。場にフォロワーが残った時のセザールは特に強力です。」
- 「マーズから一気に攻め立てる」: 「8PPのマーズから一気に攻め立てましょう。マーズで連携20を達成し、そのあとはバニー＆バロンやギルダリアの連打で試合を決めに行きます。」
- マリガン 「序盤から動けるようにマリガン」: 「序盤から連携を稼ぎやすい低コストカードをキープしていきます。特に優しき援軍は2コストでも4コストでも使えるため優先度の高いカードです。」 共通キープ: 無音の包囲、聴略の諜報兵、優しき援軍.
- 「低コストとセットで5コストのカードをキープ」: 「序盤の動きが確保できている場合は、中盤で使用するカードをキープしましょう。5コストのカードは連携を稼ぎやすく、ゲームを有利に進めることができます。」 セット: 斬奏の衛生兵、響爪の分班長.
- No 対面/キーカード/入れ替え/弱点 sections on page [V2].

## B2. note — ホヤ「【BEYOND到達！】純連携ロイヤル簡易解説！」 — https://note.com/452745274527527/n/n6a67ddb4489f — 2026-07-09 (第8弾期, PRE-pack-9; old) [V1]
- 「マーズ8点、ギルダリア＋バニバロ8点の9ターン16点ラインを基準にして、打点と連携数を計算しながら詰めていく」
- 疾走打点系: クイブレ、ランドル、ゼタベア、マーズ、ケンタウロス / 連携稼ぎ系: 諜報兵、連絡兵、分班長、ギルダリア
- マリガン: 「序盤のマナパスは敗北に直結します。マリガンはソフトにいきましょう」 先攻共通: クイブレ、無音、諜報兵、連絡兵、レポーター; 後攻追加: イドメタ、ギルダリア
- 対面 (old meta): ランプドラゴン 微有利, 魔手ウィッチ 微有利, 進化ビショップ 不利 (「順当に動かれるとほぼ負けです」), ミラー 微不利（先攻有利）.

## B3. GameWith — https://gamewith.jp/shadowverse-wb/559138 — fetched but content stale/unrendered (最終更新 shows "0", no hash, mentions シエテ/サンダルフォン/新ギルダリア, 入れ替え候補「彼我の調律」「空の命運を握る少女ルリア」「颶風の天業グリームニル」, "Tier S"). [UNVERIFIED / likely old pack]. GameWith Tier page 497197 also stale (連携ロイヤル Aランク(Tier2)).
## B4. Community: livedoor まとめ 2026-08-26 https://shadowversewb.livedoor.blog/archives/16868215.html — 「これベルテゾールだけ連携ロイにいれるのがつよくなーい？」 (Beltezore splash into Synergy — matches Game8 後ろ寄せ ×2).
## B5. Pirate-player view of the matchup: dexel テンジン — 後攻ではセザール対処が鍵 (see A2).

## B6. Variants (Synergy)
- 前寄せ: 3 Quickblader, 3 Silence, 3 優しき援軍, 2 イドメタ, 3 諜報兵, 3 連絡兵, 3 Zeta, 3 Gildaria, 3 Medic, 3 Lieutenant, 3 B&B, 3 Cesar, 2 ナハト＆ヴィンセント, 3 Mars.
- 後ろ寄せ: drops Quickblader/援軍/ナハト, −1 Medic; adds ルリア1, シエテ3, ロードノエル四世2, ベルテゾール2, イドメタ 3.

## Not retrieved / limitations
- GameWith deck pages: 403 (all). YouTube descriptions: rate-limited (429) — https://www.youtube.com/watch?v=G3mC6aUselQ not read. appmedia/altema: no Royal pages found for this pack.
- No aggregate win-rate/usage statistics exist in any fetched source.
