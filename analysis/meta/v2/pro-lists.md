# Pro-league and tournament decklists for pack 9 (アズヴォルト・レヴナント), compared with ladder guides, plus how credible each guide author is
Compiled 2026-10-07.

**Tags**
- [V2]: two independent fetches agree, or two sources agree.
- [V1]: one fetch only.
- [UNVERIFIED]: not confirmed.
- [INF]: my own inference.

All card names below come from the local DB decode (`deck.py` / `ps/cmp.py`), not from the summarizer. Every decklist hash was fetched twice and compared character by character (see §1).

---
## 0. Key findings
1. **The Premier Series official API is readable, and it has the full pro decklists with deck hashes.** The endpoint is `https://wb-ps.g.kuroco.app/rcms-api/1/news/detail/<id>`. The site's own pages are a JS shell, so WebFetch only sees blank pages there.
   - Each matchday, every team submits **7 decks, one per class**.
   - For an online matchday the lists lock at **17:00 the day before**.
   - So 第8節後半 (match 10/7, lists published 10/6) is the **first post-patch pro data**: 28 decks.
   - 第8節前半 (match 9/23, lists 9/22) is the last pre-patch set: 28 decks.
   - Both hash sets match exactly across two fetches [V2].
2. **What pros switched to after the 9/29 patch:** compare 8前半 (pre-patch) with 8後半 (post-patch), 4 teams each, all 7 classes.
   - Royal: 4/4 連携 → **4/4 海賊旗**.
   - Nemesis: 4/4 AF (3-copy) → **4/4 カットスロート (highlander)**.
   - Witch: 4/4 魔手 → **0 魔手**; replaced by 2 実験体/セフィー and 2 リンクル (spell) ウィッチ.
   - Nightmare: 4/4 Midrange → 3 Midrange + 1 Aggro (まっつ).
   - Elf, Dragon and Bishop: unchanged. Every list is DDE, Ramp and Kandima-control Amulet respectively.
   - shadowverse-vision.com's distribution for 第8節 says the same: 魔手4 / スペル2 / セフィー2, 海賊旗4 / 連携4, カットスロート4 / AF4, ミッドレンジ7 / アグロ1 [V2].
3. **Several Game8 lists are outliers that no tournament player runs.** The tournament set here is 19 Elf, 16 Dragon and 13 Bishop lists across PS 7後半, 8前半, 8後半 and JCS S3 Playoff/GF.
   - **Elf:** Game8 (and NARU) run 香風の変貌・ヒエン ×2–3, 緑傘会の二枚看板 ×3 and 精霊の罠師. **0 of 19** PS/JCS Elf lists run Hien. All 19 are the Moelle ×3 / 緑風細剑 ×3 / Sathanid build, which is Spicies' build.
   - **Bishop:** Game8's Azvaldt Storm build (ミラクルアルミラージ ×3, 英雄幻視トルー ×3, 大遊戯世界 ×3, アズヴォルト ×2) appears in **0 of 13** pro/JCS Bishop lists. Every pro list is the カンディマ ×3 / 崇奉の怯者 ×3 / Tikoh ×3 / 闇の次元 control build, the same family as zhangyue616's dexel list. The only Azvaldt deck in tournament play is siesta's 監獄 build in the JCS Playoff, which has a different shell.
   - **Ramp Dragon:** Game8 (10/06) runs 日珥咆哮 ×2, 《世界》 ×2 and 焦龍の午睡 ×1, with **0 Wilnas and 0 狐火**. Post-patch pros run Wilnas 1–3 (3 of 4 lists), 狐火 1–2 (4 of 4), and **日珥咆哮 in only 1 of 4** lists (1 copy).
   - **Pirate Royal:** all 4 post-patch pro lists run 迷茫的狮子·モードレッド 1–2. テンジン's dexel guide drops Mordred on purpose (「進化権との相性が悪く…不採用」).
4. **ICS Singapore (9/26–27, pre-patch).** Top 8 class pairs [V2]:
   - Chappy (RIDDLE ORDER): Elf/Dragon, champion.
   - Kraken: Elf/Bishop.
   - jiean/深紅蘭: Witch/Dragon.
   - kafsao: Elf/Nightmare.
   - VL|まっつ: Elf/Witch.
   - 奏/REV: Elf/Nemesis.
   - ぴゅあ: Elf/Witch.
   - DragonOracle: Dragon/Nightmare.
   - Elf appears in 6 of 8. No ICS decklists could be read: the official page is a Next.js shell and liquipedia returns 429.
   - jiean/深紅蘭 (3rd) is the author of dexel's 魔手ウィッチ「CR瞬間1位」 guide, so that list is effectively a top-4 ICS player's list.
5. **About the user's question「为什么龙族带日珥咆哮」:**
   - In the pack 8 PS lists (5節後半), every pro ran 日珥咆哮 1–3.
   - Pre-patch pack 9 (7後半): 3 of 4 ran it, 1–2 copies.
   - Post-patch (8後半): only DFM ミル ran it, ×1. The other three cut it to 0.
   - 6-cost 6/9 隔断的龙斗士 / Impeding Pugilist (守护 + 屏障): **0 copies in all 30+ tournament/guide lists**. The [INF] explanation is in §4.1.

---
## 1. Sources and reliability
| Source | What | Reliability |
|---|---|---|
| `https://wb-ps.g.kuroco.app/rcms-api/1/news?contents_type=deck-list&cnt=50` | Index of PS decklist posts. topics: 352 = 8節後半 (published 10/06), 346 = 8節前半 (9/22), 341 = 7節後半 (9/08), 339 = 7節前半 (9/01), 336 = 6節 (8/29), 328 = 5節後半 (8/25, pack 8), … back to 220 = 開幕 | [V1] list |
| `…/rcms-api/1/news/detail/352` and `/346` | Full 7-class lists for 4 teams each, with hashes and image filenames (player = filename) | **[V2]**: two fetches with different prompts, diffed: 28/28 and 28/28 identical. Saved to `scratchpad/ps/s8a_fetch{1,2}.txt` and `s8b_fetch{1,2}.txt` |
| `…/detail/341` (7節後半: MRG, VARREL, REJECT, LVH) and `/328` (5節後半: LVH, DFM, VARREL, ZETA; pack 8) | Same format, but **no player names** (filenames like 07_mrg_ドラゴン.png) | [V1]; every hash decodes to exactly 40 cards. `ps/s7b.txt`, `ps/s5b.txt` |
| ps.shadowverse-wb.com/26-27/about/ and shadowverse-magazine rule page | Format: 3 players, 7 decks with different classes submitted in advance. Online matchdays lock at 前日17:00, offline at 2日前17:00. Battle 1 brings 3 decks, battles 2 and 3 bring 2 each, BO1; battle 4 is a team battle using the remaining 4 decks; battle 5 is a team battle with 3 | [V2] |
| shadowverse-vision.com (unofficial PS stats) | Rosters, schedule, player profiles (peak rating, BEYOND count, PS record, streams). The `/decks` page shows the 第8節 class distribution | Distribution [V2] against the API. **Its per-player table was hallucinated by the summarizer** (a second fetch showed no player names attached), so it is discarded. Profiles [V1] |
| gamer.ne.jp/news/202610010047 | ICS top 8 with classes | [V2]: two fetches, verbatim table |
| beyondmeta.jp/jcs (via sibling research `research2/jcs.txt`, `nemesis.md`) | JCS 2026 S3: prelims 10/3–4 (**post-patch**), GF 10/25. 24 Playoff/GF decks with hashes | [V2] per the sibling. Format confirmed here: Day1 8 rounds and Day2 7 rounds, 2 decks BO1; Playoff BO3; GF BO3 |
| beyond-dexel.com author pages | Labels only ("CR瞬間1位" and so on). **No author bios on the pages** | [V1] |
| svlabo.jp, beyondmeta.jp/premier, ICS official, GameWith | JS-rendered (svlabo, ICS), images only (beyondmeta premier = twimg / kuroco PNG; WebFetch cannot read images), 403 (GameWith) | — |

---
## 2. Premier Series: archetype choice by matchday (each team must field all 7 classes)
Teams (rosters from shadowverse-vision [V1]):
- Crazy Raccoon: Atom, ふぇぐ, ふえた, 空白, Winter.
- ZETA DIVISION: CQCQ, ヘイム, ねぎま, TBT.
- DetonatioN FocusMe: かなで, ミル, MingiGod, ユーリ.
- VARREL: まっつ, Mishadow51, monakawan, Terarina.
- MURASH GAMING: glory, マイト, もっちゃま, Spicies, Toby.
- REJECT: あぐのむ, ぱらちゃん, たばた, 拓海, つきあかめん.
- RIDDLE ORDER: Chappy, 折り紙, ぱんさく, Stylish_deko, 山田レクイエム.
- レバンガ北海道: だーよね, Era53, Hirobosu, rikka, 智念せいら.

