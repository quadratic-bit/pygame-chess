import os

import pygame


def load_image(name: str) -> pygame.Surface:
    """Load image as surface"""
    path = os.path.join("data", name)
    if not os.path.isfile(path):
        raise ValueError(f"File {path} is not found")
    return pygame.image.load(path).convert_alpha()


def extract_piece(piece: int) -> int:
    """Split piece on colour and actual piece and return piece type"""
    return int(bin(piece)[-3:], 2)


def extract_colour(piece: int) -> int:
    """Split piece on colour and actual piece and return piece colour"""
    return piece >> 3
