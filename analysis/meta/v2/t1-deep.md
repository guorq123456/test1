# T1 deep-dive, second pass: Nightmare / Combo Elf / Pirate Royal / Face Dragon
Collected 2026-10-07 by WebFetch/WebSearch, with the local card DB (/home/claude/sv/svsim/cards/data/rotation.json plus script docstrings) used as a cross-check.
This file only adds to /mnt/project-files/shadowverse/meta-research-2026-10-07/ and does not repeat it.

**Tags**
- [V2]: two independent fetches or sources agree, or one verbatim fetch agrees with the local DB.
- [V1]: one fetch only.
- [UNVERIFIED]: suspect or conflicting.
- [INF]: my own inference or arithmetic.

**Pages that failed this pass**
- YouTube (www.youtube.com/watch?v=96gfa507NUc, "【1位達成！】少しやりすぎてしまった上方修正！「海賊旗ロイヤル」…デッキ&マリガン&立ち回り解説") returned HTTP 429 (rate limited, told not to retry). No YouTube description was read.
- GameWith (573927 Pirate, 558820 鹿王, 558802 徒姫) returned 403 every time.
- svwbmeta.com returned 403.
- onj wiki 海賊旗ロイヤル (updated 2026-10-06 20:23) still comes back as garbled EUC-JP and is unusable.
- coolyu's second note is paywalled (¥400).
- shadowverse-magazine card pages return 404 for pack-7 card IDs (107xxxxx). They work for pack-8 and pack-9 IDs.

**Main finding:** I found no new post-09-29 player guide for Midrange Nightmare, Combo Elf or Face Dragon. The only post-patch player guide for any of the four decks is still テンジン's Pirate page (dexel, 2026-10-06). beyond-dexel deck pages from 2026-09-01 to 2026-10-07 are: nightmare 0829 / 0909 / 0925, elf 0901 / 0906 / 0929, dragon 0917, royal 1006, witch 0908 / 0911. There is no dexel nightmare page dated after 09-25.

---

## 1. ラストワード / ミッドレンジナイトメア

### 1.1 Card text, verbatim JP
- **傍死のアナテマ・徒姫** (6 cost; DB stats 5/4; Anathema), from Game8 https://game8.jp/shadowverse-beyond/781904 (updated 2026-09-11 17:04), [V2: two fetches identical, matches DB]
  - 進化前: 「【ファンファーレ】自分のデッキのコスト2以下のナイトメア・フォロワーからランダム2種類を自分の場に出す。自分の他のナイトメア・フォロワーが場に出たとき、それは【突進】を持つ。」
  - 進化後: 「【超進化時】自分の場の他のナイトメア・フォロワーすべては+2/+2する。」
  - It has no cost-reduction text.
  - Notes [INF]:
    - It pulls 2 *differently named* ≤2-cost followers. That thins out リリム / ラズ / 中尉 and fills the board at once.
    - The Rush aura works only while 徒姫 is on the field.
    - Super-evolve is a one-shot +2/+2 to whatever is on board at that moment. It is not an aura.
- **イステンデッドVSマルチルゲート**: crest text is already [V2] in nightmare-witch.md. Game8 crest list https://game8.jp/shadowverse-beyond/698642 (updated 2026-09-30) gives the same text again: 「自分のターン終了時、自分の場に【ラストワード】を持つカードがあるなら、自分の場の【ラストワード】を持つカードからランダム1枚と相手の場のフォロワーからランダム1枚を破壊。」 [V2]
  - The crest has **no countdown**, so it stays for the rest of the game. [V2: two sources show no カウントダウン]
  - [INF] It destroys your own Last Words card, so that card's Last Words fires each turn. 幽冥の中尉 comes back as a 2/1 Rush. 淵底の大佐 destroys another random enemy and heals 2. 腐臭のゾンビ makes a new zombie. The crest therefore usually trades 1-for-2 or better every turn.
