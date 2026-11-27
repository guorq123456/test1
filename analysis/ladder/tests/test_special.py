"""Special periods (S27, A62): the team claim, room on a team, and the team's decks only. No games are played."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
from ladder import special, submit  # noqa: E402
from ladder.pool import Pool, list_key  # noqa: E402

MRG, LVH, RC, CR = "MURASH GAMING", "レバンガ北海道", "REJECT", "Crazy Raccoon"


@pytest.fixture
def p1(tmp_path, monkeypatch):
    """A pool in period 1 (a deck period) made special with period 3's round."""
    monkeypatch.setattr(special, "SPECIAL", {1: special.SPECIAL[3]})
    special.teams.cache_clear()
    pool = Pool.create(tmp_path / "pool", seeds=(99001460, 99001470), rng_seed=1)
    pool.advance()
    yield pool
    special.teams.cache_clear()


def claim(i, player, team, period=1, verdict="收下"):
    return {"ev": "receipt", "id": f"S-{i:04d}", "player": player, "period": period, "kind": "team", "team": team,
            "verdict": verdict}


def team_sub(team):
    return {"kind": "team", "meta": {"type": "选队", "team": team}}


def test_period_3_round():
    special.teams.cache_clear()
    t = special.teams(3)
    assert sorted(t) == sorted([MRG, LVH, RC, CR])
    assert all(sorted(by) == list(range(1, 8)) and all(len(e["ids"]) == 40 for e in by.values()) for by in t.values())
    assert t[LVH][1]["ids"] == t[RC][1]["ids"]                  # the one list two teams share (forest)
    keys = {list_key(e["ids"]) for by in t.values() for e in by.values()}
    assert len(keys) == 27
    for by in t.values():                                       # every list is legal as the simulator has it
        for e in by.values():
            assert submit.check_deck(e["code"])[1] == []


def test_claims_first_come(p1):
    assert special.check_claim(team_sub(MRG), "astra", p1, [])[0] == []
    problems, _ = special.check_claim(team_sub("ZETA DIVISION"), "astra", p1, [])
    assert problems and "能选的是" in problems[0]
    lines = [claim(1, "astra", MRG)]
    problems, _ = special.check_claim(team_sub(CR), "astra", p1, lines)
    assert problems and "一期只选一次" in problems[0]
    lines += [claim(2, "sol", MRG)]
    problems, _ = special.check_claim(team_sub(MRG), "opus", p1, lines)
    assert problems and "最多 2 个" in problems[0]
    assert special.check_claim(team_sub(CR), "opus", p1, lines)[0] == []
    refused = [claim(1, "astra", MRG, verdict="拒收")]          # a refused claim holds nothing
    assert special.check_claim(team_sub(MRG), "astra", p1, refused)[0] == []
    other = [claim(1, "astra", MRG, period=2)]                  # nor one of another period
    assert special.check_claim(team_sub(MRG), "astra", p1, other)[0] == []


def test_a_shared_list_counts_against_both_teams(p1):
    lines = [claim(1, "astra", LVH), claim(2, "sol", RC)]       # their forest list is the same one: 2 already
    problems, _ = special.check_claim(team_sub(LVH), "opus", p1, lines)
    assert len(problems) == 1 and "精灵卡表放不下" in problems[0]
    problems, _ = special.check_claim(team_sub(RC), "opus", p1, lines)
    assert len(problems) == 1 and "精灵卡表放不下" in problems[0]


def test_a_list_already_in_the_pool_leaves_one_place(p1):
    abyss = special.teams(1)[MRG][5]["ids"]
    p1.enter(abyss, "bot:mcts:100+plan", "fable-ultracode")      # an older member (here: this period's, not a claim)
    assert special.check_claim(team_sub(MRG), "astra", p1, [])[0] == []
    problems, _ = special.check_claim(team_sub(MRG), "sol", p1, [claim(1, "astra", MRG)])
    assert len(problems) == 1 and "梦魇卡表放不下" in problems[0]


def test_an_entered_claimed_deck_is_not_counted_twice(p1):
    lines = [claim(1, "astra", CR)]
    forest = special.teams(1)[CR][1]["ids"]
    p1.enter(forest, "bot:mcts:100+plan", "astra")              # astra's CR forest deck is in: the claim already held it
    assert special.check_claim(team_sub(CR), "sol", p1, lines)[0] == []


