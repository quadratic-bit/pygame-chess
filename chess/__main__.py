from sys import exit
from typing import Optional, Final

import pygame
from rich.traceback import install

from chess.board import Chessboard, Move, PieceType, PieceColour
from chess.bot import ChessBot
from chess.const import GameState
from chess.utils import load_image, load_sound, load_font

install(show_locals=True)


def terminate() -> None:
    pygame.quit()
    exit(0)


def main():
    # Game setup

    # Pygame stuff
    pygame.init()
    SCREEN_W, SCREEN_H = SCREEN_SHAPE = 1200, 800  # type: Final
    screen = pygame.display.set_mode(SCREEN_SHAPE)
    pygame.display.set_caption("Chess")
    # Colours
    colour_bg = pygame.Color("#443742")
    colour_contrast_bg = pygame.Color("#8D80AD")
    # FPS handler
    clock = pygame.time.Clock()
    FPS = 60
    # Creating a board using FEN
    # Start position: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    # Advanced:       1r1q3r/3b2bk/p5pp/2QB4/5p2/P5nP/1PP5/2KRR3 b - - 6 12
    # Pawn promotion: 8/6P1/2Q5/4p3/3qP3/5Q2/1q3PK1/qk6 w - - 36 73
    # Checkmate:      3rkbnr/1p1bp3/1q1p3p/p5p1/3n4/PPR2Q2/5PPP/6K1 w - - 1 2
    board = Chessboard.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    # Sounds
    sound_common = load_sound("common.ogg")
    sound_check = load_sound("check.ogg")
    # Fonts
    font_header = load_font("ubuntumono/UbuntuMono-R.ttf", 90)
    font_option = load_font("ubuntumono/UbuntuMono-B.ttf", 55)
    # Defining variables to interact with player
    grabbing: Optional[tuple[int, int]] = None
    hovering = False
    # Render Flag
    last_move: Optional[Move] = None

    def start_screen() -> None:
        """Start screen"""
        nonlocal screen
        bg_start_img = pygame.transform.scale(load_image('bg_start.png'), SCREEN_SHAPE)
        screen.blit(bg_start_img, (0, 0))
        pygame.display.flip()
        start_waiting = True
        while start_waiting:
            for event_ in pygame.event.get():
                if event_.type == pygame.QUIT:
                    terminate()
                elif event_.type == pygame.KEYDOWN or event_.type == pygame.MOUSEBUTTONDOWN:
                    start_waiting = False
                    break
            clock.tick(FPS)

    def choose_game_mode_screen() -> bool:
        """Game mode screen ( True if vs AI, False otherwise )"""
        nonlocal screen
        screen.fill(colour_bg)
        pygame.draw.rect(screen, colour_contrast_bg, (300, 352, 600, 96))
        pygame.draw.rect(screen, colour_contrast_bg, (340, 576, 520, 96))
        button_vs_ai = font_header.render("Выберите режим игры", True, "white")
        button_vs_player = font_option.render("Против компьютера", True, "black")
        screen.blit(button_vs_ai, (170, 131))
        screen.blit(button_vs_player, (400, 368))
        screen.blit(font_option.render("Против игрока", True, "black"), (460, 593))
        # Icons by Font Awesome!
        # License: https://fontawesome.com/license/free
        screen.blit(pygame.transform.scale(load_image('desktop-solid.png'), (80, 80)), (308, 360))
        screen.blit(pygame.transform.scale(load_image('chess-solid.png'), (80, 80)), (348, 584))
        pygame.display.flip()
        button_rects = [pygame.Rect(300, 352, 600, 96), pygame.Rect(340, 576, 520, 96)]

        def is_colliding(m_pos: tuple[int, int]) -> bool:
            return any(map(lambda b: b.x < m_pos[0] < b.x + b.w and b.y < m_pos[1] < b.y + b.h, button_rects))

        while True:
            for event_ in pygame.event.get():
                if event_.type == pygame.QUIT:
                    terminate()
                elif event_.type == pygame.MOUSEBUTTONDOWN:
                    if is_colliding(event_.pos):
                        if button_rects[0].x < event_.pos[0] < button_rects[0].x + button_rects[0].w and \
                                button_rects[0].y < event_.pos[1] < button_rects[0].y + button_rects[0].h:
                            return True
                        return False
                elif event_.type == pygame.MOUSEMOTION:
                    if is_colliding(event_.pos):
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                    else:
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            clock.tick(FPS)

    def end_screen(state: GameState, board_state: tuple) -> None:
        board.render(screen, last_move, game_info=board_state)
        scaffold = pygame.Surface(SCREEN_SHAPE)
        pygame.draw.rect(scaffold, pygame.Color("black"),
                         (0, 0, SCREEN_W, SCREEN_H))
        scaffold.set_alpha(0)
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
        mate.set_alpha(255)
        score.set_alpha(255)
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

    def toggle_state(board_state: tuple) -> None:
        """Check and toggle game state (for endgames especially)"""
        state = board.toggle_state()
        if state == GameState.Continue:
            return
        else:
            end_screen(state, board_state)

    def game_loop(vs_ai: bool) -> None:
        """Main game loop"""
        nonlocal grabbing, hovering, last_move

        if vs_ai:
            # Initialising the AI
            bot = ChessBot()
            # Bot Flag
            last_move_uncaught = False
        # Toggle flag
        board_info: Optional[tuple] = None
        # Initial rendering
        board.render(screen)
        pygame.display.flip()

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
                    if board.at(*grabbing).Colour != board.active_colour:
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
                            if board.king_is_safe(board.passive_colour):
                                sound_common.play()
                            else:
                                sound_check.play()
                            last_move = move
                            last_move_uncaught = True
                            toggle_state(board_info)
                    # Stop grabbing
                    grabbing = None
                    # Rendering board after releasing piece
                    board.render(screen, last_move, game_info=board_info)
                    pygame.display.flip()
                    if vs_ai:
                        # Bot's turn
                        if last_move is not None and last_move_uncaught:
                            last_move, board_info = bot.get_move(board, last_move)
                            board.make_move(last_move)
                            if board.king_is_safe(board.passive_colour):
                                sound_common.play()
                            else:
                                sound_check.play()
                            toggle_state(board_info)
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

    # Starting the game
    start_screen()
    game_loop(choose_game_mode_screen())


if __name__ == "__main__":
    main()
