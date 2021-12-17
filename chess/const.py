from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Union

from rich.console import Console

Number = Union[float, int]
console = Console(color_system="truecolor", width=100)


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
    White = 1
    Black = 2


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


@dataclass(frozen=True)
class Move:
    From: int
    To: int
    Captured: Piece
    Flags = MoveFlags()

    def __lt__(self, other: Move) -> bool:
        return SCORES[self.Captured.Type] < SCORES[other.Captured.Type]
