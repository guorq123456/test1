"""Replay Salem's 27 games to the 10 divergence positions and write the full-information file."""
import json, sys, datetime
S = sys.argv[1]; OUT = sys.argv[2]
sys.path.insert(0, S + "/builder")
sys.path.insert(0, S + "/analyst/analysis/mirror-regression")
from glossary import COMMON, rename
from svsim.core.actions import from_dict, PlayCard, Attack, Evolve, EndTurn, UseBonusPP, Mulligan
from svsim.core.engine import apply, play_form
from svsim.core.enums import Keyword
from svsim.tools import records

games = json.load(open(S + "/analyst/analysis/mirror-regression/salem_games.json", encoding="utf-8"))["records"]
order = sorted(games)
rows = {}
for line in open(S + "/analyst/analysis/ramp-benchmark/salem_games_shallow_deep_results.jsonl", encoding="utf-8"):
    r = json.loads(line)
    if r["source"] == "salem27":
        rows[(r["ref"]["game"], r["at"])] = r
picks = [l.split() for l in open(S + "/top10/picks.txt")]
KW = [(Keyword.WARD, "守护"), (Keyword.STORM, "疾驰"), (Keyword.RUSH, "突进"), (Keyword.BANE, "必杀"),
      (Keyword.DRAIN, "吸血"), (Keyword.AMBUSH, "潜行"), (Keyword.BARRIER, "屏障"), (Keyword.INTIMIDATE, "威慑"), (Keyword.AURA, "光环")]
VER = {"mcts:200+plan+learned": "10-06 晚的旧 strong 档（mcts:200+plan+learned，线性评估器）",
       "mcts:200+plan+learned+phased": "10-07 的 v2s strong 档（第 13 版，构建 5175def）"}

def nm(defn):
    full = defn.name_zh or defn.name
    return COMMON.get(full, (full, ""))[0]

def lab(defn):
    full = defn.name_zh or defn.name
    n, s = COMMON.get(full, (full, ""))
    return f"{n}（{s}）" if s else n + "（词表无此牌，译名待 Salem 定）"

def unit(c, st):
    d = c.defn
    s = nm(d)
    if d.is_follower:
        s += f" {c.atk}/{c.life}" + (f"（血上限 {c.max_life}）" if c.max_life != c.life else "")
    elif d.is_amulet:
        s += "（护符" + (f"，倒数 {c.countdown}" if c.countdown is not None else "") + "）"
    elif not d.is_spell:
        s += "（纹章）"
    tags = [z for k, z in KW if c.keywords & k]
    if c.super_evolved: tags.append("已超进化")
    elif c.evolved: tags.append("已进化")
    if c.entered_turn == st.turn: tags.append("本回合入场")
    if d.is_follower and c.attacks_made >= c.max_attacks: tags.append("本回合已攻击")
    if c.silenced: tags.append("已沉默")
    return s + ("［" + "、".join(tags) + "］" if tags else "")

def tname(st, uid, me):
    if uid is not None and uid < 0:
        return "对手主战者" if -uid - 1 != me else "自己主战者"
    c = st.on_field(uid) or st.in_hand(me, uid)
    return nm(c.defn) if c is not None else str(uid)

def pct(x): return f"{round(x * 100)}%"

out = []
for gid, at in picks:
    at = int(at); rec = games[gid]; st = records.start(rec)
    log = []
    for a in rec["actions"][:at]:
        act = from_dict(a); me = st.active; ps = st.players[me]
        if isinstance(act, PlayCard):
            c = st.in_hand(me, act.uid); form = play_form(ps, c)
            how = ""
            if form is not None and form.alt is not None: how = f"（加速形态，{form.paid}费）"
            elif form is not None and form.enhanced: how = f"（强化，{form.enhanced}费）"
            t = ("，目标 " + "、".join(tname(st, x, me) for x in act.targets)) if act.targets else ""
            log.append((st.turn, me, f"出 {nm(c.defn)}{how}{t}"))
        elif isinstance(act, Evolve):
            c = st.on_field(act.uid)
            log.append((st.turn, me, f"{'超进化' if act.super_ else '进化'} {nm(c.defn) if c else act.uid}"))
        elif isinstance(act, Attack):
            log.append((st.turn, me, f"{tname(st, act.attacker, me)} 攻击 {tname(st, act.target, me)}"))
        elif isinstance(act, UseBonusPP):
            log.append((st.turn, me, "用额外 PP"))
        elif isinstance(act, Mulligan):
            log.append((0, me, f"换 {len(act.indices)} 张"))
        apply(st, act)
    p = st.active; r = rows[(gid, at)]; assert r["side"] == p
    out.append(dict(gid=gid, no=order.index(gid) + 1, at=at, rec=rec, st=st, p=p, r=r, log=log))