def test_new_decks_only_from_the_team(p1):
    t = special.teams(1)
    sword = t[CR][2]["ids"]
    sub = {"kind": "deck", "meta": {"member": "CR 皇家"}, "deck_ids": list(reversed(sword))}
    problems, info = submit.check_slots(sub, "astra", p1, [])
    assert any("先交「选队」" in p for p in problems)
    problems, info = submit.check_slots(sub, "astra", p1, [claim(1, "astra", CR)])
    assert problems == [] and info["team"] == CR and info["craft"] == 2   # the same 40 cards in any order
    other = {"kind": "deck", "meta": {"member": "MRG 皇家"}, "deck_ids": t[MRG][2]["ids"]}
    problems, _ = submit.check_slots(other, "astra", p1, [claim(1, "astra", CR)])
    assert any("不是你选的队" in p for p in problems)


def test_not_a_special_period(tmp_path, monkeypatch):
    special.teams.cache_clear()
    code = special.teams(3)[MRG][2]["code"]
    monkeypatch.setattr(special, "SPECIAL", {})
    pool = Pool.create(tmp_path / "pool", seeds=(99001460, 99001470), rng_seed=1)
    pool.advance()
    problems, _ = special.check_claim(team_sub(MRG), "astra", pool, [])
    assert problems and "不是特殊期" in problems[0]
    ids = submit.check_deck(code)[0]
    problems, info = submit.check_slots({"kind": "deck", "meta": {"member": "x"}, "deck_ids": ids}, "astra", pool, [])
    assert problems == [] and "team" not in info                  # an ordinary deck period: any legal list


def test_a_claim_is_received_without_games(p1, tmp_path):
    d = tmp_path / "in" / "选队"
    d.mkdir(parents=True)
    (d / "submission.json").write_text(json.dumps({"type": "选队", "team": CR}, ensure_ascii=False), encoding="utf-8")
    assert submit.precheck(d)["ok"]
    subs = tmp_path / "subs"
    rec = submit.receive(d, "astra", p1.dir, subs)
    assert rec["verdict"] == "收下" and rec["kind"] == "team" and rec["team"] == CR and rec["smoke_seeds"] == []
    assert "队：Crazy Raccoon（这一期你就是这个队了）" in (subs / rec["id"] / "receipt.md").read_text(encoding="utf-8")
    again = submit.receive(d, "astra", p1.dir, subs)
    assert again["verdict"] == "拒收" and any("一期只选一次" in r for r in again["reasons"])
    st = submit.status(subs, p1.dir, "astra")
    assert st["team"] == CR
    assert "你选的队：Crazy Raccoon" in submit.status_text(st, submit.ledger(subs))
    assert submit.status(subs, p1.dir, "sol")["team"] is None
    bad = tmp_path / "in" / "空队"
    bad.mkdir()
    (bad / "submission.json").write_text(json.dumps({"type": "选队"}), encoding="utf-8")
    with pytest.raises(submit.Refused):
        submit.read_dir(bad)
    rec = submit.receive(bad, "sol", p1.dir, subs)
    assert rec["verdict"] == "拒收" and rec["kind"] == "team"


def test_review_slips_a_name_a_neutral_deck_a_bom(p1, tmp_path):
    # 11-24 review: a name with stray spaces or other case is the team; a claimant's all-neutral deck is refused, not
    # a crash; a 选队 saved with a BOM says so instead of asking for strategy.py, notes.md and evidence.md
    problems, info = special.check_claim(team_sub(" crazy  raccoon "), "astra", p1, [])
    assert problems == [] and info["team"] == CR
    assert special.check_claim(team_sub("CRZ"), "astra", p1, [])[0]
    neutral = {"kind": "deck", "meta": {"member": "x"}, "deck_ids": [10501110] * 40}
    problems, _ = submit.check_slots(neutral, "astra", p1, [claim(1, "astra", CR)])
    assert any("不是你选的队" in p for p in problems)
    d = tmp_path / "名字"
    d.mkdir()
    for name, ok in (("Crazy raccoon ", True), ("LVH", False)):
        (d / "submission.json").write_text(json.dumps({"type": "选队", "team": name}, ensure_ascii=False),
                                           encoding="utf-8")
        assert submit.precheck(d)["ok"] is ok
    (d / "submission.json").write_text(json.dumps({"type": "选队", "team": CR}, ensure_ascii=False),
                                       encoding="utf-8-sig")
    res = submit.precheck(d)
    assert not res["ok"] and len(res["problems"]) == 1 and "读不了" in res["problems"][0]


