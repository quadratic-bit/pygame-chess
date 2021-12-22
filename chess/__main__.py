import os
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
    # Start position: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    # Advanced:       1r1q3r/3b2bk/p5pp/2QB4/5p2/P5nP/1PP5/2KRR3 b - - 6 12
    # Pawn promotion: 8/6P1/2Q5/4p3/3qP3/5Q2/1q3PK1/qk6 w - - 0 73
    board = Chessboard.from_fen(
        "8/6P1/2Q5/4p3/3qP3/5Q2/1q3PK1/qk6 w - - 0 73")
    # Colour
    COLOUR_PLAYER = PieceColour.White
    COLOUR_OPPONENT = PieceColour.Black
    # Sounds
    path = os.path.dirname(os.path.abspath(__file__))
    sound_common = pygame.mixer.Sound(os.path.join(path, "data", "common.ogg"))
    sound_check = pygame.mixer.Sound(os.path.join(path, "data", "check.ogg"))
    # Initialising the AI
    bot = ChessBot()
    # Defining variables to interact with player
    grabbing: Optional[tuple[int, int]] = None
    hovering = False
    # Render Flag
    last_move: Optional[Move] = None
    # Bot Flag
    last_move_uncaught = False
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
                if board.at(*grabbing).Colour != COLOUR_PLAYER:
                    # Wrong colour!
                    grabbing = None
                else:
                    # Render a board with that grabbed piece being grabbed
                    board.render(screen, last_move, grabbing, event.pos)
                    pygame.display.flip()
            # Releasing LMB
            elif event.type == pygame.MOUSEBUTTONUP and \
                    event.button == pygame.BUTTON_LEFT:
                # Get position where player dropped the piece
                released = (event.pos[0] // 100, event.pos[1] // 100)
                if pygame.mouse.get_focused() and grabbing is not None and \
                        released != grabbing:
                    # Trying to make move
                    move = Move(grabbing[0] + grabbing[1] * 8,
                                released[0] + released[1] * 8,
                                board.at(*released))
                    # If we can make move -> let the bot make the next one
                    move = board.can_make(move)
                    if move is not None:
                        board.make_move(move)
                        if board.king_is_safe(COLOUR_OPPONENT):
                            sound_common.play()
                        else:
                            sound_check.play()
                        last_move = move
                        last_move_uncaught = True
                # Stop grabbing
                grabbing = None
                # Rendering board after releasing piece
                board.render(screen, last_move)
                pygame.display.flip()
                # Bot's turn
                if last_move is not None and last_move_uncaught:
                    last_move = bot.get_move(board, last_move, debug=True)
                    board.make_move(last_move)
                    if board.king_is_safe(COLOUR_PLAYER):
                        sound_common.play()
                    else:
                        sound_check.play()
                    # Updating flag
                    last_move_uncaught = False
                    # Rendering board after bot's turn
                    board.render(screen, last_move)
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
                board.render(screen, last_move, grabbing, pos)
                pygame.display.flip()
        else:
            # Mouse is out of window -> stop grabbing
            grabbing = None
            board.render(screen, last_move)
            pygame.display.flip()
            hovering = False
        clock.tick(FPS)
