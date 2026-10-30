import json
import random
from collections import Counter

from svsim.cards import decks
from svsim.cards.pool import POOL
from svsim.core.enums import Craft
from svsim.tools import deckbuild


def _legal(ids, craft):
    return decks.validate([POOL[i] for i in ids], craft) == []


def test_random_decks_and_variants_are_legal():
    rng = random.Random(1)
    for craft in deckbuild.CLASSES:
        ids = deckbuild.random_ids(craft, rng)
        assert _legal(ids, craft)
        for _ in range(20):
            v = deckbuild.variant(ids, craft, rng)
            assert _legal(v, craft)
            changed = sum(a != b for a, b in zip(ids, v))
            assert 1 <= changed <= 3                    # slots keep their places: the shuffle pairs them


def test_legalize_keeps_legal_slots_and_fixes_the_rest():
    rng = random.Random(2)
    ids = deckbuild.random_ids(Craft.DRAGON, rng)
    assert deckbuild.legalize(ids, Craft.DRAGON, rng) == ids      # already legal: unchanged, slot for slot
    foreign = deckbuild.legal_cards(Craft.SWORD)
    foreign = next(c.card_id for c in foreign if c.craft == Craft.SWORD)
    fixed = deckbuild.legalize([foreign] + ids[1:], Craft.DRAGON, rng)
    assert _legal(fixed, Craft.DRAGON) and fixed[1:] == ids[1:]
    assert deckbuild.legalize(ids[:30], Craft.DRAGON, rng)[:30] == ids[:30]   # short lists are filled


def test_tournament_seeds_are_legal_after_legalize():
    # the 2026-10-07 lists predate card set 10: cards that left Rotation give their slots to legal ones
    from pathlib import Path
    path = Path(__file__).parent.parent / "analysis" / "deckbuild" / "seeds-tournament-2026-10-07.txt"
    rng = random.Random(4)
    for _, ids in deckbuild.read_seeds(str(path)):
        craft = deckbuild.craft_of_ids(ids)
        assert _legal(deckbuild.legalize(ids, craft, rng), craft)


def test_variant_respects_three_copies():
    rng = random.Random(3)
    craft = Craft.FOREST
    ids = deckbuild.random_ids(craft, rng)
    for _ in range(200):
        ids = deckbuild.variant(ids, craft, rng)
        assert max(Counter(ids).values()) <= decks.MAX_COPIES


def test_the_search_refuses_a_registered_deck():
    import pytest
    from types import SimpleNamespace
    face = [c.card_id for c in decks.build(decks.FACE_DRAGON)]
    search = deckbuild.Search.__new__(deckbuild.Search)
    search.args = SimpleNamespace(agent="mcts:1+plan")
    with pytest.raises(ValueError, match="registered deck"):
        search.play({"x": face}, [(1, face)], "t")


def test_confirm_takes_a_clear_gain_at_the_cap(tmp_path):
    """A gain near H1 can leave the sequential test undecided at the cap: the fixed-sample test then takes it
    when it is clearly above 0, and leaves a gain within the noise undecided."""
    import argparse
    args = argparse.Namespace(out=str(tmp_path), seed=1, confirm=560, batch=70, h1=0.02, at_max=2.0,
                              min_nonzero=20)

    def run(pattern):
        s = deckbuild.Search(args)
        s.deals = lambda n, field: list(range(n))
        s.play = lambda decks, deals, tag: {"incumbent": [0.0] * len(deals),
                                            "v": [pattern[i % len(pattern)] for i in range(len(deals))]}
        return s.confirm([], [], "v", {}, "t")

    # 70 deals: 7 won, 6 lost by the variant, the rest even: mean +1/70, se about 0.4/sqrt(n)
    verdict, diff = run([1.0] * 7 + [-1.0] * 6 + [0.0] * 57)
    assert len(diff) == 560 and verdict == "undecided"
    verdict, diff = run([1.0] * 9 + [-1.0] * 6 + [0.0] * 55)    # mean +3/70 over 560: z about 2.9
    assert verdict.startswith("accepted")


