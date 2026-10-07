# Deep dive: 実験体(セフィー)ウィッチ / アミュレットビショップ / 連携ロイヤル
Rotation, 第9弾 アズヴォルト・レヴナント. Balance patch 2026-09-29. Research date 2026-10-07.
This file builds on /mnt/project-files/shadowverse/meta-research-2026-10-07/{nightmare-witch,nemesis-bishop,royal}.md and does not repeat what is already there (Game8 lists and hashes, the はせ/ハガネ notes, the Game8 Bishop 立ち回り, the Game8 Synergy lists).

Tags:
- [V2] = two independent sources, or two differently-worded fetches that agree, or a source plus the local card DB (/home/claude/sv/svsim/cards/data/rotation.json and the script docstrings).
- [V1] = one fetch.
- [UNVERIFIED] = conflicting sources, or the summarizer is suspect.
- [INFERENCE] = my own arithmetic or reasoning from card text, not stated by any source.

Main limitations:
- No post-patch (after 09-29) written guide exists for any of the three decks. The newest guides are beyond-dexel Beita (09-11), Game8 (09-30, which is only a list refresh), and NAXAN 監獄ビショップ (09-18).
- The post-patch evidence is player comments on shadowverse-wins.com from 10-01 to 10-07.
- YouTube returned HTTP 429 (rate-limited) on every video, so no descriptions or hashes were read.
- x.com is blocked by robots.txt.
- GameWith returned 403 on 573926, 580404, 546031 and 558814.

---

## 0. Rules context needed for the math [V1 Game8 unless noted]
- **Evolution and super-evolution timing** (Game8 696356):
  - Evolve from turn 5 going first (先攻) or turn 4 going second (後攻).
  - Super-evolve (超進化) from turn 7 (先攻) or turn 6 (後攻).
  - Evolve gives +2/+2 and super-evolve gives +3/+3, and both grant Rush (突進).
  - You get 2 EP and 2 SEP, and can evolve once per turn.
  - A super-evolved follower takes no damage during its controller's turn and cannot be destroyed by enemy abilities.
- **Keyword definitions** (Game8 697567):
  - 連携: 「この対戦中場に出たフォロワーの数が連携の値の数以上なら発動」
  - カウントダウン: 「ターン開始時にカウントが1つ減り、0になったら破壊される」
  - クレスト: you can hold at most 5.
  - 奥義 needs 奥義ゲージ 10 and 解放奥義 needs 15. The gauge is the current turn number plus the number of times your followers evolved while this card was in hand (Game8 732594). [V1]
- **Fusion (融合) is limited to once per turn**: per turn, or per fusion card per turn, is unclear. The local sim's design docs list this as an open question; they note "英文和日文描述不一致". [UNVERIFIED]
  - Consequence: with Sephie in hand you can make about 1 extra Test Subject per turn for 2 PP.
- **Token stats** (local DB, which agrees with the Game8 arithmetic in §2):
  - ホーリーファルコン 3-cost 2/2 【疾走】 [V2]
  - ナイト 1/1 (兵士 trait)
  - スティールナイト 2/2 (兵士 trait)
  - 天書の深淵 1-cost spell
  - ソニック・フォー and 大いなる回帰 are 1-cost spells
  - デスペラードショット 1-cost spell

---

## 1. 実験体ウィッチ / セフィーウィッチ (Runecraft)

### 1.1 Card text, verbatim JP (shadowverse-magazine card pages; cross-checked against the local DB English) [V2 unless noted]
- **万術の咎人・セフィー** (7, Legend, 4/4) — c10934110
  - Base: 「【融合】カード これに【融合】したとき、自分のPPを2消費して、『没入の実験体』1枚を自分の場に出す。 ーーー 【ファンファーレ】『没入の実験体』2枚を自分の場に出す。」
  - Evolved: 「【超進化時】自分は『クレスト：万術の咎人・セフィー』を持つ。」
  - **Crest**: 「自分の『没入の実験体』が場に出たとき、自分のターンごとに1回、それは【疾走】を持つ。」 [V2: magazine + GameWith 573312 from the earlier session + DB "Once on each of your turns"]
  - Notes: the fusion fodder can be any card (「カード」). The sim author confirms that 2 PP is spent even when the board is full.
- **没入の実験体** (2, Bronze, 2/2 突進) — c10931110: 「これが場に出たとき、このバトル中に場に出た自分の他の『没入の実験体』の枚数が5以上なら、これは+3/+3する。」 and 【突進】.
  - Official Q&A, via the DB: if two are summoned together after four have already entered, the first stays 2/2 and the second gets +3/+3. So the 6th Subject onward enters as 5/5. [V2]
- **恍惚の才媛** (5, Gold, 2/3) — c10933110
  - Base: 「【融合】カード ーーー 【ファンファーレ】自分のデッキから2枚を引く。『没入の実験体』1枚を自分の場に出す。」
  - Evolved: 「【超進化時】これに【融合】していたなら、自分の場の『没入の実験体』1枚を選ぶ。それは【ドレイン】を持つ。」 [V2]
- **烏ノ涅** (5, Gold, spell) — c10933310: 「『没入の実験体』1枚を自分の場に出す。「相手の場のフォロワーからランダム1枚に7ダメージ。」を2回行う。」 [V2]
- **人らしい愛** (3, Silver, spell) — c10932310: 「『没入の実験体』1枚を自分の場に出す。それは+1/+0する。『没入の実験体』1枚を自分の手札に加える。それは+1/+0する。」 [V2]
  - So the hand copy is a 2-cost 3/2 (or 6/5 once the count is reached).
- **心酔の研究者** (4, Silver, 1/1) — c10932110
  - Base: 「【ファンファーレ】『没入の実験体』2枚を自分の場に出す。【エンハンス_8】2枚ではなく3枚。それは【守護】を持つ。」
  - Evolved: 「【進化時】自分の場の『没入の実験体』1枚を選ぶ。それは【必殺】を持つ。」 [V2]
