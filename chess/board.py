from __future__ import annotations

import math
import os
from collections import deque
from typing import Optional, Callable

import numpy as np
import pygame

from chess.const import PieceType, PieceColour, Piece, CastlingType, Move, \
    PIECE_INDICES, init_zobrist, MoveFlags
from chess.utils import load_image


class Chessboard:
    """Chessboard interface (8x8 field)"""

    def __init__(self, light_colour="#F0D9B5", dark_colour="#B58863") -> None:
        # Board itself
        self._board = np.array([Piece.empty()] * 64)
        # Active colour
        self._active_colour = PieceColour.White
        # Castling rights
        self._castling_rights = {
            PieceColour.White: {
                CastlingType.KingSide: False,
                CastlingType.QueenSide: False
            },
            PieceColour.Black: {
                CastlingType.KingSide: False,
                CastlingType.QueenSide: False
            }
        }
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
        # Init zobrist hash
        self._z_table = init_zobrist()
        # Board appearance
        self._light_colour = pygame.Color(light_colour)
        self._dark_colour = pygame.Color(dark_colour)
        self._light_complementary = pygame.Color("#DBAB84")
        self._dark_complementary = pygame.Color("#DBC095")
        self._side = 100  # px

    @property
    def board(self) -> np.ndarray:
        return self._board

    @property
    def halfmoves(self) -> int:
        return self._halfmoves

    def hash(self) -> int:
        h = 0
        for i in range(64):
            piece = self._board[i]
            if piece.Type != PieceType.Empty:
                j = PIECE_INDICES[piece.Type.value | piece.Colour.value]
                h ^= self._z_table[i][j]
        return h

    def set_colours(self, light_colour: str, dark_colour: str,
                    light_complementary: str, dark_complementary: str) -> None:
        self._light_colour = pygame.Color(light_colour)
        self._dark_colour = pygame.Color(dark_colour)
        self._light_complementary = pygame.Color(light_complementary)
        self._dark_complementary = pygame.Color(dark_complementary)

    def render(self, screen: pygame.Surface,
               last_move=None, skip=None, pos=None) -> None:
        """Render chessboard"""
        if skip is not None and pos is None:
            raise ValueError("skip is not None but pos is None")
        screen.fill(self._dark_colour)
        group = pygame.sprite.Group()
        path = os.path.dirname(os.path.abspath(__file__))
        grabbed_data = None
        for i, piece in enumerate(self._board):
            x, y = i % 8, i // 8
            if last_move is not None and last_move.From == i:
                pygame.draw.rect(screen, self._light_complementary,
                                 (x * self._side, y * self._side,
                                  self._side, self._side))
            elif last_move is not None and last_move.To == i or (x, y) == skip:
                pygame.draw.rect(screen, self._dark_complementary,
                                 (x * self._side, y * self._side,
                                  self._side, self._side))
            elif (x + y) % 2 == 0:
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

    def _force_can_make(self, move: Move) -> Optional[Move]:
        """
        Check if the move is correct with adding corresponding flags
        (!) Without checking king safety and turn order
        """
        # Can't make incorrect move
        if move.Captured != self._board[move.To]:
            return None
        this_piece: Piece = self._board[move.From]
        other_piece: Piece = self._board[move.To]
        # Can't make move w/o piece itself
        if this_piece.Type == PieceType.Empty:
            return None
        # Resolving colours and types
        # # Can't make move when it's not your turn
        # if this_piece[0] != self._active_colour:
        #     return False
        # # Lines above will complicate debugging
        # Can't eat pieces of your colour
        if other_piece.Type != PieceType.Empty and \
                other_piece.Colour == this_piece.Colour:
            return None
        # Resolving piece xy coordinates to calculate move possibility
        y1, y2 = move.From // 8, move.To // 8
        x1, x2 = move.From % 8, move.To % 8
        # Castling
        if this_piece.Type == PieceType.King and \
                y1 == y2 and abs(x1 - x2) == 2 \
                and move.Captured == Piece.empty():
            castling = CastlingType.QueenSide if x1 - x2 == 2 \
                else CastlingType.KingSide
            if castling == CastlingType.QueenSide and (
                    self._board[move.To - 1] != Piece.empty() or
                    self._board[move.From - 1] != Piece.empty() or
                    self._board[move.From - 2] != Piece.empty()):
                return None
            elif castling == CastlingType.KingSide and (
                    self._board[move.From + 1] != Piece.empty() or
                    self._board[move.From + 2] != Piece.empty()):
                return None
            if self._castling_rights[this_piece.Colour][castling]:
                lost_castling = {castling}
                other_side = CastlingType.KingSide \
                    if castling == CastlingType.QueenSide \
                    else CastlingType.QueenSide
                if self._castling_rights[this_piece.Colour][other_side]:
                    lost_castling.add(other_side)
                move = Move(move.From, move.To, move.Captured,
                            MoveFlags(Castling=castling,
                                      LoseCastling=lost_castling))
            else:
                return None
        elif this_piece.Type == PieceType.King:
            lost_castling = set()
            if self._castling_rights[this_piece.Colour][
                    CastlingType.KingSide]:
                lost_castling.add(CastlingType.KingSide)
            if self._castling_rights[this_piece.Colour][
                    CastlingType.QueenSide]:
                lost_castling.add(CastlingType.QueenSide)
            move = Move(move.From, move.To, move.Captured,
                        MoveFlags(LoseCastling=lost_castling))
        elif this_piece.Type == PieceType.Rook:
            if x1 == 0 and self._castling_rights[this_piece.Colour][
                    CastlingType.QueenSide]:
                move = Move(move.From, move.To,
                            move.Captured,
                            MoveFlags(LoseCastling={CastlingType.QueenSide}))
            elif x1 == 7 and self._castling_rights[this_piece.Colour][
                    CastlingType.KingSide]:
                move = Move(move.From, move.To,
                            move.Captured,
                            MoveFlags(LoseCastling={CastlingType.KingSide}))
        if self._get_validator[this_piece.Type](x1, y1, x2, y2):
            return move
        return None

    def can_make(self, move: Move) -> Optional[Move]:
        """Check if the move is correct"""
        # Checking basic move correctness
        completed_move = self._force_can_make(move)
        if completed_move is not None:
            # Can't capture the king
            if self._board[move.To].Type == PieceType.King:
                return None
            # Checking king safety
            self.make_move(move)
            safety = self._king_is_safe(self._board[move.To].Colour)
            self.unmake_move(move)
            return completed_move if safety else None
        return None

    def make_move(self, move: Move) -> None:
        """
        Make move on the board
        Use board.make_move() to check if move is correct
        """
        if move.Flags.LoseCastling is not None:
            this_colour = self._board[move.From].Colour
            for castling in move.Flags.LoseCastling:
                self._castling_rights[this_colour][castling] = False
        self._halfmoves += 1
        self._board[move.To] = self._board[move.From]
        self._board[move.From] = Piece.empty()
        if move.Flags.Castling is not None:
            if move.Flags.Castling == CastlingType.KingSide:
                self._board[move.From + 1] = self._board[move.To + 1]
                self._board[move.To + 1] = Piece.empty()
            else:
                self._board[move.From - 1] = self._board[move.To - 2]
                self._board[move.To - 2] = Piece.empty()

    def unmake_move(self, move: Move) -> None:
        """Unmake move on the board (no additional checking)"""
        if move.Flags.LoseCastling is not None:
            this_colour = self._board[move.To].Colour
            for castling in move.Flags.LoseCastling:
                self._castling_rights[this_colour][castling] = True
        self._halfmoves -= 1
        self._board[move.From] = self._board[move.To]
        self._board[move.To] = move.Captured
        if move.Flags.Castling is not None:
            if move.Flags.Castling == CastlingType.KingSide:
                self._board[move.To + 1] = self._board[move.From + 1]
                self._board[move.From + 1] = Piece.empty()
            else:
                self._board[move.To - 2] = self._board[move.From - 1]
                self._board[move.From - 1] = Piece.empty()

    def get_all_moves(self, colour: PieceColour) -> deque[Move]:
        moves: deque[Move] = deque()
        for i, piece_from in enumerate(self._board):
            if piece_from.Type == PieceType.Empty or \
                    piece_from.Colour != colour:
                continue
            for j, piece_to in enumerate(self._board):
                move = self.can_make(Move(i, j, piece_to))
                if move is not None:
                    moves.append(move)
        return moves

    def king_is_safe(self, colour: PieceColour) -> bool:
        return self._king_is_safe(colour)

    def _king_is_safe(self, colour: PieceColour) -> bool:
        """Check if king is safe on current board state"""
        king_pos = np.where(self._board == Piece(PieceType.King, colour))[0][0]
        king_x, king_y = king_pos % 8, king_pos // 8
        right_side = range(king_x + 1, 8)
        left_side = range(king_x - 1, -1, -1)
        bottom_side = range(king_y + 1, 8)
        top_side = range(king_y - 1, -1, -1)
        o_colour = PieceColour.White if \
            colour == PieceColour.Black else PieceColour.Black
        o_pawn = Piece(PieceType.Pawn, o_colour)
        o_knight = Piece(PieceType.Knight, o_colour)
        o_bishop = Piece(PieceType.Bishop, o_colour)
        o_rook = Piece(PieceType.Rook, o_colour)
        o_queen = Piece(PieceType.Queen, o_colour)
        o_king = Piece(PieceType.King, o_colour)

        # Horizontal and vertical
        def _line(iter_side: range, const_x: bool) -> bool:
            for component in iter_side:
                attacking_piece = self.at(king_x, component) \
                    if const_x \
                    else self.at(component, king_y)
                if attacking_piece.Type != PieceType.Empty:
                    if attacking_piece == o_rook or \
                            attacking_piece == o_queen:
                        return True
                    return False
            return False

        if _line(right_side, False) or _line(left_side, False) or \
                _line(top_side, True) or _line(bottom_side, True):
            return False

        # All diagonals
        def _diagonal(iter_side_x: range, iter_side_y: range) -> bool:
            for x, y in zip(iter_side_x, iter_side_y):
                attacking_piece = self.at(x, y)
                if attacking_piece.Type != PieceType.Empty:
                    if attacking_piece == o_bishop or \
                            attacking_piece == o_queen:
                        return True
                    return False
            return False

        if _diagonal(right_side, bottom_side) or \
                _diagonal(left_side, bottom_side) or \
                _diagonal(right_side, top_side) or \
                _diagonal(left_side, top_side):
            return False

        # Pawns
        sign_ = -1 if colour == PieceColour.White else 1
        if self.at(king_x + 1, king_y + sign_) == o_pawn or \
                self.at(king_x - 1, king_y + sign_) == o_pawn:
            return False

        # Knight
        if self.at(king_x + 1, king_y + 2) == o_knight or \
                self.at(king_x - 1, king_y + 2) == o_knight or \
                self.at(king_x + 2, king_y + 1) == o_knight or \
                self.at(king_x - 2, king_y + 1) == o_knight or \
                self.at(king_x + 1, king_y - 2) == o_knight or \
                self.at(king_x - 1, king_y - 2) == o_knight or \
                self.at(king_x + 2, king_y - 1) == o_knight or \
                self.at(king_x - 2, king_y - 1) == o_knight:
            return False
        # King
        opponent_king_pos = np.where(self._board == o_king)[0][0]
        if self._can_king_make(opponent_king_pos % 8,
                               opponent_king_pos // 8,
                               king_x, king_y):
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
        return (abs(x2 - x1) < 2 and abs(y2 - y1) < 2) or \
               (abs(x1 - x2) == 2 and y1 == y2)

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
                        PieceColour.White if castling.isupper()
                        else PieceColour.Black][CastlingType.QueenSide] = True
                elif castling.lower() == "k":
                    tmp_board._castling_rights[
                        PieceColour.White if castling.isupper()
                        else PieceColour.Black][CastlingType.KingSide] = True
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
        # Parse Fifth field (Full-move Number)
        assert fields[4].isnumeric()
        # Parse Sixth field (Half-move Clock)
        assert fields[5].isnumeric() and int(fields[5]) >= 0, error_info
        tmp_board._halfmoves = int(fields[5])
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
