# 规则裁定登记（R-xx 引擎规则，C-xx 卡牌细节）

2026-11-02 入库。来源：paper 线程的初稿（/mnt/project-files/shadowverse/process/rulings-draft.md）、docs/architecture.md 第 14 节、
set 10 审计、Salem 的裁定；每条的实现位置和测试由逐行核对代码得到（行号以本文件入库时的代码为准，改代码后以函数名为准）。

## 用法
1. 写卡或改引擎前先查这里。拿不准的地方在代码里标 `UNSURE`，在本文件登记为「未决」，再实现。
2. 两栏分开写：**依据**（已确认 = 官方文字、官方问答或 Salem 的裁定；推断 = 引擎按某种读法实现，没有权威依据；未决 = 还没决定）
   和 **钉住**（是 = 把读法反过来测试会挂；部分 = 只钉住一部分；否 = 没有测试）。钉住不是「是」的条目都在第 C 节的待补清单里。
3. 改裁定不改旧条目：写新条目，在旧条目「依据」后写「被 R-xx / C-xx 取代」。
4. 「未决」非空时，审计报告和门控报告顶部列出它（门控报告模板的「未决裁定」一行）。
5. Salem 的每条新裁定：当天登记，写日期、原话一句、编号。

## A. 引擎规则

| 编号 | 对象 | 现在的实现 | 依据 | 钉住 | 测试 |
|---|---|---|---|---|---|
| R-01 | 回合上限 | 全局回合数超过 `max_turns`（默认 60）判平局（engine.py:429-431，state.py:286） | 未决：初代第 40 回合双方判负，超凡世界未确认 | 部分 | tests/test_leaf_contract.py::test_the_last_turns_end_is_a_draw_and_the_one_before_is_not 只查搜索和引擎在上限处一致，断言只在平局时执行；60 这个值、平局还是双负都没测 |
| R-02 | 进化点、超进化点 | 开局各 2；回复封顶 2（effects.py:873、878）；解锁前回复的点也不能用（engine.py:227-229）；解锁回合先手己方第 5/7、后手第 4/6 回合（engine.py:27-28）；每回合用点进化 1 次 | 推断 | 部分 | tests/test_evolve.py::test_unlock_turns_first_and_second_player 钉住解锁回合；封顶 2、解锁前用回复的点：没有 |
| R-03 | 融合次数 | 每张带融合的牌每回合 1 次，不同的牌同回合可以各融合一次（engine.py:269、569） | 推断：英日文描述不一致 | 是 | tests/test_tournament_nemesis_t_a.py::test_isaac_congenial_engineer（同回合三张不同的牌融合，按「每回合 1 次」会挂） |
| R-04 | 0 点伤害与屏障 | 任何一次受伤事件都消耗屏障，包括 0 点（effects.py:167-169）；有些卡 X=0 时直接不造成伤害（诺克坦的审问 abyss.py:434，劫焰奇美拉 rune.py:590），屏障留着 | 推断：超进化随从 0 伤屏障消失的问答；「0 点伤害也算受到伤害」 | 部分 | tests/test_mechanics.py::test_barrier_is_used_up_by_any_damage_event 只测超进化随从；非超进化随从：没有 |
| R-05 | 随机效果与不能被选择的随从 | 随机效果从不过滤的列表里抽，能打到光环、潜行随从（neutral.py:106-108、abyss.py:154-156、sword.py:481-485）；过滤只用于指定目标 | 推断（光环有官方问答，光环和潜行共用 UNSELECTABLE） | 部分 | tests/test_cards_neutral.py::test_jailor_random_part_hits_aura_when_nothing_can_be_selected 只测光环；潜行：没有 |
| R-06 | 奥义的「当前回合数」 | 己方回合数（`turns_taken`）加计数，手牌里时己方进化也计入（effects.py:720、346-348） | 推断 | 是 | tests/test_mechanics.py::test_skybound_gauge_counts_turns_and_evolutions_in_hand（己方 8、全局 1）；另有艾云尼亚、希耶提、尤斯提斯、丘比丹各一个 |
| R-07 | 法术进入墓场的时机 | 效果结算完后墓场 +1，再算增幅（engine.py:453-455） | 推断 | 否 | 现有测试只查最终计数，两种时机结果一样 |
| R-08 | 护符每回合启动一次 | 每个护符实例每回合只能启动一次，所有护符都适用，不只证据护符（engine.py:255-256、553）；合并进场的新土之印护符同回合能再启动 | 推断：官方卡面没写；审计列为影响可能大 | 是 | tests/test_clue.py::test_with_two_clues_the_amulet_stays_after_one_engage；巴别隆城、魔法沉积、侵蚀世界的测试也钉住；合并后再启动只对土之印钉住（tests/test_cards_rune.py::test_witchs_new_brew_qa_engage_again_after_merging），证据护符没有 |
| R-09 | 证据合并算「消失」 | 新证据护符进场时先让已有的消失，再并证据，触发消失时效果（effects.py:500-505） | 推断：审计列为影响可能大，官方未确认 | 部分 | tests/test_clue.py::test_nacreheim_heals_when_banished_also_by_a_merge（涅格尔赫亚回复）、test_a_second_clue_amulet_banishes_the_first_and_takes_its_clues、tests/test_set10_engine.py::test_on_card_banished_fires_on_both_sides_for_followers_and_amulets_and_on_a_merge；诺克坦经合并召唤骷髅：没有 |
| R-10 | 劫焰奇美拉「割りふる」 | 从最早进场的敌方随从起，每只最多吃到剩余体力，余量打主战者（rune.py:590-591，effects.py:204-218） | 推断：官方可能逐点随机 | 是 | tests/test_cards_rune.py::test_infernal_chimera_splits_x_between_all_enemies_without_spending_sigils；tests/test_mechanics.py::test_split_damage_oldest_first |
| R-11 | 证据为 0 时护符 | 破坏，不算消失（effects.py:776-778，开关 CLUE_ZERO_DESTROYS） | **已确认**：Salem 2026-10-29「线索到0，证据会破坏」（初稿写的「参照土之印推测」已过时） | 是 | tests/test_clue.py::test_nacreheim_destroyed_at_zero_clues_does_not_heal、test_engage_draws_and_consumes_a_clue_and_the_amulet_goes_at_zero；tests/test_set10_engine.py::test_consume_clues_needs_enough_clues_like_earth_rite |
| R-12 | 重复获得同名纹章 | 不生效，已有的纹章不动、倒数不重置（effects.py:575-576） | 「不生效」**已确认**（官方问答，见 tests/test_ramp_dragon.py 注释）；「不重置倒数」推断 | 部分 | tests/test_rules_m1.py::test_leader_area_holds_one_of_each_and_at_most_five、tests/test_ramp_dragon.py::test_burnite_crest_punishes_the_opponent；不重置倒数、格莫瑞第二只：没有 |
| R-13 | 天噬抢劫犯的 PP 上限 +1 | 条件式：弃掉一张证据护符才 +1（dragon.py:543-545、623-624）。收集的显现没有 PP 上限效果，它的条件部分是「抽一张原始费用 5 以上的牌」（dragon.py:609-613），初稿把两张卡写在一起是错的 | 推断，置信 0.9：官方文本 32 个「if…, A. B.」块、斯洛士等三例证明分句仍是条件式；翻转实验：无条件会让 DFM 龙族 +12.5±2.7 | 是 | tests/test_set10_dragon.py::test_obliviationist_mugger_ramps_only_with_a_clue、test_collection_manifest_without_a_clue_only_damages |
| R-14 | 人灭三恶·兰佩吉的「最大体力减半」 | 向上取整（portal.py:615） | 推断，影响小 | 否 | 现有测试只减半 20，没测奇数 |