- **恩愛の大地・テトラ＆ラティカ** (6, Legend, 5/5 疾走) — c10834110: 「Xは0から始まる。【スペルブースト時】これのXを+1する。ーーー【ファンファーレ】Xが10以上なら、『ソニック・フォー』1枚を自分の手札に加える。20以上なら、『大いなる回帰』1枚を自分の手札に加える。ーーー【疾走】」 Evolved: none.
  - Tokens: 『ソニック・フォー』 (1 cost): 「相手の場のフォロワーすべてに5ダメージ。」 『大いなる回帰』 (1 cost): 「自分の場のフォロワー1枚を選ぶ。それは『1ターンに2回攻撃できる。』を持つ。」 [V2]
  - beyond-dexel Beita writes the token name as 「ソニックフォー」.
- Flex cards seen in lists:
  - **睦まやかな団欒** (2, spell): heal 2 and spellboost your hand (DB: "Restore 2 defense to your leader. Spellboost your hand…"). The JP name comes from Beita's article. [V1 name]
  - Others: マナリアスクリプター・ティコ, 魔女の錬金釜, アルケミックフレア, スウィートエンティティ, ラブリーマスターピース (DB texts are in the decodes below).

### 1.2 Lists: the newest player list plus the Game8 baseline
**A. Beita 「セフィーウィッチ・CR瞬間1位」 — beyond-dexel https://beyond-dexel.com/deck-witch-20260911/ (2026-09-11, pre-patch; the newest player-authored list found) [hash V1, content V2 across 3 fetches]**
```
https://shadowverse-wb.com/ja/deck/detail/?hash=1.3.cH3E.cH3E.cH3E.cfTu.cfTu.cfTu.eB7k.eB7k.fDXk.fDXk.fDXk.fKcs.fKcs.fKpM.fKpM.fKpM.fKsU.fKsU.fKsU.fL2-.fL2-.fL2-.fikc.fikc.fikc.fink.fink.fi-E.fi-E.fi-E.fj1M.fj1M.fj1M.fjDs.fjDs.fjG-.fjG-.fjTU.fjTU.fjTU
```
Decoded (JP names via Game8/dexel mapping): 知恵の輝き3, ストームブラスト3, 過剰反応2, 明越花の転変2, 相承の意思3, 睦まやかな団欒2, 没入の実験体3, マナリアスクリプター・ティコ3, 鋼鉄の微睡み3, 人らしい愛3, 心酔の研究者3, 恍惚の才媛2, 烏ノ涅2, 恩愛の大地・テトラ＆ラティカ3, 万術の咎人・セフィー3 = 40.

**B. Figole 「実験体ウィッチ・CR瞬間1位」 — https://beyond-dexel.com/deck-witch-20260902/ (2026-09-02; the 土/秘術 hybrid that はせ's note credits to Figole) [hash V1]**
```
https://shadowverse-wb.com/ja/deck/detail/?hash=1.3.e4Gg.e4Gg.e4Gg.cH1g.cH1g.cH1g.fDXk.fDXk.fDXk.fikc.fikc.fikc.dpCU.dpCU.dpCU.fKpM.fKpM.fKpM.fj1M.fj1M.fj1M.fi-E.fi-E.fi-E.eyOs.eyOs.fjDs.fjDs.fjDs.fjG-.fjG-.fjG-.fL2-.fL2-.fL2-.fjTU.fjTU.fjTU.eyee.eyee
```
Decoded: 魔女の錬金釜3, 大遊戯世界3, アルケミックフレア3 (4 dmg + earth sigil; 奥義: 2 to face), 相承の意思3, 没入の実験体3, ティコ3, 人らしい愛3, 心酔の研究者3, スウィートエンティティ2 (土の秘術: 3 AoE or draw 2; evolve replicates), 恍惚の才媛3, 烏ノ涅3, テトラ＆ラティカ3, セフィー3, ラブリーマスターピース2 (8-cost 4/8 Ward, FF 6 AoE, LW 秘術 3 face). This decode resolves the earlier はせ list that was marked UNVERIFIED.

**Card counts compared** (G8 = Game8 9/30 list in nightmare-witch.md §2a):

| card | G8 | Beita | Figole |
|---|---|---|---|
| セフィー | 3 | 3 | 3 |
| 没入の実験体 / 人らしい愛 / 心酔の研究者 / 相承の意思 | 3 each | 3 each | 3 each |
| 恍惚の才媛 | 3 | 2 | 3 |
| 烏ノ涅 | 3 | 2 | 3 |
| テトラ＆ラティカ | **1** | **3** | **3** |
| マナリアスクリプター・ティコ | 0 | 3 | 3 |
| 大遊戯世界 | 3 | 0 | 3 |
| 知恵の輝き / ストームブラスト | 3/3 | 3/3 | 0/0 |
| 過剰反応 / 明越花の転変 | 3/3 | 2/2 | 0/0 |
| 鋼鉄の微睡み | 3 | 3 | 0 |
| 睦まやかな団欒 | 0 | 2 | 0 |
| 錬金釜 / アルケミックフレア / スウィートエンティティ / ラブリーマスターピース | 0 | 0 | 3/3/2/2 |

- Consensus core (all three lists): 3 Sephie, 3 Test Subject, 3 人らしい愛, 3 研究者, 3 相承の意思, plus 才媛 and 烏ノ涅 at 2–3 each.
- Player lists run **3 Tetra and 3 Tico**; Game8 runs only 1 Tetra and no Tico.
- Two shells exist: the spellboost/draw shell (Beita, Game8) and the 土の秘術 shell (Figole).
- Post-patch ladder comment ころたん (10-06, 13連勝): 「無理にスペルとか土と混ぜるよりちゃんと実験体いっぱい出した方が強かったです。」 [V1]
- うおちゃ (10-06) instead reached BEYOND with "スペル実験体". So both shells are being played post-patch. [V1]

