# Research: コンボエルフ / ランプドラゴン / フェイスドラゴン (Rotation, 第9弾「アズヴォルト・レヴナント」環境)

Collected 2026-10-07. All quotes were obtained via WebFetch (a summarizer model sits between the page and me). Where I say "verified x2" the text came back the same from two differently-worded fetches. "(1 fetch)" = seen once only, treat with care. English glosses are mine.

## 0. Environment facts / cross-deck findings

- **Game8 Rotation Tier表** https://game8.jp/shadowverse-beyond/694512 — 最終更新 2026年10月7日 05:39. Tier1: 海賊ロイヤル / ラストワードナイトメア / **ランプドラゴン** / **コンボエルフ**. **フェイスドラゴン = Tier2**. Comments (1 fetch):
  - ランプドラゴン: 「PP加速で大型フォロワーを展開。相手の制圧盤面をひっくり返せる。コンボが少なく初心者にもおすすめ」
  - コンボエルフ: 「ダストデイズでデッキフォロワーを強化。強化した高スタッツフォロワーで一気に攻める」
  - フェイスドラゴン: 「疾走＆威圧持ち主体のアグロデッキ。難しいことは考えずに相手のリーダーを狙える。必須レジェンドは少なく低レアで代用可」
  - No usage / win-rate numbers on the page.
- **GameWith Tier page** https://gamewith.jp/shadowverse-wb/497197 — the fetch returned what looks like an older (第8弾) tier list (Tier1 テンポエルフ/魔手ウィッチ/ランプドラゴン/疾走AFネメシス/破壊ネメシス), no update date. **Unverified / probably stale cache; do not use.**
- **ガルミーユ (烈絶の顕現・ガルミーユ) has ROTATED OUT at 第9弾** — verified x2 from independent sites:
  - Game8 ローテ落ち一覧 https://game8.jp/shadowverse-beyond/776155 (最終更新 2026-09-30): ドラゴンは「烈絶の顕現・ガルミーユ」がローテ落ち; it was 「ドラゴンのデッキを組むならまず3枚入れるカード」, rotation is 「厳しい状況」 for Dragon. Elf loses 「不殺の継承者・クルル」 (テンポエルフが弱体化).
  - GameWith ランプドラゴン入れ替え候補 (プロミネンスロア): 「ガルミーユが落ちて評価が下がった」.
  - => **The Game8 Ramp Dragon page's マリガン table and 立ち回り still mention ガルミーユ and 舞姫 (stale text from 第8弾); the Game8 deck list itself has neither.** (The caller's warning about a hallucinated ガルミーユ: the page *does* literally contain it — confirmed with image links to game8 712329 — but it is stale, not playable in Rotation now.)
- Rotation = latest 6 packs (Game8 776155: 「ローテーションは最新の6パックで戦われるモード」). All decoded cards are set 10004–10009 (+ basic 竜の啓示 set 10000), consistent.
- Tournament / streak data:
  - SNC 2026 Grand Finals (NetEase, Guangzhou), 2026-09-19, 2-deck BO3: champion 「b站美少女莉莉猪」 used **人形ウィッチ + ランプドラゴン**. Source https://beyond-dexel.com/shadowverse-snc-grand-finals-result/ (1 fetch; no deck distribution numbers; format (rotation?) not confirmed).
  - shadowverse-wins.com (Twitter streak aggregator), Rotation Dragon, Azvaldt season https://shadowverse-wins.com/?format=rotation&group=topaz&leader=D&mp=A&seasonId=69 : 2026/09/16–09/21 entries incl. ランプドラゴン 13連勝 (砂利 暴威, 9/21), 13連勝 (まさきんぐ, 9/20), 10連勝 (カツうどん, 9/20), 8連勝 (がわこ, 9/18); フェイスドラゴン 6連勝 (ボール, 9/17); a "ドラゴン" 22連勝 (みけきゅあすかい, 9/16). (1 fetch; archetype labels as summarized.)
  - beyond-dexel: ランプドラゴン 味噌日 **CR瞬間1位** (9/17); ダストデイズエルフ Spicies **CR最終2位** (9/29), NARU **Dexel StarSeed Cup優勝** (9/7), hqzuki 6連勝でBEYOND到達 (9/1).
  - No public aggregated win-rate / usage-rate numbers found for any of the three decks.
- Sites that failed / were stale: gamewith.jp started returning **403** mid-session (Face Dragon page 503021 and dragon list 558713 never fetched); shadowverse.gg Ramp guide 403; altema deck17 (Face Dragon) is from 2025-07-01 and gamerch 927385 from 2025-07-10 (old 1st-pack lists — ignored); note うさごん 疾走ドラゴン (2025-10-12) and note kt ランプ徹底解説 (2025-11-08) are old environments — ignored. shadowverse-magazine deck index showed nothing newer than 2026/05. appmedia: no relevant page found.

---

## 1. ランプドラゴン (Ramp Dragon)

### 1.1 Sources
| # | Source | Date | Notes |
|---|---|---|---|
| R1 | Game8 https://game8.jp/shadowverse-beyond/698541 | 最終更新 2026.10.06 05:28 | Tier1. Deck list current; mulligan/立ち回り text partially stale (ガルミーユ, 舞姫) |
| R2 | GameWith https://gamewith.jp/shadowverse-wb/503022 | 最終更新 date not rendered | Tier A, 生成コスト 90,990, フォロワー30/スペル8/アミュレット2. Card list not extractable (images); no hash found |
| R3 | beyond-dexel 味噌日 CR瞬間1位 https://beyond-dexel.com/deck-dragon-20260917/ | 公開 2026.09.17 / 更新 2026.09.18 | Best matchup-level mulligan source |
| R4 | note いろは「ランプドラゴン 解説」 https://note.com/m_o_o_m7/n/n06da885a9fe0 | 2026-09-15 11:11 | 前期最終1桁. Free part only; rest ¥300 paywall |
| R5 | note Kamijames「キミカ天刀型ランプD解説」 https://note.com/kj_ssbu/n/nc8bc41af0661 | 2026-07-16 | **Pre-第9弾 (8弾 environment, has ガルミーユ)** – only for general principles |
| R6 | beyond-dexel しし氏 CR最終1位 (2026-07-30), Amano CR瞬間1位 (2026-07-05) | pre-第9弾 | not fetched (old env) https://beyond-dexel.com/deck-dragon-20260730/ , https://beyond-dexel.com/deck-dragon-20260705/ |
| R7 | YouTube 「【Tier1筆頭！】ノマグダラ←ガチでヤバい！「ランプドラゴン」デッキ&マリガン&立ち回り解説！！」 https://www.youtube.com/watch?v=QoeZvypWJew | ? | not watchable via tools |

### 1.2 Deck share URLs (verbatim)
- R1 Game8 (2026.10.06): `https://shadowverse-wb.com/ja/deck/detail/?hash=1.4.cJl6.cJl6.cJl6.dhqm.dhqm.dhqm.drrO.drrO.drrO.e4IE.e4IE.eDpc.eDpc.eE3E.eE3E.eE3E.eEFk.eEFk.eEFk.ecgE.ecgE.ecgE.ecgO.ecgO.ecgO.e-Ls.e-Ls.e-Ls.e-ec.e_4k.e_4k.e_4k.fN08.fN08.fNVO.fNVO.fNVO.flvu.flvu.flvu` (verified x2)
- R3 味噌日 (2026.09.17/18): `https://shadowverse-wb.com/ja/deck/detail/?hash=1.4.cJl6.cJl6.cJl6.dhqm.dhqm.dhqm.drrE.drrE.drrO.drrO.drrO.eDpc.eE3E.eE3E.eE3E.eEFk.eEFk.eEFk.ecgE.ecgE.ecgE.ecgO.ecgO.ecgO.e-Ls.e-Ls.e-Ls.e_4k.e_4k.e_4k.fN08.fN08.fNIk.fNIk.fNVO.fNVO.fNVO.flvu.flvu.flvu` (1 fetch, decodes to a legal 40)

Game8 list in Japanese (verified: page list matches decode):
空の命運を握る少女・ルリア×3 / 旧き天刀・ヴォーラライ×3 / 喧伝の龍人×3 / 笑顔の調理・キミカ×2 / 怠惰なる波揺花×3 / 竜の啓示×3 / 焦龍の午睡×1 / プロミネンスロア×2 / 世界の味方・ゾーイ×3 / 《世界》の提示×2 / 断頭の斬姫・サガツマツ×3 / 禁牙の変貌・ノマグダラ×3 / 金銀絢爛・リュミオール＆アルジャンテ×3 / 焦灰のアナテマ・バーンドナイト×3 / 律する《正義》・イランツァ×3. 必要エーテル 84,170.

R1 vs R3 difference (from decodes): R3 = +狐火陽炎×2 (1-cost), +炎の理・ウィルナス×2; −《世界》の提示×2, −焦龍の午睡×1, プロミネンスロア 2→1. Neither has クラゲの舞姫 or バハムート.

Decoded card lists: see Appendix D1, D2.