- **デッドプレゼンター・マクミラン** (9 cost, 4/4), from Game8 https://game8.jp/shadowverse-beyond/781881 (updated 2026-09-30 12:35), [V2: two fetches]
  - 進化前: 「【ファンファーレ】【ネクロマンス_10】『腐臭のゾンビ』3枚を自分の場に出す。自分の死者・フォロワーが場に出たとき、自分のターンなら、それは+1/+0して【突進】と【守護】を持つ。相手のリーダーに1ダメージ。」
  - 進化後: 「-」 (no evolve text).
  - Game8 rating SS: 「進化権を使わずに盤面へ干渉できる」, works with 徒姫.
  - **The trait is 死者 (EN "Departed"), not 亡者.** [V2: second fetch confirmed the character]
- **Which followers are 死者**:
  - スケルトン, タイプ 死者: Game8 https://game8.jp/shadowverse-beyond/698743 [V1]. Local DB: Skeleton, Departed [V2].
  - 腐臭のゾンビ, タイプ 死者: Game8 https://game8.jp/shadowverse-beyond/706551 [V1 + DB = V2].
  - ゴースト / 怨霊 (Ghost) is Departed in the DB only [V1 DB; Game8 page did not state its type].
  - No non-token 死者 follower exists in the rotation pool (DB scan of rotation.json) [V1 DB].
  - In these lists, 死者 come from:
    - トラブルネクロマンサー (FF: Ghost + Skeleton; evolve: Zombie)
    - デーモンドラム・ラズ (LW: Skeleton)
    - タイトロープキャット (FF: Skeleton)
    - 腐臭のゾンビ's own LW
    - マクミラン's FF (3 zombies). Each one deals 1 to face and gets Rush and Ward when it enters on your turn. Macmillan itself is therefore at least 3 face damage, plus 3 Rush/Ward 3/2 zombies. [INF: arithmetic]
- **旧き天眼・ビバティー** (4 cost, Legend, type アサイラント), from shadowverse-magazine https://shadowverse-magazine.com/svwb/cardpack/all-cards/c10654120/ [V1 + DB = V2]
  - 「【ファンファーレ】【ネクロマンス_4】これは進化する。 ーーー これが進化したとき、『天眼の深淵』1枚を自分の手札に加える。」 『天眼の深淵』 = draw 2 (DB).
  - [INF] The trigger is worded 「これが進化したとき」, not 【進化時】. Per the Game8 glossary, 【進化時】 = 「EP（進化権）を使用して進化した時に発動」. So the Necromancy self-evolve does draw 2 without spending EP.
