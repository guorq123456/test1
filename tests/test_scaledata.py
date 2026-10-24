"""The scaling test's card tokens (learn.tokens) and its sharded self-play data (learn.scaledata)."""
import gzip
import json
from argparse import Namespace

import numpy as np

from svsim.cards import decks
from svsim.core.engine import new_game
from svsim.learn import scaledata as SD
from svsim.learn import tokens as T
from svsim.ui.session import DECKS


def _state(seed=7):
    cards = decks.build(DECKS["ramp-t"][1])
    return new_game(cards, list(cards), seed=seed)


def test_encode_shapes_and_zones():
    s = _state()
    me = s.active
    cids, toks, glob = T.encode(s, me)
    assert cids.dtype == np.int32 and toks.dtype == np.int16 and glob.dtype == np.float32
    assert toks.shape == (len(cids), len(T.TOKEN)) and glob.shape == (len(T.GLOBALS),)
    zone, count = toks[:, 0], toks[:, 1]
    p, o = s.players[me], s.players[1 - me]
    assert count[zone == T.ZONES.index("my_hand")].sum() == len(p.hand)
    assert count[zone == T.ZONES.index("my_deck")].sum() == len(p.deck_view())
    assert count[zone == T.ZONES.index("op_unseen")].sum() == len(o.hand) + len(o.deck_view())
    assert glob[T.GLOBALS.index("op_hand")] == len(o.hand)


def test_opponent_hand_is_a_count_only():
    """Swapping a card between the opponent's hand and deck changes nothing the encoding shows."""
    s = _state()
    me = s.active
    o = s.players[1 - me]
    before = T.encode(s, me)
    t = s.clone()
    ot = t.players[1 - me]
    deck = ot.deck_view()
    k = next(i for i, c in enumerate(deck) if c.defn.card_id != ot.hand[0].defn.card_id)
    ot._deck = list(deck)
    ot._deck_shared = False
    ot.hand[0], ot._deck[k] = ot._deck[k], ot.hand[0]
    assert [c.defn.card_id for c in ot.hand] != [c.defn.card_id for c in o.hand]
    after = T.encode(t, me)
    for a, b in zip(before, after):
        assert np.array_equal(a, b)


def test_static_rows():
    s = _state()
    names = T.static_names()
    for c in s.players[0].hand:
        row = T.static(c.defn)
        assert row.shape == (len(names),) and row.dtype == np.float32
        assert row[names.index("cost")] == c.defn.cost
        assert np.array_equal(row, T.static(c.defn))


def test_read_part_drops_a_cut_last_line(tmp_path):
    part = tmp_path / "rec-1.part.jsonl"
    part.write_text(json.dumps({"g": 0}) + "\n" + json.dumps({"g": 1}) + "\n" + '{"g": 2, "acti', encoding="utf-8")
    assert [r["g"] for r in SD._read_part(part)] == [0, 1]
    assert part.read_text(encoding="utf-8").count("\n") == 2


def test_play_resume_merge_encode(tmp_path):
    rec = tmp_path / "rec"
    args = Namespace(base=61000, stride=1, shards=[0, 2], per_shard=2, deck="ramp-t", opponent="ramp-t", spec="greedy",
                     workers=1, every=10, out=str(rec))
    rec.mkdir()
    with open(rec / "rec-61001.part.jsonl", "w", encoding="utf-8") as fh:   # half a shard, its last line cut off
        _, first = SD._play((61001, 0, "ramp-t", "ramp-t", "greedy"))
        fh.write(json.dumps(first) + "\n" + '{"g": 1, "act')
    SD.play_main(args)
    for seed in (61000, 61001):
        rs = list(SD._records(rec / f"rec-{seed}.jsonl.gz"))
        assert [r["g"] for r in rs] == [0, 1] and all(r["winner"] is not None and r["cpu"] >= 0 for r in rs)
        assert all(r["seed"] == seed * 100003 + r["g"] for r in rs)
    assert not list(rec.glob("*.part.jsonl"))
    SD.play_main(args)                               # nothing left to play
    other = tmp_path / "other"
    other.mkdir()
    rs = list(SD._records(rec / "rec-61001.jsonl.gz"))
    rs[1] = dict(rs[1], winner=1 - rs[1]["winner"])  # a duplicate that differs
    with gzip.open(other / "rec-61001.jsonl.gz", "wt", encoding="utf-8") as fh:
        for r in rs:
            fh.write(json.dumps(dict(r, date="x", cpu=0.0)) + "\n")
    merged = tmp_path / "merged"
    SD.merge_main(Namespace(inputs=[str(rec), str(other)], out=str(merged)))
    assert sorted(p.name for p in merged.glob("rec-*.jsonl.gz")) == ["rec-61000.jsonl.gz", "rec-61001.jsonl.gz"]
    assert len(list(SD._records(merged / "rec-61001.jsonl.gz"))) == 2
    tok = tmp_path / "tok"
    SD.encode_main(Namespace(records=str(merged), out=str(tok), spec=SD.SPEC, workers=1, net=None))
    z, c = np.load(tok / "tok-61000.npz"), np.load(tok / "cards.npz")
    n = len(z["result"])
    assert n > 0 and z["offsets"].shape == (n + 1,) and z["offsets"][-1] == len(z["tokens"]) == len(z["cards"])
    assert z["globals"].shape == (n, len(T.GLOBALS)) and set(np.unique(z["result"])) <= {0.0, 0.5, 1.0}
    assert set(z["cards"]) <= set(c["card_id"]) and c["static"].shape[1] == len(T.static_names())
    assert np.all(np.isfinite(z["linear"]))
