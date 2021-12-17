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
        # First n moves will be completely random
        self._random_moves = 0
        # Set randomness to equally good moves
        self._random_state = 0.2
        # Debug variable to log evaluated states amount
        self._count_states = 0

    def set_random_moves(self, moves_n: int) -> None:
        """First moves_n moves will be random"""
        self._random_moves = max(0, moves_n)

    @staticmethod
    def _get_ordered_moves(board: Chessboard,
                           colour: PieceColour) -> list[Move]:
        """Order moves to reduce amount of states to evaluate"""
        moves = board.get_all_moves(colour)
        return sorted(list(moves), reverse=True)

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
        if depth == 0:
            return self._evaluate(board_), move_
        # Checking for random moves
        if self._random_moves > 0:
            self._random_moves -= 1
            return 0, choice(board_.get_all_moves(self._colour))
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
        if depth == 0:
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
                 depth=3, debug=False) -> Move:
        # Logging
        self._count_states = 0
        if not debug:
            # Returning result
            return self._maxi(board_, last_move_, -np.inf, np.inf, depth)[1]
        # Set up performance test
        start = perf_counter()
        # Calculating result
        result = self._maxi(board_, last_move_, -np.inf, np.inf, depth)[1]
        end = perf_counter()
        console.log(f"Performed the best move in [bold cyan]"
                    f"{round((end - start) * 1000)}[/bold cyan]ms "
                    f"with [bold cyan]{self._count_states}[/bold cyan] "
                    f"positions evaluated.")
        return result