# --- period 4: three blueprints (Salem 11-27) ---------------------------------------------------------------------
# No game is played here except in test_a_blueprint_deck_is_received_and_kept_out_of_the_pool: 1 load-check game and
# 2 smoke deals (each played by the submission and by the default strategy: 4 games), seeds 92648000-92648049.

P4_SEEDS = (92648000, 92648050)
FOREST, DRAGON, HAVEN = "快攻妖精", "跳费龙", "兔子教"


@pytest.fixture
def p4(tmp_path):
    """A pool in period 4: the pool (pool.py, locked) calls it merged; special period 4 for the players."""
    pool = Pool.create(tmp_path / "pool", seeds=(99001460, 99001470), rng_seed=1)
    while pool.period < 4:
        pool.advance(force="test")
    return pool


def changed(name, k):
    """The blueprint `name` with k cards changed: one copy each of its first k kinds out, k cards of the same class
    from period 3's lists (none of the blueprint's, at most 3 of each) in. Legal as the simulator has it."""
    b = special.blueprints(4)[name]
    ids = list(b["ids"])
    for c in sorted(set(ids))[:k]:
        ids.remove(c)
    others = sorted({c for by in special.teams(3).values() for c in by[b["craft"]]["ids"]} - set(b["ids"]))
    return ids + [c for c in others for _ in range(3)][:k]


def deck_sub(ids, member="一号"):
    return {"kind": "deck", "meta": {"member": member}, "deck_ids": list(ids)}


def p4_receipt(i, player, name, member, verdict="收下", period=4, changes=0):
    b = special.blueprints(4)[name]
    return {"ev": "receipt", "id": f"S-{i:04d}", "player": player, "period": period, "kind": "deck",
            "verdict": verdict, "craft": b["craft"], "member": member,
            "blueprint": {"name": name, "craft": b["craft"], "max_changes": b["max_changes"], "changes": changes,
                          "out": [], "in": []}}


def test_period_4_blueprints_and_flags():
    bps = special.blueprints(4)
    assert list(bps) == [FOREST, DRAGON, HAVEN]
    assert [(b["craft"], b["max_changes"]) for b in bps.values()] == [(1, 7), (4, 7), (6, 6)]
    guide = (HERE.parent / "public" / "special-P4.md").read_text(encoding="utf-8")
    for b in bps.values():
        ids, problems = submit.check_deck(b["code"])
        assert problems == [] and sorted(ids) == b["ids"] and len(ids) == 40
        assert b["code"] in guide                                   # the players' guide gives the same codes
    assert special.style(3) == "teams" and special.style(4) == "blueprints" and special.style(5) is None
    assert not special.takes_updates(4) and special.takes_updates(5) and not special.takes_updates(3)
    assert special.admits(3) and not special.admits(4) and special.admits(5)
    assert special.freezes_pool(3) and not special.freezes_pool(4) and special.first_merged() == 5
    assert special.SPECIAL[4]["eval_seeds"] == (96310000, 96410000)
    assert sorted(special.all_team_names()) == sorted([MRG, LVH, RC, CR])     # period 3's teams only
    assert special.kind_zh(4, "合并期") == "特殊期" and special.kind_zh(3, "卡组期") == "卡组期"


