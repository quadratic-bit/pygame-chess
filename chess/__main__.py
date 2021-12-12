from typing import Optional

import pygame

from board import Chessboard, Move
from chess.utils import render_board


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 800))
    pygame.display.set_caption("Chess")
    board = Chessboard.from_fen(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    grabbing: Optional[tuple[int, int]] = None
    hovering = False
    render_board(screen, board)
    pygame.display.flip()
    clock = pygame.time.Clock()
    FPS = 60
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.MOUSEBUTTONDOWN and \
                    event.button == pygame.BUTTON_LEFT and hovering:
                grabbing = (event.pos[0] // 100, event.pos[1] // 100)
                render_board(screen, board, grabbing, event.pos)
                pygame.display.flip()
            elif event.type == pygame.MOUSEBUTTONUP and \
                    event.button == pygame.BUTTON_LEFT:
                released = (event.pos[0] // 100, event.pos[1] // 100)
                if pygame.mouse.get_focused() and grabbing is not None and \
                        released != grabbing:
                    move = Move(grabbing[0] + grabbing[1] * 8,
                                released[0] + released[1] * 8)
                    board.make_move(move)
                grabbing = None
                render_board(screen, board)
                pygame.display.flip()
        if pygame.mouse.get_focused():
            pos = pygame.mouse.get_pos()
            if board.at(pos[0] // 100, pos[1] // 100):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                hovering = True
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                hovering = False
            if grabbing:
                render_board(screen, board, grabbing, pos)
                pygame.display.flip()
        else:
            grabbing = None
            hovering = False
        clock.tick(FPS)
