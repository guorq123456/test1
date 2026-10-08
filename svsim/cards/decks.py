"""Decklists and deck validation.

The starter decklists are Game8's (Pirate Sword 2026-09-30, Ramp Dragon
2026-10-05), decoded through the official deck API.
"""
from collections import Counter
import random

from svsim.core.carddef import CardDef
from svsim.core.enums import Craft
from svsim.core.script import has_script

from . import deckcode, dragon, forest, neutral, sword, unlimited
from .pool import POOL, collectible

DECK_SIZE = 40
MAX_COPIES = 3

PIRATE_SWORD = {
    sword.FLASHSTEP_QUICKBLADER: 3, sword.ORCHESTRATED_SILENCE: 3, sword.YIDMETRA: 3,
    sword.OPEN_SEA_SCOUT: 3, sword.WHIRLPOOL_GUNNER: 3, sword.SPLENDOR_OF_THE_GOLDBLOOM: 3,
    sword.SEVERED_TIES: 3, sword.ZETA_AND_BEA: 3, sword.LAGE_DOR: 3, sword.UNKEI: 3,
    sword.ROUGHWATER_FIRST_MATE: 3, sword.GOLDEN_KNIGHT: 3, sword.BARBAROS: 3,
    sword.BELTEZORE: 1,
}

RAMP_DRAGON = {
    neutral.LYRIA: 3, dragon.VORLALAI: 3, dragon.DRAGONEWT_PROMOTER: 3, dragon.KIMIKA: 2,
    dragon.SLOTH_OF_THE_CRESTPETAL: 3, dragon.DRAGONSIGN: 3, dragon.LAZING_FLAME: 1,
    dragon.ROAR_OF_PROMINENCE: 2, neutral.FATE_OF_THE_WORLD: 2, dragon.ZOOEY: 3,
    dragon.SAGATSUMATSU: 3, dragon.NORMAGDALA: 3, dragon.LUMIORE_AND_ARGENTE: 3,
    dragon.BURNITE: 3, dragon.ERNTZ: 3,
}

# Unlimited: "Rhinoceroach Forest" (破魔虫精灵), from the player's deck list (2026-10-05).
# Killer Rhinoceroach gains +1 attack per card played this turn and has Storm; the
# deck plays cheap cards and returns it to hand to play it again and again.
RHINO_FOREST = {
    neutral.WORLD_OF_GAMES: 3, forest.SPROUTING_INITIATE: 3, unlimited.FAIRY_CONVOCATION: 3,
    unlimited.BABY_CARBUNCLE: 2, unlimited.GARDENS_ALLURE: 3, unlimited.KILLER_RHINOCEROACH: 3,
    unlimited.GODWOOD_STAFF: 2, unlimited.BAYLE: 3, forest.SATHANID: 2, forest.BUG_ALERT: 3,
    unlimited.ERADICATING_ARROW: 3, forest.VIRID_LIEUTENANT: 1, unlimited.LAMBENT_CAIRN: 3,
    forest.MIROKU: 3, unlimited.GLADE: 3,
}
UNLIMITED_DECKS = {"rhino": RHINO_FOREST}

# Every card the simulator knows, by id (deck cards, tokens, leader-area objects).
KNOWN: dict[int, CardDef] = POOL


def build(counts: dict[CardDef, int]) -> list[CardDef]:
    return [card for card, n in counts.items() for _ in range(n)]


def craft_of(deck: list[CardDef]) -> Craft:
    crafts = {c.craft for c in deck} - {Craft.NEUTRAL}
    return crafts.pop() if len(crafts) == 1 else Craft.NEUTRAL


def validate(deck: list[CardDef], craft: Craft | None = None, unlimited: bool = False) -> list[str]:
    """Problems that make a deck illegal (empty list = legal) in Rotation, or in
    Unlimited with `unlimited`."""
    craft = craft_of(deck) if craft is None else craft
    problems = []
    if len(deck) != DECK_SIZE:
        problems.append(f"{len(deck)} cards, need {DECK_SIZE}")
    for card, n in Counter(deck).items():
        if n > MAX_COPIES:
            problems.append(f"{n} copies of {card.name}")
        if card.is_token:
            problems.append(f"{card.name} is a token")
        if card.craft not in (Craft.NEUTRAL, craft):
            problems.append(f"{card.name} is not {craft.name.title()} or Neutral")
        if card.card_set and not card.rotation and not card.is_token and not unlimited:
            problems.append(f"{card.name} is not legal in Rotation")
    return problems