## B. 卡牌细节

| 编号 | 对象 | 结论 | 依据 | 钉住 | 测试 / 实现 |
|---|---|---|---|---|---|
| C-01 | 黄金时代 | 召唤的海盗旗不被这张黄金时代本身推进（使用卡牌时就入队） | Salem 10-05 | 是 | tests/test_rules_m1.py::test_reactions_are_queued_when_the_card_is_played；tests/test_tournament_pirate_t.py::test_lage_dor |
| C-02 | 伊德梅塔 | 进化时信仰不足 5：什么都不发生，不扣信仰 | Salem 10-05 | 是 | tests/test_pirate_sword.py::test_yidmetra_evolve_without_five_faith_does_nothing |
| C-03 | 伊德梅塔 ×2 | 两张都进化，增益叠加；触发的那张自己也吃到 | Salem 10-05 | 是 | tests/test_pirate_sword.py::test_yidmetra_buff_abilities_stack、test_faith_buff_includes_the_enhanced_follower_itself |
| C-04 | 斯洛士纹章 | 吟唱归零那回合回合开始照样发动，3 回合发动 3 次。引擎现在自己在归零时排入回合开始效果（engine.py:390-395），不再靠谢幕曲（初稿和 docs/architecture.md 6.6 节的近似表已过时） | Salem 10-05 | 是 | tests/test_cards_portal.py::test_slaus_crest_activates_each_bad_ability_once；tests/test_tournament_nemesis_t_a.py::test_slaus_revolving_wheel_of_fortune；tests/test_set10_engine.py::test_a_countdown_cards_start_of_turn_ability_also_activates_when_the_count_reaches_zero |
| C-05 | 大游戏世界 | 自己也算「战场上原始费用为 X 的其他卡牌」 | Salem 10-05 | 是 | tests/test_tournament_nemesis_t_b.py::test_world_of_games；tests/test_tournament_elf_t.py::test_world_of_games |
| C-06 | 森林陷阱 | 目标在结算前离场或不会被破坏时，陷阱自己照样破坏（forest.py:469-475） | Salem 10-05 | 否 | 现有测试只有正常情况和「多只只打第一只」 |
| C-07 | 圣德芬 | 瞬念召唤后被森林陷阱破坏，仍获得纹章 | Salem 10-05 | 是 | tests/test_cards_neutral.py::test_sandalphon_destroyed_by_trap_in_the_woods_still_gives_its_crest |
| C-08 | 阿兹弗特等「从本局被破坏的卡里随机挑」 | 被破坏次数越多越容易被选中（每次破坏记一条，effects.py:446） | Salem 10-05 | 部分 | 阿兹弗特：tests/test_cards_neutral.py::test_azvaldt_favours_names_destroyed_more_often；崇高的天书、康蒂玛、吉尔克、Aika：没有 |
| C-09 | 拉拉安瑟姆 | 进化时没有敌方随从可选，仍进行土之秘术 | Salem 10-05 | 是 | tests/test_cards_rune.py::test_lilanthim_evolve_performs_earth_rite_without_a_target |
| C-10a | 巴别隆城 | 空手启动仍推迟吟唱（neutral.py:453） | Salem 10-05 确认按原实现 | 否 | 现有测试每次启动都弃了一张手牌 |
| C-10b | 进化的 +2/+2 | 算增益，触发露芙蕾、蒂亚这类「被增益时」（effects.py:341） | 同上 | 否 | 露芙蕾、蒂亚的测试只用直接增益和爆能强化触发 |
| C-10c | 慈惠的心腹 | 自己进化也算 | 同上 | 是 | tests/test_cards_forest.py::test_merciful_attendant_heals_on_every_allied_evolution |
| C-10d | 丘比丹 | ≥15 时两种奥义都发动 | 同上 | 是 | tests/test_cards_forest.py::test_cupitan_super_skybound_also_hits_the_leader |
| C-10e | 卡婕 | 每回合一次，没有目标也用掉（sword.py:817） | 同上 | 否 | 现有测试总有敌方随从 |
| C-10f | 卡特斯罗特纹章 | 每回合一次，只在真的进化时用掉（portal.py:385-386） | 同上 | 否（已进化或已离场的情况） | 现有测试只钉住「法术不消耗」 |
| C-10g | 罗德诺艾尔四世 | 爆能强化两档叠加 | 同上 | 是 | tests/test_cards_sword.py::test_noel_iv_enhance_tiers |
| C-10h | 希耶提 | 奥义进化含自己 | 同上 | 是 | tests/test_cards_sword.py::test_seofon_skybound_art |
| C-10i | 骁勇骑士 | 「最左」= 最早登场 | 同上 | 是 | tests/test_cards_sword.py::test_knightly_ardor_attack_twice_goes_to_the_leftmost_swordcraft_follower |
| C-10j | 琳库露 | 可以把对面最大体力降到 0（rune.py:368） | 同上 | 否 | 现有测试只测 20 → 18 |
| C-10k | 赛菲 | 满场融合仍扣 2 PP（rune.py:714-716） | 同上 | 否 | 现有测试没有满场 |
| C-10l | 波摇花的裁决 | X = 被销毁那张牌的费用（dragon.py:1116） | 同上 | 否（满手销毁的情况） | 现有测试只测正常抽牌 |
| C-10m | 伊斯坦戴德的纹章 | 己方破坏没成功也照样破坏敌方（abyss.py:257-260） | 同上 | 否 | 现有测试没有不会被破坏的己方卡 |
| C-10n | 莉迪耶尔 | 自伤在模式效果之后（haven.py:832） | 同上 | 否 | tests/test_cards_haven.py::test_zoe_modes_self_damage_and_crest 两种顺序都过 |
| C-10o | 审理的守卫 | 按英文：屏障在「三个护符」条件之内 | 同上 | 是 | tests/test_cards_haven.py::test_deacon_of_security |
| C-10p | 天书深渊 | 按英文：加入手牌在「己方护符」条件之内 | 同上 | 是 | tests/test_cards_haven.py::test_depths_of_the_eld_tome |
| C-10q | 艾尔拉德的纹章 | 按英文：回复在「原始费用 6」条件之内 | 同上 | 是 | tests/test_cards_haven.py::test_erralde_fanfare_evolve_and_crest |
| C-10r | 索菲娜 | 沿用拉姆蕾达的问答（回合结束时已进化就不打） | 同上 | 部分 | 只有共用基类的 tests/test_cards_haven.py::test_lamretta_evolved_by_galleon_at_end_of_turn_deals_no_damage；索菲娜本身：没有 |
| C-10s | 回复 0 点 | 也触发「回复时」 | 同上 | 是 | tests/test_ramp_dragon.py::test_burnite_crest_triggers_on_zero_restoration |
| C-10t | 锻磨保镖 | 没目标也回复 | 同上 | 是 | tests/test_tournament_nemesis_t_b.py::test_ironwork_bodyguard |
| C-10u | 尤斯提斯 | 没有其他随从时自己照样进化 | 同上 | 是 | tests/test_cards_portal.py::test_eustace |
| C-11 | 钢铁的小憩 | 增幅不到 5 时不回复 PP，也不回血（rune.py:829-831） | Salem 10-31 22:01Z，置信 0.9 | 是 | tests/test_cards_rune.py::test_amethysts_naptime_threshold |
| C-12 | set 10 全部 46 张 | 费用、身材、关键字、倒数、证据特性、生成的卡都和官方一致 | 审计（对照官方中英日文） | 是 | tests/test_set10_engine.py 等 |

