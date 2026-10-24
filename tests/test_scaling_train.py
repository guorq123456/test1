"""analysis/scaling/train.py's shard lists: --base-shards (the architecture thread 2026-10-17, for net-elft-gen3-29000)
leaves every earlier command's shards as they were."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

from svsim.learn.setnet import SetNet

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def train(monkeypatch):
    spec = importlib.util.spec_from_file_location("scaling_train", ROOT / "analysis/scaling/train.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module


def _parse(train, monkeypatch, argv):
    """main()'s arguments for `argv`, without running the command."""
    seen = {}
    monkeypatch.setattr(train, "net_main", lambda args: seen.setdefault("args", args))
    monkeypatch.setattr(sys, "argv", ["train.py"] + argv)
    train.main()
    return seen["args"]


@pytest.mark.parametrize("base, argv, model", [
    (70100000, ["--size", "59000", "--add", "70800000:10", "--add", "71300000:10", "--add", "71600000:9",
                "--add", "72300000:40"], "net-gen4-59000"),
    (71900000, ["--size", "19500", "--add", "72800000:19"], "net-elft-gen2-19500"),
    (71900000, ["--size", "10000"], "net-elft-10000"),
])
def test_without_the_option_the_shards_are_the_trained_nets_own(train, monkeypatch, base, argv, model):
    args = _parse(train, monkeypatch, ["--base", str(base), "net", "--tokens", "T"] + argv)
    assert args.base_shards is None
    assert train.shards(args.size, args.add, args.base_shards) == SetNet.load(
        ROOT / f"analysis/scaling/models/{model}.npz").info["shards"]
    for size in train.SIZES:                                          # every size: the first SIZES[size] of BASE
        assert train.shards(size, args.add, None) == train.shards(size, args.add, train.SIZES[size])


def test_elft_gen3_takes_ten_base_shards_and_both_self_play_generations(train, monkeypatch):
    args = _parse(train, monkeypatch, ["--deck", "elf-t", "--opponent", "elf-t", "--base", "71900000",
                                       "--holdout-base", "72000000", "net", "--size", "29000", "--base-shards", "10",
                                       "--name", "elft-gen3", "--add", "72800000:19", "--add", "74100000:19",
                                       "--tokens", "T", "--extra-holdout", "selfplay:72800038",
                                       "--extra-holdout", "selfplay3:74100038"])
    got = train.shards(args.size, args.add, args.base_shards)
    want = ([71900000 + 2 * k for k in range(10)] + [72800000 + 2 * k for k in range(19)]
            + [74100000 + 2 * k for k in range(19)])
    assert got == want and len(set(got)) == 48
    held = set(train.HOLDOUT) | {72800038, 74100038}
    assert train.HOLDOUT == [72000000 + 2 * h for h in range(5)]
    assert not held & set(got)
    assert train._tag(args) == "elft-gen3-29000"
    assert 500 * (19 + 19) + 1000 * 10 == 29000                         # the name's number is the games


def test_the_next_cycle_s_elft_net_takes_three_self_play_generations_and_no_holdout(train, monkeypatch):
    args = _parse(train, monkeypatch, ["--deck", "elf-t", "--opponent", "elf-t", "--base", "71900000",
                                       "--holdout-base", "72000000", "net", "--size", "38500", "--name", "elft-gen4",
                                       "--add", "72800000:19", "--add", "74100000:19", "--add", "75500000:19",
                                       "--init", "analysis/scaling/models/net-elft-gen2-19500.npz", "--tokens", "T"])
    got = train.shards(args.size, args.add, args.base_shards)
    want = [71900000 + 2 * k for k in range(10)] + [b + 2 * k for b in (72800000, 74100000, 75500000) for k in range(19)]
    assert got == want and len(set(got)) == 67
    assert not {72800038, 74100038, 75500038} & set(got)
    assert 1000 * 10 + 500 * 19 * 3 == 38500
    assert args.init == "analysis/scaling/models/net-elft-gen2-19500.npz"
    assert _parse(train, monkeypatch, ["net", "--size", "10000", "--tokens", "T"]).init is None   # off by default


class _Tokens:
    """What _init_net reads of a learn.setnet.Data: its cards and their static rows, and the input version."""
    def __init__(self, card_ids, static, inputs="v1"):
        self.card_ids, self.static, self.inputs = np.asarray(card_ids), np.asarray(static), inputs


def _init_args(train, monkeypatch, extra=()):
    return _parse(train, monkeypatch, ["net", "--size", "10000", "--tokens", "T",
                                       "--init", str(ROOT / "analysis/scaling/models/net-elft-gen2-19500.npz")]
                  + list(extra))


def test_init_keeps_the_net_s_weights_card_table_and_standardization(train, monkeypatch):
    ref = SetNet.load(ROOT / "analysis/scaling/models/net-elft-gen2-19500.npz")
    rows = np.arange(len(ref.card_ids))[::-1]                    # the tokens' table in another order
    net = train._init_net(_init_args(train, monkeypatch), _Tokens(ref.card_ids[rows], ref.static[rows]))
    for k in SetNet.PARAMS + ("smean", "sstd", "card_ids", "static"):
        assert np.array_equal(getattr(net, k), getattr(ref, k))


def test_init_refuses_another_shape_an_unknown_card_or_another_static_row(train, monkeypatch):
    ref = SetNet.load(ROOT / "analysis/scaling/models/net-elft-gen2-19500.npz")
    with pytest.raises(SystemExit):
        train._init_net(_init_args(train, monkeypatch, ["--rho", "64", "64"]), _Tokens(ref.card_ids, ref.static))
    with pytest.raises(SystemExit):
        train._init_net(_init_args(train, monkeypatch), _Tokens(ref.card_ids, ref.static, inputs="v2"))
    with pytest.raises(SystemExit):
        train._init_net(_init_args(train, monkeypatch),
                        _Tokens(np.append(ref.card_ids, 999999999), np.vstack([ref.static, ref.static[:1]])))
    changed = ref.static.copy()
    changed[0, 0] += 1.0
    with pytest.raises(SystemExit):
        train._init_net(_init_args(train, monkeypatch), _Tokens(ref.card_ids, changed))