### 1.3 Game8 (R1) verbatim — verified x2 unless noted
**マリガン早見表**: 共通「全対面・先攻後攻問わずキープ」: 喧伝の龍人 / 竜の啓示 / 烈絶の顕現・ガルミーユ (**stale – rotated**) / 世界の味方・ゾーイ / 金銀絢爛・リュミオール＆アルジャンテ. コントロール対面: 焦灰のアナテマ・バーンドナイト.
- 「PPブーストカードは最優先でキープ」: 「ランプドラゴンはどれだけ早くPPブーストできるかで動きが決まるため、PPブーストカードは先攻後攻問わずキープがおすすめです。」 (Keep PP-boost cards first, on play and draw.)
- 「コントロール対面ではバーンドナイトをキープ」: 「序盤にフォロワーが展開されないアミュレットビショップなどの対面では、最速でバーンドナイトをプレイしたいため、キープがおすすめです。」 (vs Amulet Bishop etc., keep Burnite to slam it ASAP.)

**立ち回り** (headings: 序盤はPPブーストでPPを伸ばす / 舞姫や波揺花で相手の盤面に対応 [heading in summary table; body heading says 喧伝の龍人や波揺花] / ガルミーユで有利状況を作る [stale] / バーンドナイトのクレストを付与する / 疾走やバーンダメージで体力を削る)
- 「序盤はPPブーストカードでPPを伸ばしていきましょう。ゾーイは若干コストが高いので置くのに時間がかかりますが、竜の啓示や退屈な睥睨はコストが軽いため最速で使えるとその後の展開がしやすくなります。」 (「退屈な睥睨」 is not in the list — stale, unverified card.)
- 「相手の動きが早い場合や理想的な展開を押し付けられている場合は、喧伝の龍人や波揺花などを使って対応しましょう。」 (vs fast starts, answer with Promoter / Crestpetal.)
- 「中盤以降はガルミーユで有利な状況を作っていきましょう。クレストで相手フォロワーしながら10PPまで繋げられると理想です。」 (stale)
- 「9PP到達後はバーンドナイトのクレストを付与しましょう。毎ターン相手リーダーに2ダメージが入るため、リーサルを狙いやすくなります。」 (At 9PP super-evolve Burnite for the crest: 2 dmg to enemy leader every turn.)
- 「10PP到達後は《世界》の提示やイランツァなどで対戦相手の体力を削りましょう。1ターンで削りきれない場合は、回復やゾーイのエンハンスで耐久し、次のターンにリーサルを狙いましょう。」 (At 10PP push face with Fate of the World enhance / Erntz; if no lethal, stall with healing or Zooey enhance 10, then lethal next turn.)

