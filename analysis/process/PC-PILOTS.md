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
- **Later generations.** g2 and g3 follow whatever g1 shows (the corrected rule, analysis/pilot/README.md: every
  hero's g1 so far lost or tied), each in the next 3000 seeds of its bank, the layout of PRIOR-HAVEN.md.

## Predictions (before any gate result)

The precedents at g1, equal CPU: 巫师 (rune bot) −7.3, Portal bot −6.5, DFM Portal −5.7, 主教 +0.7.

- (P1) For at least 3 of the 4 heroes, g1's paired difference at equal CPU lies between −10 and +5 points: 0.7.
- (P2) At least 2 of the 4 are below 0 at equal CPU: 0.6.
- (P3) None of the 4 has its 95% interval wholly above 0 at equal CPU: 0.7.

No conclusion about a deck's strength is drawn from g1. Nothing is installed in the bot or the trainer page without
Salem's word.
