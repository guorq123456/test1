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

## 6b: decision divergence table (registered after 6a reports)

## 6c: opponent weighting (waits for 50 games)