## C. 待补测试（每条一个最小用例，把现在的读法钉住，以后改裁定时测试会报警）

按影响排序（前四条可能改变对局，后面的影响小）：
1. R-02 回复封顶 2、解锁前不能用回复的点。
2. R-09 诺克坦经证据合并召唤骷髅。
3. R-08 证据护符合并进场后同回合能否再启动（现在只对土之印钉住）。
4. R-07 法术进墓场在结算之后（找一张结算中读墓场数的法术）。
5. R-01 把「超过上限判平局」和上限值本身钉住。
6. R-04 非超进化随从吃 0 点伤害丢屏障；R-05 随机效果打到潜行随从。
7. R-12 第二个同名纹章不重置倒数；R-14 奇数最大体力减半取整。
8. C-06、C-10a、C-10b、C-10e、C-10f、C-10j、C-10k、C-10l、C-10m、C-10n、C-10r（索菲娜本身）、C-08 的其余四张卡。

## D. 被取代或更正的初稿内容
- 初稿 R-11 的依据（「参照土之印推测」）：已由 Salem 10-29 的裁定取代，见 R-11。
- 初稿 R-13 把收集的显现也写成「PP 上限 +1」：错，见 R-13。
- 初稿 C-04 的「引擎用谢幕曲完成最后一次」：已过时，见 C-04；docs/architecture.md 6.6 节的近似表同样过时，待改。
- 初稿 R-03 的测试路径少了 `tests/`。
