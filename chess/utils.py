import os

import pygame


def load_image(name: str) -> pygame.surface.Surface:
    """Load image as surface"""
    path = f"chess/data/{name}"
    if not os.path.isfile(path):
        raise ValueError(f"File {path} is not found")
    return pygame.image.load(path).convert_alpha()

