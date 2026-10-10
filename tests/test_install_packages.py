"""Install packages (analysis/install/make_pkg.py): every installed model file byte for byte, only the Ramp mirror's
ENDED file replaced by the candidate's; and loaded, every pairing's model the installed one but that file's."""
import json
from pathlib import Path

import pytest

from svsim.learn.phased import load

MODELS = Path(__file__).resolve().parents[1] / "svsim/learn/phased_models"
PACKAGES = sorted(p for p in MODELS.iterdir() if p.is_dir() and (p / "PACKAGE.json").exists())
REPLACED = "ramp-ramp-ended.json"


def _installed_files():
    return sorted(p.name for p in MODELS.iterdir() if p.is_file() and p.suffix in (".json", ".npz"))


def test_there_are_packages():
    assert {p.name for p in PACKAGES} >= {"pkg-kc-ramp-ramp", "pkg-nl-ramp-ramp"}


@pytest.mark.parametrize("pkg", PACKAGES, ids=lambda p: p.name)
def test_files_are_the_installed_ones_but_the_ramp_mirror_ended(pkg):
    manifest = json.loads((pkg / "PACKAGE.json").read_text())
    names = sorted(p.name for p in pkg.iterdir() if p.suffix in (".json", ".npz") and p.name != "PACKAGE.json")
    assert names == _installed_files()
    for name in names:
        if name == REPLACED:
            cand = MODELS / manifest["candidate"] / REPLACED
            assert (pkg / name).read_bytes() == cand.read_bytes()
            assert (pkg / name).read_bytes() != (MODELS / name).read_bytes()
        else:
            assert (pkg / name).read_bytes() == (MODELS / name).read_bytes(), name


def _model_json(m):
    return json.dumps({"coef": m.coef, "mean": m.mean, "std": m.std, "hidden": m.hidden,
                       "extras": list(m.extras), "version": m.version})


@pytest.mark.parametrize("pkg", PACKAGES, ids=lambda p: p.name)
def test_loaded_models_are_the_installed_ones_but_the_ramp_mirror_ended(pkg):
    installed, packaged = load(MODELS), load(pkg)
    assert set(installed) == set(packaged)
    for key in installed:
        same = _model_json(installed[key]) == _model_json(packaged[key])
        assert same == (key != ("ramp", "ramp", "ended")), key


@pytest.mark.parametrize("pkg", PACKAGES, ids=lambda p: p.name)
def test_an_agent_with_the_package_scores_other_pairings_as_installed(pkg):
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.search.evaluate import evaluate
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    wi = _search(make_agent("level-strong", 0)).weights
    wp = _search(make_agent(f"mcts:200+plan+learned+phased={pkg.name}", 0)).weights
    for name in ("pirate-t", "elf-t"):
        d = decks.build(decks.NAMED[name])
        s = new_game(d, d, seed=7)
        g = make_agent("greedy", 0)
        for _ in range(30):
            if s.over:
                break
            apply(s, g.act(s, legal_actions(s)))
        for moves_next in (False, True):
            assert evaluate(s, s.active, wi, moves_next) == evaluate(s, s.active, wp, moves_next)
