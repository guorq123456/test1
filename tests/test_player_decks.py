"""The page's own decks (ui.deckbuilder): deck checks, codes, the bot's decks, and games with a custom deck."""
import json

import pytest

from svsim.cards import decks
from svsim.ui import deckbuilder
from svsim.ui.session import GENERIC, LEVELS, Session, level_spec


def _bot(i=0):
    return deckbuilder.bot_decks()["decks"][i]


def test_bot_decks_play_and_are_one_per_class():
    bd = deckbuilder.bot_decks()["decks"]
    assert bd and all(len(deckbuilder.deck_from(d)) == 40 for d in bd)    # even one the search left a card over
    assert len({d["craft"] for d in bd}) == len(bd)


def test_reprints_share_the_name_limit():
    from collections import defaultdict
    from svsim.cards.pool import collectible
    names = defaultdict(list)
    for c in collectible():
        names[(c.name, c.craft)].append(c)
    a, b = next(v for v in names.values() if len(v) > 1)[:2]
    others = [c.card_id for c in collectible(a.craft) if c.name != a.name and c.craft == a.craft][:12]
    ids = [a.card_id] * 3 + [b.card_id] + [i for i in others for _ in range(3)][:36]
    assert any("重印" in p for p in deckbuilder.problems(ids))


def test_pool_is_rotation_without_tokens():
    p = deckbuilder.pool()
    assert all(c["set"] != 10004 for c in p["cards"])
    assert sum(c["new"] for c in p["cards"]) == 76


def test_check_names_the_problems():
    code = next(d["code"] for d in deckbuilder.bot_decks()["decks"] if not d["problems"] and d["craft"] == 2)
    assert deckbuilder.check(code)["problems"] == []
    assert deckbuilder.check("https://example/deck/detail/?hash=" + code + "&lang=chs")["problems"] == []
    dragon = decks.RAMP_T_HASH.split(".")[2]                      # a Dragon card in a Sword deck
    assert any("不能放进皇家卡组" in p for p in deckbuilder.check(code[:-5] + "." + dragon)["problems"])
    short = deckbuilder.check(code.rsplit(".", 1)[0])
    assert any("39 张" in p for p in short["problems"])
    old = deckbuilder.check(decks.RAMP_T_HASH)                     # set 4 cards rotated out
    assert any("退环境" in p for p in old["problems"]) and old["others"]
    with pytest.raises(ValueError):
        deckbuilder.check("not a code")


def test_custom_deck_plays_the_generic_bot_and_resumes():
    s = Session()
    mine = {"name": "我的", "code": _bot(0)["code"]}
    v = s.start(mine, {"name": "对面", "code": _bot(3)["code"]}, "strong", 7, "you")
    assert v["decks"] == ["我的", "对面"] and s.record["ai"] == GENERIC["strong"] and s.record["bot"]["generic"]
    while not s.state.over and len(s.record["actions"]) < 25:
        if s.state.active == 0:
            v = s.mulligan([]) if v.get("mulligan") else s.act(0)
        else:
            v = s.ai_step()
    again = Session().resume(json.loads(json.dumps(s.record)))
    assert again["decks"] == ["我的", "对面"]


def test_named_decks_keep_their_levels():
    assert level_spec("normal", "ramp-t", "elf-t") == LEVELS["normal"]
    assert level_spec("normal", "custom", "elf-t") == GENERIC["normal"]


def test_illegal_custom_deck_is_refused():
    with pytest.raises(ValueError):
        Session().start({"name": "旧", "code": decks.RAMP_T_HASH}, "ramp", "fast", 1)