### 1.3 Game plan and kill turn
- **Count engine.** Each Subject that enters counts toward the threshold, and from the 6th Subject on they are 5/5 Rush. Subject sources in Beita's list:
  - 3 実験体 cards
  - 人らしい愛 ×3 (2 Subjects each: one on the board, one to hand)
  - 研究者 ×3 (2 each, 3 when enhanced)
  - 才媛 ×2 (1 each)
  - 烏ノ涅 ×2 (1 each)
  - Sephie fanfare (2)
  - Sephie fusion (1 per fuse, at 2 PP)
  - 相承の意思 mode 2 (Reanimate 2) re-summons a Subject, which counts as another entry. [INFERENCE from text]
- **Phases (Game8 headings, already noted):** 「序盤はドローをしながら実験体のカウントを稼ぐ」→「セフィーを超進化してクレストを付与」→「実験体やテトラ＆ラティカでリーサルを狙う」.
  - Figole frames it as "2/2 Rush tempo early, then late-game damage from 5/5s made via Sephie", finishing around turns 9–10. [V1]
- **Sephie timing.** Beita calls Sephie 「多くの対面で最速超進化を狙う起点」.
  - Fastest line [INFERENCE from rules]: going first, play Sephie on turn 7 (7 PP) and super-evolve her the same turn. Going second, she can come down on turn 6 only with extra PP or cost help, so turn 7 is more realistic.
  - The fanfare Subjects enter **before** the crest exists, so the first crest-Storm Subject usually arrives the turn after Sephie.
- **Crest damage per turn** [INFERENCE from the crest text]:
  - Only one Subject per turn gets Storm.
  - Best options: the 2-PP 6/5 hand copy from 人らしい愛 for 6 damage, or 人らしい愛 cast for 3 PP putting a 6/5 straight onto the board. GameWith 573312: 「2コストで5点疾走を用意可能」.
  - Everything else must be on board from the previous turn, or be Tetra (5 Storm).
  - Figole: after Sephie, 「5、6点を詰め、テトラ＆ラティカと合わせたリーサルラインで決めきる」 (vs Nightmare). [V1, quoted in Japanese]
- **Burst lines** [INFERENCE]:
  - Tetra with X≥20 gives 大いなる回帰 (1 PP): Tetra + 回帰 on Tetra = 10 for 7 PP. Or 回帰 on a crest-Storm 5/5 or 6/5 Subject = 10–12. Tetra 10 + Storm Subject 6 → about 16 or more with 9–10 PP plus any board.
  - This is the "20点OTK搭載型" mentioned by X user ポーテクフルスの杖 (search snippet only) [UNVERIFIED].
  - Tetra's X counts spellboosts. That is why Beita and Figole both run 3 Tetra with Tico, 団欒 and 微睡み.
- **Fusion decisions.**
  - Beita: whether to turn Tico's 魔弾 into Subjects (fuse them into Sephie) or keep them to spellboost by 1 must be decided 「その場の盤面や手札で見極める」 [V2].
  - うおちゃ (post-patch): 「セフィーターンに5/5であれば良いので中盤は手札をなるべく温存・0コス魔弾を抱えてセフィーを置けるように」 [V1]. This means: hit the count by the Sephie turn, and hold Tico's 魔弾 (cost 0 after Tico evolves) so you can play Sephie and still remove a threat in the same turn.
- **Board sizing.** Beita: 「相手の処理範囲を見極めたうえで、それに見合う数・スタッツの盤面を作る」. Don't overextend into AoE.
- **Card roles.**
  - 恍惚の才媛: Beita says treat it as 「ドローソースとしてはほぼ機能しない回復寄りのカード」. Its drain comes from the super-evolve; はせ calls it essential vs Pirate.
  - 烏ノ涅: 「シンプルに除去として強い」 (はせ).
  - 明越花・アラ is not run: 「事故の原因になりやすく、不採用」 (Beita).

### 1.4 Mulligan [V2: Beita, 2 fetches]
- Top priority, all matchups:
  - 万術の咎人・セフィー
  - 過剰反応 (「出なくても『明越花の転変』の捨て札にしたり、最悪『ゴーレム』を出してターンをしのぐ」)
  - 人らしい愛
- Compromise keeps:
  - 没入の実験体 (「セフィーがない場合は必ずキープしたいカード」)
  - ティコ (「2コストが見えている場面ではキープ候補」)
- By matchup:
  - vs Dragon and Bishop: 「ティコ…基本的に持ちません」.
  - vs Nemesis: Tico 単キープ, because 「進化しておかないと『アイズエデン』で詰まれてしまう」.
  - vs Nightmare: no Tico.
- Figole: Sephie, 大遊戯世界, 魔女の錬金釜 first (one copy each), then 実験体, 人らしい愛 and 研究者. Game8: 大遊戯世界 and セフィー in every matchup.

### 1.5 Matchups (pre-patch writers plus post-patch ladder comments)

