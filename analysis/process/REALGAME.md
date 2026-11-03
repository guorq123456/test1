# Item 6: the real-game loop (the architecture thread)

Data: /mnt/project-files/shadowverse/salem-games/tracker/games.jsonl. It holds 42 ranked games, 7 on 10-31 and 35 on
11-01. The tracker parser built it from the client's breadcrumb file.

**The rule stands:** these games are only for checking the simulator and showing Salem where the bot would play
differently. They never enter deck search, self-play, training or the trainer (陪练台).
- The data stays in /mnt/project-files.
- Only scripts and aggregate results are committed. Per-game tables go to /mnt/project-files/shadowverse/salem-games/.

## 6a: card-level consistency (pre-registered 2026-11-02 11:2xZ, before running any check)

Seen before writing this: the file's fields, and the move list of one game (the last one, 三轴土 vs 兔子主教). No
check has been run.

### What the breadcrumb gives

The parser keeps three things for each side:
- the cards played;
- evolve and super-evolve events, each with the own-turn number;
- the cards seen (the starting hand plus draws and created cards; for the opponent, revealed or played cards).

It does not give attack targets, trades, HP, spell targets, random results, or whether a card was enhanced. The
`moves` list has no created-card or summon events. Who played each move is inferred: anchored on class, guessed for
neutral cards. Each game carries an `ambiguous` count.

### The checks

Each flag is then read by hand and put into one of four classes:
- **sim**: a simulator bug;
- **parse**: a parser error, such as the wrong side, a wrong turn, or the wrong first player;
- **legit**: an effect the check ignores, such as a cost reduction or an effect evolve;
- **unclear**.

1. **Pool.** Every card id played or seen, normalised as the parser does (a leading 7 becomes 1, the last digit becomes
   0), exists in the simulator's card tables. A missing card is a pool gap.
2. **Created cards.** Every token a side plays or holds must come from a card seen in that game. A token is an id
   starting with 9, or a card marked as a token. The simulator's scripts must be able to create it, read statically:
   - the token's constant is referenced by the card's registered script class;
   - or by that class's same-module base classes and helper functions;
   - or by cross-module `module.NAME` references.

   The generator is looked for first on the same side, then on the other side. A token with no generator gets a flag.
3. **Evolve timing.** A point evolve before own turn 5 going first (4 going second) gets a flag, and so does a
   super-evolve before own turn 7 (6). These are the engine's EVOLVE_TURN and SUPER_EVOLVE_TURN, rulings R-02.
   - An early evolve is legit only when a card played that game can evolve by effect, and the simulator's script calls
     `evolve`.
   - Games whose `first_why` is not a clean draw-order call are reported separately.
4. **PP budget.** For each own turn, the play points available are min(10, own turn) plus any max-PP gains and PP
   recovery the side's earlier cards can give (from the scripts: `gain_max_pp`, `recover_pp`).
   - The sum of the cards' printed costs that turn must not exceed that.
   - A flag is first checked against cost reducers: spellboost, earth-rite and 增幅 cost-downs, `cost` changes in
     scripts. Only then is it called.
5. **Class.** No side plays a card of a class other than its own or neutral. The parser assigns by class, so only
   neutral-to-wrong-side shows up here; it is reported, not counted.

### Predictions

- The plan's prediction, kept as registered: the games show at least one disagreement that is a simulator bug or a
  parser error 〔0.5〕.
- At least one of them is a simulator bug, not a parser error 〔0.3〕.
- Every card id maps to the simulator pool 〔0.85〕.
- At least 95% of tokens have a generator in their game 〔0.7〕.

### Results (written after the run, 2026-11-02 11:5xZ; ledger F-16)

Deviations from the registration, all made before reading any flag as sim or parse:
- The id normalisation keeps alternate play forms. Last digit 2 is Crystallize or Accelerate; 3 is its alternate art.
  The tracker's base_id folds them into the base card, which made every crystallized 奇迹独角兔 a 3-cost play.
- The PP check has a second, generous level (`PP·可解释` vs `PP·未解释`). A card counts 0 if any script can change
  its cost. A token counts 0 when its generator was played earlier that turn, since a summon is logged as a play. Each
  PP-recovery or max-PP card played or evolved that turn adds 2.
- Token generation is followed through created non-deck cards (crests, alternate forms). 雾卷花·茎白 makes 神圣猎鹰
  through its crest.

Counts:
- Pool: 1027 of 1027 card ids (game x side x card) exist in the simulator.
- Tokens: 119 of 120 have a generator in their game. The exception is a 蝙蝠 the 中速梦魇 opponent played and
  super-evolved in game 25. None of that opponent's seen cards make bats in the simulator. Classified **unclear**.
