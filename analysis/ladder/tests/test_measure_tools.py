"""Host measurement tools' bookkeeping (no games): tools/pilot_conditions.py (2.5) leaves a voided pair out of both
conditions instead of counting it a loss (LD-59); tools/lethal_bank.py (2.2) counts finds per try and per position."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

import lethal_bank as LB  # noqa: E402
import pilot_conditions as PC  # noqa: E402


def row(who, game, winner, seat=0, result="normal"):
    return {"labels": {"pilot": "P", "opp": "o", "game": game, "who": who, "seat": seat}, "winner": winner,
            "cpu": [10, 10], "steps": [1, 1], "result": result}


def test_a_voided_game_drops_its_pair_in_both_conditions():
    guess = [row("pilot", 0, 0), row("ref", 0, 1), row("pilot", 1, None, result="void"), row("ref", 1, 0),
             row("pilot", 2, 0), row("ref", 2, 0)]
    native = [row("pilot", 0, 0), row("ref", 0, 0), row("pilot", 1, 0), row("ref", 1, 0), row("pilot", 2, 1),
              row("ref", 2, 0)]
    for r in native:
        r.pop("result")
    skip = frozenset((g["labels"]["pilot"], g["labels"]["opp"], g["labels"]["game"]) for g in guess
                     if g["result"] not in PC.OK)
    g, n = PC.summarize(guess, "g", skip)["P"], PC.summarize(native, "n", skip)["P"]
    assert g["games"] == n["games"] == 2 and g["dropped_pairs"] == n["dropped_pairs"] == 1
    assert g["pilot_rate"] == 1.0 and g["ref_rate"] == 0.5          # the void is no loss for the pilot
    assert n["pilot_rate"] == 0.5 and n["ref_rate"] == 1.0


def test_lethal_bank_counts_every_try():
    won = {"won": True}
    lost = {"won": False}
    pos = [{"lethal": True, "complete": True, "search_s": 1, "tries": {"planner": [won, won], "exact": [won, lost]},
            "in_game": True, "why": {"default_budget_finds": False, "default_screened": True,
                                     "sure_on_samples": [True, True]}},
           {"lethal": False, "complete": True, "search_s": 2},
           {"lethal": False, "complete": False, "search_s": 3}]
    s = LB.summarize([{"positions": pos}])
    assert s["lethal"] == 1 and s["no_lethal_proven"] == 1 and s["undecided"] == 1
    assert s["planner"] == {"found_every_try": 1, "missed_some_try": 0, "tries_won": 2, "tries": 2}
    assert s["exact"]["missed_some_try"] == 1 and s["misses"]["screened"] == 1


def test_a_torn_guess_log_is_read_on_resume(tmp_path):
    import json
    log = tmp_path / "guess.jsonl"
    whole = [json.dumps({"id": i, "labels": {}, "result": "normal"}) for i in ("a", "b", "c")]
    log.write_bytes((whole[0] + "\n" + whole[1][:9]).encode() + b"\xe4\xb8\x00\x00\n" + (whole[1] + "\n").encode()
                    + (whole[2] + "\n\n").encode())
    got = PC.read_guess(log, {"a", "b"})
    assert sorted(got) == ["a", "b"] and got["b"]["result"] == "normal"