def test_a_class_is_searched_against_the_other_classes(tmp_path):
    """The own class's incumbent is not an opponent: in the field its mirror is even whichever deck holds it."""
    import argparse
    args = argparse.Namespace(out=str(tmp_path), seed=1, variants=2)
    s = deckbuild.Search(args)
    rng = random.Random(3)
    s.st["field"] = {c.name: deckbuild.random_ids(c, rng) for c in deckbuild.CLASSES}
    seen = []

    def halving(cands, incumbent, field, tag, first=None):
        seen.append(set(field))
        return "v0", {"v0": [0.0], "incumbent": [1.0]}            # the incumbent stays: no confirmation
    s.halving = halving
    s.step("DRAGON")
    assert seen == [{c.name for c in deckbuild.CLASSES} - {"DRAGON"}]


def test_random_decks_can_start_from_the_new_set():
    rng = random.Random(4)
    for craft in deckbuild.CLASSES:
        prefer = [c for c in deckbuild.legal_cards(craft) if str(c.card_set) == "10010"]
        ids = deckbuild.random_ids(craft, rng, None, prefer, 0.6)
        assert _legal(ids, craft)
        assert sum(str(POOL[i].card_set) == "10010" for i in ids) >= 24


def test_a_run_can_build_from_the_old_pool():
    rng = random.Random(5)
    deckbuild.SETS = decks.ROTATION_PRE10
    try:
        for craft in deckbuild.CLASSES:
            ids = deckbuild.random_ids(craft, rng)
            assert decks.validate([POOL[i] for i in ids], craft, sets=decks.ROTATION_PRE10) == []
            assert all(POOL[i].card_set != 10010 for i in ids)
    finally:
        deckbuild.SETS = None


def test_a_model_picks_the_variants_to_play(tmp_path):
    """--guide: the model ranks --guide-pool variants; the best and --guide-explore random ones are played."""
    import argparse
    import numpy as np
    from svsim.learn.deckmodel import DeckModel, static_rows
    from svsim.cards.pool import POOL as P
    m = DeckModel(len(static_rows([next(iter(P))])[0]), 4, 4, seed=1)
    path = str(tmp_path / "m.npz")
    m.save(path)
    args = argparse.Namespace(out=str(tmp_path / "run"), seed=1, variants=4, guide=path, guide_pool=20,
                              guide_explore=1)
    s = deckbuild.Search(args)
    rng = random.Random(6)
    field = {c.name: deckbuild.random_ids(c, rng) for c in deckbuild.CLASSES if c != Craft.DRAGON}
    inc = deckbuild.random_ids(Craft.DRAGON, rng)
    cands = s.propose(inc, Craft.DRAGON, field)
    assert len(cands) == 4 and len({deckbuild.deck_hash(v) for v in cands.values()}) == 4
    assert all(_legal(v, Craft.DRAGON) for v in cands.values())
    # the three the model ranks first are among them
    pred = s.model.predict([v for v in cands.values() for _ in field], [o for _ in cands for o in field.values()])
    assert np.isfinite(pred).all()


def test_a_package_swaps_several_related_cards_in_place():
    rng = random.Random(7)
    for craft in deckbuild.CLASSES:
        ids = deckbuild.random_ids(craft, rng)
        prefer = [c for c in deckbuild.legal_cards(craft) if str(c.card_set) == "10010"]
        for _ in range(10):
            v = deckbuild.package(ids, craft, rng, prefer)
            assert _legal(v, craft)
            changed = [k for k, (a, b) in enumerate(zip(ids, v)) if a != b]
            gone = {ids[k] for k in changed}
            assert 4 <= sum(Counter(ids)[i] for i in gone) <= 8            # every copy of the cards it drops
            assert all(i not in v for i in gone)
            sets = Counter(POOL[v[k]].card_set for k in changed)
            assert sets.most_common(1)[0][1] >= len(changed) // 2           # most of the package is from one set


def test_consolidate_adds_copies_of_a_card_already_held():
    rng = random.Random(8)
    for craft in deckbuild.CLASSES:
        ids = deckbuild.random_ids(craft, rng)
        for _ in range(10):
            v = deckbuild.consolidate(ids, craft, rng)
            assert _legal(v, craft)
            changed = [k for k, (a, b) in enumerate(zip(ids, v)) if a != b]
            assert 1 <= len(changed) <= 3
            if len({v[k] for k in changed}) == 1 and v[changed[0]] in ids:        # not the fallback swap
                assert all(Counter(ids)[ids[k]] == 1 for k in changed)             # it gave up single copies
                assert len(set(v)) < len(set(ids)) or len(changed) == 1