- PP: 60 turns spend more than the turn number. 49 are explained at the generous level. The other 11, and the 2 early
  evolves, all sit in games the parser itself marks as unreliable, so they are classified **parse**:
  - 7 in same-class games, where the side of each play is inferred from turn timing;
  - 5 in game 38, where both sides' turn numbers are one low and the parser warned;
  - 1 in the one partial game, where the ramp turns are missing.
- **sim** (a simulator bug): 0.

Predictions:
- At least one sim or parse disagreement (0.5): TRUE, all of them parse.
- At least one sim bug (0.3): FALSE.
- All ids in the pool (0.85): TRUE.
- At least 95% of tokens generated (0.7): TRUE, 99.2%.

Limits: the check sees neither HP, targets nor random results. It rules out pool gaps, ungeneratable tokens and clearly
wrong costs or evolve turns, nothing finer. The per-game table is in
/mnt/project-files/shadowverse/salem-games/realgame-6a-2026-11-02.md (not in the repo).

For 6b: use only games that are not same-class, not partial, and carry no turn-number warning.

## 6b: decision divergence table (pre-registered 2026-11-02 12:0xZ, before any position is rebuilt)

### Data

games.jsonl alone can't rebuild Salem's hand at the start of a turn:
- my_seen has no turn or time, and it repeats hand events;
- the opening cards he mulliganed away are not recorded.

So 6b waits for the raw breadcrumb files (asked for 11-02 12:0xZ). Once they are here, the tracker's own parser runs
in the cloud with one extra output: Salem's hand events with times, each placed on his turns.

Games: the 27 that 6a found reliable. Each is not same-class, not partial, and has no turn-number warning: 20 兔子主教,
7 三轴土.

### Positions

One position per Salem own turn 1 to 5, at the start of that turn.

- **His hand.** The opening hand after the mulligan, plus his draws and created cards up to that point, minus what he
  played.
  - A card from the first four counts as kept when he later plays it with no second hand event of that card before.
    It counts as returned when a replacement count requires it.
  - A turn where any card in hand is uncertain is dropped and counted.
- **Boards.** Both sides' cards that entered play, at printed stats. Deaths and damage are unknown, so every follower
  is assumed alive. A turn where the opponent has a follower on board at its start is tagged 「可能有交换」, and is
  reported in its own column.
- **Decks.**
  - Salem's: the DFM list he plays for that archetype (兔子主教 dfm/HAVEN-ユーリ, 三轴土 dfm/RUNE-ユーリ), minus his
    known cards, in random order. This uses the external lists as a check only.
  - The opponent's: the tracker's archetype reference list for the opp_deck label, or that class's most common
    reference list when the label is 未知. Its hand is a count only.
  - Condition line on every result: 「对手卡表按套路参照表猜（牌序、手牌未知）」.

### The bot

- 三轴土: the DFM rune g5 value net with prior2 under PUCT, N 30, as in the round-2 gate. These are measurement models;
  this is a check, and they are not installed.
- 兔子主教: mcts:100+plan with the hand-set evaluator. No 主教 net exists, so this is the bot's weakest pilot and is
  reported as such.
- The bot plays its whole turn in the simulator, with the same seed per position.

### Comparison

- **Agreement:** the same multiset of cards played and the same evolve or super-evolve targets, ignoring attacks and
  order.
- **Secondary:** the same first card.
- The table for Salem lists every divergence with game, turn, hand, both boards, his play and the bot's play, plus an
  empty column for his verdict.

### Predictions

- The plan's: bot and Salem agree on fewer than 70% of the kept turns 〔0.6〕.
- The plan's: Salem marks at least 3 bot lines 「我绝对不会这么打」 〔0.8〕.
- Mine: the 三轴土 bot (trained net + prior) agrees more often than the 兔子主教 bot (hand-set evaluator) 〔0.6〕.

### Results (written after the run, 2026-11-02 12:5xZ; ledger F-17)

Code: `realgame_6b.py` rebuilds the positions and runs the bot; `realgame_6b_table.py` writes the table for Salem. The
table and the per-position results stay in /mnt/project-files/shadowverse/salem-games/realgame-6b-2026-11-02.md.

Deviations from the registration, all made before the full run was read:
- **Games.** 28 reliable games, not 27: after the tracker's re-parse, game 38 has no turn-number warning.
- **Mulligan.** No card-by-card rule could tell kept from returned cards. The replacements are found by timing: the
  cluster of Salem's hand events within 1 s of each other, before his first turn starts. The kept set is then any
  subset of the opening four that is consistent with the replacement count and with his later plays. A turn with more
  than one consistent hand is dropped.
- **Drawn and played at once.** When a card is played without having entered his hand, the reveal just before the
  play counts as the draw.
