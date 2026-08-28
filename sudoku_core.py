# sudoku_core.py
import random

class SudokuCore:
    """数独核心逻辑（完全独立于界面）"""
    
    @staticmethod
    def generate_solution():
        board = [[0 for _ in range(9)] for _ in range(9)]
        SudokuCore._solve(board)
        return board
    
    @staticmethod
    def _solve(board):
        empty = SudokuCore._find_empty(board)
        if not empty: return True
        row, col = empty
        numbers = list(range(1, 10))
        random.shuffle(numbers)
        for num in numbers:
            if SudokuCore._is_valid(board, row, col, num):
                board[row][col] = num
                if SudokuCore._solve(board): return True
                board[row][col] = 0
        return False
    
    @staticmethod
    def _find_empty(board):
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0: return (i, j)
        return None
    
    @staticmethod
    def _is_valid(board, row, col, num):
        for j in range(9):
            if board[row][j] == num: return False
        for i in range(9):
            if board[i][col] == num: return False
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(start_row, start_row + 3):
            for j in range(start_col, start_col + 3):
                if board[i][j] == num: return False
        return True

    @staticmethod
    def _count_solutions(board, limit=2):
        """统计解的数量，数到 limit 即提前返回（用于唯一性判断）。
        用最少候选数(MRV)优先展开最受限的空格，剪枝极快。"""
        best = None
        best_count = 10
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    c = sum(1 for n in range(1, 10) if SudokuCore._is_valid(board, i, j, n))
                    if c == 0:
                        return 0  # 已无解
                    if c < best_count:
                        best_count = c
                        best = (i, j)
        if best is None:
            return 1
        row, col = best
        count = 0
        for num in range(1, 10):
            if SudokuCore._is_valid(board, row, col, num):
                board[row][col] = num
                count += SudokuCore._count_solutions(board, limit)
                board[row][col] = 0
                if count >= limit:
                    return count
        return count

    @staticmethod
    def generate_puzzle(difficulty='easy'):
        solution = SudokuCore.generate_solution()
        puzzle = [row[:] for row in solution]
        # 目标挖空数量（作为上限，实际以保证唯一解为准）
        cells_to_remove = {'easy': 38, 'medium': 48, 'hard': 56}.get(difficulty, 38)
        positions = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(positions)
        removed = 0
        for i, j in positions:
            if removed >= cells_to_remove:
                break
            backup = puzzle[i][j]
            puzzle[i][j] = 0
            # 仅当挖空后仍然唯一解时才保留这次挖空，否则还原
            if SudokuCore._count_solutions([row[:] for row in puzzle], limit=2) != 1:
                puzzle[i][j] = backup
            else:
                removed += 1
        return puzzle, solution

class SudokuGame:
    """游戏状态管理"""
    def __init__(self, difficulty='easy'):
        self.difficulty = difficulty
        self.puzzle, self.solution = SudokuCore.generate_puzzle(difficulty)
        self.board = [row[:] for row in self.puzzle]
        self.original_puzzle = [row[:] for row in self.puzzle]
    
    def is_valid_move(self, row, col, num):
        original = self.board[row][col]
        self.board[row][col] = 0
        valid = SudokuCore._is_valid(self.board, row, col, num)
        self.board[row][col] = original
        return valid
    
    def check_win(self):
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0 or self.board[i][j] != self.solution[i][j]:
                    return False
        return True