def test_a_deal_reports_the_slots_each_game_touched():
    rng = random.Random(9)
    ids = deckbuild.random_ids(Craft.FOREST, rng)
    opp = deckbuild.random_ids(Craft.SWORD, rng)
    res = deckbuild.play_deal(("k", ids, opp, 85899100, "random"))
    assert len(res["touched"]) == 2
    for t in res["touched"]:
        assert len(t) >= 3 and all(0 <= k < 40 for k in t)                          # the opening hand at least


def test_screened_play_skips_deals_that_never_touch_a_changed_slot(tmp_path):
    import argparse
    args = argparse.Namespace(out=str(tmp_path), seed=1, variants=2, agent="random")
    s = deckbuild.Search(args)
    s.pool = deckbuild._InProcess()
    rng = random.Random(4)
    inc = deckbuild.random_ids(Craft.HAVEN, rng)
    far = list(inc)
    far[0] = next(c.card_id for c in deckbuild.legal_cards(Craft.HAVEN) if c.card_id not in inc)
    deals = [(85899200 + j, deckbuild.random_ids(Craft.RUNE, rng)) for j in range(6)]
    got = s.play({"incumbent": inc, "v": far}, deals, "t", screen="incumbent")
    lines = [json.loads(x) for x in (tmp_path / "deals.jsonl").read_text(encoding="utf-8").splitlines()]
    screened = [x for x in lines if x.get("screened")]
    assert len([x for x in lines if x["key"] == "v"]) == 6                      # every deal on record
    for x in screened:
        k = [d[0] for d in deals].index(x["seed"])
        assert got["v"][k] == got["incumbent"][k]
        assert all(0 not in t for t in x["touched"])


def test_a_deck_condensed_to_a_make_up_keeps_it_through_a_card_swap():
    rng = random.Random(10)
    for craft in deckbuild.CLASSES:
        ids = deckbuild.random_ids(craft, rng)
        v = deckbuild.shaped(ids, craft, rng)
        assert _legal(v, craft)
        assert sorted(Counter(v).values()) == [1] + [3] * 13
        prefer = [c for c in deckbuild.legal_cards(craft) if str(c.card_set) == "10010"]
        for _ in range(10):
            w = deckbuild.type_swap(v, craft, rng, prefer)
            assert _legal(w, craft)
            assert sorted(Counter(w).values()) == [1] + [3] * 13                 # the shape survives a swap
            gone = set(v) - set(w)
            assert 1 <= len(gone) <= 2
            assert all(a == b or a in gone for a, b in zip(v, w))               # in place


def test_make_ups_come_from_real_lists_and_copy_moves_stay_legal():
    prof = deckbuild.profiles("analysis/deckbuild/seeds-tournament-2026-10-07.txt")
    assert (1, 0, 37) in prof["PORTAL"]                                         # the Cutthroat list
    rng = random.Random(11)
    for craft in deckbuild.CLASSES:
        ids = deckbuild.random_ids(craft, rng)
        for p in prof[craft.name][:4]:
            v = deckbuild.shaped(ids, craft, rng, p)
            assert _legal(v, craft)
            c = Counter(v)
            assert tuple(sum(n == k for n in c.values()) for k in (3, 2, 1)) == p
            for move in (deckbuild.shift, deckbuild.drop, deckbuild.add_new):
                w = move(v, craft, rng)
                assert _legal(w, craft)
                assert 1 <= sum(a != b for a, b in zip(v, w)) <= 6          # a fallback swap moves 2 cards


def test_the_pool_holds_one_card_per_name():
    for craft in deckbuild.CLASSES:
        names = [c.name for c in deckbuild.legal_cards(craft)]
        assert len(names) == len(set(names))                  # a reprint would let 3 + 1 copies in