- **Decision time.** The position is taken just before his first action of the turn, not at the turn start, so the
  turn's draw is in hand.
- **Turns without plays.** A turn where he played nothing is dropped, since there is no line to compare.
- **Opponent list.** The reference list with the opp_deck label; otherwise the class's first list.
- **Replay.** Attacks are not replayed. Plays and evolves are replayed with random targets, so a follower can die to a
  replayed spell. A card the engine would not let him afford gets its PP forced, and forced PP, unplayable cards and
  skipped evolves are counted per position.
- **Seeds.** Seed bank 86300000 + 100 x game + turn, one bot run per position.
- **Agreement key.** A first version dropped created cards from the key. It was changed back to the registered rule:
  created cards count, and an alternate form counts as its base card. This moved agreement from 30/86 to 28/86.
- **Seen early.** Games 13 and 41 were looked at in a test run before the full run.

Counts:
- 140 turns in the 28 games. 86 were rebuilt. Dropped: 34 with more than one possible mulligan, 15 with no play, and 5
  in one game whose opening was not four cards.
- 19 games give at least one position: 63 兔子主教 positions and 23 三轴土 positions.
- Agreement: 28/86 (33%). 兔子主教 20/63 (32%), 三轴土 8/23 (35%).
- Agreement by turn: T1 2/14, T2 6/16, T3 12/18, T4 6/19, T5 2/19.
- Secondary measure (same first card): 33/86.
- The 58 divergences:
  - the bot plays different cards: 35;
  - the bot plays nothing: 9;
  - the bot plays a subset of his cards: 8;
  - the bot plays a superset: 4;
  - the same cards with a different evolve target: 2.
- Positions where the replay deviated (forced PP, unplayable card, skipped evolve): 7. One of them agrees.

The clearest pattern is on turn 1:
- The 兔子主教 bot (hand-set evaluator) passes 7 times where Salem plays the 1-cost 羽翼石像 or a crystallized 奇迹独角兔.
- In games 9, 17 and 26 the legal actions were listed: the 1-cost play is legal each time, and the bot picks EndTurn.
- So this is the evaluator's choice, not a simulator gap. A guess, not checked: the hand-set evaluator values a card in
  hand above a 1-cost amulet or crystal on board.
- The 三轴土 bot plays 解谜旋律 or 暴食的零嘴 on turn 1 where Salem plays 智慧光辉 (2 games).

Predictions:
- Agreement under 70% (0.6): TRUE, 33%.
- Salem marks at least 3 bot lines 「我绝对不会这么打」 (0.8): waits for his verdicts on sections 1 and 2 of the table
  (24 rows).
- The 三轴土 bot agrees more often than the 兔子主教 bot (0.6): TRUE by point estimate, 35% vs 32%. With 23 and 63
  positions this is well within noise, so it is not evidence for the trained net.

Limits:
- The opponent's list is a guess from the archetype reference. Salem's list is the DFM list, not necessarily his 40.
- Boards ignore combat, so from turn 2 on, positions with opponent followers can differ a lot from the real game. The
  table therefore asks for verdicts only on turn 1 and on clean turns, meaning no replay deviation and no opponent
  follower.
- The bot runs once per position, so a close choice can flip on the seed.

### Prediction 2 withdrawn (2026-11-02 23:35Z)

Salem declined to mark the table. His reason: he often can't judge the bot's choice in these positions, because his own
earlier turns already differ from what the bot would have played.
- The prediction (at least 3 rows marked 「我绝对不会这么打」) is withdrawn, not scored.
- My mistake: a standing rule from 2026-10-07 already said not to send him per-item tables to mark. Single decisions
  are not adjudicated, by him or by Claude; only aggregate statistics over rule-based categories count.

### Part 2: play both lines out (pre-registered 2026-11-02 23:5xZ, before any rollout is read)

The question changes from "would Salem play the bot's line" to this: in the same position, which set of cards wins more
when the same pilot plays the rest of the game?

**Method.** Script: `realgame_6b_roll.py`. For each of the 58 divergent positions, and for each of K = 40 seeds:
1. Rebuild the position with that seed. Salem's remaining deck order and the opponent's hidden cards change with it.
2. Branch "salem": force his cards and evolves in his order. Branch "bot": force the bot's cards and evolves from the
   6b run, in its order.
3. When a forced play has several modes or targets, take the one the hand-set evaluator scores best right after it.
4. The bot then attacks for Salem, with his hand, evolve points and bonus PP set aside, so neither branch adds cards.
5. Both sides finish the game with bots. Salem's side uses the 6b pilot for his deck. The opponent uses mcts:100+plan.

