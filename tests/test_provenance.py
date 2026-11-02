"""learn.provenance: models bound to the simulator version (process item 2, analysis/process/PROCESS.md)."""
import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from svsim.learn import provenance as P


def _tree(root: Path) -> Path:
    """A fake checkout: two engine files, one card script, one card table, plus files that are not rules."""
    for rel, text in {"svsim/core/engine.py": "a = 1\n", "svsim/core/state.py": "b = 2\n",
                      "svsim/cards/forest.py": "c = 3\n", "svsim/cards/data/rotation.json": "[]\n",
                      "svsim/cards/decks.py": "decks\n", "svsim/learn/net.py": "not rules\n",
                      "svsim/core/__pycache__/engine.cpython-311.pyc": "x"}.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


def test_rules_files_are_engine_card_scripts_and_card_tables_only(tmp_path):
    root = _tree(tmp_path)
    assert [p.relative_to(root).as_posix() for p in P.rules_files(root)] == [
        "svsim/cards/data/rotation.json", "svsim/cards/forest.py", "svsim/core/engine.py", "svsim/core/state.py"]
    # the real checkout: the engine and every class script are in, deck lists and __pycache__ are not
    names = {p.relative_to(P.ROOT).as_posix() for p in P.rules_files()}
    assert "svsim/core/engine.py" in names and "svsim/cards/portal.py" in names and "svsim/cards/data/rotation.json" in names
    assert not any("__pycache__" in n or n.endswith(("decks.py", "deckcode.py")) for n in names)


def test_hash_is_stable_and_moves_with_any_rules_byte_but_not_with_other_files(tmp_path):
    root = _tree(tmp_path)
    h = P.rules_hash(root)
    assert h == P.rules_hash(root) and len(h) == 64
    (root / "svsim/learn/net.py").write_text("changed, not rules\n")
    (root / "svsim/cards/decks.py").write_text("changed deck list\n")
    assert P.rules_hash(root) == h
    (root / "svsim/cards/forest.py").write_text("c = 4\n")
    assert P.rules_hash(root) != h
    (root / "svsim/cards/forest.py").write_text("c = 3\n")
    assert P.rules_hash(root) == h


def _tiny_net():
    from svsim.learn.setnet import SetNet
    net = SetNet(3, phi=(4, 3), rho=(5, 3), seed=1, info={"deck": "a", "opponent": "b"})
    net.set_cards(np.array([1, 2], np.int64), np.zeros((2, 3)))
    return net


def test_save_stamps_a_model_without_a_record_and_keeps_one_it_has(tmp_path):
    from svsim.learn.setnet import SetNet
    net = _tiny_net()
    net.save(tmp_path / "n.npz")
    rec = SetNet.load(tmp_path / "n.npz").info["provenance"]
    assert rec["rules_hash"] == P.current()[0] and len(rec["rules_files"]) == len(P.rules_files())
    assert P.status(SetNet.load(tmp_path / "n.npz").info) == ("current", [])
    old = dict(rec, rules_hash="0" * 64, rules_files={**rec["rules_files"], "svsim/cards/forest.py": "x"})
    net.info["provenance"] = old                             # a record from training time is not overwritten
    net.save(tmp_path / "n2.npz")
    assert SetNet.load(tmp_path / "n2.npz").info["provenance"]["rules_hash"] == "0" * 64
    st, changed = P.status(SetNet.load(tmp_path / "n2.npz").info)
    assert st == "stale" and changed == ["svsim/cards/forest.py"]


def test_load_warns_once_for_stale_and_unregistered_never_raises(tmp_path, capsys):
    P._WARNED.clear()
    assert P.check_loaded(tmp_path / "legacy.npz", {"deck": "a"}) == "未登记"
    assert P.check_loaded(tmp_path / "legacy.npz", {"deck": "a"}) == "未登记"
    stale = {"provenance": {"rules_hash": "0" * 64, "rules_files": {}}}
    assert P.check_loaded(tmp_path / "old.npz", stale) == "stale"
    err = capsys.readouterr().err
    assert err.count("legacy.npz 未登记") == 1 and f"old.npz 与当前规则不符（{len(P.rules_files())} 个规则文件已改）" in err
    assert P.check_loaded(tmp_path / "bad.npz", {"provenance": {"rules_hash": None}}) == "stale"   # no exception


def test_gate_guard_refuses_stale_allows_with_the_flag_and_only_warns_unregistered(tmp_path):
    from svsim.learn.setnet import SetNet
    net = _tiny_net()
    net.save(tmp_path / "cur.npz")
    net.info["provenance"] = {"rules_hash": "0" * 64, "rules_files": {}}
    net.save(tmp_path / "old.npz")
    legacy = dict(np.load(tmp_path / "cur.npz"))
    legacy["info"] = np.array(json.dumps({"deck": "a", "opponent": "b"}))
    np.savez(tmp_path / "legacy.npz", **legacy)
    spec = lambda f: f"mcts:50+plan+setnet={tmp_path / f}+netmid+netany+puct={tmp_path / 'cur.npz'}:2:1"
    assert P.models_in_spec(spec("old.npz")) == [str(tmp_path / "old.npz"), str(tmp_path / "cur.npz")]
    lines = []
    rows = P.guard([spec("cur.npz"), spec("legacy.npz"), "mcts:100+plan"], out=lines.append)
    assert [r[1] for r in rows] == ["current", "未登记"] and not any("allow" in s for s in lines)
    with pytest.raises(SystemExit, match="old.npz"):
        P.guard([spec("old.npz")], out=lines.append)
    lines.clear()
    rows = P.guard([spec("old.npz")], allow_stale=True, out=lines.append)
    assert rows[0][1] == "stale" and lines[-1] == "--allow-stale：放行 1 个与当前规则不符的模型"


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "HOME": str(root), "PATH": "/usr/bin:/bin"})


def test_backfill_stamps_only_when_no_rules_file_changed_since_the_model_was_added(tmp_path, monkeypatch, capsys):
    root = _tree(tmp_path / "repo")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "rules")
    models = root / "models"
    models.mkdir()
    net = _tiny_net()
    for name in ("a.npz", "b.npz"):
        net.save(models / name)
        z = dict(np.load(models / name))
        z["info"] = np.array(json.dumps({"deck": "a", "opponent": "b"}))       # a legacy model: no record
        np.savez(models / name, **z)
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "models")
    monkeypatch.setattr(P, "ROOT", root)
    monkeypatch.setattr(P, "_CURRENT", {})
    ok, msg = P.backfill(models / "a.npz")
    assert ok and "the commit that first added the file" in msg
    assert P.status(P.model_info(models / "a.npz"))[0] == "current"
    assert P.model_info(models / "a.npz")["provenance"]["backfilled"] is True
    (root / "svsim/cards/forest.py").write_text("c = 5\n")                   # a rules change after b was added
    _git(root, "commit", "-qam", "card change")
    monkeypatch.setattr(P, "_CURRENT", {})
    ok, msg = P.backfill(models / "b.npz")
    assert not ok and "1 rules files changed" in msg and "svsim/cards/forest.py" in msg
    assert P.status(P.model_info(models / "b.npz"))[0] == "未登记"
    assert P.status(P.model_info(models / "a.npz"))[0] == "stale"            # a's stamp no longer matches
    rows = {r[0]: r for r in P.list_models(models)}
    assert rows["a.npz"][2] == "stale" and rows["a.npz"][3] == ["svsim/cards/forest.py"] and rows["b.npz"][2] == "未登记"
