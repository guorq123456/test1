# Highlander (Cutthroat) Nemesis and AF Nemesis after the 2026-09-29 patch — deep dive
Compiled 2026-10-07. This adds to `/mnt/project-files/shadowverse/meta-research-2026-10-07/nemesis-bishop.md` and does not repeat it: the Game8 lists and their decodes, the patch texts for Cutthroat, 放逐 and ハクガ, and the older AF guides are all in that file.

Tags:
- [V2] = confirmed twice, either by two sources or by two differently worded fetches of the same page.
- [V1] = one fetch only.
- [UNVERIFIED] = I could not confirm it.
- [INF] = my own inference from card text or the numbers.

All web text came through the WebFetch summarizer.

---
## 0. Key findings (read this first)
1. **The tournament build of Cutthroat Nemesis is not the Game8 list.** At JCS 2026 Season 3 (preliminaries 10/3–4), 5 of the 12 players whose decks were confirmed for Playoff or Grand Finals brought Cutthroat Nemesis. That is 5 of 24 decks, 20.8%, second only to ダストデイズエルフ at 29.2%. Four of those five reached the Grand Finals. All five lists are close to the same ~34-card core. That core is an **aggro / Artifact singleton** deck: Lyria plus Aizeden or Camiscilla, Sandalphon, Scarlet, and the Myuu/Broadcaster/Eudie Artifact package. **None of them run Zerael or Azvaldt. Only one runs Beelzebub (リンド), and none runs Olivia.** The "cost 1–8 direct summon" plan from the Game8 list (2026-09-30) was dropped by every competitive and ladder list I found. [V2: beyondmeta.jp/jcs fetched twice, same hashes both times]
2. Ladder data (beyondmeta.jp, 122 posts of streaks and rank reaches since 9/29 17:00): 海賊ロイヤル 27%, ミッドレンジナイトメア 12%, **カットスロートネメシス 10%** (12 posts, plus 4 more tagged ハイランダーネメシス), ランプドラゴン 10%. **AFネメシス has 0 posts after the patch.** Before the patch (9/1–9/29) it had more than 25. [V1]
3. **Bane check:** Cutthroat is the only Nemesis follower with 【必殺】 in the Game8 list and in all 7 post-patch lists. So its evolve draw and 屈辱なる放逐 can only find another Cutthroat. The draw "always" finds one only while a Cutthroat is still in the deck; if all 3 have left the deck, it draws nothing. Details are in §2.1. [V2]
4. **The crest does NOT trigger 【進化時】.** Game8 says verbatim: 「なお、カードの効果で進化する場合は発動しません。」 Its glossary says: 「EP（進化権）を使用して進化した時に発動。」 [V2]. A Yahoo Q&A answer agrees (about super-evolution through Olivia). The exception: cards whose text says 「これが進化したとき」 rather than 【進化時】. Asher & Lydia is one. Their ability should fire on a crest evolve. [INF, strong]
5. Cutthroat's evolved stats are not printed on any page I could read. Evolving gives +2/+2 (Game8 696356), so **evolved Cutthroat should be 3/3 with Bane**. [INF from the rule]
6. AF Nemesis was overtaken: Highlander lists absorbed its whole core (Myuu, Aizeden, Scarlet, Broadcaster, Eudie, Courier, Isaac, Imari, A&L, Camiscilla, Ordnance). AF still gets streak posts (Alice 7, じゃす 7, SHU 5/7). じゃす's post: **「AF進化ネメシス…対カッティス7戦全勝」** (7–0 against Cutthroat) — 「強カード3枚積んだ方が強い」 (running 3 copies of strong cards is stronger). [V1]

---
## 1. Sources (with dates)
| Source | Date | What it gave |
|---|---|---|
| beyondmeta.jp/jcs — JCS 2026 Season 3 | prelims 10/3–4, GF 10/25 | 24 confirmed Playoff/GF decks with hashes; 5 are Cutthroat [V2] |
| beyondmeta.jp (feed) and /meta | data from 9/29 17:00 to 10/8 00:51 | share %, result tier, 2 ladder Cutthroat hashes (パンドラ 10/6, うずまき 10/3) [V2 on hashes] |
| beyondmeta.jp/archive | 9/1–9/29 | pre-patch: many AF Nemesis posts, 1 Cutthroat |
| note ミホノブルボ 「地頭によるカッスロ基礎ノート（勝率73%）」 https://note.com/fine_murre880/n/n88bac5cb59fc | 2026-10-05 20:44 | build philosophy, the 後7 Lyria line, cut list [V1–V2 per quote] |
| shadowverse-wins.com, rotation Nemesis pages 1–2 and entry pages (single.php?manageId=109024/26/42/58/61/37/39/43/59/81/82) | 9/29–10/6 | player comments [V1 each] |
| shadowverse-magazine card pages (c10974110 Cutthroat, updated 10/3; Imari, Myuu, Aizeden, Scarlet, A&L, Camiscilla, Ordnance, tokens, Lyria, Zerk, Bluerust, 侵略されし世界, ゴッズレポーター, Eudie, Broadcaster, 誠心なる尽小花, Isaac) | various | verbatim JP texts |
| Game8 811028 (Cutthroat, 9/30), 698639 (超進化時 list, 9/30 14:23), 697567 (glossary), 696356 (evolution rules), 696222/696114 (mulligan/rules), 698622 (必殺 list, 9/30), 764055 (ブライトクリエイター, 9/30), 764057 (Ordnance, 9/30), 794080 (A&L, 9/30), 811776 (Zerael, 9/30), 811034 (Azvaldt, 8/26), 732577 (Sandalphon, 9/30), 732594 (奥義 gauge, 9/30), 789262 (AF counter guide, 9/30 but stale content) | — | rules and texts |
| appmedia 79441424 Sandalphon | 2025-10-29 | 【解放奥義】 label, stats 7/6 → 9/8 → 10/9 |
| beyond-dexel tier list | 2026-09-27 (pre-patch) | AF Nemesis Tier 2 [V2 with the existing notes] |
| YouTube (titles only; every watch page returned 429) | — | see §1.1 |

**Not available:**
- beyond-dexel.com/deck-nemesis-20260929 … 20261007: **all 9 dates returned 404**. The Dexel front page lists no Nemesis guide after 9/17; its newest deck articles are Royal 10/06, Elf 9/29, Nightmare 9/25 and Dragon 9/17.
- GameWith 573928 and its comments: 403.
- X posts: fxtwitter and vxtwitter are blocked by robots.txt.
- The おんJ wiki Highlander page (updated 2026-09-25, pre-patch) came back garbled because of its EUC-JP encoding.

