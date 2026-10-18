"""The in-browser build's binary models (the architecture thread 2026-10-17 21:01Z: the install path for +puct, made
ready, nothing published). A level's (or a --spec candidate's) +setnet= / +puct= model ships as base64 text, and the
page then gets numpy (pyodide/numpy.json). A build of the levels as they are carries neither."""
import base64
import gzip
import json
import zipfile
from pathlib import Path

import numpy as np

from svsim.tools.web import build, model_files, package_sources

ROOT = Path(__file__).resolve().parents[1]
PRIOR = "analysis/scaling/models/prior-ramp-ft-t05.npz"
SPEC = (f"mcts:12+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/"
        f"net-gen3-30000.npz+neteot+puct={PRIOR}:2:1")


def _fake_pyodide(tmp_path):
    fake = tmp_path / "pyodide-src"
    fake.mkdir()
    for name in ("pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm"):
        (fake / name).write_text("stub")
    (fake / "pyodide-lock.json").write_text(json.dumps({"packages": {"numpy": {"file_name": "numpy-x.whl"}}}))
    (fake / "numpy-x.whl").write_bytes(b"wheel bytes")
    with zipfile.ZipFile(fake / "python_stdlib.zip", "w") as z:
        z.writestr("encodings/__init__.py", "# stdlib")
    return fake


def test_the_levels_as_they_are_ship_no_binary_model_and_no_numpy(tmp_path):
    assert model_files() == []
    assert not any(n.endswith(".b64") for n in package_sources())
    out = tmp_path / "dist"
    build(out, _fake_pyodide(tmp_path))
    assert not (out / "pyodide" / "numpy.json").exists()


def test_a_candidate_spec_ships_its_models_as_base64_and_numpy(tmp_path):
    assert model_files([SPEC]) == ["analysis/scaling/models/net-gen3-30000.npz", PRIOR]
    package = package_sources(extra=[SPEC])
    assert base64.b64decode(package[PRIOR + ".b64"]) == (ROOT / PRIOR).read_bytes()
    assert "svsim/learn/phased_models/pkg-kc-ramp-ramp/ramp-t-ramp-t-ended.json" in package   # its phased folder
    out = tmp_path / "dist"
    build(out, _fake_pyodide(tmp_path), [SPEC])
    np_json = json.loads((out / "pyodide" / "numpy.json").read_text())
    assert np_json["file"] == "numpy-x.whl" and base64.b64decode(np_json["base64"]) == b"wheel bytes"
    # the levels and the ratings are the page's own: a --spec only adds files
    ratings = json.loads((out / "ratings.json").read_text(encoding="utf-8"))
    assert not any(SPEC == t.get("spec") for t in ratings["tiers"].values())


def test_the_loaders_read_a_model_shipped_as_base64(tmp_path, monkeypatch):
    from svsim.learn import setnet, setpolicy
    from svsim.learn.setnet import SetNet
    from svsim.learn.setpolicy import SetPolicy
    app = tmp_path / "app"
    for rel in ("analysis/scaling/models/net-gen3-30000.npz", PRIOR):
        target = app / (rel + ".b64")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(base64.b64encode((ROOT / rel).read_bytes()).decode("ascii"))
    monkeypatch.setattr(setnet, "_CACHE", {})
    monkeypatch.setattr(setpolicy, "_CACHE", {})
    pol = setpolicy.load_cached(app / PRIOR)
    net = setnet.load_cached(app / "analysis/scaling/models/net-gen3-30000.npz")
    ref_pol, ref_net = SetPolicy.load(ROOT / PRIOR), SetNet.load(ROOT / "analysis/scaling/models/net-gen3-30000.npz")
    assert all(np.array_equal(getattr(pol, k), getattr(ref_pol, k)) for k in SetPolicy.PARAMS)
    assert all(np.array_equal(getattr(net, k), getattr(ref_net, k)) for k in SetNet.PARAMS)


def test_self_play_records_a_puct_player_s_visits():
    from svsim.core.engine import legal_actions
    from svsim.learn.netdata import play
    from svsim.tools import records as R
    rec = play((0, 4242, "ramp-t", "ramp-t", SPEC, 0.0))
    searched = [(i, t) for i, t in enumerate(rec["search"]) if t]
    assert searched and rec["winner"] is not None
    want = dict(searched)
    checked = 0
    for i, (state, _) in enumerate(R.steps(json.loads(json.dumps(rec)))):   # the state as of action i
        if i in want:
            assert len(want[i]["visits"]) == len(legal_actions(state)) and sum(want[i]["visits"]) > 0
            checked += 1
    assert checked == len(searched)


def test_the_build_refuses_a_spec_that_sees_the_opponent_s_hand(tmp_path):
    import pytest
    from svsim.learn.netdata import _search
    from svsim.tools.arena import make_agent
    oracle = SPEC + "+oracle"                    # the diagnostic (D13): A that sees the opponent's real hand
    assert _search(make_agent(oracle, 0)).oracle is True and _search(make_agent(SPEC, 0)).oracle is False
    with pytest.raises(ValueError):
        model_files([oracle])
    with pytest.raises(ValueError):
        build(tmp_path / "dist", _fake_pyodide(tmp_path), [oracle])