def test_changes_are_counted_by_cards():
    want = special.blueprints(4)[FOREST]["ids"]
    x, z = 10501110, 11014110                                           # 3 and 2 copies in the blueprint
    y = sorted({c for by in special.teams(3).values() for c in by[1]["ids"]} - set(want))[0]
    deck = list(want)
    deck.remove(x), deck.remove(x)
    got = special.compare(deck + [y, y], want)                          # 2 X for 2 Y: 2
    assert got["changes"] == 2 and [r[0::2] for r in got["out"]] == [[x, 2]] and [r[0::2] for r in got["in"]] == [[y, 2]]
    assert got["out"][0][1] == "挥毫的怪物"
    deck = list(want)
    deck.remove(x)
    assert special.compare(deck + [z], want)["changes"] == 1           # one X out, the third Z in: 1
    same = special.compare(list(reversed(want)), want)
    assert same["changes"] == 0 and same["out"] == [] and same["in"] == []
    got = special.compare(changed(FOREST, 3), want)
    assert got["changes"] == 3 and sum(r[2] for r in got["out"]) == 3 and sum(r[2] for r in got["in"]) == 3
    assert special.describe({"name": FOREST, "max_changes": 7, **got}).startswith("和蓝本快攻妖精比改了 3 张（上限 7 张）：去掉 ")
    assert special.describe({"name": FOREST, "max_changes": 7, **same}) == "和蓝本快攻妖精比改了 0 张（上限 7 张），和蓝本一样"


def test_the_change_caps(p4):
    for name, ok, bad in ((FOREST, 7, 8), (DRAGON, 7, 8), (HAVEN, 6, 7)):
        problems, info = submit.check_slots(deck_sub(changed(name, ok)), "astra", p4, [])
        assert problems == [], (name, problems)
        assert info["blueprint"]["name"] == name and info["blueprint"]["changes"] == ok
        assert info["craft"] == special.blueprints(4)[name]["craft"] and info["uses_slot"]
        problems, info = submit.check_slots(deck_sub(changed(name, bad)), "astra", p4, [])
        cap = special.blueprints(4)[name]["max_changes"]
        assert len(problems) == 1 and f"和蓝本{name}比改了 {bad} 张（上限 {cap} 张）" in problems[0], problems
        assert "超过上限" in problems[0] and info["blueprint"]["changes"] == bad
    problems, info = submit.check_slots(deck_sub(special.blueprints(4)[HAVEN]["ids"]), "astra", p4, [])
    assert problems == [] and info["blueprint"]["changes"] == 0                 # the blueprint as given


def test_other_classes_teams_and_updates_are_refused_in_period_4(p4):
    sword = special.teams(3)[CR][2]["ids"]
    problems, info = submit.check_slots(deck_sub(sword), "astra", p4, [])
    assert len(problems) == 1 and "只收这几副：快攻妖精（精灵）、跳费龙（龙族）、兔子教（主教）" in problems[0]
    assert "皇家护卫的新卡组这一期不收" in problems[0] and info["blueprint"] is None
    problems, _ = special.check_claim(team_sub(MRG), "astra", p4, [])
    assert problems == ["第 4 期是特殊期，但这一期不选队：直接交新卡组（special-P4.md）"]
    forest = special.blueprints(4)[FOREST]["ids"]
    mid = p4.enter(forest, "bot:mcts:100+plan", "astra")                       # an older member (here entered now)
    admitted = [{"ev": "admit", "player": "astra", "member": "老妖", "mid": mid}]
    problems, info = submit.check_slots({"kind": "update", "meta": {"member": "老妖"}}, "astra", p4, admitted)
    assert problems == ["第 4 期是特殊期，不收老成员改打法，第 5 期起合并期，那时再交（special-P4.md）"]
    assert "mid" not in info


