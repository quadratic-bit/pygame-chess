from enum import Enum


class PieceColour(Enum):
    White = 8
    Black = 16


class PieceType(Enum):
    Empty = 0
    Pawn = 1
    Knight = 2
    Bishop = 3
    Rook = 4
    Queen = 5
    King = 6