| Class | 7節後半 (9/09, pre-patch; MRG/VL/RJ/LVH) | 8節前半 (9/23, pre-patch; RJ/MRG/LVH/RID) | **8節後半 (10/07, post-patch; VL/DFM/ZETA/CR)** |
|---|---|---|---|
| Elf | DDE ×4 | DDE ×4 | DDE ×4 |
| Dragon | Ramp ×4 | Ramp ×4 | Ramp ×4 |
| Royal | 連携 ×4 | 連携 ×4 | **海賊旗 ×4** |
| Witch | 魔手 ×4 | 魔手 ×4 | **実験体/セフィー ×2 (VL monakawan, ZETA ねぎま); リンクル/スペル ×2 (DFM ユーリ, CR ふえた)** |
| Nemesis | AF ×4 | AF ×4 | **カットスロート (highlander) ×4** |
| Nightmare | Midrange ×4 (REJECT's is a variant with ルルミ/フェディエル) | Midrange ×4 | Midrange ×3 + **Aggro ×1 (VL まっつ)** |
| Bishop | Amulet control ×4 | Amulet control ×4 | Amulet control ×4 |

Player per deck in 8節後半, from the image filenames [V2]:
- **VARREL:** まっつ (Elf, Royal, Nightmare), monakawan (Witch, Dragon), Terarina (Bishop, Nemesis).
- **DFM:** ユーリ (Witch, Nightmare, Bishop), ミル (Dragon, Nemesis), かなで (Elf, Royal).
- **ZETA:** ヘイム (Nightmare, Bishop, Nemesis), ねぎま (Witch, Dragon), CQCQ (Elf, Royal).
- **CR:** ふえた (Witch, Bishop, Nemesis), Atom (Royal, Dragon), 空白 (Elf, Nightmare).

Player per deck in 8節前半:
- **REJECT:** あぐのむ (Elf, Nightmare), たばた (Royal, Dragon), 拓海 (Witch, Bishop, Nemesis).
- **MRG:** Spicies (Elf, Royal, Dragon), glory (Witch, Nemesis), Toby (Bishop, Nightmare).
- **LVH:** Era53 (Elf, Royal), rikka (Witch, Bishop), Hirobosu (Dragon, Nemesis, Nightmare).
- **RID:** 折り紙 (Elf, Nemesis), ぱんさく (Royal, Witch, Bishop), Stylish_deko (Dragon, Nightmare).

Caveat [INF]: because every team must bring all 7 classes, "the most-picked archetype within a class" is a stronger signal than class counts.

### 2.1 JCS 2026 Season 3 (prelims 10/3–4, post-patch; ~31 on Day 2)
GF 8, from beyondmeta via the sibling [V2]:
- maya: DDE + Ramp.
- しょーや: DDE + Cutthroat.
- そろばん: DDE + Pirate.
- とび: 実験体 Witch + Amulet Bishop. Whether this is Toby (MRG) is [UNVERIFIED].
- ぱらちゃん (REJECT pro): リンクル/スペル Witch + Amulet Bishop.
- まっつ (VARREL pro; ICS top 8): DDE + Cutthroat.
- リンド: Pirate + Cutthroat.
- 斉キッカー: DDE + Cutthroat.

Playoff players include Atom (CR pro), siesta (実験体 + 監獄 Bishop), TIK (DDE + Ramp), まっすー (Ramp + Cutthroat) and まほ (DDE + Ramp).

Share of the confirmed Playoff/GF decks: DDE 29%, Cutthroat 21%, Ramp 17%.
- **No Midrange Nightmare and no 魔手 Witch** among the confirmed Playoff/GF decks.
- Pirate appears twice.

---
## 3. ICS Singapore 2026 (9/26–27, about 400 players, 2 decks, pre-patch)
- The top 8 is in §0.
- Day-2 top-32 distribution (shufflephase [V1]): Combo/DDE Elf 18 of 64 decks, Ramp 15, Crystal (魔手) Witch 11, Midrange Nightmare 9, other 11.
- Chappy, from the official report [V1]: 「海外の大会結果などを参考に使用デッキの傾向を研究」.
- Final [V2 with onemoregame]: G1 Elf vs Elf (Chappy won); G2 Kraken's aggressive Elf beat Chappy's Dragon; G3 Chappy's Dragon beat Kraken's Bishop.
- No ICS card lists could be read.

---
## 4. Card-by-card: tournament builds vs ladder-guide builds
Column legend:
- G8 = Game8.
- PS7b = 7節後半 (9/09, pre-patch).
- PS8a = 8節前半 (9/23, pre-patch).
- **PS8b = 8節後半 (10/07, post-patch)**.
- JCS = JCS S3 Playoff/GF (10/3–4, post-patch).
- "·" = 0 copies.

Only cards whose count differs between lists are shown. The shared core is listed under each table.

### 4.1 Ramp Dragon
| card | G8(10/06) | 味噌日 dexel 9/17 | PS7b MRG | PS7b VL | PS7b RJ | PS7b LVH | PS8a RJ tabata | PS8a MRG spicies | PS8a LVH hirobosu | PS8a RID deko | PS8b VL monakawan | PS8b DFM mil | PS8b ZETA negima | PS8b CR atom | JCS maya | JCS TIK | JCS massu | JCS maho |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [1] 狐火蜃景 / Ephemeral Foxfire | · | 2 | 2 | 1 | · | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 1 | 2 |
| [2] 掌握天空命运的少女·露莉亚 / Lyria, Skydestined | 3 | 3 | 3 | 3 | 2 | 3 | 2 | 2 | 2 | 2 | 3 | 3 | 3 | 3 | 2 | 3 | 3 | 3 |
| [2] 水母舞姬 / Jellyfish Dancer | · | · | · | · | · | · | · | · | 1 | · | · | · | · | · | · | · | 1 | · |
| [2] 满面笑容的烹饪·琪米卡 / Kimika, Cook of Happiness | 2 | 2 | 2 | · | 2 | 2 | 3 | 3 | 2 | 3 | 2 | 1 | 3 | 2 | 3 | 3 | 2 | 2 |
| [3] 焦龙的午睡 / Lazing Flame | 1 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| [4] 日珥咆哮 / Roar of Prominence | 2 | 1 | 2 | 1 | · | 1 | · | · | · | · | · | 1 | · | · | · | · | · | · |
| [4] 黑暗次元 / Dark Dimensions | · | · | · | 2 | 2 | · | · | · | · | · | · | · | 2 | · | · | · | 1 | · |
| [5] 《世界》的呈现 / Fate of the World | 2 | · | · | 1 | · | 1 | · | · | · | · | 1 | · | · | 1 | · | 1 | 1 | 1 |
| [7] 炎之法则·威尔纳斯 / Wilnas, Flame Personified | · | 2 | · | · | 2 | · | 3 | 3 | 3 | 2 | 2 | 3 | · | 1 | 2 | · | · | 1 |
| [7] 黑炎的奔流 / Blackflame Deluge | · | · | · | · | · | · | · | · | · | 1 | · | · | · | 1 | · | · | · | · |
| [9] 阿尔比昂巴哈姆特 / Alabaster Bahamut | · | · | 1 | 2 | 2 | 1 | · | · | · | · | · | 1 | · | · | 1 | 1 | 1 | 1 |

Shared by all lists (same count): [2] 古旧天刀·波菈莱 / Vorlalai, Eld Blades x3; [2] 宣扬的龙人 / Dragonewt Promoter x3; [2] 懒惰的波摇花 / Sloth of the Crestpetal x3; [3] 龙之启示 / Dragonsign x3; [5] 世界的伙伴·佐伊 / Zooey, Ally of the World x3; [7] 断头的斩姬·相枛津 / Sagatsumatsu, Fair Beheader x3; [7] 禁牙的变貌·诺玛格达拉 / Normagdala, Ravening Revenant x3; [8] 金银绚烂·璐米欧儿&雅尔贞特 / Lumiore & Argente, Shining Wings x3; [9] 焦灰的安纳提玛·班德奈特 / Burnite, Anathema of Ash x3; [10] 约束的《正义》·伊兰翠 / Erntz, Governing Justice x3

**Reading the table** [counts are V2; reasons are INF unless quoted]:
- **Game8's list is the outlier.** It runs 日珥咆哮 ×2, 《世界》の顕現 ×2 and 焦龍の午睡 ×1. It runs **no Wilnas** (炎之法则·威尔纳斯 / 炎の理・ウィルナス) and **no 狐火蜃景**.
  - In the post-patch tournament lists (PS8b + JCS, 8 lists): Wilnas appears in 5 of 8 (1–3 copies); 狐火 in 8 of 8 (1–2); 日珥咆哮 in 1 of 8 (DFM ミル ×1); アルビオンバハムート in 5 of 8 (×1); 闇の次元 in 2 of 8.
  - 味噌日 (dexel, 9/17) sits between the two: Wilnas 2, 日珥 1, 狐火 2.
- **Why 日珥咆哮 was played, and why it is leaving.**
  - Card text (DB): 「Deal X damage to all followers, X = number of followers on the field」 — X counts followers on **both** sides.
  - It is a sweeper that scales against **wide follower boards**: Midrange Nightmare (リリム, zombies, 徒姫 tokens), DDE Elf, 連携 Royal, AF Nemesis tokens.
  - In pack 8 every PS team ran 1–3 copies (see §5).
  - The post-patch field moved to Pirate Royal, which pressures with **amulets** (海賊旗) plus a few rush bodies and Barbaros/Beltezore storm, and to Cutthroat Nemesis. Against that, X is small, and the card neither touches flags nor stops burst. That fits the PS8b and JCS lists cutting it to 0–1. [INF]
  - Wilnas (8 damage to one follower + Intimidate; evolve repeats it) and 狐火 (1 damage to a follower or the leader, shuffles itself back, draws in Overflow) are what replaced the slot. Both are good against small-board or tall threats. 狐火 also thins and cycles. [INF from card text]
  - 味噌日's own mulligan advice (in elf-dragon.md) is to keep HP at 7 or more so an early Wilnas survives. That points to Wilnas as the key midgame card vs aggro.
- **The 6-cost 6/9 (隔断的龙斗士 / Impeding Pugilist, 守護 + バリア):** 0 copies in all 18 Dragon lists here and in pack 8. [INF] The 6–7 curve is already full with proactive threats (相枛津, ノマグダラ, ウィルナス). Ramp's plan is to skip ahead in PP, not to stall, and a Ward body does nothing against flag burst or Storm.
- Kimika 1–3 and Lyria 2–3 vary by player. ZETA ねぎま's list is the most "anti-aggro": Kimika 3, 闇の次元 2, no Wilnas.

### 4.2 Pirate (海賊旗) Royal — post-patch only
| card | G8 9/30 | テンジン 10/06 | PS8b VL mattsu | PS8b DFM kanade | PS8b ZETA cqcq | PS8b CR atom | JCS soroban | JCS lind |
|---|---|---|---|---|---|---|---|---|
| [1] 惨烈的天剑 / Ruthless Eld Sword | · | · | 1 | · | · | · | · | · |
| [1] 无音的包围 / Orchestrated Silence | 3 | 2 | 1 | 2 | 2 | 3 | · | 3 |
| [1] 须臾剑士 / Flashstep Quickblader | 3 | 3 | 3 | 3 | 3 | 3 | 2 | 3 |
| [2] 听略谍报兵 / Sharp-Eared Operative | · | 1 | 1 | · | · | · | 3 | · |
| [2] 相伴相随的日常 / Slice of Domesticity | · | · | 1 | · | · | · | · | · |
| [3] 燃尽之缘 / Severed Ties | 3 | 2 | 1 | 2 | 2 | 2 | 3 | 2 |
| [3] 迷茫的狮子·莫德雷德 / Mordred, Illusory Lion | · | · | 1 | 2 | 1 | 2 | · | · |
| [5] 丽金花·云庆 / Unkei, Goldbloom | 3 | 3 | 3 | 3 | 3 | 2 | 3 | 3 |
| [8] 焦灼炎将·玛尔斯 / Mars, Conflagrant Commander | · | 1 | · | · | 1 | · | · | 1 |
| [10] 武皇的变貌·贝尔铁佐 / Beltezore, Valorous Revenant | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 |

Shared by all lists (same count): [2] 古旧天剑·伊德梅塔 / Yidmetra, Eld Sword x3; [2] 海域斥候 / Open-Sea Scout x3; [3] 漩涡炮手 / Whirlpool Gunner x3; [3] 荣耀的丽金花 / Splendor of the Goldbloom x3; [4] 真红与群青·塞达&贝阿朵丽丝 / Zeta & Bea, Crimson and Blue x3; [4] 黄金时代 / L'Age d'Or x3; [5] 波涛副船长 / Roughwater First Mate x3; [6] 真王之刃·黄金骑士 / Golden Knight, True King's Blade x3; [7] 逆行的罪人·巴巴洛丝 / Barbaros, Rebellious Convict x3

- **The core is identical everywhere:** Yidmetra 3, 斥候 3, 砲手 3, 麗金花 3, ゼタ&ベア 3, アージュドール 3, 副船長 3, 黄金の騎士 3, Barbaros 3, plus クイックブレイダー 3 (2 in そろばん's list).
- **Flex slots:**
  - Game8 maxes 無音の包囲 3 and 燃え落ちる縁 3.
  - Pros trim both to 1–2 and add **モードレッド (迷茫的狮子) 1–2** in all 4: DFM and CR ×2, VL and ZETA ×1. CR keeps 無音 at 3.
  - テンジン (dexel 10/06) [V2 via royal.md]: 「進化権との相性が悪く、抜いても問題なく戦えたため現在は不採用」. So the guide author and all 4 PS teams disagree on Mordred.
  - Mars ×1 (テンジン, ZETA CQCQ, JCS リンド) is the 「相手がケアしづらい」 tech テンジン describes.
  - そろばん (JCS GF) is the outlier: 3 聴略諜報兵, 2 Beltezore, 0 無音.
  - VARREL まっつ adds 1-ofs: 惨烈の天剣, 相伴相随的日常, 聴略諜報兵.

### 4.3 連携 Royal — what pros ran before the patch (PS7b and PS8a, 8 lists), vs Game8
| card | G8 前寄せ | G8 後ろ寄せ | PS7b MRG | PS7b VL | PS7b RJ | PS7b LVH | PS8a RJ tabata | PS8a MRG spicies | PS8a LVH era53 | PS8a RID pansaku |
|---|---|---|---|---|---|---|---|---|---|---|
| [1] 无音的包围 / Orchestrated Silence | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 2 |
| [1] 须臾剑士 / Flashstep Quickblader | 3 | · | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| [2] 勇烈的士兵 / Fearless Soldier | · | · | · | · | · | · | · | · | · | 2 |
| [2] 古旧天剑·伊德梅塔 / Yidmetra, Eld Sword | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| [2] 掌握天空命运的少女·露莉亚 / Lyria, Skydestined | · | 1 | · | 1 | 1 | 1 | 1 | 1 | · | · |
| [2] 温柔援军 / Serenity's Shield | 3 | · | · | · | · | · | · | · | · | · |
| [3] 神话记者 / Intrepid Newshound | · | · | 1 | · | · | · | · | · | · | · |
| [3] 迷茫的狮子·莫德雷德 / Mordred, Illusory Lion | · | · | · | · | · | · | · | · | 1 | · |
| [4] 不动如山的将校 / Unmoving Tactician | · | · | · | · | · | · | 2 | · | · | · |
| [4] 十天众统领·希耶提 / Seofon, Leader of the Eternals | · | 3 | 3 | · | · | · | · | · | · | · |
| [5] 斩奏医护兵 / Metronomic Medic | 3 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| [6] 惨烈的剑王·罗德诺艾尔四世 / Noel IV, Ruthless Warlord | · | 2 | 1 | 1 | · | · | · | · | · | · |
| [7] 武力与治安·娜哈特·娜哈特&宾森特 / Naht & Vince, Force and Order | 2 | · | 1 | · | 2 | 1 | · | 2 | 2 | 1 |
| [8] 人马骑士 / Centaur Centurion | · | · | · | 2 | 1 | 2 | 1 | 1 | 1 | 2 |
| [8] 焦灼炎将·玛尔斯 / Mars, Conflagrant Commander | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| [10] 武皇的变貌·贝尔铁佐 / Beltezore, Valorous Revenant | · | 2 | · | · | · | · | · | · | · | · |

Shared by all lists (same count): [2] 听略谍报兵 / Sharp-Eared Operative x3; [3] 传调联络兵 / High-Strung Liaison x3; [4] 真红与群青·塞达&贝阿朵丽丝 / Zeta & Bea, Crimson and Blue x3; [4] 统音的安纳提玛·吉尔达利娅 / Gildaria, Anathema of Attunement x3; [5] 响爪分队长 / Knellclaw Lieutenant x3; [5] 天命的子弹·巴妮&巴隆 / Bunny & Baron, Fate's Bullet x3; [7] 宽严的音帅·塞扎尔 / Cesar, Accordant Major x3

- Pros are uniform: Mars 3, Medic 3, Cesar 3, Gildaria 3, ナハト&ヴィンセント 0–2, 人马骑士 1–2.
- Game8's 前寄せ list runs 温柔援军 ×3, which no pro played. Its 後ろ寄せ list runs Seofon 3 and Beltezore 2; only MRG's 7後半 list also had Seofon.
- **After the patch, 0 of 4 pro teams brought 連携.**

### 4.4 Combo / Dust Days (DDE) Elf
| card | G8 | Spicies dexel 9/29 | NARU dexel 9/07 | hqzuki 9/01 | PS7b MRG | PS7b VL | PS7b RJ | PS7b LVH | PS8a RJ agunomu | PS8a MRG spicies | PS8a LVH era53 | PS8a RID origami | PS8b VL mattsu | PS8b DFM kanade | PS8b ZETA cqcq | PS8b CR kuhaku | JCS maya | JCS shoya | JCS soroban | JCS mattsu | JCS saikicker | JCS TIK | JCS maho |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [1] 人格切换 / Cognitive Shift | 1 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| [1] 古旧天枪·萨莎妮德 / Sathanid, Eld Lance | 2 | 3 | · | 1 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| [1] 忧郁少女·莫埃尔 / Moelle, Gloomy Maiden | · | 3 | · | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| [1] 精灵陷阱师 / Elven Trapper | 1 | · | 3 | 1 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | 1 | · | · |
| [2] 掌握天空命运的少女·露莉亚 / Lyria, Skydestined | · | 1 | · | 2 | 2 | 3 | 2 | 2 | 1 | 1 | 1 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 1 |
| [2] 根延潜伏者 / Leafshadow Assassin | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| [2] 永恒冰晶·蒂亚 / Tia, Eternal Crystalian | · | · | · | · | 1 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| [2] 绿伞会两大招牌 / Verdant Ring Kindred | 3 | · | 3 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| [2] 绿风细剑师 / Virewind Fencer | · | 3 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| [2] 虫风花的飞翔 / Flight of the Swarmpetal | 1 | · | 2 | · | · | · | · | · | · | · | · | · | · | · | · | · | 1 | · | · | · | · | · | · |
| [2] 风之法则·艾云尼亚 / Ewiyar, Wind Personified | · | 1 | · | · | · | 1 | 1 | 1 | 1 | 1 | · | 1 | · | 1 | · | 1 | · | · | 1 | · | 1 | 1 | 1 |
| [3] 优雅的虫风花 / Grace of the Swarmpetal | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 2 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [3] 神话记者 / Intrepid Newshound | · | · | · | · | · | · | 2 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| [4] 征服苍空的骑空士·古兰&姬塔 / Gran & Djeeta, Valiant Skyfarers | 1 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| [4] 绯岸橙醉 / Crimson Incense | · | 2 | · | 2 | 1 | · | · | · | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 2 |
| [5] 调和的舞者·尤艾尔&苏丝雅 / Yuel & Societte, Dancing Duo | · | · | · | · | · | · | · | · | · | · | 1 | · | 1 | · | 1 | · | · | 1 | · | 1 | · | · | · |
| [6] 冰界鹿王 / Great Hart of the Glacial Realm | 3 | 2 | 3 | 3 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 2 |
| [6] 温柔读心者·米榭儿 / Michelle, Kind Mindreader | · | · | · | · | 1 | · | · | · | · | 1 | · | · | · | · | · | · | · | · | · | · | · | · | · |
| [9] 香风的变貌·飞燕 / Hien, Redolent Revenant | 3 | · | 2 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |

Shared by all lists (same count): [1] 发芽组员 / Sprouting Initiate x3; [1] 大游戏世界 / World of Games x3; [2] 枝叶大姐大 / Virid Lieutenant x3; [3] 烟管的罪人·曲千代 / Magachiyo, Aromatic Convict x3; [3] 虫风花·魅禄 / Miroku, Swarmpetal x3; [4] 操量的安纳提玛·达斯特迪兹 / Thestae, Anathema of Distortion x3; [7] 离合有终·赛德斯&梅希亚 / Setus & Maisha, Bladerights x3

- **Every tournament list (PS7b, PS8a, PS8b, JCS = 19) is one build:** Sathanid 3, Moelle 3, 緑風細剣 3, 根延 3, Lyria 1–3, 冰界鹿王 1–2, 緋岸橙醉 1–2, Ewiyar 0–1, 優雅な虫風花 1–2.
  - This is **Spicies' list** (dexel 9/29, MURASH pro, "CR最終2位").
  - **Hien builds:** Game8 (Hien 3, 二枚看板 3, 罠師) and NARU (Dexel StarSeed Cup winner, 9/07: Hien 2, 罠師 3). Neither appears once in tournament play.
- Yuel & Societte ×1 is a newer tech: LVH Era53, VL まっつ, ZETA CQCQ, JCS しょーや and JCS まっつ.
- Pre-patch REJECT tried 神話記者 ×2; MRG 7後半 tried Tia ×1 and Michelle ×1.

### 4.5 Midrange / Lastword Nightmare
| card | G8 | PS7b MRG | PS7b VL | PS7b RJ | PS7b LVH | PS8a RJ agunomu | PS8a MRG toby | PS8a LVH hirobosu | PS8a RID deko | PS8b DFM yuuri | PS8b ZETA heimu | PS8b CR kuhaku |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [1] 可爱恶魔·莉莉姆 / Lilith, Devilish Cutie | 3 | 3 | 3 | · | 3 | 3 | 3 | 3 | 3 | 3 | 3 | · |
| [1] 大游戏世界 / World of Games | · | · | · | · | · | 1 | · | · | · | · | · | · |
| [1] 魅惑的魅魔·莉莉姆 / Lilith, Enchanting Succubus | 1 | · | 1 | · | · | 1 | · | · | · | · | 1 | 3 |
| [2] 传承的意志 / Wills United | · | · | · | 2 | · | · | · | 1 | · | · | · | · |
| [2] 掌握天空命运的少女·露莉亚 / Lyria, Skydestined | · | 1 | · | · | · | · | · | · | · | · | · | · |
| [2] 暗夜键盘手·露露米 / Lulumi, Vamp on the Keys | · | · | · | 3 | 1 | · | · | · | · | · | · | · |
| [2] 锁链相连 / Chains of the Past | · | · | · | · | · | · | 1 | · | · | · | · | · |
| [3] 制造麻烦的唤灵师 / Fickle Necromancer | 3 | 2 | 3 | · | 2 | 2 | 2 | · | 2 | 1 | 2 | 2 |
| [3] 夜之歌的演唱会 / Hark to the Night Song | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| [4] 古旧天眼·比芭提 / Bibatii, Eld Sight | 2 | 3 | 3 | 1 | 3 | 3 | 1 | 2 | 2 | 2 | 2 | 2 |
| [4] 征服苍空的骑空士·古兰&姬塔 / Gran & Djeeta, Valiant Skyfarers | · | · | · | 2 | · | · | 2 | 1 | 2 | 1 | 1 | 2 |
| [4] 红符的魂魄道士 / Crimson Soulmancer | · | · | · | · | · | · | · | 2 | · | 2 | 1 | · |
| [5] 渴命的破坏者 / Deprived Destroyer | · | · | · | 1 | · | · | · | · | · | · | · | · |
| [6] 天司长的继承者·圣德芬 / Sandalphon, Primarch Successor | · | · | · | 1 | · | · | · | · | · | · | · | · |
| [6] 渊底上校 / Void Colonel | 2 | 2 | 1 | · | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 3 |
| [6] 生与死之技·涅槃 / Nehan, Dispenser of Samsara | · | · | 1 | 1 | 1 | 1 | 1 | 1 | · | · | · | · |
| [7] “最强”的诱惑 / Allure of the Mightiest | 1 | 1 | · | · | · | · | · | · | 1 | 1 | 1 | · |
| [7] 暗之法则·菲迪埃尔 / Fediel, Darkness Personified | · | · | · | 3 | · | · | · | · | · | · | · | · |
| [8] 伽罗塔德 对 泽特 / Garodeth vs. Zeth | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| [8] 出发的憧憬·苇剑&武津御 / Itsurugi & Taketsumi, Brothers | 1 | 1 | 1 | 1 | 1 | 1 | 1 | · | 1 | 1 | · | 1 |
| [9] 枯渴的魔神·阿尔弭斯 / Armes, Depletive Demon | · | · | · | · | · | · | · | 1 | · | · | · | · |

Shared by all lists (same count): [2] 幽冥中尉 / Netherworld Lieutenant x3; [2] 恶魔鼓手·拉兹 / Raz, Demon on the Drums x3; [3] 元素共鸣·巴尔 / Baal, Elemental Resonance x3; [5] 猫咪走绳师 / Highwire Feline x3; [6] 傍死的安纳提玛·徒姬 / Adahime, Anathema of Death x3; [7] 伊斯坦戴德 对 玛尔奇盖特 / Istyndet vs. Mitilykket x3; [9] 死亡主持人·马克米朗 / Macmillan, Reaper of Ceremonies x3

- The core matches Game8's. Pros' flex choices:
  - Gran & Djeeta 1–2 in 7 of 11 PS lists; Game8 has 0.
  - 制造麻烦的唤灵师 1–2 instead of Game8's 3.
  - 紅符の魂魄道士 1–2 (LVH, DFM, ZETA).
  - 涅槃 ×1 (pre-patch lists).
  - CR 空白 (post-patch) runs 魅惑の魅魔リリム ×3 and 0 キュートな悪魔リリム, and 渊底上校 ×3.
- **VARREL まっつ (post-patch) chose Aggro Nightmare instead.** Main cards: 魅惑リリム 3, キュートリリム 3, 残虐の炸裂 3, 渇望の悪魔 3, 強襲の特攻隊長 3, 安瑟珠 (Storm) 3, 丝姬 3, 激烈的副总长 3, Garodeth 2.
- JCS S3 confirmed decks include **no Midrange Nightmare**.

### 4.6 Witch
**実験体 / セフィー Witch (post-patch):**
| card | G8 実験体 | PS8b VL monakawan | PS8b ZETA negima | JCS tobi | JCS siesta |
|---|---|---|---|---|---|
| [1] 大游戏世界 / World of Games | 3 | · | · | 3 | 3 |
| [1] 智慧光辉 / Foresight | 3 | 2 | · | 3 | · |
| [1] 暴风破 / Stormy Blast | · | · | 3 | 3 | · |
| [1] 暴风破 / Stormy Blast | 3 | 3 | · | · | · |
| [1] 过度反应 / Miscalculated Experiment | 3 | 2 | 3 | 2 | · |
| [1] 魔女的炼金炉 / Witch's New Brew | · | · | · | · | 3 |
| [2] 其乐融融的团聚 / Harmonious Meal | · | · | · | 1 | · |
| [2] 掌握天空命运的少女·露莉亚 / Lyria, Skydestined | · | · | · | · | 2 |
| [2] 明越花的转变 / Metamorphosis of the Dawnblossom | 3 | · | · | · | · |
| [2] 炼金炎爆 / Alchemic Flare | · | 3 | 3 | · | 3 |
| [3] 玛纳利亚文书官·琪可 / Tico, Mysterian Spellcrafter | · | 3 | 3 | 2 | 3 |
| [3] 钢铁的小憩 / Amethyst's Naptime | 3 | 3 | 3 | 3 | · |
| [3] 魔恋的爱慕·希姆 / Shymm, Love Bewitched | · | · | 1 | · | · |
| [4] 失眠女巫 / Insomniac Witch | · | · | · | 1 | · |
| [5] 乌涅 / Obsidian Raven | 3 | 3 | 3 | 2 | 3 |
| [5] 甜美存在 / Sweet Abomination | · | · | · | · | 2 |
| [6] 恩爱的大地·坦忒拉&拉缇卡 / Tetra & Ladica, Forest BFFs | 1 | 3 | 3 | 2 | 3 |

Shared by all lists (same count): [2] 传承的意志 / Wills United x3; [2] 沉溺的实验体 / Obsessed Test Subject x3; [3] 人性的爱 / Humane Love x3; [4] 心醉的研究者 / Enamored Researcher x3; [5] 陶醉的才女 / Ecstatic Scholar x3; [7] 万术的罪人·赛菲 / Sephie, Maven Convict x3

**魔手 (Crystal) Witch:**
- Pre-patch: PS7b, PS8a, and jiean (ICS 3rd).
- Post-patch: **0 of 4 PS teams and 0 JCS Playoff/GF players**.
| card | G8 魔手(post-nerf page) | jiean dexel 9/08 | PS7b MRG | PS7b VL | PS7b RJ | PS7b LVH | PS8a RJ takumi | PS8a MRG glory | PS8a LVH rikka | PS8a RID pansaku |
|---|---|---|---|---|---|---|---|---|---|---|
| [1] 天晶魔手 / Crystalspawn | 3 | 3 | 2 | 3 | 2 | 2 | 2 | 3 | · | 2 |
| [1] 正常的侵蚀 / Reaved Order | 3 | 3 | 3 | 3 | 3 | 2 | 3 | 3 | · | 2 |
| [2] 明越花的转变 / Metamorphosis of the Dawnblossom | · | · | · | · | · | 1 | · | · | 3 | 1 |
| [5] 快乐绽花·萨米&玛莉 / Sammy & Marie, Flowers of Joy | 1 | 3 | 2 | · | 2 | 2 | 1 | 1 | 3 | 2 |
| [6] 恩爱的大地·坦忒拉&拉缇卡 / Tetra & Ladica, Forest BFFs | 1 | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [10] 明越花·阿罗 / Ara, Dawnblossom | 2 | 1 | 2 | 3 | 2 | 2 | 3 | 2 | 3 | 2 |

Shared by all lists (same count): [1] 大游戏世界 / World of Games x3; [1] 智慧光辉 / Foresight x3; [1] 暴风破 / Stormy Blast x3; [2] 传承的意志 / Wills United x3; [2] 天晶授予 / Advent of the Eld Crystals x3; [3] 玛纳利亚文书官·琪可 / Tico, Mysterian Spellcrafter x3; [3] 钢铁的小憩 / Amethyst's Naptime x3; [3] 魔恋的爱慕·希姆 / Shymm, Love Bewitched x3; [4] 魔恋的天晶 / Bewitching Eld Crystals x3; [10] 古旧天晶·卡卢基典瑟拉 / Calge-Danthla, Eld Crystals x3

**リンクル / スペル Witch (post-patch: DFM ユーリ, CR ふえた; JCS GF ぱらちゃん):**
| card | PS8b DFM yuuri | PS8b CR fueta | JCS parachan |
|---|---|---|---|
| [1] 暴风破 / Stormy Blast | · | · | 3 |
| [1] 暴风破 / Stormy Blast | 3 | 3 | · |
| [7] 灾难言灵·洋荷 / Ginger, Disastrous Word | 1 | 2 | 2 |
| [10] 破式的变貌·菲绫 / Phylene, Cleansing Revenant | 1 | · | · |

Shared by all lists (same count): [1] 大游戏世界 / World of Games x3; [1] 智慧光辉 / Foresight x3; [1] 漫步的《愚者》·琳库露 / Lhynkal, Wandering Fool x3; [2] 传承的意志 / Wills United x3; [2] 其乐融融的团聚 / Harmonious Meal x3; [2] 明越花的转变 / Metamorphosis of the Dawnblossom x3; [3] 玛纳利亚文书官·琪可 / Tico, Mysterian Spellcrafter x3; [3] 钢铁的小憩 / Amethyst's Naptime x3; [5] 快乐绽花·萨米&玛莉 / Sammy & Marie, Flowers of Joy x3; [6] 余韵俳谐师 / Woodsong Haikumaster x2; [6] 恩爱的大地·坦忒拉&拉缇卡 / Tetra & Ladica, Forest BFFs x3; [10] 明越花·阿罗 / Ara, Dawnblossom x3

- **実験体:** VL monakawan and ZETA ねぎま (pros) run 錬金炎爆 3, ティコ 3 and Tetra 3, and **0 大遊戯世界 and 0 明越花の転変**. Game8 runs World of Games 3, 転変 3, Tetra 1 and no 炎爆. The two JCS lists sit in between.
- "暴风破" shows up as two different IDs with the same ZH name. That is a DB naming collision, and the two are different cards.
- **リンクル Witch** (Lhynkal ×3, Harmonious Meal ×3, Haikumaster ×2, Ara ×3, Ginger 1–2) is a post-patch archetype with no Game8 guide among the pages checked. DFM and CR submitted identical lists except for the last two slots: DFM runs Ginger ×1 + Phylene ×1, CR runs Ginger ×2.
- The 魔手 lists hardly changed before the patch: pros flex Ara 2–3, Sammy & Marie 1–3 and Tetra 1. jiean's (ICS) list has Sammy & Marie 3, Ara 1 and no Tetra.

### 4.7 Amulet Bishop
| card | G8 698347 | zhangyue dexel | PS7b MRG | PS7b RJ | PS8a RJ takumi | PS8a MRG toby | PS8a LVH rikka | PS8a RID pansaku | PS8b VL terarina | PS8b DFM yuuri | PS8b ZETA heimu | PS8b CR fueta | JCS tobi | JCS parachan | JCS siesta(prison) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [0] 莉莉艾的鼓舞 / Awed and Inspired | · | · | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | · |
| [1] 大游戏世界 / World of Games | 3 | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| [1] 羽翼石像 / Winged Statue | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | · |
| [1] 铭刻之约 / Vow of Devotion | · | 3 | · | 1 | 1 | · | · | · | · | 1 | · | · | · | 2 | 1 |
| [1] 魔杖傍身的外科医生·缇可 / Tikoh, Asclepian Surgeon | · | · | 3 | 3 | 3 | 3 | 3 | 2 | 2 | 3 | 3 | 3 | 3 | 3 | · |
| [2] 完美的时钟 / Timepiece of Perfection | 3 | 3 | 1 | · | · | · | · | 2 | 2 | 1 | · | · | · | · | 2 |
| [2] 污浊的圣水 / Unholy Water | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 2 | 3 | 2 | 2 | 2 | 3 | · | · |
| [3] 坚固的雾卷花 / Resolve of the Mistbloom | · | · | · | · | · | · | · | · | · | · | · | · | · | 2 | · |
| [3] 奇迹独角兔 / Miraculous Al-mi'raj | 3 | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| [3] 英雄幻视·托路 / Troue, Heroic Visionary | 3 | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| [3] 蕾·菲耶的宝石 / De La Fille's Gleaming Gems | · | · | · | · | · | · | · | · | · | · | · | 1 | · | 2 | 3 |
| [4] 崇高的憎恶·康蒂玛 / Kandima, Sublime Hatred | · | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | · |
| [4] 黑暗次元 / Dark Dimensions | · | · | 2 | 2 | 2 | 2 | 2 | · | · | 2 | 2 | 2 | 2 | · | · |
| [5] 崇奉的懦者 / Prostrating Coward | · | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| [5] 希望的光彩·莉迪耶尔 / Zoe, Dazzling Hope | · | · | · | · | · | · | · | · | · | · | · | · | · | · | 3 |
| [6] 神纹的罪人·艾尔拉德 / Erralde, Signet Convict | · | · | · | · | · | · | · | · | · | · | · | · | · | · | 2 |
| [6] 神纹誓言 / Juratio | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 1 | · | 1 | 2 | 1 | 2 | · | 2 |
| [6] 翼天的变貌·奥梅里欧 / Omerio, Winged Revenant | · | · | · | · | · | · | · | 2 | 2 | · | · | · | · | · | · |
| [7] 崇拜经理人·伊尼西雅 / Initia, Chief Ordination Officer | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| [7] 誓言干部 / Executor of the Vow | · | · | · | · | · | · | · | · | · | · | · | · | · | · | 2 |
| [8] 混沌监狱·阿兹弗特 / Azvaldt, Penitentiary of Chaos | 2 | · | · | · | · | · | · | · | · | · | · | · | · | · | 3 |
| [9] 古旧天书·莲妥丝 / Lyanthoth, Eld Tome | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 2 |

Shared by all lists (same count): [1] 阳光耳饰 / Earrings of Sunlight x3; [2] 同窗好友 / Academy Hijinks x3; [2] 救赎的圣典 / Scripture of Salvation x3; [3] 海蚀三叉戟 / Trident of Eroding Tides x3; [4] 崇高的天书 / Sublime Eld Tome x3

- **Every pro and JCS Bishop except siesta is the same control shell.** Kandima 3, 崇奉の怯者 3, Tikoh 2–3, 汚濁の聖水 2–3, 莉莉艾的鼓舞 1–2, 闇の次元 0–2, ユラティオ 0–2, イニシア 2, Lyanthoth 3.
- Game8 698347 is a different deck (Azvaldt Storm-OTK: アルミラージ 3, トルー 3, 大遊戯世界 3, アズヴォルト 2, 0 Kandima, 0 Coward). Treat it as a ladder pet build, not the meta build.
- zhangyue616's dexel control list (9/01) is close to the pro shell. Differences: 刻みし約束 3, 時計 3, no Tikoh, no 闇の次元.
- Tech: 翼天の変貌オメリオ ×2 in VL Terarina (8後半, post-patch) and RID ぱんさく (8前半, pre-patch). CR ふえた runs 宝石 ×1.

### 4.8 Nemesis (details are in the sibling's `research2/nemesis.md`)
Post-patch Cutthroat:
| card | G8 cutthroat | PS8b VL terarina | PS8b DFM mil | PS8b ZETA heimu | PS8b CR fueta | JCS shoya | JCS mattsu | JCS lind | JCS saikicker | JCS massu |
|---|---|---|---|---|---|---|---|---|---|---|
| [1] 器械操纵者·吉尔克 / Zerk, Artifact Manipulator | · | 1 | 1 | 1 | 1 | · | 1 | 1 | 1 | 1 |
| [1] 大游戏世界 / World of Games | 1 | · | · | · | · | 1 | · | 1 | 1 | 1 |
| [1] 尽小花的临照 / Light of the Dewdrop | 1 | · | · | · | · | · | · | · | · | · |
| [1] 苏生调律 / Resurrection Tuner | 1 | · | · | · | · | · | · | · | · | · |
| [2] 古旧天斧·尤泽塔 / Yog-Zentha, Eld Axe | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [2] 尽小花·伊鞠 / Imari, Dewdrop | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [2] 报恩工匠·艾萨克 / Isaac, Congenial Engineer | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [2] 掌握天空命运的少女·露莉亚 / Lyria, Skydestined | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [2] 轮回转冲 / Initiation of Rebirth | 1 | · | · | · | · | · | · | · | · | · |
| [2] 过度守护者·莉欧娜 / Leona, Overbearing Guardian | · | · | 1 | · | · | · | · | · | · | · |
| [2] 遗忘的纯真·爱卡 / Aika, Elegy of Loss | · | 1 | 1 | 1 | 1 | · | 1 | · | · | · |
| [3] 夜王再起·翔 / Sho, Reborn Night King | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [3] 狂野播报员 / Brazen Broadcaster | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [3] 神话记者 / Intrepid Newshound | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [3] 被侵略的世界 / Encroached World | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [3] 身无长物唯有石 / Stone Breaker | 1 | · | · | · | · | · | · | · | · | · |
| [3] 转动的《命运之轮》·斯洛士 / Slaus, Revolving Wheel of Fortune | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [3] 门扉接续者·拉姿莉 / Lazuli, Gateway Connector | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [4] 个性店主 / Brusque Barkeep | · | 1 | · | · | 1 | · | 1 | · | 1 | · |
| [4] 双子无人机少女 / Twindrone Engineer | · | 1 | 1 | 1 | 1 | 1 | 1 | · | · | · |
| [4] 奋厉追赶·米乌 / Myuu, Hot on His Heels | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [4] 新时代地理学者 / New-Age Cartographer | · | 1 | 1 | 1 | 1 | 1 | 1 | · | · | 1 |
| [4] 舞台缔造者 / Marionette Master | · | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| [5] 《世界》的呈现 / Fate of the World | 1 | · | · | · | · | · | · | · | · | · |
| [5] 光之法则·龙敖 / Lu Woh, Light Personified | · | 1 | 1 | · | 1 | 1 | 1 | 1 | 1 | 1 |
| [5] 拙劣的人偶 / Substandard Puppet | 1 | · | · | · | · | · | · | · | · | · |
| [5] 无尽旅途·蕾娜 / Reina, Timeless Wanderer | 1 | · | · | · | · | · | · | · | · | · |
| [5] 驰骋天空的守护者·卡塔莉娜 / Katalina, Sky's Protector | · | 1 | 1 | 1 | 1 | 1 | · | 1 | 1 | 1 |
| [6] 低劣的玩具 / Shoddy Plaything | 1 | · | · | · | · | · | · | 1 | 1 | 1 |
| [6] 平庸的制图 / Myriad Designs | 1 | · | · | · | · | · | · | · | · | · |
| [6] 最古老的狱卒 / Jailor of Antiquity | 1 | · | · | · | · | · | · | · | · | · |
| [6] 特殊目标·海雷姆哈妮 / Illamrita, Designated Target | 1 | · | · | · | · | · | · | · | · | · |
| [6] 聪明的创造者 / Brilliant Inventor | · | · | · | 1 | · | 1 | 1 | · | · | · |
| [7] 严厉的教官·伊尔莎 / Ilsa, Brutal Drill Sergeant | 1 | · | · | · | · | · | · | · | · | · |
| [7] 知恩图报·米莉亚姆 / Miriam, Reciprocator | 1 | · | · | · | · | · | · | · | · | · |
| [8] 愚劣的兵器 / Ludicrous Ordnance | 1 | · | · | 1 | · | 1 | · | 1 | 1 | 1 |
| [8] 混沌监狱·阿兹弗特 / Azvaldt, Penitentiary of Chaos | 1 | · | · | · | · | · | · | · | · | · |
| [9] 唯一王者·别西卜 / Beelzebub, Supreme King | 1 | · | · | · | · | · | · | 1 | · | · |
| [9] 断绝的轮回·泽勒尔 / Zerael, Sundered Rebirth | 1 | · | · | · | · | · | · | · | · | · |
| [9] 高洁的黑翼·奥莉薇 / Olivia, Proud Dark Angel | 1 | · | · | · | · | · | · | · | · | · |

Shared by all lists (same count): [1] 屈辱流放 / Disgraceful Banishment x1; [1] 束刃的罪人·卡特斯罗特 / Cutthroat, Fluxblade Convict x3; [1] 诚心的尽小花 / Sincerity of the Dewdrop x1; [1] 跑酷 / Freerunning x1; [1] 青锈小卒 / Bluerust Underling x1; [2] 人偶剧场 / Puppet Theater x1; [2] 人偶长矛手 / Puppet Lancer x1; [2] 你的前辈·欧丝 / Eudie, Your Dependable Mentor x1; [2] 悠然的滑手 / Cool Courier x1; [3] 白牙燐敛  / Soulforge x1; [4] 征服苍空的骑空士·古兰&姬塔 / Gran & Djeeta, Valiant Skyfarers x1; [4] 锻磨保镖 / Ironwork Bodyguard x1; [5] 决断的交错·亚修雷&莉缇雅 / Asher & Lydia, Paths Beyond x1; [5] 铸铁亲信 / Steelforged Right Hand x1; [6] 天司长的继承者·圣德芬 / Sandalphon, Primarch Successor x1; [6] 混沌军势 / Chaos Legion x1; [7] 弹哭的变貌·艾兹伊甸 / Aizeden, Killshot Revenant x1; [7] 恶劣的纯心·卡密希拉 / Camiscilla, Unfeeling Heart x1; [8] 虚刻的安纳提玛·斯卡雷特 / Scarlet, Anathema of Dislocation x1

Pre-patch AF (PS8a) vs Game8 AF:
| card | G8 AF | PS8a RJ takumi | PS8a MRG glory | PS8a LVH hirobosu | PS8a RID origami |
|---|---|---|---|---|---|
| [2] 古旧天斧·尤泽塔 / Yog-Zentha, Eld Axe | · | 3 | 3 | 3 | 3 |
| [2] 尽小花·伊鞠 / Imari, Dewdrop | 3 | 2 | 3 | 3 | 3 |
| [2] 悠然的滑手 / Cool Courier | 3 | · | · | · | · |
| [2] 报恩工匠·艾萨克 / Isaac, Congenial Engineer | 3 | · | · | · | · |
| [3] 恶劣的天斧 / Unfeeling Eld Axe | · | 3 | 3 | 3 | 3 |
| [3] 狂野播报员 / Brazen Broadcaster | 3 | · | 2 | 1 | 2 |
| [4] 个性店主 / Brusque Barkeep | 1 | · | · | · | · |
| [4] 奋厉追赶·米乌 / Myuu, Hot on His Heels | 3 | · | · | · | · |
| [5] 拙劣的人偶 / Substandard Puppet | · | 2 | · | 1 | · |
| [6] 低劣的玩具 / Shoddy Plaything | · | 3 | 3 | 3 | 3 |
| [6] 天司长的继承者·圣德芬 / Sandalphon, Primarch Successor | · | 2 | 1 | 1 | 1 |
| [6] 平庸的制图 / Myriad Designs | · | 2 | 2 | 2 | 2 |
| [6] 混沌军势 / Chaos Legion | · | 2 | 2 | 2 | 2 |
| [7] 弹哭的变貌·艾兹伊甸 / Aizeden, Killshot Revenant | 3 | 2 | 2 | 2 | 1 |
| [8] 虚刻的安纳提玛·斯卡雷特 / Scarlet, Anathema of Dislocation | 3 | 1 | 1 | 1 | 2 |

Shared by all lists (same count): [1] 诚心的尽小花 / Sincerity of the Dewdrop x3; [1] 跑酷 / Freerunning x3; [2] 你的前辈·欧丝 / Eudie, Your Dependable Mentor x3; [5] 决断的交错·亚修雷&莉缇雅 / Asher & Lydia, Paths Beyond x3; [7] 恶劣的纯心·卡密希拉 / Camiscilla, Unfeeling Heart x3; [8] 愚劣的兵器 / Ludicrous Ordnance x3

- **The PS Cutthroat lists match the JCS lists.** They play Zerk, Yog-Zentha, Imari, Isaac, Lyria, 翔, Broadcaster, 記者, 侵略されし世界, Slaus, ラズリ, Myuu, マリオネットマスター, Katalina and Lu Woh. Game8's Cutthroat list is a different, slower shell: Olivia, Zerael, Beelzebub, Miriam, Ilsa.
- **Pre-patch pro AF differed from Game8 AF.** Pros ran 3 Yog-Zentha, 3 恶劣的天斧, 3 Shoddy Plaything, 2 平庸的制図, 2 混沌軍勢, Sandalphon 1–2 and only 1–2 Scarlet. Game8 had Courier 3, Isaac 3, Myuu 3, Scarlet 3.

---
## 5. Pack 8 vs pack 9: how the same pros built Ramp Dragon
PS 5節後半 (8/26, pack 8) [V1] compared with PS8b (pack 9):
| card | PS5b(pack8) LVH | PS5b(pack8) DFM | PS5b(pack8) VARREL | PS5b(pack8) ZETA | PS8b DFM mil | PS8b ZETA negima |
|---|---|---|---|---|---|---|
| [1] 狐火蜃景 / Ephemeral Foxfire | · | · | 2 | · | 1 | 2 |
| [2] 宣扬的龙人 / Dragonewt Promoter | 3 | 3 | 3 | 2 | 3 | 3 |
| [2] 掌握天空命运的少女·露莉亚 / Lyria, Skydestined | 3 | 2 | 3 | 2 | 3 | 3 |
| [2] 满面笑容的烹饪·琪米卡 / Kimika, Cook of Happiness | · | 1 | · | · | 1 | 3 |
| [3] 涸绝的显现·吉尔内莉莎 / Gilnelise, Voracity Manifest (ROTATED) | 3 | 3 | 3 | 3 | · | · |
| [3] 焦龙的午睡 / Lazing Flame | · | · | · | 2 | · | · |
| [4] 日珥咆哮 / Roar of Prominence | 2 | 2 | 1 | 3 | 1 | · |
| [4] 黑暗次元 / Dark Dimensions | · | · | · | · | · | 2 |
| [5] 烈绝的显现·嘉尔缪 / Galmieux, Ardor Manifest (ROTATED) | 3 | 3 | 3 | 3 | · | · |
| [7] 炎之法则·威尔纳斯 / Wilnas, Flame Personified | 3 | 3 | 2 | 2 | 3 | · |
| [7] 禁牙的变貌·诺玛格达拉 / Normagdala, Ravening Revenant | · | · | · | · | 3 | 3 |
| [9] 焦灰的安纳提玛·班德奈特 / Burnite, Anathema of Ash | 2 | 2 | 2 | 2 | 3 | 3 |
| [9] 阿尔比昂巴哈姆特 / Alabaster Bahamut | · | · | · | · | 1 | · |

Shared by all lists (same count): [2] 古旧天刀·波菈莱 / Vorlalai, Eld Blades x3; [2] 懒惰的波摇花 / Sloth of the Crestpetal x3; [3] 龙之启示 / Dragonsign x3; [5] 世界的伙伴·佐伊 / Zooey, Ally of the World x3; [7] 断头的斩姬·相枛津 / Sagatsumatsu, Fair Beheader x3; [8] 金银绚烂·璐米欧儿&雅尔贞特 / Lumiore & Argente, Shining Wings x3; [10] 约束的《正义》·伊兰翠 / Erntz, Governing Justice x3

- In pack 8, every pro ran **日珥咆哮 1–3 and Wilnas 2–3**, plus the now-rotated ギルネリーゼ and ガルミーユ. That was an Elf and Nightmare board meta.
- In pack 9 the 9-drop Burnite went from 2 to 3, Normagdala 3 replaced the rotated cards, and 日珥 fell to 0–1.
- [V1] for pack 8: one fetch only. Every hash decodes to 40 cards with no unknown IDs.

---
## 6. Author credibility
Scale (my reading of the in-game system, Game8 712357 [V1]):
- **BEYOND** = CR 1850+ and top 100 of that class's leaderboard.
- **LEGEND** = CR 1850+.
- PS pros' peak ratings run about 2200–2360 (shadowverse-vision).
- 「瞬間1位」 = momentarily #1 on one class leaderboard.
- 「最終n位」 = rank at season end; harder, because it has to be held.
- A "~2000 CR" player is around the BEYOND line and is not a top-rank player.

| Author | Used for | Credentials found | Assessment |
|---|---|---|---|
| **Spicies** | DDE Elf (dexel 9/29) | **MURASH GAMING PS pro** (PS record 4–2 after 第8節). Elf peak 2250, BEYOND ×3 in Elf. YouTube "Spicies Ch" (about 38h streamed in the last 7 days). Played Elf, Royal and Dragon in PS8a [V1 vision; team V2] | **Top tier.** His dexel list is effectively the tournament list (§4.4) |
| **Chappy** | (ICS champion) | RIDDLE ORDER PS pro. ICS 2026 Singapore champion [V2]. Peak 2217 (Elf), BEYOND ×35. Elf, Nightmare and Royal mains. Twitch chappy916, about 200h a month. Made a Tier list with 2 others (X, pack 6 era). PS record 1–2 [V1] | **Top tier.** No written pack-9 deck guide found; streams only |
| **jiean/深紅蘭** | 魔手 Witch (dexel 9/08) | ICS 2026 **3rd** (Witch/Dragon) [V2]. 「CR瞬間1位」. X @SV_Essia [V1] | **Top tier** for pre-nerf 魔手. The list is obsolete after the 4-cost nerf |
| **味噌日** | Ramp Dragon (dexel 9/17) | 「CR瞬間1位」 label only. X @misokaSV. No tournament result found | **Strong ladder player.** The list sits between Game8 and the pros (Wilnas 2 / 日珥 1); pre-patch |
| **テンジン** | Pirate Royal (dexel 10/06) | 「CR瞬間2位」. X @tenjin_sv. No team or tournament found | **Strong ladder player.** Core = pros; the Mordred choice disagrees with all 4 PS teams |
| **NARU** | DDE Elf (dexel 9/07) | Dexel StarSeed Cup winner (community cup, size unknown). 24 years old. 「次の目標はプレミアシリーズ」 → not a pro [V1] | Mid. His Hien build has **0 adoption** among PS/JCS players |
| **hqzuki** | DDE Elf (dexel 9/01) | 「6連勝でBEYOND到達」 only | Low–mid (BEYOND-line player). Early-format list |
| **zhangyue616** | Amulet Bishop (dexel 9/01) | 「クラス最速BEYOND」 only | Mid. His control shell matches pros' direction |
| **ふじのん** | Midrange Nightmare (dexel 8/29) | 「最速BEYOND」 | Mid. Launch-week list |
| **女神 / とりっぴよー** | Aggro Nightmare (dexel 9/09, 9/25) | 「CR瞬間1位」 | Strong ladder players. Aggro NM got 1 PS pick post-patch (まっつ) |
| **もとやしき** | Pirate (note 9/01) | 「BEYOND＆瞬間1位」 (pack 9). Earlier 「瞬間1位＆CR2000」 (pack 7). A Fukuoka area event 7–1 (older) [V1 note profile] | Mid-high ladder. Pre-patch |
| **coolyu** | Face Dragon (note 8/31, 9/06) | Self-reported 「CR2050 over」 (pack-1 era Rhinoceus Elf). 「フェイスドラ界隈最速BEYOND、ドラ界隈7番目」. Recruited RAGE practice partners | **Mid, the "~2000 CR" type.** Niche deck; no tournament Face Dragon seen |
| **いろは** | Ramp Dragon (note 9/15) | 「前期最終1桁」 (final top-10 last season, per the earlier notes) [V1] | Mid-high. Mostly paywalled |
| **Kamijames** | Ramp (note 7/16, pack 8) | 「瞬間5位」 Aggro Royal (pack 5). No tournament results | Mid. **Pack 8 list; stale** |
| **はせ** | Sephie Witch (note 9/03) | 「BEYOND到達」 only; 2 notes total | Low–mid (BEYOND line) |
| **ハガネ** | Amulet Bishop / 実験体 (notes, 9月) | note profile: craft-beer brewer, fighting-game hobbyist. Note titles 「アミュレットビショップが難しすぎる」「格ゲーで折れたおっさんをシャドバは救えるのか？」 [V1] | **Low. A casual's diary, not a guide.** Do not use for card choices |
| **yukki (ゆっきーずんだ)** | DDE Elf (note 8/31, 50 games, 27–23) | Zundamon video maker and indie dev. No rank stated | Low–mid. A 50-game sample at 54% |
| **Lilie** | Pirate / 連携 Royal (notes) | 「ゲームのオタク」. Writes mostly about Yu-Gi-Oh MD (WCSQ), Shape of Dreams and Astral Party. No SV rank stated | **Low–mid.** Generalist; good at maths (flag-damage calc) but no competitive proof |
| **Game8 / GameWith editors** | Most tier and list pages | Anonymous staff | Lists diverge strongly from tournament lists in Elf, Bishop and Dragon (§4) |

### 6.1 Strongest players, and whether they publish
- **PS players, by peak rating / BEYOND count** (shadowverse-vision rating page [V1]):
  - rikka (LVH): 2362, #1 Witch, pack 8 後半, BEYOND ×45.
  - Toby (MRG): 2340, #1 Witch, pack 5; 3 JCG wins (YouTube channel bio).
  - Terarina (VARREL captain): 2338, #1 Bishop, pack 7; BEYOND ×54.
  - ユーリ (DFM): 2320, #1; WGP 2025 champion "yuuri" [V1, saiganak search-result title only].
  - Atom (CR): 2306.
  - 空白 (CR): 2305.
  - まっつ (VARREL): 2270, #5 pack 8. ICS top 8; JCS S3 GF.
  - Chappy: 2217.
  - glory (MRG): BEYOND ×53.
  - Best PS records: Toby 7–1; Miru 6–1; Takumi 6–1 (shadowverse-vision front page [V1]; whether "Miru" is ミル (DFM) and "Takumi" is 拓海 (REJECT) was not confirmed).
- **Publishing:**
  - Spicies: dexel written guide (9/29) plus YouTube.
  - Toby: YouTube @toby6968. His hatena blog is stale (last post 3/2026: 「AFネメシス徹底解説」 2025).
  - rikka: YouTube @rikka1646 (streams).
  - Terarina: YouTube @terarina7187.
  - Era53 (LVH): YouTube 「JCS直前！PS選手によるカットスロートネメシス解説」 (title only; from the sibling).
  - Chappy: Twitch.
  - jiean: dexel.
  - Video descriptions could not be read (YouTube 429; RSS blocked).
- **The best written anchor is now the official PS lists themselves** (API above), refreshed every matchday. Next: 第9節 on 10/14 (MRG vs RID, REJECT vs DFM) and 10/21. RAGE/JCS S3 GF is on 10/25.

---
## 7. Gaps
- **ICS card lists:** not obtained. The official site is Next.js with no reachable API; liquipedia returned 429 twice.
- **The 8節後半 match results** (which decks won on 10/7) were not collected. shadowverse-vision player pages show per-round class plus W/L.
- **PS 6節, 7節前半 and 7節後半 player names:** the API has them for 6 and 7前半 (topics 336, 339); not fetched. 7後半 (341) has class filenames only.
- **CN (国服) tournament lists:** not found (bilibili search is blocked by robots; search-engine indexing is stale).

## Appendix: files
- `scratchpad/ps/s8b_fetch1.txt`: PS 8節後半, team|class|player|hash [V2].
- `scratchpad/ps/s8a_fetch1.txt`: PS 8節前半 [V2].
- `scratchpad/ps/s7b.txt`: 7節後半 [V1].
- `scratchpad/ps/s5b.txt`: 5節後半, pack 8 [V1].
- `scratchpad/ps/cmp.py`: comparison tool; usage `python3 cmp.py in_x.txt` with label|hash lines.
- `scratchpad/ps/in_*.txt` / `in_*.md`: per-archetype inputs and outputs.
- Example post-patch hashes (decode with deck.py):
  - VL まっつ Pirate: `1.2.cEZs.cEZs.cEZs.dmEA.dmj6.dmj6.dmj6.dmyk.dmyk.dmyk.e9Ak.e9Ak.e9Ak.e9NO.e9NO.e9NO.eXbE.eXnu.eXnu.eXnu.evi-.evm6.fIQE.fgIM.fgIM.fgIM.fgX-.fgX-.fgX-.fgb6.fgnc.fgnc.fgnc.fgqk.fgqk.fgqk.fh1E.fh1E.fh1E.fh1O`
  - DFM ミル Ramp: `1.4.cJl6.cJl6.cJl6.dhqm.dhqm.dhqm.drrE.drrE.drrE.drrO.drrO.drrO.eDpc.eE3E.eE3E.eE3E.eEFk.eEFk.eEFk.ecgE.ecgE.ecgE.ecgO.ecgO.ecgO.e-Ls.e-Ls.e-Ls.e_4k.e_4k.e_4k.fDkE.fN08.fNIk.fNVO.fNVO.fNVO.flvu.flvu.flvu`
  - DFM ユーリ リンクル Witch: `1.3.cH3E.cH3E.cH3E.cfTu.cfTu.cfTu.e4Gg.e4Gg.e4Gg.eB7k.eB7k.eB7k.eBKO.eBKO.eBpU.eBpU.eBpU.eBpe.eBpe.eBpe.fDXk.fDXk.fDXk.fKZk.fKZk.fKZk.fKcs.fKcs.fKcs.fKpM.fKpM.fKpM.fKsU.fKsU.fKsU.fL2-.fL2-.fL2-.fL38.fjTe`
  - ZETA ねぎま 実験体 Witch: `1.3.dpCU.dpCU.dpCU.eaD-.fDXk.fDXk.fDXk.fKNE.fKNE.fKNE.fKpM.fKpM.fKpM.fKsU.fKsU.fKsU.fL2-.fL2-.fL2-.fikc.fikc.fikc.fink.fink.fink.fi-E.fi-E.fi-E.fj1M.fj1M.fj1M.fjDs.fjDs.fjDs.fjG-.fjG-.fjG-.fjTU.fjTU.fjTU`
  - CR 空白 DDE: `1.1.dhqm.dhqm.dkWU.e4Gg.e4Gg.e4Gg.e6kU.e6x8.e6x8.e6x8.eVLe.eVLe.eVLe.etGk.etGk.etGk.etl-.etl-.etl-.etm8.etm8.fFRw.fFRw.fFRw.fGAU.fGAU.fGAU.fds6.fds6.fds6.fe5k.fe5k.fe5k.feLM.feLM.feLM.feOU.fea-.fea-.fea-`
  - ZETA ヘイム Bishop: `1.6.cOc2.cOc2.cOc2.dw0Q.dw0Q.dwU6.dwU6.dwU6.eShA.eShA.egps.egps.egps.egrQ.egrQ.eh52.eh52.eh52.ehKg.ehKg.ehKg.ehYk.ehYk.ehYk.ehYu.ehYu.ehYu.f3Fw.f3Fw.f3Fw.f3lA.f3lA.f3lA.f3zO.f3zO.fS9g.fS9g.fS9g.fqaA.fqaA`
