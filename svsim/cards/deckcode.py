"""Official deck hashes, as used in deck-builder share links:

    https://shadowverse-wb.com/{lang}/deck/detail/?hash=1.2.cQnG.cR2I...

A hash is "{battle_format}.{class}.{token}...": one 4-character token per card
(40 for a full deck), each a card_id written in base 64 with the alphabet below,
most significant digit first. Battle format 1 is Rotation, 2 Unlimited.
"""
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
_VALUE = {ch: i for i, ch in enumerate(ALPHABET)}
ROTATION, UNLIMITED = 1, 2


def encode_card(card_id: int) -> str:
    digits = []
    for _ in range(4):
        card_id, digit = divmod(card_id, 64)
        digits.append(ALPHABET[digit])
    if card_id:
        raise ValueError("card id too large for 4 digits")
    return "".join(reversed(digits))


def decode_card(token: str) -> int:
    value = 0
    for ch in token:
        value = value * 64 + _VALUE[ch]
    return value


def encode_deck(battle_format: int, craft: int, card_ids: list[int]) -> str:
    return ".".join([str(battle_format), str(craft)] + [encode_card(c) for c in card_ids])


def decode_deck(deck_hash: str) -> tuple[int, int, list[int]]:
    """Returns (battle_format, class, card_ids)."""
    battle_format, craft, *tokens = deck_hash.strip().split(".")
    return int(battle_format), int(craft), [decode_card(t) for t in tokens]
