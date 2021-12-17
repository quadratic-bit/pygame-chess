from __future__ import annotations

import math
import os
from collections import deque
from typing import Optional, Callable

import numpy as np
import pygame

from chess.const import PieceType, PieceColour, Piece, CastlingType, Move
from chess.utils import load_image


class Chessboard:
    """Chessboard interface (8x8 field)"""

    def __init__(self, light_colour="#F0D9B5", dark_colour="#B58863") -> None:
        # Board itself
        self._board = np.array([Piece.empty()] * 64)
        # Active colour
        self._active_colour = PieceColour.White
        # Castling rights
        self._castling_rights: dict[CastlingType, bool] = {
            CastlingType.BlackKing: False,
            CastlingType.BlackQueen: False,
            CastlingType.WhiteKing: False,
            CastlingType.WhiteQueen: False}
        # Store piece types as strings
        self._get_piece_str = {PieceType.Pawn: "pawn",
                               PieceType.Knight: "knight",
                               PieceType.Bishop: "bishop",
                               PieceType.Rook: "rook",
                               PieceType.Queen: "queen",
                               PieceType.King: "king"}
        # Store piece move validators
        self._get_validator: dict[
            PieceType, Callable[[int, int, int, int], bool]] \
            = {PieceType.Pawn: self._can_pawn_make,
               PieceType.Knight: self._can_knight_make,
               PieceType.Bishop: self._can_bishop_make,
               PieceType.Rook: self._can_rook_make,
               PieceType.Queen: self._can_queen_make,
               PieceType.King: self._can_king_make}
        # En Passant target
        self._en_passant_target: Optional[int] = None
        # Half-move clock
        self._halfmoves = 0
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
            if piece.Type == PieceType.Empty:
                continue
            elif (x, y) == skip:
                grabbed_data = os.path.join(
                    path, "data",
                    f"{self._get_piece_str[piece.Type]}_"
                    f"{'w' if piece.Colour == PieceColour.White else 'b'}.png"
                ), i, group
            else:
                PieceSprite(
                    os.path.join(
                        path, "data",
                        f"{self._get_piece_str[piece.Type]}_"
                        f"{'w' if piece.Colour == PieceColour.White else 'b'}"
                        f".png"), i, group)
        if grabbed_data is not None:
            grabbed_piece = PieceSprite(*grabbed_data)
            grabbed_piece.rect.x = pos[0] - 50  # type: ignore
            grabbed_piece.rect.y = pos[1] - 50  # type: ignore
        group.draw(screen)

    def at(self, x: int, y: int) -> Piece:
        """Get piece from position on the board"""
        if 0 <= x <= 7 and 0 <= y <= 7:
            return self._board[x + y * 8]
        return Piece.empty()

    def _force_can_make(self, move: Move) -> bool:
        """
        Check if the move is correct
        (!) Without checking king safety and turn order
        """
        # Can't make incorrect move
        if move.Captured != self._board[move.To]:
            return False
        this_piece, other_piece = \
            self._board[move.From], self._board[move.To]
        # Can't make move w/o piece itself
        if this_piece.Type == PieceType.Empty:
            return False
        # Resolving colours and types
        # # Can't make move when it's not your turn
        # if this_piece[0] != self._active_colour:
        #     return False
        # # Lines above will complicate debugging
        # Can't eat pieces of your colour
        if other_piece.Type != PieceType.Empty and \
                other_piece.Colour == this_piece.Colour:
            return False
        y1, y2 = move.From // 8, move.To // 8
        x1, x2 = move.From % 8, move.To % 8
        return self._get_validator[this_piece.Type](x1, y1, x2, y2)

    def can_make(self, move: Move) -> bool:
        """Check if the move is correct"""
        # Checking basic move correctness
        if self._force_can_make(move):
            # Can't capture the king
            if self._board[move.To].Type == PieceType.King:
                return False
            # Checking king safety
            self.make_move(move)
            safety = self._king_is_safe(self._board[move.To].Colour)
            self.unmake_move(move)
            return safety
        return False

    def make_move(self, move: Move) -> None:
        """
        Make move on the board
        Use board.make_move() to check if move is correct
        """
        self._board[move.To] = self._board[move.From]
        self._board[move.From] = Piece.empty()

    def unmake_move(self, move: Move) -> None:
        """Unmake move on the board (no additional checking)"""
        self._board[move.From] = self._board[move.To]
        self._board[move.To] = move.Captured

    def get_all_moves(self, colour: PieceColour) -> deque[Move]:
        moves: deque[Move] = deque()
        for i, piece_from in enumerate(self._board):
            if piece_from.Type == PieceType.Empty or \
                    piece_from.Colour != colour:
                continue
            for j, piece_to in enumerate(self._board):
                move = Move(i, j, piece_to)
                if self.can_make(move):
                    moves.append(move)
        return moves

    def _king_is_safe(self, colour: PieceColour) -> bool:
        """Check if king is safe on current board state"""
        king = Piece(PieceType.King, colour)
        king_pos = np.where(self._board == king)[0][0]
        for i, piece in enumerate(self._board):
            if piece.Type != PieceType.Empty and piece.Colour != colour:
                if self._force_can_make(Move(i, king_pos, king)):
                    return False
        return True

    def _can_pawn_make(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if pawn can make move"""
        direction = -1 if \
            self._board[y1 * 8 + x1].Colour == PieceColour.White \
            else 1
        to_capture = self._board[y2 * 8 + x2].Type != PieceType.Empty
        dx = abs(x2 - x1)
        if y2 - y1 == direction and \
                ((dx == 1 and to_capture) or (dx == 0 and not to_capture)):
            return True
        return (not to_capture and
                (y1 == 1 or y1 == 6) and
                y2 - y1 == direction * 2 and
                dx == 0)

    @staticmethod
    def _can_knight_make(x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if knight can make move"""
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        return dx == 1 and dy == 2 or dx == 2 and dy == 1

    def _can_bishop_make(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if bishop can make move"""
        return (abs(x1 - x2) == abs(y1 - y2)) and self._diagonal_is_free(
            x1, y1, x2, y2)

    def _can_rook_make(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if rook can make move"""
        return self._horizontal_is_free(x1, y1, x2, y2) \
            if y1 == y2 else self._vertical_is_free(x1, y1, x2, y2) \
            if x1 == x2 else False

    def _can_queen_make(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if queen can make move"""
        return \
            self._can_bishop_make(x1, y1, x2, y2) or \
            self._can_rook_make(x1, y1, x2, y2)

    @staticmethod
    def _can_king_make(x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if king can make move"""
        return abs(x2 - x1) < 2 and abs(y2 - y1) < 2

    def _diagonal_is_free(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if diagonal is free (not included end points)"""
        signX = int(math.copysign(1, x2 - x1))
        signY = int(math.copysign(1, y2 - y1))
        for x, y in zip(range(x1 + signX, x2, signX),
                        range(y1 + signY, y2, signY)):
            if self._board[y * 8 + x].Type != PieceType.Empty:
                return False
        return True

    def _horizontal_is_free(self, x1: int, y1: int, x2: int, _: int) -> bool:
        """Check if horizontal is free (not included end points)"""
        sign = int(math.copysign(1, x2 - x1))
        for x in range(x1 + sign, x2, sign):
            if self._board[y1 * 8 + x].Type != PieceType.Empty:
                return False
        return True

    def _vertical_is_free(self, x1: int, y1: int, _: int, y2: int) -> bool:
        """Check if vertical is free (not included end points)"""
        sign = int(math.copysign(1, y2 - y1))
        for y in range(y1 + sign, y2, sign):
            if self._board[y * 8 + x1].Type != PieceType.Empty:
                return False
        return True

    @classmethod
    def _parse_fen(cls, fen_string: str) -> Chessboard:
        """
        Parse FEN string,
        use Chessboard.from_fen() instead
        """
        # Setup
        error_info = f"Invalid FEN string: {fen_string}"
        tmp_board = cls()
        fen_dict = {"p": PieceType.Pawn,
                    "n": PieceType.Knight,
                    "b": PieceType.Bishop,
                    "r": PieceType.Rook,
                    "q": PieceType.Queen,
                    "k": PieceType.King}
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
                assert tmp_position < 65, error_info
                continue
            assert sym.lower() in fen_dict, error_info
            clr = PieceColour.White if sym.isupper() else PieceColour.Black
            type_ = fen_dict[sym.lower()]
            tmp_board._board[tmp_position] = Piece(type_, clr)
            tmp_position += 1
        assert tmp_position == 64, error_info
        # Parse Second Field (Active Color)
        if fields[1] == "b":
            tmp_board._active_colour = PieceColour.Black
        elif fields[1] == "w":
            tmp_board._active_colour = PieceColour.White
        else:
            assert False, error_info
        # Parse Third field (Castling Rights)
        if fields[2] != "-":
            for castling in fields[2]:
                if castling.lower() == "q":
                    tmp_board._castling_rights[
                        CastlingType.WhiteQueen
                        if castling.isupper()
                        else CastlingType.BlackQueen] = True
                elif castling.lower() == "k":
                    tmp_board._castling_rights[
                        CastlingType.WhiteKing
                        if castling.isupper()
                        else CastlingType.BlackKing] = True
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

    @classmethod
    def from_state(cls, state: np.ndarray) -> Chessboard:
        """Create Chessboard using state"""
        tmp_board = cls()
        tmp_board._board = state
        return tmp_board


class PieceSprite(pygame.sprite.Sprite):
    """Piece class for drawing on a board"""

    def __init__(self, sprite_img: str, pos: int,
                 *groups: pygame.sprite.AbstractGroup):
        super().__init__(*groups)
        self.image = load_image(sprite_img)
        self.rect = self.image.get_rect()
        self.move_sprite(pos)

    def move_sprite(self, position: int) -> None:
        self.rect.x = position % 8 * 100  # type: ignore
        self.rect.y = position // 8 * 100  # type: ignore
