# Haven hero: a trained pilot for bot/T1-HAVEN-1 (pre-registered 2026-11-03 ~01:30Z, before any game)

Condition: 对手卡表已知（牌序、手牌未知）.

## Why

The architecture thread asked for this on 2026-11-03 01:21Z, citing F-18. In Salem's real game 6b, continued from
the same position, the bunny bishop bot (hand-set evaluation, no net) passed turn 1 seven times. Played on by the
same bot, passing there won 8.6 points less than playing a 1-cost card first. Haven is the weakest T1 craft, and
the only one whose pilot has not been trained yet.

Only the bot's own list is trained. DFM's 兔子教 (dfm/HAVEN-ユーリ) is not: among the external lists, only 三轴土
has Salem's isolated-training exception. Nothing is installed; this line only reports numbers.

## Recipe (the rune and Portal heroes' own, analysis/pilot/README.md, PRIOR.md, ROUND2.md, PRIOR-PORTAL.md)

- **Field.** `analysis/pilot/fields/bot-frozen7.txt`. Hero bot/T1-HAVEN-1 against the field's 6 other bot decks.
  The baseline and every opponent are mcts:100+plan, the hand-set bot without a net.
- **Generations.**
  - g1: 10 x 1000 self-play games with mcts:100+plan on both sides, plus a 2 x 1000 holdout.
  - gN (N ≥ 2): 10 x 1000 games with the hero piloted by mcts:<g(N-1)'s gate N> + net g(N-1). Then
    `train_mid --shared --fresh` on gens 1..N gives `net-pilot-haven-bot-gN`.
- **Each generation's gate.**
  - Time match once, 24 pairs: N = round(100 / ratio) unless the ratio is within 0.97-1.03.
  - Then 300 pairs against mcts:100+plan on the same deals.
  - Then an equal-CPU rerun at round(N / in-gate ratio) when that ratio is over 1.08.
- **Prior** (after g3 is gated).
  - Init: the better of g2 and g3 on the same deals; g3 if g3 − g2 ≥ 0.
  - Data: the hero's decisions in the gen-2 and gen-3 self-play (`setpolicy_named.py`).
  - Fit `--tau 0.5 --ftz --epochs 35`, which gives `prior-pilot-haven-bot-ft-t05`.
  - Arm: `+puct=<prior>:2:1`, time-matched, gated on g3's bank, with an equal-CPU rerun. It is paired with the chosen
    net's own equal-CPU row on the same deals.
- **Confirmation.** A conclusion stands only on the fixed confirmation bank (`herogate --bank confirm`): the gate
  banks, not the timing banks.
- **Seeds.** As allocated by the analysis session; none chosen here. They are written below when they arrive.

## Predictions (before any game)

- (H1) g3 at equal CPU beats the hand-set bot without a net (mcts:100+plan piloting the same list) by at least +5
  points, on g3's confirmation deals: 0.7 (the architecture thread's).
