import os
from typing import NamedTuple

import pygame

Move = NamedTuple("Move", (("p_from", int), ("p_to", int), ("captured", int)))


def move_is_correct(move: Move) -> bool:
    return 0 <= move.p_to <= 64 and 0 <= move.p_from <= 64


def load_image(name: str) -> pygame.Surface:
    """Load image as surface"""
    path = os.path.join("data", name)
    if not os.path.isfile(path):
        raise ValueError(f"File {path} is not found")
    return pygame.image.load(path).convert_alpha()


def extract_type(piece: int) -> int:
    """Split piece on colour and actual piece and return piece type"""
    return int(bin(piece)[-3:], 2)


def extract_colour(piece: int) -> int:
    """Split piece on colour and actual piece and return piece colour"""
    return piece >> 3
