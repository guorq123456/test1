"""Text rendering of positions and actions, in Simplified Chinese.

Card names use the official Chinese names from the pool table (English for
cards without one, such as the demo cards). Keyword names follow the official
glossary.
"""
from __future__ import annotations

from svsim.core.actions import (Attack, EndTurn, Engage, Evolve, Fuse, Mulligan, PlayCard,
                                UseBonusPP)
from svsim.core.carddef import CardDef
from svsim.core.engine import apply, play_form
from svsim.core.enums import CardType, Keyword
from svsim.core.script import prop
from svsim.core.state import CardInstance, GameState, leader_of

KEYWORDS_ZH = [(Keyword.STORM, "疾驰"), (Keyword.RUSH, "突进"), (Keyword.WARD, "守护"),
               (Keyword.BANE, "毁灭"), (Keyword.DRAIN, "虹吸"), (Keyword.AMBUSH, "潜行"),
               (Keyword.INTIMIDATE, "威慑"), (Keyword.AURA, "灵气"), (Keyword.BARRIER, "屏障")]


def card_name(defn: CardDef) -> str:
    name = defn.name_zh or defn.name
    if defn.type == CardType.CREST:
        return f"纹章：{name}"
    if defn.type == CardType.FAITH:
        return f"信仰：{name}"
    return name


def keywords_zh(keywords: Keyword) -> str:
    return "、".join(zh for k, zh in KEYWORDS_ZH if keywords & k)


def _follower_status(state: GameState, c: CardInstance) -> str:
    if c.owner != state.active:
        return ""
    if prop(c, "cant_attack"):
        return "不能攻击"
    if c.attacks_made >= c.max_attacks:
        return "已攻击"
    fresh = c.entered_turn == state.turn
    if not fresh or c.keywords & Keyword.STORM:
        return "可攻击"
    if c.evolved or c.keywords & Keyword.RUSH:
        return "只能攻击随从"
    return "刚登场"


def card_line(state: GameState, c: CardInstance, in_hand: bool = False) -> str:
    """One card: name, cost (in hand), stats, keywords and state."""
    parts = [f"「{card_name(c.defn)}」"]
    if in_hand:
        parts.append(f"{c.cost}费" + (f"（原 {c.defn.cost}）" if c.cost != c.defn.cost else ""))
    if c.defn.is_follower:
        parts.append(f"{c.atk}/{c.life}" + (f"（上限 {c.max_life}）" if c.life < c.max_life else ""))
    if c.countdown is not None:
        parts.append(f"吟唱 {c.countdown}")
    if c.keywords:
        parts.append(keywords_zh(c.keywords))
    if c.super_evolved:
        parts.append("超进化")
    elif c.evolved:
        parts.append("已进化")
    if c.silenced:
        parts.append("无能力")
    if not in_hand and c.defn.is_follower:
        status = _follower_status(state, c)
        if status:
            parts.append(status)
    return " ".join(parts)


def render_state(state: GameState, viewer: int | None = None) -> str:
    """The position as `viewer` (default: the player to act) sees it."""
    me = state.active if viewer is None else viewer
    lines = [f"第 {state.turn} 回合（{'你的回合' if state.active == me else '对手的回合'}）"]
    for side, label in ((1 - me, "对手"), (me, "你")):
        p = state.players[side]
        head = (f"{label}：主战者 {p.leader_hp}/{p.leader_max_hp}  PP {p.pp}/{p.max_pp}  "
                f"进化点 {p.ep}  超进化点 {p.sep}  牌组 {len(p.deck)}  墓场 {p.shadows}")
        if side != me:
            head += f"  手牌 {len(p.hand)}"
        if p.extra_damage:
            head += f"  受到的伤害 +{p.extra_damage}"
        if p.damage_cap is not None:
            head += f"  每次最多受到 {p.damage_cap} 点伤害"
        lines.append(head)
        if p.leader_area:
            lines.append("  主战者区域：" + "；".join(card_line(state, c) for c in p.leader_area))
        lines.append("  战场：" + ("；".join(card_line(state, c) for c in p.field) or "（空）"))
        if side == me:
            lines.append("  手牌：" + ("；".join(card_line(state, c, in_hand=True) for c in p.hand)
                                     or "（空）"))
    return "\n".join(lines)


def _target_name(state: GameState, uid: int, chooser: int) -> str:
    leader = leader_of(uid)
    if leader is not None:
        return "敌方主战者" if leader != chooser else "己方主战者"
    for p in state.players:
        for zone, where in ((p.field, "场上"), (p.hand, "手牌中"), (p.leader_area, "")):
            for c in zone:
                if c.uid == uid:
                    side = "己方" if p.index == chooser else "敌方"
                    return f"{side}{where}的「{card_name(c.defn)}」"
    return f"#{uid}"


def _find(state: GameState, uid: int) -> CardInstance | None:
    for p in state.players:
        for c in p.field + p.hand + p.leader_area:
            if c.uid == uid:
                return c
    return None


def describe(state: GameState, action) -> str:
    """One action, named from `state` (the position before it is taken)."""
    me = state.active
    targets = lambda uids: "，选择 " + "、".join(_target_name(state, u, me) for u in uids) if uids else ""
    modes = lambda ms: f"，模式 {'+'.join(str(m + 1) for m in ms)}" if ms else ""
    if isinstance(action, PlayCard):
        card = _find(state, action.uid)
        form = play_form(state.players[me], card)
        how = ""
        if form is not None:
            if form.alt is not None:
                how = "（激奏）" if form.as_spell else "（结晶）"
            elif form.enhanced:
                how = f"（爆能强化 {form.enhanced}）"
        return f"使用「{card_name(card.defn)}」{how}{targets(action.targets)}{modes(action.modes)}"
    if isinstance(action, Attack):
        attacker = _find(state, action.attacker)
        return f"「{card_name(attacker.defn)}」攻击{_target_name(state, action.target, me)}"
    if isinstance(action, Evolve):
        card = _find(state, action.uid)
        word = "超进化" if action.super_ else "进化"
        return f"{word}「{card_name(card.defn)}」{targets(action.targets)}{modes(action.modes)}"
    if isinstance(action, Engage):
        card = _find(state, action.uid)
        return f"启动「{card_name(card.defn)}」{targets(action.targets)}{modes(action.modes)}"
    if isinstance(action, Fuse):
        card = _find(state, action.uid)
        fed = "、".join(f"「{card_name(_find(state, u).defn)}」" for u in action.cards)
        return f"把 {fed} 融合到「{card_name(card.defn)}」"
    if isinstance(action, UseBonusPP):
        return "使用额外能量点"
    if isinstance(action, EndTurn):
        return "结束回合"
    if isinstance(action, Mulligan):
        return f"换牌：{list(action.indices)}"
    return repr(action)


def describe_line(state: GameState, line: list) -> list[str]:
    """A sequence of actions, each named from the position it is taken in."""
    s, out = state.clone(), []
    for action in line:
        out.append(describe(s, action))
        if s.over:
            break
        apply(s, action)
    return out
