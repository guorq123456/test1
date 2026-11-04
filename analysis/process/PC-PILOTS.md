# Four more bot heroes get a trained pilot, on Salem's new PC (registered 2026-11-04 ~15:20Z, before any gate result)

Salem, 2026-11-04 15:10Z (relayed by the coordinator): 「现在先全核启动开跑吧」, all cores of the new PC while he is
in class. The architecture thread chose this job: the four bot heroes that have no trained pilot yet, the 主教 hero's
recipe (analysis/pilot/PRIOR-HAVEN.md on the builder line, commit 5b66f4fd), one generation per hero first.

| hero | run name | seed bank (analysis/seed-banks.md, 46f603d on ccr-da4857cc-rkpgwr) |
|---|---|---|
| bot/T1-FOREST-1 (精灵) | pilot-forest-bot-g1 | 86960000-87019999 |
| bot/T1-SWORD-1 (皇家护卫) | pilot-sword-bot-g1 | 87020000-87079999 |
| bot/T3-DRAGON-1 (龙族) | pilot-dragon-bot-g1 | 87080000-87139999 |
| bot/T1-ABYSS-1 (梦魇) | pilot-abyss-bot-g1 | 87140000-87199999 |

- **Recipe (g1).** Field `analysis/pilot/fields/bot-frozen7.txt`; 10 x 1000 self-play games, mcts:100+plan both
  sides, stride 2, from the bank's base; holdout 2 x 1000 from base + 1000; scaledata encode + midrows encode;
  `train_mid.py --shared --fresh`; time match 24 pairs from base + 2900; gate 300 pairs from base + 2000 (the
  confirmation deals) against mcts:100+plan; an equal-CPU rerun at round(N / ratio) when the in-gate ratio is over
  1.08. Driver: `analysis/process/pilot_gen_win.py` (resumable; run from the repo root), the Windows port of the builder's pilot-gen.sh.
- **Machine.** New PC, 4 jobs x 6 workers, below-normal priority, BLAS on one thread. CPU ratios are measured while
  the four jobs share the machine; X and the baseline play in the same pool, so the ratio stays paired.