**対策 (= weaknesses)**:
- 「序盤のPPブーストは隙が生まれやすい」: 「ドラゴンのPPブースト効果を持つスペルは序盤はPPブースト以外の役割を持たず、プレイするターンは盤面に干渉できないため隙が生まれやすいです。最序盤からこちらがフォロワーを並べて相手にPPブーストを使わせない、またはPPブースト直後に強い動きをすると隙をついていくことができます。」 (Ramp turns don't touch the board; opponents flood early or punish the turn after.)
- 「威圧フォロワーを処理できるようにする」: 「ドラゴンは終盤に大型の威圧フォロワーを置いてくるので、こちらの対策は必須です。威圧は攻撃されないだけで効果自体は受けてしまうので、各クラスに存在する除去効果持ちのカードを威圧フォロワーに対して使っていきましょう。」 (pictures 炎の理・ウィルナス, イランツァ)
- Game8 has no 対面別 / 採用候補 section for Ramp.

### 1.4 GameWith (R2) verbatim (1 full raw fetch; consistent with 2 earlier summary fetches)
評価: Tier A / レンジ コントロール / プレイ難度 簡単. 簡易評価: 「・ランプを主軸としたデッキ ・威圧カードの押し付けや疾走カードが強力 ・ノマグダラの追加により耐久力UP」. 「ランプドラゴンは、PPブーストして高コスト帯の強力なカードで勝ちに行くデッキ」.

**立ち回り**
- 序盤はフォロワーを並べつつPPブースト: 「序盤は竜の啓示やリュミオール&アルジャンテ（アクセラレート）などのランプカードをプレイし、PPの最大値を増やしましょう。」
- **ランプ後は盤面を処理orフォロワーを置く**: 「ランプをしたターンは盤面が弱く相手に攻める隙を与えてしまうので、ランプをした次のターンは必ず相手の盤面を処理したり、強いフォロワーを立ててテンポロスを取り返すような動きをしましょう。」 (After a ramp turn, the next turn MUST clear or develop to win back tempo.)
- ランプができない場合も処理で時間を稼ぐ: 「PPブーストができないターンには、フォロワーを展開したり、怠惰なる波揺花や喧伝の龍人などで盤面を処理しましょう。なるべく体力を高く保ったまま序盤〜中盤を乗り越えるのが目標です。」
- **中盤は隙を見てランプし7PPを目指す**: 「中盤も序盤と同様に相手の盤面が弱いタイミングではランプをし、相手の盤面が強い時は進化も駆使して盤面処理行いましょう。7PPになるとノマグダラやサガツマツといった強力なフォロワーがプレイ可能になり、覚醒能力が使えるようになります。」 (= ramp vs answer rule: ramp when their board is weak; when it's strong, spend evolves to clear.)
- 強力なフォロワーで盤面をひっくり返す: 「7PPに到達したらノマグダラやウィルナスで相手の盤面を除去して強力なフォロワーを場に残し圧を掛けましょう。相手の盤面が弱い時はサガツマツでリーダーを攻撃し体力に圧を掛けましょう。」
- 終盤は各種打点カードで体力を削る: 「終盤はバーンドナイトで盤面処理しつつ、超進化でクレストを付与しましょう。毎ターン2ダメージを与えられるようになるため、クレスト付与後はイランツァやサガツマツでリーサルが取れる体力になるまで時間稼ぎをしましょう。」
- **回復と守護で守りを固める**: 「体力に余裕がない場合は、ノマグダラやイランツァの進化前で盤面処理しつつ回復しましょう。試合が伸びるほどバーンドナイトによるダメージの蓄積でアドバンテージが取れるため、バーンドナイト後は迷ったら耐久するのがおすすめです。」 (Unevolved Normagdala/Erntz = heal + clear; after Burnite crest, when in doubt, stall.)
- バハムートで厄介なカードを対策: 「バハムートは盤面、クレスト、アミュレットを消滅させることができます。…厄介な盤面、ラストワード、クレスト、アミュレットを消すことで相手の戦術を崩すことができます。」 (GameWith list apparently runs バハムート — card/count not verified; not in R1/R3.)
- ダメージを押し込みフィニッシュ: 「バーンドナイトのクレストのダメージと相手の回復量を考慮して2ターンで削り切る意識で攻めるのがおすすめです。」
- エンハンスゾーイで時間を稼ぎながら攻める: 「もう1ターンあれば削りきれる時や、相手のリーサルが見えている時はエンハンスでゾーイをプレイすることで1ターン時間を稼ぎながら次のターンのリーサルを狙うことができます。」

**マリガン**
- 「ランプ札と低コストフォロワーをキープ」: 「PPブーストを進めるランプ札と、序盤の動きを安定させる低コストフォロワーをキープするのが基本です。」
- 「上記のカードとゾーイをキープ」: 「ランプ札や低コストフォロワーと合わせて、PPブーストができるゾーイもキープ候補になります。」
- 「盤面展開が強力な対面では処理札をキープ」: 「ロイヤルやナイトメアなど、序盤の盤面展開が強力な対面では怠惰なる波揺花、暗黒次元、プロミネンスロアなどの処理札をランプ札と合わせてキープしましょう。」 (GameWith list includes 暗黒次元 — not in R1/R3; R3 explicitly cuts it.)

**カード入れ替え候補** (verbatim bullets):
- 狐火陽炎: 体力1のフォロワーを処理できる / バーンドナイトと合わせてじわじわ削れる / 終盤は手札が減らず優秀
- 笑顔の調理キミカ: 2ターン目に出せてデッキを掘れる / ランプを引きに行けるのが強い / 回復でリーサルずらしも可能
- プロミネンスロア: 暗黒次元で処理ができない盤面を対処可能 / イマリ盤面やアサイラントなどに強い / ガルミーユが落ちて評価が下がった
- 最古の獄卒: 暇な6PPを埋められるカード / 守護と3面処理で耐久力が高い / アクセラレートで細かい処理もできる
- 断頭の天刀: ディスカードのディスアドを回避できる / 5コスト5点AOEの使い勝手が良い
- ウンギア: 並んだ体力1を3体処理できるのが利点 / 3/3にも対応可能

GameWith has no matchup table (fetch found none).

### 1.5 beyond-dexel 味噌日 CR瞬間1位 (R3) verbatim — mulligan & matchups verified x2
Intro: 「禁牙の変貌・ノマグダラ」の追加によって、pp加速から早期に大型フォロワーを着地させる動きがより重要になっています。
**マリガン**
- 「このデッキの勝率は、序盤のpp加速スピードと大型フォロワーの着地速度に直結します。」
- 最優先: 「竜の啓示」と「金銀絢爛・リュミオール＆アルジャンテ」は常に探索対象 (always hunt these two).
- 「世界の味方・ゾーイ」：先攻のみ単独でキープします。後攻はエクストラppの存在や盤面処理の要求が高いことから、キープせずに返します。 (Zooey: solo keep on play only; mulligan it on the draw because of extra-PP and board-clear demands.)
- 「笑顔の調理・キミカ」と「旧き天刀・ヴォーラライ」はセットでキープし、エルフ対面後攻・ドラゴン対面・ビショップ対面以外で採用します。 (Kimika+Vorlalai as a pair, except Elf-on-the-draw, Dragon mirror, Bishop.)
- ３コストブーストが引けている場合：「空の命運を握る少女・ルリア」「笑顔の調理・キミカ」「旧き天刀・ヴォーラライ」。先攻であれば、ドラゴン・ビショップ対面以外でキープします。 (If you have drawn the 3-cost boost, i.e. 竜の啓示 / 龙之启示 Dragonsign, the only 3-cost PP boost in this list: also keep 露莉亚 Lyria, 琪米卡 Kimika and 旧き天刀・ヴォーラライ, on play, except vs Dragon/Bishop.) [re-fetched verbatim 10-07 18:10Z, two fetches agree; the earlier line was a subject-less paraphrase. Source is the beyond-dexel article R3, not a video. Same section: Kimika+Vorlalai pair reads 「セットでのキープ。揃った場合は、エルフ対面後攻、ドラゴン対面、ビショップ対面以外ではキープします。」]
- 「喧伝の竜人」は後攻かつエルフ・ネメシス対面、「怠惰なる波揺花」は後攻かつエルフ・ナイトメア対面でキープします。 (Promoter: on the draw vs Elf/Nemesis. Crestpetal: on the draw vs Elf/Nightmare.)
**対面ごとの立ち回り**
- [matchup play, not mulligan; 「ウィルナスの体力」 = Wilnas's own health] ミッドレンジナイトメア戦: 「炎の理・ウィルナス」の早期着地を軸に戦います。ウィルナスの体力を7以上でキープできると高確率で盤面に残存します。着地に失敗した場合は「断頭の斬姫・サガツマツ」の疾走で積極的に攻め、長期戦になる前に決着をつけることが重要です。
- ダストデイズエルフ戦: 同じくウィルナスが強力ですが、相手の回答札が複数存在するため、ウィルナス単独では勝ち切れない場合があります。サガツマツで相手の「離合の有終・セタス＆メイシア」を妨害しながら継続的に攻める意識が必要です。
- 進化ネメシス戦: 「劣悪の純心・カミシラ」の盤面が非常に重く、常に対応できる手札を整えることが肝要です。進化権の温存を優先し、不用意に消費してはいけません。ウィルナスで最速のカミシラを1ターン牽制する選択肢も有効です。 (Save evolve points.)
- No mirror section, no turn-by-turn section, no mention of バーンドナイト/イランツァ/超進化 (verified by direct question).
**採用・不採用**
- 「狐火陽炎」: 序盤の除去と終盤の打点を両立でき、ナイトメア対面で1コスト除去として機能します。
- 「笑顔の調理・キミカ」: 2コストフォロワー層の厚さが重要な環境において、ドローと終盤回復の両立が有用です。
- 「暗黒次元」は不採用: 後攻2ターン目のpp加速後では使いづらく、4コストAoEの採用メリットが低いため採用していません。

### 1.6 note いろは (R4, 2026-09-15) — free part
- 「ランプドラゴンはリスクを背負ってppを増やし、高コストのカードを相手より先に投げて戦うデッキです！！」 + judge whether to act with current hand or ramp for later turns.
- 全対面共通「先行後攻単キープ」: 「掲示、リュミオール1枚。このデッキの核、これが打てなければ勝てない、絶対にどんな状況であっても1枚は持ちましょう。」 (「掲示」 = 竜の啓示 presumably — author's spelling, verbatim.)
- キミカ: kept (fetch 1 said 先行単キープ; fetch 2 said simply キープ — **先後 condition unverified**).
- 後攻 EP tech (1 fetch, paraphrase by summarizer): 後3で掲示を打つ場合、後2のエクピを温存すると、ランプが続かなくても「後5で6pp+エクピ=7コスト」→ ノマグダラ/ウィルナス on 後5. (Keep the turn-2 extra PP; ramp on 後3; then 7-drop on 後5.)
- Key cards per matchup (1 fetch, table from summarizer): エルフ=ウィルナス; ナイトメア=ノマグダラ, ウィルナス; ウィッチ=サガツマツ, ウィルナス; ビショップ=バーンドナイト; ロイヤル旗=ノマグダラ, イランツァ. **Unverified (1 fetch).** Paywall ¥300 after this.

### 1.7 Kamijames (R5, 2026-07-16, PRE-第9弾 — principles only, 1 fetch)
対ドラゴン(ミラー)「2Cキープは基本先攻のみ」; ミラーは「ランプ札全力サーチ」; 超進化権を温存する判断が重要; 対ビショップ「バンドナ単キープ」検討; キミカ＋天刀「5PPキミカ進化で3コス3点AOEを飛ばしながら2回復」. (8弾 list; mentions ガルミーユ — not legal now.)

### 1.8 Mirror / クラゲの舞姫 / Garmille: what I could and could not find
- No post-9/29 source has a dedicated Ramp mirror section. Closest: 味噌日 (R3) excludes Kimika+Vorlalai keep vs Dragon and says 3-cost-boost extra keeps OK on play except vs Dragon; Kamijames (pre-9) "2C keep only on play, search ramp all-out".
- **クラゲの舞姫**: none of the current Ramp lists (Game8 R1, 味噌日 R3) run it; Game8's 立ち回り table heading 「舞姫や波揺花で相手の盤面に対応」 is stale (body heading uses 喧伝の龍人). No source explains a Jellyfish Dancer Ramp variant. coolyu (Face Dragon) cuts it for 「2/1スタッツ」.
- **ガルミーユ**: rotated out (see §0). Any Garmille-type advice is 8弾-era.

---

## 2. コンボエルフ / ダストデイズエルフ (Combo Elf)

### 2.1 Sources
| # | Source | Date |
|---|---|---|
| E-G8 | Game8 https://game8.jp/shadowverse-beyond/781941 — 「コンボエルフのローテーションデッキレシピと立ち回り・マリガン」, Tier1, ミッドレンジ, 必要エーテル 68,590 | 最終更新 2026.09.30 12:35 |
| E-SP | beyond-dexel Spicies (MURASH GAMING) CR最終2位 https://beyond-dexel.com/deck-elf-20260929/ | 2026-09-29 |
| E-NA | beyond-dexel NARU Dexel StarSeed Cup優勝 https://beyond-dexel.com/deck-elf-20260906/ | 2026-09-07 |
| E-HQ | beyond-dexel hqzuki 6連勝BEYOND到達 https://beyond-dexel.com/deck-elf-20260901/ | 2026-09-01 / 09-02 |
| E-GW | GameWith https://gamewith.jp/shadowverse-wb/559139 — rendered as 「バフエルフ」 page, Tier「-」, 70,690, no date (probably the same archetype under old name; low value) | ? |
| — | fuwakumo https://fuwakumo.net/shadowverse-wb/post-4276/ (not fetched) | ? |

### 2.2 Deck share URLs (verbatim)
- E-G8: `https://shadowverse-wb.com/ja/deck/detail/?hash=1.1.dhqc.e4Gg.e4Gg.e4Gg.e6FE.e6kU.e6x8.e6x8.e6x8.eVLe.eVLe.et1G.et4E.etl-.etl-.etl-.etm8.etm8.etm8.fGAU.fGAU.fGAU.fds6.fds6.fds6.fe5k.fe5k.fe5k.fe8s.fe8s.fe8s.feLM.feLM.feLM.fea-.fea-.fea-.feb8.feb8.feb8`
- E-SP: `https://shadowverse-wb.com/ja/deck/detail/?hash=1.1.e4Gg.e4Gg.e4Gg.eVLe.eVLe.eVLe.fFRw.fFRw.fFRw.fds6.fds6.fds6.dhqm.dkWU.etGk.etGk.etGk.fe5k.fe5k.fe5k.feLM.feLM.feLM.e6x8.e6x8.e6x8.fea-.fea-.fea-.e6kU.etl-.etl-.etl-.feOU.feOU.etm8.etm8.fGAU.fGAU.fGAU`
- E-NA: `https://shadowverse-wb.com/ja/deck/detail/?hash=1.1.e4Gg.e4Gg.e4Gg.e6FE.e6FE.e6kU.e6kU.e6x8.e6x8.e6x8.et1G.et1G.et1G.etGk.etGk.etl-.etl-.etl-.etm8.etm8.etm8.fGAU.fGAU.fGAU.fds6.fds6.fds6.fe5k.fe5k.fe8s.fe8s.fe8s.feLM.feLM.feLM.fea-.fea-.fea-.feb8.feb8`
- E-HQ: `https://shadowverse-wb.com/ja/deck/detail/?hash=1.1.e4Gg.e4Gg.e4Gg.eVLe.et1G.fFRw.fFRw.fFRw.fds6.fds6.fds6.dhqm.dhqm.etGk.etGk.etGk.fe5k.fe5k.fe5k.feLM.feLM.feLM.e6x8.e6x8.e6x8.fea-.fea-.fea-.e6kU.etl-.etl-.etl-.feOU.feOU.etm8.etm8.etm8.fGAU.fGAU.fGAU`
(each 1 fetch; all decode to legal 40-card Elf decks — Appendix E1–E4)

Game8 list in Japanese (1 fetch, matches decode counts): 発芽の組員×3, エルフトラッパー×1, 旧き天槍・ササニド×2, マインドシフト×1, 大遊戯世界×3, 根差の刺客×3, 枝葉の舎弟頭×3, 虫風花の飛翔×1, 緑傘会の二枚看板×3, 虫風花・ミロク×3, 煙管の咎人・マガチヨ×3, 優雅なる虫風花×1, 操嵩のアナテマ・ダストデイズ×3, 蒼い空を征く騎空士・グラン＆ジータ×1, 氷界の鹿王×3, 離合の有終・セタス＆メイシア×3, 香風の変貌・ヒエン×3.

### 2.3 Game8 verbatim (1 fetch each section; consistent across 2 fetches in substance)
- 序盤は盤面処理と手札交換を優先: 「序盤はフェアリーやダメージを飛ばす系のカードで盤面処理がメインになります。最速でダストデイズのクレスト発動を狙いたいので、ドローも優先しつつフィニッシャーが手札に来た場合は（マインドシフト等の）カードで山札に戻すことが重要です。」 (return finishers to deck so they get buffed later)
- 5PPでダストデイズ出し進化＋1コストカード使用: 「ダストデイズは進化時にクレストを付与し、3ターンの間、3コンボしたターン終わりにデッキのフォロワーに+1/+1バフを付与できます」。進化と同時に1コストカード使用でコンボ3達成が目標。
- バフをかけたフィニッシャーを引き込む: クレスト発動後、毎ターンコンボ3を達成しながらデッキのフォロワーにバフをかけ、「高スタッツで押し込んでいきましょう」。
- マリガン: 共通 = 操嵩のアナテマ・ダストデイズ; 次点 = 虫風花・ミロク, マインドシフト. 「ダストデイズは最速でクレストを発動させるのが重要で、使用するターンも早めなので初手で来た場合1枚はキープしておくのが良いでしょう」。
- No 対策/採用候補/対面別 section on Game8 (verified by direct question).

### 2.4 Spicies CR最終2位 (E-SP) verbatim-ish (1 fetch; returned in Japanese)
**マリガン**: 「核となるカードを探しにいく動きと、序盤の盤面を落とさないための妥協キープの二本立て」.
① 最優先: 「ダストデイズ」(デッキの核)、「大遊戯世界」(前後どちらの安定感にも貢献し、早く引くほど使いやすい).
② 妥協キープ: 「根差の刺客」(瞬間のテンポと後続の手数を同時に確保でき、2ターン目として最強)、「虫風花・ミロク」(序盤の処理か手数確保として優秀で、中盤以降も進化先として機能)。序盤の盤面で押し込まれないこと、むしろ押し込んでいくことの価値が高いため、ダストデイズが見えていなくてもキープする。
対面変更: ビショップなど序盤の面の取り合いの価値が低い対面では、「ダストデイズ」と「大遊戯世界」を全力で探す。
**立ち回り**
- vsミッドレンジ系統（エルフ、ロイヤル、ナイトメア、ネメシスなど）: 可能な限り進化、特に超進化の温存を意識する。「煙管の咎人・マガチヨ」でまとめて返し、「旧き天槍・ササニド」で回復する方が得なことが多い。
- **vsドラゴン**: 打点で押し込み、相手を回復に回らせることが必要。攻めてきたときに返しで勝てる状況を作っておく。序盤の盤面と「マガチヨ」の超進化が重要。 (Elf POV vs Ramp: pressure to force Normagdala heal mode; Magachiyo super-evolve = Storm.)
- vsビショップ: 「旧き天書・リアントース」を置く瞬間だけ相手の回復が弱くなる（「アドアマネージャー・イニシア」「崇高の憎悪・カンディマ」が使えなくなるため）。置かれる直前から打点を入れ始める。もう一つは5面展開して「リアントース」進化の処理漏れを起点に攻める形。
**自由枠**: ドラゴンへの警戒を落とすなら「彼岸陶酔」を減らすことは選択肢。代わりに「優しき読心者・ミツェル」がおすすめ…ダストデイズがない試合でも「ミロク」「ミツェル」から「離合の有終・セタス＆メイシア」へつなぐ。 (i.e. 彼岸陶酔 (Crimson Incense, 4-cost destroy+draw) is anti-Dragon tech.)
**ワンポイント**: 「ダストデイズが引けなそうな試合で、序盤の盤面と疾走打点で押し込むプランに切り替える判断ができると、勝率が少し上がります。」

### 2.5 NARU StarSeed Cup優勝 (E-NA, 1 fetch)
- マリガン: 「最優先（確定キープ）は『大遊戯世界』『操嵩のアナテマ・ダストデイズ』『エルフトラッパー』。ダストデイズが見えている場合は、序盤札も緩くキープを広げて良い。」
- 立ち回り: 「『大遊戯世界』『エルフトラッパー』で土台を整えつつ、『操嵩のアナテマ・ダストデイズ』のバフ後はとにかくドローを優先し、手数で押し切る形を作る。」
- 採用候補: 「緑風のレイピア使い」の3枚目と「グルーミーガール・モエル」（今回不採用）.

### 2.6 hqzuki (E-HQ, 1 fetch)
- マリガン: 最優先はドローソース掘り。「操嵩のアナテマ・ダストデイズ」「大遊戯世界」「枝葉の舎弟頭」を軸に、妥協案として「根差の刺客」と「虫風花・ミロク」。ナイトメア対面では後者2枚の優先度↑、ビショップ対面ではドローソース以外基本見送り。
- **ドラゴン対面**: テンポより「リソース稼ぐことを優先」。盤面の強さで「禁牙の変貌・ノマグダラ」の回復を制限し、横展開や高体力フォロワー複数並べで相手の回復モード自体を制御する。「離合の有終・セタス＆メイシア」超進化は「律する《正義》・イランツァ」対策に機能させる。 (Useful for Ramp player: Elf will go wide / high-HP to make Normagdala's -0/-4 mode mandatory instead of heal mode, and save Setus&Maisha super-evolve for Erntz.)
- 不採用: 「香風の変貌・ヒエン」：出す時のリソース消費が重く、明確な有効場面がナイトメア戦程度。**ドラゴンのバハムート複数採用も逆風材料**。「緑傘会の二枚看板」：前述カード非採用時のバリュー不足（セット採用前提）。

### 2.7 GameWith (E-GW, 1 fetch, low confidence)
入れ替え候補: エルフトラッパー（コンボを稼ぎやすくなる。戻したいカードが無い時は使いづらい）, アドベンチャーエルフメイ, 勇気に満ちし者, バベロンメイヤーエルタロ, グロースベア. マリガン: ダストデイズ優先、次点で大遊戯世界・ミロク、盤面デッキ対策にクルル (**クルル rotated out per Game8 776155 → this GameWith page is stale/unverified**).

### 2.8 Elf list variants
- Core in all 4 lists: 大遊戯世界×3, 発芽の組員×3, 根差の刺客, 枝葉の舎弟頭×3, 虫風花・ミロク×3, 煙管の咎人・マガチヨ×3, 操嵩のアナテマ・ダストデイズ×3, 離合の有終・セタス＆メイシア×3, 優雅なる虫風花 1–2, 氷界の鹿王 2–3.
- **Hien (香風の変貌・ヒエン) build** (Game8 3, NARU 2) with 緑傘会の二枚看板×3 + 虫風花の飛翔 vs **Hien-less build** (Spicies, hqzuki) with グルーミーガール・モエル×3, 緑風のレイピア使い×3, 彼岸陶酔×2, ルリア 1–2 (Spicies also 風の理・エイウニア? — decoded as 风之法则·艾云尼亚 ×1).
- Game8 uniquely has グラン＆ジータ×1, マインドシフト×1, ササニド×2.

---

## 3. フェイスドラゴン (Face Dragon)

### 3.1 Sources
| # | Source | Date |
|---|---|---|
| F-G8 | Game8 https://game8.jp/shadowverse-beyond/698337 — Tier2, アグロ, 必要エーテル 41,230 | 最終更新 2026.09.30 12:34 |
| F-CY | note coolyu「第9弾フェイスドラゴン考察」 https://note.com/coolyu338867/n/n06ea17479a38 — 「フェイスドラ界隈では最速でBEYOND達成、ドラ界隈7番目」 | 2026-08-31 23:07 |
| F-AM | Game8 アンテマリア card page https://game8.jp/shadowverse-beyond/811756 — 評価 S, 採用デッキ フェイスドラゴン | ? |
| — | GameWith https://gamewith.jp/shadowverse-wb/503021 — **403, not fetched** | — |
| — | altema deck17 (2025-07-01), gamerch 927385 (2025-07-10), note ra (2025-07-01), note うさごん (2025-10-12) — old environments, ignored | — |

### 3.2 Deck share URL (verbatim, F-G8, 1 fetch; decodes to legal 40)
`https://shadowverse-wb.com/ja/deck/detail/?hash=1.4.eDme.eDme.eDme.eE3E.eE3E.eE3E.eb-U.eb-U.ecTk.ecTk.ecgE.ecgE.ecgE.ecgO.ecgO.ecgO.fN08.fN08.fN08.flAs.flAs.flAs.flD-.flD-.flD-.flQU.flQU.flQU.flTc.flTc.flTc.flg6.flg6.flg6.fljE.fljE.fljE.flvk.flvk.flvk`
Game8 Japanese list (1 fetch; the summarizer omitted one 3x 1-cost — decode shows 碎裂的盗匪 / Ripper-Clawed Thief ×3, Japanese name not captured — coolyu calls it 「盗人」): 幼竜の癇癪×3, 絶倒の襲撃者×3, 笑顔の調理・キミカ×3, 旧き天刀・ヴォーラライ×3, クラゲの舞姫×3, 怠惰なる波揺花×3, ウンギア×3 (inferred = 利牙 Artiglio in decode, 3 dmg split; JP↔CN mapping not verified), 顎門の別れ×3, 天刀授与×2, 塵土の無頼漢×3, 断頭の斬姫・サガツマツ×3, 穿孔の咎人・アンテマリア×3, 断頭の天刀×2. (So クラゲの舞姫 appears in **Face** Dragon, not Ramp.)

### 3.3 Game8 text (verified x2)
「疾走で相手のリーダーを殴り続けて勝つアグロタイプのデッキです。序盤が弱いデッキや威圧フォロワーの除去が苦手なデッキに対して有利で、守護を展開できたり回復手段が豊富なデッキに対しては不利となっています。」 (Favored vs slow starters / decks bad at removing Intimidate; unfavored vs Ward-heavy / heal-heavy.) **Game8 has no マリガン or 立ち回り section for Face Dragon** (checked twice incl. offset read).

### 3.4 coolyu (F-CY) — 1–2 fetches, summarizer-mediated; quotes ≤ short
- Concept: 「低コストでアグロし、サガツマツ・アンテマリアという高打点フィニッシャーで締める」; 「顔を殴り続けないとデッキの出力が落ちる」; 「このデッキはアグロドラではなく、(中盤から)フェイス(を殴り続ける)ドラという認識」.
- マリガン (verified x2): 共通単キープ = 1コス, キミカ, ファイアリザード. セット = キミカ横に捨てれる札 / 1・2コスとセットでドラゴニュート / ウンギア, 無頼漢. 後攻 = アルフィード, ワイバーン. Do not keep サガツマツ/アンテマリア.
- 立ち回り: 「サガツマツは捨てろ」 — 「このデッキは7コス超進化1個で勝つことが多いデッキです。そのためサガツマツ、アンテマリアをガメて序盤を弱くするくらいならどんどん捨てています」; 「盗人は極力温存」 — 「盗人は再度ハンドに返ってきて、余った1ppで走れる」.
- 採用: ファイアリザード(ナイトメア対策「盗人の返しとして優秀」), 顎門の別れ(ピン), キャリーワイバーン(「先攻はワイバーン通せないとかなりきつい」), 天刀授与(必須), サガツマツ/アンテマリア 3投. 不採用: 大遊戯世界(「そんな暇はない。顔を殴りましょう」), **クラゲの舞姫 (2/1スタッツが環境で隙を見せる)**, 波揺花 (ナイトメア相性), PPブースト札.
- 対面 (verdicts verified x2 except Ramp): ミッドメア 不利「序盤が強くバットが強すぎるためめっちゃきつい」; スペル/実験体ウィッチ 有利より「まともな回復がないためゴリ押しできる」; エルフ 有利「1番のカモ」; 旗ロイヤル 5分; 連携ロイヤル 不明; アミュ・進化ビショップ 微有利; **ランプドラ: verdict inconsistent between fetches (有利目 / 有利), quote 「ノマグダラが重たすぎて負けます。ただ…アグロ仕切れると思ってます」 — UNVERIFIED**.
- Note: coolyu's list (ファイアリザード, キャリーワイバーン, アルフィード) differs from Game8's; no hash found in the note.

### 3.5 Antemaria (F-AM, 1 fetch)
評価 S級; 【ファンファーレ】直前の自分のターンに自分のフォロワーがリーダーを攻撃していたなら、これは「疾走を持つ」; 突進; (decode: 6/5, Rush, ignores Ward). Full JP evolve/super-evolve text not obtained.

---

## 4. Card-effect note
deck.py printed no "(no script)" cards for any of the 7 decoded lists. Lumiore & Argente's "Accelerate (3): see LumioreAccelerate" resolves in /home/claude/sv/svsim/cards/dragon.py:203 to **"Accelerate (3): gain 1 max play point."** (matches GameWith 「リュミオール&アルジャンテ（アクセラレート）などのランプカード」).

---

## Appendix: deck.py decodes (verbatim output)

#### D1. Game8 Ramp Dragon (最終更新 2026.10.06 05:28)
```
hash=1.4.cJl6.cJl6.cJl6.dhqm.dhqm.dhqm.drrO.drrO.drrO.e4IE.e4IE.eDpc.eDpc.eE3E.eE3E.eE3E.eEFk.eEFk.eEFk.ecgE.ecgE.ecgE.ecgO.ecgO.ecgO.e-Ls.e-Ls.e-Ls.e-ec.e_4k.e_4k.e_4k.fN08.fN08.fNVO.fNVO.fNVO.flvu.flvu.flvu
format 1 class 4
3x [2] 掌握天空命运的少女·露莉亚 / Lyria, Skydestined (1/1; Barrier; set 10004) :: Enhance (8): draw a follower that costs 7 or more, then recover 7 play points. Barrier.
3x [2] 懒惰的波摇花 / Sloth of the Crestpetal (spell; ; set 10005) :: Twice: deal 2 damage to a random enemy follower. If you're in Overflow, deal 2 damage to the enemy leader.
3x [2] 古旧天刀·波菈莱 / Vorlalai, Eld Blades (0/2; Bane; set 10006) :: When discarded, summon a Vorlalai. Bane. Evolve: add a Depths of the Eld Blades to your hand. Super-Evolve: add 3 instead.
     -> 古旧天刀·波菈莱 / Vorlalai, Eld Blades :: When discarded, summon a Vorlalai. Bane. Evolve: add a Depths of the Eld Blades to your hand. Super-Evolve: add 3 instead.
     -> 天刀深渊 / Depths of the Eld Blades :: Deal 1 damage to the enemy leader and restore 1 defense to your leader. Does the same when discarded.
3x [2] 宣扬的龙人 / Dragonewt Promoter (2/1; Rush; set 10007) :: Enhance (4): summon 2 Dragonewt Promoters. Rush.
     -> 宣扬的龙人 / Dragonewt Promoter :: Enhance (4): summon 2 Dragonewt Promoters. Rush.
2x [2] 满面笑容的烹饪·琪米卡 / Kimika, Cook of Happiness (2/1; ; set 10008) :: Fanfare: select a card in your hand and discard it; draw a card; restore 1 defense to your leader. Evolve: replicate the Fanfare.
3x [3] 龙之启示 / Dragonsign (spell; ; set 10000) :: Gain 1 max play point. Then, if you have 10 max play points, draw a card.
1x [3] 焦龙的午睡 / Lazing Flame (spell; ; set 10007) :: Restore 3 defense to your leader. If you're in Overflow, draw a card.
2x [4] 日珥咆哮 / Roar of Prominence (spell; ; set 10005) :: Deal X damage to all followers, X = the number of followers on the field.
3x [5] 世界的伙伴·佐伊 / Zooey, Ally of the World (5/5; ; set 10004) :: Fanfare: gain 1 max play point. Enhance (10): give this follower Storm, set your leader's max defense to 1, and give your leader "Can't take more than 0 damage at a time" until the end of your opponent's turn.
2x [5] 《世界》的呈现 / Fate of the World (spell; ; set 10005) :: Draw 2 cards. Destroy a random enemy follower with the highest attack. Enhance (10): also deal 4 damage to all enemies.
3x [7] 断头的斩姬·相枛津 / Sagatsumatsu, Fair Beheader (5/4; Storm,Bane,Aura; set 10006) :: Fanfare: select a card in your hand and discard it; add 2 Spilling Red to your hand. Storm, Bane, Aura.
     -> 赤流 / Spilling Red :: Select a card in your hand and discard it. Select an enemy follower and destroy it. (Needs both targets: official Q&A.)
3x [7] 禁牙的变貌·诺玛格达拉 / Normagdala, Ravening Revenant (5/6; Ward; set 10009) :: Fanfare: Mode: 1. Draw a card and restore 3 defense to your leader. 2. Give all enemy followers -0/-4. Ward. Evolve: replicate the Fanfare (choose again).
3x [8] 金银绚烂·璐米欧儿&雅尔贞特 / Lumiore & Argente, Shining Wings (6/6; ; set 10008) :: Fanfare: select 2 cards in your hand and discard them; deal 4 damage to all enemies. Super-Evolve: draw 3 cards. Accelerate (3): see LumioreAccelerate.
3x [9] 焦灰的安纳提玛·班德奈特 / Burnite, Anathema of Ash (9/9; ; set 10007) :: Fanfare: deal 9 damage to all enemy followers. Super-Evolve: give your opponent Crest: Burnite, Anathema of Ash.
3x [10] 约束的《正义》·伊兰翠 / Erntz, Governing Justice (8/8; Ward; set 10005) :: Ward. At the end of your turn: if unevolved, deal 8 damage to 2 random enemy followers and restore 8 defense to your leader; if evolved, deal 8 damage to the enemy leader. Evolve: remove Ward, gain Intimidate.
total 40
```

#### D2. beyond-dexel Ramp Dragon - 味噌日 CR瞬間1位 (公開 2026.09.17 / 更新 2026.09.18)
```
hash=1.4.cJl6.cJl6.cJl6.dhqm.dhqm.dhqm.drrE.drrE.drrO.drrO.drrO.eDpc.eE3E.eE3E.eE3E.eEFk.eEFk.eEFk.ecgE.ecgE.ecgE.ecgO.ecgO.ecgO.e-Ls.e-Ls.e-Ls.e_4k.e_4k.e_4k.fN08.fN08.fNIk.fNIk.fNVO.fNVO.fNVO.flvu.flvu.flvu
format 1 class 4
2x [1] 狐火蜃景 / Ephemeral Foxfire (spell; ; set 10008) :: Select an enemy follower or the enemy leader and deal it 1 damage. Put an Ephemeral Foxfire into your deck. If you're in Overflow, draw a card.
     -> 狐火蜃景 / Ephemeral Foxfire :: Select an enemy follower or the enemy leader and deal it 1 damage. Put an Ephemeral Foxfire into your deck. If you're in Overflow, draw a card.
3x [2] 掌握天空命运的少女·露莉亚 / Lyria, Skydestined (1/1; Barrier; set 10004) :: Enhance (8): draw a follower that costs 7 or more, then recover 7 play points. Barrier.
3x [2] 懒惰的波摇花 / Sloth of the Crestpetal (spell; ; set 10005) :: Twice: deal 2 damage to a random enemy follower. If you're in Overflow, deal 2 damage to the enemy leader.
3x [2] 古旧天刀·波菈莱 / Vorlalai, Eld Blades (0/2; Bane; set 10006) :: When discarded, summon a Vorlalai. Bane. Evolve: add a Depths of the Eld Blades to your hand. Super-Evolve: add 3 instead.
     -> 古旧天刀·波菈莱 / Vorlalai, Eld Blades :: When discarded, summon a Vorlalai. Bane. Evolve: add a Depths of the Eld Blades to your hand. Super-Evolve: add 3 instead.
     -> 天刀深渊 / Depths of the Eld Blades :: Deal 1 damage to the enemy leader and restore 1 defense to your leader. Does the same when discarded.
3x [2] 宣扬的龙人 / Dragonewt Promoter (2/1; Rush; set 10007) :: Enhance (4): summon 2 Dragonewt Promoters. Rush.
     -> 宣扬的龙人 / Dragonewt Promoter :: Enhance (4): summon 2 Dragonewt Promoters. Rush.
2x [2] 满面笑容的烹饪·琪米卡 / Kimika, Cook of Happiness (2/1; ; set 10008) :: Fanfare: select a card in your hand and discard it; draw a card; restore 1 defense to your leader. Evolve: replicate the Fanfare.
3x [3] 龙之启示 / Dragonsign (spell; ; set 10000) :: Gain 1 max play point. Then, if you have 10 max play points, draw a card.
1x [4] 日珥咆哮 / Roar of Prominence (spell; ; set 10005) :: Deal X damage to all followers, X = the number of followers on the field.
3x [5] 世界的伙伴·佐伊 / Zooey, Ally of the World (5/5; ; set 10004) :: Fanfare: gain 1 max play point. Enhance (10): give this follower Storm, set your leader's max defense to 1, and give your leader "Can't take more than 0 damage at a time" until the end of your opponent's turn.
2x [7] 炎之法则·威尔纳斯 / Wilnas, Flame Personified (8/6; Intimidate; set 10004) :: Fanfare: select an enemy follower and deal it 8 damage. Intimidate. Evolve: replicate the Fanfare.
3x [7] 断头的斩姬·相枛津 / Sagatsumatsu, Fair Beheader (5/4; Storm,Bane,Aura; set 10006) :: Fanfare: select a card in your hand and discard it; add 2 Spilling Red to your hand. Storm, Bane, Aura.
     -> 赤流 / Spilling Red :: Select a card in your hand and discard it. Select an enemy follower and destroy it. (Needs both targets: official Q&A.)
3x [7] 禁牙的变貌·诺玛格达拉 / Normagdala, Ravening Revenant (5/6; Ward; set 10009) :: Fanfare: Mode: 1. Draw a card and restore 3 defense to your leader. 2. Give all enemy followers -0/-4. Ward. Evolve: replicate the Fanfare (choose again).
3x [8] 金银绚烂·璐米欧儿&雅尔贞特 / Lumiore & Argente, Shining Wings (6/6; ; set 10008) :: Fanfare: select 2 cards in your hand and discard them; deal 4 damage to all enemies. Super-Evolve: draw 3 cards. Accelerate (3): see LumioreAccelerate.
3x [9] 焦灰的安纳提玛·班德奈特 / Burnite, Anathema of Ash (9/9; ; set 10007) :: Fanfare: deal 9 damage to all enemy followers. Super-Evolve: give your opponent Crest: Burnite, Anathema of Ash.
3x [10] 约束的《正义》·伊兰翠 / Erntz, Governing Justice (8/8; Ward; set 10005) :: Ward. At the end of your turn: if unevolved, deal 8 damage to 2 random enemy followers and restore 8 defense to your leader; if evolved, deal 8 damage to the enemy leader. Evolve: remove Ward, gain Intimidate.
total 40
```

#### E1. Game8 Combo Elf (最終更新 2026.09.30 12:35)
```
hash=1.1.dhqc.e4Gg.e4Gg.e4Gg.e6FE.e6kU.e6x8.e6x8.e6x8.eVLe.eVLe.et1G.et4E.etl-.etl-.etl-.etm8.etm8.etm8.fGAU.fGAU.fGAU.fds6.fds6.fds6.fe5k.fe5k.fe5k.fe8s.fe8s.fe8s.feLM.feLM.feLM.fea-.fea-.fea-.feb8.feb8.feb8
format 1 class 1
3x [1] 大游戏世界 / World of Games (countdown_amulet; ; set 10005) :: Countdown (5). Whenever you play another card, if there's a card on the field other than it with the same base cost, advance this amulet's count by 1. Last Words: draw 2 cards.
2x [1] 古旧天枪·萨莎妮德 / Sathanid, Eld Lance (1/1; Drain; set 10006) :: Fanfare: spend 10 faith to add a Depths of the Eld Lance and give the faith an evolve ping. Drain.
     -> 天枪深渊 / Depths of the Eld Lance :: Select an unevolved allied follower on the field and evolve it.
1x [1] 精灵陷阱师 / Elven Trapper (1/1; ; set 10007) :: Fanfare: return a card in your hand to your deck; add 2 Fairies to your hand.
1x [1] 人格切换 / Cognitive Shift (spell; ; set 10007) :: Return 2 cards in your hand to your deck. Draw 2 cards.
3x [1] 发芽组员 / Sprouting Initiate (1/1; Rush; set 10009) :: Fanfare: Combo (3) - draw a card. Rush.
1x [2] 虫风花的飞翔 / Flight of the Swarmpetal (spell; ; set 10005) :: Deal 3 damage split between all enemy followers. Add a Fairy to your hand.
3x [2] 根延潜伏者 / Leafshadow Assassin (2/2; ; set 10009) :: Fanfare: add a Fairy to your hand. Combo (3) - give it Bane.
3x [2] 绿伞会两大招牌 / Verdant Ring Kindred (spell; ; set 10009) :: Mode: 1. 4 damage to a random enemy follower; 2. add a Deepwood Bounty and a Fairy. Combo (3): both.
     -> 森林的奥秘 / Deepwood Bounty :: Restore 1 defense to your leader.
3x [2] 枝叶大姐大 / Virid Lieutenant (1/3; ; set 10009) :: Fanfare: Combo (3) - draw 2 cards. Evolve: give another allied follower +1/+1 and Rush.
1x [3] 优雅的虫风花 / Grace of the Swarmpetal (spell; ; set 10005) :: Draw X cards, X = your Combo.
3x [3] 虫风花·魅禄 / Miroku, Swarmpetal (2/2; ; set 10005) :: Fanfare and Evolve: Mode - add 2 Fairies / recover 2 PP / 3 damage split between enemy followers.
3x [3] 烟管的罪人·曲千代 / Magachiyo, Aromatic Convict (2/2; ; set 10009) :: Fanfare: 4 damage to an enemy follower (Combo (3): to all enemy followers). Super-Evolve: Storm.
1x [4] 征服苍空的骑空士·古兰&姬塔 / Gran & Djeeta, Valiant Skyfarers (3/2; ; set 10004) :: Fanfare: Mode: 1. Deal 5 damage to a random enemy follower. 2. Draw 2 followers. Skybound Art - evolve this follower.
3x [4] 操量的安纳提玛·达斯特迪兹 / Thestae, Anathema of Distortion (3/3; ; set 10007) :: Fanfare: an enemy follower gets -0/-X (X = this attack); Combo +1. Evolve: gain Crest: Thestae.
3x [6] 冰界鹿王 / Great Hart of the Glacial Realm (5/5; ; set 10007) :: Fanfare: add 2 Deepwood Bounty. Turn end: split X (its attack) damage. Super-Evolve: gain its crest.
     -> 森林的奥秘 / Deepwood Bounty :: Restore 1 defense to your leader.
3x [7] 离合有终·赛德斯&梅希亚 / Setus & Maisha, Bladerights (4/6; Ward,Storm; set 10008) :: Fanfare: destroy an enemy follower; give all other allied followers +1/+1. Storm, Ward.
3x [9] 香风的变貌·飞燕 / Hien, Redolent Revenant (4/4; ; set 10009) :: In hand: cost -1 this turn per card you play. Fanfare: 4 damage to an enemy. Last Words: summon one.
     -> 香风的变貌·飞燕 / Hien, Redolent Revenant :: In hand: cost -1 this turn per card you play. Fanfare: 4 damage to an enemy. Last Words: summon one.
total 40
```

#### E2. beyond-dexel Dustdays Elf - Spicies CR最終2位 (公開 2026.09.29)
```
hash=1.1.e4Gg.e4Gg.e4Gg.eVLe.eVLe.eVLe.fFRw.fFRw.fFRw.fds6.fds6.fds6.dhqm.dkWU.etGk.etGk.etGk.fe5k.fe5k.fe5k.feLM.feLM.feLM.e6x8.e6x8.e6x8.fea-.fea-.fea-.e6kU.etl-.etl-.etl-.feOU.feOU.etm8.etm8.fGAU.fGAU.fGAU
format 1 class 1
3x [1] 大游戏世界 / World of Games (countdown_amulet; ; set 10005) :: Countdown (5). Whenever you play another card, if there's a card on the field other than it with the same base cost, advance this amulet's count by 1. Last Words: draw 2 cards.
3x [1] 古旧天枪·萨莎妮德 / Sathanid, Eld Lance (1/1; Drain; set 10006) :: Fanfare: spend 10 faith to add a Depths of the Eld Lance and give the faith an evolve ping. Drain.
     -> 天枪深渊 / Depths of the Eld Lance :: Select an unevolved allied follower on the field and evolve it.
3x [1] 忧郁少女·莫埃尔 / Moelle, Gloomy Maiden (1/1; Ward; set 10008) :: Fanfare: return a card in your hand to your deck; draw a card. Ward.
3x [1] 发芽组员 / Sprouting Initiate (1/1; Rush; set 10009) :: Fanfare: Combo (3) - draw a card. Rush.
1x [2] 掌握天空命运的少女·露莉亚 / Lyria, Skydestined (1/1; Barrier; set 10004) :: Enhance (8): draw a follower that costs 7 or more, then recover 7 play points. Barrier.
1x [2] 风之法则·艾云尼亚 / Ewiyar, Wind Personified (2/1; Rush; set 10004) :: Fanfare: Skybound Art - recover 1 evolution point. Rush.
3x [2] 绿风细剑师 / Virewind Fencer (2/2; ; set 10007) :: Fanfare: Combo (3) - give this follower Storm.
3x [2] 根延潜伏者 / Leafshadow Assassin (2/2; ; set 10009) :: Fanfare: add a Fairy to your hand. Combo (3) - give it Bane.
3x [2] 枝叶大姐大 / Virid Lieutenant (1/3; ; set 10009) :: Fanfare: Combo (3) - draw 2 cards. Evolve: give another allied follower +1/+1 and Rush.
1x [3] 优雅的虫风花 / Grace of the Swarmpetal (spell; ; set 10005) :: Draw X cards, X = your Combo.
3x [3] 虫风花·魅禄 / Miroku, Swarmpetal (2/2; ; set 10005) :: Fanfare and Evolve: Mode - add 2 Fairies / recover 2 PP / 3 damage split between enemy followers.
3x [3] 烟管的罪人·曲千代 / Magachiyo, Aromatic Convict (2/2; ; set 10009) :: Fanfare: 4 damage to an enemy follower (Combo (3): to all enemy followers). Super-Evolve: Storm.
3x [4] 操量的安纳提玛·达斯特迪兹 / Thestae, Anathema of Distortion (3/3; ; set 10007) :: Fanfare: an enemy follower gets -0/-X (X = this attack); Combo +1. Evolve: gain Crest: Thestae.
2x [4] 绯岸橙醉 / Crimson Incense (spell; ; set 10009) :: In hand: at the end of your turn, Combo (3) - cost -1. Destroy an enemy follower; draw a card.
2x [6] 冰界鹿王 / Great Hart of the Glacial Realm (5/5; ; set 10007) :: Fanfare: add 2 Deepwood Bounty. Turn end: split X (its attack) damage. Super-Evolve: gain its crest.
     -> 森林的奥秘 / Deepwood Bounty :: Restore 1 defense to your leader.
3x [7] 离合有终·赛德斯&梅希亚 / Setus & Maisha, Bladerights (4/6; Ward,Storm; set 10008) :: Fanfare: destroy an enemy follower; give all other allied followers +1/+1. Storm, Ward.
total 40
```

#### E3. beyond-dexel Dustdays Elf - NARU Dexel StarSeed Cup優勝 (公開/更新 2026.09.07)
```
hash=1.1.e4Gg.e4Gg.e4Gg.e6FE.e6FE.e6kU.e6kU.e6x8.e6x8.e6x8.et1G.et1G.et1G.etGk.etGk.etl-.etl-.etl-.etm8.etm8.etm8.fGAU.fGAU.fGAU.fds6.fds6.fds6.fe5k.fe5k.fe8s.fe8s.fe8s.feLM.feLM.feLM.fea-.fea-.fea-.feb8.feb8
format 1 class 1
3x [1] 大游戏世界 / World of Games (countdown_amulet; ; set 10005) :: Countdown (5). Whenever you play another card, if there's a card on the field other than it with the same base cost, advance this amulet's count by 1. Last Words: draw 2 cards.
3x [1] 精灵陷阱师 / Elven Trapper (1/1; ; set 10007) :: Fanfare: return a card in your hand to your deck; add 2 Fairies to your hand.
3x [1] 发芽组员 / Sprouting Initiate (1/1; Rush; set 10009) :: Fanfare: Combo (3) - draw a card. Rush.
2x [2] 虫风花的飞翔 / Flight of the Swarmpetal (spell; ; set 10005) :: Deal 3 damage split between all enemy followers. Add a Fairy to your hand.
2x [2] 绿风细剑师 / Virewind Fencer (2/2; ; set 10007) :: Fanfare: Combo (3) - give this follower Storm.
2x [2] 根延潜伏者 / Leafshadow Assassin (2/2; ; set 10009) :: Fanfare: add a Fairy to your hand. Combo (3) - give it Bane.
3x [2] 绿伞会两大招牌 / Verdant Ring Kindred (spell; ; set 10009) :: Mode: 1. 4 damage to a random enemy follower; 2. add a Deepwood Bounty and a Fairy. Combo (3): both.
     -> 森林的奥秘 / Deepwood Bounty :: Restore 1 defense to your leader.
3x [2] 枝叶大姐大 / Virid Lieutenant (1/3; ; set 10009) :: Fanfare: Combo (3) - draw 2 cards. Evolve: give another allied follower +1/+1 and Rush.
2x [3] 优雅的虫风花 / Grace of the Swarmpetal (spell; ; set 10005) :: Draw X cards, X = your Combo.
3x [3] 虫风花·魅禄 / Miroku, Swarmpetal (2/2; ; set 10005) :: Fanfare and Evolve: Mode - add 2 Fairies / recover 2 PP / 3 damage split between enemy followers.
3x [3] 烟管的罪人·曲千代 / Magachiyo, Aromatic Convict (2/2; ; set 10009) :: Fanfare: 4 damage to an enemy follower (Combo (3): to all enemy followers). Super-Evolve: Storm.
3x [4] 操量的安纳提玛·达斯特迪兹 / Thestae, Anathema of Distortion (3/3; ; set 10007) :: Fanfare: an enemy follower gets -0/-X (X = this attack); Combo +1. Evolve: gain Crest: Thestae.
3x [6] 冰界鹿王 / Great Hart of the Glacial Realm (5/5; ; set 10007) :: Fanfare: add 2 Deepwood Bounty. Turn end: split X (its attack) damage. Super-Evolve: gain its crest.
     -> 森林的奥秘 / Deepwood Bounty :: Restore 1 defense to your leader.
3x [7] 离合有终·赛德斯&梅希亚 / Setus & Maisha, Bladerights (4/6; Ward,Storm; set 10008) :: Fanfare: destroy an enemy follower; give all other allied followers +1/+1. Storm, Ward.
2x [9] 香风的变貌·飞燕 / Hien, Redolent Revenant (4/4; ; set 10009) :: In hand: cost -1 this turn per card you play. Fanfare: 4 damage to an enemy. Last Words: summon one.
     -> 香风的变貌·飞燕 / Hien, Redolent Revenant :: In hand: cost -1 this turn per card you play. Fanfare: 4 damage to an enemy. Last Words: summon one.
total 40
```

#### E4. beyond-dexel Dustdays Elf - hqzuki BEYOND到達 (公開 2026.09.01 / 更新 2026.09.02)
```
hash=1.1.e4Gg.e4Gg.e4Gg.eVLe.et1G.fFRw.fFRw.fFRw.fds6.fds6.fds6.dhqm.dhqm.etGk.etGk.etGk.fe5k.fe5k.fe5k.feLM.feLM.feLM.e6x8.e6x8.e6x8.fea-.fea-.fea-.e6kU.etl-.etl-.etl-.feOU.feOU.etm8.etm8.etm8.fGAU.fGAU.fGAU
format 1 class 1
3x [1] 大游戏世界 / World of Games (countdown_amulet; ; set 10005) :: Countdown (5). Whenever you play another card, if there's a card on the field other than it with the same base cost, advance this amulet's count by 1. Last Words: draw 2 cards.
1x [1] 古旧天枪·萨莎妮德 / Sathanid, Eld Lance (1/1; Drain; set 10006) :: Fanfare: spend 10 faith to add a Depths of the Eld Lance and give the faith an evolve ping. Drain.
     -> 天枪深渊 / Depths of the Eld Lance :: Select an unevolved allied follower on the field and evolve it.
1x [1] 精灵陷阱师 / Elven Trapper (1/1; ; set 10007) :: Fanfare: return a card in your hand to your deck; add 2 Fairies to your hand.
3x [1] 忧郁少女·莫埃尔 / Moelle, Gloomy Maiden (1/1; Ward; set 10008) :: Fanfare: return a card in your hand to your deck; draw a card. Ward.
3x [1] 发芽组员 / Sprouting Initiate (1/1; Rush; set 10009) :: Fanfare: Combo (3) - draw a card. Rush.
2x [2] 掌握天空命运的少女·露莉亚 / Lyria, Skydestined (1/1; Barrier; set 10004) :: Enhance (8): draw a follower that costs 7 or more, then recover 7 play points. Barrier.
3x [2] 绿风细剑师 / Virewind Fencer (2/2; ; set 10007) :: Fanfare: Combo (3) - give this follower Storm.
3x [2] 根延潜伏者 / Leafshadow Assassin (2/2; ; set 10009) :: Fanfare: add a Fairy to your hand. Combo (3) - give it Bane.
3x [2] 枝叶大姐大 / Virid Lieutenant (1/3; ; set 10009) :: Fanfare: Combo (3) - draw 2 cards. Evolve: give another allied follower +1/+1 and Rush.
1x [3] 优雅的虫风花 / Grace of the Swarmpetal (spell; ; set 10005) :: Draw X cards, X = your Combo.
3x [3] 虫风花·魅禄 / Miroku, Swarmpetal (2/2; ; set 10005) :: Fanfare and Evolve: Mode - add 2 Fairies / recover 2 PP / 3 damage split between enemy followers.
3x [3] 烟管的罪人·曲千代 / Magachiyo, Aromatic Convict (2/2; ; set 10009) :: Fanfare: 4 damage to an enemy follower (Combo (3): to all enemy followers). Super-Evolve: Storm.
3x [4] 操量的安纳提玛·达斯特迪兹 / Thestae, Anathema of Distortion (3/3; ; set 10007) :: Fanfare: an enemy follower gets -0/-X (X = this attack); Combo +1. Evolve: gain Crest: Thestae.
2x [4] 绯岸橙醉 / Crimson Incense (spell; ; set 10009) :: In hand: at the end of your turn, Combo (3) - cost -1. Destroy an enemy follower; draw a card.
3x [6] 冰界鹿王 / Great Hart of the Glacial Realm (5/5; ; set 10007) :: Fanfare: add 2 Deepwood Bounty. Turn end: split X (its attack) damage. Super-Evolve: gain its crest.
     -> 森林的奥秘 / Deepwood Bounty :: Restore 1 defense to your leader.
3x [7] 离合有终·赛德斯&梅希亚 / Setus & Maisha, Bladerights (4/6; Ward,Storm; set 10008) :: Fanfare: destroy an enemy follower; give all other allied followers +1/+1. Storm, Ward.
total 40
```

#### F1. Game8 Face Dragon (最終更新 2026.09.30 12:34)
```
hash=1.4.eDme.eDme.eDme.eE3E.eE3E.eE3E.eb-U.eb-U.ecTk.ecTk.ecgE.ecgE.ecgE.ecgO.ecgO.ecgO.fN08.fN08.fN08.flAs.flAs.flAs.flD-.flD-.flD-.flQU.flQU.flQU.flTc.flTc.flTc.flg6.flg6.flg6.fljE.fljE.fljE.flvk.flvk.flvk
format 1 class 4
3x [1] 碎裂的盗匪 / Ripper-Clawed Thief (1/1; ; set 10009) :: Fanfare: if an allied follower attacked a leader on your last turn, gain Storm. Last Words: add a Ripper-Clawed Thief to your hand and remove its Last Words.
     -> 碎裂的盗匪 / Ripper-Clawed Thief :: Fanfare: if an allied follower attacked a leader on your last turn, gain Storm. Last Words: add a Ripper-Clawed Thief to your hand and remove its Last Words.
3x [1] 幼龙闹脾气 / Drake Whelp's Tantrum (spell; ; set 10009) :: Summon a Fire Drake Whelp. Enhance (3): also deal 3 damage to a random enemy follower.
3x [2] 水母舞姬 / Jellyfish Dancer (2/1; ; set 10005) :: Fanfare: add a Majestic Megalorca to your hand. Whenever an allied Marine follower enters the field, give this follower Rush and Bane.
3x [2] 懒惰的波摇花 / Sloth of the Crestpetal (spell; ; set 10005) :: Twice: deal 2 damage to a random enemy follower. If you're in Overflow, deal 2 damage to the enemy leader.
3x [2] 古旧天刀·波菈莱 / Vorlalai, Eld Blades (0/2; Bane; set 10006) :: When discarded, summon a Vorlalai. Bane. Evolve: add a Depths of the Eld Blades to your hand. Super-Evolve: add 3 instead.
     -> 古旧天刀·波菈莱 / Vorlalai, Eld Blades :: When discarded, summon a Vorlalai. Bane. Evolve: add a Depths of the Eld Blades to your hand. Super-Evolve: add 3 instead.
     -> 天刀深渊 / Depths of the Eld Blades :: Deal 1 damage to the enemy leader and restore 1 defense to your leader. Does the same when discarded.
3x [2] 满面笑容的烹饪·琪米卡 / Kimika, Cook of Happiness (2/1; ; set 10008) :: Fanfare: select a card in your hand and discard it; draw a card; restore 1 defense to your leader. Evolve: replicate the Fanfare.
3x [2] 绝倒的袭击者 / High-Spirited Marauder (1/2; Storm; set 10009) :: Storm. Strike: if an allied follower attacked a leader on your last turn, gain +1/+0 until the end of the turn.
3x [2] 利牙 / Artiglio (spell; ; set 10009) :: Deal 3 damage split between all enemy followers, 6 if an allied follower attacked a leader on your last turn.
3x [3] 颚口之别 / Parting Jaws (spell; ; set 10009) :: Select 2 cards in your hand and discard them. Deal 3 damage to a random enemy follower and the enemy leader.
2x [4] 天刀授予 / Advent of the Eld Blades (spell; ; set 10006) :: Select an allied follower and give it +2/+2. When discarded, if its cost is 4, add an Advent of the Eld Blades to your hand and set its cost to 2.
     -> 天刀授予 / Advent of the Eld Blades :: Select an allied follower and give it +2/+2. When discarded, if its cost is 4, add an Advent of the Eld Blades to your hand and set its cost to 2.
3x [5] 尘土的不法者 / Barren-Earth Tyrant (4/4; ; set 10009) :: Fanfare: deal 4 damage to a random enemy follower, twice if an allied follower attacked a leader on your last turn. Evolve: summon a High-Spirited Marauder.
     -> 绝倒的袭击者 / High-Spirited Marauder :: Storm. Strike: if an allied follower attacked a leader on your last turn, gain +1/+0 until the end of the turn.
2x [7] 断头的天刀 / Beheading Eld Blades (spell; ; set 10006) :: Deal X damage to all enemy followers, X = this card's cost. When discarded, if its cost is 7, add a Beheading Eld Blades costing 5 to your hand; if 5, one costing 3.
     -> 断头的天刀 / Beheading Eld Blades :: Deal X damage to all enemy followers, X = this card's cost. When discarded, if its cost is 7, add a Beheading Eld Blades costing 5 to your hand; if 5, one costing 3.
3x [7] 断头的斩姬·相枛津 / Sagatsumatsu, Fair Beheader (5/4; Storm,Bane,Aura; set 10006) :: Fanfare: select a card in your hand and discard it; add 2 Spilling Red to your hand. Storm, Bane, Aura.
     -> 赤流 / Spilling Red :: Select a card in your hand and discard it. Select an enemy follower and destroy it. (Needs both targets: official Q&A.)
3x [7] 穿孔的罪人·安缇马丽亚 / Antemaria, Piercing Convict (6/5; Rush; set 10009) :: Fanfare: if an allied follower attacked a leader on your last turn, gain Storm. Rush. Ignores Ward.
total 40
```

