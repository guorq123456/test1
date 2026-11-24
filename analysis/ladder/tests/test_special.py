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
