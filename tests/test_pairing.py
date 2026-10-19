"""A non-mirror pairing's pieces (D15, the architecture thread 2026-10-19 00:34Z; off by default): a value net that
answers for both orders of a pairing (info "pairs"), a start's card table grown to the pairing's cards
(setnet.extend_table), and one side's decisions for its prior (setpolicy encode --deck)."""
import gzip
import json
from pathlib import Path

import numpy as np
import pytest

from svsim.cards import decks
from svsim.core.engine import new_game
from svsim.learn import setnet as SN
from svsim.learn import setpolicy as SP
from svsim.learn import tokens as T
from svsim.ui.session import DECKS

ROOT = Path(__file__).resolve().parents[1]
RAMP = ROOT / "analysis/scaling/models/net-mid-ramp-t.npz"
REC = ROOT / "analysis/scaling/data/ramp-t4/rec/rec-75400038.jsonl.gz"


@pytest.fixture(scope="module")
def record():
    """One ramp-t vs elf-t game of a cheap searching bot (a test's fixed seed, part of no data)."""
    from svsim.learn.netdata import play
    return play((0, 4242, "ramp-t", "elf-t", "mcts:8+plan+learned+phased", 0.0))


def _deal(a, b):
    return new_game(decks.build(DECKS[a][1]), decks.build(DECKS[b][1]), seed=3)


def _mirror_states(n):
    with gzip.open(REC, "rt") as fh:
        rec = json.loads(next(fh))
    return [st.clone() for _i, st, *_ in SP.decisions(rec)][:n]


class _Base:
    def score(self, state, player, player_moves_next=False):
        return 12345.0


def test_a_net_answers_for_the_orders_its_info_names():
    net = SN.SetNet.load(RAMP)
    st = _deal("ramp-t", "elf-t")
    plain = SN.SetNetEnded(_Base(), net)
    assert plain.pairs == {("ramp-t", "ramp-t")}
    assert plain.score(st, 0) == 12345.0 and plain.score(st, 1) == 12345.0
    net.info = {**net.info, "deck": "ramp-t", "opponent": "elf-t", "pairs": [["ramp-t", "elf-t"], ["elf-t", "ramp-t"]]}
    both = SN.SetNetEnded(_Base(), net)
    assert both.score(st, 0) != 12345.0 and both.score(st, 1) != 12345.0
    assert both.score(st, 0, player_moves_next=True) == 12345.0
    assert both.score(_deal("ramp-t", "ramp-t"), 0) == 12345.0


def test_a_grown_table_scores_the_cards_it_knew_as_before():
    base = SN.SetNet.load(RAMP)
    net = SN.SetNet.load(RAMP)
    st = _deal("ramp-t", "elf-t")
    defs = {}
    for p in st.players:
        for c in p.hand + p.field + p.leader_area + p.deck_view():
            defs[c.defn.card_id] = c.defn
    ids = sorted(defs)
    rows = np.stack([T.static(defs[c]) for c in ids])
    n0 = len(net.card_ids)
    idx = SN.extend_table(net, ids, rows)
    assert len(net.card_ids) > n0 and np.array_equal(net.card_ids[:n0], base.card_ids)
    assert np.array_equal(net.card_ids[idx], ids) and np.array_equal(net.smean, base.smean)
    for s in _mirror_states(20):
        assert net.logit(s, s.active, mid=True) == base.logit(s, s.active, mid=True)
    assert np.isfinite(net.logit(st, 0)) and np.isfinite(net.logit(st, 1))
    again = SN.extend_table(net, ids, rows)                       # nothing more to add
    assert len(net.card_ids) == n0 + len(set(ids) - set(base.card_ids.tolist())) and np.array_equal(again, idx)
    bad = rows.copy()
    bad[0, 0] += 1
    with pytest.raises(ValueError):
        SN.extend_table(net, ids, bad)


def test_one_side_s_decisions(record, tmp_path):
    rec = tmp_path / "rec-4242.jsonl.gz"
    with gzip.open(rec, "wt") as fh:
        fh.write(json.dumps(record) + "\n")
    SP._encode_shard((str(rec), tmp_path / "both.npz"))
    SP._encode_shard((str(rec), tmp_path / "ramp.npz", "ramp-t"))
    SP._encode_shard((str(rec), tmp_path / "elf.npz", "elf-t"))
    both, ramp, elf = (np.load(tmp_path / f"{k}.npz") for k in ("both", "ramp", "elf"))
    movers = [st.players[st.active].deck_name for _i, st, *_ in SP.decisions(record)]
    assert len(ramp["step"]) == movers.count("ramp-t") > 0 and len(elf["step"]) == movers.count("elf-t") > 0
    assert sorted(np.concatenate([ramp["step"], elf["step"]]).tolist()) == sorted(both["step"].tolist())
    assert np.array_equal(ramp["step"], both["step"][np.isin(both["step"], ramp["step"])])
