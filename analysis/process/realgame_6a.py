"""Item 6a: card-level consistency between Salem's real games and the simulator (pre-registration: REALGAME.md).

Reads /mnt/project-files/shadowverse/salem-games/tracker/games.jsonl. Check only, never training. Prints aggregate
counts and every flag; with --out writes the per-game flag table (keep it in /mnt/project-files, not in the repo).

    python analysis/process/realgame_6a.py [--games PATH] [--out PATH.md]
"""
import argparse
import collections
import importlib
import json
import pkgutil
import types

import svsim.cards as cards_pkg
from svsim.cards.pool import CardDef
from svsim.core import engine as ENG
from svsim.core import script as S

GAMES = "/mnt/project-files/shadowverse/salem-games/tracker/games.jsonl"
SKIP = {"deckcode", "decks", "demo"}
CLS = {0: "中立", 1: "精灵", 2: "皇家护卫", 3: "巫师", 4: "龙族", 5: "梦魇", 6: "主教", 7: "超越者"}

for m in pkgutil.iter_modules(cards_pkg.__path__):
    if m.name not in SKIP:
        importlib.import_module(f"svsim.cards.{m.name}")

def all_defs():
    out = {}
    for m in pkgutil.iter_modules(cards_pkg.__path__):
        if m.name in SKIP:
            continue
        mod = importlib.import_module(f"svsim.cards.{m.name}")
        for v in vars(mod).values():
            if isinstance(v, CardDef):
                out[v.card_id] = v
    return out


