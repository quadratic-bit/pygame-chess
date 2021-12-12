from __future__ import annotations

from typing import NamedTuple, Optional

import numpy as np
from pygame.sprite import Sprite, AbstractGroup

import chess.utils as utils


Move = NamedTuple("Move", (("p_from", int), ("p_to", int)))


class Chessboard:
    """Chessboard interface (8x8 field)"""

    def __init__(self) -> None:
        """
        Leading byte: 8 - White / 16 - Black
        Trailing byte: 0 - Empty
        1 - Pawn   / 2 - Knight
        3 - Bishop / 4 - Rook
        5 - Queen  / 6 - King
        """
        # Board itself
        self._board = np.zeros(64, dtype=int)
        # Active colour (or 8 either 16)
        self._active_colour = 8
        # Castling rights (bk, bq, wk, wq)
        self._castling_rights = {"bk": False, "bq": False,
                                 "wk": False, "wq": False}
        # En Passant target
        self._en_passant_target: Optional[int] = None
        # Half-move clock
        self._halfmoves = 0

    def at(self, x: int, y: int) -> int:
        if 0 <= x <= 7 and 0 <= y <= 7:
            return self._board[x + y * 8]
        return 0

    def make_move(self, move: Move):
        self._board[move.p_to] = self._board[move.p_from]
        self._board[move.p_from] = 0

    @classmethod
    def _parse_fen(cls, fen_string: str) -> Chessboard:
        """
        Parse FEN string,
        use Chessboard.from_fen() instead
        """
        # Setup
        _error_info = f"Invalid FEN string: {fen_string}"
        _tmp_board = cls()
        _fen_dict = {"p": 1, "n": 2, "b": 3, "r": 4, "q": 5, "k": 6}
        _fields = fen_string.split()
        assert len(_fields) == 6, _error_info
        _tmp_position = 0
        # Parse First field (Piece Placement)
        for sym in _fields[0]:
            if sym == "/":
                assert _tmp_position % 8 == 0, _error_info
                continue
            if sym.isdigit():
                _tmp_position += int(sym)
                assert _tmp_position < 64, _error_info
                continue
            assert sym.lower() in _fen_dict, _error_info
            _clr = 8 if sym.isupper() else 16
            _type = _fen_dict[sym.lower()]
            _tmp_board._board[_tmp_position] = _clr | _type
            _tmp_position += 1
        assert _tmp_position == 64, _error_info
        # Parse Second Field (Active Color)
        if _fields[1] == "b":
            _tmp_board._active_colour = 16
        elif _fields[1] == "w":
            _tmp_board._active_colour = 8
        else:
            assert False, _error_info
        # Parse Third field (Castling Rights)
        if _fields[2] != "-":
            for castling in _fields[2]:
                if castling.lower() == "q":
                    _tmp_board._castling_rights[
                        "wq" if castling.isupper() else "bq"] = True
                elif castling.lower() == "k":
                    _tmp_board._castling_rights[
                        "wk" if castling.isupper() else "bk"] = True
                else:
                    assert False, _error_info
        # Parse Fourth field (Possible En Passant Targets)
        _alg_cell = _fields[3]
        if _alg_cell != "-":
            assert len(_alg_cell) == 2, _error_info
            assert 96 < ord(_alg_cell[0]) < 105, _error_info
            assert _alg_cell[1].isdigit() and 0 < int(_alg_cell[1]) < 9
            _tmp_board._en_passant_target = int(
                (8 - int(_alg_cell[1])) * 8 + ord(_alg_cell[0]) - 97)
        # Parse Fifth field (Half-move Clock)
        assert _fields[4].isnumeric() and int(_fields[4]) >= 0, _error_info
        _tmp_board._halfmoves = int(_fields[4])
        # Parse Sixth field (Full-move Number)
        assert \
            _fields[5].isnumeric() and \
            abs(_tmp_board._halfmoves * 2 - int(_fields[5])) < 2, _error_info
        return _tmp_board

    @classmethod
    def from_fen(cls, fen_string: str) -> Chessboard:
        """Create Chessboard using FEN"""
        try:
            return cls._parse_fen(fen_string)
        except AssertionError as e:
            raise ValueError(str(e))

    @property
    def board(self) -> np.ndarray:
        return self._board


class ChessPiece(Sprite):
    """Chess Piece class"""

    def __init__(self, sprite_img: str, pos: int, *groups: AbstractGroup):
        super().__init__(*groups)
        self.image = utils.load_image(sprite_img)
        self.rect = self.image.get_rect()
        self.move_sprite(pos)

    def move_sprite(self, position: int) -> None:
        self.rect.x = position % 8 * 100
        self.rect.y = position // 8 * 100
