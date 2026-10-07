"""How the cards are named in everything Salem reads: the common name with cost and stats.

The common names and costs come from the card glossary (claude/bot-architecture-design 469f714,
analysis/card-glossary.md, kept by another session: send it new entries, don't copy it here). Only
the cards of the games in this directory. Spilling Red and Depths of the Eld Blades are tokens the
glossary doesn't list yet; they are named here by the short Chinese name until it does.
Internal names (scripts, checks, card ids) stay the simulator's.
"""

# simulator's full Chinese name -> (common name, cost and stats)
COMMON = {
    "约束的《正义》·伊兰翠": ("正义", "10费 8/8"),
    "焦灰的安纳提玛·班德奈特": ("班德", "9费 9/9"),
    "金银绚烂·璐米欧儿&雅尔贞特": ("金银", "8费 6/6"),
    "禁牙的变貌·诺玛格达拉": ("牢头", "7费 5/6"),
    "断头的斩姬·相枛津": ("口人魔", "7费 5/4"),
    "世界的伙伴·佐伊": ("佐伊", "5费 5/5"),
    "古旧天刀·波菈莱": ("波菈莱", "2费 0/2"),
    "满面笑容的烹饪·琪米卡": ("琪米卡", "2费 2/1"),
    "掌握天空命运的少女·露莉亚": ("露莉亚", "2费 1/1"),
    "宣扬的龙人": ("宣扬的龙人", "2费 2/1"),
    "《世界》的呈现": ("《世界》的呈现", "5费 法术"),
    "日珥咆哮": ("日珥咆哮", "4费 法术"),
    "龙之启示": ("龙之启示", "3费 法术"),
    "焦龙的午睡": ("焦龙的午睡", "3费 法术"),
    "懒惰的波摇花": ("懒惰的波摇花", "2费 法术"),
    "赤流": ("赤流", "1费 法术，口人魔给的衍生牌"),
    "天刀深渊": ("天刀深渊", "2费 法术，波菈莱给的衍生牌"),
}


def common(full):
    """The common name (the simulator's name when the card isn't listed)."""
    return COMMON.get(full, (full, ""))[0]


def labelled(full):
    """The common name with cost and stats: 口人魔（7费 5/4）."""
    n, stats = COMMON.get(full, (full, ""))
    return f"{n}（{stats}）" if stats else n


def label_first(text):
    """Each card's first mention in the text (by common name, outside Salem's words in 「」) with its cost and stats."""
    masked = list(text)
    inside = False
    for i, ch in enumerate(text):                  # blank out quoted words so they are never matched
        if ch == "「":
            inside = True
        elif ch == "」":
            inside = False
        elif inside:
            masked[i] = "\0"
    masked = "".join(masked)
    firsts = sorted(((masked.find(n), n, s) for n, s in COMMON.values() if s and n in masked), reverse=True)
    for i, n, s in firsts:
        text = text[:i] + f"{n}（{s}）" + text[i + len(n):]
    return text


# short forms the older notes used, after the full names are replaced (Salem's words in 「」 are kept as they are)
SHORT = (("璐米欧儿&雅尔贞特", "金银"), ("璐米欧儿", "金银"), ("诺玛格达拉", "牢头"), ("诺玛", "牢头"),
         ("伊兰翠", "正义"), ("相枛津", "口人魔"), ("班德奈特", "班德"))


def rename(text):
    """Common names for every card in free text; quoted words (「…」) untouched."""
    parts = text.split("「")
    out = [_rename(parts[0])]
    for p in parts[1:]:
        quote, _, rest = p.partition("」")
        out.append("「" + quote + "」" + _rename(rest) if _ else "「" + p)
    return "".join(out)


def _rename(s):
    for full, (n, _) in sorted(COMMON.items(), key=lambda kv: -len(kv[0])):
        s = s.replace(full, n)
    for a, b in SHORT:
        s = s.replace(a, b)
    return s


def for_salem(probe):
    """A probe's text fields the way Salem reads them: names in why / turns / context; checks keep the simulator's names."""
    p = dict(probe)
    p["why"] = label_first(rename(p["why"]))
    if "salem_turn" in p:
        p["salem_turn"] = [rename(m) for m in p["salem_turn"]]
    if "bot_turn" in p:
        p["bot_turn"] = {k: {**v, "most_common": rename(v["most_common"])} for k, v in p["bot_turn"].items()}
    ctx = dict(p.get("context") or {})
    if "hand" in ctx:
        ctx["hand"] = [labelled(n) for n in ctx["hand"]]
    for k in ("board", "opp_board"):
        if k in ctx:
            ctx[k] = [f"{labelled(e.rsplit(' ', 1)[0])} 现 {e.rsplit(' ', 1)[1]}" if " " in e else labelled(e)
                      for e in ctx[k]]
    if ctx:
        p["context"] = ctx
    return p
