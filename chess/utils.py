import os

import pygame

import chess.board as bd


def render_board(screen: pygame.Surface, board: bd.Chessboard,
                 skip=None, pos=None) -> None:
    """Render chessboard"""
    if skip is not None and pos is None:
        raise ValueError("skip is not None but pos is None")
    side = 100
    light_clr, dark_clr = pygame.Color("#F0D9B5"), pygame.Color("#B58863")
    screen.fill(dark_clr)
    group = pygame.sprite.Group()
    pieces_dict = {1: "pawn", 2: "knight", 3: "bishop",
                   4: "rook", 5: "queen", 6: "king"}
    path = os.path.dirname(os.path.abspath(__file__))
    grabbed_data = None
    for i, piece in enumerate(board.board):
        x, y = i % 8, i // 8
        if (x + y) % 2 == 0:
            pygame.draw.rect(screen, light_clr,
                             (x * side, y * side, side, side))
        if piece == 0:
            continue
        elif (x, y) == skip:
            grabbed_data = os.path.join(
                path, "data", f"{pieces_dict[int(bin(piece)[-3:], 2)]}_"
                              f"{'w' if piece >> 3 == 1 else 'b'}.png"), i, \
                           group
        else:
            bd.ChessPiece(
                os.path.join(path, "data",
                             f"{pieces_dict[int(bin(piece)[-3:], 2)]}_"
                             f"{'w' if piece >> 3 == 1 else 'b'}.png"),
                i, group)
    if grabbed_data is not None:
        grabbed_piece = bd.ChessPiece(*grabbed_data)
        grabbed_piece.rect.x = pos[0] - 50
        grabbed_piece.rect.y = pos[1] - 50
    group.draw(screen)


def load_image(name: str) -> pygame.Surface:
    """Load image as surface"""
    path = os.path.join("data", name)
    if not os.path.isfile(path):
        raise ValueError(f"File {path} is not found")
    return pygame.image.load(path).convert_alpha()
