# Shadowverse: Worlds Beyond — rules check (researched 2026-10-07)

Tags: [V2] = two independent sources agree (or the same page fetched twice with consistent verbatim text); [V1] = one source; [UNVERIFIED] = inference or summarizer-only.
Note: the official site (shadowverse-wb.com) card list and system pages render via JS, and the /ja/rule/ page returned 403, so I could not get official Q&A text through WebFetch. Every citation below is to press coverage of the official announcements (2025-03-13) or to strategy sites (Game8, GameWith, AppMedia). The summarizer sometimes made errors (see item 5), so the verbatim quotes are only those that came back the same twice.

## 1. Evolution / Super Evolution
- 進化: 先攻 can evolve from its 5th turn, 後攻 from its 4th. [V2] Game8 696356 and 696114, AppMedia 78980654, GameWith 497248 ("後攻4ターン目から可能"). (GameWith 497213 says "both turn 5". That is an outlier or a summarizer error.)
- 超進化: "先攻は7ターン目、後攻は6ターン目から可能" [V2] Altema chousinka, GameWith 497248, Game8 696356, AppMedia.
- EP = 2 for both players: "持っている EP の数を先攻、後攻とも 2 ポイントに統一" [V2] (denfaminicogamer 2025-03-13, Game8 698154). SEP = 2 for both players: "「EP」と「SEP」は 1 戦の中でそれぞれ「2 回」ずつ、合わせて「4 回」" [V2] (denfaminicogamer, 4gamer 2025-03-13).
- Stat bonus: "フォロワーが進化した時の攻撃力・体力の上昇値はそれぞれ＋2、超進化した時はそれぞれ＋3に固定されます。" [V2] (denfaminicogamer, 4gamer).
- Super-evolve text from the official announcement, quoted by 4gamer 2025-03-13: "SEPを1点消費して実行できる。指定した味方フォロワーの攻撃力 / 体力を3ずつ増加させ，【突進】を付与し，自ターン中に受けるダメージが0になり，能力によって破壊されなくなる。" [V2]. The immunity is to damage taken during your own turn and to destruction by abilities during your own turn (AppMedia: "自分のターン中は能力によって破壊されない"; note.com 2025-07-07: survives 必殺 too).
- Knockback: when the super-evolved follower destroys an enemy follower, it deals 1 damage to the enemy leader. [V2] (4gamer, Altema "相手のフォロワーを破壊すると、相手リーダーに対して1ダメージを与えられます", GameWith).
- Only one evolve OR super-evolve per turn (Game8 696356). [V1] Super-evolving also fires 【進化時】 abilities: "特別な記載がない限りは超進化時にも発動します。" [V2] (note.com, AppMedia, GameWith.net 68403).

## 2. エクストラPP (second player only)
- Official wording (denfaminicogamer and 4gamer, 2025-03-13): "後攻のプレイヤーが任意のタイミングで自分の残り「PP(プレイポイント)」を+1することができます。「エクストラ PP」は 5 ターン目までに 1 回、6 ターン目以降にもう 1 回使用することができ、最大 2 回まで使用することができます。" [V2]
- No carry-over: "5ターン目までに使わず6ターン目以降に2回使うことはできません" (Game8 696480). An unused first charge is lost after turn 5. [V1] There is therefore no "refresh" as such; it is a second, separate charge that becomes available from turn 6. GameWith calls it "6ターン目に1度だけエクストラPP回復", which describes the same thing.
- The +1 lasts only for the turn it is used: "使ったターン中のみPPを1増やせる" (Game8 698154). An activation you don't spend is wasted. [V1]
- You can cancel the activation until you play a card: "エクストラPPを有効化した後でも取り消すことは可能ですが、この状態でカードをプレイすると取り消すことはできません" (Game8 696480). [V1]
- It raises current PP, not max PP, so it should not count toward 覚醒. [UNVERIFIED inference]

## 3. 覚醒 (Overflow)
- "自分の最大PPが7以上の状態" (Game8 keyword list 697567, fetched twice). [V2-same-page]