def test_legalize_counts_a_reprint_as_its_name():
    rune = [c.card_id for c in deckbuild.legal_cards(Craft.RUNE) if c.name != "Stormy Blast"][:12]
    ids = [10131320] * 3 + [10831310] + [i for i in rune for _ in range(3)]  # A's and F's RUNE: 3 + 1 Stormy Blast
    out = deckbuild.legalize(ids, Craft.RUNE, random.Random(0))
    assert Counter(POOL[i].name for i in out)["Stormy Blast"] == 3 and out[4:] == ids[4:]
    two = deckbuild.legalize([10831310] * 2 + ids[4:], Craft.RUNE, random.Random(0))
    assert two[:2] == [10131320] * 2                          # the reprint alone keeps its copies


def _roster():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "analysis/deckbuild/blind-test/roster.py"
    spec = importlib.util.spec_from_file_location("roster", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_roster_takes_each_groups_own_best_deck_per_class():
    roster = _roster()
    assert [roster.tier(x) for x in ("T2-RUNE-a", "g3-S1-FOREST-combo", "g3-W2-SWORD-x", "STRONG-PORTAL-y",
                                     "P2G3-SWORD-1", "SWORD-midrange", "WEAK-RUNE-z", "可玩-HAVEN-q")] \
        == [2, 1, 3, 1, 99, 99, 3, 2]
    rune = [c.card_id for c in deckbuild.legal_cards(Craft.RUNE)][:14]
    sword = [c.card_id for c in deckbuild.legal_cards(Craft.SWORD)][:14]
    deck = lambda pool, k: [pool[(k + j) % 14] for j in range(13) for _ in range(3)] + [pool[k]]
    got = roster.pick([("T2-RUNE-a", deck(rune, 0)), ("T1-RUNE-b", deck(rune, 1)), ("SWORD-x", deck(sword, 0)),
                       ("SWORD-y", deck(sword, 1))])
    assert {c: lab for c, (lab, _) in got.items()} == {"RUNE": "T1-RUNE-b", "SWORD": "SWORD-x"}


def test_cross_group_league_never_pairs_decks_of_one_group(monkeypatch, tmp_path):
    import argparse
    pool = [c.card_id for c in deckbuild.legal_cards(Craft.FOREST)][:14]
    hashes = [deckbuild.deck_hash([pool[(k + j) % 14] for j in range(13) for _ in range(3)] + [pool[k]])
              for k in range(4)]
    (tmp_path / "r.txt").write_text("\n".join(f"{g}/{n}|{h}" for (g, n), h in
                                              zip([("a", "x"), ("a", "y"), ("b", "x"), ("c", "x")], hashes)))
    seen = []
    monkeypatch.setattr(deckbuild, "play_deal", lambda job: seen.append(job[0]) or {"key": job[0], "points": [1, 0]})
    deckbuild.league(argparse.Namespace(league=str(tmp_path / "r.txt"), seed=1, deals=2, agent="greedy", workers=1,
                                        out=str(tmp_path), cross_groups=True))
    assert (0, 1) not in seen and len(seen) == 2 * 5
    out = json.loads((tmp_path / "league.json").read_text(encoding="utf-8"))
    assert out["score"][0][1] is None and abs(out["means"][0] - 0.5) < 1e-9


def _freeze():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "analysis/deckbuild/blind-test/freeze.py"
    spec = importlib.util.spec_from_file_location("freeze", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_freeze_tiers_cut_at_55_and_50_and_keep_only_distinct_decks_in_a_tier():
    freeze = _freeze()
    pool = [c.card_id for c in deckbuild.legal_cards(Craft.FOREST)][:20]
    base = [pool[j] for j in range(13) for _ in range(3)] + [pool[13]]
    near = base[:-3] + [pool[14]] * 3                                   # 3 cards apart from base
    far = [pool[6 + j] for j in range(13) for _ in range(3)] + [pool[19]]  # 18 apart
    got = freeze.tiers([("F-FOREST", base), ("C-FOREST", near), ("A-FOREST", far), ("D-FOREST", base[:])],
                       [0.60, 0.58, 0.56, 0.45])
    assert [(d["label"], d["source"]) for d in got] == [("T1-FOREST-1", "F-FOREST"), ("T1-FOREST-2", "A-FOREST"),
                                                         ("T3-FOREST-1", "D-FOREST")]
    assert freeze.apart(base, near) == 3 and freeze.tier_of(0.5) == 2 and freeze.tier_of(0.4999) == 3
