from __future__ import annotations

import os
from collections import deque
from typing import Optional, Callable

import numpy as np
import pygame

import chess.utils as utils
from chess.utils import Move

WHITE = 8
BLACK = 16


class Chessboard:
    """Chessboard interface (8x8 field)"""

    def __init__(self, light_colour="#F0D9B5", dark_colour="#B58863") -> None:
        """
        Leading byte: 8 - White / 16 - Black
        Trailing byte: 0 - Empty
        1 - Pawn   / 2 - Knight
        3 - Bishop / 4 - Rook
        5 - Queen  / 6 - King
        """
        # Board itself
        self._board = np.zeros(64, dtype=int)
        # Stack of moves
        self._moves: deque[Move] = deque()
        # Active colour (or 8 either 16)
        self._active_colour = WHITE
        # Castling rights (bk, bq, wk, wq)
        self._castling_rights = {"bk": False, "bq": False,
                                 "wk": False, "wq": False}
        # En Passant target
        self._en_passant_target: Optional[int] = None
        # Half-move clock
        self._halfmoves = 0
        # Store piece types
        self._get_piece_type = {1: "pawn", 2: "knight", 3: "bishop",
                                4: "rook", 5: "queen", 6: "king"}
        # Store piece move validators
        self._get_validator: dict[int, Callable[[int, int, int, int], bool]] \
            = {1: self._can_pawn_make, 2: self._can_knight_make,
               3: self._can_bishop_make, 4: self._can_rook_make,
               5: self._can_queen_make, 6: self._can_king_make}
        # Board appearance
        self._light_colour = pygame.Color(light_colour)
        self._dark_colour = pygame.Color(dark_colour)
        self._side = 100  # px

    @property
    def board(self) -> np.ndarray:
        return self._board

    def render(self, screen: pygame.Surface,
               skip=None, pos=None) -> None:
        """Render chessboard"""
        if skip is not None and pos is None:
            raise ValueError("skip is not None but pos is None")
        screen.fill(self._dark_colour)
        group = pygame.sprite.Group()
        path = os.path.dirname(os.path.abspath(__file__))
        grabbed_data = None
        for i, piece in enumerate(self._board):
            x, y = i % 8, i // 8
            if (x + y) % 2 == 0:
                pygame.draw.rect(screen, self._light_colour,
                                 (x * self._side, y * self._side,
                                  self._side, self._side))
            if piece == 0:
                continue
            elif (x, y) == skip:
                grabbed_data = os.path.join(
                    path, "data",
                    f"{self._get_piece_type[utils.extract_type(piece)]}_"
                    f"{'w' if utils.extract_colour(piece) == 1 else 'b'}.png"
                ), i, group
            else:
                ChessPiece(
                    os.path.join(
                        path, "data",
                        f"{self._get_piece_type[utils.extract_type(piece)]}_"
                        f"{'w' if utils.extract_colour(piece) == 1 else 'b'}"
                        f".png"), i, group)
        if grabbed_data is not None:
            grabbed_piece = ChessPiece(*grabbed_data)
            grabbed_piece.rect.x = pos[0] - 50
            grabbed_piece.rect.y = pos[1] - 50
        group.draw(screen)

    def at(self, x: int, y: int) -> int:
        """Get piece from position on the board"""
        if 0 <= x <= 7 and 0 <= y <= 7:
            return self._board[x + y * 8]
        return 0

    def _force_can_make(self, move: Move) -> bool:
        """
        Check if the move is correct
        (!) Without checking king safety and turn order
        """
        # Can't make incorrect move
        if not utils.move_is_correct(move) or \
                move.captured != self._board[move.p_to]:
            return False
        this_piece, other_piece = \
            self._board[move.p_from], self._board[move.p_to]
        # Can't make move w/o piece itself
        if not this_piece:
            return False
        # Resolving colours and types
        this_colour = utils.extract_colour(this_piece)
        # # Can't make move when it's not your turn
        # if this_colour != self._active_colour:
        #     return False
        # # Lines above will complicate debugging
        this_type = utils.extract_type(this_piece)
        other_colour = utils.extract_colour(other_piece)
        # Can't eat pieces of your colour
        if other_colour == this_colour:
            return False
        y1, y2 = move.p_from // 8, move.p_to // 8
        x1, x2 = move.p_from % 8, move.p_to % 8
        return self._get_validator[this_type](x1, y1, x2, y2)

    def can_make(self, move: Move) -> bool:
        """Check if the move is correct"""
        # Checking basic move correctness
        if self._force_can_make(move):
            this_colour = utils.extract_colour(self._board[move.p_from])
            other_type = utils.extract_type(self._board[move.p_to])
            # Can't capture the king
            if other_type and self._get_piece_type[other_type] == "king":
                return False
            # Checking king safety
            self.make_move(move)
            safety = self._king_is_safe(this_colour)
            self.unmake_last_move()
            return safety
        return False

    def _horizontal_is_free(self, x1: int, y1: int, x2: int, _: int) -> bool:
        """Check if horizontal is free (not included end points)"""
        sign: int = np.sign(x2 - x1)
        for x in range(x1 + sign, x2, sign):
            if self._board[y1 * 8 + x]:
                return False
        return True

    def _vertical_is_free(self, x1: int, y1: int, _: int, y2: int) -> bool:
        """Check if vertical is free (not included end points)"""
        sign: int = np.sign(y2 - y1)
        for y in range(y1 + sign, y2, sign):
            if self._board[y * 8 + x1]:
                return False
        return True

    def _diagonal_is_free(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if diagonal is free (not included end points)"""
        signX: int = np.sign(x2 - x1)
        signY: int = np.sign(y2 - y1)
        for x, y in zip(range(x1 + signX, x2, signX),
                        range(y1 + signY, y2, signY)):
            if self._board[y * 8 + x]:
                return False
        return True

    def _can_bishop_make(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if bishop can make move"""
        return (abs(x1 - x2) == abs(y1 - y2)) and self._diagonal_is_free(
            x1, y1, x2, y2)

    def _can_rook_make(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if rook can make move"""
        return self._horizontal_is_free(x1, y1, x2, y2) \
            if y1 == y2 else self._vertical_is_free(x1, y1, x2, y2) \
            if x1 == x2 else False

    def _can_pawn_make(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if pawn can make move"""
        direction = -1 if \
            utils.extract_colour(self._board[y1 * 8 + x1]) == WHITE // 8 else 1
        to_capture = bool(self._board[y2 * 8 + x2])
        dx = abs(x2 - x1)
        if y2 - y1 == direction and \
                ((dx == 1 and to_capture) or (dx == 0 and not to_capture)):
            return True
        return (not to_capture and
                (y1 == 1 or y1 == 6) and
                y2 - y1 == direction * 2 and
                dx == 0)

    def _can_queen_make(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if queen can make move"""
        return \
            self._can_bishop_make(x1, y1, x2, y2) or \
            self._can_rook_make(x1, y1, x2, y2)

    @staticmethod
    def _can_knight_make(x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if knight can make move"""
        return abs(x2 - x1) + abs(y2 - y1) == 3

    @staticmethod
    def _can_king_make(x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if king can make move"""
        return abs(x2 - x1) < 2 and abs(y2 - y1) < 2

    def _king_is_safe(self, colour: int) -> bool:
        this_king = (colour * 8) | 6
        this_king_pos, = np.where(self._board == this_king)[0]
        for i, piece in enumerate(self._board):
            if utils.extract_colour(piece) != colour and piece != 0:
                if self._force_can_make(Move(i, this_king_pos, this_king)):
                    return False
        return True

    def make_move(self, move: Move) -> None:
        """
        Make move on the board
        Use board.make_move() to check if move is correct
        """
        self._board[move.p_to] = self._board[move.p_from]
        self._board[move.p_from] = 0
        self._moves.append(move)

    def unmake_last_move(self) -> None:
        """Unmaking last move on the board (no additional checking)"""
        last = self._moves.pop()
        self._board[last.p_from] = self._board[last.p_to]
        self._board[last.p_to] = last.captured

    @classmethod
    def _parse_fen(cls, fen_string: str) -> Chessboard:
        """
        Parse FEN string,
        use Chessboard.from_fen() instead
        """
        # Setup
        error_info = f"Invalid FEN string: {fen_string}"
        tmp_board = cls()
        fen_dict = {"p": 1, "n": 2, "b": 3, "r": 4, "q": 5, "k": 6}
        fields = fen_string.split()
        assert len(fields) == 6, error_info
        tmp_position = 0
        # Parse First field (Piece Placement)
        for sym in fields[0]:
            if sym == "/":
                assert tmp_position % 8 == 0, error_info
                continue
            if sym.isdigit():
                tmp_position += int(sym)
                assert tmp_position < 64, error_info
                continue
            assert sym.lower() in fen_dict, error_info
            clr = 8 if sym.isupper() else 16
            type_ = fen_dict[sym.lower()]
            tmp_board._board[tmp_position] = clr | type_
            tmp_position += 1
        assert tmp_position == 64, error_info
        # Parse Second Field (Active Color)
        if fields[1] == "b":
            tmp_board._active_colour = 16
        elif fields[1] == "w":
            tmp_board._active_colour = 8
        else:
            assert False, error_info
        # Parse Third field (Castling Rights)
        if fields[2] != "-":
            for castling in fields[2]:
                if castling.lower() == "q":
                    tmp_board._castling_rights[
                        "wq" if castling.isupper() else "bq"] = True
                elif castling.lower() == "k":
                    tmp_board._castling_rights[
                        "wk" if castling.isupper() else "bk"] = True
                else:
                    assert False, error_info
        # Parse Fourth field (Possible En Passant Targets)
        alg_cell = fields[3]
        if alg_cell != "-":
            assert len(alg_cell) == 2, error_info
            assert 96 < ord(alg_cell[0]) < 105, error_info
            assert alg_cell[1].isdigit() and 0 < int(alg_cell[1]) < 9
            tmp_board._en_passant_target = int(
                (8 - int(alg_cell[1])) * 8 + ord(alg_cell[0]) - 97)
        # Parse Fifth field (Half-move Clock)
        assert fields[4].isnumeric() and int(fields[4]) >= 0, error_info
        tmp_board._halfmoves = int(fields[4])
        # Parse Sixth field (Full-move Number)
        assert \
            fields[5].isnumeric() and \
            abs(tmp_board._halfmoves * 2 - int(fields[5])) < 2, error_info
        return tmp_board

    @classmethod
    def from_fen(cls, fen_string: str) -> Chessboard:
        """Create Chessboard using FEN"""
        try:
            return cls._parse_fen(fen_string)
        except AssertionError as e:
            raise ValueError(str(e))


class ChessPiece(pygame.sprite.Sprite):
    """Chess Piece class"""

    def __init__(self, sprite_img: str, pos: int,
                 *groups: pygame.sprite.AbstractGroup):
        super().__init__(*groups)
        self.image = utils.load_image(sprite_img)
        self.rect = self.image.get_rect()
        self.move_sprite(pos)

    def move_sprite(self, position: int) -> None:
        self.rect.x = position % 8 * 100
        self.rect.y = position // 8 * 100
