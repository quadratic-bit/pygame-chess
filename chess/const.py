from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from random import randint
from typing import Optional, Union

import numpy as np
from rich.console import Console

Number = Union[float, int]
console = Console(color_system="256", width=100)


class PieceType(Enum):
    Empty = 0
    Pawn = 1
    Knight = 2
    Bishop = 3
    Rook = 4
    Queen = 5
    King = 6


class PieceColour(Enum):
    Empty = 0
    White = 8
    Black = 16


@dataclass(init=True, frozen=True)
class Piece:
    Type: PieceType
    Colour: PieceColour

    @classmethod
    def empty(cls) -> Piece:
        return cls(PieceType.Empty, PieceColour.Empty)


class CastlingType(Enum):
    BlackKing = auto()
    WhiteKing = auto()
    BlackQueen = auto()
    WhiteQueen = auto()


@dataclass(init=True, frozen=True)
class MoveFlags:
    PawnPromotion: Optional[Piece] = None
    Castling: Optional[CastlingType] = None


SCORES: dict[PieceType, Number] = {
    PieceType.Empty: 0,
    PieceType.Pawn: 1, PieceType.Knight: 3,
    PieceType.Bishop: 3, PieceType.Rook: 5,
    PieceType.Queen: 9, PieceType.King: 10}

PIECE_INDICES: dict[int, int] = {
    PieceType.Pawn.value | PieceColour.White.value: 0,
    PieceType.Pawn.value | PieceColour.Black.value: 1,
    PieceType.Knight.value | PieceColour.White.value: 2,
    PieceType.Knight.value | PieceColour.Black.value: 3,
    PieceType.Bishop.value | PieceColour.White.value: 4,
    PieceType.Bishop.value | PieceColour.Black.value: 5,
    PieceType.Rook.value | PieceColour.White.value: 6,
    PieceType.Rook.value | PieceColour.Black.value: 7,
    PieceType.Queen.value | PieceColour.White.value: 8,
    PieceType.Queen.value | PieceColour.Black.value: 9,
    PieceType.King.value | PieceColour.White.value: 10,
    PieceType.King.value | PieceColour.Black.value: 11}


@dataclass(frozen=True)
class Move:
    From: int
    To: int
    Captured: Piece
    Flags = MoveFlags()

    def __lt__(self, other: Move) -> bool:
        return SCORES[self.Captured.Type] < SCORES[other.Captured.Type]


def init_zobrist() -> list[list[int]]:
    """Fill a table with random bits"""
    return [[randint(1, 2**64 - 1) for _ in range(12)] for _ in range(64)]