def test_one_deck_per_blueprint_no_list_cap_and_names_taken(p4):
    forest = special.blueprints(4)[FOREST]["ids"]
    p4.enter(forest, "bot:mcts:100+plan", "fable")                             # the blueprint held twice in the pool
    p4.enter(forest, "bot:mcts:100+plan", "sol")
    problems, info = submit.check_slots(deck_sub(forest), "astra", p4, [])
    assert problems == [] and info["warnings"] == []                            # no list cap, no same-list note
    lines = [p4_receipt(1, "astra", FOREST, "妖一")]
    problems, _ = submit.check_slots(deck_sub(changed(FOREST, 1), "妖二"), "astra", p4, lines)
    assert any("这一期你的精灵已经交过一副、收下了（S-0001）" in p for p in problems)
    problems, _ = submit.check_slots(deck_sub(special.blueprints(4)[DRAGON]["ids"], "妖一"), "astra", p4, lines)
    assert any("成员名 '妖一' 你已经用过了" in p for p in problems)               # kept out of the pool, still taken
    assert submit.check_slots(deck_sub(special.blueprints(4)[DRAGON]["ids"], "妖一"), "sol", p4, lines)[0] == []
    refused = [p4_receipt(1, "astra", FOREST, "妖一", verdict="拒收")]          # a refused one leaves both open
    assert submit.check_slots(deck_sub(forest, "妖一"), "astra", p4, refused)[0] == []
    p4.advance(force="test")                                                    # period 5: merged
    problems, _ = submit.check_slots({"kind": "update", "meta": {"member": "妖一"}}, "astra", p4, lines)
    assert problems == ["'妖一' 是特殊期收下、没进池子的新卡组（S-0001），池子里没有这个成员，不能改打法"]
    problems, _ = submit.check_slots(deck_sub(changed(FOREST, 2), "妖一"), "astra", p4, lines)
    assert problems == ["成员名 '妖一' 你已经用过了"]                             # a new deck of period 5: taken too
    assert submit.check_slots(deck_sub(changed(FOREST, 2), "妖二"), "astra", p4, lines)[0] == []


def test_period_4_receipts_status_admit_and_precheck(p4, tmp_path, capsys):
    subs = tmp_path / "subs"
    rec = p4_receipt(1, "astra", HAVEN, "兔", changes=2)
    rec["blueprint"].update(out=[[10062210, "羽翼石像", 2]], **{"in": [[10061210, "投影鸟像", 2]]})
    rec.update(time="t", version="v", reasons=[], warnings=[], checks=[], dir=str(tmp_path / "兔"))
    submit._append(subs, rec)
    text = submit.receipt_text(rec)
    assert "- 蓝本：和蓝本兔子教比改了 2 张（上限 6 张）：去掉 羽翼石像（10062210）×2；换上 投影鸟像（10061210）×2" in text
    assert special.NOT_IN_POOL in text
    assert special.NOT_IN_POOL not in submit.receipt_text(dict(rec, verdict="拒收", reasons=["[卡组] x"]))
    with pytest.raises(SystemExit, match="先不进池子"):
        submit.admit(subs, "S-0001", p4.dir)
    assert [m for m in Pool(p4.dir).members.values() if m.owner == "astra"] == []
    st = submit.status(subs, p4.dir, "astra")
    assert st["kind"] == "merged" and st["kind_zh"] == "特殊期" and "classes_open" not in st
    assert [(d["name"], d["receipt"], d["changes"]) for d in st["decks"]] == [(FOREST, None, None),
                                                                            (DRAGON, None, None), (HAVEN, "S-0001", 2)]
    text = submit.status_text(st, submit.ledger(subs))
    assert text.startswith("# 第 4 期（特殊期）你的提交")
    assert "新卡组已经收下的：兔子教（S-0001，和蓝本比改了 2 张）" in text
    assert "还没交的：快攻妖精（精灵，最多改 7 张）、跳费龙（龙族，最多改 7 张）（少交的那一副" in text
    assert "打法更新：这一期不收（第 5 期起合并期）" in text and "special-P4.md" in text
    other = submit.status_text(submit.status(subs, p4.dir, "sol"), submit.ledger(subs))
    assert "兔子教（S-0001" not in other and "astra" not in other                # never another player's
    # precheck --period 4: the blueprint and its cap; a team claim is refused
    d = tmp_path / "in"
    from test_submit import make_sub                                            # noqa: E402
    from svsim.cards.decks import to_hash
    from svsim.cards.pool import card
    code = lambda ids: to_hash([card(c) for c in ids])
    over = submit.precheck(make_sub(d / "over", "新卡组", deck=code(changed(DRAGON, 8))), period=4)
    assert not over["ok"] and any("和蓝本跳费龙比改了 8 张（上限 7 张）" in p for p in over["problems"])
    fine = submit.precheck(make_sub(d / "fine", "新卡组", deck=code(changed(DRAGON, 7))), period=4)
    assert fine["ok"] and fine["warnings"][0].startswith("蓝本：和蓝本跳费龙比改了 7 张（上限 7 张）：去掉 ")
    assert any(w.startswith("蓝本：和蓝本跳费龙比改了 8 张") for w in over["warnings"])      # what differs: once
    assert not any("）×" in p for p in over["problems"])                       # the cards only in the warning
    bad = submit.precheck(make_sub(d / "41", "新卡组", deck=code(special.blueprints(4)[DRAGON]["ids"] + [10542120])),
                          period=4)                                     # a 41st card: illegal, no change count
    assert not bad["ok"] and bad["warnings"] == [] and not any("蓝本" in p for p in bad["problems"])
    sword = submit.precheck(make_sub(d / "剑", "新卡组", deck=code(special.teams(3)[CR][2]["ids"])), period=4)
    assert not sword["ok"] and any("皇家护卫的新卡组这一期不收" in p for p in sword["problems"])
    assert submit.precheck(d / "over")["ok"]                                    # no period: only the general checks
    (d / "队").mkdir()
    (d / "队" / "submission.json").write_text(json.dumps({"type": "选队", "team": CR}), encoding="utf-8")
    res = submit.precheck(d / "队", period=4)
    assert not res["ok"] and "不选队" in res["problems"][0]
    capsys.readouterr()
    assert submit.main(["precheck", str(d / "fine"), "--period", "4"]) == 0                  # the command line
    assert json.loads(capsys.readouterr().out)["warnings"] == fine["warnings"]
    assert submit.main(["precheck", str(d / "over"), "--period", "4"]) == 1
    assert json.loads(capsys.readouterr().out)["problems"] == over["problems"]
    assert submit.main(["precheck", str(d / "over")]) == 0                                   # no period given