### 1.1 YouTube titles found (no descriptions could be read)
- 「【シャドバWB】能力調整で魔改造された結果『カットスロート』超絶強化で遂に環境入りしたハイランダーデッキ 『カッスロネメシス』がマジで強過ぎるwww」 https://www.youtube.com/watch?v=jJFnZ_5huXU
- 「【改良版】ネオジオが強すぎる件。BEYOND帯でも重宝した話題のカード採用カットスロートネメシス【シャドバWB】」 https://www.youtube.com/watch?v=L8yWyrXBaSo ("ネオジオ" = ネオジオグラファー / New-Age Cartographer)
- 「【シャドバWB】JCS直前！PS選手によるカットスロートネメシス解説」, channel **LVH / Era53** (from oEmbed) https://www.youtube.com/watch?v=8J_LldZIiw0
- 「【シャドバWB】害悪戦法で海賊を返り討ち‼要塞型のハイランダーネメシスがヤバすぎる」 https://www.youtube.com/watch?v=T7hPbG0b_Po (a defensive "fortress" build that beats Pirate)
- Pre-patch ones: lH8ob0adF4E, EjCg5BdsVEo, t806-soA7CM, tMjK4CwzCIw, 3wE_KGIrR6I.

---
## 2. Rules and mechanics checks

### 2.1 Bane (【必殺】) — the claim "Cutthroat is the only Bane Nemesis follower in the list"
- Game8's 必殺 card list (698622, updated 2026-09-30) names these Nemesis cards: ハートスローター・フィア (2), 束刃の咎人・カットスロート (1), オートマタアサシン (3), 獣性の鉄人 (6), ブライトクリエイター (6), プロシードハート・オーキス (8).
  - **ブライトクリエイター does not have Bane itself.** Its text is 「【ファンファーレ】『デストロイアーティファクトα』1枚を自分の場に出す。それは【必殺】と【守護】を持つ。」 It is on the list only because it gives Bane to a token. [V2: Game8 764055 + simulator data]
  - **獣性の鉄人** (Mechanized Beast, 6-cost Ward + Bane, basic set) is rotation-legal according to the simulator data. It is **not in any of the lists**.
  - フィア, オートマタアサシン and オーキス are not in the rotation pool of the simulator data, and are in none of the lists.
- **Game8 list (9/30):** the Nemesis followers are 青錆の下っ端 (突進), カットスロート (必殺), エース, チルスケーター, マリオネットランサー, 錬磨の用心棒 (守護), 鋳鉄の腹心, 拙劣の人形, 低劣の玩具 (守護), ミリアム, イルザ, カミシラ, アイズエデン, 愚劣の兵器, スカーレット (守護/疾走), ベルゼバブ. **Only カットスロート has 【必殺】.** [V2]
- **JCS and ladder lists:** they add ジルク, イマリ, ヨグゼンタ (突進), アイザック, ワイルドキャスター, ラズリ, 翔 (疾走), スロース (潜伏), ミュー, エッジーマスター, ネオジオグラファー, ツインドローン(?), マリオネットマスター(?), ルオー(?), ブライトクリエイター. **None of these has Bane.** [V2 for the keyword data; some JP names are UNVERIFIED]
- **Precise version of the claim [INF, from the verbatim texts]:**
  - When Cutthroat evolves with EP, the draw always finds another Cutthroat if one is still in the deck. If all 3 are already out of the deck, it draws nothing.
  - **The crest is guaranteed on the first EP evolve of any Cutthroat**, assuming every other card is a single copy. The Cutthroat being evolved is not in the deck. If 2 are left in the deck, the draw removes one, so 1 remains and there is no duplicate. If 0 or 1 is left, there is no duplicate anyway.
  - 屈辱なる放逐 cast with ≥1 Cutthroat already out of the deck always ends with ≤1 in the deck, so its "+2 draw" always fires. With no Cutthroat drawn yet, it tutors one: 2 remain, there are duplicates, and the +2 draw does not fire.
  - **Every no-duplicates payoff is off until 2 Cutthroats have left the deck.** These are 青錆の下っ端 5 dmg, 錬磨の用心棒 4 dmg + 4 heal, 鋳鉄の腹心 Storm, ハクガ燐斂 wipe, and 放逐 +2.
  - 誠心なる尽小花, 侵略されし世界 and Zerk transform or add cards in hand or on the field, so they never create duplicates in the deck.
  - **Game8-list only:** 輪廻転衝 shuffles a copy of the highest-cost destroyed follower into the deck. It can only create a duplicate if that follower is a Cutthroat and another Cutthroat is still in the deck. [INF]
- The crest wording is 「自分がフォロワーをプレイしたとき、自分のターンごとに1回、それは進化する。」 [V2: magazine + Game8]. There is no "may", so **it is mandatory on the first follower you play each turn**. That makes sequencing a real decision (§3.3). [INF from the wording]

### 2.2 Cutthroat stats
- Cost 1, 1/1, Legend, 必殺. The evolve-side text is 【進化時】… [V2: magazine c10974110 updated 2026-10-03 + Game8 811028 updated 2026-09-30]
- **Evolved stats: not printed on any page** (magazine, Game8 and GameWith all omit them). Evolving gives +2/+2 and super-evolving gives +3/+3 (Game8 696356), so **3/3 必殺 evolved and 4/4 super-evolved** [INF].
- Game8 rates it S overall and C for 2Pick. Voice actor 花江夏樹.