def table_defs():
    import pathlib
    d = {}
    for f in sorted(pathlib.Path(cards_pkg.__path__[0], "data").glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for c in (data if isinstance(data, list) else data.values()):
            d[c["id"]] = c
    return d


TABLE = table_defs()
CONST = all_defs()


def base_id(cid):
    """The simulator's id for a breadcrumb id: a leading 7 becomes 1; last digit 1 (alternate art) becomes 0 and 3
    becomes 2. Last digit 2 is a card's alternate play form (Crystallize, Accelerate), which has its own cost, so it is
    kept. The tracker's own base_id folds 2 into 0 too, which is right for deck matching but not for costs."""
    s = str(cid)
    if s.startswith("7"):
        s = "1" + s[1:]
    if len(s) == 8 and s[-1] in "13":
        s = s[:-1] + {"1": "0", "3": "2"}[s[-1]]
    return int(s)


def is_token(i):
    return str(i).startswith("9") or bool(TABLE.get(i, {}).get("token"))


def code_names(obj, seen):
    """All names a class or function's code refers to, following same-package base classes and helper functions."""
    names, mods = set(), []
    stack = [obj]
    while stack:
        o = stack.pop()
        if id(o) in seen:
            continue
        seen.add(id(o))
        if isinstance(o, type):
            for b in o.__mro__:
                if b.__module__.startswith("svsim.cards") or b.__module__ == "svsim.core.script":
                    for v in vars(b).values():
                        f = getattr(v, "__func__", v)
                        if isinstance(f, types.FunctionType):
                            stack.append(f)
                        elif isinstance(v, property) and v.fget:
                            stack.append(v.fget)
            continue
        if not isinstance(o, types.FunctionType):
            continue
        codes = [o.__code__]
        g = o.__globals__
        while codes:
            c = codes.pop()
            names.update(c.co_names)
            codes.extend(k for k in c.co_consts if isinstance(k, types.CodeType))
        for n in list(names):
            v = g.get(n)
            if isinstance(v, types.ModuleType):
                mods.append(v)
            elif isinstance(v, (types.FunctionType, type)) and getattr(v, "__module__", "").startswith("svsim.cards"):
                stack.append(v)
            elif isinstance(v, CardDef):
                names.add(f"#{v.card_id}")
    for mod in mods:
        if mod.__name__.startswith("svsim.cards"):
            for n in list(names):
                v = getattr(mod, n, None)
                if isinstance(v, CardDef):
                    names.add(f"#{v.card_id}")
    return names


PROFILE = {}
REFS = {cid: {int(n[1:]) for n in code_names(type(inst), set()) if n.startswith("#")} for cid, inst in S._SCRIPTS.items()}


def makes(cid, depth=3):
    """Tokens a card can create, also through a card it creates that is not in a deck: a token, or an alternate form
    (last digit 2: crests, crystallized forms), e.g. 雾卷花·茎白 -> its crest -> 神圣猎鹰."""
    out, frontier = set(), {cid}
    for _ in range(depth):
        nxt = set()
        for c in frontier:
            for r in REFS.get(c, ()):
                if is_token(r):
                    out.add(r)
                if (is_token(r) or str(r).endswith("2")) and r not in out | {cid}:
                    nxt.add(r)
        frontier = nxt
    return out


for cid, inst in S._SCRIPTS.items():
    names = code_names(type(inst), set())
    PROFILE[cid] = {
        "makes": makes(cid),
        "evolves": "evolve" in names,
        "max_pp": "gain_max_pp" in names,
        "recover": "recover_pp" in names,
        "cost": bool({"add_cost", "set_cost", "halve_cost", "cost_mods"} & names),
    }


def prof(cid):
    return PROFILE.get(cid, {"makes": set(), "evolves": False, "max_pp": False, "recover": False, "cost": False})


def name(cid):
    c = TABLE.get(cid)
    return f"{c['zh']}（{c['cost']}费）" if c else f"#{cid}"


def check(games):
    flags = []
    tok_total = tok_ok = 0
    ids_total, missing = 0, collections.Counter()
    for gi, g in enumerate(games):
        tag = f"第{gi + 1}局 {g['my_deck']} 对 {g['opp_deck']}"
        if g.get("mirror"):
            tag += "（同职业局，出牌归属靠回合推断）"
        if g.get("partial"):
            tag += "（记录不完整）"
        if any("回合号" in w or "回合数" in w for w in g.get("warnings", [])):
            tag += "（解析器已警告回合号可能有偏差）"
        clean_first = g.get("first") is not None and "另一方" not in (g.get("first_why") or "") and "把握" not in (g.get("first_why") or "")
        played = {"me": [], "opp": []}
        for m in g["moves"]:
            played[m["side"]].append(m)
        seen = {"me": {base_id(c) for c in g["my_seen"] + g["my_hand0"]} | {base_id(m["cid"]) for m in played["me"]},
                "opp": {base_id(c) for c in g["opp_seen"]} | {base_id(m["cid"]) for m in played["opp"]}}
        # 1 pool
        for side in seen:
            for c in seen[side]:
                ids_total += 1
                if c not in TABLE:
                    missing[c] += 1
                    flags.append((tag, "卡池", side, f"模拟器没有这张卡 #{c}"))
        # 2 created cards
        for side in ("me", "opp"):
            other = "opp" if side == "me" else "me"
            for c in sorted(x for x in seen[side] if is_token(x)):
                tok_total += 1
                own = [x for x in seen[side] if c in prof(x)["makes"]]
                oth = [x for x in seen[other] if c in prof(x)["makes"]]
                if own or oth:
                    tok_ok += 1
                else:
                    flags.append((tag, "衍生物", side, f"{name(c)} 找不到本局能生成它的牌"))
        # 3 evolve timing, 4 PP budget
        for side in ("me", "opp"):
            first = g.get("first") if side == "me" else (None if g.get("first") is None else not g["first"])
            by_turn = collections.defaultdict(list)
            for m in played[side]:
                by_turn[m["turn"]].append(m)
            gains = 0
            for turn in sorted(by_turn):
                ms = by_turn[turn]
                for m in ms:
                    if m["kind"] in ("进化", "超进化") and first is not None:
                        need = (ENG.SUPER_EVOLVE_TURN if m["kind"] == "超进化" else ENG.EVOLVE_TURN)[first]
                        if turn < need:
                            effect = [x for x in {base_id(y["cid"]) for y in played[side] if y["turn"] <= turn} if prof(x)["evolves"]]
                            why = "可由效果进化：" + "、".join(name(x) for x in effect) if effect else "没有能效果进化的牌"
                            flags.append((tag, "进化时机", side, f"己方第 {turn} 回合{m['kind']} {name(base_id(m['cid']))}，规则最早第 {need} 回合（{'先手' if first else '后手'}；{why}；先后手判定：{'清楚' if clean_first else g.get('first_why')}）"))
                plays = [base_id(m["cid"]) for m in ms if m["kind"] == "出牌"]
                cost = sum(TABLE.get(c, {}).get("cost", 0) for c in plays)
                avail = min(10, turn) + gains + (1 if first is False else 0)
                if cost > avail:
                    # Second, generous level: cards whose cost a script can change (their own script, or any card of
                    # this side played up to this turn) count 0; a token counts 0 when its generator was played this
                    # turn before it (it may have been summoned, which the breadcrumb also logs as a play); each PP
                    # recovery or max-PP card played this turn adds 2.
                    so_far = {base_id(y["cid"]) for y in played[side] if y["turn"] <= turn and y["kind"] == "出牌"}
                    changers = [x for x in so_far if prof(x)["cost"]]
                    low, before, why = 0, set(), []
                    for c in plays:
                        made = is_token(c) and any(c in prof(x)["makes"] for x in before)
                        if prof(c)["cost"] or changers or made:
                            why.append(name(c) + ("（自带减费）" if prof(c)["cost"] else "（衍生，可能是召唤）" if made else "（有减费牌）"))
                        else:
                            low += TABLE.get(c, {}).get("cost", 0)
                        before.add(c)
                    extra = 2 * sum(1 for m in ms if m["kind"] in ("出牌", "进化", "超进化")
                                    and (prof(base_id(m["cid"]))["recover"] or prof(base_id(m["cid"]))["max_pp"]))
                    level = "PP·未解释" if low > avail + extra else "PP·可解释"
                    flags.append((tag, level, side, f"己方第 {turn} 回合打出 {cost} 费（" + "、".join(name(c) for c in plays) + f"），可用约 {avail}"
                                  + (f"，回复或加上限约 +{extra}" if extra else "") + f"；不能减费的部分 {low} 费；可能的解释：" + ("、".join(why) if why else "无")))
                gains += sum(1 for c in plays if prof(c)["max_pp"])
    return flags, (tok_ok, tok_total), (ids_total, missing)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", default=GAMES)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    games = [json.loads(line) for line in open(a.games, encoding="utf-8")]
    flags, (tok_ok, tok_total), (ids_total, missing) = check(games)
    print(f"{len(games)} 局；脚本数 {len(PROFILE)}；卡表 {len(TABLE)}")
    print(f"卡池：{ids_total} 个（局×方×卡）编号，模拟器缺 {sum(missing.values())}：{dict(missing)}")
    print(f"衍生物：{tok_ok}/{tok_total} 找得到生成它的牌")
    by = collections.Counter(f[1] for f in flags)
    print("标记：", dict(by))
    lines = [f"| {t} | {k} | {'我方' if s == 'me' else '对手'} | {d} |" for t, k, s, d in flags]
    for line in lines:
        print(line)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write("| 对局 | 检查 | 方 | 内容 |\n|---|---|---|---|\n" + "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