def who(side): return "你" if side == 0 else "bot"
def bonus(ps, first):
    if ps.index == first: return "先手，无额外 PP"
    if ps.bonus_active: return "后手额外 PP 本回合已用上"
    if ps.bonus_ready: return "后手额外 PP 可用（还没用）"
    return "后手额外 PP 已用完" + ("（自己第 6 回合再得一个）" if ps.turns_taken < 6 else "")

L = []
L += ["# 你那 27 局里：浅搜和深搜走法不同、差得最多的 10 个局面（请你判断）", "",
      "> 13:25Z 重做：你 13:03 说这份信息不全（没有当前回合数、对方进化点、已打出的牌）。这版每个局面都从存档逐步回放到那一步，补了：整局第几回合、谁先手、双方 PP 和额外 PP、双方剩余进化点 / 超进化点、双方此前每回合出过的牌和进化、双方墓地 / 手牌 / 牌库张数、场上随从的攻血和状态（守护、已进化、本回合入场、本回合已攻击）、行动方的全部手牌。不列的只有一样：**非行动方的手牌**，因为 bot 下这步时也看不到它，列出来会让你用 bot 没有的信息来评。",
      "> 参考可靠度（07:03Z 补）：这 10 个局面全部来自原版跳费龙镜像的 27 局（分析线的 salem27：10-06 中午 10 局 + 10-06 晚 10 局 + 10-07 对 v2s 7 局），没有一个来自宇宙鱼 / 旗皇的对局（弱参考）。",
      "> **要你确认一件事（13:20Z）**：10-06 中午 16:43～17:13Z（纽约时间 12:43～13:13）那 10 局跳费龙镜像，座位 0 10 胜 0 负，**是你打的吗？** 分析线一直把它们记成你的局（你 10-07 也评过其中一局的一步：「我不清楚那局具体发生了什么，但这个决定是根据复杂情况判断的……」），而我 04:25 的外战汇总把它们记成「分析会话用页面打的，不算你的外战」。两处相反，只有你能定。这里的第 1、4、6、7 个局面就来自那批，先照常列出，标了「待确认」。", "",
      "## 要你做什么", "",
      "每个局面回一句话就够，格式随意，例如「3：深搜对，口人魔点掉《世界》的呈现换节奏」。三种答法：",
      "- **浅搜对**（或：你实际那步对）；",
      "- **深搜对**；",
      "- **两步都不对，该走 ×××**。",
      "后面加一句理由（为什么）。理由是这 10 个局面最值钱的部分：bot 现在的评估器看不出来的东西，多半就在你的理由里。不想答的局面写「跳过」。", "",
      "## 怎么读", "",
      "条件：对手卡表已知（牌序、手牌未知）。两边都是原版跳费龙。",
      "做法：在同一个局面上，浅搜（v2，每步 100 次模拟）和深搜（每步 800 次模拟）各选一步。两步不一样时，各走一遍，这一回合剩下的都由 v2s 打完，比回合结束时 bot 估的胜率。对手没见过的牌按已知卡表发 8 次，取平均。",
      "「差多少」是 bot 估的胜率差：深搜那步减去浅搜那步，单位是胜率点。这个差是 bot 自己估的，它也可能估错；哪步更好请你来判。「后面这样打」是 8 次里第 1 次的走法，只是举例。",
      "回合数：「整局第 N 回合」从先手第 1 回合起数，双方各算一回合；括号里是行动方自己的第几回合。「此前的出牌」按整局回合列，含双方；同一回合里按先后顺序。",
      "牌名：常用名（费用 身材）；手牌一栏每张都带费用身材，场上和出牌记录只写常用名。额外 PP：后手开局有 1 个，自己第 6 回合再得 1 个；用了但没花掉会退回。赤流、天刀深渊是衍生牌（口人魔给 2 张赤流；波菈莱进化给天刀深渊）。", ""]