- **幽冥の中尉** (2 cost, bronze), from shadowverse-magazine c10951120 [V1 + DB = V2]: 「【ラストワード】『幽冥の中尉』1枚を自分の場に出す。それは+1/+0して【突進】を持つ。それは【ラストワード】を失う。」
- **キュートな悪魔・リリム** (1 cost, bronze), from shadowverse-magazine c10851120 [V1 + DB = V2]: 「【攻撃時】リーダーすべてに1ダメージ。【ラストワード】『バット』1枚を自分の手札に加える。」 Its self-damage helps reach the Garodeth line.
- 「ガロダートVSゼット」: text already [V2] (in-hand discount at the end of your turn while your leader's HP is ≤12; Storm mode costs 2 self-damage).

### 1.2 Super-evolve: 徒姫 or イステンデッド?
No source states a rule directly. Here is what the sources do say:
- ふじのん (dexel, Midrange Nightmare 最速BEYOND, published 2026-08-29, updated 2026-09-02; pre-patch, but it is the closest list to Game8's) https://beyond-dexel.com/deck-nightmare-20260829/ [V1, quotes under 100 chars]:
  - 結論: 「大佐で盤面強化→場残りから徒姫で展開→ガロダートvsゼットの高打点で押し切る」
  - ワンポイント: 「淵底の大佐の結晶を徒姫の超進化に合わせる」
  - The crystal trick, [V2: two fetches]: 「5ターン目に結晶が割れるため、『タイトロープキャット』と組み合わせられます」. In full, going second you spend the extra PP on turn 1 to crystallize 淵底の大佐 (countdown 4). It breaks on turn 5, so the 4/6 Ward appears next to an evolved Tightrope Cat, and on turn 6 徒姫 super-evolve pumps that board.
  - 「イステンデッド VS マルチルゲート」は2枚採用：「3枚目は使い勝手が悪く感じた」. Prioritise it in the keep only vs Nemesis.
  - Decoded hash: Game8's list minus 1 Istyndet, 1 『最強』の魅惑 and 1 Lilith Enchanting, plus 3 淵底の大佐 and 2 イツルギ＆タケツミ. It has 3 徒姫, 3 マクミラン and 3 ガロダート.
    `1.5.cM8E.fPCm.fPCm.fPCm.f0oG.f0oG.f0oG.fndG.fndG.fndG.dtoY.dtoY.dtoY.eGCk.eGCk.eGCk.f1KU.f1KU.f1KU.ef6e.ef6e.f11k.f11k.f11k.f1W-.f1W-.f1W-.fnsk.fnsk.fnsk.foL-.foL-.fPxU.fPxU.foM8.foM8.foM8.f1X8.f1X8.f1X8`
- nyantan (2026-08-29, already in notes): 「T7 イステンデッド超進化 or ガロダート by situation」. nyantan ?p=3409 (Azvaldt build): T6 徒姫 SE, then T7 イステンデッド SE.
- [INF] Synthesis:
  - On the 徒姫 turn (6PP), super-evolve 徒姫 when the board already has 2 or more Nightmare followers. The FF adds 2 more, so +2/+2 is on 4 or more bodies and becomes a tempo and lethal setup.
  - Save the super-evolve for イステンデッド (7PP) when the game will go long. The crest is permanent, so it is worth more each extra turn, and it is best with Last Words bodies already in play.
  - Both are 超進化, and super-evolve points are limited. Standard practice in the sources is 徒姫 on T6, then イステンデッド on T7 if the game is still a board fight, or ガロダート/マクミラン burn if not.
  - vs Nemesis, ふじのん prefers keeping イステンデッド (AoE 2 + crest vs wide/必殺 boards).

### 1.3 Managing your own HP for ガロダート (≤12)
- 女神 (dexel Aggro Nightmare CR瞬間1位, published 2026-09-09) https://beyond-dexel.com/deck-nightmare-20260909/ [V2: two fetches with matching quotes]:
  - 「『ガロダートVSゼット』は自分のライフが12点以下になるとコストが下がる効果を持っています。」
  - 「この性質を利用して、相手フォロワーを無視してリーダーを攻撃するよう誘導したり」
  - 「あえて『炸裂』をお互いがダメージを受ける形で使用したりするのも覚えておくとよいテクニックです。」 (炸裂 = 残虐な炸裂, 3 damage to the leader(s) with the lowest HP)
  - 「12点ラインを気にしながら攻める場面が増え、その際は『誠実なる呪い屋・スージー』などでバフをしたフォロワーで一気にライフを削るのが有効です。」
  - vs Nightmare mirror: 「12点ラインの管理を優先する」
  - vs Witch: 「ガロダートで仕留めるプランを軸にする」
  - vs Dragon: 「1コストを全力で探す」
- nyantan (already in notes): 激烈の副総長 helps reach ≤12, but 「過度な自傷は禁物」.
- [INF] Rules mechanics:
  - The discount checks at the end of **your** turn, −1 each time.
  - Being at ≤12 at the end of T5, T6 and T7 makes Garodeth 5 cost by T8, so you could play Garodeth plus another card in one turn.
  - In the Midrange list the only self-damage sources are キュートな悪魔・リリム's attack ping and Garodeth's own Storm mode (2 to self). The Midrange deck mostly reaches ≤12 by letting the opponent hit face (女神's 「相手フォロワーを無視してリーダーを攻撃するよう誘導」).
  - vs Pirate (Barbaros up to 15 to 20 burst) and Face Dragon, sitting at 12 is dangerous. Against them, prefer the Ward mode (8 to all enemy followers), and don't go out of your way to take damage.

### 1.4 Mulligan by matchup (best available; none is post-patch)
- ふじのん (08-29):
  - 全対面: 1～2コストフォロワー, タイトロープキャット, 元素の共鳴・バアル.
  - 後攻 add: トラブルネクロマンサー, 淵底の大佐 (extra-PP crystal on turn 1).
  - vs ネメシス: イステンデッド VS マルチルゲート. [V2: two fetches]
- silvervine (09-14): go all-out for 1-costs (already in notes).
- Game8 698647 (old 7th-pack Midrange list, still updated 2026-09-30): 「どの対面に対しても序盤の動きとして強力なラズとリミルは優先的にキープ」, and on the evolve turn 「タイトロープキャット進化を優先」. Game8 811839 (the T1 page) still has **no** mulligan, play or matchup text, and 0 comments. [V2]
- とりっぴよー (Aggro, 09-25) [V1]:
  - Keep リミル in every matchup.
  - vs Nightmare: keep 夜の唱のライブ alone.
  - vs Dragon: early cards plus ガロダート.
  - vs Dust Days Elf: 「セタス＆メイシア」 needs a lethal already set up.
- Matchup notes from the opponents' guides (Nightmare's perspective, [INF] inverted):
  - **vs Pirate Royal** (もとやしき, pre-patch): the Pirate plan is to hit face early and swing back with アージュドール, and to answer 淵底の大佐 with ウンケイ (banish, so its LW doesn't trigger).
    - So for Nightmare: Ward bodies and Last Words stickiness blunt Pirate's board, but keep HP above Barbaros range. Banish (ウンケイ) is the specific counter to 大佐 and イステンデッド value.
  - **vs Ramp Dragon** (味噌日, 09-17): Dragon's plan is an early 炎の理・ウィルナス (keep HP ≥7 so it survives), else race with サガツマツ before the long game.
    - So for Nightmare: kill or chump Wilnas fast. Dragon keeps 波揺花 on the draw vs Nightmare. Ramp keeps 狐火陽炎 as a 1-cost removal for Nightmare's 1-HP bodies.
  - **vs Combo Elf** (yukki note, 2026-08-31): 「ミッドレンジナイトメアに対しても10戦して5勝5敗でした。」 hqzuki: Hien's only clear use is vs Nightmare.
    - So Elf with ヒエン builds is the version Nightmare should fear. Spicies says vs midrange the Elf player saves super-evolve and sweeps with マガチヨ.
  - **vs Face Dragon**: coolyu calls ミッドメア 不利 for Face (「序盤が強くバットが強すぎる」). Favourable for Nightmare.
  - **vs Sephie Witch**: Witch players call Nightmare their bad matchup (はせ, already in notes).

---

## 2. コンボエルフ (ダストデイズ)

### 2.1 Card text, verbatim JP
- **操嵩のアナテマ・ダストデイズ** (4 cost; DB 3/3), Game8 https://game8.jp/shadowverse-beyond/781891 (updated 2026-09-30 12:35), [V2: two Game8 fetches plus the Game8 crest list 698642, matches DB]
  - 進化前: 「【ファンファーレ】相手の場のフォロワー1枚を選ぶ。それは-0/-Xする。Xはこれの攻撃力である。自分の【コンボ】を+1する。」
  - 進化後: 「【進化時】自分は『クレスト：操嵩のアナテマ・ダストデイズ』を持つ。」
  - **Crest:** 「【カウントダウン_3】 自分のターン終了時、【コンボ_3】自分のデッキのフォロワーすべては+1/+1する。」
- **Your questions, answered:**
  - **How many turns:** countdown 3, so at most 3 end-of-turn triggers.
  - **End of turn?** Yes, 「自分のターン終了時」, and only if Combo 3 that turn.
  - **Does the turn it is gained count?** Yes, the crest can fire at the end of the same turn Dust Days evolves. Evidence:
    - yukki note https://note.com/yuki_svwb/n/n71098fc3e434 (2026-08-31; 50 games, 27-23, 54%): 「重要なのは、ダストデイズを進化したターンからクレスト効果を起動することです。」 and 「そのターンに起動できなければ、バフ1回分を損することになります。」 [V1 verbatim; agrees with Game8 「進化と同時に1コストカード使用でコンボ3達成が目標」 → V2]
    - The arithmetic [INF]: countdown drops at the start of your turn (Game8 glossary https://game8.jp/shadowverse-beyond/697567: 「ターン開始時にカウントが1つ減り、0になったら破壊される。」). Gained on turn N, the crest fires at the end of N, N+1 and N+2, then hits 0 at the start of N+3.
    - The standard play is Dust Days on 5PP: Dust Days (4PP, card 1, plus its own +1 combo) with evolve, then any 1-cost card (card 2). That is Combo 3 on the same turn.
  - **Re-gaining the crest:** Game8 crest guide https://game8.jp/shadowverse-beyond/696009 (user-comment level, [V1]): a later copy of the same countdown crest overwrites the earlier one and resets it to 3. Max 5 crests.
  - **[INF] Caveat:** 【進化時】 = 「EP（進化権）を使用して進化した時」 (Game8 glossary). So evolving Dust Days through 天槍の深淵 (旧き天槍・ササニド) or other effect-evolves should *not* grant the crest. Not tested in any source.
- **離合の有終・セタス＆メイシア** (7 cost, Legend, 第8弾), shadowverse-magazine https://shadowverse-magazine.com/svwb/cardpack/all-cards/c10814110/ [V1 + DB = V2]
  - 「【ファンファーレ】相手の場のフォロワー1枚を選ぶ。それを破壊。自分の場の他のフォロワーすべては+1/+1する。 ーーー 【疾走】 【守護】」
  - **No evolve or super-evolve text.** Super-evolving it only adds stats and keywords from super-evolution. DB stats are 4/6. hqzuki's 「超進化は…イランツァ対策」 means super-evolving it to attack through, not an effect.
- **香風の変貌・ヒエン** (9 cost, Legend, 第9弾), shadowverse-magazine c10914120 [V1 + DB = V2]
  - 「手札で働く。自分がカードをプレイしたとき、ターン終了まで、これのコストを-1する。 ーーー 【ファンファーレ】相手の場のフォロワー1枚を選ぶ。それに4ダメージ。 ーーー 【ラストワード】『香風の変貌・ヒエン』1枚を自分の場に出す。」
  - No evolve text. The discount lasts this turn only, so you need about 5 cards played before it in one turn to cast it on 4PP, and so on. The Last Words copy also has Last Words (no 「失う」 clause), so it keeps returning. [INF]
- **氷界の鹿王** (6 cost; DB 5/5), Game8 crest list 698642 [V1 + DB = V2 in substance]
  - 「【ファンファーレ】『森の神秘』2枚を自分の手札に加える。自分のターン終了時、相手の場のフォロワーすべてにXダメージを割りふる。Xはこれの攻撃力である。」
  - Super-evolve gives the crest: 「【カウントダウン_3】自分のターン終了時、【コンボ_3】『森の神秘』1枚を自分の手札に加える。」 (森の神秘 = 1-cost "heal leader 1" spell, i.e. a free combo enabler.) The exact 【超進化時】 line was not captured verbatim. yukki: the super-evolve target is usually 鹿王, 「森の神秘」 for recurring combo fuel.

### 2.2 Post-patch Elf vs Pirate
- **No post-09-29 Elf-side source discusses Pirate.** Spicies (dexel, 09-29, the patch day) only says vs midrange (「エルフ、ロイヤル、ナイトメア、ネメシスなど」) to save super-evolve, sweep with マガチヨ and heal with ササニド. A re-fetch found no 海賊 / バルバロス mention. [V2]
- Pre-patch evidence:
  - yukki (08-31): Pirate Royal is listed among the matchups where Combo Elf 「比較的良い戦績を残せています」. W-L numbers are image-only. [V1]
  - もとやしき (Pirate POV, 09-01): Pirate wins with 低コスト横で【アージュドール】 keeps and 副船長 super-evolve setting up lethal (「大体勝てる」), and handles ヒエン with ウンケイ (banish beats its Last Words). [V1]
  - silvervine (09-30): Pirate and Cutthroat 「結局はダストデイズエルフにわからせられる」.
  - The two sides contradict each other, so I would call the matchup roughly even, slightly Elf-favoured, before the patch. [UNVERIFIED]
- [INF] What the patch changed: 渦潮の砲手 is now 4/2 Rush and 海域の斥候 is 2/2. That hurts the Elf's 1-damage pings and splits (虫風花の飛翔 3-split, ミロク 3-split) and Fairy trades. Pirate's early board now survives Elf's cheap removal more often. Elf's answer is the Combo-3 マガチヨ AoE (4 to all), which still clears 4/2 and 2/2.
- Tier context: Game8 (10-07) has both decks at T1. ICS Singapore (09-26/27, pre-patch) top 32 had 18 Combo Forest and 1 Sword.

---

## 3. 海賊ロイヤル

### 3.1 Flag countdown and treasure tokens
- 戦慄の海賊旗, Game8 https://game8.jp/shadowverse-beyond/811031 (updated 2026-09-30 15:09): 「【カウントダウン_7】自分がスペルをプレイしたとき、これのカウントを-1する。【ラストワード】相手のリーダーに2ダメージ。」 [V2 with svlabo / DB]
- **Countdown ticks at the start of your own turn.** [V2]
  - Game8 glossary: 「ターン開始時にカウントが1つ減り…」.
  - Lilie note https://note.com/lilie_lily/n/n93fb320d2e3f (2026-09-03) computes damage with 「ターン開始時の旗割れ2枚×2点」. Flags left at count 1 at the end of your turn break at your next turn start, before you act.
  - The local DB rules doc agrees (吟唱: "每个己方回合开始时 -1").
- **Treasure tokens are all spells (タイプ: 財宝), so each one advances every flag by 1.**
  - 黄金の小剣 (the JP name is **小剣**, not 短剣): Game8 https://game8.jp/shadowverse-beyond/712986, スペル, 財宝, cost 1. 「相手の場のフォロワー1枚か相手のリーダーを選ぶ。それに1ダメージ。」 [V1 + DB]
  - 黄金の杯: Game8 712987, スペル, 財宝, cost 1. 「自分のリーダーを2回復。」 [V1 + DB]
  - 黄金の靴: Game8 712988, スペル, 財宝, cost 1. 「自分の場のフォロワー1枚を選ぶ。それは+1/+0して【突進】を持つ。」 [V2: two fetches + DB]
  - 黄金の首飾り: Game8 712989, cost 1. 「自分の場のフォロワー1枚を選ぶ。それは+0/+1して【守護】を持つ。」 The summarizer twice called it アミュレット, but the raw table has no type row, and the DB says spell (Loot). The targeting text matches the other treasure spells. Treat it as a **spell**. [UNVERIFIED: the amulet claim looks like a summarizer error]
  - So 渦潮の砲手 (杯), 海域の斥候 evolve (靴) and 副船長 super-evolve (小剣 + 首飾り at cost 0) each bring their own flag tick. 輝く金貨 (栄耀なる麗金花 / ウンケイ) is also a spell.
- **Barbaros burst math**, Lilie (2026-09-03, pre-patch), [V1 verbatim]: 「理論上は7PPで20点(残カウント1の旗2枚を含む旗5面で前ターンを終え、ターン開始時の旗割れ2枚×2点+バルバロス設置分を含む旗4枚×2点+バルバロス超進化7点+0コスト小剣1点)」
  - Breakdown: 4 (2 flags break at turn start) + 8 (Barbaros adds a 4th flag, −5 breaks all 4) + 7 (super-evolved 4/3 Barbaros) + 1 (0-cost 小剣) = 20.
  - Realistic output: 「11～15点程度」 (paraphrase).
  - Game8's "up to 15 with evolve" is a lower, more practical ceiling.
  - Also: 「ちなみに旗2枚に0コス小剣またはEXPPクイブレが絡めば20点OTKも見えてくる」.

### 3.2 Evolve text
- 武皇の変貌・ベルテゾール: Game8 811748 (updated 2026-09-30) gives 進化前 「【疾走】【必殺】【守護】【オーラ】1ターンに3回攻撃できる。」 and **進化後: no additional text**. [V2: two Game8 fetches + svlabo + DB]
  - Lilie: 「アクセラレートもコスト軽減も持たない10コストなので順当に回れば基本的に使う事はない」 but 「幾度となくベルテゾールに救われている」 (long games).
- 逆行の咎人・バルバロス: no evolve text [V2, in royal.md]. Super-evolved = 7 attack per Lilie, i.e. super-evolution gives +3/+3 [INF].

### 3.3 テンジン's 「副船長超進化＋ベルテゾール超進化で20点OTK」
- The source sentence is only (dexel 2026-10-06, [V2]): 「『波濤の副船長』の超進化と『武皇の変貌・ベルテゾール』の超進化を組み合わせることで、20点のOTK（ワンターンキル）が可能です。」 The page gives no step-by-step.
- [INF] A reconstruction that fits the card texts:
  - **Turn N (5PP+):** super-evolve 波濤の副船長.
    - FF + evolve-replicate: 3 damage twice and 2 flags.
    - Super-evolve adds 黄金の小剣 and 黄金の首飾り to hand **at cost 0**. Hold both.
  - **Turn N+1 or later (10PP):** play ベルテゾール (10PP; Storm, Bane, Aura, 3 attacks) and super-evolve it.
    - 2/12 → 5/15, 3 face attacks = **15**.
    - 0-cost 小剣 to face = **1**.
    - The two 0-cost spells (小剣 + 首飾り) tick every flag down by 2. Any flag at count ≤2 breaks for 2 damage each. You need 2 such flags for **4**, giving 15 + 1 + 4 = 20.
    - Older flags can be pre-ticked by earlier spells (金貨, アージュドール is itself a spell, 燃え落ちる縁).
  - Why it is "vs control": Beltezore cannot ignore Ward. You need the opponent's board free of Ward, or cleared first. Its Aura stops targeted removal before attacks.
  - The 首飾り on Beltezore is just a flag tick (it already has Ward). Alternatively, keep 首飾り for the mirror defence that テンジン recommends (「リーサルがない場面では基本的に『黄金の首飾り』を温存」).
  - Not confirmed by any source. Super-evolve +3/+3 is inferred from Lilie's 「バルバロス超進化7点」.

### 3.4 Post-patch guides beyond テンジン
- I found none with text.
  - Game8 811814 (09-30) still has only list, mulligan and a 15-damage blurb, and 0 comments.
  - YouTube 96gfa507NUc is a post-patch Pirate guide by title ("少しやりすぎてしまった上方修正！…1位達成"), but it was not readable (429).
  - 水野五郞 notes (mizugoro0489) are rants, not guides, and their dates were not checked.
  - onj wiki was updated 10-06 but is garbled.
  - livedoor まとめ's newest post is 09-27 (patch announcement reactions, no matchup talk).
- Matchup notes available:
  - **vs Ramp Dragon**
    - テンジン (post-patch): 「ライフを詰めて相手にEPを使わせる。中盤の進化権は節約し、リーサルが見えたら惜しまず使う。」
    - もとやしき (pre): limit ノマグダラ's heal mode to one use. Put 黄金の首飾り on マーズ to "cancel" the イランツァ landing (Ward forces Erntz's end-of-turn damage onto Ward? the exact meaning is [UNVERIFIED]).
    - Ramp side (いろは 09-15): key cards vs 旗ロイヤル are ノマグダラ and イランツァ.
  - **vs Combo Elf:** no post-patch text. Pre-patch: see §2.2.
  - **vs Face Dragon:** coolyu's paywalled note (2026-09-06) heading: 「対海賊ロイヤル:イドメタ次第」. Its first note said 旗ロイヤル 5分.

---

## 4. フェイスドラゴン

### 4.1 JP names, verbatim, shadowverse-magazine (all [V1 verbatim + DB = V2])
| Decoder (CN/EN) | JP name | Cost | Text |
|---|---|---|---|
| 碎裂的盗匪 / Ripper-Clawed Thief | **寸裂の盗人** (not 裂爪の盗人) | 1 | 「【ファンファーレ】直前の自分のターンに自分のフォロワーがリーダーを攻撃していたなら、これは【疾走】を持つ。ーーー【ラストワード】『寸裂の盗人』1枚を自分の手札に加える。それは【ラストワード】を失う。」 (c10941110) |
| 利牙 / Artiglio | **ウンギア** | 2 | 「相手の場のフォロワーすべてに3ダメージを割りふる。直前の自分のターンに自分のフォロワーがリーダーを攻撃していたなら、3ダメージではなく6ダメージ。」 (c10943310) |
| 幼龙闹脾气 | **幼竜の癇癪** | 1 | 「『ベビーファイアドレイク』1枚を自分の場に出す。【エンハンス_3】相手の場のフォロワーからランダム1枚に3ダメージ。」 (c10941310) |
| 绝倒的袭击者 | **絶倒の襲撃者** | 2 | 「【疾走】 【攻撃時】直前の自分のターンに自分のフォロワーがリーダーを攻撃していたなら、ターン終了まで、これは+1/+0する。」 (c10942110) |
| 尘土的不法者 | **塵土の無頼漢** | 5 | 「【ファンファーレ】「相手の場のフォロワーからランダム1枚に4ダメージ。」を1回行う。直前の自分のターンに自分のフォロワーがリーダーを攻撃していたなら、1回ではなく2回。ーーー【進化時】『絶倒の襲撃者』1枚を自分の場に出す。」 (c10943110) |
| 穿孔的罪人·安缇马丽亚 | **穿孔の咎人・アンテマリア** | 7 | 「【ファンファーレ】直前の自分のターンに自分のフォロワーがリーダーを攻撃していたなら、これは【疾走】を持つ。ーーー【突進】【守護】を無視して攻撃できる。」 (c10944110) |

Other names already in elf-dragon.md: 顎門の別れ, 天刀授与, 断頭の天刀, クラゲの舞姫, 旧き天刀・ヴォーラライ, 笑顔の調理・キミカ, 怠惰なる波揺花, 断頭の斬姫・サガツマツ.

### 4.2 Post-patch lists and guides
- **No post-09-29 list or guide was found.**
  - Game8 698337 (Tier 2, updated 09-30) is still the latest list.
  - coolyu's second note 「9弾フェイスドラゴン使い方ガイド」 https://note.com/coolyu338867/n/ne06523d3da5d (2026-09-06 09:59, ¥400 paywall) has this table of contents: このデッキの強みについて / 勝ち方とそれに沿った構築について / 先攻:無理な攻めを通す / 後攻:eppと進化権の使い方がカギ / 試合の流れから逆算して打点を通す / 共通マリガン / **対DDエルフ:五分** / **対海賊ロイヤル:イドメタ次第** / … (rest truncated). [V1]
  - Note that the first coolyu note called Elf 「1番のカモ」, but this one says 五分.
- Ladder evidence: shadowverse-wins (Dragon, season 69) has 1 Face Dragon streak after the patch, Sirius 13連勝 on 2026-10-03. The other 9 entries from 10-03 to 10-07 are Ramp or unlabelled Dragon. [V1]

---

## Sources (this pass)
- beyond-dexel:
  - Home and tier list (tier list last modified 2026-09-27)
  - deck-nightmare-20260829 (ふじのん, 08-29 / 09-02)
  - deck-nightmare-20260909 (女神, 09-09)
  - deck-nightmare-20260925 (とりっぴよー, 09-25)
  - canvas-nightmare-01 (pack-8, 07-25 / 08-15: old)
  - deck-royal-20261006 (テンジン, 10-06)
  - deck-elf-20260929 (Spicies) and deck-elf-20260906 (NARU), re-checked
- Game8:
  - Cards: 781904 徒姫 (09-11), 781881 マクミラン (09-30), 781891 ダストデイズ (09-30)
  - Crest and keyword pages: 698642 crest list (09-30), 696009 crest rules (2025-11-21), 697567 keyword glossary
  - Tokens: 698743 スケルトン and 706551 腐臭のゾンビ (09-30)
  - Pirate: 811031 海賊旗 (09-30), 712986 / 712987 / 712988 / 712989 treasure tokens (09-30), 811748 ベルテゾール (09-30)
  - Decks: 811839 / 698647 / 700068 (Nightmare; 700068 is stale, 04-14), 811814 Pirate, 784381 (Treasure Royal, not relevant)
- shadowverse-magazine card pages: c10654120, c10951120, c10851120, c10814110, c10914120, c10941110, c10943310, c10944110, c10943110, c10942110, c10941310
- note.com:
  - Lilie 海賊旗ロイヤル (2026-09-03)
  - yukki コンボエルフ50戦 (2026-08-31)
  - みあ ダストデイズ変更案 (2026-07-20)
  - coolyu 9弾フェイスドラゴン使い方ガイド (2026-09-06)
  - hieroglyph (2025-08-23) and itsukakoyoi (2025-08-09), both old and irrelevant
- shadowverse-wins.com Dragon (fetched 10-07)
- nyantan homepage: no post-patch Shadowverse posts. Newest SV post is 09-04 (死神払い).
- livedoor まとめ: newest post 09-27.
