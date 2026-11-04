"""analysis/scaling/relabel.py: the move prior's decisions searched again, in the records' own "search" format."""
import gzip
import importlib.util
import json
from pathlib import Path

import numpy as np

from svsim.learn.setpolicy import decisions

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "analysis/scaling/data/ramp-t4/rec/rec-75400038.jsonl.gz"
SPEC = "mcts:8+plan+learned+phased=pkg-kc-ramp-ramp+setnet=analysis/scaling/models/net-mid-ramp-t.npz+netmid"


def _relabel():
    spec = importlib.util.spec_from_file_location("relabel", ROOT / "analysis/scaling/relabel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record():
    with gzip.open(REC, "rt") as fh:
        return json.loads(next(fh))


def test_the_new_searches_sit_at_the_prior_s_decisions_and_nowhere_else():
    R = _relabel()
    rec = _record()
    want = [i for i, *_ in decisions(rec)]
    out, n = R.relabel_record(rec, SPEC, 7, 0, np.random.default_rng(0))
    assert n == len(want) and len(out["search"]) == len(rec["actions"])
    assert [i for i, t in enumerate(out["search"]) if t is not None] == want
    assert [i for i, *_ in decisions(out)] == [i for i in want if sum(out["search"][i]["visits"]) > 0]
    for i, _state, legal, *_ in decisions(rec):
        t = out["search"][i]
        assert len(t["visits"]) == len(legal) and set(t) == {"visits", "value", "center"}
    assert out["actions"] == rec["actions"] and out["relabel"] == {"spec": SPEC, "seed_base": 7, "rate": 1.0}
    again, _ = R.relabel_record(rec, SPEC, 7, 0, np.random.default_rng(0))
    assert again == out                                                      # seeded: the same searches
    assert rec["search"] != out["search"]                                    # the input record is untouched


def test_thinning_keeps_a_seeded_share_of_the_decisions():
    R = _relabel()
    rec = _record()
    none, n0 = R.relabel_record(rec, SPEC, 7, 0, np.random.default_rng(0), rate=0.0)
    assert n0 == 0 and all(t is None for t in none["search"])
    half, n = R.relabel_record(rec, SPEC, 7, 0, np.random.default_rng(1), rate=0.5)
    total = sum(1 for _ in decisions(rec))
    assert 0 < n < total and sum(t is not None for t in half["search"]) == n
