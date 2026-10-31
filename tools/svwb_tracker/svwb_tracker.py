#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读取《影之诗：巅峰对决》客户端自己写在硬盘上的崩溃上报「面包屑」(bt-breadcrumbs)，整理成对局记录。

只读游戏写出的文件，不读内存、不截屏、不碰游戏进程。数据只留在本机。

用法（在 Salem 的电脑上）：
    python svwb_tracker.py parse --raw C:\\claude\\svwb-tracker\\raw --out C:\\claude\\svwb-tracker\\out
    python svwb_tracker.py parse ... --decks C:\\claude\\svwb-tracker\\decks.txt   # 我的卡组登记：每行「名字|卡组代码」
    python svwb_tracker.py watch ...   # 每 60 秒重跑一次 parse

输出（--out 目录）：
    games.jsonl   每局完整记录（事件、每一手、推断依据），供以后重新分析
    games.csv     「影之诗战绩本」页面能直接导入的表（按对局编号合并）
    review.md     人读的每局回顾：双方每一手、进化、胜负、先后手
    summary.txt   按「我的卡组 × 对手套路」的胜负汇总

面包屑格式（2026-10-31 在 1.10.0 版客户端上看到的）：每条 {"timestamp": 毫秒, "id": 流水号, "type": "manual"/"system",
"level": "info", "message": 日文调试文本}。有用的信息全在 message 里，用正则取。调试字段以后的版本可能改，改了就要调这里的正则。
"""
import argparse
import collections
import csv
import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASS_NAMES = {0: "中立", 1: "精灵", 2: "皇家护卫", 3: "巫师", 4: "龙族", 5: "梦魇", 6: "主教", 7: "超越者"}
UNKNOWN = "未知"

# ---------- 正则：面包屑 message 里能认出来的事件 ----------
RE_HAND = re.compile(r"GetOrCreateHandCard開始 CardId=(\d+) IsCreate=(True|False)")
RE_HAND_EVO = re.compile(r"GetOrCreateHandCardEvolve開始 CardId=(\d+)")
RE_PLAY = re.compile(r"カードプレイ時クラッシュ調査：カードID Card\((\d+)\)")
RE_FIELD = re.compile(r"GetOrCreateField(Follower|Amulet)開始 CardId=(\d+)")
RE_EVOLVE = re.compile(r"進化時クラッシュ調査：カードID Card\((\d+)\) / リーダースキンID (\d+) / isAlly (True|False) / isSuper (True|False)")
RE_SKIN = re.compile(r"LeaderSkinクラッシュ調査：LoadResourceAsync開始, id:(vs|class)_(\d+), ally:(True|False), result:(True|False), battleStart:(True|False)")
RE_CUTIN_END = re.compile(r"BattleStartCutin\.OnDestroy")
RE_RESULT_TL = re.compile(r"PlayTimeline, name=BattleResult(\w+?)Timeline")
RE_RESULT_BG = re.compile(r"object=ResultBG(\w+?)Effect")
RE_RESULT_UI = re.compile(r"Instantiate, name=Prefabs/Battle/BattleResult$")
RE_RANK_GAUGE = re.compile(r"source=BattleResultRankGauge")
RE_REPORT = re.compile(r"reasn: \w+ .*?ally_turn: (\d+) oppo_turn: (\d+)")
RE_SCENE = re.compile(r"シーンロード完了 name=(\S+)")
RE_QUIT = re.compile(r"Application:quitting")

PREPLAY_WINDOW = 1.6    # 「亮牌/选项」到打出的最长间隔（秒）：对手亮牌 0.5～1.4 秒，我方选择类卡牌的选项 0.9～1.9 秒
PASS_GAP_A = 2.0        # 推断「对方空过」：对方的抽牌至少要在我方最后一个动作之后这么多秒
PASS_GAP_B = 3.0        # 推断「对方空过」：我方再次抽牌至少要在对方抽牌之后这么多秒
SETTLED_GAP = 3.0       # 当前回合的一方还没动过时，这回合至少要过了这么多秒，才允许推断「对方开始了新回合/空过」
SUMMON_WINDOW = 1.2     # 出牌到入场的最长间隔（秒）；超过就当作效果召唤


# ---------- 卡表与卡组 ----------
def load_cards(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def card_class(cid):
    """卡牌 ID 第 4 位是职业（0 中立，1 精灵 … 7 超越者）。9 开头的衍生牌也一样。"""
    s = str(cid)
    if len(s) != 8:
        return None
    try:
        return int(s[3])
    except ValueError:
        return None


def lookup(cards, cid):
    """卡表里找名字：原 ID → 7 开头的异画换成 1 开头 → 末位换成 0（版本位）。"""
    s = str(cid)
    cands = [s]
    if s.startswith("7"):
        cands.append("1" + s[1:])
    cands += [c[:-1] + "0" for c in list(cands)]
    for c in cands:
        if c in cards:
            return cards[c]
    return None


def card_name(cards, cid):
    info = lookup(cards, cid)
    return info["zh"] if info else "卡#%s" % cid


def base_id(cid):
    """用于比对卡组的规范 ID：7→1，末位归 0。"""
    s = str(cid)
    if s.startswith("7"):
        s = "1" + s[1:]
    return s[:-1] + "0" if len(s) == 8 else s


def is_token(cards, cid):
    s = str(cid)
    if s.startswith("9"):
        return True
    info = lookup(cards, cid)
    return bool(info and info.get("token"))


ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
_VAL = {ch: i for i, ch in enumerate(ALPHABET)}


def decode_deck(code):
    """官方卡组代码 "1.3.cH3E...." → (职业号, [卡牌 ID])。"""
    parts = code.strip().split(".")
    craft = int(parts[1])
    ids = []
    for tok in parts[2:]:
        v = 0
        for ch in tok:
            v = v * 64 + _VAL[ch]
        ids.append(str(v))
    return craft, ids


def load_my_decks(path):
    """decks.txt：每行「名字|卡组代码」，# 开头是注释。"""
    decks = []
    if not path or not Path(path).exists():
        return decks
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        name, code = line.split("|", 1)
        try:
            craft, ids = decode_deck(code)
        except Exception:
            continue
        decks.append({"name": name.strip(), "cls": craft, "cards": collections.Counter(ids)})
    return decks