## 4. Does evolving by a card effect fire the follower's 【進化時】?
- No. Game8 keyword list: 【進化時】 = "EP（進化権）を使用して進化した時に発動。" (fetched twice). [V2-same-page]
- Yahoo知恵袋 (2025-06-22/23) quotes the official help for super evolution: "SEPを消費して超進化したときに、能力が働きます。" Its best answer reads: "超進化時の効果/進化時の効果は発動しません。超進化ポイントを消費しての進化ではないからです。" [V1, community quoting official]
- Abilities worded "フォロワーが進化したとき" (for example ササニド's 信仰) DO trigger on effect evolution (GameWith 546208; おんJ wiki 進化時 page). The evolved stats and "進化後なら" conditions still apply.
- So a follower evolved by カットスロート's crest ("自分がフォロワーをプレイしたとき、自分のターンごとに1回、それは進化する。"), by 天槍の深淵 ("自分の場の進化前のフォロワー1枚を選ぶ。それは進化する。") or similar gets +2/+2 but not its own 【進化時】. [V1-V2; no official card Q&A found]

## 5. Countdown / 戦慄の海賊旗
- Countdown: "ターン開始時にカウントが1つ減り、0になったら破壊される" (Game8 697567). Game8 doesn't say whose turn. By SV convention it is the owner's turn start. [V1]
- 戦慄の海賊旗 token: "【カウントダウン_7】自分がスペルをプレイしたとき、これのカウントを-1する。【ラストワード】相手のリーダーに2ダメージ。" (GameWith 573272). It is made by 逆行の咎人バルバロス: "『戦慄の海賊旗』1枚を自分の場に出す。自分の場の『戦慄の海賊旗』すべてのカウントを-5する。" [V1]
- Treasures (財宝): the dagger's name per Game8 is 「黄金の小剣」, not 短剣. Game8 712986 / 712988 / 712987 list 黄金の小剣, 黄金の靴 and 黄金の杯 as 1-cost スペル (タイプ 財宝). [V1 each]
  - 黄金の首飾り ("自分の場のフォロワー1枚を選ぶ。それは+0/+1して【守護】を持つ。", cost 1): the summarizer called it an amulet but admitted the page only shows タイプ 財宝. The effect is spell-style.
  - Verdict: all four are very likely spells, so each one lowers the flag's count by 1. [V1 for 3; UNVERIFIED for 首飾り]

## 6. 世界の味方・ゾーイ (Dragon, 5 cost) — Game8 734041, fetched twice, consistent [V2-same-page]
"【ファンファーレ】自分のPP最大値を+1する。【エンハンス_10】これは【疾走】を持つ。自分のリーダーの体力の最大値を1にする。相手のターン終了まで、自分のリーダーは「受ける1以上のダメージを0にする。」を持つ。"
- Max HP is set to 1, which is permanent (no duration). The damage immunity lasts until the end of the opponent's next turn.
- Current HP: no source states it. By the standard rule, current HP is capped at the new max, so it becomes 1. [UNVERIFIED]

## 7. バーンドナイト / イランツァ
- 焦灰のアナテマ・バーンドナイト (Dragon, 9 cost; Game8 781902, fetched twice) [V2-same-page]:
  - 進化前: "【ファンファーレ】相手の場のフォロワーすべてに9ダメージ。"
  - 進化後: "【超進化時】相手は『クレスト：焦灰のアナテマ・バーンドナイト』を持つ。"
  - Crest: "自分のターン開始時、自分のリーダーに2ダメージ。自分のリーダーが回復したとき、自分のターンごとに1回、自分のリーダーに1ダメージ。" ("自分" here is the crest holder, i.e. the opponent.)
- 律する《正義》・イランツァ (Dragon, 10 cost; Game8 752648, fetched twice) [V2-same-page]:
  - 進化前: "【守護】 自分のターン終了時、これが進化前なら、相手の場のフォロワーからランダム2枚に8ダメージ。自分のリーダーを8回復。"
  - 進化後: "【進化時】これは【守護】を失う。これは【威圧】を持つ"
  - The summarizer showed "cost 10 (evolved: 8)", which is probably a stat mix-up. Check the stats if they matter.
- Aura and random damage: オーラ = "相手の能力で選択できない". Random damage does not select a target, so it hits Aura and Stealth followers. note.com (2025-07-07) gives 「神の雷霆」's random damage as the answer to 潜伏/オーラ. → イランツァ's random 8 damage CAN hit オーラ followers. [V1]

## 8. Keywords (Game8 697567)
- 守護: "相手は守護を持つフォロワー以外を攻撃できない". A 疾走 follower therefore can't hit the leader past a 守護 follower. [V2 with SV convention]
- 威圧: "このフォロワーは攻撃されない" (Game8). Gamerch: "相手のフォロワーから攻撃されない". Game8 783119: "相手から攻撃対象に選ばれない能力". It covers attacks only, so the follower can still be targeted by abilities (Game8 has a page of 威圧 removal cards). [V2]
- 必殺: "ダメージを与えたフォロワーを破壊する（0ダメージでも破壊する）". It does not kill a super-evolved follower during its owner's turn. [V1 note.com]
- オーラ: "相手の能力で選択できない".
- 潜伏: "相手の能力で選択されず、相手のフォロワーから攻撃されない".
- 疾走 vs 突進: 疾走 can attack followers or the leader the turn it is played; 突進 can attack followers only.

## 9. Mulligan
- Game8 696222: "デッキから4枚のカードを引く" → "不要なカードを好きな枚数（0〜4枚）選んでデッキに戻す" → "デッキに戻した枚数と同じ枚数のカードを新たに引き" ; "マリガンは1回しか行えません。" [V1 detailed, consistent with Game8 696114]
- Whether returned cards can be redrawn is not stated. In the original SV the replacements are drawn before the returned cards are shuffled back, so you can't redraw them. Probably the same in WB. [UNVERIFIED]

## 10. Opening hand / first draw
- Opening hand is 4 cards: "初期手札が3枚から4枚に変更" (GameWith 497213), "初手の枚数が3枚から4枚に増え" (Game8 698154). [V2]
- "先攻・後攻の最初のターンのドロー枚数は1枚に統一" (Game8 698154; GameWith agrees). The first player DOES draw 1 on turn 1. [V2]
- Other basics (Game8 696114): leader HP 20, 40-card deck (max 3 copies), max hand 9, 5 board slots, max PP 10. [V1]

Sources: 4gamer.net/games/760/G076037/20250313060/ ; news.denfaminicogamer.jp/news/2503132c ; game8.jp/shadowverse-beyond/{696356,696114,698154,696480,697567,696222,734041,752648,781902,712986,712987,712988,712989,783119,811028,764093} ; gamewith.jp/shadowverse-wb/{497213,497248,573270,573272,546208} ; altema.jp/shadowversewb/chousinka ; appmedia.jp/shadowverse-wb/78980654 ; note.com/ham_delicious/n/n9220db583332 ; detail.chiebukuro.yahoo.co.jp/qa/question_detail/q10316620810 ; gamerch.com/shadowverse-wb/922906