**Scoring.**
- A pair (same seed, both branches) scores Salem's result minus the bot's: +1, 0 or −1.
- Each position's score is the mean of its 40 pairs.
- Each category's score is the mean over its positions. Its standard error is computed over positions, not pairs.
- Seeds: 86400000 + 10000 × game + 1000 × turn + k, the range 86400000–86899999.

**Categories.** Fixed now, from the lines only, by turn (1, or 2 to 5) and by how the bot's cards and evolves relate
to Salem's:
- turn 1, the bot plays nothing: 7 positions;
- turn 1, different cards: 5;
- turns 2–5, the bot plays nothing: 2;
- turns 2–5, the bot plays a subset of his cards: 8;
- turns 2–5, the bot plays a superset: 4;
- turns 2–5, different cards: 32.

**Biases, stated before the run.**
- Both branches are continued by the bot. A line that needs Salem's plan on later turns is judged by how the bot
  follows it up, which favours the bot's own line.
- Targets and modes in Salem's line are the evaluator's choice, not his.
- Boards ignore combat before the position, and the opponent's list is a guess from the archetype reference.

**Predictions.**
- H1: in "turn 1, the bot plays nothing", Salem's line scores above 0, by more than 2 standard errors 〔0.7〕.
- H2: over all 58 positions, each weighted equally, Salem's line scores at least 0 〔0.65〕. The bias above points
  the other way. The prior for a pro list played by its expert pilot is strong.
- No prediction for the other categories. They are reported as they come.

**Meaning, fixed now.**
- H1 true: the hand-set evaluator's turn-1 pass is a measured blind spot. Turn-1 cheap plays become an acceptance
  category. Nothing is installed from this.
- H1 false: the pass is not shown to cost games under this pilot. It stays a divergence, not a defect.

### Part 2 results (written after the run, 2026-11-03 01:3xZ; ledger F-18)

All 58 positions x 40 pairs = 2320 pairs ran; none was skipped. The container restarted once at 2289 pairs, and the
script resumed from its output file. Summary script: `realgame_6b_roll_report.py`.

| Category | Positions | Salem's line wins | Bot's line wins | Difference (per position, ± SE) |
|---|---|---|---|---|
| Turn 1, the bot plays nothing | 7 | 81.1% | 72.5% | +0.086 ± 0.029 |
| Turn 1, different cards | 5 | 71.0% | 67.0% | +0.040 ± 0.024 |
| Turns 2–5, the bot plays nothing | 2 | 55.0% | 60.0% | −0.050 ± 0.125 |
| Turns 2–5, the bot plays a subset | 8 | 76.9% | 70.6% | +0.062 ± 0.077 |
| Turns 2–5, the bot plays a superset | 4 | 21.2% | 21.2% | +0.000 ± 0.060 |
| Turns 2–5, different cards | 32 | 66.1% | 66.8% | −0.007 ± 0.019 |
| All | 58 | | | +0.017 ± 0.016 |

Turns 2–5 together (46 positions): +0.004 ± 0.020. By deck: 兔子主教 +0.017 ± 0.020 (43), 三轴土 +0.017 ± 0.027 (15).

Forced lines that could not be played as recorded:
- In Salem's branch: a card in hand with no legal play 221 times, a skipped evolve 40 times. They sit in 7 turn-5
  positions, where his real turn had PP or a cost reduction the rebuilt position lacks. In game 26 turn 5, for
  example, his line was never playable.
- A card absent from hand 104 times. These are mostly tokens the breadcrumb logs as plays (三轴土).
- In the bot's branch: 16 unplayable cards and 48 skipped evolves, from seeds whose rebuilt board differs.
- Sensitivity check, chosen after seeing these counts: drop the 8 positions where at least 10% of pairs hit an
  unplayable card or a skipped evolve. All 50 then score +0.028 ± 0.017, and turn 1 is unchanged.

Predictions:
- H1 (turn 1, bot passes: Salem above 0 by more than 2 SE) (0.7): TRUE. +0.086 ± 0.029 is 3.0 SE.
- H2 (all 58: Salem at least 0) (0.65): TRUE as a point estimate, +0.017 ± 0.016. It is not a measured advantage.

Meaning, as fixed before the run:
- The 兔子主教 bot's turn-1 pass is a measured blind spot of the hand-set evaluator. The same pilot, playing the rest
  of the game, wins 8.6 points more after Salem's 1-cost play than after passing.
- Turn-1 cheap plays become an acceptance category. Nothing is installed from this.
- On turns 2–5 this method finds no difference. That does not show the bot chooses as well as Salem:
  - the bot continues both branches, which favours its own line;
  - the method compares only the cards played that turn.
  So the tool's reach ends at turn 1 here.

## 6c: opponent weighting (waits for 50 games)