def unimplemented(cards) -> list[CardDef]:
    """Cards with abilities but no script. Keyword-only and vanilla cards are fine
    without one; anything else silently playing as a vanilla card would be wrong."""
    return sorted({c for c in cards if c.has_ability and not has_script(c.card_id)},
                  key=lambda c: c.card_id)


def random_deck(craft: Craft, rng: random.Random, implemented_only: bool = True) -> list[CardDef]:
    """A random legal Rotation deck for `craft` (class and Neutral cards, up to 3
    copies each). With `implemented_only`, cards still missing a script are left out."""
    options = [c for c in collectible(craft)
               if not (implemented_only and c.has_ability and not has_script(c.card_id))]
    if len(options) * MAX_COPIES < DECK_SIZE:
        raise ValueError(f"only {len(options)} usable {craft.name.title()} cards")
    deck: list[CardDef] = []
    while len(deck) < DECK_SIZE:
        card = rng.choice(options)
        if deck.count(card) < MAX_COPIES:
            deck.append(card)
    return deck


def from_hash(deck_hash: str, pool: dict[int, CardDef] | None = None) -> list[CardDef]:
    """Build a deck from an official deck hash. Card ids missing from `pool`
    (default: the implemented cards) raise KeyError."""
    pool = KNOWN if pool is None else pool
    _, _, ids = deckcode.decode_deck(deck_hash)
    return [pool[i] for i in ids]


def to_hash(deck: list[CardDef], battle_format: int = deckcode.ROTATION) -> str:
    return deckcode.encode_deck(battle_format, int(craft_of(deck)), [c.card_id for c in deck])


# Rotation meta decks from Game8's tier list (Azvaldt Revenant, 2026-10-06), by their deck
# codes: Combo Elf (Tier 1) and Face Dragon (Tier 2). Ramp Dragon and Pirate Royal (Tier 1)
# match RAMP_DRAGON and PIRATE_SWORD card for card; the list's other decks use cards not
# scripted yet.
COMBO_FOREST_HASH = ("1.1.dhqc.e4Gg.e4Gg.e4Gg.e6FE.e6kU.e6x8.e6x8.e6x8.eVLe.eVLe.et1G.et4E.etl-.etl-.etl-.etm8."
                     "etm8.etm8.fGAU.fGAU.fGAU.fds6.fds6.fds6.fe5k.fe5k.fe5k.fe8s.fe8s.fe8s.feLM.feLM.feLM.fea-.fea-."
                     "fea-.feb8.feb8.feb8")
FACE_DRAGON_HASH = ("1.4.eDme.eDme.eDme.eE3E.eE3E.eE3E.eb-U.eb-U.ecTk.ecTk.ecgE.ecgE.ecgE.ecgO.ecgO.ecgO.fN08.fN08."
                    "fN08.flAs.flAs.flAs.flD-.flD-.flD-.flQU.flQU.flQU.flTc.flTc.flTc.flg6.flg6.flg6.fljE.fljE.fljE."
                    "flvk.flvk.flvk")


def _listing(deck_hash: str) -> dict[CardDef, int]:
    out: dict[CardDef, int] = {}
    for c in from_hash(deck_hash):
        out[c] = out.get(c, 0) + 1
    return out


COMBO_FOREST = _listing(COMBO_FOREST_HASH)
FACE_DRAGON = _listing(FACE_DRAGON_HASH)