- (H2) g3 + prior at equal CPU beats g3 by at least +5 points more, on the same deals: 0.6 (the architecture
  thread's).
- (H3, mine) g1 is below the baseline (paired difference < 0): 0.7. Every hero's g1 so far lost: rune bot −7.3, DFM
  Portal −5.7, bot Portal −6.5.
- (H4, mine) The baseline (the hand-set bot) scores under 50% against the other six bot decks on g1's gate bank:
  0.75. Haven is the weakest T1 craft.

## Seeds

Bank 86900000-86959999 was allocated by the analysis session (ef44d23 on ccr-da4857cc-rkpgwr,
analysis/seed-banks.md). The split is decided here, before any game; nothing outside the bank is used.

| step | self-play (10 x 1000, stride 2) | holdout (2 x 1000) | gate (300 pairs, confirmation) | time match (24 pairs, selection) |
|---|---|---|---|---|
| g1 | 86900000 | 86901000 | 86902000 | 86902900 |
| g2 | 86903000 | - | 86904000 | 86904900 |
| g3 | 86905000 | - | 86906000 | 86906900 |
| prior | - | - | 86906000 (g3's deals) | 86909800 |

- g2 on g3's deals, which decides the prior's init, uses g3's bank 86906000.
- Spare for a gen 4 or a rerun: 86910000-86959999. It is reported back to the analysis session as used.

## Results (written after the runs)

| generation | gate N (ratio) | paired | equal CPU N (ratio) | paired at equal CPU | X / baseline at equal CPU |
|---|---|---|---|---|---|
| g1 | 55 (1.261) | +2.3 ± 4.4 | 44 (1.090) | +0.7 ± 4.6 | 46.7% / 46.0% |
| g2 | 53 (1.180) | +6.5 ± 4.8 | 45 (1.062) | +3.7 ± 4.9 | 52.0% / 48.3% |
| g3 | 55 (1.208) | +14.0 ± 4.7 | 46 (1.108) | **+12.5 ± 4.9** | 61.3% / 48.8% |

**g1** (records `data/haven-bot/`, logs `logs/haven-bot/`):
- Self-play: 10 x 1000 from 86900000, both sides mcts:100+plan, 2.2 CPU s a game. The hero scored 48.6% (holdout
  48.6%).
- Net: `net-pilot-haven-bot-g1`, trained fresh, best epoch 7 of 11. Valid brier 0.187, log loss 0.549. Stamped with
  the rules hash (provenance, current).
- Time match (86902900): ratio 1.813 → N 55.
- Gate (confirmation bank 86902000): X 48.3% ± 4.0%, baseline 46.0% ± 4.2%, paired **+2.3 ± 4.4** (95% −2.1 to
  +6.7). Ratio 1.261.
- Equal CPU (N 44): X 46.7%, paired **+0.7 ± 4.6** (95% −4.0 to +5.3). Ratio 1.090, still a little over 1.08; one
  rerun per generation, as the rule says.
  - By opponent: Abyss +10, Dragon 0, Rune +2, Portal +2, Forest −4, Sword −6.
- Predictions:
  - H3 (g1 below the baseline, paired < 0; 0.7): **FALSE**. +0.7 at equal CPU and +2.3 at N 55, both intervals
    around 0. This is the first hero whose g1 did not lose.
  - H4 (baseline under 50% on g1's bank; 0.75): **TRUE**, 46.0%.

**g2** (records `data/haven-bot/rec-g2/`):
- Self-play: 10 x 1000 from 86903000, the hero piloted by mcts:55 + net g1 (g1's gate N). The hero scored 47.3%.
- Net: `net-pilot-haven-bot-g2`, trained fresh on gens 1-2. Chunk 1's deadline came during training at epoch 3;
  chunk 2 resumed from the checkpoint. Best epoch 8 of 12: valid brier 0.184, log loss 0.541.
- Time match (86904900): ratio 1.898 → N 53.
- Gate (confirmation bank 86904000): X 54.8% ± 4.1%, baseline 48.3% ± 4.3%, paired **+6.5 ± 4.8** (95% +1.7 to
  +11.3). Ratio 1.180.
  - By opponent: Portal +16, Abyss +12, Sword +8, Rune +3, Dragon +2, Forest −2.
- Equal CPU (N 45): X 52.0%, paired **+3.7 ± 4.9** (95% −1.3 to +8.6). Ratio 1.062.
  - By opponent: Portal +12, Sword +4, Dragon +4, Forest +2, Rune 0, Abyss 0.

**g3** (records `data/haven-bot/rec-g3/`):
- Self-play: 10 x 1000 from 86905000, the hero piloted by mcts:53 + net g2, 2.8 CPU s a game; two chunks. The hero
  scored 54.0% (g2 47.3%, g1 48.6%).
- Net: `net-pilot-haven-bot-g3`, trained fresh on gens 1-3. Best epoch 17 of 21: valid brier 0.179, log loss 0.527.
- Time match (86906900): ratio 1.818 → N 55.
- Gate (confirmation bank 86906000): X 62.8% ± 4.0%, baseline 48.8% ± 4.1%, paired **+14.0 ± 4.7** (95% +9.3 to
  +18.7). Ratio 1.208.
  - By opponent: Portal +21, Forest +19, Rune +13, Dragon +13, Sword +11, Abyss +7. Above the baseline against all
    six.
- **Equal CPU** (N 46; the rerun ran into chunk 2's deadline at 51 pairs and was finished from its jsonl in chunk
  3): X 61.3% ± 3.9%, paired **+12.5 ± 4.9** (95% +7.6 to +17.4). Ratio 1.108.
  - By opponent: Forest +20, Sword +15, Rune +15, Portal +10, Abyss +8, Dragon +7.
- **H1** (g3 at equal CPU ≥ +5 over the hand-set bot; 0.7): **TRUE**. +12.5, and the whole 95% interval is above +5.
- Route at equal CPU: g1 +0.7, g2 +3.7, g3 +12.5.

**Prior** (logs `runs/pilot-haven-bot/logs/`, the prior's own section below when gated):
- Init. g2 on g3's confirmation deals (86906000) at g3's equal-CPU N 46: X 51.5% ± 4.0%, paired with the baseline
  +2.7 ± 4.5 (95% −1.9 to +7.2), ratio 1.097. Paired with g3's equal-CPU row on the same deals: g3 − g2 = **+9.8 ±
  4.4**, so the init is **g3**.
- Data: the hero's decisions in the gen-2 and gen-3 self-play (20 shards, `setpolicy_named.py encode`).
- Fit from g3, `--tau 0.5 --ftz --epochs 35`. Chunk 1's deadline came at epoch 30 (valid ce 1.32506, best);
  chunk 2 resumed from the checkpoint. Done at epoch 35: train ce 1.31276, valid ce 1.32504 (best epoch 34). Model
  `prior-pilot-haven-bot-ft-t05`, stamped with the rules hash (provenance, current). Log
  `logs/haven-bot/prior-haven-bot.log`.
