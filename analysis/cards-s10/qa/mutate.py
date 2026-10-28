"""Mutation check for the set 10 scripts: each mutant must make the class's test file fail.

Mutants, one at a time, inside the set 10 code of a card module (the crest classes and the
set 10 section): (a) a hook method's body replaced by `return`; (b) an integer literal n
changed to n + 1; (c) `0 in ctx.modes` / `1 in ctx.modes` swapped; (d) a comparison flipped
(== / !=). Run from the worktree root: python mutate.py rune
"""
import ast, os, re, subprocess, sys

MODULES = {
    "rune": ("svsim/cards/rune.py", "tests/test_cards_rune.py",
             ["NoeinhowellsInterrogationCrest", "NoeinhowellCrest", "_summon_evidence", "DedicatedAide",
              "WilyWitch", "AtelierRelocation", "LeisurelyAttendant", "RulerOfTempests", "DiscerningMelody",
              "DramaticAssistant", "NoeinhowellsInterrogation", "Noeinhowell", "InfernalChimera"]),
    "abyss": ("svsim/cards/abyss.py", "tests/test_cards_abyss.py",
              ["GremoryCrest", "summon_evidence", "allied_banished_on_your_turn", "summon_ghost_with_bane",
               "DiligentUndertaker", "VengefulCapra", "RunawaySouls", "SolemnGravekeeper", "RestiveCentaur",
               "LastWillAndTestament", "AttendingAmanuensis", "NocturnesInterrogation", "Nocturne", "Gremory"]),
    "haven": ("svsim/cards/haven.py", "tests/test_cards_haven.py",
              ["BunniesOfDesolation", "FruitlessTestimonyCrest", "LapinetteCrest", "_summon_bunnies",
               "DesolationistRefiner", "CombativeMonk", "SolitaryCultivation", "DesolationistTamer",
               "WingedAccordionist", "DestructivePropagation", "DesolationistRehabilitator",
               "FruitlessTestimony", "Lapinette", "ParareligiousIdol"]),
    "neutral": ("svsim/cards/neutral.py", "tests/test_set10_neutral.py tests/test_clue.py tests/test_cards_neutral.py",
                ["_ClueEngage", "DivineEvidence", "Nacreheim", "Exias", "Dynames", "SceneOfDeicide", "Kyrios",
                 "Rezeal", "_SummonCopyOnDeath", "_CantAttack", "RezealCrest"]),
    "dragon": ("svsim/cards/dragon.py", "tests/test_set10_dragon.py tests/test_cards_dragon.py",
               ["_clues_in_hand", "_discard_random_clue", "ObliviationistMarauder", "FreezingIcenewt",
                "DanceOfTheWaterwyrm", "ObliviationistSmuggler", "DragonewtScout", "CollectionManifest",
                "ObliviationistMugger", "BirdsEyeView", "Leizaut", "Jerva"]),
    "forest": ("svsim/cards/forest.py", "tests/test_set10_forest.py tests/test_cards_forest.py",
               ["UntamedTestimonyCrest", "_one_cost_allies", "DebonairDogsitter", "WolfPackLackey",
                "NaturalReincarnation", "InquiringMischief", "GardenElf", "UntamedTestimony", "SleuthsBestFriend",
                "NoschesInterrogation", "Nosche", "HearteningHyphae"]),
    "sword": ("svsim/cards/sword.py", "tests/test_set10_sword.py tests/test_cards_sword.py",
              ["_set_stats", "_swap_stats", "_SwapOnClueEngage", "_engaged_clue", "GuilelessNewsie", "BejeweledLady",
               "OnwardCharge", "CheekyArchitect", "_allied_amulet", "ErrantKnight", "DichotomousForensics",
               "PlacidDilettante", "NoLifesCrossExamination", "NoLife", "Almaelys", "AlmaelysCrest"]),
    "portal": ("svsim/cards/portal.py", "tests/test_cards_portal.py",
               ["DimensionalWandererCrest", "is_amulet", "fused_an_amulet", "add_evidence",
                "_FuseAmuletsForEvidence", "ExtinctionistMajordomo", "IncohesiveConstruction",
                "ExtinctionistSocialite", "BestialBeamcannoneer", "HandOfExtinction", "ExtinctionistDandy",
                "CalamityInCustody", "Lineage", "DimensionalWanderer"]),
}


def spans(src, names):
    tree = ast.parse(src)
    out = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names:
            start = node.lineno - 1 - len(node.decorator_list)
            out.append((node.name, start, node.end_lineno))
    assert len(out) == len(names), set(names) - {n for n, _, _ in out}
    return out


def docstring_lines(tree):
    """0-based line numbers covered by docstrings (module, class or function)."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)) and node.body:
            d = node.body[0]
            if isinstance(d, ast.Expr) and isinstance(getattr(d, "value", None), ast.Constant) \
                    and isinstance(d.value.value, str):
                out.update(range(d.lineno - 1, d.end_lineno))
    return out


def mutants(src, names):
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    docs = docstring_lines(tree)
    for name, a, b in spans(src, names):
        # (a) hook bodies
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and a < node.lineno <= b and node.name != "fused":
                body0 = node.body[0]
                if isinstance(body0, ast.Expr) and isinstance(getattr(body0, "value", None), ast.Constant) and len(node.body) > 1:
                    body0 = node.body[1]
                first, last = body0.lineno - 1, node.body[-1].end_lineno
                indent = re.match(r"\s*", lines[first]).group(0)
                new = lines[:first] + [indent + "return\n"] + lines[last:]
                yield f"{name}.{node.name}: body -> return", "".join(new)
        # (b) integer literals, (c) modes, (d) comparisons
        for i in range(a, b):
            line = lines[i]
            code = line.split("#")[0]
            if i in docs or code.strip().startswith(("class ", "def ", "@register")):
                continue
            for m in re.finditer(r"(?<![\w.])(\d+)(?![\w.])", code):
                n = int(m.group(1))
                new_line = line[:m.start()] + str(n + 1) + line[m.end():]
                yield f"{name} L{i+1}: {n} -> {n+1}", "".join(lines[:i] + [new_line] + lines[i+1:])
            for old, new in (("0 in ctx.modes", "1 in ctx.modes"), ("1 in ctx.modes", "0 in ctx.modes"),
                             (" == ", " != "), (" != ", " == ")):
                if old in code:
                    yield f"{name} L{i+1}: {old.strip()} -> {new.strip()}", "".join(lines[:i] + [line.replace(old, new, 1)] + lines[i+1:])


def main(which):
    path, test, names = MODULES[which]
    src = open(path).read()
    survived, total = [], 0
    try:
        for label, text in mutants(src, names):
            # skip docstring-only changes
            open(path, "w").write(text)
            total += 1
            # No bytecode at all: a same-size mutant written within the same second would otherwise
            # leave a .pyc that still looks valid for the next mutant (or the restored file).
            subprocess.run(["find", ".", "-name", "__pycache__", "-type", "d", "-prune", "-exec", "rm", "-rf", "{}", "+"])
            r = subprocess.run([sys.executable, "-B", "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *test.split()],
                               capture_output=True, text=True, timeout=600,
                               env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            if r.returncode == 0:
                survived.append(label)
                print("SURVIVED", label, flush=True)
    finally:
        open(path, "w").write(src)
        subprocess.run(["find", ".", "-name", "__pycache__", "-type", "d", "-prune", "-exec", "rm", "-rf", "{}", "+"])
    print(f"{which}: {total} mutants, {len(survived)} survived")
    for s in survived:
        print("  ", s)


if __name__ == "__main__":
    main(sys.argv[1])
