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

## 6b: decision divergence table (registered after 6a reports)

## 6c: opponent weighting (waits for 50 games)
