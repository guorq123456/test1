"""An install package for a turn-end candidate (the architecture thread 2026-10-10 15:27Z): a phased-models folder
holding every installed model file byte for byte, with only the Ramp mirror's ENDED file (ramp-ramp-ended.json)
replaced by the candidate's. A candidate folder alone (e.g. cand-kc-ramp-ramp) holds only ramp-ramp files, and
loading it as `phased=<folder>` drops every other pairing to the fallback model; a package keeps them all.
Nothing is installed by this: a package is used only by naming it (`mcts:N+plan+learned+phased=<package>`), and
which level uses what is Salem's decision. Condition: the opponent's deck list is known (order and hand not).

    python3 make_pkg.py CANDIDATE_FOLDER PACKAGE_NAME      (both under svsim/learn/phased_models)
    python3 make_pkg.py PACKAGE_NAME --replace FOLDER:FILE [--replace FOLDER:FILE ...]
                                                           (several files, each from its candidate folder)

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
    args = sys.argv[1:]
    if "--replace" in args:                        # PACKAGE_NAME --replace FOLDER:FILE ...
        name = args[0]
        pairs = [args[i + 1].split(":", 1) for i, a in enumerate(args) if a == "--replace"]
    else:                                          # CANDIDATE_FOLDER PACKAGE_NAME: the Ramp mirror's ENDED file
        name, pairs = args[1], [[args[0], REPLACED]]
    out = MODELS / name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    installed = sorted(p for p in MODELS.iterdir() if p.is_file() and p.suffix in (".json", ".npz"))
    files = {}
    for p in installed:
        shutil.copyfile(p, out / p.name)
        files[p.name] = {"from": f"phased_models/{p.name}", "sha256": sha(p)}
    for cand, fname in pairs:
        if not (MODELS / fname).is_file():
            raise SystemExit(f"{fname} is not an installed file")
        shutil.copyfile(MODELS / cand / fname, out / fname)
        files[fname] = {"from": f"phased_models/{cand}/{fname}", "sha256": sha(MODELS / cand / fname)}
    manifest = {"package": name, "candidate": pairs[0][0] if len(pairs) == 1 else None,
                "candidates": {fname: cand for cand, fname in pairs}, "replaced": [f for _, f in pairs],
                "rule": "every other file is the installed one, byte for byte", "files": files}
    (out / "PACKAGE.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"package": name, "files": len(files),
                      "replaced": {f: files[f]["sha256"] for _, f in pairs}}, indent=1))


if __name__ == "__main__":
    main()
