# Salem 10 局面补全（2026-10-08 13:25Z）

`render.py` 把分析线 `analysis/ramp-benchmark/salem_games_shallow_deep_results.jsonl`（source = salem27）里 `picks.txt` 列的 10 个局面（对局号 + 动作下标）从 `analysis/mirror-regression/salem_games.json` 的存档逐步回放到那一步，写出给 Salem 判断的文件。

```
python3 render.py <scratch> <out.md>
# <scratch>/builder = 建造线 e434e24 的仓库（svsim），<scratch>/analyst/analysis/{mirror-regression,ramp-benchmark} = 分析线 643b83b 的两个目录
```

补的信息：整局回合数、先后手、双方 PP 与后手额外 PP、双方剩余进化点 / 超进化点、双方此前每回合的出牌 / 进化 / 攻击、墓地 / 手牌 / 牌库张数、场上随从攻血与状态、行动方全部手牌。非行动方手牌不列（bot 决策时看不到）。牌名按 card-glossary.md（glossary.py 的 COMMON）；加速形态 / 强化按 `svsim.core.engine.play_form`。
