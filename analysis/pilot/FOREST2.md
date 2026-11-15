# A pilot for the bot's combo elf T3-FOREST-2 (written 2026-11-15 07:0xZ, before any of its games)

Why: the WGP comparison report (/mnt/project-files/shadowverse/wgpq-2026-11-14/wgpq-vs-bot-2026-11-15.md, section 7;
branch claude/wgpq-compare). The bot's pool already has combo elf (T3-FOREST-2 shares 32-33 cards with the 25
professional lists), but the hand-set ruler ranks it 16th of 19 (41%), and the hand-set bot plays it with one or two
three-card turns a game. Salem (11-15): the training loop is stuck in a local optimum. This line separates "the pilot
can't play it" from "the ruler is self-referential" on a deck the bot built itself; no external list is trained on.

Condition: 对手卡表已知（牌序、手牌未知）.

## Recipe (PRIOR-HAVEN.md, unchanged)

- Field analysis/pilot/fields/bot-frozen7-forest2.txt: bot-frozen7 with T3-FOREST-2 in place of T1-FOREST-1, so the
  opponents are the same six non-Forest decks every other bot pilot trained against, at mcts:100+plan.
- g1: 10 x 1000 self-play with mcts:100+plan, 2 x 1000 holdout; value net with the in-turn branch (train_mid
  --shared --fresh); time match, gate (300 pairs vs mcts:100+plan piloting the same list), equal-CPU rerun.
- g2, g3: the hero piloted by the previous net at its gate N, the net retrained fresh on all generations.
- Prior: setpolicy fit from the better of g2/g3, tau 0.5, ftz, 35 epochs; arm +puct=<prior>:2:1, gated the same way.
- New PC, E-cores, at most 12 processes, low priority: analysis/process/pilot_chain_win.py forest2 10.
- Seeds (the analysis line; requested 07:0xZ): bank 87240000-87299999 in the four new-PC pilots' layout.

## Acceptance (the report's standard) and the transfer test

- Acceptance: the pilot (its gated arm, native equal-CPU N) against the five bot decks with an installed pilot, each
  played by its own pilot (field forest2-vs-trained5.txt, herogate --opp-pilots), paired with the hand-set bot
  piloting the same list; 300 pairs. Pass: the pilot scores at least 50%.
- Transfer (measure only, never installed): the same pilot net and prior piloting the professional combo elf list,
  paired with the hand-set bot piloting that list, same opponents.

## Predictions

- (F1) g1 at equal CPU is within ±3 points of the hand-set bot, or below it: 0.7 (every bot pilot's g1 so far).
- (F2) The final arm (g2/g3 + prior) beats the hand-set bot on the training field by at least +15 points: 0.6.
- (F3) Acceptance: at least 50% against the five trained T1/T3 pilots: 0.3. The hand-set bot playing this list scores
  about 30% against untrained opponents (the report's reference table), and training the opponents takes 10-20 points
  off; 50% needs a gain like 三轴土's (5 -> 35).
- (F4) The acceptance score is at most 45%: 0.55. If so, the report says to look at the simulator and the card
  scripts (the combo count, 爱意天使's evidence, 橙醉's cost reduction) before blaming the loop.
- (F5) Transfer: the pilot on the professional list beats the hand-set bot on it by at least +10 points: 0.45.

## Results

(to come)