def load_archetypes(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for d in data.get("decks", []):
        cls = {v: k for k, v in CLASS_NAMES.items()}.get(d["cls"])
        out.append({"name": d["name"], "cls": cls, "cards": collections.Counter({k: int(v) for k, v in d["cards"].items()})})
    return out


def match_deck(seen_ids, decks, cls, cards, min_seen, min_score, margin):
    """seen_ids：这一方被看到的卡（不含衍生牌）。返回 (名字, 分数, 依据) 或 (None, ...)。
    分数 = 看到的不同卡里有几成在这副卡组里。同名卡组取最高分。"""
    seen = {base_id(c) for c in seen_ids if not is_token(cards, c)}
    seen = {c for c in seen if card_class(c) in (cls, 0, None)}
    if len(seen) < min_seen:
        return None, 0.0, "看到的牌太少（%d 张）" % len(seen)
    best = {}
    for d in decks:
        if cls is not None and d["cls"] not in (cls, None):
            continue
        hit = sum(1 for c in seen if c in d["cards"])
        score = hit / len(seen)
        if d["name"] not in best or score > best[d["name"]][0]:
            best[d["name"]] = (score, hit)
    if not best:
        return None, 0.0, "没有这个职业的参照卡组"
    ranked = sorted(best.items(), key=lambda kv: -kv[1][0])
    name, (score, hit) = ranked[0]
    second = ranked[1][1][0] if len(ranked) > 1 else 0.0
    why = "看到 %d 张不同的牌，%d 张在「%s」里（%.0f%%）" % (len(seen), hit, name, 100 * score)
    if score < min_score:
        return None, score, why + "，不够像"
    if score - second < margin and len(ranked) > 1:
        return None, score, why + "，但和「%s」（%.0f%%）分不开" % (ranked[1][0], 100 * second)
    return name, score, why


# ---------- 读取原始面包屑 ----------
def load_raw(raw_dir, since=None):
    entries = {}
    for f in sorted(Path(raw_dir).glob("*.jsonl")):
        if since and f.stem.replace("breadcrumbs-", "") < since and f.stem.startswith("breadcrumbs-"):
            continue
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip().rstrip(",")
                if not line or line in "[]":
                    continue
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if not isinstance(e, dict) or "timestamp" not in e or "message" not in e:
                    continue
                key = (e["timestamp"], e.get("id"), e["message"])
                entries[key] = e
    out = sorted(entries.values(), key=lambda e: (e["timestamp"], e.get("id") or 0))
    return out


def classify(e):
    """一条面包屑 → (种类, 字段)。认不出来的返回 (None, None)。"""
    m = e["message"]
    r = RE_HAND.search(m)
    if r:
        return "hand", {"cid": r.group(1), "create": r.group(2) == "True"}
    r = RE_PLAY.search(m)
    if r:
        return "play", {"cid": r.group(1)}
    r = RE_FIELD.search(m)
    if r:
        return "field", {"kind": r.group(1), "cid": r.group(2)}
    r = RE_EVOLVE.search(m)
    if r:
        return "evolve", {"cid": r.group(1), "skin": r.group(2), "ally": r.group(3) == "True", "super": r.group(4) == "True"}
    r = RE_HAND_EVO.search(m)
    if r:
        return "hand_evo", {"cid": r.group(1)}
    r = RE_SKIN.search(m)
    if r:
        return "skin", {"where": r.group(1), "skin": r.group(2), "ally": r.group(3) == "True", "result": r.group(4) == "True", "start": r.group(5) == "True"}
    if RE_CUTIN_END.search(m):
        return "cutin_end", {}
    r = RE_RESULT_TL.search(m)
    if r:
        return "result", {"word": r.group(1)}
    r = RE_RESULT_BG.search(m)
    if r:
        return "result_bg", {"word": r.group(1)}
    if RE_RESULT_UI.search(m):
        return "result_ui", {}
    if RE_RANK_GAUGE.search(m):
        return "rank_gauge", {}
    r = RE_REPORT.search(m)
    if r:
        return "report", {"ally_turn": int(r.group(1)), "oppo_turn": int(r.group(2))}
    r = RE_SCENE.search(m)
    if r:
        return "scene", {"name": r.group(1)}
    if RE_QUIT.search(m):
        return "quit", {}
    return None, None


# ---------- 切成一局一局 ----------
def segment(entries):
    """一局从「battleStart:True 的皮肤加载」开始（没有就从 BattleStartCutin 结束算），到结算画面之后、下一局开始之前结束。"""
    games = []
    cur = None
    for e in entries:
        kind, f = classify(e)
        if kind is None:
            continue
        ev = {"t": e["timestamp"] / 1000.0, "kind": kind, **f}
        starts_new = (kind == "skin" and f["start"]) or (kind == "cutin_end" and (cur is None or cur["cutin_end"] is not None))
        if starts_new and (cur is None or cur["result"] is not None or cur["cutin_end"] is not None and ev["t"] - cur["last_t"] > 120):
            if cur is not None:
                games.append(cur)
            cur = {"events": [], "cutin_end": None, "result": None, "last_t": ev["t"], "start_t": ev["t"], "partial": False}
        if cur is None:
            if kind == "quit":
                continue
            cur = {"events": [], "cutin_end": None, "result": None, "last_t": ev["t"], "start_t": ev["t"], "partial": True}
        if kind == "quit":
            games.append(cur)
            cur = None
            continue
        cur["events"].append(ev)
        cur["last_t"] = ev["t"]
        if kind == "cutin_end" and cur["cutin_end"] is None:
            cur["cutin_end"] = ev["t"]
            # 开场动画结束之前还没有任何手牌/出牌事件 → 这局其实是完整的，只是没看到 battleStart 那条
            if cur["partial"] and not any(x["kind"] in ("hand", "play", "evolve") for x in cur["events"]):
                cur["partial"] = False
        if kind == "result" and cur["result"] is None:
            cur["result"] = f["word"]
    if cur is not None:
        games.append(cur)
    return games


# ---------- 一局之内：谁的牌、第几回合、每一手 ----------
def analyze(game, cards, my_decks, archetypes, cfg):
    ev = game["events"]
    g = {
        "start": game["start_t"], "cutin_end": game["cutin_end"], "end": None,
        "result": None, "result_raw": game["result"], "ranked": False,
        "my_skin": None, "opp_skin": None, "my_cls": None, "opp_cls": None,
        "first": None, "first_why": "", "my_turns": 0, "opp_turns": 0,
        "my_hand0": [], "my_seen": [], "opp_seen": [], "moves": [], "report": None, "scene": None,
        "warnings": [], "partial": bool(game.get("partial")),
    }
    # 1) 皮肤：class_#### 的 ally 字段可信；vs_#### 的不可信
    for x in ev:
        if x["kind"] == "skin" and x["where"] == "class" and not x["result"]:
            if x["ally"] and g["my_skin"] is None:
                g["my_skin"] = x["skin"]
            if not x["ally"] and g["opp_skin"] is None:
                g["opp_skin"] = x["skin"]
        if x["kind"] == "scene" and g["scene"] is None:
            g["scene"] = x["name"]
        if x["kind"] == "rank_gauge":
            g["ranked"] = True
        if x["kind"] == "report":
            g["report"] = {"ally_turn": x["ally_turn"], "oppo_turn": x["oppo_turn"]}
        if x["kind"] in ("result", "result_ui") and g["end"] is None:
            g["end"] = x["t"]
    # 开头没存到的局：皮肤编号从进化记录里补（进化记录带「リーダースキンID + isAlly」）
    for x in ev:
        if x["kind"] == "evolve" and x.get("skin"):
            if x["ally"] and g["my_skin"] is None:
                g["my_skin"] = x["skin"]
            if not x["ally"] and g["opp_skin"] is None:
                g["opp_skin"] = x["skin"]
    # 皮肤 ID 末位 = 职业（10-31 在 7 局、7 个不同皮肤上验证：1 精灵、3 巫师、4 龙族、6 主教都对）
    skin_cls = lambda s: int(s[-1]) if s and s[-1].isdigit() and 1 <= int(s[-1]) <= 7 else None  # noqa: E731

    # 2) 只看开场动画结束之后的牌
    t0 = game["cutin_end"] if game["cutin_end"] is not None else game["start_t"]
    body = [x for x in ev if x["t"] >= t0 and x["kind"] in ("hand", "play", "field", "evolve")]
    n_body = len(body)

    # 3) 双方职业（不依赖任何一手牌的归属判断）
    #   我方：开场 3 秒内看得见 ID 的起手牌里，非中立牌的职业众数；没有就看我方进化的牌，再没有就看皮肤末位。
    #   对手：所有出牌、进化、可见手牌里，除我方职业和中立之外最常见的职业（对手进化的牌权重加大）；
    #         一张都没有就看皮肤末位；皮肤也没有就按同职业（镜像局）处理。
    #   主战者皮肤编号末位 = 职业，已在 7 局里验证（6/6 有皮肤的局都对），所以皮肤优先，牌只做校验和兜底。
    opening_vis = [x for x in body if x["kind"] == "hand" and x["cid"] != "0" and x["t"] - t0 <= 3.0]
    votes = collections.Counter(card_class(x["cid"]) for x in opening_vis if card_class(x["cid"]))
    my_cls_cards = votes.most_common(1)[0][0] if votes else None
    if my_cls_cards is None:
        votes = collections.Counter(card_class(x["cid"]) for x in body if x["kind"] == "evolve" and x["ally"] and card_class(x["cid"]))
        my_cls_cards = votes.most_common(1)[0][0] if votes else None
    my_cls = skin_cls(g["my_skin"]) or my_cls_cards
    other = collections.Counter()
    for x in body:
        c = card_class(x["cid"]) if x["kind"] in ("play", "evolve", "hand") and x["cid"] != "0" else None
        if not c or c == my_cls:
            continue
        if x["kind"] == "evolve":
            if x["ally"]:
                continue
            other[c] += 3
        else:
            other[c] += 1
    opp_skin_c = skin_cls(g["opp_skin"])
    opp_cls_cards = other.most_common(1)[0][0] if other else None
    opp_cls = opp_skin_c or opp_cls_cards or my_cls
    g["my_cls"], g["opp_cls"] = my_cls, opp_cls
    g["skins"] = {"me": g["my_skin"], "opp": g["opp_skin"], "me_cls": skin_cls(g["my_skin"]), "opp_cls": opp_skin_c}
    if skin_cls(g["my_skin"]) and my_cls_cards and skin_cls(g["my_skin"]) != my_cls_cards:
        g["warnings"].append("我方皮肤末位说是%s，起手牌却是%s，职业按皮肤算" % (CLASS_NAMES.get(my_cls), CLASS_NAMES.get(my_cls_cards)))
    if opp_skin_c and opp_cls_cards and opp_skin_c != opp_cls_cards and other[opp_cls_cards] >= 2:
        g["warnings"].append("对手皮肤末位说是%s，出的牌却多是%s，职业按皮肤算" % (CLASS_NAMES.get(opp_cls), CLASS_NAMES.get(opp_cls_cards)))
    mirror = my_cls is not None and my_cls == opp_cls
    g["mirror"] = mirror
    if mirror:
        g["warnings"].append("同职业局：双方出牌归属只能靠回合推断，把握较低")

    # 4) 第一遍：可靠的归属（锚点）
    #   暗牌（CardId=0）→ 对手；进化 → isAlly 旗标；非镜像局里出牌/可见手牌按职业归属；
    #   中立牌和镜像局里的牌 → 待定（None），第二遍按「当时是谁的回合」归属。
    #   「亮牌/选项」：一张可见手牌之后 PREPLAY_WINDOW 秒内就有同一张（规范 ID）被打出，这条手牌事件不是抽牌：
    #   既可能是对手亮牌后打出，也可能是我方选择类卡牌弹出的选项，它的归属跟那次出牌走。
    side_of = [None] * n_body
    preplay_of = [None] * n_body
    for i, x in enumerate(body):
        if x["kind"] != "hand" or x["cid"] == "0":
            continue
        b = base_id(x["cid"])
        for j in range(i + 1, min(n_body, i + 10)):
            y = body[j]
            if y["t"] - x["t"] > PREPLAY_WINDOW:
                break
            if y["kind"] == "play" and base_id(y["cid"]) == b:
                preplay_of[i] = j
                break
    for i, x in enumerate(body):
        if x["kind"] == "hand":
            if x["cid"] == "0":
                side_of[i] = "opp"
            elif preplay_of[i] is not None:
                side_of[i] = None
            else:
                c = card_class(x["cid"])
                if not mirror and c and c == opp_cls:
                    side_of[i] = "opp"      # 对手被效果亮出来的牌（不是抽牌）
                else:
                    side_of[i] = "me"       # 我抽到/拿到的牌
        elif x["kind"] == "play":
            c = card_class(x["cid"])
            if not mirror and c and c == my_cls:
                side_of[i] = "me"
            elif not mirror and c and c == opp_cls:
                side_of[i] = "opp"
        elif x["kind"] == "evolve":
            side_of[i] = "me" if x["ally"] else "opp"

    # 5) 先后手：回合从「换牌后第一次孤立的抽牌」开始
    #   孤立 = 前后 3 秒内没有另一方的手牌事件；起手那 8 张在开场后 2 秒内一起出现，不算；亮牌/选项不算抽牌。
    first_play_i = next((i for i, x in enumerate(body) if x["kind"] == "play"), None)
    first_play_t = body[first_play_i]["t"] if first_play_i is not None else None
    hand_evts = [(i, x, side_of[i]) for i, x in enumerate(body) if x["kind"] == "hand" and preplay_of[i] is None]
    D = []
    for i, x, s in hand_evts:
        if first_play_t is not None and x["t"] >= first_play_t:
            break
        if x["t"] - t0 < 5:
            continue
        if s == "opp" and x["cid"] != "0":
            continue  # 对手被亮出来的牌，不是抽牌
        other_near = any(abs(y["t"] - x["t"]) <= 3.0 and s2 != s for j, y, s2 in hand_evts if j != i)
        if other_near:
            continue
        D.append((s, x["t"]))
    while len(D) >= 2 and D[0][0] == D[1][0]:
        D.pop(0)  # 连着两次都是同一方：前一次是换牌（或效果抽牌）
    g["opening"] = [{"dt": round(x["t"] - t0, 1), "side": side_of[i] if preplay_of[i] is None else "pre", "cid": x["cid"], "create": x["create"]}
                    for i, x in enumerate(body) if x["kind"] == "hand" and (first_play_t is None or x["t"] < first_play_t) and x["t"] - t0 <= 120]
    first_play_side = None
    if first_play_i is not None:
        first_play_side = side_of[first_play_i]
    if g["partial"]:
        D = []
        turn1_t = body[0]["t"] if body else None
        g["first_why"] = "开头没存到，先后手只能看结算记录"
    elif D:
        turn1_t = D[0][1]
        g["first"] = D[0][0] == "me"
        g["first_why"] = "换牌后第一个抽牌的是%s" % ("我方" if g["first"] else "对手")
        if first_play_side is not None and first_play_side != D[0][0]:
            g["first_why"] += "（第一个出牌的是另一方，可能是先手空过了第 1 回合）"
    elif first_play_side is not None:
        turn1_t = first_play_t
        g["first"] = first_play_side == "me"
        g["first_why"] = "第一个出牌的是%s（没看到开局抽牌，把握中等）" % ("我方" if g["first"] else "对手")
    else:
        turn1_t = None
    for i, x, s in hand_evts:
        if turn1_t is not None and x["t"] >= turn1_t:
            break
        if s == "me" and x["cid"] != "0":
            g["my_hand0"].append(x["cid"])

    # 6) 第二遍：回合与每一手
    #   回合切换主要认「锚点动作」：归属可靠的一方出牌/进化，就是这一方的回合。
    #   抽牌事件只在这些情况下算回合开始：(a) 它后面的下一个锚点动作就是这一方的；(b) 后面没有锚点动作可参照
    #   （镜像局、尾声），且离最后一个动作 ≥ PASS_GAP_A 秒；(c) 下一个锚点动作是对方的，但对方在 ≥ PASS_GAP_B 秒后
    #   又抽了一张且其间没有动作（= 这一方这回合空过了）。(b)(c) 都要求当前回合的一方已经动过，或这回合已经过了
    #   SETTLED_GAP 秒以上（否则等于连着两次空过，更可能是效果抽牌）。待定归属的出牌归当时回合的一方。
    moves = []
    turn_side, my_turns, opp_turns = None, 0, 0
    turn_actions = 0
    turn_start_t = None
    last_action_t = None
    last_field_play_t = {}
    ambiguous = 0

    def switch(s, t):
        nonlocal turn_side, my_turns, opp_turns, turn_actions, turn_start_t
        if s is None or s == turn_side:
            return
        turn_side = s
        turn_actions = 0
        turn_start_t = t
        if s == "me":
            my_turns += 1
        else:
            opp_turns += 1

    import bisect
    anchor_idx = [k for k, y in enumerate(body) if y["kind"] in ("play", "evolve") and side_of[k] is not None]

    def next_anchor(i):
        k = bisect.bisect_right(anchor_idx, i)
        return anchor_idx[k] if k < len(anchor_idx) else None

    for i, x in enumerate(body):
        if turn1_t is None or x["t"] < turn1_t:
            continue
        s = side_of[i]
        if x["kind"] == "hand":
            if preplay_of[i] is not None:
                continue
            if s == "me" and x["cid"] != "0":
                g["my_seen"].append(x["cid"])
            if s == turn_side:
                continue
            j = next_anchor(i)
            if j is not None and side_of[j] == s:
                switch(s, x["t"])
                continue
            settled = turn_side is None or turn_actions > 0 or (turn_start_t is not None and x["t"] - turn_start_t >= SETTLED_GAP)
            if not settled or (last_action_t is not None and x["t"] - last_action_t < PASS_GAP_A):
                continue
            if j is None:
                switch(s, x["t"])
                continue
            opposite = "opp" if s == "me" else "me"
            passed = any(body[k]["kind"] == "hand" and preplay_of[k] is None and side_of[k] == opposite
                         and body[k]["t"] - x["t"] >= PASS_GAP_B for k in range(i + 1, j))
            if passed:
                switch(s, x["t"])
        elif x["kind"] == "play":
            if s is None:
                s = turn_side or (("me" if g["first"] else "opp") if g["first"] is not None else "me")
                side_of[i] = s
                ambiguous += 1
            switch(s, x["t"])
            turn_actions += 1
            last_action_t = x["t"]
            last_field_play_t[x["cid"]] = x["t"]
            (g["my_seen"] if s == "me" else g["opp_seen"]).append(x["cid"])
            moves.append({"t": x["t"], "side": s, "turn": my_turns if s == "me" else opp_turns, "kind": "出牌", "cid": x["cid"]})
        elif x["kind"] == "field":
            tp = last_field_play_t.get(x["cid"])
            if tp is None or x["t"] - tp > SUMMON_WINDOW:
                s2 = turn_side
                moves.append({"t": x["t"], "side": s2, "turn": (my_turns if s2 == "me" else opp_turns) if s2 else 0, "kind": "入场（效果）", "cid": x["cid"]})
                if s2 == "opp":
                    g["opp_seen"].append(x["cid"])
                elif s2 == "me":
                    g["my_seen"].append(x["cid"])
        elif x["kind"] == "evolve":
            switch(s, x["t"])
            turn_actions += 1
            last_action_t = x["t"]
            moves.append({"t": x["t"], "side": s, "turn": my_turns if s == "me" else opp_turns, "kind": "超进化" if x["super"] else "进化", "cid": x["cid"]})
            (g["my_seen"] if s == "me" else g["opp_seen"]).append(x["cid"])
    g["moves"] = moves
    g["ambiguous"] = ambiguous
    g["my_turns"], g["opp_turns"] = my_turns, opp_turns
    # 费用线索：一方在第 k 回合打出的牌原费高于 k。巫师的法术增幅减费、龙族的跳费都会让它误报，所以只当线索，不当警告
    g["hints"] = []
    if not g["partial"]:
        for side_key, label in (("me", "我方"), ("opp", "对手")):
            for m in moves:
                if m["side"] != side_key or m["kind"] != "出牌":
                    continue
                info = lookup(cards, m["cid"])
                if info and info.get("cost") is not None and m["turn"] and info["cost"] > m["turn"]:
                    g["hints"].append("%s第 %d 回合打出 %d 费的「%s」" % (label, m["turn"], info["cost"], info["zh"]))
                    break
    if g["report"] and not g["partial"] and (g["report"]["ally_turn"], g["report"]["oppo_turn"]) != (my_turns, opp_turns):
        g["warnings"].append("按动作数出来的回合数（我 %d / 对手 %d）和结算记录（我 %d / 对手 %d）不一致，表里的回合号可能有偏差"
                             % (my_turns, opp_turns, g["report"]["ally_turn"], g["report"]["oppo_turn"]))
    if g["report"]:
        if g["partial"]:
            dm, do = g["report"]["ally_turn"] - my_turns, g["report"]["oppo_turn"] - opp_turns
            for m in moves:
                if m["side"] == "me":
                    m["turn"] += dm
                elif m["side"] == "opp":
                    m["turn"] += do
        g["my_turns"], g["opp_turns"] = g["report"]["ally_turn"], g["report"]["oppo_turn"]
        # 用结算记录核对先后手：谁的回合结束的 + 双方回合数
        if moves:
            last_side = moves[-1]["side"]
            at, ot = g["report"]["ally_turn"], g["report"]["oppo_turn"]
            if last_side == "me":
                rep_first = True if at == ot + 1 else (False if at == ot else None)
            else:
                rep_first = False if ot == at + 1 else (True if at == ot else None)
            if rep_first is not None:
                if g["first"] is None:
                    g["first"], g["first_why"] = rep_first, "按结算记录的双方回合数推出"
                elif rep_first != g["first"]:
                    g["warnings"].append("先后手两种算法不一致（抽牌顺序说%s，结算回合数说%s）" % ("先手" if g["first"] else "后手", "先手" if rep_first else "后手"))

    # 5) 胜负
    w = (game["result"] or "").lower()
    if w.startswith("win"):
        g["result"] = "胜"
    elif w.startswith("lose") or w.startswith("loss") or w.startswith("defeat"):
        g["result"] = "负"
    elif w.startswith("draw"):
        g["result"] = "平"
    elif game["result"]:
        g["result"] = "?" + game["result"]
    if g["result"] is None:
        # 第二信号：结算时加载的主战者皮肤 ally:True result:True = 赢家是我方
        for x in ev:
            if x["kind"] == "skin" and x["result"]:
                g["result"] = "胜" if x["ally"] else "负"
                break

    # 6) 卡组识别
    my_seen_ids = [c for c in g["my_seen"] + g["my_hand0"]]
    name, score, why = match_deck(my_seen_ids, my_decks, g["my_cls"], cards, cfg["my_min_seen"], cfg["my_min_score"], 0.0) if my_decks else (None, 0, "没有登记我的卡组")
    g["my_deck"] = name or (CLASS_NAMES.get(g["my_cls"], "未知职业") + ("（未登记）" if my_decks else ""))
    g["my_deck_why"] = why
    oname, oscore, owhy = match_deck(g["opp_seen"], archetypes, g["opp_cls"], cards, cfg["opp_min_seen"], cfg["opp_min_score"], cfg["opp_margin"])
    g["opp_deck"] = oname or UNKNOWN
    g["opp_deck_why"] = owhy
    return g


# ---------- 输出 ----------
def local_iso(ts):
    return dt.datetime.fromtimestamp(ts).astimezone().isoformat(timespec="seconds")


def fmt_clock(ts):
    return dt.datetime.fromtimestamp(ts).strftime("%m/%d %H:%M")


def write_outputs(games, cards, out_dir, season):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    with open(out / "games.jsonl", "w", encoding="utf-8") as fh:
        for g in games:
            fh.write(json.dumps(g, ensure_ascii=False) + "\n")
    head = ["对局编号", "时间", "我的卡组", "我的职业", "对手职业", "对手卡组", "先后手", "结果", "段位", "分组", "我的积分", "对手积分", "结束回合", "备注", "赛季"]
    with open(out / "games.csv", "w", encoding="utf-8-sig", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(head)
        for g in games:
            if g["result"] not in ("胜", "负"):
                continue
            opp_cards = []
            for c in dict.fromkeys(g["opp_seen"]):
                if not is_token(cards, c):
                    opp_cards.append(card_name(cards, c))
            note = "自动读取"
            if not g["ranked"]:
                note += "｜非天梯"
            if g["partial"]:
                note += "｜开头没存到"
            if g["first"] is None:
                note += "｜先后手没判出来"
            if g.get("mirror"):
                note += "｜同职业局，双方出牌归属把握较低"
            if g["opp_deck"] == UNKNOWN:
                note += "｜对手套路：" + g["opp_deck_why"]
            if opp_cards:
                note += "｜对手出过：" + "、".join(opp_cards[:14])
            rows.append([
                "bt-%d" % int(g["start"] * 1000), local_iso(g["start"]), g["my_deck"], CLASS_NAMES.get(g["my_cls"], ""),
                CLASS_NAMES.get(g["opp_cls"], ""), g["opp_deck"], ("先手" if g["first"] else "后手") if g["first"] is not None else "先手",
                g["result"], "", "", "", "", g["my_turns"] or "", note, season,
            ])
        wr.writerows(rows)
    # review.md：每一手
    lines = ["# 对局回顾（自动读取）", "", "时间是本机时间。记录文件里没有「换回合」事件，回合数是按双方动作的交替推出来的，可能偏差一回合；结算记录里的双方回合数更可靠。", ""]
    for g in reversed(games):
        res = g["result"] or "未完成"
        lines.append("## %s  %s（%s） 对 %s（%s）  %s  %s" % (
            fmt_clock(g["start"]), g["my_deck"], CLASS_NAMES.get(g["my_cls"], "?"), g["opp_deck"], CLASS_NAMES.get(g["opp_cls"], "?"),
            ("先手" if g["first"] else "后手") if g["first"] is not None else "先后手不明", res))
        meta = ["%s" % ("天梯" if g["ranked"] else ("进行中，还没打完" if g["result"] is None else "非天梯/未知模式")), "我方 %d 回合，对手 %d 回合" % (g["my_turns"], g["opp_turns"])]
        if g["end"]:
            meta.append("用时 %d 分 %02d 秒" % divmod(int(g["end"] - (g["cutin_end"] or g["start"])), 60))
        if g.get("skins"):
            meta.append("主战者皮肤：我 %s / 对手 %s" % (g["skins"].get("me") or "?", g["skins"].get("opp") or "?"))
        if g.get("ambiguous"):
            meta.append("按回合归属的出牌 %d 手（中立牌或同职业局）" % g["ambiguous"])
        meta.append("先后手依据：%s" % (g["first_why"] or "无"))
        meta.append("我的卡组依据：%s" % g["my_deck_why"])
        meta.append("对手套路依据：%s" % g["opp_deck_why"])
        if g["partial"]:
            meta.append("这局开头没存到（存档程序启动前的部分丢了），回合号从存到的地方数起")
        if g["warnings"]:
            meta.append("注意：" + "；".join(g["warnings"]))
        if g.get("hints"):
            meta.append("费用线索（巫师减费、龙族跳费会误报）：" + "；".join(g["hints"]))
        lines.append("- " + "；".join(meta))
        if g["my_hand0"]:
            lines.append("- 我的起手/换牌看到：" + "、".join(card_name(cards, c) for c in g["my_hand0"]))
        if g.get("opening"):
            lines.append("- 开局手牌事件（秒 / 谁 / 牌 / 新建）：" + "，".join("%.0f %s %s%s" % (o["dt"], {"me": "我", "opp": "敌", "pre": "亮"}.get(o["side"], "?"), o["cid"] if o["cid"] != "0" else "暗", "*" if o["create"] else "") for o in g["opening"]))
        lines.append("")
        lines.append("| 时刻 | 谁 | 回合 | 动作 | 牌 | 费 |")
        lines.append("|---|---|---|---|---|---|")
        for m in g["moves"]:
            info = lookup(cards, m["cid"])
            cost = info["cost"] if info and info.get("cost") is not None else ""
            lines.append("| %s | %s | %s | %s | %s | %s |" % (
                dt.datetime.fromtimestamp(m["t"]).strftime("%H:%M:%S"), "我" if m["side"] == "me" else ("对手" if m["side"] == "opp" else "?"),
                m["turn"] or "", m["kind"], card_name(cards, m["cid"]), cost))
        lines.append("")
    (out / "review.md").write_text("\n".join(lines), encoding="utf-8")
    # summary.txt
    agg = collections.defaultdict(lambda: [0, 0])
    for g in games:
        if g["result"] in ("胜", "负"):
            k = (g["my_deck"], CLASS_NAMES.get(g["opp_cls"], "?") + "·" + g["opp_deck"])
            agg[k][0] += 1
            agg[k][1] += g["result"] == "胜"
    s = ["我的卡组 | 对手 | 局数 | 胜 | 胜率"]
    for (a, b), (n, w) in sorted(agg.items()):
        s.append("%s | %s | %d | %d | %.0f%%" % (a, b, n, w, 100.0 * w / n))
    tot_n = sum(v[0] for v in agg.values())
    tot_w = sum(v[1] for v in agg.values())
    s.append("合计 | | %d | %d | %s" % (tot_n, tot_w, ("%.0f%%" % (100.0 * tot_w / tot_n)) if tot_n else "-"))
    (out / "summary.txt").write_text("\n".join(s) + "\n", encoding="utf-8")
    return rows


def run_parse(a):
    cards = load_cards(a.cards)
    my_decks = load_my_decks(a.decks)
    archetypes = load_archetypes(a.archetypes)
    cfg = {"my_min_seen": 3, "my_min_score": 0.75, "opp_min_seen": 2, "opp_min_score": 0.6, "opp_margin": 0.15}
    entries = load_raw(a.raw, a.since)
    segs = segment(entries)
    games = [analyze(s, cards, my_decks, archetypes, cfg) for s in segs]
    games = [g for g in games if g["moves"] or g["result"]]
    rows = write_outputs(games, cards, a.out, a.season)
    fin = [g for g in games if g["result"] in ("胜", "负")]
    print("读到 %d 条面包屑，切出 %d 局，其中有胜负的 %d 局（胜 %d），写入 %s" % (
        len(entries), len(games), len(fin), sum(1 for g in fin if g["result"] == "胜"), a.out))
    for g in games[-12:]:
        print("  %s %s 对 %s·%s %s %s" % (fmt_clock(g["start"]), g["my_deck"], CLASS_NAMES.get(g["opp_cls"], "?"), g["opp_deck"],
                                        ("先手" if g["first"] else "后手") if g["first"] is not None else "先后不明", g["result"] or "未完成"))
    return games


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("parse", "watch"):
        q = sub.add_parser(name)
        q.add_argument("--raw", required=True, help="存档程序写的 raw 目录（*.jsonl）")
        q.add_argument("--out", required=True, help="输出目录")
        q.add_argument("--cards", default=str(HERE / "cards_zh.json"))
        q.add_argument("--archetypes", default=str(HERE / "archetypes.json"))
        q.add_argument("--decks", default=None, help="我的卡组登记文件：每行「名字|卡组代码」")
        q.add_argument("--season", default="第10弹")
        q.add_argument("--since", default=None, help="只读这一天之后的 raw 文件，格式 YYYY-MM-DD")
        q.add_argument("--interval", type=int, default=60)
    a = p.parse_args(argv)
    if a.cmd == "parse":
        run_parse(a)
    else:
        while True:
            try:
                run_parse(a)
            except Exception as e:  # 不让一次解析错误停掉循环
                print("解析出错：%r" % (e,), file=sys.stderr)
            time.sleep(a.interval)


if __name__ == "__main__":
    main()
