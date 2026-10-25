"""数独核心逻辑：生成、求解、唯一解校验与会话状态。

本模块不依赖 Kivy，可单独运行测试。
"""

import random
from typing import List, Optional, Tuple

SIZE = 9
BOX = 3
DIFFICULTY_HOLES = {"easy": 38, "medium": 48, "hard": 52}

Board = List[List[int]]
Position = Tuple[int, int]


def _empty_board() -> Board:
    return [[0] * SIZE for _ in range(SIZE)]


class SudokuCore:
    """纯算法集合，不保存任何状态。"""

    @staticmethod
    def generate_solution() -> Board:
        """生成一个随机的完整解。"""
        board = _empty_board()
        SudokuCore._solve(board)
        return board

    @staticmethod
    def _solve(board: Board) -> bool:
        empty = SudokuCore._find_empty(board)
        if empty is None:
            return True
        row, col = empty
        numbers = list(range(1, SIZE + 1))
        random.shuffle(numbers)
        for num in numbers:
            if SudokuCore._is_valid(board, row, col, num):
                board[row][col] = num
                if SudokuCore._solve(board):
                    return True
                board[row][col] = 0
        return False

    @staticmethod
    def _find_empty(board: Board) -> Optional[Position]:
        for row in range(SIZE):
            for col in range(SIZE):
                if board[row][col] == 0:
                    return row, col
        return None

    @staticmethod
    def _is_valid(board: Board, row: int, col: int, num: int) -> bool:
        """num 放在 (row, col) 是否与同行/同列/同宫冲突。"""
        for c in range(SIZE):
            if board[row][c] == num:
                return False
        for r in range(SIZE):
            if board[r][col] == num:
                return False
        start_row = (row // BOX) * BOX
        start_col = (col // BOX) * BOX
        for r in range(start_row, start_row + BOX):
            for c in range(start_col, start_col + BOX):
                if board[r][c] == num:
                    return False
        return True

    @staticmethod
    def _count_solutions(board: Board, limit: int = 2) -> int:
        """统计解的个数，达到 limit 即提前返回（用于唯一性判断）。

        按最少候选数（MRV）优先展开，剪枝更快。
        """
        best: Optional[Position] = None
        best_candidates = SIZE + 1
        for row in range(SIZE):
            for col in range(SIZE):
                if board[row][col] != 0:
                    continue
                candidates = sum(
                    1
                    for num in range(1, SIZE + 1)
                    if SudokuCore._is_valid(board, row, col, num)
                )
                if candidates == 0:
                    return 0
                if candidates < best_candidates:
                    best_candidates = candidates
                    best = (row, col)
        if best is None:
            return 1

        row, col = best
        count = 0
        for num in range(1, SIZE + 1):
            if not SudokuCore._is_valid(board, row, col, num):
                continue
            board[row][col] = num
            count += SudokuCore._count_solutions(board, limit)
            board[row][col] = 0
            if count >= limit:
                return count
        return count

    @staticmethod
    def generate_puzzle(difficulty: str = "easy") -> Tuple[Board, Board]:
        """返回 (题面, 完整解)，题面保证唯一解。"""
        if difficulty not in DIFFICULTY_HOLES:
            raise ValueError(f"未知难度: {difficulty}")

        solution = SudokuCore.generate_solution()
        puzzle = [row[:] for row in solution]
        target_holes = DIFFICULTY_HOLES[difficulty]
        positions = [(row, col) for row in range(SIZE) for col in range(SIZE)]
        random.shuffle(positions)

        holes = 0
        for row, col in positions:
            if holes >= target_holes:
                break
            backup = puzzle[row][col]
            puzzle[row][col] = 0
            if SudokuCore._count_solutions([r[:] for r in puzzle]) == 1:
                holes += 1
            else:
                puzzle[row][col] = backup
        return puzzle, solution


class SudokuGame:
    """一局游戏的状态：题面、解答、玩家棋盘。"""

    def __init__(self, difficulty: str = "easy"):
        self.difficulty = difficulty
        self.puzzle, self.solution = SudokuCore.generate_puzzle(difficulty)
        self.board = [row[:] for row in self.puzzle]

    def is_valid_move(self, row: int, col: int, num: int) -> bool:
        """玩家把 num 填到 (row, col) 是否与当前棋盘冲突（不改动棋盘）。"""
        board = [row_copy[:] for row_copy in self.board]
        board[row][col] = 0
        return SudokuCore._is_valid(board, row, col, num)

    def check_win(self) -> bool:
        return self.board == self.solution
