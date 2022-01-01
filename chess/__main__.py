from sys import exit
from typing import Optional, Final

import pygame
from rich.traceback import install

from chess.board import Chessboard, Move, PieceType, PieceColour
from chess.bot import ChessBot
from chess.const import GameState

install(show_locals=True)


def terminate() -> None:
    pygame.quit()
    exit(0)


def main():
    # Pygame setup
    pygame.init()
    SCREEN_W, SCREEN_H = SCREEN_SHAPE = 1200, 800  # type: Final
    screen = pygame.display.set_mode(SCREEN_SHAPE)
    pygame.display.set_caption("Chess")
    # Creating a board using FEN
    # Start position: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    # Advanced:       1r1q3r/3b2bk/p5pp/2QB4/5p2/P5nP/1PP5/2KRR3 b - - 6 12
    # Pawn promotion: 8/6P1/2Q5/4p3/3qP3/5Q2/1q3PK1/qk6 w - - 36 73
    # Checkmate:      3rkbnr/1p1bp3/1q1p3p/p5p1/3n4/PPR2Q2/5PPP/6K1 w - - 1 2
    board = Chessboard.from_fen(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    # Colour
    COLOUR_PLAYER = PieceColour.White
    COLOUR_OPPONENT = PieceColour.Black
    # Sounds
    sound_common = pygame.mixer.Sound("chess/data/common.ogg")
    sound_check = pygame.mixer.Sound("chess/data/check.ogg")
    # Initialising the AI
    bot = ChessBot()
    # Defining variables to interact with player
    grabbing: Optional[tuple[int, int]] = None
    hovering = False
    # Render Flag
    last_move: Optional[Move] = None
    # Bot Flags
    last_move_uncaught = False
    board_info: Optional[tuple] = None
    # Initial rendering
    board.render(screen)
    pygame.display.flip()
    # FPS handler
    clock = pygame.time.Clock()
    FPS = 60

    # Functions
    def toggle_state() -> None:
        state = board.toggle_state()
        if state == GameState.Continue:
            return
        else:
            board.render(screen, last_move, game_info=board_info)
            scaffold = pygame.Surface(SCREEN_SHAPE)
            pygame.draw.rect(scaffold, pygame.Color("black"),
                             (0, 0, SCREEN_W, SCREEN_H))
            scaffold.set_alpha(64)
            screen.blit(scaffold, (0, 0))
            mate = pygame.font.SysFont("arial", 80).render(
                "Мат!"
                if state == GameState.Checkmate
                else "Пат!", True, pygame.Color("white"))
            score = pygame.font.SysFont("arial", 80).render(
                "0-1"
                if board.active_colour == PieceColour.White
                else "1-0", True, pygame.Color("white"))
            bg = pygame.Surface((600, 400))
            bg.fill(pygame.Color("black"))
            bg.set_alpha(180)
            mate.set_alpha(128)
            score.set_alpha(128)
            mate_rect = mate.get_rect()
            bg_rect = bg.get_rect()
            score_rect = score.get_rect()
            mdx = (bg_rect.w - mate_rect.w) // 2
            mdy = (bg_rect.h - mate_rect.h) // 3
            sdx = (bg_rect.w - score_rect.w) // 2
            sdy = (bg_rect.h - score_rect.h) // 1.5
            screen.blit(bg, (300, 200))
            screen.blit(mate, (300 + mdx, 200 + mdy))
            screen.blit(score, (300 + sdx, 200 + sdy))
            pygame.display.flip()
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            while True:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        terminate()

    # Starting main loop
    while True:
        for event in pygame.event.get():
            # Quitting game
            if event.type == pygame.QUIT:
                terminate()
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
                    board.render(screen, last_move, grabbing, event.pos,
                                 game_info=board_info)
                    pygame.display.flip()
            # Releasing LMB
            elif event.type == pygame.MOUSEBUTTONUP and \
                    event.button == pygame.BUTTON_LEFT:
                # Get position where player dropped the piece
                released = (event.pos[0] // 100, event.pos[1] // 100)
                if pygame.mouse.get_focused() and grabbing is not None and \
                        released != grabbing and event.pos[0] <= 800 and \
                        event.pos[1] <= 800:
                    # Trying to make move
                    x, y = grabbing[0] + grabbing[1] * 8, \
                           released[0] + released[1] * 8
                    move = Move(x, y, board.at(*released))
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
                        toggle_state()
                # Stop grabbing
                grabbing = None
                # Rendering board after releasing piece
                board.render(screen, last_move, game_info=board_info)
                pygame.display.flip()
                # Bot's turn
                if last_move is not None and last_move_uncaught:
                    last_move, board_info = bot.get_move(board, last_move)
                    board.make_move(last_move)
                    if board.king_is_safe(COLOUR_PLAYER):
                        sound_common.play()
                    else:
                        sound_check.play()
                    toggle_state()
                    # Updating flag
                    last_move_uncaught = False
                    # Rendering board after bot's turn
                    board.render(screen, last_move, game_info=board_info)
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
                board.render(screen, last_move, grabbing, pos,
                             game_info=board_info)
                pygame.display.flip()
        else:
            # Mouse is out of window -> stop grabbing
            grabbing = None
            board.render(screen, last_move, game_info=board_info)
            pygame.display.flip()
            hovering = False
        clock.tick(FPS)
