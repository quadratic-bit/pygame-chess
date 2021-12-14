from typing import Optional

import pygame

from board import Chessboard, Move


def main():
    # Pygame setup
    pygame.init()
    screen = pygame.display.set_mode((800, 800))
    pygame.display.set_caption("Chess")
    # Creating a board using FEN
    board = Chessboard.from_fen(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    # Defining variables
    grabbing: Optional[tuple[int, int]] = None
    hovering = False
    # Initial rendering
    board.render(screen)
    pygame.display.flip()
    # FPS counter
    clock = pygame.time.Clock()
    FPS = 60
    # Starting main loop
    running = True
    while running:
        for event in pygame.event.get():
            # Quitting game
            if event.type == pygame.QUIT:
                running = False
                break
            # LMB while hovering above a piece (grab a piece)
            if event.type == pygame.MOUSEBUTTONDOWN and \
                    event.button == pygame.BUTTON_LEFT and hovering:
                grabbing = (event.pos[0] // 100, event.pos[1] // 100)
                board.render(screen, grabbing, event.pos)
                pygame.display.flip()
            # Releasing LMB
            elif event.type == pygame.MOUSEBUTTONUP and \
                    event.button == pygame.BUTTON_LEFT:
                # Get position, where player dropped the piece
                released = (event.pos[0] // 100, event.pos[1] // 100)
                if pygame.mouse.get_focused() and grabbing is not None and \
                        released != grabbing:
                    # Trying to make move
                    move = Move(grabbing[0] + grabbing[1] * 8,
                                released[0] + released[1] * 8,
                                board.at(*released))
                    if board.can_make(move):
                        board.make_move(move)
                # Stop grabbing
                grabbing = None
                # Rendering board after releasing piece
                board.render(screen)
                pygame.display.flip()
        if pygame.mouse.get_focused():
            pos = pygame.mouse.get_pos()
            # Changing cursor state
            if board.at(pos[0] // 100, pos[1] // 100):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                hovering = True
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                hovering = False
            # Rendering board and a hovering piece
            if grabbing:
                board.render(screen, grabbing, pos)
                pygame.display.flip()
        else:
            # Mouse is out of window -> stop grabbing
            grabbing = None
            board.render(screen)
            pygame.display.flip()
            hovering = False
        clock.tick(FPS)
