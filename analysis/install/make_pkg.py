"""An install package for a turn-end candidate (the architecture thread 2026-10-10 15:27Z): a phased-models folder
holding every installed model file byte for byte, with only the Ramp mirror's ENDED file (ramp-ramp-ended.json)
replaced by the candidate's. A candidate folder alone (e.g. cand-kc-ramp-ramp) holds only ramp-ramp files, and
loading it as `phased=<folder>` drops every other pairing to the fallback model; a package keeps them all.
Nothing is installed by this: a package is used only by naming it (`mcts:N+plan+learned+phased=<package>`), and
which level uses what is Salem's decision. Condition: the opponent's deck list is known (order and hand not).

    python3 make_pkg.py CANDIDATE_FOLDER PACKAGE_NAME      (both under svsim/learn/phased_models)

Writes svsim/learn/phased_models/PACKAGE_NAME/ with the files and PACKAGE.json (the source of every file and its
sha256); tests/test_install_packages.py checks every package against the installed folder."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "svsim/learn/phased_models"
REPLACED = "ramp-ramp-ended.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cand, name = sys.argv[1], sys.argv[2]
    src = MODELS / cand
    out = MODELS / name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    installed = sorted(p for p in MODELS.iterdir() if p.is_file() and p.suffix in (".json", ".npz"))
    files = {}
    for p in installed:
        shutil.copyfile(p, out / p.name)
        files[p.name] = {"from": f"phased_models/{p.name}", "sha256": sha(p)}
    shutil.copyfile(src / REPLACED, out / REPLACED)
    files[REPLACED] = {"from": f"phased_models/{cand}/{REPLACED}", "sha256": sha(src / REPLACED)}
    manifest = {"package": name, "candidate": cand, "replaced": [REPLACED],
                "rule": "every other file is the installed one, byte for byte", "files": files}
    (out / "PACKAGE.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"package": name, "files": len(files), "replaced": REPLACED,
                      "sha256": files[REPLACED]["sha256"]}, indent=1))


if __name__ == "__main__":
    main()