for i, o in enumerate(out, 1):
    st, p, r, rec = o["st"], o["p"], o["r"], o["rec"]
    me, op = st.players[p], st.players[1 - p]
    mover = who(p); other = who(1 - p)
    first = who(rec["first"])
    winner = rec.get("winner"); res = "未记录（中途结束）" if winner is None else (who(winner) + " 胜")
    dt = datetime.datetime.fromtimestamp(int(o["gid"]) / 1000, datetime.timezone.utc)   # the id is the game's ms timestamp
    exp = json.load(open("/mnt/project-files/shadowverse/salem-games/db-export-2026-10-08/" + o["gid"] + ".json", encoding="utf-8"))
    noon = dt < datetime.datetime(2026, 10, 6, 18, 0, tzinfo=datetime.timezone.utc) and dt.day == 6
    regret = round(r["regret"] * 100)
    L.append(f"## {i}. 第 {o['no']} 局（{o['gid']}），整局第 {st.turn} 回合（{mover}的第 {me.turns_taken} 回合，{first}先手），{mover}那步的局面，差 {regret} 个胜率点")
    L.append("")
    L.append(f"- 对局：{dt:%m-%d %H:%M}Z，对手是 {VER.get(rec['ai'], rec['ai'])}；{first}先手；结果 {res}，整局共 {exp.get('turn', '?')} 回合、{exp.get('moves', '?')} 步。" + ("**这局属 10-06 中午批（16:43～17:13Z），是不是你打的待你一句话确认，见文首。**" if noon else ""))
    L.append(f"- **{mover}（行动方）**：主战者 {me.leader_hp}/{me.leader_max_hp}；PP {me.pp}/{me.max_pp}，{bonus(me, rec['first'])}；进化点剩 {me.ep}、超进化点剩 {me.sep}（本局已进化 {me.evolutions} 次{'，本回合已进化' if me.evolved_this_turn else ''}）；手牌 {len(me.hand)} 张，牌库 {len(me.deck)} 张，墓地 {me.shadows} 张；本回合已出 {me.combo} 张牌。")
    L.append(f"- **{other}**：主战者 {op.leader_hp}/{op.leader_max_hp}；PP 上限 {op.max_pp}（{bonus(op, rec['first'])}）；进化点剩 {op.ep}、超进化点剩 {op.sep}（本局已进化 {op.evolutions} 次）；手牌 {len(op.hand)} 张（不列），牌库 {len(op.deck)} 张，墓地 {op.shadows} 张。")
    L.append(f"- {mover}场上：" + ("、".join(unit(c, st) for c in me.field) if me.field else "无") + (("；主战者区：" + "、".join(unit(c, st) for c in me.leader_area)) if me.leader_area else ""))
    L.append(f"- {other}场上：" + ("、".join(unit(c, st) for c in op.field) if op.field else "无") + (("；主战者区：" + "、".join(unit(c, st) for c in op.leader_area)) if op.leader_area else ""))
    L.append(f"- {mover}手牌（{len(me.hand)} 张）：" + "、".join(lab(c.defn) + (f"〔现费 {c.cost}〕" if c.cost != c.defn.cost else "") for c in me.hand))
    # history
    L.append(f"- 此前的出牌（{mover} = 行动方）：")
    m = [x for x in o["log"] if x[0] == 0]
    if m:
        L.append("  - 换牌：" + "，".join(f"{who(s)}{t}" for _, s, t in m))
    by_turn = {}
    for t, s, txt in o["log"]:
        if t > 0: by_turn.setdefault(t, (s, []))[1].append(txt)
    for t in range(1, st.turn + 1):
        side = rec["first"] if t % 2 == 1 else 1 - rec["first"]
        own = (t + 1) // 2
        s_txt = by_turn.get(t, (side, []))[1]
        tag = "（本回合，到这步为止）" if t == st.turn else ""
        L.append(f"  - 第 {t} 回合（{who(side)}第 {own}）{tag}：" + (" → ".join(s_txt) if s_txt else "没出牌"))
    # moves
    def line(xs): return " → ".join(rename(x) for x in xs) if xs else "结束回合"
    L.append(f"- 浅搜：{rename(r['shallow'])}；后面这样打：{line(r['line_shallow'])}")
    L.append(f"- 深搜：{rename(r['deep'])}；后面这样打：{line(r['line_deep'])}")
    L.append(f"- bot 估的胜率：浅搜那步之后 {pct(r['v_shallow'])}，深搜那步之后 {pct(r['v_deep'])}。")
    act = rename(r["actual"])
    same = "（和深搜一样）" if act == rename(r["deep"]) else ("（和浅搜一样）" if act == rename(r["shallow"]) else "（两步都不是）")
    L.append(f"- {'你实际' if p == 0 else '当时 bot 实际'}：{act}{same}")
    L.append(f"- 出处：salem27，{{\"game\": \"{o['gid']}\"}}，第 {o['at']} 步；存档 salem-games/db-export-2026-10-08/{o['gid']}.json；回放脚本见文末。")
    L.append("")
L += ["## 数据出处", "",
      "- 局面与浅深结果：分析线 ccr-da4857cc-rkpgwr，`analysis/ramp-benchmark/salem_games_shallow_deep_results.jsonl`（source = salem27，按 ref.game + at 取行），字段 shallow / deep / actual / v_shallow / v_deep / regret / line_shallow / line_deep。",
      "- 对局存档：`salem-games/db-export-2026-10-08/<对局号>.json`（record.actions 逐步回放，seat 0 = 你，seat 1 = bot）；回放用建造线 e434e24 的 svsim（`svsim.tools.records.start` + `svsim.core.engine.apply`），读到第 at 步之前的状态。",
      "- 牌名对照：card-glossary.md；加速形态 / 强化按 `svsim.core.engine.play_form` 判定。",
      "- 本文件由架构线脚本生成（claude/bot-architecture-design，analysis/salem-top10/render.py）。"]
open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("wrote", OUT, len("\n".join(L)), "chars")