def test_the_evaluation_receipt_name_is_kept_for_the_host():
    # a directory handed in as 特殊期评测-P4 would overwrite the evaluation's receipt (special_eval, special_rr)
    assert submit.box_name("特殊期评测-P4", "S-0007", set()) == "S-0007"
    assert submit.box_name("特殊期评测", "S-0008", set()) == "S-0008"
    assert submit.box_name("评测-P4", "S-0009", set()) == "评测-P4"


def test_a_team_claim_is_refused_in_period_4_without_games(p4, tmp_path):
    d = tmp_path / "in" / "选队"
    d.mkdir(parents=True)
    (d / "submission.json").write_text(json.dumps({"type": "选队", "team": CR}, ensure_ascii=False), encoding="utf-8")
    rec = submit.receive(d, "astra", p4.dir, tmp_path / "subs")
    assert rec["verdict"] == "拒收" and rec["smoke_seeds"] == [] and any("不选队" in r for r in rec["reasons"])


def test_a_blueprint_deck_is_received_and_kept_out_of_the_pool(p4, tmp_path):
    # the whole receipt on a real deck (7 changes, the cap): load check and smoke games on 92648000-92648049
    from test_submit import make_sub                                            # noqa: E402
    from svsim.cards.decks import to_hash
    from svsim.cards.pool import card
    deck = changed(FOREST, 7)
    d = make_sub(tmp_path / "in" / "妖七", "新卡组", deck=to_hash([card(c) for c in deck]), member="妖七")
    subs = tmp_path / "subs"
    rec = submit.receive(d, "astra", p4.dir, subs, workers=2, rng_seed=7, smoke_games=2, seeds=P4_SEEDS)
    assert rec["verdict"] == "收下", rec["reasons"]
    assert rec["blueprint"]["name"] == FOREST and rec["blueprint"]["changes"] == 7 and rec["craft"] == 1
    assert all(P4_SEEDS[0] <= s < P4_SEEDS[1] for s in rec["smoke_seeds"]) and len(rec["smoke_seeds"]) == 2
    text = (subs / rec["id"] / "receipt.md").read_text(encoding="utf-8")
    assert "和蓝本快攻妖精比改了 7 张（上限 7 张）" in text and special.NOT_IN_POOL in text
    with pytest.raises(SystemExit, match="先不进池子"):
        submit.admit(subs, rec["id"], p4.dir)
    assert not [l for l in submit.ledger(subs) if l.get("ev") == "admit"]
    assert special.accepted(submit.ledger(subs), 4) == {"astra": {FOREST: submit.ledger(subs)[0]}}