# Tournament decks (the architecture session's import list, 2026-10-07: JCS season 3 and the pro
# league's lists, analysis/tournament-decks-2026-10-07.md on claude/bot-architecture-design): for each
# archetype the full 40 that the most tournament lists share. Combo Elf (连击妖), Nemesis puppets
# (机锋), Ramp Dragon's tournament build (2 Kitsunebi, 2 Fire Dragon, 1 Bahamut; no Solar Flare, Dragon's
# Nap or World) and Pirate Royal's (3 Listening Spy, 2 Martial Emperor; no Silent Siege). The Game8
# decks above stay: saved games refer to them.
ELF_T_HASH = ("1.1.dhqm.dhqm.dkWe.e4Gg.e4Gg.e4Gg.e6kU.e6x8.e6x8.e6x8.eVLe.eVLe.eVLe.etGk.etGk.etGk.etl-.etl-."
              "etl-.etm8.etm8.fFRw.fFRw.fFRw.fGAU.fGAU.fGAU.fds6.fds6.fds6.fe5k.fe5k.fe5k.feLM.feLM.feLM.feOU."
              "fea-.fea-.fea-")
NEMESIS_T_HASH = ("1.7.cQnG.cR2I.dhLM.dhqc.dhqm.di4E.dyR6.dyRQ.dyzU.dz9-.eKrc.eL5E.eLN-.eLaU.eLae.eSRY.ej--.ej_8."
                  "eqqU.f5gc.f5jk.f5wE.f69s.f6PU.f6Pe.fDUc.fU5Q.fUKu.fUp-.fUq8.fsVc.fsVm.fslE.fsoM.fs-s.ft1-.ftEU."
                  "ftEU.ftEU.ftEe")
RAMP_T_HASH = ("1.4.cJl6.cJl6.cJl6.dhqm.dhqm.drrE.drrE.drrO.drrO.drrO.eE3E.eE3E.eE3E.eEFk.eEFk.eEFk.ecgE.ecgE."
               "ecgE.ecgO.ecgO.ecgO.e-Ls.e-Ls.e-Ls.e_4k.e_4k.e_4k.fDkE.fN08.fN08.fN08.fNIk.fNIk.fNVO.fNVO.fNVO."
               "flvu.flvu.flvu")
PIRATE_T_HASH = ("1.2.cEZs.cEZs.dmj6.dmj6.dmj6.dmyk.dmyk.dmyk.e9Ak.e9Ak.e9Ak.e9NO.e9NO.e9NO.eXnu.eXnu.eXnu.evi-."
                 "evi-.evi-.fgIM.fgIM.fgIM.fgX-.fgX-.fgX-.fgb6.fgb6.fgb6.fgnc.fgnc.fgnc.fgqk.fgqk.fgqk.fh1E.fh1E."
                 "fh1E.fh1O.fh1O")
ELF_T = _listing(ELF_T_HASH)
NEMESIS_T = _listing(NEMESIS_T_HASH)
RAMP_T = _listing(RAMP_T_HASH)
PIRATE_T = _listing(PIRATE_T_HASH)


