from typing import Optional

import pygame
from rich.traceback import install

from chess.board import Chessboard, Move, PieceType, PieceColour
from chess.bot import ChessBot

install(show_locals=True)


def main():
    # Pygame setup
    pygame.init()
    screen = pygame.display.set_mode((800, 800))
    pygame.display.set_caption("Chess")
    # Creating a board using FEN
    # 1r1q3r/3b2bk/p5pp/2QB4/5p2/P5nP/1PP5/2KRR3 b - - 3 6
    board = Chessboard.from_fen(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    COLOUR = PieceColour.White
    # Initialising the AI
    bot = ChessBot()
    # Let a first couple of moves be completely random!
    bot.set_random_moves(2)
    # Defining variables to interact with player
    grabbing: Optional[tuple[int, int]] = None
    hovering = False
    # Initial rendering
    board.render(screen)
    pygame.display.flip()
    # FPS handler
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
                # Find grabbed piece
                grabbing = (event.pos[0] // 100, event.pos[1] // 100)
                if board.at(*grabbing).Colour != COLOUR:
                    # Wrong colour!
                    grabbing = None
                else:
                    # Render a board with that grabbed piece being grabbed
                    board.render(screen, grabbing, event.pos)
                    pygame.display.flip()
            # Releasing LMB
            elif event.type == pygame.MOUSEBUTTONUP and \
                    event.button == pygame.BUTTON_LEFT:
                # Bot Flag
                last_move: Optional[Move] = None
                # Get position where player dropped the piece
                released = (event.pos[0] // 100, event.pos[1] // 100)
                if pygame.mouse.get_focused() and grabbing is not None and \
                        released != grabbing:
                    # Trying to make move
                    move = Move(grabbing[0] + grabbing[1] * 8,
                                released[0] + released[1] * 8,
                                board.at(*released))
                    # If we can make move -> let the bot make the next one
                    if board.can_make(move):
                        board.make_move(move)
                        last_move = move
                # Stop grabbing
                grabbing = None
                # Rendering board after releasing piece
                board.render(screen)
                pygame.display.flip()
                # Bot's turn
                if last_move is not None:
                    board.make_move(
                        bot.get_move(board, last_move, depth=3, debug=True))
                    # Rendering board after bot's turn
                    board.render(screen)
                    pygame.display.flip()
        # Handling mouse and cursor
        if pygame.mouse.get_focused():
            pos = pygame.mouse.get_pos()
            # Changing cursor state
            if board.at(pos[0] // 100, pos[1] // 100).Type != PieceType.Empty:
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
