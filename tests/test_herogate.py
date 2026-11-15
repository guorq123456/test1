"""tools.herogate: the hero deck piloted by X and by the baseline on the same deals, against the field's other decks."""
import pytest

from svsim.tools import herogate as H
from svsim.tools.deckgate import read_field

from test_deckgate import FIELD_LINES


def _field(tmp_path):
    path = tmp_path / "field.txt"
    third = "c|" + FIELD_LINES[1].split("|", 1)[1]
    path.write_text("\n".join(FIELD_LINES + [third]) + "\n", encoding="utf-8")
    return read_field(str(path))


def test_opponents_are_the_other_decks_and_the_hero_must_be_there_once(tmp_path):
    field = _field(tmp_path)
    assert H.opponents(field, "a") == [1, 2]
    with pytest.raises(SystemExit):
        H.opponents(field, "zz")


def test_a_pair_plays_both_arms_from_both_seats_and_the_same_pilot_gives_the_same_games(tmp_path):
    field = _field(tmp_path)
    job = (0, 31, 1, field[0][1], field[1][1], "greedy", "greedy", "random")
    d = H.play_pair(job)
    assert [(g["arm"], g["seat"]) for g in d["games"]] == [("x", 0), ("x", 1), ("base", 0), ("base", 1)]
    x, b = H.scores(d)
    assert x == b                                       # the same pilot on the same deals and agent seeds
    assert [g["points"] for g in d["games"][:2]] == [g["points"] for g in d["games"][2:]]
    lines = H.report([d], [label for label, _ in field])
    assert "配对差 +0.0%" in lines[0]


def test_time_match_rule():
    assert H.time_match(100, 1.02) == 100 and H.time_match(100, 1.6) == 62 and H.budget("mcts:56+plan") == 56


def test_opp_pilots_gives_each_bot_deck_with_a_pilot_its_own_and_the_rest_the_opp_spec(tmp_path, monkeypatch, capsys):
    # the T3-FOREST-2 pilot's acceptance (WGP comparison report 2026-11-15, section 7): trained opponents
    import json
    import sys
    from svsim.ui import deckbuilder
    from svsim.ui.session import pilot_native_spec
    code = {d["key"]: d["code"] for d in deckbuilder.bot_decks()["decks"]}
    path = tmp_path / "field.txt"
    path.write_text("".join(f"bot/{k}|{code[k]}\n" for k in ("T3-FOREST-2", "T1-SWORD-1", "T1-HAVEN-2")), encoding="utf-8")
    out = tmp_path / "g.jsonl"
    monkeypatch.setattr(sys, "argv", ["herogate", "--hero", "bot/T3-FOREST-2", "--field", str(path), "--x", "greedy",
                                      "--base", "greedy", "--opp", "random", "--opp-pilots", "--seed", "5",
                                      "--pairs", "2", "--workers", "1", "--out", str(out)])
    H.main()
    printed = capsys.readouterr().out
    sword = pilot_native_spec("T1-SWORD-1")
    assert sword.startswith("mcts:39+") and "net-pilot-sword-bot-g2.npz" in sword
    assert f"对手 bot/T1-SWORD-1：它自己练过的驾驶员 {sword}" in printed and "对手 bot/T1-HAVEN-2：random" in printed
    assert pilot_native_spec("T1-HAVEN-2") is None
    assert len([json.loads(x) for x in out.read_text().splitlines()]) == 2
