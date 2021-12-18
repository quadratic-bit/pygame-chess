from random import choice
from time import perf_counter
from typing import Optional

import numpy as np

from chess.board import Chessboard
from chess.const import PieceType, PieceColour, Move, Number, console


class ChessBot:
    """Chess AI"""

    def __init__(self, colour=PieceColour.Black):
        """
        Performance logs
        Pure MiniMax       : 76543 states
        Alpha Beta Pruning : 5309  states
        Ordering Moves     : 1418  states
        """
        # Pieces' scores for evaluating board states
        self._scores: dict[PieceType, Number] = {
            PieceType.Pawn: 1, PieceType.Knight: 3,
            PieceType.Bishop: 3, PieceType.Rook: 5,
            PieceType.Queen: 9, PieceType.King: np.inf}
        # Bot's colour
        self._colour = colour
        # Opponent's (player) colour
        self._opponent_colour = PieceColour.White \
            if colour == PieceColour.Black else PieceColour.Black
        # Set randomness to equally good moves
        self._random_state = 0.2
        # Debug variable to log evaluated states amount
        self._count_states = 0

    @staticmethod
    def _get_ordered_moves(board: Chessboard,
                           colour: PieceColour) -> list[Move]:
        """Order moves to reduce amount of states to evaluate"""
        moves = board.get_all_moves(colour)
        return sorted(list(moves), reverse=True)

    @staticmethod
    def _get_depth(board: Chessboard) -> int:
        halfmoves = board.halfmoves
        return \
            1 if halfmoves < 7 else \
            2 if halfmoves < 13 else \
            3 if halfmoves < 19 else \
            4

    def _evaluate(self, board_state: Chessboard) -> Number:
        """Resolve position score for this colour"""
        counter: Number = 0
        for piece in board_state.board:
            # Don't count empty cells
            if piece.Type == PieceType.Empty:
                continue
            side = 1 if piece.Colour == self._colour else -1
            type_ = piece.Type
            # Don't count king
            if type_ != PieceType.King:
                counter += side * self._scores[type_]
        return counter

    def _maxi(self, board_: Chessboard, move_: Move, alpha: Number,
              beta: Number, depth: int) -> tuple[Number, Move]:
        """Maxi part of minimax algorithm"""
        # Simple state evaluation on 0 depth
        if depth < 1:
            return self._evaluate(board_), move_
        # Initialising best found move variable (score, move)
        best_state: tuple[Number, Optional[Move]] = -np.inf, None
        # Iterating through ordered moves to find the best
        for move in self._get_ordered_moves(board_, self._colour):
            # Logging
            self._count_states += 1
            # Making move on the board
            board_.make_move(move)
            # Evaluating the board state
            score = self._mini(board_, move_, alpha, beta,
                               depth - 1)
            # Updating the best score
            if score[0] > best_state[0] or \
                    (score[0] == best_state[0] and
                     np.random.exponential(scale=1) < self._random_state):
                best_state = score[0], move
            # Unmaking the move (because the board will be used later on)
            board_.unmake_move(move)
            # Trying to prune positions' tree
            alpha = max(alpha, score[0])
            if beta <= alpha:
                break
        return best_state  # type: ignore

    def _mini(self, board_: Chessboard, move_: Move, alpha: Number,
              beta: Number, depth: int) -> tuple[Number, Move]:
        """Mini part of minimax algorithm"""
        # Simple state evaluation on 0 depth
        if depth < 1:
            return self._evaluate(board_), move_
        # Initialising best found move variable (score, move)
        best_state: tuple[Number, Optional[Move]] = np.inf, None
        # Iterating through ordered moves to find the best
        for move in self._get_ordered_moves(board_, self._opponent_colour):
            # Logging
            self._count_states += 1
            # Making move on the board
            board_.make_move(move)
            # Evaluating the board state
            score = self._maxi(board_, move_, alpha, beta,
                               depth - 1)
            # Updating the best score
            if score[0] < best_state[0] or \
                    (score[0] == best_state[0] and
                     np.random.exponential(scale=1) < self._random_state):
                best_state = score[0], move
            # Unmaking the move (because the board will be used later on)
            board_.unmake_move(move)
            # Trying to prune positions' tree
            beta = min(beta, score[0])
            if beta <= alpha:
                break
        return best_state  # type: ignore

    def get_move(self, board_: Chessboard, last_move_: Move,
                 debug=False) -> Move:
        # Logging
        self._count_states = 0
        # Depth
        depth = self._get_depth(board_)
        if not debug:
            # Returning result
            return self._maxi(board_, last_move_, -np.inf, np.inf, depth)[1]
        # Set up performance test
        start = perf_counter()
        # Calculating result
        result = self._maxi(board_, last_move_, -np.inf, np.inf, depth)[1]
        end = perf_counter()
        console.log(f"[bold cyan]{round(end - start, 1)}[/bold cyan]s :"
                    f" [bold cyan]{self._count_states}[/bold cyan] positions :"
                    f" [bold cyan]{depth}[/bold cyan] depth")
        return result
