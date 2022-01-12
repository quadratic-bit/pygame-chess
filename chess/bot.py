from time import perf_counter
from typing import Optional

import numpy as np

from chess.board import Chessboard
from chess.const import PieceType, PieceColour, Move, Number


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
        self._scores: dict[PieceType, int] = {
            PieceType.Pawn: 1, PieceType.Knight: 3,
            PieceType.Bishop: 3, PieceType.Rook: 5,
            PieceType.Queen: 9, PieceType.King: 0}
        # Bot's colour
        self._colour = colour
        # Set randomness to equally good moves
        self._random_state = 0.2
        # Debug variable to log evaluated states amount
        self._count_states = 0
        # Store hashed tables to prune repeated positions
        self._zobrist_hash: dict[int, (Number, Move)] = {}

    @staticmethod
    def _get_ordered_moves(board: Chessboard,
                           colour: PieceColour) -> list[Move]:
        """Order moves to reduce amount of states to evaluate"""
        # No castling because bot can't perform it properly
        moves = list(board.get_all_moves(colour, no_castling=True))
        moves.sort(reverse=True)
        return moves

    @staticmethod
    def _get_depth(board: Chessboard) -> int:
        halfmoves = board.halfmoves
        return 2 if halfmoves < 13 else 4

    def _evaluate(self, board_state: Chessboard) -> Number:
        """Resolve position score for white colour"""
        counter: Number = 0
        for piece in board_state.board:
            # Don't count empty cells
            if piece.Type == PieceType.Empty:
                continue
            counter += self._scores[piece.Type] * (
                1 if piece.Colour == PieceColour.White else -1)
        return counter

    def _minimax(self, board_: Chessboard, move_: Move, alpha: Number,
                 beta: Number, depth: int,
                 maximise: bool) -> tuple[Number, Move]:
        # Prune evaluated position
        board_hash = board_.hash()
        if board_hash in self._zobrist_hash:
            return self._zobrist_hash[board_hash]
        # Initialising best found move variable (score, move)
        best_state: tuple[Number, Optional[Move]]
        # Simple state evaluation on 0 depth
        if depth < 1:
            return self._evaluate(board_), move_
        elif maximise:
            best_state = -np.inf, None
            # Iterating through ordered moves to find the best
            for move in self._get_ordered_moves(board_, PieceColour.White):
                # Logging
                self._count_states += 1
                # Making move on the board
                board_.make_move(move)
                # Evaluating the board state
                score = self._minimax(board_, move_, alpha, beta,
                                      depth - 1, False)
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
        else:
            # Initialising best found move variable (score, move)
            best_state = np.inf, None
            # Iterating through ordered moves to find the best
            for move in self._get_ordered_moves(board_, PieceColour.Black):
                # Logging
                self._count_states += 1
                # Making move on the board
                board_.make_move(move)
                # Evaluating the board state
                score = self._minimax(board_, move_, alpha, beta,
                                      depth - 1, True)
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
        self._zobrist_hash[board_hash] = best_state
        return best_state  # type: ignore

    def get_move(self, board_: Chessboard,
                 last_move_: Move) -> tuple[Move, tuple]:
        # Logging
        self._count_states = 0
        # Depth
        depth = self._get_depth(board_)
        # Hash
        self._zobrist_hash = {}
        # Colour
        bot_side = self._colour == PieceColour.White
        # Set up performance test
        start = perf_counter()
        # Calculating result
        result = self._minimax(board_, last_move_, -np.inf, np.inf, depth,
                               bot_side)
        end = perf_counter()
        evaluation, dtime, states = \
            result[0], round(end - start, 1), self._count_states
        return result[1], (evaluation, dtime, states, depth)