- **Later generations.** g2 and g3 (driver `analysis/process/pilot_next_win.py DECK GEN WORKERS`) follow whatever g1 shows (the corrected rule, analysis/pilot/README.md: every
  hero's g1 so far lost or tied), each in the next 3000 seeds of its bank, the layout of PRIOR-HAVEN.md.

## Predictions (before any gate result)

The precedents at g1, equal CPU: 巫师 (rune bot) −7.3, Portal bot −6.5, DFM Portal −5.7, 主教 +0.7.

- (P1) For at least 3 of the 4 heroes, g1's paired difference at equal CPU lies between −10 and +5 points: 0.7.
- (P2) At least 2 of the 4 are below 0 at equal CPU: 0.6.
- (P3) None of the 4 has its 95% interval wholly above 0 at equal CPU: 0.7.

No conclusion about a deck's strength is drawn from g1. Nothing is installed in the bot or the trainer page without
Salem's word.

## Result, g1 (reported by the new PC's RC thread 2026-11-04 17:59Z; all four ended 17:35-17:46Z)

300 pairs on each deck's confirmation deals (base + 2000), X = mcts:N+plan+setnet=net-pilot-DECK-bot-g1+netmid+netany,
baseline mcts:100+plan, opponents the field's six other bot decks at mcts:100+plan. ± is the 95% half-width.

| hero | time match ratio -> N | gate at N: X / baseline, paired (in-gate ratio) | equal CPU N: X, paired (ratio) |
|---|---|---|---|
| 精灵 bot/T1-FOREST-1 | 1.433 -> 70 | 42.5% / 43.8%, −1.3 ± 4.9 (1.214) | 58: 43.5%, **−0.3 ± 4.7** (1.082) |
| 皇家护卫 bot/T1-SWORD-1 | 1.295 -> 77 | 53.5% / 64.0%, −10.5 ± 4.6 (1.186) | 65: 52.8%, **−11.2 ± 4.7** (1.058) |
| 龙族 bot/T3-DRAGON-1 | 1.430 -> 70 | 29.5% / 37.5%, −8.0 ± 4.6 (1.197) | 58: 29.2%, **−8.3 ± 4.6** (1.056) |
| 梦魇 bot/T1-ABYSS-1 | 1.320 -> 76 | 55.0% / 57.2%, −2.2 ± 4.4 (1.198) | 63: 54.5%, **−2.7 ± 4.8** (1.078) |

Self-play 10 shards and holdout 2 shards complete for all four. Seeds used exactly as registered (base, +1000,
+2000, +2900).

- P1 (at least 3 of 4 between −10 and +5 at equal CPU; 0.7): **TRUE**, 3 of 4 (皇家护卫 −11.2 is out).
- P2 (at least 2 of 4 below 0; 0.6): **TRUE**, all 4.
- P3 (none with its 95% interval wholly above 0; 0.7): **TRUE**; 皇家护卫 and 龙族 have theirs wholly below 0.

Reading: the usual g1 picture (rune bot −7.3, Portal bot −6.5, DFM Portal −5.7, 主教 +0.7); 皇家护卫 −11.2 is the
worst g1 so far, about one standard error beyond the rune hero's. g2 follows (the corrected rule). A pipeline check
runs alongside: the training logs' best epoch and validation loss, the self-play hero score. If 皇家护卫's net did
not learn (best epoch 1, or validation loss flat), its g2 stops; the others go on.

Pipeline check (RC thread, 18:05Z, read-only): every net learned. Fresh, shared, patience 4; validation log loss at
the first epoch → the best: 精灵 0.587 → 0.556 (epoch 6 of 10), 皇家护卫 0.562 → 0.523 (epoch 9 of 13), 龙族 0.538 →
0.503 (epoch 6 of 10), 梦魇 0.568 → 0.532 (epoch 4 of 8). So 皇家护卫's g1 loss is not a training failure; all four
go on to g2. By opponent at equal CPU the largest drops: 皇家护卫 vs 梦魇 −24 and vs 主教 −19, 龙族 vs 精灵 −21,
精灵 vs 梦魇 −15 (± 10-13 each). The self-play logs do not print the hero's score.

## Result, g2 (RC thread 2026-11-04 22:13Z, relayed by the coordinator; started 18:03Z on all 24 cores, Salem's word 18:01Z)

g2 ended 19:16-19:40Z. 300 pairs on each deck's g2 confirmation deals (base + 4000); ± is the 95% half-width. The
hero self-played as mcts:<g1's gate N> + net g1 (70, 77, 70, 76); the net is fresh on g1 + g2 with g1's holdout.

| hero | net: valid log loss epoch 1 → best | time match ratio -> N | gate at N: X / baseline, paired (ratio) | equal CPU N: X, paired (ratio) |
|---|---|---|---|---|
| 精灵 | 0.564 → 0.538 (epoch 10 of 14) | 1.500 -> 67 | 51.3% / 44.3%, +7.0 ± 4.4 (1.152) | 58: 50.2%, **+5.8 ± 4.5** (1.058) |
| 皇家护卫 | 0.529 → 0.502 (epoch 17 of 21) | 1.264 -> 79 | 72.3% / 66.0%, +6.3 ± 4.2 (1.223) | 65: 69.0%, **+3.0 ± 4.2** (1.074) |
| 龙族 | 0.522 → 0.492 (epoch 9 of 13) | 1.348 -> 74 | 50.7% / 38.7%, +12.0 ± 4.3 (1.249) | 59: 50.5%, **+11.8 ± 4.5** (1.114) |
| 梦魇 | 0.546 → 0.523 (epoch 8 of 12) | 1.620 -> 62 | 67.8% / 59.0%, +8.8 ± 4.7 (1.194) | 52: 69.3%, **+10.3 ± 4.6** (1.083) |

- Route at equal CPU, g1 → g2: 精灵 −0.3 → +5.8, 皇家护卫 −11.2 → +3.0, 龙族 −8.3 → +11.8, 梦魇 −2.7 → +10.3. Three of
  four have their intervals wholly above 0; 皇家护卫's reaches below 0. Each generation is gated on its own deals, so
  the step g1 → g2 is not a paired difference.
- 龙族's equal-CPU row still uses 11% more CPU than the baseline (ratio 1.114; the script reruns once). Its gate at N
  74 (ratio 1.249) gave +12.0, the rerun at 59 gave +11.8, so the gain does not come from the extra CPU.
- By opponent at equal CPU, the largest: 龙族 vs 主教 +22 and vs 精灵 +18; 梦魇 vs 龙族 +20; 精灵 vs 龙族 +19
  (± 10-12 each). The five drops are all small and within their errors (the largest: 精灵 vs 梦魇 −6).

g3 started 22:11:49Z (the same script, GEN 3; seeds base + 5000 / + 6000 / + 6900; hero N 67, 79, 74, 62 from g2's gate) on the usual cap: 12
processes on E-cores only, Salem's class time being over.
