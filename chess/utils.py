import os

import pygame


def load_image(name: str) -> pygame.surface.Surface:
    """Load image as surface"""
    path = f"chess/data/images/{name}"
    if not os.path.isfile(path):
        raise ValueError(f"File {path} is not found")
    return pygame.image.load(path).convert_alpha()


def load_sound(name: str) -> pygame.mixer.Sound:
    return pygame.mixer.Sound(f"chess/data/sounds/{name}")


def load_font(name: str, size: int) -> pygame.font.Font:
    return pygame.font.Font(f"chess/data/fonts/{name}", size)