# The decks the tools know by name (ui.session.DECKS uses the same keys). A learned evaluation
# is kept per pair of these (learn.model, learn.phased): two decks of one class can want
# different evaluations (Ramp Dragon's mirror model must not score Face Dragon's games).
# More tournament decks for the universal bot's leave-one-deck-out test (claude/universal-bot, 2026-10-08): for each
# archetype of the meta research's tournament lists, the list sharing the most cards with the others (medoid).
HAVEN_T_HASH = "1.6.cOc2.cOc2.cOc2.dw0Q.dwU6.dwU6.dwU6.eShA.eShA.egps.egps.egps.egrQ.egrQ.egrQ.eh52.eh52.eh52.ehKg.ehKg.ehKg.ehYk.ehYk.ehYk.ehYu.ehYu.ehYu.f3Fw.f3Fw.f3Fw.f3lA.f3lA.f3lA.f3zO.f3zO.fS9g.fS9g.fS9g.fqaA.fqaA"   # bishop, PS8a MRG toby
ABYSS_T_HASH = "1.5.dhqc.dhqc.dtoY.dtoY.dtoY.eGCk.eGCk.eegM.ef6e.ef6e.f0oG.f0oG.f0oG.f11k.f11k.f11k.f1KU.f1KU.f1KU.f1W-.f1W-.f1W-.f1X8.f1X8.f1X8.fPCm.fPCm.fPCm.fPxU.fndG.fndG.fndG.fnsk.fnsk.foL-.foL-.foL-.foM8.foM8.foM8"   # nm, PS8a RID deko
RUNE_T_HASH = "1.3.cH3E.cH3E.cH3E.cfTu.cfTu.cfTu.e4Gg.e4Gg.e4Gg.eBpe.eBpe.eZV6.eZV6.eZYE.eZYE.eZYE.eZns.eZns.eZns.ea1U.ea1U.ea1U.eaD-.eaD-.eaD-.eaE8.eaE8.eaE8.fDXk.fDXk.fDXk.fKZk.fKZk.fKpM.fKpM.fKpM.fKsU.fKsU.fKsU.fL2-"   # crystal (魔手法), PS7b MRG — before the 09-29 patch: label results "补丁前样本"
SWORD2_T_HASH = "1.2.cEZs.cEZs.cEZs.cEaA.dhqm.dmyk.dmyk.dmyk.eXnu.eXnu.eXnu.evTW.evTW.evTW.evi-.evi-.evi-.evj8.evj8.evj8.evm6.evm6.evm6.evyc.evyc.evyc.ewCE.ewCE.ewCE.ewCO.ewCO.ewCO.fHts.fHts.fIck.fIck.fIck.fIcu.fIcu.fIcu"   # synergy (连携皇家), PS7b RJ — before the 09-29 patch: label results "补丁前样本"
EXP_T_HASH = "1.3.cH3E.cH3E.cfTu.cfTu.cfTu.dpCU.dpCU.dpCU.fDXk.fDXk.fDXk.fKpM.fKpM.fKpM.fKsU.fKsU.fKsU.fL2-.fL2-.fL2-.fikc.fikc.fikc.fink.fink.fi-E.fi-E.fi-E.fj1M.fj1M.fj1M.fjDs.fjDs.fjDs.fjG-.fjG-.fjG-.fjTU.fjTU.fjTU"   # experiment (实验体法, Sephie), PS8b VL monakawan — after the 09-29 patch, medoid of 5 post-patch lists
HAVEN_T = _listing(HAVEN_T_HASH)
ABYSS_T = _listing(ABYSS_T_HASH)
RUNE_T = _listing(RUNE_T_HASH)
SWORD2_T = _listing(SWORD2_T_HASH)
EXP_T = _listing(EXP_T_HASH)

NAMED = {"rhino": RHINO_FOREST, "ramp": RAMP_DRAGON, "pirate": PIRATE_SWORD, "combo": COMBO_FOREST,
         "face": FACE_DRAGON, "elf-t": ELF_T, "nemesis-t": NEMESIS_T, "ramp-t": RAMP_T, "pirate-t": PIRATE_T,
         "bishop-t": HAVEN_T, "nm-t": ABYSS_T, "crystal-t": RUNE_T, "synergy-t": SWORD2_T, "exp-t": EXP_T}
_NAMED_IDS: dict | None = None


def identify(cards) -> str | None:
    """The named deck these cards (CardDefs or CardInstances: a deck list at the start of a game,
    which engine.new_game files as PlayerState.deck_name; tokens ignored) can all come from: the
    one they fit with the fewest cards to spare, or None. Mid-game the cards a player has left
    may not fit (Dragonewt Promoter adds copies of itself), so read deck_name then."""
    global _NAMED_IDS
    if _NAMED_IDS is None:
        _NAMED_IDS = {key: {c.card_id: n for c, n in listing.items()} for key, listing in NAMED.items()}
    counts: dict[int, int] = {}
    for c in cards:
        defn = getattr(c, "defn", c)
        if not defn.is_token:
            counts[defn.card_id] = counts.get(defn.card_id, 0) + 1
    if not counts:
        return None
    best, spare = None, None
    for key, ids in _NAMED_IDS.items():
        if all(ids.get(cid, 0) >= n for cid, n in counts.items()):
            left = sum(ids.values()) - sum(counts.values())
            if spare is None or left < spare:
                best, spare = key, left
    return best