| Opponent | Verdicts |
|---|---|
| **Pirate (海賊/バルバロス) Royal** | dexel matrix ▲ (pre-buff) [V2 cross-row]. はせ 微有利 and 「恍惚の才媛 — これが無いと海賊旗ロイヤルに勝てません」. **Post-patch players:** 激旨炒飯 10-05 「海賊ロイヤルを盤面で蹴散らせるからおすすめ」; みぬん2nd 10-04 「環境に多い財宝とカッスロに強く出れて」; うおちゃ 10-06 「セフィー超無しで勝つ対面がある(海賊、カッティスなど)」 [all V1 on shadowverse-wins]. Pirate view (もとやしき): Sephie boards are answered with ウンケイ or 副船長 super-evolve plus 1-cost 燃え落ちる縁. → **Slightly favorable post-patch (anecdotal).** Flags are amulets, so Witch cannot stop the burst; the plan is to win the board race, and drain/heal from 才媛 and 団欒 matter. |
| **Ramp Dragon** | dexel ○; Figole 有利; はせ 有利寄り; GameWith-era Kuru (09-20): 「ウィルナス自体は簡単に返せるが、同時にセフィーを置くのが難しい」. Loss conditions (Figole): 「イランツァで無理やり詰まされたり、アルビオンバハムートでクレストを消されたり」. Plan: 「なるべく横に広げて『打たれても勝っている』状況」, keep Subjects at 4+ HP. → **Favorable** [V2]. |
| **Combo / Dust Days Elf** | dexel "-" (even); はせ 大不利 (worst matchup); Kuru 「初手からセフィーを持てていてようやく五分」. → **Unfavorable to even, needs Sephie in the opener** [UNVERIFIED degree]. |
| **Lastword / Midrange Nightmare** | Consistently **unfavorable**: はせ 不利; Figole "unfavorable resource race"; Kuru 「全部持たれていたら勝てるビジョンが見えない」 (タイトロープ, イステンマルチル); Beita calls it the hardest matchup. Plan: hold 研究者 for タイトロープキャット (Figole: 「先攻4ターン目・後攻4ターン目では一旦置かずに握っておきます」); get ソニックフォー from Tetra (X≥10) to sweep (Beita); keep several HP-5 followers vs イステンデッド's 2 AoE (はせ). [V2] |
| Amulet Bishop | dexel ○; はせ 五分; Kuru 「アミュレットの方がやりやすい」. |
| Synergy Royal | dexel ○; はせ 微有利; Kuru 「初手でセフィー引けていればほぼ負けない」. → Favorable. |
| Nemesis | AF Nemesis ○ (dexel); Cutthroat Nemesis good post-patch (みぬん2nd, うおちゃ). Evolution Nemesis is annoying (Kuru). Keep Tico vs アイズエデン. |
| Face Dragon | (from elf-dragon.md, coolyu) Face Dragon is 有利 vs 実験体 「まともな回復がないためゴリ押しできる」. → Unfavorable for Witch. |

---

## 2. アミュレットビショップ (Havencraft)

### 2.1 Card text, verbatim JP [V2 unless noted]
- **旧き天書・リアントース** (9, Legend, 9/9) — magazine c10664120:
  - Main text: 「【ファンファーレ】場の他のカード3枚を選ぶ。それを破壊。 ーーー 【守護】 自分のターン終了時、信仰値を-10して、『天書の深淵』1枚を自分の手札に加える。 ーーー 【信仰】 信仰値は0から始まる。 ーーー 自分のアミュレットが破壊されたとき、信仰値を+1する。」
  - Sources: magazine plus appmedia 79779191 (2026-02-26). Game8 763912 says a 2026-03-30 buff added 守護 and moved the 深淵 generation to the unevolved side [V1 on the date].
- **天書の深淵** (1-cost token spell): 「場のカード1枚を選ぶ。それを破壊。自分のアミュレットを選んだなら、相手のリーダーに2ダメージ。『天書の深淵』1枚を自分の手札に加える。」
  - Source: Game8 763912, matching the DB English. The sim author also confirms that the self-copy is inside the "if you chose an allied amulet" clause [V2].
  - So 深淵 on your own amulet = 1 PP for 2 face damage, and it comes back. 深淵 on an enemy card = removal, but the loop ends.
- **崇高の天書** (4, Gold, countdown amulet) — c10663210: 「【ファンファーレ】場の他のカード1枚を選ぶ。それを破壊。自分のアミュレットを選んだなら、自分のPPを2回復。ーーー【カウントダウン_2】【ラストワード】このバトル中に破壊された自分の「元のコスト2以下の、【ラストワード】を持つアミュレット」からランダム1枚と同名のカード1枚を自分の場に出す。」 [V2]
- **有翼の石像** (1, Silver, amulet) — c10062210: 「【カウントダウン_4】【ラストワード】『ホーリーファルコン』1枚を自分の場に出す。－－－コスト1【アクト】これのカウントを-1する。」 ホーリーファルコン = 3-cost 2/2 【疾走】 token. [V2]
- **英雄幻視・トルー** (3, Bronze, 2/1) — c10461110: 「【疾走】 自分がアミュレットを【アクト】したとき、これは【ドレイン】を持つ。」 [V2]
- **ミラクルアルミラージ** (3, Silver, 2/1) — c10962120: 「【疾走】ーーー【結晶】【コスト1】【カウントダウン_3】【ラストワード】『ミラクルアルミラージ』1枚を自分の場に出す。ーーー コスト1【アクト】これのカウントを-1する。」 [V2: magazine + Game8 811766 + DB]
  - This makes it a second "1-PP amulet whose Last Words gives a 2/x Storm" piece, the same as 有翼の石像.
- **混迷の監獄・アズヴォルト** (8, Gold, Neutral amulet) — c10903210: 「自分のターン終了時、このバトル中に自分がプレイしたカードの元のコストに1~8すべてが含まれているなら、これを破壊。【ラストワード】このバトル中に破壊された自分のフォロワーからランダム4種類と同名のカード1枚ずつを自分の場に出す。自分の場のフォロワーすべては+3/+3する。」 [V2: magazine + Game8 811034]
  - Ruling note (DB, official Q&A with ゼラエル): at end of turn Azvaldt is destroyed, then Zerael invokes, then the Last Words resolve.

### 2.2 How 「手札に有翼の石像を2枚以上残して8点（超進化で11点）…21点」 works
Game8 698347 (2026-09-30), verbatim and [V2], fetched twice:
- 「手札に有翼の石像を2枚以上残すことで、8点（超進化で11点）を削ることができます。超進化が残っていれば、追加でアミュレットを5枚破壊することで21点を削り切れます。」
- 「天書の深淵は対戦相手のカードを選択することができます。1PPを残すことで守護を1枚破壊しながら、疾走を通すことが可能です。」

