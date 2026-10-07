"""Build cross_turn.json: the positions where Salem's turn differs from the bots'
for a reason that only shows after this turn (the cross-turn planner's probe set).

    python3 build_cross_turn.py positions.json TURNS_JSONL > cross_turn.json

TURNS_JSONL is analysis/cross-turn/play_turns.py's output (every turn of
Salem's 10 games, with v2 and v2s playing the same starts). The positions and
their reasons are chosen by hand below, from reading every turn side by side;
the file adds each position's start, Salem's turn and the bots' most common
turn. Checks use check.py's conditions (all of a check's conditions must hold).
"""
import json
import sys
from collections import Counter

ERNTZ, BURNITE, RED = "约束的《正义》·伊兰翠", "焦灰的安纳提玛·班德奈特", "赤流"
VORLALAI, ZOOEY = "古旧天刀·波菈莱", "世界的伙伴·佐伊"
BOTS = {"v2": "mcts:100+plan+learned+phased", "v2s": "mcts:200+plan+learned+phased"}

# (game, own turn, category, check, confidence, why it takes more than this turn to see)
# confidence: 高 / 中; "看局面" for the turn-1 bonus PP: Salem says spending it on turn 1 is
# sometimes better (six games are too few), so those four are observed, not required; "belief"
# for a choice that rests on what the opponent is believed to hold (not counted either).
PROBES = [
    # --- the bonus PP: second player's own turn 1 (observed, not required) ----------------
    ("1791305347029", 1, "bonus_keep", {"keeps_bonus": True}, "看局面",
     "额外 PP 在自己第 6 回合前只能用一次。Salem 留到第 2 回合，2+1 PP 打 3 费的龙之启示，提前一回合跳费。"
     "bot 第 1 回合用掉额外 PP 打琪米卡，还把龙之启示弃了：第 2 回合既没额外 PP，也没有跳费牌。"),
    ("1791305539194", 1, "bonus_keep", {"keeps_bonus": True}, "看局面",
     "同上：Salem 第 2 回合用额外 PP 打璐米欧儿加速（3 费，+1 PP 上限）。bot 第 1 回合用额外 PP 下龙人，第 2 回合就跳不了费。"),
    ("1791306497426", 1, "bonus_keep", {"keeps_bonus": True}, "看局面",
     "同上：Salem 第 2 回合额外 PP + 龙之启示。bot 第 1 回合用额外 PP 打琪米卡，弃掉一张璐米欧儿。"),
    ("1791306781701", 1, "bonus_keep", {"keeps_bonus": True}, "看局面",
     "Salem 第 1 回合不用额外 PP（第 2 回合打了琪米卡，第 3 回合用 3 PP 打璐米欧儿加速，额外 PP 一直留着）。"
     "bot 第 1 回合用额外 PP 打琪米卡。代价要到第 2、3 回合才看得见。"),
    # --- ramp now, the payoff comes later ---------------------------------------------------
    ("1791304981889", 4, "ramp_first", {"ramps": True}, "高",
     "先手第 4 回合 5 PP：Salem 打龙之启示（+1 上限，剩 2 PP，手里的波菈莱不下）。"
     "bot 打《世界》的呈现（抽 2，破坏对面 0/2 的波菈莱），PP 用满但不跳费。跳费的回报在之后每个回合。"),
    ("1791305347029", 3, "ramp_first", {"ramps": True}, "高",
     "后手第 3 回合 4 PP：Salem 打璐米欧儿加速（+1 上限，剩 1 PP）。bot 打琪米卡（弃波菈莱）+ 龙人，PP 用满但不跳费。"),
    ("1791306781701", 3, "ramp_first", {"ramps": True}, "高",
     "后手第 3 回合 3 PP：Salem 打璐米欧儿加速，额外 PP 继续留着。bot 用额外 PP 打强化龙人（3 个 2/1），不跳费。"),
    ("1791306269709", 5, "ramp_first", {"ramps": True}, "中",
     "后手第 5 回合 8 PP，对面诺玛 7/8：Salem 用《世界》的呈现破坏诺玛并抽 2，再打龙之启示到 9 上限，下回合 10 PP 超进化伊兰翠。"
     "v2s 用相枛津 + 赤流（把《世界》的呈现弃了）解诺玛，不跳费；v2 打波摇花 +《世界》的呈现，剩 1 PP。"),
    # --- keep a card for a later turn -------------------------------------------------------
    ("1791304981889", 2, "keep_card", {"never_plays": [VORLALAI]}, "中",
     "波菈莱被弃时会召唤一张自己，进化拿 1 张深渊，超进化拿 3 张。Salem 把它留在手里，"
     "等琪米卡、相枛津、赤流、璐米欧儿弃牌时免费上场；先手第 2 回合宁可空过。bot 直接花 2 PP 下。"),
    ("1791306333962", 2, "keep_card", {"never_plays": [VORLALAI]}, "中",
     "同上：两张 2 费里 Salem 下龙人，留波菈莱当以后的弃牌。bot 下波菈莱。"),
    ("1791304981889", 6, "keep_card", {"never_discards": [ERNTZ, BURNITE]}, "中",
     "先手第 6 回合 8 PP，对面相枛津 7/4：Salem 用露莉亚和龙人解掉它，再打璐米欧儿加速，两张伊兰翠都留着。"
     "bot 打璐米欧儿本体，弃掉伊兰翠和诺玛。伊兰翠的价值在之后的 10 PP 回合。"),
    ("1791305215412", 6, "keep_card", {"never_plays": [BURNITE]}, "中",
     "先手第 6 回合 9 PP，对面只有一个 2/4：Salem 只打《世界》的呈现（破坏它、抽 2），剩 4 PP，把班德留到下回合（先手第 7 回合才能超进化）。"
     "bot 9 PP 下班德，9 点全场伤害只打一个 2/4，下回合也没有班德可超进化。"),
    ("1791306781701", 9, "keep_card", {"removes_biggest": True, "keeps_card": {RED: 1}}, "高",
     "相枛津给 2 张赤流。Salem 只用一张打诺玛 5/6，另一张留着（下回合正好用它解对面的班德 9/9）。"
     "bot 两张都用，一张打在 1/1 的露莉亚上。"),
    ("1791305347029", 10, "keep_card", {"removes_biggest": True, "keeps_card": {RED: 1}}, "中",
     "对面白板伊兰翠 8/8：Salem 用《世界》的呈现破坏它（还抽 2），赤流留着。bot 用赤流解它，弃掉《世界》的呈现。"),
    ("1791306497426", 10, "keep_card", {"removes_biggest": True, "keeps_card": {RED: 1}}, "中",
     "对面白板伊兰翠 8/8：Salem 下班德，9 点全场伤害解掉它，赤流留着。v2s 5 次里 3 次用赤流解它，再下午睡和佐伊。"),
    # --- keep the super-evolution point -----------------------------------------------------
    ("1791305539194", 7, "keep_sep", {"no_super_evolve": True, "removes_biggest": True}, "高",
     "对面诺玛 8/9：Salem 下诺玛，用普通进化（不是超进化）解掉它，超进化点和波菈莱都留着。"
     "下回合超进化伊兰翠撞璐米欧儿 9/9。bot 这回合就把超进化点用在诺玛或波菈莱上，下回合没得用。"),
    # --- evolve next turn, not this one -----------------------------------------------------
    ("1791306396169", 9, "evolve_timing", {"plays_unevolved": ERNTZ}, "中",
     "8 血：Salem 白板下伊兰翠，回合结束回 8 血，对诺玛打 8；下回合进化后攻击，加上回合结束的 8 点，斩杀。"
     "bot 当回合进化伊兰翠，不回血，进化点也用完了。"),
    ("1791305215412", 8, "evolve_timing", {"plays_unevolved": ERNTZ}, "中",
     "9 血：Salem 白板下伊兰翠回 8 血；下回合超进化它直接斩杀。v2 下班德并超进化，不回血。"),
    # --- super-evolve the card whose damage keeps coming -------------------------------------
    ("1791305539194", 6, "super_evolve_clock", {"super_evolves": BURNITE}, "中",
     "班德下场 9 点全场伤害解掉相枛津，超进化给对面纹章（对面每回合开始扣 2，回血时再扣 1），之后每个回合都在扣血。"
     "bot 超进化诺玛去撞相枛津。"),
    ("1791305120171", 6, "super_evolve_clock", {"super_evolves": BURNITE}, "中",
     "同样是班德全场 9 点解场 + 纹章，赤流留着，下回合用赤流解对面伊兰翠斩杀。v2s 用赤流解 3/3、超进化波菈莱拿深渊，班德留在手里。"),
    ("1791306269709", 6, "super_evolve_clock", {"super_evolves": ERNTZ}, "中",
     "超进化伊兰翠撞佐伊 7/7，活下来以后每个回合结束打对面 8，下回合配赤流斩杀。"
     "bot 打璐米欧儿本体并超进化它抽 3。平滑网络能修好这一个，说明换评分也能补。"),
    ("1791304981889", 8, "super_evolve_clock", {"super_evolves": BURNITE}, "中",
     "班德全场 9 点 + 纹章。v2s 和 Salem 一样，v2 下诺玛 + 午睡，班德留在手里。"),
    ("1791305347029", 7, "super_evolve_clock", {"super_evolves": BURNITE}, "中",
     "班德全场 9 点 + 纹章。bot 5 次里 2 次超进化诺玛去撞琪米卡。"),
    ("1791306781701", 7, "super_evolve_clock", {"super_evolves": ERNTZ}, "中",
     "超进化伊兰翠撞波菈莱 3/5，之后每回合打 8。v2s 和 Salem 一样，v2 超进化班德。"),
    # --- depends on what the opponent is believed to hold (not in the acceptance total: for the
    # planner's belief sampling, which reweights redraws by what the opponent has not played) -----
    ("1791304981889", 7, "belief", {"super_evolves": ERNTZ}, "belief",
     "10 血，对面相枛津 8/7：Salem 超进化伊兰翠撞死相枛津，回合结束打对面 8（19→11）。"
     "Salem 的理由（原话）：判断对方手里没有相枛津 / 赤流时，超进化正义是更好的进攻手段；10 血很难一回合暴毙；"
     "对方用《世界》解正义等于亏轮次，解不掉就直接赢。bot 白板下伊兰翠（回合结束 8 点打死相枛津，回 8 血）。"
     "这局对面其实有赤流，下回合用它解了伊兰翠。"),
]


def main(positions_path, turns_path):
    regression = json.load(open(positions_path, encoding="utf-8"))["positions"]
    turns = {(r["game"], r["own_turn"]): r for r in map(json.loads, open(turns_path, encoding="utf-8"))}
    out = []
    for game, own, category, check, confidence, why in PROBES:
        r = turns[(game, own)]
        related = [p["id"] for p in regression if p["game"] == game and p["at"] == r["at"]]
        bots = {}
        for label, spec in BOTS.items():
            lines = Counter(" | ".join(b["moves"]) for b in r["bots"][spec])
            line, n = lines.most_common(1)[0]
            bots[label] = {"most_common": line, "times": f"{n}/{len(r['bots'][spec])}"}
        out.append({"id": f"{game}-t{own}-{category}", "category": category, "check": check,
                    "confidence": confidence, "why": why, "game": game, "at": r["at"],
                    "own_turn": own, "first": r["first"], "context": r["context"],
                    "salem_turn": r["salem"]["moves"], "bot_turn": bots, "related": related})
    json.dump({"source": "Salem's 10 Ramp mirror games (positions.json records); bots' turns from "
                         "analysis/cross-turn/play_turns.py at svsim e8d190a, 5 seeds",
               "positions": out}, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