### 2.3 Does a crest evolve trigger the played follower's 【進化時】? — **No**
- Game8 698639 (超進化時 list, 2026.09.30 14:23), verbatim: 「なお、カードの効果で進化する場合は発動しません。」 [V1 verbatim]
- Game8 glossary 697567, fetched twice: 進化時 = 「EP（進化権）を使用して進化した時に発動。」 [V2]
- Yahoo!知恵袋 q10316620810 (2025-06): an evolve or super-evolve done by another card (Olivia) does not trigger 進化時 or 超進化時 abilities, 「進化権を消費する進化ではないから」. A conditional or static text such as "if this is super-evolved" still works. [V1]
- **What this means for Highlander:** a crest evolve on エース, チルスケーター, ミュー, ツインドローン, 愚劣の兵器 or ネオジオ only gives stats, plus the evolved form's ability to attack followers that turn. Their 【進化時】 value (another evolve, an Ancient or Analyzing Artifact, the 3-split ping) needs EP. Camiscilla's auto-evolves also do not trigger 【進化時】 (for example, Ordnance's on-evolve ping).
- **The exception is wording-based.** A&L's evolve text is 「これが進化したとき、相手の場の【守護】を持つフォロワーからランダム2枚を破壊。」 [V2: magazine + Game8 794080]. It is not 【進化時】, and its own 【エンハンス_9】これは進化する depends on it firing from an effect evolve. So **a crest or Camiscilla evolve of A&L should destroy up to 2 random enemy Ward followers**, including the one its Fanfare just gave Ward. [INF, strong; not seen in any Q&A]
- **Timing between Fanfare and the crest trigger** (does the target get Ward before A&L is evolved?) is not documented. [UNVERIFIED]

### 2.4 Sandalphon / Zerael / Azvaldt texts and timing
- **Sandalphon (6-cost neutral, 7/6 → 9/8 → 10/9; appmedia + magazine):**
  - 「デッキで働く。自分のターン開始時、このバトル中に自分のフォロワーが進化した回数が6以上なら、これを【直接召喚】する。」 When invoked: you gain the crest and it returns to your hand.
  - Fanfare is **【解放奥義】**: 「相手の場のフォロワーか相手のリーダーからランダム1枚に2ダメージ。」を5回行う。
  - Crest: 【カウントダウン_2】 at the end of your turn, restore 1 to all your followers and your leader. [V2]
- **奥義 gauge** (Game8 732594, verbatim): 「ゲージは『現在のターン数』と『手札にある時に自分のフォロワーが進化・超進化した回数』の合計」. 奥義 needs 10 and 解放奥義 needs 15. [V1 verbatim; the glossary confirms 10/15, V2]
  - So after Sandalphon is invoked and returns to hand, the 5×2 random damage needs turn number + evolutions since it came back ≥15. [INF]
- **Does a crest or effect evolve count toward "進化した回数"?** The wording is generic. Game8 811028 sums up the deck as 「毎ターン進化を稼ぐことで直接召喚効果を活かしやすい」, and Hirobosu wrote 「1コスカットスロートから最速サンダルフォンの動きが強くてパワーを感じる」. Both imply yes. [V1 implied]
  - Whether super-evolutions count as evolutions is [UNVERIFIED].
- **Rules that set the clock** (Game8 696356/696222/696114):
  - Evolve from your turn 5 going first and turn 4 going second. Super-evolve from turn 7 first and turn 6 second.
  - 2 EP and 2 SEP each.
  - **Only one of evolve or super-evolve per turn** (「1ターンに進化と超進化のどちらか1回しかできません」).
  - Opening hand 4 cards, one mulligan of 0–4 cards. [V1–V2]
- **Fastest Sandalphon (6 evolutions) [INF]:**
  - Going second: T4 EP-evolve Cutthroat (1), crest on the next follower (2). T5 crest (3) + EP (4). T6 crest (5) + SEP (6). → **Sandalphon invokes at the start of turn 7.**
  - Going first: T5 (2), T6 (4), T7 (6) → **start of turn 8**.
  - Each extra source moves it up about half a turn. Extra sources: エース EP-evolved evolves another (+1); カミシラ auto-evolves its 2 tokens and any other base-cost-5+ arrival (+2 or more); グラン&ジータ 奥義 self-evolve; A&L 【エンハンス_9】.
  - After the invoke, the 解放奥義 needs about 15 − turn evolutions in hand. In practice the 10-point random burn comes around T9–T10. Earlier, Sandalphon is a 6-mana 7/6 that the crest evolves into a 9/8, plus the heal crest. [INF]
- **Zerael (9-cost neutral, Game8 811776, 9/30):** 「デッキで働く。自分のターン終了時、このバトル中に自分がプレイしたカードの元のコストに1〜8すべてが含まれているなら、これを【直接召喚】する。【ファンファーレ】相手の場のフォロワー1枚を選ぶ。それに9ダメージ。【威圧】」 [V2 with the existing notes]
  - When invoked it is summoned, not played, so the 9-damage Fanfare does not happen [INF].
  - Game8 glossary: 威圧 =「このフォロワーは攻撃されない」 [V1].
- **Azvaldt (8-cost neutral amulet):** 「自分のターン終了時、このバトル中に自分がプレイしたカードの元のコストに1〜8すべてが含まれているなら、これを破壊。【ラストワード】…ランダム4種類…場に出す。自分の場のフォロワーすべては+3/+3する。」 Game8 811034 (dated 8/26) says 「該当するデッキはありません」. [V1]
- **How fast the Game8 list covers costs 1–8 [INF]:** an 8-cost card has to be *played* (Ordnance, Scarlet or Azvaldt itself), so the earliest is the end of turn 8. Accelerating Ordnance might count, since its base cost stays 8, but that is [UNVERIFIED]. The 7 slot (Ilsa, Camiscilla, Miriam, Aizeden) and the 3–4 slots (only 2 cards each in the Game8 list) are the gaps. Realistically you get T8–T10, around when Sandalphon's 解放奥義 and Camiscilla already end games. This is why every competitive list dropped Zerael, Azvaldt, Beelzebub and Olivia and lowered the curve (§3.1).

---
## 3. ハイランダー / カットスロートネメシス

### 3.1 Post-patch lists (all decoded with deck.py; each is 40 cards, 37 singletons + 3 Cutthroat)
Hashes are saved in `research2/hashes.txt`.

| key | player / event | hash |
|---|---|---|
| shoya | しょーや — JCS S3 Grand Finals (paired with DDE) | 1.7.cQnG.cR2I.dhLM.dhqc.dhqm.di4E.dyR6.dyRQ.dyzU.dz9-.e4Gg.eKrc.eL5E.eLN-.eLaU.eLae.eSRY.ejGG.ejlM.ej--.ej_8.eqqU.f5jk.f5wE.f69s.f6PU.f6Pe.fUKu.fUp-.fUq8.fsVc.fsVm.fslE.fsoM.fs-s.ft1-.ftEU.ftEU.ftEU.ftEe |
| mattsu | まっつ (PS/VARREL) — JCS S3 GF (with DDE). **Same hash as パンドラ's ladder BEYOND list (10/6, 15連勝)** | 1.7.cQnG.cR2I.dhqc.dhqm.di4E.dyR6.dyRQ.dyzU.dz9-.eKrc.eL5E.eLN-.eLaU.eLae.eSRY.ejGG.ej--.ej_8.eqqU.f5gc.f5jk.f5wE.f69s.f6PU.f6Pe.fDUc.fU5Q.fUKu.fUp-.fUq8.fsVc.fsVm.fslE.fsoM.fs-s.ft1-.ftEU.ftEU.ftEU.ftEe |
| lind | リンド — JCS S3 GF (with Pirate Royal) | 1.7.cQnG.cR2I.dhLM.dhqc.dhqm.di4E.dyR6.dyRQ.dyzU.dz9-.dzA8.e4Gg.eKrc.eLN-.eLaU.eLae.eSRY.ejG6.ejlM.ej--.ej_8.eqqU.f5jk.f5wE.f69s.f6PU.f6Pe.fU5Q.fUKu.fUp-.fUq8.fsVc.fslE.fsoM.fs-s.ft1-.ftEU.ftEU.ftEU.ftEe |
| saikicker | 斉キッカー — JCS S3 GF (with DDE) | 1.7.cQnG.cR2I.dhLM.dhqc.dhqm.di4E.dyR6.dyRQ.dyzU.dz9-.e4Gg.eKrc.eLN-.eLaU.eLae.eSRY.ejG6.ejlM.ej--.ej_8.eqqU.f5gc.f5jk.f5wE.f69s.f6PU.f6Pe.fU5Q.fUKu.fUp-.fUq8.fsVc.fslE.fsoM.fs-s.ft1-.ftEU.ftEU.ftEU.ftEe |
| massu | まっすー — JCS S3 Playoff, Day2 6-1 (with Ramp Dragon) | 1.7.cQnG.cR2I.dhLM.dhqc.dhqm.di4E.dyR6.dyRQ.dyzU.dz9-.e4Gg.eKrc.eL5E.eLN-.eLaU.eLae.eSRY.ejG6.ejlM.ej--.ej_8.eqqU.f5jk.f5wE.f69s.f6PU.f6Pe.fU5Q.fUKu.fUp-.fUq8.fsVc.fslE.fsoM.fs-s.ft1-.ftEU.ftEU.ftEU.ftEe |
| uzumaki | うずまき — ladder BEYOND 10/3, 「8時間でCR＋300」 | 1.7.e4Gg.fU5Q.fsVc.ftEU.ftEU.ftEU.eLN-.f5jk.fsoM.dhqm.cQnG.dyRQ.eLae.ej_8.f5wE.fUq8.cR2I.dyR6.eLaU.f69s.fUKu.ft1-.dhqc.eKrc.eL5E.f6Pe.fsVm.fslE.dhLM.dz9-.fUp-.fs-s.di4E.ejG6.ejGG.dyzU.ej--.ftEe.ejlM.f6PU |
| game8 | Game8 811840 (9/30) — see the existing notes | (in nemesis-bishop.md) |

**Decoded comparison** (1 = one copy; "." = not in the list). JP names are from magazine or Game8 where checked; "(?)" means the JP name is unverified.

| cost | card | shoya | mattsu | lind | saiki | massu | uzu | game8 |
|---|---|---|---|---|---|---|---|---|
| 1 | 束刃の咎人・カットスロート | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| 1 | 青錆の下っ端 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 屈辱なる放逐 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | ストリートラン (Freerunning) | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 誠心なる尽小花 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 大遊戯世界 | 1 | . | 1 | 1 | 1 | 1 | 1 |
| 1 | デバイスマニピュレーター・ジルク | . | 1 | 1 | 1 | 1 | 1 | . |
| 1 | 尽小花の照臨 / リヴァイブチューニング | . | . | . | . | . | . | 1 each |
| 2 | チルスケーター, アナタの先輩・エース, マリオネットランサー, ドールズシアター | 1 each in all 7 lists |  |  |  |  |  |  |
| 2 | 尽小花・イマリ | 1 | 1 | 1 | 1 | 1 | 1 | . |
| 2 | 報恩の技師・アイザック | 1 | 1 | 1 | 1 | 1 | 1 | . |
| 2 | 空の命運を握る少女・ルリア | 1 | 1 | 1 | 1 | 1 | 1 | . |
| 2 | 旧き天斧・ヨグゼンタ (Yog-Zentha) | 1 | 1 | 1 | 1 | 1 | 1 | . |
| 2 | アイカ (Aika, Elegy of Loss)(?) | . | 1 | . | . | . | . | . |
| 2 | 輪廻転衝 | . | . | . | . | . | . | 1 |
| 3 | ワイルドキャスター | 1 | 1 | 1 | 1 | 1 | 1 | . |
| 3 | ゴッズレポーター (Intrepid Newshound) | 1 | 1 | 1 | 1 | 1 | . | . |
| 3 | 侵略されし世界 (amulet) | 1 | 1 | 1 | 1 | 1 | . | . |
| 3 | ラズリ (Lazuli; gives a Radiant Artifact)(?) | 1 | 1 | 1 | 1 | 1 | 1 | . |
| 3 | 翔 (Sho, Reborn Night King; Storm)(?) | 1 | 1 | 1 | 1 | 1 | 1 | . |
| 3 | スロース (Slaus, 潜伏)(?) | 1 | 1 | 1 | 1 | 1 | 1 | . |
| 3 | ハクガ燐斂 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 3 | ストーン・ブレイク | . | . | . | . | . | . | 1 |
| 4 | 蒼い空を征く騎空士・グラン&ジータ, 錬磨の用心棒 | 1 each in all 7 lists |  |  |  |  |  |  |
| 4 | 奮励の追走・ミュー | 1 | 1 | 1 | 1 | 1 | 1 | . |
| 4 | Marionette Master(?) | 1 | 1 | 1 | 1 | 1 | 1 | . |
| 4 | ネオジオグラファー (New-Age Cartographer) | 1 | 1 | . | . | 1 | 1 | . |
| 4 | Twindrone Engineer(?) | 1 | 1 | . | . | . | 1 | . |
| 4 | エッジーマスター (Brusque Barkeep) | . | 1 | . | 1 | . | . | . |
| 5 | 決断の交差・アシュレイ＆リディア, 鋳鉄の腹心 | 1 each in all 7 lists |  |  |  |  |  |  |
| 5 | Lu Woh, Light Personified(?) | 1 | 1 | 1 | 1 | 1 | 1 | . |
| 5 | Katalina, Sky's Protector(?) | 1 | . | 1 | 1 | 1 | 1 | . |
| 5 | Reina / 《世界》の提示 / 拙劣の人形 | . | . | . | . | . | . | 1 each |
| 6 | 天司長の後継・サンダルフォン, ケイオス・レギオン | 1 each in all 7 lists |  |  |  |  |  |  |
| 6 | 低劣の玩具 | . | . | 1 | 1 | 1 | 1 | 1 |
| 6 | ブライトクリエイター | 1 | 1 | . | . | . | 1 | . |
| 6 | ヘイレムハニィ / 最古の獄卒 / 凡百の製図 | . | . | . | . | . | . | 1 each |
| 7 | 劣悪の純心・カミシラ, 弾哭の変貌・アイズエデン | 1 each in all 7 lists |  |  |  |  |  |  |
| 7 | イルザ / ミリアム | . | . | . | . | . | . | 1 each |
| 8 | 虚刻のアナテマ・スカーレット | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 8 | 愚劣の兵器 | 1 | . | 1 | 1 | 1 | 1 | 1 |
| 8 | 混迷の監獄・アズヴォルト | . | . | . | . | . | . | 1 |
| 9 | 全一の王・ベルゼバブ | . | . | 1 | . | . | . | 1 |
| 9 | オリヴィエ / ゼラエル | . | . | . | . | . | . | 1 each |

- **JCS core: 32 distinct cards = 34 cards** shared by all 5 JCS lists. The remaining 6 slots come from these flex cards:
  - in 4 of 5 lists: カタリナ, 大遊戯世界, 愚劣の兵器, ジルク
  - in 3 of 5: ネオジオグラファー, 低劣の玩具
  - in 2 of 5: ブライトクリエイター, ツインドローン, エッジーマスター
  - in 1 of 5: アイカ, ベルゼバブ
- **Curve** (JCS, per list, cost 1/2/3/4/5/6/7/8): about 8–9 / 8–9 / 7 / 4–7 / 3–4 / 3 / 2 / 1–2. Compare Game8: 10/5/2/2/5/6/4/3, plus 3 nine-drops.
- **Followers costing 7+ (the pool for ルリア's 【エンハンス_8】):** カミシラ, アイズエデン, スカーレット, and 愚劣の兵器 where it is played. **パンドラ/まっつ cut 愚劣 because 「ルリアから引いてきたとき微妙」** (V1, パンドラ via shadowverse-wins + beyondmeta). ミホノブルボ also says 愚劣 is out because 「ルリアからのサーチに引っかかる点が最大の弱点」 [V2, two independent players]. Lyria refunds 7 PP, so an 8-cost hit can't be played that turn.

### 3.2 Build philosophy (note ミホノブルボ, 2026-10-05, BEYOND 帯 and 勝率73%; quotes verbatim through the summarizer)
- The deck is **aggro** — win before the combo decks spike. 「デッキの性質を理解した上で構築を組む方が勝率が高くなる」.
- **The core value line is 後攻7ターン目 (going second, turn 7) + エクストラPP:** 「後7エクピルリア+カミシラorアイズエデンがこのデッキの最大バリューであり、積極的に狙っていきたい。」 and 「後7PP時にエクピを使用し、ルリア（or1コスト）+アイズエデンorカミシラ超進化の動きを実現する為には6PP時にエクピを極力使いたくないのです。」
  - The line: 8 PP → Lyria 【エンハンス_8】 draws a 7+ follower and refunds 7 → a 7-drop plus super-evolve.
- Card notes:
  - ジルク: 「手札を減らさず小粒を横並びが出来る点が非常に強力」
  - アイカ: 「先行の動きと後攻の動きを逆転してくれる」. The author doesn't want to 「マリガンでキープしたカットスロートをハンドに抱えて1パス」 (keep Cutthroat in the mulligan and then pass turn 1 with it in hand).
  - ゴッズレポーター: 「後6PP時にエクピを切らずに超進化を吐き横並びが出来る」. Its super-evolve summons 2 more ゴッズレポーター; its 【ラストワード】 draws 1. [text V2: magazine]
  - ネオジオグラファー: 「エクピを切らずに面を形成出来る」
  - Sandalphon: cited in a リグゼ matchup example for a turn 8–9 activation.
- **Cuts and why:** 低劣の玩具 「単純にドローをしないバニラだと感じた」; ストーンブレイク 「打点を出せれない点がこのデッキ（アグロ）と噛み合っていない」; ブライトクリエイター 「面の圧が弱過ぎる」; 愚劣の兵器 (Lyria search).

### 3.3 Turn plan (my synthesis of the texts, the JCS list and the notes — [INF] unless quoted)
- **T1:** play カットスロート (a 1/1 Bane that trades with anything) or a 1-drop body (ジルク, 青錆 as a 1/1 Rush without the 5 dmg before the deck is singleton). 大遊戯世界 is also fine. Don't sit on Cutthroat (the ミホノブルボ quote above).
- **T2–T3:** curve the 2/3-drops. Priority: イマリ (discard → draw a spell; can find 放逐 or ハクガ), エース and チルスケーター (Artifact tokens raise Scarlet's X), アイザック, ワイルドキャスター (artifacts gain 突進).
  - Cast 屈辱なる放逐 when it is the Cutthroat tutor or you already have one out (then +2 cards).
  - Hold ハクガ燐斂 until the deck is singleton: then 3 PP 「1枚を選ぶのではなくすべて」 destroys every enemy follower.
- **First evolve turn (T4 going second / T5 going first):** **EP-evolve Cutthroat first.** It draws a Cutthroat if one is left, then you get the crest. The deck is now singleton, which turns on 青錆 5 dmg, 用心棒 4 dmg/+4 heal, 鋳鉄 destroy + Storm, ハクガ wipe and 放逐 +2. Then play a follower; the crest evolves it.
- **Crest sequencing (mandatory, first follower each turn):**
  - Lead with the follower that gains most from a free +2/+2 and an immediate attack on a follower. Examples: 鋳鉄の腹心 (5/5 Storm after its Fanfare destroy), A&L (destroys up to 2 Ward followers via 「これが進化したとき」), Lyria (a Barrier body).
  - Don't lead with one whose value is a 【進化時】 you plan to EP (エース, チルスケーター, ミュー, ツインドローン). The crest evolve would waste it, since crest evolves don't trigger 【進化時】.
  - **Before a 7-drop you want to super-evolve** (カミシラ for X face damage, アイズエデン for a second 看守 + destroy), play a cheap follower first so it takes the crest. Can an already-evolved follower be super-evolved at all? [UNVERIFIED — assume not]
  - Only one evolve OR super-evolve per turn, so plan the EP/SEP turns.
- **T6 (going second):** first super-evolve turn. ゴッズレポーター super-evolve makes 3 bodies without spending extra PP (save エクピ for T7).
- **T7 (going second, with エクピ):** ルリア 【エンハンス_8】 → カミシラ or アイズエデン → super-evolve.
  - カミシラ: its Fanfare summons 低劣の玩具 (6) and 拙劣の人形 (5) and auto-evolves both. Super-evolve then deals X to the leader, where X = base-cost-5+ followers on your side (≥3).
  - アイズエデン: 撃針の看守 is an Artifact follower, so it triggers the random destroy; the super-evolve repeats it.
- **Finishers:** サンダルフォン (invokes around T7 going second / T8 going first by the count in §2.4; then a 9/8 body + heal crest; the 10-damage 解放奥義 around T9–T10). スカーレット (Storm + Ward 6/6, AoE X = Artifact types). 鋳鉄 Storm. 翔 Storm. ラズリ's レディアントアーティファクト (Storm). ケイオス・レギオン (3 to all enemies, 6 with 解放奥義 — face damage too).
- Ludicrous Ordnance (lists that run it): 8 PP gives 3 bodies that each ping 3 split at your end of turn. **Accelerate (4)** puts 1 Ordnance into play. The cost is [V2: Game8 764057 + simulator]; the magazine summary said 「コスト1」, which is likely a misread.

### 3.4 Mulligan (by matchup)
- **Game8 (9/30):** 「全対面・先攻後攻問わずキープ」 = カットスロート only.
- **Odds of finding a Cutthroat [INF, my Monte Carlo]:** 4-card hand, ship everything else, 4 draws to the evolve turn.
  - P(a Cutthroat by T4 going second / T5 going first) ≈ **65%** counting only Cutthroats.
  - ≈ **76–79%** counting 屈辱なる放逐 as a fifth out (4 outs).
  - The many Analyzing-Artifact draws, ゴッズレポーター, イマリ (draws a spell, so it can hit 放逐) and グラン&ジータ (mode "2 followers") push it higher.
  - Pre-buff the deck needed one specific card, which is why Hirobosu wrote 「カットスロート引けない試合が激減で使用感◎」.
- **Suggested by matchup** [INF, built on the note and the card roles; no source gives a matchup table]:
  - **Always:** カットスロート, 屈辱なる放逐 (with or without Cutthroat), plus one cheap follower so you don't pass turn 1 or 2 (アイカ / ジルク / エース / チルスケーター / イマリ).
  - **Against aggro** (海賊ロイヤル, アグロナイトメア, フェイスドラゴン): チルスケーター (deals with 3-defense followers, as the Game8 AF guide notes), 錬磨の用心棒 (heal), early bodies. Soulforge is only one-target removal until the deck is singleton.
  - **Against slow decks** (ランプドラゴン, アミュレットビショップ, ダストデイズエルフ): the aggro curve (エース, イマリ, キャスター), 侵略されし世界 against DDE (see §3.5), and going second consider ルリア for the T7 line.

### 3.5 Matchup evidence (all player claims, [V1] unless noted)
- **Pirate Royal (27% of BEYOND/streak posts):** conflicting.
  - Against Highlander: Pirate player らきちゃ, 10/4: 「vsハイランダーネメシスに関しては11戦全勝で、流石にガン有利かもしれない」 (beyondmeta, seen once).
  - For Highlander: Lostwiz (Highlander, 10/5) 「vsロイヤル5連勝 … 押し切るか耐久するかを考える」. YouTube 「害悪戦法で海賊を返り討ち‼要塞型のハイランダーネメシス」 suggests the defensive builds are the ones aimed at Pirate.
  - Net: roughly even, and it depends on the build. [UNVERIFIED]
- **Dust Days Elf:** hatena blog author (existing notes): 「…カットスロートネメシスは安定感が増したが結局はダストデイズエルフにわからせられる」 (DDE beats it). LVH Hirobosu (9/29): good results vs Dust Days thanks to 侵略されし世界, which every JCS list then ran.
  - 侵略されし世界: 「【アクト】自分の手札1枚を選ぶ。それは相手のデッキからランダム1枚のコピーに変身する。」 [V1 magazine]
  - 4 of 5 JCS Cutthroat players paired it with DDE, which suggests they treat DDE as the other best deck rather than a counter. [INF]
- **AF (evolution) Nemesis:** じゃす (10/5) 「AF進化ネメシスで7連勝…このデッキ、対カッティス7戦全勝です。やっぱ強カード3枚積んだ方が強いって」 (7–0 vs Cutthroat).
- **Experiment Witch:** player 萩鷲 (10/3) 「アッパーされた2デッキに対しては特に不利はついてない」 (no bad matchups against the two buffed decks, i.e. Pirate and Cutthroat).
- **All classes:** TREND LAB (9/29, 11連勝 to ULTIMATE): 「ハイランダー使ってて楽しいのとカッスロアッパーで化けました。Tier1あります。ウィッチ／ドラゴン／ネメシス／エルフ／ナイトメア／ビショップ/ロイヤル 全クラス対応可」 (mulligan and play notes were in X replies I could not read).
- **Pre-patch** (note ユキ, 8/29): hard matchups were Nightmare (幽冥の中尉 stacking) and Face Dragon.
- Players say the deck is hard to pilot: 「与えられたハンドで最大値を出すのが難しいけど…攻めと受け両立できる」 (もる, 10/3); 「アドリブプレイ多くて使ってて楽しい」 (パンドラ); 「噛めば噛むほど味がする」 (和田竜洸).

### 3.6 Results and tiers
- **JCS S3:** 5 of 12 players. Cutthroat 20.8% of the confirmed Playoff/GF decks, second to DDE 29.2%. GF: しょーや, まっつ, リンド, 斉キッカー. Playoff: まっすー (Day2 6-1). [V2]
- **beyondmeta Result Tier (since 9/29):** S 海賊ロイヤル 33 posts; A ミッドレンジナイトメア 15; **B カットスロートネメシス 12**, ランプドラゴン 12, 連携ロイヤル 11, 実験体ウィッチ 9, クキシロビショップ 6, ダストデイズエルフ 5, ハイランダーネメシス 4. Nemesis total = 18 of 122 posts (15%). [V1]
- **shadowverse-wins.com (Nemesis, rotation, 9/29–10/6):** Cutthroat/Highlander streaks:
  - 11 TREND LAB 9/29; 11 MRG Toby 9/29 (「開幕11連勝でビヨンド」); 10 LVH Hirobosu 9/29 (瞬間2位); 14 Arusu 10/2; 7 もる 10/3; 16 ちづる 10/4 (swapped 「ミュー、ヘイレムハニィ」 for 「カタリナ、ネオジオ」); 8 ぎゅう 10/4; 9 Lostwiz 10/5; 10 なっく 10/5; 15 パンドラ 10/6; 10 和田竜洸 10/6.
- **Game8 tier (10/07):** Tier 2 (existing notes). **Dexel:** no post-patch guide or tier update was found.

---
## 4. AFネメシス

### 4.1 Status after the patch
- Game8 698326 (9/30): Tier 2, list = 尽小花 / ストリートラン / アイザック / イマリ / チルスケーター / エース / ワイルドキャスター / ミュー / A&L / カミシラ / アイズエデン / 愚劣 / スカーレット ×3 each, plus エッジーマスター ×1 (existing notes).
- Dexel 9/27 (pre-patch): Tier 2 (fetched twice; one summary said 1.5, the full-table fetch said Tier 2) [V2 for Tier 2].
- **beyondmeta, post-patch: 0 AF posts.** Before the patch there were 25+, for example ototaku/のぱ/Chappy 9/4 BEYOND/GM. [V1]
- Post-patch streaks on shadowverse-wins: Alice. 7 (10/6), じゃす 7 「AF進化」 (10/5, 7–0 vs Cutthroat), 슈/SHU 5 and 7 (10/4–5) 「大部カミシラで勝ちます」「辛すぎてカミシラ使ったら強かった」.
- **Read [INF]:** AF lost players to Cutthroat, which runs most of the same cards as singletons plus the crest. What remains is the Camiscilla or Evolution-hybrid ×3 version.

### 4.2 Verbatim JP card texts (shadowverse-magazine unless noted; [V1] each unless noted)
- **尽小花・イマリ** (2-cost Legend): 【ファンファーレ】自分の手札1枚を選ぶ。それを捨てる。自分のデッキからスペル1枚を引く。 Evolved: 自分がスペルをプレイしたとき、これが進化後なら、『イマリの小鬼』1枚を自分の場に出す。 **超進化時:** 自分のデッキからコスト1のスペル2種類を引く。 Token イマリの小鬼: 2-cost 【突進】 (3/3 per the simulator data).
- **誠心なる尽小花** (1-cost spell): 「場のカード1枚を選ぶ。それは『イマリの小鬼』に変身する。」 This works on *any* card on the field, so it can turn an enemy threat or amulet into a 3/3 (Yomi did this to 大遊戯世界 at CROSS BORDER, per the existing notes).
- **奮励の追走・ミュー** (4-cost, 3/5): 自分のアーティファクト・フォロワーが場に出たとき、相手の場のフォロワーからランダム1枚に3ダメージ。 **【進化時】** 『エンシェントアーティファクト』1枚を自分の場に出す。 **超進化時:** その後、このバトル中に場に出た自分のアーティファクト・フォロワーの種類が3以上なら、これは【疾走】を持つ。
- **弾哭の変貌・アイズエデン** (7-cost, 5/5): 【ファンファーレ】『撃針の看守』1枚を自分の場に出す。自分のアーティファクト・フォロワーが場に出たとき、相手の場のフォロワーからランダム1枚を破壊。 **超進化時:** 【ファンファーレ】と同じ能力が働く。
  - Token 撃針の看守: 3-cost **アーティファクト・フォロワー**, 3/3, 【守護】【ラストワード】自分のリーダーを2回復。
  - So the Fanfare itself triggers the destroy once, and each super-evolve adds a Warden and another destroy. [INF from the token type]
- **虚刻のアナテマ・スカーレット** (8-cost, 6/6 【疾走】【守護】): 【ファンファーレ】相手の場のフォロワーすべてにXダメージ。Xはこのバトル中に場に出た自分のアーティファクト・フォロワーの種類である。
- **決断の交差・アシュレイ＆リディア** (5-cost, 5/5): 【ファンファーレ】相手の場のフォロワー1枚を選ぶ。それは【守護】を持つ。【エンハンス_9】これは進化する。これは【疾走】を持つ。 / これが進化したとき、相手の場の【守護】を持つフォロワーからランダム2枚を破壊。 [V2: magazine + Game8 794080]
- **劣悪の純心・カミシラ** (7-cost, 6/6): 【ファンファーレ】『低劣の玩具』1枚と『拙劣の人形』1枚を自分の場に出す。自分の他の元のコスト5以上のフォロワーが場に出たとき、それは進化する。 **超進化時:** 相手のリーダーにXダメージ。Xは自分の場の元のコスト5以上のフォロワーの枚数である。
  - The tokens are real cards: 低劣の玩具 (6-cost 1/3 Ward; its Fanfare draws 3 but doesn't fire when summoned) and 拙劣の人形 (5-cost 2/1).
- **愚劣の兵器** (8-cost Gold, 3/4): 【ファンファーレ】『愚劣の兵器』2枚を自分の場に出す。自分のターン終了時、相手の場のフォロワーすべてに3ダメージを割りふる。【アクセラレート】(cost **4**; Game8 + simulator; the magazine text said コスト1) 『愚劣の兵器』1枚を自分の場に出す。 **【進化時】** 相手の場のフォロワーすべてに3ダメージを割りふる。
- Support texts:
  - アナタの先輩・エース: Fanfare 『アナライズアーティファクト』 to hand; **【進化時】** select another unevolved follower of yours and evolve it.
  - ワイルドキャスター: Fanfare summon an アナライズアーティファクト; 【エンハンス_5】 also a ミスティックアーティファクト; 自分のアーティファクト・フォロワーが場に出たとき、それは【突進】を持つ.
  - 報恩の技師・アイザック: 【ラストワード】『アタックアーティファクト』1枚を自分の手札に加える。
  - デバイスマニピュレーター・ジルク: 【ファンファーレ】このバトル中に破壊された自分のアーティファクト・フォロワーからランダム1枚と同名のカード1枚を非公開で自分の手札に加える。
  - 空の命運を握る少女・ルリア (neutral 2-cost): 【エンハンス_8】自分のデッキからコスト7以上のフォロワー1枚を引く。自分のPPを7回復。【バリア】

### 4.3 Artifact tokens (magazine for the text; stats from the simulator data)
| JP name (EN) | Cost | Stats | Text | Sources in the lists |
|---|---|---|---|---|
| アナライズアーティファクト (Analyzing) | 1 | 1/1 | 「これが場に出たとき、自分のデッキから1枚を引く。」 | エース (to hand), ストリートラン mode 1, ワイルドキャスター (summon), ツインドローン |
| エンシェントアーティファクト (Ancient) | 1 | 3/1 | 【突進】 | チルスケーター (to hand; its 【進化時】 repeats it), ストリートラン mode 2, ミュー 【進化時】 (summon) |
| ミスティックアーティファクト (Mystic) | 3 | 4/5 | 【守護】 | ワイルドキャスター 【エンハンス_5】, エッジーマスター evolve |
| レディアントアーティファクト (Radiant) | 3 | 2/2 | 【疾走】 | ラズリ (to hand) — Highlander lists only |
| アタックアーティファクト ("Striker") | 3 | 5/1 | 【融合】アーティファクト・カード; transforms by fused cost: 1⇒デストロイα, 2⇒β, 3+⇒γ; 【突進】 | アイザック 【ラストワード】 |
| 撃針の看守 (Warden of the Trigger) | 3 | 3/3 | 【守護】【ラストワード】 leader +2 | アイズエデン Fanfare and super-evolve |

- ストリートラン (Freerunning) gives both tokens once ≥3 different Artifact types have entered (per the simulator text; the existing notes have the JP).
- **Scarlet's X and Myuu's Storm count different names.** A typical game reaches 4–5 by T8: Analyzing + Ancient + Mystic/Warden + アタック. [INF]

### 4.4 How AF deals damage and closes the game [INF from the texts above; GameWith 503019's old-pack summary agrees on the general shape]
1. **Board control engine:**
   - Every artifact entering = 3 damage from ミュー, or 1 random destroy from アイズエデン.
   - With ワイルドキャスター on board, every artifact also gets 突進 and trades at once.
   - 愚劣の兵器 gives three bodies that each ping 3 split at your end of turn (9 split damage per turn).
   - スカーレット wipes small boards with X = number of Artifact types.
2. **Damage to the leader:**
   - スカーレット: 6 Storm.
   - ミュー super-evolved with ≥3 types: 6/8 Storm.
   - A&L 【エンハンス_9】: evolved 7/7 Storm, which also destroys 2 Ward followers (its own Fanfare picks one to give Ward).
   - カミシラ super-evolve: X = number of your base-cost-5+ followers.
     - Camiscilla + its 2 tokens = 3.
     - Add 3 Ordnances or A&L/Scarlet/Aizeden for 4–7.
     - Camiscilla also auto-evolves every 5+ cost follower that enters, so A&L's 「これが進化したとき」 fires on arrival.
3. **Typical finishing turns:**
   - T8: スカーレット AoE + 6 Storm.
   - T9: A&L enhanced (Storm 7) + a cheap artifact trigger.
   - Camiscilla line: T7 Camiscilla (+ super-evolve going second on T6/T7 → about 3 to face), then T8 愚劣 → 3 more 5+ bodies → the next super-evolve does about 6. Super-evolve is limited to 2 per game and one evolve or super-evolve per turn.
4. **Disruption:** 誠心なる尽小花 transforms the biggest enemy follower (or an amulet such as 大遊戯世界 or Bishop countdowns) into a 3/3.

### 4.5 AF mulligan and matchups
- **Game8 (9/30):** keep ストリートラン and チルスケーター (existing notes).
- Older guides add エース, アイザック and ワイルドキャスター.
- **Matchups:**
  - Dexel 9/27 matchup row (summarizer, [UNVERIFIED]): ▲ vs 魔手/セフィー Witch, Ramp Dragon, Amulet Bishop, 進化ビショップ; ○ vs フェイスドラゴン, バルバロス/連携 Royal.
  - Post-patch: 7–0 vs Cutthroat (じゃす, [V1]).
  - The Amulet Bishop guide (Dexel 9/01) treats AF as a disruptive matchup because of 尽小花 (existing notes).
- Game8 789262 "AFネメシス対策" (stamped 9/30) describes old-pack cards (デストロイβ/γ, ヨグゼンタ, カルラ) and calls AF "Tier1". **It is stale and should not be used.**

---
## 5. Unverified / open items
- Cutthroat evolved stats 3/3 (inferred from the +2/+2 rule; no page prints them).
- Whether a crest/effect evolve of A&L fires 「これが進化したとき」 (strong inference, no Q&A), and whether A&L's Fanfare Ward resolves before the crest evolve.
- Whether super-evolutions, crest evolves and Camiscilla evolves count toward Sandalphon's 6 (implied by Game8 and player comments, not stated in any rule). Whether an already-evolved follower can be super-evolved.
- 奥義 gauge formula (only Game8 732594, read once with a verbatim quote). This sets when Sandalphon's 10-damage 解放奥義 becomes live.
- Whether Accelerating Ordnance counts as playing a base-cost-8 card for Zerael/Azvaldt.
- らきちゃ's "11–0 vs Highlander" quote was seen in only one beyondmeta fetch. The pairing data comes from beyondmeta's reading of player posts.
- The beyondmeta share numbers come from X posts it collected (BEYOND reaches and streaks), not from ladder win rates. No real win-rate or matchup percentages were found for either deck.
- JP names marked (?) in §3.1: Marionette Master, Twindrone Engineer, Lu Woh, Katalina, Sho, Slaus, Lazuli, Aika.
- First-player turn-1 draw (Game8 rules page summary) — this affects the mulligan math only slightly.
- The note ミホノブルボ's full card list could not be read (image). The GameWith Highlander guide, X reply threads and every YouTube description were unreadable (403/429/robots).