Step by step [INFERENCE; the numbers match Game8's exactly, and the Falcon's 2/2 stats come from the DB]:

**Prerequisite.** You need 天書の深淵 in hand. Get it by reaching 10 faith (10 of your amulets destroyed this match; faith counts from Lyanthoth's own tracking) and ending a turn with リアントース on the field. Lyanthoth's fanfare (destroy 3 cards, usually your own amulets) feeds faith and triggers their Last Words. So the usual setup is Lyanthoth on turn 9 and the combo on turn 10. You can also go off on turn 9 if you already hold 深淵.

| Step | Action | PP spent (running total) | Face damage (running total) |
|---|---|---|---|
| 1 | Play 有翼の石像 #1 | 1 (1) | – |
| 2 | 天書の深淵 targets that 石像: 2 face. Its Last Words summons ホーリーファルコン 2/2 Storm, and 深淵 returns to hand. | 1 (2) | 2 (2) |
| 3 | Falcon attacks face | – | 2 (4) |
| 4 | Repeat steps 1–3 with 石像 #2 | 2 (4) | 4 (**8**) |
| 5 | Super-evolve one Falcon (+3/+3) before it attacks | – | 3 (**11**) |
| 6 | 深淵 on 5 more of your amulets already on the field (2 each, 1 PP each) | 5 (9) | 10 (**21**) |

Notes:
- **Why "keep 2+ 石像 in hand":** each 石像 played from hand is a 1-PP amulet you can break at once for 4 damage. Played early, it is just a 4-turn clock.
- **Why 9–10 PP:** the full line uses 9 PP, leaving 1 PP for one 深淵 on an enemy Ward (the second Game8 sentence). That last 深淵 does not return.
- The other 5 amulets can be any of your amulets: 汚濁の聖水, 救済の聖典, 無欠の時計, 朋友の学級, 陽光の耳飾り, 海蝕の三叉槍, 崇高の天書 and so on. Their Last Words fire as they break:
  - 聖水: draw and destroy a random enemy follower.
  - 聖典: 2 AoE, heal 2, draw 2.
  - 崇高の天書: re-summons a ≤2-cost Last Words amulet, which is more fodder.
- **ミラクルアルミラージ crystals** (1 PP) work exactly like extra 石像: each is 1 PP for 2 face plus a 2/1 Storm when broken by 深淵.
- **トルー** gains Drain whenever you engage (アクト) an amulet. Engaging 石像 or アルミラージ for 1 PP each makes トルー a lifelink Storm attacker.
- **アズヴォルト line** (Game8: 「リアントースのファンファーレや天書の深淵でアズヴォルトを破壊できれば、9PPの時点で大ダメージ」):
  - Breaking Azvaldt with 深淵 gives 2 face. Its Last Words then re-summon 4 random different followers of yours that died this match, and give all your followers +3/+3.
  - If the dead followers are mostly Storm (トルー 2/1, アルミラージ 2/1, ホーリーファルコン 2/2), they return as 5/4 to 5/5 Storm. That is why Game8 says 「デッキ内の疾走フォロワーを増やすのがおすすめ」. [INFERENCE: a typical Azvaldt break adds about 10–20 burst]
  - 崇高の天書 can also break Azvaldt and refunds 2 PP.
  - You can also let Azvaldt break naturally: once you have played cards of every base cost 1–8, it breaks at your end of turn, which only gives the +3/+3 board.
- **Counterplay** [INFERENCE]: The combo needs 10 faith, Lyanthoth to survive until end of turn (it has 9/9 Ward), and amulets on the field.
  - Banish effects and Ramp Dragon's バハムート (「盤面、クレスト、アミュレットを消滅」, elf-dragon.md) wreck it.
  - Pirate view (もとやしき): 「相手手札がパンパンなら面を空にして【旧き天書・リアントース】着地キャンセル」. Lyanthoth needs other cards to destroy, so an empty enemy board reduces its value.
  - Combo-Elf view (Spicies): the turn Lyanthoth is played, Bishop cannot heal with イニシア or カンディマ, so start pushing face just before it lands.

### 2.3 Lists [hashes from earlier notes]
- **A — Game8 698347 (09-30), Storm/Azvaldt build:** 大遊戯世界3, 陽光の耳飾り3, 有翼の石像3, 朋友の学級3, 無欠の時計3, 汚濁の聖水3, 救済の聖典3, ミラクルアルミラージ3, 英雄幻視・トルー3, 海蝕の三叉槍3, 崇高の天書3, 神紋ユラティオ1, アドアマネージャー・イニシア1, 混迷の監獄・アズヴォルト2, 旧き天書・リアントース3.
- **B — dexel zhangyue616 (09-01), control:** no Azvaldt, no Storm. Runs 刻みし約束(?)3, 崇高の憎悪・カンディマ3, 崇奉の怯者3, ユラティオ2, イニシア2.
- **C — 監獄ビショップ (NAXAN note https://note.com/naxan13/n/n0d0341607b22, 2026-09-18, rating about 1500) [V1; the summarizer garbled card names in English]:**
  - Core: アズヴォルト 2–3, 崇奉の怯者3, リアントース 2–3, イニシア3, エルラーデ1 (name UNVERIFIED), 救済の聖典3, 崇高の天書3, 無欠の時計3, ユラティオ 2–3, 暗黒次元 0–2.
  - Concept: survive (「耐久」), then break Azvaldt.
  - Kill turn 9–10.
  - Matchups: Dust Days Elf even to favorable; Ramp Dragon 不利; Nightmare even to favorable; Nemesis 不利.
  - Mulligan: always 聖典 and 怯者; 「セットキープで聖典天書」.
- **Post-patch ladder (shadowverse-wins):**
  - 池元組カサハ 09-29: 「新シーズンは疾走よりのアミュレットビショップ」 (8連勝).
  - kuritama 09-21: アミュビショ 10連勝.
  - LVH|mickey 10-07, Bishop 11連勝: 「ドラゴンとリンクルはほぼ無理」.
  - **Note:** the post-patch Bishop streak posts are dominated by **クキシロビショップ**: aura got 瞬間1位 twice (10-02 and 10-06), まおう got 瞬間1位 (10-03), plus 進化ビショップ. Amulet Bishop appears less often. [V1]
- No post-patch Amulet Bishop hash was found.

### 2.4 Mulligan by matchup (already in nemesis-bishop.md; summary)
- Always keep: 救済の聖典, 汚濁の聖水, 大遊戯世界. zhangyue: landing 聖典 on turn 2 「ネメシス以外の対面では…ほぼ勝ち」.
- vs board-flood decks (Pirate, Nightmare, Combo Elf): 無欠の時計 and 海蝕の三叉槍.
- vs Ramp Dragon: keep イニシア; save heals except 聖典.
- Bishop mirror: keep リアントース.
- vs AF Nemesis: 朋友の学級.
- For the OTK build [INFERENCE]: never mulligan for 石像. Keep them in hand later in the game (they are 1-PP OTK fuel).

### 2.5 Matchups

| Opponent | Verdicts |
|---|---|
| **Pirate Royal** | dexel ○ (pre-buff) [V2 cross-row]. もとやしき (Pirate POV): イニシア can only be answered by ゼタ＆ベア; cancel Lyanthoth by emptying the board. Post-patch the Pirate early drops are sturdier (斥候 2/2, 砲手 4/2) and Game8's stated weakness is 「序盤からフォロワーを展開してくるデッキに押されやすい」. Pirate flags are amulets: 深淵 or 崇高の天書 can destroy them, but their Last Words still deal 2 to Bishop, so heal (聖典, イニシア 3, ユラティオ) is the real answer [INFERENCE]. → **Probably even to slightly unfavorable after the buff** [INFERENCE; no post-patch source]. |
| **Ramp Dragon** | dexel × (Bishop side) and ◎ (Dragon side) [V2]; NAXAN 不利; mickey 「ほぼ無理」 (post-patch). バハムート erases amulets and crests. → **Unfavorable** [V2]. |
| **Combo / Dust Days Elf** | dexel "-"; NAXAN even to favorable (監獄 build); Spicies (Elf POV) plans to burst during the Lyanthoth turn. → **Even**. |
| **Lastword Nightmare** | dexel ◎ vs ミッドレンジナイトメア [V2]; NAXAN even to favorable; zhangyue: take early damage, set up removal amulets, stay out of lethal until Lyanthoth. Caveat: Game8 calls LW Nightmare 「序盤から隙が無く攻めれる」, and Bishop's weakness is early boards. → **Favorable** (pre-patch data). |
| Others | ○ vs Synergy Royal (dexel ◎ on the Bishop row, × on the Synergy row) [V2]; × vs 魔手ウィッチ (now T3 after the nerf); ▲ vs Sephie Witch; ◎ vs Evolution Bishop; Nemesis 不利 per NAXAN; Linkle (リンクル) Witch "ほぼ無理" per mickey. |

---

## 3. 連携ロイヤル (Swordcraft)

### 3.1 Card text, verbatim JP [V2 unless noted]
- **統音のアナテマ・ギルダリア** (4, Legend, 4/4) — magazine c10724110, fetched twice:
  - Base: 「【ファンファーレ】【連携_20】自分は『クレスト：統音のアナテマ・ギルダリア』を持つ。これは進化する。 ーーー 自分の他のフォロワーが場に出たとき、自分のターンなら、それは【突進】を持つ。」 The Rush line is a separate, always-on ability, not part of 連携_20.
  - Evolved: 「これが進化したとき、『スティールナイト』2枚を自分の場に出す。」
  - **Crest**: 「【カウントダウン_1】自分のフォロワーが場に出たとき、自分のターンなら、相手のリーダーに1ダメージ。」 [V2 magazine + DB]
  - The crest has countdown 1 and ticks at the start of your turn, so it **only works during the turn you play Gildaria**.
  - [INFERENCE] Two Gildarias at 連携20 give two crests (you can hold up to 5), so 2 damage per follower.
- **天命の弾丸・バニー＆バロン** (5, Legend, 4/4 突進) — c10824110:
  - Base: 「【ファンファーレ】『天命の弾丸・バニー＆バロン』1枚を自分の場に出す。【連携_20】相手のリーダーに４ダメージ。【突進】」
  - Evolved: 「【進化時】『デスペラードショット』1枚を自分の手札に加える。」
  - Token: 『デスペラードショット』 (1-cost spell): 「相手の場のフォロワーからランダム1枚に4ダメージ。」を2回行う。 [V2]
- **寛厳の音帥・セザール** (7, Legend, 5/7) — Game8 781872 (最終更新 2026-09-30, rated SS) and shadowversewbwiki (2026-04-30):
  - Base: 「【ファンファーレ】『スティールナイト』2枚を自分の場に出す。自分の場の他のロイヤル・フォロワーすべては+1/+3して【守護】を持つ。【守護】」
  - Evolved: 「【超進化時】相手の場のフォロワー1枚を選ぶ。それを破壊。」 [V2]
  - The magazine page c10724120 returned 404.
- **焦がれし炎将・マーズ** (8, Legend, 1/5) — c10824120: 「【ファンファーレ】『ナイト』3枚を自分の場に出す。【疾走】【必殺】自分の兵士・フォロワーが場に出たとき、それは+2/+0して【突進】を持つ。これは+1/+0する。」 Evolved: 「【超進化時】『ナイト』1枚を自分の場に出す。」 [V2 magazine + DB]
- **響爪の分班長** (5, Gold, 3/2) — c10723110: 「【ファンファーレ】『ナイト』3枚を自分の場に出す。【モード】1つを選んでその能力が働く。（1）自分の場の他のフォロワーすべては+1/+0して【突進】を持つ。（2）自分の場の他のフォロワーすべては+0/+1して【守護】を持つ。」 No evolve text. [V2]
- **十天衆の頭目・シエテ** (4, Legend, 4/3) — c10424120: 「【ファンファーレ】【奥義】自分の場の進化前のフォロワーすべては進化する。」 and 「【解放奥義】進化するのではなく超進化する。」 [V2 magazine + DB]. 奥義 = gauge 10, 解放奥義 = gauge 15 (§0).

### 3.2 Lethal math [INFERENCE from the text above; matches the note by ホヤ (pack 8): 「マーズ8点、ギルダリア＋バニバロ8点の9ターン16点ライン」]
- **連携 count** = followers that have entered your field this match.
  - Every token counts: ナイト, スティールナイト, and the Bunny & Baron copy.
  - Mars alone adds 4 (Mars + 3 Knights). Game8: 「マーズで連携20を達成し、そのあとはバニー＆バロンやギルダリアの連打」.
- **Mars, 8 PP:**
  - Mars enters 1/5 Storm. The 3 Knights each enter as 3/1 Rush and give Mars +1, so Mars is 4/5.
  - Evolve: 6. Super-evolve (+3/+3, plus 1 more Knight, +1): 1+3+3+1 = **8 face**.
  - The Knights have Rush only, so they cannot hit face that turn.
- **Gildaria (at 連携≥20) + Bunny & Baron, 9 PP:**
  - Gildaria gets the crest and evolves, summoning 2 スティールナイト → 2.
  - B&B enters → 1. Its copy enters → 1. B&B's 連携20 fanfare → 4.
  - Total = **8**, with no attacks. Every new follower also gets Rush from Gildaria.
- **Two turns, turns 9–10, ≈16 or more:** Mars turn (8), then Gildaria + B&B (8). This is the 「16点ライン」.
  - Any followers already on board add damage, Cesar's Ward board keeps them alive, and ベルテゾール (10 PP, 3 attacks, Storm) is the top end in the 後ろ寄せ list.
- **Bunny & Baron ×2 at 連携20 (10 PP):** 2 × (4 + 2 entries ×0) = 8. With the Gildaria crest active it would be more, but Gildaria + 2 B&B costs 14 PP, which is not possible.
- **シエテ (4):** 奥義 evolves every unevolved ally on the field. That triggers each one's 【進化時】, including Gildaria's Steelclads and the 3-damage pings from 衛生兵 and 諜報兵, and gives each Rush plus +2/+2. 解放奥義 (gauge 15) super-evolves them all.
  - 後ろ寄せ line: 「分班長シエテ」 on turn 9 (5+4 PP; ホヤ, pack 7) to pump a board that survived. This is the "連携進化ロイヤル" face of the deck.

### 3.3 Lists and turn plan
- **Game8 781940 (09-30), two lists** (in royal.md B1):
  - 前寄せ: クイックブレイダー/援軍/ナハト, 3 Mars.
  - 後ろ寄せ: ルリア1, シエテ3, ロードノエル2, ベルテゾール2.
  - Game8 adds: 「場にフォロワーが残った時のセザールは特に強力です」 and 「8PPのマーズから一気に攻め立てましょう」.
- **No 9th-pack player list or hash was found.**
- **Post-patch ladder (shadowverse-wins, 10-04 to 10-07):**
  - kt 14連勝 BEYOND (10-05): 「連携進化ロイヤルで…対面によって連携ロイの顔と進化ロイの顔を使い分けつつ、攻め受け両刀」.
  - Rihito 10連勝 (10-07): 連携進化ロイヤル 「プレイング簡単でガチで楽しい」.
  - ゑ 12連勝 (10-04): 「安定感あって結構かてる！マーズはピン」 (only 1 Mars).
  - ありしべる 8連勝 (10-04): 「連携ロイヤルが1番やっぱり使いやすくて強い」.
  - 竜城めり 8連勝 (10-07).
  - All V1, decklists were images only, no hashes. → The post-patch build trend is toward the "進化" build (シエテ, Cesar super-evolve) with Mars cut to 1 copy [UNVERIFIED trend from 2 comments].
- **Turn plan** (Game8 + ホヤ, pack 7, structurally the same):
  - Turns 1–4: build 連携 with cheap followers and 優しき援軍 (2 Knights, or 4 when enhanced). Game8: 「進化可能ターンまでの盤面を取り返す能力は低いため、序盤では常に盤面の有利を取り続ける」.
  - Turn 5: 衛生兵 (draw 2 plus 2 Knights) or 分班長.
  - Turn 7: セザール (ホヤ calls it 「最強」; 超進化権はセザールに全通しした方が絶対強い).
  - Turns 8–9: ルリア (enhance 8 draws a 7+ cost follower and recovers 7 PP) into セザール, or 分班長 + シエテ, or Mars.
  - Turns 9–10: Gildaria + B&B lethal.
- **Mulligan** (Game8, verbatim in royal.md):
  - Always: 無音の包囲, 聴略の諜報兵, 優しき援軍 (援軍 has top priority).
  - With early plays secured: 衛生兵 and 分班長.
  - ホヤ: 「序盤のマナパスは敗北に直結します。マリガンはソフトに」.

### 3.4 Matchups

| Opponent | Verdicts |
|---|---|
| **Pirate Royal** | dexel matrix: 連携 ○ vs バルバロス (pre-buff) [V2 cross-row]. テンジン (Pirate, 10-06, post-patch): 「後攻の場合は、相手の『寛厳の音帥・セザール』とどう向き合うかが重要」; Pirate uses its extra PP to evolve Barbaros. Cesar's +1/+3 Ward board stops Rush trades but not flag Last Words or Storm Barbaros. → **Even, Cesar-dependent; probably worse after the Pirate buffs** [INFERENCE]. |
| **Ramp Dragon** | dexel ○ (Synergy row) and ▲ (Dragon row) [V2 cross-row]. ホヤ (pack 8) 微有利. Note: royal.md recorded 「不利」 from an English-translated summary; the raw matrix row shows ○. **Favorable** pre-patch. Dragon AoE plus バハムート (crest and board removal) are the risk. |
| **Combo / Dust Days Elf** | dexel "-" (even). No other source. |
| **Lastword Nightmare** | dexel "-" vs ミッドレンジNi. Old note (pack 7, ホヤ): Nightmare even. No 9th-pack source. |
| Amulet Bishop | dexel × (Synergy row) and ◎ (Bishop row) [V2]; Lilie (pack 8) 「祈ることで対策」. → **Unfavorable**. |
| Evolution Bishop | × (dexel). |
| Sephie Witch | ▲ (dexel); Kuru: Witch 「初手でセフィー引けていればほぼ負けない」. → **Unfavorable**. |
| AF Nemesis | ▲ (dexel). |

---

## 4. beyond-dexel matchup matrix (raw text rows, 2026-09-27, PRE-PATCH) [V2: the raw rows were copied twice, and the opposing rows agree, e.g. Sephie○Dragon ↔ Dragon▲Sephie]
Legend: ◎ 有利, ○ やや有利, - 五分, ▲ やや不利, × 不利.

| Row deck | MidNi | 魔手W | DDE | ランプD | AFNm | アミュB | セフィーW | 進化B | フェイスD | バルバロスR | 連携R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 連携R | - | - | - | ○ | ▲ | × | ▲ | × | - | ○ | ― |
| セフィーW | - | - | - | ○ | ○ | ○ | ― | ▲ | - | ▲ | ○ |
| アミュB | ◎ | × | - | × | ○ | ― | ▲ | ◎ | ○ | ○ | ◎ |

Caveats:
- The column header tiers in this fetch (e.g. ランプD T1.5, AFNm T1.5) differ slightly from the tier blurb in meta.md. [UNVERIFIED header]
- All three decks are "-" vs ダストデイズエルフ. Elf's own row is ○ only vs ランプD and バルバロスR.
- Pirate was buffed after this matrix, so treat the バルバロスR column as optimistic for all three decks.

---

## 5. Sources (with dates)
- beyond-dexel:
  - Beita セフィーウィッチ https://beyond-dexel.com/deck-witch-20260911/ (2026-09-11)
  - Figole 実験体ウィッチ /deck-witch-20260902/ (2026-09-02)
  - Song スペルウィッチ /deck-witch-20260830/ (08-30)
  - ダーモボー クキシロビショップ /deck-bishop-20260907/ (09-07)
  - NARU バルバロス /deck-royal-20260906/ (09-07)
  - Tier and matrix /dexel-decktier/ (09-27)
  - Index (root, /page/2/) and sitemap wp-sitemap-posts-post-1.xml. No Witch, Bishop or Synergy deck page dated after 09-11 exists.
- shadowverse-magazine card pages (c + card id): c10934110, c10931110, c10933110, c10933310, c10932310, c10932110, c10834110, c10664120, c10663210, c10062210, c10461110, c10962120, c10903210, c10724110, c10824110, c10824120, c10723110, c10424120 (undated).
- Game8:
  - Cards: セザール 781872 (2026-09-30), リアントース 763912, アズヴォルト 811034 (08-26)
  - Amulet Bishop 698347 (09-30), Synergy Royal 781940 (09-30)
  - Rules: 超進化 696356, キーワード 697567, 奥義 732594
- shadowversewbwiki セザール考察 (2026-04-30). appmedia リアントース 79779191 (2026-02-26). GameWith セフィー 573312 (no date).
- note:
  - くるー御名月 「現環境セフィーウィッチ考察」 https://note.com/kuru_minatuki/n/n42f1759073fd (2026-09-20)
  - ナカムラ 「セフィーウィッチ所感」 https://note.com/tdnshoptyknrtit/n/nb199b7ca5534 (08-28)
  - NAXAN 監獄ビショップ https://note.com/naxan13/n/n0d0341607b22 (09-18)
  - ハガネ アミュビショ https://note.com/novel_mango2288/n/nbfa73e152032 (09-03)
  - ホヤ 連携進化 https://note.com/452745274527527/n/n3c2ff1ecfac1 (05-17, pack 7)
  - Lilie 連携 https://note.com/lilie_lily/n/ne7025857871c (07-03, pack 8)
  - くるー 「新環境アミュレットビショップ考察」 (05-05, pack 7)
  - Took (09-12)
- shadowverse-wins.com (?leader=W, ?leader=B, ?format=rotation&group=topaz&leader=R&mp=A&seasonId=69, single.php?manageId=109046/109126/109127/109147/109188/109195), entries from 2026-09-21 to 10-07.
- Local data: /home/claude/sv/svsim/cards/data/rotation.json (stats, tokens), cards/*.py docstrings, docs/architecture.md §13 (open fusion-rule question).
- Not readable:
  - YouTube (429): pAS9tOcYAlI 「13連勝 改良版実験体ウィッチ」, or8K-KdY6rE, -0V-CnD6J2w 「逆OTKアミュレットビショップ」, TkitKHJvw_A 「対面してて強かった連携ロイヤル」, g95H9bFtR3I 「修正で楽しさ倍増した連携進化ロイヤル」, iQOnC6ou1XY 監獄ビショップ.
  - x.com (robots).
  - GameWith 573926, 580404 (監獄ビショップ), 546031, 558814 (403).
  - hon-to-game.com (timeout).
